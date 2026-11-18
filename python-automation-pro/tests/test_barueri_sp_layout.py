# -*- coding: utf-8 -*-
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_BARUERI
from src.transformers.abrasf_transformer import Abrasf201Transformer

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


# ---------------------------------------------------------------------------
# Barueri/SP ESCANEADA (PDF imagem, sem camada de texto -> OCR do pipeline).
# Texto REAL produzido por `_extract_via_ocr` (Tesseract, zoom 3x) da NFS-e nº
# 0000088 — IGOR GUERRA ARQUITETURA EIRELI -> NAUTICA INDUSTRIA E COMERCIO DE
# MOVEIS E SERVIÇOS LTDA, R$13.290,00, prestador do Simples Nacional.
# Preservado verbatim. O OCR lê a página por LINHA (rótulo e valor lado a
# lado), não por coluna como o pdfminer da versão digital — e traz ruídos
# típicos: "pata Emissão" (Data), "PISIPASEP", "CS" (CSLL), "ur" (UF), "sP",
# "grassconsultoriaQgmail.com" (@ lido como Q) e o código de autenticidade do
# rodapé com espaços espúrios ("2 3X.9325.3289.1 094899-S").
# ---------------------------------------------------------------------------
OCR_TEXT_0000088 = """E A ta isa Batrtica ds Serviços PREFEITURA MUNICIPAL DE BARUERI

BAR |] É R | SECRETARIA DE FINANÇAS

NOTA FISCAL ELETRONICA DE SERVICOS - NFE pata Emissão ora Emissão NOTA FISCAL ELETRÔNICA DE

ini . No . 24/02/2026 10:18 SERVICOS E FATURA
A autenticidade desta Nota Fiscal Eletrônica de Serviços Eis Anencade Ea =
poderá ser confirmada na página da Prefeitura de Barueri o

. 0000088
RR Ran nad 213X.9325.3289.1094899-S TONS SUCH —EGRES

<http:/Awww.barueri.sp.gov.br/nfe>

Prestador de Serviços IGOR GUERRA ARQUITETURA EIRELI
AVENIDA ANDROMEDA , 885 - SALA 0921 - BRASCAN CENTURY OF
GREEN VALLEY / ALPHAVILLE
CEP 06473-000 - BARUERI - SP

CNPJ/CPF 27.124.679/0001-87 Inscrição Municipal 4.AB321-5
Telefone e-mail

Nome Tomador de Serviços CPF/CNPJ

NAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVIÇOS LTDA 16.699.869/0002-97

Endereço Complemento

RUA GABRIEL MONTEIRO DA SILVA, 1480

CEP
01442-001

Bairro Cidade ur

JARDIM AMERICA SÃO PAULO sP

E-mail
grassconsultoriaQgmail.com

Qtde Descrição do Serviço Código Serviço Alíquota | Valor Unitário Valor Total
1 Decoração. 071101220 2,00 13.290,00 13.290,00
DISCRIMINAÇÃO DOS SERVIÇOS E INFORMAÇÕES RELEVANTES
REFERENTE AOS SERVIÇOS PRESTADOS
DADOS BANCARIOS
IGOR GUERRA ARQUITETURA
BANCO C6 S.A (336)
AGENCIA 0001
CONTA 40785313-8
CNPJ 27.124.679/0001-87
PIX CNPJ 27.124.679/0001-87
VALORES DE REPASSE A TERCEIROS Observações
R$ 0,00 ISSQN devido a: BARUERI-SP
IRRF PISIPASEP COFINS CS Documento emitido por ME ou EP optante pelo
SIMPLES NACIONAL ou MEI. Não gera direito a
0,00 0,00 0,00 0,00 crédito Fiscal de ICMS, de ISS e de IPI
VALOR TOTAL DA NOTA 13.290,00
Fatura Nº Valor da Fatura R$ Forma Pagamento

Valor por Extenso

ei . . Código Autenticidade
A autenticidade desta Nota Fiscal Eletrônica de Serviços poderá ser confirmada

na página da Prefeitura de Barueri na Internet, no Endereço: 2 3X.9325.3289.1 094899-S

hitp:/Awww barueri. sp.gov.brinte

RECEBEMOS DA EMPRESA IGOR GUERRA ARQUITETURA EIRELI OS SERVIÇOS CONSTANTES DESTA | | Número da Nota Série da Nota
NOTA FISCAL ELETRÔNICA DE SERVIÇOS 0000088

Local Data Assinatura

"""


