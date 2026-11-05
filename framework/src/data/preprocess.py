"""Imputes, one-hot encodes, standardises and drops ethically excluded columns."""
from __future__ import annotations

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .schema import catCol, excluded

idCol = ["userId", "timestamp", "label", "alertThreshold"]

passCol = ["userId", "timestamp", "alertThreshold"]


def _splitColumns(featureDf: pd.DataFrame) -> tuple[list[str], list[str]]:
    catCols = [c for c in catCol if c in featureDf.columns]
    numCols = [
        c
        for c in featureDf.columns
        if c not in catCols and pd.api.types.is_numeric_dtype(featureDf[c])
    ]
    return numCols, catCols


def buildPreprocessor(numCols: list[str], catCols: list[str]) -> ColumnTransformer:
    numPipe = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    catPipeline = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("encode", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("numeric", numPipe, numCols),
            ("categorical", catPipeline, catCols),
        ]
    )


def _wrap(X_array, featureNames, df: pd.DataFrame) -> pd.DataFrame:
    X = pd.DataFrame(
        X_array.toarray() if hasattr(X_array, "toarray") else X_array,
        columns=featureNames,
        index=df.index,
    )
    for position, column in enumerate(c for c in passCol if c in df.columns):
        X.insert(position, column, df[column].values)
    return X


def preprocess(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, ColumnTransformer]:
    """Fits and transforms; returns (X, y, preprocessor)."""
    df = df.drop(columns=[c for c in excluded if c in df.columns])

    y = df["label"].astype(int)
    featureDf = df.drop(columns=[c for c in idCol if c in df.columns])

    numCols, catCols = _splitColumns(featureDf)
    preprocessor = buildPreprocessor(numCols, catCols)
    X_array = preprocessor.fit_transform(featureDf)
    X = _wrap(X_array, preprocessor.get_feature_names_out(), df)
    return X, y, preprocessor


def preprocessApply(
    df: pd.DataFrame, preprocessor: ColumnTransformer
) -> tuple[pd.DataFrame, pd.Series]:
    """Transforms with an already-fitted preprocessor."""
    df = df.drop(columns=[c for c in excluded if c in df.columns])

    y = df["label"].astype(int)
    featureDf = df.drop(columns=[c for c in idCol if c in df.columns])

    X_array = preprocessor.transform(featureDf)
    X = _wrap(X_array, preprocessor.get_feature_names_out(), df)
    return X, y
