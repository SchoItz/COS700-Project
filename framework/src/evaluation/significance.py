"""Paired Wilcoxon signed-rank tests over per-fold results."""
from __future__ import annotations

import pandas as pd
from scipy.stats import wilcoxon

ALPHA = 0.05


def compareStrategies(
    resA: pd.DataFrame, resB: pd.DataFrame, metric: str = "f1"
) -> dict[str, float]:
    """Paired test between two strategies."""
    a, b = resA[metric].to_numpy(), resB[metric].to_numpy()
    if len(a) != len(b):
        raise ValueError("Both result sets must have the same number of folds to pair on.")
    if (a == b).all():
        return {"statistic": 0.0, "pValue": 1.0, "meanDiff": 0.0}
    statistic, pValue = wilcoxon(a, b)
    return {
        "statistic": float(statistic),
        "pValue": float(pValue),
        "meanDiff": float((a - b).mean()),
    }


def holmBonferroni(pValues: list[float], alpha: float = ALPHA) -> list[bool]:
    """Holm-Bonferroni correction; returns significance per p-value, in order."""
    order = sorted(range(len(pValues)), key=lambda i: pValues[i])
    n = len(pValues)
    significant = [False] * n
    for rank, idx in enumerate(order):
        if pValues[idx] <= alpha / (n - rank):
            significant[idx] = True
        else:
            break
    return significant


def compareAllToBest(
    perFold: dict[str, pd.DataFrame], metric: str = "f1", alpha: float = ALPHA
) -> pd.DataFrame:
    """Tests every strategy against the best on `metric`."""
    columns = ["strategy", "mean", "meanDiffVsBest", "pValue", "significant"]
    if not perFold:
        return pd.DataFrame(columns=columns)

    means = {name: float(df[metric].mean()) for name, df in perFold.items()}
    best = max(means, key=means.get)

    rows, pValues = [], []
    for name, df in perFold.items():
        if name == best:
            continue
        comparison = compareStrategies(perFold[best], df, metric=metric)
        rows.append(
            {
                "strategy": name,
                "mean": means[name],
                "meanDiffVsBest": comparison["meanDiff"],
                "pValue": comparison["pValue"],
            }
        )
        pValues.append(comparison["pValue"])

    for row, isSignif in zip(rows, holmBonferroni(pValues, alpha)):
        row["significant"] = bool(isSignif)

    out = (
        pd.DataFrame(rows, columns=columns)
        .sort_values("mean", ascending=False)
        .reset_index(drop=True)
    )
    out.attrs["bestStrat"] = best
    out.attrs["bestMean"] = means[best]
    out.attrs["metric"] = metric
    return out
