"""Validation checks for real-model leaderboard configs.

These tests validate config shape only. They never call providers or download
models.
"""

from __future__ import annotations

from pathlib import Path

from mimirbench.evals.leaderboard import (
    LeaderboardModel,
    build_agent_config,
    load_leaderboard_config,
    validate_leaderboard_config,
)

LEADERBOARD_CONFIGS = [
    Path("configs/leaderboard/leaderboard_openai_tiny.yaml"),
    Path("configs/leaderboard/leaderboard_anthropic_tiny.yaml"),
    Path("configs/leaderboard/leaderboard_local_tiny.yaml"),
    Path("configs/leaderboard/leaderboard_all_available_tiny.yaml"),
]


def test_all_leaderboard_configs_validate() -> None:
    for path in LEADERBOARD_CONFIGS:
        config = load_leaderboard_config(path)
        validate_leaderboard_config(config)


def test_leaderboard_configs_are_tiny_paired_runs() -> None:
    for path in LEADERBOARD_CONFIGS:
        config = load_leaderboard_config(path)
        assert config.run.cache is True
        assert config.run.max_workers == 1
        assert config.run.output_dir is not None
        assert config.run.output_dir.startswith("reports/runs/leaderboard/")
        assert config.agents == ["direct", "tool", "reflective"]
        assert config.robustness.enabled is True
        for env in config.environments:
            assert 10 <= env.num_tasks <= 20
            assert env.seed == 123
        for model in config.models:
            assert model.temperature == 0


def test_leaderboard_model_request_extra_flows_to_agent_config() -> None:
    model = LeaderboardModel(
        name="openai_gpt55_rescue",
        provider="openai",
        model="gpt-5.5",
        request_extra={"reasoning_effort": "low"},
    )

    agent_config = build_agent_config(model, "direct")

    assert agent_config.request_extra == {"reasoning_effort": "low"}


def test_leaderboard_model_supports_gemini_provider() -> None:
    model = LeaderboardModel(
        name="gemini_flash_lite",
        provider="gemini",
        model="gemini-3.1-flash-lite",
        request_extra={"use_default_temperature": True},
    )

    agent_config = build_agent_config(model, "direct")

    assert agent_config.provider == "gemini"
    assert agent_config.model == "gemini-3.1-flash-lite"
    assert agent_config.request_extra == {"use_default_temperature": True}
