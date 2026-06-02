"""Orchestrate the Stage 8 interpretability experiments end to end.

Given a small YAML config, the runner: loads a trained checkpoint and tokenizer;
deterministically generates synthetic Bayesian traces and counterfactual pairs;
runs the requested experiments (linear probes, activation patching, attention
analysis); and writes JSON/JSONL artefacts, figures, and a Markdown report.

If the checkpoint or vocab is missing — or torch is unavailable — it does not
crash: it writes a report that states the experiments are *pending* and returns a
summary with ``status="pending"``. Torch is imported lazily.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from mimirbench.interpretability.attention_analysis import AttentionAnalysisResult
from mimirbench.interpretability.counterfactuals import (
    generate_counterfactual_pairs,
)
from mimirbench.interpretability.probes import ProbeResult
from mimirbench.training.synthetic_traces import (
    BayesianTraceConfig,
    PayoffRiskConfig,
    generate_trace_splits,
)

__all__ = [
    "InterpretabilityConfig",
    "load_interpretability_config",
    "run_interpretability",
]

# Probe label -> output filename stem.
_PROBE_FILES = {
    "posterior_bucket": "posterior_probe",
    "action": "action_probe",
    "risk_flag": "risk_probe",
    "confidence_bucket": "confidence_probe",
}

_NO_FRONTIER_CLAIM = (
    "These results characterise one small, fully synthetic Bayesian transformer. "
    "They are not evidence about frontier-model internals and must not be read that way."
)


@dataclass(frozen=True)
class InterpRunConfig:
    name: str = "interp_bayes_all_tiny"
    seed: int = 123
    output_dir: str = "reports/interpretability/interp_bayes_all_tiny"


@dataclass(frozen=True)
class InterpModelConfig:
    checkpoint_path: str = "reports/training/small_transformer_bayes_tiny/checkpoints/best.pt"
    vocab_path: str = "reports/training/small_transformer_bayes_tiny/vocab.json"
    device: str = "cpu"


@dataclass(frozen=True)
class InterpDataConfig:
    source: str = "synthetic"
    num_examples: int = 64
    num_pairs: int = 32
    seed: int = 123
    num_hypotheses: int = 2
    min_observations: int = 1
    max_observations: int = 6
    signal_reliability: float = 0.7
    posterior_buckets: int = 20
    payoff: PayoffRiskConfig = field(default_factory=PayoffRiskConfig)

    def trace_config(self) -> BayesianTraceConfig:
        return BayesianTraceConfig(
            seed=self.seed,
            num_hypotheses=self.num_hypotheses,
            min_observations=self.min_observations,
            max_observations=self.max_observations,
            signal_reliability=self.signal_reliability,
            posterior_buckets=self.posterior_buckets,
            payoff=self.payoff,
        )


@dataclass(frozen=True)
class InterpExperimentsConfig:
    probes: bool = True
    activation_patching: bool = True
    attention_analysis: bool = True


@dataclass(frozen=True)
class InterpretabilityConfig:
    run: InterpRunConfig = field(default_factory=InterpRunConfig)
    model: InterpModelConfig = field(default_factory=InterpModelConfig)
    data: InterpDataConfig = field(default_factory=InterpDataConfig)
    experiments: InterpExperimentsConfig = field(default_factory=InterpExperimentsConfig)
    sites: list[str] | None = None
    batch_size: int = 16
    max_examples: int | None = None
    alpha: float = 1.0

    def validate(self) -> None:
        self.data.trace_config().validate()
        if self.data.num_examples <= 0:
            raise ValueError("data.num_examples must be positive.")
        if self.data.num_pairs <= 0:
            raise ValueError("data.num_pairs must be positive.")
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive.")
        if self.alpha < 0:
            raise ValueError("alpha must be >= 0.")


def load_interpretability_config(path: str | Path) -> InterpretabilityConfig:
    """Load and validate an interpretability config from YAML."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("interpretability config must be a YAML mapping.")
    run = InterpRunConfig(**_mapping(data.get("run")))
    data_mapping = _mapping(data.get("data"))
    data_mapping.setdefault("seed", run.seed)
    config = InterpretabilityConfig(
        run=run,
        model=InterpModelConfig(**_mapping(data.get("model"))),
        data=_load_data_config(data_mapping),
        experiments=InterpExperimentsConfig(**_mapping(data.get("experiments"))),
        sites=_optional_str_list(data.get("sites")),
        batch_size=int(data.get("batch_size", 16)),
        max_examples=_optional_int(data.get("max_examples")),
        alpha=float(data.get("alpha", 1.0)),
    )
    config.validate()
    return config


