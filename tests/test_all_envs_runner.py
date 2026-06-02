"""Runner smoke tests across all six environments."""

from __future__ import annotations

from pathlib import Path

from mimirbench.evals.runner import run_eval_config
from mimirbench.evals.schemas import (
    AgentConfig,
    EnvironmentRunConfig,
    EvalRunConfig,
    ReportingConfig,
    RunSettings,
)
from mimirbench.evals.writers import load_records_jsonl

ALL_ENV_RUNS = [
    EnvironmentRunConfig(name="bayesian_games", num_tasks=2, seed=11),
    EnvironmentRunConfig(name="auctions", num_tasks=2, seed=21),
    EnvironmentRunConfig(name="hidden_regimes", num_tasks=2, seed=31),
    EnvironmentRunConfig(name="market_making", num_tasks=2, seed=41),
    EnvironmentRunConfig(name="prediction_markets", num_tasks=2, seed=51),
    EnvironmentRunConfig(name="adversarial_risk", num_tasks=2, seed=61),
]


def _config(tmp_path: Path, agent: AgentConfig, name: str) -> EvalRunConfig:
    return EvalRunConfig(
        run=RunSettings(
            name=name,
            seed=123,
            output_dir=str(tmp_path / name),
            cache=True,
            max_workers=1,
        ),
        agent=agent,
        environments=ALL_ENV_RUNS,
        reporting=ReportingConfig(),
    )


def test_reference_agent_runs_all_new_and_existing_environments(tmp_path) -> None:  # type: ignore[no-untyped-def]
    summary = run_eval_config(_config(tmp_path, AgentConfig(type="reference"), "reference_all"))
    records = load_records_jsonl(Path(summary["output_dir"]) / "results.jsonl")
    assert len(records) == 12
    assert summary["metrics"]["overall"]["runtime_error_rate"] == 0.0
    assert summary["metrics"]["overall"]["pass_rate"] == 1.0


def test_mock_agent_runs_all_new_and_existing_environments(tmp_path) -> None:  # type: ignore[no-untyped-def]
    summary = run_eval_config(
        _config(
            tmp_path,
            AgentConfig(type="mock", behaviour="random_valid", seed=7),
            "mock_all",
        )
    )
    records = load_records_jsonl(Path(summary["output_dir"]) / "results.jsonl")
    assert len(records) == 12
    assert summary["metrics"]["overall"]["runtime_error_rate"] == 0.0
