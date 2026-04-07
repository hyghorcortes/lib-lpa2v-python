from __future__ import annotations

from typing import TypeVar

from .base import LPA2vAlgorithm

AlgorithmType = TypeVar("AlgorithmType", bound=type[LPA2vAlgorithm])


def _normalize_name(name: str) -> str:
    return name.strip().lower().replace("-", "_").replace(" ", "_")


class AlgorithmRegistry:
    """Registro de algoritmos LPA2v por nome e alias."""

    def __init__(self) -> None:
        self._algorithms: dict[str, type[LPA2vAlgorithm]] = {}

    def register(self, algorithm_class: AlgorithmType) -> AlgorithmType:
        for raw_name in algorithm_class.supported_names():
            name = _normalize_name(raw_name)
            current = self._algorithms.get(name)
            if current is not None and current is not algorithm_class:
                raise ValueError(f"Nome de algoritmo ja registrado: {raw_name!r}")
            self._algorithms[name] = algorithm_class
        return algorithm_class

    def get_class(self, name: str) -> type[LPA2vAlgorithm]:
        normalized_name = _normalize_name(name)
        try:
            return self._algorithms[normalized_name]
        except KeyError as exc:
            available = ", ".join(self.available())
            raise KeyError(f"Algoritmo desconhecido: {name!r}. Disponiveis: {available}") from exc

    def create(self, name: str, **kwargs: object) -> LPA2vAlgorithm:
        algorithm_class = self.get_class(name)
        return algorithm_class(**kwargs)

    def available(self) -> tuple[str, ...]:
        canonical_names = {algorithm_class.name for algorithm_class in self._algorithms.values()}
        return tuple(sorted(canonical_names))


registry = AlgorithmRegistry()
