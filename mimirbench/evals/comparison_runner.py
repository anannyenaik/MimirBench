"""Paired comparison runner for Stage 6 benchmark analyses.

The comparison runner evaluates multiple agents on the same environment list
and seeds, then aligns records by ``(environment, task_id)``. Each agent run is
a normal Stage 2 run, so downstream tooling can inspect ``results.jsonl``,
``summary.json``, and ``report.md`` without learning a new schema.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

import mimirbench.evals.registry as registry
from mimirbench.agents.resolver import resolve_agent as resolve_agent_from_config
from mimirbench.evals.runner import run_eval_config
from mimirbench.evals.schemas import (
    AgentConfig,
    EnvironmentRunConfig,
    EvalRunConfig,
    EvalTaskRecord,
    ReportingConfig,
    RunSettings,
)
from mimirbench.evals.scoring import is_risk_violation
from mimirbench.evals.writers import load_records_jsonl, write_summary_json

__all__ = [
    "ComparisonConfig",
    "agent_baseline_kind",
    "load_comparison_config",
    "run_comparison_config",
    "summarise_comparison",
    "validate_comparison_config",
]


class ComparisonConfig(BaseModel):
    """Top-level config for a paired comparison run."""

    model_config = ConfigDict(extra="forbid")

    run: RunSettings
    agents: list[AgentConfig] = Field(min_length=1)
    environments: list[EnvironmentRunConfig] = Field(min_length=1)
    reporting: ReportingConfig = Field(default_factory=ReportingConfig)
    baseline_agent: str | None = None


def load_comparison_config(path: Path) -> ComparisonConfig:
    """Load a Stage 6 comparison config from YAML."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"comparison config {path} must contain a YAML mapping.")
    try:
        return ComparisonConfig(**data)
    except ValidationError:
        raise


def validate_comparison_config(config: ComparisonConfig) -> None:
    """Validate registry references and agent construction without running tasks."""
    if not config.environments:
        raise ValueError("comparison config must include at least one environment.")
    specs = [registry.get(env.name) for env in config.environments]
    first_spec = specs[0]
    for agent in config.agents:
        resolve_agent_from_config(agent, spec=first_spec)
    keys = _agent_keys(config.agents)
    if config.baseline_agent is not None and config.baseline_agent not in keys:
        names = {agent.name for agent in config.agents if agent.name is not None}
        if config.baseline_agent not in names:
            raise ValueError(
                f"baseline_agent {config.baseline_agent!r} must match an agent key "
                f"or configured agent name. Available keys: {', '.join(keys)}"
            )


