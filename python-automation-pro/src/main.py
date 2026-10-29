from .extractors.pdf_extractor import SPPdfExtractor
from .transformers.abrasf_transformer import Abrasf201Transformer
from .transformers.nfe_transformer import NfeTransformer
from .transformers.nfe_produto_transformer import NfeProdutoTransformer
from .transformers.cte_transformer import CteTransformer
from .transformers.contrato_transformer import ContratoLocacaoTransformer
from .models.contrato_locacao_model import ContratoLocacao
from .models.nfe_produto_models import NfeProduto
from .models.cte_os_model import CteOS
from .utils.pdf_senha import pdf_desprotegido
from .gui_selecao import nome_xml_lote
from .utils.erros import descrever_erro, NenhumCteOsError
import os

# Opção "CT-e OS (DACTE OS - Modelo 67)" da GUI/CLI: converte SÓ os `CteOS`
# do PDF e ignora as demais páginas (NFS-e, NF-e). Nos outros formatos um
# CT-e OS continua sendo auto-roteado pelo tipo (ver `_pick_transformer`).
FORMATO_CTE_OS = "cteos"


def separar_por_formato(nfse_list, output_format: str):
    """Devolve `(mantidos, ignorados)`. Só o formato "cteos" filtra: mantém os
    `CteOS` e devolve o resto como ignorado; qualquer outro formato mantém a
    lista inteira (comportamento anterior, sem mudança). Filtro pelo TIPO do
    objeto extraído - a mesma fonte de verdade de `_pick_transformer`."""
    if output_format != FORMATO_CTE_OS:
        return list(nfse_list), []
    mantidos = [n for n in nfse_list if isinstance(n, CteOS)]
    ignorados = [n for n in nfse_list if not isinstance(n, CteOS)]
    return mantidos, ignorados


def _tipo_documento(nota) -> str:
    return "NF-e" if isinstance(nota, NfeProduto) else "NFS-e"


def mensagens_ignoradas(ignorados, prefixo: str = "") -> list:
    """Uma linha por documento ignorado pela opção CT-e OS + um resumo."""
    if not ignorados:
        return []
    msgs = []
    for n in ignorados:
        pag = getattr(n, "pagina_origem", None)
        onde = f"Página {pag}" if pag else f"Nota {getattr(n, 'numero', '?')}"
        msgs.append(
            f"[AVISO] {prefixo}{onde} não é DACTE OS (Modelo 67) — ignorada nesta opção "
            f"(reconhecida como {_tipo_documento(n)} nº {getattr(n, 'numero', '?')})"
        )
    msgs.append(f"[*] {prefixo}Opção CT-e OS: {len(ignorados)} página(s) ignorada(s) por não serem DACTE OS (Modelo 67).")
    return msgs


def _reportar(msgs, progress_callback=None, progresso: float = 0.0):
    for m in msgs:
        print(m)
        if progress_callback:
            progress_callback(progresso, m)


def _pick_transformer(nfse_obj, output_format: str):
    """Escolhe o transformer pelo TIPO real do objeto extraído, não só pelo
    dropdown escolhido: um `NfeProduto` (DANFE Estadual genuíno, ver
    LAYOUT_DANFE_PRODUTO) ou um `CteOS` (CT-e OS/DACTE OS, ver
    LAYOUT_DACTE_OS) sempre usam seu transformer real (ICMS/estadual), mesmo
    que o usuário tenha deixado o dropdown em "abrasf" - não há XML ABRASF de
    serviço possível para um documento de mercadoria nem para um CT-e, e um
    CT-e (Modelo 67) não é uma NF-e de produto (Modelo 55) - usar as tags de
    uma para representar a outra seria uma inverdade estrutural."""
    if isinstance(nfse_obj, NfeProduto):
        return NfeProdutoTransformer()
    if isinstance(nfse_obj, CteOS):
        return CteTransformer()
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


