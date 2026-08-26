"""Validation checks for the training and eval configs."""

from __future__ import annotations

from pathlib import Path

from mimirbench.training.evaluate_small_transformer import load_eval_config
from mimirbench.training.train_small_transformer import load_config


def test_training_configs_validate() -> None:
    for path in (
        Path("configs/train_small_transformer_bayes_tiny.yaml"),
        Path("configs/train_small_transformer_bayes_small.yaml"),
    ):
        config = load_config(path)
        config.data.trace_config().validate()
        assert config.data.num_train > 0
        assert config.data.num_val > 0
        assert config.model.n_heads <= config.model.d_model
        assert config.run.output_dir.startswith("reports/training/")


def test_eval_config_validates() -> None:
    config = load_eval_config(Path("configs/eval_small_transformer_bayes.yaml"))
    assert config.run.output_dir == "reports/runs/small_transformer_bayes_eval"
    assert config.data.num_tasks > 0
    assert config.checkpoint_path.endswith("checkpoints/best.pt")
