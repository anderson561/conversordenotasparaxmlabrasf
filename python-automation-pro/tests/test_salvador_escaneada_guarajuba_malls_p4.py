# -*- coding: utf-8 -*-
"""Salvador/BA ESCANEADA — nota real nº 00009925, METROFILE BRASIL GESTAO DA
INFORMACAO LTDA. -> GUARAJUBA MALLS S/A (R$514,82, armazenamento, "GUARAJUBA
MALLS - NFSe.pdf", pág. 4; impressão pelo navegador, com URL e margens no
topo).

O scan FECHA a barriga do "5" e o Tesseract o lê "6" em toda leitura
(página inteira e recortes em zoom 3-8x): CNPJ do prestador "03.301.926/
0008-37" (impresso ...925...), do tomador "24.890.396/0001-03" (...395...),
Base "614,82" (514,82), ISS "26,74" (25,74), endereço "1660" (1650). Antes:
os dois CNPJs no sentinela, razão social "METROFILE ... LTDA. Neto eres
Nome/Razão Social METROFILE ..." (logotipo colado + a razão recortada
emendada de novo), IM "00646", Código de Verificação "NOTAFISCALDESERVI"
(o recorte da linha do código, calculado a 16% da altura, cortava a linha
pelo meio nesta impressão), ISS 26,74 com aviso de divergência.

MOCK_OCR é cópia literal de `SPPdfExtractor._ocr_page(3)` da nota real, já
com os recortes Salvador desta correção (código "8PZ3-P2RH" prependido,
CNPJs corrigidos 6->5 pelo DV, endereço relido "1650", razão recortada no
lugar do trecho poluído, marcador `SSA_DIGITO_5_LIDO_6` e as leituras da
célula do ISS)."""
import os

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor

PDF_REAL = r"L:\USUARIOS\ANDERSON\ARQUIVOS DESKTOP\Notas\GUARAJUBA MALLS - NFSe.pdf"

MOCK_OCR = 'Código de Verificação:\n8PZ3-P2RH\n\nBASE_CALCULO_RECUPERADA: 614,82\nTOMADOR DE SERVIÇOS\n\nNormie/Razão Social:\n\nGUARAJUBA MALLS S/A\n\nCPF/CNPJ: Inscrição Municipal:\n\n24.890.395/0001-03 en\n\nEndereço:\n\nROD BA 099 ESTRADA DO COCO SN, ALAMEDA DAS DUNAS GUARAJUBA (MONTE GORDO) - Camaçari - CEP: 42840-310/BA\n\nSUMASÃR DER SERVIÇOS\n\nNumero de memorial de servico 2623581\nvencimento 10/08/2026\n\nVALOR TOTAL DA NOTA = R$514,82\nCNAE:\n6211799 - Depósitos de mercadorias para terceiros, exceto armazéns gerais e guarda-móveis\n\nItem da Lista de Serviços:\n01104 - Armazenamento, depósito, carga, descarga, arrumação e guarda de bens de qualquer espécie.\n\nValor Total das Deduções (R$): | Base de Cálculo (R$): Aliquota (%); Crédito Nota Salvador (R$):\nii iscas dai DO 6,00% 26,74 0,00\n\nValor PIS ROO Valor COFINS (8% | Valor re IR (R$) Valor CSLL (R$): Valor Líquido (R$);\n0,00] 0,00 9,00 0,00 0,00 614,82\n\nOUTRAS INFORMAÇÕES\n\n- Esta Nota Salvador foi emitida com respaldo na Lei 7.186/2008.\n\n- Data de vencimento do ISS desta Nota Salvador: 05/08/2026\n\n- COMPETÊNCIA; 07/2026 (més/ano)\n\n- Código de Tributação do Município: 1104-0/01 - Armazenamento, depósito e guarda de bens de qualquer espécie\n\nTIO KO catro tony)\n\nlofl 21/07/2026, 12:\nNúmero da Nota:\n00009925\n\nalvador.ba.gov.br/site/contribuinte/nota/notaprint.aspx?insc...\nNúmero da Nota:\n\nJOR 00009925\nData e Hora de Emissão:\n21/07/2026 10:37:53\n\nMES coca, fo junricaçõos\n\nSalvador\n\nlofl\n\nhttps://nfse.salvador.ba. gov.br/site/contribuinte/nota/notaprint.aspx?insc...\n\nú da Nota:\nDooUasas No\n\nPREFEITURA MUNICIPAL DO SALVADOR\n\nHora de Emissão:\nSECRETARIA MUNICIPAL DA FAZENDA 5 Data dido 10:57:53\n\nCódigo de Verificação:\nNOTA FISCAL DE SERVIÇOS ELETRÔNICA - Nota Salvador SPLSPIRH\n\nPRESTADOR DE SERVIÇOS\n\nCPF/CNPJ: Inscrição Municipal:\n\n03.301.925/0008-37 00.646. 776/001-57\n\nNome/Razão Social:\nMETROFILE BRASIL GESTAO DA INFORMACAO LTDA.\nEndereço:\nRua Doutor Altino Teixeira 1650 - PORTO SECO PIRAJA - Salvador - CEP: 41233-010 - BA\n\nF CIADOR DES SERVIÇOS\n\nNome/Razão Social;\n\nGUARAJUBA MALLS S/A\n\nCPF/CNPJ: Inscrição Municipal:\n\n24.890.395/0001-03 e\n\nEndereço:\n\nROD BA 099 ESTRADA DO COCO SN, ALAMEDA DAS DUNAS GUARAJUBA (MONTE GORDO) - Camaçari - CEP: 42840-S10/BA\n\nE S SE Vig Ss\nPBiiS Ur p SERVE Ê.\nNumero de memorial de ia 2623581\nvencimento 10/08/2026\n\nVALOR TOTAL DA NOTA = R$514,82\nCNAE:\n6211799 - Depósitos de mercadorias para terceiros, exceto armazéns gerais e guarda-móveis\n\nItem da Lista de Serviços:\n\n01104 - Armazenamento, depósito, carga, descarga, arrumação e guarda de bens de qualquer espécie.\n\nValor Total das Deduções (R$): Base de Cálculo (R$): Aliquota (%): Valor do ISS (R$): Crédito Nota Salvador (R$):\n0,00 614,82 5,00% 26,74 0,00\n\nValor INSS (R$): Valor PIS (R$). Valor COFINS (R$): Valor IR (R$) Valor CSLL (R$): Outras Retenções (R$)] Valor Líquido (R$);\n0,00 00 0,00 0,00 0,00 614,92\n\nO)\nAlíquota BS (5%): Valor IBS (R$): anda [UR ValorCES (R$).\n\nOUTRAS INFORMAÇÕES\n\n- Esta Nota Salvador foi emitida com respaldo na Lei 7186/2006.\n\n- Data de vencimento do ISS desta Nota Salvador: 05/08/2026\n\n- COMPETÊNCIA: 07/2026 (mós/ano)\n\n- Código de Tributação do Município: 1104-0/01 - Armazenamento, depósito e guarda de bens de qualquer espécie\n\nTIO YO Geo tpij)\n\n21/07/2026, 12:\n\nSSA_DIGITO_5_LIDO_6\nSSA_ALIQ_ISS_LEITURAS: aliq=5,00;6,00;6,00;8,00;6,00;6,00;6,00;6,00;6,00;5,00;6,00;6,00;6,00;5,00;6,00;5,00;5,00;5,00;6,00;5,00;6,00;5,00;5,00;5,00;6,00;5,00;5,00 iss=26,74;26,74;26,74;26,74;26,74;26,74;26,74;26,74;26,74;26,78;26,74;26,74;26,74;26,74;28,74;26,74;26,74;25,74;26,74;28,74;26,74;26,74'


