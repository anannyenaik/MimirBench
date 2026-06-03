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


def test_require_tool_first_reprompts_until_a_tool_is_used() -> None:
    spec = get("bayesian_games")
    instance = spec.generator(1)
    meta = instance.task.metadata
    # Step 1: model answers directly (no tool) -> rejected. Step 2: it calls the
    # allowed tool. Step 3: it finalizes from the tool output.
    client = ScriptedClient(
        [
            json.dumps({"posterior": [0.5, 0.5], "reasoning_summary": "tried direct"}),
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
    agent = ModelToolAgent(
        client,
        environment="bayesian_games",
        family=spec.family,
        max_steps=3,
        require_tool_first=True,
    )
    response = agent.act(instance.task)
    steps = response.metadata["tool_audit_steps"]
    # The premature direct answer is recorded as a no-tool step...
    assert any(s["validation_status"] == "no_tool_requested" for s in steps)
    # ...and the model then actually used the allowed tool.
    assert any(
        s["validation_status"] == "allowed" and s["requested_tool"] == "bayes_calculator"
        for s in steps
    )


def test_require_tool_first_terminates_safely_if_model_never_uses_a_tool() -> None:
    spec = get("bayesian_games")
    instance = spec.generator(1)
    # The model answers directly on every turn and never calls a tool.
    client = ScriptedClient(
        [json.dumps({"posterior": [0.5, 0.5], "reasoning_summary": "x"})] * 10
    )
    agent = ModelToolAgent(
        client,
        environment="bayesian_games",
        family=spec.family,
        max_steps=3,
        require_tool_first=True,
    )
    response = agent.act(instance.task)
    steps = response.metadata["tool_audit_steps"]
    # Every in-loop step rejected the premature answer; bounded by max_steps.
    assert len(steps) == 3
    assert all(s["validation_status"] == "no_tool_requested" for s in steps)
    # finalize() still returns the model's direct answer -> no hard failure.
    assert response.error is None
    assert response.parsed_answer is not None
    assert response.parsed_answer.get("posterior") == [0.5, 0.5]


def test_require_tool_first_default_off_accepts_direct_answer() -> None:
    # With the flag off (default), a direct answer on step 1 is accepted as the
    # final answer and no tool is used -- the pre-existing behaviour is preserved.
    spec = get("bayesian_games")
    instance = spec.generator(1)
    client = ScriptedClient([json.dumps({"posterior": [0.5, 0.5], "reasoning_summary": "x"})])
    agent = ModelToolAgent(client, environment="bayesian_games", family=spec.family)
    response = agent.act(instance.task)
    assert agent.require_tool_first is False
    assert response.metadata["tool_audit_steps"] == []
    assert response.parsed_answer == {"posterior": [0.5, 0.5], "reasoning_summary": "x"}


def test_bayes_tool_renormalises_prompt_rounded_rows() -> None:
    # Rows copied from prompt values rounded to 3 dp (e.g. sum 0.999) still work.
    fn = default_tools()["bayes_calculator"].fn
    out = fn(
        priors=[0.333, 0.333, 0.334],
        likelihood=[[0.333, 0.333, 0.333], [0.5, 0.25, 0.25], [0.1, 0.1, 0.8]],
        observations=[0, 1],
    )
    post = out["posterior"]
    assert len(post) == 3
    assert abs(sum(post) - 1.0) < 1e-9


def test_bayes_tool_accepts_one_indexed_observations() -> None:
    from mimirbench.tools.bayes_calculator import posterior

    fn = default_tools()["bayes_calculator"].fn
    priors = [0.5, 0.5]
    likelihood = [[0.2, 0.3, 0.5], [0.6, 0.3, 0.1]]  # m = 3 signals
    # 1..3 are out of the 0-indexed range [0, 3) but valid as 1-indexed labels.
    one_indexed = fn(priors=priors, likelihood=likelihood, observations=[1, 3])
    assert one_indexed["posterior"] == posterior(priors, likelihood, [0, 2])


def test_bayes_tool_leaves_valid_zero_indexed_observations() -> None:
    from mimirbench.tools.bayes_calculator import posterior

    fn = default_tools()["bayes_calculator"].fn
    priors = [0.5, 0.5]
    likelihood = [[0.2, 0.3, 0.5], [0.6, 0.3, 0.1]]  # m = 3 signals
    # [1, 2] is valid as 0-indexed (in [0, 3)); it must NOT be shifted to [0, 1].
    out = fn(priors=priors, likelihood=likelihood, observations=[1, 2])
    assert out["posterior"] == posterior(priors, likelihood, [1, 2])


def test_bayes_tool_still_rejects_genuinely_malformed_input() -> None:
    from mimirbench.tools.bayes_calculator import BayesError

    fn = default_tools()["bayes_calculator"].fn
    # A likelihood row nowhere near a distribution (sum 0.4) is not renormalised.
    with pytest.raises(BayesError):
        fn(priors=[0.5, 0.5], likelihood=[[0.2, 0.2], [0.5, 0.5]], observations=[0])
