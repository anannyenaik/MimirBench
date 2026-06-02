"""High-level orchestration of interpretability experiments.

Ties together probes, activation patching, and attention analysis into named
experiments. The plan is encoded as data (real and inspectable) so it can be
listed and reviewed now; the executors land alongside the trained models.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["EVIDENCE_ACCUMULATION_PLAN", "ExperimentStep", "describe_plan"]


@dataclass(frozen=True)
class ExperimentStep:
    """One step of an interpretability experiment."""

    name: str
    technique: str
    hypothesis: str


# The plan for the flagship "where is the belief?" experiment.
EVIDENCE_ACCUMULATION_PLAN: tuple[ExperimentStep, ...] = (
    ExperimentStep(
        name="belief_probe",
        technique="linear_probe",
        hypothesis="The Bayes-filtered P(regime) is linearly decodable from the residual stream.",
    ),
    ExperimentStep(
        name="evidence_patch",
        technique="activation_patching",
        hypothesis="Patching a single evidence position flips the model's prediction predictably.",
    ),
    ExperimentStep(
        name="update_heads",
        technique="attention_analysis",
        hypothesis="Specific heads route prior-token evidence into the current belief.",
    ),
)


def describe_plan(steps: tuple[ExperimentStep, ...] = EVIDENCE_ACCUMULATION_PLAN) -> list[str]:
    """Render an experiment plan as human-readable lines."""
    return [f"[{step.technique}] {step.name}: {step.hypothesis}" for step in steps]
