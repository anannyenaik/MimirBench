"""Prediction-market tasks: belief, price, edge, and risk-limited action."""

from mimirbench.environments.prediction_markets.generator import generate_params, generate_task
from mimirbench.environments.prediction_markets.grader import brier_score, grade, log_score
from mimirbench.environments.prediction_markets.schemas import (
    PredictionMarketAction,
    PredictionMarketParams,
    PredictionMarketTaskParams,
    ProbabilityForecast,
)
from mimirbench.environments.prediction_markets.simulator import lmsr_cost, lmsr_prices
from mimirbench.environments.prediction_markets.solver import (
    posterior_probability,
    reference_solver,
    solve_params,
)
from mimirbench.evals.registry import EnvironmentSpec
from mimirbench.evals.schemas import EnvironmentFamily

__all__ = [
    "PredictionMarketAction",
    "PredictionMarketParams",
    "PredictionMarketTaskParams",
    "ProbabilityForecast",
    "brier_score",
    "build_spec",
    "generate_params",
    "generate_task",
    "grade",
    "lmsr_cost",
    "lmsr_prices",
    "log_score",
    "posterior_probability",
    "reference_solver",
    "solve_params",
]


def build_spec() -> EnvironmentSpec:
    """Construct the registry spec for the prediction-markets environment."""
    return EnvironmentSpec(
        name="prediction_markets",
        family=EnvironmentFamily.PREDICTION_MARKETS,
        description="Binary prediction-market decisions separating belief, price, edge, and limits.",
        generator=generate_task,
        grader=grade,
        reference_solver=reference_solver,
    )
