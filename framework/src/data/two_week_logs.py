"""Loader for the two-week dataset (`data/generated/twoWeekLogs/`). Not used in the report."""
from __future__ import annotations

import pandas as pd

from paths import twoWeekLogsDir
from .schema import dailySummaryToSchema


class TwoWeekLogsNotFound(FileNotFoundError):
    pass


def loadTwoWeekLogs() -> pd.DataFrame:
    csvs = sorted(twoWeekLogsDir.glob("*.csv"))
    if not csvs:
        raise TwoWeekLogsNotFound(f"No CSV files found in {twoWeekLogsDir}")
    df = pd.concat([pd.read_csv(f) for f in csvs], ignore_index=True)
    return dailySummaryToSchema(df, "twoWeekLogs")
