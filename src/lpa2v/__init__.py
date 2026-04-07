"""Biblioteca orientada a objetos para algoritmos baseados em LPA2v."""

from .algorithms import available_algorithms, create_algorithm, registry
from .algorithms.base import LPA2vAlgorithm
from .algorithms.para_analyzer import (
    ParaAnalyzer,
    ParaAnalyzerResult,
    ParaAnalyzerState,
    ParaAnalyzerThresholds,
)
from .models import EvidencePair

__all__ = [
    "EvidencePair",
    "LPA2vAlgorithm",
    "ParaAnalyzer",
    "ParaAnalyzerResult",
    "ParaAnalyzerState",
    "ParaAnalyzerThresholds",
    "available_algorithms",
    "create_algorithm",
    "registry",
]

__version__ = "0.1.0"
