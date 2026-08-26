"""Robustness evaluation runner.

Generates base tasks, derives controlled variants, runs the selected agent on
both, grades everything deterministically, compares base versus variant
behaviour, computes robustness metrics, extracts failure cases, and writes the
structured artefacts.

Like the standard runner, this module only ever hands an agent a
:class:`~mimirbench.evals.schemas.Task`; grading keys are used solely by the
deterministic graders. Reference and mock agents are supported out of the box;
real-model agents plug in through the same :func:`resolve_agent` path without any
changes here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from mimirbench.agents.base import BaseAgent
from mimirbench.agents.resolver import resolve_agent
from mimirbench.analysis.robustness import PRESSURE_VARIANT_TYPES, compute_robustness_metrics
from mimirbench.artefacts import make_run_id, utc_timestamp
from mimirbench.evals import registry
from mimirbench.evals.cache import ResponseCache, make_cache_key
from mimirbench.evals.registry import EnvironmentSpec
from mimirbench.evals.schemas import (
    AgentConfig,
    GraderResult,
    ModelResponse,
    RobustnessRecord,
    RobustnessRunConfig,
    Task,
    TaskInstance,
)
from mimirbench.evals.scoring import canonical_action, is_invalid, is_risk_violation, is_unsafe
from mimirbench.evals.variants import (
    VariantGenerator,
    VariantType,
    applicable_variant_types,
)
from mimirbench.evals.writers import (
    build_robustness_summary,
    write_failure_cases_jsonl,
    write_failure_cases_markdown,
    write_robustness_report,
    write_robustness_results_jsonl,
    write_robustness_summary_json,
)

__all__ = [
    "load_robustness_config",
    "run_robustness_config",
    "validate_robustness_config",
]


def load_robustness_config(path: Path) -> RobustnessRunConfig:
    """Load and validate a robustness YAML config."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"config {path} must contain a YAML mapping.")
    return RobustnessRunConfig(**data)


def validate_robustness_config(config: RobustnessRunConfig) -> None:
    """Validate registry references, agent construction, and variant types."""
    first_spec: EnvironmentSpec | None = None
    for env in config.environments:
        spec = registry.get(env.name)
        first_spec = first_spec or spec
        applicable = {vt.value for vt in applicable_variant_types(env.name)}
        for raw in env.variant_types:
            try:
                vtype = VariantType(raw)
            except ValueError as exc:
                raise ValueError(
                    f"unknown variant type {raw!r} for environment {env.name!r}."
                ) from exc
            if vtype.value not in applicable:
                raise ValueError(
                    f"variant type {raw!r} is not defined for environment {env.name!r}. "
                    f"Available: {sorted(applicable)}"
                )
    assert first_spec is not None
    resolve_agent(config.agent, spec=first_spec)


def run_robustness_config(config: RobustnessRunConfig) -> dict[str, Any]:
    """Run a robustness config and write requested artefacts; return the summary."""
    validate_robustness_config(config)
    output_dir = _output_dir(config)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = utc_timestamp()
    run_id = make_run_id(config.run.name, timestamp)
    cache = ResponseCache(
        _cache_path(config, output_dir),
        enabled=config.run.cache,
        bypass=config.run.cache_bypass,
    )

    records: list[RobustnessRecord] = []
    n_base_tasks = 0
    agent_name = config.agent.name or config.agent.type

    for env in config.environments:
        spec = registry.get(env.name)
        agent = resolve_agent(config.agent, spec=spec)
        agent_name = agent.name
        env_seed = env.seed if env.seed is not None else config.run.seed
        requested = _requested_types(env.variant_types)
        generator = VariantGenerator(env.name, seed=env_seed)

        for i in range(env.num_tasks):
            instance = spec.generator(env_seed + i)
            n_base_tasks += 1
            base = _BaseOutcome.build(
                agent,
                spec,
                instance,
                agent_config=config.agent,
                cache=cache,
            )

            if config.robustness.include_base_records:
                records.append(_base_record(run_id, timestamp, env.name, base))

            variants = generator.generate(
                instance,
                variant_types=requested,
                max_variants=min(env.variants_per_task, config.robustness.max_variants_per_task),
                answer_preserving_only=config.robustness.answer_preserving_only,
            )
            for variant in variants:
                records.append(
                    _variant_record(
                        run_id=run_id,
                        timestamp=timestamp,
                        agent=agent,
                        spec=spec,
                        base=base,
                        variant=variant,
                        agent_config=config.agent,
                        cache=cache,
                    )
                )

    metrics = compute_robustness_metrics(records)
    summary = build_robustness_summary(
        config=config,
        run_id=run_id,
        timestamp=timestamp,
        output_dir=output_dir,
        agent_name=agent_name,
        n_base_tasks=n_base_tasks,
        records=records,
        metrics=metrics,
    )

    failure_cases: list[dict[str, Any]] = []
    if config.robustness.extract_failure_cases:
        # Imported here to keep the analysis dependency lazy for plain runs.
        from mimirbench.analysis.failure_cases import extract_failure_cases

        failure_cases = extract_failure_cases(records, limit=config.robustness.max_failure_cases)
        summary["n_failure_cases"] = len(failure_cases)

    if config.reporting.write_jsonl:
        write_robustness_results_jsonl(records, output_dir / "robustness_results.jsonl")
    if config.reporting.write_summary:
        write_robustness_summary_json(summary, output_dir / "robustness_summary.json")
    if config.reporting.write_markdown:
        write_robustness_report(
            summary=summary,
            failure_cases=failure_cases,
            path=output_dir / "robustness_report.md",
        )
    if config.reporting.write_failure_cases and config.robustness.extract_failure_cases:
        write_failure_cases_jsonl(failure_cases, output_dir / "failure_cases.jsonl")
        write_failure_cases_markdown(
            failure_cases,
            summary=summary,
            path=output_dir / "failure_cases.md",
        )
    return summary


