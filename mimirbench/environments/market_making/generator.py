"""Synthetic one-shot market-making task generator."""

from __future__ import annotations

import numpy as np

from mimirbench.environments.market_making.schemas import MarketMakingTaskParams
from mimirbench.environments.market_making.solver import solve_params
from mimirbench.evals.schemas import EnvironmentFamily, GradingKey, Task, TaskInstance

__all__ = ["generate_params", "generate_task"]


def generate_params(seed: int) -> MarketMakingTaskParams:
    """Generate deterministic toy quote-decision parameters."""
    rng = np.random.default_rng(seed)
    mid_price = round(float(rng.uniform(40.0, 160.0)), 2)
    position_limit = float(rng.choice([8.0, 10.0, 12.0, 15.0, 20.0]))
    inventory = round(float(rng.uniform(-0.95, 0.95) * position_limit), 2)
    if rng.random() < 0.2:
        inventory = round(float(rng.choice([-0.9, 0.9]) * position_limit), 2)

    max_daily_loss = float(rng.choice([100.0, 150.0, 250.0, 400.0]))
    current_daily_pnl = round(float(rng.uniform(-0.95 * max_daily_loss, 0.35 * max_daily_loss)), 2)
    if rng.random() < 0.12:
        current_daily_pnl = round(float(rng.uniform(-1.1 * max_daily_loss, -0.98 * max_daily_loss)), 2)

    volatility = round(float(rng.uniform(0.01, 0.09)), 4)
    spread = round(float(rng.uniform(0.05, 0.75)), 2)
    adverse_selection_risk = round(float(rng.uniform(0.05, 0.95)), 3)
    order_arrival_intensity = round(float(rng.uniform(0.5, 4.0)), 3)
    risk_aversion = round(float(rng.uniform(0.2, 2.5)), 3)
    max_quote_size = float(rng.choice([2.0, 3.0, 5.0]))

    recent_price_path = _recent_path(mid_price, volatility, seed)
    return MarketMakingTaskParams(
        mid_price=mid_price,
        inventory=inventory,
        position_limit=position_limit,
        max_daily_loss=max_daily_loss,
        current_daily_pnl=current_daily_pnl,
        volatility=volatility,
        spread=spread,
        adverse_selection_risk=adverse_selection_risk,
        order_arrival_intensity=order_arrival_intensity,
        risk_aversion=risk_aversion,
        recent_price_path=recent_price_path,
        max_quote_size=max_quote_size,
    )


def generate_task(seed: int) -> TaskInstance:
    """Generate a complete market-making decision task."""
    params = generate_params(seed)
    task = Task(
        task_id=f"market_making-{seed}",
        family=EnvironmentFamily.MARKET_MAKING,
        seed=seed,
        prompt=_format_prompt(params),
        metadata=params.model_dump(mode="json"),
    )
    key = GradingKey(task_id=task.task_id, payload=solve_params(params))
    return TaskInstance(task=task, key=key)


def _recent_path(mid_price: float, volatility: float, seed: int) -> list[float]:
    rng = np.random.default_rng(seed + 17)
    path = [mid_price]
    step_scale = max(mid_price * volatility * 0.2, 0.01)
    for _ in range(4):
        path.append(round(max(0.01, path[-1] + float(rng.normal(0.0, step_scale))), 2))
    return path


def _format_prompt(params: MarketMakingTaskParams) -> str:
    path = ", ".join(f"{price:.2f}" for price in params.recent_price_path)
    actions = ", ".join(params.candidate_actions)
    return (
        "Toy market-making quote decision. This is a synthetic benchmark task, "
        "not live-market data and not investment advice.\n\n"
        f"Mid price: {params.mid_price:.2f}\n"
        f"Current inventory: {params.inventory:.2f}\n"
        f"Position limit: +/-{params.position_limit:.2f}\n"
        f"Maximum daily loss: {params.max_daily_loss:.2f}\n"
        f"Current daily PnL: {params.current_daily_pnl:.2f}\n"
        f"Toy volatility: {params.volatility:.4f}\n"
        f"Displayed base spread: {params.spread:.2f}\n"
        f"Adverse-selection risk: {params.adverse_selection_risk:.3f}\n"
        f"Order-arrival intensity: {params.order_arrival_intensity:.3f}\n"
        f"Risk aversion: {params.risk_aversion:.3f}\n"
        f"Maximum quote size per side: {params.max_quote_size:.2f}\n"
        f"Recent toy mid-price path: {path}\n"
        f"Candidate actions: {actions}\n\n"
        "Return a JSON object with keys: bid_price, ask_price, bid_size, ask_size, "
        "reduce_inventory, abstain, confidence, reasoning_summary. If abstaining, "
        "set bid_size and ask_size to 0."
    )
