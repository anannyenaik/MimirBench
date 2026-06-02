"""CLI smoke tests for the Stage 8 interpretability commands."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from mimirbench.cli import app


def _write_config(path: Path, *, checkpoint: Path, vocab: Path, output_dir: Path) -> None:
    path.write_text(
        f"""
run:
  name: cli_interp
  seed: 123
  output_dir: {output_dir.as_posix()}
model:
  checkpoint_path: {checkpoint.as_posix()}
  vocab_path: {vocab.as_posix()}
  device: cpu
data:
  source: synthetic
  num_examples: 16
  num_pairs: 8
  seed: 123
  min_observations: 2
experiments:
  probes: true
  activation_patching: true
  attention_analysis: true
batch_size: 8
max_examples: 8
""",
        encoding="utf-8",
    )


def test_run_interpretability_pending_cli(tmp_path: Path) -> None:
    config = tmp_path / "interp.yaml"
    output_dir = tmp_path / "out"
    _write_config(
        config,
        checkpoint=tmp_path / "missing.pt",
        vocab=tmp_path / "missing.json",
        output_dir=output_dir,
    )
    result = CliRunner().invoke(app, ["run-interpretability", str(config)])
    assert result.exit_code == 0, result.output
    assert "pending" in result.output.lower()
    assert (output_dir / "INTERPRETABILITY_REPORT.md").exists()


def test_run_and_inspect_interpretability_cli(tiny_interp_checkpoint: dict, tmp_path: Path) -> None:
    pytest.importorskip("torch")
    config = tmp_path / "interp.yaml"
    output_dir = tmp_path / "run"
    _write_config(
        config,
        checkpoint=tiny_interp_checkpoint["checkpoint"],
        vocab=tiny_interp_checkpoint["vocab"],
        output_dir=output_dir,
    )
    runner = CliRunner()
    run_result = runner.invoke(app, ["run-interpretability", str(config)])
    assert run_result.exit_code == 0, run_result.output
    assert (output_dir / "summary.json").exists()

    inspect_result = runner.invoke(app, ["inspect-interpretability", str(output_dir)])
    assert inspect_result.exit_code == 0, inspect_result.output
    assert "Linear probes" in inspect_result.output
    assert "frontier-model claim" in inspect_result.output


def test_inspect_interpretability_missing_summary(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    result = CliRunner().invoke(app, ["inspect-interpretability", str(empty)])
    assert result.exit_code == 1
