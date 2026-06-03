"""Named, JSON-friendly tool registry for tool-using agents.

Each entry wraps one of the deterministic primitives in :mod:`mimirbench.tools`
behind a stable name and a JSON-serialisable signature, so an agent can request a
tool by name with a dict of arguments and receive a dict result. Sharing the
exact primitives the graders use means a tool-using agent can, in principle,
compute precisely the answer it is graded against.

Three safety properties hold by construction:

* tools are a **fixed registry** — there is no arbitrary code/`eval` path;
* tools are **pure and offline** — no network, no filesystem, no global state;
* tools receive only the arguments the agent proposes — never the
  :class:`~mimirbench.evals.schemas.GradingKey`.

:data:`ENVIRONMENT_TOOL_ALLOWLIST` declares which tools are permitted per
environment; the agent loop validates every request against it.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from mimirbench.tools.auction_solver import expected_bidder_surplus, summarize_second_price_auction
from mimirbench.tools.bayes_calculator import posterior
from mimirbench.tools.ev_calculator import best_action, expected_value, variance
from mimirbench.tools.market_simulator import simulate_mid_price
from mimirbench.tools.risk_checker import RiskLimits, RiskState, check_risk

__all__ = [
    "ALL_TOOL_NAMES",
    "ENVIRONMENT_TOOL_ALLOWLIST",
    "ToolSpec",
    "allowed_tools_for",
    "default_tools",
    "tool_descriptions",
]


@dataclass(frozen=True)
class ToolSpec:
    """A named, JSON-friendly deterministic tool exposed to an agent."""

    name: str
    description: str
    args_hint: str
    fn: Callable[..., dict[str, Any]]


# --------------------------------------------------------------------------- #
# Tool implementations (thin, validating wrappers around the shared primitives).
# --------------------------------------------------------------------------- #
# Small, principled tolerances so an agent that copies prompt-rounded
# probabilities (shown to 3 decimals) or 1-indexed symbol labels still produces a
# usable tool call. These never mask genuinely malformed input: a vector that is
# not already close to a distribution, or observations out of range under both 0-
# and 1-indexed readings, are passed through untouched for the strict primitive to
# reject.
_RENORM_TOL = 1e-2


def _coerce_distribution(values: Any) -> Any:
    """Renormalise a near-valid probability vector to sum to exactly 1.

    Returns ``values`` unchanged unless it is a finite, non-negative numeric
    vector that already sums to within ``_RENORM_TOL`` of 1.
    """
    if not isinstance(values, (list, tuple)) or not values:
        return values
    try:
        floats = [float(v) for v in values]
    except (TypeError, ValueError):
        return values
    if any(not math.isfinite(v) or v < 0 for v in floats):
        return values
    total = math.fsum(floats)
    if total <= 0.0 or not math.isclose(total, 1.0, abs_tol=_RENORM_TOL):
        return values
    return [v / total for v in floats]


def _normalize_observations(observations: Any, likelihood: Any) -> Any:
    """Coerce 1-indexed observations to 0-indexed signal indices when unambiguous.

    The prompt labels signals ``symbol 1 .. symbol m``, so an agent often passes
    1-indexed values. If the observations fall outside the 0-indexed range
    ``[0, m)`` but every value fits a 1-indexed reading ``[1, m]``, shift them down
    by one. Valid 0-indexed observations are returned unchanged.
    """
    if not isinstance(observations, (list, tuple)) or not observations:
        return observations
    try:
        obs = [int(s) for s in observations]
    except (TypeError, ValueError):
        return observations
    try:
        n_signals = len(likelihood[0])
    except (TypeError, IndexError, KeyError):
        return obs
    if n_signals <= 0:
        return obs
    if all(0 <= s < n_signals for s in obs):
        return obs
    if all(1 <= s <= n_signals for s in obs):
        return [s - 1 for s in obs]
    return obs


def _bayes_calculator(
    priors: list[float],
    likelihood: list[list[float]],
    observations: list[int],
) -> dict[str, Any]:
    priors = _coerce_distribution(priors)
    if isinstance(likelihood, (list, tuple)):
        likelihood = [_coerce_distribution(row) for row in likelihood]
    observations = _normalize_observations(observations, likelihood)
    return {"posterior": posterior(priors, likelihood, observations)}


def _ev_calculator(
    payoffs: list[float],
    probabilities: list[float],
    actions: dict[str, list[list[float]]] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "expected_value": expected_value(payoffs, probabilities),
        "variance": variance(payoffs, probabilities),
    }
    if actions:
        action_payoffs: dict[str, tuple[Sequence[float], Sequence[float]]] = {
            name: (pair[0], pair[1]) for name, pair in actions.items()
        }
        name, ev = best_action(action_payoffs)
        result["best_action"] = name
        result["best_action_ev"] = ev
    return result


def _risk_checker(
    position: float,
    proposed_trade: float = 0.0,
    realized_pnl: float = 0.0,
    max_abs_position: float = float("inf"),
    max_loss: float = float("inf"),
    min_inventory: float | None = None,
    max_inventory: float | None = None,
) -> dict[str, Any]:
    limits = RiskLimits(
        max_abs_position=max_abs_position,
        max_loss=max_loss,
        min_inventory=float("-inf") if min_inventory is None else min_inventory,
        max_inventory=float("inf") if max_inventory is None else max_inventory,
    )
    state = RiskState(position=position, realized_pnl=realized_pnl)
    result = check_risk(state, limits, proposed_trade=proposed_trade)
    return {
        "ok": result.ok,
        "resulting_position": result.resulting_position,
        "violations": result.violation_names,
    }


def _auction_solver(
    your_value: float,
    n_bidders: int,
    v_max: float = 1.0,
    auction_type: str = "second_price",
) -> dict[str, Any]:
    if auction_type != "second_price":
        raise ValueError(f"unsupported auction_type {auction_type!r} (only 'second_price').")
    summary = summarize_second_price_auction(n_bidders, v_max)
    return {
        "expected_surplus": expected_bidder_surplus(your_value, n_bidders, v_max),
        "expected_welfare": summary.expected_welfare,
        "expected_revenue": summary.expected_revenue,
    }


def _market_simulator(
    n_steps: int,
    start: float = 100.0,
    drift: float = 0.0,
    volatility: float = 1.0,
    seed: int = 0,
) -> dict[str, Any]:
    path = simulate_mid_price(n_steps, start=start, drift=drift, volatility=volatility, seed=seed)
    return {"path": [float(x) for x in path]}


_TOOL_SPECS: tuple[ToolSpec, ...] = (
    ToolSpec(
        name="bayes_calculator",
        description=(
            "Exact discrete Bayesian posterior over hypotheses given a likelihood table and "
            "observations. Priors and each likelihood row should sum to 1 (minor rounding is "
            "tolerated and renormalised)."
        ),
        args_hint=(
            '{"priors": [..], "likelihood": [[..]], "observations": [j, ..]} '
            "where observations are 0-indexed signal positions (the first symbol shown is 0); "
            "1-indexed symbol numbers are also accepted."
        ),
        fn=_bayes_calculator,
    ),
    ToolSpec(
        name="ev_calculator",
        description="Expected value and variance of a discrete lottery; optionally the EV-maximising action.",
        args_hint='{"payoffs": [..], "probabilities": [..]}',
        fn=_ev_calculator,
    ),
    ToolSpec(
        name="risk_checker",
        description="Check whether a proposed trade keeps a book within hard position/loss/inventory limits.",
        args_hint='{"position": float, "proposed_trade": float, "max_abs_position": float, "max_loss": float}',
        fn=_risk_checker,
    ),
    ToolSpec(
        name="auction_solver",
        description="Closed-form expected surplus/revenue/welfare for a symmetric second-price IPV auction.",
        args_hint='{"your_value": float, "n_bidders": int, "v_max": float}',
        fn=_auction_solver,
    ),
    ToolSpec(
        name="market_simulator",
        description="Deterministic toy mid-price path (arithmetic Brownian motion) for a given seed.",
        args_hint='{"n_steps": int, "start": float, "drift": float, "volatility": float, "seed": int}',
        fn=_market_simulator,
    ),
)

ALL_TOOL_NAMES: tuple[str, ...] = tuple(spec.name for spec in _TOOL_SPECS)

# Which tools each environment is allowed to use. The agent loop rejects any
# request outside this set and records it as an invalid tool call.
ENVIRONMENT_TOOL_ALLOWLIST: dict[str, frozenset[str]] = {
    "bayesian_games": frozenset({"bayes_calculator", "ev_calculator"}),
    "hidden_regimes": frozenset({"bayes_calculator", "ev_calculator", "market_simulator"}),
    "auctions": frozenset({"auction_solver", "ev_calculator"}),
    "market_making": frozenset({"risk_checker", "ev_calculator", "market_simulator"}),
    "prediction_markets": frozenset({"bayes_calculator", "ev_calculator", "risk_checker"}),
    "adversarial_risk": frozenset({"risk_checker", "ev_calculator"}),
}


def default_tools() -> dict[str, ToolSpec]:
    """Return the full tool registry keyed by name."""
    return {spec.name: spec for spec in _TOOL_SPECS}


def allowed_tools_for(environment: str) -> frozenset[str]:
    """Return the allowed tool names for an environment (empty if unknown)."""
    return ENVIRONMENT_TOOL_ALLOWLIST.get(environment, frozenset())


def tool_descriptions(names: frozenset[str] | set[str] | tuple[str, ...]) -> str:
    """Render a compact, prompt-friendly description of the named tools."""
    registry = default_tools()
    lines = []
    for name in sorted(names):
        spec = registry.get(name)
        if spec is not None:
            lines.append(f"- {spec.name}: {spec.description} args={spec.args_hint}")
    return "\n".join(lines)
