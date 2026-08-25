# -*- coding: utf-8 -*-
"""3ª variante do layout Lauro de Freitas/BA (`LAYOUT_LAURO_FREITAS`) — nota
real nº 202600000016748 (MAG COMERCIO VAREJISTA DE MATERIAL ELETRICO E
SERVICOS TECNICOS DE INSTALACAO E MANUTEN -> BONI LOGISTICA LTDA, R$220,00),
achado real 2026-08-25.

Um template NOVO da plataforma da Prefeitura (campos da Reforma Tributária —
IBS/CBS, NBS, Finalidade, Destinatário, Classificação Tributária — ausentes
das 2 variantes já cobertas por `_extrair_entidade_lauro_freitas`). A leitura
de página inteira (zoom 3x) PERDE POR COMPLETO (não corrompe — some) vários
campos: Número NFS-e/Código de Verificação saem truncados ("4F723" em vez de
"4F7233055"), o CEP do prestador nunca aparece, o bloco "Cód. Trib.
Municipal" desaparece e a grade VALORES sai com metade das colunas. Resolvido
via `_ocr_recut_lauro_freitas_v3`: 4 recortes dedicados devolvidos como
sentinelas `LFV3_*` que as funções de extração conferem ANTES da lógica das
variantes 1/2 (fallback total preservado para elas).

`MOCK_TEXT` abaixo é o texto REAL capturado via `_ocr_page` (sentinelas +
OCR de página inteira concatenados, exatamente como a pipeline real produz),
não uma reconstrução limpa — inclui os mesmos ruídos que motivaram os
recortes dedicados (CNPJ do prestador com dígito trocado "242"->"243" na
leitura de página inteira, UF "ur: BA", nº da casa do tomador lido "TI" em
vez de "11").
"""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_LAURO_FREITAS

