"""Evaluation runner.

The legacy :func:`run_eval` API remains a small single-environment convenience
wrapper. Stage 2 config-driven runs use :func:`run_eval_config`, which writes
structured per-task records, summaries, and Markdown reports.
"""

from __future__ import annotations

import hashlib
import time
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from mimirbench.agents.base import BaseAgent
from mimirbench.agents.resolver import resolve_agent as resolve_agent_from_config
from mimirbench.evals import registry
from mimirbench.evals.cache import ResponseCache, make_cache_key, stable_json_dumps
from mimirbench.evals.registry import EnvironmentSpec
from mimirbench.evals.schemas import (
    AgentConfig,
    EvalConfig,
    EvalReport,
    EvalRunConfig,
    EvalTaskRecord,
    GraderResult,
    ModelResponse,
    TaskInstance,
)
from mimirbench.evals.scoring import aggregate
from mimirbench.evals.tool_audit import (
    aggregate_tool_audit,
    collect_tool_audits,
    has_tool_audit,
    write_tool_audit_jsonl,
    write_tool_audit_markdown,
)
from mimirbench.evals.writers import (
    build_summary,
    load_records_jsonl,
    write_markdown_report,
    write_results_jsonl,
    write_summary_json,
)

__all__ = [
    "iter_instances",
    "load_eval_config",
    "resolve_agent",
    "run_eval",
    "run_eval_config",
    "validate_eval_config",
]


def iter_instances(spec: EnvironmentSpec, n_tasks: int, seed: int) -> Iterator[TaskInstance]:
    """Yield ``n_tasks`` deterministically-seeded task instances."""
    for i in range(n_tasks):
        yield spec.generator(seed + i)


def resolve_agent(config: EvalConfig, spec: EnvironmentSpec) -> BaseAgent:
    """Map legacy ``EvalConfig.agent`` to a concrete agent."""
    return resolve_agent_from_config({"type": config.agent}, spec=spec)


def run_eval(config: EvalConfig, agent: BaseAgent | None = None) -> EvalReport:
    """Run a legacy single-environment evaluation and return an aggregate report."""
    spec = registry.get(config.environment)
    if agent is None:
        agent = resolve_agent(config, spec)

    results: list[GraderResult] = []
    for instance in iter_instances(spec, config.n_tasks, config.seed):
        response = _act_agent(agent, instance)
        result = _grade_or_error(spec, instance, response)
        results.append(result)

    return aggregate(
        results,
        environment=config.environment,
        agent=agent.name,
        seed=config.seed,
    )


