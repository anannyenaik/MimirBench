"""Tests for the deterministic Bayesian posterior calculator and solver."""

from __future__ import annotations

import math

import numpy as np
import pytest

from mimirbench.environments.bayesian_games import generate_task, reference_solver
from mimirbench.tools.bayes_calculator import BayesError, posterior, validate_distribution


def test_posterior_sums_to_one() -> None:
    post = posterior([0.5, 0.5], [[0.9, 0.1], [0.2, 0.8]], [0, 0, 1])
    assert math.isclose(sum(post), 1.0, abs_tol=1e-9)
    assert all(0.0 <= p <= 1.0 for p in post)


def test_known_single_update() -> None:
    # Prior 0.5/0.5; observe signal 0 with likelihoods 0.9 vs 0.2.
    post = posterior([0.5, 0.5], [[0.9, 0.1], [0.2, 0.8]], [0])
    assert post[0] == pytest.approx(0.45 / 0.55)
    assert post[1] == pytest.approx(0.10 / 0.55)


def test_order_of_independent_evidence_does_not_matter() -> None:
    priors = [0.2, 0.3, 0.5]
    likelihood = [[0.6, 0.3, 0.1], [0.2, 0.5, 0.3], [0.1, 0.2, 0.7]]
    obs = [0, 1, 2, 2, 0]
    base = posterior(priors, likelihood, obs)
    reversed_obs = posterior(priors, likelihood, list(reversed(obs)))
    permuted = posterior(priors, likelihood, list(np.random.default_rng(0).permutation(obs)))
    assert np.allclose(base, reversed_obs)
    assert np.allclose(base, permuted)


def test_empty_observations_returns_prior() -> None:
    priors = [0.3, 0.7]
    post = posterior(priors, [[0.5, 0.5], [0.5, 0.5]], [])
    assert np.allclose(post, priors)


def test_invalid_priors_raise_useful_error() -> None:
    with pytest.raises(BayesError, match="sum to 1"):
        posterior([0.5, 0.6], [[0.5, 0.5], [0.5, 0.5]], [0])
    with pytest.raises(BayesError, match="negative"):
        posterior([-0.1, 1.1], [[0.5, 0.5], [0.5, 0.5]], [0])


def test_likelihood_shape_mismatch_raises() -> None:
    with pytest.raises(BayesError, match="rows"):
        posterior([0.5, 0.5], [[0.5, 0.5]], [0])


def test_observation_out_of_range_raises() -> None:
    with pytest.raises(BayesError, match="out of range"):
        posterior([0.5, 0.5], [[0.5, 0.5], [0.5, 0.5]], [2])


def test_impossible_observation_raises() -> None:
    with pytest.raises(BayesError, match="impossible"):
        posterior([0.5, 0.5], [[1.0, 0.0], [1.0, 0.0]], [1])


def test_validate_distribution_returns_array() -> None:
    arr = validate_distribution([0.25, 0.75])
    assert arr.shape == (2,)


def test_reference_solver_matches_grading_key() -> None:
    instance = generate_task(seed=3)
    answer = reference_solver(instance.task)
    assert np.allclose(answer["posterior"], instance.key.payload["posterior"])
    assert math.isclose(sum(answer["posterior"]), 1.0, abs_tol=1e-9)
