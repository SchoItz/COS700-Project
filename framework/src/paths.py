"""All filesystem paths."""
from __future__ import annotations

from pathlib import Path

projectRoot = Path(__file__).resolve().parents[1]

dataDir = projectRoot / "data"
rawDir = dataDir / "raw"
genDir = dataDir / "generated"
monthLogsDir = genDir / "monthLogs"
dailyLogsDir = genDir / "dailyLogs"
twoWeekLogsDir = genDir / "twoWeekLogs"
rawInsiderThreatFile = rawDir / "insider_threat_dataset.csv"

resDir = dataDir / "processed"

runsDir = resDir / "runs"
quickResultsDir = resDir / "quick"

paperDir = projectRoot.parent / "Paper"
tablesDir = paperDir / "tables"
figDir = paperDir / "figures"
