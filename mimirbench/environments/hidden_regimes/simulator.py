"""Deterministic HMM path simulator for hidden-regime tasks."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

__all__ = ["simulate_path"]


def simulate_path(
    initial: Sequence[float],
    transition: Sequence[Sequence[float]],
    emission: Sequence[Sequence[float]],
    n_steps: int,
    *,
    seed: int = 0,
) -> tuple[list[int], list[int]]:
    """Simulate a hidden regime sequence and the observations it emits.

    Returns ``(regimes, observations)``, each of length ``n_steps``.
    """
    if n_steps < 1:
        raise ValueError("n_steps must be >= 1.")
    rng = np.random.default_rng(seed)
    init = np.asarray(initial, dtype=np.float64)
    trans = np.asarray(transition, dtype=np.float64)
    emit = np.asarray(emission, dtype=np.float64)
    n_regimes = init.shape[0]
    n_signals = emit.shape[1]

    regimes: list[int] = []
    observations: list[int] = []
    regime = int(rng.choice(n_regimes, p=init))
    for _ in range(n_steps):
        regimes.append(regime)
        observations.append(int(rng.choice(n_signals, p=emit[regime])))
        regime = int(rng.choice(n_regimes, p=trans[regime]))
    return regimes, observations
