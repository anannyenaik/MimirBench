"""Compact transformer for supervised synthetic Bayesian trace labels.

``torch`` is optional for MimirBench core imports. This module can be imported
without torch; constructing or loading the model raises a clear error only when
the training/inference path is actually invoked.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:  # pragma: no cover - availability is environment-dependent.
    import torch
    from torch import nn
    from torch.nn import functional as F
except ImportError:  # pragma: no cover - exercised by optional-dependency checks.
    torch = None  # type: ignore[assignment]
    nn = None  # type: ignore[assignment]
    F = None  # type: ignore[assignment]

__all__ = [
    "EMBED_SITE",
    "HEAD_NAMES",
    "SmallTransformerConfig",
    "SmallTransformerForTracePrediction",
    "attention_head_site_names",
    "attn_head_out_site",
    "attn_out_site",
    "interpretability_site_names",
    "mlp_out_site",
    "parameter_count",
    "require_torch",
    "resid_post_site",
]

HEAD_NAMES = (
    "posterior_bucket",
    "action",
    "ev_bucket",
    "risk_flag",
    "confidence_bucket",
    "rationale_class",
)

# Canonical names for the interpretability patch / capture sites. They mirror the
# transformer-lens convention so a reader familiar with that library can map them
# straight onto our hand-rolled encoder.
EMBED_SITE = "embed"


def attn_out_site(layer: int) -> str:
    """Name of the attention sub-block output of ``layer`` (pre-residual-add)."""
    return f"blocks.{layer}.attn_out"


def attn_head_out_site(layer: int, head: int) -> str:
    """Name of one head's projected contribution to an attention sub-block."""
    return f"blocks.{layer}.attn_heads.{head}.out"


def attention_head_site_names(n_layers: int, n_heads: int) -> tuple[str, ...]:
    """Ordered per-head attention-output patch/capture site names."""
    return tuple(
        attn_head_out_site(layer, head)
        for layer in range(n_layers)
        for head in range(n_heads)
    )


def mlp_out_site(layer: int) -> str:
    """Name of the MLP sub-block output of ``layer`` (pre-residual-add)."""
    return f"blocks.{layer}.mlp_out"


def resid_post_site(layer: int) -> str:
    """Name of the residual stream after ``layer`` (the block output)."""
    return f"blocks.{layer}.resid_post"


def interpretability_site_names(n_layers: int) -> tuple[str, ...]:
    """Ordered patch/capture site names for a model with ``n_layers`` blocks."""
    sites: list[str] = [EMBED_SITE]
    for layer in range(n_layers):
        sites.extend([attn_out_site(layer), mlp_out_site(layer), resid_post_site(layer)])
    return tuple(sites)

_HEAD_CONFIG_ATTRS = {
    "posterior_bucket": "num_posterior_buckets",
    "action": "num_actions",
    "ev_bucket": "num_ev_buckets",
    "risk_flag": "num_risk_flags",
    "confidence_bucket": "num_confidence_buckets",
    "rationale_class": "num_rationale_classes",
}


@dataclass(frozen=True)
class SmallTransformerConfig:
    """Architecture and output-head dimensions."""

    vocab_size: int
    max_seq_len: int = 128
    d_model: int = 64
    n_layers: int = 2
    n_heads: int = 2
    dim_feedforward: int = 128
    dropout: float = 0.0
    pad_token_id: int = 0
    num_posterior_buckets: int = 20
    num_actions: int = 2
    num_ev_buckets: int = 7
    num_risk_flags: int = 2
    num_confidence_buckets: int = 3
    num_rationale_classes: int = 4
    lm_loss_weight: float = 0.0

    def validate(self) -> None:
        if self.vocab_size <= 0:
            raise ValueError("vocab_size must be positive.")
        if self.max_seq_len <= 0:
            raise ValueError("max_seq_len must be positive.")
        if self.d_model <= 0 or self.n_layers <= 0 or self.n_heads <= 0:
            raise ValueError("d_model, n_layers, and n_heads must be positive.")
        if self.d_model % self.n_heads != 0:
            raise ValueError("d_model must be divisible by n_heads.")
        for name, attr in _HEAD_CONFIG_ATTRS.items():
            if int(getattr(self, attr)) <= 0:
                raise ValueError(f"{name} output head must have at least one label.")


def require_torch() -> tuple[Any, Any, Any]:
    """Return torch modules or raise the project-standard optional-dependency error."""
    if torch is None or nn is None or F is None:
        raise ImportError(
            'small-transformer training/inference requires the "ml" extra. '
            'Install it with: pip install -e ".[ml]"'
        )
    return torch, nn, F


_TORCH_BASE: Any = nn.Module if nn is not None else object


