"""Approximate full-benchmark CI-width planning from saved pilot artefacts only."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from mimirbench.analysis.statistical_validity import CANONICAL_ROWS, CanonicalRow, load_task_scores

__all__ = [
    "PowerPlanningEstimate",
    "build_power_planning_markdown",
    "estimate_ci_widths",
    "write_power_planning_report",
]

_SCENARIOS: tuple[tuple[str, int, int], ...] = (
    ("Pilot: 20/env x 1 seed", 20, 1),
    ("Full track A: 100/env x 3 seeds", 100, 3),
    ("Full track B: 200/env x 5 seeds", 200, 5),
)
_ENVIRONMENT_COUNT = 6


@dataclass(frozen=True)
class PowerPlanningEstimate:
    """One normal-approximation CI-width estimate derived from pilot variance."""

    scenario: str
    tasks_per_environment: int
    seeds: int
    planned_n: int
    approximate_ci_width: float


def estimate_ci_widths(
    scores: Sequence[float],
    *,
    scenarios: Sequence[tuple[str, int, int]] = _SCENARIOS,
    environment_count: int = _ENVIRONMENT_COUNT,
) -> list[PowerPlanningEstimate]:
    """Estimate total 95% CI widths using pilot score variance and iid scaling."""
    if len(scores) < 2:
        raise ValueError("at least two pilot scores are required for power planning.")
    sample_sd = float(np.std(np.asarray(scores, dtype=np.float64), ddof=1))
    estimates: list[PowerPlanningEstimate] = []
    for name, tasks_per_environment, seeds in scenarios:
        planned_n = environment_count * tasks_per_environment * seeds
        width = 2.0 * 1.96 * sample_sd / np.sqrt(planned_n)
        estimates.append(
            PowerPlanningEstimate(
                scenario=name,
                tasks_per_environment=tasks_per_environment,
                seeds=seeds,
                planned_n=planned_n,
                approximate_ci_width=float(width),
            )
        )
    return estimates


def build_power_planning_markdown(
    base_dir: str | Path = Path("reports") / "runs" / "leaderboard",
    *,
    rows: Sequence[CanonicalRow] = CANONICAL_ROWS,
) -> str:
    """Render planning estimates from existing saved pilot result rows."""
    base = Path(base_dir)
    lines = [
        "# Full benchmark power plan",
        "",
        "**These are planning estimates based on pilot variance, not results from unrun "
        "hosted-model evaluations.**",
        "",
        "The table uses each saved pilot row's task-level score variance and the normal "
        "approximation `total 95% CI width ~= 2 x 1.96 x pilot_sd / sqrt(n)`. It assumes "
        "iid task-level scaling. The current single-seed pilot cannot estimate seed-to-seed "
        "variation, so the full-run intervals may be wider than these planning values.",
        "",
        "| Model | Pilot n | Pilot mean | Pilot SD | 20/env x 1 seed | "
        "100/env x 3 seeds | 200/env x 5 seeds |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    missing: list[str] = []
    for row in rows:
        if "clean" not in row.track:
            continue
        path = (
            base
            / row.run_dir
            / "models"
            / row.model_dir
            / "agents"
            / row.agent
            / "results.jsonl"
        )
        if not path.exists():
            missing.append(row.display)
            continue
        task_scores = load_task_scores(path)
        values = [score.score for score in task_scores]
        estimates = estimate_ci_widths(values)
        lines.append(
            f"| {row.display} | {len(values)} | {np.mean(values):.4f} | "
            f"{np.std(values, ddof=1):.4f} | "
            + " | ".join(f"{estimate.approximate_ci_width:.4f}" for estimate in estimates)
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Widths are approximate total interval widths, not half-widths and not achieved results.",
            "- Full tracks must report seed-level means and seed-to-seed variation directly; this "
            "pilot-derived calculation cannot substitute for those observations.",
            "- Synthetic tasks, track-specific decoding, and row-classification caveats still apply.",
            "- No provider-superiority or statistical-significance claim follows from this plan.",
        ]
    )
    if missing:
        lines.extend(["", "## Missing saved pilot rows", ""])
        lines.extend(f"- {name}" for name in missing)
    lines.append("")
    return "\n".join(lines)


def write_power_planning_report(
    base_dir: str | Path = Path("reports") / "runs" / "leaderboard",
    *,
    output_path: str | Path = Path("reports") / "runs" / "leaderboard" / "full_benchmark_power_plan.md",
    rows: Sequence[CanonicalRow] = CANONICAL_ROWS,
) -> Path:
    """Write the saved-artifact-only power-planning report."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_power_planning_markdown(base_dir, rows=rows), encoding="utf-8")
    return path
