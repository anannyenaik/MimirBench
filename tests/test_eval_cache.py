"""Response cache tests."""

from __future__ import annotations

from pathlib import Path

from mimirbench.environments.bayesian_games.generator import generate_task
from mimirbench.evals.cache import ResponseCache, make_cache_key
from mimirbench.evals.schemas import AgentConfig, ModelResponse


def test_cache_key_is_deterministic_and_config_sensitive() -> None:
    task = generate_task(0).task
    config = AgentConfig(type="mock", behaviour="random_valid", seed=1)
    same = AgentConfig(type="mock", behaviour="random_valid", seed=1)
    different = AgentConfig(type="mock", behaviour="random_valid", seed=2)

    first_key = make_cache_key(agent_config=config, environment="bayesian_games", task=task)
    second_key = make_cache_key(agent_config=same, environment="bayesian_games", task=task)
    different_key = make_cache_key(agent_config=different, environment="bayesian_games", task=task)

    assert first_key == second_key
    assert first_key != different_key


def test_cache_hit_miss_and_bypass(tmp_path: Path) -> None:
    path = tmp_path / "cache.jsonl"
    cache = ResponseCache(path, enabled=True)
    response = ModelResponse(
        task_id="task-1",
        agent_name="agent",
        raw_text='{"answer": 1}',
        parsed_answer={"answer": 1},
    )

    assert cache.get("missing") is None
    cache.set("key", response, metadata={"source": "test"})

    loaded = ResponseCache(path, enabled=True)
    entry = loaded.get("key")
    assert entry is not None
    assert entry.model_response == response
    assert entry.metadata == {"source": "test"}

    bypassed = ResponseCache(path, enabled=True, bypass=True)
    assert bypassed.get("key") is None
