"""Tests for the small-transformer agent wrapper."""

from __future__ import annotations

import inspect

import pytest

from mimirbench.agents.small_transformer_agent import SmallTransformerAgent
from mimirbench.environments.adversarial_risk.generator import generate_task as generate_risk_task
from mimirbench.environments.bayesian_games.generator import generate_task as generate_bayes_task
from mimirbench.training.datasets import BayesianTraceDatasetConfig
from mimirbench.training.train_small_transformer import (
    ModelConfig,
    RunConfig,
    SmallTransformerTrainConfig,
    TrainingConfig,
    train,
)


def test_small_transformer_agent_answers_bayesian_task_and_rejects_unsupported(tmp_path) -> None:  # type: ignore[no-untyped-def]
    pytest.importorskip("torch")
    summary = train(
        SmallTransformerTrainConfig(
            run=RunConfig(name="agent_source", seed=4, output_dir=str(tmp_path / "training")),
            data=BayesianTraceDatasetConfig(num_train=8, num_val=4, num_test=4, seed=4),
            model=ModelConfig(d_model=16, n_layers=1, n_heads=2, dim_feedforward=32, max_seq_len=96),
            training=TrainingConfig(batch_size=4, epochs=1, device="cpu"),
        )
    )
    agent = SmallTransformerAgent(summary["paths"]["best_checkpoint"], device="cpu")
    response = agent.act(generate_bayes_task(1).task)
    assert response.parsed_answer is not None
    assert "posterior" in response.parsed_answer

    with pytest.raises(ValueError, match="only supports bayesian_games"):
        agent.act(generate_risk_task(1).task)


def test_small_transformer_agent_source_does_not_reference_grading_key() -> None:
    assert "GradingKey" not in inspect.getsource(SmallTransformerAgent)
