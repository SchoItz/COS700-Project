"""The report's experiments and tables. Tables are always built from the CSVs on disk."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

import settings
from paths import resDir, tablesDir
from reporting import (
    Table,
    datasetsTable,
    importanceTable,
    resultsTable,
    significanceTable,
    variantTable,
    writeTex,
)


@dataclass(frozen=True)
class Protocol:
    """Run settings: `paper()` for the report, `quick()` for a fast check."""

    nSplits: int = settings.nSplits
    includeDeep: bool = True
    resDir: Path = resDir

    @classmethod
    def paper(cls) -> Protocol:
        return cls()

    @classmethod
    def quick(cls, resDir: Path) -> Protocol:
        return cls(nSplits=3, includeDeep=False, resDir=resDir)

    def csv(self, name: str) -> Path:
        return self.resDir / f"{name}.csv"


def _join(*parts: str) -> str:
    return parts[0] + "".join(s[:1].upper() + s[1:] for s in parts[1:])


def _datasets(p: Protocol):
    from data.registry import DATASETS, describe

    rows = [
        {"dataset": info.name, "title": info.title, "origin": info.origin,
         "generator": info.generator,
         **describe(info.load())}
        for info in DATASETS.values()
        if info.inPaper
    ]
    p.csv("datasets").parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(p.csv("datasets"), index=False)


def _crossValidated(dataset: str, stem: str, alerts: bool, sample: dict | None = None):
    def runExperiment(p: Protocol):
        from pipeline.experiments import run
        from pipeline.experiments import significanceTable as significance

        _, perFold = run(
            dataset, nSplits=p.nSplits, includeDeep=p.includeDeep,
            outPath=p.csv(_join("results", stem)),
            alertsPath=p.csv(_join("alerts", stem)) if alerts else None,
            retFolds=True, sample=sample,
        )
        significance(perFold, outPath=p.csv(_join("significance", stem)))

    return runExperiment


def _ablation(dataset: str, stem: str, sample: dict | None = None):
    def runExperiment(p: Protocol):
        from pipeline.experiments import runTemporalLayer

        runTemporalLayer(
            dataset, nSplits=p.nSplits, includeDeep=settings.layerIncludeDeep,
            outPath=p.csv(_join("resultsLayer", stem)), **(sample or {}),
        )

    return runExperiment


def _generalise(train: str):
    def runExperiment(p: Protocol):
        from pipeline.experiments import runFinalTest

        runFinalTest(
            train, "rawInsiderThreat", includeDeep=p.includeDeep,
            outPath=p.csv(_join("resultsGeneralise", train)),
        )

    return runExperiment


def _trust(p: Protocol):
    from pipeline.experiments import runTrustComparison

    runTrustComparison(
        "month", nSplits=p.nSplits, includeDeep=p.includeDeep,
        outPath=p.csv("resultsTrustDesigns"),
    )


def _imbalance(p: Protocol):
    from pipeline.experiments import runImbalanceComparison

    runImbalanceComparison(
        "month", nSplits=p.nSplits, includeDeep=p.includeDeep,
        outPath=p.csv("resultsImbalance"),
    )


def _signals(p: Protocol):
    from pipeline.experiments import runSignalImportance

    runSignalImportance(
        "month", strategy="randomForest",
        outPath=p.csv("signalImportance"),
        byKindPath=p.csv("signalImportanceByKind"),
    )


@dataclass(frozen=True)
class Experiment:
    id: str
    dataset: str
    question: str
    run: Callable[[Protocol], None]
    tables: tuple[str, ...] = field(default_factory=tuple)


EXPERIMENTS: dict[str, Experiment] = {
    e.id: e
    for e in (
        Experiment("DS", "All", "Size and class balance of each dataset.",
                   _datasets, ("datasets",)),
        Experiment("E1", "30-day", "How do the fifteen strategies compare under cross-validation?",
                   _crossValidated("month", "month", alerts=True),
                   ("resultsMonth", "significanceMonth")),
        Experiment("E2", "Single-day", "The same comparison on single-day employee records.",
                   _crossValidated("singleDay", "singleDay", alerts=True),
                   ("resultsSingleDay", "significanceSingleDay")),
        Experiment("E3", "Kaggle", "The same comparison on the third-party Kaggle data.",
                   _crossValidated("rawInsiderThreat", "kaggle", alerts=False,
                                    sample=settings.kaggleSample),
                   ("resultsKaggle", "significanceKaggle")),
        Experiment("E4", "30-day", "Does multi-day history beat a single-day snapshot?",
                   _ablation("month", "month"), ("layerMonth",)),
        Experiment("E5", "Kaggle", "The same ablation on the third-party Kaggle data.",
                   _ablation("rawInsiderThreat", "kaggle", sample=settings.kaggleSample),
                   ("layerKaggle",)),
        Experiment("E6", "30-day → Kaggle", "Do the strategies generalise to a dataset never seen?",
                   _generalise("month"), ("generalMonth",)),
        Experiment("E7", "Single-day → Kaggle",
                   "The same generalisation test from single-day data.",
                   _generalise("singleDay"), ("generalSingleDay",)),
        Experiment("E8", "30-day",
                   "Which trust-integration design works, and does trust help at all?",
                   _trust, ("trustDesigns",)),
        Experiment("E9", "30-day",
                   "Does SMOTE or under-sampling improve on class weighting alone?",
                   _imbalance, ("imbalance",)),
        Experiment("E10", "30-day",
                   "Which behavioural signals does the detection actually rest on?",
                   _signals, ("signalImportance",)),
    )
}


@dataclass(frozen=True)
class TableSpec:
    kind: str
    sources: tuple[str, ...]
    caption: str
    texLabel: str
    varColumn: str | None = None


_kaggleEmp = sum(settings.kaggleSample.values())

TABLES: dict[str, TableSpec] = {
    "datasets": TableSpec(
        "datasets", ("datasets",),
        "Datasets. All three are synthetic.",
        "tab:datasets",
    ),
    "resultsMonth": TableSpec(
        "results", ("resultsMonth",),
        "Results on the 30-day logs. Means over ten folds; FP is per fold.",
        "tab:results-month",
    ),
    "resultsSingleDay": TableSpec(
        "results", ("resultsSingleDay",),
        "Results on the single-day logs. Means over ten folds.",
        "tab:results-single-day",
    ),
    "resultsKaggle": TableSpec(
        "results", ("resultsKaggle",),
        f"Results on the Kaggle dataset, sampled to {_kaggleEmp} employees. Means over ten folds.",
        "tab:results-kaggle",
    ),
    "generalMonth": TableSpec(
        "results", ("resultsGeneraliseMonth",),
        "Trained on the 30-day logs, tested on the full Kaggle dataset. FP is the total count.",
        "tab:generalise-month",
    ),
    "generalSingleDay": TableSpec(
        "results", ("resultsGeneraliseSingleDay",),
        "Trained on the single-day logs, tested on the full Kaggle dataset.",
        "tab:generalise-single-day",
    ),
    "significanceMonth": TableSpec(
        "significance", ("significanceMonth", "resultsMonth"),
        "Wilcoxon tests against the best strategy, 30-day logs (Holm-Bonferroni).",
        "tab:significance-month",
    ),
    "significanceSingleDay": TableSpec(
        "significance", ("significanceSingleDay", "resultsSingleDay"),
        "Wilcoxon tests against the best strategy, single-day logs (Holm-Bonferroni).",
        "tab:significance-single-day",
    ),
    "significanceKaggle": TableSpec(
        "significance", ("significanceKaggle", "resultsKaggle"),
        "Wilcoxon tests against the best strategy, Kaggle dataset (Holm-Bonferroni).",
        "tab:significance-kaggle",
    ),
    "layerMonth": TableSpec(
        "variant", ("resultsLayerMonth",),
        "Single-day vs multi-day features, 30-day logs.",
        "tab:ablation-month", varColumn="variant",
    ),
    "layerKaggle": TableSpec(
        "variant", ("resultsLayerKaggle",),
        "Single-day vs multi-day features, Kaggle dataset.",
        "tab:ablation-kaggle", varColumn="variant",
    ),
    "trustDesigns": TableSpec(
        "variant", ("resultsTrustDesigns",),
        "Trust designs against no trust.",
        "tab:trust-designs", varColumn="variant",
    ),
    "imbalance": TableSpec(
        "variant", ("resultsImbalance",),
        "Class imbalance treatments.",
        "tab:imbalance", varColumn="resampling",
    ),
    "signalImportance": TableSpec(
        "importance", ("signalImportance", "signalImportanceByKind"),
        "Permutation importance on the 30-day logs, best strategy.",
        "tab:signal-importance",
    ),
}


def buildTable(name: str, resDir: Path = resDir) -> Table | None:
    """Builds table `name` from `resDir`; None if a CSV is missing."""
    spec = TABLES[name]
    paths = [resDir / f"{source}.csv" for source in spec.sources]
    if not all(path.exists() for path in paths):
        return None
    args = (spec.caption, spec.texLabel)

    if spec.kind == "results":
        return resultsTable(pd.read_csv(paths[0], index_col=0), *args, name=name)
    if spec.kind == "variant":
        return variantTable(
            pd.read_csv(paths[0]), *args, varColumn=spec.varColumn, name=name
        )
    if spec.kind == "significance":
        summary = pd.read_csv(paths[1], index_col=0)
        return significanceTable(
            pd.read_csv(paths[0]), *args, name=name,
            bestStrat=summary["f1"].idxmax(), bestMean=float(summary["f1"].max()),
        )
    if spec.kind == "importance":
        return importanceTable(pd.read_csv(paths[0]), pd.read_csv(paths[1]), *args, name=name)
    if spec.kind == "datasets":
        return datasetsTable(pd.read_csv(paths[0]), *args, name=name)
    raise ValueError(f"Unknown table kind '{spec.kind}'")


def writeTables(
    names=None, resDir: Path = resDir, tablesDir: Path = tablesDir
) -> tuple[list[str], list[str]]:
    """Writes tables to `tablesDir`; returns (written, skipped)."""
    written, skipped = [], []
    for name in names or TABLES:
        table = buildTable(name, resDir)
        if table is None:
            skipped.append(name)
            continue
        writeTex(table, tablesDir / f"{name}.tex")
        written.append(name)
    return written, skipped
