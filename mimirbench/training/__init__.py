"""Small-transformer training utilities for interpretability experiments.

Dataset generation and tokenisation are dependency-free. Actual model training
and checkpoint inference import ``torch`` only when invoked.
"""

from mimirbench.training.datasets import (
    BayesianTraceDatasetConfig,
    RegimeDatasetConfig,
    bayes_optimal_nll,
    make_bayesian_trace_dataset,
    make_regime_dataset,
)
from mimirbench.training.synthetic_traces import BayesianTraceConfig, generate_trace
from mimirbench.training.tokenizer import SymbolTokenizer, TraceTokenizer

__all__ = [
    "BayesianTraceConfig",
    "BayesianTraceDatasetConfig",
    "RegimeDatasetConfig",
    "SymbolTokenizer",
    "TraceTokenizer",
    "bayes_optimal_nll",
    "generate_trace",
    "make_bayesian_trace_dataset",
    "make_regime_dataset",
]


def __getattr__(name: str) -> object:
    """Lazily expose training/evaluation entry points without import cycles."""
    if name in {"SmallTransformerTrainConfig", "TrainConfig", "load_config", "train"}:
        from mimirbench.training import train_small_transformer

        return getattr(train_small_transformer, name)
    if name in {"SmallTransformerEvalConfig", "evaluate_checkpoint", "token_accuracy"}:
        from mimirbench.training import evaluate_small_transformer

        return getattr(evaluate_small_transformer, name)
    raise AttributeError(name)
