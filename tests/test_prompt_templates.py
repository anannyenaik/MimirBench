"""Tests for environment-aware prompt builders."""

from __future__ import annotations

import pytest

from mimirbench.agents.prompts import (
    DEFAULT_SYSTEM_PROMPT,
    EXPECTED_KEYS,
    TOOL_SYSTEM_PROMPT,
    build_messages,
    build_tool_step_prompt,
)
from mimirbench.evals.registry import environment_names, get

# Phrases that would (wrongly) request hidden/private chain-of-thought.
_FORBIDDEN_REQUEST_PHRASES = (
    "think step by step",
    "let's think step by step",
    "show your reasoning",
    "show your work",
    "explain your reasoning in detail",
    "walk me through your reasoning",
    "internal monologue:",
)


def _all_task_prompts() -> list[tuple[str, str, str]]:
    bundles = []
    for name in environment_names():
        spec = get(name)
        task = spec.generator(1).task
        bundle = build_messages(task)
        bundles.append((name, bundle.system, bundle.user))
    return bundles


def test_every_prompt_states_expected_json_keys() -> None:
    for name in environment_names():
        spec = get(name)
        task = spec.generator(1).task
        bundle = build_messages(task)
        keys = EXPECTED_KEYS[task.family]
        # The primary answer key (first non-summary key) must appear in the user prompt.
        primary = next(k for k in keys if k != "reasoning_summary")
        assert primary in bundle.user, f"{name}: missing key {primary!r}"
        assert "reasoning_summary" in bundle.user


def test_no_prompt_requests_hidden_chain_of_thought() -> None:
    prompts = [DEFAULT_SYSTEM_PROMPT, TOOL_SYSTEM_PROMPT]
    for _name, system, user in _all_task_prompts():
        prompts.extend([system, user])
    for text in prompts:
        lowered = text.lower()
        for phrase in _FORBIDDEN_REQUEST_PHRASES:
            assert phrase not in lowered, f"prompt requests hidden CoT: {phrase!r}"


def test_prompts_forbid_hidden_cot_and_ask_for_summary() -> None:
    for _name, system, user in _all_task_prompts():
        combined = (system + "\n" + user).lower()
        assert "hidden chain-of-thought" in combined
        assert "reasoning_summary" in combined


def test_prompts_instruct_abstention_and_constraints() -> None:
    for _name, system, _user in _all_task_prompts():
        lowered = system.lower()
        assert "abstain" in lowered
        assert "limit" in lowered  # obey risk/hard limits


def test_prompts_avoid_live_trading_advice_language() -> None:
    for _name, system, _user in _all_task_prompts():
        assert "not financial, investment, or trading advice" in system.lower()


def test_tool_system_prompt_forbids_hidden_cot() -> None:
    lowered = TOOL_SYSTEM_PROMPT.lower()
    assert "hidden chain-of-thought" in lowered
    assert '"tool"' in TOOL_SYSTEM_PROMPT
    assert '"final"' in TOOL_SYSTEM_PROMPT


def test_build_tool_step_prompt_contains_tools_and_finalize_flag() -> None:
    task = get("bayesian_games").generator(1).task
    step = build_tool_step_prompt(task, tool_block="- bayes_calculator: ...", observations="(none)")
    assert "bayes_calculator" in step
    assert "tool" in step.lower()
    final = build_tool_step_prompt(
        task, tool_block="- bayes_calculator: ...", observations="x", must_finalize=True
    )
    assert "final answer" in final.lower()


def test_distribution_envs_request_probability_vector() -> None:
    for name in ("bayesian_games", "hidden_regimes"):
        task = get(name).generator(2).task
        user = build_messages(task).user
        assert "sum" in user.lower()  # probabilities must sum to 1


@pytest.mark.parametrize("name", ["prediction_markets", "adversarial_risk"])
def test_decision_envs_list_action_vocabulary(name: str) -> None:
    task = get(name).generator(3).task
    user = build_messages(task).user
    assert "action" in user
