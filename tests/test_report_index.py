"""Tests for reports/INDEX.md generation."""

from __future__ import annotations

import json
from pathlib import Path

from mimirbench.reports.index import build_report_index


def test_report_index_includes_expected_directories(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    run_dir = reports / "runs" / "baseline"
    run_dir.mkdir(parents=True)
    (run_dir / "summary.json").write_text(
        json.dumps(
            {
                "run_name": "baseline",
                "agent": {"type": "mock"},
                "metrics": {"overall": {"n_tasks": 1, "mean_score": 0.5}},
            }
        ),
        encoding="utf-8",
    )
    comparison_dir = reports / "runs" / "comparisons" / "mock_bayes"
    comparison_dir.mkdir(parents=True)
    (comparison_dir / "comparison_summary.json").write_text(
        json.dumps(
            {
                "comparison_name": "mock_bayes",
                "baseline_kind": "reference sanity check",
                "environments": [{"name": "bayesian_games", "num_tasks": 1}],
            }
        ),
        encoding="utf-8",
    )
    robustness_dir = reports / "runs" / "leaderboard" / "robustness_cell"
    robustness_dir.mkdir(parents=True)
    (robustness_dir / "robustness_summary.json").write_text(
        json.dumps(
            {
                "run_name": "nested_robustness",
                "baseline_kind": "real model",
                "counts": {"n_base_tasks": 2},
                "metrics": {"mean_score_drop": 0.1},
            }
        ),
        encoding="utf-8",
    )
    leaderboard_dir = reports / "runs" / "leaderboard" / "pending"
    leaderboard_dir.mkdir(parents=True)
    (leaderboard_dir / "leaderboard_summary.json").write_text(
        json.dumps(
            {
                "leaderboard_name": "pending",
                "models_run": [],
                "models_pending": [{"label": "configured_model"}],
                "tasks_per_agent": 10,
                "headline_candidates": [],
                "preliminary": True,
            }
        ),
        encoding="utf-8",
    )
    notes_path = reports / "runs" / "leaderboard" / "model_ladder_note.md"
    notes_path.write_text("# note\n", encoding="utf-8")
    figures = comparison_dir / "figures"
    figures.mkdir()
    (figures / "score_by_environment.png").write_bytes(b"png")
    cards = reports / "model_cards"
    cards.mkdir()
    (cards / "baseline.md").write_text("# card\n", encoding="utf-8")

    index_path = build_report_index(reports)
    text = index_path.read_text(encoding="utf-8")
    assert "baseline" in text
    assert "mock_bayes" in text
    assert "nested_robustness" in text
    assert "pending" in text
    assert "Leaderboard rows are hosted/local-model results only" in text
    assert "model_ladder_note.md" in text
    assert "score_by_environment.png" in text
    assert "baseline.md" in text
