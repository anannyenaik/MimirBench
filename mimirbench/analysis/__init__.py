"""Analysis: turn raw grader results into calibration, regret, and robustness views."""

from mimirbench.analysis.calibration import (
    brier_score,
    expected_calibration_error,
    reliability_curve,
)
from mimirbench.analysis.failure_cases import extract_failure_cases
from mimirbench.analysis.regret import (
    average_regret,
    cumulative_regret,
    per_step_regret,
    total_regret,
)
from mimirbench.analysis.robustness import (
    answer_agreement_rate,
    compute_robustness_metrics,
    robustness_drop,
    score_dispersion,
)

__all__ = [
    "answer_agreement_rate",
    "average_regret",
    "brier_score",
    "compute_robustness_metrics",
    "cumulative_regret",
    "expected_calibration_error",
    "extract_failure_cases",
    "per_step_regret",
    "reliability_curve",
    "robustness_drop",
    "score_dispersion",
    "total_regret",
]
