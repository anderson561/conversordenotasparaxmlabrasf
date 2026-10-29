# -*- coding: utf-8 -*-
"""Fatura Sem Parar nº 710253204 (fatura 26202710742), pág. 2 do
"Scan2026-10-26_095859.pdf" - achado real 2026-10-26, layout
`sem_parar_fatura` (LAYOUT_SEM_PARAR), cliente Nordeste Tubetes.

Impresso (conferido no pixel, render 300-500 dpi) x XML antes da correção:
- Resumo: GHF5G48 544,20 + PDC2I48 154,00 + SJW4B44 257,10 (= 955,30) +
  Outras Arrec. 75,00 = TOTAL 1.030,30 D -> saía R$ 7,70. Esta variante não
  imprime "Subtotal"; o ramo antigo somava QUALQUER "<3-6 dígitos>D" da
  página e o único que casou foi um pedágio solto do "Detalhamento das
  Passagens" ("770D"). Decisão do usuário: valor = TOTAL da fatura.
- Endereço "Boa Viagem, 146 0" -> saía logradouro "Boa Viagem, 146 0" e
  Número "S/N".

MOCK_P2 é o texto REAL do Tesseract para a página (verbatim).
"""
from datetime import datetime

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_P2 = """\
Av. Dra. Ruth Cardoso, 7221, Andares 17, 18, 19 e 26 parte -
05425-902 - Pinheiros - São Paulo/SP

SEMP

Central de Relacionamento

SEM PARAR INSTITUIÇÃO DE PAGAMENTO LTDA.

CNPJ/MF: 04.088.208/0001-65 - Insc. Municipal nº 6.486.165-1

NOTA FISCAL FATURA DE SERVIÇOS
Nº DA FATURA: 26202710742

Página 1/3

90ZLL94

4002 1552 (Capitais e regiões metropolitanas)
0800 015 02 52 (Demais Localidades)

PARAR

EMPRESAS

Nome: Nordeste Tubetes Embalagens Ltda Me
CNPJ: 11.474.414/0001-79

Endereço: Boa Viagem, 146 0

Bairro: Parque Petropolis

CEP: 42850-000

Cidade/UF: Dias D'avila - BA

Nº da Fatura: 26202710742
Nº da Nota Fiscal: 710253204

Código do Cliente: 4611706

E-Mail: rodrigoQOnordestetubetes.com.br
CPF/CNPJ: 11.474.414/0001-79
Banco/Agência: 341/9658

Data de Emissão: 13/09/26

Data de Fechamento: 13/09/26
Débito em conta corrente

Bancc Itau

Agência: 9658

Data de Vencimento: 20/09/26
Prev. próx. faturamento: 13/10/26

PAGUE AGORA. .

3

É RÁPIDO, SEGURO E EM ATÉ 2X.
MANTENHA O IPVA DA SUA FROTA EM DIA,

SEM PARAR A OPERAÇÃO.
;

través do portal Sem Parar Empresas.

Extrato de Uso

ca no a Ria Resumo da sua Fatura :
Placa Tag Pref. Plano Contratado

Passagens Qtd Estacionamento Qtd Estabelecimento Qtd Vale Pedágio Qtd TOTAL

GHFSG48 0746771722 0,00 200,20 D 26 344,00D 4 0,00 o 0,00 0 544,20D

PDC2148 0736697948 0,00 154,00D0 20 0,00 (o) 0,00 [o] 0,00 | 154,00 D

SJW4B44 0742130710 0,00 212100 27 45,00D 2 0,00 o 0,00 0 257,10D

Adesão Qtd Crédito Qtd Encargos Impostos retidos OutrasArrec. Qtd Outros Serv. Qtd Demais tens VP Qtd
0,00 0 0,00 [o 0,00 0,00 75,00 D 1 0,00 (o 0,00 0
TOTAL í Ep no E É Fa : 1.030,30 D
Detalhamento de Outras Arrecadações

Data Placa Tipo Descrição Valor(R$)
10/09/26 - TAXA DE SERVICO TAXA DE SERVICO Vencimento: 20/09/2026 | TAXA DE SERVICO 75,00D

- TOTAL OUTRAS ARRECADAÇÕES ; BR CM : 75,00D.

Descritivo: GHF5G48 - Plano: PAGAMENTO COM CARGA PROGRAMADA
Detalhamento das Estadias em Estacionamentos
Data Saída Permanência Local Valor(R$)
27/08/26 -08:41:46  30/08/26-20:12:15  83h31m2ºs — 45124- AEROPORTO SALVADO 300,00 D
31/08/26 -09:10:02  31/08/26- 11:55:41 02h45maz9s SHOPPING PARALELA é 16,00 D
01/09/26 09:38:48 01/09/26- 11:54:38  02h16m50s — SHOPPING PARALELA 16,00 D
09/09/26-13:24:51  09/09/26- 16:56:04  03h32mi3s — SHOPSCP PARQUE BAHIA 12,00D
Detalhamento das Passagens por Pedágios

Data Hora Concessionária Praça Cat Valor(R$)
17/08/26 | 15:42:48 BAHIA NORTE BAS39, KM016+000, SUL, VIA PARAFUSO 1 7,100
18/08/26 17:11:40 BAHIA NORTE BAS39, KM008+000, NORTE, SIMOES FILHO 1 770D
18/08/26 17:42:51 BAHIA NORTE BAS39, KM015+400, NORTE, CIA AEROPORTO 1 7,100
18/08/26 19:31:39 BAHIA NORTE BAS539, KM016+000, SUL, VIA PARAFUSO 1 7,700
21/08/26 1s:sz:a7 BAHIA NORTE BAS539, KM008+000, NORTE, SIMOES FILHO 1 7,70D
21/08/26 21:25:53 BAHIA NORTE BAS39, KM016+000. VIA PARAFUSO 1 7,700

Cuidado com os golpes e fraudes! Contar com nossos can is digitais é a Forma mais fácil de
exclusivamente: portal Sem Parar Empresas e Portal de Nogociação!

Ao efetuar o pagamento de um boleto Sem Parar, confira se o beneficiário é SEM PARAR INSTITUIÇÃO DE PAGAMENTOS LTDA, com o CNP) 04.088.208/0001-65, Atenção: J.
compartilhe suas senhas com terceiros.”

garantir sua segu; 2nça! Por isso, em caso de necessidade de um novo boleto, utilize

Jamais

Central de Relacionamento
4002 1552 (Capitais e regiões metropolitanas)
0800 015 02 52 (Demais localidades)

SAC 0800 723 2245
SAC (Deficiência auditiva ou de fala) 0800 722 0270
Ouvidoria 0800 770 0686
"""