def run_comparison_config(config: ComparisonConfig) -> dict[str, Any]:
    """Run a paired comparison and write comparison artefacts."""
    validate_comparison_config(config)
    output_dir = _comparison_output_dir(config)
    agent_root = output_dir / "agent_runs"
    output_dir.mkdir(parents=True, exist_ok=True)
    agent_root.mkdir(parents=True, exist_ok=True)

    timestamp = _utc_timestamp()
    comparison_run_id = _make_run_id(config.run.name, timestamp)
    agent_keys = _agent_keys(config.agents)
    baseline_key = _baseline_key(config, agent_keys)

    agent_payloads: dict[str, dict[str, Any]] = {}
    records_by_agent: dict[str, list[EvalTaskRecord]] = {}

    for agent_key, agent in zip(agent_keys, config.agents, strict=True):
        run_dir = agent_root / agent_key
        eval_config = EvalRunConfig(
            run=config.run.model_copy(
                update={
                    "name": f"{config.run.name}_{agent_key}",
                    "output_dir": str(run_dir),
                    "cache_path": None,
                }
            ),
            agent=agent,
            environments=config.environments,
            reporting=config.reporting,
        )
        summary = run_eval_config(eval_config)
        summary["baseline_kind"] = agent_baseline_kind(agent)
        summary["comparison"] = {
            "comparison_name": config.run.name,
            "comparison_run_id": comparison_run_id,
            "agent_key": agent_key,
            "baseline_agent_key": baseline_key,
        }
        if config.reporting.write_summary:
            write_summary_json(summary, run_dir / "summary.json")

        records = load_records_jsonl(run_dir / "results.jsonl")
        records_by_agent[agent_key] = records
        agent_payloads[agent_key] = {
            "agent_key": agent_key,
            "baseline_kind": agent_baseline_kind(agent),
            "run_id": summary["run_id"],
            "run_name": summary["run_name"],
            "agent": summary["agent"],
            "output_dir": str(run_dir),
            "results_path": str(run_dir / "results.jsonl"),
            "summary_path": str(run_dir / "summary.json"),
            "report_path": str(run_dir / "report.md"),
            "metrics": summary["metrics"],
            "cost_latency": summary.get("cost_latency", {}),
        }

    _assert_aligned(records_by_agent, baseline_key=baseline_key)
    paired_rows = _paired_rows(records_by_agent, baseline_key=baseline_key)
    paired_path = output_dir / "paired_results.jsonl"
    _write_jsonl(paired_rows, paired_path)

    paired_metrics = _aggregate_paired_metrics(paired_rows)
    figures = _try_generate_figures(output_dir)
    summary_payload = {
        "comparison_name": config.run.name,
        "run_id": comparison_run_id,
        "timestamp": timestamp,
        "output_dir": str(output_dir),
        "baseline_agent_key": baseline_key,
        "baseline_kind": agent_payloads[baseline_key]["baseline_kind"],
        "agents": [agent_payloads[key] for key in agent_keys],
        "environments": [
            {
                "name": env.name,
                "num_tasks": env.num_tasks,
                "seed": env.seed if env.seed is not None else config.run.seed,
            }
            for env in config.environments
        ],
        "paired_metrics": paired_metrics,
        "artefacts": {
            "paired_results": str(paired_path),
            "comparison_summary": str(output_dir / "comparison_summary.json"),
            "comparison_report": str(output_dir / "comparison_report.md"),
            "agent_runs": str(agent_root),
            "figures": [str(path) for path in figures],
        },
        "caveats": _comparison_caveats(agent_payloads.values()),
    }
    _write_json(summary_payload, output_dir / "comparison_summary.json")
    _write_comparison_report(summary_payload, output_dir / "comparison_report.md")
    return summary_payload


def summarise_comparison(run_dir: Path) -> dict[str, Any]:
    """Read a comparison summary from ``run_dir``."""
    path = run_dir / "comparison_summary.json"
    if not path.exists():
        raise FileNotFoundError(f"no comparison_summary.json found at {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def agent_baseline_kind(agent: AgentConfig) -> str:
    """Return the required Stage 6 result label for an agent config."""
    agent_type = agent.type.lower().strip()
    if agent_type == "reference":
        return "reference sanity check"
    if agent_type == "mock":
        return "mock diagnostic baseline"
    if agent_type == "tool" and (agent.tool_policy or "reference").lower().strip() == "reference":
        return "deterministic non-model tool baseline"
    if agent_type == "local" or agent.model_name:
        return "real local model"
    if agent_type in {"api", "direct", "reflective", "tool"}:
        return "real API model"
    return agent_type


def _comparison_output_dir(config: ComparisonConfig) -> Path:
    if config.run.output_dir:
        return Path(config.run.output_dir)
    return Path("reports") / "runs" / "comparisons" / config.run.name


def _agent_keys(agents: list[AgentConfig]) -> list[str]:
    counts: dict[str, int] = {}
    keys: list[str] = []
    for agent in agents:
        base = _agent_key_base(agent)
        count = counts.get(base, 0)
        counts[base] = count + 1
        keys.append(base if count == 0 else f"{base}_{count + 1}")
    return keys


def _agent_key_base(agent: AgentConfig) -> str:
    if agent.name:
        return _slug(agent.name)
    agent_type = agent.type.lower().strip()
    if agent_type == "mock":
        return _slug(f"mock_{agent.behaviour or 'random_valid'}")
    if agent_type == "tool":
        policy = (agent.tool_policy or "reference").lower().strip()
        backend = agent.model or agent.model_name or policy
        return _slug(f"tool_{policy}_{backend}")
    if agent_type in {"api", "direct", "reflective"}:
        backend = agent.model or agent.model_name or "model"
        provider = agent.provider or ("local" if agent.model_name else "api")
        return _slug(f"{agent_type}_{provider}_{backend}")
    if agent_type == "local":
        return _slug(f"local_{agent.model_name or 'model'}")
    return _slug(agent_type)


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip()).strip("_.-")
    return slug.lower() or "agent"


