"""Paired leaderboard deltas must align on task identity and seed."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mimirbench.evals.leaderboard import _eval_pair_rows, _robustness_pair_rows
from mimirbench.evals.schemas import (
    EnvironmentFamily,
    EvalTaskRecord,
    GraderResult,
    RobustnessRecord,
)


def _eval_record(task_id: str, seed: int, score: float) -> EvalTaskRecord:
    return EvalTaskRecord(
        run_id="r",
        timestamp="2026-06-02T00:00:00Z",
        environment="bayesian_games",
        task_id=task_id,
        seed=seed,
        agent_type="direct",
        agent_name="agent",
        raw_prompt="prompt",
        model_response="{}",
        parsed_response={},
        grader_result=GraderResult(
            task_id=task_id,
            family=EnvironmentFamily.BAYESIAN_GAMES,
            score=score,
            passed=score > 0,
        ),
    )


def _robustness_record(seed: int, variant_score: float) -> RobustnessRecord:
    return RobustnessRecord(
        run_id="r",
        timestamp="2026-06-02T00:00:00Z",
        environment="bayesian_games",
        seed=seed,
        parent_task_id="bayesian_games-1",
        variant_id="bayesian_games-1::paraphrase",
        variant_type="paraphrase",
        answer_preserving=True,
        base_score=1.0,
        variant_score=variant_score,
        score_delta=variant_score - 1.0,
    )


def test_eval_pairing_requires_matching_seed() -> None:
    rows = _eval_pair_rows(
        model_label="model",
        baseline_mode="direct",
        candidate_mode="tool",
        baseline=[_eval_record("task-1", 1, 0.25)],
        candidate=[_eval_record("task-1", 2, 1.0), _eval_record("task-1", 1, 0.75)],
    )

    assert len(rows) == 1
    assert rows[0]["seed"] == 1
    assert rows[0]["deltas"]["score_difference"] == 0.5


def test_robustness_pairing_requires_matching_seed(tmp_path: Path) -> None:
    baseline_dir = tmp_path / "baseline"
    candidate_dir = tmp_path / "candidate"
    baseline_dir.mkdir()
    candidate_dir.mkdir()
    (baseline_dir / "robustness_results.jsonl").write_text(
        json.dumps(_robustness_record(1, 0.8).model_dump(mode="json")) + "\n",
        encoding="utf-8",
    )
    (candidate_dir / "robustness_results.jsonl").write_text(
        json.dumps(_robustness_record(2, 0.1).model_dump(mode="json"))
        + "\n"
        + json.dumps(_robustness_record(1, 0.9).model_dump(mode="json"))
        + "\n",
        encoding="utf-8",
    )

    rows = _robustness_pair_rows(
        model_label="model",
        baseline_mode="direct",
        candidate_mode="tool",
        baseline_dir=str(baseline_dir),
        candidate_dir=str(candidate_dir),
    )

    assert len(rows) == 1
    assert rows[0]["seed"] == 1
    assert rows[0]["deltas"]["variant_score_difference"] == pytest.approx(0.1)
