"""Deterministic prompt paraphrasing for consistency testing.

Paraphrase consistency asks whether an agent gives the same answer to
semantically-equivalent restatements of a task. This module provides simple,
*meaning-preserving* templated reframings that are fully deterministic given a
seed. Model-generated paraphrases are planned future work; the interface here is
intended to remain stable when that lands.

A deliberate constraint: paraphrases never edit the *body* of a task (the priors,
likelihoods, prices, limits, ...). They only re-frame the surrounding wording, so
every numeric fact an agent needs is preserved verbatim and the correct answer is
unchanged. This keeps the transformation auditable and provably answer-preserving.
"""

from __future__ import annotations

import numpy as np

__all__ = [
    "ENVIRONMENT_FRAMINGS",
    "PARAPHRASE_TEMPLATES",
    "paraphrase",
    "paraphrase_prompt",
]


# Each template must preserve the task's meaning and therefore its correct answer.
PARAPHRASE_TEMPLATES: tuple[str, ...] = (
    "{prompt}",
    "Consider the following problem.\n\n{prompt}",
    "Here is a task for you to solve:\n\n{prompt}",
    "Problem statement:\n{prompt}\n\nProvide your answer.",
    "Please work through the task below.\n\n{prompt}",
)


# Environment-specific opening reframings. Each is a meaning-preserving lead-in
# that re-tells the *story* of the task without altering any of its numbers.
ENVIRONMENT_FRAMINGS: dict[str, tuple[str, ...]] = {
    "bayesian_games": (
        "Reframed as an inference exercise (the numbers below are unchanged).",
        "A colleague restates the same source-identification problem this way.",
        "Same priors and likelihoods, told as a diagnostics puzzle.",
    ),
    "hidden_regimes": (
        "Reframed as a regime-tracking exercise (the dynamics below are unchanged).",
        "A colleague restates the same filtering problem this way.",
        "Same transition and emission tables, told as a monitoring puzzle.",
    ),
    "auctions": (
        "Reframed as a bidding exercise (the auction rules below are unchanged).",
        "A colleague restates the same surplus question this way.",
        "Same values and auction format, told as a procurement puzzle.",
    ),
    "market_making": (
        "Reframed as a quoting exercise (the toy market state below is unchanged).",
        "A colleague restates the same quote decision this way.",
        "Same inventory and limits, told as a desk drill.",
    ),
    "prediction_markets": (
        "Reframed as a forecasting exercise (the market state below is unchanged).",
        "A colleague restates the same trade decision this way.",
        "Same probabilities and costs, told as a betting puzzle.",
    ),
    "adversarial_risk": (
        "Reframed as a risk-control exercise (the policy and numbers below are unchanged).",
        "A colleague restates the same approval decision this way.",
        "Same hard limits, told as a compliance drill.",
    ),
}

_DEFAULT_FRAMINGS: tuple[str, ...] = (
    "Reframed restatement of the same task (all data below is unchanged).",
    "A colleague restates the same problem this way.",
    "Same task, different framing.",
)


def paraphrase(prompt: str, n: int = 3, *, seed: int = 0) -> list[str]:
    """Return ``n`` deterministic, meaning-preserving paraphrases of ``prompt``.

    The original prompt is always included first; the remaining variants are
    drawn without replacement from :data:`PARAPHRASE_TEMPLATES` (cycling if
    ``n`` exceeds the template count).
    """
    if n < 1:
        raise ValueError("n must be >= 1.")
    rng = np.random.default_rng(seed)
    others = [t for t in PARAPHRASE_TEMPLATES if t != "{prompt}"]
    rng.shuffle(others)
    chosen = ["{prompt}"]
    while len(chosen) < n:
        chosen.append(others[(len(chosen) - 1) % len(others)])
    return [template.format(prompt=prompt) for template in chosen[:n]]


def paraphrase_prompt(prompt: str, environment: str, *, seed: int = 0) -> str:
    """Return one deterministic, answer-preserving reframing of ``prompt``.

    The task body is preserved verbatim; only an environment-flavoured lead-in
    and a neutral template wrapper are applied. The choice is seed-controlled so
    the same ``(prompt, environment, seed)`` always yields the same text.
    """
    rng = np.random.default_rng(seed)
    framings = ENVIRONMENT_FRAMINGS.get(environment, _DEFAULT_FRAMINGS)
    lead = framings[int(rng.integers(0, len(framings)))]
    template = PARAPHRASE_TEMPLATES[int(rng.integers(1, len(PARAPHRASE_TEMPLATES)))]
    return template.format(prompt=f"{lead}\n\n{prompt}")
