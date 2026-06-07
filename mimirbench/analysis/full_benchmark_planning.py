"""No-execute planning for full-scale hosted-model leaderboard configs.

This module only parses configuration, generates representative synthetic tasks,
and performs arithmetic. It never checks provider availability, reads credentials,
imports provider SDKs, or runs inference.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from mimirbench.agents.model_client import Pricing
from mimirbench.agents.prompts import build_messages
from mimirbench.evals import registry
from mimirbench.evals.leaderboard import (
    LeaderboardConfig,
    LeaderboardModel,
    load_leaderboard_config,
)

__all__ = [
    "build_full_benchmark_plan",
    "format_cost_range",
    "validate_full_benchmark_config",
    "write_full_benchmark_plan",
]

_HOSTED_PROVIDERS = frozenset({"openai", "anthropic", "gemini", "generic_http"})
_FULL_TRACKS = frozenset({"strict-512", "best-valid"})
_REQUIRED_ENVIRONMENTS = frozenset(
    {
        "bayesian_games",
        "auctions",
        "hidden_regimes",
        "market_making",
        "prediction_markets",
        "adversarial_risk",
    }
)
_FULL_SCALES = {
    "full-a": (100, 3),
    "full-b": (200, 5),
}


def validate_full_benchmark_config(config: LeaderboardConfig) -> None:
    """Validate balanced full-scale protocol metadata without touching providers."""
    protocol = config.protocol
    if protocol is None:
        raise ValueError("full benchmark config requires a 'protocol' block.")
    if protocol.track not in _FULL_TRACKS:
        raise ValueError(f"unsupported full benchmark track: {protocol.track!r}.")
    expected_scale = _FULL_SCALES.get(protocol.scale)
    if expected_scale is None:
        raise ValueError(f"unsupported full benchmark scale: {protocol.scale!r}.")
    if (protocol.tasks_per_environment, len(protocol.task_seeds)) != expected_scale:
        raise ValueError(
            f"{protocol.scale} requires tasks_per_environment/seeds={expected_scale}, got "
            f"{protocol.tasks_per_environment}/{len(protocol.task_seeds)}."
        )
    if protocol.execution_status != "planned_not_run":
        raise ValueError("unrun hosted full configs must use execution_status='planned_not_run'.")
    if config.agents != ["direct"]:
        raise ValueError("full hosted-model protocol currently requires agents: [direct].")
    if config.robustness.enabled:
        raise ValueError("full hosted-model leaderboard configs must keep robustness disabled.")
    if len(set(protocol.task_seeds)) != len(protocol.task_seeds):
        raise ValueError("protocol.task_seeds must be unique.")
    for model in config.models:
        if model.provider.lower().strip() not in _HOSTED_PROVIDERS:
            raise ValueError(f"full hosted config contains non-hosted provider {model.provider!r}.")
        if protocol.track == "strict-512" and model.max_tokens != 512:
            raise ValueError(f"strict-512 model {model.label!r} must use max_tokens=512.")

    cells: dict[str, dict[int, int]] = defaultdict(dict)
    for environment in config.environments:
        registry.get(environment.name)
        seed = environment.seed if environment.seed is not None else config.run.seed
        if seed in cells[environment.name]:
            raise ValueError(f"duplicate environment/seed cell: {environment.name}/{seed}.")
        cells[environment.name][seed] = environment.num_tasks

    expected_seeds = set(protocol.task_seeds)
    if not cells:
        raise ValueError("full benchmark config requires environments.")
    if set(cells) != _REQUIRED_ENVIRONMENTS:
        raise ValueError(
            f"full benchmark environments must be exactly {sorted(_REQUIRED_ENVIRONMENTS)}."
        )
    for name, by_seed in cells.items():
        if set(by_seed) != expected_seeds:
            raise ValueError(
                f"{name} seeds {sorted(by_seed)} do not match protocol seeds "
                f"{sorted(expected_seeds)}."
            )
        if any(count != protocol.tasks_per_environment for count in by_seed.values()):
            raise ValueError(
                f"{name} must use {protocol.tasks_per_environment} tasks for every seed."
            )


def build_full_benchmark_plan(
    config_path: str | Path,
    *,
    command_prefix: str = "python -m mimirbench.cli",
) -> dict[str, Any]:
    """Build a deterministic no-execute plan for one full benchmark config."""
    path = Path(config_path)
    config = load_leaderboard_config(path)
    validate_full_benchmark_config(config)
    assert config.protocol is not None

    environment_rows = _environment_rows(config)
    tasks_per_model = sum(int(row["tasks"]) for row in environment_rows)
    output_dir = Path(
        config.run.output_dir or Path("reports") / "runs" / "leaderboard" / config.run.name
    )
    model_rows = [
        _model_plan(
            model,
            tasks_per_model=tasks_per_model,
            environment_rows=environment_rows,
            output_dir=output_dir,
        )
        for model in config.models
    ]
    scheduled_calls = sum(int(row["scheduled_calls"]) for row in model_rows)
    retry_upper = sum(int(row["retry_attempt_upper"]) for row in model_rows)
    input_tokens = sum(int(row["estimated_input_tokens"]) for row in model_rows)
    output_upper = sum(int(row["estimated_output_tokens_upper"]) for row in model_rows)
    cost_low, cost_high = _sum_cost_ranges(model_rows)
    exact_command = f"{command_prefix} run-leaderboard {path.as_posix()} --allow-real-models"

    return {
        "manifest_type": "mimirbench_full_benchmark_plan",
        "no_execute": True,
        "provider_calls_made": 0,
        "config_path": path.as_posix(),
        "leaderboard_name": config.run.name,
        "protocol": config.protocol.model_dump(mode="json"),
        "models": model_rows,
        "environments": environment_rows,
        "counts": {
            "models": len(config.models),
            "environments": len({row["environment"] for row in environment_rows}),
            "seeds": len(config.protocol.task_seeds),
            "tasks_per_environment_per_seed": config.protocol.tasks_per_environment,
            "tasks_per_model": tasks_per_model,
            "scheduled_model_calls": scheduled_calls,
            "retry_attempt_upper": retry_upper,
        },
        "token_estimate": {
            "input_tokens_approx": input_tokens,
            "output_tokens_range": [0, output_upper],
            "total_tokens_range": [input_tokens, input_tokens + output_upper],
        },
        "cost_estimate_usd": {
            "range": [cost_low, cost_high] if cost_low is not None and cost_high is not None else None,
            "formatted": format_cost_range(cost_low, cost_high),
            "basis": "configured pricing fields; input-only lower bound and max-output upper bound",
        },
        "artefacts": {
            "output_dir": output_dir.as_posix(),
            "leaderboard_summary": (output_dir / "leaderboard_summary.json").as_posix(),
            "leaderboard_report": (output_dir / "leaderboard_report.md").as_posix(),
            "headline_candidates": (output_dir / "headline_candidates.md").as_posix(),
            "paired_deltas": (output_dir / "paired_deltas.jsonl").as_posix(),
            "per_model_pattern": (output_dir / "models" / "<model>" / "agents" / "direct").as_posix(),
        },
        "exact_run_command": exact_command,
        "caveats": [
            "Planning only: no provider was contacted and no hosted-model result was generated.",
            "Token estimates use one representative synthetic prompt per environment and ~4 chars/token.",
            "Scheduled calls exclude retries; retry_attempt_upper assumes every call uses max_retries.",
            "Cost ranges use configured pricing fields and exclude taxes, provider changes, and cache effects.",
        ],
    }


def write_full_benchmark_plan(
    config_path: str | Path,
    *,
    output_dir: str | Path = Path("reports") / "plans",
) -> Path:
    """Write a no-execute JSON manifest and return its path."""
    plan = build_full_benchmark_plan(config_path)
    path = Path(output_dir) / f"{Path(config_path).stem}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def format_cost_range(low: float | None, high: float | None) -> str:
    """Format an estimated USD range without implying false precision."""
    if low is None or high is None:
        return "not estimated (pricing fields missing)"
    return f"${low:,.2f}-${high:,.2f} USD"


def _environment_rows(config: LeaderboardConfig) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for environment in config.environments:
        seed = environment.seed if environment.seed is not None else config.run.seed
        spec = registry.get(environment.name)
        bundle = build_messages(spec.generator(seed).task)
        rows.append(
            {
                "environment": environment.name,
                "seed": seed,
                "tasks": environment.num_tasks,
                "representative_input_tokens_approx": _approx_tokens(
                    len(bundle.system) + len(bundle.user)
                ),
            }
        )
    return rows


def _model_plan(
    model: LeaderboardModel,
    *,
    tasks_per_model: int,
    environment_rows: list[dict[str, Any]],
    output_dir: Path,
) -> dict[str, Any]:
    input_tokens = sum(
        int(row["tasks"]) * int(row["representative_input_tokens_approx"])
        for row in environment_rows
    )
    output_upper = tasks_per_model * model.max_tokens
    pricing = Pricing.from_mapping(model.pricing)
    cost_low: float | None = None
    cost_high: float | None = None
    if pricing is not None:
        cost_low = input_tokens / 1000.0 * pricing.input_usd_per_1k
        cost_high = cost_low + output_upper / 1000.0 * pricing.output_usd_per_1k
        cost_low = round(cost_low, 4)
        cost_high = round(cost_high, 4)
    artefact_dir = output_dir / "models" / _slug(model.label) / "agents" / "direct"
    return {
        "label": model.label,
        "provider": model.provider,
        "model": model.model,
        "scheduled_calls": tasks_per_model,
        "retry_attempt_upper": tasks_per_model * model.max_retries,
        "estimated_input_tokens": input_tokens,
        "estimated_output_tokens_upper": output_upper,
        "configured_max_tokens": model.max_tokens,
        "configured_max_retries": model.max_retries,
        "cost_range_usd": [cost_low, cost_high] if cost_low is not None else None,
        "cost_range_formatted": format_cost_range(cost_low, cost_high),
        "artefacts": {
            "output_dir": artefact_dir.as_posix(),
            "results": (artefact_dir / "results.jsonl").as_posix(),
            "summary": (artefact_dir / "summary.json").as_posix(),
            "report": (artefact_dir / "report.md").as_posix(),
        },
    }


def _sum_cost_ranges(rows: list[dict[str, Any]]) -> tuple[float | None, float | None]:
    ranges = [row["cost_range_usd"] for row in rows]
    if any(value is None for value in ranges):
        return None, None
    lows = [float(value[0]) for value in ranges if value is not None]
    highs = [float(value[1]) for value in ranges if value is not None]
    return round(sum(lows), 4), round(sum(highs), 4)


def _approx_tokens(chars: int) -> int:
    return max(1, round(chars / 4))


def _slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value).strip("_").lower()
