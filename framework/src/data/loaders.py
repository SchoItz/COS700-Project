"""Stub loaders for the raw sources; they raise until files exist in `data/raw/`."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from paths import rawDir
from .schema import reqCol


class RawSourceNotFound(FileNotFoundError):
    pass


def _requireColumns(df: pd.DataFrame, source: str) -> pd.DataFrame:
    missing = [c for c in reqCol if c not in df.columns]
    if missing:
        raise ValueError(f"Loader for '{source}' is missing required columns: {missing}")
    return df[reqCol]


def _loadCsvOrRaise(sourceDir: Path, source: str) -> pd.DataFrame:
    if not sourceDir.exists():
        raise RawSourceNotFound(
            f"No raw data found for source '{source}' at {sourceDir}. "
            "Download it from Kaggle/CERT and place it there, or run the "
            "pipeline with --synthetic."
        )
    csvs = sorted(sourceDir.glob("*.csv"))
    if not csvs:
        raise RawSourceNotFound(f"No CSV files found in {sourceDir} for source '{source}'.")
    frames = [pd.read_csv(f) for f in csvs]
    df = pd.concat(frames, ignore_index=True)
    df["source"] = source
    return df


def loadZaki2024() -> pd.DataFrame:
    df = _loadCsvOrRaise(rawDir / "zaki2024", "zaki2024")
    return _requireColumns(df, "zaki2024")


def loadKaggleClassified2024() -> pd.DataFrame:
    df = _loadCsvOrRaise(rawDir / "kaggleClassified2024", "kaggleClassified2024")
    return _requireColumns(df, "kaggleClassified2024")


def loadKaggleUeba2024() -> pd.DataFrame:
    df = _loadCsvOrRaise(rawDir / "kaggleUeba2024", "kaggleUeba2024")
    return _requireColumns(df, "kaggleUeba2024")


def loadKaggleTestdataset() -> pd.DataFrame:
    df = _loadCsvOrRaise(rawDir / "kaggleTestdataset", "kaggleTestdataset")
    return _requireColumns(df, "kaggleTestdataset")


def loadKaggleR62() -> pd.DataFrame:
    df = _loadCsvOrRaise(rawDir / "kaggleR62", "kaggleR62")
    return _requireColumns(df, "kaggleR62")


def loadCertGlasser2013() -> pd.DataFrame:
    df = _loadCsvOrRaise(rawDir / "certGlasser2013", "certGlasser2013")
    return _requireColumns(df, "certGlasser2013")


allLoad = {
    "zaki2024": loadZaki2024,
    "kaggleClassified2024": loadKaggleClassified2024,
    "kaggleUeba2024": loadKaggleUeba2024,
    "kaggleTestdataset": loadKaggleTestdataset,
    "kaggleR62": loadKaggleR62,
    "certGlasser2013": loadCertGlasser2013,
}
