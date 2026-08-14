# -*- coding: utf-8 -*-
r"""NFCom da Empresa Baiana de Jornalismo S.A. (EBJ, CNPJ 14.583.041/0001-62,
Salvador/BA) - achado no pedido do usuário para criar o layout `nfcom_salvador`
depois que a nota real nº 624 (SIND DELEGADOS DE POLICIA DO EST DA BAHIA,
R$ 400,00) caiu no fallback amplo "Chave de Acesso" -> LAYOUT_NACIONAL e saiu
com o valor ZERADO (a NFCom não usa os rótulos "Valor Total dos Serviços" que
o parser DANFSe espera) e o tomador com a razão social vazada do rótulo
"Nº TELEFONE" (o parser DANFSe não serve para a estrutura de uma NFCom).

Texto REAL extraído por pdfminer (`extract_text`) - PDF DIGITAL, sem OCR.
Preservado verbatim, incluindo o quirk que trava regressão: no bloco do
destinatário, os RÓTULOS ("NOME DO DESTINATÁRIO:"/"END.:") vêm em uma ordem,
mas os VALORES vêm em ordem PARCIALMENTE INVERTIDA (o endereço antes da razão
social) - sem o parser dedicado (`_extrair_tomador_nfcom_salvador`), a razão
social do tomador sairia como o endereço ou vice-versa.

Documento tributado por ICMS (Nota Fiscal de Comunicação Eletrônica), não por
ISS - decisão do usuário: BaseCalculo/Aliquota/ValorIss ficam propositalmente
em 0,00 (não fabricados a partir de BC ICMS/ALÍQ, que são tributos
diferentes), sinalizado via `Nfse.avisos`.
"""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_NFCOM_SALVADOR

MOCK_TEXT = 'DOCUMENTO AUXILIAR DA NOTA FISCAL FATURA DE SERVIÇOS DE COMUNICAÇÃO ELETRÔNICA\n\nEMPRESA BAIANA DE JORNALISMO S.A.\n\nEND.:\n\nRUA PROFESSOR ARISTIDES NOVIS, 123\n\nBAIRRO:\n\nFEDERACAO\n\nCEP:\n\nCNPJ:\n\n40210-630\n14.583.041/0001-62\n\nMUNICÍPIO:\n\nINSC. EST.:\n\nSALVADOR\n070667430\n\nUF:\n\nBA\n\npágina 1 /\n\n1\n\nNOME DO DESTINATÁRIO:\nEND.:\n\nR DIREITA DA PIEDADE, 11 - BARRIS - SALVADOR - BA\n\nSIND DELEGADOS DE POLICIA DO EST DA BAHIA\n\nNOTA FISCAL FATURA Nº\nSÉRIE:\n\n090\n\nDATA DE EMISSÃO:\n\n05/12/2025\n\n000000624\n\nCPF/CNPJ:\n\n73.393.696/0001-37\n\nINSC. EST.:\n\nINSC. MUN.:\n\nISENTO\n\nCÓD. DO CLIENTE:\n\nNº TELEFONE:\n\nCONSULTE PELA CHAVE DE ACESSO EM: https://dfe-portal.svrs.rs.gov.br/NfCom\n\nCHAVE DE ACESSO:\n\n2925 1214 5830 4100 0162 6209 0000 0006 2410 7749 9128\n\nPROTOCOLO DE AUTORIZAÇÃO:\n\n3292500026808110 - 05/12/2025 - 17h04min\n\nPERÍODO:\n\n01/12/25 a 31/12/25\n\nREF.:\n\nDEZ/25\n\nVENCTO.:\n\n05/01/26\n\nTOTAL A PAGAR (R$):\n\n400,00\n\n     ÁREA CONTRIBUINTE: MENSAGENS PRIORITÁRIAS / AVISOS AO\nCONSUMIDOR\n\nImpostos Retidos:\n\nPIS\n\nCOFINS\n\nIRRF\n\nCSLL\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\nITENS DA FATURA\n\nUN\n\nQUANT\n\nPREÇO UNIT\n\nVALOR TOTAL\n\nPIS/COFINS\n\nBC ICMS\n\nALÍQ\n\nVALOR ICMS\n\nVEICULACAO PUBLICIDADE JORNAL IMPRESSO\n\nUN\n\n1\n\n400,00\n\n400,00\n\n14,60\n\n0,00\n\n0,00\n\n0,00\n\nVALOR TOTAL NFF\n\nTOTAL BASE DE CÁLCULO\n\nVALOR ICMS\n\nVALOR ISENTO\n\nVALOR OUTROS\n\n400,00\n\nINFORMAÇÃO DOS TRIBUTOS\n\nRESERVADO AO FISCO\n\nTRIBUTO\n\nVALOR\n\nNÃO INFORMADO\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\nPIS\n\nCOFINS\n\nCBS / IBS\n\nFUST/FUNTTEL\n\n2,60\n\n12,00\n0,00\n\n0,00\n\nINFORMAÇÕES COMPLEMENTARES\n\nEDITAL DE CONVOCAÇÃO DE POSSE PUBLICAÇÃO: 04/12/2025\n\nÁREA DO CONTRIBUINTE E DETERMINAÇÕES DA ANATEL\n\n\x0c'


