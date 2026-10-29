# -*- coding: utf-8 -*-
"""NFS-e PADRÃO da Prefeitura de Osasco/SP (LAYOUT_OSASCO_NFSE).

Achado real 2026-10-26: "Scan2026-10-26_095816.pdf", pág. 3 — NFS-e nº
0031865893, IFOOD.COM AGENCIA DE RESTAURANTES ONLINE S.A. (Osasco/SP) ->
RG RESTAURANTE LTDA (Camaçari/BA), R$ 2.733,82. A página caía em
LAYOUT_GENERICO e era descartada ("Layout não reconhecido"): nenhum XML.
Não é a NF-R de repasse (LAYOUT_OSASCO_REPASSE), que tem blocos
EMITENTE/RECEPTOR e não tem grade de ISS.

MOCK_TEXT abaixo é o texto REAL do OCR (Tesseract, `_ocr_page`) da página,
incluindo o ruído do carimbo/anotação à caneta (". A\ndio Wo alo fu)").
"""
import os
import pytest
from src.extractors.pdf_extractor import (
    SPPdfExtractor, LAYOUT_OSASCO_NFSE, LAYOUT_OSASCO_REPASSE, LAYOUT_GENERICO,
)
from src.transformers.abrasf_transformer import Abrasf201Transformer

MOCK_TEXT = (
    'PREFEITURA DO MUNICÍPIO DE OSASCO\n'
    'Secretaria de Finanças\n'
    '\n'
    'Nota Fiscal de Serviços Eletrônica (NFS-e)\n'
    '\n'
    'Nota Nº; Emissão: érie: RPSNº:\n'
    '\n'
    '0031865893 06/09/2026\n'
    '\n'
    'PRESTADOR DO SERVIÇO\n'
    '\n'
    'CNPJ/CPF: 14.380.200/0001-21\n'
    '\n'
    'RPS Emissão:\n'
    '\n'
    '31/08/2026\n'
    '\n'
    'Equipamento: Ref. Fiscal:\n'
    '\n'
    '08/2026\n'
    '\n'
    '0035159726\n'
    '\n'
    'Inscrição Municipal: 131108\n'
    '\n'
    'Razão Social: IFOOD.COM AGENCIA DE RESTAURANTES ONLINE S.A.\n'
    '\n'
    'Endereço: AV. dos Autonomistas, 1496 - Vila Yara - 06020-012\n'
    '\n'
    'Município: Osasco UF: SP Telefone: (00)3498-8402\n'
    '\n'
    'TOMADOR DO SERVIÇO\n'
    'CNPJ/CPF: 23.918.316/0001-62\n'
    '\n'
    'Razão Social: RG RESTAURANTE LTDA\n'
    '\n'
    'Inscrição Municipal:\n'
    '\n'
    'Endereço: R Rodovia BA-535, O - Industrial - 42800-938 - País: BRASIL\n'
    'Município: Camaçari UF: BA\n'
    '\n'
    'Cód. do Serviço: 10.02 - Agenciamento, corretagem ou intermediação de títulos em geral, valores mobiliários, contratos quaisquer.\n'
    '\n'
    'NBS: 1.0905.11.00 Classif. Trib.: 000001 Ind. Operação: 100301\n'
    'Discriminação do Servico:\n'
    '\n'
    'AGENCIAMENTO CORRETAGEM E INTERMEDIACAO.\n'
    '\n'
    'Desconto incondicional: R$ -3.365,46\n'
    '\n'
    'Valor aproximado dos impostos R$ 307,56 (11.25%)\n'
    'conforme lei da transparencia 12.741/12. Fonte: IBPT\n'
    'Regra Geral\n'
    '\n'
    'Local. Incid.: Domicílio principal do adquirente\n'
    '\n'
    '. A\n'
    'dio Wo alo fu)\n'
    'Valor Total do Serviço Base de Cálculo (ISS) Alíg. ISS Valor ISS a Recolher\n'
    '2.733,82 2.733,82 2,00% 54,68\n'
    '\n'
    'Tributação Federal - Impostos Retidos na Fonte\n'
    '\n'
    'Pis: 0,00 Cofins: 0,00 CSLL: 0,00 IRRF: 0,00 INSS: 0,00\n'
    '\n'
    'Tributação Federal - Impostos Não Retidos PIS: 45,11 Cofins: 207,77\n'
    '\n'
    'Base de Cálculo IVA: 2.426,26 IBS-UF: 243 IBS-Mun: 0,00\n'
    'Autenticador: HYMUXRDB Ri a] Valor Total da Nota: 2.733,82\n'
    '\n'
    'Emissão: | Emissão: 06/09/2026 11:04:49 | 11:04:49 Chave NFS-e:  NFS35344011214380200000121000003186589326092449364116\n'
    'Local da DE do Serviço: Rodovia BA-535 42800938 Camaçari/BA\n'
    '\n'
    "Nota fiscal emitida em 06/09/2026 às 07:04 ISS Devido pelo Prestador do Serviço Prestador de Serviço enquadrado em regime de 'ISS\n"
    "Auto-Lançado' Emissão de Notas de Repasse - Série R2 (Dedutível na NF-E) - Proc. Adm. Nº 202302160105.\n"
    '\n'
    'Outros: 0,00\n'
    '\n'
)


