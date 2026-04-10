from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeAlias

from ..models import EvidencePair
from .base import LPA2vAlgorithm
from .registry import registry


def _validate_unit_interval(name: str, value: float) -> float:
    numeric_value = float(value)
    if not 0.0 <= numeric_value <= 1.0:
        raise ValueError(f"{name} deve estar no intervalo [0, 1]. Valor recebido: {value!r}")
    return numeric_value


def _signed_interval(interval: float, contradiction_degree: float) -> float:
    if contradiction_degree > 0.0:
        return interval
    if contradiction_degree < 0.0:
        return -interval
    return 0.0


def _real_certainty_degree(certainty_degree: float, distance: float) -> float:
    if certainty_degree > 0.0:
        return 1.0 - distance
    if certainty_degree < 0.0:
        return distance - 1.0
    return 0.0


def _coerce_metadata(raw_metadata: Any) -> dict[str, Any]:
    if raw_metadata is None:
        return {}
    return dict(raw_metadata)


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
        "Entrada invalida para o CAP. Use EvidencePair, tupla (favorable, contrary) "
        "ou dicionario com chaves reconhecidas."
    )


@dataclass(frozen=True, slots=True)
class CapInput:
    """Entrada padrao do CAP."""

    external_interval: float
    evidence: EvidencePair

    def __post_init__(self) -> None:
        object.__setattr__(self, "external_interval", _validate_unit_interval("external_interval", self.external_interval))

    def as_dict(self) -> dict[str, Any]:
        return {
            "external_interval": self.external_interval,
            "evidence": self.evidence.as_dict(),
        }


CapInputPayload: TypeAlias = CapInput | tuple[float, float, float] | dict[str, Any]


class CapMode(str, Enum):
    EXTERNAL_INTERVAL_INSUFFICIENT = "external_interval_insufficient"
    EXTERNAL_TRUE_SATURATION = "external_true_saturation"
    EXTERNAL_FALSE_SATURATION = "external_false_saturation"
    INTERNAL_ANALYSIS = "internal_analysis"
    INTERNAL_UNCERTAINTY = "internal_uncertainty"


@dataclass(frozen=True, slots=True)
class CapResult:
    """Resultado completo do CAP (Cubo Analisador Paraconsistente)."""

    algorithm: str
    input: CapInput
    max_true_evidence: float
    max_false_evidence: float
    internal_evidence_degree: float
    internal_normalized_contradiction: float
    internal_interval: float
    internal_signed_interval: float
    internal_certainty_degree: float
    internal_contradiction_degree: float
    internal_distance: float
    certainty_degree: float | None
    contradiction_degree: float | None
    distance: float | None
    real_certainty_degree: float
    resultant_evidence_degree: float
    interval: float
    signed_interval: float
    control_mode: CapMode
    resolved: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "input": self.input.as_dict(),
            "max_true_evidence": self.max_true_evidence,
            "max_false_evidence": self.max_false_evidence,
            "internal_evidence_degree": self.internal_evidence_degree,
            "internal_normalized_contradiction": self.internal_normalized_contradiction,
            "internal_interval": self.internal_interval,
            "internal_signed_interval": self.internal_signed_interval,
            "internal_certainty_degree": self.internal_certainty_degree,
            "internal_contradiction_degree": self.internal_contradiction_degree,
            "internal_distance": self.internal_distance,
            "certainty_degree": self.certainty_degree,
            "contradiction_degree": self.contradiction_degree,
            "distance": self.distance,
            "real_certainty_degree": self.real_certainty_degree,
            "resultant_evidence_degree": self.resultant_evidence_degree,
            "interval": self.interval,
            "signed_interval": self.signed_interval,
            "control_mode": self.control_mode.value,
            "resolved": self.resolved,
        }


