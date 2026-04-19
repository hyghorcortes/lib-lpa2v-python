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

from lpa2v import Capet, CapetResult, ParaAnalyzerState, available_algorithms, create_algorithm


@dataclass(frozen=True, slots=True)
class CpaetCase:
    title: str
    favorable: float
    contrary: float
    moving_average_in: tuple[float, ...]
    accepted_sample: bool
    me_out: tuple[float, ...]
    me: float
    me_adj: float
    phi: float
    distance: float
    gcr: float
    resultant_evidence_degree: float
    state: ParaAnalyzerState
    region_id: int
    resolved: bool


CPAET_CASES: tuple[CpaetCase, ...] = (
    CpaetCase(
        "Amostra forte atualiza a media movel e satura em V",
        1.00,
        0.00,
        (0.50, 0.60, 0.90),
        True,
        (0.60, 0.90, 1.00),
        0.8333333333333334,
        0.6833333333333333,
        1.00,
        0.00,
        1.00,
        1.00,
        ParaAnalyzerState.V,
        10,
        True,
    ),
    CpaetCase(
        "Amostra fraca preserva a janela temporal",
        0.60,
        0.40,
        (0.50, 0.60, 0.90),
        False,
        (0.50, 0.60, 0.90),
        0.6666666666666666,
        0.5166666666666666,
        1.00,
        0.80,
        0.20,
        0.60,
        ParaAnalyzerState.QV_T,
        9,
        True,
    ),
    CpaetCase(
        "Amostra contraria forte satura em F",
        0.00,
        1.00,
        (0.70, 0.80, 0.90),
        True,
        (0.80, 0.90, 1.00),
        0.90,
        0.75,
        1.00,
        0.00,
        -1.00,
        0.00,
        ParaAnalyzerState.F,
        4,
        True,
    ),
    CpaetCase(
        "Fronteira phi igual a me_adj permanece irresolvida",
        1.00,
        0.50,
        (0.50, 0.50, 0.50),
        False,
        (0.50, 0.50, 0.50),
        0.50,
        0.50,
        0.50,
        math.sqrt(0.50),
        1.0 - math.sqrt(0.50),
        0.50,
        ParaAnalyzerState.V,
        10,
        False,
    ),
)


class CpaetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.algorithm = Capet()

    def assert_cpaet_case(self, case: CpaetCase) -> None:
        result = self.algorithm.analyze(case.favorable, case.contrary, moving_average_in=case.moving_average_in)
        details = (
            f"Caso: {case.title}\n"
            f"Entrada........: favorable={case.favorable:.2f}, contrary={case.contrary:.2f}, "
            f"me_in={case.moving_average_in}\n"
            f"Esperado.......: accepted_sample={case.accepted_sample}, me={case.me:.10f}, "
            f"me_adj={case.me_adj:.10f}, phi={case.phi:.10f}, D={case.distance:.10f}, "
            f"gcr={case.gcr:.10f}, mu_er={case.resultant_evidence_degree:.10f}, "
            f"state={case.state.value}, region={case.region_id}, resolved={case.resolved}\n"
            f"Obtido.........: accepted_sample={result.accepted_sample}, me={result.me:.10f}, "
            f"me_adj={result.me_adj:.10f}, phi={result.phi:.10f}, D={result.distance:.10f}, "
            f"gcr={result.gcr:.10f}, mu_er={result.resultant_evidence_degree:.10f}, "
            f"state={result.state.value}, region={result.region_id}, resolved={result.resolved}"
        )

        self.assertIsInstance(result, CapetResult, msg=details)
        self.assertEqual(result.algorithm, "capet", msg=details)
        self.assertEqual(result.accepted_sample, case.accepted_sample, msg=details)
        self.assertEqual(result.me_out, case.me_out, msg=details)
        self.assertAlmostEqual(result.me, case.me, places=9, msg=details)
        self.assertAlmostEqual(result.me_adj, case.me_adj, places=9, msg=details)
        self.assertAlmostEqual(result.phi, case.phi, places=9, msg=details)
        self.assertAlmostEqual(result.distance, case.distance, places=9, msg=details)
        self.assertAlmostEqual(result.gcr, case.gcr, places=9, msg=details)
        self.assertAlmostEqual(result.resultant_evidence_degree, case.resultant_evidence_degree, places=9, msg=details)
        self.assertEqual(result.state, case.state, msg=details)
        self.assertEqual(result.region_id, case.region_id, msg=details)
        self.assertEqual(result.resolved, case.resolved, msg=details)
        self.assertAlmostEqual(result.input.evidence.favorable, case.favorable, places=9, msg=details)
        self.assertAlmostEqual(result.input.evidence.contrary, case.contrary, places=9, msg=details)
        self.assertEqual(result.input.moving_average_in, case.moving_average_in, msg=details)

    def test_result_serialization_contains_complete_output(self) -> None:
        """Serializa a CPAet com os campos principais da analise temporal.""" 

        result = self.algorithm.analyze(1.00, 0.00, moving_average_in=(0.50, 0.60, 0.90))
        payload = result.to_dict()

        self.assertEqual(payload["algorithm"], "capet")
        self.assertTrue(payload["accepted_sample"])
        self.assertEqual(payload["state"], ParaAnalyzerState.V.value)
        self.assertEqual(payload["me_out"], [0.60, 0.90, 1.00])
        self.assertIn("thresholds", payload)
        self.assertIn("resultant_evidence_degree", payload)

    def test_tuple_input_accepts_temporal_vector_as_third_element(self) -> None:
        """Aceita tupla no formato (favorable, contrary, moving_average_in)."""

        result = self.algorithm.run((0.70, 0.20, (0.50, 0.50, 0.50)))
        self.assertAlmostEqual(result.input.evidence.contrary, 0.20)
        self.assertAlmostEqual(result.resultant_evidence_degree, 0.7450490243203607, places=9)
        self.assertTrue(result.resolved)

    def test_dict_input_accepts_me_in_alias_and_nested_evidence(self) -> None:
        """Aceita alias `me_in` e carga aninhada de evidencia em formato mu/lambda."""

        result = self.algorithm.run({"evidence": {"mu": 1.00, "lambda": 0.00}, "me_in": [0.50, 0.60, 0.90]})
        self.assertEqual(result.input.moving_average_in, (0.50, 0.60, 0.90))
        self.assertEqual(result.me_out, (0.60, 0.90, 1.00))
        self.assertAlmostEqual(result.resultant_evidence_degree, 1.0)

    def test_bootstrap_initializes_window_with_default_seed(self) -> None:
        """Inicializa a janela temporal com bootstrap padrao quando recebe window_size."""

        result = self.algorithm.analyze(1.00, 0.00, window_size=3)
        self.assertEqual(result.input.moving_average_in, (0.50, 0.50, 0.50))
        self.assertEqual(result.me_out, (0.50, 0.50, 1.00))
        self.assertAlmostEqual(result.me_adj, 0.5166666666666666, places=9)
        self.assertTrue(result.resolved)

    def test_legacy_input_converts_complement_to_contrary_evidence(self) -> None:
        """Converte corretamente a entrada legada com complemento da evidencia contraria."""

        result = self.algorithm.analyze_legacy(
            favorable=0.70,
            contrary_complement=0.80,
            moving_average_in=(0.50, 0.50, 0.50),
        )
        self.assertAlmostEqual(result.input.evidence.contrary, 0.20, places=9)
        self.assertAlmostEqual(result.resultant_evidence_degree, 0.7450490243203607, places=9)
        self.assertTrue(result.resolved)


def _build_cpaet_case_test(case: CpaetCase):
    def test_method(self: CpaetTests) -> None:
        self.assert_cpaet_case(case)

    test_method.__doc__ = (
        f"{case.title}: mu={case.favorable:.2f}, lambda={case.contrary:.2f}, "
        f"me_in={case.moving_average_in}, resolved={case.resolved}."
    )
    return test_method


for index, case in enumerate(CPAET_CASES, start=1):
    test_name = f"test_case_{index:02d}"
    setattr(CpaetTests, test_name, _build_cpaet_case_test(case))


class CpaetRegistryTests(unittest.TestCase):
    def test_registry_lists_capet(self) -> None:
        """Lista o nome canonico capet entre os algoritmos disponiveis."""

        self.assertIn("capet", available_algorithms())

    def test_registry_creates_capet_from_cpaet_alias(self) -> None:
        """Instancia a CPAet a partir do alias `cpaet`."""

        algorithm = create_algorithm("cpaet")
        self.assertIsInstance(algorithm, Capet)


def main() -> int:
    print("=" * 79)
    print("LPA2v | Suite de testes do algoritmo CPAet")
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
