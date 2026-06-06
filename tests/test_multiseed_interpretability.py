"""Tests for the multi-seed interpretability replication runner.

The config-loading, metric-extraction, replication-verdict, and aggregation
helpers are pure (dict in, dict out) and run without torch. One torch-gated
end-to-end test exercises the full orchestration on a tiny model.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mimirbench.interpretability.multiseed import (
    MultiSeedConfig,
    aggregate_seed_records,
    load_multiseed_config,
    summarise_seed_metrics,
)
from mimirbench.interpretability.multiseed import (
    _seed_story_replicated as seed_story_replicated,
)

# --------------------------------------------------------------------------- #
# Representative trimmed per-seed summaries (mirroring the real seed-123 shapes)
# --------------------------------------------------------------------------- #


def _training_summary() -> dict:
    return {
        "counts": {"train": 12000, "val": 2000, "test": 2000},
        "model": {"parameter_count": 321455},
        "best_epoch": 25,
        "best_metrics": {
            "val_action_accuracy": 1.0,
            "val_posterior_bucket_accuracy": 0.9935,
            "val_risk_flag_accuracy": 1.0,
            "val_confidence_bucket_accuracy": 0.998,
            "val_loss": 0.0319,
        },
    }


def _full_interp_summary() -> dict:
    return {
        "experiments": {
            "activation_patching": {
                "by_site": {
                    "blocks.0.attn_out": {
                        "action_recovery_rate": 0.967,
                        "posterior_bucket_recovery_rate": 0.906,
                    },
                    "blocks.0.mlp_out": {
                        "action_recovery_rate": 0.0,
                        "posterior_bucket_recovery_rate": 0.0,
                    },
                    "blocks.1.attn_out": {
                        "action_recovery_rate": 0.975,
                        "posterior_bucket_recovery_rate": 0.922,
                    },
                }
            },
            "probes": {
                "headline": {
                    "action": {
                        "site": "blocks.1.mlp_out",
                        "test_accuracy": 1.0,
                        "majority_baseline_accuracy": 0.59375,
                    },
                    "posterior_bucket": {
                        "site": "blocks.1.resid_post",
                        "test_accuracy": 0.984,
                        "majority_baseline_accuracy": 0.297,
                    },
                }
            },
        }
    }


def _extended_summary() -> dict:
    return {
        "token_group_patching": {
            "by_site": {
                "blocks.0.attn_out": {
                    "evidence": {"action_recovery_rate": 0.0},
                    "prior": {"action_recovery_rate": 0.008},
                    "payoff_risk": {"action_recovery_rate": 0.016},
                },
                "blocks.1.resid_post": {
                    "evidence": {"action_recovery_rate": 0.0},
                    "prior": {"action_recovery_rate": 0.0},
                    "payoff_risk": {"action_recovery_rate": 0.008},
                },
            }
        },
        "mismatched_donor_control": {
            "site": "blocks.0.attn_out",
            "by_head": {
                "action": {"matched_recovery_rate": 0.967, "mismatched_recovery_rate": 0.533},
                "posterior_bucket": {
                    "matched_recovery_rate": 0.906,
                    "mismatched_recovery_rate": 0.211,
                },
            },
        },
        "label_shuffle_control": {
            "site": "blocks.1.mlp_out",
            "real_test_accuracy": 1.0,
            "shuffled_test_accuracy": 0.484,
            "majority_baseline_accuracy": 0.594,
        },
    }


def _heldout_summary() -> dict:
    return {
        "metrics": {
            "action_accuracy": 1.0,
            "posterior_bucket_accuracy": 0.99,
            "risk_flag_accuracy": 1.0,
            "confidence_bucket_accuracy": 0.99,
        },
        "config": {"data": {"num_tasks": 2000}},
    }


def _replicating_metrics() -> dict:
    return summarise_seed_metrics(
        _training_summary(), _full_interp_summary(), _extended_summary(), _heldout_summary()
    )


# --------------------------------------------------------------------------- #
# Config loading / validation
# --------------------------------------------------------------------------- #


def test_load_multiseed_config_full(tmp_path: Path) -> None:
    config_path = tmp_path / "multiseed.yaml"
    config_path.write_text(
        """
run:
  name: ms
  summary_dir: out/summaries
seeds: [123, 124, 125]
train_template: configs/train.yaml
interp_template: configs/interp.yaml
extended_template: configs/extended.yaml
skip_existing: false
run_heldout_eval: false
seed_overrides:
  123:
    training_dir: reports/training/medium
    interp_dir: reports/interp/all
    extended_dir: reports/interp/extended
