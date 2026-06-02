"""Calibration metrics for probabilistic forecasts.

Real, dependency-free implementations of the standard reliability diagnostics:
expected calibration error (ECE), the binary Brier score, and a reliability
curve. Used by environments that elicit probabilities (Bayesian games, hidden
regimes, prediction markets) to ask not just "is the answer right?" but "are the
stated probabilities trustworthy?".
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import numpy.typing as npt

from mimirbench.evals.schemas import EvalTaskRecord

__all__ = [
    "brier_score",
    "calibration_summary_from_records",
    "expected_calibration_error",
    "record_confidence_outcomes",
    "reliability_curve",
]


def _validate(predictions: Sequence[float], outcomes: Sequence[int]) -> tuple[np.ndarray, np.ndarray]:
    p = np.asarray(predictions, dtype=np.float64)
    y = np.asarray(outcomes, dtype=np.float64)
    if p.shape != y.shape:
        raise ValueError(f"predictions {p.shape} and outcomes {y.shape} must match.")
    if p.ndim != 1:
        raise ValueError("predictions and outcomes must be 1-D.")
    if p.size == 0:
        raise ValueError("predictions must be non-empty.")
    if np.any((p < 0) | (p > 1)):
        raise ValueError("predictions must lie in [0, 1].")
    if not np.all((y == 0) | (y == 1)):
        raise ValueError("outcomes must be binary (0 or 1).")
    return p, y


def brier_score(predictions: Sequence[float], outcomes: Sequence[int]) -> float:
    """Mean squared error between predicted probabilities and binary outcomes."""
    p, y = _validate(predictions, outcomes)
    return float(np.mean((p - y) ** 2))


def expected_calibration_error(
    predictions: Sequence[float],
    outcomes: Sequence[int],
    *,
    n_bins: int = 10,
) -> float:
    """Expected calibration error with equal-width probability bins.

    For each non-empty bin, the absolute gap between the empirical outcome rate
    and the mean predicted probability is weighted by the bin's share of points.
    """
    if n_bins < 1:
        raise ValueError("n_bins must be >= 1.")
    p, y = _validate(predictions, outcomes)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    # np.digitize with the open right edge; clip so p == 1.0 lands in the last bin.
    bin_ids = np.clip(np.digitize(p, edges[1:-1], right=False), 0, n_bins - 1)
    ece = 0.0
    n = p.size
    for b in range(n_bins):
        mask = bin_ids == b
        count = int(mask.sum())
        if count == 0:
            continue
        ece += (count / n) * abs(float(y[mask].mean()) - float(p[mask].mean()))
    return ece


def reliability_curve(
    predictions: Sequence[float],
    outcomes: Sequence[int],
    *,
    n_bins: int = 10,
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    """Return ``(mean_predicted, empirical_rate)`` per non-empty bin."""
    if n_bins < 1:
        raise ValueError("n_bins must be >= 1.")
    p, y = _validate(predictions, outcomes)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    bin_ids = np.clip(np.digitize(p, edges[1:-1], right=False), 0, n_bins - 1)
    mean_pred: list[float] = []
    emp_rate: list[float] = []
    for b in range(n_bins):
        mask = bin_ids == b
        if not mask.any():
            continue
        mean_pred.append(float(p[mask].mean()))
        emp_rate.append(float(y[mask].mean()))
    return np.asarray(mean_pred), np.asarray(emp_rate)


def record_confidence_outcomes(records: Sequence[EvalTaskRecord]) -> tuple[list[float], list[int]]:
    """Extract ``(confidence, passed)`` pairs from run records.

    This is a pragmatic benchmark-level calibration proxy. It uses an explicit
    ``confidence`` field when an environment/agent emits one and treats grader
    pass/fail as the binary outcome. Records without a valid confidence are
    ignored rather than imputed.
    """
    confidences: list[float] = []
    outcomes: list[int] = []
    for record in records:
        confidence = _confidence(record.parsed_response)
        if confidence is None:
            continue
        confidences.append(confidence)
        outcomes.append(1 if record.grader_result.passed else 0)
    return confidences, outcomes


def calibration_summary_from_records(records: Sequence[EvalTaskRecord]) -> dict[str, Any]:
    """Return ECE/Brier diagnostics for records with explicit confidence."""
    confidences, outcomes = record_confidence_outcomes(records)
    if not confidences:
        return {
            "n_confidence_records": 0,
            "expected_calibration_error": None,
            "brier_score": None,
        }
    return {
        "n_confidence_records": len(confidences),
        "expected_calibration_error": expected_calibration_error(confidences, outcomes),
        "brier_score": brier_score(confidences, outcomes),
    }


def _confidence(parsed: dict[str, Any] | None) -> float | None:
    if parsed is None:
        return None
    value = parsed.get("confidence")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    confidence = float(value)
    if confidence < 0.0 or confidence > 1.0:
        return None
    return confidence
