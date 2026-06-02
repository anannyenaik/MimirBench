"""Expected-value and decision helpers shared across environments.

Small, deterministic primitives for reasoning about lotteries and choosing among
actions under a known (or estimated) outcome distribution. Exposed as the
``ev_calculator`` agent tool and reused by graders that score expected-value
accuracy.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np

__all__ = [
    "best_action",
    "expected_value",
    "variance",
]


def _as_pair(payoffs: Sequence[float], probabilities: Sequence[float]) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(payoffs, dtype=np.float64)
    p = np.asarray(probabilities, dtype=np.float64)
    if x.shape != p.shape:
        raise ValueError(f"payoffs {x.shape} and probabilities {p.shape} must match.")
    if x.ndim != 1:
        raise ValueError("payoffs and probabilities must be 1-D.")
    if np.any(p < 0):
        raise ValueError("probabilities must be non-negative.")
    total = float(p.sum())
    if not math.isclose(total, 1.0, abs_tol=1e-9):
        raise ValueError(f"probabilities must sum to 1 (got {total:.6g}).")
    return x, p


def expected_value(payoffs: Sequence[float], probabilities: Sequence[float]) -> float:
    """Expected value of a discrete lottery ``sum_i p_i * x_i``."""
    x, p = _as_pair(payoffs, probabilities)
    return float(np.dot(x, p))


def variance(payoffs: Sequence[float], probabilities: Sequence[float]) -> float:
    """Variance of a discrete lottery under ``probabilities``."""
    x, p = _as_pair(payoffs, probabilities)
    mean = float(np.dot(x, p))
    return float(np.dot(p, (x - mean) ** 2))


def best_action(action_payoffs: dict[str, tuple[Sequence[float], Sequence[float]]]) -> tuple[str, float]:
    """Pick the expected-value-maximising action.

    Args:
        action_payoffs: Maps an action name to ``(payoffs, probabilities)``.

    Returns:
        ``(action_name, expected_value)`` for the best action. Ties are broken by
        the action name to keep the result deterministic.
    """
    if not action_payoffs:
        raise ValueError("action_payoffs must be non-empty.")
    scored = {
        name: expected_value(payoffs, probs)
        for name, (payoffs, probs) in action_payoffs.items()
    }
    best_ev = max(scored.values())
    winners = sorted(name for name, ev in scored.items() if math.isclose(ev, best_ev))
    return winners[0], best_ev
