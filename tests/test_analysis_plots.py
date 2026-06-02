"""Tests for Stage 6 Matplotlib plot generation."""

from __future__ import annotations

import inspect

from mimirbench.analysis import plots
from mimirbench.analysis.plots import generate_run_plots
from mimirbench.evals.schemas import EnvironmentFamily, EvalTaskRecord, GraderResult
from mimirbench.evals.writers import write_results_jsonl


def _record(
    task_id: str,
    *,
    environment: str,
    family: EnvironmentFamily,
    parsed: dict[str, object] | None,
    score: float,
    metrics: dict[str, float],
    violations: list[str] | None = None,
) -> EvalTaskRecord:
    return EvalTaskRecord(
        run_id="run",
        timestamp="2026-06-02T00:00:00Z",
        environment=environment,
        task_id=task_id,
        seed=1,
        agent_type="mock",
        agent_name="mock",
        raw_prompt="prompt",
        model_response="{}",
        parsed_response=parsed,
        grader_result=GraderResult(
            task_id=task_id,
            family=family,
            score=score,
            passed=score >= 0.8,
            metrics=metrics,
            violations=violations or [],
        ),
        latency_ms=10.0,
    )


def test_plots_generated_without_seaborn(tmp_path) -> None:  # type: ignore[no-untyped-def]
    run_dir = tmp_path / "run"
    write_results_jsonl(
        [
            _record(
                "bayes-1",
                environment="bayesian_games",
                family=EnvironmentFamily.BAYESIAN_GAMES,
                parsed={"posterior": [0.9, 0.1]},
                score=0.9,
                metrics={"posterior_tv_error": 0.1},
            ),
            _record(
                "pm-1",
                environment="prediction_markets",
                family=EnvironmentFamily.PREDICTION_MARKETS,
                parsed={"action": "buy", "confidence": 0.8},
                score=0.2,
                metrics={"regret": 0.3, "risk_limit_violation": 1.0},
                violations=["budget_limit"],
            ),
        ],
        run_dir / "results.jsonl",
    )

    generated = generate_run_plots(run_dir)
    names = {path.name for path in generated}
    assert "score_by_environment.png" in names
    assert "risk_violation_rate_by_environment.png" in names
    assert "latency_distribution.png" in names
    assert "parse_failure_rate_by_agent.png" in names
    assert all(path.exists() and path.stat().st_size > 0 for path in generated)
    assert "seaborn" not in inspect.getsource(plots).lower()
