from __future__ import annotations

import argparse
import json

from .algorithms import available_algorithms, create_algorithm
from .algorithms.cpaet import DEFAULT_BOOTSTRAP_VALUE, DEFAULT_ERROR_MARGIN
from .algorithms.para_analyzer import ParaAnalyzerThresholds


def _add_common_evidence_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--mu", type=float, required=True, help="Evidencia favoravel.")
    parser.add_argument("--lambda", dest="lambda_value", type=float, help="Evidencia contraria.")
    parser.add_argument(
        "--contrary-complement",
        type=float,
        help="Complemento da evidencia contraria no formato legado.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lpa2v", description="Biblioteca de algoritmos baseados em LPA2v.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("algorithms", help="Lista os algoritmos disponiveis.")

    para_parser = subparsers.add_parser("para-analisador", help="Executa o algoritmo para-analisador.")
    _add_common_evidence_arguments(para_parser)
    para_parser.add_argument(
        "--certainty-limit",
        type=float,
        default=0.5,
        help="Limiar superior/inferior de certeza.",
    )
    para_parser.add_argument(
        "--contradiction-limit",
        type=float,
        default=None,
        help="Limiar superior/inferior de contradicao. Por padrao usa 1 - certainty-limit.",
    )
    para_parser.add_argument(
        "--comparison-factor",
        type=float,
        default=None,
        help="Fator de comparacao entre certeza e contradicao nas regioes intermediarias.",
    )

    nap_parser = subparsers.add_parser("nap", help="Executa o algoritmo NAP.")
    _add_common_evidence_arguments(nap_parser)

    cap_parser = subparsers.add_parser("cap", help="Executa o algoritmo CAP (Cubo Analisador Paraconsistente).")
    _add_common_evidence_arguments(cap_parser)
    cap_parser.add_argument(
        "--external-interval",
        "--phi-ext",
        dest="external_interval",
        type=float,
        required=True,
        help="Intervalo externo de evidencia (phi_ext).",
    )

    capet_parser = subparsers.add_parser("capet", help="Executa o algoritmo CAPet/CPAet.")
    _add_common_evidence_arguments(capet_parser)
    capet_parser.add_argument(
        "--moving-average-in",
        "--me-in",
        dest="moving_average_in",
        type=float,
        nargs="+",
        default=None,
        help="Vetor temporal me_in com as melhores evidencias usadas na media movel.",
    )
    capet_parser.add_argument(
        "--window-size",
        type=int,
        default=None,
        help="Tamanho da janela para inicializacao bootstrap de me_in.",
    )
    capet_parser.add_argument(
        "--error-margin",
        type=float,
        default=DEFAULT_ERROR_MARGIN,
        help="Margem conservadora s aplicada sobre a media movel.",
    )
    capet_parser.add_argument(
        "--bootstrap-value",
        type=float,
        default=DEFAULT_BOOTSTRAP_VALUE,
        help="Valor semente usado para montar me_in quando window_size e informado.",
    )
    return parser


def _resolve_evidence_payload(parser: argparse.ArgumentParser, args: argparse.Namespace, algorithm_label: str) -> dict[str, float]:
    if args.lambda_value is None and args.contrary_complement is None:
        parser.error(f"Forneca --lambda ou --contrary-complement para o {algorithm_label}.")
    if args.lambda_value is not None and args.contrary_complement is not None:
        parser.error("Use apenas um entre --lambda e --contrary-complement.")

    if args.lambda_value is not None:
        return {"mu": args.mu, "lambda": args.lambda_value}
    return {"mu": args.mu, "contrary_complement": args.contrary_complement}


def _resolve_capet_temporal_payload(parser: argparse.ArgumentParser, args: argparse.Namespace) -> dict[str, object]:
    if args.moving_average_in is None and args.window_size is None:
        parser.error("Forneca --moving-average-in/--me-in ou --window-size para o CAPet.")
    if args.moving_average_in is not None and args.window_size is not None:
        parser.error("Use apenas um entre --moving-average-in/--me-in e --window-size.")

    payload: dict[str, object] = {"error_margin": args.error_margin}
    if args.moving_average_in is not None:
        payload["moving_average_in"] = args.moving_average_in
        return payload

    payload["window_size"] = args.window_size
    payload["bootstrap_value"] = args.bootstrap_value
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "algorithms":
        print(json.dumps({"algorithms": list(available_algorithms())}, ensure_ascii=True, indent=2))
        return 0

    if args.command == "para-analisador":
        thresholds = ParaAnalyzerThresholds(
            certainty_limit=args.certainty_limit,
            contradiction_limit=args.contradiction_limit,
            comparison_factor=args.comparison_factor,
        )
        algorithm = create_algorithm("para-analisador", thresholds=thresholds)
        result = algorithm.run(_resolve_evidence_payload(parser, args, "para-analisador"))
        print(json.dumps(result.to_dict(), ensure_ascii=True, indent=2))
        return 0

    if args.command == "nap":
        algorithm = create_algorithm("nap")
        result = algorithm.run(_resolve_evidence_payload(parser, args, "NAP"))
        print(json.dumps(result.to_dict(), ensure_ascii=True, indent=2))
        return 0

    if args.command == "cap":
        algorithm = create_algorithm("cap")
        payload = _resolve_evidence_payload(parser, args, "CAP")
        payload["external_interval"] = args.external_interval
        result = algorithm.run(payload)
        print(json.dumps(result.to_dict(), ensure_ascii=True, indent=2))
        return 0

    if args.command == "capet":
        algorithm = create_algorithm("capet")
        payload = _resolve_evidence_payload(parser, args, "CAPet")
        payload.update(_resolve_capet_temporal_payload(parser, args))
        result = algorithm.run(payload)
        print(json.dumps(result.to_dict(), ensure_ascii=True, indent=2))
        return 0

    parser.error(f"Comando desconhecido: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
