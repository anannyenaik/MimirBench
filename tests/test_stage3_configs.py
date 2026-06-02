"""Validation checks for Stage 3 evaluation configs."""

from __future__ import annotations

from pathlib import Path

from mimirbench.evals.runner import load_eval_config, validate_eval_config
from mimirbench.evals.schemas import EvalRunConfig

STAGE3_CONFIGS = [
    Path("configs/eval_reference_market_making.yaml"),
    Path("configs/eval_reference_prediction_markets.yaml"),
    Path("configs/eval_reference_adversarial_risk.yaml"),
    Path("configs/eval_mock_market_making.yaml"),
    Path("configs/eval_mock_prediction_markets.yaml"),
    Path("configs/eval_mock_adversarial_risk.yaml"),
    Path("configs/eval_reference_all_envs.yaml"),
    Path("configs/eval_mock_all_envs.yaml"),
]


def test_all_stage3_configs_validate() -> None:
    for path in STAGE3_CONFIGS:
        config = load_eval_config(path)
        assert isinstance(config, EvalRunConfig)
        validate_eval_config(config)


def test_stage3_configs_use_only_reference_or_mock_agents() -> None:
    for path in STAGE3_CONFIGS:
        config = load_eval_config(path)
        assert isinstance(config, EvalRunConfig)
        assert config.agent.type in {"reference", "mock"}
