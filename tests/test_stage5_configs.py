"""Validation checks for Stage 5 configs and the new CLI commands.

These tests validate configs and exercise CLI plumbing only. They never run an
API or local config (no network, no model downloads, no API keys).
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from mimirbench.cli import app
from mimirbench.evals.robustness_runner import load_robustness_config, validate_robustness_config
from mimirbench.evals.runner import load_eval_config, validate_eval_config
from mimirbench.evals.schemas import EvalRunConfig

runner = CliRunner()

STAGE5_EVAL_CONFIGS = [
    Path("configs/eval_api_openai_bayes_smoke.yaml"),
    Path("configs/eval_api_openai_all_envs_tiny.yaml"),
    Path("configs/eval_local_bayes_smoke.yaml"),
    Path("configs/eval_local_all_envs_tiny.yaml"),
    Path("configs/eval_tool_reference_bayes.yaml"),
    Path("configs/eval_tool_api_openai_bayes_smoke.yaml"),
]

STAGE5_ROBUSTNESS_CONFIGS = [
    Path("configs/eval_api_openai_robustness_bayes_tiny.yaml"),
]


def test_all_stage5_eval_configs_validate() -> None:
    for path in STAGE5_EVAL_CONFIGS:
        config = load_eval_config(path)
        assert isinstance(config, EvalRunConfig)
        validate_eval_config(config)


def test_all_stage5_robustness_configs_validate() -> None:
    for path in STAGE5_ROBUSTNESS_CONFIGS:
        config = load_robustness_config(path)
        validate_robustness_config(config)


def test_stage5_configs_use_tiny_task_counts() -> None:
    for path in STAGE5_EVAL_CONFIGS:
        config = load_eval_config(path)
        assert isinstance(config, EvalRunConfig)
        assert config.run.max_workers == 1
        for env in config.environments:
            assert env.num_tasks <= 20, f"{path}: tiny configs should stay small"


def test_stage5_configs_expose_model_backends() -> None:
    types_seen = {load_eval_config(p).agent.type for p in STAGE5_EVAL_CONFIGS}  # type: ignore[union-attr]
    assert {"api", "local", "tool"} <= types_seen


def test_cli_validate_config_on_stage5_configs() -> None:
    for path in STAGE5_EVAL_CONFIGS:
        result = runner.invoke(app, ["validate-config", str(path)])
        assert result.exit_code == 0, result.output


def test_cli_estimate_run_cost_api_config() -> None:
    result = runner.invoke(app, ["estimate-run-cost", "configs/eval_api_openai_bayes_smoke.yaml"])
    assert result.exit_code == 0
    assert "not estimated" in result.output.lower()  # no pricing configured


def test_cli_estimate_run_cost_reference_tool_is_free() -> None:
    result = runner.invoke(app, ["estimate-run-cost", "configs/eval_tool_reference_bayes.yaml"])
    assert result.exit_code == 0
    assert "no api calls" in result.output.lower()


def test_cli_inspect_failures_and_tool_audit(tmp_path) -> None:  # type: ignore[no-untyped-def]
    # Run the deterministic reference tool agent to produce artefacts, then inspect.
    run_dir = tmp_path / "run"
    config_path = tmp_path / "tool.yaml"
    config_path.write_text(
        f"""
run:
  name: stage5_cli_tool
  seed: 1
  output_dir: {run_dir.as_posix()}
  cache: false
  max_workers: 1
agent:
  type: tool
  tool_policy: reference
  tool_max_steps: 3
environments:
  - name: bayesian_games
    num_tasks: 3
    seed: 1
reporting:
  write_jsonl: true
  write_summary: true
  write_markdown: true
""",
        encoding="utf-8",
    )
    run = runner.invoke(app, ["run-eval", str(config_path)])
    assert run.exit_code == 0, run.output

    failures = runner.invoke(app, ["inspect-failures", str(run_dir)])
    assert failures.exit_code == 0

    audit = runner.invoke(app, ["inspect-tool-audit", str(run_dir)])
    assert audit.exit_code == 0
    assert "tool_call_rate" in audit.output
