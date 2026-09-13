"""Tests for the linear classification probes (pure NumPy; no torch needed)."""

from __future__ import annotations

import numpy as np

from mimirbench.interpretability.probes import (
    _fit_numpy_ridge_classifier as numpy_ridge,
)
from mimirbench.interpretability.probes import (
    confusion_matrix,
    fit_linear_classifier,
    majority_baseline,
    train_probe,
)


def _separable_dataset(seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    n = 60
    labels = np.array([0, 1, 2] * (n // 3), dtype=np.int64)
    centres = np.array([[3.0, 0.0], [0.0, 3.0], [-3.0, -3.0]])
    features = centres[labels] + 0.3 * rng.standard_normal((n, 2))
    return features.astype(np.float64), labels


def test_train_probe_beats_baseline_on_separable_data() -> None:
    features, labels = _separable_dataset()
    split = features.shape[0] // 2
    result = train_probe(
        site="embed",
        label="toy",
        class_names=["a", "b", "c"],
        train_features=features[:split],
        train_labels=labels[:split],
        val_features=features[split:],
        val_labels=labels[split:],
        test_features=features[split:],
        test_labels=labels[split:],
        alpha=1.0,
    )
    assert result.num_classes == 3
    assert result.test_accuracy > result.majority_baseline_accuracy
    assert result.test_accuracy > 0.8
    assert 0.0 <= result.majority_baseline_accuracy <= 1.0
    # confusion matrix is square and counts all test rows
    matrix = np.asarray(result.confusion_matrix)
    assert matrix.shape == (3, 3)
    assert matrix.sum() == result.n_test


def test_majority_baseline_picks_train_majority() -> None:
    train = np.array([0, 0, 0, 1], dtype=np.int64)
    evaluation = np.array([0, 0, 1, 1], dtype=np.int64)
    majority, accuracy = majority_baseline(train, evaluation)
    assert majority == 0
    assert accuracy == 0.5


def test_confusion_matrix_counts() -> None:
    truth = np.array([0, 1, 1, 2], dtype=np.int64)
    predicted = np.array([0, 1, 0, 2], dtype=np.int64)
    matrix = confusion_matrix(truth, predicted, num_classes=3)
    assert matrix.tolist() == [[1, 0, 0], [1, 1, 0], [0, 0, 1]]


def test_numpy_ridge_fallback_learns_separable() -> None:
    features, labels = _separable_dataset(seed=1)
    weights, bias = numpy_ridge(features, labels, num_classes=3, alpha=1.0)
    predictions = (features @ weights.T + bias).argmax(axis=1)
    assert float(np.mean(predictions == labels)) > 0.8


def test_fit_linear_classifier_constant_when_single_class() -> None:
    features = np.random.default_rng(0).standard_normal((10, 4))
    labels = np.ones(10, dtype=np.int64)  # only class 1 present
    probe = fit_linear_classifier(features, labels, num_classes=3, alpha=1.0)
    predictions = probe.predict(features)
    assert probe.backend == "constant"
    assert np.all(predictions == 1)