class _BaseOutcome:
    """The graded base-task outcome, cached for reuse across its variants."""

    __slots__ = (
        "action",
        "cache_hit",
        "instance",
        "invalid",
        "response",
        "result",
        "risk_violation",
        "unsafe",
    )

    def __init__(
        self,
        instance: TaskInstance,
        response: ModelResponse,
        result: GraderResult,
        *,
        cache_hit: bool,
    ) -> None:
        self.instance = instance
        self.response = response
        self.result = result
        self.action = canonical_action(instance.task.family, response.parsed_answer)
        self.invalid = is_invalid(result)
        self.unsafe = is_unsafe(result)
        self.risk_violation = is_risk_violation(result)
        self.cache_hit = cache_hit

    @classmethod
    def build(
        cls,
        agent: BaseAgent,
        spec: EnvironmentSpec,
        instance: TaskInstance,
        *,
        agent_config: AgentConfig,
        cache: ResponseCache,
    ) -> _BaseOutcome:
        response, cache_hit = _run_agent_cached(
            agent,
            instance,
            agent_config=agent_config,
            environment=spec.name,
            cache=cache,
        )
        result = _grade(spec, instance, response)
        return cls(instance, response, result, cache_hit=cache_hit)


def _variant_record(
    *,
    run_id: str,
    timestamp: str,
    agent: BaseAgent,
    spec: EnvironmentSpec,
    base: _BaseOutcome,
    variant: Any,
    agent_config: AgentConfig,
    cache: ResponseCache,
) -> RobustnessRecord:
    instance = variant.instance
    spec_meta = variant.spec
    response, cache_hit = _run_agent_cached(
        agent,
        instance,
        agent_config=agent_config,
        environment=spec.name,
        cache=cache,
    )
    result = _grade(spec, instance, response)

    action = canonical_action(instance.task.family, response.parsed_answer)
    invalid = is_invalid(result)
    unsafe = is_unsafe(result)
    risk_violation = is_risk_violation(result)

    action_changed = base.action != action
    became_invalid = invalid and not base.invalid
    became_unsafe = unsafe and not base.unsafe
    became_risk_violation = risk_violation and not base.risk_violation
    score_delta = result.score - base.result.score

    pressure = _pressure_susceptibility(
        variant_type=spec_meta.variant_type,
        answer_preserving=spec_meta.answer_preserving,
        action_changed=action_changed,
        became_unsafe=became_unsafe,
        drop=base.result.score - result.score,
        variant_metrics=result.metrics,
    )
    notes = _notes(
        spec_meta=spec_meta,
        action_changed=action_changed,
        became_invalid=became_invalid,
        became_unsafe=became_unsafe,
    )

    return RobustnessRecord(
        run_id=run_id,
        timestamp=timestamp,
        environment=spec.name,
        seed=base.instance.task.seed,
        parent_task_id=spec_meta.parent_task_id,
        variant_id=spec_meta.variant_id,
        variant_type=spec_meta.variant_type.value,
        answer_preserving=spec_meta.answer_preserving,
        base_score=base.result.score,
        variant_score=result.score,
        score_delta=score_delta,
        base_action=base.action,
        variant_action=action,
        action_changed=action_changed,
        became_invalid=became_invalid,
        became_unsafe=became_unsafe,
        pressure_susceptibility=pressure,
        base_passed=base.result.passed,
        variant_passed=result.passed,
        base_violations=list(base.result.violations),
        variant_violations=list(result.violations),
        base_response=base.response.raw_text[:600],
        variant_response=response.raw_text[:600],
        notes=notes,
        metadata={
            "became_risk_violation": became_risk_violation,
            "transformation_description": spec_meta.transformation_description,
            "expected_invariance": spec_meta.expected_invariance,
            "base_prompt": base.instance.task.prompt,
            "variant_prompt": instance.task.prompt,
            "base_metrics": dict(base.result.metrics),
            "variant_metrics": dict(result.metrics),
            "variant_confidence": _confidence(response.parsed_answer),
            "variant_tool_calls": len(response.tool_calls),
            "base_cache_hit": base.cache_hit,
            "variant_cache_hit": cache_hit,
            "base_response_metadata": dict(base.response.metadata),
            "variant_response_metadata": dict(response.metadata),
        },
    )


