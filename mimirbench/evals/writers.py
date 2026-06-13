"""Result writers for Stage 2 evaluation runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mimirbench.evals.schemas import (
    EvalRunConfig,
    EvalTaskRecord,
    RobustnessRecord,
    RobustnessRunConfig,
)
from mimirbench.evals.scoring import aggregate_cost_latency, aggregate_records

__all__ = [
    "build_robustness_summary",
    "build_summary",
    "load_records_jsonl",
    "load_robustness_records_jsonl",
    "write_failure_cases_jsonl",
    "write_failure_cases_markdown",
    "write_markdown_report",
    "write_results_jsonl",
    "write_robustness_report",
    "write_robustness_results_jsonl",
    "write_robustness_summary_json",
    "write_summary_json",
]


def write_results_jsonl(records: list[EvalTaskRecord], path: Path) -> None:
    """Write per-task records to JSONL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(_stable_json(record.model_dump(mode="json")) + "\n")


def load_records_jsonl(path: Path) -> list[EvalTaskRecord]:
    """Read per-task records from JSONL."""
    records: list[EvalTaskRecord] = []
    if not path.exists():
        return records
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                records.append(EvalTaskRecord.model_validate(json.loads(stripped)))
            except Exception as exc:
                raise RuntimeError(
                    f"failed to read result row {line_no} from {path}: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc
    return records


def build_summary(
    *,
    config: EvalRunConfig,
    run_id: str,
    timestamp: str,
    output_dir: Path,
    records: list[EvalTaskRecord],
) -> dict[str, Any]:
    """Build the machine-readable summary JSON payload."""
    agent_type = config.agent.type.lower()
    warning = _agent_warning(agent_type)
    return {
        "run_id": run_id,
        "run_name": config.run.name,
        "timestamp": timestamp,
        "agent": {
            "type": config.agent.type,
            "name": records[0].agent_name if records else config.agent.name,
            "config": _redact_agent_config(config.agent.model_dump(mode="json")),
            "warning": warning,
        },
        "output_dir": str(output_dir),
        "environments": [
            {
                "name": env.name,
                "num_tasks": env.num_tasks,
                "seed": env.seed if env.seed is not None else config.run.seed,
            }
            for env in config.environments
        ],
        "metrics": aggregate_records(records),
        "cost_latency": aggregate_cost_latency(records),
        "failure_examples": _failure_examples(records),
        "known_limitations": _known_limitations(agent_type),
    }


def write_summary_json(summary: dict[str, Any], path: Path) -> None:
    """Write ``summary.json``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_stable_json(summary, indent=2) + "\n", encoding="utf-8")


def write_markdown_report(
    *,
    summary: dict[str, Any],
    records: list[EvalTaskRecord],
    path: Path,
) -> None:
    """Write a human-readable Markdown report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    agent = summary["agent"]
    metrics = summary["metrics"]
    overall = metrics["overall"]
    warning = agent.get("warning")
    lines = [
        f"# {summary['run_name']}",
        "",
        f"- Run ID: `{summary['run_id']}`",
        f"- Timestamp: `{summary['timestamp']}`",
        f"- Agent: `{agent.get('name')}` (`{agent.get('type')}`)",
        f"- Number of tasks: `{overall['n_tasks']}`",
    ]
    if warning:
        lines.extend(["", f"**Warning:** {warning}"])

    lines.extend(
        [
            "",
            "## Environments",
            "",
            "| Environment | Tasks | Mean score | Pass rate | Invalid response rate | Runtime error rate |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for environment, env_metrics in metrics["environments"].items():
        lines.append(
            "| "
            f"{environment} | {env_metrics['n_tasks']} | "
            f"{_fmt_float(env_metrics['mean_score'])} | "
            f"{_fmt_float(env_metrics['pass_rate'])} | "
            f"{_fmt_float(env_metrics['invalid_response_rate'])} | "
            f"{_fmt_float(env_metrics['runtime_error_rate'])} |"
        )

    lines.extend(
        [
            "",
            "## Aggregate Metrics",
            "",
            f"- Mean score: `{_fmt_float(overall['mean_score'])}`",
            f"- Pass rate: `{_fmt_float(overall['pass_rate'])}`",
            f"- Violation rate: `{_fmt_float(overall['violation_rate'])}`",
            f"- Parse failure rate: `{_fmt_float(overall['parse_failure_rate'])}`",
            f"- Runtime error rate: `{_fmt_float(overall['runtime_error_rate'])}`",
            f"- Latency mean ms: `{_fmt_optional(overall['latency_mean_ms'])}`",
            f"- Latency p50 ms: `{_fmt_optional(overall['latency_p50_ms'])}`",
            f"- Latency p95 ms: `{_fmt_optional(overall['latency_p95_ms'])}`",
        ]
    )

    cost_latency = summary.get("cost_latency")
    if cost_latency:
        lines.extend(["", "## Cost and Latency", ""])
        lines.append(f"- Total input tokens: `{_fmt_count(cost_latency['total_input_tokens'])}`")
        lines.append(f"- Total output tokens: `{_fmt_count(cost_latency['total_output_tokens'])}`")
        lines.append(f"- Total tokens: `{_fmt_count(cost_latency['total_tokens'])}`")
        if cost_latency.get("cost_estimated"):
            lines.append(
                f"- Estimated total cost (USD): `{cost_latency['estimated_total_cost_usd']}` "
                f"({cost_latency['cost_note']})"
            )
        else:
            lines.append(f"- Estimated total cost (USD): **{cost_latency['cost_note']}**")
        lines.append(f"- Mean latency ms: `{_fmt_optional(cost_latency['mean_latency_ms'])}`")
        lines.append(f"- p50 latency ms: `{_fmt_optional(cost_latency['p50_latency_ms'])}`")
        lines.append(f"- p95 latency ms: `{_fmt_optional(cost_latency['p95_latency_ms'])}`")
        lines.append(f"- Timeout rate: `{_fmt_float(cost_latency['timeout_rate'])}`")
        lines.append(f"- Provider error rate: `{_fmt_float(cost_latency['provider_error_rate'])}`")
        lines.append(f"- Parse failure rate: `{_fmt_float(cost_latency['parse_failure_rate'])}`")
        lines.append(f"- Invalid response rate: `{_fmt_float(cost_latency['invalid_response_rate'])}`")

    tool_audit = summary.get("tool_audit")
    if tool_audit:
        lines.extend(["", "## Tool Use", ""])
        lines.append(f"- Tool call rate: `{_fmt_optional(tool_audit['tool_call_rate'])}`")
        lines.append(f"- Invalid tool call rate: `{_fmt_optional(tool_audit['invalid_tool_call_rate'])}`")
        lines.append(f"- Tool error rate: `{_fmt_optional(tool_audit['tool_error_rate'])}`")
        lines.append(f"- Mean tool steps: `{_fmt_optional(tool_audit['mean_tool_steps'])}`")
        lines.append(
            f"- Final answer after tool rate: `{_fmt_optional(tool_audit['final_answer_after_tool_rate'])}`"
        )
        lines.append(
            f"- Tool result ignored rate: `{_fmt_optional(tool_audit['tool_result_ignored_rate'])}`"
        )
        lines.append("- See `tool_audit.jsonl` / `tool_audit.md` for the full trace.")

    metric_means = overall.get("metric_means", {})
    if metric_means:
        lines.extend(["", "## Metric Means", ""])
        for name, value in sorted(metric_means.items()):
            lines.append(f"- `{name}`: `{_fmt_float(value)}`")

    lines.extend(["", "## Failure Examples", ""])
    failures = summary.get("failure_examples", [])
    if not failures:
        lines.append("No failures recorded.")
    else:
        for failure in failures:
            lines.append(
                "- "
                f"`{failure['environment']}/{failure['task_id']}` "
                f"score=`{_fmt_float(failure['score'])}` "
                f"violations=`{failure['violations']}` "
                f"error=`{failure['error']}`"
            )

    lines.extend(["", "## Scope and Limitations", ""])
    for limitation in summary.get("known_limitations", []):
        lines.append(f"- {limitation}")

    lines.extend(
        [
            "",
            "## Artefacts",
            "",
            "- `results.jsonl`: per-task records.",
            "- `summary.json`: machine-readable aggregate summary.",
            "- `report.md`: this report.",
        ]
    )
    if records:
        cache_hits = sum(1 for record in records if record.metadata.get("cache_hit"))
        lines.append(f"- Cache hits: `{cache_hits}`.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# Robustness artefacts.
# --------------------------------------------------------------------------- #
def write_robustness_results_jsonl(records: list[RobustnessRecord], path: Path) -> None:
    """Write per-variant robustness records to JSONL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(_stable_json(record.model_dump(mode="json")) + "\n")


def load_robustness_records_jsonl(path: Path) -> list[RobustnessRecord]:
    """Read per-variant robustness records from JSONL."""
    records: list[RobustnessRecord] = []
    if not path.exists():
        return records
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                records.append(RobustnessRecord.model_validate(json.loads(stripped)))
            except Exception as exc:
                raise RuntimeError(
                    f"failed to read robustness row {line_no} from {path}: "
                    f"{type(exc).__name__}: {exc}"
                ) from exc
    return records


def robustness_baseline_kind(agent_type: str) -> str:
    """Human-readable label for the baseline class used in a robustness run."""
    agent_type = agent_type.lower()
    if agent_type == "reference":
        return "reference solver (sanity check)"
    if agent_type == "mock":
        return "mock agent (diagnostic baseline)"
    if agent_type in {"api", "local", "direct", "reflective", "tool"}:
        return "real model"
    return agent_type


def _robustness_caveats(agent_type: str) -> list[str]:
    caveats = [
        "Robustness compares an agent on a base task versus deterministic, "
        "answer-preserving (or precisely-rescaled) variants of it.",
        "Variants are built from fixed templates and text banks, not from a language "
        "model; see ROBUSTNESS.md for the taxonomy and rationale.",
        "For answer-preserving variants a changed final action counts against "
        "robustness unless it is provably equivalent.",
    ]
    if agent_type.lower() == "reference":
        caveats.append(
            "Reference robustness is a wiring/sanity check: the deterministic solver "
            "reads structured metadata, so it is robust by construction. It is NOT a "
            "model result."
        )
    elif agent_type.lower() == "mock":
        caveats.append(
            "Mock robustness is diagnostic only: the mock RNG is keyed on the task id, "
            "so action flips under variants are expected and reflect no model."
        )
    else:
        caveats.append(
            "Real-model robustness numbers are only meaningful for the exact model, "
            "prompt, and decoding settings used."
        )
    return caveats


def build_robustness_summary(
    *,
    config: RobustnessRunConfig,
    run_id: str,
    timestamp: str,
    output_dir: Path,
    agent_name: str,
    n_base_tasks: int,
    records: list[RobustnessRecord],
    metrics: dict[str, Any],
) -> dict[str, Any]:
    """Build the machine-readable robustness summary payload."""
    # Lazy import avoids any import-order coupling with the variant catalogue.
    from mimirbench.evals.variants import applicable_variant_types

    agent_type = config.agent.type.lower()
    n_variants = sum(1 for r in records if r.variant_id is not None)
    environments = []
    for env in config.environments:
        resolved = env.variant_types or [vt.value for vt in applicable_variant_types(env.name)]
        environments.append(
            {
                "name": env.name,
                "num_tasks": env.num_tasks,
                "variants_per_task": env.variants_per_task,
                "variant_types": resolved,
                "seed": env.seed if env.seed is not None else config.run.seed,
            }
        )
    return {
        "run_id": run_id,
        "run_name": config.run.name,
        "timestamp": timestamp,
        "agent": {
            "type": config.agent.type,
            "name": agent_name,
            "config": _redact_agent_config(config.agent.model_dump(mode="json")),
            "warning": _agent_warning(agent_type),
        },
        "baseline_kind": robustness_baseline_kind(agent_type),
        "output_dir": str(output_dir),
        "environments": environments,
        "counts": {
            "n_base_tasks": n_base_tasks,
            "n_variants": n_variants,
            "n_records": len(records),
        },
        "metrics": metrics,
        "caveats": _robustness_caveats(agent_type),
    }


def write_robustness_summary_json(summary: dict[str, Any], path: Path) -> None:
    """Write ``robustness_summary.json``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_stable_json(summary, indent=2) + "\n", encoding="utf-8")


def write_robustness_report(
    *,
    summary: dict[str, Any],
    failure_cases: list[dict[str, Any]],
    path: Path,
) -> None:
    """Write the human-readable robustness Markdown report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    agent = summary["agent"]
    metrics = summary["metrics"]
    counts = summary["counts"]
    env_names = ", ".join(env["name"] for env in summary["environments"])
    variant_types = sorted({vt for env in summary["environments"] for vt in env["variant_types"]})

    lines = [
        f"# Robustness report: {summary['run_name']}",
        "",
        f"- Run ID: `{summary['run_id']}`",
        f"- Timestamp: `{summary['timestamp']}`",
        f"- Agent: `{agent.get('name')}` (`{agent.get('type')}`)",
        f"- Baseline kind: **{summary['baseline_kind']}**",
        f"- Environments: {env_names}",
        f"- Variant types: {', '.join(variant_types)}",
        f"- Base tasks: `{counts['n_base_tasks']}`",
        f"- Variants: `{counts['n_variants']}`",
    ]
    if agent.get("warning"):
        lines.extend(["", f"**Warning:** {agent['warning']}"])

    lines.extend(["", "## Overall robustness metrics", ""])
    lines.extend(_metric_lines(metrics))

    lines.extend(["", "## Environment breakdown", "", _breakdown_header()])
    for env, env_metrics in metrics.get("environment_breakdown", {}).items():
        lines.append(_breakdown_row(env, env_metrics))

    lines.extend(["", "## Variant-type breakdown", "", _breakdown_header("Variant type")])
    for vtype, type_metrics in metrics.get("variant_type_breakdown", {}).items():
        lines.append(_breakdown_row(vtype, type_metrics))

    lines.extend(["", "## Top failure cases", ""])
    if not failure_cases:
        lines.append("No failure cases were extracted.")
    else:
        for i, case in enumerate(failure_cases[:15], start=1):
            lines.append(
                f"{i}. `{case['environment']}` `{case['variant_id']}` "
                f"**{case['diagnostic_label']}** "
                f"(score {case['base_grader_result']['score']:.2f} → "
                f"{case['variant_grader_result']['score']:.2f}): {case['why_interesting']}"
            )

    lines.extend(["", "## Scope and Limitations", ""])
    for caveat in summary.get("caveats", []):
        lines.append(f"- {caveat}")

    lines.extend(
        [
            "",
            "## Artefacts",
            "",
            "- `robustness_results.jsonl`: per-variant records.",
            "- `robustness_summary.json`: machine-readable metrics.",
            "- `robustness_report.md`: this report.",
            "- `failure_cases.jsonl` / `failure_cases.md`: ranked diagnostic failures.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_failure_cases_jsonl(cases: list[dict[str, Any]], path: Path) -> None:
    """Write extracted failure cases to JSONL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for case in cases:
            handle.write(_stable_json(case) + "\n")


def write_failure_cases_markdown(
    cases: list[dict[str, Any]],
    *,
    summary: dict[str, Any],
    path: Path,
) -> None:
    """Write a readable failure-case triage list."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Failure cases: {summary['run_name']}",
        "",
        f"- Baseline kind: **{summary['baseline_kind']}**",
        f"- Total cases: `{len(cases)}`",
        "",
    ]
    if not cases:
        lines.append("No failure cases were extracted for this run.")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return

    for i, case in enumerate(cases, start=1):
        base = case["base_grader_result"]
        variant = case["variant_grader_result"]
        lines.extend(
            [
                f"## {i}. {case['diagnostic_label']} — `{case['environment']}`",
                "",
                f"- Variant: `{case['variant_id']}` (`{case['variant_type']}`, "
                f"answer_preserving={case['answer_preserving']})",
                f"- Why interesting: {case['why_interesting']}",
                f"- Base score/passed: `{base['score']:.3f}` / `{base['passed']}` "
                f"violations=`{base['violations']}`",
                f"- Variant score/passed: `{variant['score']:.3f}` / `{variant['passed']}` "
                f"violations=`{variant['violations']}`",
                f"- Base action → variant action: `{case['base_action']}` → "
                f"`{case['variant_action']}` (changed={case['action_changed']})",
                "",
                "<details><summary>variant response (truncated)</summary>",
                "",
                "```",
                str(case["variant_response"])[:500],
                "```",
                "</details>",
                "",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _metric_lines(metrics: dict[str, Any]) -> list[str]:
    keys = [
        "paraphrase_consistency_rate",
        "mean_score_drop",
        "worst_score_drop",
        "action_flip_rate",
        "invalid_response_increase",
        "unsafe_action_increase",
        "risk_violation_increase",
        "pressure_susceptibility_rate",
        "order_invariance_rate",
        "distractor_robustness_rate",
    ]
    lines = []
    for key in keys:
        value = metrics.get(key)
        lines.append(f"- `{key}`: `{_fmt_optional(value)}`")
    return lines


def _breakdown_header(first: str = "Environment") -> str:
    return (
        f"| {first} | Variants | Paraphrase consistency | Mean drop | Action flip | "
        "Unsafe incr. | Pressure susc. |\n"
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"
    )


def _breakdown_row(name: str, metrics: dict[str, Any]) -> str:
    return (
        f"| {name} | {metrics['n_variants']} | "
        f"{_fmt_optional(metrics['paraphrase_consistency_rate'])} | "
        f"{_fmt_optional(metrics['mean_score_drop'])} | "
        f"{_fmt_optional(metrics['action_flip_rate'])} | "
        f"{_fmt_optional(metrics['unsafe_action_increase'])} | "
        f"{_fmt_optional(metrics['pressure_susceptibility_rate'])} |"
    )


def _agent_warning(agent_type: str) -> str | None:
    if agent_type == "reference":
        return "This is a reference solver sanity check, not a real model benchmark."
    if agent_type == "mock":
        return "This is a deterministic mock or diagnostic baseline, not a real model benchmark."
    return None


def _known_limitations(agent_type: str) -> list[str]:
    limitations = [
        "Scores are meaningful only for the environments and graders actually run.",
        "No hidden chain-of-thought is collected; model output stores concise summaries only.",
    ]
    warning = _agent_warning(agent_type)
    if warning:
        limitations.append(warning)
    return limitations


def _failure_examples(records: list[EvalTaskRecord], limit: int = 5) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for record in records:
        result = record.grader_result
        if result.passed and record.error is None:
            continue
        failures.append(
            {
                "environment": record.environment,
                "task_id": record.task_id,
                "score": result.score,
                "violations": result.violations,
                "error": record.error,
                "response_excerpt": record.model_response[:300],
            }
        )
        if len(failures) >= limit:
            break
    return failures


def _redact_agent_config(config: dict[str, Any]) -> dict[str, Any]:
    redacted = dict(config)
    for key in ("api_key", "token", "password"):
        if key in redacted:
            redacted[key] = "<redacted>"
    return redacted


def _fmt_optional(value: float | None) -> str:
    return "n/a" if value is None else _fmt_float(value)


def _fmt_count(value: int | None) -> str:
    return "not estimated" if value is None else str(value)


def _fmt_float(value: float) -> str:
    return f"{value:.6g}"


def _stable_json(data: Any, *, indent: int | None = None) -> str:
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":") if indent is None else None,
        indent=indent,
        ensure_ascii=False,
    )
