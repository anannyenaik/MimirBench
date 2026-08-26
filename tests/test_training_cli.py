"""CLI smoke tests for the training commands."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from mimirbench.cli import app


def test_generate_traces_cli_smoke(tmp_path: Path) -> None:
    config_path = tmp_path / "train.yaml"
    run_dir = tmp_path / "training"
    config_path.write_text(
        f"""
run:
  name: cli_traces
  seed: 5
  output_dir: {run_dir.as_posix()}
data:
  num_train: 4
  num_val: 2
  num_test: 2
  num_hypotheses: 2
  min_observations: 1
  max_observations: 3
  signal_reliability: 0.7
  posterior_buckets: 20
model:
  d_model: 16
  n_layers: 1
  n_heads: 2
  dim_feedforward: 32
  max_seq_len: 96
training:
  batch_size: 2
  epochs: 1
  device: cpu
""",
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(app, ["generate-traces", str(config_path)])
    assert result.exit_code == 0, result.output
    assert (run_dir / "train_traces.jsonl").exists()


def test_train_eval_and_inspect_cli_smoke(tmp_path: Path) -> None:
    pytest.importorskip("torch")
    train_config = tmp_path / "train.yaml"
    eval_config = tmp_path / "eval.yaml"
    training_dir = tmp_path / "training"
    eval_dir = tmp_path / "eval"
    train_config.write_text(
        f"""
run:
  name: cli_train
  seed: 6
  output_dir: {training_dir.as_posix()}
data:
  num_train: 8
  num_val: 4
  num_test: 4
  num_hypotheses: 2
  min_observations: 1
  max_observations: 3
  signal_reliability: 0.7
  posterior_buckets: 20
model:
  d_model: 16
  n_layers: 1
  n_heads: 2
  dim_feedforward: 32
  max_seq_len: 96
training:
  batch_size: 4
  epochs: 1
  device: cpu
""",
        encoding="utf-8",
    )
    cards_dir = tmp_path / "model_cards"
    runner = CliRunner()
    train_result = runner.invoke(
        app,
        ["train-small-transformer", str(train_config), "--model-card-dir", str(cards_dir)],
    )
    assert train_result.exit_code == 0, train_result.output
    assert (training_dir / "summary.json").exists()

    inspect = runner.invoke(app, ["inspect-training", str(training_dir)])
    assert inspect.exit_code == 0, inspect.output
    assert "best checkpoint" in inspect.output

    eval_config.write_text(
        f"""
run:
  name: cli_eval
  seed: 7
  output_dir: {eval_dir.as_posix()}
checkpoint_path: {(training_dir / 'checkpoints' / 'best.pt').as_posix()}
device: cpu
data:
  num_tasks: 4
  num_hypotheses: 2
  min_observations: 1
  max_observations: 3
  signal_reliability: 0.7
  posterior_buckets: 20
""",
        encoding="utf-8",
    )
    eval_result = runner.invoke(
        app,
        ["eval-small-transformer", str(eval_config), "--model-card-dir", str(cards_dir)],
    )
    assert eval_result.exit_code == 0, eval_result.output
    assert (eval_dir / "summary.json").exists()
