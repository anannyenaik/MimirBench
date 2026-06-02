"""Concrete :class:`~mimirbench.agents.model_client.ModelClient` backends.

Each backend imports its heavy SDK lazily (inside methods), so importing this
package never requires ``openai``, ``anthropic``, ``torch`` or ``transformers``.
:func:`build_api_client` maps a provider name to the right client.
"""

from __future__ import annotations

from mimirbench.agents.model_client import ModelClient, Pricing, RetryConfig
from mimirbench.agents.providers.anthropic_client import AnthropicClient
from mimirbench.agents.providers.generic_http_client import GenericHTTPClient
from mimirbench.agents.providers.hf_local_client import HFLocalClient, resolve_device
from mimirbench.agents.providers.openai_client import OpenAIClient

__all__ = [
    "AnthropicClient",
    "GenericHTTPClient",
    "HFLocalClient",
    "OpenAIClient",
    "build_api_client",
    "resolve_device",
]

SUPPORTED_API_PROVIDERS: tuple[str, ...] = ("openai", "anthropic", "generic_http")


def build_api_client(
    provider: str,
    model: str,
    *,
    base_url: str | None = None,
    timeout_s: float | None = 60.0,
    retry: RetryConfig | None = None,
    pricing: Pricing | None = None,
    api_key_env: str | None = None,
) -> ModelClient:
    """Construct an API-backed model client for ``provider``.

    Raises ``ValueError`` for unknown providers. No SDK is imported here; the
    returned client imports it lazily on first use.
    """
    normalised = provider.lower().strip()
    if normalised == "openai":
        return OpenAIClient(
            model,
            base_url=base_url,
            timeout_s=timeout_s,
            retry=retry,
            pricing=pricing,
            api_key_env=api_key_env or "OPENAI_API_KEY",
        )
    if normalised == "anthropic":
        return AnthropicClient(
            model,
            base_url=base_url,
            timeout_s=timeout_s,
            retry=retry,
            pricing=pricing,
            api_key_env=api_key_env or "ANTHROPIC_API_KEY",
        )
    if normalised == "generic_http":
        if not base_url:
            raise ValueError("provider 'generic_http' requires a 'base_url'.")
        return GenericHTTPClient(
            model,
            base_url=base_url,
            timeout_s=timeout_s,
            retry=retry,
            pricing=pricing,
            api_key_env=api_key_env or "MIMIRBENCH_LLM_API_KEY",
        )
    raise ValueError(
        f"unsupported api provider {provider!r}. Supported: {', '.join(SUPPORTED_API_PROVIDERS)}."
    )
