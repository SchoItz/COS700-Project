"""Gradient boosting, voting, stacking and trust-weighted ensembles."""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import (
    GradientBoostingClassifier,
    StackingClassifier,
    VotingClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier

from models.base import DetectorFactory, ScoreThresholdMixin
from models.classical.sklearn_models import SklearnDetector, calibratedSvc

SEED = 42


def _baseEstimators():
    return [
        ("logreg", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ("tree", DecisionTreeClassifier(class_weight="balanced", random_state=SEED)),
        ("svc", calibratedSvc()),
    ]


class GradientBoostingDetector(SklearnDetector):
    def __init__(self):
        super().__init__("gradBoosting", GradientBoostingClassifier(random_state=SEED))


class VotingDetector(SklearnDetector):
    def __init__(self):
        super().__init__(
            "votingEnsemble",
            VotingClassifier(estimators=_baseEstimators(), voting="soft", n_jobs=-1),
        )


stackFolds = 3


class StackingDetector(SklearnDetector):
    def __init__(self):
        super().__init__(
            "stackingEnsemble",
            StackingClassifier(
                estimators=_baseEstimators(),
                final_estimator=LogisticRegression(max_iter=1000, class_weight="balanced"),
                cv=stackFolds,
                n_jobs=-1,
            ),
        )


class TrustWeightedEnsemble(ScoreThresholdMixin):
    """Soft voting with scores scaled by `1 - gain * trust`.

    `trustCol` is the trust column's index; it is mapped back to [0, 1] with
    training statistics. With `trustCol=None` this is plain soft voting."""

    name = "trustWeightedEnsemble"

    def __init__(
        self,
        factories: list[DetectorFactory] | None = None,
        trustCol: int | None = None,
        weights: list[float] | None = None,
        gain: float = 0.4,
    ):
        if factories is None:
            factories = [
                lambda: SklearnDetector(
                    "logreg", LogisticRegression(max_iter=1000, class_weight="balanced")
                ),
                lambda: SklearnDetector(
                    "tree", DecisionTreeClassifier(class_weight="balanced", random_state=SEED)
                ),
                GradientBoostingDetector,
            ]
        self.factories = factories
        self.trustCol = trustCol
        self.gain = gain
        self.weights = weights or [1.0 / len(factories)] * len(factories)
        self.detectors: list = []
        self._trustRange = (0.0, 1.0)

    def fit(self, X: np.ndarray, y: np.ndarray) -> TrustWeightedEnsemble:
        self.detectors = [factory() for factory in self.factories]
        for detector in self.detectors:
            detector.fit(X, y)
        if self.trustCol is not None:
            column = np.asarray(X)[:, self.trustCol].astype(float)
            lo, hi = float(column.min()), float(column.max())
            self._trustRange = (lo, max(hi, lo + 1e-9))
        return self

    def _trust(self, X: np.ndarray) -> np.ndarray | None:
        if self.trustCol is None:
            return None
        lo, hi = self._trustRange
        return np.clip((np.asarray(X)[:, self.trustCol].astype(float) - lo) / (hi - lo), 0.0, 1.0)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        scores = np.zeros(len(X), dtype=float)
        for weight, detector in zip(self.weights, self.detectors):
            scores += weight * detector.predict_proba(X)
        trust = self._trust(X)
        if trust is not None:
            scores = scores * (1.0 - self.gain * trust)
        return np.clip(scores, 0.0, 1.0)


def combinedFactories(trustCol: int | None = None) -> dict[str, DetectorFactory]:
    """`trustCol` is the trust column's index in the feature matrix."""
    return {
        "gradBoosting": GradientBoostingDetector,
        "votingEnsemble": VotingDetector,
        "stackingEnsemble": StackingDetector,
        "trustWeightedEnsemble": lambda: TrustWeightedEnsemble(trustCol=trustCol),
    }
