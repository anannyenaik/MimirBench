"""Smoke tests for tiny small-transformer training."""

from __future__ import annotations

from pathlib import Path

import pytest

from mimirbench.training.datasets import BayesianTraceDatasetConfig
from mimirbench.training.train_small_transformer import (
    ModelConfig,
    RunConfig,
    SmallTransformerTrainConfig,
    TrainingConfig,
    train,
)


def test_tiny_training_smoke_writes_artifacts(tmp_path: Path) -> None:
    pytest.importorskip("torch")
    config = SmallTransformerTrainConfig(
        run=RunConfig(name="test_tiny", seed=1, output_dir=str(tmp_path / "training")),
        data=BayesianTraceDatasetConfig(num_train=8, num_val=4, num_test=4, seed=1),
        model=ModelConfig(d_model=16, n_layers=1, n_heads=2, dim_feedforward=32, max_seq_len=96),
        training=TrainingConfig(batch_size=4, epochs=1, device="cpu"),
    )
    cards_dir = tmp_path / "model_cards"
    summary = train(config, model_card_dir=cards_dir)
    paths = summary["paths"]
    assert (tmp_path / "training" / "metrics.jsonl").exists()
    assert (tmp_path / "training" / "summary.json").exists()
    assert (tmp_path / "training" / "checkpoints" / "best.pt").exists()
    assert (tmp_path / "training" / "checkpoints" / "final.pt").exists()
    # The card is written to the isolated dir, not the tracked reports/model_cards.
    assert paths["model_card"].endswith("test_tiny.md")
    assert (cards_dir / "test_tiny.md").exists()
