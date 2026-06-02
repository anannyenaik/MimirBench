"""Typed parameters and solution for Bayesian-updating tasks."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = ["BayesianSolution", "BayesianTaskParams"]


class BayesianTaskParams(BaseModel):
    """The public problem statement for a Bayesian-updating task.

    Stored in :attr:`Task.metadata` so reference solvers and tool-using agents
    can operate on structured inputs rather than re-parsing the prompt.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    hypothesis_names: list[str]
    signal_names: list[str]
    priors: list[float]
    likelihood: list[list[float]]
    observations: list[int]

    @property
    def n_hypotheses(self) -> int:
        return len(self.hypothesis_names)

    @property
    def n_signals(self) -> int:
        return len(self.signal_names)


class BayesianSolution(BaseModel):
    """The graded answer for a Bayesian-updating task."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    posterior: list[float] = Field(description="Posterior probability per hypothesis, in order.")
