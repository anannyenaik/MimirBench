"""Synthetic task generator for second-price sealed-bid auctions."""

from __future__ import annotations

import numpy as np

from mimirbench.environments.auctions.schemas import AuctionTaskParams
from mimirbench.environments.auctions.solver import solve_params
from mimirbench.evals.schemas import EnvironmentFamily, GradingKey, Task, TaskInstance

__all__ = ["generate_params", "generate_task"]

_V_MAX_CHOICES = (1.0, 10.0, 100.0)


def generate_params(seed: int) -> AuctionTaskParams:
    """Generate structured parameters for one auction task."""
    rng = np.random.default_rng(seed)
    n_bidders = int(rng.integers(2, 6))
    v_max = float(_V_MAX_CHOICES[int(rng.integers(0, len(_V_MAX_CHOICES)))])
    # Quantise the bidder's value so the prompt and metadata agree exactly.
    your_value = round(float(rng.uniform(0.1, 1.0)) * v_max, 4)
    return AuctionTaskParams(n_bidders=n_bidders, v_max=v_max, your_value=your_value)


def _format_prompt(params: AuctionTaskParams) -> str:
    return (
        f"You are one of {params.n_bidders} bidders in a sealed-bid, second-price (Vickrey) auction "
        "for a single item. Every bidder's private value is drawn independently and "
        f"uniformly from [0, {params.v_max:g}]. The highest bid wins and pays the second-highest "
        f"bid. Your private value is {params.your_value:g}.\n\n"
        "Assuming you bid truthfully (which is optimal here), what is your expected "
        "surplus (expected value minus expected payment)?\n\n"
        "Return a JSON object with key 'expected_surplus' set to a single number."
    )


def generate_task(seed: int) -> TaskInstance:
    """Generate a complete auction :class:`TaskInstance`."""
    params = generate_params(seed)
    task = Task(
        task_id=f"auctions-{seed}",
        family=EnvironmentFamily.AUCTIONS,
        seed=seed,
        prompt=_format_prompt(params),
        metadata=params.model_dump(),
    )
    key = GradingKey(
        task_id=task.task_id,
        payload={"expected_surplus": solve_params(params)},
    )
    return TaskInstance(task=task, key=key)
