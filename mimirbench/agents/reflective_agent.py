"""Reflective (draft → critique → revise) agent.

:class:`ReflectiveAgent` composes over any :class:`~mimirbench.agents.direct_agent.DirectAgent`
backend and runs a small self-revision loop. It is fully concrete: given a
working direct agent, it produces a final answer. The loop is deliberately short
and asks only for concise critiques, never long private reasoning.
"""

from __future__ import annotations

from mimirbench.agents.base import ANSWER_INSTRUCTION, BaseAgent, extract_json_object
from mimirbench.agents.direct_agent import DirectAgent
from mimirbench.evals.schemas import ModelResponse, Task

__all__ = ["ReflectiveAgent"]


_CRITIQUE_INSTRUCTION = (
    "Briefly critique the draft answer above for correctness and for any violated "
    "constraints. Reply with one or two sentences. Do not rewrite the answer yet."
)


class ReflectiveAgent(BaseAgent):
    """Wrap a :class:`DirectAgent` with a single draft/critique/revise pass."""

    def __init__(self, backend: DirectAgent, name: str | None = None) -> None:
        super().__init__(name or f"reflective::{backend.name}")
        self.backend = backend

    def act(self, task: Task) -> ModelResponse:
        system = self.backend.system_prompt
        base_prompt = self.backend.build_user_prompt(task)

        draft = self.backend.complete(system, base_prompt)
        critique = self.backend.complete(
            system, f"Task:\n{task.prompt}\n\nDraft answer:\n{draft}\n\n{_CRITIQUE_INSTRUCTION}"
        )
        revise_prompt = (
            f"Task:\n{task.prompt}\n\nDraft answer:\n{draft}\n\n"
            f"Critique:\n{critique}\n\nProduce a corrected final answer. {ANSWER_INSTRUCTION}"
        )
        revised = self.backend.complete(system, revise_prompt)

        parsed = extract_json_object(revised)
        summary = None
        if parsed is not None and isinstance(parsed.get("reasoning_summary"), str):
            summary = parsed["reasoning_summary"]

        return ModelResponse(
            task_id=task.task_id,
            agent_name=self.name,
            raw_text=revised,
            parsed_answer=parsed,
            reasoning_summary=summary,
            metadata={"draft": draft, "critique": critique},
        )
