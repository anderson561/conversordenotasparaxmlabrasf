# -*- coding: utf-8 -*-
"""Ordem de leitura do pdfminer independente do estado do processo.

Achado real 2026-11-16: DANFSe v2.0 nº 3615 ("norta notalize.pdf", NOTALIZE
TECNOLOGIA LTDA, Campo Grande/MS -> NORTE SOLUCOES CONTABEIS SOCIEDADE
SIMPLES, Salvador/BA). Convertida sozinha num processo novo, sempre certa;
convertida depois de outros PDFs no mesmo processo (corpus sequencial, lote
da GUI) o CodigoMunicipio/Cep do prestador e do tomador saíam TROCADOS.

Causa raiz: `pdfminer.layout.LTLayoutContainer.group_textboxes` desempata
distâncias iguais pelo `id()` dos objetos — o endereço de memória, que
depende de tudo o que o processo já alocou. A ordem do `extract_text` mudava
e a colheita por ORDINAL da DANFSe v2.0 (1ª ocorrência = prestador) herdava
a troca. A correção (`src/utils/pdfminer_deterministico.py`) desempata por
sequência estável.

Os testes simulam "outro estado de memória" trocando o `id` que o módulo
`pdfminer.layout` enxerga por `-id(obj)` (inverte a ordem dos endereços):
no código antigo o resultado muda; no corrigido, não.
"""
import builtins
import os
from contextlib import contextmanager

import pytest

import src.extractors  # noqa: F401 - instala o desempate determinístico
import pdfminer.layout as pdfminer_layout
from pdfminer.high_level import extract_text

from src.extractors.pdf_extractor import SPPdfExtractor

PDF_NORTA = r'L:\USUARIOS\ANDERSON\ARQUIVOS DESKTOP\Notas\norta notalize.pdf'
precisa_pdf_norta = pytest.mark.skipif(not os.path.exists(PDF_NORTA), reason='PDF real da nota nº 3615 indisponível')


@contextmanager
def _enderecos_invertidos():
    """Outro "histórico do processo": `id()` visto pelo pdfminer invertido."""
    pdfminer_layout.id = lambda obj: -builtins.id(obj)
    try:
        yield
    finally:
        del pdfminer_layout.id


def _arvore(no):
    nome = getattr(no, 'nome', None)
    return nome if nome else tuple(_arvore(filho) for filho in no)


def test_agrupamento_de_caixas_empatadas_nao_depende_do_endereco_de_memoria():
    # Três caixas iguais em linha, mesmo espaçamento: dist(A,B) == dist(B,C).
    # O pdfminer original agrupava (A,B) ou (B,C) conforme o id() de cada uma.
    container = pdfminer_layout.LTLayoutContainer((0, 0, 600, 100))
    caixas = []
    for nome, x in zip('ABC', (0, 200, 400)):
        caixa = pdfminer_layout.LTTextBoxHorizontal()
        caixa.set_bbox((x, 10, x + 100, 30))
        caixa.nome = nome
        caixas.append(caixa)

    normal = _arvore(container.group_textboxes(pdfminer_layout.LAParams(), caixas)[0])
    with _enderecos_invertidos():
        invertido = _arvore(container.group_textboxes(pdfminer_layout.LAParams(), caixas)[0])

    assert normal == invertido == (('A', 'B'), 'C')


@precisa_pdf_norta
def test_texto_da_nota_3615_igual_em_qualquer_estado_do_processo():
    normal = extract_text(PDF_NORTA)
    with _enderecos_invertidos():
        invertido = extract_text(PDF_NORTA)
    assert normal == invertido
    # Coluna "Código IBGE / CEP": prestador (Campo Grande) antes do tomador.
    assert normal.index('5002704 / 79005-250') < normal.index('2927408 / 40020-605')


@precisa_pdf_norta
@pytest.mark.parametrize('invertido', [False, True])
def test_nota_3615_prestador_e_tomador_com_municipio_e_cep_impressos(invertido):
    if invertido:
        with _enderecos_invertidos():
            notas = SPPdfExtractor(PDF_NORTA).parse_multiple()
    else:
        notas = SPPdfExtractor(PDF_NORTA).parse_multiple()

    assert len(notas) == 1
    nota = notas[0]
    assert nota.numero == '3615'
    assert nota.prestador.cnpj_cpf == '53702242000193'
    assert (nota.prestador.endereco.codigo_municipio, nota.prestador.endereco.cep,
            nota.prestador.endereco.uf) == ('5002704', '79005250', 'MS')
    assert nota.tomador.cnpj_cpf == '49586312000118'
    assert (nota.tomador.endereco.codigo_municipio, nota.tomador.endereco.cep,
            nota.tomador.endereco.uf) == ('2927408', '40020605', 'BA')
