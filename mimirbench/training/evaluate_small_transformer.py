"""Evaluate a trained small transformer on held-out synthetic Bayesian tasks."""

from __future__ import annotations

import json
import time
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from mimirbench.artefacts import artefact_path, write_json
from mimirbench.reports.model_cards import generate_small_transformer_model_card
from mimirbench.training.datasets import BayesianTraceDatasetConfig, make_bayesian_trace_dataset
from mimirbench.training.small_transformer import SmallTransformerForTracePrediction, require_torch
from mimirbench.training.synthetic_traces import (
    PayoffRiskConfig,
    bucket_midpoint,
    regret_for_action,
)
from mimirbench.training.tokenizer import TraceTokenizer

__all__ = [
    "EvalDataConfig",
    "EvalRunConfig",
    "SmallTransformerEvalConfig",
    "evaluate_checkpoint",
    "load_eval_config",
    "token_accuracy",
]


@dataclass(frozen=True)
class EvalRunConfig:
    """Evaluation run metadata."""

    name: str = "small_transformer_bayes_eval"
    seed: int = 10_000
    output_dir: str = "reports/runs/small_transformer_bayes_eval"


@dataclass(frozen=True)
class EvalDataConfig:
    """Held-out synthetic Bayesian task settings."""

    num_tasks: int = 128
    num_hypotheses: int = 2
    min_observations: int = 1
    max_observations: int = 6
    signal_reliability: float = 0.7
    posterior_buckets: int = 20
    payoff: PayoffRiskConfig = field(default_factory=PayoffRiskConfig)


@dataclass(frozen=True)
class SmallTransformerEvalConfig:
    """Checkpoint evaluation config."""

    run: EvalRunConfig = field(default_factory=EvalRunConfig)
    checkpoint_path: str = "reports/training/small_transformer_bayes_tiny/checkpoints/best.pt"
    device: str = "cpu"
    data: EvalDataConfig = field(default_factory=EvalDataConfig)


def token_accuracy(predictions: Sequence[int], targets: Sequence[int]) -> float:
    """Fraction of predictions that match targets."""
    pred = np.asarray(predictions)
    tgt = np.asarray(targets)
    if pred.shape != tgt.shape:
        raise ValueError("predictions and targets must have the same shape.")
    if pred.size == 0:
        raise ValueError("predictions must be non-empty.")
    return float(np.mean(pred == tgt))


