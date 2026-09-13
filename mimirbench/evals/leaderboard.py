"""Run paired real-model benchmarks and assemble leaderboard summaries.

Unavailable providers are recorded as pending. Evaluations align identical
task IDs, while robustness comparisons align parent tasks and variants.
Findings are emitted only when their supporting metrics exist.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

import mimirbench.evals.registry as registry
from mimirbench.agents.providers import provider_status
from mimirbench.agents.resolver import resolve_agent as resolve_agent_from_config
from mimirbench.artefacts import artefact_path, make_run_id, utc_timestamp, write_json, write_jsonl
from mimirbench.evals.comparison_runner import agent_baseline_kind
from mimirbench.evals.robustness_runner import run_robustness_config
from mimirbench.evals.runner import run_eval_config
from mimirbench.evals.schemas import (
    AgentConfig,
    EnvironmentRunConfig,
    EvalRunConfig,
    EvalTaskRecord,
    ReportingConfig,
    RobustnessEnvironmentConfig,
    RobustnessOptions,
    RobustnessRunConfig,
    RunSettings,
)
from mimirbench.evals.scoring import is_risk_violation
from mimirbench.evals.writers import (
    load_records_jsonl,
    load_robustness_records_jsonl,
)

__all__ = [
    "AGENT_MODES",
    "LeaderboardConfig",
    "LeaderboardModel",
    "LeaderboardProtocol",
    "LeaderboardRobustness",
    "build_agent_config",
    "load_leaderboard_config",
    "run_leaderboard_config",
    "summarise_leaderboard",
    "validate_leaderboard_config",
]

# The three agent modes the leaderboard pairs against each other.
AGENT_MODES: tuple[str, ...] = ("direct", "tool", "reflective")
_MODEL_BACKED_RESULT_LABELS: frozenset[str] = frozenset(
    {"real API model", "real local model"}
)

# --------------------------------------------------------------------------- #
# Config schema
# --------------------------------------------------------------------------- #
class LeaderboardModel(BaseModel):
    """One model entry in a leaderboard config.

    ``provider`` selects the backend (``openai``, ``anthropic``, ``gemini``,
    ``generic_http``, ``local``, or the non-model ``reference`` / ``mock``
    baselines used for offline smoke runs). ``model`` is the hosted model id;
    ``model_name`` is the local checkpoint/HF id. The API key is never placed
    here - only the env-var *name* via ``api_key_env``.
    """

    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    name: str | None = None
    provider: str
    model: str | None = None
    model_name: str | None = None
    behaviour: str | None = None
    seed: int = 0
    temperature: float = 0.0
    top_p: float | None = None
    request_extra: dict[str, Any] = Field(default_factory=dict)
    do_sample: bool | None = None
    max_tokens: int = Field(default=512, ge=1)
    max_new_tokens: int = Field(default=512, ge=1)
    max_retries: int = Field(default=3, ge=1)
    timeout_seconds: float | None = Field(default=60.0, gt=0)
    base_url: str | None = None
    api_key_env: str | None = None
    device: str | None = None
    pricing: dict[str, float] | None = None
    system_prompt: str | None = None
    tool_max_steps: int = Field(default=3, ge=1)
    allowed_tools: list[str] | None = None
    require_tool_first: bool = False

    @property
    def label(self) -> str:
        """A stable display label for this model."""
        if self.name:
            return self.name
        backend = self.model or self.model_name or self.behaviour or "model"
        return f"{self.provider.lower().strip()}_{backend}"


class LeaderboardRobustness(BaseModel):
    """Robustness sub-run options for the leaderboard."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    agents: list[str] | None = None  # which modes get a robustness run; None = all
    variants_per_task: int = Field(default=4, ge=1)
    max_variants_per_task: int = Field(default=4, ge=1)
    answer_preserving_only: bool = False
    variant_types: dict[str, list[str]] = Field(default_factory=dict)


