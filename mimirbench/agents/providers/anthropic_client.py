"""Anthropic Messages API client (optional).

Implements :class:`~mimirbench.agents.model_client.ModelClient` against the
Anthropic Messages API. The ``anthropic`` package is an optional dependency and
is imported lazily; a clear :class:`ModelClientError` is raised if either the
package or the ``ANTHROPIC_API_KEY`` is missing.

Extended/"thinking" output is intentionally **not** enabled: MimirBench requests
only a concise reasoning summary inside the JSON answer and never collects hidden
chain-of-thought.
"""

from __future__ import annotations

import os
import time
from typing import Any

from mimirbench.agents.model_client import (
    ModelClient,
    ModelClientError,
    ModelRequest,
    ModelResponseEnvelope,
    ModelUsage,
    Pricing,
    ProviderStatus,
    RetryConfig,
    estimate_cost,
    run_with_retries,
)
from mimirbench.agents.parsing import extract_json

__all__ = ["AnthropicClient"]

_DEFAULT_KEY_ENV = "ANTHROPIC_API_KEY"


class AnthropicClient(ModelClient):
    """Call an Anthropic chat model with bounded retries."""

    provider = "anthropic"

    def __init__(
        self,
        model: str,
        *,
        api_key: str | None = None,
        api_key_env: str = _DEFAULT_KEY_ENV,
        base_url: str | None = None,
        timeout_s: float | None = 60.0,
        retry: RetryConfig | None = None,
        pricing: Pricing | None = None,
    ) -> None:
        if not model:
            raise ValueError("AnthropicClient requires a non-empty model name.")
        self.model = model
        self.base_url = base_url
        self.timeout_s = timeout_s
        self.retry = retry or RetryConfig()
        self.pricing = pricing
        self.api_key_env = api_key_env
        self._api_key = api_key or os.environ.get(api_key_env)
        self._client: Any | None = None

    def _ensure_client(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            from anthropic import Anthropic
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise ModelClientError(
                "Anthropic support requires the 'anthropic' package. Install it "
                'with: pip install anthropic'
            ) from exc
        if not self._api_key:
            raise ModelClientError(
                f"No Anthropic API key found. Set the {self.api_key_env} environment "
                "variable (the key is never read from configs or logged)."
            )
        kwargs: dict[str, Any] = {"api_key": self._api_key}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        self._client = Anthropic(**kwargs)
        return self._client

    def check_availability(self) -> ProviderStatus:
        try:
            import anthropic  # noqa: F401

            package_available = True
        except ImportError:
            package_available = False
        key_present = bool(self._api_key)
        usable = package_available and key_present
        if not package_available:
            detail = "anthropic package not installed (pip install anthropic)."
        elif not key_present:
            detail = f"anthropic installed but {self.api_key_env} is not set."
        else:
            detail = f"anthropic installed and {self.api_key_env} is set; appears usable."
        return ProviderStatus(
            provider=self.provider,
            package_available=package_available,
            key_required=True,
            key_present=key_present,
            key_env=self.api_key_env,
            usable=usable,
            detail=detail,
        )

    def generate(self, request: ModelRequest) -> ModelResponseEnvelope:
        client = self._ensure_client()
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "system": request.system_prompt,
            "messages": [{"role": "user", "content": request.user_prompt}],
        }
        if request.top_p is not None:
            kwargs["top_p"] = request.top_p
        if request.stop:
            kwargs["stop_sequences"] = request.stop
        if self.timeout_s is not None:
            kwargs["timeout"] = self.timeout_s
        kwargs.update(request.extra)

        start = time.perf_counter()
        response = run_with_retries(
            lambda: client.messages.create(**kwargs),
            retry=self.retry,
        )
        latency_ms = (time.perf_counter() - start) * 1000.0
        return self._to_envelope(response, latency_ms)

    def _to_envelope(self, response: Any, latency_ms: float) -> ModelResponseEnvelope:
        raw_text = self._extract_text(response)
        usage = self._extract_usage(response)
        return ModelResponseEnvelope(
            provider=self.provider,
            model=self.model,
            raw_text=raw_text,
            parsed_json=extract_json(raw_text),
            usage=usage,
            latency_ms=latency_ms,
            finish_reason=getattr(response, "stop_reason", None),
            metadata={"response_id": getattr(response, "id", None)},
        )

    def _extract_text(self, response: Any) -> str:
        blocks = getattr(response, "content", None) or []
        parts: list[str] = []
        for block in blocks:
            text = getattr(block, "text", None)
            if isinstance(text, str):
                parts.append(text)
        return "".join(parts)

    def _extract_usage(self, response: Any) -> ModelUsage:
        raw_usage = getattr(response, "usage", None)
        if raw_usage is None:
            return ModelUsage()
        input_tokens = getattr(raw_usage, "input_tokens", None)
        output_tokens = getattr(raw_usage, "output_tokens", None)
        total = None
        if input_tokens is not None and output_tokens is not None:
            total = input_tokens + output_tokens
        usage = ModelUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total,
        )
        return ModelUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total,
            estimated_cost_usd=estimate_cost(usage, self.pricing),
        )
