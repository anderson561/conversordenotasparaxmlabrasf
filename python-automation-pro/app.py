from src.main import run_conversion, run_batch_conversion, run_contrato_conversion, parse_page_spec
from src.models.contrato_locacao_model import ContratoLocacao, EntidadeContrato
from src.utils.pdf_senha import PdfSenhaError
from src.utils.erros import NenhumCteOsError
import argparse
import sys
import json
from datetime import datetime


def _configurar_saida_console(streams=None) -> None:
    """Torna stdout/stderr tolerantes a caracteres fora da codificação do console.

    O console do Windows costuma ser cp1252 com errors="strict": um nome de PDF com
    acento em forma decomposta (ex.: "c" + U+0327, gravado por scanners) derrubava a
    conversão inteira com UnicodeEncodeError num simples print. Aqui mantemos a
    codificação do console e só trocamos o tratamento de erro para "replace" — o
    caractere sai como "?" na tela, mas a conversão segue. Não afeta caminhos de
    arquivo (só a exibição). Streams None (exe sem console) ou sem reconfigure são
    ignorados.
    """
    if streams is None:
        streams = (sys.stdout, sys.stderr)
    for stream in streams:
        if stream is None:
            continue
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            # Stream sem reconfigure (não é TextIOWrapper) ou já fechado: segue sem ajuste.
            continue


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Conversor PDF NFS-e / Contratos de Locação para ABRASF XML")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input",    help="Caminho para um único PDF")
    group.add_argument("--batch",    help="Caminho para um diretório com PDFs")
    group.add_argument("--contrato", help="Caminho para JSON com dados do contrato de locação")

    parser.add_argument("--output",  required=True, help="Caminho para o XML / Diretório de saída")
    parser.add_argument("--format",  default="abrasf", choices=["abrasf", "nfe", "cteos"],
                        help="Formato de saída para PDFs: abrasf (padrão), nfe ou cteos "
                             "(CT-e OS / DACTE OS - Modelo 67: converte só os DACTE OS do PDF "
                             "e ignora as demais páginas)")
    parser.add_argument("--pages",   help="Converter apenas páginas específicas de um PDF de várias páginas "
                                          "(só com --input). Aceita páginas soltas e intervalos, ex.: "
                                          "\"1,3,6\" ou \"1-3,6\".")
    parser.add_argument("--password", help="Senha de abertura para PDFs protegidos por senha (--input e --batch). "
                                            "ATENÇÃO: a senha digitada na linha de comando fica visível no "
                                            "histórico do terminal e na lista de processos do sistema.")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.pages and not args.input:
        parser.error("--pages só pode ser usado com --input (um único PDF).")

    if args.password and args.contrato:
        parser.error("--password só pode ser usado com --input ou --batch (PDFs).")

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
        # PDF protegido sem senha / com senha errada falha só aquele arquivo (relatório final).
        run_batch_conversion(args.batch, args.output, output_format=args.format, password=args.password)
    else:
        selected_pages = None
        if args.pages:
            selected_pages = parse_page_spec(args.pages)  # ValueError -> mensagem clara na saída
            if not selected_pages:
                parser.error("--pages não contém nenhuma página válida.")
        try:
            run_conversion(args.input, args.output, output_format=args.format,
                           selected_pages=selected_pages, password=args.password)
        except (PdfSenhaError, NenhumCteOsError) as ex:
            sys.exit(f"[ERRO] {ex}")  # mensagem clara em stderr, código de saída 1, sem traceback


if __name__ == "__main__":
    _configurar_saida_console()  # antes de qualquer saída (ver docstring)
    main()