def load_eval_config(path: Path) -> EvalRunConfig | EvalConfig:
    """Load either a Stage 2 run config or a legacy single-environment config."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"config {path} must contain a YAML mapping.")
    try:
        if "run" in data or "environments" in data:
            return EvalRunConfig(**data)
        return EvalConfig(**data)
    except ValidationError:
        raise


def validate_eval_config(config: EvalRunConfig | EvalConfig) -> None:
    """Validate registry references and agent construction without running tasks."""
    if isinstance(config, EvalConfig):
        spec = registry.get(config.environment)
        if config.agent != "reference":
            resolve_agent_from_config({"type": config.agent}, spec=spec)
        return

    if not config.environments:
        raise ValueError("config must include at least one environment.")
    first_spec: EnvironmentSpec | None = None
    for environment in config.environments:
        spec = registry.get(environment.name)
        first_spec = first_spec or spec
    assert first_spec is not None
    resolve_agent_from_config(config.agent, spec=first_spec)


def run_eval_config(config: EvalRunConfig) -> dict[str, Any]:
    """Run a Stage 2 evaluation config and write requested artefacts."""
    validate_eval_config(config)
    output_dir = _output_dir(config)
    output_dir.mkdir(parents=True, exist_ok=True)

    existing_records = _recoverable_records(output_dir / "results.jsonl", config.agent)
    existing_by_key = {
        _record_recovery_key(record): record
        for record in existing_records
    }

    timestamp = _utc_timestamp()
    run_id = existing_records[0].run_id if existing_records else _make_run_id(config.run.name, timestamp)
    cache = ResponseCache(
        _cache_path(config, output_dir),
        enabled=config.run.cache,
        bypass=config.run.cache_bypass,
    )
    agent_config_hash = _agent_config_hash(config.agent)

    ordered_records: list[tuple[int, EvalTaskRecord]] = []
    jobs: list[tuple[int, EnvironmentSpec, TaskInstance, BaseAgent]] = []
    global_index = 0

    for env_config in config.environments:
        spec = registry.get(env_config.name)
        agent = resolve_agent_from_config(config.agent, spec=spec)
        env_seed = env_config.seed if env_config.seed is not None else config.run.seed
        for instance in iter_instances(spec, env_config.num_tasks, env_seed):
            recovery_key = (spec.name, instance.task.task_id, config.agent.type.lower(), agent.name)
            recovered = existing_by_key.get(recovery_key)
            if recovered is not None and recovered.metadata.get("agent_config_hash") == agent_config_hash:
                ordered_records.append((global_index, recovered))
            else:
                jobs.append((global_index, spec, instance, agent))
            global_index += 1

    if config.run.max_workers == 1:
        for index, spec, instance, agent in jobs:
            ordered_records.append(
                (
                    index,
                    _evaluate_instance(
                        run_id=run_id,
                        timestamp=timestamp,
                        spec=spec,
                        instance=instance,
                        agent=agent,
                        agent_config=config.agent,
                        agent_config_hash=agent_config_hash,
                        cache=cache,
                    ),
                )
            )
    else:
        with ThreadPoolExecutor(max_workers=config.run.max_workers) as executor:
            futures = {
                executor.submit(
                    _evaluate_instance,
                    run_id=run_id,
                    timestamp=timestamp,
                    spec=spec,
                    instance=instance,
                    agent=agent,
                    agent_config=config.agent,
                    agent_config_hash=agent_config_hash,
                    cache=cache,
                ): index
                for index, spec, instance, agent in jobs
            }
            for future in as_completed(futures):
                ordered_records.append((futures[future], future.result()))

    records = [record for _, record in sorted(ordered_records, key=lambda item: item[0])]
    summary = build_summary(
        config=config,
        run_id=run_id,
        timestamp=timestamp,
        output_dir=output_dir,
        records=records,
    )

    # Tool-use audit artefacts (only when a tool agent recorded steps).
    tool_audits = collect_tool_audits(records) if has_tool_audit(records) else []
    if tool_audits:
        tool_metrics = aggregate_tool_audit(tool_audits)
        summary["tool_audit"] = tool_metrics

    if config.reporting.write_jsonl:
        write_results_jsonl(records, output_dir / "results.jsonl")
    if config.reporting.write_summary:
        write_summary_json(summary, output_dir / "summary.json")
    if config.reporting.write_markdown:
        write_markdown_report(summary=summary, records=records, path=output_dir / "report.md")
    if tool_audits:
        write_tool_audit_jsonl(tool_audits, output_dir / "tool_audit.jsonl")
        write_tool_audit_markdown(
            tool_audits,
            summary["tool_audit"],
            run_name=config.run.name,
            agent=str(summary["agent"].get("name") or "tool"),
            path=output_dir / "tool_audit.md",
        )
    return summary


def _evaluate_instance(
    *,
    run_id: str,
    timestamp: str,
    spec: EnvironmentSpec,
    instance: TaskInstance,
    agent: BaseAgent,
    agent_config: AgentConfig,
    agent_config_hash: str,
    cache: ResponseCache,
) -> EvalTaskRecord:
    task = instance.task
    cache_key = make_cache_key(agent_config=agent_config, environment=spec.name, task=task)
    cache_entry = cache.get(cache_key)
    metadata: dict[str, Any] = {
        "agent_config_hash": agent_config_hash,
        "cache_key": cache_key,
        "cache_hit": cache_entry is not None,
    }

    if cache_entry is not None:
        response = cache_entry.model_response
        metadata.update(cache_entry.metadata)
        latency_ms = response.latency_s * 1000.0 if response.latency_s is not None else 0.0
    else:
        start = time.perf_counter()
        try:
            response = _act_agent(agent, instance)
        except Exception as exc:
            response = ModelResponse(
                task_id=task.task_id,
                agent_name=agent.name,
                raw_text="",
                parsed_answer=None,
                reasoning_summary=None,
                error=f"{type(exc).__name__}: {exc}",
            )
        latency_ms = (
            response.latency_s * 1000.0
            if response.latency_s is not None
            else (time.perf_counter() - start) * 1000.0
        )
        if response.error is None:
            cache.set(
                cache_key,
                response,
                metadata={
                    "environment": spec.name,
                    "task_id": task.task_id,
                    "agent_name": agent.name,
                },
            )

    result = _grade_or_error(spec, instance, response)
    error = response.error
    if result.violations and "runtime_error" in result.violations and error is None:
        error = str(result.details.get("reason", "runtime_error"))

    response_metadata = response.metadata
    if response_metadata:
        metadata["response_metadata"] = response_metadata

    return EvalTaskRecord(
        run_id=run_id,
        timestamp=timestamp,
        environment=spec.name,
        task_id=task.task_id,
        seed=task.seed,
        agent_type=agent_config.type.lower(),
        agent_name=agent.name,
        raw_prompt=task.prompt,
        model_response=response.raw_text,
        parsed_response=response.parsed_answer,
        grader_result=result,
        latency_ms=latency_ms,
        error=error,
        metadata=metadata,
    )


def _act_agent(agent: BaseAgent, instance: TaskInstance) -> ModelResponse:
    act_with_key = getattr(agent, "act_with_key", None)
    if getattr(agent, "diagnostic_uses_grading_key", False) and callable(act_with_key):
        response = act_with_key(instance.task, instance.key)
        if isinstance(response, ModelResponse):
            return response
        raise TypeError("diagnostic act_with_key must return ModelResponse.")
    return agent.act(instance.task)


def _grade_or_error(
    spec: EnvironmentSpec,
    instance: TaskInstance,
    response: ModelResponse,
) -> GraderResult:
    try:
        return spec.grader(instance.task, response, instance.key)
    except Exception as exc:
        return GraderResult(
            task_id=instance.task.task_id,
            family=instance.task.family,
            score=0.0,
            passed=False,
            violations=["runtime_error"],
            details={"reason": f"{type(exc).__name__}: {exc}"},
        )


def _recoverable_records(path: Path, agent_config: AgentConfig) -> list[EvalTaskRecord]:
    if not path.exists():
        return []
    agent_type = agent_config.type.lower()
    return [
        record
        for record in load_records_jsonl(path)
        if record.agent_type == agent_type
    ]


def _record_recovery_key(record: EvalTaskRecord) -> tuple[str, str, str, str]:
    return (record.environment, record.task_id, record.agent_type, record.agent_name)


def _output_dir(config: EvalRunConfig) -> Path:
    if config.run.output_dir:
        return Path(config.run.output_dir)
    return Path("reports") / "runs" / config.run.name


def _cache_path(config: EvalRunConfig, output_dir: Path) -> Path:
    if config.run.cache_path:
        return Path(config.run.cache_path)
    return output_dir / "responses_cache.jsonl"


def _agent_config_hash(agent_config: AgentConfig) -> str:
    return hashlib.sha256(
        stable_json_dumps(agent_config.model_dump(mode="json")).encode("utf-8")
    ).hexdigest()


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _make_run_id(run_name: str, timestamp: str) -> str:
    safe_timestamp = timestamp.replace(":", "").replace("-", "").replace("Z", "")
    safe_name = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in run_name)
    return f"{safe_name}-{safe_timestamp}"
