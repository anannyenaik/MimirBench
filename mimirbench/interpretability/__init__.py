"""Mechanistic interpretability toolkit (Stage 8).

The probe, counterfactual, attention, and patching primitives are dependency-free
to import (numpy only); torch is imported lazily inside the functions that drive a
trained model, so ``import mimirbench.interpretability`` never pulls in torch.

``activation_capture`` is the one module that imports torch at module load (it
binds the training package), so it is intentionally *not* re-exported here; import
it directly when you need it.
"""

from mimirbench.interpretability.activation_patching import (
    PatchingExperimentResult,
    PatchResult,
    PatchSpec,
    activation_patch,
    run_activation_patching,
)
from mimirbench.interpretability.attention_analysis import (
    AttentionAnalysisResult,
    attention_entropy,
    attention_group_mass,
    previous_token_score,
    run_attention_analysis,
    token_group_spans,
)
from mimirbench.interpretability.circuit_experiments import (
    EVIDENCE_ACCUMULATION_PLAN,
    ExperimentStep,
    describe_plan,
)
from mimirbench.interpretability.counterfactuals import (
    CounterfactualPair,
    generate_counterfactual_pairs,
)
from mimirbench.interpretability.probes import (
    LinearClassifierProbe,
    LinearProbe,
    ProbeResult,
    fit_linear_classifier,
    fit_linear_probe,
    train_probe,
)
from mimirbench.interpretability.runner import (
    InterpretabilityConfig,
    load_interpretability_config,
    run_interpretability,
)
from mimirbench.interpretability.sae_features import SAEConfig, train_sae

__all__ = [
    "EVIDENCE_ACCUMULATION_PLAN",
    "AttentionAnalysisResult",
    "CounterfactualPair",
    "ExperimentStep",
    "InterpretabilityConfig",
    "LinearClassifierProbe",
    "LinearProbe",
    "PatchResult",
    "PatchSpec",
    "PatchingExperimentResult",
    "ProbeResult",
    "SAEConfig",
    "activation_patch",
    "attention_entropy",
    "attention_group_mass",
    "describe_plan",
    "fit_linear_classifier",
    "fit_linear_probe",
    "generate_counterfactual_pairs",
    "load_interpretability_config",
    "previous_token_score",
    "run_activation_patching",
    "run_attention_analysis",
    "run_interpretability",
    "token_group_spans",
    "train_probe",
    "train_sae",
]
