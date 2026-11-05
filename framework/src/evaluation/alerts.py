"""Turns scores into a ranked alert list."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold


def generateAlerts(
    df: pd.DataFrame,
    scores: np.ndarray | pd.Series,
    defThreshold: float = 0.5,
) -> pd.DataFrame:
    """Ranked rows of `df` above `alertThreshold` (or `defThreshold`)."""
    thresholds = (
        df["alertThreshold"].to_numpy()
        if "alertThreshold" in df.columns
        else np.full(len(df), defThreshold, dtype=float)
    )
    scores = np.asarray(scores.values if hasattr(scores, "values") else scores, dtype=float)

    alerts = df[["userId", "timestamp"]].copy()
    alerts["score"] = scores
    alerts["threshold"] = thresholds
    for optional in ("trustScore", "label"):
        if optional in df.columns:
            alerts[optional] = df[optional].to_numpy()

    alerts = alerts[scores >= thresholds]
    return alerts.sort_values("score", ascending=False).reset_index(drop=True)


def outOfFoldScores(
    buildDet,
    X: np.ndarray,
    y: np.ndarray,
    nSplits: int = 10,
    seed: int = 42,
) -> np.ndarray:
    """Scores each row with a model that did not train on it."""
    scores = np.empty(len(X), dtype=float)
    splitter = StratifiedKFold(n_splits=nSplits, shuffle=True, random_state=seed)
    for trainIdx, testIdx in splitter.split(X, y):
        detector = buildDet()
        detector.fit(X[trainIdx], y[trainIdx])
        scores[testIdx] = detector.predict_proba(X[testIdx])
    return scores
