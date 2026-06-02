"""Tests for reports/INDEX.md generation."""

from __future__ import annotations

import json

from mimirbench.reports.index import build_report_index


def test_report_index_includes_expected_directories(tmp_path) -> None:  # type: ignore[no-untyped-def]
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
    assert "score_by_environment.png" in text
    assert "baseline.md" in text
