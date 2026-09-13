"""Logarithmic Market Scoring Rule (LMSR) primitives.

Real, dependency-free building blocks for a future prediction-market
environment. Hanson's LMSR maps a vector of outstanding shares ``q`` and a
liquidity parameter ``b`` to outcome prices and a bounded market-maker cost.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import numpy.typing as npt

__all__ = ["lmsr_cost", "lmsr_prices"]


def lmsr_prices(shares: Sequence[float], b: float) -> npt.NDArray[np.float64]:
    """LMSR instantaneous prices (a probability distribution over outcomes)."""
    if b <= 0:
        raise ValueError("liquidity parameter b must be > 0.")
    q = np.asarray(shares, dtype=np.float64)
    scaled = q / b
    scaled = scaled - scaled.max()  # numerical stability
    weights = np.exp(scaled)
    return weights / weights.sum()


def lmsr_cost(shares: Sequence[float], b: float) -> float:
    """LMSR cost function ``C(q) = b * log(sum_i exp(q_i / b))``."""
    if b <= 0:
        raise ValueError("liquidity parameter b must be > 0.")
    q = np.asarray(shares, dtype=np.float64)
    m = float(q.max())
    return float(m + b * np.log(np.exp((q - m) / b).sum()))
