"""Pre-run task, token and cost estimates for benchmark configurations."""

from __future__ import annotations

from typing import Any

from mimirbench.agents.model_client import Pricing
from mimirbench.agents.prompts import build_messages
from mimirbench.evals import registry
from mimirbench.evals.comparison_runner import ComparisonConfig
from mimirbench.evals.leaderboard import LeaderboardConfig, build_agent_config
from mimirbench.evals.schemas import (
    EnvironmentRunConfig,
    EvalConfig,
    EvalRunConfig,
    ReportingConfig,
    RobustnessRunConfig,
)

__all__ = [
    "estimate_comparison_cost",
    "estimate_eval_cost",
    "estimate_leaderboard_cost",
    "estimate_robustness_cost",
]


def _approximate_tokens(characters: int) -> int:
    return max(1, round(characters / 4))


def _calls_per_task(agent_type: str, agent_config: Any) -> tuple[int, bool]:
    """Return the call count and whether the agent uses a model."""
    if agent_type in {"reference", "mock"}:
        return 0, False
    if agent_type == "reflective":
        return 3, True
    if agent_type == "tool":
        policy = (getattr(agent_config, "tool_policy", "reference") or "reference").lower()
        if policy == "reference":
            return 0, False
        return int(getattr(agent_config, "tool_max_steps", 3)) + 1, True
    return 1, True


def estimate_eval_cost(config: EvalRunConfig | EvalConfig) -> dict[str, Any]:
    """Estimate task volume, token volume and configured upper-bound cost."""
    if isinstance(config, EvalConfig):
        environments = [(config.environment, config.n_tasks, config.seed)]
        agent_type = config.agent if isinstance(config.agent, str) else "reference"
        agent_config: Any = None
        system_prompt = None
        max_output = 1024
    else:
        environments = [
            (
                environment.name,
                environment.num_tasks,
                environment.seed if environment.seed is not None else config.run.seed,
            )
            for environment in config.environments
        ]
        agent_config = config.agent
        agent_type = config.agent.type.lower()
        system_prompt = config.agent.system_prompt
        max_output = (
            config.agent.max_new_tokens if agent_type == "local" else config.agent.max_tokens
        )

    calls_per_task, model_backed = _calls_per_task(agent_type, agent_config)
    per_environment: list[dict[str, Any]] = []
    total_tasks = 0
    estimated_input_tokens = 0
    for name, task_count, seed in environments:
        spec = registry.get(name)
        messages = build_messages(spec.generator(seed).task, system_prompt=system_prompt)
        tokens = _approximate_tokens(len(messages.system) + len(messages.user))
        per_environment.append(
            {
                "environment": name,
                "num_tasks": task_count,
                "input_tokens_per_task": tokens,
            }
        )
        total_tasks += task_count
        estimated_input_tokens += tokens * task_count

    total_input = estimated_input_tokens * calls_per_task
    total_output_upper = total_tasks * calls_per_task * max_output
    pricing = Pricing.from_mapping(getattr(agent_config, "pricing", None)) if agent_config else None

    cost_upper = None
    if pricing is not None and model_backed:
        cost_upper = round(
            total_input / 1000.0 * pricing.input_usd_per_1k
            + total_output_upper / 1000.0 * pricing.output_usd_per_1k,
            4,
        )

    return {
        "agent_type": agent_type,
        "model_backed": model_backed,
        "model_calls_per_task": calls_per_task,
        "total_tasks": total_tasks,
        "model_calls_total": total_tasks * calls_per_task,
        "est_total_input_tokens": total_input,
        "est_total_output_tokens_upper": total_output_upper,
        "pricing_configured": pricing is not None,
        "est_cost_usd_upper": cost_upper,
        "per_env": per_environment,
    }


