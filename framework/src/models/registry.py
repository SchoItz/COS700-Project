"""The 15 strategies, built under identical conditions.

    individual : logistic_regression, decision_tree, random_forest, svm,
                 isolation_forest, autoencoder, lstm, cnn, gnn
    combined   : gradient_boosting, voting_ensemble, stacking_ensemble,
                 cnn_rnn_hybrid, autoencoder_rnn_hybrid,
                 trust_weighted_ensemble"""
from __future__ import annotations

from .base import DetectorFactory
from .classical import classicalFactories
from .combined import combinedFactories

try:
    from .combined.hybrid_torch import hybridFactories
    from .deep import deepFactories

    torchAvailable = True
except ImportError:
    torchAvailable = False


FAMILY = {
    "logisticRegression": "individual",
    "decTree": "individual",
    "randomForest": "individual",
    "svm": "individual",
    "isolationForest": "individual",
    "autoencoder": "individual",
    "lstm": "individual",
    "cnn": "individual",
    "gnn": "individual",
    "gradBoosting": "combined",
    "votingEnsemble": "combined",
    "stackingEnsemble": "combined",
    "cnnRnnHybrid": "combined",
    "autoRnnHybrid": "combined",
    "trustWeightedEnsemble": "combined",
}

def buildStrategies(
    inDim: int,
    includeDeep: bool = True,
    deepEpochs: int = 12,
    trustCol: int | None = None,
) -> dict[str, DetectorFactory]:
    """Returns {name: factory}. `includeDeep=False` skips the torch models."""
    strategies: dict[str, DetectorFactory] = {
        **classicalFactories(),
        **combinedFactories(trustCol=trustCol),
    }
    if includeDeep and torchAvailable:
        strategies.update(deepFactories(inDim, epochs=deepEpochs))
        strategies.update(hybridFactories(inDim, epochs=deepEpochs))
    return strategies


def strategyOrder(names) -> list[str]:
    """Individual then combined, alphabetical within each."""
    return sorted(names, key=lambda n: (FAMILY.get(n, "zz") != "individual", n))
