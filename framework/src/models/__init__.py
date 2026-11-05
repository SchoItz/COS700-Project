"""Detection layer. Roster: `registry.buildStrategies`."""
from .base import Detector, DetectorFactory
from .classical import classicalFactories
from .combined import combinedFactories
from .registry import torchAvailable, buildStrategies

__all__ = [
    "Detector",
    "DetectorFactory",
    "classicalFactories",
    "combinedFactories",
    "buildStrategies",
    "torchAvailable",
]

if torchAvailable:
    from .deep import deepFactories

    __all__.append("deepFactories")
