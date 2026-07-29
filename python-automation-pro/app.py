from src.main import run_conversion, run_batch_conversion, run_contrato_conversion, parse_page_spec
from src.models.contrato_locacao_model import ContratoLocacao, EntidadeContrato
import argparse
import sys
import json
from datetime import datetime

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Conversor PDF NFS-e / Contratos de Locação para ABRASF XML")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input",    help="Caminho para um único PDF")
    group.add_argument("--batch",    help="Caminho para um diretório com PDFs")
    group.add_argument("--contrato", help="Caminho para JSON com dados do contrato de locação")

    parser.add_argument("--output",  required=True, help="Caminho para o XML / Diretório de saída")
    parser.add_argument("--format",  default="abrasf", choices=["abrasf", "nfe"],
                        help="Formato de saída para PDFs: abrasf (padrão) ou nfe")
    parser.add_argument("--pages",   help="Converter apenas páginas específicas de um PDF de várias páginas "
                                          "(só com --input). Aceita páginas soltas e intervalos, ex.: "
                                          "\"1,3,6\" ou \"1-3,6\".")

    args = parser.parse_args()

    if args.pages and not args.input:
        parser.error("--pages só pode ser usado com --input (um único PDF).")

    if args.contrato:
        # Lê JSON com dados do contrato e gera XML
        with open(args.contrato, encoding="utf-8") as f:
            dados = json.load(f)

        # Converte data de emissão se vier como string
        if isinstance(dados.get("data_emissao"), str):
            dados["data_emissao"] = datetime.fromisoformat(dados["data_emissao"])

        contrato = ContratoLocacao(**dados)
        run_contrato_conversion(contrato, args.output)

    elif args.batch:
        run_batch_conversion(args.batch, args.output, output_format=args.format)
    else:
        selected_pages = None
        if args.pages:
            selected_pages = parse_page_spec(args.pages)  # ValueError -> mensagem clara na saída
            if not selected_pages:
                parser.error("--pages não contém nenhuma página válida.")
        run_conversion(args.input, args.output, output_format=args.format, selected_pages=selected_pages)
