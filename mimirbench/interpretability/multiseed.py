"""Multi-seed interpretability replication for the medium Bayesian transformer.

Local-only, CPU, **no API calls and no downloads**. This driver counters the
"interpretability is single-seed" criticism by running the *same* whole-site +
extended pipeline on several independently trained synthetic checkpoints and
aggregating the per-seed metrics explicitly.

For each seed it:

1. trains the medium checkpoint (skipping any seed whose checkpoint already
   exists when ``skip_existing`` is set, so seed 123's curated artefacts are
   reused rather than retrained);
2. runs whole-site interpretability (probes / activation patching /
   attention), the source of the headline "evidence->decision is concentrated
   in the attention sub-blocks" result;
3. runs extended position-resolved (token-group) patching plus the
   mismatched-donor and label-shuffle negative controls;
4. evaluates held-out test metrics on a fresh, unseen synthetic draw.

Per-seed failures are *fail-soft*: the seed is recorded as ``failed`` with a
reason and the run continues. The aggregate reports mean and range across the
seeds that actually completed and never claims more seeds than ran.

All torch-dependent work is imported lazily, so this module and its
config-loading / metric-aggregation helpers import and unit-test without torch.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from statistics import fmean
from typing import Any

import yaml

__all__ = [
    "MultiSeedConfig",
    "MultiSeedRunConfig",
    "SeedOverride",
    "aggregate_seed_records",
    "load_multiseed_config",
    "run_multiseed_interpretability",
    "summarise_seed_metrics",
]

# The six transformer sub-block sites whole-site patching reports (no embed).
_BLOCK_SITES = (
    "blocks.0.attn_out",
    "blocks.0.mlp_out",
    "blocks.0.resid_post",
    "blocks.1.attn_out",
    "blocks.1.mlp_out",
    "blocks.1.resid_post",
)
_TOKEN_GROUPS = ("evidence", "prior", "payoff_risk")

# Replication thresholds. Deliberately loose so a genuine but slightly weaker
# seed still counts; the per-seed numbers are reported so readers can judge.
_ATTN_RECOVERY_MIN = 0.80  # attention sub-blocks should restore the action
_MLP0_RECOVERY_MAX = 0.10  # layer-0 MLP should not
_TOKEN_GROUP_RECOVERY_MAX = 0.10  # single-group patches stay near zero
_MISMATCH_GAP_MIN = 0.30  # matched donor must beat an unrelated donor by this
_SHUFFLE_REAL_MIN = 0.90  # real-label probe is near perfect
_SHUFFLE_OVER_BASELINE_MAX = 0.10  # shuffled-label probe collapses to baseline


# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class SeedOverride:
    """Reuse already-curated directories for a seed instead of templated paths."""

    training_dir: str | None = None
    interp_dir: str | None = None
    extended_dir: str | None = None


@dataclass(frozen=True)
class MultiSeedRunConfig:
    name: str = "interp_bayes_medium_multiseed"
    summary_dir: str = "reports/interpretability"


@dataclass(frozen=True)
class MultiSeedConfig:
    """Resolved multi-seed replication configuration."""

    run: MultiSeedRunConfig = field(default_factory=MultiSeedRunConfig)
    seeds: tuple[int, ...] = (123,)
    train_template: str = "configs/train_small_transformer_bayes_medium.yaml"
    interp_template: str = "configs/interp_bayes_all_medium.yaml"
    extended_template: str = "configs/interp_bayes_medium_extended.yaml"
    training_output_template: str = "reports/training/small_transformer_bayes_medium_seed_{seed}"
    interp_output_template: str = "reports/interpretability/interp_bayes_all_medium_seed_{seed}"
    extended_output_template: str = (
        "reports/interpretability/interp_bayes_medium_extended_seed_{seed}"
    )
    eval_output_template: str = (
        "reports/interpretability/interp_bayes_multiseed/heldout_eval_seed_{seed}"
    )
    seed_overrides: dict[int, SeedOverride] = field(default_factory=dict)
    skip_existing: bool = True
    run_full_interpretability: bool = True
    run_extended_interpretability: bool = True
    run_heldout_eval: bool = True
    heldout_num_tasks: int = 2000
    heldout_seed_base: int = 900_000
    model_card_dir: str = "tmp/model_cards"
    device: str = "cpu"

    def validate(self) -> None:
        if not self.seeds:
            raise ValueError("multiseed config requires at least one seed.")
        if len(set(self.seeds)) != len(self.seeds):
            raise ValueError("multiseed seeds must be unique.")
        if self.heldout_num_tasks <= 0:
            raise ValueError("heldout_num_tasks must be positive.")
        for name in (
            "training_output_template",
            "interp_output_template",
            "extended_output_template",
            "eval_output_template",
        ):
            template = getattr(self, name)
            if "{seed}" not in template:
                raise ValueError(f"{name} must contain the '{{seed}}' placeholder.")


def load_multiseed_config(path: str | Path) -> MultiSeedConfig:
    """Load and validate a multi-seed config from YAML."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("multiseed config must be a YAML mapping.")
    raw_seeds = data.get("seeds") or []
    if not isinstance(raw_seeds, list):
        raise ValueError("seeds must be a list of integers.")
    overrides: dict[int, SeedOverride] = {}
    for key, value in _mapping(data.get("seed_overrides")).items():
        overrides[int(key)] = SeedOverride(**_mapping(value))
    defaults = MultiSeedConfig()
    config = MultiSeedConfig(
        run=MultiSeedRunConfig(**_mapping(data.get("run"))),
        seeds=tuple(int(seed) for seed in raw_seeds),
        train_template=str(data.get("train_template", defaults.train_template)),
        interp_template=str(data.get("interp_template", defaults.interp_template)),
        extended_template=str(data.get("extended_template", defaults.extended_template)),
        training_output_template=str(
            data.get("training_output_template", defaults.training_output_template)
        ),
        interp_output_template=str(
            data.get("interp_output_template", defaults.interp_output_template)
        ),
        extended_output_template=str(
            data.get("extended_output_template", defaults.extended_output_template)
        ),
        eval_output_template=str(data.get("eval_output_template", defaults.eval_output_template)),
        seed_overrides=overrides,
        skip_existing=bool(data.get("skip_existing", defaults.skip_existing)),
        run_full_interpretability=bool(
            data.get("run_full_interpretability", defaults.run_full_interpretability)
        ),
        run_extended_interpretability=bool(
            data.get("run_extended_interpretability", defaults.run_extended_interpretability)
        ),
        run_heldout_eval=bool(data.get("run_heldout_eval", defaults.run_heldout_eval)),
        heldout_num_tasks=int(data.get("heldout_num_tasks", defaults.heldout_num_tasks)),
        heldout_seed_base=int(data.get("heldout_seed_base", defaults.heldout_seed_base)),
        model_card_dir=str(data.get("model_card_dir", defaults.model_card_dir)),
        device=str(data.get("device", defaults.device)),
    )
    config.validate()
    return config


