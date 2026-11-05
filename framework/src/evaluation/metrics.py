"""Precision, recall, F1, FPR, PR-AUC and ROC AUC for the malicious class."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

rateMetrics = [
    "precision",
    "recall",
    "f1",
    "detRate",
    "falsePositiveRate",
    "prAuc",
    "rocAuc",
]
countMetrics = ["falsePositiveCount", "truePositiveCount", "nPositives", "nSamples"]


def computeMetrics(
    yTrue: np.ndarray, yPred: np.ndarray, scores: np.ndarray | None = None
) -> dict[str, float]:
    yTrue = np.asarray(yTrue)
    yPred = np.asarray(yPred)

    tn, fp, fn, tp = confusion_matrix(yTrue, yPred, labels=[0, 1]).ravel()
    detRate = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    falsePositiveRate = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    metrics = {
        "precision": precision_score(yTrue, yPred, zero_division=0),
        "recall": recall_score(yTrue, yPred, zero_division=0),
        "f1": f1_score(yTrue, yPred, zero_division=0),
        "detRate": detRate,
        "falsePositiveRate": falsePositiveRate,
        "falsePositiveCount": int(fp),
        "truePositiveCount": int(tp),
        "nPositives": int((yTrue == 1).sum()),
        "nSamples": int(len(yTrue)),
    }

    if scores is not None and len(np.unique(yTrue)) > 1:
        scores = np.asarray(scores, dtype=float)
        metrics["prAuc"] = float(average_precision_score(yTrue, scores))
        metrics["rocAuc"] = float(roc_auc_score(yTrue, scores))
    else:
        metrics["prAuc"] = float("nan")
        metrics["rocAuc"] = float("nan")

    return metrics