# Trechos REAIS da leitura de página inteira (zoom 3) desta nota, antes dos
# recortes.
RAZAO_POLUIDA = (
    'CPF/CNPJ: Inscrição Municipal:\n\n03.301.926/0008-37 00.646. 776/001-57\n\n'
    'Nome/Razão Social:\n\nMETROFILE BRASIL GESTAO DA INFORMACAO LTDA. Neto\neres\n\n'
    'Endereço:\nRua Doutor Altino Teixeira 1660 - PORTO SECO PIRAJA - Salvador - CEP: 41233-010 - BA\n')
LINHA_ENDERECO_LIDA = 'Rua Doutor Altino Teixeira 1660 - PORTO SECO PIRAJA - Salvador - CEP: 41233-010 - BA'


@pytest.fixture
def nfse(monkeypatch):
    dummy_path = "tests/dummy_salvador_metrofile_9925.pdf"
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_OCR)
    try:
        notas = SPPdfExtractor(dummy_path).parse_multiple()
        assert len(notas) == 1
        yield notas[0]
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_cabecalho(nfse):
    assert nfse.numero == "00009925"
    assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "21/07/2026 10:37:53"
    assert nfse.codigo_verificacao == "8PZ3P2RH"
    assert nfse.competencia.strftime("%Y-%m-%d") == "2026-07-01"


def test_prestador(nfse):
    p = nfse.prestador
    assert p.cnpj_cpf == "03301925000837"
    assert p.razao_social == "METROFILE BRASIL GESTAO DA INFORMACAO LTDA"
    e = p.endereco
    assert (e.logradouro, e.numero, e.bairro, e.municipio, e.uf, e.cep) == (
        "Rua Doutor Altino Teixeira", "1650", "PORTO SECO PIRAJA", "Salvador", "BA", "41233010")
    assert e.codigo_municipio == "2927408"


def test_prestador_im_sem_dv_vira_sentinela_com_aviso(nfse):
    # IM impressa sem dígito verificador, lida num scan que troca 5 por 6:
    # nunca um valor plausível porém possivelmente errado (antes "00646").
    assert nfse.prestador.inscricao_municipal is None
    assert any('Inscrição Municipal do prestador omitida' in a and '00.646.776/001-57' in a
               for a in nfse.avisos)
    assert any('CNPJ corrigido' in a for a in nfse.avisos)


