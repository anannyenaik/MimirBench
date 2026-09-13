"""Deterministic grader for auction expected-surplus tasks."""

from __future__ import annotations

from mimirbench.evals.schemas import GraderResult, GradingKey, ModelResponse, Task

__all__ = ["PASS_REL_ERROR", "grade"]

# A numeric answer passes if its relative error is within this bound.
PASS_REL_ERROR = 0.02
_EPS = 1e-9


def _extract_number(response: ModelResponse, field: str) -> float | None:
    if response.parsed_answer is None:
        return None
    value = response.parsed_answer.get(field)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def grade(task: Task, response: ModelResponse, key: GradingKey) -> GraderResult:
    """Grade an expected-surplus answer against the closed-form value."""
    true_value = float(key.payload["expected_surplus"])
    pred = _extract_number(response, "expected_surplus")

    if pred is None:
        return GraderResult(
            task_id=task.task_id,
            family=task.family,
            score=0.0,
            passed=False,
            violations=["no_valid_answer"],
            details={"reason": "missing or malformed 'expected_surplus' field"},
        )

    abs_error = abs(pred - true_value)
    rel_error = abs_error / (abs(true_value) + _EPS)
    score = max(0.0, 1.0 - rel_error)

    return GraderResult(
        task_id=task.task_id,
        family=task.family,
        score=score,
        passed=rel_error <= PASS_REL_ERROR,
        metrics={
            "expected_value_abs_error": abs_error,
            "expected_value_rel_error": rel_error,
        },
        details={"true_value": true_value, "predicted_value": pred},
    )
