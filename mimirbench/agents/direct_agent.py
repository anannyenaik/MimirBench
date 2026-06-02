"""Single-shot ("direct") prompting agent.

:class:`DirectAgent` turns a task into one model call and parses the reply. It is
backed by a provider-agnostic :class:`~mimirbench.agents.model_client.ModelClient`,
builds an environment-aware prompt via :mod:`mimirbench.agents.prompts`, and
parses/repairs the response deterministically via
:mod:`mimirbench.agents.parsing`.

It never touches the :class:`~mimirbench.evals.schemas.GradingKey`: it only ever
sees the public :class:`~mimirbench.evals.schemas.Task`. Raw model text is
preserved on the response, token usage and cost (when available) and parse
errors are recorded in metadata, and only a concise reasoning summary is kept —
never hidden chain-of-thought.
"""

from __future__ import annotations

import time

from mimirbench.agents.base import BaseAgent
from mimirbench.agents.model_client import ModelClient, ModelClientError, ModelRequest
from mimirbench.agents.parsing import parse_response
from mimirbench.agents.prompts import DEFAULT_SYSTEM_PROMPT, build_messages, build_user_prompt
from mimirbench.evals.schemas import ModelResponse, Task, Usage

__all__ = ["DEFAULT_SYSTEM_PROMPT", "DirectAgent"]


class DirectAgent(BaseAgent):
    """Prompt-once-and-parse agent over a :class:`ModelClient` backend.

    Subclasses (API, local) only supply a configured client; prompt assembly,
    the model call, parsing/repair, timing, usage capture, and error handling all
    live here.
    """

    def __init__(
        self,
        client: ModelClient,
        *,
        name: str | None = None,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        seed: int | None = None,
        top_p: float | None = None,
    ) -> None:
        super().__init__(name or f"{client.provider}::{client.model}")
        self.client = client
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.seed = seed
        self.top_p = top_p

    def build_user_prompt(self, task: Task) -> str:
        """Assemble the environment-aware user prompt for a task."""
        return build_user_prompt(task)

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Return the model's raw text for the given prompts (no parsing).

        Kept as a thin text-in/text-out helper so composite agents (e.g. the
        reflective agent) can reuse the backend directly.
        """
        request = ModelRequest(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            seed=self.seed,
            top_p=self.top_p,
        )
        return self.client.generate(request).raw_text

    def act(self, task: Task) -> ModelResponse:
        bundle = build_messages(task, system_prompt=self.system_prompt)
        request = ModelRequest(
            system_prompt=bundle.system,
            user_prompt=bundle.user,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            seed=self.seed,
            top_p=self.top_p,
        )

        start = time.perf_counter()
        envelope = None
        error: str | None = None
        try:
            envelope = self.client.generate(request)
            raw_text = envelope.raw_text
            error = envelope.error
        except ModelClientError as exc:  # actionable, already-classified backend failure
            raw_text = ""
            error = str(exc)
        except Exception as exc:  # surface any other backend error as data, not a crash
            raw_text = ""
            error = f"{type(exc).__name__}: {exc}"
        latency_s = (
            envelope.latency_ms / 1000.0
            if envelope is not None and envelope.latency_ms is not None
            else time.perf_counter() - start
        )

        parsed = parse_response(raw_text, task.family) if raw_text else None
        parsed_answer = parsed.parsed if parsed is not None else None
        reasoning_summary = _reasoning_summary(parsed_answer)

        return ModelResponse(
            task_id=task.task_id,
            agent_name=self.name,
            raw_text=raw_text,
            parsed_answer=parsed_answer,
            reasoning_summary=reasoning_summary,
            usage=_usage(envelope),
            latency_s=latency_s,
            error=error,
            metadata=self._metadata(envelope, parsed),
        )

    def _metadata(self, envelope: object, parsed: object) -> dict[str, object]:
        metadata: dict[str, object] = {
            "agent_backend": "direct",
            "provider": self.client.provider,
            "model": self.client.model,
        }
        if envelope is not None:
            from mimirbench.agents.model_client import ModelResponseEnvelope

            if isinstance(envelope, ModelResponseEnvelope):
                metadata["finish_reason"] = envelope.finish_reason
                metadata["usage"] = envelope.usage.to_dict()
                if envelope.metadata:
                    metadata["backend_metadata"] = envelope.metadata
        if parsed is not None:
            from mimirbench.agents.parsing import ParsedResponse

            if isinstance(parsed, ParsedResponse):
                metadata["parse"] = {
                    "errors": parsed.errors,
                    "repaired": parsed.repaired,
                    "refusal": parsed.refusal,
                    "action": parsed.action,
                }
        return metadata


def _reasoning_summary(parsed_answer: dict[str, object] | None) -> str | None:
    if parsed_answer is None:
        return None
    value = parsed_answer.get("reasoning_summary")
    return value if isinstance(value, str) else None


def _usage(envelope: object) -> Usage | None:
    from mimirbench.agents.model_client import ModelResponseEnvelope

    if not isinstance(envelope, ModelResponseEnvelope):
        return None
    usage = envelope.usage
    if usage.input_tokens is None and usage.output_tokens is None and usage.total_tokens is None:
        return None
    return Usage(
        prompt_tokens=usage.input_tokens,
        completion_tokens=usage.output_tokens,
        total_tokens=usage.total_tokens,
    )
