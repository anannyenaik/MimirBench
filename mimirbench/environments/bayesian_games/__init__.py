"""Bayesian-updating games: posterior inference under a known generative model.

This is the reference environment for MimirBench — fully implemented end to end
(generator, exact solver, deterministic grader) and the template other
environments follow.
"""

from mimirbench.environments.bayesian_games.generator import generate_params, generate_task
from mimirbench.environments.bayesian_games.grader import grade
from mimirbench.environments.bayesian_games.schemas import BayesianSolution, BayesianTaskParams
from mimirbench.environments.bayesian_games.solver import reference_solver, solve_params
from mimirbench.evals.registry import EnvironmentSpec
from mimirbench.evals.schemas import EnvironmentFamily

__all__ = [
    "BayesianSolution",
    "BayesianTaskParams",
    "build_spec",
    "generate_params",
    "generate_task",
    "grade",
    "reference_solver",
    "solve_params",
]


def build_spec() -> EnvironmentSpec:
    """Construct the registry spec for the Bayesian-games environment."""
    return EnvironmentSpec(
        name="bayesian_games",
        family=EnvironmentFamily.BAYESIAN_GAMES,
        description="Posterior inference over hidden sources from an observed symbol sequence.",
        generator=generate_task,
        grader=grade,
        reference_solver=reference_solver,
    )
