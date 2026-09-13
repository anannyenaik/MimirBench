"""Reference solver for Bayesian-updating tasks.

Thin wrapper over :func:`mimirbench.tools.bayes_calculator.posterior` so that the
"correct answer" used for grading is exactly what the ``bayes_calculator`` tool
would produce for an agent.
"""

from __future__ import annotations

from typing import Any

from mimirbench.environments.bayesian_games.schemas import BayesianTaskParams
from mimirbench.evals.schemas import Task
from mimirbench.tools.bayes_calculator import posterior

__all__ = ["reference_solver", "solve_params"]


def solve_params(params: BayesianTaskParams) -> list[float]:
    """Compute the exact posterior for a parameter set."""
    return posterior(params.priors, params.likelihood, params.observations)


def reference_solver(task: Task) -> dict[str, Any]:
    """Solve a task from its public metadata; returns ``{"posterior": [...]}``."""
    params = BayesianTaskParams(**task.metadata)
    return {"posterior": solve_params(params)}
