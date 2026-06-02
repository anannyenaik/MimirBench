"""CLI smoke tests for robustness commands."""

from __future__ import annotations

from typer.testing import CliRunner

from mimirbench.cli import app


def test_robustness_cli_list_run_and_summarise(tmp_path) -> None:  # type: ignore[no-untyped-def]
    run_dir = tmp_path / "robustness_cli"
    config_path = tmp_path / "robustness.yaml"
    config_path.write_text(
        f"""
run:
  name: robustness_cli
  seed: 5
  output_dir: {run_dir.as_posix()}
  max_workers: 1
agent:
  type: reference
environments:
  - name: bayesian_games
    num_tasks: 1
    seed: 5
    variants_per_task: 2
    variant_types:
      - paraphrase
      - irrelevant_context
robustness:
  include_base_records: true
  extract_failure_cases: true
  max_variants_per_task: 2
  max_failure_cases: 5
reporting:
  write_jsonl: true
  write_summary: true
  write_markdown: true
  write_failure_cases: true
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    variant_types = runner.invoke(app, ["list-variant-types"])
    assert variant_types.exit_code == 0
    assert "prompt_injection_style" in variant_types.output

    run = runner.invoke(app, ["run-robustness", str(config_path)])
    assert run.exit_code == 0
    assert "robustness_cli" in run.output
    assert (run_dir / "robustness_summary.json").exists()

    summary = runner.invoke(app, ["summarise-robustness", str(run_dir)])
    assert summary.exit_code == 0
    assert "reference solver" in summary.output
