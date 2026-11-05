"""Synthetic event logs in the common schema, with a few drifting users."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .schema import reqCol

DEPARTMENTS = ["engineering", "finance", "hr", "sales", "it"]
ROLES = ["staff", "manager", "admin", "contractor"]
eventTypes = ["logon", "file", "email", "http", "device", "print"]


def generateSyntheticDataset(
    nUsers: int = 200,
    nDays: int = 60,
    eventsPerUserDay: float = 4.0,
    malFraction: float = 0.08,
    seed: int = 42,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    users = [f"user_{i:04d}" for i in range(nUsers)]
    departments = rng.choice(DEPARTMENTS, size=nUsers)
    roles = rng.choice(ROLES, size=nUsers)
    nMal = max(1, int(nUsers * malFraction))
    malUsers = set(rng.choice(users, size=nMal, replace=False))

    start = pd.Timestamp("2024-01-01")
    rows = []
    for idx, user in enumerate(users):
        is_malicious = user in malUsers
        driftLo = max(1, nDays // 2)
        driftHi = max(driftLo + 1, nDays - 1)
        driftStartDay = rng.integers(driftLo, driftHi) if is_malicious else None
        nEvents = rng.poisson(eventsPerUserDay * nDays)
        dayOffsets = rng.integers(0, nDays, size=nEvents)
        for day in sorted(dayOffsets):
            drifted = is_malicious and driftStartDay is not None and day >= driftStartDay
            hour = int(rng.normal(22, 3) if drifted else rng.normal(13, 3))
            hour = min(max(hour, 0), 23)
            ts = start + pd.Timedelta(days=int(day), hours=hour, minutes=int(rng.integers(0, 60)))
            offHours = int(hour < 7 or hour > 19)
            weekend = int(ts.dayofweek >= 5)
            deviceCt = rng.poisson(5 if drifted else 1)
            printCt = rng.poisson(4 if drifted else 1)
            emailCt = rng.poisson(2)
            fileCt = rng.poisson(8 if drifted else 3)
            httpCt = rng.poisson(6)
            failedLoginCt = rng.poisson(2 if drifted else 0.1)
            dataTransfMb = max(float(rng.normal(150 if drifted else 30, 20)), 0.0)
            sessionMin = float(rng.normal(90 if drifted else 45, 15))
            rows.append(
                {
                    "userId": user,
                    "timestamp": ts,
                    "source": "synthetic",
                    "eventType": rng.choice(eventTypes),
                    "department": departments[idx],
                    "role": roles[idx],
                    "offHours": offHours,
                    "weekend": weekend,
                    "deviceActivityCount": deviceCt,
                    "printActivityCount": printCt,
                    "emailActivityCount": emailCt,
                    "fileActivityCount": fileCt,
                    "httpActivityCount": httpCt,
                    "failedLoginCount": failedLoginCt,
                    "dataTransfMb": dataTransfMb,
                    "sessionDurationMinutes": max(sessionMin, 1.0),
                    "label": int(drifted),
                }
            )

    df = pd.DataFrame(rows)[reqCol]
    df = df.sort_values(["userId", "timestamp"]).reset_index(drop=True)
    return df
