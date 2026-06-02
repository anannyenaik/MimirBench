"""Registry checks for all runnable environment families."""

from __future__ import annotations

from mimirbench.evals import environment_names, list_specs

ALL_ENVS = {
    "bayesian_games",
    "auctions",
    "hidden_regimes",
    "market_making",
    "prediction_markets",
    "adversarial_risk",
}


def test_all_six_environments_register() -> None:
    assert ALL_ENVS.issubset(set(environment_names()))


def test_all_registered_specs_are_runnable_shapes() -> None:
    specs = {spec.name: spec for spec in list_specs()}
    for name in ALL_ENVS:
        spec = specs[name]
        instance = spec.generator(101)
        answer = spec.reference_solver(instance.task)
        assert instance.task.family == spec.family
        assert isinstance(answer, dict)
        assert answer
