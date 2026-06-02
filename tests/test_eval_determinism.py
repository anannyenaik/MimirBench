"""End-to-end determinism and registry tests for the eval harness."""

from __future__ import annotations

import pytest

from mimirbench.evals import environment_names, run_eval
from mimirbench.evals.schemas import EvalConfig

REGISTERED = [
    "bayesian_games",
    "auctions",
    "hidden_regimes",
    "market_making",
    "prediction_markets",
    "adversarial_risk",
]


def test_builtin_environments_are_registered() -> None:
    names = environment_names()
    for env in REGISTERED:
        assert env in names


def test_run_eval_is_deterministic() -> None:
    config = EvalConfig(environment="bayesian_games", n_tasks=20, seed=123)
    first = run_eval(config)
    second = run_eval(config)
    assert first == second
    assert first.model_dump() == second.model_dump()


@pytest.mark.parametrize("environment", REGISTERED)
def test_reference_agent_is_near_perfect(environment: str) -> None:
    config = EvalConfig(environment=environment, n_tasks=10, seed=0)
    report = run_eval(config)
    assert report.n_tasks == 10
    assert report.mean_score > 0.99
    assert report.pass_rate == 1.0
    assert report.violation_rate == 0.0


def test_different_seeds_produce_different_tasks() -> None:
    first = run_eval(EvalConfig(environment="auctions", n_tasks=5, seed=1))
    second = run_eval(EvalConfig(environment="auctions", n_tasks=5, seed=2))
    assert first != second  # same perfect scores, but different task instances


def test_unknown_environment_raises() -> None:
    with pytest.raises(KeyError):
        run_eval(EvalConfig(environment="does_not_exist", n_tasks=1, seed=0))
