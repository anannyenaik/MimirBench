"""Validation checks for the Stage 8 interpretability configs (no torch needed)."""

from __future__ import annotations

from pathlib import Path

import pytest

from mimirbench.interpretability.runner import load_interpretability_config

CONFIGS = {
    "configs/interp_bayes_probes_tiny.yaml": ("probes",),
    "configs/interp_bayes_patching_tiny.yaml": ("activation_patching",),
    "configs/interp_bayes_attention_tiny.yaml": ("attention_analysis",),
    "configs/interp_bayes_all_tiny.yaml": ("probes", "activation_patching", "attention_analysis"),
}


@pytest.mark.parametrize("config_path", sorted(CONFIGS))
def test_interpretability_configs_validate(config_path: str) -> None:
    config = load_interpretability_config(Path(config_path))
    config.validate()
    assert config.run.output_dir.startswith("reports/interpretability/")
    assert config.data.num_examples > 0
    assert config.data.num_pairs > 0
    assert config.model.device == "cpu"
    assert config.model.checkpoint_path.endswith(".pt")
    assert config.model.vocab_path.endswith(".json")


@pytest.mark.parametrize("config_path", sorted(CONFIGS))
def test_interpretability_config_experiment_flags(config_path: str) -> None:
    config = load_interpretability_config(Path(config_path))
    enabled = {
        name
        for name, flag in (
            ("probes", config.experiments.probes),
            ("activation_patching", config.experiments.activation_patching),
            ("attention_analysis", config.experiments.attention_analysis),
        )
        if flag
    }
    assert enabled == set(CONFIGS[config_path])


def test_interpretability_config_rejects_non_mapping(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("- not\n- a mapping\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_interpretability_config(bad)
