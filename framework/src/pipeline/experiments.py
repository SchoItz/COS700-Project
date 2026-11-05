"""Experiment runners. Defaults come from `settings`; `paper` calls them for E1-E10.

    python -m pipeline.experiments --dataset month"""
from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd

from data.registry import datasetNames, loadDataset
from evaluation.alerts import generateAlerts, outOfFoldScores
from evaluation.cross_validate import (
    Resample,
    crossValidateDetector,
    summariseFolds,
)
from evaluation.importance import importanceByKind, signalImportance
from evaluation.metrics import computeMetrics
from evaluation.significance import compareAllToBest
from models.registry import FAMILY, buildStrategies, strategyOrder
from paths import runsDir
from settings import decThreshold, nSplits, SEED
from trust import alertThreshold
from .design import (
    thresholdCol,
    Design,
    TrustMode,
    applyDesignMatrix,
    designMatrix,
    featurise,
    trustColumnIndex,
)

DATASETS = datasetNames

Reporter = Callable[[str], None]

__all__ = [
    "DATASETS",
    "Design",
    "applyDesignMatrix",
    "designMatrix",
    "featurise",
    "trustColumnIndex",
    "loadData",
    "sampleByEmployee",
    "evaluateStrategies",
    "buildAlerts",
    "run",
    "runFinalTest",
    "runTemporalLayer",
    "runTrustComparison",
    "runImbalanceComparison",
    "runSignalImportance",
    "significanceTable",
]


def loadData(dataset: str, nUsers: int = 150, nDays: int = 45) -> pd.DataFrame:
    """Loads a dataset by name."""
    return loadDataset(dataset, nUsers=nUsers, nDays=nDays)


def sampleByEmployee(
    df: pd.DataFrame,
    nMalEmp: int,
    nBenignEmp: int,
    seed: int = SEED,
) -> pd.DataFrame:
    """Samples whole employees, over-sampling malicious ones."""
    malUsers = df.loc[df["label"] == 1, "userId"].unique()
    otherUsers = df.loc[~df["userId"].isin(malUsers), "userId"].unique()
    rng = np.random.default_rng(seed)
    chosen = set(
        rng.choice(
            malUsers, min(nMalEmp, len(malUsers)), replace=False
        )
    ) | set(
        rng.choice(otherUsers, min(nBenignEmp, len(otherUsers)), replace=False)
    )
    return df[df["userId"].isin(chosen)].reset_index(drop=True)


def _summaryFrame(rows: list[dict]) -> pd.DataFrame:
    summary = pd.DataFrame(rows).set_index("strategy")
    summary.insert(0, "family", [FAMILY.get(name, "unknown") for name in summary.index])
    return summary.sort_values("f1", ascending=False)


def _logLine(name: str, metrics: dict) -> str:
    return (
        f"  {name:24s} F1={metrics['f1']:.3f}  P={metrics['precision']:.3f}"
        f"  R={metrics['recall']:.3f}  FPR={metrics['falsePositiveRate']:.4f}"
        f"  PR-AUC={metrics.get('prAuc', float('nan')):.3f}"
        f"  FP={metrics['falsePositiveCount']:.0f}"
    )


