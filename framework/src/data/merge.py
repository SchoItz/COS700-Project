"""Merges sources: drops duplicates, conflicting labels take the maximum."""
from __future__ import annotations

import pandas as pd

from .schema import reqCol

dedupKey = ["userId", "timestamp", "eventType", "source"]


def mergeSources(frames: list[pd.DataFrame]) -> pd.DataFrame:
    if not frames:
        raise ValueError("merge_sources requires at least one DataFrame")

    for df in frames:
        missing = [c for c in reqCol if c not in df.columns]
        if missing:
            raise ValueError(f"Frame missing required columns: {missing}")

    merged = pd.concat(frames, ignore_index=True)[reqCol]

    merged = (
        merged.sort_values("label", ascending=False)
        .drop_duplicates(subset=dedupKey, keep="first")
        .sort_values(["userId", "timestamp"])
        .reset_index(drop=True)
    )
    return merged
