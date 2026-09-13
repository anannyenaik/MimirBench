"""Robustness metric and scoring-helper tests."""

from __future__ import annotations

import pytest

from mimirbench.analysis.robustness import compute_robustness_metrics
from mimirbench.evals.schemas import EnvironmentFamily, GraderResult, RobustnessRecord
from mimirbench.evals.scoring import canonical_action, is_invalid, is_risk_violation, is_unsafe


def _record(
    variant_type: str,
    *,
    base_score: float = 1.0,
    variant_score: float = 1.0,
    answer_preserving: bool = True,
    action_changed: bool = False,
    became_invalid: bool = False,
    became_unsafe: bool = False,
    pressure_susceptibility: float | None = None,
    became_risk_violation: bool = False,
) -> RobustnessRecord:
    return RobustnessRecord(
        run_id="run",
        timestamp="2026-06-02T00:00:00Z",
        environment="bayesian_games",
        parent_task_id="task-1",
        variant_id=f"task-1::{variant_type}",
        variant_type=variant_type,
        answer_preserving=answer_preserving,
        base_score=base_score,
        variant_score=variant_score,
        score_delta=variant_score - base_score,
        base_action="argmax:0",
        variant_action="argmax:1" if action_changed else "argmax:0",
        action_changed=action_changed,
        became_invalid=became_invalid,
        became_unsafe=became_unsafe,
        pressure_susceptibility=pressure_susceptibility,
        base_passed=True,
        variant_passed=variant_score >= 0.5,
        metadata={"became_risk_violation": became_risk_violation},
    )


def test_compute_robustness_metrics_detects_drops_flips_and_safety_regressions() -> None:
    records = [
        _record("paraphrase", variant_score=0.9),
        _record("paraphrase", variant_score=0.4, action_changed=True),
        _record(
            "risk_pressure",
            variant_score=0.5,
            action_changed=True,
            became_invalid=True,
            became_unsafe=True,
            pressure_susceptibility=1.0,
            became_risk_violation=True,
        ),
        _record("distractor_signal", variant_score=1.0),
    ]

    metrics = compute_robustness_metrics(records)

    assert metrics["n_variants"] == 4
    assert metrics["n_answer_preserving"] == 4
    assert metrics["paraphrase_consistency_rate"] == pytest.approx(0.5)
    assert metrics["mean_score_drop"] == pytest.approx(0.3)
    assert metrics["worst_score_drop"] == pytest.approx(0.6)
    assert metrics["action_flip_rate"] == pytest.approx(0.5)
    assert metrics["invalid_response_increase"] == pytest.approx(0.25)
    assert metrics["unsafe_action_increase"] == pytest.approx(0.25)
    assert metrics["risk_violation_increase"] == pytest.approx(0.25)
    assert metrics["pressure_susceptibility_rate"] == pytest.approx(1.0)
    assert metrics["distractor_robustness_rate"] == pytest.approx(1.0)
    assert metrics["variant_type_breakdown"]["paraphrase"]["action_flip_rate"] == pytest.approx(0.5)


def test_non_answer_preserving_variants_are_excluded_from_flip_statistics() -> None:
    metrics = compute_robustness_metrics(
        [
            _record("unit_scale_change", answer_preserving=False, action_changed=True),
            _record("paraphrase", action_changed=False),
        ]
    )

    assert metrics["n_variants"] == 2
    assert metrics["n_answer_preserving"] == 1
    assert metrics["action_flip_rate"] == pytest.approx(0.0)


def test_scoring_helpers_detect_invalid_unsafe_and_canonical_actions() -> None:
    result = GraderResult(
        task_id="task",
        family=EnvironmentFamily.ADVERSARIAL_RISK,
        score=0.0,
        passed=False,
        metrics={"risk_limit_violation": 1.0},
        violations=["invalid_response"],
    )

    assert is_invalid(result) is True
    assert is_unsafe(result) is True
    assert is_risk_violation(result) is True
    assert canonical_action(EnvironmentFamily.PREDICTION_MARKETS, {"action": "buy"}) == "buy"
    assert canonical_action(EnvironmentFamily.BAYESIAN_GAMES, {"posterior": [0.1, 0.9]}) == "argmax:1"
