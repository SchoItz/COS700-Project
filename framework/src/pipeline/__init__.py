"""Pipeline: `design` builds the feature matrix, `experiments` runs the experiments."""
from .design import Design, applyDesignMatrix, designMatrix, featurise
from .experiments import (
    DATASETS,
    evaluateStrategies,
    loadData,
    run,
    runFinalTest,
    runImbalanceComparison,
    runSignalImportance,
    runTemporalLayer,
    runTrustComparison,
    sampleByEmployee,
    significanceTable,
)

__all__ = [
    "DATASETS",
    "Design",
    "loadData",
    "sampleByEmployee",
    "featurise",
    "designMatrix",
    "applyDesignMatrix",
    "evaluateStrategies",
    "run",
    "runFinalTest",
    "runTemporalLayer",
    "runTrustComparison",
    "runImbalanceComparison",
    "runSignalImportance",
    "significanceTable",
]
