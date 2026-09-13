"""Tests for binary prediction-market tasks."""

from __future__ import annotations

from mimirbench.environments.prediction_markets.generator import generate_task
from mimirbench.environments.prediction_markets.grader import grade
from mimirbench.environments.prediction_markets.schemas import PredictionMarketTaskParams
from mimirbench.environments.prediction_markets.solver import posterior_probability, solve_params
from mimirbench.evals.schemas import EnvironmentFamily, GradingKey, ModelResponse, Task


def _params(**updates: object) -> PredictionMarketTaskParams:
    base = PredictionMarketTaskParams(
        event_description="A synthetic event resolves yes",
        current_market_price=0.5,
        private_signal="positive",
        private_signal_reliability=0.8,
        prior_probability=0.5,
        market_impact_parameter=0.02,
        transaction_cost=0.01,
        public_evidence=["mixed"],
        position_limit=10.0,
        budget_limit=20.0,
        current_position=0.0,
    )
    return base.model_copy(update=updates)


def _task(params: PredictionMarketTaskParams) -> tuple[Task, GradingKey]:
    task = Task(
        task_id="pm-test",
        family=EnvironmentFamily.PREDICTION_MARKETS,
        seed=0,
        prompt="test",
        metadata=params.model_dump(mode="json"),
    )
    return task, GradingKey(task_id=task.task_id, payload=solve_params(params))


def _response(answer: dict[str, object]) -> ModelResponse:
    return ModelResponse(task_id="pm-test", agent_name="test", raw_text=str(answer), parsed_answer=answer)


def test_fair_probability_is_within_unit_interval() -> None:
    instance = generate_task(11)
    answer = solve_params(PredictionMarketTaskParams(**instance.task.metadata))
    assert 0.0 <= float(answer["fair_probability"]) <= 1.0


def test_no_edge_leads_to_abstention() -> None:
    params = _params()
    fair = posterior_probability(params)
    answer = solve_params(params.model_copy(update={"current_market_price": fair}))
    assert answer["action"] == "abstain"


def test_strong_positive_edge_leads_to_buy() -> None:
    params = _params(current_market_price=0.45)
    answer = solve_params(params)
    assert answer["action"] == "buy"
    assert float(answer["trade_size"]) > 0.0


def test_strong_negative_edge_leads_to_sell() -> None:
    params = _params(private_signal="negative", current_market_price=0.55)
    answer = solve_params(params)
    assert answer["action"] == "sell"
    assert float(answer["trade_size"]) > 0.0


def test_position_or_budget_limits_are_enforced() -> None:
    params = _params(current_position=10.0, current_market_price=0.4)
    task, key = _task(params)
    unsafe = {
        "action": "buy",
        "target_position": 11.0,
        "trade_size": 1.0,
        "fair_probability": 0.8,
        "expected_value": 0.1,
        "confidence": 0.8,
        "reasoning_summary": "unsafe",
    }
    result = grade(task, _response(unsafe), key)
    assert "position_limit" in result.violations
    assert result.metrics["risk_limit_violation"] == 1.0


def test_prediction_reference_solver_is_deterministic() -> None:
    params = _params(private_signal="negative", current_market_price=0.8)
    assert solve_params(params) == solve_params(params)
