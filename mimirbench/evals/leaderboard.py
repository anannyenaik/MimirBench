"""Real-model leaderboard pipeline.

The leaderboard runs *paired* benchmarks on identical task IDs for a set of agent
modes (``direct``, ``tool``, ``reflective``) across one or more configured
models, then produces an honest leaderboard with cost, latency, robustness, and
failure summaries.

Design rules (the same honesty contract used elsewhere in MimirBench):

* **Never fabricate.** A model is only run when its provider reports as usable
  (package present + key present). Unusable models are recorded as ``pending`` -
  the infrastructure ran, but no numbers are invented.
* **Reuse the existing runners.** Each (model, agent-mode) cell is an ordinary
  Stage 2 :func:`run_eval_config` run, and robustness cells are ordinary
  :func:`run_robustness_config` runs. Downstream tooling reads the same
  ``results.jsonl`` / ``summary.json`` it already understands.
* **Pairing is explicit.** Deltas are aligned by ``(environment, task_id, seed)``
  for eval tasks and ``(environment, parent_task_id, variant_id, seed)`` for
  robustness variants.
* **Headlines are evidence-gated.** A candidate finding is only emitted when the
  supporting metrics actually exist; every candidate carries its task count and a
  preliminary label for tiny runs.

No secrets are ever read from configs, printed, or written to artefacts.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

import mimirbench.evals.registry as registry
from mimirbench.agents.providers import provider_status
from mimirbench.agents.resolver import resolve_agent as resolve_agent_from_config
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
    "generate_leaderboard_model_cards",
    "load_leaderboard_config",
    "propose_headline_candidates",
    "run_leaderboard_config",
    "summarise_leaderboard",
    "validate_leaderboard_config",
]

# Result labels that denote an actual model (not a deterministic baseline). Only
# these get model cards.
_REAL_MODEL_LABELS: frozenset[str] = frozenset({"real API model", "real local model"})

# The three agent modes the leaderboard pairs against each other.
AGENT_MODES: tuple[str, ...] = ("direct", "tool", "reflective")

# Magnitude below which a mean delta is treated as "no meaningful change" for
# headline purposes. Deliberately conservative so tiny runs do not over-claim.
_HEADLINE_EPS = 0.01


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

    timestamp = _utc_timestamp()
    run_id = _make_run_id(config.run.name, timestamp)
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
        real_model = result_label in _REAL_MODEL_LABELS
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
                        "output_dir": str(run_dir),
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
                "model_dir": str(model_dir),
            }
        )

    paired_path = output_dir / "paired_deltas.jsonl"
    _write_jsonl(paired_rows, paired_path)

    summary_payload: dict[str, Any] = {
        "leaderboard_name": config.run.name,
        "run_id": run_id,
        "timestamp": timestamp,
        "output_dir": str(output_dir),
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
            "leaderboard_summary": str(output_dir / "leaderboard_summary.json"),
            "leaderboard_report": str(output_dir / "leaderboard_report.md"),
            "headline_candidates": str(output_dir / "headline_candidates.md"),
            "paired_deltas": str(paired_path),
        },
    }
    summary_payload["headline_candidates"] = propose_headline_candidates(summary_payload)
    summary_payload["model_cards"] = [
        str(path)
        for path in generate_leaderboard_model_cards(
            summary_payload, output_dir=output_dir / "model_cards"
        )
    ]

    _write_json(summary_payload, output_dir / "leaderboard_summary.json")
    _write_leaderboard_report(summary_payload, output_dir / "leaderboard_report.md")
    _write_headline_candidates(summary_payload, output_dir / "headline_candidates.md")
    return summary_payload


def generate_leaderboard_model_cards(
    summary: dict[str, Any],
    *,
    output_dir: str | Path = Path("reports") / "model_cards",
) -> list[Path]:
    """Generate model cards for every *real* model actually run.

    Reference and mock baselines are skipped (they are not models). A card is
    generated per (model, agent-mode) run directory, since each is a distinct
    evaluated configuration. Returns the list of written card paths.
    """
    from mimirbench.reports.model_cards import generate_model_card

    cards: list[Path] = []
    for model in summary.get("models_run", []):
        if model.get("result_label") not in _REAL_MODEL_LABELS:
            continue
        for agent in model.get("agents", {}).values():
            run_dir = agent.get("output_dir")
            if not run_dir:
                continue
            card = generate_model_card(run_dir, output_dir=output_dir)
            if card is not None:
                cards.append(card)
    return cards


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
                "output_dir": str(run_dir),
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
# Headline candidate extraction (deterministic, evidence-gated)
# --------------------------------------------------------------------------- #
def propose_headline_candidates(summary: dict[str, Any]) -> list[dict[str, Any]]:
    """Propose candidate findings, only when the supporting metrics exist.

    Each candidate carries the supporting numbers, the task count, and a
    ``preliminary`` flag. Returns an empty list when nothing is supported (e.g. a
    no-provider run), so the report never invents a finding.
    """
    candidates: list[dict[str, Any]] = []
    preliminary = bool(summary.get("preliminary", True))
    tasks_per_agent = summary.get("tasks_per_agent")
    paired_metrics = summary.get("paired_metrics", {})

    for model_label, pairs in paired_metrics.items():
        candidates.extend(
            _tool_vs_direct_headlines(model_label, pairs, tasks_per_agent, preliminary)
        )
        candidates.extend(
            _reflective_vs_direct_headlines(model_label, pairs, tasks_per_agent, preliminary)
        )

    candidates.extend(_cross_model_headlines(summary, preliminary))
    return candidates


def _tool_vs_direct_headlines(
    model_label: str,
    pairs: dict[str, Any],
    tasks_per_agent: Any,
    preliminary: bool,
) -> list[dict[str, Any]]:
    pair = pairs.get("tool_vs_direct")
    if not pair or not pair.get("n_pairs"):
        return []
    score_delta = pair.get("mean_score_difference")
    risk_delta = pair.get("mean_risk_violation_difference")
    if score_delta is None or risk_delta is None:
        return []
    out: list[dict[str, Any]] = []
    if score_delta > _HEADLINE_EPS and risk_delta >= -_HEADLINE_EPS:
        out.append(
            _headline(
                f"On {model_label}, tool use improved mean score by {score_delta:+.3f} "
                f"but did not reduce adversarial risk violations "
                f"(risk-violation delta {risk_delta:+.3f}).",
                evidence={
                    "model": model_label,
                    "pair": "tool_vs_direct",
                    "mean_score_difference": score_delta,
                    "mean_risk_violation_difference": risk_delta,
                    "n_pairs": pair["n_pairs"],
                },
                n_tasks=tasks_per_agent,
                preliminary=preliminary,
            )
        )
    elif score_delta > _HEADLINE_EPS and risk_delta < -_HEADLINE_EPS:
        out.append(
            _headline(
                f"On {model_label}, tool use improved mean score by {score_delta:+.3f} "
                f"and reduced risk violations by {risk_delta:+.3f}.",
                evidence={
                    "model": model_label,
                    "pair": "tool_vs_direct",
                    "mean_score_difference": score_delta,
                    "mean_risk_violation_difference": risk_delta,
                    "n_pairs": pair["n_pairs"],
                },
                n_tasks=tasks_per_agent,
                preliminary=preliminary,
            )
        )
    return out


def _reflective_vs_direct_headlines(
    model_label: str,
    pairs: dict[str, Any],
    tasks_per_agent: Any,
    preliminary: bool,
) -> list[dict[str, Any]]:
    pair = pairs.get("reflective_vs_direct")
    if not pair or not pair.get("n_pairs"):
        return []
    parse_delta = pair.get("mean_parse_failure_difference")
    latency_delta = pair.get("mean_latency_ms_difference")
    cost_delta = pair.get("mean_estimated_cost_usd_difference")
    if parse_delta is None or parse_delta >= -_HEADLINE_EPS:
        return []
    cost_clauses: list[str] = []
    if latency_delta is not None and latency_delta > 0:
        cost_clauses.append(f"increased latency by {latency_delta:+.1f} ms")
    if cost_delta is not None and cost_delta > 0:
        cost_clauses.append(f"increased cost by ${cost_delta:+.4f}/task")
    if not cost_clauses:
        return []
    return [
        _headline(
            f"On {model_label}, the reflective agent reduced parse failures by "
            f"{parse_delta:+.3f} but {' and '.join(cost_clauses)}.",
            evidence={
                "model": model_label,
                "pair": "reflective_vs_direct",
                "mean_parse_failure_difference": parse_delta,
                "mean_latency_ms_difference": latency_delta,
                "mean_estimated_cost_usd_difference": cost_delta,
                "n_pairs": pair["n_pairs"],
            },
            n_tasks=tasks_per_agent,
            preliminary=preliminary,
        )
    ]


def _cross_model_headlines(summary: dict[str, Any], preliminary: bool) -> list[dict[str, Any]]:
    rows = summary.get("leaderboard", [])
    # Compare models on the direct agent only, to keep the comparison clean.
    direct = [row for row in rows if row.get("agent") == "direct"]
    by_consistency = [
        row for row in direct if row.get("robustness_paraphrase_consistency") is not None
    ]
    if len(by_consistency) < 2:
        return []
    best = max(by_consistency, key=lambda r: r["robustness_paraphrase_consistency"])
    worst = min(by_consistency, key=lambda r: r["robustness_paraphrase_consistency"])
    if best["model"] == worst["model"]:
        return []
    delta = best["robustness_paraphrase_consistency"] - worst["robustness_paraphrase_consistency"]
    if delta <= _HEADLINE_EPS:
        return []
    return [
        _headline(
            f"{best['model']} was more robust to paraphrases than {worst['model']} "
            f"(paraphrase consistency {best['robustness_paraphrase_consistency']:.3f} "
            f"vs {worst['robustness_paraphrase_consistency']:.3f}, direct agent).",
            evidence={
                "more_robust_model": best["model"],
                "less_robust_model": worst["model"],
                "consistency_delta": delta,
            },
            n_tasks=summary.get("tasks_per_agent"),
            preliminary=preliminary,
        )
    ]


def _headline(
    text: str,
    *,
    evidence: dict[str, Any],
    n_tasks: Any,
    preliminary: bool,
) -> dict[str, Any]:
    suffix = f" (n={n_tasks} tasks/agent" if n_tasks is not None else " ("
    suffix += "; PRELIMINARY tiny run)" if preliminary else ")"
    return {
        "text": text + suffix,
        "evidence": evidence,
        "n_tasks": n_tasks,
        "preliminary": preliminary,
    }


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
        f"- Preliminary tiny run: **{'yes' if summary['preliminary'] else 'no'}**",
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

    lines.extend(["", "## Headline candidates", ""])
    candidates = summary.get("headline_candidates", [])
    if not candidates:
        lines.append(
            "No headline candidates: available metrics did not meet the evidence threshold."
        )
    for candidate in candidates:
        lines.append(f"- {candidate['text']}")

    lines.extend(["", "## Caveats", ""])
    for caveat in summary.get("caveats", []):
        lines.append(f"- {caveat}")

    lines.extend(
        [
            "",
            "## Artefacts",
            "",
            f"- `leaderboard_summary.json`: `{summary['artefacts']['leaderboard_summary']}`",
            f"- `paired_deltas.jsonl`: `{summary['artefacts']['paired_deltas']}`",
            f"- `headline_candidates.md`: `{summary['artefacts']['headline_candidates']}`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_headline_candidates(summary: dict[str, Any], path: Path) -> None:
    lines = [
        f"# Headline candidates: {summary['leaderboard_name']}",
        "",
        f"- Run ID: `{summary['run_id']}`",
        f"- Tasks per agent: `{summary['tasks_per_agent']}`",
        f"- Preliminary tiny run: **{'yes' if summary['preliminary'] else 'no'}**",
        "",
        "Candidates are proposed deterministically and only when the supporting "
        "metrics exist. They are *candidates*, not validated findings; confirm "
        "with larger runs before publishing.",
        "",
    ]
    candidates = summary.get("headline_candidates", [])
    if not candidates:
        lines.append(
            "No headline candidates were generated. This run did not produce "
            "metrics that meet the evidence threshold."
        )
    else:
        for i, candidate in enumerate(candidates, start=1):
            lines.append(f"## {i}. {candidate['text']}")
            lines.append("")
            lines.append(f"- Evidence: `{json.dumps(candidate['evidence'], sort_keys=True)}`")
            lines.append(f"- Task count: `{candidate['n_tasks']}`")
            lines.append(f"- Preliminary: `{candidate['preliminary']}`")
            lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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
        "No hidden chain-of-thought is collected or reported; graders and labels are deterministic.",
        "These are benchmark diagnostics, not evidence of trading usefulness or profitability.",
        "These are synthetic deterministic evaluation tasks, not live-market or deployment outcomes.",
        "Leaderboard rows describe only the configured model, agent mode, environments, and task set; "
        "they are not frontier-model claims.",
    ]
    if _is_preliminary(config):
        caveats.append(
            "This is a PRELIMINARY tiny real-model run (<= a handful of tasks per environment); "
            "expand the evaluation before drawing strong conclusions."
        )
    if not model_payloads:
        caveats.append(
            "No model-performance rows were produced in this run; provider checks and "
            "pending artefacts are infrastructure status, not benchmark results."
        )
    if any(p["result_label"] not in {"real API model", "real local model"} for p in model_payloads):
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


def _write_json(data: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_stable_json(data, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(_stable_json(row) + "\n")


def _stable_json(data: Any, *, indent: int | None = None) -> str:
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":") if indent is None else None,
        indent=indent,
        ensure_ascii=False,
    )


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _make_run_id(run_name: str, timestamp: str) -> str:
    safe_timestamp = timestamp.replace(":", "").replace("-", "").replace("Z", "")
    safe_name = "".join(c if c.isalnum() or c in {"-", "_"} else "_" for c in run_name)
    return f"{safe_name}-{safe_timestamp}"


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
