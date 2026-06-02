"""Auction games: expected-surplus reasoning in second-price sealed-bid auctions.

Fully implemented end to end (generator, closed-form solver, grader) and
registered with the eval runner.
"""

from mimirbench.environments.auctions.generator import generate_params, generate_task
from mimirbench.environments.auctions.grader import grade
from mimirbench.environments.auctions.schemas import AuctionSolution, AuctionTaskParams
from mimirbench.environments.auctions.solver import reference_solver, solve_params
from mimirbench.evals.registry import EnvironmentSpec
from mimirbench.evals.schemas import EnvironmentFamily

__all__ = [
    "AuctionSolution",
    "AuctionTaskParams",
    "build_spec",
    "generate_params",
    "generate_task",
    "grade",
    "reference_solver",
    "solve_params",
]


def build_spec() -> EnvironmentSpec:
    """Construct the registry spec for the auctions environment."""
    return EnvironmentSpec(
        name="auctions",
        family=EnvironmentFamily.AUCTIONS,
        description="Expected-surplus reasoning in symmetric second-price sealed-bid auctions.",
        generator=generate_task,
        grader=grade,
        reference_solver=reference_solver,
    )
