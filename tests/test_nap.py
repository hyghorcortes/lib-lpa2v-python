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

from lpa2v import Nap, NapResult, available_algorithms, create_algorithm


@dataclass(frozen=True, slots=True)
class NapCase:
    title: str
    favorable: float
    contrary: float
    mi_er: float
    phi_e: float
    phi_e_partial: float
    distance: float
    mi_ctr: float
    gc: float
    gct: float
    gcr: float
    resolved: bool


NAP_CASES: tuple[NapCase, ...] = (
    NapCase("Verdade extrema", 1.00, 0.00, 1.00, 0.00, 1.00, 0.00, 0.50, 1.00, 0.00, 1.00, True),
    NapCase("Falsidade extrema", 0.00, 1.00, 0.00, 0.00, 1.00, 0.00, 0.50, -1.00, 0.00, -1.00, True),
    NapCase("Contradicao extrema", 1.00, 1.00, 0.50, 0.00, 0.00, math.sqrt(2.0), 1.00, 0.00, 1.00, 1.0 - math.sqrt(2.0), False),
    NapCase("Paracompletude extrema", 0.00, 0.00, 0.50, 0.00, 0.00, math.sqrt(2.0), 0.00, 0.00, -1.00, 1.0 - math.sqrt(2.0), False),
    NapCase("Caso resolvido com inclinacao favoravel em paracompletude", 0.70, 0.20, 0.7450490243203607, -0.90, 0.90, math.sqrt(0.26), 0.45, 0.50, -0.10, 1.0 - math.sqrt(0.26), True),
    NapCase("Caso resolvido com inclinacao contraria em contradicao", 0.40, 0.80, 0.31622776601683794, 0.80, 0.80, math.sqrt(0.40), 0.60, -0.40, 0.20, math.sqrt(0.40) - 1.0, True),
    NapCase("Caso nao resolvido por distancia acima de 1", 0.80, 0.70, 0.50, 0.50, 0.50, math.sqrt(1.06), 0.75, 0.10, 0.50, 1.0 - math.sqrt(1.06), False),
)


class NapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.algorithm = Nap()

    def assert_nap_case(self, case: NapCase) -> None:
        result = self.algorithm.analyze(case.favorable, case.contrary)
        details = (
            f"Caso: {case.title}\n"
            f"Entrada........: favorable={case.favorable:.2f}, contrary={case.contrary:.2f}\n"
            f"Esperado.......: mi_er={case.mi_er:.10f}, phi_e={case.phi_e:.10f}, "
            f"phi_e_partial={case.phi_e_partial:.10f}, D={case.distance:.10f}, "
            f"mi_ctr={case.mi_ctr:.10f}, gc={case.gc:.10f}, gct={case.gct:.10f}, "
            f"gcr={case.gcr:.10f}, resolved={case.resolved}\n"
            f"Obtido.........: mi_er={result.mi_er:.10f}, phi_e={result.phi_e:.10f}, "
            f"phi_e_partial={result.phi_e_partial:.10f}, D={result.distance:.10f}, "
            f"mi_ctr={result.mi_ctr:.10f}, gc={result.gc:.10f}, gct={result.gct:.10f}, "
            f"gcr={result.gcr:.10f}, resolved={result.resolved}"
        )

        self.assertIsInstance(result, NapResult, msg=details)
        self.assertEqual(result.algorithm, "nap", msg=details)
        self.assertAlmostEqual(result.evidence.favorable, case.favorable, places=9, msg=details)
        self.assertAlmostEqual(result.evidence.contrary, case.contrary, places=9, msg=details)
        self.assertAlmostEqual(result.mi_er, case.mi_er, places=9, msg=details)
        self.assertAlmostEqual(result.phi_e, case.phi_e, places=9, msg=details)
        self.assertAlmostEqual(result.phi_e_partial, case.phi_e_partial, places=9, msg=details)
        self.assertAlmostEqual(result.distance, case.distance, places=9, msg=details)
        self.assertAlmostEqual(result.mi_ctr, case.mi_ctr, places=9, msg=details)
        self.assertAlmostEqual(result.gc, case.gc, places=9, msg=details)
        self.assertAlmostEqual(result.gct, case.gct, places=9, msg=details)
        self.assertAlmostEqual(result.gcr, case.gcr, places=9, msg=details)
        self.assertEqual(result.lambda_value, case.contrary, msg=details)
        self.assertEqual(result.resolved, case.resolved, msg=details)

    def test_result_serialization_contains_complete_output(self) -> None:
        """Serializa o resultado do NAP com os campos principais da analise."""

        result = self.algorithm.analyze(0.70, 0.20)
        payload = result.to_dict()

        self.assertEqual(payload["algorithm"], "nap")
        self.assertIn("mi_er", payload)
        self.assertIn("phi_e", payload)
        self.assertIn("phi_e_partial", payload)
        self.assertIn("D", payload)
        self.assertIn("legacy_vector", payload)
        self.assertEqual(len(payload["legacy_vector"]), 6)

    def test_legacy_input_converts_complement_to_contrary_evidence(self) -> None:
        """Converte corretamente a entrada legada do NAP."""

        result = self.algorithm.analyze_legacy(favorable=0.70, contrary_complement=0.80)
        self.assertAlmostEqual(result.lambda_value, 0.20)
        self.assertAlmostEqual(result.mi_er, 0.7450490243203607, places=9)
        self.assertTrue(result.resolved)

    def test_legacy_vector_preserves_matlab_output_order(self) -> None:
        """Mantem a ordem da saida vetorial da implementacao MATLAB."""

        result = self.algorithm.analyze(1.0, 0.0)
        self.assertEqual(result.as_legacy_vector(), (1.0, 0.0, 1.0, 0.0, 0.5, 0.0))


def _build_nap_case_test(case: NapCase):
    def test_method(self: NapTests) -> None:
        self.assert_nap_case(case)

    test_method.__doc__ = (
        f"{case.title}: mu={case.favorable:.2f}, lambda={case.contrary:.2f}, "
        f"mi_er esperado={case.mi_er:.10f}, resolved={case.resolved}."
    )
    return test_method


for index, case in enumerate(NAP_CASES, start=1):
    test_name = f"test_case_{index:02d}"
    setattr(NapTests, test_name, _build_nap_case_test(case))


class NapRegistryTests(unittest.TestCase):
    def test_registry_lists_nap(self) -> None:
        """Lista o algoritmo NAP entre os algoritmos disponiveis."""

        self.assertIn("nap", available_algorithms())

    def test_registry_creates_nap_from_alias(self) -> None:
        """Instancia o NAP por alias do registro central."""

        algorithm = create_algorithm("no_de_analise_paraconsistente")
        self.assertIsInstance(algorithm, Nap)


def main() -> int:
    print("=" * 79)
    print("LPA2v | Suite de testes do algoritmo NAP")
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
