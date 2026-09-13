"""Attention-pattern summaries.

The low-level utilities (:func:`attention_entropy`, :func:`previous_token_score`,
:func:`attention_group_mass`) are dependency-free and run on plain arrays, so they
work the same whether the attention came from ``transformer_lens`` or our
hand-rolled encoder. :func:`run_attention_analysis` is the project driver: it
groups input tokens into prior / likelihood / evidence / payoff-risk spans and
reports, per layer and head, how much attention mass each group receives and how
diffuse each head is. Torch is imported lazily so the module stays import-light.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import numpy.typing as npt

__all__ = [
    "TOKEN_GROUPS",
    "AttentionAnalysisResult",
    "attention_entropy",
    "attention_group_mass",
    "previous_token_score",
    "run_attention_analysis",
    "token_group_spans",
]

# The semantic spans of a synthetic Bayesian trace, in input order. Each maps to
# the section keyword that opens it.
TOKEN_GROUPS: tuple[tuple[str, str], ...] = (
    ("prior", "prior"),
    ("likelihood", "likelihood"),
    ("evidence", "observations"),
    ("payoff_risk", "payoff"),
)


def _validate_attention(attention: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    a = np.asarray(attention, dtype=np.float64)
    if a.ndim != 2 or a.shape[0] != a.shape[1]:
        raise ValueError("attention must be a square (seq_len, seq_len) matrix.")
    if np.any(a < -1e-9):
        raise ValueError("attention weights must be non-negative.")
    return a


def attention_entropy(attention: npt.NDArray[np.float64], *, eps: float = 1e-12) -> npt.NDArray[np.float64]:
    """Shannon entropy (in nats) of each query row's attention distribution."""
    a = _validate_attention(attention)
    row_sums = a.sum(axis=1, keepdims=True)
    probs = a / np.clip(row_sums, eps, None)
    return -np.sum(probs * np.log(np.clip(probs, eps, None)), axis=1)


def previous_token_score(attention: npt.NDArray[np.float64]) -> float:
    """Average attention mass placed on the immediately preceding token.

    A high score is the signature of an induction-style "previous token" head.
    The first query (no previous token) is excluded.
    """
    a = _validate_attention(attention)
    if a.shape[0] < 2:
        return 0.0
    diag = np.diagonal(a, offset=-1)
    return float(diag.mean())


def attention_group_mass(
    attention: npt.NDArray[np.float64],
    group_positions: Sequence[int],
    *,
    query_positions: Sequence[int] | None = None,
) -> float:
    """Mean attention mass that ``query_positions`` place on ``group_positions``.

    ``attention`` is a normalised ``(seq, seq)`` matrix. Rows are queries, columns
    keys. Returns the average over the selected query rows of the summed weight on
    the group's key columns.
    """
    a = _validate_attention(attention)
    keys = [p for p in group_positions if 0 <= p < a.shape[1]]
    queries = (
        list(range(a.shape[0]))
        if query_positions is None
        else [q for q in query_positions if 0 <= q < a.shape[0]]
    )
    if not keys or not queries:
        return 0.0
    block = a[np.ix_(queries, keys)]
    return float(block.sum(axis=1).mean())


def token_group_spans(tokens: Sequence[str], *, offset: int = 0) -> dict[str, list[int]]:
    """Map each :data:`TOKEN_GROUPS` span to the token indices it covers.

    ``offset`` shifts every index (use ``offset=1`` when a BOS token was prepended
    during encoding). A span runs from its keyword up to the next group's keyword.
    """
    starts: list[tuple[str, int]] = []
    for group, keyword in TOKEN_GROUPS:
        index = _first_index(tokens, keyword)
        if index is not None:
            starts.append((group, index))
    starts.sort(key=lambda item: item[1])
    spans: dict[str, list[int]] = {group: [] for group, _ in TOKEN_GROUPS}
    for position, (group, start) in enumerate(starts):
        end = starts[position + 1][1] if position + 1 < len(starts) else len(tokens)
        spans[group] = [index + offset for index in range(start, end)]
    return spans


@dataclass(frozen=True)
class AttentionAnalysisResult:
    """Aggregated attention statistics plus per-example records."""

    summary: dict[str, Any]
    examples: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)


