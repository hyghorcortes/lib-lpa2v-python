from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import inf
from typing import Any, cast

from ..models import EvidencePair
from .base import EvidenceInput, EvidencePairAlgorithm
from .registry import registry


class ParaAnalyzerState(str, Enum):
    NOT_T = "not(T)"
    QNOT_T_F = "Qnot(T)-F"
    QF_NOT_T = "QF-not(T)"
    F = "F"
    QF_T = "QF-T"
    QT_F = "QT-F"
    T = "T"
    QT_V = "QT-V"
    QV_T = "QV-T"
    V = "V"
    QV_NOT_T = "QV-not(T)"
    QNOT_T_V = "Qnot(T)-V"


@dataclass(frozen=True, slots=True)
class ParaAnalyzerThresholds:
    """Limiares configuraveis do para-analisador.

    Por padrao, a configuracao classica usa:
    - C1 = 0.5
    - C2 = -0.5
    - C3 = 0.5
    - C4 = -0.5
    """

    certainty_limit: float = 0.5
    contradiction_limit: float | None = None
    comparison_factor: float | None = None

    def __post_init__(self) -> None:
        certainty_limit = float(self.certainty_limit)
        contradiction_limit = (
            float(self.contradiction_limit) if self.contradiction_limit is not None else 1.0 - certainty_limit
        )

        if not 0.0 < certainty_limit <= 1.0:
            raise ValueError("certainty_limit deve estar no intervalo (0, 1].")
        if not 0.0 <= contradiction_limit < 1.0:
            raise ValueError("contradiction_limit deve estar no intervalo [0, 1).")

        comparison_factor = (
            float(self.comparison_factor)
            if self.comparison_factor is not None
            else (certainty_limit / contradiction_limit if contradiction_limit > 0.0 else inf)
        )
        if comparison_factor <= 0.0:
            raise ValueError("comparison_factor deve ser maior que zero.")

        object.__setattr__(self, "certainty_limit", certainty_limit)
        object.__setattr__(self, "contradiction_limit", contradiction_limit)
        object.__setattr__(self, "comparison_factor", comparison_factor)

    @classmethod
    def from_mean_and_sensitivity(cls, mean: float, sensitivity: float) -> "ParaAnalyzerThresholds":
        """Cria limiares compativeis com a CPAet baseada em m_e e s."""

        mean_value = float(mean)
        sensitivity_value = float(sensitivity)
        adjusted_mean = mean_value - sensitivity_value
        if adjusted_mean < 0.5:
            adjusted_mean = 0.5
        return cls(certainty_limit=adjusted_mean, contradiction_limit=1.0 - adjusted_mean)

    @property
    def c1(self) -> float:
        return self.certainty_limit

    @property
    def c2(self) -> float:
        return -self.certainty_limit

    @property
    def c3(self) -> float:
        return cast(float, self.contradiction_limit)

    @property
    def c4(self) -> float:
        return -self.c3

    def as_dict(self) -> dict[str, float]:
        return {
            "c1": self.c1,
            "c2": self.c2,
            "c3": self.c3,
            "c4": self.c4,
            "comparison_factor": cast(float, self.comparison_factor),
        }


@dataclass(frozen=True, slots=True)
class ParaAnalyzerResult:
    algorithm: str
    evidence: EvidencePair
    state: ParaAnalyzerState
    region_id: int
    gc: float
    gct: float
    thresholds: ParaAnalyzerThresholds

    def to_dict(self) -> dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "evidence": self.evidence.as_dict(),
            "state": self.state.value,
            "region_id": self.region_id,
            "gc": self.gc,
            "gct": self.gct,
            "thresholds": self.thresholds.as_dict(),
        }


@registry.register
class ParaAnalyzer(EvidencePairAlgorithm[ParaAnalyzerResult]):
    """Implementacao orientada a objetos do para-analisador da LPA2v."""

    name = "para-analisador"
    aliases = ("para_analisador", "para-analyzer", "para_analyzer", "paraanalisador")
    description = "Classifica um par de evidencias LPA2v nas 12 regioes do para-analisador."

    def __init__(self, thresholds: ParaAnalyzerThresholds | None = None) -> None:
        self.thresholds = thresholds or ParaAnalyzerThresholds()

    def run(self, data: EvidenceInput) -> ParaAnalyzerResult:
        evidence = self._coerce_evidence(data)
        gc = evidence.gc
        gct = evidence.gct
        state, region_id = self.classify_values(gc, gct, thresholds=self.thresholds)
        return ParaAnalyzerResult(
            algorithm=self.name,
            evidence=evidence,
            state=state,
            region_id=region_id,
            gc=gc,
            gct=gct,
            thresholds=self.thresholds,
        )

    @staticmethod
    def classify_values(
        gc: float,
        gct: float,
        *,
        thresholds: ParaAnalyzerThresholds,
    ) -> tuple[ParaAnalyzerState, int]:
        c1 = thresholds.c1
        c2 = thresholds.c2
        c3 = thresholds.c3
        c4 = thresholds.c4
        scaled_gct = cast(float, thresholds.comparison_factor) * gct
        abs_gc = abs(gc)
        abs_scaled_gct = abs(scaled_gct)

        if gc >= c1:
            return ParaAnalyzerState.V, 10
        if gc <= c2:
            return ParaAnalyzerState.F, 4
        if gct >= c3:
            return ParaAnalyzerState.T, 7
        if gct <= c4:
            return ParaAnalyzerState.NOT_T, 1

        if 0.0 <= gc < c1 and 0.0 <= gct < c3:
            if abs_gc >= abs_scaled_gct:
                return ParaAnalyzerState.QV_T, 9
            return ParaAnalyzerState.QT_V, 8

        if 0.0 <= gc < c1 and c4 < gct < 0.0:
            if abs_gc >= abs_scaled_gct:
                return ParaAnalyzerState.QV_NOT_T, 11
            return ParaAnalyzerState.QNOT_T_V, 12

        if c2 < gc < 0.0 and 0.0 <= gct < c3:
            if abs_gc >= abs_scaled_gct:
                return ParaAnalyzerState.QF_T, 5
            return ParaAnalyzerState.QT_F, 6

        if c2 < gc < 0.0 and c4 < gct < 0.0:
            if abs_gc >= abs_scaled_gct:
                return ParaAnalyzerState.QF_NOT_T, 3
            return ParaAnalyzerState.QNOT_T_F, 2

        # Fallback para pontos de fronteira afetados por arredondamento numerico.
        if gc >= 0.0 and gct >= 0.0:
            if abs_gc >= abs_scaled_gct:
                return ParaAnalyzerState.QV_T, 9
            return ParaAnalyzerState.QT_V, 8

        if gc >= 0.0 and gct < 0.0:
            if abs_gc >= abs_scaled_gct:
                return ParaAnalyzerState.QV_NOT_T, 11
            return ParaAnalyzerState.QNOT_T_V, 12

        if gc < 0.0 and gct >= 0.0:
            if abs_gc >= abs_scaled_gct:
                return ParaAnalyzerState.QF_T, 5
            return ParaAnalyzerState.QT_F, 6

        if abs_gc >= abs_scaled_gct:
            return ParaAnalyzerState.QF_NOT_T, 3
        return ParaAnalyzerState.QNOT_T_F, 2

    def _classify(self, gc: float, gct: float) -> tuple[ParaAnalyzerState, int]:
        return self.classify_values(gc, gct, thresholds=self.thresholds)
