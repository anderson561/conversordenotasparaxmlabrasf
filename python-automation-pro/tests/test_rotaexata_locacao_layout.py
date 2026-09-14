# -*- coding: utf-8 -*-
r"""Layout NOVO: Fatura de Locação da RotaExata Software Ltda (CNPJ raiz
13.661.448, Joinville/SC). Achado real: fatura nº 233530 -> NEMUS - GESTAO E
REQUALIFICACAO AMBIENTAL LTDA (Salvador/BA), R$82,60, locação de rastreadores
veiculares. Pedido do usuário: "plano de ação para o novo layout
fatura-rotaexata, caso não exista, crie um novo".

CAUSA-RAIZ: esta nota NÃO imprime a frase "FATURA DE LOCAÇÃO" em lugar nenhum
— o título é só "FATURA:  Nº  233530". Toda a família de faturas de locação já
catalogada é detectada por essa frase (genérico) ou pelo CNPJ do emitente
(ARMAC/NEO-TAGUS/PJB/F&F), então esta caía em `LAYOUT_GENERICO`. E aí o efeito
não é um XML errado, é a AUSÊNCIA de XML: `parse_multiple` descarta a página
inteira com "Layout não reconhecido", `run_conversion` recebe zero notas e
levanta "O PDF ... parece ser baseado em imagem/scan ou vazio. Nenhuma nota
pôde ser lida". Antes desta correção o PDF não gerava nota nenhuma.

Facetas próprias deste template:

  - Quase todo rótulo sai na MESMA linha do valor ("CNPJ: ... | IE: ... | IM:
    ..."), ao contrário do "rótulos todos, depois valores todos" da NEO-TAGUS —
    por isso as DUAS entidades são extraídas dinamicamente, sem prestador
    hardcoded.
  - A ÚNICA faceta "rótulos-depois-valores" é a grade do cabeçalho: "RF FATURA
    Nº / VALOR DA FATURA / EMISSÃO" e só então "233530 / R$ 82,60 / 01/08/2026".
  - Valores monetários vêm com ESPAÇO INQUEBRÁVEL depois do "R$"
    ("R$\xa0 82,60").
  - A descrição do item QUEBRA EM DUAS LINHAS ("... APARELHOS DE" + "RECEPÇÃO.").
  - Joinville/SC estava ausente de `IBGEResolver.KNOWN_CITIES`: o prestador
    cairia no fallback silencioso de Salvador/BA — erro especialmente difícil
    de notar aqui, porque o TOMADOR é de Salvador de verdade.
  - As retenções federais saem só em PERCENTUAL (IRRF 4.80%, CSLL 1%, PIS
    0.65%, COFINS 3%), sem nenhum valor em R$: ficam zeradas e sinalizadas em
    `avisos`, nunca calculadas a partir do percentual.

Texto REAL extraído via pdfminer (`extract_text`), direto do PDF original
("ROTA EXATA 05.08.pdf"), sem nenhuma edição."""
import os

import pytest

from src.extractors.pdf_extractor import (SPPdfExtractor, LAYOUT_ROTAEXATA_LOCACAO,
                                          LAYOUT_GENERICO)
from src.utils.ibge_resolver import IBGEResolver