def run_attention_analysis(
    model: Any,
    tokenizer: Any,
    traces: Sequence[Mapping[str, Any]],
    *,
    max_examples: int | None = None,
    top_k: int = 5,
    metadata: Mapping[str, Any] | None = None,
) -> AttentionAnalysisResult:
    """Summarise attention over token groups for the small transformer.

    For every trace we run the instrumented forward, group the input tokens into
    prior / likelihood / evidence / payoff-risk spans, and record, per layer and
    head, the attention entropy and the mass placed on each group (averaged over
    un-padded query positions). Aggregates are means over the analysed traces.
    """
    from mimirbench.training.small_transformer import require_torch

    torch_mod, _, _ = require_torch()
    selected = list(traces) if max_examples is None else list(traces)[:max_examples]
    if not selected:
        raise ValueError("no traces to analyse.")

    per_layer_head: dict[tuple[int, int], dict[str, list[float]]] = {}
    examples: list[dict[str, Any]] = []
    model.eval()
    for trace in selected:
        text = trace.get("input")
        if not isinstance(text, str):
            raise ValueError("trace is missing a string 'input'.")
        encoded = tokenizer.encode(text)
        input_ids = torch_mod.as_tensor([encoded["input_ids"]], dtype=torch_mod.long)
        mask = np.asarray(encoded["attention_mask"], dtype=np.int64)
        valid = [int(i) for i in np.nonzero(mask)[0]]
        token_strings = tokenizer.tokenize(text)
        spans = token_group_spans(token_strings, offset=1)  # +1 for the BOS token
        id_tokens = tokenizer.decode(encoded["input_ids"], skip_special=False).split(" ")

        with torch_mod.no_grad():
            output = model.forward_instrumented(input_ids, capture_attention=True)
        attentions = output["attentions"]
        example: dict[str, Any] = {
            "trace_id": trace.get("id"),
            "n_tokens": len(valid),
            "layers": [],
        }
        for layer_index, layer_attn in enumerate(attentions):
            heads = layer_attn.shape[1]
            layer_record: dict[str, Any] = {"layer": layer_index, "heads": []}
            for head in range(heads):
                matrix = np.asarray(layer_attn[0, head].detach().cpu().numpy(), dtype=np.float64)
                entropy = float(attention_entropy(matrix)[valid].mean()) if valid else 0.0
                group_mass = {
                    group: attention_group_mass(matrix, positions, query_positions=valid)
                    for group, positions in spans.items()
                }
                top_positions = _top_positions(matrix, valid, id_tokens, top_k)
                key = (layer_index, head)
                bucket = per_layer_head.setdefault(
                    key, {"entropy": [], **{group: [] for group, _ in TOKEN_GROUPS}}
                )
                bucket["entropy"].append(entropy)
                for group, _ in TOKEN_GROUPS:
                    bucket[group].append(group_mass[group])
                layer_record["heads"].append(
                    {
                        "head": head,
                        "mean_entropy": entropy,
                        "group_mass": group_mass,
                        "top_attended": top_positions,
                    }
                )
            example["layers"].append(layer_record)
        examples.append(example)

    summary = _aggregate_attention(per_layer_head, n_examples=len(selected))
    return AttentionAnalysisResult(
        summary=summary,
        examples=examples,
        metadata={"num_examples": len(selected), **dict(metadata or {})},
    )


def _aggregate_attention(
    per_layer_head: dict[tuple[int, int], dict[str, list[float]]],
    *,
    n_examples: int,
) -> dict[str, Any]:
    layers: dict[int, list[dict[str, Any]]] = {}
    for (layer_index, head), values in sorted(per_layer_head.items()):
        record = {
            "head": head,
            "mean_entropy": float(np.mean(values["entropy"])) if values["entropy"] else 0.0,
            "group_mass": {
                group: float(np.mean(values[group])) if values[group] else 0.0
                for group, _ in TOKEN_GROUPS
            },
        }
        layers.setdefault(layer_index, []).append(record)

    by_layer: dict[str, Any] = {}
    for layer_index, head_records in sorted(layers.items()):
        by_layer[str(layer_index)] = {
            "heads": head_records,
            "mean_entropy": float(np.mean([r["mean_entropy"] for r in head_records])),
            "mean_group_mass": {
                group: float(np.mean([r["group_mass"][group] for r in head_records]))
                for group, _ in TOKEN_GROUPS
            },
        }
    return {
        "by_layer": by_layer,
        "n_examples": n_examples,
        "groups": [group for group, _ in TOKEN_GROUPS],
    }


def _top_positions(
    matrix: npt.NDArray[np.float64],
    valid: Sequence[int],
    id_tokens: Sequence[str],
    top_k: int,
) -> list[dict[str, Any]]:
    if not valid:
        return []
    incoming = matrix[np.ix_(list(valid), list(valid))].sum(axis=0)
    order = np.argsort(incoming)[::-1][:top_k]
    result: list[dict[str, Any]] = []
    for rank in order:
        position = int(valid[int(rank)])
        token = id_tokens[position] if 0 <= position < len(id_tokens) else "?"
        result.append({"position": position, "token": token, "incoming_mass": float(incoming[int(rank)])})
    return result


def _first_index(tokens: Sequence[str], keyword: str) -> int | None:
    for index, token in enumerate(tokens):
        if token == keyword:
            return index
    return None
