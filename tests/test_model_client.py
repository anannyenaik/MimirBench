"""Tests for the provider-agnostic model client interface.

These tests never make network calls and never require optional provider SDKs.
"""

from __future__ import annotations

import sys
import types
from typing import Any, cast

import pytest

from mimirbench.agents.model_client import (
    ModelClientError,
    ModelRequest,
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
    from mimirbench.agents import providers
    from mimirbench.agents.providers import (
        AnthropicClient,
        GeminiClient,
        OpenAIClient,
    )

    assert providers is not None
    assert AnthropicClient is not None
    assert GeminiClient is not None
    assert OpenAIClient is not None


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
    from mimirbench.agents.providers import OpenAIClient

    # Inject a stand-in 'openai' module so the import succeeds but the key is absent.
    fake = types.ModuleType("openai")
    fake.OpenAI = object  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "openai", fake)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    client = OpenAIClient("gpt-test")
    with pytest.raises(ModelClientError, match="API key"):
        client.generate(ModelRequest(system_prompt="s", user_prompt="u"))


class _FakeCompletions:
    def __init__(self) -> None:
        self.create_kwargs: dict[str, object] | None = None

    def create(self, **kwargs: object) -> types.SimpleNamespace:
        self.create_kwargs = kwargs
        return types.SimpleNamespace(
            choices=[
                types.SimpleNamespace(
                    message=types.SimpleNamespace(content='{"ok": true}'),
                    finish_reason="stop",
                )
            ],
            usage=types.SimpleNamespace(
                prompt_tokens=1,
                completion_tokens=2,
                total_tokens=3,
            ),
            id="response-test",
        )


def test_openai_client_uses_max_tokens_for_legacy_chat_models() -> None:
    from mimirbench.agents.providers import OpenAIClient

    completions = _FakeCompletions()
    client = OpenAIClient("gpt-4.1-mini", api_key="unused")
    client._client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=completions))

    client.generate(ModelRequest(system_prompt="s", user_prompt="u", temperature=0.2, max_tokens=7))

    assert completions.create_kwargs is not None
    assert completions.create_kwargs["temperature"] == pytest.approx(0.2)
    assert completions.create_kwargs["max_tokens"] == 7
    assert "max_completion_tokens" not in completions.create_kwargs


@pytest.mark.parametrize("model", ["gpt-5.4-mini", "gpt-5.4"])
def test_openai_client_uses_max_completion_tokens_for_gpt5_chat_models(model: str) -> None:
    from mimirbench.agents.providers import OpenAIClient

    completions = _FakeCompletions()
    client = OpenAIClient(model, api_key="unused")
    client._client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=completions))

    client.generate(ModelRequest(system_prompt="s", user_prompt="u", temperature=0.3, max_tokens=7))

    assert completions.create_kwargs is not None
    assert completions.create_kwargs["temperature"] == pytest.approx(0.3)
    assert completions.create_kwargs["max_completion_tokens"] == 7
    assert "max_tokens" not in completions.create_kwargs


def test_openai_client_omits_temperature_for_gpt55_default_temperature_model() -> None:
    from mimirbench.agents.providers import OpenAIClient

    completions = _FakeCompletions()
    client = OpenAIClient("gpt-5.5", api_key="unused")
    client._client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=completions))

    client.generate(
        ModelRequest(
            system_prompt="s",
            user_prompt="u",
            temperature=0.0,
            max_tokens=7,
            extra={"temperature": 0.7},
        )
    )

    assert completions.create_kwargs is not None
    assert "temperature" not in completions.create_kwargs
    assert completions.create_kwargs["max_completion_tokens"] == 7
    assert "max_tokens" not in completions.create_kwargs


def test_openai_client_passes_reasoning_effort_from_request_extra() -> None:
    from mimirbench.agents.providers import OpenAIClient

    completions = _FakeCompletions()
    client = OpenAIClient("gpt-5.5", api_key="unused")
    client._client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=completions))

    client.generate(
        ModelRequest(
            system_prompt="s",
            user_prompt="u",
            max_tokens=11,
            extra={"reasoning_effort": "low"},
        )
    )

    assert completions.create_kwargs is not None
    assert completions.create_kwargs["reasoning_effort"] == "low"
    assert completions.create_kwargs["max_completion_tokens"] == 11
    assert "temperature" not in completions.create_kwargs
    assert "max_tokens" not in completions.create_kwargs


