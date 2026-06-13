"""Position-resolved (token-group) activation patching and negative controls.

The Stage 8 :func:`run_activation_patching` patches a whole site at once, so it
cannot say *which token positions* carry the causal signal. This module patches
only the positions belonging to a semantic token group (prior / evidence /
payoff-risk) of a site, which directly addresses the documented "patching is
full-sequence per site" limitation.

Because the counterfactual corruption changes **only** the evidence
(observation) tokens, the prior and payoff-risk groups are designed *negative
controls* at the sub-block sites: their activations still differ between clean
and corrupted (attention mixes the changed evidence into every position), yet
restoring them should recover the decision far less than restoring the evidence
positions. :func:`run_mismatched_donor_control` adds a second, independent
negative control: patching with a clean donor from an *unrelated* example of the
same length should not restore the specific clean decision.

Everything torch-dependent is imported lazily so importing
``mimirbench.interpretability`` stays torch-free.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from mimirbench.interpretability.attention_analysis import token_group_spans

__all__ = [
    "DEFAULT_CONTROL_SITE",
    "DEFAULT_GROUPS",
    "DEFAULT_HEADS",
    "MismatchedDonorResult",
    "TokenGroupPatchingResult",
    "run_mismatched_donor_control",
    "run_token_group_patching",
]

# Heads scored by the position-resolved experiment (first is the headline).
DEFAULT_HEADS: tuple[str, ...] = ("action", "posterior_bucket")
# Evidence is the corrupted group; prior / payoff_risk are built-in controls.
DEFAULT_GROUPS: tuple[str, ...] = ("evidence", "prior", "payoff_risk")
DEFAULT_CONTROL_SITE = "blocks.0.attn_out"


@dataclass(frozen=True)
class TokenGroupPatchingResult:
    """Per-(pair, site, group) rows plus aggregated per-(site, group) summaries."""

    rows: list[dict[str, Any]]
    summary: dict[str, Any]
    sites: list[str]
    groups: list[str]
    heads: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MismatchedDonorResult:
    """Matched vs mismatched-donor recovery at one site (a negative control)."""

    site: str
    summary: dict[str, Any]
    rows: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)


def run_token_group_patching(
    model: Any,
    tokenizer: Any,
    pairs: Sequence[Any],
    *,
    sites: Sequence[str] | None = None,
    groups: Sequence[str] = DEFAULT_GROUPS,
    heads: Sequence[str] = DEFAULT_HEADS,
    metadata: Mapping[str, Any] | None = None,
) -> TokenGroupPatchingResult:
    """Patch only each token group's positions of each site and aggregate effects."""
    from mimirbench.training.small_transformer import interpretability_site_names, require_torch

    torch_mod, _, _ = require_torch()
    if not pairs:
        raise ValueError("no counterfactual pairs supplied.")
    site_names = (
        list(sites)
        if sites is not None
        else [s for s in interpretability_site_names(model.config.n_layers) if s != "embed"]
    )
    head_names = [head for head in heads if head in model.heads]
    group_names = list(groups)
    label_vocab = {h: list(model.label_vocab.get(h, [])) for h in head_names}

    rows: list[dict[str, Any]] = []
    model.eval()
    for pair in pairs:
        clean_ids, corrupted_ids = _encode_pair(torch_mod, tokenizer, pair, model.config.max_seq_len)
        spans = _group_spans(tokenizer, pair.clean_input, clean_ids.shape[1])
        with torch_mod.no_grad():
            clean_out = model.forward_instrumented(clean_ids, capture_attention=False)
            corrupted_out = model.forward_instrumented(corrupted_ids, capture_attention=False)
        clean_probs = {h: _softmax(clean_out["logits"][h]) for h in head_names}
        corrupted_probs = {h: _softmax(corrupted_out["logits"][h]) for h in head_names}
        clean_pred = {h: int(np.argmax(clean_probs[h])) for h in head_names}
        corrupted_pred = {h: int(np.argmax(corrupted_probs[h])) for h in head_names}

        for site in site_names:
            donor = clean_out["sites"][site]
            for group in group_names:
                positions = spans.get(group, [])
                if not positions:
                    continue
                with torch_mod.no_grad():
                    patched_out = model.forward_instrumented(
                        corrupted_ids,
                        patch={site: donor},
                        patch_positions={site: positions},
                        capture_attention=False,
                    )
                patched_probs = {h: _softmax(patched_out["logits"][h]) for h in head_names}
                patched_pred = {h: int(np.argmax(patched_probs[h])) for h in head_names}
                for head in head_names:
                    target = clean_pred[head]
                    rows.append(
                        {
                            "pair_id": getattr(pair, "pair_id", None),
                            "site": site,
                            "group": group,
                            "head": head,
                            "n_positions": len(positions),
                            "clean_prediction": _label(label_vocab[head], clean_pred[head]),
                            "corrupted_prediction": _label(label_vocab[head], corrupted_pred[head]),
                            "patched_prediction": _label(label_vocab[head], patched_pred[head]),
                            "causal_effect": float(
                                patched_probs[head][target] - corrupted_probs[head][target]
                            ),
                            "corrupted_flipped": bool(corrupted_pred[head] != clean_pred[head]),
                            "recovered": bool(patched_pred[head] == clean_pred[head]),
                        }
                    )

    summary = _summarise_groups(rows, site_names, group_names, head_names)
    return TokenGroupPatchingResult(
        rows=rows,
        summary=summary,
        sites=site_names,
        groups=group_names,
        heads=head_names,
        metadata={"num_pairs": len(pairs), **dict(metadata or {})},
    )


