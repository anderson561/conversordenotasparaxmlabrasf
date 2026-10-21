# -*- coding: utf-8 -*-
"""Fatura Sem Parar nº 709678135 (fatura 26200148983), pág. 3 do
"Scan2026-10-16_110738.pdf" (lote STAUMMAQ de 16/10/2026) - achado real
2026-10-21, layout `sem_parar_fatura` (LAYOUT_SEM_PARAR).

Impresso (conferido no pixel, render 4x) x XML antes da correção:
- Data de Emissão "08/09/26" (ano de 2 dígitos) -> saía 2026-09-01, o início
  do período do plano contratado, porque nenhum rótulo aceitava o ano curto.
- Subtotal R$ 3.438,18 + Outras Arrec. R$ 27,30 = TOTAL R$ 3.465,48 -> saía
  R$ 673,54: o OCR leu "Subtotal | R$3438,18D", o "|" impedia o rótulo de
  casar e o código caía no ramo SEM Subtotal, que somou células soltas da
  tabela por placa (37878D + 22267D + 7209D, esta da coluna Plano Contratado).
- Prestador "Av. Dra. Ruth Cardoso, 7221 ... 05425-902 - Pinheiros" -> saía
  "Não informado"/CEP 00000000: o OCR de página perdeu o "0" do CEP
  ("5425-902") e o recorte do cabeçalho trazia aspas soltas antes do "Av.".
- Tomador "Stammaq Servicos Tecnicos Automocao Motores E Maq" (assim, com o
  erro do próprio emitente) -> saía truncado "Stammaq Servicos Tecnicos Aut".
- Discriminação genérica -> agora montada só com dados impressos.

MOCK_P3 é o texto REAL do Tesseract para a página (verbatim). Os campos que
dependem dos recortes dedicados (cabeçalho do emitente, linha "Nome:" do
cliente) usam a saída REAL desses recortes, também verbatim.
"""
from datetime import datetime

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_P3 = """\
SEM PAI Ã
Sen anas nerrução oe ACAMENTOLTOA — NOTA FISCAL FATURA DE SERVIÇOS
5425-902 - Pinheiros - São Paulo/SP Nº DA FATURA: 26200148983

CNPJ/MF: 04.088.208/0001-65 - Insc. Municipal nº 6.486.165-1

Central de Relacionamento Pági
PAR À 4002 1552 (Capitais e regiões metropolitanas) BRA
0800 015 02 52 (Demais Localidades)

EMPRESAS

Nome: Stammaq Servicos Tecnicos Aut:

CNPJ: 02.370.080/0001-00 peca eres Ena
Endereço: Via Urbana, 1

Bairro: Companhia Sul

CEP: 43700-000

Cidade/UF: Simoes Filho - BA

Nº da Fatura: 26200148983
Nº da Nota Fiscal: 709678135
Código do Cliente: 2876948
E-Mail: sbrunoQOstaummag.com.br
CPF/CNPJ: 02.370.080/0001-00
Banco/Agência: 001/1223

Data de Emissão: 08/09/26

Data de Fechamento: 08/09/26
Débito em conta corrente

Banco Do Brasil

Agência: 1223

Data de Vencimento: 15/09/26
Prev. próx. faturamento: 08/10/26

PAGUE AGORA.
É RÁPIDO, SEGURO E EM ATÉ 1X.

MANTENHA O IPVA DA SUA FROTA EM DIA,
SEM PARAR EMPRESAS SEM PARAR A OPERAÇÃO.

0748423730 0 o 0,00 o 315,63D
0725512106 io Rique 000 O 546630
0736905078 42 0 0 0,00 O | 37878D
730451186 ro a pao an 000 0 202990
0731204546 7209D  150,58D 20 0 0 0,00 O 22267D
orsseriao! BAND DO OO  ro Eng Ra 000 0 64190
0740503362 64,78D 292,60 D 19 0,00 o. 0,00 0 0,00 o 357,38D
orasoBero ri sa ao do Bila CREAM o OR RD O 49,91 D
; em ! i Da É b Subtotal | R$3438,18D
“Adesão Qtd Crédito Qtd Encargos Impostosretidos OutrasArrec. Qtd Outros Serv. Qtd DemaisitensVP Qtd |
0,00 0 0,00 o 0,00 0,00 27,30 D 7 0,00 o) 0,00

Placa ba
NITORAMENTO DÉBITO VEI!

NTUB674
dra / CERIA SERVIÇOS DE SAUDE
Ê 01/09/2026 a 30/09/2026 | ADESÃO ZERO EMPRESARIAL - SKLSPE
oveseor "01/09/2026 8 30/09/2026 | PARCERIASERVIÇOSDESAUDE
MONITORAMENTO DÉBITO VEICULAR
“| ADESÃO ZERO EMPRESARIAL -SKLSPE

MONITORAMENTO DÉBITO VEICULAR
/09/2026 2 30/09/2026 PARCERIA SERVIÇOS DE SAUDE
01/09/2026 a 30/09/2026 EMPRESARIAL RODOVIAS SKL 2023 SPE
04/09/2026 2 30/09/2026 PARCERIA SERVIÇOS DESAUDE
01/09/2026 a 30/09/2026 MONITORAMENTO DÉBITO VEICULAR
/2026 a 30/09/2026 ADESÃO ZERO EMPRESARIAL - SKL'SPE |

Cuidado com os golpes e fraudes! Contar com nossos canais digitais é a forma mais fácil de garantir sua segurança! Por isso, em caso de necessidade de um novo boleto, utilize

exclusivamente: portal Sem Parar Empresas e Portal de Negociação! o.
Ao efetuar o pagamento de um boleto Sem Parar, confira se o beneficiário é SEM PARAR INSTITUIÇÃO DE PAGAMENTOS LTDA, com o CNPJ 04.088.208/0001-65. Atenção: Jamais

compartilhe suas senhas com terceiros.”
Central de Relacionamento SAC 0800 723 2245
4002 1552 (Capitais e regiões metropolitanas) SAC (Deficiência auditiva ou de fala) 0800 722 0270
0800 015 02 52 (Demais localidades) Ouvidoria 0800 770 0686

8769/82
"""

