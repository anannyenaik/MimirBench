"""CLI smoke tests for Stage 2 commands."""

from __future__ import annotations

from typer.testing import CliRunner

from mimirbench.cli import app


def test_cli_validate_run_and_summarise(tmp_path) -> None:  # type: ignore[no-untyped-def]
    run_dir = tmp_path / "cli_run"
    config_path = tmp_path / "eval.yaml"
    config_path.write_text(
        f"""
run:
  name: cli_smoke
  seed: 5
  output_dir: {run_dir.as_posix()}
  cache: true
  max_workers: 1
agent:
  type: mock
  behaviour: random_valid
  seed: 5
environments:
  - name: bayesian_games
    num_tasks: 2
    seed: 5
reporting:
  write_jsonl: true
  write_summary: true
  write_markdown: true
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    validate = runner.invoke(app, ["validate-config", str(config_path)])
    assert validate.exit_code == 0
    assert "OK" in validate.output

    run = runner.invoke(app, ["run-eval", str(config_path)])
    assert run.exit_code == 0
    assert "cli_smoke" in run.output
    assert (run_dir / "summary.json").exists()

    summary = runner.invoke(app, ["summarise-run", str(run_dir)])
    assert summary.exit_code == 0
    assert "cli_smoke" in summary.output
