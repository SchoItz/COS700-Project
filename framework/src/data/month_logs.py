"""Loader for the 30-day dataset (`data/generated/monthLogs/`)."""
from __future__ import annotations

import pandas as pd

from paths import monthLogsDir
from .schema import dailySummaryToSchema


class MonthLogsNotFound(FileNotFoundError):
    pass


def loadMonthLogs() -> pd.DataFrame:
    csvs = sorted(monthLogsDir.glob("*.csv"))
    if not csvs:
        raise MonthLogsNotFound(f"No CSV files found in {monthLogsDir}")
    df = pd.concat([pd.read_csv(f) for f in csvs], ignore_index=True)
    return dailySummaryToSchema(df, "monthLogs")
