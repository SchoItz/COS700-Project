"""Results -> `Table` -> LaTeX."""
from .labels import featureLabel, formatValue, label, signed
from .latex import toLatex, writeTex
from .tables import (
    Table,
    datasetsTable,
    importanceTable,
    resultsTable,
    significanceTable,
    variantTable,
)

__all__ = [
    "Table",
    "resultsTable",
    "variantTable",
    "significanceTable",
    "importanceTable",
    "datasetsTable",
    "toLatex",
    "writeTex",
    "label",
    "featureLabel",
    "formatValue",
    "signed",
]
