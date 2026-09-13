"""Synthetic binary prediction-market task generator."""

from __future__ import annotations

import numpy as np

from mimirbench.environments.prediction_markets.schemas import PredictionMarketTaskParams
from mimirbench.environments.prediction_markets.solver import posterior_probability, solve_params
from mimirbench.evals.schemas import EnvironmentFamily, GradingKey, Task, TaskInstance

__all__ = ["generate_params", "generate_task"]

_EVENTS = (
    "A simulated research project meets its replication target by the deadline",
    "A toy supply index finishes above its threshold at settlement",
    "A synthetic policy proposal passes committee review",
    "A benchmark model clears a fixed validation threshold",
    "A simulated launch checklist completes without a blocking issue",
)


def generate_params(seed: int) -> PredictionMarketTaskParams:
    """Generate deterministic binary prediction-market parameters."""
    rng = np.random.default_rng(seed)
    prior = round(float(rng.uniform(0.2, 0.8)), 3)
    reliability = round(float(rng.uniform(0.56, 0.9)), 3)
    signal = str(rng.choice(["positive", "negative", "neutral"], p=[0.42, 0.42, 0.16]))
    impact = round(float(rng.uniform(0.01, 0.08)), 4)
    transaction_cost = round(float(rng.uniform(0.003, 0.02)), 4)

    draft = PredictionMarketTaskParams(
        event_description=_EVENTS[int(rng.integers(0, len(_EVENTS)))],
        current_market_price=prior,
        private_signal=signal,  # type: ignore[arg-type]
        private_signal_reliability=reliability,
        prior_probability=prior,
        market_impact_parameter=impact,
        transaction_cost=transaction_cost,
        public_evidence=_public_evidence(prior),
        position_limit=float(rng.choice([5.0, 10.0, 15.0, 20.0])),
        budget_limit=float(rng.choice([5.0, 10.0, 20.0, 30.0])),
        current_position=round(float(rng.uniform(-2.0, 2.0)), 2),
    )
    fair = posterior_probability(draft)

    mode = seed % 5
    if mode == 0:
        price = fair
    elif mode in {1, 3}:
        price = fair - float(rng.uniform(0.08, 0.22))
    else:
        price = fair + float(rng.uniform(0.08, 0.22))
    price = round(float(np.clip(price, 0.03, 0.97)), 3)

    return draft.model_copy(update={"current_market_price": price})


def generate_task(seed: int) -> TaskInstance:
    """Generate a complete prediction-market task."""
    params = generate_params(seed)
    task = Task(
        task_id=f"prediction_markets-{seed}",
        family=EnvironmentFamily.PREDICTION_MARKETS,
        seed=seed,
        prompt=_format_prompt(params),
        metadata=params.model_dump(mode="json"),
    )
    key = GradingKey(task_id=task.task_id, payload=solve_params(params))
    return TaskInstance(task=task, key=key)


def _public_evidence(prior: float) -> list[str]:
    if prior >= 0.6:
        return ["Public base-rate evidence is moderately favourable."]
    if prior <= 0.4:
        return ["Public base-rate evidence is moderately unfavourable."]
    return ["Public base-rate evidence is mixed."]


def _format_prompt(params: PredictionMarketTaskParams) -> str:
    evidence = " ".join(params.public_evidence)
    return (
        "Binary prediction-market decision task using synthetic data only.\n\n"
        f"Event: {params.event_description}.\n"
        f"Current YES market price: {params.current_market_price:.3f}\n"
        f"Prior probability before the private signal: {params.prior_probability:.3f}\n"
        f"Private signal: {params.private_signal}\n"
        f"Private signal reliability: {params.private_signal_reliability:.3f}\n"
        f"Market impact parameter: {params.market_impact_parameter:.4f}\n"
        f"Transaction cost per share: {params.transaction_cost:.4f}\n"
        f"Public evidence: {evidence}\n"
        f"Current position: {params.current_position:.2f}\n"
        f"Position limit: +/-{params.position_limit:.2f}\n"
        f"Budget/loss limit for this toy decision: {params.budget_limit:.2f}\n\n"
        "Return a JSON object with keys: action (buy, sell, abstain), target_position, "
        "trade_size, fair_probability, expected_value, confidence, reasoning_summary."
    )
