"""Offline verification of the selected empirical evidence."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

import scripts.reproduce_results as reproduction
from scripts.plot_results import environment_score_matrix, head_metric_matrix

ROOT = Path(__file__).resolve().parents[1]
SELECTED = ROOT / "experiments" / "selected_results"


def _selected_hashes() -> dict[str, str]:
    return {
        path.relative_to(SELECTED).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in SELECTED.rglob("*")
        if path.is_file()
    }


def test_reproduction_verifies_without_mutating_selected_results() -> None:
    before = _selected_hashes()
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "reproduce_results.py")],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "960 aligned task records verified" in completed.stdout
    assert _selected_hashes() == before


def test_default_plotting_does_not_mutate_publication_figures() -> None:
    publication_hashes = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (ROOT / "figures").iterdir()
        if path.is_file()
    }
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "plot_results.py")],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    output_dir = ROOT / "build" / "figures"
    expected_stems = {
        "benchmark_profiles",
        "benchmark_scores",
        "head_mechanisms",
        "interpretability_recovery",
    }
    assert {path.stem for path in output_dir.glob("*.png")} == expected_stems
    assert {path.stem for path in output_dir.glob("*.pdf")} == expected_stems
    assert {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (ROOT / "figures").iterdir()
        if path.is_file()
    } == publication_hashes


def test_selected_data_hashes_are_enforced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = json.loads((SELECTED / "manifest.json").read_text(encoding="utf-8"))
    assert "figures" not in manifest

    copied = tmp_path / "selected_results"
    shutil.copytree(SELECTED, copied)
    tampered = copied / "benchmark" / "openai_gpt_5_4.jsonl"
    tampered.write_bytes(tampered.read_bytes() + b"\n")
    monkeypatch.setattr(reproduction, "SELECTED", copied)
    monkeypatch.setattr(reproduction, "MANIFEST_PATH", copied / "manifest.json")
    monkeypatch.setattr(reproduction, "CHECKSUMS_PATH", copied / "SHA256SUMS")

    with pytest.raises(ValueError, match="manifest mismatch"):
        reproduction.verify_integrity_files()


def test_figure_input_matrices_come_from_selected_results() -> None:
    benchmark = json.loads((SELECTED / "benchmark" / "summary.json").read_text(encoding="utf-8"))
    strict_models = [model for model in benchmark["models"] if model["track"] == "strict-512"]
    assert len(strict_models) == 5
    assert all(model["protocol"]["max_tokens"] == 512 for model in strict_models)
    assert {model["protocol"]["temperature"] for model in strict_models} == {
        0,
        "provider default",
    }

    labels, environment_scores = environment_score_matrix(benchmark)
    assert environment_scores.shape == (8, 6)
    first_model = next(model for model in benchmark["models"] if model["display"] == labels[0])
    assert environment_scores[0, 0] == first_model["environment_metrics"]["bayesian_games"][
        "mean_score"
    ]

    interventions = json.loads(
        (SELECTED / "interpretability" / "head_position_summary.json").read_text(
            encoding="utf-8"
        )
    )
    seeds, patching = head_metric_matrix(
        interventions, "per_head_patching", "matched_action_recovery"
    )
    ablation_seeds, ablation = head_metric_matrix(
        interventions, "per_head_ablation", "posterior_bucket_accuracy_degradation"
    )
    assert seeds == ablation_seeds == [123, 124, 125, 126, 127, 128]
    assert patching.shape == ablation.shape == (6, 8)
    assert float(np.max(patching.mean(axis=0))) == pytest.approx(0.14089386630370238)
    assert float(np.max(ablation.mean(axis=0))) == pytest.approx(0.3138020833333333)
