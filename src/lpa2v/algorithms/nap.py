from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..models import EvidencePair
from .base import EvidenceInput, EvidencePairAlgorithm
from .registry import registry


@dataclass(frozen=True, slots=True)
class NapResult:
    """Resultado completo do algoritmo NAP."""

    algorithm: str
    evidence: EvidencePair
    mi_er: float
    phi_e: float
    phi_e_partial: float
    distance: float
    mi_ctr: float
    gc: float
    gct: float
    gcr: float
    lambda_value: float
    resolved: bool

    def as_legacy_vector(self) -> tuple[float, float, float, float, float, float]:
        """Retorna a saida no mesmo formato vetorial da implementacao MATLAB.

        Ordem:
        1. mi_er
        2. phi_e
        3. phi_e_partial
        4. D
        5. mi_ctr
        6. lambda
        """

        return (
            self.mi_er,
            self.phi_e,
            self.phi_e_partial,
            self.distance,
            self.mi_ctr,
            self.lambda_value,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "evidence": self.evidence.as_dict(),
            "mi_er": self.mi_er,
            "phi_e": self.phi_e,
            "phi_e_partial": self.phi_e_partial,
            "D": self.distance,
            "mi_ctr": self.mi_ctr,
            "gc": self.gc,
            "gct": self.gct,
            "gcr": self.gcr,
            "lambda": self.lambda_value,
            "resolved": self.resolved,
            "legacy_vector": list(self.as_legacy_vector()),
        }


@registry.register
class Nap(EvidencePairAlgorithm[NapResult]):
    """Implementacao completa do NAP (No de Analise Paraconsistente)."""

    name = "nap"
    aliases = (
        "NAP",
        "no_de_analise_paraconsistente",
        "no-de-analise-paraconsistente",
        "no de analise paraconsistente",
    )
    description = "Executa o algoritmo NAP completo e retorna todos os valores principais da analise."

    def run(self, data: EvidenceInput) -> NapResult:
        evidence = self._coerce_evidence(data)
        mu = evidence.favorable
        lambda_value = evidence.contrary

        mi_ctr = (mu + lambda_value) * 0.5
        phi_e_partial = 1.0 - abs((2.0 * mi_ctr) - 1.0)
        gc = evidence.gc
        gct = evidence.gct
        distance = (((1.0 - abs(gc)) ** 2) + (gct**2)) ** 0.5
        gcr = (1.0 - distance) if gc >= 0.0 else (distance - 1.0)

        resolved = phi_e_partial > 0.25 and distance <= 1.0
        if not resolved:
            mi_er = 0.5
            phi_e = phi_e_partial
        else:
            if mi_ctr < 0.5:
                phi_e = -phi_e_partial
            elif mi_ctr > 0.5:
                phi_e = phi_e_partial
            else:
                phi_e = 0.0
            mi_er = (gcr + 1.0) * 0.5

        return NapResult(
            algorithm=self.name,
            evidence=evidence,
            mi_er=mi_er,
            phi_e=phi_e,
            phi_e_partial=phi_e_partial,
            distance=distance,
            mi_ctr=mi_ctr,
            gc=gc,
            gct=gct,
            gcr=gcr,
            lambda_value=lambda_value,
            resolved=resolved,
        )
