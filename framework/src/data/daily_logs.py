"""Loader for the single-day corpus (`data/generated/daily_logs/`).

Takes an `nWeeks` window per employee around a drift onset, with benign
employees given starts from the same onsets so time does not leak the label."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from paths import dailyLogsDir
from settings import SEED
from .schema import dailySummaryToSchema

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

deftWeeks = 20


class DailyLogsNotFound(FileNotFoundError):
    pass


def _csvPaths() -> list[Path]:
    if not dailyLogsDir.exists():
        raise DailyLogsNotFound(f"No daily logs found at {dailyLogsDir}")
    paths = [dailyLogsDir / f"{day}.csv" for day in WEEKDAYS]
    present = [p for p in paths if p.exists()]
    if not present:
        raise DailyLogsNotFound(f"No weekday CSV files found in {dailyLogsDir}")
    return present


def _driftOnsets(paths: list[Path]) -> pd.Series:
    """First malicious week per employee."""
    frames = [
        pd.read_csv(p, usecols=["employee_id", "weekNumber", "label"]) for p in paths
    ]
    labels = pd.concat(frames, ignore_index=True)
    return labels.loc[labels["label"] == 1].groupby("employee_id")["weekNumber"].min()


def _employeeWindows(
    paths: list[Path], nWeeks: int, seed: int
) -> tuple[pd.Series, pd.Series]:
    """Per-employee (first_week, last_week) window."""
    frames = [pd.read_csv(p, usecols=["employee_id", "weekNumber"]) for p in paths]
    index = pd.concat(frames, ignore_index=True)
    allEmp = pd.Index(sorted(index["employee_id"].unique()), name="employee_id")
    maxWeek = int(index["weekNumber"].max())

    onsets = _driftOnsets(paths)
    half = nWeeks // 2

    starts = pd.Series(index=allEmp, dtype=float)
    starts.loc[onsets.index] = onsets.to_numpy() - half

    undrifted = allEmp.difference(onsets.index)
    if len(undrifted):
        rng = np.random.default_rng(seed)
        drawn = rng.choice(onsets.to_numpy(), size=len(undrifted), replace=True) - half
        starts.loc[undrifted] = drawn

    starts = starts.clip(lower=0, upper=max(maxWeek - nWeeks + 1, 0)).astype(int)
    return starts, starts + nWeeks - 1


def loadDailyLogs(nWeeks: int = deftWeeks, seed: int = SEED) -> pd.DataFrame:
    """Loads the windowed corpus in the common schema. `n_weeks=0` loads all weeks."""
    paths = _csvPaths()

    if nWeeks and nWeeks > 0:
        firstWeek, lastWeek = _employeeWindows(paths, nWeeks, seed)
    else:
        firstWeek = lastWeek = None

    frames = []
    for path in paths:
        day = pd.read_csv(path)
        if firstWeek is not None:
            lo = day["employee_id"].map(firstWeek)
            hi = day["employee_id"].map(lastWeek)
            day = day[(day["weekNumber"] >= lo) & (day["weekNumber"] <= hi)]
        frames.append(day)

    df = pd.concat(frames, ignore_index=True)
    if df.empty:
        raise DailyLogsNotFound(
            f"The requested {nWeeks}-week window selected no rows from {dailyLogsDir}"
        )

    return dailySummaryToSchema(df, "dailyLogs")