def run_interpretability(config: InterpretabilityConfig | str | Path) -> dict[str, Any]:
    """Run the configured experiments and write all artefacts.

    Returns a top-level ``summary`` dict (also written to ``summary.json``).
    """
    cfg = config if isinstance(config, InterpretabilityConfig) else load_interpretability_config(config)
    cfg.validate()
    output_dir = Path(cfg.run.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_resolved_config(cfg, output_dir / "config_resolved.yaml")

    torch_available, torch_detail = _torch_status()
    checkpoint = Path(cfg.model.checkpoint_path)
    vocab = Path(cfg.model.vocab_path)
    blockers = _readiness_blockers(checkpoint, vocab, torch_available, torch_detail)
    if blockers:
        return _write_pending(cfg, output_dir, blockers)

    # Torch is available and artefacts exist: import the heavy paths now.
    from mimirbench.training.small_transformer import (
        SmallTransformerForTracePrediction,
        interpretability_site_names,
    )
    from mimirbench.training.tokenizer import TraceTokenizer

    model, payload = SmallTransformerForTracePrediction.load_checkpoint(
        checkpoint, map_location=cfg.model.device
    )
    model.to(cfg.model.device)
    tokenizer = _load_tokenizer(TraceTokenizer, vocab, payload)
    sites = cfg.sites or list(interpretability_site_names(model.config.n_layers))

    splits = generate_trace_splits(
        num_train=cfg.data.num_examples,
        num_val=max(8, cfg.data.num_examples // 2),
        num_test=max(8, cfg.data.num_examples // 2),
        config=cfg.data.trace_config(),
    )
    pairs = generate_counterfactual_pairs(
        cfg.data.num_pairs, config=cfg.data.trace_config(), seed=cfg.data.seed, split="interp"
    )

    experiments_run: list[str] = []
    summary: dict[str, Any] = {
        "run_name": cfg.run.name,
        "timestamp": _now(),
        "status": "complete",
        "output_dir": output_dir.as_posix(),
        "checkpoint_path": checkpoint.as_posix(),
        "vocab_path": vocab.as_posix(),
        "model": {
            "architecture": "compact_transformer_encoder",
            "n_layers": model.config.n_layers,
            "d_model": model.config.d_model,
            "n_heads": model.config.n_heads,
            "sites": sites,
        },
        "data": {
            "source": cfg.data.source,
            "num_examples": cfg.data.num_examples,
            "num_pairs": len(pairs),
            "seed": cfg.data.seed,
        },
        "experiments": {},
        "no_frontier_claim": _NO_FRONTIER_CLAIM,
    }

    if cfg.experiments.probes:
        summary["experiments"]["probes"] = _run_probes(
            cfg, model, tokenizer, splits, sites, output_dir
        )
        experiments_run.append("probes")
    if cfg.experiments.activation_patching:
        summary["experiments"]["activation_patching"] = _run_patching(
            model, tokenizer, pairs, sites, output_dir
        )
        experiments_run.append("activation_patching")
    if cfg.experiments.attention_analysis:
        summary["experiments"]["attention_analysis"] = _run_attention(
            cfg, model, tokenizer, splits["test"], output_dir
        )
        experiments_run.append("attention_analysis")

    summary["experiments_run"] = experiments_run
    report_path = _write_report(cfg, summary, output_dir)
    summary["report_path"] = report_path.as_posix()
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    return summary


# --------------------------------------------------------------------------- #
# Experiment drivers
# --------------------------------------------------------------------------- #


def _run_probes(
    cfg: InterpretabilityConfig,
    model: Any,
    tokenizer: Any,
    splits: Mapping[str, list[dict[str, Any]]],
    sites: list[str],
    output_dir: Path,
) -> dict[str, Any]:
    from mimirbench.interpretability.activation_capture import (
        DEFAULT_LABEL_KEYS,
        capture_trace_activations,
    )
    from mimirbench.interpretability.probes import train_probe

    probes_dir = output_dir / "probes"
    figures_dir = probes_dir / "figures"
    probes_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    label_keys = dict(DEFAULT_LABEL_KEYS)
    label_classes = {name: list(model.label_vocab.get(name, [])) for name in label_keys}
    captured = {
        split: capture_trace_activations(
            model,
            tokenizer,
            traces,
            sites=sites,
            label_keys=label_keys,
            label_classes=label_classes,
            batch_size=cfg.batch_size,
            metadata={
                "dataset_split": split,
                "checkpoint_path": cfg.model.checkpoint_path,
                "config_path": (output_dir / "config_resolved.yaml").as_posix(),
            },
        )
        for split, traces in splits.items()
    }
    # Persist the captured activations for reproducibility/inspection.
    activations_dir = output_dir / "activations"
    activations_dir.mkdir(parents=True, exist_ok=True)
    for split, capture in captured.items():
        capture.save(activations_dir / f"{split}")

    per_label: dict[str, list[ProbeResult]] = {}
    for label in label_keys:
        results: list[ProbeResult] = []
        for site in sites:
            results.append(
                train_probe(
                    site=site,
                    label=label,
                    class_names=label_classes[label],
                    train_features=captured["train"].features[site],
                    train_labels=captured["train"].labels[label],
                    val_features=captured["val"].features[site],
                    val_labels=captured["val"].labels[label],
                    test_features=captured["test"].features[site],
                    test_labels=captured["test"].labels[label],
                    alpha=cfg.alpha,
                )
            )
        per_label[label] = results
        payload = {
            "label": label,
            "sites": sites,
            "results": [r.to_dict() for r in results],
        }
        (probes_dir / f"{_PROBE_FILES[label]}.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
        )

    figures = _probe_figures(per_label, sites, figures_dir)
    headline = {
        label: _best_probe_row(results) for label, results in per_label.items()
    }
    summary = {
        "labels": list(label_keys),
        "sites": sites,
        "headline": headline,
        "files": {
            label: (probes_dir / f"{_PROBE_FILES[label]}.json").as_posix() for label in label_keys
        },
        "figures": [path.as_posix() for path in figures],
        "activations_dir": activations_dir.as_posix(),
    }
    (probes_dir / "probe_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    return summary


def _run_patching(
    model: Any,
    tokenizer: Any,
    pairs: list[Any],
    sites: list[str],
    output_dir: Path,
) -> dict[str, Any]:
    from mimirbench.interpretability.activation_patching import run_activation_patching

    patch_dir = output_dir / "activation_patching"
    figures_dir = patch_dir / "figures"
    patch_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    result = run_activation_patching(model, tokenizer, pairs, sites=sites)
    with (patch_dir / "patching_results.jsonl").open("w", encoding="utf-8") as handle:
        for row in result.rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    summary_payload = {
        "sites": result.sites,
        "heads": result.heads,
        "num_pairs": result.metadata.get("num_pairs"),
        "summary": result.summary,
    }
    (patch_dir / "patching_summary.json").write_text(
        json.dumps(summary_payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    figures = _patching_figures(result.summary, result.sites, figures_dir)
    return {
        "sites": result.sites,
        "heads": result.heads,
        "num_pairs": result.metadata.get("num_pairs"),
        "best_action_recovery_site": result.summary.get("best_action_recovery_site"),
        "by_site": result.summary["by_site"],
        "results_path": (patch_dir / "patching_results.jsonl").as_posix(),
        "summary_path": (patch_dir / "patching_summary.json").as_posix(),
        "figures": [path.as_posix() for path in figures],
    }


def _run_attention(
    cfg: InterpretabilityConfig,
    model: Any,
    tokenizer: Any,
    traces: list[dict[str, Any]],
    output_dir: Path,
) -> dict[str, Any]:
    from mimirbench.interpretability.attention_analysis import run_attention_analysis

    attn_dir = output_dir / "attention"
    figures_dir = attn_dir / "figures"
    attn_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    limit = cfg.max_examples if cfg.max_examples is not None else min(32, len(traces))
    result = run_attention_analysis(model, tokenizer, traces, max_examples=limit)
    (attn_dir / "attention_summary.json").write_text(
        json.dumps(result.summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    with (attn_dir / "attention_examples.jsonl").open("w", encoding="utf-8") as handle:
        for example in result.examples:
            handle.write(json.dumps(example, sort_keys=True) + "\n")
    figures = _attention_figures(result, figures_dir)
    return {
        "by_layer": result.summary["by_layer"],
        "n_examples": result.summary["n_examples"],
        "summary_path": (attn_dir / "attention_summary.json").as_posix(),
        "examples_path": (attn_dir / "attention_examples.jsonl").as_posix(),
        "figures": [path.as_posix() for path in figures],
    }


# --------------------------------------------------------------------------- #
# Figures (matplotlib imported lazily, Agg backend)
# --------------------------------------------------------------------------- #


def _probe_figures(
    per_label: Mapping[str, list[ProbeResult]],
    sites: list[str],
    figures_dir: Path,
) -> list[Path]:
    paths: list[Path] = []
    names = {
        "posterior_bucket": "posterior_probe_accuracy_by_layer.png",
        "action": "action_probe_accuracy_by_layer.png",
        "risk_flag": "risk_probe_accuracy_by_layer.png",
        "confidence_bucket": "confidence_probe_accuracy_by_layer.png",
    }
    for label, results in per_label.items():
        path = figures_dir / names.get(label, f"{label}_probe_accuracy_by_layer.png")
        test_acc = [r.test_accuracy for r in results]
        baseline = [r.majority_baseline_accuracy for r in results]
        _bar_with_baseline(
            sites, test_acc, baseline, path,
            title=f"{label} probe accuracy by site", ylabel="test accuracy",
        )
        paths.append(path)
    return paths


def _patching_figures(
    summary: Mapping[str, Any], sites: list[str], figures_dir: Path
) -> list[Path]:
    by_site = summary["by_site"]
    causal = [by_site[s]["heads"]["action"].get("mean_causal_effect") or 0.0 for s in sites]
    label_recovery = [by_site[s].get("label_recovery_rate") or 0.0 for s in sites]
    action_recovery = [by_site[s].get("action_recovery_rate") or 0.0 for s in sites]
    paths = [
        _simple_bar(sites, causal, figures_dir / "causal_effect_by_layer.png",
                    title="Action-head causal effect by site", ylabel="patched - corrupted prob"),
        _simple_bar(sites, label_recovery, figures_dir / "label_recovery_by_layer.png",
                    title="Label recovery rate by site", ylabel="recovery rate"),
        _simple_bar(sites, action_recovery, figures_dir / "action_recovery_by_layer.png",
                    title="Action recovery rate by site", ylabel="recovery rate"),
    ]
    return paths


def _attention_figures(result: AttentionAnalysisResult, figures_dir: Path) -> list[Path]:
    by_layer = result.summary["by_layer"]
    layers = sorted(by_layer.keys(), key=int)
    entropy = [by_layer[layer]["mean_entropy"] for layer in layers]
    evidence = [by_layer[layer]["mean_group_mass"]["evidence"] for layer in layers]
    prior = [by_layer[layer]["mean_group_mass"]["prior"] for layer in layers]
    labels = [f"layer {layer}" for layer in layers]
    return [
        _simple_bar(labels, entropy, figures_dir / "attention_entropy_by_layer.png",
                    title="Mean attention entropy by layer", ylabel="entropy (nats)"),
        _simple_bar(labels, evidence, figures_dir / "evidence_attention_by_layer.png",
                    title="Attention mass on evidence tokens by layer", ylabel="mean mass"),
        _simple_bar(labels, prior, figures_dir / "prior_attention_by_layer.png",
                    title="Attention mass on prior tokens by layer", ylabel="mean mass"),
    ]


def _bar_with_baseline(
    labels: list[str],
    values: list[float],
    baseline: list[float],
    path: Path,
    *,
    title: str,
    ylabel: str,
) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    positions = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(positions, values, width=0.6, label="probe test accuracy")
    ax.plot(positions, baseline, color="crimson", marker="o", linestyle="--", label="majority baseline")
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_ylim(0.0, 1.0)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def _simple_bar(
    labels: list[str], values: list[float], path: Path, *, title: str, ylabel: str
) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    positions = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(positions, values, width=0.6, color="steelblue")
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #


def _write_report(cfg: InterpretabilityConfig, summary: dict[str, Any], output_dir: Path) -> Path:
    lines: list[str] = [
        f"# Interpretability report: {cfg.run.name}",
        "",
        f"- Generated: {summary['timestamp']}",
        f"- Checkpoint analysed: `{summary['checkpoint_path']}`",
        f"- Tokenizer/vocab: `{summary['vocab_path']}`",
        "- Model: compact transformer encoder "
        f"({summary['model']['n_layers']} layer(s), d_model={summary['model']['d_model']}, "
        f"{summary['model']['n_heads']} head(s))",
        f"- Dataset: {summary['data']['num_examples']} synthetic traces/split, "
        f"{summary['data']['num_pairs']} counterfactual pairs (seed {summary['data']['seed']})",
        f"- Experiments run: {', '.join(summary['experiments_run']) or 'none'}",
        "",
        "## What is analysed",
        "",
        "Whether the small transformer's internal activations linearly encode the "
        "Bayesian posterior bucket, the action, the risk flag, and the confidence "
        "bucket (probes), and whether those activations are *causally* responsible "
        "for the decision (clean/corrupted activation patching). Attention analysis "
        "reports how attention mass is distributed across the prior, likelihood, "
        "evidence, and payoff/risk token groups.",
        "",
    ]
    experiments = summary.get("experiments", {})
    if "probes" in experiments:
        lines.extend(_probe_report_section(experiments["probes"]))
    if "activation_patching" in experiments:
        lines.extend(_patching_report_section(experiments["activation_patching"]))
    if "attention_analysis" in experiments:
        lines.extend(_attention_report_section(experiments["attention_analysis"]))

    lines.extend(
        [
            "## What would count as causal evidence",
            "",
            "- A patch at a specific site that consistently moves the corrupted "
            "prediction back to the clean decision (high recovery rate, positive "
            "causal effect concentrated at that site).",
            "- A probe direction whose ablation degrades the matching decision.",
            "",
            "## What would NOT count as causal evidence",
            "",
            "- High probe accuracy alone (decodability is correlational, not causal).",
            "- Causal effects within noise, or recovery rates near the flip rate.",
            "- Any result here transferring to larger or frontier models.",
            "",
            "## Limitations and caveats",
            "",
            "- The model is tiny (see header), fully synthetic, and trained on a "
            "narrow Bayesian generator; mean pooling dilutes individual token effects.",
            "- Probe/patching numbers are specific to this checkpoint and seed.",
            "- Negative or near-zero results are reported as-is and are expected for an "
            "underpowered model organism.",
            f"- {_NO_FRONTIER_CLAIM}",
            "",
        ]
    )
    report_path = output_dir / "INTERPRETABILITY_REPORT.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def _probe_report_section(probes: dict[str, Any]) -> list[str]:
    lines = ["## Probe results", "", "| Label | Best site | Test acc | Baseline | Above baseline |", "| --- | --- | ---: | ---: | ---: |"]
    for label, row in probes.get("headline", {}).items():
        lines.append(
            f"| {label} | {row['site']} | {row['test_accuracy']:.3f} | "
            f"{row['majority_baseline_accuracy']:.3f} | {row['test_accuracy_above_baseline']:+.3f} |"
        )
    lines.extend(
        [
            "",
            "Accuracy above the majority-class baseline indicates linear decodability; "
            "it does not by itself establish that the model uses that information.",
            "",
        ]
    )
    return lines


def _patching_report_section(patching: dict[str, Any]) -> list[str]:
    lines = [
        "## Activation patching results",
        "",
        f"- Counterfactual pairs: {patching.get('num_pairs')}",
        f"- Best action-recovery site: {patching.get('best_action_recovery_site') or 'n/a'}",
        "",
        "| Site | Action causal effect | Action recovery | Label recovery |",
        "| --- | ---: | ---: | ---: |",
    ]
    for site, block in patching.get("by_site", {}).items():
        action = block.get("heads", {}).get("action", {})
        lines.append(
            f"| {site} | {_fmt(action.get('mean_causal_effect'))} | "
            f"{_fmt(block.get('action_recovery_rate'))} | {_fmt(block.get('label_recovery_rate'))} |"
        )
    lines.extend(
        [
            "",
            "`causal_effect = P(clean target | patched) - P(clean target | corrupted)`. "
            "Recovery rate is computed over pairs whose prediction the corruption flipped.",
            "",
        ]
    )
    return lines


def _attention_report_section(attention: dict[str, Any]) -> list[str]:
    lines = [
        "## Attention analysis results",
        "",
        f"- Examples analysed: {attention.get('n_examples')}",
        "",
        "| Layer | Mean entropy | Prior mass | Evidence mass | Payoff/risk mass |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for layer, block in attention.get("by_layer", {}).items():
        mass = block.get("mean_group_mass", {})
        lines.append(
            f"| {layer} | {_fmt(block.get('mean_entropy'))} | {_fmt(mass.get('prior'))} | "
            f"{_fmt(mass.get('evidence'))} | {_fmt(mass.get('payoff_risk'))} |"
        )
    lines.append("")
    return lines


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _write_pending(
    cfg: InterpretabilityConfig, output_dir: Path, blockers: list[str]
) -> dict[str, Any]:
    summary = {
        "run_name": cfg.run.name,
        "timestamp": _now(),
        "status": "pending",
        "output_dir": output_dir.as_posix(),
        "checkpoint_path": cfg.model.checkpoint_path,
        "vocab_path": cfg.model.vocab_path,
        "blockers": blockers,
        "experiments_run": [],
        "no_frontier_claim": _NO_FRONTIER_CLAIM,
    }
    lines = [
        f"# Interpretability report: {cfg.run.name}",
        "",
        "> **Status: pending.** The experiments could not run yet.",
        "",
        "## Blockers",
        "",
        *[f"- {item}" for item in blockers],
        "",
        "The interpretability infrastructure is implemented and tested; rerun this "
        "config once the blockers above are resolved (e.g. train the checkpoint with "
        "`mimirbench train-small-transformer ...` and install the `ml` extra).",
        "",
        f"{_NO_FRONTIER_CLAIM}",
        "",
    ]
    (output_dir / "INTERPRETABILITY_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    return summary


def _readiness_blockers(
    checkpoint: Path, vocab: Path, torch_available: bool, torch_detail: str
) -> list[str]:
    blockers: list[str] = []
    if not torch_available:
        blockers.append(f"torch is unavailable ({torch_detail}); install the 'ml' extra.")
    if not checkpoint.exists():
        blockers.append(f"checkpoint not found: {checkpoint}")
    if not vocab.exists():
        blockers.append(f"vocab not found: {vocab}")
    return blockers


def _torch_status() -> tuple[bool, str]:
    try:
        from mimirbench.training.small_transformer import require_torch

        require_torch()
    except ImportError as exc:
        return False, str(exc)
    return True, "ok"


def _load_tokenizer(tokenizer_cls: Any, vocab: Path, payload: Mapping[str, Any]) -> Any:
    if vocab.exists():
        return tokenizer_cls.load(vocab)
    tokenizer_payload = payload.get("tokenizer")
    if isinstance(tokenizer_payload, dict):
        return tokenizer_cls.from_dict(tokenizer_payload)
    raise ValueError("no tokenizer vocab available (checkpoint or vocab_path).")


def _best_probe_row(results: list[ProbeResult]) -> dict[str, Any]:
    best = max(results, key=lambda r: r.test_accuracy)
    return best.to_dict()


def _load_data_config(data: dict[str, Any]) -> InterpDataConfig:
    payoff_data = _mapping(data.pop("payoff", None))
    return InterpDataConfig(payoff=PayoffRiskConfig(**payoff_data), **data)


def _write_resolved_config(cfg: InterpretabilityConfig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(asdict(cfg), sort_keys=False), encoding="utf-8")


def _mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("config section must be a mapping.")
    return dict(value)


def _optional_str_list(value: Any) -> list[str] | None:
    if value is None:
        return None
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError("sites must be a list of strings.")
    return list(value)


def _optional_int(value: Any) -> int | None:
    return None if value is None else int(value)


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{value:.3f}"
    return str(value)


def _now() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat()
