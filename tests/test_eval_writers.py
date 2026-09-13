"""Result writer tests."""

from __future__ import annotations

import json
from pathlib import Path

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
from mimirbench.evals.writers import (
    build_summary,
    load_records_jsonl,
    write_markdown_report,
    write_results_jsonl,
    write_summary_json,
)


def test_writers_emit_expected_files(tmp_path: Path) -> None:
    record = EvalTaskRecord(
        run_id="run-1",
        timestamp="2026-06-02T00:00:00Z",
        environment="bayesian_games",
        task_id="task-1",
        seed=1,
        agent_type="mock",
        agent_name="mock::random_valid",
        raw_prompt="prompt",
        model_response='{"posterior": [1.0]}',
        parsed_response={"posterior": [1.0]},
        grader_result=GraderResult(
            task_id="task-1",
            family=EnvironmentFamily.BAYESIAN_GAMES,
            score=1.0,
            passed=True,
        ),
        latency_ms=1.0,
    )
    config = EvalRunConfig(
        run=RunSettings(name="writer_test", output_dir=str(tmp_path)),
        agent=AgentConfig(type="mock", behaviour="random_valid"),
        environments=[EnvironmentRunConfig(name="bayesian_games", num_tasks=1, seed=1)],
        reporting=ReportingConfig(),
    )

    results_path = tmp_path / "results.jsonl"
    summary_path = tmp_path / "summary.json"
    report_path = tmp_path / "report.md"

    write_results_jsonl([record], results_path)
    loaded = load_records_jsonl(results_path)
    assert loaded == [record]

    summary = build_summary(
        config=config,
        run_id="run-1",
        timestamp="2026-06-02T00:00:00Z",
        output_dir=tmp_path,
        records=[record],
    )
    write_summary_json(summary, summary_path)
    write_markdown_report(summary=summary, records=[record], path=report_path)

    assert json.loads(summary_path.read_text(encoding="utf-8"))["run_name"] == "writer_test"
    report_text = report_path.read_text(encoding="utf-8")
    assert "deterministic mock" in report_text
    assert "bayesian_games" in report_text
