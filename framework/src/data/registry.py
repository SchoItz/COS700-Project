"""Every loadable dataset, by name."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class DatasetInfo:
    name: str
    title: str
    origin: str
    inPaper: bool
    load: Callable[..., pd.DataFrame]
    generator: str = "Own generator"


def _month(**_):
    from .month_logs import loadMonthLogs

    return loadMonthLogs()


def _singleDay(**_):
    from .daily_logs import loadDailyLogs

    return loadDailyLogs()


def _kaggle(**_):
    from .raw_insider_threat import loadRawInsiderThreat

    return loadRawInsiderThreat()


def _twoWeek(**_):
    from .two_week_logs import loadTwoWeekLogs

    return loadTwoWeekLogs()


def _synthetic(nUsers: int = 150, nDays: int = 45, **_):
    from .synthetic import generateSyntheticDataset

    return generateSyntheticDataset(nUsers=nUsers, nDays=nDays)


def _rawSources(**_):
    """All raw sources, merged."""
    from .loaders import allLoad
    from .merge import mergeSources

    frames = []
    for name, loader in allLoad.items():
        try:
            frames.append(loader())
        except FileNotFoundError as exc:
            print(f"[data] skipping '{name}': {exc}")
    if not frames:
        raise RuntimeError(
            "No raw sources found under data/raw/. Download the Kaggle/CERT "
            "datasets, or use one of the bundled datasets instead."
        )
    return mergeSources(frames)


DATASETS: dict[str, DatasetInfo] = {
    info.name: info
    for info in (
        DatasetInfo("month", "30-day logs", "Synthetic", True, _month),
        DatasetInfo("singleDay", "Single-day logs", "Synthetic", True, _singleDay),
        DatasetInfo(
            "rawInsiderThreat", "Kaggle insider threat", "Synthetic", True, _kaggle,
            generator="Third party",
        ),
        DatasetInfo("twoWeek", "Two-week logs", "Synthetic", False, _twoWeek),
        DatasetInfo("synthetic", "Synthetic data", "Synthetic", False, _synthetic),
        DatasetInfo("raw", "Merged raw sources", "Synthetic", False, _rawSources,
                    generator="Third party"),
    )
}

datasetNames = tuple(DATASETS)


def loadDataset(name: str, nUsers: int = 150, nDays: int = 45) -> pd.DataFrame:
    """Loads a dataset by name in the common schema."""
    if name not in DATASETS:
        raise ValueError(f"Unknown dataset '{name}', expected one of {datasetNames}")
    return DATASETS[name].load(nUsers=nUsers, nDays=nDays)


def describe(df: pd.DataFrame) -> dict[str, float]:
    """Size and class balance of a dataset."""
    return {
        "rows": int(len(df)),
        "employees": int(df["userId"].nunique()),
        "positiveRows": int(df["label"].sum()),
        "positiveRate": float(df["label"].mean()),
    }
