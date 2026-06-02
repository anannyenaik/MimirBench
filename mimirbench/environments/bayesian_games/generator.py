"""Synthetic task generator for Bayesian-updating games.

Each task describes a set of *sources*, a prior over which source is active, and
each source's emission distribution over *symbols*. The agent observes a short
symbol sequence and must report the posterior over sources.

Distributions are built from small integer weights so the numbers shown in the
prompt match the structured ``metadata`` exactly, and so the task is fully
reproducible from its seed.
"""

from __future__ import annotations

import numpy as np

from mimirbench.environments.bayesian_games.schemas import BayesianTaskParams
from mimirbench.environments.bayesian_games.solver import solve_params
from mimirbench.evals.schemas import EnvironmentFamily, GradingKey, Task, TaskInstance

__all__ = ["generate_params", "generate_task"]

_HYPOTHESIS_LABELS = ["A", "B", "C", "D", "E"]


def _weighted_distribution(rng: np.random.Generator, k: int) -> list[float]:
    """A clean probability vector from small integer weights (sums to ~1.0)."""
    weights = rng.integers(1, 10, size=k).astype(np.float64)
    return (weights / weights.sum()).tolist()


def generate_params(seed: int) -> BayesianTaskParams:
    """Generate the structured parameters for one Bayesian task."""
    rng = np.random.default_rng(seed)
    n_hyp = int(rng.integers(2, 5))
    n_sig = int(rng.integers(2, 5))

    hypothesis_names = [f"Source {_HYPOTHESIS_LABELS[i]}" for i in range(n_hyp)]
    signal_names = [f"symbol {j + 1}" for j in range(n_sig)]
    priors = _weighted_distribution(rng, n_hyp)
    likelihood = [_weighted_distribution(rng, n_sig) for _ in range(n_hyp)]

    # Draw observations from a randomly chosen "true" source so the evidence is
    # informative rather than uniform.
    true_source = int(rng.integers(0, n_hyp))
    n_obs = int(rng.integers(1, 6))
    probs = np.asarray(likelihood[true_source], dtype=np.float64)
    observations = [int(rng.choice(n_sig, p=probs)) for _ in range(n_obs)]

    return BayesianTaskParams(
        hypothesis_names=hypothesis_names,
        signal_names=signal_names,
        priors=priors,
        likelihood=likelihood,
        observations=observations,
    )


def _format_prompt(params: BayesianTaskParams) -> str:
    lines: list[str] = [
        "A single hidden source generated a sequence of symbols.",
        "Your task is to compute the posterior probability that each source is the hidden one.",
        "",
        "Prior probability that each source is active:",
    ]
    for name, prob in zip(params.hypothesis_names, params.priors, strict=True):
        lines.append(f"  - {name}: {prob:.3f}")

    lines.append("")
    lines.append("Each source emits symbols independently with these probabilities:")
    for name, row in zip(params.hypothesis_names, params.likelihood, strict=True):
        parts = ", ".join(
            f"{sig}={p:.3f}" for sig, p in zip(params.signal_names, row, strict=True)
        )
        lines.append(f"  - {name}: {parts}")

    observed = ", ".join(params.signal_names[s] for s in params.observations)
    lines.append("")
    lines.append(f"Observed symbol sequence (in order): {observed}")
    lines.append("")
    lines.append(
        "Return a JSON object with key 'posterior': a list of probabilities, one per "
        "source in the order listed above, summing to 1."
    )
    return "\n".join(lines)


def generate_task(seed: int) -> TaskInstance:
    """Generate a complete :class:`TaskInstance` (public task + private key)."""
    params = generate_params(seed)
    prompt = _format_prompt(params)
    task = Task(
        task_id=f"bayesian_games-{seed}",
        family=EnvironmentFamily.BAYESIAN_GAMES,
        seed=seed,
        prompt=prompt,
        metadata=params.model_dump(),
    )
    key = GradingKey(
        task_id=task.task_id,
        payload={"posterior": solve_params(params)},
    )
    return TaskInstance(task=task, key=key)
