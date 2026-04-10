from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Generic, TypeVar

from ..models import EvidencePair

InputT = TypeVar("InputT")
ResultT = TypeVar("ResultT")

EvidenceInput = EvidencePair | tuple[float, float] | dict[str, Any]


def _coerce_metadata(raw_metadata: Any) -> dict[str, Any]:
    if raw_metadata is None:
        return {}
    return dict(raw_metadata)


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


class EvidencePairAlgorithm(LPA2vAlgorithm[EvidenceInput, ResultT], ABC, Generic[ResultT]):
    """Base comum para algoritmos que operam sobre um par de evidencias LPA2v."""

    def analyze(self, favorable: float, contrary: float, **metadata: Any) -> ResultT:
        return self.run(EvidencePair(favorable=favorable, contrary=contrary, metadata=metadata))

    def analyze_legacy(self, favorable: float, contrary_complement: float, **metadata: Any) -> ResultT:
        return self.run(EvidencePair.from_legacy(favorable, contrary_complement, **metadata))

    def _coerce_evidence(self, data: EvidenceInput) -> EvidencePair:
        if isinstance(data, EvidencePair):
            return data

        if isinstance(data, tuple):
            if len(data) != 2:
                raise ValueError("A tupla de entrada deve ter exatamente dois valores: (favorable, contrary).")
            return EvidencePair(favorable=data[0], contrary=data[1])

        if isinstance(data, dict):
            if "favorable" in data and "contrary" in data:
                return EvidencePair(
                    favorable=float(data["favorable"]),
                    contrary=float(data["contrary"]),
                    metadata=_coerce_metadata(data.get("metadata")),
                )

            if "mu" in data and "lambda" in data:
                return EvidencePair(
                    favorable=float(data["mu"]),
                    contrary=float(data["lambda"]),
                    metadata=_coerce_metadata(data.get("metadata")),
                )

            if "mu" in data and "contrary_complement" in data:
                return EvidencePair.from_legacy(
                    favorable=float(data["mu"]),
                    contrary_complement=float(data["contrary_complement"]),
                    **_coerce_metadata(data.get("metadata")),
                )

        raise TypeError(
            "Entrada invalida para o algoritmo. Use EvidencePair, tupla (favorable, contrary) "
            "ou dicionario com chaves reconhecidas."
        )
