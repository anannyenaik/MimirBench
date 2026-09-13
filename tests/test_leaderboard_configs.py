"""Validation checks for the retained hosted-model configurations."""

from __future__ import annotations

from pathlib import Path

from mimirbench.evals.leaderboard import (
    LeaderboardModel,
    build_agent_config,
    load_leaderboard_config,
    validate_leaderboard_config,
)


def test_selected_hosted_config_validates() -> None:
    config = load_leaderboard_config(Path("configs/benchmark/hosted_pilot.yaml"))
    validate_leaderboard_config(config)
    assert len(config.models) == 8
    assert len(config.environments) == 6
    assert sum(environment.num_tasks for environment in config.environments) == 120
    assert config.agents == ["direct"]
    assert config.run.output_dir == "runs/hosted_pilot"


def test_leaderboard_model_request_extra_flows_to_agent_config() -> None:
    model = LeaderboardModel(
        name="gemini_flash",
        provider="gemini",
        model="gemini-3.5-flash",
        request_extra={"thinking_config": {"thinking_budget": 0}},
    )
    agent_config = build_agent_config(model, "direct")
    assert agent_config.provider == "gemini"
    assert agent_config.request_extra == {"thinking_config": {"thinking_budget": 0}}
