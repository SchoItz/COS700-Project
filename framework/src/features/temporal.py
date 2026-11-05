"""Temporal layer: deviation from each user's prior baseline and from peers."""
from __future__ import annotations

import numpy as np
import pandas as pd

from data.schema import actCol

defWindow = 14

minPeriods = 3

peerKeys = ["department", "role", "date"]


def _present(df: pd.DataFrame) -> list[str]:
    return [c for c in actCol if c in df.columns]


def buildUserBaselines(df: pd.DataFrame, window: int = defWindow) -> pd.DataFrame:
    """Adds rolling mean/std over the previous `window` events per activity."""
    df = df.sort_values(["userId", "timestamp"]).copy()
    users = df["userId"]

    for col in _present(df):
        prior = df.groupby(users, sort=False)[col].shift(1)
        rolling = prior.groupby(users, sort=False).rolling(window, min_periods=minPeriods)
        df[f"{col}_baselineMean"] = rolling.mean().reset_index(level=0, drop=True)
        df[f"{col}_baselineStd"] = rolling.std().reset_index(level=0, drop=True)

    return df


def computeDeviationFeatures(
    df: pd.DataFrame, window: int = defWindow
) -> pd.DataFrame:
    """Adds self and peer z-scores and `devScore`. Zero std gives zero."""
    df = buildUserBaselines(df, window=window)
    df["date"] = pd.to_datetime(df["timestamp"]).dt.normalize()

    activityCols = _present(df)
    hasPeers = all(k in df.columns for k in peerKeys)
    peerGroups = df.groupby(peerKeys, sort=False) if hasPeers else None

    zScoreCols = []
    newCols: dict[str, pd.Series] = {}
    for col in activityCols:
        stdSelf = df[f"{col}_baselineStd"].replace(0.0, np.nan)
        zSelf = (df[col] - df[f"{col}_baselineMean"]) / stdSelf
        newCols[f"{col}_zscoreSelf"] = zSelf.fillna(0.0)
        zScoreCols.append(f"{col}_zscoreSelf")

        if peerGroups is not None:
            peerMean = peerGroups[col].transform("mean")
            peerStd = peerGroups[col].transform("std").replace(0.0, np.nan)
            newCols[f"{col}_zscorePeer"] = ((df[col] - peerMean) / peerStd).fillna(0.0)
            zScoreCols.append(f"{col}_zscorePeer")

    df = pd.concat([df, pd.DataFrame(newCols, index=df.index)], axis=1)
    df["devScore"] = df[zScoreCols].abs().mean(axis=1)
    return df.drop(columns=["date"])
