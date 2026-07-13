import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_OSASCO_REPASSE
import os


def test_detect_osasco_repasse_layout():
    """Testa a detecção correta do layout Osasco/SP (NF-R de Repasse)"""
    mock_text = """
    Prefeitura do Município de Osasco
    Secretaria de Finanças
    Nota Fiscal Eletrônica de Repasse - NF-R
    """

    dummy_path = "tests/dummy_osasco_repasse.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = mock_text
    layout = extractor._detect_layout()

    assert layout == LAYOUT_OSASCO_REPASSE, f"Expected {LAYOUT_OSASCO_REPASSE}, got {layout}"

    if os.path.exists(dummy_path):
        os.remove(dummy_path)


def test_extract_osasco_repasse_full_nfse():
    """Testa extração completa de uma NF-R do layout Osasco/SP (ex: iFood Benefícios)"""
    mock_text = """
    Prefeitura do Município de Osasco
    Secretaria de Finanças
    Nota Fiscal Eletrônica de Repasse - NF-R
    Série: R1
    Nota No.: 2440738
    Emissão: 10/06/2026

    EMITENTE
    Razão Social/Nome: IFOOD BENEFICIOS E SERVICOS LTDA.
    CPF/CNPJ: 33.157.312/0001-62
    Inscrição Municipal: 0000145284
    Endereço: AV. dos Autonomistas, 1496-BLOCO-B,3º ANDAR,PARTE-Vila Yara-06020012
    Município: Osasco
    UF: SP
    Email: tributario@ifood.com.br
    Fone: (00)3498-8402

    RECEPTOR
    Razão Social/Nome: PHGESTAO E CONSULTORIA S.A.
    CPF/CNPJ: 25.311.856/0001-09
    Inscrição Municipal:
    Endereço: A AL HUMAITA, 0 - GUARAJUBA ,42840-562
    Município: Camaçari
    UF: BA
    Email: priscila@guarajubanegocios.com.br
    Fone: 3248-7400

    DISCRIMINAÇÃO
    SERVICO RECARGA IFOOD BENEFICIOS.
    Regra Geral Saldo Livre: R$ 422,77

    IMPOSTOS ADICIONAIS - Lei 12.741/2012 (Os valores informados sao de responsabilidade exclusiva do emissor)
    INSS (R$): 0,00     IRRF (R$): 0,00     CSLL (R$): 0,00     COFINS (R$): 0,00     PIS/PASEP (R$): 0,00

    Referência: 6/2026          Valor da Nota: 422,77          Valor do Repasse: 422,77

    Código de autenticidade: SGMFBFJB
    Verifique a autenticidade desta nota no site http://www.nfe.osasco.sp.gov.br
    """

    dummy_path = "tests/dummy_osasco_repasse_full.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = mock_text
    extractor.layout = extractor._detect_layout()

    assert extractor.layout == LAYOUT_OSASCO_REPASSE

    nfse = extractor.parse()

    assert nfse.numero == "2440738"
    assert nfse.codigo_verificacao == "SGMFBFJB"
    assert nfse.data_emissao.day == 10
    assert nfse.data_emissao.month == 6
    assert nfse.data_emissao.year == 2026
    assert nfse.competencia.month == 6
    assert nfse.competencia.year == 2026

    assert nfse.prestador.cnpj_cpf == "33157312000162"
    assert nfse.prestador.razao_social == "IFOOD BENEFICIOS E SERVICOS LTDA."
    assert nfse.prestador.endereco.municipio == "Osasco"
    assert nfse.prestador.endereco.uf == "SP"
    assert nfse.prestador.email == "tributario@ifood.com.br"

    assert nfse.tomador.cnpj_cpf == "25311856000109"
    assert nfse.tomador.razao_social == "PHGESTAO E CONSULTORIA S.A."
    assert nfse.tomador.endereco.municipio == "Camaçari"
    assert nfse.tomador.endereco.uf == "BA"
    assert nfse.tomador.endereco.cep == "42840562"

    assert nfse.valores.valor_servicos == pytest.approx(422.77)
    assert nfse.valores.valor_liquido_nfse == pytest.approx(422.77)

    assert nfse.avisos == []

    if os.path.exists(dummy_path):
        os.remove(dummy_path)


