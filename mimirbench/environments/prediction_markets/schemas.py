"""Typed structures for prediction-market tasks."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "PredictionMarketAction",
    "PredictionMarketParams",
    "PredictionMarketTaskParams",
    "ProbabilityForecast",
]

Signal = Literal["positive", "negative", "neutral"]
MarketAction = Literal["buy", "sell", "abstain"]


class PredictionMarketTaskParams(BaseModel):
    """Public binary prediction-market decision task parameters."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    event_description: str
    current_market_price: float = Field(ge=0, le=1)
    private_signal: Signal
    private_signal_reliability: float = Field(ge=0.5, le=0.99)
    prior_probability: float = Field(ge=0.001, le=0.999)
    market_impact_parameter: float = Field(gt=0)
    transaction_cost: float = Field(default=0.01, ge=0)
    public_evidence: list[str] = Field(default_factory=list)
    position_limit: float = Field(gt=0)
    budget_limit: float = Field(gt=0)
    current_position: float = 0.0


class PredictionMarketAction(BaseModel):
    """Agent response for a binary prediction-market decision."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: MarketAction
    target_position: float | None = None
    trade_size: float = Field(default=0.0, ge=0)
    fair_probability: float = Field(ge=0, le=1)
    expected_value: float
    confidence: float | None = Field(default=None, ge=0, le=1)
    reasoning_summary: str | None = None


class PredictionMarketParams(BaseModel):
    """Public problem statement for a prediction-market task.

    This legacy multiclass forecast schema is kept for the LMSR/proper-scoring
    helpers. Runner tasks use :class:`PredictionMarketTaskParams`.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    question: str
    outcome_names: list[str]
    market_prices: list[float]


class ProbabilityForecast(BaseModel):
    """A calibrated probability forecast over mutually-exclusive outcomes."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    probabilities: list[float]
