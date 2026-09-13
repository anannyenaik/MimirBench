"""Agents: map a task to a response under a single, swappable interface.

The model backends (``local``/``api``/``tool``) import their heavy optional
dependencies lazily, so importing this package never requires ``torch``,
``openai``, ``anthropic``, or ``google-genai``.
"""

from mimirbench.agents.api_model_agent import APIModelAgent
from mimirbench.agents.base import BaseAgent, ReferenceAgent, extract_json_object
from mimirbench.agents.direct_agent import DirectAgent
from mimirbench.agents.local_model_agent import LocalModelAgent
from mimirbench.agents.mock_agents import AlwaysAbstainAgent, NoisyReferenceAgent, RandomValidAgent
from mimirbench.agents.model_client import (
    ModelClient,
    ModelClientError,
    ModelRequest,
    ModelResponseEnvelope,
    ModelUsage,
    Pricing,
    ProviderStatus,
    RetryConfig,
)
from mimirbench.agents.reflective_agent import ReflectiveAgent
from mimirbench.agents.resolver import resolve_agent
from mimirbench.agents.small_transformer_agent import SmallTransformerAgent
from mimirbench.agents.tool_agent import (
    ModelToolAgent,
    ReferenceToolAgent,
    Tool,
    ToolAgent,
    ToolDecision,
)
from mimirbench.agents.tools_registry import ToolSpec

__all__ = [
    "APIModelAgent",
    "AlwaysAbstainAgent",
    "BaseAgent",
    "DirectAgent",
    "LocalModelAgent",
    "ModelClient",
    "ModelClientError",
    "ModelRequest",
    "ModelResponseEnvelope",
    "ModelToolAgent",
    "ModelUsage",
    "NoisyReferenceAgent",
    "Pricing",
    "ProviderStatus",
    "RandomValidAgent",
    "ReferenceAgent",
    "ReferenceToolAgent",
    "ReflectiveAgent",
    "RetryConfig",
    "SmallTransformerAgent",
    "Tool",
    "ToolAgent",
    "ToolDecision",
    "ToolSpec",
    "extract_json_object",
    "resolve_agent",
]
