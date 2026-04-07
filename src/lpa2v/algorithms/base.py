from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar, Generic, TypeVar

InputT = TypeVar("InputT")
ResultT = TypeVar("ResultT")


class LPA2vAlgorithm(ABC, Generic[InputT, ResultT]):
    """Contrato base para algoritmos da biblioteca LPA2v."""

    name: ClassVar[str]
    aliases: ClassVar[tuple[str, ...]] = ()
    description: ClassVar[str] = ""

    @classmethod
    def supported_names(cls) -> tuple[str, ...]:
        return (cls.name, *cls.aliases)

    @abstractmethod
    def run(self, data: InputT) -> ResultT:
        """Executa o algoritmo a partir da entrada padronizada."""

    def __call__(self, data: InputT) -> ResultT:
        return self.run(data)
