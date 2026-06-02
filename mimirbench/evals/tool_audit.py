"""Tool-use audit logs and metrics.

A tool-using agent records one audit entry per step on its response metadata
(``tool_audit_steps``). This module turns those per-task traces into a flat,
auditable log (``tool_audit.jsonl``), a human-readable summary
(``tool_audit.md``), and a small set of deterministic metrics.

Every metric here is computed deterministically from the recorded trace and the
final answer — no model is consulted. In particular
``final_answer_used_tool_result`` is a *heuristic* (numeric overlap between a tool
output and the final answer); it is reported as ``unknown`` (``null``) whenever
the heuristic cannot decide, never guessed.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from mimirbench.evals.schemas import EvalTaskRecord

__all__ = [
    "ToolAuditStep",
    "ToolTaskAudit",
    "aggregate_tool_audit",
    "collect_tool_audits",
    "has_tool_audit",
    "write_tool_audit_jsonl",
    "write_tool_audit_markdown",
]

# Validation statuses that denote an invalid tool request.
_INVALID_STATUSES = frozenset({"not_allowed", "unknown_tool"})


class ToolAuditStep(BaseModel):
    """One row of the flat tool-use audit log."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    task_id: str
    environment: str
    agent: str
    step_number: int
    requested_tool: str | None = None
    tool_arguments: dict[str, Any] = Field(default_factory=dict)
    validation_status: str = "unknown"
    tool_output: Any | None = None
    tool_error: str | None = None
    final_answer_used_tool_result: bool | None = None
    latency_ms: float | None = None


class ToolTaskAudit(BaseModel):
    """The full per-task audit: every step plus the final answer."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    task_id: str
    environment: str
    agent: str
    final_answer: dict[str, Any] | None = None
    steps: list[ToolAuditStep] = Field(default_factory=list)

    @property
    def tool_request_steps(self) -> list[ToolAuditStep]:
        """Steps where the policy actually requested a tool (valid or not)."""
        return [s for s in self.steps if s.validation_status != "no_tool_requested"]

    @property
    def executed_steps(self) -> list[ToolAuditStep]:
        """Steps whose tool was allowed and ran (regardless of tool error)."""
        return [s for s in self.steps if s.validation_status == "allowed"]


def has_tool_audit(records: list[EvalTaskRecord]) -> bool:
    """True if any record carries tool-audit metadata."""
    return any(_raw_steps(record) is not None for record in records)


def collect_tool_audits(records: list[EvalTaskRecord]) -> list[ToolTaskAudit]:
    """Build per-task audits from records that carry tool-audit metadata."""
    audits: list[ToolTaskAudit] = []
    for record in records:
        raw_steps = _raw_steps(record)
        if raw_steps is None:
            continue
        final = record.parsed_response
        steps = [
            _build_step(record, raw, final)
            for raw in raw_steps
            if isinstance(raw, dict)
        ]
        audits.append(
            ToolTaskAudit(
                task_id=record.task_id,
                environment=record.environment,
                agent=record.agent_name,
                final_answer=final,
                steps=steps,
            )
        )
    return audits


def _raw_steps(record: EvalTaskRecord) -> list[Any] | None:
    response_metadata = record.metadata.get("response_metadata")
    if not isinstance(response_metadata, dict):
        return None
    steps = response_metadata.get("tool_audit_steps")
    return steps if isinstance(steps, list) else None


def _build_step(
    record: EvalTaskRecord,
    raw: dict[str, Any],
    final_answer: dict[str, Any] | None,
) -> ToolAuditStep:
    status = str(raw.get("validation_status", "unknown"))
    tool_output = raw.get("tool_output")
    used = (
        _final_used_tool_result(final_answer, tool_output)
        if status == "allowed" and raw.get("tool_error") is None
        else None
    )
    return ToolAuditStep(
        task_id=record.task_id,
        environment=record.environment,
        agent=record.agent_name,
        step_number=int(raw.get("step_number", 0)),
        requested_tool=raw.get("requested_tool"),
        tool_arguments=raw.get("tool_arguments") or {},
        validation_status=status,
        tool_output=tool_output,
        tool_error=raw.get("tool_error"),
        final_answer_used_tool_result=used,
        latency_ms=raw.get("latency_ms"),
    )


def _final_used_tool_result(final: dict[str, Any] | None, tool_output: Any) -> bool | None:
    """Heuristic: did the final answer reuse a numeric value from the tool output?

    Returns ``None`` (unknown) when there is nothing numeric to compare.
    """
    if final is None:
        return None
    output_numbers = _numbers(tool_output)
    if not output_numbers:
        return None
    final_numbers = _numbers(final)
    if not final_numbers:
        return False
    for o in output_numbers:
        for f in final_numbers:
            if math.isclose(o, f, rel_tol=1e-6, abs_tol=1e-9):
                return True
    return False


def _numbers(value: Any) -> list[float]:
    out: list[float] = []
    if isinstance(value, bool):
        return out
    if isinstance(value, (int, float)):
        return [float(value)]
    if isinstance(value, dict):
        for item in value.values():
            out.extend(_numbers(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            out.extend(_numbers(item))
    return out


def aggregate_tool_audit(audits: list[ToolTaskAudit]) -> dict[str, Any]:
    """Compute deterministic tool-use metrics over per-task audits."""
    n_tasks = len(audits)
    if n_tasks == 0:
        return {
            "n_tasks": 0,
            "tool_call_rate": None,
            "invalid_tool_call_rate": None,
            "tool_error_rate": None,
            "mean_tool_steps": None,
            "final_answer_after_tool_rate": None,
            "tool_result_ignored_rate": None,
        }

    tasks_with_call = 0
    tasks_with_call_and_final = 0
    total_request_steps = 0
    invalid_request_steps = 0
    executed_steps = 0
    error_steps = 0
    tasks_with_usable_output = 0
    tasks_ignoring_output = 0

    for audit in audits:
        request_steps = audit.tool_request_steps
        executed = audit.executed_steps
        total_request_steps += len(request_steps)
        invalid_request_steps += sum(1 for s in request_steps if s.validation_status in _INVALID_STATUSES)
        executed_steps += len(executed)
        error_steps += sum(1 for s in executed if s.tool_error is not None)

        if request_steps:
            tasks_with_call += 1
            if audit.final_answer is not None:
                tasks_with_call_and_final += 1

        usable = [s for s in executed if s.tool_error is None and s.final_answer_used_tool_result is not None]
        if usable and audit.final_answer is not None:
            tasks_with_usable_output += 1
            if not any(s.final_answer_used_tool_result for s in usable):
                tasks_ignoring_output += 1

    return {
        "n_tasks": n_tasks,
        "tool_call_rate": tasks_with_call / n_tasks,
        "invalid_tool_call_rate": (
            invalid_request_steps / total_request_steps if total_request_steps else 0.0
        ),
        "tool_error_rate": error_steps / executed_steps if executed_steps else 0.0,
        "mean_tool_steps": total_request_steps / n_tasks,
        "final_answer_after_tool_rate": (
            tasks_with_call_and_final / tasks_with_call if tasks_with_call else None
        ),
        "tool_result_ignored_rate": (
            tasks_ignoring_output / tasks_with_usable_output if tasks_with_usable_output else None
        ),
    }


def write_tool_audit_jsonl(audits: list[ToolTaskAudit], path: Path) -> None:
    """Write one JSON row per tool step to ``tool_audit.jsonl``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for audit in audits:
            for step in audit.steps:
                handle.write(
                    json.dumps(step.model_dump(mode="json"), sort_keys=True, ensure_ascii=False) + "\n"
                )


