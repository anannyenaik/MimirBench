"""Public, import-light interfaces for MimirBench."""

from mimirbench.evals.registry import environment_names
from mimirbench.evals.runner import run_eval, run_eval_config
from mimirbench.evals.schemas import (
    AgentConfig,
    EnvironmentFamily,
    EnvironmentRunConfig,
    EvalConfig,
    EvalReport,
    EvalRunConfig,
    EvalTaskRecord,
    GraderResult,
    ModelResponse,
    ReportingConfig,
    RunSettings,
    Task,
    TaskInstance,
)

# Keep the runtime and package metadata versions in sync.
__version__ = "0.2.0"

__all__ = [
    "AgentConfig",
    "EnvironmentFamily",
    "EnvironmentRunConfig",
    "EvalConfig",
    "EvalReport",
    "EvalRunConfig",
    "EvalTaskRecord",
    "GraderResult",
    "ModelResponse",
    "ReportingConfig",
    "RunSettings",
    "Task",
    "TaskInstance",
    "__version__",
    "environment_names",
    "run_eval",
    "run_eval_config",
]
