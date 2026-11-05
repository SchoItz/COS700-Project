"""Generates the single-day corpus: 7 weekday files, 100 employees x 1000 weeks.

Per-employee baselines, noisy benign days and gradual, partial drift keep
the classes from being perfectly separable."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

outDir = Path(__file__).resolve().parents[1] / "data" / "generated" / "dailyLogs"

nEmpl = 100
nWeeks = 1000
malFrac = 0.10
SEED = 42

DEPARTMENTS = ["engineering", "finance", "hr", "sales", "it"]
ROLES = ["staff", "manager", "admin", "contractor"]
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

rampWeeks = 6

busyDayProb = 0.05
lateNightProb = 0.03

driftFeat = ["login", "device", "print", "file", "failed", "transfer", "session"]
nDriftFeat = (3, 5)
sevRange = (0.5, 1.2)


def generate() -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(SEED)

    empIds = [f"EMP{i:04d}" for i in range(nEmpl)]
    departments = rng.choice(DEPARTMENTS, size=nEmpl)
    roles = rng.choice(ROLES, size=nEmpl)

    habit = {
        name: rng.lognormal(0.0, sigma, nEmpl)
        for name, sigma in [
            ("device", 0.45), ("print", 0.45), ("email", 0.35), ("file", 0.4),
            ("http", 0.3), ("failed", 0.6), ("transfer", 0.45), ("session", 0.25),
        ]
    }
    loginMean = rng.normal(9.0, 1.0, nEmpl)
    loginSd = rng.uniform(1.0, 2.0, nEmpl)

    nMal = max(1, int(nEmpl * malFrac))
    malicious = rng.choice(nEmpl, size=nMal, replace=False)
    onset = np.full(nEmpl, -1)
    onset[malicious] = rng.integers(nWeeks // 2, nWeeks - 4, size=nMal)
    severity = np.zeros(nEmpl)
    severity[malicious] = rng.uniform(*sevRange, size=nMal)
    changes = np.zeros((nEmpl, len(driftFeat)), dtype=bool)
    for emp in malicious:
        k = rng.integers(nDriftFeat[0], nDriftFeat[1] + 1)
        changes[emp, rng.choice(len(driftFeat), size=k, replace=False)] = True

    def effect(name: str, amount: np.ndarray) -> np.ndarray:
        """Drift amount for employees whose drift includes `name`."""
        return np.where(changes[:, driftFeat.index(name)], amount, 0.0)

    startDate = pd.Timestamp("2024-01-01")
    frames: dict[str, list[pd.DataFrame]] = {d: [] for d in WEEKDAYS}

    for week in range(nWeeks):
        weekStart = startDate + pd.Timedelta(weeks=week)
        drifted = (onset >= 0) & (week >= onset)
        ramp = np.where(drifted, np.minimum(1.0, (week - onset + 1) / rampWeeks), 0.0)
        amount = severity * ramp

        for dayIdx, dayName in enumerate(WEEKDAYS):
            date = weekStart + pd.Timedelta(days=dayIdx)
            isWeekend = dayIdx >= 5
            damp = 0.15 if isWeekend else 1.0
            n = nEmpl

            busy = rng.random(n) < busyDayProb
            busyFactor = np.where(busy, rng.uniform(1.5, 3.0, n), 1.0)
            late = rng.random(n) < lateNightProb

            login = rng.normal(loginMean + 4.0 * effect("login", amount), loginSd)
            login = np.where(late, rng.normal(21.0, 2.0, n), login)
            login = np.clip(login, 0, 23)
            offHours = ((login < 7) | (login > 19)).astype(int)

            def count(base: float, name: str, drift: str | None = None) -> np.ndarray:
                lift = 1.0 + (1.5 * effect(drift, amount) if drift else 0.0)
                return rng.poisson(base * habit[name] * lift * busyFactor * damp)

            device = count(1.2, "device", "device")
            printed = count(1.0, "print", "print")
            email = count(3.0, "email")
            files = count(4.0, "file", "file")
            http = count(7.0, "http")

            sessionMean = 45 * habit["session"] * (1 + 0.8 * effect("session", amount))
            session = np.maximum(
                rng.normal(sessionMean * (0.5 if isWeekend else 1.0), 15), 0.0
            )
            failed = rng.poisson(0.3 * habit["failed"] + 1.0 * effect("failed", amount))

            transferMean = 60 * habit["transfer"] * (1 + 2.0 * effect("transfer", amount))
            transfer = np.maximum(rng.normal(transferMean * busyFactor, 0.35 * transferMean), 0.0)

            frames[dayName].append(
                pd.DataFrame(
                    {
                        "employee_id": empIds,
                        "date": date.date().isoformat(),
                        "weekNumber": week,
                        "dayOfWeek": dayName,
                        "department": departments,
                        "role": roles,
                        "loginHour": login.round(2),
                        "offHours": offHours,
                        "weekend": int(isWeekend),
                        "deviceActivityCount": device,
                        "printActivityCount": printed,
                        "emailActivityCount": email,
                        "fileActivityCount": files,
                        "httpActivityCount": http,
                        "failedLoginCount": failed,
                        "dataTransfMb": transfer.round(2),
                        "sessionDurationMinutes": session.round(2),
                        "label": drifted.astype(int),
                    }
                )
            )

    return {day: pd.concat(parts, ignore_index=True) for day, parts in frames.items()}


def main():
    outDir.mkdir(parents=True, exist_ok=True)
    frames = generate()
    total = 0
    for day, df in frames.items():
        outPath = outDir / f"{day}.csv"
        df.to_csv(outPath, index=False)
        total += len(df)
        print(f"{outPath}: {len(df):,} rows")
    print(f"Total records across all 7 files: {total:,}")


if __name__ == "__main__":
    main()
