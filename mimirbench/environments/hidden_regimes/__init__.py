"""Hidden-regime market games: sequential belief updating in a hidden Markov model.

Fully implemented end to end (generator, exact forward-filter solver, grader) and
registered with the eval runner. This environment is the bridge between
single-shot Bayesian updating and dynamic, time-series reasoning.
"""

from mimirbench.environments.hidden_regimes.generator import generate_params, generate_task
from mimirbench.environments.hidden_regimes.grader import grade
from mimirbench.environments.hidden_regimes.schemas import HiddenRegimeParams, RegimeSolution
from mimirbench.environments.hidden_regimes.simulator import simulate_path
from mimirbench.environments.hidden_regimes.solver import (
    filtered_beliefs,
    final_belief,
    reference_solver,
)
from mimirbench.evals.registry import EnvironmentSpec
from mimirbench.evals.schemas import EnvironmentFamily

__all__ = [
    "HiddenRegimeParams",
    "RegimeSolution",
    "build_spec",
    "filtered_beliefs",
    "final_belief",
    "generate_params",
    "generate_task",
    "grade",
    "reference_solver",
    "simulate_path",
]


def build_spec() -> EnvironmentSpec:
    """Construct the registry spec for the hidden-regimes environment."""
    return EnvironmentSpec(
        name="hidden_regimes",
        family=EnvironmentFamily.HIDDEN_REGIMES,
        description="Filtered regime inference in a discrete hidden Markov model.",
        generator=generate_task,
        grader=grade,
        reference_solver=reference_solver,
    )
