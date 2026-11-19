# -*- coding: utf-8 -*-
"""NFS-e da Prefeitura Municipal do Natal/RN - "Nota Natalense" (`natal_rn`).

Achado real 2026-11-19: `PRISCILA FARIAS_NF15.pdf`, 1 página SEM camada de
texto (pdfminer devolve só "\\x0c"). O OCR do pipeline lia a página
direitinho, mas sem layout próprio ela caía em `LAYOUT_GENERICO`, era
descartada como "Layout não reconhecido" e a conversão terminava com
"parece ser baseado em imagem/scan ou vazio" - nenhum XML.
"""
import os

import pytest

from src.extractors import natal_nfse
from src.extractors.pdf_extractor import LAYOUT_NATAL, SPPdfExtractor
from src.transformers.abrasf_transformer import Abrasf201Transformer

PDF_REAL = r'L:\USUARIOS\ANDERSON\ARQUIVOS DESKTOP\Notas\Nova pasta\PRISCILA FARIAS_NF15.pdf'

# Texto REAL do OCR do pipeline (`_ocr_page`, Tesseract 'por', zoom 3x) da
# NFS-e nº 0000000015, preservado verbatim - inclusive os erros típicos de
# OCR: "RALDO" (impresso "R ALDO"), "CPF/CNPJINIF", e-mails com o "@" lido
# como "Q"/"QQ" e as células "*,**" (mascaradas, Simples Nacional) que o OCR
# não leu.
OCR_TEXT_NF15 = """Prefeitura Municipal do Natal Nº da Nota: 0000000015

Secretaria Municipal de Finanças Competência: MAR/2026
Nota Fiscal de Serviços Eletrônica - NFS-e Data Prestação Serviço: 17/03/2026
Nota Natalense Nº da Nota Substituída:
Data/Hora de Emissão: 17/03/2026 às 17:30:28 Código de Verificação: 350796290
Prestador de Serviços
CPF/CNPJ: 17.084.578/0001-76 Inscrição Municipal: 221.161-3

Razão Social: PRISCILA FARIAS CARVALHO VALIAS
Endereço: RALDO DE MELO FREIRE, 1876, APTO 502 , Capim Macio, 59082-030

Município: NATAL UF: RN
Telefone: (84) 9903-4747 E-mail:  PFCVALIASQGMAIL.COM

Tomador de Serviços

Nome/Razão Social: NAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA

CPF/CNPJINIF: 16.699.869/0002-97 Inscrição Municipal:
Endereço: RUA GABRIEL MONTEIRO DA SILVA, 1480, CASA TÉRREA, JARDIM AMERICA, 01442-001
Cidade: SAO PAULO Estado: SP
Telefone: E-mail: | lorenaQQnauticamoveis.com
Serviços

7.01.04 - Arquitetura, urbanismo e congêneres.
NBS: 114021500 - Serviços de arquitetura relativos ao acompanhamento e fiscalização da execução de projetos arquitetônicos e urbanísticos

Item Descrição Quant. Vlr. Unitário Valor Total
1 Serviços de arquitetura realizados nesse mês 1,0000 20.857,95 20.857,95

Valor Total da NFS-e R$: 20.857,95
Deduções (R$) Base Cálculo (R$) Alíquota (%) Valor do ISS (R$) Outras Retenções (R$)
INSS (R$) IRPJ (R$) CSLL (R$) COFINS (R$) PIS/PASEP (R$)

Outras Informações

Documento emitido por ME ou EPP optante pelo SIMPLES NACIONAL. Não gera direito a crédito fiscal de IPI.
Dados bancários: Priscila Faria Carvalho Valias, Banco C6, Agencia: 0001, conta corrente: 3527194-9, PIX: 17.084.578/0001-79.
"""


def _parse_ocr(monkeypatch, texto, dummy_path):
    """Caminho real de um PDF sem texto: pdfminer vazio -> OCR global."""
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: texto)
    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert extractor.from_ocr is True
        return extractor, nfse_list
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def _parse_texto(texto):
    ex = SPPdfExtractor("tests/nao_existe_natal.pdf")
    ex.raw_text = texto
    return ex, ex.parse()


def test_detect_layout_natal_escaneada():
    ex = SPPdfExtractor("tests/nao_existe_natal.pdf")
    ex.raw_text = OCR_TEXT_NF15
    assert ex._detect_layout() == LAYOUT_NATAL
    assert ex._detect_layout_page(OCR_TEXT_NF15) == LAYOUT_NATAL


