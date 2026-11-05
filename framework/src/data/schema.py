"""Common schema every source is mapped onto."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class ColumnSpec:
    name: str
    dtype: str


commonSchema: list[ColumnSpec] = [
    ColumnSpec("userId", "id"),
    ColumnSpec("timestamp", "datetime"),
    ColumnSpec("source", "categorical"),
    ColumnSpec("eventType", "categorical"),
    ColumnSpec("department", "categorical"),
    ColumnSpec("role", "categorical"),
    ColumnSpec("offHours", "numeric"),
    ColumnSpec("weekend", "numeric"),
    ColumnSpec("deviceActivityCount", "numeric"),
    ColumnSpec("printActivityCount", "numeric"),
    ColumnSpec("emailActivityCount", "numeric"),
    ColumnSpec("fileActivityCount", "numeric"),
    ColumnSpec("httpActivityCount", "numeric"),
    ColumnSpec("failedLoginCount", "numeric"),
    ColumnSpec("dataTransfMb", "numeric"),
    ColumnSpec("sessionDurationMinutes", "numeric"),
    ColumnSpec("label", "label"),
]

catCol = [c.name for c in commonSchema if c.dtype == "categorical"]
excluded = [
    "originCountry",
    "citizenship",
    "medicalHistory",
]

reqCol = [c.name for c in commonSchema]


actCol = [
    "deviceActivityCount",
    "printActivityCount",
    "emailActivityCount",
    "fileActivityCount",
    "httpActivityCount",
    "failedLoginCount",
    "dataTransfMb",
    "sessionDurationMinutes",
]


def conform(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """Validates `df` and returns the schema columns sorted by employee and time."""
    missing = [c for c in reqCol if c not in df.columns]
    if missing:
        raise ValueError(f"{source} is missing required columns after mapping: {missing}")
    return df[reqCol].sort_values(["userId", "timestamp"]).reset_index(drop=True)


def dailySummaryToSchema(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """Maps a one-row-per-employee-day CSV onto the schema. Missing `loginHour` becomes midnight."""
    loginHour = pd.to_numeric(df["loginHour"], errors="coerce").fillna(0.0)
    df = df.assign(
        timestamp=pd.to_datetime(df["date"]) + pd.to_timedelta(loginHour, unit="h"),
        userId=df["employee_id"],
        source=source,
        eventType="dailySummary",
    )
    return conform(df, source)