def estimate_comparison_cost(config: ComparisonConfig) -> dict[str, Any]:
    """Estimate all agent cells in a comparison configuration."""
    agents: list[dict[str, Any]] = []
    for agent in config.agents:
        estimate = estimate_eval_cost(
            EvalRunConfig(
                run=config.run,
                agent=agent,
                environments=config.environments,
                reporting=config.reporting,
            )
        )
        estimate["agent_name"] = agent.name or agent.type
        agents.append(estimate)

    return {
        "comparison_name": config.run.name,
        "agents": agents,
        "total_tasks_per_agent": sum(environment.num_tasks for environment in config.environments),
        "model_calls_total": sum(int(agent["model_calls_total"]) for agent in agents),
        "est_total_input_tokens": sum(int(agent["est_total_input_tokens"]) for agent in agents),
        "est_total_output_tokens_upper": sum(
            int(agent["est_total_output_tokens_upper"]) for agent in agents
        ),
        "model_backed": any(bool(agent["model_backed"]) for agent in agents),
        "est_cost_usd_upper": _sum_optional_costs(agents),
    }


def estimate_leaderboard_cost(config: LeaderboardConfig) -> dict[str, Any]:
    """Estimate evaluation and optional robustness cells for a leaderboard."""
    cells: list[dict[str, Any]] = []
    robustness_modes = {
        mode.lower().strip() for mode in (config.robustness.agents or config.agents)
    }
    for model in config.models:
        for mode in config.agents:
            agent_config = build_agent_config(model, mode)
            estimate = estimate_eval_cost(
                EvalRunConfig(
                    run=config.run,
                    agent=agent_config,
                    environments=config.environments,
                    reporting=config.reporting,
                )
            )
            estimate.update(
                {
                    "model_label": model.label,
                    "provider": model.provider,
                    "agent_mode": mode,
                    "phase": "eval",
                }
            )
            cells.append(estimate)

            if config.robustness.enabled and mode.lower().strip() in robustness_modes:
                variant_count = config.robustness.max_variants_per_task
                robustness_environments = [
                    EnvironmentRunConfig(
                        name=environment.name,
                        num_tasks=environment.num_tasks * variant_count,
                        seed=environment.seed,
                    )
                    for environment in config.environments
                ]
                robustness_estimate = estimate_eval_cost(
                    EvalRunConfig(
                        run=config.run,
                        agent=agent_config,
                        environments=robustness_environments,
                        reporting=config.reporting,
                    )
                )
                robustness_estimate.update(
                    {
                        "model_label": model.label,
                        "provider": model.provider,
                        "agent_mode": mode,
                        "phase": "robustness",
                    }
                )
                cells.append(robustness_estimate)

    return {
        "leaderboard_name": config.run.name,
        "cells": cells,
        "base_tasks_per_cell": sum(environment.num_tasks for environment in config.environments),
        "model_calls_total": sum(int(cell["model_calls_total"]) for cell in cells),
        "est_total_input_tokens": sum(int(cell["est_total_input_tokens"]) for cell in cells),
        "est_total_output_tokens_upper": sum(
            int(cell["est_total_output_tokens_upper"]) for cell in cells
        ),
        "model_backed": any(bool(cell["model_backed"]) for cell in cells),
        "est_cost_usd_upper": _sum_optional_costs(cells),
        "robustness_enabled": config.robustness.enabled,
    }


def estimate_robustness_cost(config: RobustnessRunConfig) -> dict[str, Any]:
    """Estimate base and upper-bound variant volume for a robustness run."""
    robustness_environments = [
        EnvironmentRunConfig(
            name=environment.name,
            num_tasks=environment.num_tasks
            * (1 + min(environment.variants_per_task, config.robustness.max_variants_per_task)),
            seed=environment.seed,
        )
        for environment in config.environments
    ]
    estimate = estimate_eval_cost(
        EvalRunConfig(
            run=config.run,
            agent=config.agent,
            environments=robustness_environments,
            reporting=ReportingConfig(),
        )
    )
    estimate["robustness_base_tasks"] = sum(
        environment.num_tasks for environment in config.environments
    )
    estimate["robustness_variant_tasks_upper"] = sum(
        environment.num_tasks
        * min(environment.variants_per_task, config.robustness.max_variants_per_task)
        for environment in config.environments
    )
    return estimate


def _sum_optional_costs(estimates: list[dict[str, Any]]) -> float | None:
    numeric_costs = [
        float(cost)
        for estimate in estimates
        if isinstance((cost := estimate["est_cost_usd_upper"]), (int, float))
        and not isinstance(cost, bool)
    ]
    model_backed = [estimate for estimate in estimates if estimate["model_backed"]]
    if not model_backed or len(numeric_costs) != len(model_backed):
        return None
    return round(sum(numeric_costs), 4)