def test_extract_natal_nf_0000000015(monkeypatch):
    """Antes: nenhuma nota (página descartada como layout não reconhecido)."""
    extractor, nfse_list = _parse_ocr(monkeypatch, OCR_TEXT_NF15, "tests/dummy_natal_nf15.pdf")
    assert extractor.invalid_pages == []
    assert len(nfse_list) == 1
    nfse = nfse_list[0]

    assert nfse.numero == "0000000015"
    assert nfse.codigo_verificacao == "350796290"
    assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "17/03/2026 17:30:28"
    assert (nfse.competencia.year, nfse.competencia.month, nfse.competencia.day) == (2026, 3, 1)
    # "7.01.04": item 7.01 da LC 116 + desdobramento municipal "04".
    assert nfse.servico_codigo == "0701"
    assert nfse.codigo_cnae is None
    assert nfse.discriminacao == "Serviços de arquitetura realizados nesse mês"
    assert nfse.optante_simples_nacional is True
    assert nfse.regime_especial_tributacao == "6"

    p = nfse.prestador
    assert p.cnpj_cpf == "17084578000176"
    assert p.inscricao_municipal == "2211613"
    assert p.razao_social == "PRISCILA FARIAS CARVALHO VALIAS"
    # Sem o PDF não há recorte: fica a leitura da página ("RALDO").
    assert p.endereco.logradouro == "RALDO DE MELO FREIRE"
    assert p.endereco.numero == "1876"
    assert p.endereco.complemento == "APTO 502"
    assert p.endereco.bairro == "Capim Macio"
    assert p.endereco.codigo_municipio == "2408102"
    assert p.endereco.uf == "RN"
    assert p.endereco.cep == "59082030"
    assert p.telefone == "8499034747"
    assert p.email == "PFCVALIAS@GMAIL.COM"

    t = nfse.tomador
    assert t.cnpj_cpf == "16699869000297"
    assert t.inscricao_municipal is None
    assert t.razao_social == "NAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA"
    assert t.endereco.logradouro == "RUA GABRIEL MONTEIRO DA SILVA"
    assert t.endereco.numero == "1480"
    assert t.endereco.complemento == "CASA TÉRREA"
    assert t.endereco.bairro == "JARDIM AMERICA"
    assert t.endereco.codigo_municipio == "3550308"
    assert t.endereco.uf == "SP"
    assert t.endereco.cep == "01442001"
    assert t.email == "lorena@nauticamoveis.com"
    assert t.telefone is None

    v = nfse.valores
    assert v.valor_servicos == pytest.approx(20857.95)
    assert v.valor_liquido_nfse == pytest.approx(20857.95)
    assert v.valor_deducoes == 0.0
    # Base/Alíquota/ISS mascarados ("*,**", Simples Nacional): nada inventado.
    assert v.base_calculo == pytest.approx(20857.95)
    assert v.aliquota == 0.0
    assert v.valor_iss == 0.0
    assert v.iss_retido is False
    for campo in ("valor_pis", "valor_cofins", "valor_inss", "valor_ir", "valor_csll", "outras_retencoes"):
        assert getattr(v, campo) == 0.0, campo
    assert any("Simples Nacional" in a and "ValorIss" in a for a in nfse.avisos)
    assert not any("capital" in a for a in nfse.avisos)

    xml = Abrasf201Transformer().transform(nfse)
    for trecho in ("<Numero>0000000015</Numero>", "<ValorServicos>20857.95</ValorServicos>",
                   "<ValorLiquidoNfse>20857.95</ValorLiquidoNfse>", "<ValorIss>0.00</ValorIss>",
                   "<Aliquota>0.00</Aliquota>", "<IssRetido>2</IssRetido>",
                   "<ItemListaServico>0701</ItemListaServico>",
                   "<MunicipioIncidencia>2408102</MunicipioIncidencia>",
                   "<OptanteSimplesNacional>1</OptanteSimplesNacional>",
                   "<DataEmissao>2026-03-17T17:30:28</DataEmissao>",
                   "<Competencia>2026-03-01</Competencia>"):
        assert trecho in xml, trecho


def test_natal_nao_rouba_nota_de_outra_cidade_que_cita_natal():
    """Guarda: "Natal" como município de prestador/tomador, sem o cabeçalho
    da prefeitura no topo, não é Nota Natalense."""
    texto = OCR_TEXT_NF15.replace("Prefeitura Municipal do Natal", "Prefeitura Municipal de Parnamirim")
    assert natal_nfse.eh_natal(texto) is False
    ex = SPPdfExtractor("tests/nao_existe_natal.pdf")
    assert ex._detect_layout_page(texto) != LAYOUT_NATAL
    # Cabeçalho da prefeitura só lá embaixo (endereço/observação): também não.
    assert natal_nfse.eh_natal("x\n" * 400 + OCR_TEXT_NF15) is False
    assert natal_nfse.eh_natal("") is False