def _baseline_key(config: ComparisonConfig, agent_keys: list[str]) -> str:
    if config.baseline_agent is None:
        return agent_keys[0]
    if config.baseline_agent in agent_keys:
        return config.baseline_agent
    for key, agent in zip(agent_keys, config.agents, strict=True):
        if agent.name == config.baseline_agent:
            return key
    return agent_keys[0]


def _assert_aligned(records_by_agent: dict[str, list[EvalTaskRecord]], *, baseline_key: str) -> None:
    baseline_ids = _record_keys(records_by_agent[baseline_key])
    for agent_key, records in records_by_agent.items():
        current = _record_keys(records)
        if current == baseline_ids:
            continue
        missing = sorted(set(baseline_ids) - set(current))[:5]
        extra = sorted(set(current) - set(baseline_ids))[:5]
        raise ValueError(
            f"agent {agent_key!r} did not preserve task IDs. "
            f"missing={missing} extra={extra}"
        )


def _record_keys(records: Iterable[EvalTaskRecord]) -> list[tuple[str, str]]:
    return [(record.environment, record.task_id) for record in records]


def _paired_rows(
    records_by_agent: dict[str, list[EvalTaskRecord]],
    *,
    baseline_key: str,
) -> list[dict[str, Any]]:
    baseline_records = {
        (record.environment, record.task_id): record
        for record in records_by_agent[baseline_key]
    }
    rows: list[dict[str, Any]] = []
    for candidate_key, records in records_by_agent.items():
        if candidate_key == baseline_key:
            continue
        for candidate in records:
            base = baseline_records[(candidate.environment, candidate.task_id)]
            rows.append(_paired_row(base, candidate, baseline_key, candidate_key))
    return rows


def _paired_row(
    baseline: EvalTaskRecord,
    candidate: EvalTaskRecord,
    baseline_key: str,
    candidate_key: str,
) -> dict[str, Any]:
    base_values = _comparison_values(baseline)
    candidate_values = _comparison_values(candidate)
    deltas = {
        f"{name}_difference": _difference(candidate_values[name], base_values[name])
        for name in base_values
    }
    return {
        "environment": candidate.environment,
        "task_id": candidate.task_id,
        "seed": candidate.seed,
        "baseline_agent_key": baseline_key,
        "candidate_agent_key": candidate_key,
        "baseline_agent_name": baseline.agent_name,
        "candidate_agent_name": candidate.agent_name,
        "baseline": base_values,
        "candidate": candidate_values,
        "deltas": deltas,
    }


def _comparison_values(record: EvalTaskRecord) -> dict[str, float | None]:
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
        "robustness_score": None,
    }


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


def _aggregate_paired_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_candidate: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_candidate.setdefault(str(row["candidate_agent_key"]), []).append(row)

    summaries: dict[str, Any] = {}
    for candidate_key, candidate_rows in sorted(by_candidate.items()):
        deltas = [row["deltas"] for row in candidate_rows]
        fields = sorted({field for delta in deltas for field in delta})
        summary: dict[str, Any] = {"n_pairs": len(candidate_rows)}
        for field in fields:
            values = [
                float(delta[field])
                for delta in deltas
                if isinstance(delta.get(field), (int, float)) and not isinstance(delta.get(field), bool)
            ]
            summary[f"mean_{field}"] = sum(values) / len(values) if values else None
        summaries[candidate_key] = summary
    return summaries


