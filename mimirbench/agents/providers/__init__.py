"""Concrete :class:`~mimirbench.agents.model_client.ModelClient` backends.

Each backend imports its heavy SDK lazily (inside methods), so importing this
package never requires ``openai``, ``anthropic``, ``google-genai``, ``torch`` or
``transformers``.
:func:`build_api_client` maps a provider name to the right client.
"""

from __future__ import annotations

from mimirbench.agents.model_client import (
    ModelClient,
    Pricing,
    ProviderStatus,
    RetryConfig,
)
from mimirbench.agents.providers.anthropic_client import AnthropicClient
from mimirbench.agents.providers.gemini_client import GeminiClient
from mimirbench.agents.providers.generic_http_client import GenericHTTPClient
from mimirbench.agents.providers.hf_local_client import HFLocalClient, resolve_device
from mimirbench.agents.providers.openai_client import OpenAIClient

__all__ = [
    "AnthropicClient",
    "GeminiClient",
    "GenericHTTPClient",
    "HFLocalClient",
    "OpenAIClient",
    "build_api_client",
    "provider_status",
    "resolve_device",
]

SUPPORTED_API_PROVIDERS: tuple[str, ...] = ("openai", "anthropic", "gemini", "generic_http")

# Deterministic, non-model baselines that never call a provider and are always
# "usable". They are diagnostics, not model results; callers must label them.
NON_MODEL_PROVIDERS: tuple[str, ...] = ("reference", "mock")


def provider_status(
    provider: str,
    *,
    base_url: str | None = None,
    api_key_env: str | None = None,
    model: str = "probe",
) -> ProviderStatus:
    """Report whether ``provider`` looks usable, without making any network call.

    This is the single place the leaderboard and the ``check-provider`` CLI use to
    decide whether a real run can proceed. It never reads, prints, or returns an
    API key value, only whether one was found. Unknown providers return an
    unusable status rather than raising, so a config with one bad provider still
    reports cleanly for the others.
    """
    name = provider.lower().strip()
    if name in NON_MODEL_PROVIDERS:
        return ProviderStatus(
            provider=name,
            package_available=True,
            key_required=False,
            key_present=False,
            key_env=None,
            usable=True,
            detail=f"{name} is a deterministic non-model baseline; always available (not a model result).",
        )
    if name == "openai":
        return OpenAIClient(model, api_key_env=api_key_env or "OPENAI_API_KEY").check_availability()
    if name == "anthropic":
        return AnthropicClient(
            model, api_key_env=api_key_env or "ANTHROPIC_API_KEY"
        ).check_availability()
    if name == "gemini":
        return GeminiClient(model, api_key_env=api_key_env or "GEMINI_API_KEY").check_availability()
    if name == "local":
        return HFLocalClient(model).check_availability()
    if name == "generic_http":
        if not base_url:
            return ProviderStatus(
                provider="generic_http",
                package_available=True,
                key_required=False,
                key_present=False,
                key_env=api_key_env,
                usable=False,
                detail="generic_http requires a 'base_url' to be configured.",
            )
        return GenericHTTPClient(
            model, base_url=base_url, api_key_env=api_key_env or "MIMIRBENCH_LLM_API_KEY"
        ).check_availability()
    return ProviderStatus(
        provider=name,
        package_available=False,
        key_required=False,
        key_present=False,
        key_env=None,
        usable=False,
        detail=(
            f"unknown provider {provider!r}. Expected one of: openai, anthropic, gemini, "
            "local, generic_http (or reference/mock baselines)."
        ),
    )


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
    if normalised == "gemini":
        return GeminiClient(
            model,
            base_url=base_url,
            timeout_s=timeout_s,
            retry=retry,
            pricing=pricing,
            api_key_env=api_key_env or "GEMINI_API_KEY",
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
