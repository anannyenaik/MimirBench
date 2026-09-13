"""Deterministic grader for Bayesian-updating tasks.

Compares the agent's reported posterior to the exact posterior in the grading
key using total-variation distance. The grader is pure and side-effect free, so
the same response always yields the same result.
"""

from __future__ import annotations

import numpy as np

from mimirbench.evals.schemas import GraderResult, GradingKey, ModelResponse, Task

__all__ = ["PASS_TV_THRESHOLD", "grade"]

# A response passes if its total-variation distance from the true posterior is
# within this bound. The exact reference solver scores 0 and always passes.
PASS_TV_THRESHOLD = 0.05


def _extract_posterior(response: ModelResponse, n: int) -> list[float] | None:
    if response.parsed_answer is None:
        return None
    raw = response.parsed_answer.get("posterior")
    if not isinstance(raw, (list, tuple)) or len(raw) != n:
        return None
    out: list[float] = []
    for value in raw:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        out.append(float(value))
    return out


def grade(task: Task, response: ModelResponse, key: GradingKey) -> GraderResult:
    """Grade a Bayesian-updating response against the exact posterior."""
    true_post = np.asarray(key.payload["posterior"], dtype=np.float64)
    pred = _extract_posterior(response, true_post.size)

    if pred is None:
        return GraderResult(
            task_id=task.task_id,
            family=task.family,
            score=0.0,
            passed=False,
            violations=["no_valid_answer"],
            details={"reason": "missing or malformed 'posterior' field"},
        )

    pred_arr = np.asarray(pred, dtype=np.float64)
    l1 = float(np.abs(pred_arr - true_post).sum())
    tv = 0.5 * l1
    max_err = float(np.abs(pred_arr - true_post).max())
    score = float(np.clip(1.0 - tv, 0.0, 1.0))

    return GraderResult(
        task_id=task.task_id,
        family=task.family,
        score=score,
        passed=tv <= PASS_TV_THRESHOLD,
        metrics={
            "posterior_tv_error": tv,
            "posterior_l1_error": l1,
            "posterior_max_error": max_err,
            "answer_sum": float(pred_arr.sum()),
        },
        details={
            "true_posterior": true_post.tolist(),
            "predicted_posterior": pred,
        },
    )
