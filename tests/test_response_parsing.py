"""Tests for robust response parsing and deterministic repair."""

from __future__ import annotations

from mimirbench.agents.parsing import (
    coerce_numeric_strings,
    extract_json,
    looks_like_refusal,
    normalise_action,
    parse_response,
)
from mimirbench.evals.schemas import EnvironmentFamily


def test_extract_clean_json() -> None:
    assert extract_json('{"posterior": [0.5, 0.5]}') == {"posterior": [0.5, 0.5]}


def test_extract_json_from_markdown_fence() -> None:
    text = 'Here is my answer:\n```json\n{"expected_surplus": 1.25}\n```\nThanks!'
    assert extract_json(text) == {"expected_surplus": 1.25}


def test_extract_json_with_prose_around() -> None:
    text = 'I think the answer is {"action": "buy", "fair_probability": 0.7} based on the signal.'
    assert extract_json(text) == {"action": "buy", "fair_probability": 0.7}


def test_extract_json_handles_nested_braces() -> None:
    text = 'prefix {"a": {"b": 1}, "c": [1, 2]} suffix'
    assert extract_json(text) == {"a": {"b": 1}, "c": [1, 2]}


def test_invalid_json_records_error_without_crashing() -> None:
    result = parse_response("definitely not json", EnvironmentFamily.AUCTIONS)
    assert result.parsed is None
    assert result.errors == ["no_json_object"]
    assert result.ok is False


def test_missing_required_field_is_recorded() -> None:
    result = parse_response('{"reasoning_summary": "no answer here"}', EnvironmentFamily.BAYESIAN_GAMES)
    assert result.parsed is not None
    assert "missing_field:posterior" in result.errors


def test_wrong_action_label_is_normalised() -> None:
    result = parse_response(
        '{"action": "LONG", "fair_probability": 0.6, "expected_value": 0.1}',
        EnvironmentFamily.PREDICTION_MARKETS,
    )
    assert result.parsed is not None
    assert result.parsed["action"] == "buy"
    assert result.errors == []


def test_unknown_action_label_recorded_as_invalid() -> None:
    result = parse_response(
        '{"action": "yolo", "fair_probability": 0.6, "expected_value": 0.1}',
        EnvironmentFamily.PREDICTION_MARKETS,
    )
    assert "invalid_field:action" in result.errors


def test_numeric_strings_are_coerced() -> None:
    result = parse_response('{"expected_surplus": "1.5"}', EnvironmentFamily.AUCTIONS)
    assert result.parsed == {"expected_surplus": 1.5}
    assert result.errors == []


def test_percent_strings_are_coerced() -> None:
    assert coerce_numeric_strings({"p": "50%"}) == {"p": 0.5}
    assert coerce_numeric_strings({"label": "buy"}) == {"label": "buy"}


def test_refusal_text_is_flagged() -> None:
    result = parse_response("I cannot help with that request.", EnvironmentFamily.ADVERSARIAL_RISK)
    assert result.refusal is True
    assert result.parsed is None
    assert result.errors == ["refusal_no_answer"]
    assert looks_like_refusal("I'm unable to comply") is True


def test_repair_trailing_comma_and_python_literals() -> None:
    text = '{"abstain": True, "bid_size": 0, "ask_size": 0,}'
    result = parse_response(text, EnvironmentFamily.MARKET_MAKING)
    assert result.repaired is True
    assert result.parsed is not None
    assert result.parsed["abstain"] is True


def test_repair_field_alias_decision_to_action() -> None:
    result = parse_response(
        '{"decision": "reject", "risk_policy_followed": true}',
        EnvironmentFamily.ADVERSARIAL_RISK,
    )
    assert result.parsed is not None
    assert result.parsed.get("action") == "reject"
    assert result.errors == []


def test_market_making_quote_validation() -> None:
    ok = parse_response(
        '{"bid_price": 99.0, "ask_price": 101.0, "bid_size": 1, "ask_size": 1}',
        EnvironmentFamily.MARKET_MAKING,
    )
    assert ok.errors == []
    bad = parse_response('{"reduce_inventory": false}', EnvironmentFamily.MARKET_MAKING)
    assert "invalid_field:quote" in bad.errors
    abstain = parse_response('{"abstain": true}', EnvironmentFamily.MARKET_MAKING)
    assert abstain.errors == []


def test_normalise_action_is_family_specific() -> None:
    assert normalise_action("Approve", EnvironmentFamily.ADVERSARIAL_RISK) == "approve"
    assert normalise_action("reduce", EnvironmentFamily.ADVERSARIAL_RISK) == "reduce_size"
    assert normalise_action("hold", EnvironmentFamily.PREDICTION_MARKETS) == "abstain"


def test_parse_without_family_skips_validation() -> None:
    result = parse_response('{"anything": 1}', None)
    assert result.parsed == {"anything": 1}
    assert result.errors == []
