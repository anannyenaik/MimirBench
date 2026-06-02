"""OpenAI-compatible Chat Completions client.

Implements :class:`~mimirbench.agents.model_client.ModelClient` against any
OpenAI-compatible Chat Completions endpoint. The ``openai`` package is an
optional dependency (``pip install -e ".[api]"``) imported lazily, so importing
this module never requires it. The ``base_url`` is configurable, so OpenAI,
Azure-style gateways, and local OpenAI-compatible servers all work.

The API key is read from the environment (``OPENAI_API_KEY`` by default) and is
never logged or stored in run records.
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

__all__ = ["OpenAIClient"]

_DEFAULT_KEY_ENV = "OPENAI_API_KEY"


class OpenAIClient(ModelClient):
    """Call an OpenAI-compatible chat model with bounded retries."""

    provider = "openai"

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
        organization: str | None = None,
    ) -> None:
        if not model:
            raise ValueError("OpenAIClient requires a non-empty model name.")
        self.model = model
        self.base_url = base_url
        self.timeout_s = timeout_s
        self.retry = retry or RetryConfig()
        self.pricing = pricing
        self.api_key_env = api_key_env
        self._organization = organization
        # Resolve the key once, but never store it in any serialised record.
        self._api_key = api_key or os.environ.get(api_key_env)
        self._client: Any | None = None

    # -- backend wiring ---------------------------------------------------- #
    def _ensure_client(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise ModelClientError(
                "OpenAI support requires the 'api' extra. Install it with: "
                'pip install -e ".[api]"'
            ) from exc
        if not self._api_key:
            raise ModelClientError(
                f"No OpenAI API key found. Set the {self.api_key_env} environment "
                "variable (the key is never read from configs or logged)."
            )
        self._client = OpenAI(
            api_key=self._api_key,
            base_url=self.base_url,
            organization=self._organization,
        )
        return self._client

    def check_availability(self) -> ProviderStatus:
        try:
            import openai  # noqa: F401

            package_available = True
        except ImportError:
            package_available = False
        key_present = bool(self._api_key)
        usable = package_available and key_present
        if not package_available:
            detail = 'openai package not installed (pip install -e ".[api]").'
        elif not key_present:
            detail = f"openai installed but {self.api_key_env} is not set."
        else:
            detail = f"openai installed and {self.api_key_env} is set; appears usable."
        return ProviderStatus(
            provider=self.provider,
            package_available=package_available,
            key_required=True,
            key_present=key_present,
            key_env=self.api_key_env,
            usable=usable,
            detail=detail,
        )

    # -- generation -------------------------------------------------------- #
    def generate(self, request: ModelRequest) -> ModelResponseEnvelope:
        client = self._ensure_client()
        kwargs: dict[str, Any] = {
            "model": self.model,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ],
        }
        if request.seed is not None:
            kwargs["seed"] = request.seed
        if request.top_p is not None:
            kwargs["top_p"] = request.top_p
        if request.stop:
            kwargs["stop"] = request.stop
        if self.timeout_s is not None:
            kwargs["timeout"] = self.timeout_s
        kwargs.update(request.extra)

        start = time.perf_counter()
        response = run_with_retries(
            lambda: client.chat.completions.create(**kwargs),
            retry=self.retry,
        )
        latency_ms = (time.perf_counter() - start) * 1000.0
        return self._to_envelope(response, latency_ms)

    def _to_envelope(self, response: Any, latency_ms: float) -> ModelResponseEnvelope:
        choice = response.choices[0]
        raw_text = choice.message.content or ""
        finish_reason = getattr(choice, "finish_reason", None)
        usage = self._extract_usage(response)
        return ModelResponseEnvelope(
            provider=self.provider,
            model=self.model,
            raw_text=raw_text,
            parsed_json=extract_json(raw_text),
            usage=usage,
            latency_ms=latency_ms,
            finish_reason=finish_reason,
            metadata={"response_id": getattr(response, "id", None)},
        )

    def _extract_usage(self, response: Any) -> ModelUsage:
        raw_usage = getattr(response, "usage", None)
        if raw_usage is None:
            return ModelUsage(estimated_cost_usd=None)
        input_tokens = getattr(raw_usage, "prompt_tokens", None)
        output_tokens = getattr(raw_usage, "completion_tokens", None)
        total_tokens = getattr(raw_usage, "total_tokens", None)
        usage = ModelUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )
        return ModelUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=estimate_cost(usage, self.pricing),
        )
