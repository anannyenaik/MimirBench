"""Tests for the compact transformer model."""

from __future__ import annotations

from pathlib import Path

import pytest

from mimirbench.training.small_transformer import (
    SmallTransformerConfig,
    SmallTransformerForTracePrediction,
)
from mimirbench.training.synthetic_traces import label_vocab_for_config


def test_small_transformer_forward_and_checkpoint_roundtrip(tmp_path: Path) -> None:
    torch = pytest.importorskip("torch")
    label_vocab = label_vocab_for_config()
    model = SmallTransformerForTracePrediction(
        SmallTransformerConfig(
            vocab_size=16,
            max_seq_len=8,
            d_model=16,
            n_layers=1,
            n_heads=2,
            dim_feedforward=32,
            num_posterior_buckets=len(label_vocab["posterior_bucket"]),
        ),
        label_vocab=label_vocab,
    )
    input_ids = torch.randint(0, 16, (2, 8))
    attention_mask = torch.ones((2, 8), dtype=torch.long)
    labels = {
        "posterior_bucket": torch.zeros(2, dtype=torch.long),
        "action": torch.zeros(2, dtype=torch.long),
        "ev_bucket": torch.zeros(2, dtype=torch.long),
        "risk_flag": torch.zeros(2, dtype=torch.long),
        "confidence_bucket": torch.zeros(2, dtype=torch.long),
        "rationale_class": torch.zeros(2, dtype=torch.long),
    }
    output = model(input_ids, attention_mask=attention_mask, labels=labels)
    assert "loss" in output
    assert output["logits"]["action"].shape == (2, 2)

    checkpoint = model.save_checkpoint(tmp_path / "model.pt")
    loaded, payload = SmallTransformerForTracePrediction.load_checkpoint(checkpoint)
    assert payload["format_version"] == 1
    prediction = loaded.predict(input_ids[:1], attention_mask=attention_mask[:1])
    assert "posterior_bucket" in prediction
