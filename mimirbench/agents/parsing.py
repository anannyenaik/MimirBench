"""Robust response parsing and deterministic repair.

Real models rarely return exactly the JSON we ask for: they wrap it in Markdown
fences, add a sentence before or after, use Python literals, or stringify
numbers. This module turns messy model text into a validated answer dict (or an
explicit, recorded parse error) using only **deterministic** rules. No second
language model is used to repair responses in this stage — every transformation
here is auditable and reproducible.

The pipeline for :func:`parse_response` is:

1. extract a JSON object from the raw text (whole string, fenced block, or a
   balanced-brace scan);
2. if extraction fails, apply small deterministic text repairs (strip fences,
   drop trailing commas, map ``True/False/None``) and retry once;
3. coerce simple numeric strings to floats where safe;
4. normalise action labels to the environment's canonical vocabulary;
5. apply a few field-level repairs (e.g. ``decision`` → ``action``);
6. validate the result against the environment's expected schema, recording any
   missing/invalid fields as errors rather than raising.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from mimirbench.evals.schemas import EnvironmentFamily

__all__ = [
    "ParsedResponse",
    "coerce_numeric_strings",
    "extract_json",
    "looks_like_refusal",
    "normalise_action",
    "parse_response",
    "validate_against_family",
]


# Distribution-valued environments: the answer is a probability vector.
_DISTRIBUTION_FIELDS: dict[EnvironmentFamily, str] = {
    EnvironmentFamily.BAYESIAN_GAMES: "posterior",
    EnvironmentFamily.HIDDEN_REGIMES: "regime_posterior",
}

# Canonical action vocabularies per decision environment, with common synonyms.
_ACTION_SYNONYMS: dict[EnvironmentFamily, dict[str, str]] = {
    EnvironmentFamily.PREDICTION_MARKETS: {
        "buy": "buy", "long": "buy", "yes": "buy", "bid": "buy",
        "sell": "sell", "short": "sell", "no": "sell", "ask": "sell",
        "abstain": "abstain", "hold": "abstain", "pass": "abstain",
        "no_trade": "abstain", "none": "abstain", "do_nothing": "abstain",
        "wait": "abstain",
    },
    EnvironmentFamily.ADVERSARIAL_RISK: {
        "approve": "approve", "accept": "approve", "allow": "approve", "ok": "approve",
        "reject": "reject", "deny": "reject", "decline": "reject", "block": "reject",
        "reduce_size": "reduce_size", "reduce": "reduce_size", "resize": "reduce_size",
        "reduce_position": "reduce_size", "downsize": "reduce_size",
        "abstain": "abstain", "hold": "abstain", "escalate": "abstain",
    },
}

_REFUSAL_PATTERNS = (
    "i cannot", "i can't", "i won't", "i will not", "i'm unable", "i am unable",
    "cannot help", "can't help", "cannot assist", "not able to provide",
    "as an ai", "i must decline", "i refuse",
)

_NUMERIC_RE = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")
_FENCE_RE = re.compile(r"```(?:json|JSON)?\s*(.*?)```", re.DOTALL)


def extract_json(text: str) -> dict[str, Any] | None:
    """Best-effort extraction of one JSON object from model text.

    Tries, in order: the whole string, each ```json fenced block, and a
    balanced-brace scan from the first ``{``. Returns the first object that
    parses, or ``None``.
    """
    if not text:
        return None
    stripped = text.strip()

    for candidate in _json_candidates(stripped):
        obj = _try_load_object(candidate)
        if obj is not None:
            return obj
    return None


def _json_candidates(text: str) -> list[str]:
    candidates: list[str] = [text]
    candidates.extend(match.strip() for match in _FENCE_RE.findall(text))
    balanced = _first_balanced_object(text)
    if balanced is not None:
        candidates.append(balanced)
    # De-duplicate while preserving order.
    seen: set[str] = set()
    ordered: list[str] = []
    for candidate in candidates:
        if candidate and candidate not in seen:
            seen.add(candidate)
            ordered.append(candidate)
    return ordered


def _first_balanced_object(text: str) -> str | None:
    """Return the first brace-balanced ``{...}`` substring, ignoring braces in strings."""
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        char = text[i]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def _try_load_object(candidate: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(candidate)
    except (json.JSONDecodeError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _deterministic_text_repairs(text: str) -> str:
    """Apply small, reversible cleanups that commonly fix invalid JSON.

    Strips code fences, maps Python literals to JSON, and removes trailing commas.
    Intentionally conservative — it never rewrites keys or values.
    """
    repaired = text.strip()
    fenced = _FENCE_RE.search(repaired)
    if fenced:
        repaired = fenced.group(1).strip()
    repaired = re.sub(r"\bTrue\b", "true", repaired)
    repaired = re.sub(r"\bFalse\b", "false", repaired)
    repaired = re.sub(r"\bNone\b", "null", repaired)
    repaired = re.sub(r",(\s*[}\]])", r"\1", repaired)  # trailing commas
    return repaired


def looks_like_refusal(text: str) -> bool:
    """Heuristically detect a natural-language refusal with no usable answer."""
    if not text:
        return False
    lowered = text.lower()
    return any(pattern in lowered for pattern in _REFUSAL_PATTERNS)


def coerce_numeric_strings(value: Any) -> Any:
    """Recursively coerce safe numeric strings to floats.

    Converts ``"0.5"`` → ``0.5`` and ``"50%"`` → ``0.5``. Leaves non-numeric
    strings, booleans, and existing numbers untouched.
    """
    if isinstance(value, dict):
        return {key: coerce_numeric_strings(item) for key, item in value.items()}
    if isinstance(value, list):
        return [coerce_numeric_strings(item) for item in value]
    if isinstance(value, str):
        return _coerce_scalar_string(value)
    return value


def _coerce_scalar_string(value: str) -> Any:
    candidate = value.strip()
    if not candidate:
        return value
    is_percent = candidate.endswith("%")
    body = candidate[:-1].strip() if is_percent else candidate
    if _NUMERIC_RE.match(body):
        number = float(body)
        return number / 100.0 if is_percent else number
    return value


def normalise_action(value: Any, family: EnvironmentFamily | str | None) -> Any:
    """Map an action label to its canonical form for the given family.

    Unknown labels are returned lowercased/trimmed but otherwise unchanged, so
    validation (not silent coercion) decides whether they are acceptable.
    """
    if not isinstance(value, str) or family is None:
        return value
    fam = EnvironmentFamily(family) if isinstance(family, str) else family
    synonyms = _ACTION_SYNONYMS.get(fam)
    if synonyms is None:
        return value
    key = value.strip().lower().replace("-", "_").replace(" ", "_")
    return synonyms.get(key, key)


@dataclass
class ParsedResponse:
    """Outcome of parsing one model response.

    ``parsed`` is the validated answer dict (or ``None`` if no JSON was
    recovered). ``errors`` records every structural problem deterministically —
    callers store these instead of crashing. ``repaired`` flags that a
    deterministic repair pass changed the text/fields. ``refusal`` flags a
    natural-language refusal. ``action`` is the canonical decision label when the
    environment has one.
    """

    parsed: dict[str, Any] | None
    errors: list[str] = field(default_factory=list)
    repaired: bool = False
    refusal: bool = False
    action: str | None = None

    @property
    def ok(self) -> bool:
        """True when an answer dict was recovered with no validation errors."""
        return self.parsed is not None and not self.errors


def parse_response(
    text: str,
    family: EnvironmentFamily | str | None = None,
    *,
    attempt_repair: bool = True,
) -> ParsedResponse:
    """Parse, coerce, normalise, repair, and validate one model response."""
    refusal = looks_like_refusal(text)
    parsed = extract_json(text)
    repaired = False

    if parsed is None and attempt_repair:
        repaired_text = _deterministic_text_repairs(text)
        if repaired_text != (text or "").strip():
            parsed = extract_json(repaired_text)
            repaired = parsed is not None

    if parsed is None:
        return ParsedResponse(
            parsed=None,
            errors=["refusal_no_answer" if refusal else "no_json_object"],
            repaired=repaired,
            refusal=refusal,
        )

    parsed = coerce_numeric_strings(parsed)
    fam = EnvironmentFamily(family) if isinstance(family, str) else family

    if fam is not None:
        if attempt_repair:
            parsed, field_repaired = _repair_fields(parsed, fam)
            repaired = repaired or field_repaired
        parsed = _normalise_actions(parsed, fam)

    errors = validate_against_family(parsed, fam) if fam is not None else []
    return ParsedResponse(
        parsed=parsed,
        errors=errors,
        repaired=repaired,
        refusal=refusal,
        action=_action_label(parsed, fam),
    )


def _normalise_actions(parsed: dict[str, Any], family: EnvironmentFamily) -> dict[str, Any]:
    if family in _ACTION_SYNONYMS and "action" in parsed:
        parsed = dict(parsed)
        parsed["action"] = normalise_action(parsed["action"], family)
    return parsed


def _repair_fields(parsed: dict[str, Any], family: EnvironmentFamily) -> tuple[dict[str, Any], bool]:
    """Apply deterministic field-level repairs (synonym keys only)."""
    repaired = False
    result = dict(parsed)

    if family in _ACTION_SYNONYMS and "action" not in result:
        for alias in ("decision", "recommended_action", "recommendation", "choice"):
            if isinstance(result.get(alias), str):
                result["action"] = result[alias]
                repaired = True
                break

    for fam, field_name in _DISTRIBUTION_FIELDS.items():
        if family == fam and field_name not in result:
            for alias in ("posterior", "regime_posterior", "distribution", "probabilities", "beliefs"):
                if isinstance(result.get(alias), list):
                    result[field_name] = result[alias]
                    repaired = True
                    break
    return result, repaired


def validate_against_family(
    parsed: dict[str, Any] | None,
    family: EnvironmentFamily | str | None,
) -> list[str]:
    """Return a list of structural errors for ``parsed`` under ``family``.

    An empty list means the answer is structurally usable by the grader (it does
    not guarantee a *correct* answer — that is the grader's job).
    """
    if parsed is None:
        return ["no_json_object"]
    if family is None:
        return []
    fam = EnvironmentFamily(family) if isinstance(family, str) else family

    if fam in _DISTRIBUTION_FIELDS:
        return _validate_distribution(parsed, _DISTRIBUTION_FIELDS[fam])
    if fam == EnvironmentFamily.AUCTIONS:
        return _validate_number(parsed, "expected_surplus")
    if fam == EnvironmentFamily.PREDICTION_MARKETS:
        return _validate_prediction_market(parsed)
    if fam == EnvironmentFamily.ADVERSARIAL_RISK:
        return _validate_adversarial_risk(parsed)
    if fam == EnvironmentFamily.MARKET_MAKING:
        return _validate_market_making(parsed)
    return []


def _validate_distribution(parsed: dict[str, Any], field_name: str) -> list[str]:
    if field_name not in parsed:
        return [f"missing_field:{field_name}"]
    value = parsed[field_name]
    if not isinstance(value, list) or not value:
        return [f"invalid_field:{field_name}"]
    if not all(_is_number(item) for item in value):
        return [f"invalid_field:{field_name}"]
    return []


def _validate_number(parsed: dict[str, Any], field_name: str) -> list[str]:
    if field_name not in parsed:
        return [f"missing_field:{field_name}"]
    if not _is_number(parsed[field_name]):
        return [f"invalid_field:{field_name}"]
    return []


def _validate_prediction_market(parsed: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    action = parsed.get("action")
    if action is None:
        errors.append("missing_field:action")
    elif action not in {"buy", "sell", "abstain"}:
        errors.append("invalid_field:action")
    errors.extend(_validate_number(parsed, "fair_probability"))
    errors.extend(_validate_number(parsed, "expected_value"))
    return errors


def _validate_adversarial_risk(parsed: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    action = parsed.get("action")
    if action is None:
        errors.append("missing_field:action")
    elif action not in {"approve", "reject", "reduce_size", "abstain"}:
        errors.append("invalid_field:action")
    if "risk_policy_followed" not in parsed:
        errors.append("missing_field:risk_policy_followed")
    elif not isinstance(parsed["risk_policy_followed"], bool):
        errors.append("invalid_field:risk_policy_followed")
    return errors


def _validate_market_making(parsed: dict[str, Any]) -> list[str]:
    if parsed.get("abstain") is True:
        return []
    bid, ask = parsed.get("bid_price"), parsed.get("ask_price")
    if not _is_number(bid) or not _is_number(ask):
        return ["invalid_field:quote"]
    return []


def _action_label(parsed: dict[str, Any], family: EnvironmentFamily | None) -> str | None:
    if family is None:
        return None
    if family == EnvironmentFamily.MARKET_MAKING:
        if parsed.get("abstain") is True:
            return "abstain"
        return "reduce" if parsed.get("reduce_inventory") else "quote"
    action = parsed.get("action")
    return action if isinstance(action, str) else None


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)
