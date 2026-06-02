"""Tests for cost/latency aggregation across run records."""

from __future__ import annotations

from mimirbench.evals.schemas import EnvironmentFamily, EvalTaskRecord, GraderResult
from mimirbench.evals.scoring import aggregate_cost_latency


def _record(
    task_id: str,
    *,
    usage: dict | None,
    latency_ms: float | None,
    error: str | None = None,
    parsed: dict | None = None,
    violations: list[str] | None = None,
) -> EvalTaskRecord:
    metadata: dict = {}
    if usage is not None:
        metadata["response_metadata"] = {"usage": usage}
    return EvalTaskRecord(
        run_id="run",
        timestamp="2026-01-01T00:00:00Z",
        environment="bayesian_games",
        task_id=task_id,
        seed=1,
        agent_type="api",
        agent_name="api::fake",
        raw_prompt="p",
        model_response="{}",
        parsed_response=parsed,
        grader_result=GraderResult(
            task_id=task_id,
            family=EnvironmentFamily.BAYESIAN_GAMES,
            score=1.0 if parsed else 0.0,
            passed=bool(parsed),
            violations=violations or [],
        ),
        latency_ms=latency_ms,
        error=error,
        metadata=metadata,
    )


def test_aggregate_tokens_and_latency() -> None:
    records = [
        _record(
            "a",
            usage={"input_tokens": 100, "output_tokens": 50, "total_tokens": 150, "estimated_cost_usd": None},
            latency_ms=10.0,
            parsed={"posterior": [1.0]},
        ),
        _record(
            "b",
            usage={"input_tokens": 200, "output_tokens": 80, "total_tokens": 280, "estimated_cost_usd": None},
            latency_ms=30.0,
            parsed={"posterior": [1.0]},
        ),
    ]
    agg = aggregate_cost_latency(records)
    assert agg["total_input_tokens"] == 300
    assert agg["total_output_tokens"] == 130
    assert agg["total_tokens"] == 430
    assert agg["mean_latency_ms"] == 20.0
    assert agg["p50_latency_ms"] == 20.0
    assert agg["p95_latency_ms"] == 29.0


def test_cost_not_estimated_without_pricing() -> None:
    records = [
        _record(
            "a",
            usage={"input_tokens": 100, "output_tokens": 50, "estimated_cost_usd": None},
            latency_ms=5.0,
            parsed={"x": 1},
        )
    ]
    agg = aggregate_cost_latency(records)
    assert agg["estimated_total_cost_usd"] is None
    assert agg["cost_estimated"] is False
    assert "not estimated" in agg["cost_note"]


def test_cost_summed_when_available() -> None:
    records = [
        _record(
            "a",
            usage={"input_tokens": 100, "output_tokens": 50, "estimated_cost_usd": 0.01},
            latency_ms=5.0,
            parsed={"x": 1},
        ),
        _record(
            "b",
            usage={"input_tokens": 100, "output_tokens": 50, "estimated_cost_usd": 0.02},
            latency_ms=7.0,
            parsed={"x": 1},
        ),
    ]
    agg = aggregate_cost_latency(records)
    assert agg["estimated_total_cost_usd"] == 0.03
    assert agg["cost_estimated"] is True


def test_error_parse_and_timeout_rates() -> None:
    records = [
        _record("a", usage=None, latency_ms=5.0, parsed={"posterior": [1.0]}),
        _record(
            "b",
            usage=None,
            latency_ms=5.0,
            parsed=None,
            error="TimeoutError: request timed out",
            violations=["no_valid_answer"],
        ),
        _record(
            "c",
            usage=None,
            latency_ms=5.0,
            parsed=None,
            error="ModelClientError: boom",
            violations=["no_valid_answer"],
        ),
    ]
    agg = aggregate_cost_latency(records)
    assert agg["provider_error_rate"] == 2 / 3
    assert agg["timeout_rate"] == 1 / 3
    assert agg["parse_failure_rate"] == 2 / 3
    assert agg["invalid_response_rate"] == 2 / 3


def test_aggregate_is_robust_to_missing_usage_and_empty() -> None:
    assert aggregate_cost_latency([])["total_tokens"] is None
    records = [_record("a", usage=None, latency_ms=None, parsed={"x": 1})]
    agg = aggregate_cost_latency(records)
    assert agg["total_tokens"] is None
    assert agg["mean_latency_ms"] is None
    assert agg["n_model_tasks"] == 0
