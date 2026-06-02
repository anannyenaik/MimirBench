"""Closed-form helpers for a toy sealed-bid auction.

We model the textbook independent-private-values (IPV) setting: ``n`` bidders
whose valuations are i.i.d. ``Uniform[0, v_max]``. Under a second-price
(Vickrey) sealed-bid auction, truthful bidding is a (weakly) dominant strategy,
which makes the expected outcomes analytically tractable and therefore ideal as
deterministic ground truth.

Derived quantities (all for ``Uniform[0, v_max]`` values):

* expected winning (highest) value:        ``v_max * n / (n + 1)``
* expected second-highest value (revenue):  ``v_max * (n - 1) / (n + 1)``
* expected surplus of a bidder with value ``v`` bidding truthfully:
  ``v**n / (n * v_max**(n - 1))``  (see :func:`expected_bidder_surplus`).

These formulas are unit-tested against both hand-computed values and a seeded
Monte-Carlo simulation.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = [
    "AuctionSummary",
    "expected_bidder_surplus",
    "expected_revenue_second_price",
    "expected_welfare",
    "summarize_second_price_auction",
]


class AuctionSummary(BaseModel):
    """Expected outcomes of a symmetric second-price IPV auction."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    n_bidders: int
    v_max: float
    expected_welfare: float
    expected_revenue: float
    expected_winner_surplus: float


def _validate(n_bidders: int, v_max: float) -> None:
    if n_bidders < 1:
        raise ValueError(f"n_bidders must be >= 1, got {n_bidders}.")
    if v_max <= 0:
        raise ValueError(f"v_max must be > 0, got {v_max}.")


def expected_welfare(n_bidders: int, v_max: float) -> float:
    """Expected value realized by the auction (the highest of ``n`` values)."""
    _validate(n_bidders, v_max)
    return v_max * n_bidders / (n_bidders + 1)


def expected_revenue_second_price(n_bidders: int, v_max: float) -> float:
    """Expected seller revenue: the expected second-highest of ``n`` values."""
    _validate(n_bidders, v_max)
    if n_bidders == 1:
        return 0.0  # single bidder pays the (zero) reserve.
    return v_max * (n_bidders - 1) / (n_bidders + 1)


def expected_bidder_surplus(value: float, n_bidders: int, v_max: float) -> float:
    """Expected surplus of one bidder with private ``value`` bidding truthfully.

    With ``n - 1`` competitors drawn i.i.d. ``Uniform[0, v_max]``, the bidder
    wins iff its value is the maximum and then pays the second price. Integrating
    ``(value - max_competitor)`` over the winning region gives the closed form
    ``value**n / (n * v_max**(n - 1))``.
    """
    _validate(n_bidders, v_max)
    if value < 0:
        raise ValueError(f"value must be >= 0, got {value}.")
    capped = min(value, v_max)
    return capped**n_bidders / (n_bidders * v_max ** (n_bidders - 1))


def summarize_second_price_auction(n_bidders: int, v_max: float = 1.0) -> AuctionSummary:
    """Bundle the standard expected outcomes for a symmetric IPV auction."""
    _validate(n_bidders, v_max)
    welfare = expected_welfare(n_bidders, v_max)
    revenue = expected_revenue_second_price(n_bidders, v_max)
    return AuctionSummary(
        n_bidders=n_bidders,
        v_max=v_max,
        expected_welfare=welfare,
        expected_revenue=revenue,
        expected_winner_surplus=welfare - revenue,
    )
