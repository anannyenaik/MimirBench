"""Validation checks for robustness configs."""

from __future__ import annotations

from pathlib import Path

from mimirbench.evals.robustness_runner import load_robustness_config, validate_robustness_config
from mimirbench.evals.schemas import RobustnessRunConfig
from mimirbench.evals.variants import variant_type_values

ROBUSTNESS_CONFIGS = [
    Path("configs/robustness_reference_bayes.yaml"),
    Path("configs/robustness_mock_bayes.yaml"),
    Path("configs/robustness_reference_all_envs.yaml"),
    Path("configs/robustness_mock_all_envs.yaml"),
    Path("configs/robustness_adversarial_risk_pressure.yaml"),
]


def test_all_robustness_configs_validate() -> None:
    for path in ROBUSTNESS_CONFIGS:
        config = load_robustness_config(path)
        assert isinstance(config, RobustnessRunConfig)
        validate_robustness_config(config)


def test_robustness_configs_use_only_reference_or_mock_agents() -> None:
    for path in ROBUSTNESS_CONFIGS:
        config = load_robustness_config(path)
        assert config.agent.type in {"reference", "mock"}


def test_robustness_config_variant_types_are_catalogued() -> None:
    known = set(variant_type_values())
    for path in ROBUSTNESS_CONFIGS:
        config = load_robustness_config(path)
        for environment in config.environments:
            assert set(environment.variant_types) <= known
            assert environment.variants_per_task <= config.robustness.max_variants_per_task
