"""Environment registry.

A tiny, explicit registry mapping environment names to the callables the runner
needs: a deterministic ``generator(seed) -> TaskInstance``, a
``grader(task, response, key) -> GraderResult``, and a ``reference_solver`` used
by the deterministic baseline agent.

Built-in environments are registered lazily via :func:`load_builtin_environments`
to avoid import cycles (environments import the shared schemas, not the
registry).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from mimirbench.evals.schemas import (
    EnvironmentFamily,
    GraderResult,
    GradingKey,
    ModelResponse,
    Task,
    TaskInstance,
)

__all__ = [
    "EnvironmentSpec",
    "environment_names",
    "get",
    "list_specs",
    "load_builtin_environments",
    "register",
]

GeneratorFn = Callable[[int], TaskInstance]
GraderFn = Callable[[Task, ModelResponse, GradingKey], GraderResult]
SolverFn = Callable[[Task], dict[str, Any]]


@dataclass(frozen=True)
class EnvironmentSpec:
    """Everything the runner needs to evaluate one environment."""

    name: str
    family: EnvironmentFamily
    description: str
    generator: GeneratorFn
    grader: GraderFn
    reference_solver: SolverFn


_REGISTRY: dict[str, EnvironmentSpec] = {}
_BUILTINS_LOADED = False


def register(spec: EnvironmentSpec, *, overwrite: bool = False) -> None:
    """Register an environment spec by name."""
    if spec.name in _REGISTRY and not overwrite:
        raise ValueError(f"environment {spec.name!r} is already registered.")
    _REGISTRY[spec.name] = spec


def get(name: str) -> EnvironmentSpec:
    """Return the spec for ``name``, loading built-ins on first access."""
    load_builtin_environments()
    if name not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY)) or "(none)"
        raise KeyError(f"unknown environment {name!r}. Available: {available}")
    return _REGISTRY[name]


def list_specs() -> list[EnvironmentSpec]:
    """Return all registered specs (built-ins included), sorted by name."""
    load_builtin_environments()
    return [_REGISTRY[name] for name in sorted(_REGISTRY)]


def environment_names() -> list[str]:
    """Return all registered environment names."""
    load_builtin_environments()
    return sorted(_REGISTRY)


def load_builtin_environments() -> None:
    """Register the environments that ship with MimirBench (idempotent)."""
    global _BUILTINS_LOADED
    if _BUILTINS_LOADED:
        return
    # Local imports break the environments <-> registry import cycle.
    from mimirbench.environments.adversarial_risk import build_spec as _risk_spec
    from mimirbench.environments.auctions import build_spec as _auctions_spec
    from mimirbench.environments.bayesian_games import build_spec as _bayes_spec
    from mimirbench.environments.hidden_regimes import build_spec as _regimes_spec
    from mimirbench.environments.market_making import build_spec as _market_making_spec
    from mimirbench.environments.prediction_markets import build_spec as _prediction_markets_spec

    for build in (
        _bayes_spec,
        _auctions_spec,
        _regimes_spec,
        _market_making_spec,
        _prediction_markets_spec,
        _risk_spec,
    ):
        spec = build()
        _REGISTRY.setdefault(spec.name, spec)
    _BUILTINS_LOADED = True
