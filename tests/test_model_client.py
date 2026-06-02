"""Tests for the provider-agnostic model client interface.

These tests never make network calls and never require optional provider SDKs.
"""

from __future__ import annotations

import sys
import types

import pytest

from mimirbench.agents.model_client import (
    ModelClientError,
    ModelUsage,
    Pricing,
    RetryConfig,
    estimate_cost,
    is_retryable_error,
    next_retry_delay,
    run_with_retries,
)


def test_module_imports_without_optional_deps() -> None:
    # Importing the interface and provider clients must not require any SDK.
    import mimirbench.agents.providers  # noqa: F401
    from mimirbench.agents.providers import AnthropicClient, OpenAIClient  # noqa: F401


def test_estimate_cost_is_none_without_pricing() -> None:
    usage = ModelUsage(input_tokens=1000, output_tokens=2000, total_tokens=3000)
    assert estimate_cost(usage, None) is None


def test_estimate_cost_with_pricing() -> None:
    usage = ModelUsage(input_tokens=1000, output_tokens=2000)
    pricing = Pricing(input_usd_per_1k=0.001, output_usd_per_1k=0.002)
    assert estimate_cost(usage, pricing) == pytest.approx(0.001 + 0.004)


def test_estimate_cost_none_when_tokens_missing() -> None:
    pricing = Pricing(input_usd_per_1k=1.0, output_usd_per_1k=1.0)
    assert estimate_cost(ModelUsage(), pricing) is None


def test_pricing_from_mapping_variants() -> None:
    assert Pricing.from_mapping(None) is None
    assert Pricing.from_mapping({}) is None
    per_1k = Pricing.from_mapping({"input_usd_per_1k": 0.5, "output_usd_per_1k": 1.5})
    assert per_1k == Pricing(0.5, 1.5)
    per_1m = Pricing.from_mapping({"input_usd_per_1m": 500.0, "output_usd_per_1m": 1500.0})
    assert per_1m == Pricing(0.5, 1.5)


def test_retry_config_validates() -> None:
    with pytest.raises(ValueError):
        RetryConfig(max_retries=0)


def test_is_retryable_classifies_status_and_names() -> None:
    retry = RetryConfig()

    class WithStatus(Exception):
        status_code = 503

    class AuthError(Exception):
        status_code = 401

    class Timeout(Exception):
        pass

    assert is_retryable_error(WithStatus(), retry) is True
    assert is_retryable_error(AuthError(), retry) is False
    assert is_retryable_error(Timeout(), retry) is True
    assert is_retryable_error(ValueError("bad arg"), retry) is False


def test_next_retry_delay_is_bounded_and_monotonic() -> None:
    retry = RetryConfig(base_delay_s=1.0, max_delay_s=4.0)
    assert next_retry_delay(0, retry) == 1.0
    assert next_retry_delay(1, retry) == 2.0
    assert next_retry_delay(2, retry) == 4.0
    assert next_retry_delay(10, retry) == 4.0  # capped


def test_run_with_retries_succeeds_after_transient_failures() -> None:
    calls = {"n": 0}

    class Transient(Exception):
        status_code = 503

    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise Transient()
        return "ok"

    result = run_with_retries(flaky, retry=RetryConfig(max_retries=5), sleep=lambda _s: None)
    assert result == "ok"
    assert calls["n"] == 3


def test_run_with_retries_raises_model_client_error_after_exhaustion() -> None:
    class Transient(Exception):
        status_code = 503

    def always_fail() -> str:
        raise Transient()

    with pytest.raises(ModelClientError, match="after 2 attempt"):
        run_with_retries(always_fail, retry=RetryConfig(max_retries=2), sleep=lambda _s: None)


def test_run_with_retries_does_not_retry_non_transient() -> None:
    calls = {"n": 0}

    def auth_fail() -> str:
        calls["n"] += 1
        raise PermissionError("nope")  # not transient

    with pytest.raises(ModelClientError):
        run_with_retries(auth_fail, retry=RetryConfig(max_retries=5), sleep=lambda _s: None)
    assert calls["n"] == 1


def test_openai_client_missing_package_raises_clear_error() -> None:
    from mimirbench.agents.model_client import ModelRequest
    from mimirbench.agents.providers import OpenAIClient

    # No 'openai' package is installed in the test environment.
    client = OpenAIClient("gpt-test", api_key="unused")
    with pytest.raises(ModelClientError, match="api"):
        client.generate(ModelRequest(system_prompt="s", user_prompt="u"))


def test_openai_client_missing_key_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    from mimirbench.agents.model_client import ModelRequest
    from mimirbench.agents.providers import OpenAIClient

    # Inject a stand-in 'openai' module so the import succeeds but the key is absent.
    fake = types.ModuleType("openai")
    fake.OpenAI = object  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "openai", fake)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    client = OpenAIClient("gpt-test")
    with pytest.raises(ModelClientError, match="API key"):
        client.generate(ModelRequest(system_prompt="s", user_prompt="u"))
