from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Sequence, TypeAlias

from ..models import EvidencePair
from .base import LPA2vAlgorithm
from .para_analyzer import ParaAnalyzer, ParaAnalyzerState, ParaAnalyzerThresholds
from .registry import registry

DEFAULT_ERROR_MARGIN = 0.15
DEFAULT_BOOTSTRAP_VALUE = 0.5
STRICT_COMPARISON_TOLERANCE = 1e-12


def _coerce_metadata(raw_metadata: Any) -> dict[str, Any]:
    if raw_metadata is None:
        return {}
    return dict(raw_metadata)


def _validate_unit_interval(name: str, value: float) -> float:
    numeric_value = float(value)
    if not 0.0 <= numeric_value <= 1.0:
        raise ValueError(f"{name} deve estar no intervalo [0, 1]. Valor recebido: {value!r}")
    return numeric_value


def _validate_moving_average_value(name: str, value: float) -> float:
    numeric_value = _validate_unit_interval(name, value)
    if numeric_value < 0.5:
        raise ValueError(f"{name} deve estar no intervalo [0.5, 1]. Valor recebido: {value!r}")
    return numeric_value


def _validate_error_margin(value: float) -> float:
    numeric_value = float(value)
    if not 0.0 <= numeric_value <= 0.5:
        raise ValueError(f"error_margin deve estar no intervalo [0, 0.5]. Valor recebido: {value!r}")
    return numeric_value


def _coerce_moving_average_vector(values: Sequence[float]) -> tuple[float, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError("moving_average_in deve ser uma sequencia numerica e nao texto.")

    vector = tuple(_validate_moving_average_value("moving_average_in", value) for value in values)
    if not vector:
        raise ValueError("moving_average_in deve conter ao menos um valor.")
    return vector


def _build_bootstrap_vector(window_size: int, bootstrap_value: float = DEFAULT_BOOTSTRAP_VALUE) -> tuple[float, ...]:
    numeric_window_size = int(window_size)
    if numeric_window_size <= 0:
        raise ValueError(f"window_size deve ser maior que zero. Valor recebido: {window_size!r}")

    seed = _validate_moving_average_value("bootstrap_value", bootstrap_value)
    return (seed,) * numeric_window_size


def _real_certainty_degree(certainty_degree: float, distance: float) -> float:
    if certainty_degree >= 0.0:
        return 1.0 - distance
    return distance - 1.0


def _is_strictly_greater(left: float, right: float, *, abs_tol: float = STRICT_COMPARISON_TOLERANCE) -> bool:
    return (left - right) > abs_tol


def _coerce_evidence_payload(data: EvidencePair | tuple[float, float] | dict[str, Any]) -> EvidencePair:
    if isinstance(data, EvidencePair):
        return data

    if isinstance(data, tuple):
        if len(data) != 2:
            raise ValueError("A tupla de evidencia deve ter exatamente dois valores: (favorable, contrary).")
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
        "Entrada invalida para a CPAet. Use EvidencePair, tupla (favorable, contrary) "
        "ou dicionario com chaves reconhecidas."
    )


@dataclass(frozen=True, slots=True)
class CapetInput:
    """Entrada padrao da CPAet."""

    evidence: EvidencePair
    moving_average_in: tuple[float, ...]
    error_margin: float = DEFAULT_ERROR_MARGIN

    def __post_init__(self) -> None:
        object.__setattr__(self, "moving_average_in", _coerce_moving_average_vector(self.moving_average_in))
        object.__setattr__(self, "error_margin", _validate_error_margin(self.error_margin))

    @classmethod
    def bootstrap(
        cls,
        evidence: EvidencePair,
        window_size: int,
        error_margin: float = DEFAULT_ERROR_MARGIN,
        bootstrap_value: float = DEFAULT_BOOTSTRAP_VALUE,
    ) -> "CapetInput":
        return cls(
            evidence=evidence,
            moving_average_in=_build_bootstrap_vector(window_size, bootstrap_value),
            error_margin=error_margin,
        )

    @property
    def best_values_count(self) -> int:
        return len(self.moving_average_in)

    def as_dict(self) -> dict[str, Any]:
        return {
            "evidence": self.evidence.as_dict(),
            "moving_average_in": list(self.moving_average_in),
            "best_values_count": self.best_values_count,
            "error_margin": self.error_margin,
        }