# Saída REAL de `_ocr_cabecalho_sem_parar` nesta página (300 dpi, psm 6).
RECORTE_CABECALHO = (
    'SEM PARAR INSTITUIÇÃO DE PAGAMENTO LTDA. NOT\n'
    'Av. Dra. Ruth Cardoso, 7221, Andares 17, 18, 19 e 26 parte - o\n'
    '05425-902 - Pinheiros - São Paulo/SP NºD\n'
    'CNPJ/MF: 04.088.208/0001-65 - Insc. Municipal nº 6.486.165-1\n'
)
# Saída REAL de `_ocr_nome_cliente_sem_parar` nesta página.
RECORTE_NOME = 'Nordeste Tubetes Embalagens Ltda Me'


def _parse(monkeypatch, tmp_path, mock, cabecalho=RECORTE_CABECALHO, nome=RECORTE_NOME):
    caminho = tmp_path / "sem parar - fatura 710253204.pdf"
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
    return _parse(monkeypatch, tmp_path, MOCK_P2)


@pytest.fixture
def nota_sem_recortes(monkeypatch, tmp_path):
    return _parse(monkeypatch, tmp_path, MOCK_P2, "", "")


# --------------------------------------------------------------------- valor

def test_valor_independe_dos_recortes(nota_sem_recortes):
    assert nota_sem_recortes.valores.valor_servicos == pytest.approx(1030.30)


