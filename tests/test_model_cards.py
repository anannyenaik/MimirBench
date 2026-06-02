"""Tests for model-card generation from actual artefacts."""

from __future__ import annotations

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
from mimirbench.evals.writers import build_summary, write_results_jsonl, write_summary_json
from mimirbench.reports.model_cards import generate_model_card


def test_model_card_generated_only_from_actual_run_artefacts(tmp_path) -> None:  # type: ignore[no-untyped-def]
    missing = tmp_path / "missing"
    missing.mkdir()
    assert generate_model_card(missing, output_dir=tmp_path / "cards") is None

    run_dir = tmp_path / "run"
    record = EvalTaskRecord(
        run_id="run-1",
        timestamp="2026-06-02T00:00:00Z",
        environment="bayesian_games",
        task_id="task-1",
        seed=1,
        agent_type="mock",
        agent_name="mock::random_valid",
        raw_prompt="prompt",
        model_response='{"posterior":[1.0]}',
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
        run=RunSettings(name="card_run", output_dir=str(run_dir)),
        agent=AgentConfig(type="mock", behaviour="random_valid"),
        environments=[EnvironmentRunConfig(name="bayesian_games", num_tasks=1, seed=1)],
        reporting=ReportingConfig(),
    )
    write_results_jsonl([record], run_dir / "results.jsonl")
    summary = build_summary(
        config=config,
        run_id="run-1",
        timestamp="2026-06-02T00:00:00Z",
        output_dir=run_dir,
        records=[record],
    )
    write_summary_json(summary, run_dir / "summary.json")

    card = generate_model_card(run_dir, output_dir=tmp_path / "cards")
    assert card is not None
    text = card.read_text(encoding="utf-8")
    assert "mock diagnostic baseline" in text
    assert "No LLM judges" in text
