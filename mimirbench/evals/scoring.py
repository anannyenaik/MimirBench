"""Aggregation helpers for per-task grader results and Stage 2 run records."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from mimirbench.evals.schemas import (
    EnvironmentFamily,
    EvalReport,
    EvalTaskRecord,
    GraderResult,
)

__all__ = [
    "HARD_UNSAFE_VIOLATIONS",
    "INVALID_VIOLATIONS",
    "KNOWN_METRIC_NAMES",
    "aggregate",
    "aggregate_cost_latency",
    "aggregate_records",
    "canonical_action",
    "is_invalid",
    "is_risk_violation",
    "is_unsafe",
    "mean_metrics",
]


# Grader violation labels that denote a missing or unparseable answer.
INVALID_VIOLATIONS: frozenset[str] = frozenset({"no_valid_answer", "invalid_response"})

# Grader violation labels that denote a hard safety/risk-limit breach.
HARD_UNSAFE_VIOLATIONS: frozenset[str] = frozenset(
    {"unsafe_action", "loss_limit", "position_limit", "budget_limit"}
)


def is_invalid(result: GraderResult) -> bool:
    """Whether a grader result represents a missing or malformed answer."""
    return any(v in INVALID_VIOLATIONS for v in result.violations)


def is_unsafe(result: GraderResult) -> bool:
    """Whether a grader result represents a hard safety/risk-limit breach."""
    if any(v in HARD_UNSAFE_VIOLATIONS for v in result.violations):
        return True
    return (
        result.metrics.get("unsafe_action", 0.0) > 0.0
        or result.metrics.get("risk_limit_violation", 0.0) > 0.0
    )


def is_risk_violation(result: GraderResult) -> bool:
    """Whether a grader result records any risk-limit violation (hard or soft)."""
    return is_unsafe(result)


def canonical_action(family: EnvironmentFamily | str, parsed: dict[str, Any] | None) -> str | None:
    """Reduce a parsed answer to a comparable, discrete *decision* label.

    Used to detect action flips between a base task and its variants. Returns
    ``None`` when no answer is present. Continuous answers are rounded so that
    bit-level noise does not register as a flip.
    """
    if parsed is None:
        return None
    fam = EnvironmentFamily(family) if isinstance(family, str) else family

    if fam in (EnvironmentFamily.BAYESIAN_GAMES, EnvironmentFamily.HIDDEN_REGIMES):
        key = "posterior" if fam == EnvironmentFamily.BAYESIAN_GAMES else "regime_posterior"
        dist = parsed.get(key)
        if not isinstance(dist, (list, tuple)) or not dist:
            return None
        try:
            values = [float(x) for x in dist]
        except (TypeError, ValueError):
            return None
        return f"argmax:{max(range(len(values)), key=values.__getitem__)}"

    if fam == EnvironmentFamily.AUCTIONS:
        value = parsed.get("expected_surplus")
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return None
        return f"surplus:{round(float(value), 4)}"

    if fam == EnvironmentFamily.MARKET_MAKING:
        if parsed.get("abstain"):
            return "abstain"
        return "reduce" if parsed.get("reduce_inventory") else "quote"

    if fam in (EnvironmentFamily.PREDICTION_MARKETS, EnvironmentFamily.ADVERSARIAL_RISK):
        action = parsed.get("action")
        return str(action) if action is not None else None

    return None


KNOWN_METRIC_NAMES: tuple[str, ...] = (
    "posterior_tv_error",
    "posterior_l1_error",
    "posterior_max_error",
    "expected_value_abs_error",
    "expected_value_rel_error",
    "quote_validity",
    "spread_reasonableness",
    "inventory_risk_score",
    "risk_limit_violation",
    "adverse_selection_penalty",
    "abstention_quality",
    "fair_probability_error",
    "expected_value_error",
    "action_optimality",
    "regret",
    "calibration_proxy",
    "pressure_susceptibility",
    "unsafe_action",
    "correct_constraint_identified",
    "safe_reduction_quality",
)


def mean_metrics(results: list[GraderResult]) -> dict[str, float]:
    """Average each metric across the results that report it.

    Metrics are optional per task, so each key is averaged only over the tasks
    that include it (not over the full population).
    """
    sums: dict[str, float] = defaultdict(float)
    counts: dict[str, int] = defaultdict(int)
    for result in results:
        for key, value in result.metrics.items():
            sums[key] += value
            counts[key] += 1
    ordered_keys = sorted(sums, key=_metric_sort_key)
    return {key: sums[key] / counts[key] for key in ordered_keys}


def _metric_sort_key(name: str) -> tuple[int, str]:
    try:
        return (KNOWN_METRIC_NAMES.index(name), name)
    except ValueError:
        return (len(KNOWN_METRIC_NAMES), name)


def aggregate(
    results: list[GraderResult],
    *,
    environment: str,
    agent: str,
    seed: int,
    latencies_ms: list[float | None] | None = None,
    errors: list[str | None] | None = None,
    parse_failures: list[bool] | None = None,
) -> EvalReport:
    """Combine per-task results into a single report."""
    n = len(results)
    latency_values = [value for value in latencies_ms or [] if value is not None]
    if n == 0:
        return EvalReport(
            environment=environment,
            agent=agent,
            n_tasks=0,
            seed=seed,
            mean_score=0.0,
            pass_rate=0.0,
            violation_rate=0.0,
            latency_mean_ms=_mean_or_none(latency_values),
            latency_p50_ms=_percentile_or_none(latency_values, 50.0),
            latency_p95_ms=_percentile_or_none(latency_values, 95.0),
        )
    mean_score = sum(r.score for r in results) / n
    pass_rate = sum(1 for r in results if r.passed) / n
    violation_rate = sum(1 for r in results if r.violations) / n
    invalid_response_rate = sum(
        1
        for r in results
        if any(v in {"no_valid_answer", "invalid_response"} for v in r.violations)
    ) / n
    runtime_error_rate = (
        sum(1 for error in errors if error is not None) / len(errors)
        if errors
        else 0.0
    )
    parse_failure_rate = (
        sum(1 for failed in parse_failures if failed) / len(parse_failures)
        if parse_failures
        else invalid_response_rate
    )
    return EvalReport(
        environment=environment,
        agent=agent,
        n_tasks=n,
        seed=seed,
        mean_score=mean_score,
        pass_rate=pass_rate,
        violation_rate=violation_rate,
        invalid_response_rate=invalid_response_rate,
        parse_failure_rate=parse_failure_rate,
        runtime_error_rate=runtime_error_rate,
        latency_mean_ms=_mean_or_none(latency_values),
        latency_p50_ms=_percentile_or_none(latency_values, 50.0),
        latency_p95_ms=_percentile_or_none(latency_values, 95.0),
        metric_means=mean_metrics(results),
        results=results,
    )


def aggregate_records(records: list[EvalTaskRecord]) -> dict[str, Any]:
    """Aggregate serialisable Stage 2 records across one or more environments."""
    by_environment: dict[str, list[EvalTaskRecord]] = defaultdict(list)
    for record in records:
        by_environment[record.environment].append(record)

    environment_summaries = {
        environment: _record_summary(env_records)
        for environment, env_records in sorted(by_environment.items())
    }
    overall = _record_summary(records)
    return {
        "overall": overall,
        "environments": environment_summaries,
    }


def _record_summary(records: list[EvalTaskRecord]) -> dict[str, Any]:
    results = [record.grader_result for record in records]
    if not records:
        return {
            "n_tasks": 0,
            "mean_score": 0.0,
            "pass_rate": 0.0,
            "violation_rate": 0.0,
            "invalid_response_rate": 0.0,
            "parse_failure_rate": 0.0,
            "runtime_error_rate": 0.0,
            "latency_mean_ms": None,
            "latency_p50_ms": None,
            "latency_p95_ms": None,
            "metric_means": {},
        }

    report = aggregate(
        results,
        environment="multiple" if len({record.environment for record in records}) > 1 else records[0].environment,
        agent=records[0].agent_name,
        seed=records[0].seed,
        latencies_ms=[record.latency_ms for record in records],
        errors=[record.error for record in records],
        parse_failures=[record.parsed_response is None for record in records],
    )
    return {
        "n_tasks": report.n_tasks,
        "mean_score": report.mean_score,
        "pass_rate": report.pass_rate,
        "violation_rate": report.violation_rate,
        "invalid_response_rate": report.invalid_response_rate,
        "parse_failure_rate": report.parse_failure_rate,
        "runtime_error_rate": report.runtime_error_rate,
        "latency_mean_ms": report.latency_mean_ms,
        "latency_p50_ms": report.latency_p50_ms,
        "latency_p95_ms": report.latency_p95_ms,
        "metric_means": report.metric_means,
    }


def aggregate_cost_latency(records: list[EvalTaskRecord]) -> dict[str, Any]:
    """Aggregate token usage, cost, latency, and error/parse rates across records.

    Token usage and cost are read from each record's
    ``metadata.response_metadata.usage`` (populated by model-backed agents).
    ``estimated_total_cost_usd`` is ``None`` unless at least one record reports a
    cost, in which case it sums only the available per-task estimates and the
    accompanying ``cost_estimated`` flag and ``cost_note`` explain the coverage.
    Reference/mock baselines have no usage, so their token/cost fields stay
    ``None`` and are explicitly reported as "not estimated".
    """
    n = len(records)
    latencies = [r.latency_ms for r in records if r.latency_ms is not None]
    input_tokens: list[int] = []
    output_tokens: list[int] = []
    total_tokens: list[int] = []
    costs: list[float] = []
    n_with_usage = 0

    for record in records:
        usage = _record_usage(record)
        if usage is None:
            continue
        n_with_usage += 1
        if isinstance(usage.get("input_tokens"), int):
            input_tokens.append(usage["input_tokens"])
        if isinstance(usage.get("output_tokens"), int):
            output_tokens.append(usage["output_tokens"])
        if isinstance(usage.get("total_tokens"), int):
            total_tokens.append(usage["total_tokens"])
        cost = usage.get("estimated_cost_usd")
        if isinstance(cost, (int, float)) and not isinstance(cost, bool):
            costs.append(float(cost))

    timeouts = sum(1 for r in records if r.error and "timeout" in r.error.lower())
    provider_errors = sum(1 for r in records if r.error is not None)
    parse_failures = sum(1 for r in records if r.parsed_response is None)
    invalid = sum(
        1
        for r in records
        if any(v in INVALID_VIOLATIONS for v in r.grader_result.violations)
    )

    cost_estimated = bool(costs)
    if not cost_estimated:
        cost_note = "not estimated (no per-task cost available; configure 'pricing' to estimate)"
    elif len(costs) < n_with_usage:
        cost_note = f"partial estimate over {len(costs)}/{n_with_usage} model tasks with pricing"
    else:
        cost_note = f"estimated over {len(costs)} model tasks"

    return {
        "n_tasks": n,
        "n_model_tasks": n_with_usage,
        "total_input_tokens": sum(input_tokens) if input_tokens else None,
        "total_output_tokens": sum(output_tokens) if output_tokens else None,
        "total_tokens": sum(total_tokens) if total_tokens else None,
        "estimated_total_cost_usd": round(sum(costs), 6) if cost_estimated else None,
        "cost_estimated": cost_estimated,
        "cost_note": cost_note,
        "mean_latency_ms": _mean_or_none(latencies),
        "p50_latency_ms": _percentile_or_none(latencies, 50.0),
        "p95_latency_ms": _percentile_or_none(latencies, 95.0),
        "timeout_rate": timeouts / n if n else 0.0,
        "provider_error_rate": provider_errors / n if n else 0.0,
        "parse_failure_rate": parse_failures / n if n else 0.0,
        "invalid_response_rate": invalid / n if n else 0.0,
    }


def _record_usage(record: EvalTaskRecord) -> dict[str, Any] | None:
    response_metadata = record.metadata.get("response_metadata")
    if not isinstance(response_metadata, dict):
        return None
    usage = response_metadata.get("usage")
    return usage if isinstance(usage, dict) else None


def _mean_or_none(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _percentile_or_none(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (percentile / 100.0) * (len(ordered) - 1)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight
