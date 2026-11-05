"""Generates the 30-day dataset: 100 employees, 20 insiders across 5 archetypes.

A gradual escalation, B sudden spike, C off-hours only, D weekend work,
E subtle exfiltration. Five benign employees are deliberately noisy."""
from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

outDir = Path(__file__).resolve().parents[1] / "data" / "generated" / "monthLogs"
outDir.mkdir(parents=True, exist_ok=True)

RNG = random.Random(42)

DEPARTMENTS = ["engineering", "finance", "hr", "sales", "it"]
ROLES = ["staff", "manager", "admin", "contractor"]

roleBase = {
    "staff":      dict(loginHour=8.75, device=1, print=1, email=3, file=4, http=6, failed=0, transfer=35.0, session=45.0),
    "manager":    dict(loginHour=8.5,  device=1, print=1, email=5, file=5, http=5, failed=0, transfer=55.0, session=60.0),
    "admin":      dict(loginHour=8.0,  device=2, print=1, email=3, file=8, http=4, failed=0, transfer=70.0, session=55.0),
    "contractor": dict(loginHour=9.5,  device=1, print=0, email=2, file=3, http=5, failed=0, transfer=22.0, session=40.0),
}

employees = []
comboIdx = 0
for _ in range(5):
    for dept in DEPARTMENTS:
        for role in ROLES:
            employees.append({"id": f"EMP{comboIdx:04d}", "department": dept, "role": role, "comboIdx": comboIdx})
            comboIdx += 1
byId = {e["id"]: e for e in employees}


def personality(emp):
    i = emp["comboIdx"]
    return {
        "loginShift": ((i % 5) - 2) * 0.15,
        "printBonus": 1 if i % 7 == 0 else 0,
        "emailBonus": 1 if i % 6 == 0 else 0,
        "httpBonus": 1 if i % 4 == 0 else 0,
    }


ARCHETYPES = {
    "gradEscalation": ["EMP0003", "EMP0019", "EMP0044", "EMP0067"],
    "suddenSpike": ["EMP0008", "EMP0026", "EMP0052", "EMP0079"],
    "offHoursOnly": ["EMP0011", "EMP0033", "EMP0058", "EMP0084"],
    "weekendInfiltrator": ["EMP0015", "EMP0037", "EMP0061", "EMP0088"],
    "subtleExfiltration": ["EMP0021", "EMP0045", "EMP0070", "EMP0093"],
}
threatTypes = {empId: archetype for archetype, ids in ARCHETYPES.items() for empId in ids}
assert len(threatTypes) == 20
assert set(threatTypes).issubset(byId)

noisyNorm = {"EMP0005", "EMP0030", "EMP0055", "EMP0072", "EMP0095"}
assert noisyNorm.isdisjoint(threatTypes)
assert noisyNorm.issubset(byId)

START = date(2026, 8, 3)
nDays = 30
DAYS = [START + timedelta(days=i) for i in range(nDays)]
dayNames = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

FIELDS = [
    "employee_id", "date", "dayOfWeek", "weekNumber", "department", "role",
    "loginHour", "offHours", "weekend",
    "deviceActivityCount", "printActivityCount", "emailActivityCount",
    "fileActivityCount", "httpActivityCount", "failedLoginCount",
    "dataTransfMb", "sessionDurationMinutes", "threatType", "label",
]


def jitterCount(base, spread=0.3):
    """Non-negative integer jitter around a baseline."""
    return max(0, round(base + RNG.gauss(0, max(base, 0.5) * spread)))


def jitterFloat(base, spread=0.18):
    return max(0.0, round(base + RNG.gauss(0, base * spread), 2))


def jitterHour(base, sd=0.35):
    return round(min(max(base + RNG.gauss(0, sd), 0.0), 23.9), 2)


def baseRow(emp, d, dayIdx, noisy=False, **overrides):
    role = emp["role"]
    base = roleBase[role]
    p = personality(emp)
    mult = 1.8 if noisy else 1.0

    loginHour = jitterHour(base["loginHour"] + p["loginShift"], sd=0.35 * mult)
    offHours = 0
    if noisy and RNG.random() < 0.08:
        loginHour = jitterHour(21.5, sd=1.2)
        offHours = int(loginHour < 7 or loginHour > 19)

    row = {
        "employee_id": emp["id"], "date": d.isoformat(),
        "dayOfWeek": dayNames[dayIdx % 7], "weekNumber": dayIdx // 7,
        "department": emp["department"], "role": role,
        "loginHour": loginHour,
        "offHours": offHours, "weekend": 0,
        "deviceActivityCount": jitterCount(base["device"], 0.35 * mult),
        "printActivityCount": jitterCount(base["print"] + p["printBonus"], 0.4 * mult),
        "emailActivityCount": jitterCount(base["email"] + p["emailBonus"], 0.3 * mult),
        "fileActivityCount": jitterCount(base["file"], 0.3 * mult),
        "httpActivityCount": jitterCount(base["http"] + p["httpBonus"], 0.3 * mult),
        "failedLoginCount": 1 if RNG.random() < (0.04 if noisy else 0.015) else 0,
        "dataTransfMb": jitterFloat(base["transfer"], 0.22 * mult),
        "sessionDurationMinutes": jitterFloat(base["session"], 0.2 * mult),
        "threatType": "",
        "label": 0,
    }
    row.update(overrides)
    return row


def weekendRow(emp, d, dayIdx, checksIn=False, **overrides):
    role = emp["role"]
    base = roleBase[role]
    p = personality(emp)
    if not checksIn:
        row = {
            "employee_id": emp["id"], "date": d.isoformat(),
            "dayOfWeek": dayNames[dayIdx % 7], "weekNumber": dayIdx // 7,
            "department": emp["department"], "role": role,
            "loginHour": "", "offHours": 0, "weekend": 1,
            "deviceActivityCount": 0, "printActivityCount": 0,
            "emailActivityCount": 0, "fileActivityCount": 0,
            "httpActivityCount": 0, "failedLoginCount": 0,
            "dataTransfMb": 0.0, "sessionDurationMinutes": 0.0,
            "threatType": "", "label": 0,
        }
    else:
        row = {
            "employee_id": emp["id"], "date": d.isoformat(),
            "dayOfWeek": dayNames[dayIdx % 7], "weekNumber": dayIdx // 7,
            "department": emp["department"], "role": role,
            "loginHour": jitterHour(base["loginHour"] + p["loginShift"] + 2.0, sd=0.5),
            "offHours": 0, "weekend": 1,
            "deviceActivityCount": jitterCount(0.3, 1.0),
            "printActivityCount": 0,
            "emailActivityCount": jitterCount(1, 0.5),
            "fileActivityCount": jitterCount(0.2, 1.0),
            "httpActivityCount": jitterCount(1, 0.5),
            "failedLoginCount": 0,
            "dataTransfMb": jitterFloat(2.0, 0.4),
            "sessionDurationMinutes": jitterFloat(12.0, 0.4),
            "threatType": "", "label": 0,
        }
    row.update(overrides)
    return row


