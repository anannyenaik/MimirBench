"""Model-card generation from saved run artefacts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from mimirbench.analysis.calibration import calibration_summary_from_records
from mimirbench.analysis.failure_cases import extract_eval_failure_cases
from mimirbench.evals.comparison_runner import agent_baseline_kind
from mimirbench.evals.schemas import AgentConfig, EvalTaskRecord
from mimirbench.evals.scoring import is_risk_violation
from mimirbench.evals.writers import load_records_jsonl

__all__ = ["generate_model_card", "generate_small_transformer_model_card"]


def generate_model_card(
    run_dir: str | Path,
    *,
    output_dir: str | Path = Path("reports") / "model_cards",
) -> Path | None:
    """Generate one model/agent card from an actual run directory.

    Returns ``None`` when the directory lacks concrete run artefacts. This is the
    guardrail that prevents cards for configs or models that were never run.
    """
    root = Path(run_dir)
    summary_path = root / "summary.json"
    results_path = root / "results.jsonl"
    if not summary_path.exists() or not results_path.exists():
        return None
    records = load_records_jsonl(results_path)
    if not records:
        return None
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{_slug(summary['run_name'])}__{_slug(_agent_name(summary))}.md"
    path.write_text(_render_card(summary, records, root), encoding="utf-8")
    return path


def generate_small_transformer_model_card(
    training_dir: str | Path,
    *,
    eval_dir: str | Path | None = None,
    output_dir: str | Path = Path("reports") / "model_cards",
) -> Path:
    """Generate a model card for an actual small-transformer training run."""
    root = Path(training_dir)
    summary_path = root / "summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"training summary not found: {summary_path}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    eval_summary = _load_optional_eval_summary(eval_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    run_name = str(summary.get("run_name") or root.name)
    path = out_dir / f"{_slug(run_name)}.md"
    path.write_text(
        _render_small_transformer_card(summary, root, eval_summary=eval_summary),
        encoding="utf-8",
    )
    return path


def _render_small_transformer_card(
    summary: dict[str, Any],
    training_dir: Path,
    *,
    eval_summary: dict[str, Any] | None,
) -> str:
    config = summary.get("config", {})
    model = summary.get("model", {})
    counts = summary.get("counts", {})
    paths = summary.get("paths", {})
    best_metrics = summary.get("best_metrics", {})
    eval_metrics = eval_summary.get("metrics", {}) if eval_summary else None
    run_name = str(summary.get("run_name") or training_dir.name)
    lines = [
        f"# Model card: {run_name}",
        "",
        "## Identity",
        "",
        f"- Model name: `{run_name}`",
        "- Model type: compact synthetic Bayesian trace transformer",
        f"- Training run directory: `{training_dir}`",
        "- Created from actual training artefacts: `yes`",
        "",
        "## Architecture",
        "",
        f"- Architecture: `{model.get('architecture', 'compact_transformer_encoder')}`",
        f"- Parameter count: `{_fmt(model.get('parameter_count'))}`",
        f"- Target heads: `{', '.join(model.get('target_heads', []))}`",
        f"- Model config: `{_compact(model.get('config', {}))}`",
        "",
        "## Training Data",
        "",
        "- Data source: deterministic synthetic Bayesian traces generated inside MimirBench",
        f"- Synthetic traces: train=`{counts.get('train')}`, val=`{counts.get('val')}`, test=`{counts.get('test')}`",
        f"- Data config: `{_compact(config.get('data', {}))}`",
        "- Stored targets are final labels and concise rationale classes only; hidden chain-of-thought is not generated or stored.",
        "",
        "## Training Config",
        "",
        f"- Optimisation config: `{_compact(config.get('training', {}))}`",
        f"- Full resolved config: `{paths.get('config', 'n/a')}`",
        "",
        "## Validation Metrics",
        "",
        f"- Best epoch: `{summary.get('best_epoch')}`",
        f"- Best validation metrics: `{_compact(best_metrics)}`",
        "",
        "## Held-Out MimirBench Metrics",
        "",
    ]
    if eval_metrics and eval_summary is not None:
        lines.append(f"- Held-out evaluation summary: `{_compact(eval_metrics)}`")
        lines.append(f"- Evaluation run directory: `{eval_summary.get('output_dir', 'n/a')}`")
    else:
        lines.append("- Held-out checkpoint evaluation has not been run for this card.")

    lines.extend(
        [
            "",
            "## Interpretability Readiness",
            "",
            "- Checkpoints include model config, label vocabularies, tokenizer vocabulary, and reproducibility metadata.",
            "- The supervised heads expose posterior bucket, action, EV, risk, confidence, and rationale-class targets for later probes.",
            "- The model is small enough for CPU smoke runs and later activation-capture experiments.",
            "",
            "## Checkpoints",
            "",
            f"- Best checkpoint: `{paths.get('best_checkpoint', 'n/a')}`",
            f"- Final checkpoint: `{paths.get('final_checkpoint', 'n/a')}`",
            f"- Tokenizer vocabulary: `{paths.get('vocab', 'n/a')}`",
            "",
            "## Scope and Limitations",
            "",
            "- This is a small synthetic model, not a frontier model.",
            "- Training traces come from a narrow deterministic Bayesian generator and do not represent open-ended strategic reasoning.",
            "- Metrics should not be interpreted as evidence of real-world trading, forecasting, or deployment usefulness.",
            "- No external model downloads, external datasets, or LLM judges are used.",
            "",
        ]
    )
    return "\n".join(lines)


def _load_optional_eval_summary(eval_dir: str | Path | None) -> dict[str, Any] | None:
    if eval_dir is None:
        return None
    path = Path(eval_dir) / "summary.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else None


def _render_card(summary: dict[str, Any], records: list[EvalTaskRecord], run_dir: Path) -> str:
    agent = summary["agent"]
    config = agent.get("config", {})
    baseline_kind = _baseline_kind(summary)
    provider, model = _provider_model(config, records)
    overall = summary["metrics"]["overall"]
    metric_means = overall.get("metric_means", {})
    cost_latency = summary.get("cost_latency", {})
    calibration = calibration_summary_from_records(records)
    failures = extract_eval_failure_cases(records, limit=5)
    robustness_summary = _robustness_summary(run_dir)

    lines = [
        f"# Model card: {_agent_name(summary)}",
        "",
        "## Identity",
        "",
        f"- Model or agent: `{_agent_name(summary)}`",
        f"- Result label: **{baseline_kind}**",
        f"- Provider: `{provider or 'n/a'}`",
        f"- Model: `{model or 'n/a'}`",
        f"- Run ID: `{summary['run_id']}`",
        f"- Run name: `{summary['run_name']}`",
        f"- Date/time: `{summary['timestamp']}`",
        f"- Run directory: `{run_dir}`",
        "",
        "## Evaluation",
        "",
        f"- Environments evaluated: {', '.join(env['name'] for env in summary['environments'])}",
        f"- Number of tasks: `{overall['n_tasks']}`",
        f"- Decoding settings: `{_decoding_settings(config)}`",
        f"- Tool policy: `{config.get('tool_policy') or 'n/a'}`",
        f"- Prompt version: {_prompt_version(config)}",
        f"- Parse/repair policy: {_parse_policy(agent.get('type'))}",
        "",
        "## Metrics",
        "",
        f"- Mean score: `{_fmt(overall.get('mean_score'))}`",
        f"- Mean regret: `{_fmt(metric_means.get('regret'))}`",
        f"- Calibration summary: `{_compact(calibration)}`",
        f"- Risk violation rate: `{_fmt(_risk_violation_rate(records))}`",
        f"- Parse failure rate: `{_fmt(overall.get('parse_failure_rate'))}`",
        f"- Robustness summary: `{_compact(robustness_summary)}`",
        f"- Cost/latency summary: `{_compact(_cost_latency_summary(cost_latency))}`",
        "",
        "## Known Failure Modes",
        "",
    ]
    if not failures:
        lines.append("No deterministic failure cases were extracted from this run.")
    else:
        for failure in failures:
            lines.append(
                "- "
                f"`{failure['environment']}/{failure['task_id']}` "
                f"severity=`{_fmt(failure['severity'])}` "
                f"labels=`{', '.join(failure['labels'])}`: {failure['explanation']}"
            )

    lines.extend(["", "## Limitations", ""])
    for limitation in _limitations(summary, baseline_kind):
        lines.append(f"- {limitation}")
    lines.append("")
    return "\n".join(lines)


def _agent_name(summary: dict[str, Any]) -> str:
    agent = summary.get("agent", {})
    return str(agent.get("name") or summary.get("run_name") or "agent")


def _baseline_kind(summary: dict[str, Any]) -> str:
    value = summary.get("baseline_kind")
    if isinstance(value, str):
        return value
    config = summary.get("agent", {}).get("config", {})
    if isinstance(config, dict):
        try:
            return agent_baseline_kind(AgentConfig(**config))
        except Exception:
            pass
    agent_type = str(summary.get("agent", {}).get("type") or "").lower()
    if agent_type == "reference":
        return "reference sanity check"
    if agent_type == "mock":
        return "mock diagnostic baseline"
    return agent_type or "unknown"


def _provider_model(config: dict[str, Any], records: list[EvalTaskRecord]) -> tuple[str | None, str | None]:
    provider = config.get("provider")
    model = config.get("model") or config.get("model_name")
    if isinstance(provider, str) or isinstance(model, str):
        return provider if isinstance(provider, str) else None, model if isinstance(model, str) else None
    metadata = records[0].metadata.get("response_metadata")
    if isinstance(metadata, dict):
        provider_value = metadata.get("provider")
        model_value = metadata.get("model")
        return (
            provider_value if isinstance(provider_value, str) else None,
            model_value if isinstance(model_value, str) else None,
        )
    return None, None


def _decoding_settings(config: dict[str, Any]) -> dict[str, Any]:
    keys = ("temperature", "top_p", "do_sample", "max_tokens", "max_new_tokens", "seed")
    return {key: config.get(key) for key in keys if config.get(key) is not None}


def _prompt_version(config: dict[str, Any]) -> str:
    if config.get("system_prompt"):
        return "custom system prompt from run config"
    return "MimirBench default prompt templates (no explicit prompt-version tag)"


def _parse_policy(agent_type: Any) -> str:
    value = str(agent_type or "").lower()
    if value in {"api", "direct", "local", "reflective", "tool"}:
        return "deterministic JSON extraction/repair; no hidden chain-of-thought is requested or stored"
    return "deterministic structured baseline output; parser repair is not model-facing"


def _risk_violation_rate(records: list[EvalTaskRecord]) -> float:
    return sum(1 for record in records if is_risk_violation(record.grader_result)) / len(records)


def _robustness_summary(run_dir: Path) -> dict[str, Any] | None:
    path = run_dir / "robustness_summary.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    metrics = data.get("metrics", {})
    return {
        "paraphrase_consistency_rate": metrics.get("paraphrase_consistency_rate"),
        "mean_score_drop": metrics.get("mean_score_drop"),
        "action_flip_rate": metrics.get("action_flip_rate"),
    }


def _cost_latency_summary(cost_latency: dict[str, Any]) -> dict[str, Any]:
    return {
        "estimated_total_cost_usd": cost_latency.get("estimated_total_cost_usd"),
        "cost_note": cost_latency.get("cost_note"),
        "mean_latency_ms": cost_latency.get("mean_latency_ms"),
        "p95_latency_ms": cost_latency.get("p95_latency_ms"),
    }


def _limitations(summary: dict[str, Any], baseline_kind: str) -> list[str]:
    limitations = list(summary.get("known_limitations", []))
    limitations.extend(
        [
            "Results apply only to the saved task set, prompt, parser, and decoding settings.",
            "No LLM judges are used; all grading and failure labels are deterministic.",
            "These benchmark diagnostics are not evidence of trading usefulness or profitability.",
        ]
    )
    if baseline_kind in {
        "reference sanity check",
        "mock diagnostic baseline",
        "deterministic non-model tool baseline",
    }:
        limitations.append("This card describes a non-model baseline, not model capability.")
    return list(dict.fromkeys(limitations))


def _compact(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{value:.6g}"
    return str(value)


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip()).strip("_.-")
    return slug.lower() or "agent"
