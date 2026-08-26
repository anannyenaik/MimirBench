"""Deterministic clean/corrupted Bayesian trace pairs for causal experiments.

Activation patching needs *minimal pairs*: two inputs that share everything
except the one thing whose causal role we want to test. Here that thing is the
evidence. For each base trace we build:

* **clean**: the original trace (evidence supports one posterior/action);
* **corrupted**: same prior, likelihood, and payoff, but the observations are
  replaced with evidence for a *different* hypothesis, so the Bayes-optimal
  posterior bucket (and often the action) changes;
* **order-control**: the clean evidence in a different order. Bayesian updating
  is order-invariant, so the labels are unchanged; a model that respects the
  maths should be invariant too;
* **distractor**: the clean trace plus label-irrelevant filler tokens.

Everything is generated from the synthetic-trace machinery, so labels are computed
by the same :func:`compute_trace_targets` used during training. This module is
torch-free.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np

from mimirbench.training.synthetic_traces import (
    BayesianTraceConfig,
    PayoffRiskConfig,
    compute_trace_targets,
    format_trace_input,
    generate_trace,
)

__all__ = [
    "PROBE_LABEL_KEYS",
    "CounterfactualPair",
    "generate_counterfactual_pairs",
]

# Label keys surfaced on each pair (the supervised heads we causally test).
PROBE_LABEL_KEYS: tuple[str, ...] = (
    "posterior_bucket",
    "action",
    "risk_flag",
    "confidence_bucket",
)

_DISTRACTOR_CLAUSE = "; note context memo review archived pending unchanged"


@dataclass(frozen=True)
class CounterfactualPair:
    """A clean/corrupted minimal pair plus order and distractor controls."""

    pair_id: str
    clean_input: str
    corrupted_input: str
    clean_labels: dict[str, str]
    corrupted_labels: dict[str, str]
    changed_fields: list[str]
    expected_direction: dict[str, str]
    order_control_input: str
    distractor_input: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def labels_differ(self) -> bool:
        """True if any surfaced label differs between clean and corrupted."""
        return any(
            self.clean_labels.get(key) != self.corrupted_labels.get(key)
            for key in PROBE_LABEL_KEYS
        )


def generate_counterfactual_pairs(
    num_pairs: int,
    *,
    config: BayesianTraceConfig | None = None,
    seed: int = 0,
    split: str = "interp",
    start_index: int = 0,
) -> list[CounterfactualPair]:
    """Generate ``num_pairs`` deterministic counterfactual pairs.

    The same ``(num_pairs, config, seed, split, start_index)`` always yields the
    same pairs. Base traces with too few observations to corrupt (0 or 1
    observation) are skipped so that corruption is always meaningful.
    """
    if num_pairs <= 0:
        raise ValueError("num_pairs must be positive.")
    cfg = config or BayesianTraceConfig()
    cfg.validate()

    pairs: list[CounterfactualPair] = []
    index = start_index
    guard = start_index + 50 * num_pairs + 100
    while len(pairs) < num_pairs and index < guard:
        pair = _build_pair(index, cfg, seed=seed, split=split)
        index += 1
        if pair is None:
            continue
        pairs.append(pair)
    if len(pairs) < num_pairs:
        raise RuntimeError(
            f"could only build {len(pairs)} / {num_pairs} counterfactual pairs; "
            "increase max_observations or reduce num_pairs."
        )
    return pairs


def _build_pair(
    index: int,
    cfg: BayesianTraceConfig,
    *,
    seed: int,
    split: str,
) -> CounterfactualPair | None:
    trace = generate_trace(index, cfg, split=split)
    meta = trace["metadata"]
    observations: list[int] = list(meta["observations"])
    if len(observations) < 2:
        return None

    priors: list[float] = list(meta["prior"])
    likelihood: list[list[float]] = [list(row) for row in meta["likelihood"]]
    hypothesis_labels: list[str] = list(meta["hypothesis_labels"])
    signal_labels: list[str] = list(meta["signal_labels"])
    payoff = PayoffRiskConfig(**meta["payoff"])
    posterior_values: list[float] = list(meta["posterior"])

    leading = int(np.argmax(posterior_values))
    target_hypothesis = int(np.argmin(posterior_values))
    if target_hypothesis == leading:
        target_hypothesis = (leading + 1) % cfg.num_hypotheses

    # Corrupted evidence: every observation points at ``target_hypothesis``.
    # For the diagonal likelihood table, observing signal ``h`` favours
    # hypothesis ``h``, so we repeat that signal index.
    corrupted_observations = [target_hypothesis] * len(observations)

    clean_targets = trace["targets"]
    corrupted_targets, corrupted_posterior, _ = compute_trace_targets(
        priors=priors,
        likelihood=likelihood,
        observations=corrupted_observations,
        payoff=payoff,
        posterior_buckets=cfg.posterior_buckets,
    )

    clean_input = trace["input"]
    corrupted_input = format_trace_input(
        priors=priors,
        hypothesis_labels=hypothesis_labels,
        likelihood=likelihood,
        signal_labels=signal_labels,
        observations=corrupted_observations,
        payoff=payoff,
    )
    order_observations = _reorder(observations, seed=seed, index=index)
    order_control_input = format_trace_input(
        priors=priors,
        hypothesis_labels=hypothesis_labels,
        likelihood=likelihood,
        signal_labels=signal_labels,
        observations=order_observations,
        payoff=payoff,
    )
    distractor_input = clean_input + _DISTRACTOR_CLAUSE

    clean_labels = _surface_labels(clean_targets)
    corrupted_labels = _surface_labels(corrupted_targets)
    expected_direction = {
        "posterior_A": _direction(posterior_values[0], corrupted_posterior[0]),
        "action": f"{clean_labels['action']}->{corrupted_labels['action']}",
        "order_control": "invariant",
        "distractor": "invariant",
    }
    pair_id = _pair_id(cfg, seed, split, index)
    return CounterfactualPair(
        pair_id=pair_id,
        clean_input=clean_input,
        corrupted_input=corrupted_input,
        clean_labels=clean_labels,
        corrupted_labels=corrupted_labels,
        changed_fields=["observations"],
        expected_direction=expected_direction,
        order_control_input=order_control_input,
        distractor_input=distractor_input,
        metadata={
            "base_trace_id": trace["id"],
            "prior": priors,
            "leading_hypothesis": hypothesis_labels[leading],
            "target_hypothesis": hypothesis_labels[target_hypothesis],
            "clean_observations": observations,
            "corrupted_observations": corrupted_observations,
            "order_observations": order_observations,
            "clean_posterior": posterior_values,
            "corrupted_posterior": corrupted_posterior,
        },
    )


def _surface_labels(targets: dict[str, Any]) -> dict[str, str]:
    return {
        "posterior_bucket": str(targets["posterior_A_bucket"]),
        "action": str(targets["action"]),
        "risk_flag": str(targets["risk_flag"]),
        "confidence_bucket": str(targets["confidence_bucket"]),
    }


def _direction(clean_value: float, corrupted_value: float, *, tol: float = 1e-9) -> str:
    if corrupted_value < clean_value - tol:
        return "down"
    if corrupted_value > clean_value + tol:
        return "up"
    return "flat"


def _reorder(observations: Sequence[int], *, seed: int, index: int) -> list[int]:
    rng = np.random.default_rng(_stable_seed(f"order:{seed}:{index}"))
    order = list(observations)
    if len(set(order)) <= 1:
        return order
    for _ in range(8):
        permuted = list(rng.permutation(len(order)))
        candidate = [order[i] for i in permuted]
        if candidate != order:
            return candidate
    return list(reversed(order))


def _pair_id(config: BayesianTraceConfig, seed: int, split: str, index: int) -> str:
    digest = hashlib.sha1(
        f"{asdict(config)}:{seed}:{split}:{index}".encode()
    ).hexdigest()[:12]
    return f"cf-pair-{split}-{index:06d}-{digest}"


def _stable_seed(text: str) -> int:
    digest = hashlib.sha256(text.encode()).digest()
    return int.from_bytes(digest[:8], "big") % (2**32)