def run_conversion(pdf_path: str, output_xml_path: str, output_format: str = "abrasf", selected_pages: list = None, progress_callback=None, password: str = None):
    """`password`: senha de abertura, só necessária se o PDF for protegido.
    Sem ela (ou errada) levanta `PdfProtegidoPorSenhaError`/`PdfSenhaIncorretaError`
    (mensagem em português, nunca vazia). O PDF é aberto a partir de uma cópia
    temporária desprotegida (apagada ao final); a senha nunca é logada."""
    print(f"[*] Carregando PDF: {pdf_path}")
    with pdf_desprotegido(pdf_path, password) as pdf_legivel:
        nfse_list = SPPdfExtractor(pdf_legivel).parse_multiple()

    if not nfse_list:
        raise ValueError(
            f"O PDF '{os.path.basename(pdf_path)}' parece ser baseado em imagem/scan ou vazio. "
            "Nenhuma nota pôde ser lida."
        )

    if selected_pages is not None:
        nfse_list = [n for n in nfse_list if n.pagina_origem in selected_pages]
        if not nfse_list:
            raise ValueError("Nenhuma nota encontrada nas páginas selecionadas.")

    nfse_list, ignorados = separar_por_formato(nfse_list, output_format)
    _reportar(mensagens_ignoradas(ignorados), progress_callback)
    if not nfse_list:
        raise NenhumCteOsError(os.path.basename(pdf_path), paginas_selecionadas=selected_pages is not None)

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

def run_batch_conversion(input_dir: str = None, output_dir: str = None, pdf_files: list = None, progress_callback=None, output_format: str = "abrasf", password: str = None, senhas: dict = None, paginas_por_arquivo: dict = None):
    """`password`: senha única aplicada a todo PDF protegido do lote (CLI
    `--password`); `senhas`: dict caminho->senha por arquivo (GUI), que tem
    precedência. PDF protegido sem senha / com senha errada falha SÓ aquele
    arquivo (contabilizado em "PDFs Falhos"), sem derrubar os demais.

    `paginas_por_arquivo`: dict caminho->lista de páginas (GUI, janela de
    seleção com vários PDFs). Arquivo presente no dict converte só as notas
    dessas páginas; ausente converte todas. Os nomes dos XMLs seguem o mesmo
    padrão do lote (`nome_xml_lote`)."""
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
            with pdf_desprotegido(pdf_path, (senhas or {}).get(pdf_path, password)) as pdf_legivel:
                nfse_list = SPPdfExtractor(pdf_legivel).parse_multiple()

            if not nfse_list:
                msg = f"[AVISO] {filename} IGNORADO (Nenhuma nota fiscal reconhecida)"
                print(f"[!] {msg}")
                if progress_callback:
                    progress_callback(i / total_files, msg)
                skip_count += 1
                continue

            paginas = (paginas_por_arquivo or {}).get(pdf_path)
            if paginas is not None:
                nfse_list = [n for n in nfse_list if getattr(n, 'pagina_origem', None) in paginas]
                if not nfse_list:
                    msg = f"[AVISO] {filename} IGNORADO (Nenhuma nota nas páginas selecionadas)"
                    print(f"[!] {msg}")
                    if progress_callback:
                        progress_callback(i / total_files, msg)
                    skip_count += 1
                    continue

            nfse_list, ignorados = separar_por_formato(nfse_list, output_format)
            _reportar(mensagens_ignoradas(ignorados, prefixo=f"{filename} - "), progress_callback, i / total_files)
            if not nfse_list:
                msg = f"[AVISO] {filename} IGNORADO (Nenhum DACTE OS (Modelo 67) encontrado)"
                print(f"[!] {msg}")
                if progress_callback:
                    progress_callback(i / total_files, msg)
                skip_count += 1
                continue

            for nfse_data in nfse_list:
                num_nota = getattr(nfse_data, 'numero', '00000000')
                pag_origem = getattr(nfse_data, 'pagina_origem', None)
                xml_name = nome_xml_lote(filename, pag_origem, num_nota)
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
            print(f"[ERROR] Falha ao processar {filename}: {descrever_erro(e)}")
            if progress_callback:
                progress_callback(i / total_files, f"[ERRO] {filename}: {descrever_erro(e)}")
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
