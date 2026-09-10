# -*- coding: utf-8 -*-
"""Texto REAL do OCR (Tesseract) da NFS-e de Salvador/BA ESCANEADA — nota real
nº 00000080, RISERIO ARQUITETURA E ENGENHARIA LTDA -> UFFICIO - COMÉRCIO,
REPRESENTAÇÃO, INSTALAÇÃO E MONTAGEM DE MÓVEIS LTDA.ME (arquivo "UFFICIO.pdf",
página única). Reportado pelo usuário: "Extração do tomador de serviços
incorreto" — mas a investigação revelou que o PRESTADOR é quem sai errado (o
sintoma visível — Prestador e Tomador saindo com os MESMOS dados — é real,
só a atribuição de qual lado estava quebrado que era o oposto do relato).

Causa raiz, em 2 partes independentes:

1. **Prestador "herda" os dados do Tomador**: o rótulo "PRESTADOR DE
   SERVIÇOS" saiu do OCR como "PRESPADOR,DESSERVIÇOS" (T→P, não coberto por
   nenhuma tolerância de `_LABELS_PRESTADOR` já existente) — a busca do
   bloco do prestador (`m_bloco`) não encontra nada. O fallback ANTIGO nesse
   caso usava o DOCUMENTO INTEIRO como bloco de busca — como o próprio CNPJ
   do prestador também saiu ilegível ("35457.695) 02", sem "/"), a busca de
   CNPJ varria o documento inteiro e só achava o CNPJ do TOMADOR (o único
   bem formado), atribuindo os dados do Tomador ao Prestador. Corrigido
   delimitando esse fallback pelo rótulo da OUTRA entidade (`TOMADOR DE
   SERVIÇOS`, que sobreviveu ao OCR) em vez do texto inteiro — restringe o
   escopo já usado, nunca amplia. Um 2º guard evita que o "chute" de último
   recurso (1º CNPJ válido do documento inteiro) reintroduza a mesma
   contaminação quando o bloco já veio desse fallback delimitado. Como o
   CNPJ do prestador é genuinamente irrecuperável por regex neste texto (a
   pontuação foi destruída, não só os dígitos), o resultado correto aqui é
   o sentinela + aviso — dado ausente, não dado ERRADO.

2. **Valor da nota truncado por "/" espúrio**: "VALOR TOTAL DA NOTA =
   R$18.080,73" saiu do OCR como "R$18/080,73" (o "." virou "/"). A classe
   de caracteres original da captura (`[\\d\\.,]+`) não incluía "/", então
   parava em "18" — derrubando Valor dos Serviços/Base de Cálculo pra
   18,00. Corrigido tolerando "/" como separador espúrio (equivalente a
   "."; nunca aparece de verdade num valor monetário) nessa captura
   específica do LAYOUT_SALVADOR.

3. **Alíquota/Valor do ISS zerados**: o cabeçalho da grade de 5 valores
   exigia "Valor do ISS" (saiu "Vajócdo ISS") e "Crédito" (saiu "Cito") —
   corrigido tolerando a sigla curta "ISS" (mais resistente ao OCR que a
   palavra inteira "Valor") e descartando a exigência de reconhecer
   "Crédito" por extenso. Isso NÃO recupera os valores desta nota
   específica: a própria LINHA de valores abaixo do cabeçalho está corrompida
   demais (só 4 dos 5 números sobrevivem em formato reconhecível; o ISS real,
   R$904,04, não sobra em nenhuma forma numérica no texto) — decisão do
   usuário 2026-09-04: manter Alíquota/ISS zerados + aviso explícito (não
   fabricar um valor sem lastro no documento), em vez de perseguir um recorte
   dedicado de imagem (escopo maior, mesma família de
   `_ocr_recut_base_calculo_grade_salvador`).

O texto abaixo é o resultado real de `_ocr_page(0)` para esta nota (1913
caracteres)."""
import os

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_TEXT = """Código de Verificação: TJSS-BEIY
Número da Nota:
00000080

Número da Nota:
JOR 00000080

Data e Hora de Emissão:

09/01/2025 15:35:19
R Código de Verificação:
alvador TJSÉ-BEIY

io Número da Nota:
PREFEITURA MUNICIPAL DO SALVADOR 00000080
“SECRETARIA MUNICIPAL DA FAZENDA Data e Hora de Emissão:
E 09/01/2025 15:35:19
PN a A Código de Verificação:
É NOTA FISCAL DE SERVIÇOS ELETRÔNICA - Nota Salvador TIse BEI Ação

PRESPADOR,DESSERVIÇOS

GPFICNP E p a Inscrição Municipal

35457.695) 02 = “gs 00.713.012/001-28

RISERIQ ARQ URKE ENGENHARIA LTDA

Ave Oceáriiça oosósbisaL. PE304:+ RIGAMERMELHO - Sályador - CEP: 41950-000 - BA

Email ES 0 “

TOMADOR DE SERVIÇOS PhBEIUIRENTE “

Nome/Razão Social: « Pa NS

UFFICIO - COMERCIÓ, REPRI TACAQ,NISTALÃCAO E MONTAGEM DE MOVEIS LTDA.ME.

CPF/CNPJ à < E “Inscrição Municipal

16.306.110/0001-16 RA Ca O li “e, 00.061.325/001-89

Ave Antônio Carlos Magalhãda, 012960 EpIF SHOPPING CIDADE  SALA,ITAIGARA - Salvador - CEP: 41825-000/BA

carmenfBufficio-ba.com.br E é q Pd EN

DISCRIMINAÇÃO DOS SERVÍSOS “2 SE cs a

Consultoria. E, e E a ido e

Noz 6
wo Bo as N
NES N
N A, “ed o
VALOR TOTAL DA NOTA = R$18/080,73 4 a

CNAE E, , FR ae e ' Es

7111100 - Serviços de arquitetura a E 2 É a

00701 - Engenharia, agronomia, agrimensura, arquitetura, geologia, urbanismo, pai Sagismo eFiongêntias » a a

Valor Total das Deduções (R$): | Base de Cálculo (R$) Alíquota (%) E Vajócdo ISS (R$g887) Cito Nota Salvadêy (R$)

0,00 18.080,73 5,09 E g6ãos | q “2,00 |
E E = a a
0,00 117,52 542,42 271,21 180:87 B Pa 16.064,73 |

- Esta Nota Salvador foi emitida com respaldo na Lei 7.186/2006 gg

- Esta Nota Salvador não gera crédito A

- O ISS desta Nota Salvador será RETIDO pelo Tomador de Serviço que deverá recolher através da Guia de Nota Salvador,

- COMPETÊNCIA: 01/2025 (mês/ano) “mg

- Código de Tributação do Município: 0701-0/04 - Arquitetura, exceto execução material de obra é
"""


