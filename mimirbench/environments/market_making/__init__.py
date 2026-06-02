"""Market-making decision games: quote under inventory and risk constraints."""

from mimirbench.environments.market_making.avellaneda_stoikov_toy import (
    optimal_quote,
    optimal_spread,
    reservation_price,
)
from mimirbench.environments.market_making.generator import generate_params, generate_task
from mimirbench.environments.market_making.grader import grade, grade_episode
from mimirbench.environments.market_making.risk import check_inventory, would_breach
from mimirbench.environments.market_making.schemas import (
    MarketMakingAction,
    MarketMakingEpisodeResult,
    MarketMakingTaskParams,
    Quote,
)
from mimirbench.environments.market_making.simulator import (
    avellaneda_stoikov_policy,
    constant_spread_policy,
    simulate_episode,
)
from mimirbench.environments.market_making.solver import reference_solver, solve_params
from mimirbench.evals.registry import EnvironmentSpec
from mimirbench.evals.schemas import EnvironmentFamily

__all__ = [
    "MarketMakingAction",
    "MarketMakingEpisodeResult",
    "MarketMakingTaskParams",
    "Quote",
    "avellaneda_stoikov_policy",
    "build_spec",
    "check_inventory",
    "constant_spread_policy",
    "generate_params",
    "generate_task",
    "grade",
    "grade_episode",
    "optimal_quote",
    "optimal_spread",
    "reference_solver",
    "reservation_price",
    "simulate_episode",
    "solve_params",
    "would_breach",
]


def build_spec() -> EnvironmentSpec:
    """Construct the registry spec for the market-making environment."""
    return EnvironmentSpec(
        name="market_making",
        family=EnvironmentFamily.MARKET_MAKING,
        description="Toy quote decisions under inventory, loss, and adverse-selection constraints.",
        generator=generate_task,
        grader=grade,
        reference_solver=reference_solver,
    )
