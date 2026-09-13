"""Typed parameters and solution for sealed-bid auction tasks."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = ["AuctionSolution", "AuctionTaskParams"]


class AuctionTaskParams(BaseModel):
    """Public problem statement for a second-price sealed-bid auction task."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    n_bidders: int = Field(ge=1)
    v_max: float = Field(gt=0)
    your_value: float = Field(ge=0)
    auction_type: str = "second_price"


class AuctionSolution(BaseModel):
    """The graded answer: expected surplus from truthful bidding."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    expected_surplus: float
