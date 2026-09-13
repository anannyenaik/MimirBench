"""A toy Avellaneda-Stoikov optimal market-making model.

Implements the classic finite-horizon results (Avellaneda & Stoikov, 2008) in
their simplest closed form. This is a *reference policy* for studying inventory
and risk behaviour, not investment advice and not a model of any real market.

Notation:
    s      mid-price
    q      current inventory
    gamma  risk-aversion coefficient (> 0)
    sigma  volatility of the mid-price
    tau    time remaining to the horizon (T - t), in [0, T]
    k      order-arrival / liquidity parameter (> 0)
"""

from __future__ import annotations

import math

from mimirbench.environments.market_making.schemas import Quote

__all__ = ["optimal_quote", "optimal_spread", "reservation_price"]


def reservation_price(mid: float, inventory: float, gamma: float, sigma: float, tau: float) -> float:
    """Inventory-adjusted reservation price ``r = s - q * gamma * sigma^2 * tau``."""
    if gamma <= 0:
        raise ValueError("gamma must be > 0.")
    if sigma < 0:
        raise ValueError("sigma must be >= 0.")
    if tau < 0:
        raise ValueError("tau must be >= 0.")
    return mid - inventory * gamma * sigma**2 * tau


def optimal_spread(gamma: float, sigma: float, tau: float, k: float) -> float:
    """Total optimal bid-ask spread ``gamma*sigma^2*tau + (2/gamma)*ln(1 + gamma/k)``."""
    if gamma <= 0:
        raise ValueError("gamma must be > 0.")
    if k <= 0:
        raise ValueError("k must be > 0.")
    if sigma < 0:
        raise ValueError("sigma must be >= 0.")
    if tau < 0:
        raise ValueError("tau must be >= 0.")
    return gamma * sigma**2 * tau + (2.0 / gamma) * math.log1p(gamma / k)


def optimal_quote(
    mid: float,
    inventory: float,
    *,
    gamma: float,
    sigma: float,
    tau: float,
    k: float,
    size: float = 1.0,
) -> Quote:
    """Symmetric quotes around the reservation price using the optimal spread."""
    reservation = reservation_price(mid, inventory, gamma, sigma, tau)
    half = 0.5 * optimal_spread(gamma, sigma, tau, k)
    return Quote(bid=reservation - half, ask=reservation + half, size=size)
