"""Failure-case extraction tests."""

from __future__ import annotations

from mimirbench.analysis.failure_cases import classify_failure, extract_failure_cases
from mimirbench.evals.schemas import RobustnessRecord


def _record(
    label: str,
    *,
    variant_type: str = "paraphrase",
    base_score: float = 1.0,
    variant_score: float = 0.2,
    base_passed: bool = True,
    variant_passed: bool = True,
    action_changed: bool = False,
    became_invalid: bool = False,
    became_unsafe: bool = False,
    variant_violations: list[str] | None = None,
    metadata: dict[str, object] | None = None,
) -> RobustnessRecord:
    return RobustnessRecord(
        run_id="run",
        timestamp="2026-06-02T00:00:00Z",
        environment="adversarial_risk",
        parent_task_id=f"task-{label}",
        variant_id=f"task-{label}::{variant_type}",
        variant_type=variant_type,
        answer_preserving=True,
        base_score=base_score,
        variant_score=variant_score,
        score_delta=variant_score - base_score,
        base_action="reject",
        variant_action="approve" if action_changed else "reject",
        action_changed=action_changed,
        became_invalid=became_invalid,
        became_unsafe=became_unsafe,
        base_passed=base_passed,
        variant_passed=variant_passed,
        base_violations=[],
        variant_violations=variant_violations or [],
        base_response='{"action":"reject"}',
        variant_response='{"action":"approve"}',
        metadata={
            "base_prompt": "base prompt",
            "variant_prompt": "variant prompt",
            **(metadata or {}),
        },
    )


def _failure_label(record: RobustnessRecord) -> str:
    classified = classify_failure(record)
    assert classified is not None
    return classified[0]


def test_extract_failure_cases_prioritises_safety_and_keeps_payload_context() -> None:
    cases = extract_failure_cases(
        [
            _record("drop", variant_type="irrelevant_context", variant_score=0.6),
            _record(
                "unsafe",
                variant_type="risk_pressure",
                variant_score=0.4,
                action_changed=True,
                became_unsafe=True,
                variant_violations=["unsafe_action"],
            ),
        ],
        limit=2,
    )

    assert [case["diagnostic_label"] for case in cases] == ["safe_to_unsafe", "large_score_drop"]
    assert cases[0]["base_prompt"] == "base prompt"
    assert cases[0]["variant_prompt"] == "variant prompt"
    assert cases[0]["base_grader_result"]["passed"] is True
    assert cases[0]["variant_grader_result"]["violations"] == ["unsafe_action"]


def test_failure_classifier_detects_required_failure_modes() -> None:
    assert _failure_label(
        _record(
            "risk",
            variant_type="risk_pressure",
            variant_score=0.5,
            metadata={"became_risk_violation": True},
        )
    ) == "pressure_risk_violation"
    assert _failure_label(
        _record(
            "invalid",
            became_invalid=True,
            variant_violations=["invalid_response"],
        )
    ) == "became_invalid"
    assert _failure_label(
        _record(
            "paraphrase",
            variant_score=0.8,
            action_changed=True,
        )
    ) == "paraphrase_action_flip"
    assert _failure_label(
        _record(
            "confidence",
            variant_type="misleading_authority",
            variant_score=0.2,
            base_passed=False,
            variant_passed=False,
            metadata={"variant_confidence": 0.9},
        )
    ) == "overconfident_wrong"
    assert _failure_label(
        _record(
            "regret",
            variant_type="distractor_signal",
            variant_score=0.8,
            base_passed=False,
            variant_passed=True,
            metadata={"variant_metrics": {"regret": 0.25}},
        )
    ) == "high_regret"
