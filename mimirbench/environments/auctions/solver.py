"""Reference solver for sealed-bid auction tasks."""

from __future__ import annotations

from typing import Any

from mimirbench.environments.auctions.schemas import AuctionTaskParams
from mimirbench.evals.schemas import Task
from mimirbench.tools.auction_solver import expected_bidder_surplus

__all__ = ["reference_solver", "solve_params"]


def solve_params(params: AuctionTaskParams) -> float:
    """Expected surplus from truthful bidding for the given parameters."""
    if params.auction_type != "second_price":
        raise ValueError(f"unsupported auction_type {params.auction_type!r}.")
    return expected_bidder_surplus(params.your_value, params.n_bidders, params.v_max)


def reference_solver(task: Task) -> dict[str, Any]:
    """Solve from public metadata; returns ``{"expected_surplus": ...}``."""
    params = AuctionTaskParams(**task.metadata)
    return {"expected_surplus": solve_params(params)}
