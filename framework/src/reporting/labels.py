"""Display names and number formats."""
from __future__ import annotations

import pandas as pd

metricLbs = {
    "precision": "P",
    "recall": "R",
    "f1": "F1",
    "falsePositiveRate": "FPR",
    "prAuc": "PR-AUC",
    "falsePositiveCount": "FP",
}

stratLbs = {
    "logisticRegression": "Logistic regression",
    "decTree": "Decision tree",
    "randomForest": "Random forest",
    "svm": "SVM",
    "isolationForest": "Isolation forest",
    "autoencoder": "Autoencoder",
    "lstm": "LSTM",
    "cnn": "CNN",
    "gnn": "GNN",
    "gradBoosting": "Gradient boosting",
    "votingEnsemble": "Voting ensemble",
    "stackingEnsemble": "Stacking ensemble",
    "cnnRnnHybrid": "CNN-RNN hybrid",
    "autoRnnHybrid": "AE-RNN hybrid",
    "trustWeightedEnsemble": "Trust-weighted ensemble",
}

varLbs = {
    "singleDaySnapshot": "Single-day snapshot",
    "multiDayTemporal": "Multi-day temporal",
    "noTrust": "No trust layer",
    "trustAsFeature": "Trust as feature",
    "trustAsSensitivity": "Trust as sensitivity",
    "none": "Class weighting only",
    "smote": "+ SMOTE",
    "undersample": "+ Under-sampling",
}

actLbs = {
    "deviceActivityCount": "device activity",
    "printActivityCount": "print activity",
    "emailActivityCount": "email activity",
    "fileActivityCount": "file activity",
    "httpActivityCount": "web activity",
    "failedLoginCount": "failed logins",
    "dataTransfMb": "data transferred",
    "sessionDurationMinutes": "session duration",
    "offHours": "off-hours access",
    "weekend": "weekend access",
    "trustScore": "dynamic trust score",
}


def label(name: str) -> str:
    """Display name for a strategy or arm."""
    return stratLbs.get(name, varLbs.get(name, name.replace("_", " ")))


def featureLabel(name: str) -> str:
    """Readable feature name."""
    bare = name.split("__", 1)[-1]
    for suffix, qualifier in (
        ("_zscoreSelf", " (vs own baseline)"),
        ("_zscorePeer", " (vs peers)"),
    ):
        if bare.endswith(suffix):
            base = bare[: -len(suffix)]
            return actLbs.get(base, base.replace("_", " ")) + qualifier
    if name.startswith("categorical__"):
        field, _, value = bare.partition("_")
        return f"{field}: {value}"
    return actLbs.get(bare, bare.replace("_", " "))


def signed(value: float, places: int = 3) -> str:
    """Signed difference; values that round to zero print as 0.000."""
    rounded = round(value, places)
    if rounded == 0:
        return f"{0.0:.{places}f}"
    return f"{rounded:+.{places}f}"


def formatValue(value, column: str) -> str:
    """Formats a metric value."""
    if pd.isna(value):
        return "n/a"
    if column == "falsePositiveCount":
        return f"{value:,.0f}"
    if column == "falsePositiveRate":
        return f"{value:.4f}"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)