class LeaderboardProtocol(BaseModel):
    """Optional metadata for a planned benchmark protocol.

    The ordinary leaderboard runner ignores this metadata. Planning tools use it
    to verify that repeated environment entries form a balanced multi-seed run.
    """

    model_config = ConfigDict(extra="forbid")

    track: str
    scale: str
    tasks_per_environment: int = Field(ge=1)
    task_seeds: list[int] = Field(min_length=1)
    execution_status: str = "planned_not_run"


class LeaderboardConfig(BaseModel):
    """Top-level configuration for a paired real-model leaderboard run."""

    model_config = ConfigDict(extra="forbid")

    run: RunSettings
    protocol: LeaderboardProtocol | None = None
    models: list[LeaderboardModel] = Field(min_length=1)
    agents: list[str] = Field(default_factory=lambda: list(AGENT_MODES))
    environments: list[EnvironmentRunConfig] = Field(min_length=1)
    robustness: LeaderboardRobustness = Field(default_factory=LeaderboardRobustness)
    reporting: ReportingConfig = Field(default_factory=ReportingConfig)


def load_leaderboard_config(path: Path) -> LeaderboardConfig:
    """Load a leaderboard config from YAML."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"leaderboard config {path} must contain a YAML mapping.")
    return LeaderboardConfig(**data)


def validate_leaderboard_config(config: LeaderboardConfig) -> None:
    """Validate registry references, agent modes, and agent construction.

    This does *not* check provider availability (a config is valid even with no
    keys present) and does *not* run any task or import any model SDK.
    """
    if not config.environments:
        raise ValueError("leaderboard config must include at least one environment.")
    if not config.agents:
        raise ValueError("leaderboard config must include at least one agent mode.")
    for mode in config.agents:
        if mode.lower().strip() not in AGENT_MODES:
            raise ValueError(
                f"unknown agent mode {mode!r}. Expected one of: {', '.join(AGENT_MODES)}."
            )
    robustness_agents = config.robustness.agents or config.agents
    for mode in robustness_agents:
        if mode.lower().strip() not in AGENT_MODES:
            raise ValueError(f"unknown robustness agent mode {mode!r}.")

    specs = [registry.get(env.name) for env in config.environments]
    first_spec = specs[0]
    labels = [model.label for model in config.models]
    if len(set(labels)) != len(labels):
        raise ValueError(f"model labels must be unique; got duplicates in {labels}.")
    for model in config.models:
        for mode in config.agents:
            agent_config = build_agent_config(model, mode)
            resolve_agent_from_config(agent_config, spec=first_spec)


# --------------------------------------------------------------------------- #
# Agent-config construction (provider + mode -> AgentConfig)
# --------------------------------------------------------------------------- #
def build_agent_config(model: LeaderboardModel, mode: str) -> AgentConfig:
    """Map a model entry and an agent mode to a concrete :class:`AgentConfig`.

    Non-model providers (``reference`` / ``mock``) collapse all modes to their
    single deterministic baseline; the mode is still kept in the agent name so the
    runs remain distinct rows. Real providers map ``direct`` / ``tool`` /
    ``reflective`` onto the existing model-backed agent types.
    """
    mode = mode.lower().strip()
    if mode not in AGENT_MODES:
        raise ValueError(f"unknown agent mode {mode!r}.")
    provider = model.provider.lower().strip()
    name = f"{model.label}::{mode}"

    if provider == "reference":
        return AgentConfig(type="reference", name=name)
    if provider == "mock":
        return AgentConfig(
            type="mock",
            behaviour=model.behaviour or "random_valid",
            seed=model.seed,
            name=name,
        )

    is_local = provider == "local" or (model.model_name is not None and model.model is None)
    common: dict[str, Any] = {
        "name": name,
        "temperature": model.temperature,
        "top_p": model.top_p,
        "request_extra": model.request_extra,
        "max_retries": model.max_retries,
        "timeout_seconds": model.timeout_seconds,
        "max_tokens": model.max_tokens,
        "max_new_tokens": model.max_new_tokens,
        "system_prompt": model.system_prompt,
        "seed": model.seed,
    }
    if is_local:
        if not model.model_name:
            raise ValueError(f"local model {model.label!r} requires 'model_name'.")
        backend: dict[str, Any] = {
            **common,
            "model_name": model.model_name,
            "device": model.device,
            "do_sample": model.do_sample,
        }
    else:
        if not model.model:
            raise ValueError(f"model {model.label!r} (provider {provider!r}) requires 'model'.")
        backend = {
            **common,
            "provider": provider,
            "model": model.model,
            "base_url": model.base_url,
            "api_key_env": model.api_key_env,
            "pricing": model.pricing,
        }

    if mode == "direct":
        return AgentConfig(type="direct", **backend)
    if mode == "reflective":
        return AgentConfig(type="reflective", **backend)
    # tool mode
    return AgentConfig(
        type="tool",
        tool_policy="model",
        tool_max_steps=model.tool_max_steps,
        allowed_tools=model.allowed_tools,
        require_tool_first=model.require_tool_first,
        **backend,
    )


# --------------------------------------------------------------------------- #
# Runner
# --------------------------------------------------------------------------- #
def run_leaderboard_config(
    config: LeaderboardConfig,
    *,
    allow_unavailable: bool = False,
    allow_real_models: bool = False,
) -> dict[str, Any]:
    """Run a paired leaderboard and write artefacts; return the summary payload.

    Real API/local models are only run when their provider reports usable *and*
    ``allow_real_models`` is true. Reference/mock diagnostic baselines may run
    without that permission. ``allow_unavailable`` is reserved for offline
    diagnostics and never overrides provider checks for real API/local models.
    """
    validate_leaderboard_config(config)
    output_dir = _output_dir(config)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = utc_timestamp()
    run_id = make_run_id(config.run.name, timestamp)
    robustness_modes = {
        mode.lower().strip() for mode in (config.robustness.agents or config.agents)
    }

    availability = {
        model.label: provider_status(
            model.provider,
            base_url=model.base_url,
            api_key_env=model.api_key_env,
            model=model.model or model.model_name or "probe",
        )
        for model in config.models
    }

    model_payloads: list[dict[str, Any]] = []
    leaderboard_rows: list[dict[str, Any]] = []
    paired_rows: list[dict[str, Any]] = []
    paired_metrics: dict[str, Any] = {}
    pending_models: list[dict[str, Any]] = []

    for model in config.models:
        status = availability[model.label]
        model_dir = output_dir / "models" / _slug(model.label)
        result_label = _model_result_label(model)
        real_model = result_label in _MODEL_BACKED_RESULT_LABELS
        can_run = (
            status.usable and allow_real_models
            if real_model
            else status.usable or allow_unavailable
        )
        if not can_run:
            detail = status.detail
            if real_model and status.usable and not allow_real_models:
                detail = (
                    "provider appears usable, but real model execution requires explicit "
                    "permission via the CLI --allow-real-models flag or allow_real_models=True."
                )
            pending_models.append(
                {
                    "label": model.label,
                    "provider": status.provider,
                    "detail": detail,
                    "key_env": status.key_env,
                }
            )
            continue

        agent_records: dict[str, list[EvalTaskRecord]] = {}
        agent_summaries: dict[str, dict[str, Any]] = {}
        robustness_summaries: dict[str, dict[str, Any]] = {}

        for mode in config.agents:
            agent_config = build_agent_config(model, mode)
            run_dir = model_dir / "agents" / mode
            eval_config = EvalRunConfig(
                run=config.run.model_copy(
                    update={
                        "name": f"{config.run.name}__{_slug(model.label)}__{mode}",
                        "output_dir": artefact_path(run_dir),
                    }
                ),
                agent=agent_config,
                environments=config.environments,
                reporting=config.reporting,
            )
            summary = run_eval_config(eval_config)
            summary["baseline_kind"] = agent_baseline_kind(agent_config)
            agent_summaries[mode] = summary
            agent_records[mode] = load_records_jsonl(run_dir / "results.jsonl")

            if config.robustness.enabled and mode in robustness_modes:
                rob_summary = _run_robustness_cell(
                    config, model, mode, model_dir / "robustness" / mode
                )
                robustness_summaries[mode] = rob_summary

            leaderboard_rows.append(
                _leaderboard_row(
                    model=model,
                    mode=mode,
                    summary=summary,
                    records=agent_records[mode],
                    robustness=robustness_summaries.get(mode),
                )
            )

        model_paired_rows, model_paired_metrics = _paired_for_model(
            model_label=model.label,
            records_by_mode=agent_records,
            robustness_by_mode=robustness_summaries,
        )
        paired_rows.extend(model_paired_rows)
        if model_paired_metrics:
            paired_metrics[model.label] = model_paired_metrics

        model_payloads.append(
            {
                "label": model.label,
                "provider": status.provider,
                "usable": status.usable,
                "result_label": _model_result_label(model),
                "agent_modes": list(config.agents),
                "agents": {mode: _agent_payload(agent_summaries[mode]) for mode in config.agents},
                "robustness": {
                    mode: _robustness_payload(summary)
                    for mode, summary in robustness_summaries.items()
                },
                "model_dir": artefact_path(model_dir),
            }
        )

    paired_path = output_dir / "paired_deltas.jsonl"
    write_jsonl(paired_rows, paired_path)

    summary_payload: dict[str, Any] = {
        "leaderboard_name": config.run.name,
        "run_id": run_id,
        "timestamp": timestamp,
        "output_dir": artefact_path(output_dir),
        "preliminary": _is_preliminary(config),
        "real_execution_permitted": allow_real_models,
        "agent_modes": list(config.agents),
        "environments": [
            {
                "name": env.name,
                "num_tasks": env.num_tasks,
                "seed": env.seed if env.seed is not None else config.run.seed,
            }
            for env in config.environments
        ],
        "tasks_per_agent": sum(env.num_tasks for env in config.environments),
        "provider_availability": {
            label: status.to_dict() for label, status in availability.items()
        },
        "models_run": model_payloads,
        "models_pending": pending_models,
        "leaderboard": leaderboard_rows,
        "paired_metrics": paired_metrics,
        "caveats": _leaderboard_caveats(model_payloads, config),
        "artefacts": {
            "leaderboard_summary": artefact_path(output_dir / "leaderboard_summary.json"),
            "leaderboard_report": artefact_path(output_dir / "leaderboard_report.md"),
            "paired_deltas": artefact_path(paired_path),
        },
    }
    write_json(summary_payload, output_dir / "leaderboard_summary.json")
    _write_leaderboard_report(summary_payload, output_dir / "leaderboard_report.md")
    return summary_payload


def summarise_leaderboard(run_dir: Path) -> dict[str, Any]:
    """Read an existing leaderboard summary from ``run_dir``."""
    path = run_dir / "leaderboard_summary.json"
    if not path.exists():
        raise FileNotFoundError(f"no leaderboard_summary.json found at {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"leaderboard_summary.json at {path} is not a JSON object.")
    return data


# --------------------------------------------------------------------------- #
# Robustness cell
# --------------------------------------------------------------------------- #
def _run_robustness_cell(
    config: LeaderboardConfig,
    model: LeaderboardModel,
    mode: str,
    run_dir: Path,
) -> dict[str, Any]:
    agent_config = build_agent_config(model, mode)
    rob_envs = [
        RobustnessEnvironmentConfig(
            name=env.name,
            num_tasks=env.num_tasks,
            seed=env.seed,
            variants_per_task=config.robustness.variants_per_task,
            variant_types=config.robustness.variant_types.get(env.name, []),
        )
        for env in config.environments
    ]
    rob_config = RobustnessRunConfig(
        run=config.run.model_copy(
            update={
                "name": f"{config.run.name}__{_slug(model.label)}__{mode}__robustness",
                "output_dir": artefact_path(run_dir),
            }
        ),
        agent=agent_config,
        environments=rob_envs,
        robustness=RobustnessOptions(
            answer_preserving_only=config.robustness.answer_preserving_only,
            max_variants_per_task=config.robustness.max_variants_per_task,
        ),
    )
    return run_robustness_config(rob_config)


# --------------------------------------------------------------------------- #
# Leaderboard row + payload helpers
# --------------------------------------------------------------------------- #
def _leaderboard_row(
    *,
    model: LeaderboardModel,
    mode: str,
    summary: dict[str, Any],
    records: list[EvalTaskRecord],
    robustness: dict[str, Any] | None,
) -> dict[str, Any]:
    overall = summary["metrics"]["overall"]
    cost_latency = summary.get("cost_latency", {})
    rob_metrics = (robustness or {}).get("metrics", {})
    return {
        "model": model.label,
        "provider": model.provider.lower().strip(),
        "agent": mode,
        "result_label": summary.get("baseline_kind", _model_result_label(model)),
        "n_envs": len(summary.get("environments", [])),
        "n_tasks": overall.get("n_tasks"),
        "mean_score": overall.get("mean_score"),
        "robustness_paraphrase_consistency": rob_metrics.get("paraphrase_consistency_rate"),
        "robustness_mean_score_drop": rob_metrics.get("mean_score_drop"),
        "risk_violation_rate": _risk_violation_rate(records),
        "parse_failure_rate": overall.get("parse_failure_rate"),
        "estimated_cost_usd": cost_latency.get("estimated_total_cost_usd"),
        "cost_estimated": cost_latency.get("cost_estimated", False),
        "latency_p50_ms": overall.get("latency_p50_ms"),
        "latency_p95_ms": overall.get("latency_p95_ms"),
    }


def _agent_payload(summary: dict[str, Any]) -> dict[str, Any]:
    overall = summary["metrics"]["overall"]
    return {
        "run_id": summary["run_id"],
        "run_name": summary["run_name"],
        "output_dir": summary["output_dir"],
        "baseline_kind": summary.get("baseline_kind"),
        "n_tasks": overall.get("n_tasks"),
        "mean_score": overall.get("mean_score"),
        "parse_failure_rate": overall.get("parse_failure_rate"),
        "latency_p50_ms": overall.get("latency_p50_ms"),
        "latency_p95_ms": overall.get("latency_p95_ms"),
        "cost_latency": summary.get("cost_latency", {}),
    }


def _robustness_payload(summary: dict[str, Any]) -> dict[str, Any]:
    metrics = summary.get("metrics", {})
    return {
        "output_dir": summary.get("output_dir"),
        "n_base_tasks": summary.get("counts", {}).get("n_base_tasks"),
        "n_variants": summary.get("counts", {}).get("n_variants"),
        "paraphrase_consistency_rate": metrics.get("paraphrase_consistency_rate"),
        "mean_score_drop": metrics.get("mean_score_drop"),
        "action_flip_rate": metrics.get("action_flip_rate"),
    }


def _model_result_label(model: LeaderboardModel) -> str:
    provider = model.provider.lower().strip()
    if provider == "reference":
        return "reference sanity check"
    if provider == "mock":
        return "mock diagnostic baseline"
    if provider == "local":
        return "real local model"
    return "real API model"


# --------------------------------------------------------------------------- #
# Paired comparison (within a model, across agent modes)
# --------------------------------------------------------------------------- #
def _paired_for_model(
    *,
    model_label: str,
    records_by_mode: dict[str, list[EvalTaskRecord]],
    robustness_by_mode: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Build paired rows + aggregated metrics for every ordered mode pair."""
    rows: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}
    modes = [mode for mode in AGENT_MODES if mode in records_by_mode]
    for baseline_mode, candidate_mode in _mode_pairs(modes):
        pair_key = f"{candidate_mode}_vs_{baseline_mode}"
        eval_rows = _eval_pair_rows(
            model_label=model_label,
            baseline_mode=baseline_mode,
            candidate_mode=candidate_mode,
            baseline=records_by_mode[baseline_mode],
            candidate=records_by_mode[candidate_mode],
        )
        rob_rows = _robustness_pair_rows(
            model_label=model_label,
            baseline_mode=baseline_mode,
            candidate_mode=candidate_mode,
            baseline_dir=robustness_by_mode.get(baseline_mode, {}).get("output_dir"),
            candidate_dir=robustness_by_mode.get(candidate_mode, {}).get("output_dir"),
        )
        rows.extend(eval_rows)
        rows.extend(rob_rows)
        metrics[pair_key] = _aggregate_pair_metrics(
            eval_rows,
            rob_rows,
            baseline_robustness=robustness_by_mode.get(baseline_mode),
            candidate_robustness=robustness_by_mode.get(candidate_mode),
        )
    return rows, metrics


