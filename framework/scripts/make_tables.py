"""Rebuilds the LaTeX tables from `data/processed/` without re-running experiments.

    python scripts/make_tables.py"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from paper import writeTables
from paths import resDir, tablesDir


def main():
    print(f"Reading results from {resDir}")
    written, skipped = writeTables()
    for name in written:
        print(f"  wrote {name}.tex")
    if skipped:
        print(f"\n  skipped (no result file yet): {', '.join(skipped)}")
    print(f"\n{len(written)} table(s) -> {tablesDir}")


if __name__ == "__main__":
    main()