CapetInputPayload: TypeAlias = CapetInput | tuple[float, float, Sequence[float]] | dict[str, Any]


@dataclass(frozen=True, slots=True)
class CapetResult:
    """Resultado completo da CPAet."""

    algorithm: str
    input: CapetInput
    accepted_sample: bool
    e: float
    me: float
    me_adj: float
    me_out: tuple[float, ...]
    vmaxu: float
    vminu: float
    vmaxc: float
    vminc: float
    gc: float
    gct: float
    phi: float
    distance: float
    gcr: float
    mu_er: float
    state: ParaAnalyzerState
    region_id: int
    thresholds: ParaAnalyzerThresholds
    resolved: bool

    @property
    def resultant_evidence_degree(self) -> float:
        return self.mu_er

    def to_dict(self) -> dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "input": self.input.as_dict(),
            "accepted_sample": self.accepted_sample,
            "e": self.e,
            "me": self.me,
            "me_adj": self.me_adj,
            "me_out": list(self.me_out),
            "vmaxu": self.vmaxu,
            "vminu": self.vminu,
            "vmaxc": self.vmaxc,
            "vminc": self.vminc,
            "gc": self.gc,
            "gct": self.gct,
            "phi": self.phi,
            "distance": self.distance,
            "gcr": self.gcr,
            "mu_er": self.mu_er,
            "resultant_evidence_degree": self.resultant_evidence_degree,
            "state": self.state.value,
            "region_id": self.region_id,
            "thresholds": self.thresholds.as_dict(),
            "resolved": self.resolved,
        }