@pytest.fixture
def nfse(monkeypatch, tmp_path):
    dummy = tmp_path / "dummy_osasco_nfse.pdf"
    dummy.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_TEXT)
    notas = SPPdfExtractor(str(dummy)).parse_multiple()
    assert len(notas) == 1, "a página era descartada como 'Layout não reconhecido'"
    return notas[0]


def _extrator(texto):
    e = SPPdfExtractor.__new__(SPPdfExtractor)
    e.raw_text = texto
    return e


def test_deteccao_layout_osasco_nfse():
    assert _extrator(MOCK_TEXT)._detect_layout_page(MOCK_TEXT) == LAYOUT_OSASCO_NFSE


def test_nfr_repasse_continua_no_layout_proprio():
    # A NF-R também imprime "Prefeitura do Município de Osasco"; o título
    # "Nota Fiscal Eletrônica de Repasse" tem prioridade.
    nfr = ("Prefeitura do Município de Osasco\nSecretaria de Finanças\n"
           "Nota Fiscal Eletrônica de Repasse - NF-R\nSérie: RI Nota No.: 2279456\n"
           "EMITENTE\nRazão Social/Nome: IFOOD BENEFICIOS E SERVICOS LTDA.\n"
           "RECEPTOR\nCódigo de autenticidade: CKIGTPTE\n")
    assert _extrator(nfr)._detect_layout_page(nfr) == LAYOUT_OSASCO_REPASSE
    # Sem título de repasse e sem rótulo estrutural da NFS-e: não vira NFS-e.
    so_cidade = "Prefeitura do Município de Osasco\nEMITENTE\nRECEPTOR\nCódigo de autenticidade: X\n"
    assert _extrator(so_cidade)._detect_layout_page(so_cidade) != LAYOUT_OSASCO_NFSE


def test_cabecalho(nfse):
    assert nfse.numero == "0031865893"          # como impresso (zeros à esquerda)
    assert nfse.codigo_verificacao == "HYMUXRDB"  # "Autenticador"
    d = nfse.data_emissao
    assert (d.year, d.month, d.day, d.hour, d.minute, d.second) == (2026, 9, 6, 11, 4, 49)


def test_competencia_ref_fiscal_prevalece(nfse):
    # Decisão do usuário 2026-10-26: Ref. Fiscal impressa (08/2026) vence o
    # mês da emissão (09/2026).
    assert (nfse.competencia.year, nfse.competencia.month, nfse.competencia.day) == (2026, 8, 1)


def test_prestador(nfse):
    p = nfse.prestador
    assert p.cnpj_cpf == "14380200000121"
    assert p.inscricao_municipal == "131108"
    assert p.razao_social == "IFOOD.COM AGENCIA DE RESTAURANTES ONLINE S.A."
    assert p.endereco.logradouro == "AV. dos Autonomistas"
    assert p.endereco.numero == "1496"
    assert p.endereco.bairro == "Vila Yara"
    assert p.endereco.cep == "06020012"
    assert p.endereco.uf == "SP"
    assert p.endereco.codigo_municipio == "3534401"


