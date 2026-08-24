# -*- coding: utf-8 -*-
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_BARUERI

# Texto REAL extraído (`extract_text`, pdfminer, PDF digital sem OCR) da NFS-e
# nº 0380578 — ALELO INSTITUIÇAO DE PAGAMENTO S.A. -> CLINICA PNEUMOLOGICA
# PROF ALMERIO MACHADO (nome truncado na própria nota, ver abaixo), Prefeitura
# Municipal de Barueri/SP, R$2,74 de tarifa sobre um repasse de benefício-
# alimentação de R$430,00.
MOCK_TEXT = (
    'PREFEITURA MUNICIPAL DE BARUERI\n\nSECRETARIA DE FINANÇAS\n\n'
    'NOTA FISCAL ELETRONICA DE SERVICOS - NFE\n'
    'A autenticidade desta Nota Fiscal Eletrônica de Serviços\n'
    'poderá ser confirmada na página da Prefeitura de Barueri\n'
    'na Internet, no Endereço:\n<http://www.barueri.sp.gov.br/nfe>\n\n'
    'Data Emissão\n06/01/2026\nCódigo Autenticidade\n\nHora Emissão\n08:21\n\n'
    '153Z.3080.1301.6770899-S\n\n'
    'NOTA FISCAL ELETRÔNICA DE\nSERVICOS E FATURA\n\n'
    'Número da Nota\n0380578\nNúmero RPS\n\nSérie da Nota\n\nSérie RPS\n\n'
    '0029103265\n\nRP\n\nData RPS\n\n06/01/2026\n\n'
    'Prestador de Serviços\n\n'
    'ALELO INSTITUIÇAO DE PAGAMENTO S.A.\n'
    'ALAMEDA XINGU , 512 - ANDAR 3 E 4 E 16 PARTE \n'
    'ALPHAVILLE CENTRO INDUSTR E EMPR / ALPHAVILLE\n'
    'CEP 06455-030 - BARUERI - SP\n'
    'CNPJ/CPF\nTelefone\n\n04.740.876/0001-25\n\n'
    'Inscrição Municipal\ne-mail\n\n4.44096-8\n\n'
    'Nome Tomador de Serviços\n'
    'CLINICA PNEUMOLOGICA PROF ALMERIO MACHA\n\n'
    'CPF/CNPJ\n\n13.057.112/0001-20\n\n'
    'Endereço\n\nR Humberto de Campos, 144\n\n'
    'CEP\n\nBairro\n\n40150-130 Graça\n\n'
    'E-mail\nclippampneumologia2020@gmail.com\n\n'
    'Complemento\n\nSala 1103\n\nCidade\n\nSalvador\n\nUF\n\nBA\n\n'
    'Qtde\n\n1\n\n'
    'Descrição do Serviço\n\nCódigo Serviço\n\nAlíquota\n\nValor Unitário\n\nValor Total\n\n'
    'Agenciamento, corretagem ou intermediação de contratos quais\n\n'
    '100202220\n\n2,00\n\n2,74\n\n2,74\n\n'
    'DISCRIMINAÇÃO DOS SERVIÇOS E INFORMAÇÕES RELEVANTES\n\n'
    'ALELO ALIMENTACAO = R$ 430,00\n'
    'TOTAL DE TARIFA = R$ 2,74\n'
    'TOTAL DE IMPOSTOS = R$ 0,04\n'
    'VALOR LIQUIDO DA NOTA = R$ 432,74\n'
    'Auto-retenção conf. determinado pelas INs nº 153/87, 177/87 e 107/91, art. 15.\n\n'
    'VALORES DE REPASSE A TERCEIROS\n\nObservações\n\nR$ 430,00\n\n'
    'ISSQN devido a: BARUERI-SP\n\n'
    'IRRF\n\n0,04\n\nPIS/PASEP\n\n0,00\n\nCOFINS\n\n0,00\n\nCSLL\n\n0,00\n\n'
    'Fatura Nº\n\n291032\n\nValor por Extenso\n\nValor da Fatura R$\n\nR$ 432,74\n\n'
    'Forma Pagamento\n\nVcto=06/01/2026\n\n'
    'quatrocentos e trinta e dois reais e setenta e quatro centavos\n\n'
    'VALOR TOTAL DA NOTA\n\n432,74\n\n'
    'A autenticidade desta Nota Fiscal Eletrônica de Serviços poderá ser confirmada\n'
    'na página da Prefeitura de Barueri na Internet, no Endereço:\n\n'
    'http://www.barueri.sp.gov.br/nfe\n\n'
    'Código Autenticidade\n\n153Z.3080.1301.6770899-S\n\n'
    'RECEBEMOS DA EMPRESA ALELO INSTITUIÇAO DE PAGAMENTO OS SERVIÇOS CONSTANTES DESTA\n\n'
    'NOTA FISCAL ELETRÔNICA DE SERVIÇOS\n\n'
    'Número da Nota\n0380578\n\nSérie da Nota\n\nLocal\n\nData\n\nAssinatura\n\n'
)