def run_mismatched_donor_control(
    model: Any,
    tokenizer: Any,
    pairs: Sequence[Any],
    *,
    site: str = DEFAULT_CONTROL_SITE,
    heads: Sequence[str] = DEFAULT_HEADS,
    seed: int = 123,
    metadata: Mapping[str, Any] | None = None,
) -> MismatchedDonorResult:
    """Compare matched vs unrelated-donor recovery at ``site`` (negative control).

    For each pair we patch the full ``site`` with (a) its own clean activation
    (matched) and (b) a clean activation from a *different* pair of the same
    token length (mismatched). A localised, evidence-carrying activation should
    recover the clean decision when matched and not when mismatched.
    """
    from mimirbench.training.small_transformer import require_torch

    torch_mod, _, _ = require_torch()
    if not pairs:
        raise ValueError("no counterfactual pairs supplied.")
    head_names = [head for head in heads if head in model.heads]

    # Cache encodings, clean donors, and predictions; bucket by token length.
    encoded: list[dict[str, Any]] = []
    by_length: dict[int, list[int]] = {}
    model.eval()
    for idx, pair in enumerate(pairs):
        clean_ids, corrupted_ids = _encode_pair(torch_mod, tokenizer, pair, model.config.max_seq_len)
        with torch_mod.no_grad():
            clean_out = model.forward_instrumented(clean_ids, capture_attention=False)
            corrupted_out = model.forward_instrumented(corrupted_ids, capture_attention=False)
        clean_probs = {h: _softmax(clean_out["logits"][h]) for h in head_names}
        corrupted_probs = {h: _softmax(corrupted_out["logits"][h]) for h in head_names}
        encoded.append(
            {
                "pair_id": getattr(pair, "pair_id", None),
                "corrupted_ids": corrupted_ids,
                "donor": clean_out["sites"][site],
                "length": int(clean_ids.shape[1]),
                "clean_pred": {h: int(np.argmax(clean_probs[h])) for h in head_names},
                "corrupted_pred": {h: int(np.argmax(corrupted_probs[h])) for h in head_names},
            }
        )
        by_length.setdefault(int(clean_ids.shape[1]), []).append(idx)

    donor_for = _deterministic_donor_map(by_length, seed=seed)

    rows: list[dict[str, Any]] = []
    for idx, item in enumerate(encoded):
        donor_idx = donor_for.get(idx)
        with torch_mod.no_grad():
            matched_out = model.forward_instrumented(
                item["corrupted_ids"], patch={site: item["donor"]}, capture_attention=False
            )
            matched_pred = {h: int(np.argmax(_softmax(matched_out["logits"][h]))) for h in head_names}
            mismatched_pred = None
            if donor_idx is not None:
                mismatched_out = model.forward_instrumented(
                    item["corrupted_ids"],
                    patch={site: encoded[donor_idx]["donor"]},
                    capture_attention=False,
                )
                mismatched_pred = {
                    h: int(np.argmax(_softmax(mismatched_out["logits"][h]))) for h in head_names
                }
        for head in head_names:
            if item["corrupted_pred"][head] == item["clean_pred"][head]:
                continue  # only count pairs the corruption flipped
            row = {
                "pair_id": item["pair_id"],
                "head": head,
                "matched_recovered": bool(matched_pred[head] == item["clean_pred"][head]),
                "has_mismatched_donor": donor_idx is not None,
            }
            if mismatched_pred is not None:
                row["mismatched_recovered"] = bool(
                    mismatched_pred[head] == item["clean_pred"][head]
                )
            rows.append(row)

    summary = _summarise_mismatched(rows, head_names)
    return MismatchedDonorResult(
        site=site,
        summary=summary,
        rows=rows,
        metadata={"num_pairs": len(pairs), "seed": seed, **dict(metadata or {})},
    )