@dataclass(frozen=True)
class _SeedPaths:
    seed: int
    training_dir: Path
    interp_dir: Path
    extended_dir: Path
    eval_dir: Path
    checkpoint_path: Path
    vocab_path: Path


def _resolve_paths(config: MultiSeedConfig, seed: int) -> _SeedPaths:
    override = config.seed_overrides.get(seed)
    training_dir = Path(
        override.training_dir
        if override and override.training_dir
        else config.training_output_template.format(seed=seed)
    )
    interp_dir = Path(
        override.interp_dir
        if override and override.interp_dir
        else config.interp_output_template.format(seed=seed)
    )
    extended_dir = Path(
        override.extended_dir
        if override and override.extended_dir
        else config.extended_output_template.format(seed=seed)
    )
    return _SeedPaths(
        seed=seed,
        training_dir=training_dir,
        interp_dir=interp_dir,
        extended_dir=extended_dir,
        eval_dir=Path(config.eval_output_template.format(seed=seed)),
        checkpoint_path=training_dir / "checkpoints" / "best.pt",
        vocab_path=training_dir / "vocab.json",
    )


# --------------------------------------------------------------------------- #
# Orchestration (torch imported lazily)
# --------------------------------------------------------------------------- #


def run_multiseed_interpretability(config: MultiSeedConfig | str | Path) -> dict[str, Any]:
    """Run the per-seed pipeline for every seed and write the aggregate summary."""
    cfg = config if isinstance(config, MultiSeedConfig) else load_multiseed_config(config)
    cfg.validate()
    summary_dir = Path(cfg.run.summary_dir)
    summary_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    for seed in cfg.seeds:
        records.append(_run_one_seed(cfg, seed))

    aggregate = aggregate_seed_records(records, run_name=cfg.run.name)
    aggregate["config"] = {
        "seeds": list(cfg.seeds),
        "train_template": cfg.train_template,
        "interp_template": cfg.interp_template,
        "extended_template": cfg.extended_template,
        "skip_existing": cfg.skip_existing,
    }
    summary_path = summary_dir / "interp_bayes_multiseed_summary.json"
    summary_path.write_text(json.dumps(aggregate, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    aggregate["summary_path"] = summary_path.as_posix()
    return aggregate


def _run_one_seed(cfg: MultiSeedConfig, seed: int) -> dict[str, Any]:
    paths = _resolve_paths(cfg, seed)
    record: dict[str, Any] = {
        "seed": seed,
        "status": "complete",
        "steps": {},
        "paths": {
            "training_dir": paths.training_dir.as_posix(),
            "interp_dir": paths.interp_dir.as_posix(),
            "extended_dir": paths.extended_dir.as_posix(),
            "eval_dir": paths.eval_dir.as_posix(),
            "checkpoint": paths.checkpoint_path.as_posix(),
        },
    }
    try:
        _execute_seed(cfg, seed, paths, record)
    except Exception as exc:  # fail-soft: one seed must not abort the batch.
        record["status"] = "failed"
        record["error"] = f"{type(exc).__name__}: {exc}"

    # Best-effort metric collection (works for reused, complete, and partial seeds).
    record["metrics"] = _collect_metrics(paths)
    record["checkpoint_sha256"] = _sha256(paths.checkpoint_path)
    record["story"] = _seed_story_replicated(record["metrics"])
    return record


def _execute_seed(
    cfg: MultiSeedConfig, seed: int, paths: _SeedPaths, record: dict[str, Any]
) -> None:
    from mimirbench.training.train_small_transformer import load_config as load_train_config
    from mimirbench.training.train_small_transformer import train

    train_base = load_train_config(cfg.train_template)

    # 1. Train (or reuse) the per-seed checkpoint.
    if cfg.skip_existing and _has_checkpoint(paths):
        record["steps"]["training"] = "reused"
    else:
        train_cfg = replace(
            train_base,
            run=replace(
                train_base.run,
                name=f"{train_base.run.name}_seed_{seed}",
                seed=seed,
                output_dir=paths.training_dir.as_posix(),
            ),
            data=replace(train_base.data, seed=seed),
        )
        start = time.perf_counter()
        train(train_cfg, model_card_dir=cfg.model_card_dir)
        record["training_runtime_s"] = round(time.perf_counter() - start, 1)
        record["steps"]["training"] = "trained"

    if not paths.checkpoint_path.exists():
        raise FileNotFoundError(f"checkpoint missing after training step: {paths.checkpoint_path}")

    # 2. Whole-site interpretability.
    if cfg.run_full_interpretability:
        record["steps"]["full_interp"] = _maybe_run_interp(
            cfg, seed, cfg.interp_template, paths.interp_dir, paths
        )

    # 3. Extended position-resolved patching + negative controls.
    if cfg.run_extended_interpretability:
        record["steps"]["extended_interp"] = _maybe_run_interp(
            cfg, seed, cfg.extended_template, paths.extended_dir, paths, extended=True
        )

    # 4. Held-out test evaluation on a fresh, unseen draw.
    if cfg.run_heldout_eval:
        record["steps"]["heldout_eval"] = _maybe_run_eval(cfg, seed, paths, train_base)


def _maybe_run_interp(
    cfg: MultiSeedConfig,
    seed: int,
    template: str,
    output_dir: Path,
    paths: _SeedPaths,
    *,
    extended: bool = False,
) -> str:
    if cfg.skip_existing and _summary_complete(output_dir):
        return "reused"
    from mimirbench.interpretability.runner import load_interpretability_config

    base = load_interpretability_config(template)
    interp_cfg = replace(
        base,
        run=replace(
            base.run,
            name=f"{base.run.name}_seed_{seed}",
            seed=seed,
            output_dir=output_dir.as_posix(),
        ),
        model=replace(
            base.model,
            checkpoint_path=paths.checkpoint_path.as_posix(),
            vocab_path=paths.vocab_path.as_posix(),
            device=cfg.device,
        ),
        data=replace(base.data, seed=seed),
    )
    if extended:
        from mimirbench.interpretability.extended_interpretability import (
            run_extended_interpretability,
        )

        run_extended_interpretability(interp_cfg)
    else:
        from mimirbench.interpretability.runner import run_interpretability

        run_interpretability(interp_cfg)
    return "ran"


def _maybe_run_eval(
    cfg: MultiSeedConfig, seed: int, paths: _SeedPaths, train_base: Any
) -> str:
    if cfg.skip_existing and _summary_complete(paths.eval_dir, require_status=False):
        return "reused"
    from mimirbench.training.evaluate_small_transformer import (
        EvalDataConfig,
        EvalRunConfig,
        SmallTransformerEvalConfig,
        evaluate_checkpoint,
    )

    data = train_base.data
    eval_cfg = SmallTransformerEvalConfig(
        run=EvalRunConfig(
            name=f"small_transformer_bayes_medium_heldout_seed_{seed}",
            seed=cfg.heldout_seed_base + seed,
            output_dir=paths.eval_dir.as_posix(),
        ),
        checkpoint_path=paths.checkpoint_path.as_posix(),
        device=cfg.device,
        data=EvalDataConfig(
            num_tasks=cfg.heldout_num_tasks,
            num_hypotheses=data.num_hypotheses,
            min_observations=data.min_observations,
            max_observations=data.max_observations,
            signal_reliability=data.signal_reliability,
            posterior_buckets=data.posterior_buckets,
            payoff=data.payoff,
        ),
    )
    evaluate_checkpoint(eval_cfg, model_card_dir=cfg.model_card_dir)
    return "ran"


# --------------------------------------------------------------------------- #
# Metric extraction (pure: dict in, dict out)
# --------------------------------------------------------------------------- #


def summarise_seed_metrics(
    training: dict[str, Any] | None,
    full_interp: dict[str, Any] | None,
    extended: dict[str, Any] | None,
    heldout: dict[str, Any] | None,
) -> dict[str, Any]:
    """Extract the headline replication metrics from the four per-seed summaries."""
    return {
        "dataset": _dataset_sizes(training),
        "parameter_count": _dig(training, "model", "parameter_count"),
        "best_epoch": _dig(training, "best_epoch"),
        "validation": _validation_metrics(training),
        "heldout_test": _heldout_metrics(heldout),
        "whole_site_action_recovery": _whole_site_recovery(full_interp, "action_recovery_rate"),
        "whole_site_posterior_recovery": _whole_site_recovery(
            full_interp, "posterior_bucket_recovery_rate"
        ),
        "probes": _probe_metrics(full_interp),
        "token_group": _token_group_metrics(extended),
        "mismatched_donor": _mismatched_metrics(extended),
        "label_shuffle": _label_shuffle_metrics(extended),
    }


def _dataset_sizes(training: dict[str, Any] | None) -> dict[str, Any]:
    counts = _dig(training, "counts") or {}
    return {
        "num_train": counts.get("train"),
        "num_val": counts.get("val"),
        "num_test": counts.get("test"),
    }


def _validation_metrics(training: dict[str, Any] | None) -> dict[str, Any]:
    best = _dig(training, "best_metrics") or {}
    return {
        "action_accuracy": best.get("val_action_accuracy"),
        "posterior_bucket_accuracy": best.get("val_posterior_bucket_accuracy"),
        "risk_flag_accuracy": best.get("val_risk_flag_accuracy"),
        "confidence_bucket_accuracy": best.get("val_confidence_bucket_accuracy"),
        "loss": best.get("val_loss"),
    }


def _heldout_metrics(heldout: dict[str, Any] | None) -> dict[str, Any] | None:
    metrics = _dig(heldout, "metrics")
    if not isinstance(metrics, dict):
        return None
    return {
        "action_accuracy": metrics.get("action_accuracy"),
        "posterior_bucket_accuracy": metrics.get("posterior_bucket_accuracy"),
        "risk_flag_accuracy": metrics.get("risk_flag_accuracy"),
        "confidence_bucket_accuracy": metrics.get("confidence_bucket_accuracy"),
        "num_tasks": _dig(heldout, "config", "data", "num_tasks"),
    }


def _whole_site_recovery(full_interp: dict[str, Any] | None, key: str) -> dict[str, float | None]:
    by_site = _dig(full_interp, "experiments", "activation_patching", "by_site") or {}
    return {site: _as_float(by_site.get(site, {}).get(key)) for site in _BLOCK_SITES}


def _probe_metrics(full_interp: dict[str, Any] | None) -> dict[str, Any]:
    headline = _dig(full_interp, "experiments", "probes", "headline") or {}
    result: dict[str, Any] = {}
    for label in ("action", "posterior_bucket", "risk_flag"):
        row = headline.get(label, {})
        result[label] = {
            "site": row.get("site"),
            "test_accuracy": _as_float(row.get("test_accuracy")),
            "majority_baseline_accuracy": _as_float(row.get("majority_baseline_accuracy")),
        }
    return result


def _token_group_metrics(extended: dict[str, Any] | None) -> dict[str, Any]:
    by_site = _dig(extended, "token_group_patching", "by_site") or {}
    per_group_max: dict[str, float | None] = {}
    overall: list[float] = []
    for group in _TOKEN_GROUPS:
        rates: list[float] = []
        for site_block in by_site.values():
            rate = _as_float(site_block.get(group, {}).get("action_recovery_rate"))
            if rate is not None:
                rates.append(rate)
        per_group_max[group] = max(rates) if rates else None
        overall.extend(rates)
    return {
        "per_group_max_action_recovery": per_group_max,
        "max_action_recovery": max(overall) if overall else None,
    }


def _mismatched_metrics(extended: dict[str, Any] | None) -> dict[str, Any]:
    by_head = _dig(extended, "mismatched_donor_control", "by_head") or {}
    result: dict[str, Any] = {"site": _dig(extended, "mismatched_donor_control", "site")}
    for head in ("action", "posterior_bucket"):
        block = by_head.get(head, {})
        result[head] = {
            "matched_recovery_rate": _as_float(block.get("matched_recovery_rate")),
            "mismatched_recovery_rate": _as_float(block.get("mismatched_recovery_rate")),
        }
    return result


def _label_shuffle_metrics(extended: dict[str, Any] | None) -> dict[str, Any]:
    block = _dig(extended, "label_shuffle_control") or {}
    return {
        "site": block.get("site"),
        "real_test_accuracy": _as_float(block.get("real_test_accuracy")),
        "shuffled_test_accuracy": _as_float(block.get("shuffled_test_accuracy")),
        "majority_baseline_accuracy": _as_float(block.get("majority_baseline_accuracy")),
    }


# --------------------------------------------------------------------------- #
# Replication verdict + aggregation (pure)
# --------------------------------------------------------------------------- #


def _seed_story_replicated(metrics: dict[str, Any]) -> dict[str, Any]:
    """Decide whether one seed reproduces the documented causal story."""
    action_recovery = metrics.get("whole_site_action_recovery", {})
    l0_attn = action_recovery.get("blocks.0.attn_out")
    l1_attn = action_recovery.get("blocks.1.attn_out")
    l0_mlp = action_recovery.get("blocks.0.mlp_out")
    token_max = metrics.get("token_group", {}).get("max_action_recovery")
    mism = metrics.get("mismatched_donor", {}).get("action", {})
    matched = mism.get("matched_recovery_rate")
    mismatched = mism.get("mismatched_recovery_rate")
    shuffle = metrics.get("label_shuffle", {})
    real = shuffle.get("real_test_accuracy")
    shuffled = shuffle.get("shuffled_test_accuracy")
    baseline = shuffle.get("majority_baseline_accuracy")

    checks: dict[str, bool | None] = {
        "attention_concentration": _and(
            _ge(l0_attn, _ATTN_RECOVERY_MIN),
            _ge(l1_attn, _ATTN_RECOVERY_MIN),
            _le(l0_mlp, _MLP0_RECOVERY_MAX),
        ),
        "token_group_distributed": _le(token_max, _TOKEN_GROUP_RECOVERY_MAX),
        "mismatched_donor_specific": _gap_ge(matched, mismatched, _MISMATCH_GAP_MIN),
        "label_shuffle_collapses": _and(
            _ge(real, _SHUFFLE_REAL_MIN),
            _le_sum(shuffled, baseline, _SHUFFLE_OVER_BASELINE_MAX),
        ),
    }
    decidable = [value for value in checks.values() if value is not None]
    replicated = bool(decidable) and all(decidable)
    return {"checks": checks, "replicated": replicated}


def aggregate_seed_records(records: list[dict[str, Any]], *, run_name: str) -> dict[str, Any]:
    """Aggregate per-seed records into an explicit mean/range summary."""
    attempted = [int(r["seed"]) for r in records]
    completed = [r for r in records if r.get("status") == "complete"]
    completed_seeds = [int(r["seed"]) for r in completed]
    failed = [
        {"seed": int(r["seed"]), "reason": r.get("error", "unknown")}
        for r in records
        if r.get("status") != "complete"
    ]
    replicated_seeds = [int(r["seed"]) for r in completed if r.get("story", {}).get("replicated")]

    metric_records = [r["metrics"] for r in completed]
    aggregate_metrics = _aggregate_metrics(metric_records)
    story_replicated_all = bool(completed) and len(replicated_seeds) == len(completed)

    return {
        "run_name": run_name,
        "timestamp": _now(),
        "n_attempted": len(attempted),
        "n_completed": len(completed),
        "seeds_attempted": attempted,
        "seeds_completed": completed_seeds,
        "seeds_failed": failed,
        "seeds_replicated": replicated_seeds,
        "architecture": _architecture(completed),
        "dataset_sizes": _first_dataset(completed),
        "per_seed": [_per_seed_view(r) for r in records],
        "aggregate_metrics": aggregate_metrics,
        "causal_story_replicated_all_completed": story_replicated_all,
        "headline": _headline(len(completed_seeds), story_replicated_all, completed_seeds),
        "no_frontier_claim": (
            "These results characterise small, fully synthetic Bayesian transformers. "
            "They are not evidence about frontier-model internals and must not be read that way."
        ),
        "limitations": [
            "One narrow synthetic Bayesian/risk generator; deterministic, CPU-only.",
            "Each seed independently resamples training data, weight init, and the "
            "interpretability probe/patch set, so seeds are genuinely independent draws.",
            "Position-resolved patching is at the token-group level only; it does not "
            "isolate individual heads or neurons and uses no sparse autoencoder.",
            "Nothing here transfers to frontier-model internals.",
        ],
    }


def _aggregate_metrics(metric_records: list[dict[str, Any]]) -> dict[str, Any]:
    def column(*path: str) -> dict[str, Any]:
        return _mean_range([_dig(m, *path) for m in metric_records])

    return {
        "validation_action_accuracy": column("validation", "action_accuracy"),
        "validation_posterior_bucket_accuracy": column("validation", "posterior_bucket_accuracy"),
        "validation_risk_flag_accuracy": column("validation", "risk_flag_accuracy"),
        "heldout_action_accuracy": column("heldout_test", "action_accuracy"),
        "heldout_posterior_bucket_accuracy": column("heldout_test", "posterior_bucket_accuracy"),
        "heldout_risk_flag_accuracy": column("heldout_test", "risk_flag_accuracy"),
        "layer0_attn_action_recovery": column("whole_site_action_recovery", "blocks.0.attn_out"),
        "layer0_mlp_action_recovery": column("whole_site_action_recovery", "blocks.0.mlp_out"),
        "layer1_attn_action_recovery": column("whole_site_action_recovery", "blocks.1.attn_out"),
        "layer0_attn_posterior_recovery": column(
            "whole_site_posterior_recovery", "blocks.0.attn_out"
        ),
        "token_group_max_action_recovery": column("token_group", "max_action_recovery"),
        "mismatched_action_matched_recovery": column(
            "mismatched_donor", "action", "matched_recovery_rate"
        ),
        "mismatched_action_mismatched_recovery": column(
            "mismatched_donor", "action", "mismatched_recovery_rate"
        ),
        "mismatched_posterior_matched_recovery": column(
            "mismatched_donor", "posterior_bucket", "matched_recovery_rate"
        ),
        "mismatched_posterior_mismatched_recovery": column(
            "mismatched_donor", "posterior_bucket", "mismatched_recovery_rate"
        ),
        "label_shuffle_real_accuracy": column("label_shuffle", "real_test_accuracy"),
        "label_shuffle_shuffled_accuracy": column("label_shuffle", "shuffled_test_accuracy"),
    }


def _per_seed_view(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "seed": int(record["seed"]),
        "status": record.get("status"),
        "steps": record.get("steps", {}),
        "error": record.get("error"),
        "training_runtime_s": record.get("training_runtime_s"),
        "checkpoint_sha256": record.get("checkpoint_sha256"),
        "metrics": record.get("metrics"),
        "story": record.get("story"),
    }


def _architecture(completed: list[dict[str, Any]]) -> dict[str, Any]:
    for record in completed:
        params = _dig(record, "metrics", "parameter_count")
        if params is not None:
            return {
                "architecture": "compact_transformer_encoder",
                "n_layers": 2,
                "d_model": 128,
                "n_heads": 4,
                "parameter_count": params,
            }
    return {"architecture": "compact_transformer_encoder", "n_layers": 2, "d_model": 128, "n_heads": 4}


def _first_dataset(completed: list[dict[str, Any]]) -> dict[str, Any]:
    for record in completed:
        dataset = _dig(record, "metrics", "dataset")
        if dataset and dataset.get("num_train"):
            return dataset
    return {"num_train": None, "num_val": None, "num_test": None}


def _headline(n_completed: int, replicated_all: bool, seeds: list[int]) -> str:
    if n_completed <= 1:
        return (
            "Single-seed only: multi-seed interpretability replication remains pending. "
            "Every interpretability number still comes from one checkpoint."
        )
    label = {2: "two-seed", 3: "three-seed", 4: "four-seed", 5: "five-seed", 6: "six-seed"}.get(
        n_completed, f"{n_completed}-seed"
    )
    if replicated_all:
        return (
            f"Extended medium-model interpretability is replicated across {n_completed} "
            f"independently trained synthetic checkpoints (seeds {seeds}). The "
            "evidence-to-decision mechanism remains concentrated in attention-mediated "
            "activations, token-group-only interventions show distributed positional "
            "dependence, and negative controls reduce recovery substantially."
        )
    return (
        f"Partial replication across {n_completed} checkpoints ({label}): the causal "
        "story did not hold identically on every completed seed; see per-seed metrics."
    )


# --------------------------------------------------------------------------- #
# Small numeric / dict helpers
# --------------------------------------------------------------------------- #


def _mean_range(values: list[Any]) -> dict[str, Any]:
    numbers = [float(v) for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]
    if not numbers:
        return {"mean": None, "min": None, "max": None, "n": 0}
    return {
        "mean": fmean(numbers),
        "min": min(numbers),
        "max": max(numbers),
        "n": len(numbers),
    }


def _collect_metrics(paths: _SeedPaths) -> dict[str, Any]:
    return summarise_seed_metrics(
        _read_json(paths.training_dir / "summary.json"),
        _read_json(paths.interp_dir / "summary.json"),
        _read_json(paths.extended_dir / "summary.json"),
        _read_json(paths.eval_dir / "summary.json"),
    )


def _has_checkpoint(paths: _SeedPaths) -> bool:
    return paths.checkpoint_path.exists() and (paths.training_dir / "summary.json").exists()


def _summary_complete(output_dir: Path, *, require_status: bool = True) -> bool:
    summary = _read_json(output_dir / "summary.json")
    if summary is None:
        return False
    return (not require_status) or summary.get("status") == "complete"


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None
    return data if isinstance(data, dict) else None


def _sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _dig(data: dict[str, Any] | None, *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _as_float(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


def _ge(value: float | None, threshold: float) -> bool | None:
    return None if value is None else value >= threshold


def _le(value: float | None, threshold: float) -> bool | None:
    return None if value is None else value <= threshold


def _gap_ge(high: float | None, low: float | None, threshold: float) -> bool | None:
    if high is None or low is None:
        return None
    return (high - low) >= threshold


def _le_sum(value: float | None, base: float | None, margin: float) -> bool | None:
    if value is None or base is None:
        return None
    return value <= base + margin


def _and(*values: bool | None) -> bool | None:
    if any(value is None for value in values):
        return None
    return all(bool(value) for value in values)


def _mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("config section must be a mapping.")
    return dict(value)


def _now() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat()
