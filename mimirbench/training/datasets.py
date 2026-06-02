"""Synthetic datasets for the small-transformer experiments.

A canonical, sticky 2-regime / 3-signal hidden Markov model produces observation
sequences. A model trained to predict the next symbol must implicitly track a
*belief* over the hidden regime — exactly the capability the interpretability
experiments probe for. :func:`bayes_optimal_nll` gives the irreducible (Bayes
optimal) next-token loss, the natural yardstick for a trained model.

Stage 7 adds deterministic Bayesian strategic traces. Those traces are
supervised records for posterior/action/risk heads and intentionally contain no
hidden chain-of-thought.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt

from mimirbench.environments.hidden_regimes.simulator import simulate_path
from mimirbench.training.synthetic_traces import (
    BayesianTraceConfig,
    PayoffRiskConfig,
    generate_trace_splits,
    load_traces_jsonl,
    write_traces_jsonl,
)

__all__ = [
    "BayesianTraceDatasetConfig",
    "RegimeDatasetConfig",
    "bayes_optimal_nll",
    "export_trace_dataset",
    "load_trace_dataset",
    "make_bayesian_trace_dataset",
    "make_regime_dataset",
]


@dataclass(frozen=True)
class RegimeDatasetConfig:
    """Configuration for the canonical regime-switching dataset."""

    n_sequences: int = 2048
    seq_len: int = 32
    seed: int = 0
    initial: tuple[float, ...] = (0.5, 0.5)
    transition: tuple[tuple[float, ...], ...] = ((0.9, 0.1), (0.1, 0.9))
    emission: tuple[tuple[float, ...], ...] = ((0.7, 0.2, 0.1), (0.1, 0.2, 0.7))

    @property
    def n_signals(self) -> int:
        return len(self.emission[0])


@dataclass(frozen=True)
class BayesianTraceDatasetConfig:
    """Train/validation/test sizing plus Bayesian trace generation settings."""

    num_train: int = 512
    num_val: int = 128
    num_test: int = 128
    seed: int = 0
    num_hypotheses: int = 2
    min_observations: int = 1
    max_observations: int = 6
    signal_reliability: float = 0.7
    posterior_buckets: int = 20
    payoff: PayoffRiskConfig = field(default_factory=PayoffRiskConfig)

    def trace_config(self) -> BayesianTraceConfig:
        """Return the generation-only configuration."""
        return BayesianTraceConfig(
            seed=self.seed,
            num_hypotheses=self.num_hypotheses,
            min_observations=self.min_observations,
            max_observations=self.max_observations,
            signal_reliability=self.signal_reliability,
            posterior_buckets=self.posterior_buckets,
            payoff=self.payoff,
        )


def make_regime_dataset(
    config: RegimeDatasetConfig | None = None,
) -> tuple[npt.NDArray[np.int64], npt.NDArray[np.int64]]:
    """Return ``(inputs, targets)`` int arrays of shape ``(n_sequences, seq_len - 1)``.

    ``targets[i, t]`` is the symbol following ``inputs[i, t]`` (next-token task).
    """
    config = config or RegimeDatasetConfig()
    if config.seq_len < 2:
        raise ValueError("seq_len must be >= 2 for a next-token task.")
    sequences = []
    for s in range(config.n_sequences):
        _, observations = simulate_path(
            config.initial, config.transition, config.emission, config.seq_len, seed=config.seed + s
        )
        sequences.append(observations)
    arr = np.asarray(sequences, dtype=np.int64)
    return arr[:, :-1], arr[:, 1:]


def make_bayesian_trace_dataset(
    config: BayesianTraceDatasetConfig | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Return deterministic Bayesian trace splits."""
    cfg = config or BayesianTraceDatasetConfig()
    return generate_trace_splits(
        num_train=cfg.num_train,
        num_val=cfg.num_val,
        num_test=cfg.num_test,
        config=cfg.trace_config(),
    )


def export_trace_dataset(
    splits: dict[str, list[dict[str, Any]]],
    output_dir: str | Path,
) -> dict[str, Path]:
    """Write train/validation/test trace splits as JSONL files."""
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for split, traces in sorted(splits.items()):
        path = root / f"{split}_traces.jsonl"
        write_traces_jsonl(traces, path)
        paths[split] = path
    return paths


def load_trace_dataset(root: str | Path) -> dict[str, list[dict[str, Any]]]:
    """Load any ``*_traces.jsonl`` files from a dataset directory."""
    directory = Path(root)
    splits: dict[str, list[dict[str, Any]]] = {}
    for path in sorted(directory.glob("*_traces.jsonl")):
        split = path.name.removesuffix("_traces.jsonl")
        splits[split] = load_traces_jsonl(path)
    return splits


def bayes_optimal_nll(
    config: RegimeDatasetConfig | None = None,
) -> float:
    """Average Bayes-optimal next-token negative log-likelihood for the source.

    For each position the optimal predictor uses the HMM forward belief:
    ``P(o_{t+1} | o_1..t) = emission^T @ (transition^T @ filtered_t)``.
    """
    config = config or RegimeDatasetConfig()
    inputs, targets = make_regime_dataset(config)
    initial = np.asarray(config.initial, dtype=np.float64)
    transition = np.asarray(config.transition, dtype=np.float64)
    emission = np.asarray(config.emission, dtype=np.float64)

    total_nll = 0.0
    count = 0
    for seq_in, seq_tgt in zip(inputs, targets, strict=True):
        belief = initial.copy()  # P(regime_1)
        # Condition on the first input symbol before predicting the first target.
        belief = belief * emission[:, seq_in[0]]
        belief = belief / belief.sum()
        for t in range(seq_in.shape[0]):
            predicted_regime = transition.T @ belief
            next_obs_dist = emission.T @ predicted_regime
            total_nll += -float(np.log(next_obs_dist[seq_tgt[t]]))
            count += 1
            # Advance the filter with the observed target symbol.
            belief = predicted_regime * emission[:, seq_tgt[t]]
            belief = belief / belief.sum()
    return total_nll / count
