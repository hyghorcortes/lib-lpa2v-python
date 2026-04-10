from __future__ import annotations

import math
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lpa2v import Cap, CapMode, CapResult, available_algorithms, create_algorithm


@dataclass(frozen=True, slots=True)
class CapCase:
    title: str
    external_interval: float
    favorable: float
    contrary: float
    control_mode: CapMode
    resolved: bool
    resultant_evidence_degree: float
    signed_interval: float
    certainty_degree: float | None
    contradiction_degree: float | None


CAP_CASES: tuple[CapCase, ...] = (
    CapCase(
        "Incerteza por intervalo externo insuficiente",
        0.20,
        0.80,
        0.10,
        CapMode.EXTERNAL_INTERVAL_INSUFFICIENT,
        False,
        0.50,
        0.20,
        None,
        None,
    ),
    CapCase(
        "Saturacao externa tendendo ao verdadeiro",
        0.60,
        1.00,
        0.00,
        CapMode.EXTERNAL_TRUE_SATURATION,
        True,
        0.717157287525381,
        0.60,
        0.60,
        0.40,
    ),
    CapCase(
        "Saturacao externa tendendo ao falso",
        0.60,
        0.00,
        1.00,
        CapMode.EXTERNAL_FALSE_SATURATION,
        True,
        0.282842712474619,
        0.60,
        -0.60,
        0.40,
    ),
    CapCase(
        "Analise interna regular",
        0.60,
        0.70,
        0.20,
        CapMode.INTERNAL_ANALYSIS,
        True,
        0.7450490243203607,
        -0.90,
        0.50,
        -0.10,
    ),
    CapCase(
        "Incerteza interna por distancia acima de 1",
        0.60,
        0.80,
        0.70,
        CapMode.INTERNAL_UNCERTAINTY,
        False,
        0.50,
        0.50,
        None,
        None,
    ),
)


class CapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.algorithm = Cap()

    def assert_cap_case(self, case: CapCase) -> None:
        result = self.algorithm.analyze(case.external_interval, case.favorable, case.contrary)
        details = (
            f"Caso: {case.title}\n"
            f"Entrada........: phi_ext={case.external_interval:.2f}, "
            f"favorable={case.favorable:.2f}, contrary={case.contrary:.2f}\n"
            f"Esperado.......: mode={case.control_mode.value}, resolved={case.resolved}, "
            f"mu_er={case.resultant_evidence_degree:.10f}, phi={case.signed_interval:.10f}\n"
            f"Obtido.........: mode={result.control_mode.value}, resolved={result.resolved}, "
            f"mu_er={result.resultant_evidence_degree:.10f}, phi={result.signed_interval:.10f}"
        )

        self.assertIsInstance(result, CapResult, msg=details)
        self.assertEqual(result.algorithm, "cap", msg=details)
        self.assertEqual(result.control_mode, case.control_mode, msg=details)
        self.assertEqual(result.resolved, case.resolved, msg=details)
        self.assertAlmostEqual(result.resultant_evidence_degree, case.resultant_evidence_degree, places=9, msg=details)
        self.assertAlmostEqual(result.signed_interval, case.signed_interval, places=9, msg=details)
        self.assertAlmostEqual(result.input.external_interval, case.external_interval, places=9, msg=details)
        self.assertAlmostEqual(result.input.evidence.favorable, case.favorable, places=9, msg=details)
        self.assertAlmostEqual(result.input.evidence.contrary, case.contrary, places=9, msg=details)

        if case.certainty_degree is None:
            self.assertIsNone(result.certainty_degree, msg=details)
        else:
            self.assertAlmostEqual(result.certainty_degree, case.certainty_degree, places=9, msg=details)

        if case.contradiction_degree is None:
            self.assertIsNone(result.contradiction_degree, msg=details)
        else:
            self.assertAlmostEqual(result.contradiction_degree, case.contradiction_degree, places=9, msg=details)

    def test_result_serialization_contains_complete_output(self) -> None:
        """Serializa o CAP com campos operacionais e diagnosticos principais."""

        result = self.algorithm.analyze(0.60, 1.00, 0.00)
        payload = result.to_dict()

        self.assertEqual(payload["algorithm"], "cap")
        self.assertEqual(payload["control_mode"], CapMode.EXTERNAL_TRUE_SATURATION.value)
        self.assertIn("input", payload)
        self.assertIn("internal_interval", payload)
        self.assertIn("resultant_evidence_degree", payload)

    def test_tuple_input_uses_external_interval_first(self) -> None:
        """Aceita tupla no formato (external_interval, favorable, contrary)."""

        result = self.algorithm.run((0.60, 0.70, 0.20))
        self.assertEqual(result.control_mode, CapMode.INTERNAL_ANALYSIS)
        self.assertAlmostEqual(result.resultant_evidence_degree, 0.7450490243203607, places=9)

    def test_legacy_input_converts_complement_to_contrary_evidence(self) -> None:
        """Converte corretamente a entrada legada do CAP."""

        result = self.algorithm.analyze_legacy(0.60, favorable=0.70, contrary_complement=0.80)
        self.assertEqual(result.control_mode, CapMode.INTERNAL_ANALYSIS)
        self.assertAlmostEqual(result.input.evidence.contrary, 0.20)
        self.assertAlmostEqual(result.resultant_evidence_degree, 0.7450490243203607, places=9)

    def test_false_saturation_matches_expected_distance(self) -> None:
        """Mantem a geometria da saturacao externa no ramo falso."""

        result = self.algorithm.analyze(0.60, 0.00, 1.00)
        self.assertAlmostEqual(result.distance or 0.0, math.sqrt(0.32), places=9)
        self.assertAlmostEqual(result.real_certainty_degree, math.sqrt(0.32) - 1.0, places=9)


def _build_cap_case_test(case: CapCase):
    def test_method(self: CapTests) -> None:
        self.assert_cap_case(case)

    test_method.__doc__ = (
        f"{case.title}: phi_ext={case.external_interval:.2f}, mu={case.favorable:.2f}, "
        f"lambda={case.contrary:.2f}, mode={case.control_mode.value}."
    )
    return test_method


for index, case in enumerate(CAP_CASES, start=1):
    test_name = f"test_case_{index:02d}"
    setattr(CapTests, test_name, _build_cap_case_test(case))


class CapRegistryTests(unittest.TestCase):
    def test_registry_lists_cap(self) -> None:
        """Lista o CAP entre os algoritmos disponiveis."""

        self.assertIn("cap", available_algorithms())

    def test_registry_creates_cap_from_alias(self) -> None:
        """Instancia o CAP por alias do registro central."""

        algorithm = create_algorithm("cubo_analisador_paraconsistente")
        self.assertIsInstance(algorithm, Cap)


def main() -> int:
    print("=" * 79)
    print("LPA2v | Suite de testes do algoritmo CAP")
    print("=" * 79)
    print(f"Projeto : {ROOT}")
    print(f"Python  : {sys.version.split()[0]}")
    print("-" * 79)

    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2, stream=sys.stdout).run(suite)

    print("-" * 79)
    print("Resumo da execucao")
    print(f"Testes executados : {result.testsRun}")
    print(f"Falhas           : {len(result.failures)}")
    print(f"Erros            : {len(result.errors)}")
    print(f"Ignorados        : {len(result.skipped)}")
    print(f"Status final     : {'SUCESSO' if result.wasSuccessful() else 'FALHA'}")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
