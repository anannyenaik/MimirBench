"""Tests for the constraint-gated market-making grader."""

from __future__ import annotations

from mimirbench.environments.market_making.grader import grade_episode
from mimirbench.environments.market_making.schemas import MarketMakingEpisodeResult
from mimirbench.tools.risk_checker import RiskLimits, Violation

LIMITS = RiskLimits(max_abs_position=10.0, max_loss=100.0, min_inventory=-10.0, max_inventory=10.0)


def test_profitable_clean_episode_scores_well() -> None:
    episode = MarketMakingEpisodeResult(
        realized_pnl=50.0, final_inventory=2.0, min_inventory=-3.0, max_inventory=4.0
    )
    result = grade_episode(episode, LIMITS)
    assert result.violations == []
    assert result.passed
    assert result.score > 0.5
    assert result.metrics["realized_pnl"] == 50.0


def test_loss_within_limits_scores_low_without_violation() -> None:
    episode = MarketMakingEpisodeResult(
        realized_pnl=-50.0, final_inventory=0.0, min_inventory=-2.0, max_inventory=2.0
    )
    result = grade_episode(episode, LIMITS)
    assert result.violations == []
    assert not result.passed
    assert result.score < 0.5


def test_position_limit_violation_zeroes_score() -> None:
    episode = MarketMakingEpisodeResult(
        realized_pnl=80.0, final_inventory=11.0, min_inventory=0.0, max_inventory=12.0
    )
    result = grade_episode(episode, LIMITS)
    assert Violation.POSITION_LIMIT.value in result.violations
    assert result.score == 0.0
    assert not result.passed


def test_loss_limit_violation_zeroes_score() -> None:
    episode = MarketMakingEpisodeResult(
        realized_pnl=-150.0, final_inventory=0.0, min_inventory=-1.0, max_inventory=1.0
    )
    result = grade_episode(episode, LIMITS)
    assert Violation.LOSS_LIMIT.value in result.violations
    assert result.score == 0.0


def test_inventory_bounds_violation_zeroes_score() -> None:
    tight = RiskLimits(max_abs_position=100.0, max_loss=1000.0, min_inventory=-2.0, max_inventory=2.0)
    episode = MarketMakingEpisodeResult(
        realized_pnl=10.0, final_inventory=0.0, min_inventory=-1.0, max_inventory=5.0
    )
    result = grade_episode(episode, tight)
    assert Violation.INVENTORY_BOUNDS.value in result.violations
    assert result.score == 0.0
