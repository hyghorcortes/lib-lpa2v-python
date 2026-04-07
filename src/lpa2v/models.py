from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _validate_unit_interval(name: str, value: float) -> float:
    numeric_value = float(value)
    if not 0.0 <= numeric_value <= 1.0:
        raise ValueError(f"{name} deve estar no intervalo [0, 1]. Valor recebido: {value!r}")
    return numeric_value


@dataclass(frozen=True, slots=True)
class EvidencePair:
    """Representa um par de evidencias LPA2v.

    Attributes:
        favorable: grau de evidencia favoravel (mu).
        contrary: grau de evidencia contraria (lambda).
        metadata: dados auxiliares opcionais do contexto da evidenciacao.
    """

    favorable: float
    contrary: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "favorable", _validate_unit_interval("favorable", self.favorable))
        object.__setattr__(self, "contrary", _validate_unit_interval("contrary", self.contrary))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @classmethod
    def from_legacy(cls, favorable: float, contrary_complement: float, **metadata: Any) -> "EvidencePair":
        """Cria um par de evidencias a partir do formato legado.

        Em algumas implementacoes anteriores, o segundo valor representava o complemento
        da evidencia contraria. Neste caso, a biblioteca converte automaticamente para
        o formato padrao baseado em `lambda`.
        """

        contrary = 1.0 - _validate_unit_interval("contrary_complement", contrary_complement)
        return cls(favorable=favorable, contrary=contrary, metadata=metadata)

    @property
    def gc(self) -> float:
        """Grau de certeza."""

        return self.favorable - self.contrary

    @property
    def gct(self) -> float:
        """Grau de contradicao."""

        return self.favorable + self.contrary - 1.0

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "favorable": self.favorable,
            "contrary": self.contrary,
        }
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        return payload