def _mode_pairs(modes: list[str]) -> list[tuple[str, str]]:
    """Ordered (baseline, candidate) mode pairs, ``direct`` preferred as baseline."""
    pairs: list[tuple[str, str]] = []
    for i, baseline in enumerate(modes):
        for candidate in modes[i + 1 :]:
            pairs.append((baseline, candidate))
    return pairs


def _eval_pair_rows(
    *,
    model_label: str,
    baseline_mode: str,
    candidate_mode: str,
    baseline: list[EvalTaskRecord],
    candidate: list[EvalTaskRecord],
) -> list[dict[str, Any]]:
    baseline_by_key = {(r.environment, r.task_id, r.seed): r for r in baseline}
    rows: list[dict[str, Any]] = []
    for cand in candidate:
        base = baseline_by_key.get((cand.environment, cand.task_id, cand.seed))
        if base is None:
            continue
        base_values = _task_values(base)
        cand_values = _task_values(cand)
        rows.append(
            {
                "kind": "eval",
                "model": model_label,
                "pair": f"{candidate_mode}_vs_{baseline_mode}",
                "baseline_mode": baseline_mode,
                "candidate_mode": candidate_mode,
                "environment": cand.environment,
                "task_id": cand.task_id,
                "variant_id": None,
                "seed": cand.seed,
                "baseline": base_values,
                "candidate": cand_values,
                "deltas": _delta_map(cand_values, base_values),
            }
        )
    return rows


