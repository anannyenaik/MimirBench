"""Tool-using agent loop with per-environment validation and auditing.

:class:`ToolAgent` runs a bounded act/observe loop: a policy proposes either a
tool call or a final answer, every tool request is validated against the
environment's allow-list, allowed calls are executed against the deterministic
:mod:`mimirbench.agents.tools_registry`, and observations are fed back. Each step
(including invalid ones) is recorded as an audit entry on the response metadata,
which the runner persists to ``tool_audit.jsonl`` / ``tool_audit.md``.

Two concrete policies ship here:

* :class:`ReferenceToolAgent` — a deterministic, non-model policy that consults an
  allowed tool and then answers from the tool output (or the environment's public
  reference solver). It is the tool-loop analogue of the reference baseline and is
  fully reproducible, so it anchors the audit/metrics tests.
* :class:`ModelToolAgent` — a model-backed policy that asks a
  :class:`~mimirbench.agents.model_client.ModelClient` to propose tool calls and a
  final answer in JSON.

Safety: the loop never exposes the :class:`~mimirbench.evals.schemas.GradingKey`,
tools are a fixed offline registry (no arbitrary code, no network), and invalid
requests are recorded and skipped rather than executed.
"""

from __future__ import annotations

import json
import time
from abc import abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from mimirbench.agents.base import BaseAgent
from mimirbench.agents.model_client import ModelClient, ModelRequest
from mimirbench.agents.parsing import extract_json, parse_response
from mimirbench.agents.prompts import TOOL_SYSTEM_PROMPT, build_tool_step_prompt
from mimirbench.agents.tools_registry import (
    ToolSpec,
    allowed_tools_for,
    default_tools,
    tool_descriptions,
)
from mimirbench.evals.schemas import EnvironmentFamily, ModelResponse, Task, ToolCall, Usage

__all__ = [
    "DEFAULT_MAX_TOOL_STEPS",
    "ModelToolAgent",
    "ReferenceToolAgent",
    "Tool",
    "ToolAgent",
    "ToolDecision",
]

# Tool calls are intentionally cheap and bounded: a few deterministic steps are
# enough for these tasks, and a small cap keeps cost and audit logs manageable.
DEFAULT_MAX_TOOL_STEPS = 3

# Backwards-compatible alias: the registry's ToolSpec is the canonical tool type.
Tool = ToolSpec


@dataclass
class ToolDecision:
    """The policy's choice at one step: call a tool, or finish.

    Exactly one of ``tool_name`` / ``final`` should be set.
    """

    tool_name: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)
    final: dict[str, Any] | None = None
    reasoning_summary: str | None = None


