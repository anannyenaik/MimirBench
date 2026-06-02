"""Agent resolver tests."""

from __future__ import annotations

import pytest

from mimirbench.agents import APIModelAgent, LocalModelAgent, ReferenceAgent
from mimirbench.agents.mock_agents import RandomValidAgent
from mimirbench.agents.resolver import resolve_agent
from mimirbench.evals.registry import get


def test_resolves_reference_agent() -> None:
    agent = resolve_agent({"type": "reference"}, spec=get("bayesian_games"))
    assert isinstance(agent, ReferenceAgent)
    assert agent.name == "reference"


def test_resolves_mock_agent() -> None:
    agent = resolve_agent({"type": "mock", "behaviour": "random_valid", "seed": 7})
    assert isinstance(agent, RandomValidAgent)
    assert agent.seed == 7


def test_resolves_api_without_importing_optional_client() -> None:
    agent = resolve_agent({"type": "api", "provider": "openai", "model": "test-model"})
    assert isinstance(agent, APIModelAgent)
    assert agent.model == "test-model"


def test_resolves_local_without_loading_model() -> None:
    agent = resolve_agent({"type": "local", "model_name": "local-test", "device": "auto"})
    assert isinstance(agent, LocalModelAgent)
    assert agent.model_name == "local-test"
    assert agent.device is None


def test_tool_agent_requires_spec() -> None:
    with pytest.raises(ValueError, match="requires an environment spec"):
        resolve_agent({"type": "tool"})


def test_resolves_reference_tool_agent_with_spec() -> None:
    from mimirbench.agents.tool_agent import ReferenceToolAgent

    agent = resolve_agent({"type": "tool", "tool_policy": "reference"}, spec=get("bayesian_games"))
    assert isinstance(agent, ReferenceToolAgent)
    assert agent.max_steps == 3


def test_resolves_model_tool_agent_without_importing_client() -> None:
    from mimirbench.agents.tool_agent import ModelToolAgent

    agent = resolve_agent(
        {"type": "tool", "tool_policy": "model", "provider": "openai", "model": "test-model"},
        spec=get("bayesian_games"),
    )
    assert isinstance(agent, ModelToolAgent)
    assert agent.client.model == "test-model"
