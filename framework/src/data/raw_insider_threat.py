"""Loader for the Kaggle insider threat dataset, mapped onto the common schema.

`is_malicious` (per day) is the label; the per-employee flag would leak identity."""
from __future__ import annotations

import pandas as pd

from paths import rawInsiderThreatFile as RAW_FILE
from .schema import conform


class RawInsiderThreatNotFound(FileNotFoundError):
    pass


def loadRawInsiderThreat() -> pd.DataFrame:
    if not RAW_FILE.exists():
        raise RawInsiderThreatNotFound(f"No file found at {RAW_FILE}")

    raw = pd.read_csv(RAW_FILE)

    date = pd.to_datetime(raw["date"])
    entryTime = pd.to_timedelta(raw["first_entry_time"].fillna("08:00") + ":00", errors="coerce")
    entryTime = entryTime.fillna(pd.Timedelta(hours=8))
    timestamp = date + entryTime

    df = pd.DataFrame(
        {
            "userId": "RAW" + raw["employee_id"].astype(str),
            "timestamp": timestamp,
            "source": "rawInsiderThreat",
            "eventType": "dailySummary",
            "department": raw["employee_department"],
            "role": raw["employee_position"],
            "offHours": raw["entered_during_night_hours"].fillna(0).astype(int),
            "weekend": raw["entry_during_weekend"].fillna(0).astype(int),
            "deviceActivityCount": raw["num_burn_requests"].fillna(0),
            "printActivityCount": raw["num_print_commands"].fillna(0),
            "emailActivityCount": 0,
            "fileActivityCount": raw["total_files_burned"].fillna(0),
            "httpActivityCount": raw["num_exits"].fillna(0),
            "failedLoginCount": 0,
            "dataTransfMb": raw["total_burn_volume_mb"].fillna(0.0),
            "sessionDurationMinutes": raw["total_presence_minutes"].fillna(0.0),
            "label": raw["is_malicious"].fillna(0).astype(int),
        }
    )

    return conform(df, "rawInsiderThreat")
