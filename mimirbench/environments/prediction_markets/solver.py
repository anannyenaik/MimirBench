"""Reference solver for binary prediction-market tasks."""

from __future__ import annotations

from typing import Any

from mimirbench.environments.prediction_markets.schemas import (
    PredictionMarketAction,
    PredictionMarketTaskParams,
)
from mimirbench.evals.schemas import Task

__all__ = [
    "posterior_probability",
    "reference_solver",
    "solve_params",
    "trade_utility",
]


def posterior_probability(params: PredictionMarketTaskParams) -> float:
    """Bayesian posterior for a binary event from a ternary private signal."""
    prior = params.prior_probability
    reliability = params.private_signal_reliability
    if params.private_signal == "neutral":
        return prior
    if params.private_signal == "positive":
        likelihood_true = reliability
        likelihood_false = 1.0 - reliability
    else:
        likelihood_true = 1.0 - reliability
        likelihood_false = reliability

    numerator = prior * likelihood_true
    denominator = numerator + (1.0 - prior) * likelihood_false
    if denominator <= 0.0:
        return prior
    return max(0.0, min(1.0, numerator / denominator))


def solve_params(params: PredictionMarketTaskParams) -> dict[str, Any]:
    """Return a conservative reference trade decision."""
    fair = posterior_probability(params)
    buy_edge = fair - params.current_market_price - params.transaction_cost
    sell_edge = params.current_market_price - fair - params.transaction_cost

    if buy_edge <= 0.0 and sell_edge <= 0.0:
        return _action(
            action="abstain",
            trade_size=0.0,
            target_position=params.current_position,
            fair_probability=fair,
            expected_value=0.0,
            confidence=_confidence(fair, params.current_market_price),
            reasoning_summary="Posterior fair probability does not clear toy cost and impact.",
        )

    if buy_edge >= sell_edge:
        action = "buy"
        edge = buy_edge
        capacity = max(0.0, params.position_limit - params.current_position)
        unit_budget = max(params.current_market_price, 1e-9)
    else:
        action = "sell"
        edge = sell_edge
        capacity = max(0.0, params.position_limit + params.current_position)
        unit_budget = max(1.0 - params.current_market_price, 1e-9)

    budget_capacity = params.budget_limit / unit_budget
    impact_optimal = edge / (2.0 * params.market_impact_parameter)
    trade_size = max(0.0, min(capacity, budget_capacity, impact_optimal))

    if trade_size <= 1e-9:
        return _action(
            action="abstain",
            trade_size=0.0,
            target_position=params.current_position,
            fair_probability=fair,
            expected_value=0.0,
            confidence=0.74,
            reasoning_summary="Edge exists, but budget or position limits leave no safe trade size.",
        )

    expected_value = trade_utility(params, action=action, trade_size=trade_size, fair_probability=fair)
    signed_trade = trade_size if action == "buy" else -trade_size
    return _action(
        action=action,
        trade_size=round(trade_size, 4),
        target_position=round(params.current_position + signed_trade, 4),
        fair_probability=fair,
        expected_value=expected_value,
        confidence=_confidence(fair, params.current_market_price),
        reasoning_summary="Trade direction follows posterior edge after toy cost and impact, sized within limits.",
    )


def trade_utility(
    params: PredictionMarketTaskParams,
    *,
    action: str,
    trade_size: float,
    fair_probability: float,
) -> float:
    """Expected utility for the toy trade, net of linear cost and quadratic impact."""
    if action == "buy":
        edge = fair_probability - params.current_market_price - params.transaction_cost
    elif action == "sell":
        edge = params.current_market_price - fair_probability - params.transaction_cost
    else:
        return 0.0
    return edge * trade_size - params.market_impact_parameter * trade_size**2


def reference_solver(task: Task) -> dict[str, Any]:
    """Solve from public metadata."""
    return solve_params(PredictionMarketTaskParams(**task.metadata))


def _action(
    *,
    action: str,
    trade_size: float,
    target_position: float,
    fair_probability: float,
    expected_value: float,
    confidence: float,
    reasoning_summary: str,
) -> dict[str, Any]:
    return PredictionMarketAction(
        action=action,  # type: ignore[arg-type]
        trade_size=trade_size,
        target_position=target_position,
        fair_probability=round(fair_probability, 6),
        expected_value=round(expected_value, 6),
        confidence=round(confidence, 4),
        reasoning_summary=reasoning_summary,
    ).model_dump(mode="json")


def _confidence(fair_probability: float, market_price: float) -> float:
    edge = abs(fair_probability - market_price)
    return max(0.5, min(0.95, 0.55 + 1.5 * edge))