def _parse_barueri_ocr(monkeypatch, texto, dummy_path):
    """Simula o caminho real de um PDF sem texto: pdfminer devolve vazio, o
    pipeline cai no OCR global (`from_ocr = True`)."""
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: texto)
    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert extractor.from_ocr is True
        return nfse_list
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_detect_layout_barueri_escaneada():
    dummy_path = "tests/dummy_barueri_scan_detect.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    try:
        ex = SPPdfExtractor(dummy_path)
        ex.raw_text = OCR_TEXT_0000088
        ex.from_ocr = True
        assert ex._detect_layout() == LAYOUT_BARUERI
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_extract_barueri_escaneada_nf_0000088(monkeypatch):
    """Antes: tudo menos número/data caía em fallback (prestador/tomador "Não
    Identificado" CNPJ 000..., ValorServicos 0,00, item 03115, discriminação
    genérica, código de autenticidade XXXX-XXXX)."""
    nfse_list = _parse_barueri_ocr(monkeypatch, OCR_TEXT_0000088, "tests/dummy_barueri_scan_88.pdf")
    assert len(nfse_list) == 1
    nfse = nfse_list[0]

    assert nfse.numero == "0000088"
    assert nfse.codigo_verificacao == "213X.9325.3289.1094899-S"
    assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M") == "24/02/2026 10:18"
    assert (nfse.competencia.year, nfse.competencia.month) == (2026, 2)
    # "071101220" (código municipal de Barueri) -> item 7.11 da LC 116.
    assert nfse.servico_codigo == "0711"
    assert nfse.discriminacao.startswith("Decoração. - REFERENTE AOS SERVIÇOS PRESTADOS")
    assert "PIX CNPJ 27.124.679/0001-87" in nfse.discriminacao
    assert "VALORES DE REPASSE" not in nfse.discriminacao
    assert nfse.optante_simples_nacional is True

    p = nfse.prestador
    assert p.cnpj_cpf == "27124679000187"
    assert p.razao_social == "IGOR GUERRA ARQUITETURA EIRELI"
    assert p.inscricao_municipal == "4.AB321-5"
    assert p.endereco.logradouro == "AVENIDA ANDROMEDA"
    assert p.endereco.numero == "885"
    assert p.endereco.complemento == "SALA 0921 - BRASCAN CENTURY OF"
    assert p.endereco.bairro == "ALPHAVILLE"
    assert p.endereco.municipio == "BARUERI"
    assert p.endereco.uf == "SP"
    assert p.endereco.cep == "06473000"
    assert p.endereco.codigo_municipio == "3505708"

    t = nfse.tomador
    assert t.cnpj_cpf == "16699869000297"
    assert t.razao_social == "NAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVIÇOS LTDA"
    assert t.endereco.logradouro == "RUA GABRIEL MONTEIRO DA SILVA"
    assert t.endereco.numero == "1480"
    assert t.endereco.complemento is None
    assert t.endereco.cep == "01442001"
    assert t.endereco.bairro == "JARDIM AMERICA"
    assert t.endereco.municipio == "SÃO PAULO"
    assert t.endereco.uf == "SP"
    assert t.endereco.codigo_municipio == "3550308"
    assert t.email == "grassconsultoria@gmail.com"

    v = nfse.valores
    assert v.valor_servicos == pytest.approx(13290.00)
    assert v.base_calculo == pytest.approx(13290.00)
    assert v.aliquota == pytest.approx(0.02)
    # Simples Nacional: ISS não destacado na nota -> 0,00, nunca Base x Alíquota.
    assert v.valor_iss == pytest.approx(0.0)
    assert v.iss_retido is False
    assert (v.valor_ir, v.valor_pis, v.valor_cofins, v.valor_csll) == (0.0, 0.0, 0.0, 0.0)
    assert v.valor_liquido_nfse == pytest.approx(13290.00)

    assert any("Simples Nacional" in a and "ValorIss" in a for a in nfse.avisos)
    assert not any("repasse" in a.lower() for a in nfse.avisos)
    assert not any("ilegível" in a for a in nfse.avisos)

    xml = Abrasf201Transformer().transform(nfse)
    for trecho in ("<ItemListaServico>0711</ItemListaServico>",
                   "<CodigoTributacaoMunicipio>0711</CodigoTributacaoMunicipio>",
                   "<CodigoCnae>0000000</CodigoCnae>",
                   "<MunicipioIncidencia>3505708</MunicipioIncidencia>",
                   "<IssRetido>2</IssRetido>",
                   "<OptanteSimplesNacional>1</OptanteSimplesNacional>",
                   "<Competencia>2026-02-01</Competencia>"):
        assert trecho in xml


def test_barueri_escaneada_sem_valor_confiavel_nao_fabrica(monkeypatch):
    """Guarda: grade do item corrompida (código com 8 dígitos) E repasse a
    terceiros > 0 -> o "VALOR TOTAL DA NOTA" não pode virar ValorServicos (na
    digital ele inclui o repasse); CNPJ do tomador com dígito verificador
    errado -> sentinela, nunca o número lido."""
    texto = (OCR_TEXT_0000088
             .replace("1 Decoração. 071101220 2,00 13.290,00 13.290,00",
                      "1 Decoração. 07110122 2,00 13.290,00 13.290,00")
             .replace("R$ 0,00 ISSQN devido a", "R$ 430,00 ISSQN devido a")
             .replace("16.699.869/0002-97", "16.699.869/0002-98"))
    nfse = _parse_barueri_ocr(monkeypatch, texto, "tests/dummy_barueri_scan_guarda.pdf")[0]

    assert nfse.valores.valor_servicos == pytest.approx(0.0)
    assert nfse.valores.aliquota == pytest.approx(0.0)
    assert nfse.servico_codigo != "0711"
    assert nfse.tomador.cnpj_cpf.startswith("00000000000")
    assert nfse.prestador.cnpj_cpf == "27124679000187"
    assert any("ilegível" in a for a in nfse.avisos)
    assert any("430,00" in a and "repasse" in a.lower() for a in nfse.avisos)


def test_barueri_parser_escaneado_so_roda_com_ocr():
    """Guarda do ramo digital: sem `from_ocr`, o texto linha-a-linha do OCR
    não é interpretado pelos parsers da versão escaneada (o ramo digital,
    nota ALELO 0380578, continua sendo o único caminho para PDFs com texto)."""
    dummy_path = "tests/dummy_barueri_scan_gate.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    try:
        ex = SPPdfExtractor(dummy_path)
        ex.raw_text = OCR_TEXT_0000088
        ex.from_ocr = False
        ex.layout = ex._detect_layout()
        assert ex._barueri_escaneada() is False
        ex.from_ocr = True
        assert ex._barueri_escaneada() is True
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
