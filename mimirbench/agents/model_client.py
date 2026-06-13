"""Provider-agnostic model client interface.

This module defines the single contract every hosted or local model backend
implements, so the rest of the harness never depends on a particular SDK:

* :class:`ModelRequest` — the prompt and decoding settings going *in*;
* :class:`ModelResponseEnvelope` — text, parsed JSON, usage, latency, and any
  error coming *out*;
* :class:`ModelClient` — the abstract backend that maps one to the other.

Three deliberate design choices:

* **Costs are explicit.** :attr:`ModelUsage.estimated_cost_usd` is ``None`` unless
  a :class:`Pricing` was explicitly configured. We never silently invent a
  dollar figure from a hard-coded price table.
* **No hidden chain-of-thought.** The contract carries a single ``raw_text`` plus
  an optional parsed answer. Backends must not request or store private
  reasoning traces; prompt builders ask only for a concise summary.
* **Provider SDKs are optional and lazy.** Nothing here imports ``openai``,
  ``anthropic``, ``torch`` or ``transformers``; concrete clients import them
  inside methods so the core harness and tests run without them.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

__all__ = [
    "DEFAULT_RETRY_STATUS_CODES",
    "ModelClient",
    "ModelClientError",
    "ModelRequest",
    "ModelResponseEnvelope",
    "ModelUsage",
    "Pricing",
    "ProviderStatus",
    "RetryConfig",
    "estimate_cost",
    "is_retryable_error",
    "next_retry_delay",
    "run_with_retries",
]

T = TypeVar("T")

# HTTP status codes that typically indicate a transient failure worth retrying.
DEFAULT_RETRY_STATUS_CODES: frozenset[int] = frozenset({408, 409, 425, 429, 500, 502, 503, 504})


class ModelClientError(RuntimeError):
    """Raised for unrecoverable model-backend problems.

    Used for missing packages, missing API keys, and exhausted retries. The
    message is meant to be actionable (it names the env var or extra to install)
    and never contains secret values.
    """


@dataclass(frozen=True)
class Pricing:
    """Per-token pricing for cost estimation, in USD per 1,000 tokens.

    Pricing must be supplied explicitly (via config); there is no built-in price
    table. When pricing is absent the estimated cost is ``None`` and reports must
    state that cost was *not estimated*.
    """

    input_usd_per_1k: float
    output_usd_per_1k: float

    @classmethod
    def from_mapping(cls, data: dict[str, Any] | None) -> Pricing | None:
        """Build pricing from a config mapping, or ``None`` if not configured.

        Accepts either ``{input_usd_per_1k, output_usd_per_1k}`` or the
        per-million aliases ``{input_usd_per_1m, output_usd_per_1m}``.
        """
        if not data:
            return None
        if "input_usd_per_1k" in data or "output_usd_per_1k" in data:
            return cls(
                input_usd_per_1k=float(data.get("input_usd_per_1k", 0.0)),
                output_usd_per_1k=float(data.get("output_usd_per_1k", 0.0)),
            )
        if "input_usd_per_1m" in data or "output_usd_per_1m" in data:
            return cls(
                input_usd_per_1k=float(data.get("input_usd_per_1m", 0.0)) / 1000.0,
                output_usd_per_1k=float(data.get("output_usd_per_1m", 0.0)) / 1000.0,
            )
        return None


@dataclass(frozen=True)
class ModelUsage:
    """Token accounting for a single model call (best-effort, provider-dependent).

    ``estimated_cost_usd`` is ``None`` when pricing was not configured. A ``None``
    cost must be reported as "not estimated" rather than as zero.
    """

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    estimated_cost_usd: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": self.estimated_cost_usd,
        }


@dataclass(frozen=True)
class ModelRequest:
    """The prompt and decoding settings for one model call.

    ``seed`` and ``top_p`` are passed through only when the backend supports
    them. ``stop`` and ``extra`` allow provider-specific knobs without widening
    the core contract.
    """

    system_prompt: str
    user_prompt: str
    temperature: float = 0.0
    max_tokens: int = 1024
    seed: int | None = None
    top_p: float | None = None
    stop: list[str] | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelResponseEnvelope:
    """Everything a backend returns for one call.

    ``parsed_json`` is a convenience: a best-effort JSON object extracted from
    ``raw_text`` if one is obviously present. Full schema-aware parsing/repair is
    the job of :mod:`mimirbench.agents.parsing`; this is only a cheap pre-parse.
    """

    provider: str
    model: str
    raw_text: str
    parsed_json: dict[str, Any] | None = None
    usage: ModelUsage = field(default_factory=ModelUsage)
    latency_ms: float | None = None
    finish_reason: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_metadata(self) -> dict[str, Any]:
        """A compact, JSON-serialisable view for run records (no secrets)."""
        return {
            "provider": self.provider,
            "model": self.model,
            "finish_reason": self.finish_reason,
            "usage": self.usage.to_dict(),
            "latency_ms": self.latency_ms,
            **({"error": self.error} if self.error else {}),
            **self.metadata,
        }


@dataclass(frozen=True)
class RetryConfig:
    """Bounded retry policy for transient backend failures.

    Backoff is deterministic by default (``jitter=0.0``) so runs are
    reproducible. ``sleep`` is injectable so tests never actually wait.
    """

    max_retries: int = 3
    base_delay_s: float = 0.25
    max_delay_s: float = 8.0
    jitter: float = 0.0
    retry_on_status: frozenset[int] = DEFAULT_RETRY_STATUS_CODES

    def __post_init__(self) -> None:
        if self.max_retries < 1:
            raise ValueError("max_retries must be >= 1.")
        if self.base_delay_s < 0 or self.max_delay_s < 0:
            raise ValueError("retry delays must be non-negative.")


@dataclass(frozen=True)
class ProviderStatus:
    """Result of a provider availability check (used by ``check-provider``).

    Never carries the API key itself — only whether one was found.
    """

    provider: str
    package_available: bool
    key_required: bool
    key_present: bool
    key_env: str | None
    usable: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "package_available": self.package_available,
            "key_required": self.key_required,
            "key_present": self.key_present,
            "key_env": self.key_env,
            "usable": self.usable,
            "detail": self.detail,
        }


def estimate_cost(usage: ModelUsage, pricing: Pricing | None) -> float | None:
    """Estimate USD cost from token usage, or ``None`` if not estimable.

    Returns ``None`` when pricing is not configured or token counts are missing,
    so callers can faithfully report "not estimated".
    """
    if pricing is None:
        return None
    if usage.input_tokens is None and usage.output_tokens is None:
        return None
    input_tokens = usage.input_tokens or 0
    output_tokens = usage.output_tokens or 0
    cost = (
        input_tokens / 1000.0 * pricing.input_usd_per_1k
        + output_tokens / 1000.0 * pricing.output_usd_per_1k
    )
    return round(cost, 6)


def is_retryable_error(exc: Exception, retry: RetryConfig) -> bool:
    """Classify whether an exception represents a transient, retryable failure.

    Auth errors (401/403) and malformed-request errors (400/404/422) are *not*
    retried — retrying them only burns quota. Status is read from common SDK
    attributes; otherwise the exception class name is matched against a small set
    of transient-failure tokens.
    """
    status = getattr(exc, "status_code", None)
    if status is None:
        status = getattr(exc, "status", None)
    if isinstance(status, int):
        return status in retry.retry_on_status
    name = type(exc).__name__.lower()
    transient_tokens = (
        "timeout",
        "connection",
        "apiconnection",
        "ratelimit",
        "serviceunavailable",
        "internalserver",
        "overloaded",
        "temporarilyunavailable",
    )
    return any(token in name for token in transient_tokens)


def next_retry_delay(attempt: int, retry: RetryConfig) -> float:
    """Exponential backoff delay (seconds) for a zero-based ``attempt`` index."""
    delay = retry.base_delay_s * (2.0**attempt)
    delay = min(delay, retry.max_delay_s)
    if retry.jitter > 0.0:
        # Deterministic, attempt-derived perturbation (no RNG, so still reproducible).
        delay += (attempt % 3) * retry.jitter
    return delay


def run_with_retries(
    fn: Callable[[], T],
    *,
    retry: RetryConfig,
    sleep: Callable[[float], None] = time.sleep,
    on_retry: Callable[[int, Exception], None] | None = None,
) -> T:
    """Run ``fn`` with bounded retries on transient failures.

    Non-retryable errors (e.g. auth) raise immediately. When all attempts are
    exhausted the final exception is wrapped in :class:`ModelClientError`.
    """
    last_error: Exception | None = None
    for attempt in range(retry.max_retries):
        try:
            return fn()
        except Exception as exc:
            last_error = exc
            is_last = attempt + 1 >= retry.max_retries
            if is_last or not is_retryable_error(exc, retry):
                break
            if on_retry is not None:
                on_retry(attempt, exc)
            sleep(next_retry_delay(attempt, retry))
    assert last_error is not None
    raise ModelClientError(
        f"model call failed after {retry.max_retries} attempt(s): "
        f"{type(last_error).__name__}: {last_error}"
    ) from last_error


class ModelClient(ABC):
    """Abstract, provider-agnostic text model backend.

    Concrete subclasses (OpenAI, Anthropic, generic HTTP, local HF) set
    :attr:`provider` and :attr:`model` and implement :meth:`generate` and
    :meth:`check_availability`. They import their heavy SDK lazily.
    """

    provider: str = "unknown"
    model: str = "unknown"

    @abstractmethod
    def generate(self, request: ModelRequest) -> ModelResponseEnvelope:
        """Run one model call and return a fully-populated envelope."""
        raise NotImplementedError

    @abstractmethod
    def check_availability(self) -> ProviderStatus:
        """Report whether this backend looks usable, without making a call."""
        raise NotImplementedError