def _robustness_pair_rows(
    *,
    model_label: str,
    baseline_mode: str,
    candidate_mode: str,
    baseline_dir: str | None,
    candidate_dir: str | None,
) -> list[dict[str, Any]]:
    if not baseline_dir or not candidate_dir:
        return []
    baseline = load_robustness_records_jsonl(Path(baseline_dir) / "robustness_results.jsonl")
    candidate = load_robustness_records_jsonl(Path(candidate_dir) / "robustness_results.jsonl")
    baseline_by_key = {
        (r.environment, r.parent_task_id, r.seed, r.variant_id): r for r in baseline
    }
    rows: list[dict[str, Any]] = []
    for cand in candidate:
        key = (cand.environment, cand.parent_task_id, cand.seed, cand.variant_id)
        base = baseline_by_key.get(key)
        if base is None:
            continue
        base_values = {"variant_score": base.variant_score, "score_delta": base.score_delta}
        cand_values = {"variant_score": cand.variant_score, "score_delta": cand.score_delta}
        rows.append(
            {
                "kind": "robustness",
                "model": model_label,
                "pair": f"{candidate_mode}_vs_{baseline_mode}",
                "baseline_mode": baseline_mode,
                "candidate_mode": candidate_mode,
                "environment": cand.environment,
                "task_id": cand.parent_task_id,
                "variant_id": cand.variant_id,
                "seed": cand.seed,
                "baseline": base_values,
                "candidate": cand_values,
                "deltas": _delta_map(cand_values, base_values),
            }
        )
    return rows


