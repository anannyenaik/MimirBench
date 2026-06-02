"""Shared data contracts for MimirBench.

These pydantic models are the stable interface between the three moving parts of
the benchmark:

* **environments** produce :class:`TaskInstance` objects (a public :class:`Task`
  plus a private :class:`GradingKey`);
* **agents** consume a :class:`Task` and produce a :class:`ModelResponse`;
* **graders** consume the task, the response, and the key, and produce a
  :class:`GraderResult`.

A deliberate design choice: ground-truth information lives in
:class:`GradingKey`, never in :class:`Task`. Agents are only ever handed the
:class:`Task`, so it is structurally impossible to leak the answer to a model.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EnvironmentFamily(StrEnum):
    """The top-level environment families shipped (or planned) in MimirBench."""

    BAYESIAN_GAMES = "bayesian_games"
    HIDDEN_REGIMES = "hidden_regimes"
    MARKET_MAKING = "market_making"
    AUCTIONS = "auctions"
    PREDICTION_MARKETS = "prediction_markets"
    ADVERSARIAL_RISK = "adversarial_risk"


class Task(BaseModel):
    """A single evaluation task as presented to an agent.

    Everything an agent is allowed to see lives here. ``metadata`` carries the
    machine-readable *problem statement* (e.g. priors and likelihoods) so that
    reference solvers and tool-using agents can operate without re-parsing the
    natural-language ``prompt``. It must never contain the solution.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    task_id: str
    family: EnvironmentFamily
    seed: int
    prompt: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class GradingKey(BaseModel):
    """Private ground-truth payload used only by deterministic graders."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    task_id: str
    payload: dict[str, Any] = Field(default_factory=dict)


class TaskInstance(BaseModel):
    """A task paired with its grading key, as returned by a generator."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    task: Task
    key: GradingKey


class ToolCall(BaseModel):
    """A record of a single tool invocation made by an agent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    result: Any | None = None


class Usage(BaseModel):
    """Token / cost accounting for a model call (best-effort, provider-dependent)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class ModelResponse(BaseModel):
    """The output of an agent for a single task.

    ``reasoning_summary`` is intentionally a *concise, post-hoc summary* of the
    decision rationale. MimirBench never asks models to emit hidden or private
    chain-of-thought, and graders never reward verbose internal reasoning.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    task_id: str
    agent_name: str
    raw_text: str
    parsed_answer: dict[str, Any] | None = None
    reasoning_summary: str | None = None
    tool_calls: list[ToolCall] = Field(default_factory=list)
    usage: Usage | None = None
    latency_s: float | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraderResult(BaseModel):
    """The output of a deterministic grader for a single task.

    ``score`` is the primary scalar (higher is better, conventionally in
    ``[0, 1]``). ``metrics`` holds finer-grained quantities (posterior error,
    expected-value error, regret, ...) that downstream analysis aggregates.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    task_id: str
    family: EnvironmentFamily
    score: float
    passed: bool
    metrics: dict[str, float] = Field(default_factory=dict)
    violations: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class EvalConfig(BaseModel):
    """Declarative configuration for a single evaluation run.

    Legacy single-environment configuration. These objects are still accepted by
    :func:`mimirbench.evals.runner.run_eval` for backwards compatibility; new
    Stage 2 YAML files use :class:`EvalRunConfig` below.
    """

    model_config = ConfigDict(extra="forbid")

    environment: str
    n_tasks: int = Field(default=20, ge=1)
    seed: int = 0
    agent: str = "reference"
    pass_threshold: float | None = None
    output_dir: str | None = None
    notes: str | None = None


