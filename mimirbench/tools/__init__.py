"""Deterministic decision tools.

Each tool is a small, pure, deterministic primitive that (a) agents may call
during a task and (b) environments reuse to build ground truth. Sharing one
implementation guarantees agents are graded against exactly the answer the tool
would have produced.
"""

from mimirbench.tools.auction_solver import (
    AuctionSummary,
    expected_bidder_surplus,
    expected_revenue_second_price,
    expected_welfare,
    summarize_second_price_auction,
)
from mimirbench.tools.bayes_calculator import BayesError, posterior, validate_distribution
from mimirbench.tools.ev_calculator import best_action, expected_value, variance
from mimirbench.tools.market_simulator import simulate_mid_price, simulate_regime_path
from mimirbench.tools.risk_checker import (
    RiskCheckResult,
    RiskLimits,
    RiskState,
    Violation,
    check_risk,
)

__all__ = [
    "AuctionSummary",
    "BayesError",
    "RiskCheckResult",
    "RiskLimits",
    "RiskState",
    "Violation",
    "best_action",
    "check_risk",
    "expected_bidder_surplus",
    "expected_revenue_second_price",
    "expected_value",
    "expected_welfare",
    "posterior",
    "simulate_mid_price",
    "simulate_regime_path",
    "summarize_second_price_auction",
    "validate_distribution",
    "variance",
]
