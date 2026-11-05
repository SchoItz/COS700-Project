"""Stratified k-fold CV. Resampling is applied to the training fold only."""
from __future__ import annotations

from collections.abc import Callable
from typing import Literal

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

from .metrics import countMetrics, rateMetrics, computeMetrics

Resample = Literal["none", "smote", "undersample"]

SEED = 42
minMinSmote = 6


def resampleTrainingFold(
    X: np.ndarray, y: np.ndarray, strategy: Resample = "none", seed: int = SEED
) -> tuple[np.ndarray, np.ndarray]:
    """Rebalances a training fold; returns it unchanged if resampling is impossible."""
    if strategy == "none":
        return X, y

    nMin = int((y == 1).sum())
    if nMin < 2 or nMin == len(y):
        return X, y

    if strategy == "smote":
        if nMin < minMinSmote:
            return X, y
        from imblearn.over_sampling import SMOTE

        k = min(5, nMin - 1)
        return SMOTE(random_state=seed, k_neighbors=k).fit_resample(X, y)

    if strategy == "undersample":
        from imblearn.under_sampling import RandomUnderSampler

        nMaj = int((y == 0).sum())
        target = min(nMaj, 3 * nMin)
        sampler = RandomUnderSampler(
            random_state=seed, sampling_strategy={0: target, 1: nMin}
        )
        return sampler.fit_resample(X, y)

    raise ValueError(f"Unknown resampling strategy '{strategy}'")


def crossValidateDetector(
    buildDet: Callable[[], object],
    X: np.ndarray,
    y: np.ndarray,
    nSplits: int = 5,
    threshold: float = 0.5,
    seed: int = SEED,
    resample: Resample = "none",
    thresholds: np.ndarray | None = None,
) -> pd.DataFrame:
    """Per-fold metrics. `thresholds` optionally sets a per-row cut-off."""
    skf = StratifiedKFold(n_splits=nSplits, shuffle=True, random_state=seed)
    rows = []
    for fold, (trainIdx, testIdx) in enumerate(skf.split(X, y)):
        X_train, yTrain = resampleTrainingFold(
            X[trainIdx], y[trainIdx], resample, seed=seed
        )
        detector = buildDet()
        detector.fit(X_train, yTrain)

        scores = detector.predict_proba(X[testIdx])
        cutOff = threshold if thresholds is None else thresholds[testIdx]
        metrics = computeMetrics(y[testIdx], (scores >= cutOff).astype(int), scores=scores)
        metrics["fold"] = fold
        rows.append(metrics)
    return pd.DataFrame(rows)


def summariseFolds(perFold: pd.DataFrame) -> dict[str, float]:
    """Mean of each metric across folds, plus F1 standard deviation."""
    summary = {m: float(perFold[m].mean()) for m in rateMetrics if m in perFold}
    summary.update(
        {m: float(perFold[m].mean()) for m in countMetrics if m in perFold}
    )
    if "f1" in perFold:
        summary["f1Std"] = float(perFold["f1"].std(ddof=0))
    summary["nFolds"] = int(len(perFold))
    return summary
