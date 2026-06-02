"""Smoke tests for tiny small-transformer training."""

from __future__ import annotations

import pytest

from mimirbench.training.datasets import BayesianTraceDatasetConfig
from mimirbench.training.train_small_transformer import (
    ModelConfig,
    RunConfig,
    SmallTransformerTrainConfig,
    TrainingConfig,
    train,
)


def test_tiny_training_smoke_writes_artifacts(tmp_path) -> None:  # type: ignore[no-untyped-def]
    pytest.importorskip("torch")
    config = SmallTransformerTrainConfig(
        run=RunConfig(name="test_tiny", seed=1, output_dir=str(tmp_path / "training")),
        data=BayesianTraceDatasetConfig(num_train=8, num_val=4, num_test=4, seed=1),
        model=ModelConfig(d_model=16, n_layers=1, n_heads=2, dim_feedforward=32, max_seq_len=96),
        training=TrainingConfig(batch_size=4, epochs=1, device="cpu"),
    )
    summary = train(config)
    paths = summary["paths"]
    assert (tmp_path / "training" / "metrics.jsonl").exists()
    assert (tmp_path / "training" / "summary.json").exists()
    assert (tmp_path / "training" / "checkpoints" / "best.pt").exists()
    assert (tmp_path / "training" / "checkpoints" / "final.pt").exists()
    assert paths["model_card"].endswith("test_tiny.md")
