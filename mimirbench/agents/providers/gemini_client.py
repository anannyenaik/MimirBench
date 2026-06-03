"""Google Gemini API client (optional).

Implements :class:`~mimirbench.agents.model_client.ModelClient` against the
Gemini Developer API using the official ``google-genai`` SDK. The package is an
optional dependency and imported lazily; API keys are read only from the
environment and are never logged or written to run records.
"""

from __future__ import annotations

import os
import time
from enum import Enum
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

__all__ = ["GeminiClient"]

_DEFAULT_KEY_ENV = "GEMINI_API_KEY"


class GeminiClient(ModelClient):
    """Call a Google Gemini model with bounded retries."""

    provider = "gemini"

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
            raise ValueError("GeminiClient requires a non-empty model name.")
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
            from google import genai
            from google.genai import types
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise ModelClientError(
                "Gemini support requires the 'google-genai' package. Install it "
                "with: pip install google-genai"
            ) from exc
        if not self._api_key:
            raise ModelClientError(
                f"No Gemini API key found. Set the {self.api_key_env} environment "
                "variable (the key is never read from configs or logged)."
            )

        http_options = None
        if self.base_url or self.timeout_s is not None:
            kwargs: dict[str, Any] = {}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            if self.timeout_s is not None:
                kwargs["timeout"] = int(self.timeout_s * 1000)
            http_options = types.HttpOptions(**kwargs)
        self._client = genai.Client(api_key=self._api_key, http_options=http_options)
        return self._client

    def check_availability(self) -> ProviderStatus:
        try:
            from google import genai  # noqa: F401

            package_available = True
        except ImportError:
            package_available = False
        key_present = bool(self._api_key)
        usable = package_available and key_present
        if not package_available:
            detail = "google-genai package not installed (pip install google-genai)."
        elif not key_present:
            detail = f"google-genai installed but {self.api_key_env} is not set."
        else:
            detail = f"google-genai installed and {self.api_key_env} is set; appears usable."
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
        config = self._build_config(request)

        start = time.perf_counter()
        response = run_with_retries(
            lambda: client.models.generate_content(
                model=self.model,
                contents=request.user_prompt,
                config=config,
            ),
            retry=self.retry,
        )
        latency_ms = (time.perf_counter() - start) * 1000.0
        return self._to_envelope(response, latency_ms)

    def _build_config(self, request: ModelRequest) -> Any:
        try:
            from google.genai import types
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise ModelClientError(
                "Gemini support requires the 'google-genai' package. Install it "
                "with: pip install google-genai"
            ) from exc

        extra = dict(request.extra)
        use_default_temperature = bool(extra.pop("use_default_temperature", False))
        kwargs: dict[str, Any] = {
            "system_instruction": request.system_prompt,
            "max_output_tokens": request.max_tokens,
        }
        if not use_default_temperature:
            kwargs["temperature"] = request.temperature
        if request.top_p is not None:
            kwargs["top_p"] = request.top_p
        if request.seed is not None:
            kwargs["seed"] = request.seed
        if request.stop:
            kwargs["stop_sequences"] = request.stop
        kwargs.update(extra)
        return types.GenerateContentConfig(**kwargs)

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
            finish_reason=self._finish_reason(response),
            metadata=self._metadata(response),
        )

    def _extract_text(self, response: Any) -> str:
        try:
            text = getattr(response, "text", None)
        except Exception:
            text = None
        if isinstance(text, str):
            return text

        parts: list[str] = []
        for candidate in getattr(response, "candidates", None) or []:
            content = getattr(candidate, "content", None)
            for part in getattr(content, "parts", None) or []:
                part_text = getattr(part, "text", None)
                if isinstance(part_text, str):
                    parts.append(part_text)
        return "".join(parts)

    def _extract_usage(self, response: Any) -> ModelUsage:
        raw_usage = getattr(response, "usage_metadata", None)
        if raw_usage is None:
            return ModelUsage()
        input_tokens = _int_or_none(getattr(raw_usage, "prompt_token_count", None))
        visible_output_tokens = _int_or_none(getattr(raw_usage, "candidates_token_count", None))
        thoughts_tokens = _int_or_none(getattr(raw_usage, "thoughts_token_count", None))
        output_tokens = _sum_tokens(visible_output_tokens, thoughts_tokens)
        total_tokens = _int_or_none(getattr(raw_usage, "total_token_count", None))
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

    def _finish_reason(self, response: Any) -> str | None:
        candidates = getattr(response, "candidates", None) or []
        if not candidates:
            return None
        return _stringify(getattr(candidates[0], "finish_reason", None))

    def _metadata(self, response: Any) -> dict[str, Any]:
        raw_usage = getattr(response, "usage_metadata", None)
        metadata: dict[str, Any] = {
            "response_id": getattr(response, "response_id", None),
            "model_version": getattr(response, "model_version", None),
        }
        if raw_usage is not None:
            metadata["visible_output_tokens"] = _int_or_none(
                getattr(raw_usage, "candidates_token_count", None)
            )
            metadata["thinking_tokens"] = _int_or_none(
                getattr(raw_usage, "thoughts_token_count", None)
            )
        candidates = getattr(response, "candidates", None) or []
        if candidates:
            finish_message = getattr(candidates[0], "finish_message", None)
            if isinstance(finish_message, str):
                metadata["finish_message"] = finish_message
        return {key: value for key, value in metadata.items() if value is not None}


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return None


def _sum_tokens(*values: int | None) -> int | None:
    present = [value for value in values if value is not None]
    return sum(present) if present else None


def _stringify(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)
