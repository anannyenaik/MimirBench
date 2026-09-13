"""Tests for deterministic mock agents."""

from __future__ import annotations

from mimirbench.agents.mock_agents import AlwaysAbstainAgent, NoisyReferenceAgent, RandomValidAgent
from mimirbench.environments.bayesian_games.generator import generate_task
from mimirbench.environments.bayesian_games.grader import grade


def test_always_abstain_is_invalid_for_bayes_grader() -> None:
    instance = generate_task(0)
    response = AlwaysAbstainAgent().act(instance.task)
    result = grade(instance.task, response, instance.key)
    assert response.parsed_answer == {
        "abstain": True,
        "reasoning_summary": "Deterministic mock abstention; not a model output.",
    }
    assert not result.passed
    assert "no_valid_answer" in result.violations


def test_random_valid_is_deterministic_per_task() -> None:
    instance = generate_task(1)
    agent = RandomValidAgent(seed=123)
    first = agent.act(instance.task)
    second = agent.act(instance.task)
    assert first == second
    assert first.parsed_answer is not None
    assert "posterior" in first.parsed_answer


def test_noisy_reference_uses_key_in_diagnostic_mode() -> None:
    instance = generate_task(2)
    agent = NoisyReferenceAgent(seed=123)
    response = agent.act_with_key(instance.task, instance.key)
    result = grade(instance.task, response, instance.key)
    assert result.passed
    assert response.metadata["diagnostic_uses_grading_key"] is True
    assert response.parsed_answer is not None
    assert "posterior" in response.parsed_answer
