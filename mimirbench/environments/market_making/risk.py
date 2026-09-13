"""Market-making risk helpers built on the shared risk checker."""

from __future__ import annotations

from mimirbench.tools.risk_checker import RiskCheckResult, RiskLimits, RiskState, check_risk

__all__ = ["check_inventory", "would_breach"]


def check_inventory(inventory: float, limits: RiskLimits) -> RiskCheckResult:
    """Check a standing inventory against the hard limits (no new trade)."""
    return check_risk(RiskState(position=inventory), limits, proposed_trade=0.0)


def would_breach(inventory: float, trade: float, limits: RiskLimits) -> bool:
    """Return ``True`` if adding ``trade`` to ``inventory`` would breach a limit."""
    return not check_risk(RiskState(position=inventory), limits, proposed_trade=trade).ok
