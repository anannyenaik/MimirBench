"""Tests for DirectAgent over a fake ModelClient backend (no network)."""

from __future__ import annotations

import json

import pytest

from mimirbench.agents.direct_agent import DirectAgent
from mimirbench.agents.model_client import (
    ModelClient,
    ModelClientError,
    ModelRequest,
    ModelResponseEnvelope,
    ModelUsage,
    ProviderStatus,
)
from mimirbench.agents.parsing import extract_json
from mimirbench.evals.registry import get


class FakeClient(ModelClient):
    """Deterministic in-memory model client returning scripted responses."""

    provider = "fake"
    model = "fake-model"

    def __init__(self, response: str | Exception) -> None:
        self.response = response
        self.requests: list[ModelRequest] = []

    def generate(self, request: ModelRequest) -> ModelResponseEnvelope:
        self.requests.append(request)
        if isinstance(self.response, Exception):
            raise self.response
        return ModelResponseEnvelope(
            provider=self.provider,
            model=self.model,
            raw_text=self.response,
            parsed_json=extract_json(self.response),
            usage=ModelUsage(input_tokens=12, output_tokens=8, total_tokens=20),
            latency_ms=5.0,
            finish_reason="stop",
        )

    def check_availability(self) -> ProviderStatus:
        return ProviderStatus("fake", True, False, False, None, True, "fake client")


def _bayes_task():  # type: ignore[no-untyped-def]
    return get("bayesian_games").generator(1)


def test_direct_agent_returns_structured_response_and_preserves_raw_text() -> None:
    raw = '```json\n{"posterior": [0.2, 0.7, 0.1], "reasoning_summary": "did bayes"}\n```'
    agent = DirectAgent(FakeClient(raw), name="fake-direct")
    instance = _bayes_task()
    response = agent.act(instance.task)

    assert response.raw_text == raw  # raw model text preserved
    assert response.parsed_answer is not None
    assert response.reasoning_summary == "did bayes"
    assert response.usage is not None and response.usage.total_tokens == 20
    assert response.metadata["provider"] == "fake"
    assert response.metadata["parse"]["errors"] == []


def test_direct_agent_records_parse_errors_without_crashing() -> None:
    agent = DirectAgent(FakeClient("the answer is definitely not json"), name="fake-direct")
    response = agent.act(_bayes_task().task)
    assert response.parsed_answer is None
    assert "no_json_object" in response.metadata["parse"]["errors"]
    assert response.error is None  # backend succeeded; parsing failure is recorded, not raised


def test_direct_agent_surfaces_backend_errors_as_data() -> None:
    agent = DirectAgent(FakeClient(ModelClientError("boom")), name="fake-direct")
    response = agent.act(_bayes_task().task)
    assert response.error is not None
    assert "boom" in response.error
    assert response.parsed_answer is None


def test_direct_agent_does_not_access_grading_key() -> None:
    agent = DirectAgent(FakeClient('{"posterior": [1.0]}'), name="fake-direct")
    # No diagnostic key-access hook, unlike NoisyReferenceAgent.
    assert getattr(agent, "diagnostic_uses_grading_key", False) is False
    assert not hasattr(agent, "act_with_key")
    # act() takes only the public task.
    import inspect

    params = list(inspect.signature(agent.act).parameters)
    assert params == ["task"]


def test_direct_agent_grades_correctly_when_backend_is_right() -> None:
    instance = _bayes_task()
    spec = get("bayesian_games")
    correct = {"posterior": instance.key.payload["posterior"], "reasoning_summary": "exact"}
    agent = DirectAgent(FakeClient(json.dumps(correct)), name="fake-direct")
    response = agent.act(instance.task)
    result = spec.grader(instance.task, response, instance.key)
    assert result.passed is True
    assert result.score == pytest.approx(1.0, abs=1e-6)


def test_direct_agent_sends_environment_aware_prompt() -> None:
    client = FakeClient('{"posterior": [1.0]}')
    agent = DirectAgent(client, name="fake-direct")
    agent.act(_bayes_task().task)
    assert client.requests
    assert "posterior" in client.requests[0].user_prompt
    assert "hidden chain-of-thought" in client.requests[0].system_prompt.lower()


def test_direct_agent_passes_request_extra_to_client() -> None:
    client = FakeClient('{"posterior": [1.0]}')
    agent = DirectAgent(
        client,
        name="fake-direct",
        request_extra={"reasoning_effort": "low"},
    )
    agent.act(_bayes_task().task)

    assert client.requests
    assert client.requests[0].extra == {"reasoning_effort": "low"}
