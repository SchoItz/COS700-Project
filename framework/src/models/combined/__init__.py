from .strategies import TrustWeightedEnsemble, combinedFactories

__all__ = ["combinedFactories", "TrustWeightedEnsemble"]

try:
    from .hybrid_torch import (
        AutoencoderRNNHybridDetector,
        CNNRNNHybridDetector,
        hybridFactories,
    )

    __all__ += ["hybridFactories", "CNNRNNHybridDetector", "AutoencoderRNNHybridDetector"]
except ImportError:
    pass
