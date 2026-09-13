"""Deterministic Bayesian posterior calculator.

This is the canonical, fully-specified reference used both as an agent *tool*
(``bayes_calculator``) and by the Bayesian-games environment's reference solver
and grader. Keeping a single implementation means the "right answer" an agent
could compute with the tool is exactly the answer it is graded against.

The model is a discrete naive-Bayes update: a set of mutually exclusive
hypotheses ``H_0 .. H_{k-1}`` with a prior ``P(H_i)``, a likelihood table
``P(signal_j | H_i)``, and a sequence of observed signals assumed conditionally
independent given the hypothesis. The posterior is

    P(H_i | obs) ∝ P(H_i) * prod_t P(obs_t | H_i).

Computation is done in log-space so that long observation sequences do not
underflow and so that the result is invariant to the order of the evidence.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
import numpy.typing as npt

__all__ = ["BayesError", "posterior", "validate_distribution"]


class BayesError(ValueError):
    """Raised for malformed priors, likelihood tables, or observations."""


def validate_distribution(
    values: Sequence[float],
    *,
    name: str = "distribution",
    tol: float = 1e-9,
) -> npt.NDArray[np.float64]:
    """Validate and return a 1-D probability distribution as a float array.

    A valid distribution is a finite, non-negative 1-D vector that sums to 1
    within ``tol``. Raising early with a clear message is intentional: silent
    renormalisation hides bugs in task generators and graders.
    """
    arr = np.asarray(values, dtype=np.float64)
    if arr.ndim != 1:
        raise BayesError(f"{name} must be 1-D, got shape {arr.shape}.")
    if arr.size == 0:
        raise BayesError(f"{name} must be non-empty.")
    if not np.all(np.isfinite(arr)):
        raise BayesError(f"{name} contains non-finite values: {arr.tolist()}.")
    if np.any(arr < 0):
        raise BayesError(f"{name} has negative entries: {arr.tolist()}.")
    total = float(arr.sum())
    if not math.isclose(total, 1.0, abs_tol=tol):
        raise BayesError(f"{name} must sum to 1 (got {total:.6g}).")
    return arr


def posterior(
    priors: Sequence[float],
    likelihood: Sequence[Sequence[float]],
    observations: Sequence[int],
    *,
    tol: float = 1e-9,
) -> list[float]:
    """Compute the posterior ``P(H_i | observations)``.

    Args:
        priors: Prior probabilities ``P(H_i)``; length ``k``, sums to 1.
        likelihood: Row-major table where ``likelihood[i][j] = P(signal_j | H_i)``;
            shape ``(k, m)``. Rows are conditional distributions over signals
            and must each sum to 1.
        observations: Observed signal indices in ``[0, m)``. May be empty, in
            which case the posterior equals the prior.
        tol: Absolute tolerance used when validating that distributions sum to 1.

    Returns:
        The posterior as a list of floats that sums to 1.

    Raises:
        BayesError: If any input is malformed, or if the observations are
            impossible under every hypothesis (zero total likelihood).
    """
    prior_arr = validate_distribution(priors, name="priors", tol=tol)
    n_hypotheses = prior_arr.shape[0]

    like = np.asarray(likelihood, dtype=np.float64)
    if like.ndim != 2:
        raise BayesError(f"likelihood must be 2-D, got shape {like.shape}.")
    if like.shape[0] != n_hypotheses:
        raise BayesError(
            f"likelihood has {like.shape[0]} rows but there are {n_hypotheses} priors."
        )
    n_signals = like.shape[1]
    if n_signals == 0:
        raise BayesError("likelihood must have at least one signal column.")
    for i in range(n_hypotheses):
        validate_distribution(like[i], name=f"likelihood row {i}", tol=tol)

    obs = [int(s) for s in observations]
    for s in obs:
        if not 0 <= s < n_signals:
            raise BayesError(f"observation {s} out of range [0, {n_signals}).")

    # Accumulate evidence in log-space. Summation is order-independent, so the
    # posterior does not depend on the order of conditionally-independent signals.
    with np.errstate(divide="ignore"):
        log_post = np.log(prior_arr)
        if obs:
            log_post = log_post + np.log(like[:, obs]).sum(axis=1)

    # Stable normalisation: subtract the max before exponentiating.
    finite_max = log_post[np.isfinite(log_post)]
    if finite_max.size == 0:
        raise BayesError("observations are impossible under every hypothesis.")
    log_post = log_post - finite_max.max()
    unnormalised = np.exp(log_post)
    total = float(unnormalised.sum())
    if total <= 0.0:
        raise BayesError("observations are impossible under every hypothesis.")
    result = unnormalised / total
    return [float(x) for x in result]
