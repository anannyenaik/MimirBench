"""Tests for provider availability checks (no network, no SDK required)."""

from __future__ import annotations

import sys
import types

import pytest
from typer.testing import CliRunner

from mimirbench.agents.providers import (
    AnthropicClient,
    GenericHTTPClient,
    HFLocalClient,
    OpenAIClient,
)
from mimirbench.cli import app

runner = CliRunner()


def test_openai_status_without_package_or_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    status = OpenAIClient("gpt-test").check_availability()
    assert status.provider == "openai"
    assert status.package_available is False  # openai not installed in test env
    assert status.key_required is True
    assert status.key_present is False
    assert status.usable is False


def test_openai_status_detects_key_without_exposing_it(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-super-secret-value")
    status = OpenAIClient("gpt-test").check_availability()
    assert status.key_present is True
    # The secret value must never appear anywhere in the status.
    blob = str(status.to_dict()) + status.detail
    assert "sk-super-secret-value" not in blob


def test_anthropic_status(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    status = AnthropicClient("claude-test").check_availability()
    assert status.provider == "anthropic"
    assert status.key_required is True
    assert status.usable is False


def test_local_status_without_torch() -> None:
    status = HFLocalClient("tiny-model").check_availability()
    assert status.provider == "hf_local"
    assert status.key_required is False
    assert status.usable is False  # torch/transformers not installed in test env


def test_generic_http_status_is_usable_with_base_url() -> None:
    status = GenericHTTPClient("m", base_url="http://localhost:8000").check_availability()
    assert status.provider == "generic_http"
    assert status.package_available is True  # urllib is always available
    assert status.usable is True
    assert status.key_required is False


def test_package_available_when_module_present(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = types.ModuleType("openai")
    monkeypatch.setitem(sys.modules, "openai", fake)
    monkeypatch.setenv("OPENAI_API_KEY", "present")
    status = OpenAIClient("gpt-test").check_availability()
    assert status.package_available is True
    assert status.key_present is True
    assert status.usable is True


def test_cli_check_provider_runs_and_hides_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-do-not-print")
    result = runner.invoke(app, ["check-provider", "openai"])
    assert result.exit_code == 0
    assert "sk-do-not-print" not in result.output
    assert "openai" in result.output.lower()


def test_cli_check_provider_unknown() -> None:
    result = runner.invoke(app, ["check-provider", "nope"])
    assert result.exit_code == 2


def test_cli_check_provider_local() -> None:
    result = runner.invoke(app, ["check-provider", "local"])
    assert result.exit_code == 0
    assert "hf_local" in result.output
