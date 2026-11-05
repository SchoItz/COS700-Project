"""Table model built from results frames. `tex` holds LaTeX-specific markup."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

import pandas as pd

from .labels import (
    metricLbs,
    featureLabel,
    formatValue,
    label,
    signed,
)


@dataclass
class Cell:
    text: str
    tex: str | None = None
    bold: bool = False


@dataclass
class Header:
    text: str
    span: int = 1
    tex: str | None = None


@dataclass
class Row:
    label: Cell
    cells: list[Cell]
    key: str | None = None
    values: dict[str, float] = field(default_factory=dict)


@dataclass
class Section:
    rows: list[Row]
    title: str | None = None
    ruleAfterTitle: bool = False


@dataclass
class Table:
    name: str
    caption: str
    texLabel: str
    align: str
    header: list[list[Header]]
    sections: list[Section]
    colsep: str | None = None

    @property
    def width(self) -> int:
        return len(self.align)

    def to_dict(self) -> dict:
        return asdict(self)


def _cell(value, column: str) -> Cell:
    text = formatValue(value, column)
    return Cell(text, tex=text.replace("_", r"\_").replace("&", r"\&").replace("%", r"\%"))


def _values(row, columns) -> dict[str, float]:
    return {
        c: (None if pd.isna(getattr(row, c)) else float(getattr(row, c)))
        for c in columns
        if hasattr(row, c)
    }


def resultsTable(
    summary: pd.DataFrame,
    caption: str,
    texLabel: str,
    name: str = "",
    metrics: list[str] | None = None,
    groupCol: str | None = "family",
    highlightBest: str = "f1",
) -> Table:
    """Per-strategy results, best `highlightBest` in bold."""
    metrics = [m for m in (metrics or list(metricLbs)) if m in summary.columns]
    frame = summary.reset_index()
    bestVal = frame[highlightBest].max() if highlightBest in frame else None

    groups = (
        [(None, frame)]
        if groupCol is None or groupCol not in frame.columns
        else [(g, frame[frame[groupCol] == g]) for g in ("individual", "combined")]
    )

    sections = []
    for groupName, group in groups:
        if group.empty:
            continue
        rows = []
        for row in group.itertuples():
            cells = []
            for metric in metrics:
                cell = _cell(getattr(row, metric), metric)
                if metric == highlightBest and bestVal is not None:
                    cell.bold = bool(abs(getattr(row, metric) - bestVal) < 1e-12)
                cells.append(cell)
            rows.append(
                Row(Cell(label(row.strategy)), cells, key=row.strategy, values=_values(row, metrics))
            )
        title = f"{groupName.title()} strategies" if groupName is not None else None
        sections.append(Section(rows, title))

    return Table(
        name, caption, texLabel,
        align="l" + "r" * len(metrics),
        header=[[Header("Strategy")] + [Header(metricLbs.get(m, m)) for m in metrics]],
        sections=sections,
    )


def variantTable(
    combined: pd.DataFrame,
    caption: str,
    texLabel: str,
    varColumn: str,
    name: str = "",
    metric: str = "f1",
    extraMetric: str | None = "falsePositiveRate",
) -> Table:
    """One row per strategy, one column pair per variant, plus a mean row."""
    from models.registry import strategyOrder

    variants = list(combined[varColumn].unique())
    pivot = combined.pivot_table(
        index="strategy", columns=varColumn, values=metric, aggfunc="mean"
    )[variants]
    pivot = pivot.reindex(strategyOrder(pivot.index))
    extra = None
    if extraMetric and extraMetric in combined.columns:
        extra = combined.pivot_table(
            index="strategy", columns=varColumn, values=extraMetric, aggfunc="mean"
        )[variants].reindex(pivot.index)

    measures = [metric] + ([extraMetric] if extra is not None else [])
    frames = {metric: pivot, **({extraMetric: extra} if extra is not None else {})}

    def cellsFor(get) -> tuple[list[Cell], dict[str, float]]:
        cells, values = [], {}
        for variant in variants:
            for measure in measures:
                value = get(frames[measure], variant)
                cells.append(_cell(value, measure))
                values[f"{variant}.{measure}"] = None if pd.isna(value) else float(value)
        return cells, values

    rows = []
    for strategy in pivot.index:
        cells, values = cellsFor(lambda frame, v, s=strategy: frame.loc[s, v])
        rows.append(Row(Cell(label(strategy)), cells, key=strategy, values=values))
    meanCells, meanValues = cellsFor(lambda frame, v: frame[v].mean())

    return Table(
        name, caption, texLabel,
        align="l" + "r" * len(measures) * len(variants),
        header=[
            [Header("Strategy")] + [Header(label(v), span=len(measures)) for v in variants],
            [Header("")] + [Header(metricLbs.get(m, m)) for _ in variants for m in measures],
        ],
        sections=[
            Section(rows),
            Section([Row(Cell("Mean"), meanCells, key="mean", values=meanValues)]),
        ],
    )


def significanceTable(
    table: pd.DataFrame,
    caption: str,
    texLabel: str,
    name: str = "",
    metric: str = "f1",
    bestStrat: str | None = None,
    bestMean: float | None = None,
) -> Table:
    """Every strategy against the best one."""
    best = bestStrat if bestStrat is not None else table.attrs.get("bestStrat", "")
    bestMean = bestMean if bestMean is not None else table.attrs.get("bestMean", float("nan"))
    dash = Cell("n/a")

    bestRow = Row(
        Cell(f"{label(best)} (best)"),
        [Cell(f"{bestMean:.3f}"), dash, dash, dash],
        key=best,
        values={"mean": float(bestMean)},
    )
    rows = [
        Row(
            Cell(label(row.strategy)),
            [
                Cell(f"{row.mean:.3f}"),
                Cell(signed(-row.meanDiffVsBest)),
                Cell(f"{row.pValue:.4f}"),
                Cell("yes" if row.significant else "no"),
            ],
            key=row.strategy,
            values={
                "mean": float(row.mean),
                "deltaVsBest": float(-row.meanDiffVsBest),
                "pValue": float(row.pValue),
                "significant": float(bool(row.significant)),
            },
        )
        for row in table.itertuples()
    ]
    return Table(
        name, caption, texLabel,
        align="lrrrc",
        header=[[
            Header("Strategy"),
            Header(metricLbs.get(metric, metric)),
            Header("Δ vs. best", tex=r"$\Delta$ vs.\ best"),
            Header("p", tex="$p$"),
            Header("Sig."),
        ]],
        sections=[Section([bestRow]), Section(rows)],
    )


def importanceTable(
    importance: pd.DataFrame,
    byKind: pd.DataFrame,
    caption: str,
    texLabel: str,
    name: str = "",
    topN: int = 12,
) -> Table:
    """Top-N features, then totals per kind."""
    top = [
        Row(
            Cell(
                featureLabel(row.feature),
                tex=featureLabel(row.feature).replace("vs. ", r"vs.\ "),
            ),
            [Cell(f"{row.importance:.4f}"), Cell(f"{row.importanceStd:.4f}")],
            key=row.feature,
            values={"importance": float(row.importance), "sd": float(row.importanceStd)},
        )
        for row in importance.head(topN).itertuples()
    ]
    kinds = [
        Row(
            Cell(f"{row.kind.capitalize()} ({row.n_features} feature{'' if row.n_features == 1 else 's'})"),
            [
                Cell(f"{row.total:.4f}"),
                Cell(f"{row.share * 100:.1f}%", tex=f"{row.share * 100:.1f}\\%"),
            ],
            key=row.kind,
            values={"total": float(row.total), "share": float(row.share)},
        )
        for row in byKind.itertuples()
    ]
    return Table(
        name, caption, texLabel,
        align="lrr",
        header=[[Header("Signal"), Header("Importance"), Header("SD")]],
        sections=[
            Section(top),
            Section(kinds, title="Total importance by kind of signal", ruleAfterTitle=True),
        ],
    )


def _originLabel(row) -> str:
    """e.g. "Synthetic (third party)"."""
    generator = getattr(row, "generator", "")
    if not isinstance(generator, str) or not generator:
        return row.origin
    return f"{row.origin} ({generator.lower()})"


def datasetsTable(summary: pd.DataFrame, caption: str, texLabel: str, name: str = "") -> Table:
    """Size and class balance of each dataset."""

    def count(n: int) -> Cell:
        return Cell(f"{n:,}", tex=f"{n:,}".replace(",", "{,}"))

    rows = [
        Row(
            Cell(row.title),
            [
                count(int(row.rows)),
                count(int(row.employees)),
                count(int(row.positiveRows)),
                Cell(f"{row.positiveRate * 100:.3f}%", tex=f"{row.positiveRate * 100:.3f}\\%"),
                Cell(_originLabel(row)),
            ],
            key=row.dataset,
            values={
                "rows": float(row.rows),
                "employees": float(row.employees),
                "positiveRows": float(row.positiveRows),
                "positiveRate": float(row.positiveRate),
            },
        )
        for row in summary.itertuples()
    ]
    return Table(
        name, caption, texLabel,
        align="lrrrrl",
        header=[[
            Header(h)
            for h in ("Dataset", "Rows", "Staff", "Pos. rows", "Pos. rate", "Origin")
        ]],
        sections=[Section(rows)],
        colsep="3pt",
    )
