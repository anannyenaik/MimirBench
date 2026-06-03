"""Leaderboard runner guardrails for pending/no-provider runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from mimirbench.agents.model_client import ProviderStatus
from mimirbench.evals import leaderboard


def _write_openai_config(path: Path, run_dir: Path) -> None:
    path.write_text(
        f"""
run:
  name: pending_test
  seed: 11
  output_dir: {run_dir.as_posix()}
  cache: true
  max_workers: 1
models:
  - name: configured_model
    provider: openai
    model: configured-model-id
    api_key_env: OPENAI_API_KEY
    temperature: 0
agents:
  - direct
  - tool
  - reflective
environments:
  - name: bayesian_games
    num_tasks: 1
    seed: 11
robustness:
  enabled: true
reporting:
  write_jsonl: true
  write_summary: true
  write_markdown: true
""",
        encoding="utf-8",
    )


def _unavailable_status(provider: str, **_: Any) -> ProviderStatus:
    return ProviderStatus(
        provider=provider,
        package_available=False,
        key_required=True,
        key_present=False,
        key_env="OPENAI_API_KEY",
        usable=False,
        detail=f"{provider} unavailable for test.",
    )


def _usable_status(provider: str, **_: Any) -> ProviderStatus:
    return ProviderStatus(
        provider=provider,
        package_available=True,
        key_required=True,
        key_present=True,
        key_env="OPENAI_API_KEY",
        usable=True,
        detail=f"{provider} usable for test.",
    )


def test_no_provider_run_writes_pending_artefacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_dir = tmp_path / "leaderboard"
    config_path = tmp_path / "leaderboard.yaml"
    _write_openai_config(config_path, run_dir)
    monkeypatch.setattr(leaderboard, "provider_status", _unavailable_status)
    monkeypatch.setattr(
        leaderboard,
        "run_eval_config",
        lambda *_args, **_kwargs: pytest.fail("provider-gated run should not call eval"),
    )

    config = leaderboard.load_leaderboard_config(config_path)
    summary = leaderboard.run_leaderboard_config(config)

    assert summary["models_run"] == []
    assert summary["models_pending"][0]["label"] == "configured_model"
    assert summary["headline_candidates"] == []
    assert summary["real_execution_permitted"] is False
    assert (run_dir / "leaderboard_summary.json").exists()
    assert (run_dir / "leaderboard_report.md").exists()
    assert (run_dir / "headline_candidates.md").exists()
    assert (run_dir / "paired_deltas.jsonl").read_text(encoding="utf-8") == ""

    persisted = json.loads((run_dir / "leaderboard_summary.json").read_text(encoding="utf-8"))
    assert persisted["models_run"] == []
    report = (run_dir / "leaderboard_report.md").read_text(encoding="utf-8")
    assert "| Model | Provider | Agent | Envs | Tasks | Mean score | Robustness" in report
    assert "No model-performance rows were produced" in report


def test_usable_real_provider_still_requires_explicit_permission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_dir = tmp_path / "leaderboard"
    config_path = tmp_path / "leaderboard.yaml"
    _write_openai_config(config_path, run_dir)
    monkeypatch.setattr(leaderboard, "provider_status", _usable_status)
    monkeypatch.setattr(
        leaderboard,
        "run_eval_config",
        lambda *_args, **_kwargs: pytest.fail("real model run requires explicit permission"),
    )

    summary = leaderboard.run_leaderboard_config(leaderboard.load_leaderboard_config(config_path))

    assert summary["models_run"] == []
    assert "explicit permission" in summary["models_pending"][0]["detail"]
