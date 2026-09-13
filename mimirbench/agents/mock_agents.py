"""Deterministic mock agents for harness tests and scoring diagnostics.

These agents are not language models. They exist to exercise parsers, graders,
cache behaviour, and aggregate metrics without network calls or optional model
dependencies.
"""

from __future__ import annotations

import copy
import hashlib
import json
import random
from typing import Any

from mimirbench.agents.base import BaseAgent
from mimirbench.evals.schemas import EnvironmentFamily, GradingKey, ModelResponse, Task

__all__ = [
    "AlwaysAbstainAgent",
    "NoisyReferenceAgent",
    "RandomValidAgent",
]


def _stable_seed(base_seed: int, task_id: str) -> int:
    digest = hashlib.sha256(f"{base_seed}:{task_id}".encode()).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def _normalised_random_distribution(rng: random.Random, n: int) -> list[float]:
    values = [rng.random() for _ in range(n)]
    total = sum(values)
    if total <= 0.0:
        return [1.0 / n for _ in range(n)]
    return [value / total for value in values]


def _as_json_response(
    *,
    task: Task,
    agent_name: str,
    answer: dict[str, Any],
    reasoning_summary: str,
    metadata: dict[str, Any] | None = None,
) -> ModelResponse:
    payload = dict(answer)
    payload.setdefault("reasoning_summary", reasoning_summary)
    return ModelResponse(
        task_id=task.task_id,
        agent_name=agent_name,
        raw_text=json.dumps(payload, sort_keys=True),
        parsed_answer=payload,
        reasoning_summary=reasoning_summary,
        metadata=metadata or {},
    )


class AlwaysAbstainAgent(BaseAgent):
    """Always returns an explicit abstention payload.

    Current environment graders do not accept abstention as a valid answer, so
    this baseline should produce invalid-answer failures. That is intentional:
    it tests invalid/parse-failure accounting.
    """

    def __init__(self, name: str = "mock::always_abstain") -> None:
        super().__init__(name)

    def act(self, task: Task) -> ModelResponse:
        return _as_json_response(
            task=task,
            agent_name=self.name,
            answer={"abstain": True},
            reasoning_summary="Deterministic mock abstention; not a model output.",
            metadata={"baseline_type": "local stub/mock baseline"},
        )


class RandomValidAgent(BaseAgent):
    """Produces deterministic, schema-shaped random answers.

    Answers are random but validly shaped for the registered environments. The
    RNG seed is derived from ``(seed, task_id)``, so concurrency and task order do
    not affect outputs.
    """

    def __init__(self, seed: int = 0, name: str = "mock::random_valid") -> None:
        super().__init__(name)
        self.seed = seed

    def act(self, task: Task) -> ModelResponse:
        rng = random.Random(_stable_seed(self.seed, task.task_id))
        answer: dict[str, Any]

        if task.family == EnvironmentFamily.BAYESIAN_GAMES:
            n = len(task.metadata.get("priors", []))
            answer = {"posterior": _normalised_random_distribution(rng, max(n, 1))}
        elif task.family == EnvironmentFamily.HIDDEN_REGIMES:
            n = len(task.metadata.get("initial", []))
            answer = {"regime_posterior": _normalised_random_distribution(rng, max(n, 1))}
        elif task.family == EnvironmentFamily.AUCTIONS:
            v_max = float(task.metadata.get("v_max", 1.0))
            answer = {"expected_surplus": rng.random() * max(v_max, 1.0)}
        elif task.family == EnvironmentFamily.MARKET_MAKING:
            mid = float(task.metadata.get("mid_price", 100.0))
            spread = max(float(task.metadata.get("spread", 1.0)), 0.01)
            max_quote_size = max(float(task.metadata.get("max_quote_size", 1.0)), 0.1)
            abstain = rng.random() < 0.15
            answer = {
                "bid_price": None if abstain else round(mid - spread * rng.uniform(0.5, 2.0), 4),
                "ask_price": None if abstain else round(mid + spread * rng.uniform(0.5, 2.0), 4),
                "bid_size": 0.0 if abstain else round(rng.random() * max_quote_size, 4),
                "ask_size": 0.0 if abstain else round(rng.random() * max_quote_size, 4),
                "reduce_inventory": rng.random() < 0.5,
                "abstain": abstain,
                "confidence": round(rng.uniform(0.35, 0.9), 4),
            }
        elif task.family == EnvironmentFamily.PREDICTION_MARKETS:
            action = rng.choice(["buy", "sell", "abstain"])
            limit = max(float(task.metadata.get("position_limit", 1.0)), 1.0)
            fair = rng.random()
            answer = {
                "action": action,
                "target_position": round(rng.uniform(-limit, limit), 4),
                "trade_size": 0.0 if action == "abstain" else round(rng.random() * limit, 4),
                "fair_probability": round(fair, 6),
                "expected_value": round(rng.uniform(-0.5, 0.5), 6),
                "confidence": round(rng.uniform(0.35, 0.9), 4),
            }
        elif task.family == EnvironmentFamily.ADVERSARIAL_RISK:
            action = rng.choice(["approve", "reject", "reduce_size", "abstain"])
            proposed = abs(float(task.metadata.get("proposed_trade", 0.0)))
            answer = {
                "action": action,
                "proposed_size": 0.0 if action in {"reject", "abstain"} else round(proposed * rng.random(), 4),
                "risk_policy_followed": rng.random() < 0.75,
                "cited_constraint": rng.choice(["none", "exposure_limit", "daily_loss_limit"]),
                "confidence": round(rng.uniform(0.35, 0.9), 4),
            }
        else:
            answer = {"answer": rng.random()}

        return _as_json_response(
            task=task,
            agent_name=self.name,
            answer=answer,
            reasoning_summary="Deterministic random valid mock answer; not a model output.",
            metadata={"baseline_type": "local stub/mock baseline"},
        )


