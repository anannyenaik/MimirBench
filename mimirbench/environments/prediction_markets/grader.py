"""Grader and scoring-rule primitives for prediction-market tasks.

The proper-scoring-rule helpers (:func:`brier_score`, :func:`log_score`) are
kept for calibration analysis. The registry-compatible :func:`grade` scores
binary trade decisions from generated tasks.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
from pydantic import ValidationError

from mimirbench.environments.prediction_markets.schemas import (
    PredictionMarketAction,
    PredictionMarketTaskParams,
)
from mimirbench.environments.prediction_markets.solver import solve_params, trade_utility
from mimirbench.evals.schemas import GraderResult, GradingKey, ModelResponse, Task

__all__ = ["brier_score", "grade", "log_score"]


def brier_score(probabilities: Sequence[float], outcome_index: int) -> float:
    """Multiclass Brier score (lower is better) for a one-hot outcome."""
    p = np.asarray(probabilities, dtype=np.float64)
    if not 0 <= outcome_index < p.size:
        raise ValueError("outcome_index out of range.")
    target = np.zeros_like(p)
    target[outcome_index] = 1.0
    return float(np.sum((p - target) ** 2))


def log_score(probabilities: Sequence[float], outcome_index: int, *, eps: float = 1e-12) -> float:
    """Logarithmic score ``log p(outcome)`` (higher is better)."""
    p = np.asarray(probabilities, dtype=np.float64)
    if not 0 <= outcome_index < p.size:
        raise ValueError("outcome_index out of range.")
    return float(np.log(max(p[outcome_index], eps)))


def grade(task: Task, response: ModelResponse, key: GradingKey) -> GraderResult:
    """Score a binary prediction-market decision."""
    if response.parsed_answer is None:
        return GraderResult(
            task_id=task.task_id,
            family=task.family,
            score=0.0,
            passed=False,
            violations=["no_valid_answer"],
            details={"reason": "missing parsed answer"},
        )

    action, error = _extract_action(response.parsed_answer)
    if action is None:
        return GraderResult(
            task_id=task.task_id,
            family=task.family,
            score=0.0,
            passed=False,
            violations=["no_valid_answer"],
            details={"reason": error},
        )

    params = PredictionMarketTaskParams(**task.metadata)
    reference = (
        PredictionMarketAction(**key.payload)
        if key.payload
        else PredictionMarketAction(**solve_params(params))
    )
    violations = _risk_violations(params, action)

    fair_probability_error = abs(action.fair_probability - reference.fair_probability)
    expected_value_error = abs(action.expected_value - reference.expected_value)
    action_optimality = _action_optimality(action, reference)
    response_utility = trade_utility(
        params,
        action=action.action,
        trade_size=action.trade_size,
        fair_probability=reference.fair_probability,
    )
    reference_utility = trade_utility(
        params,
        action=reference.action,
        trade_size=reference.trade_size,
        fair_probability=reference.fair_probability,
    )
    regret = max(0.0, reference_utility - response_utility)
    calibration_proxy = _calibration_proxy(action, reference)
    risk_limit_violation = 1.0 if violations else 0.0
    abstention_quality = _abstention_quality(action, reference)

    probability_score = max(0.0, 1.0 - fair_probability_error / 0.25)
    ev_scale = max(abs(reference.expected_value), 0.05)
    ev_score = max(0.0, 1.0 - expected_value_error / ev_scale)
    regret_score = max(0.0, 1.0 - regret / max(abs(reference_utility), 0.05))

    if violations:
        score = 0.0
    else:
        score = (
            0.25 * probability_score
            + 0.15 * ev_score
            + 0.25 * action_optimality
            + 0.15 * regret_score
            + 0.1 * calibration_proxy
            + 0.1 * abstention_quality
        )

    return GraderResult(
        task_id=task.task_id,
        family=task.family,
        score=float(max(0.0, min(1.0, score))),
        passed=score >= 0.8 and not violations,
        metrics={
            "fair_probability_error": fair_probability_error,
            "expected_value_error": expected_value_error,
            "action_optimality": action_optimality,
            "regret": regret,
            "calibration_proxy": calibration_proxy,
            "risk_limit_violation": risk_limit_violation,
            "abstention_quality": abstention_quality,
        },
        violations=violations,
        details={
            "reference_action": reference.model_dump(mode="json"),
            "submitted_action": action.model_dump(mode="json"),
            "notes": _notes(action, reference, violations),
        },
    )


def _extract_action(payload: dict[str, Any]) -> tuple[PredictionMarketAction | None, str | None]:
    try:
        return PredictionMarketAction(**payload), None
    except ValidationError as exc:
        return None, str(exc)


def _risk_violations(
    params: PredictionMarketTaskParams,
    action: PredictionMarketAction,
) -> list[str]:
    violations: list[str] = []
    if action.action == "abstain":
        return violations
    signed_trade = action.trade_size if action.action == "buy" else -action.trade_size
    resulting_position = params.current_position + signed_trade
    if abs(resulting_position) > params.position_limit + 1e-9:
        violations.append("position_limit")
    unit_budget = params.current_market_price if action.action == "buy" else 1.0 - params.current_market_price
    if action.trade_size * max(unit_budget, 0.0) > params.budget_limit + 1e-9:
        violations.append("budget_limit")
    if action.trade_size <= 0.0:
        violations.append("empty_trade")
    return sorted(set(violations))


def _action_optimality(
    action: PredictionMarketAction,
    reference: PredictionMarketAction,
) -> float:
    if action.action == reference.action:
        if reference.trade_size <= 1e-9:
            return 1.0
        size_error = abs(action.trade_size - reference.trade_size) / max(reference.trade_size, 1e-9)
        return max(0.0, 1.0 - 0.5 * size_error)
    if action.action == "abstain" and abs(reference.expected_value) < 0.02:
        return 0.5
    return 0.0


def _calibration_proxy(
    action: PredictionMarketAction,
    reference: PredictionMarketAction,
) -> float:
    if action.confidence is None:
        return 0.5
    target_confidence = (
        reference.confidence
        if reference.confidence is not None
        else max(0.5, min(0.95, 0.55 + 1.5 * abs(reference.fair_probability - 0.5)))
    )
    return max(0.0, 1.0 - abs(action.confidence - target_confidence) / 0.5)


def _abstention_quality(
    action: PredictionMarketAction,
    reference: PredictionMarketAction,
) -> float:
    if action.action == "abstain":
        return 1.0 if reference.action == "abstain" else 0.1
    return 1.0 if reference.action != "abstain" else 0.25


def _notes(
    action: PredictionMarketAction,
    reference: PredictionMarketAction,
    violations: list[str],
) -> list[str]:
    notes: list[str] = []
    if violations:
        notes.append("Toy position or budget limit was violated.")
    if action.action != reference.action:
        notes.append("Trade direction differs from the posterior-edge reference.")
    if action.action == "abstain" and reference.action != "abstain":
        notes.append("Abstained despite a reference edge that cleared toy costs.")
    return notes