def test_tomador(nfse):
    t = nfse.tomador
    assert t.cnpj_cpf == "23918316000162"
    assert t.razao_social == "RG RESTAURANTE LTDA"
    assert t.inscricao_municipal is None
    assert t.endereco.logradouro == "R Rodovia BA-535"
    assert t.endereco.numero == "0"      # OCR lê "O"
    assert t.endereco.bairro == "Industrial"
    assert t.endereco.cep == "42800938"  # sufixo "- País: BRASIL" removido
    assert t.endereco.uf == "BA"
    assert t.endereco.codigo_municipio == "2905701"


def test_servico_e_discriminacao(nfse):
    assert nfse.servico_codigo == "1002"
    assert nfse.discriminacao == (
        "AGENCIAMENTO CORRETAGEM E INTERMEDIACAO. Desconto incondicional: R$ -3.365,46 "
        "Valor aproximado dos impostos R$ 307,56 (11.25%) conforme lei da transparencia "
        "12.741/12. Fonte: IBPT Regra Geral")
    # ruído do carimbo/caneta não entra
    assert "Wo alo" not in nfse.discriminacao
    assert "Local. Incid" not in nfse.discriminacao


def test_valores(nfse):
    v = nfse.valores
    assert v.valor_servicos == pytest.approx(2733.82)
    assert v.base_calculo == pytest.approx(2733.82)
    assert v.aliquota == pytest.approx(0.02)
    assert v.valor_iss == pytest.approx(54.68)
    assert v.iss_retido is False
    # Retidos todos 0,00; os "Não Retidos" (PIS 45,11 / Cofins 207,77) não
    # são retenção.
    for campo in ("valor_pis", "valor_cofins", "valor_csll", "valor_ir", "valor_inss", "outras_retencoes"):
        assert getattr(v, campo) == 0.0, campo
    assert v.valor_liquido_nfse == pytest.approx(2733.82)
    # Desconto incondicional só na discriminação: valores impressos intactos.
    assert v.desconto_incondicionado == 0.0


def test_xml_incidencia_osasco(nfse):
    # Decisão do usuário 2026-10-26: ISS incide em OSASCO (prestador, "ISS
    # Auto-Lançado"); "Domicílio principal do adquirente" é do IBS/CBS.
    xml = Abrasf201Transformer().transform(nfse)
    assert "<MunicipioIncidencia>3534401</MunicipioIncidencia>" in xml
    assert "<MunicipioIncidencia>2905701</MunicipioIncidencia>" not in xml
    assert "<IssRetido>2</IssRetido>" in xml
    assert "<ItemListaServico>1002</ItemListaServico>" in xml
    assert "<Competencia>2026-08-01</Competencia>" in xml


def test_numero_pela_chave_quando_cabecalho_some():
    texto = MOCK_TEXT.replace("0031865893 06/09/2026", "")
    e = _extrator(texto)
    e.layout = LAYOUT_OSASCO_NFSE
    assert e._chave_osasco_nfse() == "35344011214380200000121000003186589326092449364116"
    assert e._extrair_numero() == "31865893"


PDF_REAL = r"L:\USUARIOS\ANDERSON\ARQUIVOS DESKTOP\Notas\Scan2026-10-26_095816.pdf"


@pytest.mark.skipif(not os.path.exists(PDF_REAL), reason="PDF real do usuário indisponível")
def test_pdf_real_quatro_paginas():
    """Págs. 1, 2 e 4 continuam saindo iguais; a pág. 3 passa a gerar XML."""
    notas = SPPdfExtractor(PDF_REAL).parse_multiple()
    por_pag = {n.pagina_origem: n for n in notas}
    assert sorted(por_pag) == [1, 2, 3, 4]
    assert por_pag[1].numero == "6"
    assert por_pag[2].numero == "00188671"
    assert por_pag[4].numero == "829"
    p3 = por_pag[3]
    assert p3.numero == "0031865893"
    assert p3.prestador.cnpj_cpf == "14380200000121"
    assert p3.tomador.cnpj_cpf == "23918316000162"
    assert p3.valores.valor_servicos == pytest.approx(2733.82)
