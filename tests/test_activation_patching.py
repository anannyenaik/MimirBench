"""Tests for activation patching primitives and the experiment driver."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from mimirbench.interpretability.activation_patching import PatchResult, PatchSpec
from mimirbench.interpretability.counterfactuals import generate_counterfactual_pairs
from mimirbench.training.synthetic_traces import BayesianTraceConfig, PayoffRiskConfig


def test_patch_result_restoration_math() -> None:
    spec = PatchSpec(hook_name="embed", position=-1)
    full = PatchResult(spec, clean_metric=1.0, corrupted_metric=0.0, patched_metric=1.0)
    assert full.restoration == pytest.approx(1.0)
    none = PatchResult(spec, clean_metric=1.0, corrupted_metric=0.0, patched_metric=0.0)
    assert none.restoration == pytest.approx(0.0)
    half = PatchResult(spec, clean_metric=1.0, corrupted_metric=0.0, patched_metric=0.5)
    assert half.restoration == pytest.approx(0.5)
    flat = PatchResult(spec, clean_metric=0.5, corrupted_metric=0.5, patched_metric=0.5)
    assert flat.restoration == 0.0


def _config() -> BayesianTraceConfig:
    return BayesianTraceConfig(
        seed=123, min_observations=2, signal_reliability=0.7, payoff=PayoffRiskConfig(1.0, 1.0, 0.0, 0.35)
    )


def test_activation_patch_resid_post_restores_clean(tiny_interp_checkpoint: dict) -> None:
    pytest.importorskip("torch")
    from mimirbench.interpretability.activation_patching import activation_patch

    model = tiny_interp_checkpoint["model"]
    tokenizer = tiny_interp_checkpoint["tokenizer"]
    pair = generate_counterfactual_pairs(1, config=_config(), seed=5)[0]
    clean = tokenizer.encode(pair.clean_input)["input_ids"]
    corrupted = tokenizer.encode(pair.corrupted_input)["input_ids"]

    def action_logit_gap(output: Mapping[str, Any]) -> float:
        logits = output["logits"]["action"].detach().numpy().reshape(-1)
        return float(logits[0] - logits[1])

    result = activation_patch(
        model, clean, corrupted, PatchSpec("blocks.0.resid_post", position=-1), action_logit_gap
    )
    # Patching the full final residual stream reproduces the clean metric exactly.
    assert result.patched_metric == pytest.approx(result.clean_metric, abs=1e-4)


def test_run_activation_patching_aggregates(tiny_interp_checkpoint: dict) -> None:
    pytest.importorskip("torch")
    from mimirbench.interpretability.activation_patching import run_activation_patching
    from mimirbench.training.small_transformer import interpretability_site_names

    model = tiny_interp_checkpoint["model"]
    tokenizer = tiny_interp_checkpoint["tokenizer"]
    pairs = generate_counterfactual_pairs(8, config=_config(), seed=9)
    result = run_activation_patching(model, tokenizer, pairs)
    assert result.sites == list(interpretability_site_names(model.config.n_layers))
    assert "action" in result.heads
    # one row per (pair, site, head)
    assert len(result.rows) == len(pairs) * len(result.sites) * len(result.heads)
    for row in result.rows:
        assert set(row) >= {
            "clean_target_prob",
            "corrupted_target_prob",
            "patched_target_prob",
            "causal_effect",
        }
        assert row["causal_effect"] == pytest.approx(
            row["patched_target_prob"] - row["corrupted_target_prob"]
        )
    by_site = result.summary["by_site"]
    for site in result.sites:
        assert "label_recovery_rate" in by_site[site]
        assert "action_recovery_rate" in by_site[site]
        assert "posterior_bucket_recovery_rate" in by_site[site]
    # determinism
    again = run_activation_patching(model, tokenizer, pairs)
    assert again.summary == result.summary