# --------------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------------- #


def _summarise_groups(
    rows: list[dict[str, Any]],
    site_names: list[str],
    group_names: list[str],
    head_names: list[str],
) -> dict[str, Any]:
    by_site: dict[str, Any] = {}
    for site in site_names:
        group_block: dict[str, Any] = {}
        for group in group_names:
            head_block: dict[str, Any] = {}
            for head in head_names:
                subset = [
                    r for r in rows if r["site"] == site and r["group"] == group and r["head"] == head
                ]
                head_block[head] = _recovery_metrics(subset)
            group_block[group] = {
                "heads": head_block,
                "action_recovery_rate": head_block.get("action", {}).get("recovery_rate"),
                "mean_causal_effect_action": head_block.get("action", {}).get("mean_causal_effect"),
            }
        by_site[site] = group_block
    return {
        "by_site": by_site,
        "site_order": site_names,
        "groups": group_names,
        "heads": head_names,
    }


def _recovery_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"recovery_rate": None, "mean_causal_effect": None, "n_flipped": 0, "n": 0}
    flipped = [r for r in rows if r["corrupted_flipped"]]
    recovery = float(np.mean([r["recovered"] for r in flipped])) if flipped else None
    effects = np.asarray([r["causal_effect"] for r in rows], dtype=np.float64)
    return {
        "recovery_rate": recovery,
        "mean_causal_effect": float(effects.mean()),
        "n_flipped": len(flipped),
        "n": len(rows),
    }


def _summarise_mismatched(rows: list[dict[str, Any]], head_names: list[str]) -> dict[str, Any]:
    by_head: dict[str, Any] = {}
    for head in head_names:
        head_rows = [r for r in rows if r["head"] == head]
        matched = [r["matched_recovered"] for r in head_rows]
        mismatched = [r["mismatched_recovered"] for r in head_rows if "mismatched_recovered" in r]
        by_head[head] = {
            "n_flipped": len(head_rows),
            "matched_recovery_rate": float(np.mean(matched)) if matched else None,
            "mismatched_recovery_rate": float(np.mean(mismatched)) if mismatched else None,
            "n_with_mismatched_donor": len(mismatched),
        }
    return {"by_head": by_head, "heads": head_names}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _group_spans(tokenizer: Any, text: str, seq_len: int) -> dict[str, list[int]]:
    token_strings = tokenizer.tokenize(text)
    spans = token_group_spans(token_strings, offset=1)  # +1 for the prepended BOS
    return {group: [p for p in positions if 0 <= p < seq_len] for group, positions in spans.items()}


def _deterministic_donor_map(by_length: dict[int, list[int]], *, seed: int) -> dict[int, int]:
    """Map each pair index to a different same-length pair index (a derangement)."""
    donor_for: dict[int, int] = {}
    for length, indices in by_length.items():
        if len(indices) < 2:
            continue
        rng = np.random.default_rng(_stable_seed(f"donor:{seed}:{length}"))
        # Rotate by a non-zero offset so no index maps to itself.
        offset = 1 + int(rng.integers(0, len(indices) - 1))
        for position, source in enumerate(indices):
            donor_for[source] = indices[(position + offset) % len(indices)]
    return donor_for


def _encode_pair(torch_mod: Any, tokenizer: Any, pair: Any, max_seq_len: int) -> tuple[Any, Any]:
    clean = tokenizer.encode(pair.clean_input)
    corrupted = tokenizer.encode(pair.corrupted_input)
    clean_ids = torch_mod.as_tensor([clean["input_ids"][:max_seq_len]], dtype=torch_mod.long)
    corrupted_ids = torch_mod.as_tensor([corrupted["input_ids"][:max_seq_len]], dtype=torch_mod.long)
    if clean_ids.shape[1] != corrupted_ids.shape[1]:
        raise ValueError("clean and corrupted inputs tokenized to different lengths.")
    return clean_ids, corrupted_ids


def _softmax(logits: Any) -> Any:
    values = np.asarray(logits.detach().cpu().numpy(), dtype=np.float64).reshape(-1)
    shifted = values - values.max()
    exp = np.exp(shifted)
    return exp / exp.sum()


def _label(vocab: list[str], index: int) -> str | int:
    return vocab[index] if 0 <= index < len(vocab) else index


def _stable_seed(text: str) -> int:
    digest = hashlib.sha256(text.encode()).digest()
    return int.from_bytes(digest[:8], "big") % (2**32)
