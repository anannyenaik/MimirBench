"""Deterministic graders for market-making tasks.

The legacy :func:`grade_episode` scorer remains for simulator tests. The
registry-compatible :func:`grade` scores one-shot quote decisions and is
constraint-gated: hard risk-limit violations receive severe penalties before
quote quality is considered.
"""

from __future__ import annotations

import math
from typing import Any

from pydantic import ValidationError

from mimirbench.environments.market_making.schemas import (
    MarketMakingAction,
    MarketMakingEpisodeResult,
    MarketMakingTaskParams,
)
from mimirbench.environments.market_making.solver import expected_spread, solve_params
from mimirbench.evals.schemas import (
    EnvironmentFamily,
    GraderResult,
    GradingKey,
    ModelResponse,
    Task,
)
from mimirbench.tools.risk_checker import RiskLimits, Violation

__all__ = ["DEFAULT_PNL_SCALE", "grade", "grade_episode"]

# PnL is squashed through tanh(pnl / scale); `scale` sets the PnL at which the
# score reaches ~0.88 above the break-even baseline of 0.5.
DEFAULT_PNL_SCALE = 100.0


def grade_episode(
    episode: MarketMakingEpisodeResult,
    limits: RiskLimits,
    *,
    task_id: str = "market_making",
    pnl_scale: float = DEFAULT_PNL_SCALE,
) -> GraderResult:
    """Grade a single market-making episode against hard risk limits."""
    if pnl_scale <= 0:
        raise ValueError("pnl_scale must be > 0.")

    violations: list[str] = []
    if episode.max_abs_inventory > limits.max_abs_position:
        violations.append(Violation.POSITION_LIMIT.value)
    if episode.realized_pnl < -limits.max_loss:
        violations.append(Violation.LOSS_LIMIT.value)
    if episode.max_inventory > limits.max_inventory or episode.min_inventory < limits.min_inventory:
        violations.append(Violation.INVENTORY_BOUNDS.value)

    if violations:
        score = 0.0
        passed = False
    else:
        score = float(min(1.0, max(0.0, 0.5 + 0.5 * math.tanh(episode.realized_pnl / pnl_scale))))
        passed = episode.realized_pnl >= 0.0

    return GraderResult(
        task_id=task_id,
        family=EnvironmentFamily.MARKET_MAKING,
        score=score,
        passed=passed,
        metrics={
            "realized_pnl": episode.realized_pnl,
            "max_abs_inventory": episode.max_abs_inventory,
            "final_inventory": episode.final_inventory,
        },
        violations=violations,
    )


def grade(task: Task, response: ModelResponse, key: GradingKey) -> GraderResult:
    """Grade a one-shot quote decision against deterministic toy risk rules."""
    if response.parsed_answer is None:
        return GraderResult(
            task_id=task.task_id,
            family=task.family,
            score=0.0,
            passed=False,
            violations=["no_valid_answer"],
        )
    if "realized_pnl" in response.parsed_answer:
        return _grade_legacy_episode(task, response, key)

    params = MarketMakingTaskParams(**task.metadata)
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

    reference = MarketMakingAction(**key.payload) if key.payload else MarketMakingAction(**solve_params(params))
    violations = _risk_violations(params, action)
    quote_validity, quote_violations = _quote_validity(action)
    violations.extend(quote_violations)

    spread_reasonableness = _spread_reasonableness(params, action, reference)
    inventory_risk_score = _inventory_risk_score(params, action)
    adverse_selection_penalty = _adverse_selection_penalty(params, action, reference)
    abstention_quality = _abstention_quality(params, action, reference)
    risk_limit_violation = 1.0 if _has_hard_risk_violation(violations) else 0.0

    if risk_limit_violation:
        score = 0.0 if "loss_limit" in violations or "position_limit" in violations else 0.1
    elif action.abstain:
        score = 0.15 + 0.85 * abstention_quality
    else:
        score = (
            0.25 * quote_validity
            + 0.2 * spread_reasonableness
            + 0.25 * inventory_risk_score
            + 0.15 * (1.0 - adverse_selection_penalty)
            + 0.15 * abstention_quality
        )
    score = _clip01(score)

    return GraderResult(
        task_id=task.task_id,
        family=task.family,
        score=score,
        passed=score >= 0.75 and not _has_hard_risk_violation(violations),
        metrics={
            "quote_validity": quote_validity,
            "spread_reasonableness": spread_reasonableness,
            "inventory_risk_score": inventory_risk_score,
            "risk_limit_violation": risk_limit_violation,
            "adverse_selection_penalty": adverse_selection_penalty,
            "abstention_quality": abstention_quality,
        },
        violations=sorted(set(violations)),
        details={
            "reference_action": reference.model_dump(mode="json"),
            "submitted_action": action.model_dump(mode="json"),
            "notes": _notes(params, action, reference, violations),
        },
    )


def _grade_legacy_episode(task: Task, response: ModelResponse, key: GradingKey) -> GraderResult:
    if response.parsed_answer is None:
        return GraderResult(
            task_id=task.task_id,
            family=task.family,
            score=0.0,
            passed=False,
            violations=["no_valid_answer"],
            details={"reason": "missing parsed answer"},
        )
    try:
        episode = MarketMakingEpisodeResult(**response.parsed_answer)
        limits = RiskLimits(**key.payload["limits"])
    except (TypeError, ValueError, KeyError) as exc:
        return GraderResult(
            task_id=task.task_id,
            family=task.family,
            score=0.0,
            passed=False,
            violations=["no_valid_answer"],
            details={"reason": str(exc)},
        )
    return grade_episode(episode, limits, task_id=task.task_id)


