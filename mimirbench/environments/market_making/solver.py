"""Deterministic reference solver for toy market-making quote decisions."""

from __future__ import annotations

from typing import Any

from mimirbench.environments.market_making.schemas import (
    MarketMakingAction,
    MarketMakingTaskParams,
)
from mimirbench.evals.schemas import Task

__all__ = [
    "expected_spread",
    "reference_solver",
    "solve_params",
]


def expected_spread(params: MarketMakingTaskParams) -> float:
    """Return the toy risk-adjusted spread used by the reference policy.

    This is inspired by inventory-aware market-making formulae, but deliberately
    simpler: it is a deterministic benchmark heuristic, not a trading strategy.
    """
    liquidity_term = 0.15 / max(params.order_arrival_intensity, 0.1)
    multiplier = (
        1.0
        + 8.0 * params.volatility
        + 1.2 * params.adverse_selection_risk
        + 0.25 * params.risk_aversion
        + liquidity_term
    )
    return max(params.spread * multiplier, params.tick_size)


def solve_params(params: MarketMakingTaskParams) -> dict[str, Any]:
    """Choose a safe deterministic quote for a one-shot toy task."""
    loss_used = _loss_used(params)
    inventory_ratio = params.inventory / params.position_limit
    abs_inventory_ratio = abs(inventory_ratio)

    if params.current_daily_pnl <= -params.max_daily_loss:
        return _action(
            abstain=True,
            reduce_inventory=abs(params.inventory) > 0.0,
            confidence=0.95,
            reasoning_summary="Hard daily loss limit is already breached; do not quote.",
        )

    if loss_used >= 0.92 and abs(params.inventory) < 0.1 * params.position_limit:
        return _action(
            abstain=True,
            reduce_inventory=False,
            confidence=0.86,
            reasoning_summary="Daily loss budget is nearly exhausted and inventory is small.",
        )

    total_spread = expected_spread(params)
    reservation_shift = (
        -inventory_ratio
        * params.spread
        * (1.0 + 3.0 * params.volatility + params.risk_aversion)
    )
    reservation = params.mid_price + reservation_shift
    bid_price = _round_to_tick(reservation - 0.5 * total_spread, params.tick_size)
    ask_price = _round_to_tick(reservation + 0.5 * total_spread, params.tick_size)
    if bid_price >= ask_price:
        ask_price = _round_to_tick(bid_price + params.tick_size, params.tick_size)

    base_size = min(
        params.max_quote_size,
        max(1.0, params.order_arrival_intensity * 1.5),
    )
    if loss_used >= 0.82:
        base_size *= 0.5
    if params.adverse_selection_risk >= 0.75:
        base_size *= 0.6

    bid_capacity = max(0.0, params.position_limit - params.inventory)
    ask_capacity = max(0.0, params.position_limit + params.inventory)
    bid_size = min(base_size, bid_capacity)
    ask_size = min(base_size, ask_capacity)
    reduce_inventory = abs_inventory_ratio >= 0.65 or loss_used >= 0.82

    if inventory_ratio >= 0.85:
        bid_size = 0.0
        ask_size = min(max(base_size, 1.0), ask_capacity)
    elif inventory_ratio >= 0.55:
        bid_size *= max(0.0, 1.0 - inventory_ratio) ** 2
        ask_size = min(max(base_size, ask_size), ask_capacity)
    elif inventory_ratio <= -0.85:
        ask_size = 0.0
        bid_size = min(max(base_size, 1.0), bid_capacity)
    elif inventory_ratio <= -0.55:
        ask_size *= max(0.0, 1.0 + inventory_ratio) ** 2
        bid_size = min(max(base_size, bid_size), bid_capacity)

    if loss_used >= 0.82:
        if params.inventory > 0:
            bid_size = 0.0
            ask_size = min(max(ask_size, 1.0), ask_capacity)
        elif params.inventory < 0:
            ask_size = 0.0
            bid_size = min(max(bid_size, 1.0), bid_capacity)

    if bid_size <= 0.0 and ask_size <= 0.0:
        return _action(
            abstain=True,
            reduce_inventory=abs(params.inventory) > 0.0,
            confidence=0.9,
            reasoning_summary="No safe quote size remains under the position limits.",
        )

    return _action(
        bid_price=bid_price,
        ask_price=ask_price,
        bid_size=_round_size(bid_size),
        ask_size=_round_size(ask_size),
        reduce_inventory=reduce_inventory,
        abstain=False,
        confidence=0.78 if reduce_inventory else 0.72,
        reasoning_summary="Quote is widened for toy risk and sized to avoid expanding inventory near limits.",
    )


def reference_solver(task: Task) -> dict[str, Any]:
    """Solve a task from its public metadata."""
    return solve_params(MarketMakingTaskParams(**task.metadata))


def _action(
    *,
    bid_price: float | None = None,
    ask_price: float | None = None,
    bid_size: float = 0.0,
    ask_size: float = 0.0,
    reduce_inventory: bool = False,
    abstain: bool = False,
    confidence: float,
    reasoning_summary: str,
) -> dict[str, Any]:
    return MarketMakingAction(
        bid_price=bid_price,
        ask_price=ask_price,
        bid_size=bid_size,
        ask_size=ask_size,
        reduce_inventory=reduce_inventory,
        abstain=abstain,
        confidence=confidence,
        reasoning_summary=reasoning_summary,
    ).model_dump(mode="json")


def _loss_used(params: MarketMakingTaskParams) -> float:
    if params.max_daily_loss <= 0:
        return 1.0 if params.current_daily_pnl < 0 else 0.0
    return max(0.0, -params.current_daily_pnl / params.max_daily_loss)


def _round_to_tick(value: float, tick_size: float) -> float:
    return round(round(value / tick_size) * tick_size, 10)


def _round_size(value: float) -> float:
    return round(max(0.0, value), 4)