def test_natal_grade_de_valores_preenchida():
    """Prestador fora do Simples: as 2 linhas da grade com os 5 valores
    cada são mapeadas por posição; ISS impresso, nunca recalculado."""
    texto = OCR_TEXT_NF15.replace(
        "Documento emitido por ME ou EPP optante pelo SIMPLES NACIONAL.", "").replace(
        "Outras Retenções (R$)\n", "Outras Retenções (R$)\n0,00 20.857,95 5,00 1.042,90 0,00\n").replace(
        "PIS/PASEP (R$)\n", "PIS/PASEP (R$)\n0,00 312,87 208,58 625,74 135,58\n")
    _, nfse = _parse_texto(texto)
    v = nfse.valores
    assert nfse.optante_simples_nacional is False
    assert v.base_calculo == pytest.approx(20857.95)
    assert v.aliquota == pytest.approx(0.05)
    assert v.valor_iss == pytest.approx(1042.90)
    assert (v.valor_inss, v.valor_ir, v.valor_csll, v.valor_cofins, v.valor_pis) == pytest.approx(
        (0.0, 312.87, 208.58, 625.74, 135.58))
    assert v.valor_liquido_nfse == pytest.approx(20857.95 - 312.87 - 208.58 - 625.74 - 135.58)
    assert not any("ISS" in a and "não fecha" in a for a in nfse.avisos)


def test_natal_guardas_sem_fabricar_valor():
    """Grade com célula em branco no meio (posição incerta), alíquota acima
    do teto, número ilegível e CNPJ com dígito errado: sentinela/0 + aviso."""
    texto = OCR_TEXT_NF15.replace(
        "Outras Retenções (R$)\n", "Outras Retenções (R$)\n0,00 20.857,95 7,00 1.042,90\n").replace(
        "PIS/PASEP (R$)\n", "PIS/PASEP (R$)\n312,87 625,74\n").replace(
        "Nº da Nota: 0000000015", "Nº da Nota: ").replace(
        "16.699.869/0002-97", "16.699.869/0002-98")
    _, nfse = _parse_texto(texto)
    v = nfse.valores
    assert nfse.numero == "00000000"
    assert any("Número da nota não lido" in a for a in nfse.avisos)
    assert any("dígito" in a and "tomador" in a for a in nfse.avisos)
    # 4 de 5 valores na 1ª linha / 2 de 5 na 2ª: nenhum usado.
    assert v.aliquota == 0.0 and v.valor_iss == 0.0
    assert (v.valor_ir, v.valor_cofins, v.valor_pis, v.valor_csll, v.valor_inss) == (0.0,) * 5
    assert v.base_calculo == pytest.approx(20857.95)
    assert sum("de 5 valores legíveis" in a for a in nfse.avisos) == 2

    # Alíquota impressa acima de 5% (erro de leitura): sentinela 0 + aviso.
    texto = OCR_TEXT_NF15.replace(
        "Outras Retenções (R$)\n", "Outras Retenções (R$)\n0,00 20.857,95 7,00 1.042,90 0,00\n")
    _, nfse = _parse_texto(texto)
    assert nfse.valores.aliquota == 0.0
    assert nfse.valores.valor_iss == pytest.approx(1042.90)
    assert any("teto legal de 5%" in a for a in nfse.avisos)


@pytest.mark.parametrize("raw,esperado", [
    ("PFCVALIASQGMAIL.COM", "PFCVALIAS@GMAIL.COM"),
    ("| lorenaQQnauticamoveis.com", "lorena@nauticamoveis.com"),
    ("fulano@empresa.com.br", "fulano@empresa.com.br"),
    ("FULANOQEMPRESA.COM.BR", None),  # domínio desconhecido: "@" ambíguo
    ("", None),
])
def test_natal_corrigir_email(raw, esperado):
    assert natal_nfse.corrigir_email(raw) == esperado


def test_natal_releitura_endereco_so_troca_espacos():
    linha = natal_nfse.linha_endereco_prestador(OCR_TEXT_NF15)
    assert linha.startswith("Endereço: RALDO DE MELO FREIRE")
    bom = "Endereço: R ALDO DE MELO FREIRE, 1876, APTO 502 , Capim Macio, 59082-030"
    novo = natal_nfse.aplicar_releitura_endereco(OCR_TEXT_NF15, linha, bom)
    assert "R ALDO DE MELO FREIRE, 1876" in novo
    assert novo.count("Endereço:") == OCR_TEXT_NF15.count("Endereço:")
    # Releitura com conteúdo diferente (dígito trocado) é ignorada.
    ruim = bom.replace("1876", "1878")
    assert natal_nfse.aplicar_releitura_endereco(OCR_TEXT_NF15, linha, ruim) == OCR_TEXT_NF15
    assert natal_nfse.aplicar_releitura_endereco(OCR_TEXT_NF15, linha, None) == OCR_TEXT_NF15


@pytest.mark.skipif(not os.path.exists(PDF_REAL), reason="PDF real indisponível")
def test_natal_pdf_real_ponta_a_ponta():
    """PDF real: OCR + recorte da linha de endereço ("R ALDO")."""
    ex = SPPdfExtractor(PDF_REAL)
    notas = ex.parse_multiple()
    assert len(notas) == 1
    nfse = notas[0]
    assert nfse.numero == "0000000015"
    assert nfse.prestador.endereco.logradouro == "R ALDO DE MELO FREIRE"
    assert nfse.valores.valor_servicos == pytest.approx(20857.95)
    assert nfse.tomador.cnpj_cpf == "16699869000297"
