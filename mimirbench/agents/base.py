"""Agent interfaces and a deterministic reference baseline.

An *agent* maps a :class:`~mimirbench.evals.schemas.Task` to a
:class:`~mimirbench.evals.schemas.ModelResponse`. Everything else in the harness
(the runner, graders, analysis) depends only on this contract, so swapping a
direct prompt for a tool-using or local model never touches the eval code.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from mimirbench.evals.schemas import ModelResponse, Task

__all__ = ["ANSWER_INSTRUCTION", "BaseAgent", "ReferenceAgent", "extract_json_object"]


# Standard instruction appended to task prompts for LLM agents. MimirBench never
# requests hidden or private chain-of-thought; it asks only for a short rationale
# plus a machine-readable answer.
ANSWER_INSTRUCTION = (
    "Respond with a single JSON object containing your answer for the task, "
    "and a short field 'reasoning_summary' (one or two sentences) summarising "
    "why. Do not include long step-by-step internal reasoning."
)


def extract_json_object(text: str) -> dict[str, Any] | None:
    """Best-effort extraction of a single JSON object from model text.

    Tries to parse the whole string first, then falls back to the substring
    between the first ``{`` and the last ``}``. Returns ``None`` if no JSON
    object can be recovered.
    """
    text = text.strip()
    candidates = [text]
    start = text.find("{")
    end = text.rfind("}")
    if 0 <= start < end:
        candidates.append(text[start : end + 1])
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def act(self, task: Task) -> ModelResponse:
        """Produce a response for a single task."""
        raise NotImplementedError


class ReferenceAgent(BaseAgent):
    """A deterministic, non-LLM baseline driven by an environment's solver.

    Given a ``solve_fn`` that maps a task to a structured answer dict (computed
    from the task's *public* ``metadata``, never the grading key), this agent
    returns that answer. It serves three purposes:

    * a smoke test that the generate → grade pipeline is wired correctly;
    * a determinism anchor (same seed → identical results);
    * an approximate upper bound for environments whose reference solver is exact.

    It is explicitly *not* a model and should never be reported as a model score.
    """

    def __init__(
        self,
        solve_fn: Callable[[Task], dict[str, Any]],
        name: str = "reference",
    ) -> None:
        super().__init__(name)
        self._solve_fn = solve_fn

    def act(self, task: Task) -> ModelResponse:
        answer = self._solve_fn(task)
        return ModelResponse(
            task_id=task.task_id,
            agent_name=self.name,
            raw_text=json.dumps(answer, sort_keys=True),
            parsed_answer=answer,
            reasoning_summary="Deterministic reference solver output.",
        )
