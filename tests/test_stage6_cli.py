"""CLI smoke tests for Stage 6 commands."""

from __future__ import annotations

from typer.testing import CliRunner

from mimirbench.cli import app


def test_stage6_cli_commands_smoke(tmp_path) -> None:  # type: ignore[no-untyped-def]
    reports_dir = tmp_path / "reports"
    run_dir = reports_dir / "runs" / "comparisons" / "cli_compare"
    config_path = tmp_path / "comparison.yaml"
    config_path.write_text(
        f"""
run:
  name: cli_compare
  seed: 11
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
    seed: 11
environments:
  - name: bayesian_games
    num_tasks: 2
    seed: 11
reporting:
  write_jsonl: true
  write_summary: true
  write_markdown: true
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    estimate = runner.invoke(app, ["estimate-run-cost", str(config_path)])
    assert estimate.exit_code == 0, estimate.output
    assert "Comparison estimate" in estimate.output

    run = runner.invoke(app, ["run-comparison", str(config_path)])
    assert run.exit_code == 0, run.output
    assert (run_dir / "comparison_summary.json").exists()

    summary = runner.invoke(app, ["summarise-comparison", str(run_dir)])
    assert summary.exit_code == 0, summary.output
    assert "Paired deltas" in summary.output

    plots = runner.invoke(app, ["make-plots", str(run_dir)])
    assert plots.exit_code == 0, plots.output
    assert "Generated" in plots.output

    card = runner.invoke(
        app,
        [
            "make-model-card",
            str(run_dir / "agent_runs" / "reference"),
            "--output-dir",
            str(reports_dir / "model_cards"),
        ],
    )
    assert card.exit_code == 0, card.output
    assert "Model card written" in card.output

    index = runner.invoke(app, ["build-report-index", "--reports-dir", str(reports_dir)])
    assert index.exit_code == 0, index.output
    assert (reports_dir / "INDEX.md").exists()