MOCK_ROTAEXATA = (
    'RotaExata  Software  Ltda\n'
    '\n'
    'CNPJ:  13.661.448/0001-06  |  IE:  256832196  |  IM:  34571\n'
    '\n'
    'Rua  Cuiabá,  32  -  Costa  e  Silva  -  Joinville/SC  |  CEP:  89220-110\n'
    '\n'
    'FATURA:  Nº  233530\n'
    '\n'
    '(47)  3032-8400\n'
    '\n'
    'RF  FATURA  Nº\n'
    '\n'
    'VALOR  DA  FATURA\n'
    '\n'
    'EMISSÃO\n'
    '\n'
    '233530\n'
    '\n'
    'R$\xa0 82,60\n'
    '\n'
    '01/08/2026\n'
    '\n'
    'NOME  DO  SACADO:  NEMUS  -  GESTAO  E  REQUALIFICACAO  AMBIENTAL  LTDA\n'
    '\n'
    'ENDEREÇO:  TERRITORIO  DO  AMAPA,  146  -  PITUBA\n'
    '\n'
    'MUNICÍPIO:  SALVADOR/BA  |  CEP:  41830-540\n'
    '\n'
    'CNPJ:  19886820000150  |  IE:  xxxxx  |  IM:  71983552675\n'
    '\n'
    'VALOR  POR  EXTENSO\n'
    '\n'
    'OITENTA  E  DOIS  REAIS  E  SESSENTA  CENTAVOS\n'
    '\n'
    'QUANT. UNIDADE\n'
    '\n'
    'DESCRIÇÃO  DOS  EQUIPAMENTOS  LOCADOS\n'
    '\n'
    '1\n'
    '\n'
    'UN\n'
    '\n'
    'LOCAÇÃO  DE  BENS  MÓVEIS  -  RASTREADORES  E  APARELHOS  DE\n'
    '\n'
    'RECEPÇÃO.\n'
    '\n'
    'VALOR\n'
    '\n'
    'UNITÁRIO\n'
    '\n'
    'VALOR\n'
    '\n'
    'TOTAL\n'
    '\n'
    'R$\xa0 82,60\n'
    '\n'
    'R$\xa0 82,60\n'
    '\n'
    'IMPOSTOS:\n'
    '\n'
    'IRRF:  4.80%\n'
    '\n'
    'Nº  DO  CONTRATO\n'
    '\n'
    'Observações:\n'
    '\n'
    'Informações  Complementares:\n'
    '\n'
    'CSLL:  1%\n'
    '\n'
    'PIS:  0.65%\n'
    '\n'
    'COFINS:  3%\n'
    '\n'
    'VALOR  TOTAL  DA  FATURA\n'
    '\n'
    'R$\xa0 82,60\n'
    '\n'
    'Documento  emitido  nos  termos  do  art.  1o  da  Lei  no  8.846/94.\n'
    '\n'
    'Locação  de  bens  móveis  não  incidente  da  cobrança  de  imposto  ISSQN\n'
    '\n'
    'conforme  lei  federal  complementar  n°  116,  de  julho  de  2003\n'
    '\n'
    'Recebi(emos)  e  conferi(emos)  de  RotaExata  Software  Ltda  os  bens  locados  constantes  desta  fatura.\n'
    '\n'
    'Joinville,  _______  de  ________________________  de  20_______.\n'
    '\n'
    'Nome:  __________________________________________________________  CPF:  _________________________________________.\n'
    '\n'
    'Assinatura:  _____________________________________________________________________________________________________.\n'
    '\n'
    '\x0c'
)


def _parse(texto, monkeypatch, nome_arquivo="tests/dummy_fatura_locacao.pdf"):
    """Roda o extrator sobre um texto injetado.

    O nome do arquivo dummy NÃO contém o número da nota de propósito: existe um
    fallback que pesca o número do nome do arquivo, e um dummy chamado
    "233530.pdf" faria o teste de número passar pelo motivo errado."""
    os.makedirs("tests", exist_ok=True)
    with open(nome_arquivo, "wb") as f:
        f.write(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text",
                        lambda path: texto)
    try:
        ex = SPPdfExtractor(nome_arquivo)
        return ex, ex.parse()
    finally:
        os.remove(nome_arquivo)


# ----------------------------------------------------------------------
# Detecção — a causa-raiz
# ----------------------------------------------------------------------

def test_layout_dedicado_detectado_pelo_cnpj_raiz(monkeypatch):
    ex, _ = _parse(MOCK_ROTAEXATA, monkeypatch)
    assert ex.layout == LAYOUT_ROTAEXATA_LOCACAO


def test_nao_cai_mais_em_layout_generico(monkeypatch):
    """Era exatamente isso que acontecia antes: sem a frase "FATURA DE
    LOCAÇÃO", a nota não casava nenhum padrão da cadeia."""
    ex, _ = _parse(MOCK_ROTAEXATA, monkeypatch)
    assert ex.layout != LAYOUT_GENERICO


def test_pagina_nao_e_descartada_como_layout_nao_reconhecido(monkeypatch):
    """`parse_multiple` descarta toda página cujo `_detect_layout_page` devolve
    LAYOUT_GENERICO — era assim que o PDF inteiro saía sem nota nenhuma."""
    ex, _ = _parse(MOCK_ROTAEXATA, monkeypatch)
    assert ex._detect_layout_page(MOCK_ROTAEXATA) == LAYOUT_ROTAEXATA_LOCACAO


def test_pdf_gera_exatamente_uma_nota(monkeypatch):
    ex, _ = _parse(MOCK_ROTAEXATA, monkeypatch)
    notas = ex.parse_multiple()
    assert len(notas) == 1
    assert notas[0].numero == '233530'


def test_deteccao_casa_filial_futura(monkeypatch):
    """A detecção é pelo CNPJ RAIZ: uma filial (sufixo diferente) da mesma
    locadora continua caindo neste layout, sem revisão."""
    filial = MOCK_ROTAEXATA.replace('13.661.448/0001-06', '13.661.448/0002-87')
    ex, _ = _parse(filial, monkeypatch)
    assert ex.layout == LAYOUT_ROTAEXATA_LOCACAO


