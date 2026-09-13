"""Tests for tool-use audit logs and metrics."""

from __future__ import annotations

import json
from pathlib import Path

from mimirbench.evals.runner import run_eval_config
from mimirbench.evals.schemas import (
    AgentConfig,
    EnvironmentFamily,
    EnvironmentRunConfig,
    EvalRunConfig,
    EvalTaskRecord,
    GraderResult,
    ReportingConfig,
    RunSettings,
)
from mimirbench.evals.tool_audit import (
    aggregate_tool_audit,
    collect_tool_audits,
    has_tool_audit,
)


def _tool_config(tmp_path: Path) -> EvalRunConfig:
    return EvalRunConfig(
        run=RunSettings(
            name="tool_audit_test",
            seed=1,
            output_dir=str(tmp_path / "run"),
            cache=False,
            max_workers=1,
        ),
        agent=AgentConfig(type="tool", tool_policy="reference", tool_max_steps=3),
        environments=[EnvironmentRunConfig(name="bayesian_games", num_tasks=4, seed=1)],
        reporting=ReportingConfig(),
    )


def test_tool_audit_artefacts_written(tmp_path: Path) -> None:
    summary = run_eval_config(_tool_config(tmp_path))
    output_dir = Path(summary["output_dir"])
    assert (output_dir / "tool_audit.jsonl").exists()
    assert (output_dir / "tool_audit.md").exists()

    metrics = summary["tool_audit"]
    assert metrics["n_tasks"] == 4
    assert metrics["tool_call_rate"] == 1.0
    assert metrics["invalid_tool_call_rate"] == 0.0
    assert metrics["tool_error_rate"] == 0.0
    assert metrics["final_answer_after_tool_rate"] == 1.0

    rows = [
        json.loads(line)
        for line in (output_dir / "tool_audit.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert rows
    for row in rows:
        assert set(row) >= {
            "task_id",
            "environment",
            "agent",
            "step_number",
            "requested_tool",
            "tool_arguments",
            "validation_status",
            "tool_output",
            "tool_error",
            "final_answer_used_tool_result",
            "latency_ms",
        }


def _record(
    task_id: str,
    *,
    steps: list[dict],
    final: dict | None,
) -> EvalTaskRecord:
    return EvalTaskRecord(
        run_id="run",
        timestamp="2026-01-01T00:00:00Z",
        environment="bayesian_games",
        task_id=task_id,
        seed=1,
        agent_type="tool",
        agent_name="tool::test",
        raw_prompt="p",
        model_response=json.dumps(final) if final else "",
        parsed_response=final,
        grader_result=GraderResult(
            task_id=task_id, family=EnvironmentFamily.BAYESIAN_GAMES, score=1.0, passed=True
        ),
        metadata={"response_metadata": {"tool_audit_steps": steps}},
    )


def test_invalid_and_ignored_rates_are_detected() -> None:
    # Task A: valid tool call, final answer reuses the tool's posterior -> used.
    record_a = _record(
        "a",
        steps=[
            {
                "step_number": 1,
                "requested_tool": "bayes_calculator",
                "tool_arguments": {},
                "validation_status": "allowed",
                "tool_output": {"posterior": [0.25, 0.75]},
                "tool_error": None,
                "latency_ms": 0.1,
            }
        ],
        final={"posterior": [0.25, 0.75]},
    )
    # Task B: one invalid (disallowed) call + a valid call whose output is ignored.
    record_b = _record(
        "b",
        steps=[
            {
                "step_number": 1,
                "requested_tool": "risk_checker",
                "tool_arguments": {},
                "validation_status": "not_allowed",
                "tool_output": None,
                "tool_error": "not allowed",
                "latency_ms": 0.0,
            },
            {
                "step_number": 2,
                "requested_tool": "bayes_calculator",
                "tool_arguments": {},
                "validation_status": "allowed",
                "tool_output": {"posterior": [0.1, 0.9]},
                "tool_error": None,
                "latency_ms": 0.1,
            },
        ],
        final={"posterior": [0.6, 0.4]},  # does not match the tool output -> ignored
    )

    records = [record_a, record_b]
    assert has_tool_audit(records) is True
    audits = collect_tool_audits(records)
    metrics = aggregate_tool_audit(audits)

    assert metrics["n_tasks"] == 2
    # 3 tool-request steps total, 1 invalid -> 1/3.
    assert metrics["invalid_tool_call_rate"] == 1 / 3
    assert metrics["tool_error_rate"] == 0.0  # executed steps had no execution error
    assert metrics["mean_tool_steps"] == 1.5
    # Both tasks have a usable tool output + final answer; task B ignored it.
    assert metrics["tool_result_ignored_rate"] == 0.5


def test_used_tool_result_heuristic_flags_reuse() -> None:
    record = _record(
        "a",
        steps=[
            {
                "step_number": 1,
                "requested_tool": "bayes_calculator",
                "tool_arguments": {},
                "validation_status": "allowed",
                "tool_output": {"posterior": [0.25, 0.75]},
                "tool_error": None,
                "latency_ms": 0.1,
            }
        ],
        final={"posterior": [0.25, 0.75]},
    )
    audit = collect_tool_audits([record])[0]
    assert audit.steps[0].final_answer_used_tool_result is True


def test_non_tool_records_have_no_audit() -> None:
    record = EvalTaskRecord(
        run_id="run",
        timestamp="2026-01-01T00:00:00Z",
        environment="bayesian_games",
        task_id="x",
        seed=1,
        agent_type="reference",
        agent_name="reference",
        raw_prompt="p",
        model_response="{}",
        parsed_response={},
        grader_result=GraderResult(
            task_id="x", family=EnvironmentFamily.BAYESIAN_GAMES, score=1.0, passed=True
        ),
    )
    assert has_tool_audit([record]) is False
    assert collect_tool_audits([record]) == []
    assert aggregate_tool_audit([])["n_tasks"] == 0
