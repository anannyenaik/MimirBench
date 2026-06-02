"""Robustness runner tests."""

from __future__ import annotations

from pathlib import Path

from mimirbench.evals.robustness_runner import run_robustness_config
from mimirbench.evals.schemas import (
    AgentConfig,
    RobustnessEnvironmentConfig,
    RobustnessOptions,
    RobustnessReportingConfig,
    RobustnessRunConfig,
    RunSettings,
)
from mimirbench.evals.writers import load_robustness_records_jsonl


def test_robustness_runner_writes_records_summary_and_failures(tmp_path: Path) -> None:
    config = RobustnessRunConfig(
        run=RunSettings(
            name="robustness_runner_test",
            seed=11,
            output_dir=str(tmp_path / "robustness_runner_test"),
            max_workers=1,
        ),
        agent=AgentConfig(type="reference"),
        environments=[
            RobustnessEnvironmentConfig(
                name="bayesian_games",
                num_tasks=2,
                seed=11,
                variants_per_task=2,
                variant_types=["paraphrase", "irrelevant_context"],
            )
        ],
        robustness=RobustnessOptions(
            include_base_records=True,
            extract_failure_cases=True,
            max_variants_per_task=2,
        ),
        reporting=RobustnessReportingConfig(),
    )

    summary = run_robustness_config(config)
    output_dir = Path(summary["output_dir"])
    records = load_robustness_records_jsonl(output_dir / "robustness_results.jsonl")

    assert summary["counts"]["n_base_tasks"] == 2
    assert summary["counts"]["n_variants"] == 4
    assert summary["baseline_kind"] == "reference solver (sanity check)"
    assert (output_dir / "robustness_summary.json").exists()
    assert (output_dir / "robustness_report.md").exists()
    assert (output_dir / "failure_cases.jsonl").exists()
    assert (output_dir / "failure_cases.md").exists()

    base_records = [record for record in records if record.variant_id is None]
    variant_records = [record for record in records if record.variant_id is not None]
    assert len(base_records) == 2
    assert len(variant_records) == 4
    assert all(record.parent_task_id in {base.parent_task_id for base in base_records} for record in variant_records)
    assert all(record.metadata["base_prompt"] for record in variant_records)
    assert all(record.metadata["variant_prompt"] for record in variant_records)
    assert all(record.base_score == record.variant_score for record in variant_records)
    assert all(not record.action_changed for record in variant_records)
