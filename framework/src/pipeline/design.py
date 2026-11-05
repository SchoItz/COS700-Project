"""raw frame -> temporal layer -> trust layer -> preprocessing -> Design"""
from __future__ import annotations

from typing import Literal, NamedTuple

import numpy as np
import pandas as pd

from data.preprocess import preprocess, preprocessApply
from features.temporal import computeDeviationFeatures
from trust import DynamicTrustModel

nonFeatCol = ("userId", "timestamp", "alertThreshold")

thresholdCol = "alertThreshold"

trustFeat = "numeric__trustScore"

TrustMode = Literal["none", "feature", "sensitivity"]

defTrustMode: TrustMode = "feature"


def featurise(rawDf: pd.DataFrame, trustMode: TrustMode = defTrustMode) -> pd.DataFrame:
    """Runs the temporal and trust layers and keeps the z-scores.

    trustMode: "none" (no trust), "feature" (adds `trustScore`),
    "sensitivity" (also adds a per-row `alertThreshold`)."""
    featurised = computeDeviationFeatures(rawDf)

    if trustMode == "none":
        withTrust = featurised
    elif trustMode == "feature":
        withTrust = DynamicTrustModel().applyAsFeature(featurised)
    elif trustMode == "sensitivity":
        withTrust = DynamicTrustModel().applyAsSensitivity(featurised)
    else:
        raise ValueError(f"Unknown trustMode '{trustMode}'")

    drop = [c for c in withTrust.columns if c.endswith(("_baselineMean", "_baselineStd"))]
    drop.append("devScore")
    return withTrust.drop(columns=[c for c in drop if c in withTrust.columns])


class Design(NamedTuple):
    """Feature matrix plus what detection and validation need."""

    X: np.ndarray
    y: np.ndarray
    names: list[str]
    preprocessor: object
    thresholds: np.ndarray | None

    @property
    def trustCol(self) -> int | None:
        return trustColumnIndex(self.names)


def _featureColumns(X_df: pd.DataFrame) -> list[str]:
    return [c for c in X_df.columns if c not in nonFeatCol]


def _thresholds(X_df: pd.DataFrame) -> np.ndarray | None:
    if thresholdCol not in X_df.columns:
        return None
    return X_df[thresholdCol].to_numpy(dtype=float)


def designMatrix(df: pd.DataFrame) -> Design:
    """Fits and transforms `df` into a `Design`."""
    X_df, y, preprocessor = preprocess(df)
    names = _featureColumns(X_df)
    return Design(
        X_df[names].to_numpy(dtype=float), y.to_numpy(), names, preprocessor, _thresholds(X_df)
    )


def applyDesignMatrix(df: pd.DataFrame, preprocessor, names: list[str]) -> Design:
    """Transforms `df` with a fitted preprocessor."""
    X_df, y = preprocessApply(df, preprocessor)
    return Design(
        X_df[names].to_numpy(dtype=float), y.to_numpy(), names, preprocessor, _thresholds(X_df)
    )


def trustColumnIndex(names: list[str]) -> int | None:
    """Index of the trust column, or None."""
    return names.index(trustFeat) if trustFeat in names else None
