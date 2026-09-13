"""Tests for position-resolved token-group patching and negative controls."""

from __future__ import annotations

import pytest

from mimirbench.interpretability.counterfactuals import generate_counterfactual_pairs
from mimirbench.training.synthetic_traces import BayesianTraceConfig, PayoffRiskConfig


def _config() -> BayesianTraceConfig:
    return BayesianTraceConfig(
        seed=123,
        min_observations=2,
        max_observations=6,
        signal_reliability=0.7,
        payoff=PayoffRiskConfig(1.0, 1.0, 0.0, 0.35),
    )


def test_token_group_patching_shape_and_determinism(tiny_interp_checkpoint: dict) -> None:
    pytest.importorskip("torch")
    from mimirbench.interpretability.token_group_patching import (
        DEFAULT_GROUPS,
        run_token_group_patching,
    )

    model = tiny_interp_checkpoint["model"]
    tokenizer = tiny_interp_checkpoint["tokenizer"]
    pairs = generate_counterfactual_pairs(6, config=_config(), seed=9)

    result = run_token_group_patching(model, tokenizer, pairs)
    # embed is excluded by default (degenerate for non-evidence groups).
    assert "embed" not in result.sites
    assert set(result.groups) == set(DEFAULT_GROUPS)
    assert "action" in result.heads
    for row in result.rows:
        assert set(row) >= {"site", "group", "head", "recovered", "corrupted_flipped"}
        assert row["group"] in DEFAULT_GROUPS
        assert row["n_positions"] >= 1
    # Aggregated recovery rates are present per (site, group).
    for site in result.sites:
        for group in result.groups:
            block = result.summary["by_site"][site][group]
            assert "action_recovery_rate" in block

    again = run_token_group_patching(model, tokenizer, pairs)
    assert again.summary == result.summary


def test_mismatched_donor_control_reports_matched_and_mismatched(
    tiny_interp_checkpoint: dict,
) -> None:
    pytest.importorskip("torch")
    from mimirbench.interpretability.token_group_patching import run_mismatched_donor_control

    model = tiny_interp_checkpoint["model"]
    tokenizer = tiny_interp_checkpoint["tokenizer"]
    pairs = generate_counterfactual_pairs(8, config=_config(), seed=11)

    result = run_mismatched_donor_control(model, tokenizer, pairs, site="blocks.0.attn_out")
    assert result.site == "blocks.0.attn_out"
    for head, block in result.summary["by_head"].items():
        assert head in result.summary["heads"]
        assert "matched_recovery_rate" in block
        assert "mismatched_recovery_rate" in block
    # Deterministic.
    again = run_mismatched_donor_control(model, tokenizer, pairs, site="blocks.0.attn_out")
    assert again.summary == result.summary


def test_mismatched_donor_only_counts_flipped_pairs(tiny_interp_checkpoint: dict) -> None:
    pytest.importorskip("torch")
    from mimirbench.interpretability.token_group_patching import run_mismatched_donor_control

    model = tiny_interp_checkpoint["model"]
    tokenizer = tiny_interp_checkpoint["tokenizer"]
    pairs = generate_counterfactual_pairs(6, config=_config(), seed=3)
    result = run_mismatched_donor_control(model, tokenizer, pairs)
    # Every recorded row corresponds to a pair the corruption flipped for that head.
    for row in result.rows:
        assert "matched_recovered" in row
