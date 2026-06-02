"""Tests for the deterministic risk checker."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from mimirbench.tools.risk_checker import RiskLimits, RiskState, Violation, check_risk

LIMITS = RiskLimits(max_abs_position=10.0, max_loss=100.0, min_inventory=-5.0, max_inventory=8.0)


def test_trade_within_limits_is_ok() -> None:
    result = check_risk(RiskState(position=0.0, realized_pnl=0.0), LIMITS, proposed_trade=3.0)
    assert result.ok
    assert result.violations == []
    assert result.resulting_position == 3.0


def test_position_limit_violation() -> None:
    limits = RiskLimits(max_abs_position=5.0, max_loss=100.0)  # inventory bounds default to +/-inf
    result = check_risk(RiskState(position=4.0), limits, proposed_trade=3.0)  # -> 7 > 5
    assert not result.ok
    assert Violation.POSITION_LIMIT in result.violations
    assert Violation.INVENTORY_BOUNDS not in result.violations


def test_loss_limit_violation() -> None:
    result = check_risk(RiskState(position=0.0, realized_pnl=-150.0), LIMITS, proposed_trade=0.0)
    assert Violation.LOSS_LIMIT in result.violations


def test_inventory_upper_bound_violation_without_position_limit() -> None:
    # 7 + 3 = 10: equals max_abs_position (not a position breach) but exceeds max_inventory=8.
    result = check_risk(RiskState(position=7.0), LIMITS, proposed_trade=3.0)
    assert Violation.INVENTORY_BOUNDS in result.violations
    assert Violation.POSITION_LIMIT not in result.violations


def test_inventory_lower_bound_violation() -> None:
    result = check_risk(RiskState(position=-3.0), LIMITS, proposed_trade=-3.0)  # -> -6 < -5
    assert Violation.INVENTORY_BOUNDS in result.violations


def test_violation_names_are_plain_strings() -> None:
    result = check_risk(RiskState(position=0.0, realized_pnl=-150.0), LIMITS)
    assert "loss_limit" in result.violation_names


def test_inconsistent_inventory_bounds_rejected() -> None:
    with pytest.raises(ValidationError):
        RiskLimits(max_abs_position=10.0, max_loss=10.0, min_inventory=5.0, max_inventory=1.0)