def test_detect_layout_barueri():
    dummy_path = "tests/dummy_barueri.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    try:
        ex = SPPdfExtractor(dummy_path)
        ex.raw_text = MOCK_TEXT
        assert ex._detect_layout() == LAYOUT_BARUERI
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_extract_barueri_nfse_0380578(monkeypatch):
    """PDF digital sem OCR, mas com peculiaridades de ordem de leitura por
    campo: "Data Emissão"/"Hora Emissão" ficam em colunas separadas da caixa
    de cabeçalho; "Código Autenticidade" aparece 2x (a 1ª tem "Hora Emissão"
    colado, não o valor real); CEP/Bairro do tomador saem com um único valor
    combinado ("40150-130 Graça"); a grade do item (Descrição do Serviço/
    Código Serviço/Alíquota/Valor Unitário/Valor Total) segue o padrão
    "rótulos dumped, depois valores dumped". "VALOR LIQUIDO DA NOTA"
    (R$432,74) inclui um repasse de R$430,00 a terceiros que NÃO é receita
    tributável do serviço - só a "TOTAL DE TARIFA" (R$2,74) vira
    ValorServicos/BaseCalculo, e o repasse é sinalizado em `Nfse.avisos`."""
    dummy_path = "tests/dummy_barueri_full.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        assert nfse.numero == "0380578"
        assert nfse.codigo_verificacao == "153Z.3080.1301.6770899-S"
        assert nfse.servico_codigo == "1002"
        assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M") == "06/01/2026 08:21"
        assert nfse.competencia.year == 2026
        assert nfse.competencia.month == 1
        assert "Agenciamento" in nfse.discriminacao
        assert "ALELO ALIMENTACAO" in nfse.discriminacao

        p = nfse.prestador
        assert p.cnpj_cpf == "04740876000125"
        assert p.razao_social == "ALELO INSTITUIÇAO DE PAGAMENTO S.A."
        assert p.inscricao_municipal == "4.44096-8"
        assert p.endereco.logradouro == "ALAMEDA XINGU"
        assert p.endereco.numero == "512"
        assert p.endereco.complemento == "ANDAR 3 E 4 E 16 PARTE"
        assert p.endereco.bairro == "ALPHAVILLE"
        assert p.endereco.municipio == "BARUERI"
        assert p.endereco.uf == "SP"
        assert p.endereco.cep == "06455030"
        assert p.endereco.codigo_municipio == "3505708"

        t = nfse.tomador
        assert t.cnpj_cpf == "13057112000120"
        assert t.cnpj_cpf != p.cnpj_cpf
        assert t.razao_social.startswith("CLINICA PNEUMOLOGICA")
        assert t.endereco.logradouro == "R Humberto de Campos"
        assert t.endereco.numero == "144"
        assert t.endereco.complemento == "Sala 1103"
        assert t.endereco.bairro == "Graça"
        assert t.endereco.municipio == "Salvador"
        assert t.endereco.uf == "BA"
        assert t.endereco.cep == "40150130"
        assert t.endereco.codigo_municipio == "2927408"
        assert t.email == "clippampneumologia2020@gmail.com"

        v = nfse.valores
        # Achado real: usar "VALOR LIQUIDO DA NOTA" (R$432,74) sobrestimaria o
        # valor tributável em ~150x - inclui R$430,00 de repasse a terceiros
        # que não é receita de serviço.
        assert v.valor_servicos == pytest.approx(2.74)
        assert v.base_calculo == pytest.approx(2.74)
        assert v.aliquota == pytest.approx(0.02)
        assert v.valor_iss == pytest.approx(0.0)
        assert v.valor_ir == pytest.approx(0.04)
        assert v.valor_pis == pytest.approx(0.0)
        assert v.valor_cofins == pytest.approx(0.0)
        assert v.valor_csll == pytest.approx(0.0)
        assert v.valor_liquido_nfse == pytest.approx(2.70)

        assert any("430,00" in a and "repasse" in a.lower() for a in nfse.avisos)
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
