"""Lightweight, deterministic price-path simulator.

A single, dependency-free primitive used by the market-making and
hidden-regime environments and exposed as the ``market_simulator`` agent tool.
Given a seed, the path is fully reproducible.

This is deliberately a *toy*: an arithmetic Brownian motion (Bachelier-style)
mid-price with optional regime-dependent drift/volatility. It is sufficient for
studying inventory and risk behaviour and is not a model of any real market.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import numpy.typing as npt

__all__ = ["simulate_mid_price", "simulate_regime_path"]


def simulate_mid_price(
    n_steps: int,
    *,
    start: float = 100.0,
    drift: float = 0.0,
    volatility: float = 1.0,
    seed: int = 0,
) -> npt.NDArray[np.float64]:
    """Simulate an arithmetic Brownian-motion mid-price path.

    Args:
        n_steps: Number of price steps to generate (path length is ``n_steps + 1``
            including the starting price).
        start: Initial mid-price.
        drift: Per-step additive drift.
        volatility: Per-step standard deviation of the Gaussian increments.
        seed: RNG seed; the path is a deterministic function of all arguments.

    Returns:
        A float array of length ``n_steps + 1``.
    """
    if n_steps < 0:
        raise ValueError(f"n_steps must be >= 0, got {n_steps}.")
    if volatility < 0:
        raise ValueError(f"volatility must be >= 0, got {volatility}.")
    rng = np.random.default_rng(seed)
    increments = drift + volatility * rng.standard_normal(n_steps)
    path = np.empty(n_steps + 1, dtype=np.float64)
    path[0] = start
    path[1:] = start + np.cumsum(increments)
    return path


def simulate_regime_path(
    n_steps: int,
    *,
    start: float = 100.0,
    drifts: Sequence[float] = (-0.1, 0.1),
    volatilities: Sequence[float] = (0.5, 1.5),
    regimes: Sequence[int] | None = None,
    seed: int = 0,
) -> npt.NDArray[np.float64]:
    """Simulate a mid-price whose drift/volatility switch with a regime sequence.

    Args:
        n_steps: Number of price steps to generate.
        start: Initial mid-price.
        drifts: Per-regime additive drift.
        volatilities: Per-regime increment standard deviation.
        regimes: Length-``n_steps`` regime index per step. If ``None``, regime 0
            is used throughout.
        seed: RNG seed.

    Returns:
        A float array of length ``n_steps + 1``.
    """
    if n_steps < 0:
        raise ValueError(f"n_steps must be >= 0, got {n_steps}.")
    if len(drifts) != len(volatilities):
        raise ValueError("drifts and volatilities must have the same length.")
    if regimes is None:
        regimes = [0] * n_steps
    if len(regimes) != n_steps:
        raise ValueError(f"regimes must have length n_steps={n_steps}, got {len(regimes)}.")

    rng = np.random.default_rng(seed)
    drift_arr = np.asarray(drifts, dtype=np.float64)
    vol_arr = np.asarray(volatilities, dtype=np.float64)
    regime_arr = np.asarray(regimes, dtype=np.int64)
    if regime_arr.size and (regime_arr.min() < 0 or regime_arr.max() >= drift_arr.size):
        raise ValueError("regime indices out of range for the given drifts/volatilities.")

    increments = drift_arr[regime_arr] + vol_arr[regime_arr] * rng.standard_normal(n_steps)
    path = np.empty(n_steps + 1, dtype=np.float64)
    path[0] = start
    path[1:] = start + np.cumsum(increments)
    return path
