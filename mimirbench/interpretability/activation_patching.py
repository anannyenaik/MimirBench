"""Activation patching (causal tracing) for the small Bayesian transformer.

The question probes answer is *where is information represented*. Patching asks
the harder, causal question: *which activation, if restored from a clean run,
moves a corrupted run's prediction back?* The recipe per minimal pair is:

1. run the **clean** input and cache every site's activation;
2. run the **corrupted** input (different evidence) — the prediction shifts;
3. for each site, re-run the corrupted input but overwrite that site with the
   clean activation, and measure how far the prediction snaps back.

The headline quantity is

    causal_effect = P(clean target | patched corrupted) - P(clean target | corrupted)

where the "clean target" is the model's own clean-run decision, so the measure
is about restoring the clean computation rather than about being correct.

``PatchSpec`` / ``PatchResult`` are the original stable primitives; everything
torch-dependent is imported lazily so ``import mimirbench.interpretability`` stays
torch-free.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import numpy.typing as npt

__all__ = [
    "DEFAULT_PATCH_HEADS",
    "PatchResult",
    "PatchSpec",
    "PatchingExperimentResult",
    "activation_patch",
    "run_activation_patching",
]

# Heads tracked by the patching experiment; the first is the headline decision.
DEFAULT_PATCH_HEADS: tuple[str, ...] = (
    "action",
    "posterior_bucket",
    "risk_flag",
    "confidence_bucket",
)


@dataclass(frozen=True)
class PatchSpec:
    """Where to patch: a named site and a sequence position (-1 for all)."""

    hook_name: str
    position: int


@dataclass(frozen=True)
class PatchResult:
    """Effect of replacing a clean activation with a corrupted one (or vice versa)."""

    spec: PatchSpec
    clean_metric: float
    corrupted_metric: float
    patched_metric: float

    @property
    def restoration(self) -> float:
        """Fraction of the clean→corrupted metric gap restored by the patch."""
        gap = self.clean_metric - self.corrupted_metric
        if gap == 0.0:
            return 0.0
        return (self.patched_metric - self.corrupted_metric) / gap


@dataclass(frozen=True)
class PatchingExperimentResult:
    """Per-(pair, site) rows plus aggregated per-site and overall summaries."""

    rows: list[dict[str, Any]]
    summary: dict[str, Any]
    sites: list[str]
    heads: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)


def activation_patch(
    model: Any,
    clean_tokens: Sequence[int],
    corrupted_tokens: Sequence[int],
    spec: PatchSpec,
    metric: Callable[[Mapping[str, Any]], float],
) -> PatchResult:
    """Run a single activation patch and measure ``metric`` restoration.

    The clean activation at ``spec.hook_name`` (whole sequence when
    ``spec.position < 0``, else just that position) is spliced into the corrupted
    forward pass. ``metric`` maps a model output dict to a scalar.
    """
    from mimirbench.training.small_transformer import require_torch

    torch_mod, _, _ = require_torch()
    if len(clean_tokens) != len(corrupted_tokens):
        raise ValueError("clean and corrupted token sequences must be the same length.")
    clean_ids = torch_mod.as_tensor([list(clean_tokens)], dtype=torch_mod.long)
    corrupted_ids = torch_mod.as_tensor([list(corrupted_tokens)], dtype=torch_mod.long)
    model.eval()
    with torch_mod.no_grad():
        clean_out = model.forward_instrumented(clean_ids, capture_attention=False)
        corrupted_out = model.forward_instrumented(corrupted_ids, capture_attention=False)
        if spec.hook_name not in clean_out["sites"]:
            raise KeyError(f"unknown patch site {spec.hook_name!r}.")
        donor = clean_out["sites"][spec.hook_name]
        positions = None if spec.position < 0 else {spec.hook_name: [spec.position]}
        patched_out = model.forward_instrumented(
            corrupted_ids,
            patch={spec.hook_name: donor},
            patch_positions=positions,
            capture_attention=False,
        )
    return PatchResult(
        spec=spec,
        clean_metric=float(metric(clean_out)),
        corrupted_metric=float(metric(corrupted_out)),
        patched_metric=float(metric(patched_out)),
    )


def run_activation_patching(
    model: Any,
    tokenizer: Any,
    pairs: Sequence[Any],
    *,
    sites: Sequence[str] | None = None,
    heads: Sequence[str] = DEFAULT_PATCH_HEADS,
    metadata: Mapping[str, Any] | None = None,
) -> PatchingExperimentResult:
    """Patch every site for every clean/corrupted pair and aggregate the effects."""
    from mimirbench.training.small_transformer import (
        interpretability_site_names,
        require_torch,
    )

    torch_mod, _, _ = require_torch()
    if not pairs:
        raise ValueError("no counterfactual pairs supplied.")
    site_names = list(sites) if sites is not None else list(
        interpretability_site_names(model.config.n_layers)
    )
    head_names = [head for head in heads if head in model.heads]
    label_vocab: dict[str, list[str]] = {h: list(model.label_vocab.get(h, [])) for h in head_names}

    rows: list[dict[str, Any]] = []
    model.eval()
    for pair in pairs:
        clean_ids, corrupted_ids = _encode_pair(torch_mod, tokenizer, pair, model.config.max_seq_len)
        with torch_mod.no_grad():
            clean_out = model.forward_instrumented(clean_ids, capture_attention=False)
            corrupted_out = model.forward_instrumented(corrupted_ids, capture_attention=False)
        clean_probs = {h: _softmax(clean_out["logits"][h]) for h in head_names}
        corrupted_probs = {h: _softmax(corrupted_out["logits"][h]) for h in head_names}
        clean_pred = {h: int(np.argmax(clean_probs[h])) for h in head_names}
        corrupted_pred = {h: int(np.argmax(corrupted_probs[h])) for h in head_names}

        for site in site_names:
            donor = clean_out["sites"][site]
            with torch_mod.no_grad():
                patched_out = model.forward_instrumented(
                    corrupted_ids, patch={site: donor}, capture_attention=False
                )
            patched_probs = {h: _softmax(patched_out["logits"][h]) for h in head_names}
            patched_pred = {h: int(np.argmax(patched_probs[h])) for h in head_names}
            for head in head_names:
                target = clean_pred[head]
                rows.append(
                    {
                        "pair_id": getattr(pair, "pair_id", None),
                        "site": site,
                        "head": head,
                        "clean_prediction": _label(label_vocab[head], clean_pred[head]),
                        "corrupted_prediction": _label(label_vocab[head], corrupted_pred[head]),
                        "patched_prediction": _label(label_vocab[head], patched_pred[head]),
                        "clean_target_prob": float(clean_probs[head][target]),
                        "corrupted_target_prob": float(corrupted_probs[head][target]),
                        "patched_target_prob": float(patched_probs[head][target]),
                        "causal_effect": float(
                            patched_probs[head][target] - corrupted_probs[head][target]
                        ),
                        "corrupted_flipped": bool(corrupted_pred[head] != clean_pred[head]),
                        "recovered": bool(patched_pred[head] == clean_pred[head]),
                    }
                )

    summary = _summarise(rows, site_names, head_names)
    return PatchingExperimentResult(
        rows=rows,
        summary=summary,
        sites=site_names,
        heads=head_names,
        metadata={"num_pairs": len(pairs), **dict(metadata or {})},
    )


def _summarise(
    rows: list[dict[str, Any]],
    site_names: list[str],
    head_names: list[str],
) -> dict[str, Any]:
    by_site: dict[str, Any] = {}
    for site in site_names:
        site_rows = [row for row in rows if row["site"] == site]
        head_block: dict[str, Any] = {}
        for head in head_names:
            head_rows = [row for row in site_rows if row["head"] == head]
            head_block[head] = _head_metrics(head_rows)
        recoveries = [head_block[h]["recovery_rate"] for h in head_names if head_block[h]["recovery_rate"] is not None]
        by_site[site] = {
            "heads": head_block,
            "mean_causal_effect_action": head_block.get("action", {}).get("mean_causal_effect"),
            "label_recovery_rate": float(np.mean(recoveries)) if recoveries else None,
            "action_recovery_rate": head_block.get("action", {}).get("recovery_rate"),
            "posterior_bucket_recovery_rate": head_block.get("posterior_bucket", {}).get("recovery_rate"),
        }
    best_site = _argmax_site(by_site, "action_recovery_rate")
    return {
        "by_site": by_site,
        "site_order": site_names,
        "heads": head_names,
        "best_action_recovery_site": best_site,
    }


def _head_metrics(head_rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not head_rows:
        return {
            "mean_clean_target_prob": None,
            "mean_corrupted_target_prob": None,
            "mean_patched_target_prob": None,
            "mean_causal_effect": None,
            "recovery_rate": None,
            "n_flipped": 0,
            "n": 0,
        }
    flipped = [row for row in head_rows if row["corrupted_flipped"]]
    recovery = (
        float(np.mean([row["recovered"] for row in flipped])) if flipped else None
    )
    effects = np.asarray([r["causal_effect"] for r in head_rows], dtype=np.float64)
    return {
        "mean_clean_target_prob": float(np.mean([r["clean_target_prob"] for r in head_rows])),
        "mean_corrupted_target_prob": float(np.mean([r["corrupted_target_prob"] for r in head_rows])),
        "mean_patched_target_prob": float(np.mean([r["patched_target_prob"] for r in head_rows])),
        "mean_causal_effect": float(effects.mean()),
        "mean_abs_causal_effect": float(np.abs(effects).mean()),
        "recovery_rate": recovery,
        "n_flipped": len(flipped),
        "n": len(head_rows),
    }


def _argmax_site(by_site: Mapping[str, Any], key: str) -> str | None:
    best: str | None = None
    best_value = -np.inf
    for site, block in by_site.items():
        value = block.get(key)
        if value is not None and value > best_value:
            best_value = value
            best = site
    return best


def _encode_pair(torch_mod: Any, tokenizer: Any, pair: Any, max_seq_len: int) -> tuple[Any, Any]:
    clean = tokenizer.encode(pair.clean_input)
    corrupted = tokenizer.encode(pair.corrupted_input)
    clean_ids = torch_mod.as_tensor([clean["input_ids"][:max_seq_len]], dtype=torch_mod.long)
    corrupted_ids = torch_mod.as_tensor([corrupted["input_ids"][:max_seq_len]], dtype=torch_mod.long)
    if clean_ids.shape[1] != corrupted_ids.shape[1]:
        raise ValueError(
            "clean and corrupted inputs tokenized to different lengths; "
            "patching requires aligned positions."
        )
    return clean_ids, corrupted_ids


def _softmax(logits: Any) -> npt.NDArray[np.float64]:
    values = np.asarray(logits.detach().cpu().numpy(), dtype=np.float64).reshape(-1)
    shifted = values - values.max()
    exp = np.exp(shifted)
    return exp / exp.sum()


def _label(vocab: list[str], index: int) -> str | int:
    return vocab[index] if 0 <= index < len(vocab) else index
