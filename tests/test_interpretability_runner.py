"""End-to-end and graceful-degradation tests for the interpretability runner."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mimirbench.interpretability.runner import (
    InterpDataConfig,
    InterpExperimentsConfig,
    InterpModelConfig,
    InterpretabilityConfig,
    InterpRunConfig,
    run_interpretability,
)


def _config(*, output_dir: Path, checkpoint: Path, vocab: Path, experiments: InterpExperimentsConfig) -> InterpretabilityConfig:
    return InterpretabilityConfig(
        run=InterpRunConfig(name="interp_test", seed=123, output_dir=str(output_dir)),
        model=InterpModelConfig(checkpoint_path=str(checkpoint), vocab_path=str(vocab), device="cpu"),
        data=InterpDataConfig(num_examples=16, num_pairs=8, seed=123, min_observations=2),
        experiments=experiments,
        batch_size=8,
        max_examples=8,
    )


def test_runner_pending_when_checkpoint_missing(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"
    config = _config(
        output_dir=output_dir,
        checkpoint=tmp_path / "missing.pt",
        vocab=tmp_path / "missing.json",
        experiments=InterpExperimentsConfig(),
    )
    summary = run_interpretability(config)
    assert summary["status"] == "pending"
    assert summary["blockers"]
    report = output_dir / "INTERPRETABILITY_REPORT.md"
    assert report.exists()
    assert "pending" in report.read_text(encoding="utf-8").lower()
    # machine-readable summary is also written
    assert (output_dir / "summary.json").exists()


def test_runner_end_to_end(tiny_interp_checkpoint: dict, tmp_path: Path) -> None:
    pytest.importorskip("torch")
    output_dir = tmp_path / "run"
    config = _config(
        output_dir=output_dir,
        checkpoint=tiny_interp_checkpoint["checkpoint"],
        vocab=tiny_interp_checkpoint["vocab"],
        experiments=InterpExperimentsConfig(
            probes=True, activation_patching=True, attention_analysis=True
        ),
    )
    summary = run_interpretability(config)
    assert summary["status"] == "complete"
    assert summary["experiments_run"] == ["probes", "activation_patching", "attention_analysis"]

    # probe artefacts
    assert (output_dir / "probes" / "probe_summary.json").exists()
    for stem in ("posterior_probe", "action_probe", "risk_probe", "confidence_probe"):
        assert (output_dir / "probes" / f"{stem}.json").exists()
    # patching artefacts
    assert (output_dir / "activation_patching" / "patching_results.jsonl").exists()
    assert (output_dir / "activation_patching" / "patching_summary.json").exists()
    # attention artefacts
    assert (output_dir / "attention" / "attention_summary.json").exists()
    # report + figures
    assert (output_dir / "INTERPRETABILITY_REPORT.md").exists()
    figures = list(output_dir.rglob("figures/*.png"))
    assert len(figures) >= 9  # 4 probe + 3 patching + 3 attention (minus any single-layer dedupe)

    # headline metrics are present and well-formed
    headline = summary["experiments"]["probes"]["headline"]
    assert set(headline) == {"posterior_bucket", "action", "risk_flag", "confidence_bucket"}
    for row in headline.values():
        assert 0.0 <= row["test_accuracy"] <= 1.0
        assert 0.0 <= row["majority_baseline_accuracy"] <= 1.0


def test_runner_probes_only(tiny_interp_checkpoint: dict, tmp_path: Path) -> None:
    pytest.importorskip("torch")
    output_dir = tmp_path / "probes_only"
    config = _config(
        output_dir=output_dir,
        checkpoint=tiny_interp_checkpoint["checkpoint"],
        vocab=tiny_interp_checkpoint["vocab"],
        experiments=InterpExperimentsConfig(
            probes=True, activation_patching=False, attention_analysis=False
        ),
    )
    summary = run_interpretability(config)
    assert summary["experiments_run"] == ["probes"]
    assert not (output_dir / "activation_patching").exists()
    saved = json.loads((output_dir / "summary.json").read_text(encoding="utf-8"))
    assert saved["status"] == "complete"