def _comparison_caveats(agent_payloads: Iterable[dict[str, Any]]) -> list[str]:
    caveats = [
        "All paired deltas are candidate minus baseline on identical task IDs.",
        "Lower regret, posterior error, risk violations, parse failures, latency, and cost are better; higher score is better.",
        "No hidden chain-of-thought is collected or reported.",
        "No LLM judges are used; graders and labels are deterministic.",
        "These results are benchmark diagnostics, not evidence of trading usefulness or profitability.",
    ]
    kinds = {str(payload["baseline_kind"]) for payload in agent_payloads}
    if any(kind != "real API model" and kind != "real local model" for kind in kinds):
        caveats.append(
            "Reference, mock, and reference-tool rows are non-model baselines and must not be described as model performance."
        )
    return caveats


def _try_generate_figures(output_dir: Path) -> list[Path]:
    try:
        from mimirbench.analysis.plots import generate_comparison_plots
    except Exception:
        return []
    return generate_comparison_plots(output_dir)


def _write_comparison_report(summary: dict[str, Any], path: Path) -> None:
    lines = [
        f"# Comparison report: {summary['comparison_name']}",
        "",
        f"- Run ID: `{summary['run_id']}`",
        f"- Timestamp: `{summary['timestamp']}`",
        f"- Baseline agent key: `{summary['baseline_agent_key']}`",
        f"- Baseline kind: **{summary['baseline_kind']}**",
        "",
        "## Agents",
        "",
        "| Agent key | Agent name | Type | Result label | Tasks | Mean score | Parse failure |",
        "| --- | --- | --- | --- | ---: | ---: | ---: |",
    ]
    for agent in summary["agents"]:
        overall = agent["metrics"]["overall"]
        config = agent["agent"]
        lines.append(
            "| "
            f"`{agent['agent_key']}` | `{config.get('name')}` | `{config.get('type')}` | "
            f"{agent['baseline_kind']} | {overall['n_tasks']} | "
            f"{_fmt(overall['mean_score'])} | {_fmt(overall['parse_failure_rate'])} |"
        )

    lines.extend(
        [
            "",
            "## Paired Deltas",
            "",
            "Deltas are candidate minus baseline on matched `(environment, task_id)` rows.",
            "",
            "| Candidate | Pairs | Score diff | Regret diff | Posterior error diff | Risk violation diff | Parse failure diff | Latency diff ms | Cost diff USD |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for candidate, metrics in summary["paired_metrics"].items():
        lines.append(
            "| "
            f"`{candidate}` | {metrics['n_pairs']} | "
            f"{_fmt(metrics.get('mean_score_difference'))} | "
            f"{_fmt(metrics.get('mean_regret_difference'))} | "
            f"{_fmt(metrics.get('mean_posterior_error_difference'))} | "
            f"{_fmt(metrics.get('mean_risk_violation_difference'))} | "
            f"{_fmt(metrics.get('mean_parse_failure_difference'))} | "
            f"{_fmt(metrics.get('mean_latency_ms_difference'))} | "
            f"{_fmt(metrics.get('mean_estimated_cost_usd_difference'))} |"
        )

    lines.extend(["", "## Figures", ""])
    figures = summary["artefacts"].get("figures", [])
    if figures:
        for figure in figures:
            lines.append(f"- `{figure}`")
    else:
        lines.append("No figures were generated.")

    lines.extend(["", "## Caveats", ""])
    for caveat in summary.get("caveats", []):
        lines.append(f"- {caveat}")

    lines.extend(
        [
            "",
            "## Artefacts",
            "",
            f"- `paired_results.jsonl`: `{summary['artefacts']['paired_results']}`",
            f"- Agent run directories: `{summary['artefacts']['agent_runs']}`",
            f"- Machine-readable summary: `{summary['artefacts']['comparison_summary']}`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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
    safe_name = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in run_name)
    return f"{safe_name}-{safe_timestamp}"


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{value:.6g}"
    return str(value)
