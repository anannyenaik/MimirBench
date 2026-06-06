"""Tests for statistical-validity analysis over saved artefacts (no model runs)."""

from __future__ import annotations

import json

from mimirbench.analysis.statistical_validity import (
    CanonicalRow,
    TaskScore,
    build_statistical_validity_markdown,
    load_task_scores,
    paired_delta,
    summarise_row,
)
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


def _record(task_id: str, score: float, *, parsed: bool = True) -> EvalTaskRecord:
    return EvalTaskRecord(
        run_id="run-1",
        timestamp="2026-06-06T00:00:00Z",
        environment="bayesian_games",
        task_id=task_id,
        seed=123,
        agent_type="api",
        agent_name="direct",
        raw_prompt="prompt",
        model_response="{}",
        parsed_response={"posterior": [1.0]} if parsed else None,
        grader_result=GraderResult(
            task_id=task_id,
            family=EnvironmentFamily.BAYESIAN_GAMES,
            score=score,
            passed=score >= 0.5,
        ),
        latency_ms=100.0,
    )


def _write_run(base, run_dir_name, model_dir, records):  # type: ignore[no-untyped-def]
    results_dir = base / run_dir_name / "models" / model_dir / "agents" / "direct"
    results_dir.mkdir(parents=True)
    write_results_jsonl(records, results_dir / "results.jsonl")
    config = EvalRunConfig(
        run=RunSettings(name=model_dir, output_dir=str(results_dir)),
        agent=AgentConfig(type="api", provider="openai", model="m"),
        environments=[EnvironmentRunConfig(name="bayesian_games", num_tasks=len(records), seed=123)],
        reporting=ReportingConfig(),
    )
    summary = build_summary(
        config=config,
        run_id="run-1",
        timestamp="2026-06-06T00:00:00Z",
        output_dir=results_dir,
        records=records,
    )
    write_summary_json(summary, results_dir / "summary.json")
    # Minimal leaderboard summary so cost lookup is exercised.
    (base / run_dir_name / "leaderboard_summary.json").write_text(
        json.dumps({"leaderboard": [{"model": model_dir, "estimated_cost_usd": 0.5}]}),
        encoding="utf-8",
    )


def test_load_task_scores_round_trips(tmp_path) -> None:  # type: ignore[no-untyped-def]
    records = [_record("bayesian_games-1", 0.9), _record("bayesian_games-2", 0.1, parsed=False)]
    path = tmp_path / "results.jsonl"
    write_results_jsonl(records, path)
    scores = load_task_scores(path)
    assert [s.score for s in scores] == [0.9, 0.1]
    assert scores[0].passed is True
    assert scores[1].parse_failed is True


def test_summarise_row_brackets_the_mean(tmp_path) -> None:  # type: ignore[no-untyped-def]
    scores = [
        TaskScore("bayesian_games", f"t{i}", 123, score=0.6, passed=True,
                  parse_failed=False, risk_violation=False, latency_ms=float(i))
        for i in range(10)
    ]
    row = CanonicalRow(
        key="k", display="K", provider="openai", track="strict-track clean",
        run_dir="r", model_dir="m", agent="direct", caveat="c",
    )
    stat = summarise_row(row, scores)
    assert stat.n == 10
    assert stat.mean_score.low <= stat.mean_score.mean <= stat.mean_score.high
    # Constant scores collapse the CI to the point estimate.
    assert abs(stat.mean_score.mean - 0.6) < 1e-9


def test_paired_delta_aligns_on_task_identity() -> None:
    base = [TaskScore("bayesian_games", f"t{i}", 123, 0.5, True, False, False, 1.0) for i in range(5)]
    cand = [TaskScore("bayesian_games", f"t{i}", 123, 0.7, True, False, False, 1.0) for i in range(5)]
    delta = paired_delta("base", "cand", base, cand)
    assert delta.aligned is True
    assert delta.n_aligned == 5
    assert abs((delta.mean_delta or 0.0) - 0.2) < 1e-9

    # Disjoint task IDs cannot be paired.
    misaligned = [TaskScore("bayesian_games", f"x{i}", 123, 0.7, True, False, False, 1.0) for i in range(5)]
    unpaired = paired_delta("base", "cand", base, misaligned)
    assert unpaired.aligned is False
    assert unpaired.n_aligned == 0


def test_build_markdown_lists_missing_rows(tmp_path) -> None:  # type: ignore[no-untyped-def]
    rows = (
        CanonicalRow("present", "Present", "openai", "strict-track clean",
                     "run_present", "model_present", "direct", "caveat"),
        CanonicalRow("absent", "Absent", "openai", "best-valid clean",
                     "run_absent", "model_absent", "direct", "caveat"),
    )
    _write_run(
        tmp_path,
        "run_present",
        "model_present",
        [_record(f"bayesian_games-{i}", 0.8) for i in range(6)],
    )
    markdown = build_statistical_validity_markdown(tmp_path, rows=rows)
    assert "Present" in markdown
    assert "Missing artefacts" in markdown
    assert "model_absent" in markdown
    assert "No model is run" in markdown