# ----------------------------------------------------------------------
# Identificação da nota
# ----------------------------------------------------------------------

def test_numero_da_fatura(monkeypatch):
    _, nfse = _parse(MOCK_ROTAEXATA, monkeypatch)
    assert nfse.numero == '233530'


def test_numero_nao_vem_do_nome_do_arquivo(monkeypatch):
    """Mesmo com um número DIFERENTE no nome do arquivo, o número tem que vir
    do texto da nota (armadilha real já vista na NEO-TAGUS)."""
    _, nfse = _parse(MOCK_ROTAEXATA, monkeypatch,
                     nome_arquivo="tests/dummy_fatura_999999.pdf")
    assert nfse.numero == '233530'


def test_data_de_emissao(monkeypatch):
    _, nfse = _parse(MOCK_ROTAEXATA, monkeypatch)
    assert nfse.data_emissao.strftime('%d/%m/%Y') == '01/08/2026'


def test_codigo_de_verificacao_da_familia_de_faturas(monkeypatch):
    """Fatura não tem código de autenticidade municipal — a família inteira usa
    o literal "FATURA", em vez do sentinela de campo não encontrado."""
    _, nfse = _parse(MOCK_ROTAEXATA, monkeypatch)
    assert nfse.codigo_verificacao == 'FATURA'


# ----------------------------------------------------------------------
# Valores
# ----------------------------------------------------------------------

def test_valor_total_da_fatura(monkeypatch):
    _, nfse = _parse(MOCK_ROTAEXATA, monkeypatch)
    assert nfse.valores.valor_servicos == pytest.approx(82.60)
    assert nfse.valores.valor_liquido_nfse == pytest.approx(82.60)


def test_valor_vem_do_rodape_e_nao_do_ultimo_item_da_tabela(monkeypatch):
    """Nesta nota o item único tem o mesmo valor da fatura, então os dois
    caminhos dariam 82,60 por coincidência. Com 2 itens de valores diferentes,
    só a âncora "VALOR TOTAL DA FATURA" devolve o total certo — o último "R$"
    da tabela seria o total do ÚLTIMO ITEM."""
    dois_itens = MOCK_ROTAEXATA.replace(
        'R$\xa0 82,60\n'
        '\n'
        'R$\xa0 82,60\n'
        '\n'
        'IMPOSTOS:',
        'R$\xa0 50,00\n'
        '\n'
        'R$\xa0 50,00\n'
        '\n'
        'R$\xa0 32,60\n'
        '\n'
        'R$\xa0 32,60\n'
        '\n'
        'IMPOSTOS:'
    )
    _, nfse = _parse(dois_itens, monkeypatch)
    assert nfse.valores.valor_servicos == pytest.approx(82.60)


def test_iss_zerado_locacao_de_bens_moveis(monkeypatch):
    """A própria nota declara a não-incidência pela LC 116/2003 — nada de ISS
    fabricado a partir de uma alíquota presumida."""
    _, nfse = _parse(MOCK_ROTAEXATA, monkeypatch)
    assert nfse.valores.base_calculo == 0.0
    assert nfse.valores.aliquota == 0.0
    assert nfse.valores.valor_iss == 0.0


def test_item_lista_servico_de_locacao(monkeypatch):
    _, nfse = _parse(MOCK_ROTAEXATA, monkeypatch)
    assert nfse.servico_codigo == '0601'


def test_retencoes_federais_nao_sao_calculadas_do_percentual(monkeypatch):
    """IRRF 4.80% de 82,60 daria R$3,96 — um número plausível que a nota NÃO
    declara. Fica zerado e vira aviso."""
    _, nfse = _parse(MOCK_ROTAEXATA, monkeypatch)
    assert nfse.valores.valor_ir == 0.0
    assert nfse.valores.valor_csll == 0.0
    assert nfse.valores.valor_pis == 0.0
    assert nfse.valores.valor_cofins == 0.0


def test_aviso_de_retencoes_so_em_percentual(monkeypatch):
    _, nfse = _parse(MOCK_ROTAEXATA, monkeypatch)
    aviso = next((a for a in nfse.avisos if 'percentual' in a.lower()), None)
    assert aviso is not None
    assert 'IRRF 4.80%' in aviso
    assert 'COFINS 3%' in aviso


def test_aviso_de_iss_nao_incidente(monkeypatch):
    _, nfse = _parse(MOCK_ROTAEXATA, monkeypatch)
    assert any('116' in a and 'zerado' in a.lower() for a in nfse.avisos)


