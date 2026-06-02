"""Hosted-API model agent.

A :class:`~mimirbench.agents.direct_agent.DirectAgent` backed by a hosted-API
:class:`~mimirbench.agents.model_client.ModelClient` (OpenAI, Anthropic, or a
generic OpenAI-compatible HTTP endpoint). The provider SDKs are optional and
imported lazily by the underlying client, so the core harness and tests never
require them.

API keys are read from environment variables by the client and are never passed
through configs or stored in run records.
"""

from __future__ import annotations

from mimirbench.agents.direct_agent import DirectAgent
from mimirbench.agents.model_client import Pricing, RetryConfig
from mimirbench.agents.prompts import DEFAULT_SYSTEM_PROMPT
from mimirbench.agents.providers import build_api_client

__all__ = ["APIModelAgent"]


class APIModelAgent(DirectAgent):
    """Call a hosted chat model. ``model`` is required and has no default."""

    def __init__(
        self,
        model: str,
        *,
        provider: str = "openai",
        name: str | None = None,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        max_retries: int = 3,
        timeout_seconds: float | None = 60.0,
        base_url: str | None = None,
        api_key_env: str | None = None,
        pricing: Pricing | None = None,
        seed: int | None = None,
        top_p: float | None = None,
    ) -> None:
        client = build_api_client(
            provider,
            model,
            base_url=base_url,
            timeout_s=timeout_seconds,
            retry=RetryConfig(max_retries=max_retries),
            pricing=pricing,
            api_key_env=api_key_env,
        )
        super().__init__(
            client,
            name=name or f"api::{provider}::{model}",
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            seed=seed,
            top_p=top_p,
        )
        # Convenience attributes for resolvers/tests; the client owns the SDK.
        self.model = model
        self.provider = provider
        self.max_retries = max_retries
