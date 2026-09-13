"""Checks for the medium small-transformer milestone (configs, data, pairs).

These tests are torch-free: they validate the new medium configs, assert
content-level (not just id-level) split separation for the medium data regime,
confirm dataset determinism, and verify that the counterfactual generator
flips enough action labels for the activation-patching experiment.
"""

from __future__ import annotations

from pathlib import Path

from mimirbench.interpretability.counterfactuals import generate_counterfactual_pairs
from mimirbench.interpretability.runner import load_interpretability_config
from mimirbench.training.datasets import BayesianTraceDatasetConfig, make_bayesian_trace_dataset
from mimirbench.training.evaluate_small_transformer import load_eval_config
from mimirbench.training.synthetic_traces import BayesianTraceConfig
from mimirbench.training.train_small_transformer import load_config

_MEDIUM_DATA = BayesianTraceDatasetConfig(
    num_train=64,
    num_val=32,
    num_test=32,
    seed=123,
    num_hypotheses=2,
    min_observations=2,
    max_observations=10,
    signal_reliability=0.75,
    posterior_buckets=20,
)


def test_medium_training_config_validates() -> None:
    config = load_config(Path("configs/training/medium.yaml"))
    config.data.trace_config().validate()
    assert config.data.num_train == 12000
    assert config.model.n_layers == 2
    assert config.model.d_model == 128
    assert config.model.n_heads == 4
    assert config.model.d_model % config.model.n_heads == 0
    assert config.training.early_stopping_patience is not None
    assert config.run.output_dir == "runs/training/medium"


def test_medium_eval_config_is_held_out_from_training() -> None:
    train = load_config(Path("configs/training/medium.yaml"))
    evaluation = load_eval_config(Path("configs/training/medium_eval.yaml"))
    assert evaluation.checkpoint_path == "runs/training/medium/checkpoints/best.pt"
    # The eval seed must differ from the training seed so tasks are unseen.
    assert evaluation.run.seed != train.run.seed
    assert evaluation.data.num_tasks > 0


def test_medium_interp_config_points_at_medium_checkpoint() -> None:
    config = load_interpretability_config(Path("configs/interpretability/whole_site.yaml"))
    config.validate()
    assert config.model.checkpoint_path == "runs/training/medium/checkpoints/best.pt"
    assert config.experiments.probes
    assert config.experiments.activation_patching
    assert config.experiments.attention_analysis
    assert config.data.num_pairs > 0


def test_medium_dataset_is_deterministic() -> None:
    first = make_bayesian_trace_dataset(_MEDIUM_DATA)
    second = make_bayesian_trace_dataset(_MEDIUM_DATA)
    for split in ("train", "val", "test"):
        assert [t["input"] for t in first[split]] == [t["input"] for t in second[split]]
        assert [t["targets"] for t in first[split]] == [t["targets"] for t in second[split]]


def test_medium_splits_separate_by_content_not_just_id() -> None:
    splits = make_bayesian_trace_dataset(_MEDIUM_DATA)
    train_inputs = {t["input"] for t in splits["train"]}
    val_inputs = {t["input"] for t in splits["val"]}
    test_inputs = {t["input"] for t in splits["test"]}
    # No exact input string is shared across splits (stronger than id disjointness).
    assert train_inputs.isdisjoint(test_inputs)
    assert train_inputs.isdisjoint(val_inputs)
    assert val_inputs.isdisjoint(test_inputs)


def test_counterfactual_pairs_are_deterministic_and_flip_the_action() -> None:
    cfg = BayesianTraceConfig(
        seed=123,
        num_hypotheses=2,
        min_observations=2,
        max_observations=10,
        signal_reliability=0.75,
        posterior_buckets=20,
    )
    pairs_a = generate_counterfactual_pairs(32, config=cfg, seed=123, split="interp")
    pairs_b = generate_counterfactual_pairs(32, config=cfg, seed=123, split="interp")
    assert [p.pair_id for p in pairs_a] == [p.pair_id for p in pairs_b]
    assert [p.corrupted_input for p in pairs_a] == [p.corrupted_input for p in pairs_b]
    # Patching requires enough pairs whose actions change under corruption.
    flipped = [p for p in pairs_a if p.clean_labels["action"] != p.corrupted_labels["action"]]
    assert len(flipped) >= len(pairs_a) // 2
