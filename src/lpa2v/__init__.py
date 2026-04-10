"""Biblioteca orientada a objetos para algoritmos baseados em LPA2v."""

from .algorithms import available_algorithms, create_algorithm, registry
from .algorithms.base import EvidencePairAlgorithm, LPA2vAlgorithm
from .algorithms.cap import Cap, CapInput, CapMode, CapResult
from .algorithms.nap import Nap, NapResult
from .algorithms.para_analyzer import (
    ParaAnalyzer,
    ParaAnalyzerResult,
    ParaAnalyzerState,
    ParaAnalyzerThresholds,
)
from .models import EvidencePair

__all__ = [
    "EvidencePair",
    "EvidencePairAlgorithm",
    "LPA2vAlgorithm",
    "Cap",
    "CapInput",
    "CapMode",
    "CapResult",
    "Nap",
    "NapResult",
    "ParaAnalyzer",
    "ParaAnalyzerResult",
    "ParaAnalyzerState",
    "ParaAnalyzerThresholds",
    "available_algorithms",
    "create_algorithm",
    "registry",
]

__version__ = "0.3.0"