def rowFor(emp, d, dayIdx):
    isWeekend = dayIdx % 7 >= 5
    threatType = threatTypes.get(emp["id"])
    role = emp["role"]
    noisy = emp["id"] in noisyNorm

    if threatType is None:
        if isWeekend:
            checksIn = role in ("manager", "admin") and (emp["comboIdx"] % 3 == 0)
            return weekendRow(emp, d, dayIdx, checksIn=checksIn)
        return baseRow(emp, d, dayIdx, noisy=noisy)

    if threatType == "gradEscalation":
        if dayIdx < 14 or isWeekend:
            return weekendRow(emp, d, dayIdx, checksIn=False) if isWeekend else baseRow(emp, d, dayIdx)
        if dayIdx < 21:
            severity = 0.3 + (dayIdx - 14) * (0.7 / 6)
        else:
            severity = 1.0 + (dayIdx - 21) * (1.5 / 8)
        base = roleBase[role]
        return baseRow(
            emp, d, dayIdx,
            loginHour=jitterHour(21.0 + 1.5 * min(severity, 1.0), sd=0.4), offHours=1,
            deviceActivityCount=jitterCount(base["device"] * (1 + severity), 0.25),
            printActivityCount=jitterCount(base["print"] * (1 + severity) or severity, 0.25),
            fileActivityCount=jitterCount(base["file"] * (1 + severity), 0.25),
            failedLoginCount=round(1 + severity),
            dataTransfMb=jitterFloat(base["transfer"] * (1 + severity), 0.2),
            sessionDurationMinutes=jitterFloat(base["session"] * (1 + 0.4 * severity), 0.2),
            threatType=threatType, label=1,
        )

    if threatType == "suddenSpike":
        burstDays = {16, 17, 18}
        if dayIdx not in burstDays or isWeekend:
            return weekendRow(emp, d, dayIdx, checksIn=False) if isWeekend else baseRow(emp, d, dayIdx)
        base = roleBase[role]
        return baseRow(
            emp, d, dayIdx,
            loginHour=jitterHour(23.5, sd=0.3), offHours=1,
            deviceActivityCount=jitterCount(base["device"] * 8, 0.2),
            printActivityCount=jitterCount(base["print"] * 8 or 6, 0.2),
            fileActivityCount=jitterCount(base["file"] * 6, 0.2),
            failedLoginCount=6,
            dataTransfMb=jitterFloat(base["transfer"] * 7, 0.2),
            sessionDurationMinutes=jitterFloat(base["session"] * 2.2, 0.2),
            threatType=threatType, label=1,
        )

    if threatType == "offHoursOnly":
        if dayIdx < 14 or isWeekend:
            return weekendRow(emp, d, dayIdx, checksIn=False) if isWeekend else baseRow(emp, d, dayIdx)
        return baseRow(
            emp, d, dayIdx,
            loginHour=jitterHour(23.0 if dayIdx % 2 == 0 else 0.5, sd=0.5), offHours=1,
            threatType=threatType, label=1,
        )

    if threatType == "weekendInfiltrator":
        if not isWeekend or dayIdx < 19:
            return weekendRow(emp, d, dayIdx, checksIn=False) if isWeekend else baseRow(emp, d, dayIdx)
        base = roleBase[role]
        return baseRow(
            emp, d, dayIdx,
            loginHour=jitterHour(base["loginHour"] + 1.0, sd=0.4), offHours=0, weekend=1,
            deviceActivityCount=jitterCount(base["device"] * 5, 0.2),
            printActivityCount=jitterCount(base["print"] * 4 or 3, 0.2),
            fileActivityCount=jitterCount(base["file"] * 6, 0.2),
            failedLoginCount=2,
            dataTransfMb=jitterFloat(base["transfer"] * 4, 0.2),
            sessionDurationMinutes=jitterFloat(base["session"] * 1.6, 0.2),
            threatType=threatType, label=1,
        )

    if threatType == "subtleExfiltration":
        if dayIdx < 14 or isWeekend:
            return weekendRow(emp, d, dayIdx, checksIn=False) if isWeekend else baseRow(emp, d, dayIdx)
        base = roleBase[role]
        return baseRow(
            emp, d, dayIdx,
            dataTransfMb=jitterFloat(base["transfer"] * 1.5, 0.15),
            threatType=threatType, label=1,
        )

    raise AssertionError(f"unhandled archetype {threatType}")


rowsByDay = {i: [] for i in range(nDays)}
for emp in employees:
    for dayIdx, d in enumerate(DAYS):
        rowsByDay[dayIdx].append(rowFor(emp, d, dayIdx))

total = 0
labelTotal = 0
for dayIdx, d in enumerate(DAYS):
    fname = f"{d.isoformat()}_{dayNames[dayIdx % 7]}.csv"
    with open(outDir / fname, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rowsByDay[dayIdx])
    total += len(rowsByDay[dayIdx])
    labelTotal += sum(r["label"] for r in rowsByDay[dayIdx])

print(f"Wrote {nDays} files, {total} total rows, {labelTotal} labelled anomalous rows.")
print("Archetypes:")
for name, ids in ARCHETYPES.items():
    print(f"  {name}: {ids}")
print(f"Noisy-normal hard negatives: {sorted(noisyNorm)}")