def load_eval_config(path: str | Path) -> SmallTransformerEvalConfig:
    """Load checkpoint evaluation config from YAML."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("eval config must be a YAML mapping.")
    return SmallTransformerEvalConfig(
        run=EvalRunConfig(**_mapping(data.get("run"))),
        checkpoint_path=str(data.get("checkpoint_path", SmallTransformerEvalConfig.checkpoint_path)),
        device=str(data.get("device", "cpu")),
        data=_load_data_config(_mapping(data.get("data"))),
    )


def evaluate_checkpoint(
    config: SmallTransformerEvalConfig | str | Path,
    *,
    model_card_dir: str | Path = Path("reports") / "model_cards",
) -> dict[str, Any]:  # pragma: no cover - torch-dependent path covered when available.
    """Evaluate a saved checkpoint and write JSONL, summary, report, and figures.

    ``model_card_dir`` defaults to the curated ``reports/model_cards`` for
    production runs; tests pass an isolated ``tmp_path`` so the suite never
    rewrites tracked cards with machine-specific paths.
    """
    torch_mod, _, _ = require_torch()
    cfg = load_eval_config(config) if isinstance(config, (str, Path)) else config
    if cfg.data.num_tasks <= 0:
        raise ValueError("data.num_tasks must be positive.")
    checkpoint = Path(cfg.checkpoint_path)
    if not checkpoint.exists():
        raise FileNotFoundError(f"checkpoint not found: {checkpoint}")
    device = _resolve_device(cfg.device, torch_mod)

    model, payload = SmallTransformerForTracePrediction.load_checkpoint(
        checkpoint,
        map_location=str(device),
    )
    model.to(device)
    tokenizer_payload = payload.get("tokenizer")
    if not isinstance(tokenizer_payload, dict):
        raise ValueError("checkpoint is missing tokenizer payload.")
    tokenizer = TraceTokenizer.from_dict(tokenizer_payload)

    data_config = BayesianTraceDatasetConfig(
        num_train=0,
        num_val=0,
        num_test=cfg.data.num_tasks,
        seed=cfg.run.seed,
        num_hypotheses=cfg.data.num_hypotheses,
        min_observations=cfg.data.min_observations,
        max_observations=cfg.data.max_observations,
        signal_reliability=cfg.data.signal_reliability,
        posterior_buckets=cfg.data.posterior_buckets,
        payoff=cfg.data.payoff,
    )
    traces = make_bayesian_trace_dataset(data_config)["test"]
    output_dir = Path(cfg.run.output_dir)
    figures_dir = output_dir / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "config_resolved.yaml").write_text(
        yaml.safe_dump(asdict(cfg), sort_keys=False),
        encoding="utf-8",
        newline="\n",
    )

    rows: list[dict[str, Any]] = []
    for trace in traces:
        start = time.perf_counter()
        valid = True
        error: str | None = None
        prediction: dict[str, Any] = {}
        try:
            encoded = tokenizer.encode(str(trace["input"]))
            input_ids = torch_mod.as_tensor(
                [encoded["input_ids"]],
                dtype=torch_mod.long,
                device=device,
            )
            attention_mask = torch_mod.as_tensor(
                [encoded["attention_mask"]],
                dtype=torch_mod.long,
                device=device,
            )
            prediction = dict(model.predict(input_ids, attention_mask=attention_mask))
        except Exception as exc:  # pragma: no cover - defensive invalid-rate path.
            valid = False
            error = str(exc)
        latency_ms = (time.perf_counter() - start) * 1000.0
        row = _score_prediction(trace, prediction, valid=valid, error=error, latency_ms=latency_ms)
        rows.append(row)

    results_path = output_dir / "results.jsonl"
    with results_path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    metrics = _summarise_rows(rows)
    summary: dict[str, Any] = {
        "run_name": cfg.run.name,
        "timestamp": _now(),
        "output_dir": artefact_path(output_dir),
        "checkpoint_path": artefact_path(checkpoint),
        "config": asdict(cfg),
        "metrics": metrics,
        "paths": {
            "results": artefact_path(results_path),
            "summary": artefact_path(output_dir / "summary.json"),
            "report": artefact_path(output_dir / "report.md"),
            "figures": [],
        },
        "known_limitations": [
            "Evaluation is held out from training but still synthetic and generator-bound.",
            "Posterior error is approximate because the model predicts a posterior bucket.",
        ],
    }
    figure_paths = _write_eval_figures(rows, figures_dir)
    summary["paths"]["figures"] = [artefact_path(path) for path in figure_paths]
    write_json(summary, output_dir / "summary.json")
    (output_dir / "report.md").write_text(_render_report(summary), encoding="utf-8", newline="\n")

    training_dir = _training_dir_from_payload(payload)
    if training_dir is not None and training_dir.exists():
        card_path = generate_small_transformer_model_card(
            training_dir, eval_dir=output_dir, output_dir=model_card_dir
        )
        summary["paths"]["model_card"] = artefact_path(card_path)
        write_json(summary, output_dir / "summary.json")
    return summary


def _score_prediction(
    trace: dict[str, Any],
    prediction: dict[str, Any],
    *,
    valid: bool,
    error: str | None,
    latency_ms: float,
) -> dict[str, Any]:
    targets = trace["targets"]
    posterior_label = prediction.get("posterior_bucket")
    posterior_error = None
    if isinstance(posterior_label, str):
        posterior_error = abs(bucket_midpoint(posterior_label) - float(trace["metadata"]["posterior"][0]))
    predicted_action = prediction.get("action")
    regret = None
    if isinstance(predicted_action, str):
        try:
            regret = regret_for_action(trace, predicted_action)
        except ValueError:
            valid = False
    return {
        "trace_id": trace["id"],
        "input": trace["input"],
        "targets": targets,
        "prediction": prediction,
        "valid": valid,
        "error": error,
        "latency_ms": latency_ms,
        "metrics": {
            "posterior_bucket_correct": _correct(prediction, "posterior_bucket", targets["posterior_A_bucket"]),
            "action_correct": _correct(prediction, "action", targets["action"]),
            "risk_flag_correct": _correct(prediction, "risk_flag", targets["risk_flag"]),
            "confidence_bucket_correct": _correct(
                prediction,
                "confidence_bucket",
                targets["confidence_bucket"],
            ),
            "posterior_abs_error": posterior_error,
            "regret": regret,
            "invalid": 0.0 if valid else 1.0,
        },
    }


def _summarise_rows(rows: list[dict[str, Any]]) -> dict[str, float]:
    metrics = {
        "posterior_bucket_accuracy": _mean_metric(rows, "posterior_bucket_correct"),
        "action_accuracy": _mean_metric(rows, "action_correct"),
        "risk_flag_accuracy": _mean_metric(rows, "risk_flag_correct"),
        "confidence_bucket_accuracy": _mean_metric(rows, "confidence_bucket_correct"),
        "approx_posterior_abs_error_mean": _mean_metric(rows, "posterior_abs_error"),
        "regret_mean": _mean_metric(rows, "regret"),
        "invalid_response_rate": _mean_metric(rows, "invalid"),
        "latency_mean_ms": _mean_value([float(row["latency_ms"]) for row in rows]),
        "latency_p50_ms": _percentile([float(row["latency_ms"]) for row in rows], 50),
        "latency_p95_ms": _percentile([float(row["latency_ms"]) for row in rows], 95),
    }
    return metrics


def _write_eval_figures(rows: list[dict[str, Any]], figures_dir: Path) -> list[Path]:
    posterior_errors = _metric_values(rows, "posterior_abs_error")
    regrets = _metric_values(rows, "regret")
    generated: list[Path] = []
    if posterior_errors:
        path = figures_dir / "posterior_abs_error.png"
        _hist(posterior_errors, path, title="Approximate posterior error", xlabel="absolute error")
        generated.append(path)
    if regrets:
        path = figures_dir / "regret.png"
        _hist(regrets, path, title="Regret", xlabel="regret")
        generated.append(path)
    return generated


def _render_report(summary: dict[str, Any]) -> str:
    metrics = summary["metrics"]
    return "\n".join(
        [
            f"# Small transformer Bayesian evaluation: {summary['run_name']}",
            "",
            f"- Checkpoint: `{summary['checkpoint_path']}`",
            f"- Posterior bucket accuracy: `{metrics['posterior_bucket_accuracy']:.4f}`",
            f"- Action accuracy: `{metrics['action_accuracy']:.4f}`",
            f"- Risk flag accuracy: `{metrics['risk_flag_accuracy']:.4f}`",
            f"- Confidence bucket accuracy: `{metrics['confidence_bucket_accuracy']:.4f}`",
            f"- Approximate posterior absolute error: `{metrics['approx_posterior_abs_error_mean']:.4f}`",
            f"- Mean regret: `{metrics['regret_mean']:.4f}`",
            f"- Invalid response rate: `{metrics['invalid_response_rate']:.4f}`",
            "",
            "This report covers a small synthetic model on held-out synthetic Bayesian tasks. "
            "It is not evidence of frontier-model behaviour.",
            "",
        ]
    )


def _correct(prediction: dict[str, Any], key: str, target: str) -> float:
    return 1.0 if prediction.get(key) == target else 0.0


def _mean_metric(rows: list[dict[str, Any]], key: str) -> float:
    return _mean_value(_metric_values(rows, key))


def _metric_values(rows: list[dict[str, Any]], key: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = row["metrics"].get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            values.append(float(value))
    return values


def _mean_value(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _percentile(values: Sequence[float], q: float) -> float:
    if not values:
        return 0.0
    return float(np.percentile(np.asarray(values, dtype=np.float64), q))


def _hist(values: Sequence[float], path: Path, *, title: str, xlabel: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(list(values), bins=min(20, max(5, len(values))))
    ax.set_xlabel(xlabel)
    ax.set_ylabel("count")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _load_data_config(data: dict[str, Any]) -> EvalDataConfig:
    payoff_data = _mapping(data.pop("payoff", None))
    return EvalDataConfig(payoff=PayoffRiskConfig(**payoff_data), **data)


def _mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("config section must be a mapping.")
    return dict(value)


def _resolve_device(requested: str, torch_mod: Any) -> Any:
    name = requested.lower().strip()
    if name == "auto":
        if torch_mod.cuda.is_available():
            return torch_mod.device("cuda")
        if hasattr(torch_mod.backends, "mps") and torch_mod.backends.mps.is_available():
            return torch_mod.device("mps")
        return torch_mod.device("cpu")
    if name == "cuda" and not torch_mod.cuda.is_available():
        raise RuntimeError("device 'cuda' requested but CUDA is not available.")
    if name == "mps" and (
        not hasattr(torch_mod.backends, "mps") or not torch_mod.backends.mps.is_available()
    ):
        raise RuntimeError("device 'mps' requested but MPS is not available.")
    return torch_mod.device(name)


def _training_dir_from_payload(payload: dict[str, Any]) -> Path | None:
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        return None
    output_dir = metadata.get("output_dir")
    return Path(output_dir) if isinstance(output_dir, str) else None


def _now() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat()
