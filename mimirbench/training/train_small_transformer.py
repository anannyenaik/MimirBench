"""Train the Stage 7 compact transformer on synthetic Bayesian traces."""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from mimirbench.analysis.plots import generate_training_plots
from mimirbench.reports.model_cards import generate_small_transformer_model_card
from mimirbench.training.datasets import (
    BayesianTraceDatasetConfig,
    export_trace_dataset,
    make_bayesian_trace_dataset,
)
from mimirbench.training.small_transformer import (
    HEAD_NAMES,
    SmallTransformerConfig,
    SmallTransformerForTracePrediction,
    parameter_count,
    require_torch,
)
from mimirbench.training.synthetic_traces import (
    PayoffRiskConfig,
    label_vocab_for_config,
)
from mimirbench.training.tokenizer import TraceTokenizer

__all__ = [
    "ModelConfig",
    "RunConfig",
    "SmallTransformerTrainConfig",
    "TrainConfig",
    "TrainingConfig",
    "generate_traces_from_config",
    "load_config",
    "train",
]

_TARGET_KEYS = {
    "posterior_bucket": "posterior_A_bucket",
    "action": "action",
    "ev_bucket": "ev_bucket",
    "risk_flag": "risk_flag",
    "confidence_bucket": "confidence_bucket",
    "rationale_class": "rationale_class",
}


@dataclass(frozen=True)
class RunConfig:
    """Top-level run metadata."""

    name: str = "small_transformer_bayes_tiny"
    seed: int = 123
    output_dir: str = "reports/training/small_transformer_bayes_tiny"


@dataclass(frozen=True)
class ModelConfig:
    """Transformer architecture settings."""

    d_model: int = 64
    n_layers: int = 2
    n_heads: int = 2
    dim_feedforward: int = 128
    dropout: float = 0.0
    max_seq_len: int = 128
    lm_loss_weight: float = 0.0


@dataclass(frozen=True)
class TrainingConfig:
    """Optimisation settings."""

    batch_size: int = 32
    epochs: int = 2
    learning_rate: float = 1e-3
    weight_decay: float = 0.01
    grad_clip: float = 1.0
    device: str = "cpu"
    early_stopping_patience: int | None = None


@dataclass(frozen=True)
class SmallTransformerTrainConfig:
    """Resolved Stage 7 training configuration."""

    run: RunConfig = field(default_factory=RunConfig)
    data: BayesianTraceDatasetConfig = field(default_factory=BayesianTraceDatasetConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)


TrainConfig = SmallTransformerTrainConfig


