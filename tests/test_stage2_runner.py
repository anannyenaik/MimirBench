"""Stage 2 runner tests."""

from __future__ import annotations

from pathlib import Path

from mimirbench.evals.runner import load_eval_config, run_eval_config, validate_eval_config
from mimirbench.evals.schemas import (
    AgentConfig,
    EnvironmentRunConfig,
    EvalRunConfig,
    EvalTaskRecord,
    ReportingConfig,
    RunSettings,
)
from mimirbench.evals.writers import load_records_jsonl


def _config(tmp_path: Path, *, max_workers: int = 1) -> EvalRunConfig:
    return EvalRunConfig(
        run=RunSettings(
            name=f"runner_test_{max_workers}",
            seed=10,
            output_dir=str(tmp_path / f"run_{max_workers}"),
            cache=True,
            max_workers=max_workers,
        ),
        agent=AgentConfig(type="mock", behaviour="random_valid", seed=42),
        environments=[EnvironmentRunConfig(name="bayesian_games", num_tasks=5, seed=10)],
        reporting=ReportingConfig(),
    )


def test_stage2_runner_writes_structured_records(tmp_path) -> None:  # type: ignore[no-untyped-def]
    config = _config(tmp_path)
    summary = run_eval_config(config)
    output_dir = Path(summary["output_dir"])
    records = load_records_jsonl(output_dir / "results.jsonl")

    assert summary["run_name"] == config.run.name
    assert len(records) == 5
    assert [record.task_id for record in records] == [f"bayesian_games-{10 + i}" for i in range(5)]
    assert all(record.raw_prompt for record in records)
    assert all(record.grader_result.task_id == record.task_id for record in records)


def test_stage2_runner_order_is_deterministic_with_threads(tmp_path) -> None:  # type: ignore[no-untyped-def]
    first_summary = run_eval_config(_config(tmp_path, max_workers=1))
    second_summary = run_eval_config(_config(tmp_path, max_workers=2))
    first = _stable_record_view(load_records_jsonl(Path(first_summary["output_dir"]) / "results.jsonl"))
    second = _stable_record_view(load_records_jsonl(Path(second_summary["output_dir"]) / "results.jsonl"))
    assert first == second


def test_load_and_validate_stage2_config() -> None:
    config = load_eval_config(Path("configs/eval_mock_bayes.yaml"))
    assert isinstance(config, EvalRunConfig)
    validate_eval_config(config)


def _stable_record_view(records: list[EvalTaskRecord]) -> list[tuple[str, str, float]]:
    return [
        (record.environment, record.task_id, record.grader_result.score)
        for record in records
    ]
