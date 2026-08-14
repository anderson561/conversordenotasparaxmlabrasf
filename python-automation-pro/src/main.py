from .extractors.pdf_extractor import SPPdfExtractor
from .transformers.abrasf_transformer import Abrasf201Transformer
from .transformers.nfe_transformer import NfeTransformer
from .transformers.nfe_produto_transformer import NfeProdutoTransformer
from .transformers.contrato_transformer import ContratoLocacaoTransformer
from .models.contrato_locacao_model import ContratoLocacao
from .models.nfe_produto_models import NfeProduto
import os


def _pick_transformer(nfse_obj, output_format: str):
    """Escolhe o transformer pelo TIPO real do objeto extraído, não só pelo
    dropdown escolhido: um `NfeProduto` (DANFE Estadual genuíno, ver
    LAYOUT_DANFE_PRODUTO) sempre usa o transformer de produto real, mesmo que
    o usuário tenha deixado o dropdown em "abrasf" - não há XML ABRASF de
    serviço possível para um documento de mercadoria."""
    if isinstance(nfse_obj, NfeProduto):
        return NfeProdutoTransformer()
    return Abrasf201Transformer() if output_format == "abrasf" else NfeTransformer()


def parse_page_spec(spec: str) -> list:
    """Converte uma especificação de páginas do usuário numa lista ordenada de
    páginas (1-based, únicas). Aceita páginas soltas e intervalos, separados por
    vírgula — ex.: "1,3,6" -> [1, 3, 6]; "1-3,6" -> [1, 2, 3, 6]. Tokens vazios
    são ignorados; um intervalo com limites invertidos ("6-1") é normalizado.

    Levanta ValueError (com mensagem clara) em token não-numérico ou página < 1.
    """
    if not spec or not spec.strip():
        return []
    paginas = set()
    for token in spec.split(','):
        token = token.strip()
        if not token:
            continue
        try:
            if '-' in token:
                ini_str, fim_str = token.split('-', 1)
                ini, fim = int(ini_str), int(fim_str)
                if ini > fim:
                    ini, fim = fim, ini
                if ini < 1:
                    raise ValueError
                paginas.update(range(ini, fim + 1))
            else:
                p = int(token)
                if p < 1:
                    raise ValueError
                paginas.add(p)
        except ValueError:
            raise ValueError(
                f"Especificação de páginas inválida: '{token}'. "
                "Use páginas ≥ 1 separadas por vírgula, ex.: \"1,3,6\" ou \"1-3,6\"."
            )
    return sorted(paginas)


def run_conversion(pdf_path: str, output_xml_path: str, output_format: str = "abrasf", selected_pages: list = None, progress_callback=None):
    print(f"[*] Carregando PDF: {pdf_path}")
    extractor = SPPdfExtractor(pdf_path)

    nfse_list = extractor.parse_multiple()

    if not nfse_list:
        raise ValueError(
            f"O PDF '{os.path.basename(pdf_path)}' parece ser baseado em imagem/scan ou vazio. "
            "Nenhuma nota pôde ser lida."
        )

    if selected_pages is not None:
        nfse_list = [n for n in nfse_list if n.pagina_origem in selected_pages]
        if not nfse_list:
            raise ValueError("Nenhuma nota encontrada nas páginas selecionadas.")

    print(f"[*] Transformando para {output_format.upper()}...")
    os.makedirs(os.path.dirname(output_xml_path), exist_ok=True)

    base_dir = os.path.dirname(output_xml_path)
    base_name = os.path.basename(output_xml_path)
    name_no_ext = base_name.rsplit('.', 1)[0]

    for nfse in nfse_list:
        transformer = _pick_transformer(nfse, output_format)
        xml_content = transformer.transform(nfse)
        pag_origem = getattr(nfse, 'pagina_origem', None)
        pag_str = f"_Pagina_{pag_origem}" if pag_origem else ""
        xml_name = f"{name_no_ext}{pag_str}_NF_{nfse.numero}.xml"
        xml_path = os.path.join(base_dir, xml_name)
        
        print(f"[*] Salvando XML: {xml_path}")
        with open(xml_path, "w", encoding="utf-8") as f:
            f.write(xml_content)

        if nfse.avisos:
            msg = f"[AVISO] Nota {nfse.numero}" + (f" (pág {pag_origem})" if pag_origem else "") + f": {'; '.join(nfse.avisos)}"
            print(msg)
            if progress_callback:
                progress_callback(1.0, msg)

    print(f"[+] Conversão concluída com sucesso! ({len(nfse_list)} notas extraídas)")

