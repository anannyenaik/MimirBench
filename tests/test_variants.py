"""Robustness variant generation tests."""

from __future__ import annotations

from collections import Counter

from mimirbench.evals import registry
from mimirbench.evals.variants import (
    ANSWER_PRESERVING_BY_TYPE,
    ENVIRONMENT_VARIANT_TYPES,
    VariantGenerator,
    VariantType,
    variant_type_values,
)


def test_variant_catalogue_contains_required_types() -> None:
    assert variant_type_values() == [
        "paraphrase",
        "irrelevant_context",
        "misleading_authority",
        "emotional_pressure",
        "urgency_pressure",
        "recent_outcome_bias",
        "order_permutation",
        "unit_scale_change",
        "distractor_signal",
        "risk_pressure",
        "prompt_injection_style",
    ]
    assert ANSWER_PRESERVING_BY_TYPE[VariantType.UNIT_SCALE_CHANGE] is False
    assert all(
        ANSWER_PRESERVING_BY_TYPE[vtype]
        for vtype in VariantType
        if vtype is not VariantType.UNIT_SCALE_CHANGE
    )


def test_variant_generation_is_deterministic_for_all_environments() -> None:
    for environment in registry.environment_names():
        spec = registry.get(environment)
        instance = spec.generator(123)
        generator = VariantGenerator(environment, seed=99)
        first = generator.generate(instance, max_variants=3)
        second = generator.generate(instance, max_variants=3)

        assert [v.model_dump(mode="json") for v in first] == [
            v.model_dump(mode="json") for v in second
        ]
        assert len(first) == 3
        assert all(v.spec.environment == environment for v in first)
        assert all(v.spec.parent_task_id == instance.task.task_id for v in first)


def test_answer_preserving_variants_retain_grading_key_payload() -> None:
    for environment in registry.environment_names():
        spec = registry.get(environment)
        instance = spec.generator(321)
        generator = VariantGenerator(environment, seed=7)
        variants = generator.generate(instance, answer_preserving_only=True, max_variants=4)

        assert variants
        for variant in variants:
            assert variant.spec.answer_preserving is True
            assert variant.instance.key.payload == instance.key.payload
            assert variant.instance.key.task_id == variant.spec.variant_id
            assert variant.instance.task.task_id == variant.spec.variant_id


def test_bayesian_order_permutation_preserves_evidence_multiset() -> None:
    spec = registry.get("bayesian_games")
    instance = spec.generator(123)
    variant = VariantGenerator("bayesian_games", seed=123).generate(
        instance,
        variant_types=[VariantType.ORDER_PERMUTATION],
    )[0]

    assert variant.spec.variant_type == VariantType.ORDER_PERMUTATION
    assert variant.spec.answer_preserving is True
    assert variant.instance.key.payload == instance.key.payload
    assert Counter(variant.instance.task.metadata["observations"]) == Counter(
        instance.task.metadata["observations"]
    )


def test_hidden_regime_order_permutation_reorders_only_static_metadata() -> None:
    spec = registry.get("hidden_regimes")
    instance = spec.generator(323)
    variant = VariantGenerator("hidden_regimes", seed=123).generate(
        instance,
        variant_types=[VariantType.ORDER_PERMUTATION],
    )[0]

    assert variant.spec.variant_type == VariantType.ORDER_PERMUTATION
    assert variant.spec.answer_preserving is True
    assert variant.instance.key.payload == instance.key.payload
    assert variant.instance.task.metadata == instance.task.metadata
    assert variant.instance.task.prompt != instance.task.prompt
    assert "Observed signals (in order)" in variant.instance.task.prompt


def test_injected_variant_text_is_seed_controlled() -> None:
    spec = registry.get("bayesian_games")
    instance = spec.generator(123)
    prompts = {
        VariantGenerator("bayesian_games", seed=seed)
        .generate(instance, variant_types=[VariantType.IRRELEVANT_CONTEXT])[0]
        .instance.task.prompt
        for seed in range(20)
    }

    assert len(prompts) > 1


def test_auction_unit_scale_documents_non_preserving_key_change() -> None:
    spec = registry.get("auctions")
    instance = spec.generator(223)
    variant = VariantGenerator("auctions", seed=123).generate(
        instance,
        variant_types=[VariantType.UNIT_SCALE_CHANGE],
    )[0]

    assert variant.spec.variant_type == VariantType.UNIT_SCALE_CHANGE
    assert variant.spec.answer_preserving is False
    assert "scales" in variant.spec.expected_invariance
    assert variant.instance.key.payload != instance.key.payload


def test_environment_variant_types_cover_all_registered_environments() -> None:
    assert set(ENVIRONMENT_VARIANT_TYPES) == set(registry.environment_names())
    assert VariantType.ORDER_PERMUTATION in ENVIRONMENT_VARIANT_TYPES["bayesian_games"]
    assert VariantType.UNIT_SCALE_CHANGE in ENVIRONMENT_VARIANT_TYPES["auctions"]