@pytest.fixture
def nfse(monkeypatch):
    dummy_path = "tests/dummy_salvador_ufficio_nf80.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_TEXT)

    try:
        nfse_list = SPPdfExtractor(dummy_path).parse_multiple()
        assert len(nfse_list) == 1
        yield nfse_list[0]
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_numero_da_nota(nfse):
    assert nfse.numero == "00000080"


def test_valor_nao_trunca_no_separador_espurio(nfse):
    # Antes: "R$18/080,73" (o "." virou "/") truncava a captura para "18" —
    # Valor dos Serviços/Base de Cálculo saíam 18,00 em vez de 18.080,73.
    assert nfse.valores.valor_servicos == pytest.approx(18080.73)
    assert nfse.valores.base_calculo == pytest.approx(18080.73)


def test_prestador_nao_herda_cnpj_do_tomador(nfse):
    # Antes: Prestador saía com o MESMO CNPJ do Tomador (16.306.110/0001-16)
    # — o rótulo "PRESTADOR DE SERVIÇOS" corrompido ("PRESPADOR,DESSERVIÇOS")
    # fazia a busca de CNPJ vazar pro bloco do Tomador (o único CNPJ bem
    # formado do documento). O CNPJ real do prestador (RISERIO,
    # 35.157.695/0001-02) sai ilegível demais pra recuperar por regex nesta
    # nota ("35457.695) 02", sem "/") — o correto aqui é o sentinela +
    # aviso, não mais o CNPJ (real, porém ERRADO) do tomador.
    assert nfse.prestador.cnpj_cpf != nfse.tomador.cnpj_cpf
    assert nfse.prestador.cnpj_cpf == "00000000000100"
    assert "Dados do prestador não identificados" in " ".join(nfse.avisos)


def test_prestador_razao_social_recuperada_nao_e_a_do_tomador(nfse):
    # Antes: razão social do prestador saía idêntica à do tomador
    # ("UFFICIO..."). Agora recupera o nome real (RISERIO, garblado pelo OCR
    # mas reconhecível), sem contaminação cruzada.
    assert "UFFICIO" not in nfse.prestador.razao_social.upper()
    assert "RISERI" in nfse.prestador.razao_social.upper()


def test_tomador_permanece_correto(nfse):
    assert nfse.tomador.cnpj_cpf == "16306110000116"
    assert "UFFICIO" in nfse.tomador.razao_social.upper()


def test_aliquota_iss_zerados_com_aviso_explicito(nfse):
    # A linha de valores da grade "Deduções/Base/Alíquota/ISS/Crédito" está
    # corrompida demais pra recuperar os 5 campos (só 4 números sobrevivem
    # em formato reconhecível) — o ISS real (R$904,04) não sobra em NENHUMA
    # forma numérica no texto. Decisão do usuário: manter zerado + avisar,
    # não fabricar um valor sem lastro no documento.
    assert nfse.valores.aliquota == 0.0
    assert nfse.valores.valor_iss == 0.0
    assert "Alíquota/Valor do ISS não confiáveis" in " ".join(nfse.avisos)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
