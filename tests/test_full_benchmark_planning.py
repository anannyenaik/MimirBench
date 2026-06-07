"""Full hosted-benchmark planning tests; no provider calls are permitted."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from mimirbench.analysis.full_benchmark_planning import (
    build_full_benchmark_plan,
    format_cost_range,
    validate_full_benchmark_config,
)
from mimirbench.cli import app
from mimirbench.evals import leaderboard
from mimirbench.evals.leaderboard import load_leaderboard_config

runner = CliRunner()

FULL_CONFIGS = (
    Path("configs/full/leaderboard_strict_100env_3seeds.yaml"),
    Path("configs/full/leaderboard_best_valid_100env_3seeds.yaml"),
    Path("configs/full/leaderboard_strict_200env_5seeds.yaml"),
    Path("configs/full/leaderboard_best_valid_200env_5seeds.yaml"),
)


def test_full_configs_parse_and_balance() -> None:
    for path in FULL_CONFIGS:
        config = load_leaderboard_config(path)
        validate_full_benchmark_config(config)
        assert config.protocol is not None
        assert config.protocol.execution_status == "planned_not_run"
        assert config.robustness.enabled is False


@pytest.mark.parametrize(
    ("path", "tasks_per_model", "scheduled_calls"),
    (
        (FULL_CONFIGS[0], 1_800, 9_000),
        (FULL_CONFIGS[1], 1_800, 7_200),
        (FULL_CONFIGS[2], 6_000, 30_000),
        (FULL_CONFIGS[3], 6_000, 24_000),
    ),
)
def test_task_and_call_counts(path: Path, tasks_per_model: int, scheduled_calls: int) -> None:
    plan = build_full_benchmark_plan(path)
    assert plan["counts"]["tasks_per_model"] == tasks_per_model
    assert plan["counts"]["scheduled_model_calls"] == scheduled_calls
    assert plan["provider_calls_made"] == 0
    assert plan["no_execute"] is True


def test_cost_estimate_formatting() -> None:
    assert format_cost_range(1.234, 56.789) == "$1.23-$56.79 USD"
    assert format_cost_range(None, None) == "not estimated (pricing fields missing)"


def test_cli_writes_no_execute_manifest_without_provider_check(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        leaderboard,
        "provider_status",
        lambda *_args, **_kwargs: pytest.fail("planner must not check providers"),
    )
    result = runner.invoke(
        app,
        [
            "plan-full-benchmark",
            str(FULL_CONFIGS[0]),
            "--output-dir",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "No provider was checked or called" in result.output
    manifest = json.loads((tmp_path / f"{FULL_CONFIGS[0].stem}.json").read_text(encoding="utf-8"))
    assert manifest["provider_calls_made"] == 0
    assert manifest["exact_run_command"].endswith(
        "run-leaderboard configs/full/leaderboard_strict_100env_3seeds.yaml --allow-real-models"
    )
