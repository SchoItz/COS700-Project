"""Permutation importance of behavioural signals on held-out data."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split

SEED = 42


def signalImportance(
    buildDet,
    X: np.ndarray,
    y: np.ndarray,
    names: list[str],
    nRep: int = 10,
    testSize: float = 0.3,
    seed: int = SEED,
) -> pd.DataFrame:
    """Mean and std drop in average precision per shuffled feature, most important first."""
    X_train, X_test, yTrain, yTest = train_test_split(
        X, y, test_size=testSize, stratify=y, random_state=seed
    )
    detector = buildDet()
    detector.fit(X_train, yTrain)

    estimator = getattr(detector, "estimator", detector)
    result = permutation_importance(
        estimator,
        X_test,
        yTest,
        scoring="average_precision",
        n_repeats=nRep,
        random_state=seed,
        n_jobs=-1,
    )

    return (
        pd.DataFrame(
            {
                "feature": names,
                "importance": result.importances_mean,
                "importanceStd": result.importances_std,
            }
        )
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )


def signalKind(feature: str) -> str:
    if feature.endswith("_zscoreSelf"):
        return "deviation from own baseline"
    if feature.endswith("_zscorePeer"):
        return "deviation from peer group"
    if "trustScore" in feature:
        return "dynamic trust score"
    if feature.startswith("categorical__"):
        return "categorical attribute"
    return "raw daily value"


def importanceByKind(importance: pd.DataFrame) -> pd.DataFrame:
    """Total importance per kind of signal."""
    grouped = importance.assign(kind=importance["feature"].map(signalKind))
    out = (
        grouped.groupby("kind")["importance"]
        .agg(total="sum", mean="mean", n_features="count")
        .sort_values("total", ascending=False)
    )
    out["share"] = out["total"] / out["total"].sum()
    return out.reset_index()
