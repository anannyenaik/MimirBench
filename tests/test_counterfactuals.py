"""Tests for deterministic counterfactual pair generation (no torch needed)."""

from __future__ import annotations

import pytest

from mimirbench.interpretability.counterfactuals import (
    PROBE_LABEL_KEYS,
    generate_counterfactual_pairs,
)
from mimirbench.training.synthetic_traces import BayesianTraceConfig, PayoffRiskConfig


def _config() -> BayesianTraceConfig:
    return BayesianTraceConfig(
        seed=123,
        num_hypotheses=2,
        min_observations=2,
        max_observations=6,
        signal_reliability=0.7,
        payoff=PayoffRiskConfig(1.0, 1.0, 0.0, 0.35),
    )


def test_counterfactual_generation_is_deterministic() -> None:
    a = generate_counterfactual_pairs(8, config=_config(), seed=99)
    b = generate_counterfactual_pairs(8, config=_config(), seed=99)
    assert [p.pair_id for p in a] == [p.pair_id for p in b]
    assert [p.corrupted_input for p in a] == [p.corrupted_input for p in b]
    assert [p.clean_labels for p in a] == [p.clean_labels for p in b]


def test_counterfactual_seed_changes_pairs() -> None:
    a = generate_counterfactual_pairs(8, config=_config(), seed=1)
    b = generate_counterfactual_pairs(8, config=_config(), seed=2)
    assert [p.pair_id for p in a] != [p.pair_id for p in b]


def test_clean_and_corrupted_labels_differ() -> None:
    pairs = generate_counterfactual_pairs(12, config=_config(), seed=7)
    assert len(pairs) == 12
    # Corruption is engineered to flip the posterior bucket (and usually action).
    assert all(pair.labels_differ() for pair in pairs)
    assert all(
        pair.clean_labels["posterior_bucket"] != pair.corrupted_labels["posterior_bucket"]
        for pair in pairs
    )


def test_pair_has_required_fields() -> None:
    pair = generate_counterfactual_pairs(1, config=_config(), seed=3)[0]
    assert pair.pair_id
    assert pair.clean_input and pair.corrupted_input
    assert pair.clean_input != pair.corrupted_input
    assert set(PROBE_LABEL_KEYS) <= set(pair.clean_labels)
    assert pair.changed_fields == ["observations"]
    assert pair.expected_direction["posterior_A"] in {"up", "down", "flat"}
    assert pair.expected_direction["order_control"] == "invariant"
    assert pair.expected_direction["distractor"] == "invariant"
    assert pair.distractor_input.startswith(pair.clean_input)


def test_order_control_preserves_evidence_multiset() -> None:
    pairs = generate_counterfactual_pairs(10, config=_config(), seed=5)
    for pair in pairs:
        clean_obs = sorted(pair.metadata["clean_observations"])
        order_obs = sorted(pair.metadata["order_observations"])
        assert clean_obs == order_obs  # same evidence, possibly reordered


def test_invalid_num_pairs_raises() -> None:
    with pytest.raises(ValueError):
        generate_counterfactual_pairs(0, config=_config(), seed=1)
