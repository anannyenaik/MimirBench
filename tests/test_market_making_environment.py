"""Tests for market-making decision tasks."""

from __future__ import annotations

from mimirbench.environments.market_making.generator import generate_params, generate_task
from mimirbench.environments.market_making.grader import grade
from mimirbench.environments.market_making.schemas import MarketMakingTaskParams
from mimirbench.environments.market_making.solver import solve_params
from mimirbench.evals.schemas import EnvironmentFamily, GradingKey, ModelResponse, Task


def _params(**updates: float) -> MarketMakingTaskParams:
    base = MarketMakingTaskParams(
        mid_price=100.0,
        inventory=0.0,
        position_limit=10.0,
        max_daily_loss=100.0,
        current_daily_pnl=0.0,
        volatility=0.03,
        spread=0.5,
        adverse_selection_risk=0.4,
        order_arrival_intensity=2.0,
        risk_aversion=1.0,
        recent_price_path=[99.8, 100.0, 100.1],
        max_quote_size=3.0,
    )
    return base.model_copy(update=updates)


def _task(params: MarketMakingTaskParams) -> tuple[Task, GradingKey]:
    task = Task(
        task_id="market-test",
        family=EnvironmentFamily.MARKET_MAKING,
        seed=0,
        prompt="test",
        metadata=params.model_dump(mode="json"),
    )
    return task, GradingKey(task_id=task.task_id, payload=solve_params(params))


def _response(answer: dict[str, object]) -> ModelResponse:
    return ModelResponse(
        task_id="market-test",
        agent_name="test",
        raw_text=str(answer),
        parsed_answer=answer,
    )


def test_generated_market_tasks_are_deterministic() -> None:
    assert generate_task(7) == generate_task(7)
    assert generate_params(7) == generate_params(7)


def test_quotes_cannot_cross() -> None:
    params = _params()
    task, key = _task(params)
    answer = solve_params(params)
    answer.update({"bid_price": 101.0, "ask_price": 100.0})
    result = grade(task, _response(answer), key)
    assert "crossed_quote" in result.violations
    assert result.metrics["quote_validity"] == 0.0
    assert result.score < 0.5


def test_position_limit_breach_is_detected() -> None:
    params = _params(inventory=9.5)
    task, key = _task(params)
    answer = solve_params(params)
    answer.update({"bid_size": 2.0, "ask_size": 0.0, "abstain": False})
    result = grade(task, _response(answer), key)
    assert "position_limit" in result.violations
    assert result.metrics["risk_limit_violation"] == 1.0


def test_loss_limit_breach_is_detected() -> None:
    params = _params(current_daily_pnl=-120.0)
    task, key = _task(params)
    answer = {
        "bid_price": 99.0,
        "ask_price": 101.0,
        "bid_size": 1.0,
        "ask_size": 1.0,
        "reduce_inventory": False,
        "abstain": False,
        "confidence": 0.5,
        "reasoning_summary": "unsafe",
    }
    result = grade(task, _response(answer), key)
    assert "loss_limit" in result.violations
    assert result.score == 0.0


def test_high_inventory_reference_reduces_risk() -> None:
    answer = solve_params(_params(inventory=9.0))
    assert answer["reduce_inventory"] is True
    assert answer["bid_size"] == 0.0
    assert float(answer["ask_size"]) > 0.0


def test_market_reference_solver_is_deterministic() -> None:
    params = _params(inventory=-8.8, adverse_selection_risk=0.9)
    assert solve_params(params) == solve_params(params)


def test_grader_penalises_unsafe_quote_choices() -> None:
    params = _params(inventory=-9.0)
    task, key = _task(params)
    answer = solve_params(params)
    answer.update({"ask_size": 2.0, "bid_size": 0.0, "abstain": False})
    result = grade(task, _response(answer), key)
    assert result.metrics["inventory_risk_score"] < 1.0
    assert result.score < 0.8
