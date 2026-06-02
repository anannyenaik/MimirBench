"""Robustness variant system.

A *variant* is a controlled transformation of an original task that either
preserves the correct answer (so a robust agent's score should not move) or
changes it in a precisely characterised way (so a correct agent tracks the
change). Comparing an agent on a base task versus its variants is the core of
MimirBench's robustness evaluation.

Design principles
-----------------
* **Deterministic first.** Every transform is a pure function of
  ``(task, variant_type, seed)`` built from fixed templates and text banks — not
  a language model. Model-generated paraphrases are deliberately deferred so that
  a robustness regression is always reproducible and attributable to an
  inspectable string. See :mod:`mimirbench.evals.paraphrases` and
  :mod:`mimirbench.evals.adversarial_variants`.
* **The key follows the maths.** For answer-preserving variants the grading key
  is copied unchanged. The only transforms that touch the key are those that
  *mathematically* change the task (e.g. a currency rescale), and they recompute
  the key from the environment's reference solver so a correct agent stays
  correct.
* **No answer leakage.** Variants are produced from a task's *public* metadata
  and prompt only; the grading key is read solely to be copied or recomputed via
  the public solver, never exposed to an agent.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from enum import StrEnum
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from mimirbench.evals.adversarial_variants import INJECTORS
from mimirbench.evals.paraphrases import paraphrase_prompt
from mimirbench.evals.schemas import GradingKey, Task, TaskInstance

__all__ = [
    "ANSWER_PRESERVING_BY_TYPE",
    "ENVIRONMENT_VARIANT_TYPES",
    "VariantGenerator",
    "VariantResult",
    "VariantSpec",
    "VariantType",
    "applicable_variant_types",
    "generate_variants",
    "variant_type_values",
]


class VariantType(StrEnum):
    """The catalogue of robustness transformations."""

    PARAPHRASE = "paraphrase"
    IRRELEVANT_CONTEXT = "irrelevant_context"
    MISLEADING_AUTHORITY = "misleading_authority"
    EMOTIONAL_PRESSURE = "emotional_pressure"
    URGENCY_PRESSURE = "urgency_pressure"
    RECENT_OUTCOME_BIAS = "recent_outcome_bias"
    ORDER_PERMUTATION = "order_permutation"
    UNIT_SCALE_CHANGE = "unit_scale_change"
    DISTRACTOR_SIGNAL = "distractor_signal"
    RISK_PRESSURE = "risk_pressure"
    PROMPT_INJECTION_STYLE = "prompt_injection_style"


def variant_type_values() -> list[str]:
    """Return all variant-type string values in declaration order."""
    return [member.value for member in VariantType]


# Whether each variant type preserves the *graded answer* by construction. Every
# transform here preserves the underlying decision problem except unit rescaling,
# which scales the numeric answer (and recomputes the key accordingly).
ANSWER_PRESERVING_BY_TYPE: dict[VariantType, bool] = {
    VariantType.PARAPHRASE: True,
    VariantType.IRRELEVANT_CONTEXT: True,
    VariantType.MISLEADING_AUTHORITY: True,
    VariantType.EMOTIONAL_PRESSURE: True,
    VariantType.URGENCY_PRESSURE: True,
    VariantType.RECENT_OUTCOME_BIAS: True,
    VariantType.ORDER_PERMUTATION: True,
    VariantType.UNIT_SCALE_CHANGE: False,
    VariantType.DISTRACTOR_SIGNAL: True,
    VariantType.RISK_PRESSURE: True,
    VariantType.PROMPT_INJECTION_STYLE: True,
}


# Pure prompt-level injections share one implementation path keyed by name.
_INJECTION_TYPES: dict[VariantType, str] = {
    VariantType.IRRELEVANT_CONTEXT: "irrelevant_context",
    VariantType.MISLEADING_AUTHORITY: "misleading_authority",
    VariantType.EMOTIONAL_PRESSURE: "emotional_pressure",
    VariantType.URGENCY_PRESSURE: "urgency_pressure",
    VariantType.RECENT_OUTCOME_BIAS: "recent_outcome_bias",
    VariantType.DISTRACTOR_SIGNAL: "distractor_signal",
    VariantType.RISK_PRESSURE: "risk_pressure",
    VariantType.PROMPT_INJECTION_STYLE: "prompt_injection_style",
}


# Which variant types are meaningful for which environment. Pure prompt-level
# transforms apply everywhere; metadata-changing transforms are restricted to the
# environments where they are well-defined and provably correct.
_COMMON_TYPES: tuple[VariantType, ...] = (
    VariantType.PARAPHRASE,
    VariantType.IRRELEVANT_CONTEXT,
    VariantType.MISLEADING_AUTHORITY,
    VariantType.EMOTIONAL_PRESSURE,
    VariantType.URGENCY_PRESSURE,
    VariantType.RECENT_OUTCOME_BIAS,
    VariantType.DISTRACTOR_SIGNAL,
    VariantType.RISK_PRESSURE,
    VariantType.PROMPT_INJECTION_STYLE,
)

ENVIRONMENT_VARIANT_TYPES: dict[str, tuple[VariantType, ...]] = {
    "bayesian_games": (*_COMMON_TYPES, VariantType.ORDER_PERMUTATION),
    "hidden_regimes": (*_COMMON_TYPES, VariantType.ORDER_PERMUTATION),
    "auctions": (*_COMMON_TYPES, VariantType.UNIT_SCALE_CHANGE),
    "market_making": _COMMON_TYPES,
    "prediction_markets": _COMMON_TYPES,
    "adversarial_risk": _COMMON_TYPES,
}


def applicable_variant_types(environment: str) -> tuple[VariantType, ...]:
    """Return the variant types defined for ``environment`` (declaration order)."""
    return ENVIRONMENT_VARIANT_TYPES.get(environment, _COMMON_TYPES)


class VariantSpec(BaseModel):
    """Metadata describing a single variant transformation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    variant_id: str
    variant_type: VariantType
    parent_task_id: str
    environment: str
    answer_preserving: bool
    transformation_description: str
    expected_invariance: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class VariantResult(BaseModel):
    """A variant specification paired with its concrete task instance."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    spec: VariantSpec
    instance: TaskInstance


# Internal carrier for a transform's output before the spec/instance are built.
class _Transformed(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    prompt: str
    metadata: dict[str, Any] | None = None
    key_payload: dict[str, Any] | None = None
    answer_preserving: bool
    description: str
    expected_invariance: str


_PRESERVED_INVARIANCE = (
    "The final answer, the chosen action, and the grading score should be unchanged."
)


def _variant_seed(parent_task_id: str, variant_type: VariantType, base_seed: int) -> int:
    """Derive a stable per-variant seed from the parent id and type.

    Uses a content hash rather than :func:`hash` so the seed is identical across
    processes (Python's string hashing is randomised per interpreter).
    """
    payload = f"{parent_task_id}:{variant_type.value}:{base_seed}".encode()
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:4], "big", signed=False)


def _transform(
    instance: TaskInstance,
    variant_type: VariantType,
    *,
    seed: int,
) -> _Transformed:
    environment = instance.task.family.value
    prompt = instance.task.prompt

    if variant_type == VariantType.PARAPHRASE:
        return _Transformed(
            prompt=paraphrase_prompt(prompt, environment, seed=seed),
            answer_preserving=True,
            description="Reframed the task wording; all data and the question are unchanged.",
            expected_invariance=_PRESERVED_INVARIANCE,
        )

    if variant_type in _INJECTION_TYPES:
        injector = INJECTORS[_INJECTION_TYPES[variant_type]]
        return _Transformed(
            prompt=injector(prompt, environment, seed),
            answer_preserving=True,
            description=f"Injected {variant_type.value} text around the unchanged task.",
            expected_invariance=_PRESERVED_INVARIANCE,
        )

    if variant_type == VariantType.ORDER_PERMUTATION:
        return _order_permutation(instance, seed=seed)

    if variant_type == VariantType.UNIT_SCALE_CHANGE:
        return _unit_scale_change(instance, seed=seed)

    raise ValueError(f"no transform implemented for variant type {variant_type!r}.")


def _order_permutation(instance: TaskInstance, *, seed: int) -> _Transformed:
    """Permute exchangeable or non-temporal information without changing the answer."""
    environment = instance.task.family.value
    if environment == "hidden_regimes":
        return _hidden_metadata_order_permutation(instance, seed=seed)
    if environment != "bayesian_games":
        raise ValueError(f"order_permutation is not defined for {environment!r}.")

    # Local import keeps the environments <-> evals import graph acyclic.
    from mimirbench.environments.bayesian_games.generator import _format_prompt
    from mimirbench.environments.bayesian_games.schemas import BayesianTaskParams

    params = BayesianTaskParams(**instance.task.metadata)
    observations = list(params.observations)
    if len(observations) < 2:
        # Nothing to reorder; fall back to a paraphrase-style note (still preserving).
        new_prompt = (
            f"{instance.task.prompt}\n\n"
            "(The single observation cannot be reordered; the task is unchanged.)"
        )
        return _Transformed(
            prompt=new_prompt,
            answer_preserving=True,
            description="Order permutation requested with <2 observations; task unchanged.",
            expected_invariance=_PRESERVED_INVARIANCE,
        )

    if len(set(observations)) < 2:
        # All observations identical: any permutation is the same sequence.
        new_prompt = (
            f"{instance.task.prompt}\n\n"
            "(The observations are identical, so reordering leaves the task unchanged.)"
        )
        return _Transformed(
            prompt=new_prompt,
            answer_preserving=True,
            description="Order permutation requested on identical observations; task unchanged.",
            expected_invariance=_PRESERVED_INVARIANCE,
        )

    rng = np.random.default_rng(seed)
    permuted = observations[:]
    for _ in range(64):
        rng.shuffle(permuted)
        if permuted != observations:
            break
    new_params = params.model_copy(update={"observations": permuted})
    return _Transformed(
        prompt=_format_prompt(new_params),
        metadata=new_params.model_dump(),
        answer_preserving=True,
        description="Reordered the independent (i.i.d.) observed evidence.",
        expected_invariance=(
            "The observations are exchangeable, so the posterior — and the score — "
            "are invariant to their order."
        ),
    )


def _hidden_metadata_order_permutation(instance: TaskInstance, *, seed: int) -> _Transformed:
    """Reorder static HMM metadata sections while keeping observations in order."""
    from mimirbench.environments.hidden_regimes.schemas import HiddenRegimeParams

    params = HiddenRegimeParams(**instance.task.metadata)
    rng = np.random.default_rng(seed)
    section_order = ["initial", "transition", "emission"]
    permuted = section_order[:]
    for _ in range(16):
        rng.shuffle(permuted)
        if permuted != section_order:
            break
    if permuted == section_order:
        permuted = list(reversed(section_order))

    sections = {
        "initial": _hidden_initial_lines(params),
        "transition": _hidden_transition_lines(params),
        "emission": _hidden_emission_lines(params),
    }
    lines: list[str] = [
        "A system switches between hidden regimes following a Markov chain and emits a",
        "signal at each step. Estimate which regime is active at the final step.",
        "",
        "The static model metadata is listed in a different order; the time-ordered",
        "observed signals are unchanged.",
        "",
    ]
    for section in permuted:
        lines.extend(sections[section])
        lines.append("")

    observed = ", ".join(params.signal_names[s] for s in params.observations)
    lines.append(f"Observed signals (in order): {observed}")
    lines.append("")
    lines.append(
        "Return a JSON object with key 'regime_posterior': the probability of each "
        "regime at the final step, in the order listed above, summing to 1."
    )
    return _Transformed(
        prompt="\n".join(lines),
        metadata=params.model_dump(),
        answer_preserving=True,
        description="Reordered non-temporal HMM metadata sections; observations unchanged.",
        expected_invariance=(
            "Only the display order of static metadata changed. The HMM parameters, "
            "observation order, final belief, and grading score should be unchanged."
        ),
    )


def _hidden_initial_lines(params: Any) -> list[str]:
    lines = ["Initial regime probabilities:"]
    for name, p in zip(params.regime_names, params.initial, strict=True):
        lines.append(f"  - {name}: {p:.3f}")
    return lines


def _hidden_transition_lines(params: Any) -> list[str]:
    lines = ["Transition probabilities P(next regime | current regime):"]
    for name, row in zip(params.regime_names, params.transition, strict=True):
        parts = ", ".join(
            f"{to}={p:.3f}" for to, p in zip(params.regime_names, row, strict=True)
        )
        lines.append(f"  - from {name}: {parts}")
    return lines


def _hidden_emission_lines(params: Any) -> list[str]:
    lines = ["Emission probabilities P(signal | regime):"]
    for name, row in zip(params.regime_names, params.emission, strict=True):
        parts = ", ".join(
            f"{sig}={p:.3f}" for sig, p in zip(params.signal_names, row, strict=True)
        )
        lines.append(f"  - {name}: {parts}")
    return lines


def _unit_scale_change(instance: TaskInstance, *, seed: int) -> _Transformed:
    """Rescale currency units. Defined only for auctions; recomputes the key."""
    environment = instance.task.family.value
    if environment != "auctions":
        raise ValueError(f"unit_scale_change is not defined for {environment!r}.")

    from mimirbench.environments.auctions.generator import _format_prompt
    from mimirbench.environments.auctions.schemas import AuctionTaskParams
    from mimirbench.environments.auctions.solver import solve_params

    rng = np.random.default_rng(seed)
    factor = float(rng.choice([10.0, 100.0, 1000.0]))
    params = AuctionTaskParams(**instance.task.metadata)
    new_params = params.model_copy(
        update={
            "v_max": params.v_max * factor,
            "your_value": round(params.your_value * factor, 4),
        }
    )
    return _Transformed(
        prompt=_format_prompt(new_params),
        metadata=new_params.model_dump(),
        key_payload={"expected_surplus": solve_params(new_params)},
        answer_preserving=False,
        description=f"Rescaled all monetary units by x{factor:g} (e.g. into smaller denominations).",
        expected_invariance=(
            "Expected surplus scales linearly with the unit change; the key is "
            "recomputed, so a correct agent's score is unchanged even though the "
            "numeric answer differs."
        ),
    )


def _build_result(
    instance: TaskInstance,
    variant_type: VariantType,
    transformed: _Transformed,
) -> VariantResult:
    parent_task_id = instance.task.task_id
    variant_id = f"{parent_task_id}::{variant_type.value}"
    metadata = transformed.metadata if transformed.metadata is not None else dict(instance.task.metadata)
    key_payload = (
        transformed.key_payload
        if transformed.key_payload is not None
        else dict(instance.key.payload)
    )
    new_task = Task(
        task_id=variant_id,
        family=instance.task.family,
        seed=instance.task.seed,
        prompt=transformed.prompt,
        metadata=metadata,
    )
    new_key = GradingKey(task_id=variant_id, payload=key_payload)
    spec = VariantSpec(
        variant_id=variant_id,
        variant_type=variant_type,
        parent_task_id=parent_task_id,
        environment=instance.task.family.value,
        answer_preserving=transformed.answer_preserving,
        transformation_description=transformed.description,
        expected_invariance=transformed.expected_invariance,
        metadata={"base_seed": instance.task.seed},
    )
    return VariantResult(spec=spec, instance=TaskInstance(task=new_task, key=new_key))


class VariantGenerator:
    """Deterministic generator of robustness variants for one environment.

    The generator is stateless apart from its ``environment`` label and base
    ``seed``; given the same base task it always yields the same variants in the
    same order.
    """

    def __init__(self, environment: str, *, seed: int = 0) -> None:
        self.environment = environment
        self.seed = seed

    def applicable_types(self) -> tuple[VariantType, ...]:
        """Variant types defined for this generator's environment."""
        return applicable_variant_types(self.environment)

    def generate(
        self,
        instance: TaskInstance,
        *,
        variant_types: Sequence[VariantType] | None = None,
        max_variants: int | None = None,
        answer_preserving_only: bool = False,
    ) -> list[VariantResult]:
        """Generate variants for a single base task instance.

        Args:
            instance: The base task instance to transform.
            variant_types: Restrict to these types (intersected with the ones
                applicable to the environment). ``None`` uses all applicable.
            max_variants: Cap the number of variants returned.
            answer_preserving_only: Drop non-answer-preserving variant types.
        """
        if instance.task.family.value != self.environment:
            raise ValueError(
                f"instance family {instance.task.family.value!r} does not match "
                f"generator environment {self.environment!r}."
            )
        selected = self._select_types(variant_types, answer_preserving_only)
        results: list[VariantResult] = []
        for variant_type in selected:
            variant_seed = _variant_seed(instance.task.task_id, variant_type, self.seed)
            transformed = _transform(instance, variant_type, seed=variant_seed)
            results.append(_build_result(instance, variant_type, transformed))
            if max_variants is not None and len(results) >= max_variants:
                break
        return results

    def _select_types(
        self,
        variant_types: Sequence[VariantType] | None,
        answer_preserving_only: bool,
    ) -> list[VariantType]:
        applicable = self.applicable_types()
        if variant_types is None:
            ordered = list(applicable)
        else:
            requested = list(variant_types)
            ordered = [vt for vt in requested if vt in applicable]
        if answer_preserving_only:
            ordered = [vt for vt in ordered if ANSWER_PRESERVING_BY_TYPE[vt]]
        return ordered


def generate_variants(
    instance: TaskInstance,
    *,
    variant_types: Sequence[VariantType] | None = None,
    max_variants: int | None = None,
    answer_preserving_only: bool = False,
    seed: int = 0,
) -> list[VariantResult]:
    """Convenience wrapper: build a :class:`VariantGenerator` and generate once."""
    generator = VariantGenerator(instance.task.family.value, seed=seed)
    return generator.generate(
        instance,
        variant_types=variant_types,
        max_variants=max_variants,
        answer_preserving_only=answer_preserving_only,
    )
