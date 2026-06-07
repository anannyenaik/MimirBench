"""Power-planning tests over tiny saved-artifact fixtures only."""

from __future__ import annotations

from pathlib import Path

from mimirbench.analysis.power_planning import (
    build_power_planning_markdown,
    estimate_ci_widths,
    write_power_planning_report,
)
from mimirbench.analysis.statistical_validity import CanonicalRow
from mimirbench.evals.schemas import (
    EnvironmentFamily,
    EvalTaskRecord,
    GraderResult,
)
from mimirbench.evals.writers import write_results_jsonl


def _record(task_id: str, score: float) -> EvalTaskRecord:
    return EvalTaskRecord(
        run_id="fixture",
        timestamp="2026-06-07T00:00:00Z",
        environment="bayesian_games",
        task_id=task_id,
        seed=123,
        agent_type="api",
        agent_name="direct",
        raw_prompt="fixture",
        model_response="{}",
        parsed_response={"posterior": [1.0]},
        grader_result=GraderResult(
            task_id=task_id,
            family=EnvironmentFamily.BAYESIAN_GAMES,
            score=score,
            passed=score >= 0.5,
        ),
    )


def test_estimated_ci_width_shrinks_with_planned_scale() -> None:
    estimates = estimate_ci_widths([0.0, 0.25, 0.75, 1.0])
    assert estimates[0].planned_n == 120
    assert estimates[1].planned_n == 1_800
    assert estimates[2].planned_n == 6_000
    assert estimates[0].approximate_ci_width > estimates[1].approximate_ci_width
    assert estimates[1].approximate_ci_width > estimates[2].approximate_ci_width


def test_power_planning_output_uses_saved_tiny_fixture(tmp_path: Path) -> None:
    row = CanonicalRow(
        key="fixture",
        display="Fixture model",
        provider="openai",
        track="strict-track clean",
        run_dir="fixture_run",
        model_dir="fixture_model",
        agent="direct",
        caveat="fixture only",
    )
    results = tmp_path / "fixture_run" / "models" / "fixture_model" / "agents" / "direct"
    results.mkdir(parents=True)
    write_results_jsonl(
        [_record("t0", 0.0), _record("t1", 0.5), _record("t2", 1.0)],
        results / "results.jsonl",
    )

    markdown = build_power_planning_markdown(tmp_path, rows=(row,))
    assert "Fixture model" in markdown
    assert "planning estimates based on pilot variance" in markdown
    assert "not results from unrun hosted-model evaluations" in markdown

    path = write_power_planning_report(
        tmp_path,
        output_path=tmp_path / "power.md",
        rows=(row,),
    )
    assert path.exists()
