"""Tests for the tool-using agent policies and tool validation."""

from __future__ import annotations

import json

import pytest

from mimirbench.agents.model_client import (
    ModelClient,
    ModelRequest,
    ModelResponseEnvelope,
    ModelUsage,
    ProviderStatus,
)
from mimirbench.agents.parsing import extract_json
from mimirbench.agents.resolver import resolve_agent
from mimirbench.agents.tool_agent import DEFAULT_MAX_TOOL_STEPS, ModelToolAgent, ReferenceToolAgent
from mimirbench.agents.tools_registry import ENVIRONMENT_TOOL_ALLOWLIST, default_tools
from mimirbench.evals.registry import get
from mimirbench.evals.schemas import EnvironmentFamily


class ScriptedClient(ModelClient):
    """Returns a fixed list of raw responses, one per call."""

    provider = "fake"
    model = "fake-model"

    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.calls = 0

    def generate(self, request: ModelRequest) -> ModelResponseEnvelope:
        text = self.responses[self.calls] if self.calls < len(self.responses) else "{}"
        self.calls += 1
        return ModelResponseEnvelope(
            provider=self.provider,
            model=self.model,
            raw_text=text,
            parsed_json=extract_json(text),
            usage=ModelUsage(input_tokens=5, output_tokens=3, total_tokens=8),
            latency_ms=1.0,
            finish_reason="stop",
        )

    def check_availability(self) -> ProviderStatus:
        return ProviderStatus("fake", True, False, False, None, True, "fake")


def _reference_tool_agent(env: str = "bayesian_games") -> ReferenceToolAgent:
    spec = get(env)
    return ReferenceToolAgent(
        environment=env,
        family=spec.family,
        reference_solver=spec.reference_solver,
    )


def test_reference_tool_agent_solves_bayes_via_tool() -> None:
    spec = get("bayesian_games")
    instance = spec.generator(2)
    agent = _reference_tool_agent("bayesian_games")
    response = agent.act(instance.task)

    result = spec.grader(instance.task, response, instance.key)
    assert result.passed is True
    steps = response.metadata["tool_audit_steps"]
    assert any(s["requested_tool"] == "bayes_calculator" for s in steps)
    assert all(s["validation_status"] == "allowed" for s in steps)


def test_reference_tool_agent_resolves_via_config() -> None:
    spec = get("auctions")
    agent = resolve_agent({"type": "tool", "tool_policy": "reference"}, spec=spec)
    assert isinstance(agent, ReferenceToolAgent)
    instance = spec.generator(1)
    response = agent.act(instance.task)
    result = spec.grader(instance.task, response, instance.key)
    assert result.passed is True


def test_tool_agent_default_max_steps_is_three() -> None:
    assert DEFAULT_MAX_TOOL_STEPS == 3
    agent = _reference_tool_agent()
    assert agent.max_steps == 3


def test_tool_agent_rejects_tool_outside_allowlist() -> None:
    spec = get("bayesian_games")
    instance = spec.generator(1)
    # The model asks for risk_checker, which is NOT allowed for bayesian_games,
    # then provides a final answer.
    client = ScriptedClient(
        [
            json.dumps({"tool": "risk_checker", "arguments": {"position": 1.0}}),
            json.dumps({"final": {"posterior": [0.5, 0.5], "reasoning_summary": "ok"}}),
        ]
    )
    agent = ModelToolAgent(client, environment="bayesian_games", family=spec.family)
    response = agent.act(instance.task)

    steps = response.metadata["tool_audit_steps"]
    invalid = [s for s in steps if s["validation_status"] == "not_allowed"]
    assert len(invalid) == 1
    assert invalid[0]["requested_tool"] == "risk_checker"
    assert invalid[0]["tool_output"] is None  # never executed
    assert response.parsed_answer == {"posterior": [0.5, 0.5], "reasoning_summary": "ok"}


def test_tool_agent_records_unknown_tool() -> None:
    spec = get("bayesian_games")
    instance = spec.generator(1)
    client = ScriptedClient(
        [
            json.dumps({"tool": "rm_rf_tool", "arguments": {}}),
            json.dumps({"final": {"posterior": [1.0], "reasoning_summary": "x"}}),
        ]
    )
    agent = ModelToolAgent(client, environment="bayesian_games", family=spec.family)
    response = agent.act(instance.task)
    steps = response.metadata["tool_audit_steps"]
    assert any(s["validation_status"] == "unknown_tool" for s in steps)


def test_tool_agent_cannot_execute_arbitrary_callables() -> None:
    # The registry is fixed: there is no way to register or call code outside it.
    registry = default_tools()
    assert set(registry) == {
        "bayes_calculator",
        "ev_calculator",
        "risk_checker",
        "auction_solver",
        "market_simulator",
    }
    # Per-environment allow-lists are subsets of the registry.
    for env, allowed in ENVIRONMENT_TOOL_ALLOWLIST.items():
        assert allowed <= set(registry), env


def test_tool_agent_allowed_tool_executes_and_is_audited() -> None:
    spec = get("bayesian_games")
    instance = spec.generator(1)
    meta = instance.task.metadata
    client = ScriptedClient(
        [
            json.dumps(
                {
                    "tool": "bayes_calculator",
                    "arguments": {
                        "priors": meta["priors"],
                        "likelihood": meta["likelihood"],
                        "observations": meta["observations"],
                    },
                }
            ),
            json.dumps({"final": {"posterior": instance.key.payload["posterior"]}}),
        ]
    )
    agent = ModelToolAgent(client, environment="bayesian_games", family=spec.family)
    response = agent.act(instance.task)
    steps = response.metadata["tool_audit_steps"]
    allowed = [s for s in steps if s["validation_status"] == "allowed"]
    assert len(allowed) == 1
    assert allowed[0]["tool_output"]["posterior"]  # tool executed and produced output
    assert response.usage is not None and response.usage.total_tokens is not None


def test_tool_agent_max_steps_without_final_terminates_safely() -> None:
    spec = get("bayesian_games")
    instance = spec.generator(1)
    # Model keeps requesting a (disallowed) tool and never finalizes.
    client = ScriptedClient([json.dumps({"tool": "risk_checker", "arguments": {}})] * 10)
    agent = ModelToolAgent(client, environment="bayesian_games", family=spec.family, max_steps=3)
    response = agent.act(instance.task)
    # finalize() returns the last (empty) attempt -> parsed is None -> error recorded.
    assert len(response.metadata["tool_audit_steps"]) == 3
    assert response.parsed_answer is None or response.error is not None


def test_tool_policy_decide_only_sees_task_not_key() -> None:
    # The policy decision hook receives the public task and prior tool calls only.
    import inspect

    params = list(inspect.signature(ReferenceToolAgent.decide).parameters)
    assert params == ["self", "task", "scratchpad"]
    assert "key" not in params


def test_resolve_tool_requires_spec() -> None:
    with pytest.raises(ValueError, match="requires an environment spec"):
        resolve_agent({"type": "tool"})


def test_model_tool_agent_family_alignment() -> None:
    spec = get("auctions")
    agent = ModelToolAgent(
        ScriptedClient(["{}"]), environment="auctions", family=EnvironmentFamily.AUCTIONS
    )
    assert agent.allowed_tools == ENVIRONMENT_TOOL_ALLOWLIST["auctions"]
    assert agent.family == spec.family
