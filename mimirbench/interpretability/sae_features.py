"""Sparse autoencoder (SAE) feature extraction scaffold (optional future work).

Training SAEs on the small models' residual stream to look for monosemantic
"evidence accumulation" or "risk-limit" features is an explicitly *optional*,
later-stage direction. Only the configuration surface is defined here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = ["SAEConfig", "train_sae"]


@dataclass(frozen=True)
class SAEConfig:
    """Hyperparameters for a sparse autoencoder over a model's activations."""

    d_input: int
    expansion_factor: int = 8
    l1_coefficient: float = 1e-3
    learning_rate: float = 1e-3
    steps: int = 10_000
    seed: int = 0

    @property
    def d_hidden(self) -> int:
        return self.d_input * self.expansion_factor


def train_sae(activations: Any, config: SAEConfig) -> Any:  # pragma: no cover - optional future work
    """Planned (optional): train a sparse autoencoder on cached activations."""
    raise NotImplementedError(
        "SAE training is optional future work; see INTERPRETABILITY.md."
    )