def test_openai_client_uses_max_completion_tokens_for_o_series_chat_models() -> None:
    from mimirbench.agents.providers import OpenAIClient

    completions = _FakeCompletions()
    client = OpenAIClient("o4-mini", api_key="unused")
    client._client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=completions))

    client.generate(ModelRequest(system_prompt="s", user_prompt="u", max_tokens=7))

    assert completions.create_kwargs is not None
    assert completions.create_kwargs["max_completion_tokens"] == 7
    assert "max_tokens" not in completions.create_kwargs


def test_gemini_client_missing_package_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    from mimirbench.agents.providers import GeminiClient

    real_import = __import__

    def fake_import(
        name: str,
        globals: dict[str, object] | None = None,
        locals: dict[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> object:
        if (name == "google" and "genai" in fromlist) or name.startswith("google.genai"):
            raise ImportError("google-genai intentionally hidden for test")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr("builtins.__import__", fake_import)
    client = GeminiClient("gemini-test", api_key="unused")
    with pytest.raises(ModelClientError, match="google-genai"):
        client.generate(ModelRequest(system_prompt="s", user_prompt="u"))


class _FakeGeminiModels:
    def __init__(self) -> None:
        self.generate_kwargs: dict[str, object] | None = None

    def generate_content(self, **kwargs: object) -> types.SimpleNamespace:
        self.generate_kwargs = kwargs
        return types.SimpleNamespace(
            text='{"ok": true}',
            candidates=[
                types.SimpleNamespace(
                    finish_reason="STOP",
                    finish_message="finished",
                )
            ],
            usage_metadata=types.SimpleNamespace(
                prompt_token_count=5,
                candidates_token_count=7,
                thoughts_token_count=11,
                total_token_count=23,
            ),
            response_id="gemini-response",
            model_version="gemini-version",
        )


def test_gemini_client_request_response_usage_and_cost() -> None:
    pytest.importorskip("google.genai", reason="Gemini SDK integration requires optional api extra")
    from mimirbench.agents.providers import GeminiClient

    models = _FakeGeminiModels()
    client = GeminiClient(
        "gemini-3.1-flash-lite",
        api_key="unused",
        pricing=Pricing(input_usd_per_1k=1.0, output_usd_per_1k=2.0),
    )
    client._client = types.SimpleNamespace(models=models)

    envelope = client.generate(
        ModelRequest(
            system_prompt="s",
            user_prompt="u",
            temperature=0.0,
            max_tokens=9,
            seed=4,
            extra={
                "use_default_temperature": True,
                "response_mime_type": "application/json",
                "thinking_config": {"thinking_budget": 0},
            },
        )
    )

    assert models.generate_kwargs is not None
    assert models.generate_kwargs["model"] == "gemini-3.1-flash-lite"
    assert models.generate_kwargs["contents"] == "u"
    config = cast(Any, models.generate_kwargs["config"])
    assert config.system_instruction == "s"
    assert config.max_output_tokens == 9
    assert config.temperature is None
    assert config.seed == 4
    assert config.response_mime_type == "application/json"
    assert config.thinking_config.thinking_budget == 0

    assert envelope.provider == "gemini"
    assert envelope.raw_text == '{"ok": true}'
    assert envelope.parsed_json == {"ok": True}
    assert envelope.finish_reason == "STOP"
    assert envelope.usage.input_tokens == 5
    # Gemini bills output including thinking tokens.
    assert envelope.usage.output_tokens == 18
    assert envelope.usage.total_tokens == 23
    assert envelope.usage.estimated_cost_usd == pytest.approx(0.041)
    assert envelope.metadata["visible_output_tokens"] == 7
    assert envelope.metadata["thinking_tokens"] == 11


def test_gemini_provider_registration() -> None:
    from mimirbench.agents.providers import GeminiClient, build_api_client

    client = build_api_client("gemini", "gemini-test")

    assert isinstance(client, GeminiClient)
    assert client.model == "gemini-test"
