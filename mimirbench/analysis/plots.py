"""Matplotlib plotting helpers for run and comparison artefacts.

Only Matplotlib is used, imported lazily with the non-interactive ``Agg``
backend. Helpers skip plots whose source artefacts lack the required metric
rather than fabricating empty-looking figures.
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from mimirbench.analysis.calibration import record_confidence_outcomes, reliability_curve
from mimirbench.analysis.regret import record_regrets
from mimirbench.analysis.robustness import score_drop_by_variant_type
from mimirbench.evals.schemas import EvalTaskRecord
from mimirbench.evals.scoring import is_risk_violation
from mimirbench.evals.writers import load_records_jsonl, load_robustness_records_jsonl

__all__ = [
    "generate_comparison_plots",
    "generate_run_plots",
    "generate_training_plots",
    "plot_reliability_diagram",
    "plot_score_histogram",
    "plot_training_loss_curve",
    "plot_validation_accuracy_curve",
]


def plot_score_histogram(
    scores: Sequence[float],
    output_path: str,
    *,
    bins: int = 20,
    title: str = "Score distribution",
) -> str:
    """Save a histogram of per-task scores to ``output_path``."""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(list(scores), bins=bins, range=(0.0, 1.0), edgecolor="white")
    ax.set_xlabel("score")
    ax.set_ylabel("count")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def plot_reliability_diagram(
    mean_predicted: Sequence[float],
    empirical_rate: Sequence[float],
    output_path: str,
    *,
    title: str = "Reliability diagram",
) -> str:
    """Save a reliability diagram (calibration curve) to ``output_path``."""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot([0, 1], [0, 1], linestyle="--", label="perfect calibration")
    ax.plot(list(mean_predicted), list(empirical_rate), marker="o", label="agent")
    ax.set_xlabel("mean predicted probability")
    ax.set_ylabel("empirical outcome rate")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title(title)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def plot_training_loss_curve(
    metrics: Sequence[Mapping[str, Any]],
    output_path: str | Path,
    *,
    title: str = "Training loss",
) -> Path:
    """Save a training-loss curve from metrics JSONL rows."""
    path = Path(output_path)
    plt = _plt()
    fig, ax = plt.subplots(figsize=(6, 4))
    epochs = [int(row["epoch"]) for row in metrics if "epoch" in row and "train_loss" in row]
    values = [float(row["train_loss"]) for row in metrics if "epoch" in row and "train_loss" in row]
    ax.plot(epochs, values, marker="o")
    ax.set_xlabel("epoch")
    ax.set_ylabel("loss")
    ax.set_title(title)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_validation_accuracy_curve(
    metrics: Sequence[Mapping[str, Any]],
    output_path: str | Path,
    *,
    keys: Sequence[str],
    title: str = "Validation accuracy",
) -> Path:
    """Save validation accuracy curves for one or more metric keys."""
    path = Path(output_path)
    plt = _plt()
    fig, ax = plt.subplots(figsize=(6, 4))
    epochs = [int(row["epoch"]) for row in metrics if "epoch" in row]
    for key in keys:
        values = [float(row[key]) for row in metrics if key in row]
        if len(values) == len(epochs):
            ax.plot(epochs, values, marker="o", label=key.removeprefix("val_"))
    ax.set_xlabel("epoch")
    ax.set_ylabel("accuracy")
    ax.set_ylim(0.0, 1.0)
    ax.set_title(title)
    ax.legend(loc="best")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def generate_run_plots(run_dir: str | Path) -> list[Path]:
    """Generate supported figures for one eval or robustness run directory."""
    root = Path(run_dir)
    figures_dir = root / "figures"
    generated: list[Path] = []

    records = load_records_jsonl(root / "results.jsonl")
    if records:
        figures_dir.mkdir(parents=True, exist_ok=True)
        generated.extend(_record_plots({"run": records}, figures_dir))

    robustness_path = root / "robustness_results.jsonl"
    if robustness_path.exists():
        robustness_records = load_robustness_records_jsonl(robustness_path)
        drops = score_drop_by_variant_type(robustness_records)
        if drops:
            figures_dir.mkdir(parents=True, exist_ok=True)
            path = figures_dir / "robustness_score_drop_by_variant_type.png"
            _bar(drops, path, title="Robustness score drop by variant type", ylabel="mean score drop")
            generated.append(path)
    return generated


def generate_comparison_plots(comparison_dir: str | Path) -> list[Path]:
    """Generate supported figures for a comparison directory."""
    root = Path(comparison_dir)
    records_by_agent = _comparison_records(root)
    if not records_by_agent:
        return []
    figures_dir = root / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    return _record_plots(records_by_agent, figures_dir)


def generate_training_plots(training_dir: str | Path) -> list[Path]:
    """Generate loss and validation-accuracy figures for a training run."""
    root = Path(training_dir)
    metrics_path = root / "metrics.jsonl"
    if not metrics_path.exists():
        return []
    metrics = _load_metric_rows(metrics_path)
    if not metrics:
        return []
    figures_dir = root / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    generated = [
        plot_training_loss_curve(metrics, figures_dir / "training_loss.png"),
        plot_validation_accuracy_curve(
            metrics,
            figures_dir / "validation_accuracy.png",
            keys=[
                "val_action_accuracy",
                "val_posterior_bucket_accuracy",
                "val_risk_flag_accuracy",
            ],
        ),
        plot_validation_accuracy_curve(
            metrics,
            figures_dir / "validation_posterior_bucket_accuracy.png",
            keys=["val_posterior_bucket_accuracy"],
            title="Validation posterior bucket accuracy",
        ),
        plot_validation_accuracy_curve(
            metrics,
            figures_dir / "validation_risk_accuracy.png",
            keys=["val_risk_flag_accuracy"],
            title="Validation risk accuracy",
        ),
    ]
    return generated


def _comparison_records(root: Path) -> dict[str, list[EvalTaskRecord]]:
    agent_root = root / "agent_runs"
    if not agent_root.exists():
        return {}
    records: dict[str, list[EvalTaskRecord]] = {}
    for path in sorted(agent_root.iterdir()):
        if not path.is_dir():
            continue
        rows = load_records_jsonl(path / "results.jsonl")
        if rows:
            records[path.name] = rows
    return records


def _load_metric_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            row = json.loads(text)
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _record_plots(records_by_agent: Mapping[str, list[EvalTaskRecord]], figures_dir: Path) -> list[Path]:
    generated: list[Path] = []
    all_records = [record for records in records_by_agent.values() for record in records]

    path = figures_dir / "score_by_environment.png"
    _score_by_environment(records_by_agent, path)
    generated.append(path)

    regret = record_regrets(all_records)
    if regret:
        path = figures_dir / "regret_distribution.png"
        _hist(regret, path, title="Regret distribution", xlabel="regret")
        generated.append(path)

    posterior_errors = _metric_values(all_records, ("posterior_tv_error", "posterior_l1_error"))
    if posterior_errors:
        path = figures_dir / "posterior_error_distribution.png"
        _hist(posterior_errors, path, title="Posterior error distribution", xlabel="posterior error")
        generated.append(path)

    confidences, outcomes = record_confidence_outcomes(all_records)
    if confidences:
        mean_predicted, empirical_rate = reliability_curve(confidences, outcomes)
        path = figures_dir / "calibration_curve.png"
        plot_reliability_diagram(
            mean_predicted.tolist(),
            empirical_rate.tolist(),
            str(path),
            title="Calibration curve",
        )
        generated.append(path)

    path = figures_dir / "risk_violation_rate_by_environment.png"
    _risk_violation_by_environment(records_by_agent, path)
    generated.append(path)

    latencies = [record.latency_ms for record in all_records if record.latency_ms is not None]
    if latencies:
        path = figures_dir / "latency_distribution.png"
        _hist(latencies, path, title="Latency distribution", xlabel="latency (ms)")
        generated.append(path)

    costs = _cost_by_agent(records_by_agent)
    if costs:
        path = figures_dir / "cost_by_agent_provider.png"
        _bar(costs, path, title="Estimated cost by agent/provider", ylabel="estimated cost (USD)")
        generated.append(path)

    path = figures_dir / "parse_failure_rate_by_agent.png"
    _bar(
        _parse_failure_by_agent(records_by_agent),
        path,
        title="Parse failure rate by agent",
        ylabel="parse failure rate",
    )
    generated.append(path)
    return generated


def _score_by_environment(records_by_agent: Mapping[str, list[EvalTaskRecord]], path: Path) -> None:
    by_agent_env: dict[str, dict[str, list[float]]] = {}
    environments: set[str] = set()
    for agent, records in records_by_agent.items():
        env_scores: dict[str, list[float]] = defaultdict(list)
        for record in records:
            env_scores[record.environment].append(record.grader_result.score)
            environments.add(record.environment)
        by_agent_env[agent] = env_scores
    labels = sorted(environments)
    series = {
        agent: [_mean(by_agent_env[agent].get(env, [])) for env in labels]
        for agent in sorted(by_agent_env)
    }
    _grouped_bar(
        labels,
        series,
        path,
        title="Score by environment",
        ylabel="mean score",
        ylim=(0.0, 1.0),
    )


def _risk_violation_by_environment(records_by_agent: Mapping[str, list[EvalTaskRecord]], path: Path) -> None:
    by_agent_env: dict[str, dict[str, list[float]]] = {}
    environments: set[str] = set()
    for agent, records in records_by_agent.items():
        env_rates: dict[str, list[float]] = defaultdict(list)
        for record in records:
            env_rates[record.environment].append(1.0 if is_risk_violation(record.grader_result) else 0.0)
            environments.add(record.environment)
        by_agent_env[agent] = env_rates
    labels = sorted(environments)
    series = {
        agent: [_mean(by_agent_env[agent].get(env, [])) for env in labels]
        for agent in sorted(by_agent_env)
    }
    _grouped_bar(
        labels,
        series,
        path,
        title="Risk violation rate by environment",
        ylabel="risk violation rate",
        ylim=(0.0, 1.0),
    )


def _parse_failure_by_agent(records_by_agent: Mapping[str, list[EvalTaskRecord]]) -> dict[str, float]:
    return {
        agent: sum(1 for record in records if record.parsed_response is None) / len(records)
        for agent, records in sorted(records_by_agent.items())
        if records
    }


def _cost_by_agent(records_by_agent: Mapping[str, list[EvalTaskRecord]]) -> dict[str, float]:
    costs: dict[str, float] = {}
    for agent, records in sorted(records_by_agent.items()):
        values = [_record_cost(record) for record in records]
        numeric = [value for value in values if value is not None]
        if numeric:
            costs[_agent_provider_label(agent, records)] = sum(numeric)
    return costs


def _agent_provider_label(agent: str, records: list[EvalTaskRecord]) -> str:
    if not records:
        return agent
    metadata = records[0].metadata.get("response_metadata")
    if isinstance(metadata, dict):
        provider = metadata.get("provider")
        model = metadata.get("model")
        if isinstance(provider, str) and isinstance(model, str):
            return f"{agent}\n{provider}/{model}"
    return agent


def _record_cost(record: EvalTaskRecord) -> float | None:
    metadata = record.metadata.get("response_metadata")
    if not isinstance(metadata, dict):
        return None
    usage = metadata.get("usage")
    if not isinstance(usage, dict):
        return None
    value = usage.get("estimated_cost_usd")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _metric_values(records: Sequence[EvalTaskRecord], names: tuple[str, ...]) -> list[float]:
    values: list[float] = []
    for record in records:
        for name in names:
            value = record.grader_result.metrics.get(name)
            if value is not None:
                values.append(float(value))
                break
    return values


def _hist(values: Sequence[float], path: Path, *, title: str, xlabel: str) -> None:
    plt = _plt()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(list(values), bins=min(20, max(5, len(values))))
    ax.set_xlabel(xlabel)
    ax.set_ylabel("count")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _bar(values: Mapping[str, float], path: Path, *, title: str, ylabel: str) -> None:
    plt = _plt()
    labels = list(values)
    fig, ax = plt.subplots(figsize=_figsize(labels))
    ax.bar(labels, [values[label] for label in labels])
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.tick_params(axis="x", labelrotation=30)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _grouped_bar(
    labels: list[str],
    series: Mapping[str, list[float]],
    path: Path,
    *,
    title: str,
    ylabel: str,
    ylim: tuple[float, float] | None = None,
) -> None:
    plt = _plt()
    fig, ax = plt.subplots(figsize=_figsize(labels))
    if not labels:
        labels = ["none"]
    names = list(series)
    x_positions = list(range(len(labels)))
    width = 0.8 / max(1, len(names))
    for offset, name in enumerate(names):
        shifts = [x + (offset - (len(names) - 1) / 2) * width for x in x_positions]
        ax.bar(shifts, series[name], width=width, label=name)
    ax.set_xticks(x_positions, labels)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    if ylim is not None:
        ax.set_ylim(*ylim)
    if len(names) > 1:
        ax.legend(loc="best")
    ax.tick_params(axis="x", labelrotation=30)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _figsize(labels: Sequence[str]) -> tuple[float, float]:
    return (max(6.0, min(14.0, 1.2 * len(labels))), 4.5)


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _plt() -> Any:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt
