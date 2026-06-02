"""Deterministic synthetic Bayesian traces for small-transformer training.

The traces are deliberately compact supervised records. They contain public
Bayesian problem data plus final target labels, but no hidden chain-of-thought or
step-by-step reasoning text. The labels are intended to produce a tiny model
whose internals can later be probed for posterior, risk, and action features.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from mimirbench.environments.bayesian_games.schemas import BayesianTaskParams
from mimirbench.tools.bayes_calculator import posterior

__all__ = [
    "ACTION_LABELS",
    "CONFIDENCE_BUCKETS",
    "EV_BUCKETS",
    "RATIONALE_CLASSES",
    "RISK_FLAGS",
    "BayesianTraceConfig",
    "PayoffRiskConfig",
    "bucket_midpoint",
    "bucket_probability",
    "compute_trace_targets",
    "expected_value_for_action",
    "format_trace_input",
    "generate_trace",
    "generate_trace_splits",
    "label_vocab_for_config",
    "load_traces_jsonl",
    "regret_for_action",
    "targets_to_text",
    "task_params_to_trace_input",
    "write_traces_jsonl",
]

ACTION_LABELS = ("buy", "pass")
RISK_FLAGS = ("safe", "risky")
CONFIDENCE_BUCKETS = ("low", "medium", "high")
RATIONALE_CLASSES = (
    "evidence_favours_A",
    "evidence_favours_not_A",
    "evidence_mixed",
    "prior_dominates",
)
EV_BUCKETS = (
    "negative_high",
    "negative_medium",
    "negative_low",
    "neutral",
    "positive_low",
    "positive_medium",
    "positive_high",
)

_HYPOTHESIS_LABELS = ("A", "B", "C", "D", "E", "F")
_FORBIDDEN_REASONING_KEYS = {
    "chain_of_thought",
    "cot",
    "scratchpad",
    "reasoning_steps",
    "hidden_reasoning",
}


@dataclass(frozen=True)
class PayoffRiskConfig:
    """Decision settings used to derive EV, action, and risk labels."""

    reward_if_A: float = 1.0
    loss_if_not_A: float = 1.0
    decision_cost: float = 0.0
    risk_tolerance: float = 0.35


@dataclass(frozen=True)
class BayesianTraceConfig:
    """Configuration for deterministic Bayesian trace generation."""

    seed: int = 0
    num_hypotheses: int = 2
    min_observations: int = 1
    max_observations: int = 6
    signal_reliability: float = 0.7
    posterior_buckets: int = 20
    payoff: PayoffRiskConfig = field(default_factory=PayoffRiskConfig)

    def validate(self) -> None:
        if not 2 <= self.num_hypotheses <= len(_HYPOTHESIS_LABELS):
            raise ValueError(
                f"num_hypotheses must be in [2, {len(_HYPOTHESIS_LABELS)}], "
                f"got {self.num_hypotheses}."
            )
        if self.min_observations < 0:
            raise ValueError("min_observations must be non-negative.")
        if self.max_observations < self.min_observations:
            raise ValueError("max_observations must be >= min_observations.")
        if self.posterior_buckets < 2:
            raise ValueError("posterior_buckets must be >= 2.")
        min_reliability = 1.0 / self.num_hypotheses
        if not min_reliability <= self.signal_reliability < 1.0:
            raise ValueError(
                "signal_reliability must be at least uniform probability "
                f"({min_reliability:.3f}) and below 1.0."
            )
        if self.payoff.reward_if_A <= 0.0:
            raise ValueError("reward_if_A must be positive.")
        if self.payoff.loss_if_not_A < 0.0 or self.payoff.decision_cost < 0.0:
            raise ValueError("loss_if_not_A and decision_cost must be non-negative.")
        if not 0.0 <= self.payoff.risk_tolerance <= 1.0:
            raise ValueError("risk_tolerance must be in [0, 1].")


def generate_trace(index: int, config: BayesianTraceConfig | None = None, *, split: str = "train") -> dict[str, Any]:
    """Generate one deterministic synthetic trace."""
    cfg = config or BayesianTraceConfig()
    cfg.validate()
    if index < 0:
        raise ValueError("index must be non-negative.")

    rng = np.random.default_rng(_trace_seed(cfg.seed, split, index))
    hypothesis_labels = list(_HYPOTHESIS_LABELS[: cfg.num_hypotheses])
    signal_labels = _signal_labels(cfg.num_hypotheses)
    priors = _prior_distribution(rng, cfg.num_hypotheses)
    likelihood = _likelihood_table(cfg.num_hypotheses, cfg.signal_reliability)
    true_hypothesis = int(rng.choice(cfg.num_hypotheses, p=np.asarray(priors)))
    n_obs = int(rng.integers(cfg.min_observations, cfg.max_observations + 1))
    observations = [
        int(rng.choice(cfg.num_hypotheses, p=np.asarray(likelihood[true_hypothesis])))
        for _ in range(n_obs)
    ]
    payoff = cfg.payoff
    targets, posterior_values, buy_ev = compute_trace_targets(
        priors=priors,
        likelihood=likelihood,
        observations=observations,
        payoff=payoff,
        posterior_buckets=cfg.posterior_buckets,
    )
    _assert_no_hidden_reasoning(targets)

    trace_id = _trace_id(cfg, split, index)
    trace = {
        "id": trace_id,
        "split": split,
        "input": format_trace_input(
            priors=priors,
            hypothesis_labels=hypothesis_labels,
            likelihood=likelihood,
            signal_labels=signal_labels,
            observations=observations,
            payoff=payoff,
        ),
        "targets": targets,
        "metadata": {
            "prior": priors,
            "hypothesis_labels": hypothesis_labels,
            "likelihood": likelihood,
            "signal_labels": signal_labels,
            "observations": observations,
            "posterior": posterior_values,
            "payoff": asdict(payoff),
            "buy_expected_value": buy_ev,
            "true_hypothesis": hypothesis_labels[true_hypothesis],
        },
    }
    _assert_no_hidden_reasoning(trace)
    return trace


def generate_trace_splits(
    *,
    num_train: int,
    num_val: int,
    num_test: int,
    config: BayesianTraceConfig | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Generate deterministic train/validation/test trace splits."""
    cfg = config or BayesianTraceConfig()
    if min(num_train, num_val, num_test) < 0:
        raise ValueError("split sizes must be non-negative.")
    return {
        "train": [generate_trace(i, cfg, split="train") for i in range(num_train)],
        "val": [generate_trace(i, cfg, split="val") for i in range(num_val)],
        "test": [generate_trace(i, cfg, split="test") for i in range(num_test)],
    }


def compute_trace_targets(
    *,
    priors: Sequence[float],
    likelihood: Sequence[Sequence[float]],
    observations: Sequence[int],
    payoff: PayoffRiskConfig,
    posterior_buckets: int = 20,
) -> tuple[dict[str, Any], list[float], float]:
    """Compute supervised target labels for a Bayesian problem instance.

    Returns ``(targets, posterior_values, buy_expected_value)``. This is the
    single source of truth for the label logic; both :func:`generate_trace` and
    the interpretability counterfactual generator call it so corrupted/clean
    pairs are labelled identically to the training data.
    """
    posterior_values = posterior(priors, likelihood, observations)
    buy_ev = _buy_expected_value(posterior_values[0], payoff)
    risk_flag = "safe" if (1.0 - posterior_values[0]) <= payoff.risk_tolerance else "risky"
    action = "buy" if buy_ev > 0.0 and risk_flag == "safe" else "pass"
    confidence = _confidence_bucket(max(posterior_values))
    rationale = _rationale_class(priors[0], posterior_values[0])
    targets: dict[str, Any] = {
        "posterior_A_bucket": bucket_probability(posterior_values[0], posterior_buckets),
        "posterior_buckets": [
            bucket_probability(value, posterior_buckets) for value in posterior_values
        ],
        "action": action,
        "ev_bucket": _ev_bucket(buy_ev),
        "risk_flag": risk_flag,
        "confidence_bucket": confidence,
        "rationale_class": rationale,
    }
    return targets, list(posterior_values), buy_ev


def format_trace_input(
    *,
    priors: Sequence[float],
    hypothesis_labels: Sequence[str],
    likelihood: Sequence[Sequence[float]],
    signal_labels: Sequence[str],
    observations: Sequence[int],
    payoff: PayoffRiskConfig,
) -> str:
    """Render public Bayesian task data as compact model input text."""
    prior_text = " ".join(
        f"{label}={value:.3f}" for label, value in zip(hypothesis_labels, priors, strict=True)
    )
    likelihood_parts: list[str] = []
    for hyp_label, row in zip(hypothesis_labels, likelihood, strict=True):
        for signal_label, probability in zip(signal_labels, row, strict=True):
            likelihood_parts.append(f"{signal_label}|{hyp_label}={probability:.3f}")
    observed = " ".join(signal_labels[int(obs)] for obs in observations) or "none"
    return (
        f"prior {prior_text}; "
        f"likelihood {' '.join(likelihood_parts)}; "
        f"observations {observed}; "
        "payoff "
        f"buy_reward_if_A={payoff.reward_if_A:.3f} "
        f"buy_loss_if_not_A={payoff.loss_if_not_A:.3f} "
        f"decision_cost={payoff.decision_cost:.3f} "
        f"risk_tolerance={payoff.risk_tolerance:.3f}"
    )


def task_params_to_trace_input(
    params: BayesianTaskParams,
    *,
    payoff: PayoffRiskConfig | None = None,
) -> str:
    """Convert public Bayesian environment metadata to the synthetic input format."""
    hypothesis_labels = list(_HYPOTHESIS_LABELS[: params.n_hypotheses])
    signal_labels = _signal_labels(params.n_signals)
    return format_trace_input(
        priors=params.priors,
        hypothesis_labels=hypothesis_labels,
        likelihood=params.likelihood,
        signal_labels=signal_labels,
        observations=params.observations,
        payoff=payoff or PayoffRiskConfig(),
    )


def targets_to_text(targets: Mapping[str, Any]) -> str:
    """Stable text serialisation of supervised target labels."""
    keys = (
        "posterior_A_bucket",
        "action",
        "ev_bucket",
        "risk_flag",
        "confidence_bucket",
        "rationale_class",
    )
    return " ".join(f"{key}={targets[key]}" for key in keys)


def bucket_probability(value: float, n_buckets: int = 20) -> str:
    """Return a fixed-width probability bucket label such as ``0.70_0.75``."""
    if n_buckets < 2:
        raise ValueError("n_buckets must be >= 2.")
    clipped = min(1.0, max(0.0, float(value)))
    width = 1.0 / n_buckets
    bucket = min(n_buckets - 1, int(clipped / width))
    low = bucket * width
    high = 1.0 if bucket == n_buckets - 1 else (bucket + 1) * width
    return f"{low:.2f}_{high:.2f}"


def bucket_midpoint(bucket: str) -> float:
    """Approximate a posterior probability from a bucket label."""
    try:
        low_text, high_text = bucket.split("_", maxsplit=1)
        low = float(low_text)
        high = float(high_text)
    except ValueError as exc:
        raise ValueError(f"invalid probability bucket {bucket!r}") from exc
    if not 0.0 <= low <= high <= 1.0:
        raise ValueError(f"invalid probability bucket {bucket!r}")
    return (low + high) / 2.0


def expected_value_for_action(trace: Mapping[str, Any], action: str) -> float:
    """Return expected value for ``action`` using trace metadata."""
    metadata = _metadata(trace)
    if action == "pass":
        return 0.0
    if action != "buy":
        raise ValueError(f"unknown action {action!r}; expected one of {ACTION_LABELS}.")
    posterior_values = metadata["posterior"]
    payoff = PayoffRiskConfig(**metadata["payoff"])
    return _buy_expected_value(float(posterior_values[0]), payoff)


def regret_for_action(trace: Mapping[str, Any], action: str) -> float:
    """Return regret against the best of ``buy`` and ``pass`` for a trace."""
    buy_ev = expected_value_for_action(trace, "buy")
    pass_ev = expected_value_for_action(trace, "pass")
    chosen_ev = expected_value_for_action(trace, action)
    return max(buy_ev, pass_ev) - chosen_ev


