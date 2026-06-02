"""Typed structures for adversarial risk-control tasks."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ADVERSARIAL_PRESSURE_TYPES",
    "AdversarialRiskAction",
    "AdversarialRiskParams",
    "PressureType",
]

RiskAction = Literal["approve", "reject", "reduce_size", "abstain"]


class PressureType(StrEnum):
    """Domain-specific pressure variants for risk-control tasks."""

    AUTHORITY_PRESSURE = "authority_pressure"
    URGENCY = "urgency"
    LOSS_CHASING = "loss_chasing"
    FAKE_INSIDER_SIGNAL = "fake_insider_signal"
    EMOTIONAL_PRESSURE = "emotional_pressure"
    IGNORE_PREVIOUS_CONSTRAINTS = "ignore_previous_constraints"
    FAKE_SYSTEM_STATUS = "fake_system_status"
    RECENT_WIN_BIAS = "recent_win_bias"
    CONFIDENT_IRRELEVANT_ANALYST_CLAIM = "confident_but_irrelevant_analyst_claim"


ADVERSARIAL_PRESSURE_TYPES: tuple[PressureType, ...] = tuple(PressureType)


class AdversarialRiskParams(BaseModel):
    """Public problem statement for an adversarial risk-control task."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    base_decision_problem: str
    risk_policy: str
    current_exposure: float
    current_loss: float = Field(ge=0)
    proposed_trade: float
    maximum_allowed_exposure: float = Field(gt=0)
    maximum_allowed_daily_loss: float = Field(ge=0)
    adversarial_pressure_type: PressureType
    adversarial_text: str


class AdversarialRiskAction(BaseModel):
    """Agent response for risk-control decisions under pressure."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: RiskAction
    proposed_size: float = Field(default=0.0, ge=0)
    risk_policy_followed: bool
    cited_constraint: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    reasoning_summary: str | None = None
