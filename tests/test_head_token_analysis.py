"""Tests for per-head and individual-token interpretability."""

from __future__ import annotations

import pytest

from mimirbench.interpretability.counterfactuals import generate_counterfactual_pairs
from mimirbench.training.synthetic_traces import BayesianTraceConfig, PayoffRiskConfig


def _pairs(count: int = 4) -> list:
    config = BayesianTraceConfig(
        seed=31,
        min_observations=2,
        max_observations=4,
        signal_reliability=0.7,
        payoff=PayoffRiskConfig(1.0, 1.0, 0.0, 0.35),
    )
    return generate_counterfactual_pairs(count, config=config, seed=31)


def test_instrumented_forward_exposes_projected_per_head_outputs(
    tiny_interp_checkpoint: dict,
) -> None:
    torch = pytest.importorskip("torch")
    from mimirbench.training.small_transformer import attn_head_out_site

    model = tiny_interp_checkpoint["model"]
    tokenizer = tiny_interp_checkpoint["tokenizer"]
    encoded = tokenizer.encode(_pairs(1)[0].clean_input)
    input_ids = torch.as_tensor([encoded["input_ids"]], dtype=torch.long)
    mask = torch.as_tensor([encoded["attention_mask"]], dtype=torch.long)

    model.eval()
    with torch.no_grad():
        output = model.forward_instrumented(input_ids, attention_mask=mask)
    head_outputs = output["attention_head_outputs"][0]
    assert head_outputs.shape == (1, model.config.n_heads, model.config.max_seq_len, model.config.d_model)
    for head in range(model.config.n_heads):
        assert output["sites"][attn_head_out_site(0, head)].shape == (
            1,
            model.config.max_seq_len,
            model.config.d_model,
        )
    expected = head_outputs.sum(dim=1) + model.encoder.layers[0].self_attn.out_proj.bias
    assert torch.allclose(expected, output["sites"]["blocks.0.attn_out"], atol=1e-6)


def test_per_head_patching_and_ablation_shapes(tiny_interp_checkpoint: dict) -> None:
    pytest.importorskip("torch")
    from mimirbench.interpretability.head_token_analysis import (
        run_per_head_ablation,
        run_per_head_patching,
    )

    model = tiny_interp_checkpoint["model"]
    tokenizer = tiny_interp_checkpoint["tokenizer"]
    pairs = _pairs()
    patching = run_per_head_patching(model, tokenizer, pairs, seed=9)
    n_sites = model.config.n_layers * model.config.n_heads
    assert len(patching["rows"]) == len(pairs) * n_sites * 2 * 2
    for site in patching["sites"]:
        assert set(patching["summary"]["by_site"][site]) == {"matched", "mismatched"}

    ablation = run_per_head_ablation(model, tokenizer, pairs, seed=9)
    assert len(ablation["rows"]) == n_sites * 2
    assert set(ablation["baseline"]) == {
        "action_accuracy",
        "posterior_bucket_accuracy",
        "mean_posterior_error",
    }
    assert {row["control"] for row in ablation["rows"]} == {
        "full_head_zero",
        "random_position_zero",
    }


def test_individual_position_patching_precedes_semantic_aggregation(
    tiny_interp_checkpoint: dict,
) -> None:
    pytest.importorskip("torch")
    from mimirbench.interpretability.head_token_analysis import (
        run_individual_token_position_patching,
    )

    model = tiny_interp_checkpoint["model"]
    tokenizer = tiny_interp_checkpoint["tokenizer"]
    pairs = _pairs()
    result = run_individual_token_position_patching(model, tokenizer, pairs)
    assert result["positions"]
    assert all("position" in row and "heads" in row for row in result["positions"])
    assert set(result["summary"]) == {"by_site", "by_group"}
    for site in result["sites"]:
        assert result["summary"]["by_site"][site]["positions"]
        assert "evidence" in result["summary"]["by_group"][site]