class SmallTransformerForTracePrediction(_TORCH_BASE):  # type: ignore[misc]
    """A tiny encoder-style transformer with one classification head per label."""

    def __init__(
        self,
        config: SmallTransformerConfig,
        *,
        label_vocab: dict[str, list[str]] | None = None,
    ) -> None:
        torch_mod, nn_mod, _ = require_torch()
        super().__init__()
        config.validate()
        self.config = config
        self.label_vocab = label_vocab or {}
        self.token_embedding = nn_mod.Embedding(config.vocab_size, config.d_model)
        self.position_embedding = nn_mod.Embedding(config.max_seq_len, config.d_model)
        layer = nn_mod.TransformerEncoderLayer(
            d_model=config.d_model,
            nhead=config.n_heads,
            dim_feedforward=config.dim_feedforward,
            dropout=config.dropout,
            batch_first=True,
            activation="gelu",
        )
        self.encoder = nn_mod.TransformerEncoder(layer, num_layers=config.n_layers)
        self.dropout = nn_mod.Dropout(config.dropout)
        self.lm_head = nn_mod.Linear(config.d_model, config.vocab_size)
        self.heads = nn_mod.ModuleDict(
            {
                head: nn_mod.Linear(config.d_model, int(getattr(config, attr)))
                for head, attr in _HEAD_CONFIG_ATTRS.items()
            }
        )
        self._torch = torch_mod

    def forward(
        self,
        input_ids: Any,
        attention_mask: Any | None = None,
        labels: dict[str, Any] | None = None,
        lm_labels: Any | None = None,
    ) -> dict[str, Any]:
        """Run the model and optionally compute supervised losses."""
        torch_mod, _, functional = require_torch()
        if input_ids.ndim != 2:
            raise ValueError("input_ids must have shape (batch, seq_len).")
        batch_size, seq_len = input_ids.shape
        if seq_len > self.config.max_seq_len:
            raise ValueError(
                f"sequence length {seq_len} exceeds max_seq_len={self.config.max_seq_len}."
            )
        if attention_mask is None:
            attention_mask = (input_ids != self.config.pad_token_id).long()

        positions = torch_mod.arange(seq_len, device=input_ids.device).unsqueeze(0)
        hidden = self.token_embedding(input_ids) + self.position_embedding(positions)
        hidden = self.dropout(hidden)
        key_padding_mask = attention_mask == 0
        encoded = self.encoder(hidden, src_key_padding_mask=key_padding_mask)
        pooled = _masked_mean(encoded, attention_mask)
        logits = {head: layer(pooled) for head, layer in self.heads.items()}
        lm_logits = self.lm_head(encoded)

        output: dict[str, Any] = {
            "logits": logits,
            "lm_logits": lm_logits,
            "pooled": pooled,
        }
        losses: dict[str, Any] = {}
        if labels is not None:
            for head, target in labels.items():
                if head not in logits:
                    raise ValueError(f"unknown supervised head {head!r}.")
                losses[head] = functional.cross_entropy(logits[head], target)
        if lm_labels is not None and self.config.lm_loss_weight > 0.0:
            lm_loss = functional.cross_entropy(
                lm_logits.reshape(batch_size * seq_len, self.config.vocab_size),
                lm_labels.reshape(batch_size * seq_len),
                ignore_index=self.config.pad_token_id,
            )
            losses["lm"] = lm_loss * self.config.lm_loss_weight
        if losses:
            output["losses"] = losses
            output["loss"] = sum(losses.values())
        return output

    def forward_instrumented(
        self,
        input_ids: Any,
        attention_mask: Any | None = None,
        *,
        patch: Mapping[str, Any] | None = None,
        patch_positions: Mapping[str, Sequence[int]] | None = None,
        capture_attention: bool = True,
    ) -> dict[str, Any]:
        """Run a hand-rolled encoder pass that exposes interpretability hooks.

        Unlike :meth:`forward`, which uses ``nn.TransformerEncoder`` (and its fused
        kernels), this path computes each encoder block explicitly so it can:

        * return the residual stream after every block and the embedding output;
        * return per-head attention weights and projected per-head outputs;
        * optionally *patch* a named activation site with externally supplied
          values (the substrate for activation-patching experiments).

        At all non-padded positions this reproduces :meth:`forward` to within
        floating-point tolerance (verified in tests); padded positions are masked
        out of pooling either way. The default training path is untouched.
        """
        torch_mod, _, _ = require_torch()
        if input_ids.ndim != 2:
            raise ValueError("input_ids must have shape (batch, seq_len).")
        _, seq_len = input_ids.shape
        if seq_len > self.config.max_seq_len:
            raise ValueError(
                f"sequence length {seq_len} exceeds max_seq_len={self.config.max_seq_len}."
            )
        if attention_mask is None:
            attention_mask = (input_ids != self.config.pad_token_id).long()
        key_padding_mask = attention_mask == 0

        positions = torch_mod.arange(seq_len, device=input_ids.device).unsqueeze(0)
        hidden = self.token_embedding(input_ids) + self.position_embedding(positions)
        hidden = self.dropout(hidden)
        hidden = _apply_site_patch(torch_mod, hidden, EMBED_SITE, patch, patch_positions)

        sites: dict[str, Any] = {EMBED_SITE: hidden}
        hidden_states: list[Any] = [hidden]
        attentions: list[Any] = []
        attention_head_outputs: list[Any] = []

        x = hidden
        for layer_index, layer in enumerate(self.encoder.layers):
            attn_input = layer.norm1(x) if layer.norm_first else x
            head_outputs, attn_weights = _projected_attention_head_outputs(
                torch_mod,
                layer.self_attn,
                attn_input,
                key_padding_mask,
                capture_attention=capture_attention,
            )
            patched_head_outputs: list[Any] = []
            for head_index in range(self.config.n_heads):
                site = attn_head_out_site(layer_index, head_index)
                head_output = _apply_site_patch(
                    torch_mod,
                    head_outputs[:, head_index, :, :],
                    site,
                    patch,
                    patch_positions,
                )
                sites[site] = head_output
                patched_head_outputs.append(head_output)
            stacked_head_outputs = torch_mod.stack(patched_head_outputs, dim=1)
            attention_head_outputs.append(stacked_head_outputs)
            attn_out = stacked_head_outputs.sum(dim=1)
            if layer.self_attn.out_proj.bias is not None:
                attn_out = attn_out + layer.self_attn.out_proj.bias
            attn_out = _apply_site_patch(
                torch_mod, attn_out, attn_out_site(layer_index), patch, patch_positions
            )
            sites[attn_out_site(layer_index)] = attn_out
            if capture_attention and attn_weights is not None:
                attentions.append(attn_weights)
            if layer.norm_first:
                resid_mid = x + attn_out
                mlp_in = layer.norm2(resid_mid)
                mlp_out = layer.linear2(layer.activation(layer.linear1(mlp_in)))
                mlp_out = _apply_site_patch(
                    torch_mod, mlp_out, mlp_out_site(layer_index), patch, patch_positions
                )
                sites[mlp_out_site(layer_index)] = mlp_out
                resid_post = resid_mid + mlp_out
            else:
                resid_mid = layer.norm1(x + attn_out)
                mlp_out = layer.linear2(layer.activation(layer.linear1(resid_mid)))
                mlp_out = _apply_site_patch(
                    torch_mod, mlp_out, mlp_out_site(layer_index), patch, patch_positions
                )
                sites[mlp_out_site(layer_index)] = mlp_out
                resid_post = layer.norm2(resid_mid + mlp_out)
            resid_post = _apply_site_patch(
                torch_mod, resid_post, resid_post_site(layer_index), patch, patch_positions
            )
            sites[resid_post_site(layer_index)] = resid_post
            hidden_states.append(resid_post)
            x = resid_post

        pooled = _masked_mean(x, attention_mask)
        logits = {head: head_layer(pooled) for head, head_layer in self.heads.items()}
        return {
            "logits": logits,
            "pooled": pooled,
            "hidden_states": tuple(hidden_states),
            "attentions": tuple(attentions),
            "attention_head_outputs": tuple(attention_head_outputs),
            "sites": sites,
            "attention_mask": attention_mask,
        }

    def predict(self, input_ids: Any, attention_mask: Any | None = None) -> dict[str, str | int]:
        """Return argmax predictions, mapped to label strings when available."""
        torch_mod, _, _ = require_torch()
        if not hasattr(input_ids, "ndim"):
            input_ids = torch_mod.as_tensor(input_ids, dtype=torch_mod.long)
        if input_ids.ndim == 1:
            input_ids = input_ids.unsqueeze(0)
        if attention_mask is not None and not hasattr(attention_mask, "ndim"):
            attention_mask = torch_mod.as_tensor(attention_mask, dtype=torch_mod.long)
        if attention_mask is not None and attention_mask.ndim == 1:
            attention_mask = attention_mask.unsqueeze(0)

        self.eval()
        with torch_mod.no_grad():
            output = self.forward(input_ids, attention_mask=attention_mask)
        predictions: dict[str, str | int] = {}
        for head, logits in output["logits"].items():
            label_id = int(logits.argmax(dim=-1)[0].item())
            labels = self.label_vocab.get(head, [])
            predictions[head] = labels[label_id] if 0 <= label_id < len(labels) else label_id
        return predictions

    def save_checkpoint(
        self,
        path: str | Path,
        *,
        tokenizer: Any | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Path:
        """Save model weights, config, label vocab, tokenizer, and metadata."""
        torch_mod, _, _ = require_torch()
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        tokenizer_payload: Any = None
        if tokenizer is not None:
            to_dict = getattr(tokenizer, "to_dict", None)
            tokenizer_payload = to_dict() if callable(to_dict) else tokenizer
        torch_mod.save(
            {
                "format_version": 1,
                "model_config": asdict(self.config),
                "label_vocab": self.label_vocab,
                "tokenizer": tokenizer_payload,
                "state_dict": self.state_dict(),
                "metadata": metadata or {},
            },
            output,
        )
        return output

    @classmethod
    def load_checkpoint(
        cls,
        path: str | Path,
        *,
        map_location: str | None = "cpu",
    ) -> tuple[SmallTransformerForTracePrediction, dict[str, Any]]:
        """Load a checkpoint and return ``(model, payload)``."""
        torch_mod, _, _ = require_torch()
        payload = torch_mod.load(Path(path), map_location=map_location)
        if not isinstance(payload, dict):
            raise ValueError("checkpoint payload must be a dictionary.")
        config_data = payload.get("model_config")
        if not isinstance(config_data, dict):
            raise ValueError("checkpoint is missing model_config.")
        label_vocab = payload.get("label_vocab")
        if not isinstance(label_vocab, dict):
            label_vocab = {}
        model = cls(
            SmallTransformerConfig(**config_data),
            label_vocab={str(key): list(value) for key, value in label_vocab.items()},
        )
        state_dict = payload.get("state_dict")
        if state_dict is None:
            raise ValueError("checkpoint is missing state_dict.")
        model.load_state_dict(state_dict)
        return model, payload


def parameter_count(model: Any) -> int:
    """Return the number of trainable and frozen parameters in a torch module."""
    require_torch()
    return int(sum(parameter.numel() for parameter in model.parameters()))


def _masked_mean(encoded: Any, attention_mask: Any) -> Any:
    mask = attention_mask.unsqueeze(-1).to(encoded.dtype)
    summed = (encoded * mask).sum(dim=1)
    counts = mask.sum(dim=1).clamp(min=1.0)
    return summed / counts


def _projected_attention_head_outputs(
    torch_mod: Any,
    attention: Any,
    hidden: Any,
    key_padding_mask: Any,
    *,
    capture_attention: bool,
) -> tuple[Any, Any | None]:
    """Return each head's projected contribution and optional attention weights."""
    _, _, functional = require_torch()
    if attention.in_proj_weight is None:
        raise ValueError("instrumented attention requires a combined in_proj_weight.")
    batch_size, seq_len, embed_dim = hidden.shape
    n_heads = int(attention.num_heads)
    head_dim = embed_dim // n_heads
    qkv = functional.linear(hidden, attention.in_proj_weight, attention.in_proj_bias)
    query, key, value = qkv.chunk(3, dim=-1)

    def split_heads(tensor: Any) -> Any:
        return tensor.reshape(batch_size, seq_len, n_heads, head_dim).transpose(1, 2)

    query = split_heads(query) * (head_dim**-0.5)
    key = split_heads(key)
    value = split_heads(value)
    scores = torch_mod.matmul(query, key.transpose(-2, -1))
    scores = scores.masked_fill(key_padding_mask[:, None, None, :], float("-inf"))
    weights = functional.softmax(scores, dim=-1)
    if attention.dropout > 0.0:
        weights = functional.dropout(weights, p=float(attention.dropout), training=attention.training)
    values = torch_mod.matmul(weights, value)

    projected: list[Any] = []
    for head in range(n_heads):
        start = head * head_dim
        stop = start + head_dim
        projected.append(
            functional.linear(values[:, head, :, :], attention.out_proj.weight[:, start:stop])
        )
    return torch_mod.stack(projected, dim=1), weights if capture_attention else None


def _apply_site_patch(
    torch_mod: Any,
    value: Any,
    site: str,
    patch: Mapping[str, Any] | None,
    patch_positions: Mapping[str, Sequence[int]] | None,
) -> Any:
    """Return ``value`` with the patched site substituted in (optionally per-position)."""
    if patch is None or site not in patch:
        return value
    replacement = torch_mod.as_tensor(patch[site], dtype=value.dtype, device=value.device)
    if replacement.ndim == 2:
        replacement = replacement.unsqueeze(0)
    if replacement.shape[0] == 1 and value.shape[0] != 1:
        replacement = replacement.expand_as(value)
    positions = None if patch_positions is None else patch_positions.get(site)
    if positions is None:
        if replacement.shape != value.shape:
            raise ValueError(
                f"patch for site {site!r} has shape {tuple(replacement.shape)}, "
                f"expected {tuple(value.shape)}."
            )
        return replacement
    index = torch_mod.as_tensor(list(positions), dtype=torch_mod.long, device=value.device)
    patched = value.clone()
    patched[:, index, :] = replacement[:, index, :]
    return patched
