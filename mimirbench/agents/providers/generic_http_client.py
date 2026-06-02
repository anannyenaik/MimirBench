"""Generic OpenAI-compatible HTTP client (scaffold).

A minimal, dependency-free fallback for self-hosted or third-party endpoints that
speak the OpenAI Chat Completions JSON shape but for which the ``openai`` SDK is
unavailable or undesirable. It uses only the Python standard library
(``urllib``) and is intentionally small — it is a scaffold, not a full SDK.

The endpoint URL and key environment variable are configurable. The key is read
from the environment and never logged. A clear :class:`ModelClientError` is
raised on transport or decode failures.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
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

__all__ = ["GenericHTTPClient"]


class _HTTPStatusError(RuntimeError):
    """Carries an HTTP status code so the retry policy can classify it."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code


class GenericHTTPClient(ModelClient):
    """POST an OpenAI-style chat payload to a configurable endpoint."""

    provider = "generic_http"

    def __init__(
        self,
        model: str,
        *,
        base_url: str,
        api_key: str | None = None,
        api_key_env: str = "MIMIRBENCH_LLM_API_KEY",
        timeout_s: float | None = 60.0,
        retry: RetryConfig | None = None,
        pricing: Pricing | None = None,
        endpoint_path: str = "/v1/chat/completions",
    ) -> None:
        if not model:
            raise ValueError("GenericHTTPClient requires a non-empty model name.")
        if not base_url:
            raise ValueError("GenericHTTPClient requires a non-empty base_url.")
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.endpoint_path = endpoint_path
        self.timeout_s = timeout_s
        self.retry = retry or RetryConfig()
        self.pricing = pricing
        self.api_key_env = api_key_env
        self._api_key = api_key or os.environ.get(api_key_env)

    @property
    def _url(self) -> str:
        return f"{self.base_url}{self.endpoint_path}"

    def check_availability(self) -> ProviderStatus:
        # The transport (urllib) is always available; a key is optional for local servers.
        key_present = bool(self._api_key)
        return ProviderStatus(
            provider=self.provider,
            package_available=True,
            key_required=False,
            key_present=key_present,
            key_env=self.api_key_env,
            usable=bool(self.base_url),
            detail=(
                f"generic HTTP endpoint configured at {self.base_url}; "
                f"{'key set' if key_present else 'no key set (optional)'}."
            ),
        )

    def generate(self, request: ModelRequest) -> ModelResponseEnvelope:
        payload: dict[str, Any] = {
            "model": self.model,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ],
        }
        if request.seed is not None:
            payload["seed"] = request.seed
        if request.top_p is not None:
            payload["top_p"] = request.top_p
        if request.stop:
            payload["stop"] = request.stop
        payload.update(request.extra)

        start = time.perf_counter()
        body = run_with_retries(lambda: self._post(payload), retry=self.retry)
        latency_ms = (time.perf_counter() - start) * 1000.0
        return self._to_envelope(body, latency_ms)

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        http_request = urllib.request.Request(self._url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(http_request, timeout=self.timeout_s) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:  # carries a status code
            raise _HTTPStatusError(exc.code, f"HTTP {exc.code} from {self._url}") from exc
        except urllib.error.URLError as exc:  # transport-level (connection/timeout)
            raise ModelClientError(f"transport error calling {self._url}: {exc.reason}") from exc
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ModelClientError(f"non-JSON response from {self._url}.") from exc
        if not isinstance(parsed, dict):
            raise ModelClientError(f"unexpected response shape from {self._url}.")
        return parsed

    def _to_envelope(self, body: dict[str, Any], latency_ms: float) -> ModelResponseEnvelope:
        raw_text = ""
        finish_reason = None
        choices = body.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message", {})
                if isinstance(message, dict):
                    raw_text = str(message.get("content") or "")
                finish_reason = first.get("finish_reason")
        usage = self._extract_usage(body.get("usage"))
        return ModelResponseEnvelope(
            provider=self.provider,
            model=self.model,
            raw_text=raw_text,
            parsed_json=extract_json(raw_text),
            usage=usage,
            latency_ms=latency_ms,
            finish_reason=finish_reason,
            metadata={"endpoint": self._url},
        )

    def _extract_usage(self, raw_usage: Any) -> ModelUsage:
        if not isinstance(raw_usage, dict):
            return ModelUsage()
        input_tokens = raw_usage.get("prompt_tokens")
        output_tokens = raw_usage.get("completion_tokens")
        total_tokens = raw_usage.get("total_tokens")
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
