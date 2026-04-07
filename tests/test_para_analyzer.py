from __future__ import annotations

import sys
import unittest
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lpa2v import EvidencePair, ParaAnalyzer, ParaAnalyzerState, available_algorithms, create_algorithm


@dataclass(frozen=True, slots=True)
class AnalysisCase:
    title: str
    favorable: float
    contrary: float
    expected_state: ParaAnalyzerState
    expected_region: int

    @property
    def gc(self) -> float:
        return self.favorable - self.contrary

    @property
    def gct(self) -> float:
        return self.favorable + self.contrary - 1.0


ANALYSIS_CASES: tuple[AnalysisCase, ...] = (
    AnalysisCase("Verdade extrema", 1.00, 0.00, ParaAnalyzerState.V, 10),
    AnalysisCase("Falsidade extrema", 0.00, 1.00, ParaAnalyzerState.F, 4),
    AnalysisCase("Contradicao extrema", 1.00, 1.00, ParaAnalyzerState.T, 7),
    AnalysisCase("Paracompletude extrema", 0.00, 0.00, ParaAnalyzerState.NOT_T, 1),
    AnalysisCase("Quadrante positivo-positivo com predominio da certeza", 0.70, 0.30, ParaAnalyzerState.QV_T, 9),
    AnalysisCase("Quadrante positivo-positivo com predominio da contradicao", 0.80, 0.55, ParaAnalyzerState.QT_V, 8),
    AnalysisCase("Quadrante positivo-negativo com predominio da certeza", 0.60, 0.30, ParaAnalyzerState.QV_NOT_T, 11),
    AnalysisCase("Quadrante positivo-negativo com predominio da paracompletude", 0.35, 0.30, ParaAnalyzerState.QNOT_T_V, 12),
    AnalysisCase("Quadrante negativo-positivo com predominio da falsidade", 0.40, 0.60, ParaAnalyzerState.QF_T, 5),
    AnalysisCase("Quadrante negativo-positivo com predominio da contradicao", 0.55, 0.65, ParaAnalyzerState.QT_F, 6),
    AnalysisCase("Quadrante negativo-negativo com predominio da falsidade", 0.30, 0.60, ParaAnalyzerState.QF_NOT_T, 3),
    AnalysisCase("Quadrante negativo-negativo com predominio da paracompletude", 0.25, 0.35, ParaAnalyzerState.QNOT_T_F, 2),
)


class ParaAnalyzerStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.algorithm = ParaAnalyzer()

    def assert_analysis_case(self, case: AnalysisCase) -> None:
        result = self.algorithm.run(EvidencePair(favorable=case.favorable, contrary=case.contrary))
        details = (
            f"Caso: {case.title}\n"
            f"Entrada........: favorable={case.favorable:.2f}, contrary={case.contrary:.2f}\n"
            f"Esperado.......: state={case.expected_state.value}, region={case.expected_region}, "
            f"gc={case.gc:.4f}, gct={case.gct:.4f}\n"
            f"Obtido.........: state={result.state.value}, region={result.region_id}, "
            f"gc={result.gc:.4f}, gct={result.gct:.4f}"
        )

        self.assertEqual(result.algorithm, "para-analisador", msg=details)
        self.assertEqual(result.state, case.expected_state, msg=details)
        self.assertEqual(result.region_id, case.expected_region, msg=details)
        self.assertAlmostEqual(result.gc, case.gc, places=9, msg=details)
        self.assertAlmostEqual(result.gct, case.gct, places=9, msg=details)
        self.assertAlmostEqual(result.evidence.favorable, case.favorable, places=9, msg=details)
        self.assertAlmostEqual(result.evidence.contrary, case.contrary, places=9, msg=details)

    def test_result_serialization_contains_main_fields(self) -> None:
        """Serializa o resultado com os campos principais esperados."""

        result = self.algorithm.analyze(0.80, 0.55)
        payload = result.to_dict()

        self.assertEqual(payload["algorithm"], "para-analisador")
        self.assertEqual(payload["state"], ParaAnalyzerState.QT_V.value)
        self.assertEqual(payload["region_id"], 8)
        self.assertIn("evidence", payload)
        self.assertIn("thresholds", payload)

    def test_legacy_input_converts_complement_to_contrary_evidence(self) -> None:
        """Converte corretamente a entrada legada com complemento da evidencia contraria."""

        result = self.algorithm.analyze_legacy(favorable=0.7, contrary_complement=0.55)
        self.assertAlmostEqual(result.evidence.contrary, 0.45)
        self.assertEqual(result.state, ParaAnalyzerState.QV_T)
        self.assertEqual(result.region_id, 9)


def _build_analysis_case_test(case: AnalysisCase):
    def test_method(self: ParaAnalyzerStateTests) -> None:
        self.assert_analysis_case(case)

    test_method.__doc__ = (
        f"{case.title}: mu={case.favorable:.2f}, lambda={case.contrary:.2f}, "
        f"estado esperado={case.expected_state.value}, regiao={case.expected_region}."
    )
    return test_method


for index, case in enumerate(ANALYSIS_CASES, start=1):
    test_name = f"test_case_{index:02d}"
    setattr(ParaAnalyzerStateTests, test_name, _build_analysis_case_test(case))


class RegistryTests(unittest.TestCase):
    def test_registry_lists_canonical_name(self) -> None:
        """Lista o nome canonico do para-analisador no registro da biblioteca."""

        self.assertIn("para-analisador", available_algorithms())

    def test_registry_creates_algorithm_from_alias(self) -> None:
        """Instancia o algoritmo a partir de um alias registrado."""

        algorithm = create_algorithm("para_analyzer")
        self.assertIsInstance(algorithm, ParaAnalyzer)


def main() -> int:
    print("=" * 79)
    print("LPA2v | Suite de testes do algoritmo para-analisador")
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
