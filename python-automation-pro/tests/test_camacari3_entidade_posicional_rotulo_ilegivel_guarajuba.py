# -*- coding: utf-8 -*-
"""Texto REAL do OCR (Tesseract) da NFS-e de Camaçari/BA ESCANEADA — nota real
nº 160, AVANÇO GESTÃO E ADMINISTRAÇÃO LTDA -> GUARAJUBA SHOPPING LTDA (2º PDF
do lote Guarajuba Shopping, "NFSe TOMADOS 2.pdf", página 3 de 7). Reportado
pelo usuário: "os dados não foram extraídos" (a página inteira sumia do
resultado).

Causa raiz, em 2 partes:

1. **Página inteira ausente**: mesma classe de bug da nota 201 (PSM automático
   do Tesseract falhando por completo) — mas aqui numa variante nova: na
   orientação CORRETA (0°) o PSM automático lê 0 caracteres, MAS uma rotação
   ERRADA (90°) produz texto embaralhado que, por coincidência, pontua > 0 em
   `_score_ocr_text` — isso fazia a busca de rotação "vencer" com a rotação
   errada, e o fallback de PSM 6 (gated por `best_score == 0`) nunca disparava
   porque `best_score` não era mais zero. Corrigido em `_ocr_page` guardando a
   pontuação da tentativa em 0° SEPARADAMENTE (`score_angle_0`), usada como
   condição do fallback em vez do `best_score` da busca de rotação.

2. **Prestador/tomador "Não Identificado"**: uma vez a página recuperada via
   PSM 6, o rótulo "Nome/Razão Social" saiu com uma corrupção NOVA e mais
   severa que qualquer coisa já tolerada — as PRÓPRIAS letras do prefixo
   "Raz" saíram trocadas ("Nois Rraão Social:" no prestador, "Nomemianão
   Social:" no tomador), e o rótulo "CPF/CNPJ" saiu reduzido a só ":"/"PJ:".
   Perseguir cada grafia não escala; corrigido com fallback POSICIONAL (não
   mais por rótulo): a razão social é sempre o 1º campo impresso logo após
   o cabeçalho "PRESTADOR/TOMADOR DE SERVIÇOS" neste layout — pega-se a 1ª
   linha não-vazia do bloco e tudo depois do 1º ":" nela, não importa como o
   rótulo em si saiu; o CNPJ é buscado sem rótulo nenhum dentro do bloco já
   isolado (onde só pode aparecer o CNPJ da própria entidade).

O texto abaixo é exatamente o resultado de `_ocr_page(2)` já com o fix da
página aplicado (contém a leitura completa via PSM 6).
"""
import os

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_TEXT = """Número da Nota
160
E: 0066628001
Nº: SN
NTE GORDA)

Número de Nota
160
628001
Nº: SN
DO)
UF: BA
Re RA

180
0066628001
Nº: SN
* GORDO)

f. | PREFEITURA MUNICIPAL DE CAMAÇARI
| MD Soeretaria da Fazenda
Mo NOTA FISCAL DE SERVIÇOS ELETRÔNICA Gédigo de avtandicidaa
PRESTADOR DE SERVIÇOS
Nois Rraão Social: AVANÇO GESTÃO E ADMINISTRAÇÃO LTDA
: 59.132,742/0001-13 Inscrição Municipal: 006862800
Logradouro: RUA ALA DAS DUNAS gi à Nº; SN
Compl: :GUARAJUBA SHOPPING;LOJA:03;QUADRA:G-4 Bairro: GUARAJUBA (MONTE GORDO)
CEP: 42840312 Município: CAMAÇARI UF: BA
TOMADOR DE SERVIÇOS
Nomemianão Social: GUARAJUBA SHOPPING LTDA
PJ: 24.890,395/0001-03 Inscrição Municipal: 0032035001
Logradouro: RODOVIA BA 099 ESTRADA DO COCO Nº; SN
Compl. ALAMEDA DAS DUNAS GUARAJUBA SHOPPING Bairro: GUARAJUBA (MONTE GORDO)
CEP: 42840310 Município: CAMAÇARI UF: BA
ia DISCRIMINAÇÃO DOS SERVIÇOS
DESCRIÇÃO D
TAXA DE SERVIÇOS COMBINADOS DE ESCRITÓRIO E APOIO ADMINISTRATIVO ioita VE Ni eg) hi resgata!
ARS [O ee
Retenções (R$) Totais (R$)
PIS: 0,00 |Valor dos Serviços (R$) 3.994,77
COFINS: 0,00 | Deduções (-) 0,00
IR: 0,00 |Aliquota (%) 4,36
CSLL: 0,00 |Valor do ISS (R$) 174,17
Outras; "0,00 [Valor Líquido da Nota (=) 3.994,77
Total de Retenções: 0,00
Tipo de tributação: A RECOLHER PELO PRESTADOR Data da prestação do serviço: 27/02/2026
Município da prestação do serviço: 2905701 - CAMAGARI
Município da tributação: 2908701 - CAMACARI
CNAE: 8211-3/00 - SERVIÇOS COMB DE E E APOIO ADMINISTRATIVO
Serviço: 001703 - PLANEAMENTO, COOPER ta mata OU ORGANIZAÇÃO TÉCNICA, FINANCEIRA OU ADMINISTRATIVA.
CPqD - Gestão Pública Data impressão: 27/02/2026 11:59 É
"""


@pytest.fixture
def nfse(monkeypatch):
    dummy_path = "tests/dummy_camacari3_nota160.pdf"
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


def test_numero_e_valores(nfse):
    assert nfse.numero == "160"
    assert nfse.valores.valor_servicos == pytest.approx(3994.77)
    assert nfse.valores.base_calculo == pytest.approx(3994.77)
    assert nfse.valores.valor_iss == pytest.approx(174.17)


def test_prestador_recuperado_por_posicao_apesar_do_rotulo_ilegivel(nfse):
    # Antes: "Prestador Não Identificado" — "Nois Rraão Social:" não batia
    # nenhuma tolerância de rótulo já existente (as próprias letras de "Raz"
    # saíram trocadas, não só o sufixo "ão"/"Social").
    assert nfse.prestador.razao_social == "AVANÇO GESTÃO E ADMINISTRAÇÃO LTDA"
    assert nfse.prestador.cnpj_cpf == "59132742000113"


def test_tomador_recuperado_por_posicao_apesar_do_rotulo_ilegivel(nfse):
    # Antes: "Tomador Não Identificado" — "Nomemianão Social:" e "PJ:" (no
    # lugar de "CPF/CNPJ:") não batiam nenhuma tolerância de rótulo.
    assert nfse.tomador.razao_social == "GUARAJUBA SHOPPING LTDA"
    assert nfse.tomador.cnpj_cpf == "24890395000103"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