@registry.register
class Cap(LPA2vAlgorithm[CapInputPayload, CapResult]):
    """Implementa o CAP (Cubo Analisador Paraconsistente) controlado por intervalo externo."""

    name = "cap"
    aliases = (
        "CAP",
        "pca",
        "cubo_analisador_paraconsistente",
        "cubo-analisador-paraconsistente",
        "cubo analisador paraconsistente",
    )
    description = "Executa o CAP com um intervalo externo de evidencia e um par de evidencias internas."

    def analyze(self, external_interval: float, favorable: float, contrary: float, **metadata: Any) -> CapResult:
        return self.run(
            CapInput(
                external_interval=external_interval,
                evidence=EvidencePair(favorable=favorable, contrary=contrary, metadata=metadata),
            )
        )

    def analyze_legacy(
        self,
        external_interval: float,
        favorable: float,
        contrary_complement: float,
        **metadata: Any,
    ) -> CapResult:
        return self.run(
            CapInput(
                external_interval=external_interval,
                evidence=EvidencePair.from_legacy(
                    favorable=favorable,
                    contrary_complement=contrary_complement,
                    **metadata,
                ),
            )
        )

    def run(self, data: CapInputPayload) -> CapResult:
        input_data = self._coerce_input(data)
        evidence = input_data.evidence
        external_interval = input_data.external_interval

        max_true_evidence = (1.0 + external_interval) * 0.5
        max_false_evidence = (1.0 - external_interval) * 0.5
        internal_evidence_degree = (evidence.gc + 1.0) * 0.5
        internal_normalized_contradiction = (evidence.favorable + evidence.contrary) * 0.5
        internal_interval = 1.0 - abs((2.0 * internal_normalized_contradiction) - 1.0)
        internal_signed_interval = _signed_interval(internal_interval, evidence.gct)
        internal_distance = math.sqrt(((1.0 - abs(evidence.gc)) ** 2) + (evidence.gct**2))

        if external_interval < 0.25:
            return self._build_result(
                input_data=input_data,
                max_true_evidence=max_true_evidence,
                max_false_evidence=max_false_evidence,
                internal_evidence_degree=internal_evidence_degree,
                internal_normalized_contradiction=internal_normalized_contradiction,
                internal_interval=internal_interval,
                internal_signed_interval=internal_signed_interval,
                internal_distance=internal_distance,
                certainty_degree=None,
                contradiction_degree=None,
                distance=None,
                interval=external_interval,
                signed_interval=external_interval if external_interval > 0.0 else 0.0,
                control_mode=CapMode.EXTERNAL_INTERVAL_INSUFFICIENT,
                resolved=False,
            )

        if internal_evidence_degree >= max_true_evidence:
            certainty_degree = external_interval
            contradiction_degree = 1.0 - external_interval
            distance = math.sqrt(((1.0 - abs(certainty_degree)) ** 2) + (contradiction_degree**2))
            return self._build_result(
                input_data=input_data,
                max_true_evidence=max_true_evidence,
                max_false_evidence=max_false_evidence,
                internal_evidence_degree=internal_evidence_degree,
                internal_normalized_contradiction=internal_normalized_contradiction,
                internal_interval=internal_interval,
                internal_signed_interval=internal_signed_interval,
                internal_distance=internal_distance,
                certainty_degree=certainty_degree,
                contradiction_degree=contradiction_degree,
                distance=distance,
                interval=external_interval,
                signed_interval=external_interval,
                control_mode=CapMode.EXTERNAL_TRUE_SATURATION,
                resolved=True,
            )

        if internal_evidence_degree <= max_false_evidence:
            certainty_degree = -external_interval
            contradiction_degree = 1.0 - external_interval
            distance = math.sqrt(((1.0 - abs(certainty_degree)) ** 2) + (contradiction_degree**2))
            return self._build_result(
                input_data=input_data,
                max_true_evidence=max_true_evidence,
                max_false_evidence=max_false_evidence,
                internal_evidence_degree=internal_evidence_degree,
                internal_normalized_contradiction=internal_normalized_contradiction,
                internal_interval=internal_interval,
                internal_signed_interval=internal_signed_interval,
                internal_distance=internal_distance,
                certainty_degree=certainty_degree,
                contradiction_degree=contradiction_degree,
                distance=distance,
                interval=external_interval,
                signed_interval=external_interval,
                control_mode=CapMode.EXTERNAL_FALSE_SATURATION,
                resolved=True,
            )

        if internal_interval < 0.25 or internal_distance > 1.0:
            return self._build_result(
                input_data=input_data,
                max_true_evidence=max_true_evidence,
                max_false_evidence=max_false_evidence,
                internal_evidence_degree=internal_evidence_degree,
                internal_normalized_contradiction=internal_normalized_contradiction,
                internal_interval=internal_interval,
                internal_signed_interval=internal_signed_interval,
                internal_distance=internal_distance,
                certainty_degree=None,
                contradiction_degree=None,
                distance=None,
                interval=internal_interval,
                signed_interval=internal_signed_interval,
                control_mode=CapMode.INTERNAL_UNCERTAINTY,
                resolved=False,
            )

        return self._build_result(
            input_data=input_data,
            max_true_evidence=max_true_evidence,
            max_false_evidence=max_false_evidence,
            internal_evidence_degree=internal_evidence_degree,
            internal_normalized_contradiction=internal_normalized_contradiction,
            internal_interval=internal_interval,
            internal_signed_interval=internal_signed_interval,
            internal_distance=internal_distance,
            certainty_degree=evidence.gc,
            contradiction_degree=evidence.gct,
            distance=internal_distance,
            interval=internal_interval,
            signed_interval=internal_signed_interval,
            control_mode=CapMode.INTERNAL_ANALYSIS,
            resolved=True,
        )

    def _build_result(
        self,
        *,
        input_data: CapInput,
        max_true_evidence: float,
        max_false_evidence: float,
        internal_evidence_degree: float,
        internal_normalized_contradiction: float,
        internal_interval: float,
        internal_signed_interval: float,
        internal_distance: float,
        certainty_degree: float | None,
        contradiction_degree: float | None,
        distance: float | None,
        interval: float,
        signed_interval: float,
        control_mode: CapMode,
        resolved: bool,
    ) -> CapResult:
        if certainty_degree is None or distance is None:
            real_certainty_degree = 0.0
            resultant_evidence_degree = 0.5
        else:
            real_certainty_degree = _real_certainty_degree(certainty_degree, distance)
            resultant_evidence_degree = (real_certainty_degree + 1.0) * 0.5

        return CapResult(
            algorithm=self.name,
            input=input_data,
            max_true_evidence=max_true_evidence,
            max_false_evidence=max_false_evidence,
            internal_evidence_degree=internal_evidence_degree,
            internal_normalized_contradiction=internal_normalized_contradiction,
            internal_interval=internal_interval,
            internal_signed_interval=internal_signed_interval,
            internal_certainty_degree=input_data.evidence.gc,
            internal_contradiction_degree=input_data.evidence.gct,
            internal_distance=internal_distance,
            certainty_degree=certainty_degree,
            contradiction_degree=contradiction_degree,
            distance=distance,
            real_certainty_degree=real_certainty_degree,
            resultant_evidence_degree=resultant_evidence_degree,
            interval=interval,
            signed_interval=signed_interval,
            control_mode=control_mode,
            resolved=resolved,
        )

    def _coerce_input(self, data: CapInputPayload) -> CapInput:
        if isinstance(data, CapInput):
            return data

        if isinstance(data, tuple):
            if len(data) != 3:
                raise ValueError(
                    "A tupla de entrada do CAP deve ter exatamente tres valores: "
                    "(external_interval, favorable, contrary)."
                )
            external_interval, favorable, contrary = data
            return CapInput(
                external_interval=float(external_interval),
                evidence=EvidencePair(favorable=favorable, contrary=contrary),
            )

        if isinstance(data, dict):
            external_interval = self._extract_external_interval(data)

            if "evidence" in data:
                evidence = _coerce_evidence_payload(data["evidence"])
            else:
                evidence = _coerce_evidence_payload(data)

            return CapInput(external_interval=external_interval, evidence=evidence)

        raise TypeError(
            "Entrada invalida para o CAP. Use CapInput, tupla "
            "(external_interval, favorable, contrary) ou dicionario com chaves reconhecidas."
        )

    def _extract_external_interval(self, data: dict[str, Any]) -> float:
        if "external_interval" in data:
            return _validate_unit_interval("external_interval", data["external_interval"])
        if "phi_ext" in data:
            return _validate_unit_interval("phi_ext", data["phi_ext"])
        if "external_signed_interval" in data:
            return _validate_unit_interval("external_signed_interval", abs(float(data["external_signed_interval"])))
        if "phi_e" in data:
            return _validate_unit_interval("phi_e", abs(float(data["phi_e"])))
        raise TypeError(
            "Entrada invalida para o CAP. Informe external_interval, phi_ext, external_signed_interval ou phi_e."
        )