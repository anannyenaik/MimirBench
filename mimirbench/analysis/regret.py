"""Regret metrics for sequential decision tasks.

Regret measures how far an agent's realized rewards fall short of the best
achievable rewards (typically from the reference solver / oracle policy).
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import numpy.typing as npt

from mimirbench.evals.schemas import EvalTaskRecord

__all__ = [
    "average_regret",
    "cumulative_regret",
    "mean_record_regret",
    "per_step_regret",
    "record_regrets",
    "total_regret",
]


def _validate(agent: Sequence[float], optimal: Sequence[float]) -> tuple[np.ndarray, np.ndarray]:
    a = np.asarray(agent, dtype=np.float64)
    o = np.asarray(optimal, dtype=np.float64)
    if a.shape != o.shape:
        raise ValueError(f"agent {a.shape} and optimal {o.shape} rewards must match.")
    if a.ndim != 1:
        raise ValueError("rewards must be 1-D.")
    return a, o


def per_step_regret(agent_rewards: Sequence[float], optimal_rewards: Sequence[float]) -> npt.NDArray[np.float64]:
    """Per-step regret ``optimal - agent`` (non-negative when the oracle is optimal)."""
    a, o = _validate(agent_rewards, optimal_rewards)
    return o - a


def cumulative_regret(agent_rewards: Sequence[float], optimal_rewards: Sequence[float]) -> npt.NDArray[np.float64]:
    """Cumulative regret over the trajectory."""
    return np.cumsum(per_step_regret(agent_rewards, optimal_rewards))


def total_regret(agent_rewards: Sequence[float], optimal_rewards: Sequence[float]) -> float:
    """Total regret across the whole trajectory."""
    return float(per_step_regret(agent_rewards, optimal_rewards).sum())


def average_regret(agent_rewards: Sequence[float], optimal_rewards: Sequence[float]) -> float:
    """Mean per-step regret."""
    return float(per_step_regret(agent_rewards, optimal_rewards).mean())


def record_regrets(records: Sequence[EvalTaskRecord]) -> list[float]:
    """Extract per-task regret metrics from run records."""
    regrets: list[float] = []
    for record in records:
        value = record.grader_result.metrics.get("regret")
        if value is not None:
            regrets.append(float(value))
    return regrets


def mean_record_regret(records: Sequence[EvalTaskRecord]) -> float | None:
    """Return mean recorded regret, or ``None`` when the run has no regret metric."""
    regrets = record_regrets(records)
    return float(np.mean(np.asarray(regrets, dtype=np.float64))) if regrets else None