# Saída REAL de `_ocr_cabecalho_sem_parar` nesta página (300 dpi, psm 6).
RECORTE_CABECALHO = (
    'SEM PARAR INSTITUIÇÃO DE PAGAMENTO LTDA. NOTA\n\n'
    '" Av. Dra. Ruth Cardoso, 7221, Andares 17, 18, 19e 26 parte - o\n'
    '05425-902 - Pinheiros - São Paulo/SP Nº DA\n'
    'CNPJ/MF: 04.088.208/0001-65 - Insc. Municipal nº 6.486.165-1\n'
)
# Saída REAL de `_ocr_nome_cliente_sem_parar` nesta página.
RECORTE_NOME = 'Stammaq Servicos Tecnicos Automocao Motores E Maq'
# Como impresso — inclusive "Automocao", erro do próprio emitente.
NOME_IMPRESSO = 'Stammaq Servicos Tecnicos Automocao Motores E Maq'


def _parse(monkeypatch, tmp_path, mock, cabecalho='', nome=''):
    caminho = tmp_path / "sem parar - fatura 709678135.pdf"
    caminho.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: mock)
    monkeypatch.setattr(SPPdfExtractor, "_ocr_cabecalho_sem_parar", lambda self: cabecalho)
    monkeypatch.setattr(SPPdfExtractor, "_ocr_nome_cliente_sem_parar", lambda self: nome)
    notas = SPPdfExtractor(str(caminho)).parse_multiple()
    assert len(notas) == 1
    return notas[0]


@pytest.fixture
def nota(monkeypatch, tmp_path):
    return _parse(monkeypatch, tmp_path, MOCK_P3, RECORTE_CABECALHO, RECORTE_NOME)


@pytest.fixture
def nota_sem_recortes(monkeypatch, tmp_path):
    return _parse(monkeypatch, tmp_path, MOCK_P3)


def test_numero_da_nota(nota):
    assert nota.numero == "709678135"


# ------------------------------------------------------------ data de emissão

def test_data_de_emissao_com_ano_de_dois_digitos(nota_sem_recortes):
    assert "Data de Emissão: 08/09/26" in MOCK_P3
    assert nota_sem_recortes.data_emissao.date() == datetime(2026, 9, 8).date()


def test_data_de_emissao_nao_e_o_inicio_do_periodo_nem_o_vencimento(nota_sem_recortes):
    assert "01/09/2026 a 30/09/2026" in MOCK_P3
    assert "Data de Vencimento: 15/09/26" in MOCK_P3
    assert nota_sem_recortes.data_emissao.date() not in (
        datetime(2026, 9, 1).date(), datetime(2026, 9, 15).date())


# --------------------------------------------------------------------- valor

def test_valor_e_subtotal_mais_outras_arrecadacoes(nota_sem_recortes):
    """3.438,18 + 27,30 = 3.465,48, o TOTAL impresso (que o OCR perde)."""
    assert "Subtotal | R$3438,18D" in MOCK_P3
    v = nota_sem_recortes.valores
    assert v.valor_servicos == pytest.approx(3465.48)
    assert v.valor_liquido_nfse == pytest.approx(3465.48)