def evaluateStrategies(
    design: Design,
    report: Reporter,
    nSplits: int = nSplits,
    threshold: float = decThreshold,
    resample: Resample = "none",
    includeDeep: bool = True,
    label: str = "",
    useTrustThresholds: bool = True,
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    """Cross-validates every strategy; returns (summary, perFold)."""
    X, y = design.X, design.y
    strategies = buildStrategies(
        X.shape[1], includeDeep=includeDeep, trustCol=design.trustCol
    )
    thresholds = design.thresholds if useTrustThresholds else None
    prefix = f"[{label}] " if label else ""

    rows, perFold = [], {}
    for name in strategyOrder(strategies):
        folds = crossValidateDetector(
            strategies[name], X, y, nSplits=nSplits, threshold=threshold,
            resample=resample, thresholds=thresholds,
        )
        perFold[name] = folds
        summary = summariseFolds(folds)
        summary["strategy"] = name
        rows.append(summary)
        report(prefix + _logLine(name, summary).lstrip())

    return _summaryFrame(rows), perFold


def _write(frame: pd.DataFrame, outPath: Path | None, report: Reporter, index: bool = True):
    if outPath is None:
        return
    outPath.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(outPath, index=index)
    report(f"  -> saved {outPath}")


def _reporter(progCb=None) -> Reporter:
    def report(msg: str):
        print(msg, flush=True)
        if progCb:
            progCb(msg)

    return report


def _describe(df: pd.DataFrame) -> str:
    return (
        f"{len(df):,} rows, {df['userId'].nunique():,} employees, "
        f"{int(df['label'].sum()):,} malicious rows "
        f"({df['label'].mean() * 100:.2f}% positive)"
    )


def buildAlerts(
    design: Design,
    featurised: pd.DataFrame,
    strategy: str,
    nSplits: int = nSplits,
    trustMode: TrustMode = "sensitivity",
) -> pd.DataFrame:
    """Ranked alert list for `strategy`, from out-of-fold scores."""
    factory = buildStrategies(
        design.X.shape[1], includeDeep=True, trustCol=design.trustCol
    )[strategy]
    scores = outOfFoldScores(factory, design.X, design.y, nSplits=nSplits)

    context = featurised.reset_index(drop=True)
    if trustMode == "sensitivity" and thresholdCol not in context.columns:
        context = context.assign(**{thresholdCol: alertThreshold(context["trustScore"])})
    return generateAlerts(context, scores)


def run(
    dataset: str = "month",
    nUsers: int = 150,
    nDays: int = 45,
    outPath: Path | None = None,
    nSplits: int = nSplits,
    resample: Resample = "none",
    includeDeep: bool = True,
    alertsPath: Path | None = None,
    progCb=None,
    retFolds: bool = False,
    sample: dict | None = None,
):
    """Cross-validates all strategies on `dataset`. `sample` is passed to `sampleByEmployee`."""
    report = _reporter(progCb)

    report(f"[1/5] Data layer: acquiring data (dataset='{dataset}')")
    raw = loadData(dataset, nUsers, nDays)
    if sample:
        raw = sampleByEmployee(raw, **sample)
        report(f"      sampled to {_describe(raw)}")
    else:
        report(f"      {_describe(raw)}")

    report("[2/5] Temporal behavioural signal layer: building baselines and deviations")
    report("[3/5] Trust modelling layer: computing dynamic trust scores")
    featurised = featurise(raw)

    report("[4/5] Preprocessing (impute/encode/scale)")
    design = designMatrix(featurised)
    report(f"      feature matrix {design.X.shape[0]:,} x {design.X.shape[1]}")

    report(f"[5/5] Detection + validation layers: {nSplits}-fold stratified CV")
    summary, perFold = evaluateStrategies(
        design, report, nSplits=nSplits, resample=resample, includeDeep=includeDeep
    )

    _write(summary, outPath, report)

    if alertsPath is not None:
        best = summary.index[0]
        report(f"      decision layer: ranked alerts from '{best}' (out-of-fold scores)")
        alerts = buildAlerts(design, featurised, best, nSplits=nSplits)
        flagged = int(alerts["label"].sum()) if "label" in alerts else 0
        report(
            f"      {len(alerts):,} alerts raised, {flagged:,} of them genuinely malicious"
        )
        _write(alerts, alertsPath, report, index=False)

    return (summary, perFold) if retFolds else summary


def runFinalTest(
    trainDataset: str = "month",
    testDataset: str = "rawInsiderThreat",
    nUsers: int = 150,
    nDays: int = 45,
    outPath: Path | None = None,
    includeDeep: bool = True,
    progCb=None,
) -> pd.DataFrame:
    """Trains on `trainDataset`, tests on unseen `testDataset`."""
    report = _reporter(progCb)

    report(f"[1/5] Data layer: loading training data (dataset='{trainDataset}')")
    trainRaw = loadData(trainDataset, nUsers, nDays)
    report(f"      train: {_describe(trainRaw)}")

    report("[2/5] Temporal + trust layers: featurising training data")
    train = designMatrix(featurise(trainRaw))

    report(f"[3/5] Data layer: loading independent test data (dataset='{testDataset}')")
    testRaw = loadData(testDataset, nUsers, nDays)
    report(f"      test:  {_describe(testRaw)}")

    report("[4/5] Temporal + trust layers: featurising test data with the train-fit preprocessor")
    test = applyDesignMatrix(featurise(testRaw), train.preprocessor, train.names)

    strategies = buildStrategies(
        train.X.shape[1], includeDeep=includeDeep, trustCol=train.trustCol
    )
    cutOff = test.thresholds if test.thresholds is not None else 0.5
    report(
        f"[5/5] Detection + validation layers: training on {len(train.X):,} rows, "
        f"testing on {len(test.X):,} independent rows"
    )

    rows = []
    for name in strategyOrder(strategies):
        detector = strategies[name]()
        detector.fit(train.X, train.y)
        scores = detector.predict_proba(test.X)
        metrics = computeMetrics(test.y, (scores >= cutOff).astype(int), scores=scores)
        metrics["strategy"] = name
        rows.append(metrics)
        report(_logLine(name, metrics))

    summary = _summaryFrame(rows)
    _write(summary, outPath, report)
    return summary


def runTemporalLayer(
    dataset: str = "month",
    nMalEmp: int | None = None,
    nBenignEmp: int | None = None,
    nSplits: int = nSplits,
    includeDeep: bool = False,
    outPath: Path | None = None,
    progCb=None,
) -> pd.DataFrame:
    """Single-day snapshot vs multi-day temporal features, same rows and folds."""
    report = _reporter(progCb)

    report(f"[1/4] Data layer: loading '{dataset}'")
    raw = loadData(dataset)
    if nMalEmp and nBenignEmp:
        raw = sampleByEmployee(raw, nMalEmp, nBenignEmp)
        report(f"      sampled to {_describe(raw)}")
    else:
        report(f"      {_describe(raw)}")

    report("[2/4] Variant A: single-day snapshot (no multi-day history, no trust)")
    snapshot, snapFolds = evaluateStrategies(
        designMatrix(raw), report, nSplits=nSplits,
        includeDeep=includeDeep, label="snapshot",
    )

    report("[3/4] Variant B: multi-day history (temporal baselines + dynamic trust)")
    temporal, temporalFolds = evaluateStrategies(
        designMatrix(featurise(raw)), report, nSplits=nSplits,
        includeDeep=includeDeep, label="temporal",
    )

    report("[4/4] Comparing variants")
    combined = pd.concat(
        [
            snapshot.assign(variant="singleDaySnapshot"),
            temporal.assign(variant="multiDayTemporal"),
        ]
    ).reset_index()

    for name in sorted(set(snapFolds) & set(temporalFolds)):
        delta = temporal.loc[name, "f1"] - snapshot.loc[name, "f1"]
        report(
            f"  {name:24s} F1 snapshot={snapshot.loc[name, 'f1']:.3f} -> "
            f"temporal={temporal.loc[name, 'f1']:.3f}  (delta {delta:+.3f})"
        )

    _write(combined, outPath, report, index=False)
    combined.attrs["snapFolds"] = snapFolds
    combined.attrs["temporalFolds"] = temporalFolds
    return combined


trustVar: dict[str, TrustMode] = {
    "noTrust": "none",
    "trustAsFeature": "feature",
    "trustAsSensitivity": "sensitivity",
}


def runTrustComparison(
    dataset: str = "month",
    nSplits: int = nSplits,
    includeDeep: bool = False,
    outPath: Path | None = None,
    progCb=None,
) -> pd.DataFrame:
    """No trust vs trust as feature vs trust as sensitivity."""
    report = _reporter(progCb)

    report(f"[1/2] Data layer: loading '{dataset}'")
    raw = loadData(dataset)
    report(f"      {_describe(raw)}")

    frames = []
    for variant, mode in trustVar.items():
        report(f"[2/2] Variant '{variant}' (trustMode={mode})")
        summary, _ = evaluateStrategies(
            designMatrix(featurise(raw, trustMode=mode)), report,
            nSplits=nSplits, includeDeep=includeDeep, label=variant,
        )
        frames.append(summary.assign(variant=variant))

    combined = pd.concat(frames).reset_index()
    _write(combined, outPath, report, index=False)
    return combined


imbalanceVar: list[Resample] = ["none", "smote", "undersample"]


def runImbalanceComparison(
    dataset: str = "month",
    nSplits: int = nSplits,
    includeDeep: bool = False,
    outPath: Path | None = None,
    progCb=None,
) -> pd.DataFrame:
    """No resampling vs SMOTE vs under-sampling, on top of class weighting."""
    report = _reporter(progCb)

    report(f"[1/2] Data layer: loading '{dataset}'")
    raw = loadData(dataset)
    design = designMatrix(featurise(raw))
    report(
        f"      feature matrix {design.X.shape[0]:,} x {design.X.shape[1]}, "
        f"{int(design.y.sum()):,} positives"
    )

    frames = []
    for variant in imbalanceVar:
        report(f"[2/2] Resampling variant '{variant}' (training folds only)")
        summary, _ = evaluateStrategies(
            design, report, nSplits=nSplits, resample=variant,
            includeDeep=includeDeep, label=variant,
        )
        frames.append(summary.assign(resampling=variant))

    combined = pd.concat(frames).reset_index()
    _write(combined, outPath, report, index=False)
    return combined


def runSignalImportance(
    dataset: str = "month",
    strategy: str = "randomForest",
    nRep: int = 10,
    outPath: Path | None = None,
    byKindPath: Path | None = None,
    progCb=None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Signal importance for the best strategy."""
    report = _reporter(progCb)

    report(f"[1/3] Data layer: loading '{dataset}'")
    design = designMatrix(featurise(loadData(dataset)))

    report(f"[2/3] Permutation importance for '{strategy}' ({nRep} shuffles per feature)")
    factory = buildStrategies(design.X.shape[1], trustCol=design.trustCol)[strategy]
    importance = signalImportance(
        factory, design.X, design.y, design.names, nRep=nRep
    )

    report("[3/3] Top signals")
    for row in importance.head(10).itertuples():
        report(f"  {row.feature:48s} {row.importance:+.4f} +/- {row.importanceStd:.4f}")

    byKind = importanceByKind(importance)
    report("\n  importance by kind of signal:")
    for row in byKind.itertuples():
        report(
            f"  {row.kind:30s} total={row.total:+.4f}  share={row.share:6.1%}"
            f"  ({row.n_features} features)"
        )

    _write(importance, outPath, report, index=False)
    _write(byKind, byKindPath, report, index=False)
    return importance, byKind


def significanceTable(
    perFold: dict[str, pd.DataFrame], metric: str = "f1", outPath: Path | None = None,
    progCb=None,
) -> pd.DataFrame:
    """Wilcoxon tests against the best strategy, Holm-Bonferroni corrected."""
    report = _reporter(progCb)
    table = compareAllToBest(perFold, metric=metric)
    best = table.attrs.get("bestStrat")
    report(f"  best on {metric}: {best} ({table.attrs.get('bestMean', float('nan')):.3f})")
    for row in table.itertuples():
        marker = "*" if row.significant else " "
        report(
            f"  {marker} {row.strategy:24s} {metric}={row.mean:.3f}"
            f"  delta={row.meanDiffVsBest:+.3f}  p={row.pValue:.4f}"
        )
    _write(table, outPath, report, index=False)
    return table


def main():
    parser = argparse.ArgumentParser(
        description="Run the five-layer pipeline on one dataset (an ad-hoc run; the "
        "report's experiments are run by scripts/run_experiments.py)"
    )
    parser.add_argument("--dataset", choices=datasetNames, default="month")
    parser.add_argument("--n-users", type=int, default=150, help="synthetic data only")
    parser.add_argument("--n-days", type=int, default=45, help="synthetic data only")
    parser.add_argument("--n-splits", type=int, default=nSplits)
    parser.add_argument(
        "--resample", choices=["none", "smote", "undersample"], default="none",
        help="Resampling applied to training folds only",
    )
    parser.add_argument("--no-deep", action="store_true", help="Skip the torch strategies")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    run(
        dataset=args.dataset,
        nUsers=args.n_users,
        nDays=args.n_days,
        outPath=args.out or runsDir / f"results{args.dataset[:1].upper()}{args.dataset[1:]}.csv",
        nSplits=args.n_splits,
        resample=args.resample,
        includeDeep=not args.no_deep,
    )


if __name__ == "__main__":
    main()
