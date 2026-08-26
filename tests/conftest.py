"""Shared fixtures for the interpretability tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def tiny_interp_checkpoint(tmp_path: Path) -> dict[str, Any]:
    """Build and save a tiny (untrained) small-transformer checkpoint + vocab.

    Skips when torch is unavailable. The model has random weights, so these tests
    exercise the interpretability *infrastructure*, not model quality.
    """
    pytest.importorskip("torch")
    from mimirbench.training.small_transformer import (
        SmallTransformerConfig,
        SmallTransformerForTracePrediction,
    )
    from mimirbench.training.synthetic_traces import (
        BayesianTraceConfig,
        generate_trace_splits,
        label_vocab_for_config,
    )
    from mimirbench.training.tokenizer import TraceTokenizer

    trace_config = BayesianTraceConfig(seed=7)
    splits = generate_trace_splits(num_train=48, num_val=0, num_test=0, config=trace_config)
    tokenizer = TraceTokenizer.from_traces(splits["train"], max_length=128)
    label_vocab = label_vocab_for_config(trace_config)
    model = SmallTransformerForTracePrediction(
        SmallTransformerConfig(
            vocab_size=tokenizer.vocab_size,
            max_seq_len=128,
            d_model=32,
            n_layers=1,
            n_heads=2,
            dim_feedforward=64,
            pad_token_id=tokenizer.pad_id,
            num_posterior_buckets=len(label_vocab["posterior_bucket"]),
        ),
        label_vocab=label_vocab,
    )
    checkpoint = model.save_checkpoint(tmp_path / "checkpoints" / "best.pt", tokenizer=tokenizer)
    vocab = tokenizer.save(tmp_path / "vocab.json")
    return {
        "checkpoint": checkpoint,
        "vocab": vocab,
        "dir": tmp_path,
        "model": model,
        "tokenizer": tokenizer,
        "trace_config": trace_config,
    }
