"""Deterministic risk checker for trading-style environments.

The checker is intentionally simple and explicit: given the current risk state
and a proposed trade, it reports which hard limits would be breached. It is used
by the market-making and adversarial-risk environments (to grade constraint
obedience) and is exposed as the ``risk_checker`` agent tool.

Three independent constraints are modelled:

* **position limit**: a symmetric cap on the absolute net position
  (``|position| <= max_abs_position``);
* **loss limit**: a floor on realized PnL (``realized_pnl >= -max_loss``);
* **inventory bounds**: an explicit, possibly asymmetric range the position
  must stay within (``min_inventory <= position <= max_inventory``).

The position limit and inventory bounds overlap intentionally: a desk often has
both a symmetric risk cap and an asymmetric operational inventory band, and a
trade can violate one without the other.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

__all__ = [
    "RiskCheckResult",
    "RiskLimits",
    "RiskState",
    "Violation",
    "check_risk",
]


class Violation(StrEnum):
    """Canonical names for the risk constraints that can be breached."""

    POSITION_LIMIT = "position_limit"
    LOSS_LIMIT = "loss_limit"
    INVENTORY_BOUNDS = "inventory_bounds"


class RiskLimits(BaseModel):
    """Hard risk limits for a single instrument."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_abs_position: float = Field(gt=0, description="Cap on |position|.")
    max_loss: float = Field(ge=0, description="Maximum tolerated realized loss (a positive number).")
    min_inventory: float = Field(default=float("-inf"), description="Lower inventory bound.")
    max_inventory: float = Field(default=float("inf"), description="Upper inventory bound.")

    @model_validator(mode="after")
    def _check_bounds(self) -> RiskLimits:
        if self.min_inventory > self.max_inventory:
            raise ValueError(
                f"min_inventory ({self.min_inventory}) exceeds "
                f"max_inventory ({self.max_inventory})."
            )
        return self


class RiskState(BaseModel):
    """The current risk-relevant state of a book."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    position: float = 0.0
    realized_pnl: float = 0.0


class RiskCheckResult(BaseModel):
    """The outcome of a risk check for a single proposed trade."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    ok: bool
    resulting_position: float
    violations: list[Violation] = Field(default_factory=list)

    @property
    def violation_names(self) -> list[str]:
        """Violation values as plain strings (handy for :class:`GraderResult`)."""
        return [v.value for v in self.violations]


def check_risk(
    state: RiskState,
    limits: RiskLimits,
    proposed_trade: float = 0.0,
) -> RiskCheckResult:
    """Check whether ``proposed_trade`` keeps the book within all hard limits.

    Args:
        state: Current position and realized PnL.
        limits: Hard risk limits to enforce.
        proposed_trade: Signed size to add to the current position (0 checks the
            standing book only).

    Returns:
        A :class:`RiskCheckResult` listing every breached constraint. The result
        is ``ok`` iff there are no violations.
    """
    resulting_position = state.position + proposed_trade
    violations: list[Violation] = []

    if abs(resulting_position) > limits.max_abs_position:
        violations.append(Violation.POSITION_LIMIT)

    if state.realized_pnl < -limits.max_loss:
        violations.append(Violation.LOSS_LIMIT)

    if not (limits.min_inventory <= resulting_position <= limits.max_inventory):
        violations.append(Violation.INVENTORY_BOUNDS)

    return RiskCheckResult(
        ok=not violations,
        resulting_position=resulting_position,
        violations=violations,
    )
