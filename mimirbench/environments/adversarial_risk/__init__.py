"""Adversarial risk-control tasks: obey hard limits under misleading pressure."""

from mimirbench.environments.adversarial_risk.generator import (
    apply_pressure,
    generate_params,
    generate_task,
)
from mimirbench.environments.adversarial_risk.grader import count_breaches, grade
from mimirbench.environments.adversarial_risk.schemas import (
    ADVERSARIAL_PRESSURE_TYPES,
    AdversarialRiskAction,
    AdversarialRiskParams,
    PressureType,
)
from mimirbench.environments.adversarial_risk.solver import (
    reference_solver,
    safe_reduced_size,
    solve_params,
)
from mimirbench.evals.registry import EnvironmentSpec
from mimirbench.evals.schemas import EnvironmentFamily

__all__ = [
    "ADVERSARIAL_PRESSURE_TYPES",
    "AdversarialRiskAction",
    "AdversarialRiskParams",
    "PressureType",
    "apply_pressure",
    "build_spec",
    "count_breaches",
    "generate_params",
    "generate_task",
    "grade",
    "reference_solver",
    "safe_reduced_size",
    "solve_params",
]


def build_spec() -> EnvironmentSpec:
    """Construct the registry spec for the adversarial-risk environment."""
    return EnvironmentSpec(
        name="adversarial_risk",
        family=EnvironmentFamily.ADVERSARIAL_RISK,
        description="Risk-control decisions under adversarial pressure and hard constraints.",
        generator=generate_task,
        grader=grade,
        reference_solver=reference_solver,
    )