def _task_values(record: EvalTaskRecord) -> dict[str, float | None]:
    result = record.grader_result
    return {
        "score": result.score,
        "regret": _metric(result.metrics, ("regret",)),
        "posterior_error": _metric(
            result.metrics,
            ("posterior_tv_error", "posterior_l1_error", "posterior_max_error"),
        ),
        "risk_violation": 1.0 if is_risk_violation(result) else 0.0,
        "parse_failure": 1.0 if record.parsed_response is None else 0.0,
        "latency_ms": record.latency_ms,
        "estimated_cost_usd": _estimated_cost(record),
    }


def _delta_map(
    candidate: Mapping[str, float | None],
    baseline: Mapping[str, float | None],
) -> dict[str, float | None]:
    return {
        f"{name}_difference": _difference(candidate.get(name), baseline.get(name))
        for name in baseline
    }


def _aggregate_pair_metrics(
    eval_rows: list[dict[str, Any]],
    robustness_rows: list[dict[str, Any]],
    *,
    baseline_robustness: dict[str, Any] | None,
    candidate_robustness: dict[str, Any] | None,
) -> dict[str, Any]:
    summary: dict[str, Any] = {"n_pairs": len(eval_rows)}
    deltas = [row["deltas"] for row in eval_rows]
    for field in sorted({name for delta in deltas for name in delta}):
        summary[f"mean_{field}"] = _mean_numeric(delta.get(field) for delta in deltas)

    summary["n_robustness_pairs"] = len(robustness_rows)
    if robustness_rows:
        rob_deltas = [row["deltas"] for row in robustness_rows]
        summary["mean_variant_score_difference"] = _mean_numeric(
            delta.get("variant_score_difference") for delta in rob_deltas
        )
    # Aggregate robustness *score drop* delta from the two robustness summaries
    # (candidate minus baseline). Lower mean_score_drop is more robust.
    base_drop = (baseline_robustness or {}).get("metrics", {}).get("mean_score_drop")
    cand_drop = (candidate_robustness or {}).get("metrics", {}).get("mean_score_drop")
    summary["robustness_score_drop_difference"] = _difference(cand_drop, base_drop)
    return summary


