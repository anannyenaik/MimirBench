"""Capture internal activations from the small Bayesian transformer.

Two layers of API live here:

* :class:`ActivationCapturer` is a generic, model-agnostic forward-hook recorder.
  Give it ``{capture_name: qualified_module_name}`` and it records each module's
  output during a no-grad forward pass. This is the "named module hooks" piece
  and works on any ``torch.nn.Module``.

* :func:`capture_trace_activations` is the project-specific driver. It runs the
  small transformer's instrumented forward over a batch of synthetic Bayesian
  traces, mean-pools each site over the (un-padded) sequence, and packages the
  result, together with per-trace labels and reproducibility metadata, into a
  :class:`CapturedActivations` object that the probes consume.

Importing this module pulls in torch (lazily, via the training package). It is
deliberately *not* re-exported from ``mimirbench.interpretability`` so that
``import mimirbench.interpretability`` stays torch-free.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import numpy as np
import numpy.typing as npt

from mimirbench.training.small_transformer import (
    SmallTransformerForTracePrediction,
    interpretability_site_names,
    require_torch,
)
from mimirbench.training.tokenizer import TraceTokenizer

__all__ = [
    "DEFAULT_LABEL_KEYS",
    "ActivationCapturer",
    "CapturedActivations",
    "capture_trace_activations",
    "small_transformer_capture_sites",
]

# Trace target keys we attach to every captured example, mapped to a short probe
# name. ``posterior_A_bucket`` is renamed to ``posterior_bucket`` for the probes.
DEFAULT_LABEL_KEYS: dict[str, str] = {
    "posterior_bucket": "posterior_A_bucket",
    "action": "action",
    "risk_flag": "risk_flag",
    "confidence_bucket": "confidence_bucket",
}


class ActivationCapturer:
    """Record the outputs of named modules during a forward pass via hooks.

    Usage::

        with ActivationCapturer(model, {"resid": "encoder.layers.0"}) as cap:
            model(input_ids)
        acts = cap.activations  # {"resid": tensor}

    Hooks are removed on context exit (or :meth:`remove`). Tuple outputs (e.g.
    ``nn.MultiheadAttention``) are reduced to their first element.
    """

    def __init__(self, model: Any, sites: Mapping[str, str]) -> None:
        self.model = model
        self.sites = dict(sites)
        self._handles: list[Any] = []
        self._store: dict[str, Any] = {}

    def __enter__(self) -> ActivationCapturer:
        require_torch()
        modules = dict(self.model.named_modules())
        missing = [name for name in self.sites.values() if name not in modules]
        if missing:
            raise KeyError(f"model has no module(s) named: {sorted(set(missing))}")
        for capture_name, module_name in self.sites.items():
            handle = modules[module_name].register_forward_hook(self._make_hook(capture_name))
            self._handles.append(handle)
        return self

    def __exit__(self, *exc: object) -> None:
        self.remove()

    def _make_hook(self, capture_name: str):  # type: ignore[no-untyped-def]
        def hook(_module: Any, _inputs: Any, output: Any) -> None:
            tensor = output[0] if isinstance(output, tuple) else output
            self._store[capture_name] = tensor.detach()

        return hook

    def remove(self) -> None:
        """Remove all registered hooks."""
        for handle in self._handles:
            handle.remove()
        self._handles.clear()

    @property
    def activations(self) -> dict[str, Any]:
        """The most recently captured activations, keyed by capture name."""
        return dict(self._store)


@dataclass(frozen=True)
class CapturedActivations:
    """Mean-pooled per-site activations plus labels and reproducibility metadata."""

    features: dict[str, npt.NDArray[np.float64]]
    labels: dict[str, npt.NDArray[np.int64]]
    label_classes: dict[str, list[str]]
    trace_ids: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def site_names(self) -> list[str]:
        return list(self.features.keys())

    @property
    def num_examples(self) -> int:
        return len(self.trace_ids)

    def feature_shapes(self) -> dict[str, list[int]]:
        return {site: list(matrix.shape) for site, matrix in self.features.items()}

    def save(self, path: str | Path) -> tuple[Path, Path]:
        """Save arrays to ``<path>.npz`` and metadata to ``<path>.json``.

        Returns the ``(npz_path, json_path)`` that were written.
        """
        base = Path(path)
        base.parent.mkdir(parents=True, exist_ok=True)
        npz_path = base.with_suffix(".npz")
        json_path = base.with_suffix(".json")
        arrays: dict[str, npt.NDArray[Any]] = {}
        for site, matrix in self.features.items():
            arrays[f"feat::{site}"] = matrix
        for name, codes in self.labels.items():
            arrays[f"label::{name}"] = codes
        np.savez(npz_path, **cast(Any, arrays))
        sidecar = {
            "trace_ids": self.trace_ids,
            "site_names": self.site_names,
            "feature_shapes": self.feature_shapes(),
            "label_names": list(self.labels.keys()),
            "label_classes": self.label_classes,
            "metadata": self.metadata,
        }
        json_path.write_text(json.dumps(sidecar, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        return npz_path, json_path

    @classmethod
    def load(cls, path: str | Path) -> CapturedActivations:
        """Load activations previously written by :meth:`save`."""
        base = Path(path)
        npz_path = base.with_suffix(".npz")
        json_path = base.with_suffix(".json")
        with np.load(npz_path) as data:
            features = {
                key.removeprefix("feat::"): np.asarray(data[key], dtype=np.float64)
                for key in data.files
                if key.startswith("feat::")
            }
            labels = {
                key.removeprefix("label::"): np.asarray(data[key], dtype=np.int64)
                for key in data.files
                if key.startswith("label::")
            }
        sidecar = json.loads(json_path.read_text(encoding="utf-8"))
        return cls(
            features=features,
            labels=labels,
            label_classes={str(k): list(v) for k, v in sidecar.get("label_classes", {}).items()},
            trace_ids=list(sidecar.get("trace_ids", [])),
            metadata=dict(sidecar.get("metadata", {})),
        )


def small_transformer_capture_sites(n_layers: int) -> dict[str, str]:
    """Map the canonical interpretability site names to themselves.

    The instrumented forward already exposes activations keyed by these names, so
    the mapping is the identity; the helper exists to document the available
    sites and to mirror the :class:`ActivationCapturer` ``{name: module}`` shape.
    """
    return {site: site for site in interpretability_site_names(n_layers)}


def capture_trace_activations(
    model: SmallTransformerForTracePrediction,
    tokenizer: TraceTokenizer,
    traces: Sequence[Mapping[str, Any]],
    *,
    sites: Sequence[str] | None = None,
    label_keys: Mapping[str, str] | None = None,
    label_classes: Mapping[str, Sequence[str]] | None = None,
    batch_size: int = 16,
    max_examples: int | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> CapturedActivations:
    """Capture mean-pooled site activations for a list of synthetic traces.

    Each site's feature vector is the model's masked mean over un-padded
    positions (exactly the pooling the classification heads see), so the
    probes read the same representation the model itself reduces to a decision.

    ``label_classes`` pins the integer encoding of each label (e.g. from the
    model's label vocab) so captures over different splits stay aligned. When
    omitted, classes are derived from the observed values.
    """
    torch_mod, _, _ = require_torch()
    label_keys = dict(label_keys or DEFAULT_LABEL_KEYS)
    selected = list(traces) if max_examples is None else list(traces)[:max_examples]
    if not selected:
        raise ValueError("no traces to capture activations from.")
    site_names = list(sites) if sites is not None else list(interpretability_site_names(model.config.n_layers))

    feature_chunks: dict[str, list[npt.NDArray[np.float64]]] = {site: [] for site in site_names}
    label_values: dict[str, list[str]] = {name: [] for name in label_keys}
    trace_ids: list[str] = []

    model.eval()
    for start in range(0, len(selected), batch_size):
        batch = selected[start : start + batch_size]
        input_ids, attention_mask = _encode_batch(torch_mod, tokenizer, batch, model.config.max_seq_len)
        with torch_mod.no_grad():
            output = model.forward_instrumented(
                input_ids, attention_mask=attention_mask, capture_attention=False
            )
        mask = attention_mask.to(torch_mod.float32)
        for site in site_names:
            if site not in output["sites"]:
                raise KeyError(f"site {site!r} is not exposed by the model.")
            pooled = _masked_mean(output["sites"][site], mask)
            feature_chunks[site].append(pooled.cpu().numpy().astype(np.float64))
        for trace in batch:
            targets = trace.get("targets")
            if not isinstance(targets, Mapping):
                raise ValueError("trace is missing a targets mapping.")
            for name, target_key in label_keys.items():
                value = targets.get(target_key)
                label_values[name].append(str(value))
            trace_ids.append(str(trace.get("id", f"trace-{len(trace_ids)}")))

    features = {site: np.concatenate(chunks, axis=0) for site, chunks in feature_chunks.items()}
    labels, resolved_classes = _encode_labels(label_values, label_classes)
    meta = {
        "dataset_split": "unknown",
        "num_examples": len(trace_ids),
        "n_layers": model.config.n_layers,
        "d_model": model.config.d_model,
        "sites": site_names,
        **dict(metadata or {}),
    }
    return CapturedActivations(
        features=features,
        labels=labels,
        label_classes=resolved_classes,
        trace_ids=trace_ids,
        metadata=meta,
    )


def _encode_batch(
    torch_mod: Any,
    tokenizer: TraceTokenizer,
    batch: Iterable[Mapping[str, Any]],
    max_seq_len: int,
) -> tuple[Any, Any]:
    input_rows: list[list[int]] = []
    mask_rows: list[list[int]] = []
    for trace in batch:
        text = trace.get("input")
        if not isinstance(text, str):
            raise ValueError("trace is missing a string 'input'.")
        encoded = tokenizer.encode(text)
        ids = encoded["input_ids"][:max_seq_len]
        mask = encoded["attention_mask"][:max_seq_len]
        input_rows.append(ids)
        mask_rows.append(mask)
    input_ids = torch_mod.as_tensor(input_rows, dtype=torch_mod.long)
    attention_mask = torch_mod.as_tensor(mask_rows, dtype=torch_mod.long)
    return input_ids, attention_mask


def _masked_mean(activations: Any, mask: Any) -> Any:
    expanded = mask.unsqueeze(-1)
    summed = (activations * expanded).sum(dim=1)
    counts = expanded.sum(dim=1).clamp(min=1.0)
    return summed / counts


def _encode_labels(
    label_values: Mapping[str, list[str]],
    canonical: Mapping[str, Sequence[str]] | None,
) -> tuple[dict[str, npt.NDArray[np.int64]], dict[str, list[str]]]:
    labels: dict[str, npt.NDArray[np.int64]] = {}
    label_classes: dict[str, list[str]] = {}
    for name, values in label_values.items():
        if canonical is not None and name in canonical:
            classes = list(canonical[name])
        else:
            classes = sorted(set(values))
        code_of = {label: index for index, label in enumerate(classes)}
        missing = sorted({value for value in values if value not in code_of})
        if missing:
            raise ValueError(f"label {name!r} has values outside its class set: {missing}")
        labels[name] = np.asarray([code_of[value] for value in values], dtype=np.int64)
        label_classes[name] = classes
    return labels, label_classes