class ToolAgent(BaseAgent):
    """Bounded tool-use loop over the deterministic tool registry."""

    policy_name = "abstract"

    def __init__(
        self,
        name: str,
        *,
        environment: str,
        tools: dict[str, ToolSpec] | None = None,
        allowed_tools: list[str] | frozenset[str] | None = None,
        max_steps: int = DEFAULT_MAX_TOOL_STEPS,
    ) -> None:
        super().__init__(name)
        if max_steps < 1:
            raise ValueError("max_steps must be >= 1.")
        self.environment = environment
        self.max_steps = max_steps
        self._registry: dict[str, ToolSpec] = tools or default_tools()
        if allowed_tools is None:
            self.allowed_tools: frozenset[str] = allowed_tools_for(environment)
        else:
            self.allowed_tools = frozenset(allowed_tools)

    # -- policy hooks ------------------------------------------------------ #
    @abstractmethod
    def decide(self, task: Task, scratchpad: list[ToolCall]) -> ToolDecision:
        """Choose the next action given the task and prior tool observations."""
        raise NotImplementedError

    def finalize(self, task: Task, scratchpad: list[ToolCall]) -> dict[str, Any] | None:
        """Produce a final answer when the step budget is exhausted (optional)."""
        return None

    def _begin_episode(self) -> None:
        """Reset any per-episode accounting (overridden by model-backed policies)."""

    def _episode_stats(self) -> tuple[Usage | None, float | None, int]:
        """Return (usage, model_latency_ms, n_model_calls) for the last episode."""
        return None, None, 0

    # -- validation -------------------------------------------------------- #
    def validate_tool(self, tool_name: str | None) -> tuple[str, str | None]:
        """Classify a requested tool: allowed / not_allowed / unknown / missing."""
        if not tool_name:
            return "no_tool_requested", "policy produced neither a tool call nor a final answer"
        if tool_name not in self._registry:
            return "unknown_tool", f"unknown tool {tool_name!r}"
        if tool_name not in self.allowed_tools:
            allowed = ", ".join(sorted(self.allowed_tools)) or "(none)"
            return "not_allowed", f"tool {tool_name!r} not allowed for {self.environment}; allowed: {allowed}"
        return "allowed", None

    # -- main loop --------------------------------------------------------- #
    def act(self, task: Task) -> ModelResponse:
        self._begin_episode()
        scratchpad: list[ToolCall] = []
        audit_steps: list[dict[str, Any]] = []
        final: dict[str, Any] | None = None
        last_summary: str | None = None

        wall_start = time.perf_counter()
        for step_number in range(1, self.max_steps + 1):
            decision = self.decide(task, scratchpad)
            last_summary = decision.reasoning_summary or last_summary

            if decision.final is not None:
                final = decision.final
                break

            status, reason = self.validate_tool(decision.tool_name)
            if status != "allowed":
                audit_steps.append(
                    _audit_step(
                        step_number=step_number,
                        requested_tool=decision.tool_name,
                        arguments=decision.arguments,
                        validation_status=status,
                        tool_output=None,
                        tool_error=reason,
                        latency_ms=0.0,
                    )
                )
                continue  # record the invalid request and continue safely.

            spec = self._registry[decision.tool_name]  # type: ignore[index]
            tool_output, tool_error, latency_ms = _execute_tool(spec, decision.arguments)
            scratchpad.append(
                ToolCall(
                    tool_name=spec.name,
                    arguments=decision.arguments,
                    result=tool_output if tool_error is None else {"error": tool_error},
                )
            )
            audit_steps.append(
                _audit_step(
                    step_number=step_number,
                    requested_tool=spec.name,
                    arguments=decision.arguments,
                    validation_status="allowed",
                    tool_output=tool_output,
                    tool_error=tool_error,
                    latency_ms=latency_ms,
                )
            )

        if final is None:
            final = self.finalize(task, scratchpad)
        wall_ms = (time.perf_counter() - wall_start) * 1000.0

        usage, _model_latency_ms, n_model_calls = self._episode_stats()
        error = None if final is not None else "max_steps exceeded without a final answer"
        reasoning_summary = last_summary
        if final is not None and isinstance(final.get("reasoning_summary"), str):
            reasoning_summary = final["reasoning_summary"]

        return ModelResponse(
            task_id=task.task_id,
            agent_name=self.name,
            raw_text=json.dumps(final, sort_keys=True) if final is not None else "",
            parsed_answer=final,
            reasoning_summary=reasoning_summary,
            tool_calls=scratchpad,
            usage=usage,
            latency_s=wall_ms / 1000.0,
            error=error,
            metadata={
                "agent_backend": "tool",
                "tool_policy": self.policy_name,
                "environment": self.environment,
                "allowed_tools": sorted(self.allowed_tools),
                "tool_audit_steps": audit_steps,
                "n_model_calls": n_model_calls,
            },
        )


def _execute_tool(spec: ToolSpec, arguments: dict[str, Any]) -> tuple[Any, str | None, float]:
    start = time.perf_counter()
    try:
        output = spec.fn(**arguments)
        error: str | None = None
    except Exception as exc:  # surface tool errors as observations, not crashes
        output = None
        error = f"{type(exc).__name__}: {exc}"
    latency_ms = (time.perf_counter() - start) * 1000.0
    return output, error, latency_ms


def _audit_step(
    *,
    step_number: int,
    requested_tool: str | None,
    arguments: dict[str, Any],
    validation_status: str,
    tool_output: Any,
    tool_error: str | None,
    latency_ms: float,
) -> dict[str, Any]:
    return {
        "step_number": step_number,
        "requested_tool": requested_tool,
        "tool_arguments": arguments,
        "validation_status": validation_status,
        "tool_output": tool_output,
        "tool_error": tool_error,
        "latency_ms": latency_ms,
    }


