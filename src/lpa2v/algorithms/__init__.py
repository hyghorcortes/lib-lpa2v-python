from .base import LPA2vAlgorithm
from .para_analyzer import ParaAnalyzer
from .registry import registry


def create_algorithm(name: str, **kwargs: object) -> LPA2vAlgorithm:
    return registry.create(name, **kwargs)


def available_algorithms() -> tuple[str, ...]:
    return registry.available()


__all__ = [
    "LPA2vAlgorithm",
    "ParaAnalyzer",
    "available_algorithms",
    "create_algorithm",
    "registry",
]
