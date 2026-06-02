"""Tests for the sealed-bid auction helpers."""

from __future__ import annotations

import numpy as np
import pytest

from mimirbench.tools.auction_solver import (
    expected_bidder_surplus,
    expected_welfare,
    summarize_second_price_auction,
)


def test_single_bidder_surplus_equals_value() -> None:
    # With no competitors the second price is the (zero) reserve, so surplus = value.
    assert expected_bidder_surplus(0.7, 1, 1.0) == pytest.approx(0.7)


def test_two_bidder_known_values() -> None:
    assert expected_bidder_surplus(1.0, 2, 1.0) == pytest.approx(0.5)
    assert expected_bidder_surplus(0.5, 2, 1.0) == pytest.approx(0.125)


def test_welfare_revenue_and_surplus_decomposition() -> None:
    summary = summarize_second_price_auction(3, 1.0)
    assert summary.expected_welfare == pytest.approx(3 / 4)
    assert summary.expected_revenue == pytest.approx(2 / 4)
    assert summary.expected_winner_surplus == pytest.approx(1 / 4)


def test_value_is_capped_at_v_max() -> None:
    assert expected_bidder_surplus(5.0, 2, 1.0) == expected_bidder_surplus(1.0, 2, 1.0)


def test_monte_carlo_matches_closed_form() -> None:
    rng = np.random.default_rng(0)
    n_bidders, v_max, value, trials = 4, 1.0, 0.6, 200_000
    others = rng.uniform(0.0, v_max, size=(trials, n_bidders - 1))
    max_other = others.max(axis=1)
    won = max_other < value
    simulated = float(np.where(won, value - max_other, 0.0).mean())
    assert simulated == pytest.approx(expected_bidder_surplus(value, n_bidders, v_max), abs=2e-3)


def test_invalid_inputs_raise() -> None:
    with pytest.raises(ValueError):
        expected_bidder_surplus(0.5, 0, 1.0)
    with pytest.raises(ValueError):
        expected_welfare(2, 0.0)