""",
        encoding="utf-8",
    )
    config = load_multiseed_config(config_path)
    assert config.run.name == "ms"
    assert config.seeds == (123, 124, 125)
    assert config.skip_existing is False
    assert config.run_heldout_eval is False
    assert 123 in config.seed_overrides
    assert config.seed_overrides[123].training_dir == "reports/training/medium"


def test_load_multiseed_config_defaults(tmp_path: Path) -> None:
    config_path = tmp_path / "multiseed.yaml"
    config_path.write_text("seeds: [7]\n", encoding="utf-8")
    config = load_multiseed_config(config_path)
    assert config.seeds == (7,)
    assert config.skip_existing is True
    assert config.run_full_interpretability is True
    assert "{seed}" in config.training_output_template


@pytest.mark.parametrize(
    "mutation",
    [
        {"seeds": ()},
        {"seeds": (1, 1, 2)},
        {"training_output_template": "no-placeholder"},
        {"heldout_num_tasks": 0},
    ],
)
def test_validate_rejects_bad_config(mutation: dict) -> None:
    import dataclasses

    config = dataclasses.replace(MultiSeedConfig(), **mutation)
    with pytest.raises(ValueError):
        config.validate()


# --------------------------------------------------------------------------- #
# Metric extraction
# --------------------------------------------------------------------------- #


def test_summarise_seed_metrics_extracts_headlines() -> None:
    metrics = _replicating_metrics()
    assert metrics["dataset"] == {"num_train": 12000, "num_val": 2000, "num_test": 2000}
    assert metrics["parameter_count"] == 321455
    assert metrics["validation"]["action_accuracy"] == 1.0
    assert metrics["heldout_test"]["posterior_bucket_accuracy"] == 0.99
    assert metrics["whole_site_action_recovery"]["blocks.0.attn_out"] == pytest.approx(0.967)
    assert metrics["whole_site_action_recovery"]["blocks.0.mlp_out"] == 0.0
    assert metrics["token_group"]["max_action_recovery"] == pytest.approx(0.016)
    assert metrics["token_group"]["per_group_max_action_recovery"]["payoff_risk"] == pytest.approx(
        0.016
    )
    assert metrics["mismatched_donor"]["action"]["matched_recovery_rate"] == pytest.approx(0.967)
    assert metrics["label_shuffle"]["shuffled_test_accuracy"] == pytest.approx(0.484)


def test_summarise_seed_metrics_tolerates_missing_summaries() -> None:
    metrics = summarise_seed_metrics(None, None, None, None)
    assert metrics["heldout_test"] is None
    assert metrics["validation"]["action_accuracy"] is None
    assert metrics["whole_site_action_recovery"]["blocks.0.attn_out"] is None
    assert metrics["token_group"]["max_action_recovery"] is None


# --------------------------------------------------------------------------- #
# Replication verdict
# --------------------------------------------------------------------------- #


def test_seed_story_replicated_true() -> None:
    verdict = seed_story_replicated(_replicating_metrics())
    assert verdict["replicated"] is True
    assert all(verdict["checks"].values())


def test_seed_story_not_replicated_when_mlp_restores_action() -> None:
    full = _full_interp_summary()
    full["experiments"]["activation_patching"]["by_site"]["blocks.0.mlp_out"][
        "action_recovery_rate"
    ] = 0.8  # layer-0 MLP now restores the action -> story broken
    metrics = summarise_seed_metrics(
        _training_summary(), full, _extended_summary(), _heldout_summary()
    )
    verdict = seed_story_replicated(metrics)
    assert verdict["checks"]["attention_concentration"] is False
    assert verdict["replicated"] is False


def test_seed_story_undecidable_when_metrics_missing() -> None:
    verdict = seed_story_replicated(summarise_seed_metrics(None, None, None, None))
    assert verdict["replicated"] is False
    assert all(value is None for value in verdict["checks"].values())


# --------------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------------- #


def _record(seed: int, *, status: str = "complete", metrics: dict | None = None) -> dict:
    resolved = metrics if metrics is not None else _replicating_metrics()
    return {
        "seed": seed,
        "status": status,
        "steps": {"training": "trained"},
        "metrics": resolved,
        "story": seed_story_replicated(resolved),
        "checkpoint_sha256": "deadbeef",
        "error": None if status == "complete" else "RuntimeError: boom",
    }


def test_aggregate_three_completed_seeds_replicate() -> None:
    records = [_record(123), _record(124), _record(125)]
    aggregate = aggregate_seed_records(records, run_name="ms")
    assert aggregate["n_attempted"] == 3
    assert aggregate["n_completed"] == 3
    assert aggregate["seeds_completed"] == [123, 124, 125]
    assert aggregate["causal_story_replicated_all_completed"] is True
    stat = aggregate["aggregate_metrics"]["layer0_attn_action_recovery"]
    assert stat["n"] == 3
    assert stat["mean"] == pytest.approx(0.967)
    assert stat["min"] == pytest.approx(0.967)
    assert "replicated across 3" in aggregate["headline"]


def test_aggregate_reports_failed_seed_with_reason() -> None:
    records = [_record(123), _record(124, status="failed")]
    aggregate = aggregate_seed_records(records, run_name="ms")
    assert aggregate["n_completed"] == 1
    assert aggregate["seeds_failed"] == [{"seed": 124, "reason": "RuntimeError: boom"}]
    # Single completed seed: must not claim multi-seed replication.
    assert "Single-seed only" in aggregate["headline"]
    assert aggregate["causal_story_replicated_all_completed"] is True  # the one seed did replicate


def test_aggregate_partial_when_a_completed_seed_breaks_story() -> None:
    broken = _replicating_metrics()
    broken["whole_site_action_recovery"]["blocks.0.mlp_out"] = 0.9
    records = [_record(123), _record(124, metrics=broken)]
    aggregate = aggregate_seed_records(records, run_name="ms")
    assert aggregate["n_completed"] == 2
    assert aggregate["seeds_replicated"] == [123]
    assert aggregate["causal_story_replicated_all_completed"] is False
    assert "Partial replication" in aggregate["headline"]


# --------------------------------------------------------------------------- #
# End-to-end orchestration (torch-gated, tiny model)
# --------------------------------------------------------------------------- #


def _write_tiny_templates(tmp_path: Path) -> dict[str, Path]:
    train_template = tmp_path / "train.yaml"
    train_template.write_text(
        """