# --------------------------------------------------------------------------- #
# Writers
# --------------------------------------------------------------------------- #
def _write_leaderboard_report(summary: dict[str, Any], path: Path) -> None:
    lines = [
        f"# Leaderboard report: {summary['leaderboard_name']}",
        "",
        f"- Run ID: `{summary['run_id']}`",
        f"- Timestamp: `{summary['timestamp']}`",
        f"- Agent modes: {', '.join(summary['agent_modes'])}",
        f"- Tasks per agent: `{summary['tasks_per_agent']}`",
        f"- Pilot-scale run: **{'yes' if summary['preliminary'] else 'no'}**",
        f"- Real model execution permitted: **{'yes' if summary.get('real_execution_permitted') else 'no'}**",
        "",
        "## Provider availability",
        "",
        "| Model | Provider | Usable | Detail |",
        "| --- | --- | :---: | --- |",
    ]
    for label, status in summary["provider_availability"].items():
        lines.append(
            f"| {label} | {status['provider']} | {'yes' if status['usable'] else 'no'} | "
            f"{status['detail']} |"
        )

    if summary["models_pending"]:
        lines.extend(["", "## Models pending (not run)", ""])
        for pending in summary["models_pending"]:
            lines.append(f"- `{pending['label']}` ({pending['provider']}): {pending['detail']}")

    lines.extend(
        [
            "",
            "## Leaderboard",
            "",
            "| Model | Provider | Agent | Envs | Tasks | Mean score | Robustness (consist./drop) | "
            "Risk violation | Parse failure | Cost | Latency p50/p95 |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    if not summary["leaderboard"]:
        lines.append(
            "| _no models were run (see provider availability above)_ |  |  |  |  |  |  |  |  |  |  |"
        )
    for row in summary["leaderboard"]:
        robustness = (
            f"{_fmt(row['robustness_paraphrase_consistency'])}/"
            f"{_fmt(row['robustness_mean_score_drop'])}"
        )
        lines.append(
            "| "
            f"{row['model']} | {row['provider']} | {row['agent']} | {_fmt(row['n_envs'])} | "
            f"{_fmt(row['n_tasks'])} | {_fmt(row['mean_score'])} | {robustness} | "
            f"{_fmt(row['risk_violation_rate'])} | {_fmt(row['parse_failure_rate'])} | "
            f"{_cost_cell(row)} | {_fmt(row['latency_p50_ms'])}/{_fmt(row['latency_p95_ms'])} |"
        )

    lines.extend(["", "## Paired deltas (candidate minus baseline, identical task IDs)", ""])
    if not summary["paired_metrics"]:
        lines.append("No paired deltas (need at least two agent modes per model).")
    for model_label, pairs in summary["paired_metrics"].items():
        lines.extend(["", f"### {model_label}", ""])
        lines.append(
            "| Pair | Pairs | Score | Posterior error | Risk viol. | Parse fail | "
            "Latency ms | Cost USD | Robustness drop |"
        )
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
        for pair_key, metrics in pairs.items():
            lines.append(
                "| "
                f"`{pair_key}` | {metrics['n_pairs']} | "
                f"{_fmt(metrics.get('mean_score_difference'))} | "
                f"{_fmt(metrics.get('mean_posterior_error_difference'))} | "
                f"{_fmt(metrics.get('mean_risk_violation_difference'))} | "
                f"{_fmt(metrics.get('mean_parse_failure_difference'))} | "
                f"{_fmt(metrics.get('mean_latency_ms_difference'))} | "
                f"{_fmt(metrics.get('mean_estimated_cost_usd_difference'))} | "
                f"{_fmt(metrics.get('robustness_score_drop_difference'))} |"
            )

    lines.extend(["", "## Scope", ""])
    for caveat in summary.get("caveats", []):
        lines.append(f"- {caveat}")

    lines.extend(
        [
            "",
            "## Artefacts",
            "",
            f"- `leaderboard_summary.json`: `{summary['artefacts']['leaderboard_summary']}`",
            f"- `paired_deltas.jsonl`: `{summary['artefacts']['paired_deltas']}`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


# --------------------------------------------------------------------------- #
# Misc helpers
# --------------------------------------------------------------------------- #
def _leaderboard_caveats(
    model_payloads: list[dict[str, Any]],
    config: LeaderboardConfig,
) -> list[str]:
    caveats = [
        "All paired deltas are candidate minus baseline on identical task IDs "
        "(and identical variant IDs for robustness).",
        "Higher mean score is better; lower posterior error, risk violations, "
        "parse failures, latency, cost, and robustness score drop are better.",
        "Cost is reported only when pricing was configured; otherwise it is 'not estimated'.",
        "Results cover only the configured synthetic tasks and model settings.",
    ]
    if _is_preliminary(config):
        caveats.append(
            "This is a pilot hosted-model run (<= a handful of tasks per environment); "
            "full-scale confirmation is required for broader conclusions."
        )
    if not model_payloads:
        caveats.append(
            "No model-performance rows were produced in this run."
        )
    if any(p["result_label"] not in _MODEL_BACKED_RESULT_LABELS for p in model_payloads):
        caveats.append(
            "Reference and mock rows are non-model baselines and must not be "
            "described as model performance."
        )
    return caveats


def _is_preliminary(config: LeaderboardConfig) -> bool:
    return all(env.num_tasks <= 20 for env in config.environments)


def _risk_violation_rate(records: list[EvalTaskRecord]) -> float | None:
    if not records:
        return None
    return sum(1 for r in records if is_risk_violation(r.grader_result)) / len(records)


def _metric(metrics: dict[str, float], names: tuple[str, ...]) -> float | None:
    for name in names:
        value = metrics.get(name)
        if value is not None:
            return float(value)
    return None


def _estimated_cost(record: EvalTaskRecord) -> float | None:
    response_metadata = record.metadata.get("response_metadata")
    if not isinstance(response_metadata, dict):
        return None
    usage = response_metadata.get("usage")
    if not isinstance(usage, dict):
        return None
    value = usage.get("estimated_cost_usd")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _difference(candidate: float | None, baseline: float | None) -> float | None:
    if candidate is None or baseline is None:
        return None
    return candidate - baseline


def _mean_numeric(values: Iterable[Any]) -> float | None:
    numeric = [
        float(value)
        for value in values
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    ]
    return sum(numeric) / len(numeric) if numeric else None


def _cost_cell(row: dict[str, Any]) -> str:
    if row.get("cost_estimated") and row.get("estimated_cost_usd") is not None:
        return f"${row['estimated_cost_usd']}"
    return "not estimated"


def _output_dir(config: LeaderboardConfig) -> Path:
    if config.run.output_dir:
        return Path(config.run.output_dir)
    return Path("reports") / "runs" / "leaderboard" / config.run.name


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip()).strip("_.-")
    return slug.lower() or "model"


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, float)):
        return f"{value:.6g}"
    return str(value)