class EvalReport(BaseModel):
    """Aggregated outcome of an evaluation run over many tasks."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    environment: str
    agent: str
    n_tasks: int
    seed: int
    mean_score: float
    pass_rate: float
    violation_rate: float
    invalid_response_rate: float = 0.0
    parse_failure_rate: float = 0.0
    runtime_error_rate: float = 0.0
    latency_mean_ms: float | None = None
    latency_p50_ms: float | None = None
    latency_p95_ms: float | None = None
    metric_means: dict[str, float] = Field(default_factory=dict)
    results: list[GraderResult] = Field(default_factory=list)


class AgentConfig(BaseModel):
    """Agent factory configuration for Stage 2 runs.

    Optional model-backend fields live here, but optional packages are imported
    only by the concrete agent when it is actually used.
    """

    model_config = ConfigDict(extra="forbid")

    type: str = "reference"
    name: str | None = None
    behaviour: str | None = None
    seed: int = 0
    provider: str | None = None
    model: str | None = None
    model_name: str | None = None
    device: str | None = None
    temperature: float = 0.0
    top_p: float | None = None
    do_sample: bool | None = None
    max_retries: int = Field(default=3, ge=1)
    timeout_seconds: float | None = Field(default=60.0, gt=0)
    max_tokens: int = Field(default=1024, ge=1)
    max_new_tokens: int = Field(default=512, ge=1)
    base_url: str | None = None
    api_key_env: str | None = None
    pricing: dict[str, float] | None = None
    system_prompt: str | None = None
    backend: dict[str, Any] | None = None
    checkpoint_path: str | None = None
    max_steps: int = Field(default=6, ge=1)
    # Tool-agent options (used when ``type == "tool"``).
    tool_policy: str = "reference"
    tool_max_steps: int = Field(default=3, ge=1)
    allowed_tools: list[str] | None = None
    posterior_noise: float = Field(default=0.0, ge=0.0)
    action_error_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_bias: float = 0.0
    risk_violation_rate: float = Field(default=0.0, ge=0.0, le=1.0)


class RunSettings(BaseModel):
    """Top-level run settings shared by all environments in a config."""

    model_config = ConfigDict(extra="forbid")

    name: str
    seed: int = 0
    output_dir: str | None = None
    cache: bool = False
    cache_bypass: bool = False
    cache_path: str | None = None
    max_workers: int = Field(default=1, ge=1)


class EnvironmentRunConfig(BaseModel):
    """One environment entry inside a Stage 2 run config."""

    model_config = ConfigDict(extra="forbid")

    name: str
    num_tasks: int = Field(default=20, ge=1)
    seed: int | None = None


class ReportingConfig(BaseModel):
    """Which result artefacts to write."""

    model_config = ConfigDict(extra="forbid")

    write_jsonl: bool = True
    write_summary: bool = True
    write_markdown: bool = True
    metrics: list[str] = Field(default_factory=list)


class EvalRunConfig(BaseModel):
    """Stage 2 multi-environment evaluation configuration."""

    model_config = ConfigDict(extra="forbid")

    run: RunSettings
    agent: AgentConfig = Field(default_factory=AgentConfig)
    environments: list[EnvironmentRunConfig] = Field(min_length=1)
    reporting: ReportingConfig = Field(default_factory=ReportingConfig)


class RobustnessEnvironmentConfig(BaseModel):
    """One environment entry inside a robustness run config."""

    model_config = ConfigDict(extra="forbid")

    name: str
    num_tasks: int = Field(default=20, ge=1)
    seed: int | None = None
    variants_per_task: int = Field(default=4, ge=1)
    variant_types: list[str] = Field(default_factory=list)


class RobustnessOptions(BaseModel):
    """Behavioural options for a robustness run."""

    model_config = ConfigDict(extra="forbid")

    answer_preserving_only: bool = False
    max_variants_per_task: int = Field(default=4, ge=1)
    include_base_records: bool = True
    extract_failure_cases: bool = True
    max_failure_cases: int = Field(default=25, ge=1)


class RobustnessReportingConfig(BaseModel):
    """Which robustness artefacts to write."""

    model_config = ConfigDict(extra="forbid")

    write_jsonl: bool = True
    write_summary: bool = True
    write_markdown: bool = True
    write_failure_cases: bool = True


class RobustnessRunConfig(BaseModel):
    """Top-level robustness evaluation configuration."""

    model_config = ConfigDict(extra="forbid")

    run: RunSettings
    agent: AgentConfig = Field(default_factory=AgentConfig)
    environments: list[RobustnessEnvironmentConfig] = Field(min_length=1)
    robustness: RobustnessOptions = Field(default_factory=RobustnessOptions)
    reporting: RobustnessReportingConfig = Field(default_factory=RobustnessReportingConfig)


class RobustnessRecord(BaseModel):
    """Serialisable per-variant record written to ``robustness_results.jsonl``.

    A record with ``variant_id is None`` and ``variant_type is None`` represents
    the *base* task (emitted only when ``include_base_records`` is set).
    """

    model_config = ConfigDict(frozen=True, extra="forbid", protected_namespaces=())

    run_id: str
    timestamp: str
    environment: str
    parent_task_id: str
    variant_id: str | None = None
    variant_type: str | None = None
    answer_preserving: bool
    base_score: float
    variant_score: float
    score_delta: float
    base_action: str | None = None
    variant_action: str | None = None
    action_changed: bool = False
    became_invalid: bool = False
    became_unsafe: bool = False
    pressure_susceptibility: float | None = None
    base_passed: bool = False
    variant_passed: bool = False
    base_violations: list[str] = Field(default_factory=list)
    variant_violations: list[str] = Field(default_factory=list)
    base_response: str = ""
    variant_response: str = ""
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvalTaskRecord(BaseModel):
    """Serialisable per-task record written to ``results.jsonl``."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        protected_namespaces=(),
    )

    run_id: str
    timestamp: str
    environment: str
    task_id: str
    seed: int
    agent_type: str
    agent_name: str
    raw_prompt: str
    model_response: str
    parsed_response: dict[str, Any] | None = None
    grader_result: GraderResult
    latency_ms: float | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