run:
  name: tiny_medium
  seed: 123
  output_dir: unused
data:
  num_train: 64
  num_val: 32
  num_test: 32
  min_observations: 2
  max_observations: 6
model:
  d_model: 32
  n_layers: 2
  n_heads: 2
  dim_feedforward: 64
  max_seq_len: 64
training:
  batch_size: 16
  epochs: 1
  learning_rate: 0.001
  device: cpu
""",
        encoding="utf-8",
    )
    interp_template = tmp_path / "interp.yaml"
    interp_template.write_text(
        """
run:
  name: tiny_interp
  seed: 123
  output_dir: unused
model:
  checkpoint_path: unused
  vocab_path: unused
data:
  num_examples: 16
  num_pairs: 8
  min_observations: 2
  max_observations: 6
batch_size: 8
max_examples: 8
""",
        encoding="utf-8",
    )
    extended_template = tmp_path / "extended.yaml"
    extended_template.write_text(interp_template.read_text(encoding="utf-8"), encoding="utf-8")
    return {
        "train": train_template,
        "interp": interp_template,
        "extended": extended_template,
    }


def test_run_multiseed_end_to_end_tiny(tmp_path: Path) -> None:
    pytest.importorskip("torch")
    from mimirbench.interpretability.multiseed import run_multiseed_interpretability

    templates = _write_tiny_templates(tmp_path)
    config = MultiSeedConfig(
        seeds=(124,),
        train_template=templates["train"].as_posix(),
        interp_template=templates["interp"].as_posix(),
        extended_template=templates["extended"].as_posix(),
        training_output_template=(tmp_path / "train_seed_{seed}").as_posix(),
        interp_output_template=(tmp_path / "interp_seed_{seed}").as_posix(),
        extended_output_template=(tmp_path / "extended_seed_{seed}").as_posix(),
        eval_output_template=(tmp_path / "eval_seed_{seed}").as_posix(),
        heldout_num_tasks=32,
        model_card_dir=(tmp_path / "cards").as_posix(),
    )
    import dataclasses

    config = dataclasses.replace(config, run=dataclasses.replace(config.run, summary_dir=(tmp_path / "summaries").as_posix()))
    aggregate = run_multiseed_interpretability(config)

    assert aggregate["n_attempted"] == 1
    assert aggregate["seeds_attempted"] == [124]
    seed_record = aggregate["per_seed"][0]
    assert seed_record["status"] == "complete"
    assert seed_record["checkpoint_sha256"]  # checkpoint was produced
    # whole-site, extended, and held-out steps all ran for the fresh seed.
    assert seed_record["steps"]["training"] == "trained"
    assert seed_record["steps"]["full_interp"] == "ran"
    assert seed_record["steps"]["extended_interp"] == "ran"
    summary_json = json.loads(
        (tmp_path / "summaries" / "interp_bayes_multiseed_summary.json").read_text(encoding="utf-8")
    )
    assert summary_json["n_attempted"] == 1

    # Re-running with skip_existing reuses everything (no retrain).
    second = run_multiseed_interpretability(config)
    assert second["per_seed"][0]["steps"]["training"] == "reused"
    assert second["per_seed"][0]["steps"]["full_interp"] == "reused"
