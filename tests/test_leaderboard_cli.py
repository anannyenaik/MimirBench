"""CLI smoke tests for leaderboard commands without network calls."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from mimirbench.agents.model_client import ProviderStatus
from mimirbench.cli import app
from mimirbench.evals import leaderboard

runner = CliRunner()


def _write_cli_config(path: Path, run_dir: Path) -> None:
    path.write_text(
        f"""
run:
  name: cli_leaderboard
  seed: 3
  output_dir: {run_dir.as_posix()}
  cache: true
  max_workers: 1
models:
  - name: cli_model
    provider: openai
    model: configured-model-id
    temperature: 0
agents:
  - direct
  - tool
  - reflective
environments:
  - name: bayesian_games
    num_tasks: 1
    seed: 3
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
        detail=f"{provider} unavailable for CLI smoke.",
    )


def test_cli_run_and_summarise_leaderboard_pending(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_dir = tmp_path / "leaderboard"
    config_path = tmp_path / "leaderboard.yaml"
    _write_cli_config(config_path, run_dir)
    monkeypatch.setattr(leaderboard, "provider_status", _unavailable_status)
    monkeypatch.setattr(
        leaderboard,
        "run_eval_config",
        lambda *_args, **_kwargs: pytest.fail("pending leaderboard should not run eval"),
    )

    run = runner.invoke(app, ["run-leaderboard", str(config_path)])
    assert run.exit_code == 0, run.output
    assert "headline candidates: none" in run.output.lower()
    assert (run_dir / "leaderboard_summary.json").exists()

    summary = runner.invoke(app, ["summarise-leaderboard", str(run_dir)])
    assert summary.exit_code == 0, summary.output
    assert "cli_leaderboard" in summary.output


def test_cli_estimate_leaderboard_cost(tmp_path: Path) -> None:
    run_dir = tmp_path / "leaderboard"
    config_path = tmp_path / "leaderboard.yaml"
    _write_cli_config(config_path, run_dir)

    estimate = runner.invoke(app, ["estimate-run-cost", str(config_path)])

    assert estimate.exit_code == 0, estimate.output
    assert "Leaderboard estimate" in estimate.output


def test_cli_check_provider_smoke_commands() -> None:
    for provider in ("openai", "anthropic", "gemini", "local"):
        result = runner.invoke(app, ["check-provider", provider])
        assert result.exit_code == 0, result.output
        assert provider.split("_")[0] in result.output.lower()