MOCK_TEXT = (
    "LFV3_NUMERO: 202600000016748\n"
    "LFV3_CODVERIF: 4F7233055\n"
    "LFV3_PREST_CNPJ: 15243835000140\n"
    "LFV3_PREST_IM: 0000394220011\n"
    "LFV3_PREST_RAZAO: MAG COMERCIO VAREJISTA DE MATERIAL ELETRICO E SERVICOS TECNICOS DE INSTALACAO E MANUTEN\n"
    "LFV3_PREST_LOGRADOURO: Avenida Luiz Tarquínio Pontes\n"
    "LFV3_PREST_NUMERO: 1904\n"
    "LFV3_PREST_COMPLEMENTO: Sala 1D\n"
    "LFV3_PREST_BAIRRO: Prangueiras\n"
    "LFV3_PREST_MUNICIPIO: LAURO DE FREITAS\n"
    "LFV3_PREST_CEP: 42701450\n"
    "LFV3_TOM_CNPJ: 04555283000199\n"
    "LFV3_TOM_RAZAO: BONI LOGISTICA LTDA\n"
    "LFV3_TOM_LOGRADOURO: RUA GÉRINO DE SOUZA FILHO TI ITINGA\n"
    "LFV3_TOM_NUMERO: S/N\n"
    "LFV3_TOM_MUNICIPIO: Lauro de Freitas\n"
    "LFV3_TOM_UF: BA\n"
    "LFV3_TOM_CEP: 42738200\n"
    "LFV3_COD_SERVICO: 1401\n"
    "LFV3_VALOR_SERVICO: 220,00\n"
    "LFV3_DESC_COND: 0,00\n"
    "LFV3_DESC_INCOND: 0,00\n"
    "LFV3_DEDUCOES: 0,00\n"
    "LFV3_BASE_CALCULO: 220,00\n"
    "LFV3_ALIQUOTA: 5,0000\n"
    "LFV3_VALOR_ISS: 11,00\n"
    "LFV3_ISSQN_RETIDO: 0,00\n"
    "PREFEITURA MUNICIPAL DE 2025000000 16748\n\n"
    "LAURO DE FREITAS / BA Data e Hora de Emissão\n\n"
    "28/07/2026 17:48:12\n"
    "NOTA FISCAL DE SERVIÇOS ELETRÔNICA - NFS-e Código de Verificação\n\n"
    "4F723\n"
    "RPS Nº: 6971 Série: 1 Emitido em: 28/07/2026 x\n\n"
    "PRESTADOR DE SERVIÇOS\n"
    "CNPJ! CPF: 15.242.835/0001-40 Inscrição Municipal: 0000394220011 Inscrição Estadual: 26784463\n"
    "Nome/Razão Social: MAG COMERCIO VAREJISTA DE MATERIAL ELETRICO E SERVICOS TECNICOS DE INSTALAÇAO E MANUTEN\n"
    "Endereço: Avenida Luiz Tarquínio Pontes 1904 Sala 1D, Pitangueiras\n"
    "Município: LAURO DE FREITAS ur: BA\n"
    "Fone: (71) 3289-ga50 E-mail: — assistenciadbmagengenharia com.br\n"
    "TOMADOR DE SERVIÇOS\n"
    "CNPJ/CPF: 04.555.2830001-99 Inscrição Municipal: Inscrição Estadual; ISENTO\n"
    "Nome/Razão Social: BONI LOGISTICA LTDA\n"
    "Endereço: RUA GERINO DE SOUZA FILHO TI ITINGA\n"
    "Município: pes de e\n"
    "one ê 10\n\n"
    "CEP: 42701-450\n\n"
    ", UF:BA CEP: 42738-200 PAÍS: Brasil\n\n"
    "- S .br\n"
    "DISCRIMINAÇÃO DOS SERVIÇOS\n"
    "Ordem de Servico 8192 - 1.1.2 - Serviço Manutenção Laboratório\n\n"
    "- Sesviço de manutenção preventiva e corretiva em nobresk com substituição e peças - Garantia de baterias: 12 meses à partir da\n"
    "Instalação (Materiais aplicados conforme OS:Bateris 12 V TAH )- 08:268192 - Sorio0GXM1401282KS NOBREAK ATTIV 700 VA BIVOLT INTELBRAS\n\n"
    "- Forma de pagamento: Boleto - 28.08.2026\n"
    "NBS:12)018900\n\n"
    "TRIBUTAÇÃO DE ISSQN\n"
    "Regime Especial de Tributação: 6 - ME EPP - Simples Nacional\n"
    "Natureza da Operação: 1 - Tributação no municipio\n"
    "Local de Prestação: LAURO DE FREITAS / BA\n\n"
    "Finalidade: NF'S-s regular Ente Governamental: Não\n"
    "Destinatário: Tomador Adquirente igual ao Destinatário\n"
    "Indicador da Operação:\n"
    "Classificação Tributária:\n\n"
    "VALORES\n\n"
    "Deduções Base de Cálculo ISS (%) Valor ISS ISSQN Retido\n"
    "R$ 0,00 R$ 0,00 R$ 220,00 Ng 5,0000 R$ 11,00 R$ 0,00\n\n"
    "OUTRAS INFORMAÇÕES\n"
    "- Esta NFS-e foi emitida através do RPS Nº 6971 sórie 1, emitido em 28/07/26.\n"
    "- ma via desta Nota Fiscal será enviada através do e-mail fomecido pela tomador das serviços.\n"
    "- À autenticidade desta nota poderá ser verificada no site, com utilização do código de verificação.\n\n"
    "Recebi(emos) de MAG COMERCIO VAREJISTA DE MATERIAL ELETRICO E SERVICOS TECNICOS DE INSTALACAO E MANUTEN, CNPJ:\n"
    "15.243.835/0001-40 os serviços constantes na Nota Fiscal de Serviço especificada abaixo:\n"
    "[4 /\n\n"
    "Nome / Assinstura do Recebedor\n"
)


def _novo_extrator():
    dummy_path = "tests/dummy_lauro_freitas_v3_mag_comercio.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = MOCK_TEXT
    return extractor, dummy_path


def test_deteccao_layout_lauro_freitas_v3():
    extractor, dummy_path = _novo_extrator()
    try:
        assert extractor._detect_layout() == LAYOUT_LAURO_FREITAS
    finally:
        os.remove(dummy_path)


def test_numero_e_codigo_verificacao_vem_do_sentinela_nao_do_rps_truncado():
    extractor, dummy_path = _novo_extrator()
    try:
        extractor.layout = LAYOUT_LAURO_FREITAS
        # BUG CORRIGIDO: sem sentinela, a extração genérica pegava o "RPS Nº
        # 6971" (não o "Número NFS-e" real) e o Código de Verificação saía
        # truncado ("4F723" — a leitura de página inteira perde o resto).
        assert extractor._extrair_numero() == "202600000016748"
        assert extractor._extrair_codigo_verificacao() == "4F7233055"
    finally:
        os.remove(dummy_path)


