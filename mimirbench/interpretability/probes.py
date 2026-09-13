"""Linear probes for reading latent quantities out of model activations.

A ridge-regression probe (closed form, dependency-free) is the workhorse for the
"is the belief linearly decodable?" experiments: fit a linear map from a layer's
activations to a target such as the Bayes-filtered ``P(regime=1)``, and report
how much variance it explains.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import numpy.typing as npt

__all__ = [
    "LinearClassifierProbe",
    "LinearProbe",
    "ProbeResult",
    "confusion_matrix",
    "fit_linear_classifier",
    "fit_linear_probe",
    "majority_baseline",
    "train_probe",
]


@dataclass(frozen=True)
class LinearProbe:
    """A fitted linear probe ``y ≈ X @ weights + bias``."""

    weights: npt.NDArray[np.float64]
    bias: float

    def predict(self, features: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """Predict targets for a feature matrix of shape ``(n, d)``."""
        x = np.asarray(features, dtype=np.float64)
        return x @ self.weights + self.bias

    def r2_score(self, features: npt.NDArray[np.float64], targets: npt.NDArray[np.float64]) -> float:
        """Coefficient of determination (R^2) on the given data."""
        y = np.asarray(targets, dtype=np.float64)
        pred = self.predict(features)
        ss_res = float(np.sum((y - pred) ** 2))
        ss_tot = float(np.sum((y - y.mean()) ** 2))
        if ss_tot == 0.0:
            return 0.0
        return 1.0 - ss_res / ss_tot


def fit_linear_probe(
    features: npt.NDArray[np.float64],
    targets: npt.NDArray[np.float64],
    *,
    alpha: float = 1.0,
) -> LinearProbe:
    """Fit a ridge-regression probe in closed form.

    Args:
        features: Activation matrix of shape ``(n_samples, n_features)``.
        targets: Target vector of shape ``(n_samples,)``.
        alpha: L2 regularisation strength (the weights, not the bias, are
            penalised).
    """
    x = np.asarray(features, dtype=np.float64)
    y = np.asarray(targets, dtype=np.float64)
    if x.ndim != 2:
        raise ValueError("features must be a 2-D array.")
    if y.shape != (x.shape[0],):
        raise ValueError("targets must have shape (n_samples,).")
    if alpha < 0:
        raise ValueError("alpha must be >= 0.")

    n_features = x.shape[1]
    design = np.hstack([x, np.ones((x.shape[0], 1))])
    penalty = alpha * np.eye(n_features + 1)
    penalty[-1, -1] = 0.0  # do not regularise the bias term
    gram = design.T @ design + penalty
    coef = np.linalg.solve(gram, design.T @ y).astype(np.float64)
    return LinearProbe(weights=coef[:-1], bias=float(coef[-1]))


# --------------------------------------------------------------------------- #
# Multi-class classification probes (posterior / action / risk / confidence)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class LinearClassifierProbe:
    """A fitted multi-class linear probe over canonical class indices.

    Predictions are always returned as canonical class indices in
    ``[0, num_classes)``. When sklearn is available a ridge classifier is used;
    otherwise a closed-form NumPy one-hot ridge regression is the fallback. A
    label column that never appears in training is simply never predicted.
    """

    backend: str
    num_classes: int
    weights: npt.NDArray[np.float64]
    bias: npt.NDArray[np.float64]
    constant_class: int | None = None

    def decision_function(self, features: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        x = np.asarray(features, dtype=np.float64)
        return x @ self.weights.T + self.bias

    def predict(self, features: npt.NDArray[np.float64]) -> npt.NDArray[np.int64]:
        x = np.asarray(features, dtype=np.float64)
        if self.constant_class is not None:
            return np.full((x.shape[0],), self.constant_class, dtype=np.int64)
        scores = self.decision_function(x)
        return scores.argmax(axis=1).astype(np.int64)


def fit_linear_classifier(
    features: npt.NDArray[np.float64],
    labels: npt.NDArray[np.int64],
    *,
    num_classes: int,
    alpha: float = 1.0,
) -> LinearClassifierProbe:
    """Fit a deterministic linear classifier mapping activations to class indices.

    ``labels`` are canonical class indices in ``[0, num_classes)``. Uses sklearn's
    ``RidgeClassifier`` when importable and a NumPy one-hot ridge fallback
    otherwise; both are deterministic and seed-free.
    """
    x = np.asarray(features, dtype=np.float64)
    y = np.asarray(labels, dtype=np.int64)
    if x.ndim != 2:
        raise ValueError("features must be a 2-D array.")
    if y.shape != (x.shape[0],):
        raise ValueError("labels must have shape (n_samples,).")
    if num_classes < 1:
        raise ValueError("num_classes must be >= 1.")
    if alpha < 0:
        raise ValueError("alpha must be >= 0.")

    unique = np.unique(y)
    if unique.size <= 1:
        only = int(unique[0]) if unique.size == 1 else 0
        zeros_w = np.zeros((num_classes, x.shape[1]), dtype=np.float64)
        zeros_b = np.zeros((num_classes,), dtype=np.float64)
        return LinearClassifierProbe("constant", num_classes, zeros_w, zeros_b, constant_class=only)

    weights, bias, backend = _fit_ridge_classifier(x, y, num_classes=num_classes, alpha=alpha)
    return LinearClassifierProbe(backend, num_classes, weights, bias)


def _fit_ridge_classifier(
    x: npt.NDArray[np.float64],
    y: npt.NDArray[np.int64],
    *,
    num_classes: int,
    alpha: float,
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64], str]:
    try:
        from sklearn.linear_model import RidgeClassifier
    except ImportError:
        return (*_fit_numpy_ridge_classifier(x, y, num_classes=num_classes, alpha=alpha), "numpy_ridge")

    estimator = RidgeClassifier(alpha=alpha)
    estimator.fit(x, y)
    coef = np.asarray(estimator.coef_, dtype=np.float64)
    intercept = np.atleast_1d(np.asarray(estimator.intercept_, dtype=np.float64))
    seen = np.asarray(estimator.classes_, dtype=np.int64)
    weights = np.zeros((num_classes, x.shape[1]), dtype=np.float64)
    bias = np.full((num_classes,), -1e9, dtype=np.float64)  # unseen classes never win argmax
    if coef.ndim == 1 and seen.size == 2:
        # Binary RidgeClassifier exposes a single 1-D decision vector that scores
        # the positive class; the negative class sits at a constant 0 decision.
        # Argmax over the two reproduces RidgeClassifier's sign rule.
        weights[int(seen[1])] = coef
        bias[int(seen[1])] = float(intercept[0])
        bias[int(seen[0])] = 0.0
    else:
        coef_2d = coef if coef.ndim == 2 else coef.reshape(1, -1)
        for row, klass in enumerate(seen):
            weights[int(klass)] = coef_2d[row]
            bias[int(klass)] = float(intercept[row])
    return weights, bias, "sklearn_ridge"


def _fit_numpy_ridge_classifier(
    x: npt.NDArray[np.float64],
    y: npt.NDArray[np.int64],
    *,
    num_classes: int,
    alpha: float,
) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    n_samples, n_features = x.shape
    targets = np.full((n_samples, num_classes), -1.0, dtype=np.float64)
    targets[np.arange(n_samples), y] = 1.0
    design = np.hstack([x, np.ones((n_samples, 1))])
    penalty = alpha * np.eye(n_features + 1)
    penalty[-1, -1] = 0.0
    gram = design.T @ design + penalty
    coef = np.linalg.solve(gram, design.T @ targets)  # (n_features + 1, num_classes)
    weights = coef[:-1].T.astype(np.float64)
    bias = coef[-1].astype(np.float64)
    return weights, bias


def majority_baseline(
    train_labels: npt.NDArray[np.int64],
    eval_labels: npt.NDArray[np.int64],
) -> tuple[int, float]:
    """Return ``(majority_class, accuracy)`` of always predicting the train majority."""
    train = np.asarray(train_labels, dtype=np.int64)
    evaluation = np.asarray(eval_labels, dtype=np.int64)
    if train.size == 0:
        return 0, 0.0
    values, counts = np.unique(train, return_counts=True)
    majority = int(values[int(np.argmax(counts))])
    if evaluation.size == 0:
        return majority, 0.0
    return majority, float(np.mean(evaluation == majority))


def confusion_matrix(
    true_labels: npt.NDArray[np.int64],
    predicted_labels: npt.NDArray[np.int64],
    *,
    num_classes: int,
) -> npt.NDArray[np.int64]:
    """Return a ``(num_classes, num_classes)`` confusion matrix (rows = truth)."""
    matrix = np.zeros((num_classes, num_classes), dtype=np.int64)
    for truth, prediction in zip(true_labels, predicted_labels, strict=True):
        if 0 <= int(truth) < num_classes and 0 <= int(prediction) < num_classes:
            matrix[int(truth), int(prediction)] += 1
    return matrix


@dataclass(frozen=True)
class ProbeResult:
    """Train/val/test accuracy and diagnostics for one (site, label) probe."""

    site: str
    label: str
    backend: str
    num_classes: int
    class_names: list[str]
    train_accuracy: float
    val_accuracy: float
    test_accuracy: float
    majority_class: str
    majority_baseline_accuracy: float
    test_class_distribution: dict[str, int]
    confusion_matrix: list[list[int]]
    n_train: int
    n_val: int
    n_test: int
    metadata: dict[str, object] = field(default_factory=dict)

    @property
    def test_accuracy_above_baseline(self) -> float:
        return self.test_accuracy - self.majority_baseline_accuracy

    def to_dict(self) -> dict[str, object]:
        payload = {
            "site": self.site,
            "label": self.label,
            "backend": self.backend,
            "num_classes": self.num_classes,
            "class_names": self.class_names,
            "train_accuracy": self.train_accuracy,
            "val_accuracy": self.val_accuracy,
            "test_accuracy": self.test_accuracy,
            "majority_class": self.majority_class,
            "majority_baseline_accuracy": self.majority_baseline_accuracy,
            "test_accuracy_above_baseline": self.test_accuracy_above_baseline,
            "test_class_distribution": self.test_class_distribution,
            "confusion_matrix": self.confusion_matrix,
            "n_train": self.n_train,
            "n_val": self.n_val,
            "n_test": self.n_test,
        }
        payload.update(self.metadata)
        return payload


def train_probe(
    *,
    site: str,
    label: str,
    class_names: list[str],
    train_features: npt.NDArray[np.float64],
    train_labels: npt.NDArray[np.int64],
    val_features: npt.NDArray[np.float64],
    val_labels: npt.NDArray[np.int64],
    test_features: npt.NDArray[np.float64],
    test_labels: npt.NDArray[np.int64],
    alpha: float = 1.0,
) -> ProbeResult:
    """Fit a probe on ``train`` and report accuracy on train/val/test."""
    num_classes = len(class_names)
    probe = fit_linear_classifier(
        train_features, train_labels, num_classes=num_classes, alpha=alpha
    )
    train_acc = _accuracy(probe.predict(train_features), train_labels)
    val_acc = _accuracy(probe.predict(val_features), val_labels) if val_labels.size else 0.0
    test_pred = probe.predict(test_features) if test_labels.size else np.asarray([], dtype=np.int64)
    test_acc = _accuracy(test_pred, test_labels) if test_labels.size else 0.0
    majority_class, baseline = majority_baseline(train_labels, test_labels)
    matrix = confusion_matrix(test_labels, test_pred, num_classes=num_classes)
    distribution = _class_distribution(test_labels, class_names)
    return ProbeResult(
        site=site,
        label=label,
        backend=probe.backend,
        num_classes=num_classes,
        class_names=class_names,
        train_accuracy=train_acc,
        val_accuracy=val_acc,
        test_accuracy=test_acc,
        majority_class=class_names[majority_class] if class_names else str(majority_class),
        majority_baseline_accuracy=baseline,
        test_class_distribution=distribution,
        confusion_matrix=matrix.tolist(),
        n_train=int(train_labels.size),
        n_val=int(val_labels.size),
        n_test=int(test_labels.size),
    )


def _accuracy(predicted: npt.NDArray[np.int64], true: npt.NDArray[np.int64]) -> float:
    if true.size == 0:
        return 0.0
    return float(np.mean(np.asarray(predicted) == np.asarray(true)))


def _class_distribution(
    labels: npt.NDArray[np.int64], class_names: list[str]
) -> dict[str, int]:
    distribution: dict[str, int] = {}
    for index, name in enumerate(class_names):
        count = int(np.sum(np.asarray(labels) == index))
        if count:
            distribution[name] = count
    return distribution
