"""Tests for activation capture hooks and the trace capture driver."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from mimirbench.training.synthetic_traces import BayesianTraceConfig, generate_trace_splits


def test_activation_capturer_preserves_shapes(tiny_interp_checkpoint: dict) -> None:
    torch = pytest.importorskip("torch")
    from mimirbench.interpretability.activation_capture import ActivationCapturer

    model = tiny_interp_checkpoint["model"]
    # Hook the standard forward path (nn.TransformerEncoder calls each layer's
    # __call__, so forward hooks fire). All-ones input avoids any padding.
    sites = {"resid": "encoder.layers.0", "mlp": "encoder.layers.0.linear2"}
    input_ids = torch.ones((2, 12), dtype=torch.long)
    with ActivationCapturer(model, sites) as capturer, torch.no_grad():
        model(input_ids)
    captured = capturer.activations
    assert set(captured) == {"resid", "mlp"}
    assert tuple(captured["resid"].shape) == (2, 12, model.config.d_model)
    assert tuple(captured["mlp"].shape) == (2, 12, model.config.d_model)
    # hooks are removed on exit
    assert capturer._handles == []


def test_activation_capturer_unknown_module_raises(tiny_interp_checkpoint: dict) -> None:
    pytest.importorskip("torch")
    from mimirbench.interpretability.activation_capture import ActivationCapturer

    model = tiny_interp_checkpoint["model"]
    with pytest.raises(KeyError), ActivationCapturer(model, {"x": "does.not.exist"}):
        pass


def test_capture_trace_activations_shapes_labels_metadata(tiny_interp_checkpoint: dict) -> None:
    pytest.importorskip("torch")
    from mimirbench.interpretability.activation_capture import capture_trace_activations
    from mimirbench.training.small_transformer import interpretability_site_names

    model = tiny_interp_checkpoint["model"]
    tokenizer = tiny_interp_checkpoint["tokenizer"]
    traces = generate_trace_splits(
        num_train=16, num_val=0, num_test=0, config=BayesianTraceConfig(seed=21)
    )["train"]
    captured = capture_trace_activations(
        model, tokenizer, traces, batch_size=8, metadata={"dataset_split": "train"}
    )
    sites = list(interpretability_site_names(model.config.n_layers))
    assert captured.site_names == sites
    for site in sites:
        assert captured.features[site].shape == (16, model.config.d_model)
    assert set(captured.labels) == {"posterior_bucket", "action", "risk_flag", "confidence_bucket"}
    assert captured.metadata["dataset_split"] == "train"
    assert captured.num_examples == 16
    assert len(captured.trace_ids) == 16


def test_captured_activations_roundtrip(tiny_interp_checkpoint: dict, tmp_path: Path) -> None:
    pytest.importorskip("torch")
    from mimirbench.interpretability.activation_capture import (
        CapturedActivations,
        capture_trace_activations,
    )

    model = tiny_interp_checkpoint["model"]
    tokenizer = tiny_interp_checkpoint["tokenizer"]
    traces = generate_trace_splits(
        num_train=8, num_val=0, num_test=0, config=BayesianTraceConfig(seed=31)
    )["train"]
    captured = capture_trace_activations(model, tokenizer, traces, metadata={"dataset_split": "train"})
    npz_path, json_path = captured.save(tmp_path / "acts")
    assert npz_path.exists() and json_path.exists()
    loaded = CapturedActivations.load(tmp_path / "acts")
    assert loaded.trace_ids == captured.trace_ids
    for site in captured.site_names:
        assert np.allclose(loaded.features[site], captured.features[site])
    for label in captured.labels:
        assert np.array_equal(loaded.labels[label], captured.labels[label])
