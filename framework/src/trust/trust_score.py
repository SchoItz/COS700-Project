"""Trust layer: a per-user score in [0, 1] that drops with deviation and recovers.

Used as a feature (`applyAsFeature`) or also as a per-user alert threshold
(`applyAsSensitivity`)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class TrustConfig:
    decayRate: float = 0.25
    recovRate: float = 0.03
    devThreshold: float = 1.5
    minTrust: float = 0.0
    maxTrust: float = 1.0
    initTrust: float = 1.0


baseThreshold = 0.5
sensGain = 0.3
thresholdBounds = (0.05, 0.95)


def alertThreshold(
    trust: pd.Series | np.ndarray,
    baseThreshold: float = baseThreshold,
    sensGain: float = sensGain,
):
    """`clip(base + gain * (trust - 0.5))`."""
    return (baseThreshold + sensGain * (trust - 0.5)).clip(*thresholdBounds)


class DynamicTrustModel:
    """Running trust score per user from `devScore`."""

    def __init__(self, config: TrustConfig | None = None):
        self.config = config or TrustConfig()

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        if "devScore" not in df.columns:
            raise ValueError("Expected a 'devScore' column; run features.temporal first.")

        df = df.sort_values(["userId", "timestamp"]).copy()
        cfg = self.config

        deviations = df["devScore"].to_numpy(dtype=float)
        trust = np.empty(len(df), dtype=float)

        codes = pd.factorize(df["userId"], sort=False)[0]
        starts = np.flatnonzero(np.r_[True, codes[1:] != codes[:-1]])
        ends = np.r_[starts[1:], len(df)] if len(starts) else np.array([], dtype=int)

        for start, end in zip(starts, ends):
            value = cfg.initTrust
            for i in range(start, end):
                excess = deviations[i] - cfg.devThreshold
                value += -cfg.decayRate * excess if excess > 0 else cfg.recovRate
                value = min(max(value, cfg.minTrust), cfg.maxTrust)
                trust[i] = value

        df["trustScore"] = trust
        return df

    def applyAsFeature(self, df: pd.DataFrame) -> pd.DataFrame:
        """Adds `trustScore` as a feature."""
        return self.compute(df)

    def applyAsSensitivity(
        self,
        df: pd.DataFrame,
        baseThreshold: float = baseThreshold,
        sensGain: float = sensGain,
    ) -> pd.DataFrame:
        """Also adds a clipped per-user `alertThreshold`; low trust lowers it."""
        df = self.compute(df)
        df["alertThreshold"] = alertThreshold(
            df["trustScore"], baseThreshold, sensGain
        )
        return df