def _base_record(
    run_id: str,
    timestamp: str,
    environment: str,
    base: _BaseOutcome,
) -> RobustnessRecord:
    return RobustnessRecord(
        run_id=run_id,
        timestamp=timestamp,
        environment=environment,
        seed=base.instance.task.seed,
        parent_task_id=base.instance.task.task_id,
        variant_id=None,
        variant_type=None,
        answer_preserving=True,
        base_score=base.result.score,
        variant_score=base.result.score,
        score_delta=0.0,
        base_action=base.action,
        variant_action=base.action,
        action_changed=False,
        became_invalid=False,
        became_unsafe=False,
        pressure_susceptibility=None,
        base_passed=base.result.passed,
        variant_passed=base.result.passed,
        base_violations=list(base.result.violations),
        variant_violations=list(base.result.violations),
        base_response=base.response.raw_text[:600],
        variant_response=base.response.raw_text[:600],
        notes=["base task"],
        metadata={
            "is_base": True,
            "cache_hit": base.cache_hit,
            "response_metadata": dict(base.response.metadata),
        },
    )


def _pressure_susceptibility(
    *,
    variant_type: VariantType,
    answer_preserving: bool,
    action_changed: bool,
    became_unsafe: bool,
    drop: float,
    variant_metrics: dict[str, float],
) -> float | None:
    if variant_type.value not in PRESSURE_VARIANT_TYPES:
        return None
    metric = variant_metrics.get("pressure_susceptibility")
    if metric is not None:
        return float(max(0.0, min(1.0, metric)))
    signals = [max(0.0, min(1.0, drop))]
    if answer_preserving and action_changed:
        signals.append(1.0)
    if became_unsafe:
        signals.append(1.0)
    return max(signals)


def _notes(
    *,
    spec_meta: Any,
    action_changed: bool,
    became_invalid: bool,
    became_unsafe: bool,
) -> list[str]:
    notes: list[str] = [spec_meta.transformation_description]
    if became_unsafe:
        notes.append("Variant became unsafe though the base was safe.")
    if became_invalid:
        notes.append("Variant produced an invalid/unparseable answer though the base was valid.")
    if spec_meta.answer_preserving and action_changed:
        notes.append("Action flipped under an answer-preserving transformation.")
    return notes


def _confidence(parsed: dict[str, Any] | None) -> float | None:
    if not parsed:
        return None
    value = parsed.get("confidence")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _run_agent(agent: BaseAgent, instance: TaskInstance) -> ModelResponse:
    act_with_key = getattr(agent, "act_with_key", None)
    try:
        if getattr(agent, "diagnostic_uses_grading_key", False) and callable(act_with_key):
            response = act_with_key(instance.task, instance.key)
            if not isinstance(response, ModelResponse):
                raise TypeError("diagnostic act_with_key must return ModelResponse.")
            return response
        return agent.act(instance.task)
    except Exception as exc:
        return ModelResponse(
            task_id=instance.task.task_id,
            agent_name=agent.name,
            raw_text="",
            parsed_answer=None,
            error=f"{type(exc).__name__}: {exc}",
        )


def _run_agent_cached(
    agent: BaseAgent,
    instance: TaskInstance,
    *,
    agent_config: AgentConfig,
    environment: str,
    cache: ResponseCache,
) -> tuple[ModelResponse, bool]:
    cache_key = make_cache_key(
        agent_config=agent_config,
        environment=environment,
        task=instance.task,
    )
    cache_entry = cache.get(cache_key)
    if cache_entry is not None:
        return cache_entry.model_response, True

    response = _run_agent(agent, instance)
    if response.error is None:
        cache.set(
            cache_key,
            response,
            metadata={
                "environment": environment,
                "task_id": instance.task.task_id,
                "agent_name": agent.name,
            },
        )
    return response, False


def _grade(spec: EnvironmentSpec, instance: TaskInstance, response: ModelResponse) -> GraderResult:
    try:
        return spec.grader(instance.task, response, instance.key)
    except Exception as exc:
        return _error_result(instance.task, exc)


def _error_result(task: Task, exc: Exception) -> GraderResult:
    return GraderResult(
        task_id=task.task_id,
        family=task.family,
        score=0.0,
        passed=False,
        violations=["runtime_error"],
        details={"reason": f"{type(exc).__name__}: {exc}"},
    )


def _requested_types(raw_types: list[str]) -> list[VariantType] | None:
    if not raw_types:
        return None
    return [VariantType(value) for value in raw_types]


def _output_dir(config: RobustnessRunConfig) -> Path:
    if config.run.output_dir:
        return Path(config.run.output_dir)
    return Path("reports") / "runs" / config.run.name


def _cache_path(config: RobustnessRunConfig, output_dir: Path) -> Path:
    if config.run.cache_path:
        return Path(config.run.cache_path)
    return output_dir / "responses_cache.jsonl"
