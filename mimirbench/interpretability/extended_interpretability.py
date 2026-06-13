"""Extended, local-only interpretability: position-resolved patching + controls.

This driver deepens Stage 8 without any paid API calls. On the trained medium
checkpoint it runs:

* **token-group (position-resolved) activation patching** — patch only the
  prior / evidence / payoff-risk token positions of each sub-block site;
* a **mismatched-donor negative control** — patch with a clean activation from an
  unrelated same-length example;
* a **label-shuffle probe control** — refit the action probe on shuffled labels,
  which should collapse to the majority baseline.

If the checkpoint or torch is missing it writes a ``status="pending"`` report
explaining exactly what is needed, rather than failing the repository.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from mimirbench.interpretability.counterfactuals import generate_counterfactual_pairs
from mimirbench.interpretability.runner import (
    InterpretabilityConfig,
    load_interpretability_config,
)
from mimirbench.interpretability.token_group_patching import (
    run_mismatched_donor_control,
    run_token_group_patching,
)
from mimirbench.training.synthetic_traces import generate_trace_splits

__all__ = ["run_extended_interpretability"]

_NO_FRONTIER_CLAIM = (
    "These results characterise one small, fully synthetic Bayesian transformer. "
    "They are not evidence about frontier-model internals and must not be read that way."
)
_LABEL_SHUFFLE_SITE = "blocks.1.mlp_out"
_LABEL_SHUFFLE_LABEL = "action"


@dataclass(frozen=True)
class _Readiness:
    ready: bool
    blockers: list[str]


def run_extended_interpretability(
    config: InterpretabilityConfig | str | Path,
) -> dict[str, Any]:
    """Run the extended experiments and write all artefacts. No model is downloaded."""
    cfg = config if isinstance(config, InterpretabilityConfig) else load_interpretability_config(config)
    cfg.validate()
    output_dir = Path(cfg.run.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    readiness = _check_readiness(Path(cfg.model.checkpoint_path), Path(cfg.model.vocab_path))
    if not readiness.ready:
        return _write_pending(cfg, output_dir, readiness.blockers)

    from mimirbench.training.small_transformer import SmallTransformerForTracePrediction
    from mimirbench.training.tokenizer import TraceTokenizer

    model, payload = SmallTransformerForTracePrediction.load_checkpoint(
        Path(cfg.model.checkpoint_path), map_location=cfg.model.device
    )
    model.to(cfg.model.device)
    tokenizer = _load_tokenizer(TraceTokenizer, Path(cfg.model.vocab_path), payload)

    pairs = generate_counterfactual_pairs(
        cfg.data.num_pairs, config=cfg.data.trace_config(), seed=cfg.data.seed, split="interp"
    )
    splits = generate_trace_splits(
        num_train=cfg.data.num_examples,
        num_val=max(8, cfg.data.num_examples // 2),
        num_test=max(8, cfg.data.num_examples // 2),
        config=cfg.data.trace_config(),
    )

    token_group = run_token_group_patching(model, tokenizer, pairs)
    mismatched = run_mismatched_donor_control(model, tokenizer, pairs, seed=cfg.run.seed)
    label_shuffle = _label_shuffle_control(cfg, model, tokenizer, splits)

    summary: dict[str, Any] = {
        "run_name": cfg.run.name,
        "timestamp": _now(),
        "status": "complete",
        "output_dir": output_dir.as_posix(),
        "checkpoint_path": Path(cfg.model.checkpoint_path).as_posix(),
        "model": {
            "n_layers": model.config.n_layers,
            "d_model": model.config.d_model,
            "n_heads": model.config.n_heads,
        },
        "data": {"num_pairs": len(pairs), "seed": cfg.data.seed},
        "token_group_patching": token_group.summary,
        "mismatched_donor_control": {"site": mismatched.site, **mismatched.summary},
        "label_shuffle_control": label_shuffle,
        "no_frontier_claim": _NO_FRONTIER_CLAIM,
    }

    _write_jsonl(output_dir / "token_group_patching.jsonl", token_group.rows)
    _write_jsonl(output_dir / "mismatched_donor_control.jsonl", mismatched.rows)
    report_path = _write_report(cfg, summary, output_dir)
    summary["report_path"] = report_path.as_posix()
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    return summary


def _label_shuffle_control(
    cfg: InterpretabilityConfig,
    model: Any,
    tokenizer: Any,
    splits: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    from mimirbench.interpretability.activation_capture import (
        DEFAULT_LABEL_KEYS,
        capture_trace_activations,
    )
    from mimirbench.interpretability.probes import train_probe

    label_keys = dict(DEFAULT_LABEL_KEYS)
    label_classes = {name: list(model.label_vocab.get(name, [])) for name in label_keys}
    sites = [_LABEL_SHUFFLE_SITE]
    captured = {
        split: capture_trace_activations(
            model,
            tokenizer,
            traces,
            sites=sites,
            label_keys=label_keys,
            label_classes=label_classes,
            batch_size=cfg.batch_size,
        )
        for split, traces in splits.items()
    }
    label = _LABEL_SHUFFLE_LABEL
    real = train_probe(
        site=_LABEL_SHUFFLE_SITE,
        label=label,
        class_names=label_classes[label],
        train_features=captured["train"].features[_LABEL_SHUFFLE_SITE],
        train_labels=captured["train"].labels[label],
        val_features=captured["val"].features[_LABEL_SHUFFLE_SITE],
        val_labels=captured["val"].labels[label],
        test_features=captured["test"].features[_LABEL_SHUFFLE_SITE],
        test_labels=captured["test"].labels[label],
        alpha=cfg.alpha,
    )
    rng = np.random.default_rng(cfg.run.seed)
    shuffled_labels = np.asarray(captured["train"].labels[label]).copy()
    rng.shuffle(shuffled_labels)
    shuffled = train_probe(
        site=_LABEL_SHUFFLE_SITE,
        label=label,
        class_names=label_classes[label],
        train_features=captured["train"].features[_LABEL_SHUFFLE_SITE],
        train_labels=shuffled_labels,
        val_features=captured["val"].features[_LABEL_SHUFFLE_SITE],
        val_labels=captured["val"].labels[label],
        test_features=captured["test"].features[_LABEL_SHUFFLE_SITE],
        test_labels=captured["test"].labels[label],
        alpha=cfg.alpha,
    )
    return {
        "site": _LABEL_SHUFFLE_SITE,
        "label": label,
        "real_test_accuracy": real.test_accuracy,
        "shuffled_test_accuracy": shuffled.test_accuracy,
        "majority_baseline_accuracy": real.majority_baseline_accuracy,
        "interpretation": (
            "A genuine signal collapses to ~baseline when labels are shuffled; a large "
            "real-minus-shuffled gap indicates the probe reads structure, not noise."
        ),
    }


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #


def _write_report(cfg: InterpretabilityConfig, summary: dict[str, Any], output_dir: Path) -> Path:
    model = summary["model"]
    lines = [
        f"# Extended interpretability report: {cfg.run.name}",
        "",
        f"- Generated: {summary['timestamp']}",
        f"- Checkpoint analysed: `{summary['checkpoint_path']}`",
        f"- Model: compact transformer encoder ({model['n_layers']} layers, "
        f"d_model={model['d_model']}, {model['n_heads']} heads)",
        f"- Counterfactual pairs: {summary['data']['num_pairs']} (seed {summary['data']['seed']})",
        "",
        "All experiments are local, deterministic, CPU-only; no model is downloaded "
        "and no API is called.",
        "",
        "## Position-resolved (token-group) activation patching",
        "",
        "Each sub-block site is patched **only at the positions of one token group**. "
        "The corruption changes only the evidence (observation) tokens, so the `prior` "
        "and `payoff_risk` groups are designed negative controls: restoring them should "
        "recover the decision far less than restoring `evidence`.",
        "",
        "| Site | Group | Action recovery | Mean action causal effect | n flipped |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    by_site = summary["token_group_patching"]["by_site"]
    for site, groups in by_site.items():
        for group, block in groups.items():
            action = block.get("heads", {}).get("action", {})
            lines.append(
                f"| {site} | {group} | {_fmt(block.get('action_recovery_rate'))} | "
                f"{_fmt(block.get('mean_causal_effect_action'))} | {action.get('n_flipped', 0)} |"
            )
    lines.extend(
        [
            "",
            "Recovery is computed over pairs whose action the corruption flipped. A high "
            "`evidence` recovery with low `prior` / `payoff_risk` recovery localises the "
            "causal evidence-to-decision signal to the evidence token positions.",
            "",
            "## Mismatched-donor negative control",
            "",
            f"At `{summary['mismatched_donor_control']['site']}`, each flipped pair is "
            "patched with its own clean activation (matched) and with a clean activation "
            "from an unrelated same-length example (mismatched).",
            "",
            "| Head | Matched recovery | Mismatched recovery | n flipped | n with donor |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for head, block in summary["mismatched_donor_control"]["by_head"].items():
        lines.append(
            f"| {head} | {_fmt(block.get('matched_recovery_rate'))} | "
            f"{_fmt(block.get('mismatched_recovery_rate'))} | {block.get('n_flipped', 0)} | "
            f"{block.get('n_with_mismatched_donor', 0)} |"
        )
    shuffle = summary["label_shuffle_control"]
    lines.extend(
        [
            "",
            "A matched recovery well above the mismatched recovery confirms the patch "
            "restores the *specific* clean computation, not a generic activation shift.",
            "",
            "## Label-shuffle probe control",
            "",
            f"- Site / label: `{shuffle['site']}` / `{shuffle['label']}`",
            f"- Real probe test accuracy: `{_fmt(shuffle['real_test_accuracy'])}`",
            f"- Shuffled-label probe test accuracy: `{_fmt(shuffle['shuffled_test_accuracy'])}`",
            f"- Majority baseline: `{_fmt(shuffle['majority_baseline_accuracy'])}`",
            "",
            shuffle["interpretation"],
            "",
            "## Scope and Limitations",
            "",
            "- One checkpoint, one seed, one narrow synthetic Bayesian/risk generator.",
            "- Position-resolved patching is at the token-group level; it does not isolate "
            "individual heads or neurons, and uses no sparse autoencoder.",
            "- Negative or near-zero results are reported as-is.",
            f"- {_NO_FRONTIER_CLAIM}",
            "",
        ]
    )
    report_path = output_dir / "EXTENDED_INTERPRETABILITY_REPORT.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def _write_pending(
    cfg: InterpretabilityConfig, output_dir: Path, blockers: list[str]
) -> dict[str, Any]:
    summary = {
        "run_name": cfg.run.name,
        "timestamp": _now(),
        "status": "pending",
        "output_dir": output_dir.as_posix(),
        "checkpoint_path": cfg.model.checkpoint_path,
        "blockers": blockers,
        "no_frontier_claim": _NO_FRONTIER_CLAIM,
    }
    lines = [
        f"# Extended interpretability report: {cfg.run.name}",
        "",
        "> **Status: pending.** The experiments could not run yet.",
        "",
        "## Blockers",
        "",
        *[f"- {item}" for item in blockers],
        "",
        "Resolve the blockers (train the medium checkpoint with "
        "`mimirbench train-small-transformer configs/train_small_transformer_bayes_medium.yaml` "
        "and install the `ml` extra), then rerun "
        "`mimirbench run-extended-interpretability configs/interp_bayes_medium_extended.yaml`.",
        "",
        f"{_NO_FRONTIER_CLAIM}",
        "",
    ]
    (output_dir / "EXTENDED_INTERPRETABILITY_REPORT.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    return summary


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _check_readiness(checkpoint: Path, vocab: Path) -> _Readiness:
    blockers: list[str] = []
    try:
        from mimirbench.training.small_transformer import require_torch

        require_torch()
    except ImportError as exc:
        blockers.append(f"torch is unavailable ({exc}); install the 'ml' extra.")
    if not checkpoint.exists():
        blockers.append(f"checkpoint not found: {checkpoint}")
    if not vocab.exists():
        blockers.append(f"vocab not found: {vocab}")
    return _Readiness(ready=not blockers, blockers=blockers)


def _load_tokenizer(tokenizer_cls: Any, vocab: Path, payload: dict[str, Any]) -> Any:
    if vocab.exists():
        return tokenizer_cls.load(vocab)
    tokenizer_payload = payload.get("tokenizer")
    if isinstance(tokenizer_payload, dict):
        return tokenizer_cls.from_dict(tokenizer_payload)
    raise ValueError("no tokenizer vocab available (checkpoint or vocab_path).")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{value:.3f}"
    return str(value)


def _now() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat()
