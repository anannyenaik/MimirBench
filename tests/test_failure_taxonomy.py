"""Deterministic failure-taxonomy tests."""

from __future__ import annotations

from mimirbench.analysis.failure_cases import classify_eval_record, classify_robustness_record
from mimirbench.evals.schemas import (
    EnvironmentFamily,
    EvalTaskRecord,
    GraderResult,
    RobustnessRecord,
)


def _eval_record(
    *,
    environment: str = "bayesian_games",
    family: EnvironmentFamily = EnvironmentFamily.BAYESIAN_GAMES,
    parsed: dict[str, object] | None = None,
    response: str = "{}",
    score: float = 0.0,
    metrics: dict[str, float] | None = None,
    violations: list[str] | None = None,
) -> EvalTaskRecord:
    return EvalTaskRecord(
        run_id="run",
        timestamp="2026-06-02T00:00:00Z",
        environment=environment,
        task_id="task",
        seed=1,
        agent_type="api",
        agent_name="agent",
        raw_prompt="prompt",
        model_response=response,
        parsed_response=parsed,
        grader_result=GraderResult(
            task_id="task",
            family=family,
            score=score,
            passed=score >= 0.8,
            metrics=metrics or {},
            violations=violations or [],
            details={"reason": "missing required field"} if violations else {},
        ),
    )


def test_eval_failure_taxonomy_labels_deterministic_examples() -> None:
    assert {"invalid_json", "missing_required_field"} <= set(
        classify_eval_record(
            _eval_record(response="not json", parsed=None, violations=["no_valid_answer"])
        )
    )
    assert "posterior_miscalculation" in classify_eval_record(
        _eval_record(parsed={"posterior": [0.5, 0.5]}, score=0.5, metrics={"posterior_tv_error": 0.5})
    )
    assert "overconfidence" in classify_eval_record(
        _eval_record(
            environment="prediction_markets",
            family=EnvironmentFamily.PREDICTION_MARKETS,
            parsed={"action": "buy", "confidence": 0.95},
            score=0.2,
        )
    )
    assert "ignored_risk_limit" in classify_eval_record(
        _eval_record(
            environment="adversarial_risk",
            family=EnvironmentFamily.ADVERSARIAL_RISK,
            parsed={"action": "approve"},
            score=0.05,
            metrics={"unsafe_action": 1.0},
            violations=["unsafe_action"],
        )
    )


def test_robustness_failure_taxonomy_labels_paraphrase_flip() -> None:
    record = RobustnessRecord(
        run_id="run",
        timestamp="2026-06-02T00:00:00Z",
        environment="bayesian_games",
        parent_task_id="task",
        variant_id="task::paraphrase",
        variant_type="paraphrase",
        answer_preserving=True,
        base_score=1.0,
        variant_score=0.4,
        score_delta=-0.6,
        base_action="argmax:0",
        variant_action="argmax:1",
        action_changed=True,
        base_passed=True,
        variant_passed=False,
    )
    assert "action_flip_under_paraphrase" in classify_robustness_record(record)
