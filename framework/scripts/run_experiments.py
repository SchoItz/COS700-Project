"""Runs the paper's experiments and renders their tables.

    python scripts/run_experiments.py              # everything (~1 hour)
    python scripts/run_experiments.py --list       # experiment ids
    python scripts/run_experiments.py --only E1,E4 # a subset
    python scripts/run_experiments.py --quick      # 3 folds, no deep models, no tables"""
from __future__ import annotations

import argparse
import sys
import time
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from paper import EXPERIMENTS, Protocol, writeTables
from paths import quickResultsDir, tablesDir


def _banner(title: str):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78, flush=True)


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--only", help="Comma-separated experiment ids, e.g. E1,E4")
    parser.add_argument("--list", action="store_true", help="List the experiments and exit")
    parser.add_argument(
        "--quick", action="store_true",
        help="3 folds, no deep models, written to data/processed/quick/ -- a wiring check",
    )
    args = parser.parse_args()

    if args.list:
        for e in EXPERIMENTS.values():
            print(f"  {e.id:4s} {e.dataset:20s} {e.question}")
        return

    selected = [k.strip().upper() for k in args.only.split(",")] if args.only else list(EXPERIMENTS)
    unknown = [k for k in selected if k not in EXPERIMENTS]
    if unknown:
        parser.error(f"Unknown experiment id(s): {', '.join(unknown)}")

    protocol = Protocol.quick(quickResultsDir) if args.quick else Protocol.paper()
    protocol.resDir.mkdir(parents=True, exist_ok=True)

    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", category=UserWarning)

    timings = {}
    for key in selected:
        experiment = EXPERIMENTS[key]
        _banner(f"{key}  {experiment.dataset}: {experiment.question}")
        start = time.time()
        experiment.run(protocol)
        if not args.quick:
            written, _ = writeTables(experiment.tables)
            print(f"  tables -> {', '.join(written) or 'none'}")
        timings[key] = time.time() - start
        print(f"\n[{key}] done in {timings[key]:.0f}s", flush=True)

    _banner("Summary")
    for key, elapsed in timings.items():
        print(f"  {key:4s} {EXPERIMENTS[key].question[:60]:60s} {elapsed:7.0f}s")
    print(f"\n  results -> {protocol.resDir}")
    print(f"  tables  -> {'(not written in --quick mode)' if args.quick else tablesDir}")
    print(f"  total   -> {sum(timings.values()):.0f}s")


if __name__ == "__main__":
    main()
