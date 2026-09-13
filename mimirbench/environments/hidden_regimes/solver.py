"""Exact HMM forward-filter solver for hidden-regime tasks.

Computes the filtered belief ``P(regime_t | observations_1..t)`` by the standard
normalised forward recursion: alternate a Bayesian *update* (multiply by the
emission likelihood and renormalise) with a Markov *prediction* (push the belief
through the transition matrix). The final filtered belief is the graded answer.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from mimirbench.environments.hidden_regimes.schemas import HiddenRegimeParams
from mimirbench.evals.schemas import Task
from mimirbench.tools.bayes_calculator import validate_distribution

__all__ = ["filtered_beliefs", "final_belief", "reference_solver"]


def filtered_beliefs(params: HiddenRegimeParams) -> list[list[float]]:
    """Return the filtered belief at every observed timestep."""
    initial = validate_distribution(params.initial, name="initial")
    transition = np.asarray(params.transition, dtype=np.float64)
    emission = np.asarray(params.emission, dtype=np.float64)
    n = initial.shape[0]

    if transition.shape != (n, n):
        raise ValueError(f"transition must be {n}x{n}, got {transition.shape}.")
    if emission.shape[0] != n:
        raise ValueError(f"emission must have {n} rows, got {emission.shape[0]}.")
    for i in range(n):
        validate_distribution(transition[i], name=f"transition row {i}")
        validate_distribution(emission[i], name=f"emission row {i}")

    beliefs: list[list[float]] = []
    predicted = initial  # P(regime_1) before any observation
    for o in params.observations:
        if not 0 <= o < emission.shape[1]:
            raise ValueError(f"observation {o} out of range.")
        updated = predicted * emission[:, o]
        total = updated.sum()
        if total <= 0.0:
            raise ValueError("observation impossible under all regimes.")
        updated = updated / total
        beliefs.append([float(x) for x in updated])
        predicted = transition.T @ updated  # P(regime_{t+1} | obs_1..t)
    return beliefs


def final_belief(params: HiddenRegimeParams) -> list[float]:
    """Filtered belief at the last observed timestep (or the prior if no obs)."""
    beliefs = filtered_beliefs(params)
    if not beliefs:
        return [float(x) for x in validate_distribution(params.initial, name="initial")]
    return beliefs[-1]


def reference_solver(task: Task) -> dict[str, Any]:
    """Solve from public metadata; returns ``{"regime_posterior": [...]}``."""
    params = HiddenRegimeParams(**task.metadata)
    return {"regime_posterior": final_belief(params)}