def test_sem_aviso_de_valor_zerado(monkeypatch):
    """Guarda contra o modo de falha antigo da família (valor saindo 0,00)."""
    _, nfse = _parse(MOCK_ROTAEXATA, monkeypatch)
    assert not any('zero' in a.lower() for a in nfse.avisos)


# ----------------------------------------------------------------------
# Prestador
# ----------------------------------------------------------------------

def test_prestador_identificado(monkeypatch):
    _, nfse = _parse(MOCK_ROTAEXATA, monkeypatch)
    p = nfse.prestador
    assert p.cnpj_cpf == '13661448000106'
    assert p.razao_social == 'RotaExata Software Ltda'
    assert p.inscricao_municipal == '34571'


def test_endereco_do_prestador(monkeypatch):
    _, nfse = _parse(MOCK_ROTAEXATA, monkeypatch)
    e = nfse.prestador.endereco
    assert e.logradouro == 'Rua Cuiabá'
    assert e.numero == '32'
    assert e.bairro == 'Costa e Silva'
    assert e.municipio == 'Joinville'
    assert e.uf == 'SC'
    assert e.cep == '89220110'


def test_municipio_do_prestador_nao_cai_no_fallback_salvador(monkeypatch):
    """Joinville/SC estava ausente de KNOWN_CITIES. O fallback silencioso
    (Salvador/BA) deslocaria também OrgaoGerador e MunicipioIncidencia — ou
    seja, o município de incidência do ISS."""
    _, nfse = _parse(MOCK_ROTAEXATA, monkeypatch)
    assert nfse.prestador.endereco.codigo_municipio == '4209102'
    assert nfse.prestador.endereco.codigo_municipio != '2927408'


def test_joinville_registrada_no_resolver_ibge():
    assert IBGEResolver.KNOWN_CITIES.get('JOINVILLE') == '4209102'


# ----------------------------------------------------------------------
# Tomador (sacado)
# ----------------------------------------------------------------------

def test_tomador_identificado(monkeypatch):
    _, nfse = _parse(MOCK_ROTAEXATA, monkeypatch)
    t = nfse.tomador
    assert t.cnpj_cpf == '19886820000150'
    assert t.razao_social == 'NEMUS - GESTAO E REQUALIFICACAO AMBIENTAL LTDA'
    assert t.inscricao_municipal == '71983552675'


def test_tomador_nao_herda_o_cnpj_do_prestador(monkeypatch):
    """Modo de falha recorrente do fallback genérico nesta base."""
    _, nfse = _parse(MOCK_ROTAEXATA, monkeypatch)
    assert nfse.tomador.cnpj_cpf != nfse.prestador.cnpj_cpf


def test_endereco_do_tomador(monkeypatch):
    _, nfse = _parse(MOCK_ROTAEXATA, monkeypatch)
    e = nfse.tomador.endereco
    assert e.logradouro == 'TERRITORIO DO AMAPA'
    assert e.numero == '146'
    assert e.bairro == 'PITUBA'
    assert e.municipio == 'SALVADOR'
    assert e.uf == 'BA'
    assert e.codigo_municipio == '2927408'
    assert e.cep == '41830540'


def test_ie_placeholder_do_sacado_nao_vira_dado(monkeypatch):
    """A nota imprime "IE:  xxxxx" (placeholder literal do gerador do PDF)."""
    _, nfse = _parse(MOCK_ROTAEXATA, monkeypatch)
    assert 'xxxxx' not in nfse.tomador.razao_social.lower()
    assert (nfse.tomador.inscricao_municipal or '').isdigit()


# ----------------------------------------------------------------------
# Discriminação
# ----------------------------------------------------------------------

def test_discriminacao_completa_apesar_da_quebra_de_linha(monkeypatch):
    _, nfse = _parse(MOCK_ROTAEXATA, monkeypatch)
    assert nfse.discriminacao == (
        'LOCAÇÃO DE BENS MÓVEIS - RASTREADORES E APARELHOS DE RECEPÇÃO.'
    )


def test_discriminacao_nao_engole_quantidade_nem_unidade(monkeypatch):
    """"1" e "UN" saem em linhas próprias ANTES da descrição, na mesma grade."""
    _, nfse = _parse(MOCK_ROTAEXATA, monkeypatch)
    assert not nfse.discriminacao.startswith('1')
    assert not nfse.discriminacao.upper().startswith('UN')


def test_discriminacao_nao_vaza_o_cabecalho_da_coluna_de_valores(monkeypatch):
    _, nfse = _parse(MOCK_ROTAEXATA, monkeypatch)
    assert 'UNITÁRIO' not in nfse.discriminacao.upper()
    assert 'R$' not in nfse.discriminacao
