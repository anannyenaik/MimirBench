"""Validation checks for the retained interpretability configurations."""

from __future__ import annotations

from pathlib import Path

import pytest

from mimirbench.interpretability.multiseed import load_multiseed_config
from mimirbench.interpretability.runner import load_interpretability_config


@pytest.mark.parametrize(
    "config_path",
    [
        Path("configs/interpretability/whole_site.yaml"),
        Path("configs/interpretability/controls.yaml"),
    ],
)
def test_interpretability_configs_validate(config_path: Path) -> None:
    config = load_interpretability_config(config_path)
    config.validate()
    assert config.run.output_dir.startswith("runs/interpretability/")
    assert config.data.num_examples > 0
    assert config.data.num_pairs > 0
    assert config.model.device == "cpu"


def test_six_seed_config_is_complete() -> None:
    config = load_multiseed_config(Path("configs/interpretability/six_seed.yaml"))
    config.validate()
    assert config.seeds == (123, 124, 125, 126, 127, 128)
    assert config.train_template == "configs/training/medium.yaml"
    assert config.interp_template == "configs/interpretability/whole_site.yaml"


def test_interpretability_config_rejects_non_mapping(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("- not\n- a mapping\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_interpretability_config(bad)