def test_valor_e_o_total_impresso_da_fatura(nota):
    assert "Subtotal" not in MOCK_P2
    assert "1.030,30 D" in MOCK_P2
    v = nota.valores
    assert v.valor_servicos == pytest.approx(1030.30)
    assert v.valor_liquido_nfse == pytest.approx(1030.30)
    assert (v.base_calculo, v.aliquota, v.valor_iss) == (0.0, 0.0, 0.0)


def test_valor_nao_e_mais_o_pedagio_solto(nota):
    assert "770D" in MOCK_P2   # pedágio do detalhamento, 7,70
    assert nota.valores.valor_servicos != pytest.approx(7.70)


def test_aviso_identifica_o_total_impresso_sem_divergencia(nota):
    assert any("R$ 1.030,30" in a and "TOTAL impresso" in a for a in nota.avisos)
    assert not any("DIVERGÊNCIA" in a for a in nota.avisos)


def _sem_linha_total(texto):
    return "\n".join(l for l in texto.split("\n") if not l.startswith("TOTAL í"))


def test_sem_total_legivel_soma_coluna_total_das_placas(monkeypatch, tmp_path):
    """544,20 + 154,00 + 257,10 + 75,00 (TOTAL OUTRAS ARRECADAÇÕES) =
    1.030,30 - só a ÚLTIMA célula das linhas de placa entra na soma."""
    n = _parse(monkeypatch, tmp_path, _sem_linha_total(MOCK_P2))
    assert n.valores.valor_servicos == pytest.approx(1030.30)
    assert any("COMPOSTO" in a and "placa" in a for a in n.avisos)


def test_placa_com_ultima_celula_ilegivel_zera_com_aviso(monkeypatch, tmp_path):
    """Uma linha de placa sem a coluna TOTAL legível invalida a soma inteira
    (soma parcial pareceria completa): 0,00 + aviso, nunca células soltas."""
    texto = _sem_linha_total(MOCK_P2).replace("0,00 0 257,10D", "0,00 0 2S7,1OD")
    n = _parse(monkeypatch, tmp_path, texto)
    assert n.valores.valor_servicos == 0.0
    assert any("ZERADO" in a for a in n.avisos)


def test_total_impresso_divergente_das_rubricas_gera_aviso(monkeypatch, tmp_path):
    texto = MOCK_P2.replace("Fa : 1.030,30 D", "Fa : 1.080,30 D")
    n = _parse(monkeypatch, tmp_path, texto)
    assert n.valores.valor_servicos == pytest.approx(1080.30)
    assert any("DIVERGÊNCIA" in a and "1.030,30" in a for a in n.avisos)


# --------------------------------------------------------- demais campos

def test_numero_data_e_discriminacao(nota):
    assert nota.numero == "710253204"
    assert nota.data_emissao.date() == datetime(2026, 9, 13).date()
    assert nota.discriminacao == (
        "Nota Fiscal Fatura de Serviços Sem Parar - Fatura nº 26202710742")


def test_prestador(nota):
    p = nota.prestador
    assert p.cnpj_cpf == "04088208000165"
    assert p.inscricao_municipal == "6.486.165-1"
    e = p.endereco
    assert (e.logradouro, e.numero, e.bairro, e.cep) == (
        "Av. Dra. Ruth Cardoso", "7221", "Pinheiros", "05425902")
    assert (e.codigo_municipio, e.uf) == ("3550308", "SP")


def test_tomador(nota):
    t = nota.tomador
    assert t.cnpj_cpf == "11474414000179"
    assert t.razao_social == "Nordeste Tubetes Embalagens Ltda Me"
    e = t.endereco
    assert "Endereço: Boa Viagem, 146 0" in MOCK_P2
    assert (e.logradouro, e.numero, e.bairro, e.cep) == (
        "Boa Viagem", "146 0", "Parque Petropolis", "42850000")
    assert (e.codigo_municipio, e.uf) == ("2910057", "BA")
