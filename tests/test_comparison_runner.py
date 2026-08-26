"""Comparison-runner tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mimirbench.evals.comparison_runner import (
    load_comparison_config,
    run_comparison_config,
    validate_comparison_config,
)
from mimirbench.evals.writers import load_records_jsonl


def test_comparison_runner_preserves_task_ids_and_computes_deltas(tmp_path: Path) -> None:
    run_dir = tmp_path / "comparison"
    config_path = tmp_path / "comparison.yaml"
    config_path.write_text(
        f"""
run:
  name: comparison_test
  seed: 7
  output_dir: {run_dir.as_posix()}
  cache: true
  max_workers: 1
baseline_agent: reference
agents:
  - name: reference
    type: reference
  - name: mock_random_valid
    type: mock
    behaviour: random_valid
    seed: 7
environments:
  - name: bayesian_games
    num_tasks: 3
    seed: 7
reporting:
  write_jsonl: true
  write_summary: true
  write_markdown: true
""",
        encoding="utf-8",
    )

    config = load_comparison_config(config_path)
    validate_comparison_config(config)
    summary = run_comparison_config(config)

    reference_records = load_records_jsonl(run_dir / "agent_runs" / "reference" / "results.jsonl")
    mock_records = load_records_jsonl(run_dir / "agent_runs" / "mock_random_valid" / "results.jsonl")
    reference_ids = [(record.environment, record.task_id) for record in reference_records]
    mock_ids = [(record.environment, record.task_id) for record in mock_records]
    assert reference_ids == mock_ids

    paired_path = run_dir / "paired_results.jsonl"
    rows = [json.loads(line) for line in paired_path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 3
    expected = mock_records[0].grader_result.score - reference_records[0].grader_result.score
    assert rows[0]["deltas"]["score_difference"] == pytest.approx(expected)
    assert summary["paired_metrics"]["mock_random_valid"]["n_pairs"] == 3
    assert (run_dir / "comparison_report.md").exists()