def _render_observations(scratchpad: list[ToolCall]) -> str:
    if not scratchpad:
        return ""
    lines = []
    for i, call in enumerate(scratchpad, start=1):
        lines.append(f"{i}. {call.tool_name}({json.dumps(call.arguments, sort_keys=True)}) -> "
                     f"{json.dumps(call.result, sort_keys=True)}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Deterministic reference policy.
# --------------------------------------------------------------------------- #
class ReferenceToolAgent(ToolAgent):
    """Deterministic tool-using baseline: consult a tool, then answer.

    Not a model. It demonstrates and exercises the tool loop and audit trail with
    fully reproducible behaviour, and (for environments whose tool output *is* the
    answer, e.g. Bayesian games and auctions) genuinely derives its final answer
    from the tool result.
    """

    policy_name = "reference"

    def __init__(
        self,
        *,
        environment: str,
        family: EnvironmentFamily,
        reference_solver: Callable[[Task], dict[str, Any]],
        name: str | None = None,
        allowed_tools: list[str] | frozenset[str] | None = None,
        max_steps: int = DEFAULT_MAX_TOOL_STEPS,
    ) -> None:
        super().__init__(
            name or f"tool::reference::{environment}",
            environment=environment,
            allowed_tools=allowed_tools,
            max_steps=max_steps,
        )
        self.family = family
        self._reference_solver = reference_solver

    def decide(self, task: Task, scratchpad: list[ToolCall]) -> ToolDecision:
        if not scratchpad:
            tool_name, arguments = self._representative_call(task)
            if tool_name is not None:
                return ToolDecision(
                    tool_name=tool_name,
                    arguments=arguments,
                    reasoning_summary="Consulting a deterministic tool before answering.",
                )
        return ToolDecision(
            final=self._final_answer(task, scratchpad),
            reasoning_summary="Final answer derived from the tool output and public task data.",
        )

    def finalize(self, task: Task, scratchpad: list[ToolCall]) -> dict[str, Any] | None:
        return self._final_answer(task, scratchpad)

    def _representative_call(self, task: Task) -> tuple[str | None, dict[str, Any]]:
        meta = task.metadata
        fam = self.family
        if fam == EnvironmentFamily.BAYESIAN_GAMES and "bayes_calculator" in self.allowed_tools:
            return "bayes_calculator", {
                "priors": meta.get("priors", []),
                "likelihood": meta.get("likelihood", []),
                "observations": meta.get("observations", []),
            }
        if fam == EnvironmentFamily.AUCTIONS and "auction_solver" in self.allowed_tools:
            return "auction_solver", {
                "your_value": meta.get("your_value", 0.0),
                "n_bidders": meta.get("n_bidders", 1),
                "v_max": meta.get("v_max", 1.0),
            }
        if fam == EnvironmentFamily.HIDDEN_REGIMES and "bayes_calculator" in self.allowed_tools:
            return "bayes_calculator", {
                "priors": meta.get("initial", []),
                "likelihood": meta.get("emission", []),
                "observations": meta.get("observations", []),
            }
        if fam == EnvironmentFamily.ADVERSARIAL_RISK and "risk_checker" in self.allowed_tools:
            return "risk_checker", {
                "position": meta.get("current_exposure", 0.0),
                "proposed_trade": meta.get("proposed_trade", 0.0),
                "realized_pnl": -float(meta.get("current_loss", 0.0)),
                "max_abs_position": meta.get("maximum_allowed_exposure", float("inf")),
                "max_loss": meta.get("maximum_allowed_daily_loss", float("inf")),
            }
        if fam == EnvironmentFamily.MARKET_MAKING and "risk_checker" in self.allowed_tools:
            return "risk_checker", {
                "position": meta.get("inventory", 0.0),
                "proposed_trade": 0.0,
                "realized_pnl": meta.get("current_daily_pnl", 0.0),
                "max_abs_position": meta.get("position_limit", float("inf")),
                "max_loss": meta.get("max_daily_loss", float("inf")),
            }
        if fam == EnvironmentFamily.PREDICTION_MARKETS and "risk_checker" in self.allowed_tools:
            return "risk_checker", {
                "position": meta.get("current_position", 0.0),
                "proposed_trade": 0.0,
                "max_abs_position": meta.get("position_limit", float("inf")),
                "max_loss": meta.get("budget_limit", float("inf")),
            }
        return None, {}

    def _final_answer(self, task: Task, scratchpad: list[ToolCall]) -> dict[str, Any]:
        if self.family == EnvironmentFamily.BAYESIAN_GAMES:
            posterior = _last_tool_value(scratchpad, "bayes_calculator", "posterior")
            if isinstance(posterior, list):
                return {
                    "posterior": posterior,
                    "reasoning_summary": "Posterior computed by the bayes_calculator tool.",
                }
        if self.family == EnvironmentFamily.AUCTIONS:
            surplus = _last_tool_value(scratchpad, "auction_solver", "expected_surplus")
            if isinstance(surplus, (int, float)):
                return {
                    "expected_surplus": float(surplus),
                    "reasoning_summary": "Expected surplus computed by the auction_solver tool.",
                }
        answer = dict(self._reference_solver(task))
        answer.setdefault(
            "reasoning_summary",
            "Answer from the deterministic reference solver, after a tool consult.",
        )
        return answer


def _last_tool_value(scratchpad: list[ToolCall], tool_name: str, key: str) -> Any:
    for call in reversed(scratchpad):
        if call.tool_name == tool_name and isinstance(call.result, dict):
            return call.result.get(key)
    return None


# --------------------------------------------------------------------------- #
# Model-backed policy.
# --------------------------------------------------------------------------- #
class ModelToolAgent(ToolAgent):
    """Model-backed tool policy: the model proposes tool calls and a final answer."""

    policy_name = "model"

    def __init__(
        self,
        client: ModelClient,
        *,
        environment: str,
        family: EnvironmentFamily,
        name: str | None = None,
        allowed_tools: list[str] | frozenset[str] | None = None,
        max_steps: int = DEFAULT_MAX_TOOL_STEPS,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        seed: int | None = None,
        system_prompt: str = TOOL_SYSTEM_PROMPT,
    ) -> None:
        super().__init__(
            name or f"tool::{client.provider}::{client.model}",
            environment=environment,
            allowed_tools=allowed_tools,
            max_steps=max_steps,
        )
        self.client = client
        self.family = family
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.seed = seed
        self.system_prompt = system_prompt
        self._tool_block = tool_descriptions(self.allowed_tools)
        self._prompt_tokens = 0
        self._completion_tokens = 0
        self._model_latency_ms = 0.0
        self._n_model_calls = 0

    def _begin_episode(self) -> None:
        self._prompt_tokens = 0
        self._completion_tokens = 0
        self._model_latency_ms = 0.0
        self._n_model_calls = 0

    def _episode_stats(self) -> tuple[Usage | None, float | None, int]:
        if self._n_model_calls == 0:
            return None, None, 0
        usage = Usage(
            prompt_tokens=self._prompt_tokens or None,
            completion_tokens=self._completion_tokens or None,
            total_tokens=(self._prompt_tokens + self._completion_tokens) or None,
        )
        return usage, self._model_latency_ms, self._n_model_calls

    def _call_model(self, user_prompt: str) -> str:
        request = ModelRequest(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            seed=self.seed,
        )
        envelope = self.client.generate(request)
        self._n_model_calls += 1
        if envelope.usage.input_tokens:
            self._prompt_tokens += envelope.usage.input_tokens
        if envelope.usage.output_tokens:
            self._completion_tokens += envelope.usage.output_tokens
        if envelope.latency_ms:
            self._model_latency_ms += envelope.latency_ms
        return envelope.raw_text

    def decide(self, task: Task, scratchpad: list[ToolCall]) -> ToolDecision:
        prompt = build_tool_step_prompt(
            task,
            tool_block=self._tool_block,
            observations=_render_observations(scratchpad),
        )
        obj = extract_json(self._call_model(prompt)) or {}
        summary = obj.get("reasoning_summary")
        summary = summary if isinstance(summary, str) else None

        tool_name = obj.get("tool")
        if isinstance(tool_name, str):
            arguments = obj.get("arguments")
            return ToolDecision(
                tool_name=tool_name,
                arguments=arguments if isinstance(arguments, dict) else {},
                reasoning_summary=summary,
            )
        final = obj.get("final")
        if isinstance(final, dict):
            if "reasoning_summary" not in final and summary is not None:
                final = {**final, "reasoning_summary": summary}
            return ToolDecision(final=final, reasoning_summary=summary)
        # No recognisable tool call or final wrapper: treat the object as a direct answer.
        return ToolDecision(final=obj or None, reasoning_summary=summary)

    def finalize(self, task: Task, scratchpad: list[ToolCall]) -> dict[str, Any] | None:
        prompt = build_tool_step_prompt(
            task,
            tool_block=self._tool_block,
            observations=_render_observations(scratchpad),
            must_finalize=True,
        )
        parsed = parse_response(self._call_model(prompt), task.family).parsed
        # If the model keeps emitting a tool-call wrapper instead of an answer,
        # there is no usable final answer; terminate safely with no answer.
        if parsed is None or "tool" in parsed:
            return None
        return parsed
