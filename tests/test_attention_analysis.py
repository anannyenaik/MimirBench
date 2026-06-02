"""Tests for attention analysis utilities and the model driver."""

from __future__ import annotations

import numpy as np
import pytest

from mimirbench.interpretability.attention_analysis import (
    attention_entropy,
    attention_group_mass,
    run_attention_analysis,
    token_group_spans,
)
from mimirbench.training.synthetic_traces import BayesianTraceConfig, generate_trace_splits


def test_attention_entropy_uniform_is_max() -> None:
    seq = 4
    uniform = np.full((seq, seq), 1.0 / seq)
    entropy = attention_entropy(uniform)
    assert np.allclose(entropy, np.log(seq))


def test_attention_entropy_peaked_is_zero() -> None:
    peaked = np.eye(3)
    entropy = attention_entropy(peaked)
    assert np.allclose(entropy, 0.0)


def test_attention_group_mass_selects_columns() -> None:
    # Each query puts all mass on key 0.
    attention = np.zeros((3, 3))
    attention[:, 0] = 1.0
    assert attention_group_mass(attention, [0]) == pytest.approx(1.0)
    assert attention_group_mass(attention, [1, 2]) == pytest.approx(0.0)


def test_token_group_spans_partition_sections() -> None:
    tokens = ["prior", "A", "=", "0.5", "likelihood", "X", "0.7", "observations", "X", "X", "payoff", "risk_tolerance", "0.3"]
    spans = token_group_spans(tokens, offset=1)
    # prior starts at index 0 -> +1 offset
    assert spans["prior"][0] == 1
    assert all(spans["evidence"])  # non-empty evidence span
    # spans are disjoint and ordered
    flat = [pos for group in ("prior", "likelihood", "evidence", "payoff_risk") for pos in spans[group]]
    assert flat == sorted(flat)
    assert len(flat) == len(set(flat))


def test_run_attention_analysis_on_tiny_model(tiny_interp_checkpoint: dict) -> None:
    model = tiny_interp_checkpoint["model"]
    tokenizer = tiny_interp_checkpoint["tokenizer"]
    traces = generate_trace_splits(
        num_train=8, num_val=0, num_test=0, config=BayesianTraceConfig(seed=11)
    )["train"]
    result = run_attention_analysis(model, tokenizer, traces, max_examples=8)
    by_layer = result.summary["by_layer"]
    assert set(by_layer) == {"0"}  # single layer
    layer0 = by_layer["0"]
    assert layer0["mean_entropy"] >= 0.0
    assert set(layer0["mean_group_mass"]) == {"prior", "likelihood", "evidence", "payoff_risk"}
    assert len(result.examples) == 8
    # determinism
    again = run_attention_analysis(model, tokenizer, traces, max_examples=8)
    assert again.summary == result.summary