@registry.register
class Capet(LPA2vAlgorithm[CapetInputPayload, CapetResult]):
    """Implementa a CPAet (Cubic Paraconsistent Analyser with Evidence Filter and Temporal Analysis)."""

    name = "capet"
    aliases = (
        "CAPet",
        "CPAet",
        "cap_et",
        "cap-e-t",
        "cpa_et",
        "cpa-e-t",
        "cpaet",
        "cubic_paraconsistent_analyser_with_evidence_filter_and_temporal_analysis",
        "cubic-paraconsistent-analyser-with-evidence-filter-and-temporal-analysis",
        "cubo_analisador_paraconsistente_com_filtro_de_evidencia_e_analise_temporal",
        "cubo-analisador-paraconsistente-com-filtro-de-evidencia-e-analise-temporal",
        "cubo analisador paraconsistente com filtro de evidencia e analise temporal",
    )
    description = (
        "Executa a CPAet a partir do par de evidencias atual, do vetor temporal me_in "
        "ou de uma inicializacao bootstrap por window_size, e da margem conservadora s."
    )

    def analyze(
        self,
        favorable: float,
        contrary: float,
        moving_average_in: Sequence[float] | None = None,
        *,
        window_size: int | None = None,
        error_margin: float = DEFAULT_ERROR_MARGIN,
        bootstrap_value: float = DEFAULT_BOOTSTRAP_VALUE,
        **metadata: Any,
    ) -> CapetResult:
        evidence = EvidencePair(favorable=favorable, contrary=contrary, metadata=metadata)
        return self.run(
            self._build_input(
                evidence=evidence,
                moving_average_in=moving_average_in,
                window_size=window_size,
                error_margin=error_margin,
                bootstrap_value=bootstrap_value,
            )
        )

    def analyze_legacy(
        self,
        favorable: float,
        contrary_complement: float,
        moving_average_in: Sequence[float] | None = None,
        *,
        window_size: int | None = None,
        error_margin: float = DEFAULT_ERROR_MARGIN,
        bootstrap_value: float = DEFAULT_BOOTSTRAP_VALUE,
        **metadata: Any,
    ) -> CapetResult:
        evidence = EvidencePair.from_legacy(
            favorable=favorable,
            contrary_complement=contrary_complement,
            **metadata,
        )
        return self.run(
            self._build_input(
                evidence=evidence,
                moving_average_in=moving_average_in,
                window_size=window_size,
                error_margin=error_margin,
                bootstrap_value=bootstrap_value,
            )
        )

    def run(self, data: CapetInputPayload) -> CapetResult:
        input_data = self._coerce_input(data)
        evidence = input_data.evidence
        moving_average_in = input_data.moving_average_in
        best_values_count = len(moving_average_in)

        gc = evidence.gc
        gct = evidence.gct
        abs_gc = abs(gc)
        abs_gct = abs(gct)
        accepted_sample = abs_gc > 0.5

        if accepted_sample:
            me_out = (*moving_average_in[1:], abs_gc)
        else:
            me_out = moving_average_in

        me = sum(me_out) / best_values_count
        me_adj = max(DEFAULT_BOOTSTRAP_VALUE, me - input_data.error_margin)

        thresholds = ParaAnalyzerThresholds(certainty_limit=me_adj, contradiction_limit=1.0 - me_adj)
        state, region_id = ParaAnalyzer.classify_values(gc, gct, thresholds=thresholds)

        phi = 1.0 - abs_gct
        certainty_gap = 1.0 - abs_gc
        distance = math.sqrt((certainty_gap * certainty_gap) + (gct * gct))
        gcr = _real_certainty_degree(gc, distance)
        # Keep the legacy MATLAB boundary: phi == me_adj must remain unresolved.
        resolved = _is_strictly_greater(phi, me_adj) and distance <= 1.0
        mu_er = ((gcr + 1.0) * 0.5) if resolved else 0.5

        return CapetResult(
            algorithm=self.name,
            input=input_data,
            accepted_sample=accepted_sample,
            e=abs_gc,
            me=me,
            me_adj=me_adj,
            me_out=me_out,
            vmaxu=thresholds.c3,
            vminu=thresholds.c4,
            vmaxc=thresholds.c1,
            vminc=thresholds.c2,
            gc=gc,
            gct=gct,
            phi=phi,
            distance=distance,
            gcr=gcr,
            mu_er=mu_er,
            state=state,
            region_id=region_id,
            thresholds=thresholds,
            resolved=resolved,
        )

    def _build_input(
        self,
        *,
        evidence: EvidencePair,
        moving_average_in: Sequence[float] | None,
        window_size: int | None,
        error_margin: float,
        bootstrap_value: float,
    ) -> CapetInput:
        if moving_average_in is not None:
            return CapetInput(
                evidence=evidence,
                moving_average_in=tuple(float(value) for value in moving_average_in),
                error_margin=error_margin,
            )

        if window_size is None:
            raise ValueError("Informe moving_average_in ou window_size para inicializar a CPAet.")

        return CapetInput.bootstrap(
            evidence=evidence,
            window_size=window_size,
            error_margin=error_margin,
            bootstrap_value=bootstrap_value,
        )

    def _coerce_input(self, data: CapetInputPayload) -> CapetInput:
        if isinstance(data, CapetInput):
            return data

        if isinstance(data, tuple):
            if len(data) != 3:
                raise ValueError(
                    "A tupla de entrada da CPAet deve ter exatamente tres valores: "
                    "(favorable, contrary, moving_average_in)."
                )

            favorable, contrary, moving_average_in = data
            return CapetInput(
                evidence=EvidencePair(favorable=favorable, contrary=contrary),
                moving_average_in=tuple(float(value) for value in moving_average_in),
            )

        if isinstance(data, dict):
            if "evidence" in data:
                evidence = _coerce_evidence_payload(data["evidence"])
            else:
                evidence = _coerce_evidence_payload(data)
            moving_average_in = data.get("moving_average_in", data.get("me_in"))
            error_margin = data.get("error_margin", DEFAULT_ERROR_MARGIN)
            bootstrap_value = data.get("bootstrap_value", DEFAULT_BOOTSTRAP_VALUE)
            window_size = data.get("window_size")

            return self._build_input(
                evidence=evidence,
                moving_average_in=moving_average_in,
                window_size=window_size,
                error_margin=error_margin,
                bootstrap_value=bootstrap_value,
            )

        raise TypeError(
            "Entrada invalida para a CPAet. Use CapetInput, tupla "
            "(favorable, contrary, moving_average_in) ou dicionario com chaves reconhecidas."
        )
