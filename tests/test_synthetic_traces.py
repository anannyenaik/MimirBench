"""Tests for deterministic Bayesian synthetic traces."""

from __future__ import annotations

import numpy as np

from mimirbench.tools.bayes_calculator import posterior
from mimirbench.training.datasets import BayesianTraceDatasetConfig, make_bayesian_trace_dataset
from mimirbench.training.synthetic_traces import (
    BayesianTraceConfig,
    generate_trace,
    load_traces_jsonl,
    write_traces_jsonl,
)


def test_synthetic_traces_are_deterministic_by_seed() -> None:
    config = BayesianTraceConfig(seed=7, max_observations=4, signal_reliability=0.75)
    assert generate_trace(3, config, split="train") == generate_trace(3, config, split="train")
    assert generate_trace(3, config, split="train") != generate_trace(3, config, split="val")


def test_trace_posterior_matches_exact_bayesian_solver() -> None:
    trace = generate_trace(0, BayesianTraceConfig(seed=11))
    metadata = trace["metadata"]
    expected = posterior(metadata["prior"], metadata["likelihood"], metadata["observations"])
    assert np.allclose(metadata["posterior"], expected)


def test_trace_contains_no_hidden_chain_of_thought() -> None:
    trace = generate_trace(0, BayesianTraceConfig(seed=12))
    dumped = str(trace).lower()
    assert "chain_of_thought" not in dumped
    assert "scratchpad" not in dumped
    assert "reasoning_steps" not in dumped
    assert "rationale_class" in trace["targets"]


def test_trace_splits_do_not_overlap_by_id() -> None:
    splits = make_bayesian_trace_dataset(
        BayesianTraceDatasetConfig(num_train=8, num_val=4, num_test=4, seed=3)
    )
    ids_by_split = {split: {trace["id"] for trace in traces} for split, traces in splits.items()}
    assert ids_by_split["train"].isdisjoint(ids_by_split["val"])
    assert ids_by_split["train"].isdisjoint(ids_by_split["test"])
    assert ids_by_split["val"].isdisjoint(ids_by_split["test"])


def test_trace_jsonl_roundtrip(tmp_path) -> None:  # type: ignore[no-untyped-def]
    traces = [generate_trace(i, BayesianTraceConfig(seed=5)) for i in range(3)]
    path = write_traces_jsonl(traces, tmp_path / "traces.jsonl")
    assert load_traces_jsonl(path) == traces
