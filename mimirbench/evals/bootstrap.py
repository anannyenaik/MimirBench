"""Bootstrap confidence intervals for evaluation metrics.

A small, seeded nonparametric bootstrap used to attach uncertainty to aggregate
numbers (mean score, pass rate, ...). Determinism matters: the same values and
seed always yield the same interval.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from pydantic import BaseModel, ConfigDict

__all__ = ["BootstrapResult", "bootstrap_ci"]


class BootstrapResult(BaseModel):
    """Point estimate and a percentile bootstrap confidence interval."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    mean: float
    low: float
    high: float
    confidence: float
    n_resamples: int


def bootstrap_ci(
    values: Sequence[float],
    *,
    n_resamples: int = 2000,
    confidence: float = 0.95,
    seed: int = 0,
) -> BootstrapResult:
    """Percentile bootstrap CI for the mean of ``values``.

    Args:
        values: Per-task statistic (e.g. scores). Must be non-empty.
        n_resamples: Number of bootstrap resamples.
        confidence: Two-sided confidence level in ``(0, 1)``.
        seed: RNG seed for reproducibility.

    Returns:
        A :class:`BootstrapResult` with the sample mean and the CI bounds.
    """
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        raise ValueError("values must be non-empty.")
    if not 0.0 < confidence < 1.0:
        raise ValueError(f"confidence must be in (0, 1), got {confidence}.")

    rng = np.random.default_rng(seed)
    idx = rng.integers(0, arr.size, size=(n_resamples, arr.size))
    means = arr[idx].mean(axis=1)
    alpha = 1.0 - confidence
    low, high = np.quantile(means, [alpha / 2, 1.0 - alpha / 2])
    return BootstrapResult(
        mean=float(arr.mean()),
        low=float(low),
        high=float(high),
        confidence=confidence,
        n_resamples=n_resamples,
    )
