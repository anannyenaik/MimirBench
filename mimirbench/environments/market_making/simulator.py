"""A minimal market-making episode simulator.

A quoting *policy* maps ``(mid, inventory, tau)`` to a :class:`Quote`. The
simulator walks a deterministic mid-price path, fills the bid or ask whenever the
next mid crosses the quote, and reports the episode summary. The fill rule is a
deliberate toy: it captures inventory accumulation and mark-to-market PnL without
pretending to model real microstructure.
"""

from __future__ import annotations

from collections.abc import Callable

from mimirbench.environments.market_making.avellaneda_stoikov_toy import optimal_quote
from mimirbench.environments.market_making.schemas import MarketMakingEpisodeResult, Quote
from mimirbench.tools.market_simulator import simulate_mid_price

__all__ = ["QuotePolicy", "avellaneda_stoikov_policy", "constant_spread_policy", "simulate_episode"]

# (mid, inventory, time_to_horizon) -> Quote
QuotePolicy = Callable[[float, float, float], Quote]


def constant_spread_policy(spread: float, size: float = 1.0) -> QuotePolicy:
    """A policy that always quotes a fixed spread centred on the mid."""
    if spread <= 0:
        raise ValueError("spread must be > 0.")
    half = 0.5 * spread

    def policy(mid: float, inventory: float, tau: float) -> Quote:
        return Quote(bid=mid - half, ask=mid + half, size=size)

    return policy


def avellaneda_stoikov_policy(
    *, gamma: float, sigma: float, k: float, size: float = 1.0
) -> QuotePolicy:
    """A policy that quotes the toy Avellaneda-Stoikov optimal bid/ask."""

    def policy(mid: float, inventory: float, tau: float) -> Quote:
        return optimal_quote(mid, inventory, gamma=gamma, sigma=sigma, tau=tau, k=k, size=size)

    return policy


def simulate_episode(
    policy: QuotePolicy,
    *,
    n_steps: int = 100,
    start: float = 100.0,
    drift: float = 0.0,
    volatility: float = 1.0,
    seed: int = 0,
) -> MarketMakingEpisodeResult:
    """Run a single market-making episode and return its summary."""
    if n_steps < 1:
        raise ValueError("n_steps must be >= 1.")
    path = simulate_mid_price(n_steps, start=start, drift=drift, volatility=volatility, seed=seed)

    inventory = 0.0
    cash = 0.0
    min_inv = 0.0
    max_inv = 0.0
    n_quotes = 0

    for t in range(n_steps):
        mid = float(path[t])
        tau = float(n_steps - t)
        quote = policy(mid, inventory, tau)
        n_quotes += 1
        next_mid = float(path[t + 1])
        if next_mid <= quote.bid:
            inventory += quote.size
            cash -= quote.bid * quote.size
        elif next_mid >= quote.ask:
            inventory -= quote.size
            cash += quote.ask * quote.size
        min_inv = min(min_inv, inventory)
        max_inv = max(max_inv, inventory)

    final_mid = float(path[-1])
    realized_pnl = cash + inventory * final_mid
    return MarketMakingEpisodeResult(
        realized_pnl=realized_pnl,
        final_inventory=inventory,
        min_inventory=min_inv,
        max_inventory=max_inv,
        n_quotes=n_quotes,
    )