def test_detect_layout_nfcom_salvador():
    dummy_path = "tests/dummy_nfcom_salvador.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    try:
        ex = SPPdfExtractor(dummy_path)
        ex.raw_text = MOCK_TEXT
        assert ex._detect_layout() == LAYOUT_NFCOM_SALVADOR
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_extract_nfcom_salvador_nfse_624(monkeypatch):
    """Antes deste layout: valor_servicos saía 0.0 (aviso "extraído como
    zero"), tomador saía com CNPJ sentinela e razão social "Nº TELEFONE"
    (rótulo vazado). Depois: valor/tomador corretos, e um aviso EXPLICATIVO
    (não de erro) documentando que ISS fica zerado por não incidir (ICMS)."""
    dummy_path = "tests/dummy_nfcom_salvador_full.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        assert nfse.numero == "624"
        assert nfse.data_emissao.strftime("%d/%m/%Y") == "05/12/2025"
        assert nfse.competencia.strftime("%d/%m/%Y") == "01/12/2025"
        assert nfse.codigo_verificacao == "29251214583041000162620900000006241077499128"
        assert nfse.servico_codigo == "0000"
        assert nfse.discriminacao == "VEICULACAO PUBLICIDADE JORNAL IMPRESSO"

        p = nfse.prestador
        assert p.cnpj_cpf == "14583041000162"
        assert p.razao_social == "EMPRESA BAIANA DE JORNALISMO S.A"
        assert p.endereco.municipio == "SALVADOR"
        assert p.endereco.codigo_municipio == "2927408"
        assert p.endereco.uf == "BA"

        t = nfse.tomador
        # Antes: cnpj_cpf="00000000000100" (sentinela), razao_social="Nº TELEFONE".
        assert t.cnpj_cpf == "73393696000137"
        assert t.razao_social == "SIND DELEGADOS DE POLICIA DO EST DA BAHIA"
        assert t.endereco.logradouro == "R DIREITA DA PIEDADE"
        assert t.endereco.numero == "11"
        assert t.endereco.bairro == "BARRIS"
        assert t.endereco.municipio == "SALVADOR"
        assert t.endereco.uf == "BA"
        assert t.endereco.codigo_municipio == "2927408"

        # Antes: valor_servicos == 0.0 (aviso "Valor dos serviços extraído
        # como zero"). Valor real impresso: "TOTAL A PAGAR (R$): 400,00".
        v = nfse.valores
        assert v.valor_servicos == 400.0
        assert v.valor_liquido_nfse == 400.0
        # Tributado por ICMS, não ISS - propositalmente zerados (ver aviso).
        assert v.base_calculo == 0.0
        assert v.aliquota == 0.0
        assert v.valor_iss == 0.0

        assert not any("zero" in a.lower() for a in nfse.avisos)
        assert not any("não identificado" in a.lower() for a in nfse.avisos)
        assert any("ICMS" in a and "não sujeito a ISS" in a for a in nfse.avisos)
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
