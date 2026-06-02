"""Typed parameters and solution for hidden-regime (HMM) tasks."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = ["HiddenRegimeParams", "RegimeSolution"]


class HiddenRegimeParams(BaseModel):
    """Public problem statement for a hidden-regime filtering task.

    A discrete hidden Markov model: ``initial`` is the prior over the first
    regime, ``transition[i][j] = P(regime_t = j | regime_{t-1} = i)``, and
    ``emission[i][k] = P(signal_k | regime = i)``.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    regime_names: list[str]
    signal_names: list[str]
    initial: list[float]
    transition: list[list[float]]
    emission: list[list[float]]
    observations: list[int]

    @property
    def n_regimes(self) -> int:
        return len(self.regime_names)

    @property
    def n_signals(self) -> int:
        return len(self.signal_names)


class RegimeSolution(BaseModel):
    """The graded answer: the filtered belief over the regime at the final step."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    regime_posterior: list[float] = Field(
        description="P(regime_T | observations_1..T), one probability per regime."
    )