def test_valor_nao_e_mais_a_soma_de_celulas_soltas(nota_sem_recortes):
    assert nota_sem_recortes.valores.valor_servicos != pytest.approx(673.54)


def test_tributacao_segue_zerada_e_avisada(nota_sem_recortes):
    v = nota_sem_recortes.valores
    assert (v.base_calculo, v.aliquota, v.valor_iss) == (0.0, 0.0, 0.0)
    assert any("R$ 3.465,48" in a and "COMPOSTO" in a for a in nota_sem_recortes.avisos)


# ----------------------------------------------------------------- prestador

def test_prestador_endereco_vem_do_recorte_do_cabecalho(nota):
    assert "5425-902 - Pinheiros" in MOCK_P3     # o "0" do CEP se perdeu
    p = nota.prestador
    assert p.cnpj_cpf == "04088208000165"
    assert p.inscricao_municipal == "6.486.165-1"
    assert p.razao_social == "SEM PARAR INSTITUIÇÃO DE PAGAMENTO LTDA"
    e = p.endereco
    assert e.logradouro == "Av. Dra. Ruth Cardoso"
    assert e.numero == "7221"
    assert e.bairro == "Pinheiros"
    assert e.cep == "05425902"
    assert (e.codigo_municipio, e.uf) == ("3550308", "SP")


def test_prestador_sem_recorte_nao_inventa_cep(nota_sem_recortes):
    """Sem o recorte, o CEP de 4 dígitos do OCR de página NÃO é completado."""
    e = nota_sem_recortes.prestador.endereco
    assert e.cep == "00000000"
    assert e.logradouro == "Não informado"


# ------------------------------------------------------------------- tomador

def test_tomador_nome_completo_pelo_recorte(nota):
    assert "Nome: Stammaq Servicos Tecnicos Aut:" in MOCK_P3   # truncado na página
    assert nota.tomador.razao_social == NOME_IMPRESSO


def test_tomador_sem_recorte_mantem_a_leitura_de_pagina(nota_sem_recortes):
    assert nota_sem_recortes.tomador.razao_social == "Stammaq Servicos Tecnicos Aut"


def test_recorte_com_outro_nome_nao_substitui(monkeypatch, tmp_path):
    n = _parse(monkeypatch, tmp_path, MOCK_P3, RECORTE_CABECALHO,
               "Transportadora Qualquer Coisa Comercio De Pecas Ltda")
    assert n.tomador.razao_social == "Stammaq Servicos Tecnicos Aut"


def test_recorte_mais_curto_nao_substitui(monkeypatch, tmp_path):
    n = _parse(monkeypatch, tmp_path, MOCK_P3, RECORTE_CABECALHO, "Stammaq")
    assert n.tomador.razao_social == "Stammaq Servicos Tecnicos Aut"


def test_tomador_identificacao_e_endereco(nota):
    t = nota.tomador
    assert t.cnpj_cpf == "02370080000100"
    e = t.endereco
    assert (e.logradouro, e.numero, e.bairro, e.cep) == ("Via Urbana", "1", "Companhia Sul", "43700000")
    assert (e.codigo_municipio, e.uf) == ("2930709", "BA")


# ------------------------------------------------------------ discriminação

def test_discriminacao_montada_com_dados_impressos(nota_sem_recortes):
    assert nota_sem_recortes.discriminacao == (
        "Nota Fiscal Fatura de Serviços Sem Parar - Fatura nº 26200148983 - "
        "Plano contratado - período 01/09/2026 a 30/09/2026")


def test_discriminacao_nao_e_mais_a_generica(nota_sem_recortes):
    assert "conforme nota fiscal" not in nota_sem_recortes.discriminacao


# ------------------------------------------- não regressão: nota 705320619

def test_nota_705320619_mantem_valor_e_ganha_data_correta(monkeypatch, tmp_path):
    """Mesma fatura, mês anterior (texto real versionado em
    test_tomador_staummaq_scan2_paginas_1_e_9.py): valor inalterado; a data
    de emissão impressa "08/08/26" passa a ser lida."""
    from tests.test_tomador_staummaq_scan2_paginas_1_e_9 import MOCK_P1
    n = _parse(monkeypatch, tmp_path, MOCK_P1)
    assert n.numero == "705320619"
    assert n.valores.valor_servicos == pytest.approx(3844.86)
    assert "Data de Emissão: 08/08/26" in MOCK_P1
    assert n.data_emissao.date() == datetime(2026, 8, 8).date()
    assert n.discriminacao == (
        "Nota Fiscal Fatura de Serviços Sem Parar - Fatura nº 26176766483 - "
        "Plano contratado - período 01/08/2026 a 31/08/2026")
