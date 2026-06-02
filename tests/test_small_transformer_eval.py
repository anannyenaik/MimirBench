"""Smoke tests for small-transformer checkpoint evaluation."""

from __future__ import annotations

import pytest

from mimirbench.training.datasets import BayesianTraceDatasetConfig
from mimirbench.training.evaluate_small_transformer import (
    EvalDataConfig,
    EvalRunConfig,
    SmallTransformerEvalConfig,
    evaluate_checkpoint,
)
from mimirbench.training.train_small_transformer import (
    ModelConfig,
    RunConfig,
    SmallTransformerTrainConfig,
    TrainingConfig,
    train,
)


def test_small_transformer_eval_smoke(tmp_path) -> None:  # type: ignore[no-untyped-def]
    pytest.importorskip("torch")
    training_dir = tmp_path / "training"
    train_summary = train(
        SmallTransformerTrainConfig(
            run=RunConfig(name="eval_source", seed=2, output_dir=str(training_dir)),
            data=BayesianTraceDatasetConfig(num_train=8, num_val=4, num_test=4, seed=2),
            model=ModelConfig(d_model=16, n_layers=1, n_heads=2, dim_feedforward=32, max_seq_len=96),
            training=TrainingConfig(batch_size=4, epochs=1, device="cpu"),
        )
    )
    eval_dir = tmp_path / "eval"
    summary = evaluate_checkpoint(
        SmallTransformerEvalConfig(
            run=EvalRunConfig(name="eval_smoke", seed=3, output_dir=str(eval_dir)),
            checkpoint_path=train_summary["paths"]["best_checkpoint"],
            data=EvalDataConfig(num_tasks=4),
        )
    )
    assert (eval_dir / "results.jsonl").exists()
    assert (eval_dir / "summary.json").exists()
    assert (eval_dir / "report.md").exists()
    assert "posterior_bucket_accuracy" in summary["metrics"]