def load_config(path: str | Path) -> SmallTransformerTrainConfig:
    """Load a Stage 7 training config from YAML."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("training config must be a YAML mapping.")
    if "run" not in data and "data" not in data and "training" not in data:
        return _load_legacy_config(data)
    run = RunConfig(**_mapping(data.get("run")))
    data_mapping = _mapping(data.get("data"))
    data_mapping.setdefault("seed", run.seed)
    return SmallTransformerTrainConfig(
        run=run,
        data=_load_data_config(data_mapping),
        model=ModelConfig(**_mapping(data.get("model"))),
        training=TrainingConfig(**_mapping(data.get("training"))),
    )


def generate_traces_from_config(
    config_or_path: SmallTransformerTrainConfig | str | Path,
) -> dict[str, Path]:
    """Generate and export JSONL trace splits without training a model."""
    cfg = _coerce_config(config_or_path)
    splits = make_bayesian_trace_dataset(cfg.data)
    output_dir = Path(cfg.run.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_resolved_config(cfg, output_dir / "config_resolved.yaml")
    return export_trace_dataset(splits, output_dir)


def train(
    config: SmallTransformerTrainConfig | str | Path | None = None,
    *,
    model_card_dir: str | Path = Path("reports") / "model_cards",
) -> dict[str, Any]:  # pragma: no cover - torch-dependent path covered when available.
    """Train a compact transformer and write reproducible artefacts.

    ``model_card_dir`` is where the generated model card is written; production
    runs use the default ``reports/model_cards`` (the curated, committed location),
    while tests pass an isolated ``tmp_path`` so the suite never rewrites tracked
    cards with machine-specific paths.
    """
    torch_mod, _, _ = require_torch()
    cfg = _coerce_config(config) if config is not None else SmallTransformerTrainConfig()
    _validate_training_config(cfg)
    _seed_everything(cfg.run.seed, torch_mod)
    device = _resolve_device(cfg.training.device, torch_mod)

    output_dir = Path(cfg.run.output_dir)
    checkpoints_dir = output_dir / "checkpoints"
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    _write_resolved_config(cfg, output_dir / "config_resolved.yaml")

    splits = make_bayesian_trace_dataset(cfg.data)
    export_trace_dataset(
        {"train": splits["train"], "val": splits["val"], "test": splits["test"]},
        output_dir,
    )
    tokenizer = TraceTokenizer.from_traces(splits["train"], max_length=cfg.model.max_seq_len)
    tokenizer_path = tokenizer.save(output_dir / "vocab.json")

    label_vocab = label_vocab_for_config(cfg.data.trace_config())
    label_to_id = {
        head: {label: idx for idx, label in enumerate(labels)}
        for head, labels in label_vocab.items()
    }
    model_config = SmallTransformerConfig(
        vocab_size=tokenizer.vocab_size,
        max_seq_len=cfg.model.max_seq_len,
        d_model=cfg.model.d_model,
        n_layers=cfg.model.n_layers,
        n_heads=cfg.model.n_heads,
        dim_feedforward=cfg.model.dim_feedforward,
        dropout=cfg.model.dropout,
        pad_token_id=tokenizer.pad_id,
        num_posterior_buckets=len(label_vocab["posterior_bucket"]),
        num_actions=len(label_vocab["action"]),
        num_ev_buckets=len(label_vocab["ev_bucket"]),
        num_risk_flags=len(label_vocab["risk_flag"]),
        num_confidence_buckets=len(label_vocab["confidence_bucket"]),
        num_rationale_classes=len(label_vocab["rationale_class"]),
        lm_loss_weight=cfg.model.lm_loss_weight,
    )
    model = SmallTransformerForTracePrediction(model_config, label_vocab=label_vocab).to(device)
    optimizer = torch_mod.optim.AdamW(
        model.parameters(),
        lr=cfg.training.learning_rate,
        weight_decay=cfg.training.weight_decay,
    )

    train_examples = _encode_examples(splits["train"], tokenizer, label_to_id)
    val_examples = _encode_examples(splits["val"], tokenizer, label_to_id)
    metadata = {
        "run_name": cfg.run.name,
        "output_dir": str(output_dir),
        "created_at": _now(),
        "synthetic_data_only": True,
    }

    metrics_path = output_dir / "metrics.jsonl"
    best_val_loss = float("inf")
    best_epoch = 0
    best_metrics: dict[str, Any] = {}
    epochs_without_improvement = 0
    metrics_rows: list[dict[str, Any]] = []
    rng = np.random.default_rng(cfg.run.seed)

    with metrics_path.open("w", encoding="utf-8") as metrics_file:
        for epoch in range(1, cfg.training.epochs + 1):
            train_loss = _train_epoch(
                model=model,
                examples=train_examples,
                optimizer=optimizer,
                batch_size=cfg.training.batch_size,
                grad_clip=cfg.training.grad_clip,
                device=device,
                rng=rng,
            )
            val_metrics = _evaluate_examples(
                model=model,
                examples=val_examples,
                batch_size=cfg.training.batch_size,
                device=device,
            )
            row = {
                "epoch": epoch,
                "train_loss": train_loss,
                **{f"val_{key}": value for key, value in val_metrics.items()},
            }
            metrics_rows.append(row)
            metrics_file.write(json.dumps(row, sort_keys=True) + "\n")
            metrics_file.flush()

            val_loss = float(val_metrics["loss"])
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_epoch = epoch
                best_metrics = row
                epochs_without_improvement = 0
                model.save_checkpoint(
                    checkpoints_dir / "best.pt",
                    tokenizer=tokenizer,
                    metadata={**metadata, "checkpoint_kind": "best", "epoch": epoch},
                )
            else:
                epochs_without_improvement += 1
            if (
                cfg.training.early_stopping_patience is not None
                and epochs_without_improvement >= cfg.training.early_stopping_patience
            ):
                break

    final_checkpoint = model.save_checkpoint(
        checkpoints_dir / "final.pt",
        tokenizer=tokenizer,
        metadata={**metadata, "checkpoint_kind": "final", "epoch": metrics_rows[-1]["epoch"]},
    )
    if not (checkpoints_dir / "best.pt").exists():
        model.save_checkpoint(
            checkpoints_dir / "best.pt",
            tokenizer=tokenizer,
            metadata={**metadata, "checkpoint_kind": "best", "epoch": metrics_rows[-1]["epoch"]},
        )

    figures = generate_training_plots(output_dir)
    summary: dict[str, Any] = {
        "run_name": cfg.run.name,
        "timestamp": _now(),
        "output_dir": str(output_dir),
        "config": asdict(cfg),
        "counts": {
            "train": len(splits["train"]),
            "val": len(splits["val"]),
            "test": len(splits["test"]),
        },
        "model": {
            "architecture": "compact_transformer_encoder",
            "parameter_count": parameter_count(model),
            "target_heads": list(HEAD_NAMES),
            "config": asdict(model_config),
        },
        "best_epoch": best_epoch,
        "best_metrics": best_metrics,
        "final_metrics": metrics_rows[-1] if metrics_rows else {},
        "paths": {
            "config": str(output_dir / "config_resolved.yaml"),
            "vocab": str(tokenizer_path),
            "train_traces": str(output_dir / "train_traces.jsonl"),
            "val_traces": str(output_dir / "val_traces.jsonl"),
            "test_traces": str(output_dir / "test_traces.jsonl"),
            "metrics": str(metrics_path),
            "best_checkpoint": str(checkpoints_dir / "best.pt"),
            "final_checkpoint": str(final_checkpoint),
            "figures": [str(path) for path in figures],
        },
        "known_limitations": [
            "The model is trained only on deterministic synthetic Bayesian traces.",
            "Targets are final labels and concise rationale classes, not hidden chain-of-thought.",
            "Results do not establish frontier-model behaviour or real-world decision quality.",
        ],
    }
    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    card_path = generate_small_transformer_model_card(output_dir, output_dir=model_card_dir)
    summary["paths"]["model_card"] = str(card_path)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def _train_epoch(
    *,
    model: Any,
    examples: list[dict[str, Any]],
    optimizer: Any,
    batch_size: int,
    grad_clip: float,
    device: Any,
    rng: np.random.Generator,
) -> float:
    torch_mod, _, _ = require_torch()
    model.train()
    order = rng.permutation(len(examples))
    total_loss = 0.0
    total_items = 0
    for start in range(0, len(order), batch_size):
        batch = [examples[int(idx)] for idx in order[start : start + batch_size]]
        tensors = _batch_to_tensors(batch, device)
        output = model(
            tensors["input_ids"],
            attention_mask=tensors["attention_mask"],
            labels=tensors["labels"],
        )
        loss = output["loss"]
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        if grad_clip > 0.0:
            torch_mod.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
        optimizer.step()
        total_loss += float(loss.item()) * len(batch)
        total_items += len(batch)
    return total_loss / max(1, total_items)


def _evaluate_examples(
    *,
    model: Any,
    examples: list[dict[str, Any]],
    batch_size: int,
    device: Any,
) -> dict[str, float]:
    torch_mod, _, _ = require_torch()
    model.eval()
    total_loss = 0.0
    total_items = 0
    correct = dict.fromkeys(HEAD_NAMES, 0)
    with torch_mod.no_grad():
        for start in range(0, len(examples), batch_size):
            batch = examples[start : start + batch_size]
            tensors = _batch_to_tensors(batch, device)
            output = model(
                tensors["input_ids"],
                attention_mask=tensors["attention_mask"],
                labels=tensors["labels"],
            )
            total_loss += float(output["loss"].item()) * len(batch)
            total_items += len(batch)
            for head in HEAD_NAMES:
                predictions = output["logits"][head].argmax(dim=-1)
                correct[head] += int((predictions == tensors["labels"][head]).sum().item())
    metrics = {"loss": total_loss / max(1, total_items)}
    metrics.update(
        {f"{head}_accuracy": correct[head] / max(1, total_items) for head in HEAD_NAMES}
    )
    return metrics


def _encode_examples(
    traces: list[dict[str, Any]],
    tokenizer: TraceTokenizer,
    label_to_id: dict[str, dict[str, int]],
) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    for trace in traces:
        input_text = trace.get("input")
        targets = trace.get("targets")
        if not isinstance(input_text, str) or not isinstance(targets, dict):
            raise ValueError("trace must contain string input and target mapping.")
        encoded = tokenizer.encode(input_text)
        labels: dict[str, int] = {}
        for head, target_key in _TARGET_KEYS.items():
            value = targets.get(target_key)
            if not isinstance(value, str):
                raise ValueError(f"trace target {target_key!r} must be a string.")
            labels[head] = label_to_id[head][value]
        examples.append(
            {
                "input_ids": encoded["input_ids"],
                "attention_mask": encoded["attention_mask"],
                "labels": labels,
            }
        )
    return examples


def _batch_to_tensors(batch: list[dict[str, Any]], device: Any) -> dict[str, Any]:
    torch_mod, _, _ = require_torch()
    input_ids = torch_mod.as_tensor(
        [example["input_ids"] for example in batch],
        dtype=torch_mod.long,
        device=device,
    )
    attention_mask = torch_mod.as_tensor(
        [example["attention_mask"] for example in batch],
        dtype=torch_mod.long,
        device=device,
    )
    labels = {
        head: torch_mod.as_tensor(
            [example["labels"][head] for example in batch],
            dtype=torch_mod.long,
            device=device,
        )
        for head in HEAD_NAMES
    }
    return {"input_ids": input_ids, "attention_mask": attention_mask, "labels": labels}


def _coerce_config(
    config_or_path: SmallTransformerTrainConfig | str | Path,
) -> SmallTransformerTrainConfig:
    if isinstance(config_or_path, SmallTransformerTrainConfig):
        return config_or_path
    return load_config(config_or_path)


def _load_data_config(data: dict[str, Any]) -> BayesianTraceDatasetConfig:
    payoff_data = _mapping(data.pop("payoff", None))
    return BayesianTraceDatasetConfig(payoff=PayoffRiskConfig(**payoff_data), **data)


def _load_legacy_config(data: dict[str, Any]) -> SmallTransformerTrainConfig:
    dataset = _mapping(data.get("dataset"))
    n_sequences = int(dataset.get("n_sequences", 512))
    return SmallTransformerTrainConfig(
        run=RunConfig(name="small_transformer_bayes_legacy"),
        data=BayesianTraceDatasetConfig(
            num_train=n_sequences,
            num_val=max(16, n_sequences // 4),
            num_test=max(16, n_sequences // 4),
            seed=int(data.get("seed", dataset.get("seed", 0))),
        ),
        model=ModelConfig(
            d_model=int(data.get("d_model", 64)),
            n_heads=int(data.get("n_heads", 2)),
            n_layers=int(data.get("n_layers", 2)),
            dim_feedforward=int(data.get("dim_feedforward", 128)),
        ),
        training=TrainingConfig(
            batch_size=int(data.get("batch_size", 32)),
            epochs=max(1, int(data.get("steps", 100)) // 100),
            learning_rate=float(data.get("learning_rate", 1e-3)),
            device=str(data.get("device", "cpu")),
        ),
    )


def _validate_training_config(cfg: SmallTransformerTrainConfig) -> None:
    cfg.data.trace_config().validate()
    if cfg.data.num_train <= 0 or cfg.data.num_val <= 0:
        raise ValueError("num_train and num_val must be positive.")
    if cfg.data.num_test < 0:
        raise ValueError("num_test must be non-negative.")
    if cfg.training.batch_size <= 0 or cfg.training.epochs <= 0:
        raise ValueError("batch_size and epochs must be positive.")
    if cfg.training.learning_rate <= 0.0:
        raise ValueError("learning_rate must be positive.")
    if cfg.model.max_seq_len < 8:
        raise ValueError("max_seq_len must be >= 8.")


def _resolve_device(requested: str, torch_mod: Any) -> Any:
    name = requested.lower().strip()
    if name == "auto":
        if torch_mod.cuda.is_available():
            return torch_mod.device("cuda")
        if hasattr(torch_mod.backends, "mps") and torch_mod.backends.mps.is_available():
            return torch_mod.device("mps")
        return torch_mod.device("cpu")
    if name == "cuda" and not torch_mod.cuda.is_available():
        raise RuntimeError("training device 'cuda' requested but CUDA is not available.")
    if name == "mps" and (
        not hasattr(torch_mod.backends, "mps") or not torch_mod.backends.mps.is_available()
    ):
        raise RuntimeError("training device 'mps' requested but MPS is not available.")
    return torch_mod.device(name)


def _seed_everything(seed: int, torch_mod: Any) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch_mod.manual_seed(seed)
    if torch_mod.cuda.is_available():
        torch_mod.cuda.manual_seed_all(seed)


def _write_resolved_config(cfg: SmallTransformerTrainConfig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(asdict(cfg), sort_keys=False), encoding="utf-8")


def _mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("config section must be a mapping.")
    return dict(value)


def _now() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat()