def test_tomador(nfse):
    t = nfse.tomador
    assert t.cnpj_cpf == "24890395000103"
    assert t.razao_social == "GUARAJUBA MALLS S/A"
    assert t.endereco.municipio == "Camaçari"
    assert t.endereco.codigo_municipio == "2905701"
    assert t.endereco.cep == "42840310"


def test_valores(nfse):
    v = nfse.valores
    assert v.valor_servicos == 514.82
    assert v.valor_deducoes == 0.0
    assert v.base_calculo == 514.82
    assert v.aliquota == 0.05
    # Leitura REAL da célula (uma das releituras) que fecha 514,82 x 5%.
    assert v.valor_iss == 25.74
    assert v.valor_liquido_nfse == 514.82
    assert v.iss_retido is False
    assert (v.valor_pis, v.valor_cofins, v.valor_inss, v.valor_ir, v.valor_csll, v.outras_retencoes) == (0,) * 6
    assert not any('não confere' in a for a in nfse.avisos)
    assert nfse.servico_codigo == "1104"


def test_cnpj_5_lido_6_so_com_troca_unica_que_fecha_o_dv():
    e = SPPdfExtractor.__new__(SPPdfExtractor)
    assert e._cnpj_salvador_5_lido_6('03.301.926/0008-37') == '03.301.925/0008-37'
    assert e._cnpj_salvador_5_lido_6('24.890.396/0001-03') == '24.890.395/0001-03'
    # Já válido, ou sem troca 6->5 que feche (outro tipo de erro): None.
    assert e._cnpj_salvador_5_lido_6('03.301.925/0008-37') is None
    assert e._cnpj_salvador_5_lido_6('61.229.895/0001-90') is None


def test_base_so_5_lido_6():
    assert SPPdfExtractor._so_5_lido_6('514.82', '614.82')
    assert not SPPdfExtractor._so_5_lido_6('614.82', '514.82')
    assert not SPPdfExtractor._so_5_lido_6('514.82', '514.82')
    assert not SPPdfExtractor._so_5_lido_6('514.82', '714.82')


def test_releitura_do_endereco_so_corrige_5_lido_6():
    f = SPPdfExtractor._aplicar_releitura_5_lido_6
    assert f(LINHA_ENDERECO_LIDA, '1650 41233 010') == LINHA_ENDERECO_LIDA.replace('1660', '1650')
    assert f(LINHA_ENDERECO_LIDA, '1670 41233 010') is None
    assert f(LINHA_ENDERECO_LIDA, '1650 41233') is None
    assert f(LINHA_ENDERECO_LIDA, '1660 41233 010') is None


def test_razao_recortada_substitui_trecho_com_logotipo():
    texto = SPPdfExtractor._emendar_razao_prestador_salvador(
        RAZAO_POLUIDA, 'METROFILE BRASIL GESTAO DA INFORMACAO LTDA.')
    assert 'Neto' not in texto and 'eres' not in texto
    assert texto.count('Nome/Razão Social') == 1
    assert 'Social:\nMETROFILE BRASIL GESTAO DA INFORMACAO LTDA.\nEndereço:' in texto


def test_razao_ausente_continua_emendada_antes_do_endereco():
    # Comportamento anterior preservado (nota nº 00000061/MCLA): linha da
    # razão sumida -> rótulo + razão emendados antes do 1º "Endereço".
    texto = SPPdfExtractor._emendar_razao_prestador_salvador(
        'CPF/CNPJ:\n12.345.678/0001-95\nEndereço:\nRua X 1\n', 'MCLA CONSTRUCOES LTDA')
    assert 'CPF/CNPJ:\n12.345.678/0001-95\nNome/Razão Social\nMCLA CONSTRUCOES LTDA\nEndereço:' in texto


@pytest.mark.skipif(not os.path.exists(PDF_REAL), reason="PDF real indisponível")
def test_pdf_real_codigo_verificacao_na_impressao_do_navegador():
    import pymupdf
    doc = pymupdf.open(PDF_REAL)
    try:
        page = doc.load_page(3)
        assert SPPdfExtractor._ocr_recut_codigo_verificacao_linha_salvador(page) == '8PZ3-P2RH'
    finally:
        doc.close()


def test_sem_evidencia_5_lido_6_mantem_a_emenda_original():
    # Página sem CNPJ "5 lido 6": comportamento anterior (emenda), mesmo com
    # a razão já presente — não muda nenhuma outra nota do corpus.
    texto = SPPdfExtractor._emendar_razao_prestador_salvador(
        RAZAO_POLUIDA, 'METROFILE BRASIL GESTAO DA INFORMACAO LTDA.', substituir=False)
    assert texto.count('Nome/Razão Social') == 2
    assert 'Neto' in texto