def label_vocab_for_config(config: BayesianTraceConfig | None = None) -> dict[str, list[str]]:
    """Return stable label vocabularies for all supervised output heads."""
    cfg = config or BayesianTraceConfig()
    posterior_labels = [
        bucket_probability((i + 0.5) / cfg.posterior_buckets, cfg.posterior_buckets)
        for i in range(cfg.posterior_buckets)
    ]
    return {
        "posterior_bucket": posterior_labels,
        "action": list(ACTION_LABELS),
        "ev_bucket": list(EV_BUCKETS),
        "risk_flag": list(RISK_FLAGS),
        "confidence_bucket": list(CONFIDENCE_BUCKETS),
        "rationale_class": list(RATIONALE_CLASSES),
    }


def write_traces_jsonl(traces: Iterable[Mapping[str, Any]], path: str | Path) -> Path:
    """Write traces to JSONL in deterministic key order."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for trace in traces:
            _assert_no_hidden_reasoning(trace)
            handle.write(json.dumps(trace, sort_keys=True) + "\n")
    return output


def load_traces_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Load trace dictionaries from JSONL."""
    traces: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            loaded = json.loads(text)
            if not isinstance(loaded, dict):
                raise ValueError(f"trace row in {path} is not a JSON object.")
            _assert_no_hidden_reasoning(loaded)
            traces.append(loaded)
    return traces


def _prior_distribution(rng: np.random.Generator, n_hypotheses: int) -> list[float]:
    weights = rng.integers(2, 11, size=n_hypotheses).astype(np.float64)
    distribution = weights / weights.sum()
    return [float(value) for value in distribution]


def _likelihood_table(n_hypotheses: int, reliability: float) -> list[list[float]]:
    off = (1.0 - reliability) / (n_hypotheses - 1)
    table: list[list[float]] = []
    for hyp in range(n_hypotheses):
        row = [off for _ in range(n_hypotheses)]
        row[hyp] = reliability
        table.append(row)
    return table


def _signal_labels(n_signals: int) -> list[str]:
    if n_signals == 2:
        return ["X", "not_X"]
    return [f"signal_{i + 1}" for i in range(n_signals)]


def _buy_expected_value(posterior_a: float, payoff: PayoffRiskConfig) -> float:
    return (
        posterior_a * payoff.reward_if_A
        - (1.0 - posterior_a) * payoff.loss_if_not_A
        - payoff.decision_cost
    )


def _ev_bucket(value: float) -> str:
    if value <= -0.75:
        return "negative_high"
    if value <= -0.25:
        return "negative_medium"
    if value < -0.02:
        return "negative_low"
    if value <= 0.02:
        return "neutral"
    if value < 0.25:
        return "positive_low"
    if value < 0.75:
        return "positive_medium"
    return "positive_high"


def _confidence_bucket(value: float) -> str:
    if value < 0.55:
        return "low"
    if value < 0.75:
        return "medium"
    return "high"


def _rationale_class(prior_a: float, posterior_a: float) -> str:
    delta = posterior_a - prior_a
    if abs(delta) < 0.05:
        return "prior_dominates"
    if posterior_a > 0.55:
        return "evidence_favours_A"
    if posterior_a < 0.45:
        return "evidence_favours_not_A"
    return "evidence_mixed"


def _metadata(trace: Mapping[str, Any]) -> Mapping[str, Any]:
    metadata = trace.get("metadata")
    if not isinstance(metadata, Mapping):
        raise ValueError("trace is missing metadata.")
    return metadata


def _trace_seed(seed: int, split: str, index: int) -> int:
    digest = hashlib.sha256(f"{seed}:{split}:{index}".encode()).digest()
    return int.from_bytes(digest[:8], "big") % (2**32)


def _trace_id(config: BayesianTraceConfig, split: str, index: int) -> str:
    digest = hashlib.sha1(
        f"{asdict(config)}:{split}:{index}".encode()
    ).hexdigest()[:12]
    return f"bayes-trace-{split}-{index:06d}-{digest}"


def _assert_no_hidden_reasoning(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key).lower() in _FORBIDDEN_REASONING_KEYS:
                raise ValueError(f"trace contains forbidden hidden-reasoning key {key!r}.")
            _assert_no_hidden_reasoning(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_hidden_reasoning(item)
