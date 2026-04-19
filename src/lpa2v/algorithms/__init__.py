from .base import EvidencePairAlgorithm, LPA2vAlgorithm
from .cap import Cap
from .cpaet import Capet
from .nap import Nap
from .para_analyzer import ParaAnalyzer
from .registry import registry


def create_algorithm(name: str, **kwargs: object) -> LPA2vAlgorithm:
    return registry.create(name, **kwargs)


def available_algorithms() -> tuple[str, ...]:
    return registry.available()


__all__ = [
    "EvidencePairAlgorithm",
    "LPA2vAlgorithm",
    "Cap",
    "Capet",
    "Nap",
    "ParaAnalyzer",
    "available_algorithms",
    "create_algorithm",
    "registry",
]