def run_batch_conversion(input_dir: str = None, output_dir: str = None, pdf_files: list = None, progress_callback=None, output_format: str = "abrasf"):
    if pdf_files:
        files_to_process = pdf_files
        print(f"[*] Iniciando conversão de {len(pdf_files)} arquivos selecionados.")
    elif input_dir:
        print(f"[*] Iniciando conversão em lote do diretório: {input_dir}")
        files_to_process = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    else:
        raise ValueError("É necessário fornecer um diretório de entrada ou uma lista de arquivos.")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    total_files = len(files_to_process)
    print(f"[*] Total de {total_files} arquivos PDF para processar.")

    success_count = 0
    fail_count = 0
    skip_count = 0

    for i, pdf_path in enumerate(files_to_process):
        filename = os.path.basename(pdf_path)

        if progress_callback:
            progress_callback(i / total_files, f"Processando: {filename}")

        try:
            extractor = SPPdfExtractor(pdf_path)
            nfse_list = extractor.parse_multiple()

            if not nfse_list:
                msg = f"[AVISO] {filename} IGNORADO (Nenhuma nota fiscal reconhecida)"
                print(f"[!] {msg}")
                if progress_callback:
                    progress_callback(i / total_files, msg)
                skip_count += 1
                continue

            base_filename = filename.rsplit('.', 1)[0]
            
            for nfse_data in nfse_list:
                num_nota = getattr(nfse_data, 'numero', '00000000')
                pag_origem = getattr(nfse_data, 'pagina_origem', None)
                pag_str = f"_Pagina_{pag_origem}" if pag_origem else ""
                xml_name = f"{base_filename}{pag_str}_NF_{num_nota}.xml"
                output_xml_path = os.path.join(output_dir, xml_name)
                transformer = _pick_transformer(nfse_data, output_format)
                xml_content = transformer.transform(nfse_data)
                with open(output_xml_path, "w", encoding="utf-8") as f:
                    f.write(xml_content)

                if getattr(nfse_data, 'avisos', None):
                    msg = f"[AVISO] {filename} - Nota {num_nota}" + (f" (pág {pag_origem})" if pag_origem else "") + f": {'; '.join(nfse_data.avisos)}"
                    print(msg)
                    if progress_callback:
                        progress_callback(i / total_files, msg)

            success_count += len(nfse_list)

            print(f"[+] Gerados {len(nfse_list)} XMLs para: {filename}")

            if progress_callback:
                progress_callback(i / total_files, f"[+] {filename} -> {len(nfse_list)} XMLs Gerados!")
        except Exception as e:
            print(f"[ERROR] Falha ao processar {filename}: {str(e)}")
            if progress_callback:
                progress_callback(i / total_files, f"[ERRO] {filename}: {str(e)}")
            fail_count += 1

    if progress_callback:
        progress_callback(1.0, f"Concluído! {success_count} Notas convertidas | {skip_count} PDFs Ignorados | {fail_count} PDFs Falhos")

    print("\n" + "="*40)
    print(f"Relatório Final:")
    print(f"  - Notas Geradas (XMLs): {success_count}")
    print(f"  - PDFs Ignorados: {skip_count}")
    print(f"  - PDFs com Falha Total: {fail_count}")
    print("="*40)


def run_contrato_conversion(
    contrato: ContratoLocacao,
    output_dir: str,
    progress_callback=None
) -> str:
    """
    Gera um XML ABRASF 2.01 a partir de um ContratoLocacao.
    Retorna o caminho do arquivo gerado.
    """
    if progress_callback:
        progress_callback(0.2, "[*] Gerando XML do contrato de locação...")

    transformer = ContratoLocacaoTransformer()
    xml_content = transformer.transform(contrato)

    os.makedirs(output_dir, exist_ok=True)
    ano = contrato.data_emissao.year
    xml_name = f"CONTRATO_LOCACAO_{ano}.xml"
    output_path = os.path.join(output_dir, xml_name)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(xml_content)

    print(f"[+] Contrato XML gerado: {output_path}")

    if progress_callback:
        progress_callback(1.0, f"[+] Concluído! XML salvo: {xml_name}")

    return output_path