def _extract_action(payload: dict[str, Any]) -> tuple[MarketMakingAction | None, str | None]:
    try:
        return MarketMakingAction(**payload), None
    except ValidationError as exc:
        return None, str(exc)


def _quote_validity(action: MarketMakingAction) -> tuple[float, list[str]]:
    if action.abstain:
        return 1.0, []
    violations: list[str] = []
    if action.bid_price is None or action.ask_price is None:
        return 0.0, ["missing_quote"]
    if action.bid_price <= 0.0 or action.ask_price <= 0.0:
        violations.append("irrational_quote")
    if action.bid_price >= action.ask_price:
        violations.append("crossed_quote")
    if action.bid_size == 0.0 and action.ask_size == 0.0:
        violations.append("empty_quote")
    return (0.0 if violations else 1.0), violations


def _spread_reasonableness(
    params: MarketMakingTaskParams,
    action: MarketMakingAction,
    reference: MarketMakingAction,
) -> float:
    if action.abstain:
        return 1.0 if reference.abstain else 0.25
    if action.bid_price is None or action.ask_price is None or action.ask_price <= action.bid_price:
        return 0.0
    actual = action.ask_price - action.bid_price
    target = expected_spread(params)
    if target <= 0.0:
        return 1.0
    ratio_error = abs(math.log(max(actual, 1e-9) / target))
    return _clip01(1.0 - ratio_error / math.log(3.0))


def _inventory_risk_score(params: MarketMakingTaskParams, action: MarketMakingAction) -> float:
    if action.abstain:
        return 1.0 if _near_hard_limit(params) else 0.45
    buy_position = params.inventory + action.bid_size
    sell_position = params.inventory - action.ask_size
    if buy_position > params.position_limit or sell_position < -params.position_limit:
        return 0.0

    ratio = params.inventory / params.position_limit
    score = 1.0
    if ratio >= 0.65 and action.bid_size > action.ask_size:
        score -= 0.5
    if ratio <= -0.65 and action.ask_size > action.bid_size:
        score -= 0.5
    if ratio >= 0.85 and action.bid_size > 0.0:
        score -= 0.5
    if ratio <= -0.85 and action.ask_size > 0.0:
        score -= 0.5
    if abs(ratio) >= 0.65 and not action.reduce_inventory:
        score -= 0.2
    return _clip01(score)


def _risk_violations(params: MarketMakingTaskParams, action: MarketMakingAction) -> list[str]:
    violations: list[str] = []
    if params.current_daily_pnl <= -params.max_daily_loss and not action.abstain:
        violations.append("loss_limit")
    if params.inventory + action.bid_size > params.position_limit:
        violations.append("position_limit")
    if params.inventory - action.ask_size < -params.position_limit:
        violations.append("position_limit")
    return violations


def _adverse_selection_penalty(
    params: MarketMakingTaskParams,
    action: MarketMakingAction,
    reference: MarketMakingAction,
) -> float:
    if action.abstain:
        return 0.0
    if action.bid_price is None or action.ask_price is None or action.ask_price <= action.bid_price:
        return 1.0
    actual_spread = action.ask_price - action.bid_price
    ref_spread = (
        (reference.ask_price - reference.bid_price)
        if reference.ask_price is not None and reference.bid_price is not None
        else expected_spread(params)
    )
    tightness = max(0.0, (ref_spread - actual_spread) / max(ref_spread, 1e-9))
    reference_size = reference.bid_size + reference.ask_size
    submitted_size = action.bid_size + action.ask_size
    excess_size = max(0.0, (submitted_size - reference_size) / (2.0 * params.max_quote_size))
    return _clip01(params.adverse_selection_risk * (0.7 * tightness + 0.3 * excess_size))


def _abstention_quality(
    params: MarketMakingTaskParams,
    action: MarketMakingAction,
    reference: MarketMakingAction,
) -> float:
    if action.abstain:
        if reference.abstain:
            return 1.0
        return 0.75 if _near_hard_limit(params) else 0.15
    if reference.abstain:
        return 0.0
    return 1.0


def _near_hard_limit(params: MarketMakingTaskParams) -> bool:
    return abs(params.inventory) >= 0.85 * params.position_limit or _loss_used(params) >= 0.85


def _loss_used(params: MarketMakingTaskParams) -> float:
    if params.max_daily_loss <= 0.0:
        return 1.0 if params.current_daily_pnl < 0.0 else 0.0
    return max(0.0, -params.current_daily_pnl / params.max_daily_loss)


def _has_hard_risk_violation(violations: list[str]) -> bool:
    return any(name in {"loss_limit", "position_limit"} for name in violations)


def _notes(
    params: MarketMakingTaskParams,
    action: MarketMakingAction,
    reference: MarketMakingAction,
    violations: list[str],
) -> list[str]:
    notes: list[str] = []
    if violations:
        notes.append("Hard quote or risk constraint violation detected.")
    if action.abstain and not reference.abstain:
        notes.append("Abstention was conservative relative to the reference quote.")
    if params.adverse_selection_risk >= 0.75:
        notes.append("High toy adverse-selection risk favours wider or smaller quotes.")
    return notes


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, value))
