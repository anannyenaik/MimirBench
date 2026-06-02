"""Deterministic grader for hidden-regime filtering tasks.

Compares the agent's final-step regime belief to the exact filtered posterior
using total-variation distance, mirroring the Bayesian-games grader.
"""

from __future__ import annotations

import numpy as np

from mimirbench.evals.schemas import GraderResult, GradingKey, ModelResponse, Task

__all__ = ["PASS_TV_THRESHOLD", "grade"]

PASS_TV_THRESHOLD = 0.05


def _extract_distribution(response: ModelResponse, field: str, n: int) -> list[float] | None:
    if response.parsed_answer is None:
        return None
    raw = response.parsed_answer.get(field)
    if not isinstance(raw, (list, tuple)) or len(raw) != n:
        return None
    out: list[float] = []
    for value in raw:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        out.append(float(value))
    return out


def grade(task: Task, response: ModelResponse, key: GradingKey) -> GraderResult:
    """Grade a regime-posterior response against the exact filtered belief."""
    true_post = np.asarray(key.payload["regime_posterior"], dtype=np.float64)
    pred = _extract_distribution(response, "regime_posterior", true_post.size)

    if pred is None:
        return GraderResult(
            task_id=task.task_id,
            family=task.family,
            score=0.0,
            passed=False,
            violations=["no_valid_answer"],
            details={"reason": "missing or malformed 'regime_posterior' field"},
        )

    pred_arr = np.asarray(pred, dtype=np.float64)
    l1 = float(np.abs(pred_arr - true_post).sum())
    tv = 0.5 * l1
    score = float(np.clip(1.0 - tv, 0.0, 1.0))

    return GraderResult(
        task_id=task.task_id,
        family=task.family,
        score=score,
        passed=tv <= PASS_TV_THRESHOLD,
        metrics={
            "posterior_tv_error": tv,
            "posterior_l1_error": l1,
        },
        details={"true_posterior": true_post.tolist(), "predicted_posterior": pred},
    )
