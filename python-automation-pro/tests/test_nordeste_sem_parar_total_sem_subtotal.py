# -*- coding: utf-8 -*-
"""Nota Sem Parar nº 705900227 (2ª nota do lote "NORDESTE TUBETES -
SCAN.pdf"), achado real 2026-09-17 - VARIANTE do template `sem_parar_fatura`
(LAYOUT_SEM_PARAR, criado pelo esforço #3/nota Staummaq) que NÃO imprime
nenhum rótulo "Subtotal": o "Resumo da sua Fatura" fecha direto num "TOTAL"
cuja linha o OCR lê com confiança baixíssima demais para usar ("TOTAL
8B07,00D" em vez de "807,00 D"). Sem "Subtotal", o código anterior
retornava `valor_servicos=0.0` incondicionalmente.

Fix: quando "Subtotal" está ausente, soma-se em vez disso (a) a coluna
"TOTAL" de cada linha da tabela por placa - última célula, sempre no
formato "<valor>D" colado ao fim, tratada pela mesma convenção "2 últimos
dígitos são centavos" já usada em `_parse_valor_camacari` - com (b) o
"TOTAL OUTRAS ARRECADAÇÕES" (rótulo próprio, valor limpo, sem o ruído de
OCR que degrada a tabela). Conferido na nota real: 45,40 + 96,70 + 308,00 +
281,90 (4 linhas por placa) + 75,00 (outras arrecadações) = 807,00.

O caso em que "Subtotal" ESTÁ presente (template original, nota Staummaq -
ver `test_tomador_staummaq_scan2_paginas_1_e_9.py`) continua funcionando
exatamente como antes; este arquivo trava as duas variantes lado a lado.
"""
import pytest

from src.extractors.pdf_extractor import SPPdfExtractor

# Cabeçalho comum às duas variantes: mesmo template/emitente (CNPJ raiz
# 04.088.208), tomador fictício de Dias d'Ávila/BA (município recém-
# cadastrado em `IBGEResolver.KNOWN_CITIES` para esta mesma nota).
_HEADER = (
    "SEM PARAR INSTITUIÇÃO DE PAGAMENTOS LTDA. NOTA FISCAL FATURA DE SERVIÇOS\n"
    "05425-902 - Pinheiros - São Paulo/SP Nº DA FATURA: 26176766999\n\n"
    "CNPJ/MF: 04.088.208/0001-65 - Insc. Municipal nº 6.486.165-1\n\n"
    "EMPRESAS\n\n"
    "Nome: NORDESTE TUBETES LTDA\n"
    "CNPJ: 11.222.333/0001-81\n\n"
    "Endereço: Via Exemplo, 100\n"
    "Bairro: Centro\n\n"
    "CEP: 44580-000\n\n"
    "Cidade/UF: Dias Davila - BA\n\n"
    "Nº da Nota Fiscal: 705900227\n\n"
)

# Variante SEM "Subtotal" (achado real, nota nº 705900227): tabela por placa
# com 4 linhas + "TOTAL OUTRAS ARRECADAÇÕES" limpo, fechando num "TOTAL" com
# confiança de OCR baixa demais para usar.
MOCK_SEM_SUBTOTAL = _HEADER + (
    "Placa Ref Estabelecimento Total\n"
    "NTUB674 0748423730 4540D\n"
    "PKJ3F66 0736905078 9670D\n"
    "PkJ7438 0730451186 30800D\n"
    "PKW7748 0731204546 28190D\n\n"
    "TOTAL OUTRAS ARRECADAÇÕES 75,00\n\n"
    "TOTAL 8B07,00D\n"
)

# Variante COM "Subtotal" (template original, mesmo racional da nota
# Staummaq): Subtotal + Outras Arrec., sem tabela por placa relevante aqui.
MOCK_COM_SUBTOTAL = _HEADER + (
    "Placa Ref Estabelecimento Total\n"
    "NTUB674 0748423730 4540D\n"
    "Subtotal R$ 3.817,56 D\n"
    "Impostosretidos OutrasArrec. Qtd OutrosServ. Qtd Demaisitensvp Qtd\n"
    "0,00 2730D 7 0,00 0 0,00 0\n"
)

# Variante sem "Subtotal" E sem nenhuma rubrica somável (nem placas, nem
# outras arrecadações) - não existe "meio total": fica honestamente 0,00.
MOCK_SEM_NENHUMA_RUBRICA = _HEADER + (
    "TOTAL 8B07,00D\n"
)


def _parse(monkeypatch, tmp_path, mock, nome_arquivo):
    caminho = tmp_path / nome_arquivo
    caminho.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: mock)
    extractor = SPPdfExtractor(str(caminho))
    notas = extractor.parse_multiple()
    assert len(notas) == 1
    return notas[0]


@pytest.fixture
def nota_sem_subtotal(monkeypatch, tmp_path):
    return _parse(monkeypatch, tmp_path, MOCK_SEM_SUBTOTAL, "nordeste tubetes - pagina 1.pdf")


@pytest.fixture
def nota_com_subtotal(monkeypatch, tmp_path):
    return _parse(monkeypatch, tmp_path, MOCK_COM_SUBTOTAL, "staummaq - fatura.pdf")


@pytest.fixture
def nota_sem_nenhuma_rubrica(monkeypatch, tmp_path):
    return _parse(monkeypatch, tmp_path, MOCK_SEM_NENHUMA_RUBRICA, "nordeste tubetes - sem rubrica.pdf")


def test_total_sem_subtotal_soma_placas_mais_outras_arrecadacoes(nota_sem_subtotal):
    """45,40 + 96,70 + 308,00 + 281,90 (colunas TOTAL por placa) + 75,00
    (TOTAL OUTRAS ARRECADAÇÕES) = 807,00 - batendo com o TOTAL impresso,
    ainda que a própria linha do TOTAL seja ilegível ao OCR."""
    v = nota_sem_subtotal.valores
    assert v.valor_servicos == pytest.approx(807.00)
    assert v.valor_liquido_nfse == pytest.approx(807.00)
    assert "Subtotal" not in MOCK_SEM_SUBTOTAL
    assert "8B07,00D" in MOCK_SEM_SUBTOTAL  # a linha do TOTAL, essa o OCR perde


def test_sem_subtotal_base_aliquota_iss_zerados_com_aviso(nota_sem_subtotal):
    v = nota_sem_subtotal.valores
    assert v.base_calculo == 0.0
    assert v.aliquota == 0.0
    assert v.valor_iss == 0.0
    assert any("ZERADOS propositalmente" in a for a in nota_sem_subtotal.avisos)


def test_com_subtotal_comportamento_anterior_preservado(nota_com_subtotal):
    """Regressão: a variante ORIGINAL (com "Subtotal") continua somando
    Subtotal + Outras Arrec., sem passar pelo novo ramo por placa."""
    v = nota_com_subtotal.valores
    assert v.valor_servicos == pytest.approx(3844.86)
    assert v.valor_liquido_nfse == pytest.approx(3844.86)
    assert v.base_calculo == 0.0
    assert v.aliquota == 0.0
    assert v.valor_iss == 0.0


def test_sem_subtotal_e_sem_nenhuma_rubrica_fica_zerado_honestamente(nota_sem_nenhuma_rubrica):
    """Não existe "meio total": sem Subtotal, sem linhas por placa e sem
    "TOTAL OUTRAS ARRECADAÇÕES", o valor fica 0,00 em vez de inventado."""
    v = nota_sem_nenhuma_rubrica.valores
    assert v.valor_servicos == 0.0
    assert v.valor_liquido_nfse == 0.0
