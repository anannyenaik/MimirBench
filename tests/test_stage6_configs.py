"""Validation checks for Stage 6 comparison configs."""

from __future__ import annotations

from pathlib import Path

from mimirbench.evals.comparison_runner import load_comparison_config, validate_comparison_config

STAGE6_CONFIGS = [
    Path("configs/comparison_reference_bayes.yaml"),
    Path("configs/comparison_mock_bayes.yaml"),
    Path("configs/comparison_tool_reference_bayes.yaml"),
    Path("configs/comparison_api_openai_bayes_tiny.yaml"),
    Path("configs/comparison_api_openai_all_envs_tiny.yaml"),
    Path("configs/comparison_local_bayes_tiny.yaml"),
    Path("configs/comparison_direct_tool_reflective_bayes_tiny.yaml"),
]


def test_stage6_configs_validate_and_use_comparison_output_dir() -> None:
    for path in STAGE6_CONFIGS:
        config = load_comparison_config(path)
        validate_comparison_config(config)
        assert config.run.cache is True
        assert config.run.max_workers == 1
        assert config.run.output_dir is not None
        assert config.run.output_dir.startswith("reports/runs/comparisons/")


def test_stage6_real_model_configs_are_tiny() -> None:
    for path in STAGE6_CONFIGS:
        if not any(marker in path.name for marker in ("api", "local", "direct_tool")):
            continue
        config = load_comparison_config(path)
        for environment in config.environments:
            assert environment.num_tasks <= 10


def test_stage6_direct_tool_reflective_config_contains_all_three_modes() -> None:
    config = load_comparison_config(Path("configs/comparison_direct_tool_reflective_bayes_tiny.yaml"))
    assert {agent.type for agent in config.agents} == {"direct", "tool", "reflective"}