class NoisyReferenceAgent(BaseAgent):
    """Diagnostic baseline that corrupts grading-key answers in controlled ways.

    This agent deliberately uses :class:`GradingKey` through ``act_with_key``.
    That makes it useful for scoring-sensitivity tests, but it is not a model and
    must never be reported as model performance.
    """

    diagnostic_uses_grading_key = True

    def __init__(
        self,
        *,
        seed: int = 0,
        posterior_noise: float = 0.0,
        action_error_rate: float = 0.0,
        confidence_bias: float = 0.0,
        risk_violation_rate: float = 0.0,
        name: str = "mock::noisy_reference",
    ) -> None:
        super().__init__(name)
        self.seed = seed
        self.posterior_noise = posterior_noise
        self.action_error_rate = action_error_rate
        self.confidence_bias = confidence_bias
        self.risk_violation_rate = risk_violation_rate

    def act(self, task: Task) -> ModelResponse:
        return ModelResponse(
            task_id=task.task_id,
            agent_name=self.name,
            raw_text="",
            parsed_answer=None,
            reasoning_summary="NoisyReferenceAgent requires a grading key via the runner.",
            error="NoisyReferenceAgent can only run in diagnostic key-aware mode.",
            metadata={"baseline_type": "local stub/mock baseline"},
        )

    def act_with_key(self, task: Task, key: GradingKey) -> ModelResponse:
        rng = random.Random(_stable_seed(self.seed, task.task_id))
        answer = self._corrupt_payload(copy.deepcopy(key.payload), rng)
        metadata = {
            "baseline_type": "local stub/mock baseline",
            "diagnostic_uses_grading_key": True,
            "warning": "Artificial diagnostic baseline; not a real model run.",
        }
        return _as_json_response(
            task=task,
            agent_name=self.name,
            answer=answer,
            reasoning_summary=(
                "Artificial diagnostic mock derived from the grading key with controlled "
                "corruption; not a model output."
            ),
            metadata=metadata,
        )

    def _corrupt_payload(self, payload: dict[str, Any], rng: random.Random) -> dict[str, Any]:
        corrupted: dict[str, Any] = {}
        for key, value in payload.items():
            if _is_numeric_list(value):
                corrupted[key] = self._corrupt_distribution([float(v) for v in value], rng)
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                corrupted[key] = self._corrupt_scalar(float(value), rng)
            else:
                corrupted[key] = value

        if self.risk_violation_rate > 0.0 and rng.random() < self.risk_violation_rate:
            corrupted["risk_violation"] = True
        return corrupted

    def _corrupt_distribution(self, values: list[float], rng: random.Random) -> list[float]:
        n = len(values)
        if n == 0:
            return values
        if rng.random() < self.action_error_rate:
            return _normalised_random_distribution(rng, n)

        noisy = [
            max(0.0, value + rng.gauss(0.0, self.posterior_noise))
            for value in values
        ]
        total = sum(noisy)
        noisy = [1.0 / n for _ in range(n)] if total <= 0.0 else [value / total for value in noisy]

        if self.confidence_bias != 0.0:
            exponent = (
                1.0 + self.confidence_bias
                if self.confidence_bias > 0.0
                else 1.0 / (1.0 + abs(self.confidence_bias))
            )
            exponent = max(exponent, 0.05)
            biased = [value**exponent for value in noisy]
            total = sum(biased)
            noisy = [value / total for value in biased] if total > 0.0 else noisy
        return noisy

    def _corrupt_scalar(self, value: float, rng: random.Random) -> float:
        scale = abs(value) + 1.0
        if rng.random() < self.action_error_rate:
            return value + rng.uniform(-scale, scale)
        return (value + rng.gauss(0.0, self.posterior_noise * scale)) * (
            1.0 + self.confidence_bias
        )


def _is_numeric_list(value: object) -> bool:
    if not isinstance(value, list):
        return False
    return all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in value)
