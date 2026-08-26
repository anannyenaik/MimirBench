"""Guard the public v0.2.0 release metadata against stale pre-release wording."""

from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_declares_v020_alpha() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = data["project"]
    assert project["version"] == "0.2.0"
    assert "Development Status :: 3 - Alpha" in project["classifiers"]
    assert "Development Status :: 2 - Pre-Alpha" not in project["classifiers"]


def test_runtime_version_matches_pyproject() -> None:
    """``mimirbench --version`` must not drift from the packaged version."""
    import mimirbench

    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert mimirbench.__version__ == data["project"]["version"]


def test_release_docs_describe_existing_assets_without_stale_creation_steps() -> None:
    release_notes = (ROOT / "RELEASE_NOTES_v0.2.0.md").read_text(encoding="utf-8")
    artifacts = (ROOT / "ARTIFACTS.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "No GitHub release currently exists" not in release_notes
    assert "gh release create" not in release_notes
    assert "Convenience release assets" in artifacts
    for text in (release_notes, artifacts, readme):
        assert "best.pt" in text
        assert "vocab.json" in text
        assert "releases/tag/v0.2.0" in text
