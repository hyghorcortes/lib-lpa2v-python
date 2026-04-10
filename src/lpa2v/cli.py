from __future__ import annotations

import argparse
import json

from .algorithms import available_algorithms, create_algorithm
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
    return parser


def _resolve_evidence_payload(parser: argparse.ArgumentParser, args: argparse.Namespace, algorithm_label: str) -> dict[str, float]:
    if args.lambda_value is None and args.contrary_complement is None:
        parser.error(f"Forneca --lambda ou --contrary-complement para o {algorithm_label}.")
    if args.lambda_value is not None and args.contrary_complement is not None:
        parser.error("Use apenas um entre --lambda e --contrary-complement.")

    if args.lambda_value is not None:
        return {"mu": args.mu, "lambda": args.lambda_value}
    return {"mu": args.mu, "contrary_complement": args.contrary_complement}


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

    parser.error(f"Comando desconhecido: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
