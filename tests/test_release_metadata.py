"""Checks for the package and selected-result release surface."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_package_version_is_020() -> None:
    import mimirbench

    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["version"] == "0.2.0"
    assert mimirbench.__version__ == "0.2.0"


def test_authorship_metadata_is_consistent() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert project["authors"] == [{"name": "Anannye Naik"}]
    assert "Copyright (c) 2026 Anannye Naik" in (ROOT / "LICENSE").read_text(
        encoding="utf-8"
    )
    assert "author = {Anannye Naik}" in (ROOT / "README.md").read_text(encoding="utf-8")


def test_selected_result_manifest_counts() -> None:
    manifest = json.loads(
        (ROOT / "experiments" / "selected_results" / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["benchmark"]["model_rows"] == 8
    assert manifest["benchmark"]["task_records"] == 960
    assert manifest["interpretability"]["seeds"] == [123, 124, 125, 126, 127, 128]
