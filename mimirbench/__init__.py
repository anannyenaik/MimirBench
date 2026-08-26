"""MimirBench: evaluating and interpreting strategic reasoning in LM agents.

The public surface kept here is intentionally small and import-light: the shared
schemas, the eval entry point, and the environment registry. Heavy or optional
functionality (model backends, training, interpretability) lives in subpackages
that import their dependencies lazily.
"""

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

# Single source of truth for the runtime version. Kept in step with the
# ``version`` field in pyproject.toml by tests/test_release_metadata.py.
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
