"""Shared detector interface. Registries return factories so each fold gets a fresh model."""
from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

import numpy as np


class Detector(Protocol):
    name: str

    def fit(self, X: np.ndarray, y: np.ndarray) -> Detector: ...

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Malicious-class score in [0, 1]."""
        ...

    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        return (self.predict_proba(X) >= threshold).astype(int)


DetectorFactory = Callable[[], Detector]


class ScoreThresholdMixin:
    """`predict` from a [0, 1] `predict_proba`."""

    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        return (self.predict_proba(X) >= threshold).astype(int)


def minmaxToUnit(raw: np.ndarray) -> np.ndarray:
    """Scales a score to [0, 1]; constant input gives zeros."""
    raw = np.asarray(raw, dtype=float)
    lo, hi = raw.min(), raw.max()
    if hi - lo < 1e-12:
        return np.zeros_like(raw)
    return (raw - lo) / (hi - lo)