def test_codigo_servico_vem_do_sentinela_nao_do_fallback_generico():
    extractor, dummy_path = _novo_extrator()
    try:
        extractor.layout = LAYOUT_LAURO_FREITAS
        # BUG CORRIGIDO: o bloco "Cód. Trib. Municipal" some da leitura de
        # página inteira, caindo no fallback genérico "03115".
        assert extractor._extrair_codigo_servico() == "1401"
    finally:
        os.remove(dummy_path)


def test_prestador_recupera_cnpj_cep_e_uf_corrigidos_via_recorte():
    extractor, dummy_path = _novo_extrator()
    try:
        extractor.layout = LAYOUT_LAURO_FREITAS
        prestador = extractor._extrair_entidade('Prestador')
        # BUG CORRIGIDO: leitura de página inteira troca um dígito do CNPJ
        # ("15.242.835" em vez de "15.243.835") e nunca captura o CEP.
        assert prestador.cnpj_cpf == "15243835000140"
        assert prestador.inscricao_municipal == "0000394220011"
        assert "MAG COMERCIO VAREJISTA" in prestador.razao_social
        assert prestador.endereco.numero == "1904"
        assert prestador.endereco.complemento == "Sala 1D"
        assert prestador.endereco.bairro == "Prangueiras"
        assert prestador.endereco.cep == "42701450"
        # BUG CORRIGIDO: "UF: BA" sai "ur: BA" na leitura de página inteira —
        # sentinela valida contra whitelist e usa o default sensato (BA).
        assert prestador.endereco.uf == "BA"
        assert prestador.endereco.codigo_municipio == "2919207"
    finally:
        os.remove(dummy_path)


def test_tomador_recupera_cnpj_com_barra_e_endereco_via_recorte():
    extractor, dummy_path = _novo_extrator()
    try:
        extractor.layout = LAYOUT_LAURO_FREITAS
        tomador = extractor._extrair_entidade('Tomador')
        # BUG CORRIGIDO: leitura de página inteira perde a barra do CNPJ
        # ("04.555.2830001-99") e o Município/CEP saem embaralhados.
        assert tomador.cnpj_cpf == "04555283000199"
        assert tomador.razao_social == "BONI LOGISTICA LTDA"
        assert tomador.endereco.municipio == "Lauro de Freitas"
        assert tomador.endereco.uf == "BA"
        assert tomador.endereco.cep == "42738200"
        assert tomador.endereco.codigo_municipio == "2919207"
        # Nº da casa ("11") não é recuperável via OCR nesta nota em nenhum
        # zoom/PSM testado (Tesseract insiste em ler "TI") — nunca fabricado.
        assert tomador.endereco.numero == "S/N"
    finally:
        os.remove(dummy_path)


def test_valores_grade_via_recorte_zoom8_psm4():
    extractor, dummy_path = _novo_extrator()
    try:
        extractor.layout = LAYOUT_LAURO_FREITAS
        # BUG CORRIGIDO: a grade VALORES (10 colunas) sai com só 5 rótulos e
        # valores incompletos na leitura de página inteira, retornando zeros.
        valores = extractor._extrair_valores()
        assert valores.valor_servicos == pytest.approx(220.0)
        assert valores.base_calculo == pytest.approx(220.0)
        # "5,0000" (4 dígitos sem separador correto na leitura crua) -> 5% -> 0.05.
        assert valores.aliquota == pytest.approx(0.05)
        assert valores.valor_iss == pytest.approx(11.0)
        assert valores.valor_liquido_nfse == pytest.approx(220.0)
        assert valores.iss_retido is False
    finally:
        os.remove(dummy_path)


def test_discriminacao_para_na_tributacao_issqn_desta_variante():
    extractor, dummy_path = _novo_extrator()
    try:
        extractor.layout = LAYOUT_LAURO_FREITAS
        disc = extractor._extrair_discriminacao()
        # BUG CORRIGIDO: sem o limite dedicado a este template, a
        # discriminação vazava até o fim do documento (bloco de tributação +
        # grade de valores + rodapé).
        assert "Ordem de Servico 8192" in disc
        assert "TRIBUTAÇÃO DE ISSQN" not in disc
        assert "VALORES" not in disc
    finally:
        os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