def test_extract_osasco_repasse_real_document_variant():
    """Regressão: variante real vista em documento de produção, com rótulos
    diferentes do primeiro mock — "Nota Fiscal Eletrônica de Serviços Repasse
    (NF-R)" (não "de Repasse - NF-R"), "Nota Nº:" (não "Nota No.:"),
    "CNPJ/CPF" (ordem invertida), "Razão Social:" sem "/Nome", "E-Mail"
    (não "Email"), "Telefone" (não "Fone"), "Ref. Fiscal" (não "Referência")
    para a competência, sem campo "Valor da Nota" (só "Valor do Repasse"),
    e "Cód. de Autenticidade" colado na mesma linha do campo seguinte."""
    mock_text = """
    PREFEITURA DO MUNICIPIO DE OSASCO
    Secretaria de Finanças
    Nota Fiscal Eletrônica de Serviços Repasse (NF-R)

    Nota Nº: 02479318          Emissão: 22/06/2026          Série R1          Ref. Fiscal 06/2026

    EMITENTE   Razão Social: IFOOD BENEFICIOS E SERVICOS LTDA.
    CNPJ/CPF: 33157312000162
    Endereço: AV. dos Autonomistas, 1496 - BLOCO-B,3º ANDAR, PARTE - Vila Yara - 06020012
    Município: Osasco
    E-Mail: tributario@ifood.com.br
    Inscrição Municipal: 145284
    UF SP
    Telefone: (00) 3498-8402

    RECEPTOR   Razão Social: PHGESTAO E CONSULTORIA S.A.
    CNPJ/CPF: 25311856000109
    Endereço: A AL HUMAITA, 0 - GUARAJUBA ,42840-562
    Município: Camaçari
    E-Mail: priscila@guarajubanegocios.com.br
    UF: BA
    Telefone: 3248-7400

    Discriminação do Serviço:
    SERVICO RECARGA IFOOD BENEFICIOS.Vencimento da Cobranca: 24/06/2026 Nota Fiscal emitida de acordo com
    o Regime Especial objeto do Processo Administrativo No. 11.037/2020

    IMPOSTOS ADICIONAIS - Lei 12.741/2012 (Os valores informados são de responsabilidade do emissor da nota):
    INSS (R$): 0,00     IRRF (R$): 0,00     CSLL (R$): 0,00     COFINS (R$): 0,00     Pis/Pasep (R$): 0,00

    Usuário: IM145284     Cód. de Autenticidade: VCWSRSCV     Valor do Repasse: 427,26

    Identificador/Nº Contrato informado pelo emissor: 48074812     Nº Controle informado pelo Emissor: 2884709

    Verifique a autenticidade desta nota utilizando o código VCWSRSCV no site www.nfe.osasco.gov.br

    Nota Fiscal de Repasse R1 emitida em 22/06/2026 às 17:36:12 conforme Decreto Nº 13.377 de 03 de junho de 2022.
    """

    dummy_path = "tests/dummy_osasco_repasse_real.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = mock_text
    extractor.layout = extractor._detect_layout()

    assert extractor.layout == LAYOUT_OSASCO_REPASSE

    nfse = extractor.parse()

    assert nfse.numero == "02479318"
    assert nfse.codigo_verificacao == "VCWSRSCV"
    assert nfse.data_emissao.day == 22
    assert nfse.data_emissao.month == 6
    assert nfse.data_emissao.year == 2026
    assert nfse.competencia.month == 6
    assert nfse.competencia.year == 2026

    assert nfse.prestador.cnpj_cpf == "33157312000162"
    assert nfse.prestador.razao_social == "IFOOD BENEFICIOS E SERVICOS LTDA."
    assert nfse.prestador.inscricao_municipal == "145284"
    assert nfse.prestador.endereco.municipio == "Osasco"
    assert nfse.prestador.endereco.uf == "SP"
    assert nfse.prestador.endereco.cep == "06020012"
    assert nfse.prestador.email == "tributario@ifood.com.br"

    assert nfse.tomador.cnpj_cpf == "25311856000109"
    assert nfse.tomador.razao_social == "PHGESTAO E CONSULTORIA S.A."
    assert nfse.tomador.endereco.municipio == "Camaçari"
    assert nfse.tomador.endereco.uf == "BA"
    assert nfse.tomador.endereco.cep == "42840562"

    assert nfse.valores.valor_servicos == pytest.approx(427.26)
    assert nfse.valores.valor_liquido_nfse == pytest.approx(427.26)

    assert nfse.avisos == []

    if os.path.exists(dummy_path):
        os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