def write_tool_audit_markdown(
    audits: list[ToolTaskAudit],
    metrics: dict[str, Any],
    *,
    run_name: str,
    agent: str,
    path: Path,
) -> None:
    """Write a human-readable tool-use audit summary to ``tool_audit.md``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Tool-use audit: {run_name}",
        "",
        f"- Agent: `{agent}`",
        f"- Tasks with tool audit: `{metrics['n_tasks']}`",
        "",
        "## Metrics",
        "",
        f"- tool_call_rate: `{_fmt(metrics['tool_call_rate'])}`",
        f"- invalid_tool_call_rate: `{_fmt(metrics['invalid_tool_call_rate'])}`",
        f"- tool_error_rate: `{_fmt(metrics['tool_error_rate'])}`",
        f"- mean_tool_steps: `{_fmt(metrics['mean_tool_steps'])}`",
        f"- final_answer_after_tool_rate: `{_fmt(metrics['final_answer_after_tool_rate'])}`",
        f"- tool_result_ignored_rate: `{_fmt(metrics['tool_result_ignored_rate'])}`",
        "",
        "`tool_result_ignored_rate` and `final_answer_used_tool_result` are deterministic "
        "numeric-overlap heuristics; `unknown`/`null` means the heuristic could not decide.",
        "",
        "## Example tool steps",
        "",
        "| task | step | tool | status | error | used_result |",
        "| --- | ---: | --- | --- | --- | --- |",
    ]
    shown = 0
    for audit in audits:
        for step in audit.steps:
            lines.append(
                f"| `{step.task_id}` | {step.step_number} | `{step.requested_tool}` | "
                f"{step.validation_status} | {step.tool_error or ''} | "
                f"{_fmt_used(step.final_answer_used_tool_result)} |"
            )
            shown += 1
            if shown >= 25:
                break
        if shown >= 25:
            break
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, (int, float)):
        return f"{value:.4g}"
    return str(value)


def _fmt_used(value: bool | None) -> str:
    if value is None:
        return "unknown"
    return "yes" if value else "no"
