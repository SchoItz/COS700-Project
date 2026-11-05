"""Renders the report's figures from `data/processed/*.csv`.

    python scripts/make_figures.py"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from models.registry import strategyOrder
from paths import figDir, resDir
from reporting import label

SURFACE = "#fcfcfb"
textPrimary = "#0b0b0b"
textSecondary = "#52514e"
GRID = "#dedcd5"
SERIES = {"a": "#2a78d6", "b": "#eb6834"}

barHeight = 0.38
GAP = 0.02


def _style(ax):
    ax.set_facecolor(SURFACE)
    ax.figure.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=textSecondary, length=0)
    ax.xaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def groupedBars(
    frame: pd.DataFrame,
    varColumn: str,
    variants: tuple[str, str],
    metric: str,
    title: str,
    outName: str,
):
    pivot = frame.pivot_table(
        index="strategy", columns=varColumn, values=metric, aggfunc="mean"
    )
    missing = [v for v in variants if v not in pivot.columns]
    if missing:
        raise SystemExit(f"{outName}: missing variant(s) {missing} in {varColumn}")

    pivot = pivot.loc[strategyOrder(pivot.index)]
    pivot = pivot.sort_values(variants[1])
    positions = range(len(pivot))

    fig, ax = plt.subplots(figsize=(7.2, 0.42 * len(pivot) + 1.4))
    _style(ax)

    for offset, (variant, colour) in zip(
        (-(barHeight + GAP) / 2, (barHeight + GAP) / 2),
        ((variants[0], SERIES["a"]), (variants[1], SERIES["b"])),
    ):
        ax.barh(
            [p + offset for p in positions],
            pivot[variant],
            height=barHeight,
            color=colour,
            label=label(variant),
            zorder=3,
        )

    ax.set_yticks(list(positions))
    ax.set_yticklabels([label(s) for s in pivot.index], color=textPrimary)
    ax.set_xlim(0, 1)
    ax.set_xlabel(metric.upper().replace("_", " "), color=textSecondary)
    ax.set_title(title, color=textPrimary, loc="left", pad=12)
    legend = ax.legend(loc="lower right", frameon=False)
    for text in legend.get_texts():
        text.set_color(textPrimary)

    figDir.mkdir(parents=True, exist_ok=True)
    out = figDir / f"{outName}.png"
    fig.tight_layout()
    fig.savefig(out, dpi=200, facecolor=SURFACE)
    plt.close(fig)
    print(f"  wrote {out}")
    return out


FIGURES = [
    (
        "resultsLayerMonth.csv", "variant",
        ("singleDaySnapshot", "multiDayTemporal"), "f1",
        "Multi-day history vs single-day snapshot (30-day logs)",
        "layerMonth",
    ),
    (
        "resultsLayerKaggle.csv", "variant",
        ("singleDaySnapshot", "multiDayTemporal"), "f1",
        "Multi-day history vs single-day snapshot (Kaggle dataset)",
        "layerKaggle",
    ),
]


def main():
    print(f"Reading results from {resDir}")
    written = 0
    for filename, column, variants, metric, title, outName in FIGURES:
        path = resDir / filename
        if not path.exists():
            print(f"  skipping {outName}: {path.name} not found -- run run_experiments.py first")
            continue
        groupedBars(pd.read_csv(path), column, variants, metric, title, outName)
        written += 1
    print(f"\n{written} figure(s) -> {figDir}")


if __name__ == "__main__":
    main()
