"""Synthetic task generator for hidden-regime filtering games."""

from __future__ import annotations

import numpy as np

from mimirbench.environments.hidden_regimes.schemas import HiddenRegimeParams
from mimirbench.environments.hidden_regimes.simulator import simulate_path
from mimirbench.environments.hidden_regimes.solver import final_belief
from mimirbench.evals.schemas import EnvironmentFamily, GradingKey, Task, TaskInstance

__all__ = ["generate_params", "generate_task"]

_REGIME_LABELS = ["calm", "stressed", "trending"]


def _weighted_distribution(rng: np.random.Generator, k: int) -> list[float]:
    weights = rng.integers(1, 10, size=k).astype(np.float64)
    return (weights / weights.sum()).tolist()


def _sticky_transition(rng: np.random.Generator, k: int) -> list[list[float]]:
    """Transition rows with extra mass on the diagonal (regimes persist)."""
    rows: list[list[float]] = []
    for i in range(k):
        weights = rng.integers(1, 5, size=k).astype(np.float64)
        weights[i] += 8.0
        rows.append((weights / weights.sum()).tolist())
    return rows


def generate_params(seed: int) -> HiddenRegimeParams:
    """Generate structured parameters for one hidden-regime task."""
    rng = np.random.default_rng(seed)
    n_regimes = int(rng.integers(2, 4))
    n_signals = int(rng.integers(2, 5))

    regime_names = [_REGIME_LABELS[i] for i in range(n_regimes)]
    signal_names = [f"signal {j + 1}" for j in range(n_signals)]
    initial = _weighted_distribution(rng, n_regimes)
    transition = _sticky_transition(rng, n_regimes)
    emission = [_weighted_distribution(rng, n_signals) for _ in range(n_regimes)]

    n_steps = int(rng.integers(3, 7))
    _, observations = simulate_path(initial, transition, emission, n_steps, seed=seed)

    return HiddenRegimeParams(
        regime_names=regime_names,
        signal_names=signal_names,
        initial=initial,
        transition=transition,
        emission=emission,
        observations=observations,
    )


def _format_prompt(params: HiddenRegimeParams) -> str:
    lines: list[str] = [
        "A system switches between hidden regimes following a Markov chain and emits a",
        "signal at each step. Estimate which regime is active at the final step.",
        "",
        "Initial regime probabilities:",
    ]
    for name, p in zip(params.regime_names, params.initial, strict=True):
        lines.append(f"  - {name}: {p:.3f}")

    lines.append("")
    lines.append("Transition probabilities P(next regime | current regime):")
    for name, row in zip(params.regime_names, params.transition, strict=True):
        parts = ", ".join(
            f"{to}={p:.3f}" for to, p in zip(params.regime_names, row, strict=True)
        )
        lines.append(f"  - from {name}: {parts}")

    lines.append("")
    lines.append("Emission probabilities P(signal | regime):")
    for name, row in zip(params.regime_names, params.emission, strict=True):
        parts = ", ".join(
            f"{sig}={p:.3f}" for sig, p in zip(params.signal_names, row, strict=True)
        )
        lines.append(f"  - {name}: {parts}")

    observed = ", ".join(params.signal_names[s] for s in params.observations)
    lines.append("")
    lines.append(f"Observed signals (in order): {observed}")
    lines.append("")
    lines.append(
        "Return a JSON object with key 'regime_posterior': the probability of each "
        "regime at the final step, in the order listed above, summing to 1."
    )
    return "\n".join(lines)


def generate_task(seed: int) -> TaskInstance:
    """Generate a complete hidden-regime :class:`TaskInstance`."""
    params = generate_params(seed)
    task = Task(
        task_id=f"hidden_regimes-{seed}",
        family=EnvironmentFamily.HIDDEN_REGIMES,
        seed=seed,
        prompt=_format_prompt(params),
        metadata=params.model_dump(),
    )
    key = GradingKey(
        task_id=task.task_id,
        payload={"regime_posterior": final_belief(params)},
    )
    return TaskInstance(task=task, key=key)
