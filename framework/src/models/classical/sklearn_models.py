"""Logistic regression, decision tree, random forest, SVM and isolation forest."""
from __future__ import annotations

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from models.base import DetectorFactory, ScoreThresholdMixin, minmaxToUnit

SEED = 42


calibFolds = 3


def calibratedSvc() -> CalibratedClassifierCV:
    """SVC with Platt-scaled probabilities."""
    return CalibratedClassifierCV(
        SVC(class_weight="balanced", random_state=SEED, cache_size=1000),
        method="sigmoid",
        ensemble=False,
        cv=calibFolds,
    )


class SklearnDetector(ScoreThresholdMixin):
    """Wraps a scikit-learn classifier with `predict_proba`."""

    def __init__(self, name: str, estimator):
        self.name = name
        self.estimator = estimator
        self._constant: float | None = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> SklearnDetector:
        classes = np.unique(y)
        if len(classes) < 2:
            self._constant = 1.0 if len(classes) and classes[0] == 1 else 0.0
            return self
        self._constant = None
        self.estimator.fit(X, y)
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if self._constant is not None:
            return np.full(len(X), self._constant)
        proba = self.estimator.predict_proba(X)
        if proba.shape[1] == 1:
            return np.full(len(X), 1.0 if self.estimator.classes_[0] == 1 else 0.0)
        return proba[:, 1]


class IsolationForestDetector(ScoreThresholdMixin):
    """Trained on benign rows only."""

    name = "isolationForest"

    def __init__(self, **kwargs):
        self.estimator = IsolationForest(random_state=SEED, n_jobs=-1, **kwargs)

    def fit(self, X: np.ndarray, y: np.ndarray) -> IsolationForestDetector:
        normal = X[np.asarray(y) == 0] if y is not None else X
        self.estimator.fit(normal if len(normal) else X)
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return minmaxToUnit(-self.estimator.decision_function(X))


def classicalFactories() -> dict[str, DetectorFactory]:
    return {
        "logisticRegression": lambda: SklearnDetector(
            "logisticRegression", LogisticRegression(max_iter=1000, class_weight="balanced")
        ),
        "decTree": lambda: SklearnDetector(
            "decTree", DecisionTreeClassifier(class_weight="balanced", random_state=SEED)
        ),
        "randomForest": lambda: SklearnDetector(
            "randomForest",
            RandomForestClassifier(
                n_estimators=300, class_weight="balanced", random_state=SEED, n_jobs=-1
            ),
        ),
        "svm": lambda: SklearnDetector("svm", calibratedSvc()),
        "isolationForest": lambda: IsolationForestDetector(contamination="auto"),
    }
