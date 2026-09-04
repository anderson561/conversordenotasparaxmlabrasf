# -*- coding: utf-8 -*-
"""Texto REAL do OCR (Tesseract) da NFS-e de Camaçari/BA ESCANEADA — nota real
nº 148, AVANÇO GESTÃO E ADMINISTRAÇÃO LTDA -> GUARAJUBA SHOPPING LTDA (2º PDF
do lote Guarajuba Shopping, "NFSe TOMADOS 2.pdf"). Reportado pelo usuário:
"o valor da nota está errado, o correto é R$ 42.892,92" — apontando os DOIS
lugares onde o valor aparece no PDF (VALOR TOTAL da linha do item x VALOR DOS
SERVIÇOS da grade), que aqui DIVERGEM.

Quirks deliberadamente preservados para travar as regressões:
 - a célula "Valor dos Serviços (R$)" da grade Retenções x Totais saiu
   "42.892,8" — um número SINTATICAMENTE válido (não zero, não ilegível como
   na nota 159), mas com o último dígito de centavo perdido pelo OCR ("9" de
   "92" comido) — diferente de todos os achados anteriores deste layout
   (sempre célula vazia/ilegível), aqui o valor errado passa despercebido
   pelas guardas existentes por parecer plausível;
 - a linha do item em "DISCRIMINAÇÃO DOS SERVIÇOS" está limpa e correta,
   repetindo o valor real duas vezes (unitário = total, qtd 1,0000):
   "42.892,92 42.892,92";
 - "Valor Líquido da Nota (=)" tem um "." solto colado antes do número (ruído
   de OCR), fazendo o regex capturar só esse ponto (nenhum dígito) em vez do
   valor real;
 - o rótulo do tomador saiu "Nome/Razão Soclal:" ("i" lido como "l"), fazendo
   a razão social cair em "Tomador Não Identificado" apesar do CNPJ (sem
   dígito trocado nesta nota) já sair correto.
"""
import os

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_TEXT = """148
19/02/2026 08:30
Código de autenticidade
DY31NZFFB
: 0066628001
Nº: SN
NTE GORDO)

148
19/02/2026 08:30
Código de autenticidade
DY31NZFFB
628001
Nº: SN
DO)
UF: BA

Número da Nota
148
Data de Emissão
19/02/2026 09:30
Código de autenticidade
DY31NZFFB
cipal: 0066628001
Nº: SN

| : per PREFEITURA MUNICIPAL DE CAMAÇARI ERR
, Ê ho Secretaria da Fazenda
j = | Cbeemedo NOTA FISCAL DE SERVIÇOS ELETRÔNICA
y — DY31NZFFB
| PRESTADOR DE SERVIÇOS
Nome/Razão Social: AVANÇO GESTÃO E ADMINISTRAÇÃO LTDA
CPF/CNPJ: 59.132.742/0001-13 Inscrição Municipal: 0066628001
Logradouro: RUA ALA DAS DUNAS Nº: SN
Compl: :GUARAJUBA SHOPPING;LOJA:03;QUADRA:C-4 Bairro: GUARAJUBA (MONTE GORDO)
CEP: 42840312 Município: CAMAÇARI UF: BA
TOMADOR DE SERVIÇOS
Nome/Razão Soclal: GUARAJUBA SHOPPING LTDA
CPFI/CNPI: 24.890.395/0001-03 Inscrição Municipal: 0032035001
Logradouro: RODOVIA BA 099 ESTRADA DO COCO Nº SN
Compl.: ALAMEDA DAS DUNAS GUARAJUBA SHOPPING Bairro: GUARAJUBA (MONTE GORDO)
CEP: 42840310 Município: CAMAÇARI UF: BA
DISCRIMINAÇÃO DOS SERVIÇOS
DESCRIÇÃO : oTD VALOR UNIT (R$) VALOR TOTAL (R$)
TAXA DE SERVIÇOS COMBINADOS DE ESCRITÓRIO E APOIO ADMINISTRATIVO 1,0000 42.892,92 42.892,92
O) a AS A XML PDF [Ria
Retonções (R$) Totais (R$)
PIS: á 0,00 | Valor dos Serviços (R$) 42.892,8
COFINS: ATA 0,00 | Deduções (-) 0
INSS: J ) 0,00 |Base de Cálculo (=) 42.892,
IR: 4) Pon dm 0,00 | Aliquota (%) 4;
CSLL: Y fo 0,00 | Valor do ISS (R$) 1.870,
Outras: / 7), / 0,00 | Valor Líquido da Nota (=) . 42.892,
Total de Retenções: e 4 0,00
Tipo de tributação: A RECOLHER PELO PRESTADOR Pata da prestação do serviço: 49/02/2028
Município da prestação do serviço: 2805701 - CAMACARI
Município da tributação: 2905701 - CAMACARI
CNAE: 8211-8/00 - SERVIÇOS COMBINADOS DE ESCRITÓRIO E APOIO ADMINISTRATIVO
Serviço: 001708 - PLANEJAMENTO, COORDENAÇÃO, PROGRAMAÇÃO OU ORGANIZAÇÃO TÉCNICA, FINANCEIRA OU ADMINISTRATIV)
CPqD - Gestão Pública Data Impressão: 49/02/2026 09:30
"""


@pytest.fixture
def nfse(monkeypatch):
    dummy_path = "tests/dummy_camacari3_nf148.pdf"
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
    assert nfse.numero == "148"


def test_valor_dos_servicos_vem_da_linha_do_item_nao_da_grade_truncada(nfse):
    # A grade lê "42.892,8" (truncado); a linha do item lê "42.892,92" duas
    # vezes (unitário e total) — a linha do item vence.
    val = nfse.valores
    assert val.valor_servicos == pytest.approx(42892.92)
    assert val.base_calculo == pytest.approx(42892.92)
    assert val.valor_iss == pytest.approx(1870.0)


def test_valor_liquido_ignora_captura_degenerada_do_ruido(nfse):
    # "Valor Líquido da Nota (=) . 42.892," captura só o "." solto (nenhum
    # dígito) — tratado como não encontrado, cai no fallback = Valor dos
    # Serviços (42.892,92), não 0,00.
    assert nfse.valores.valor_liquido_nfse == pytest.approx(42892.92)


def test_nenhum_aviso_de_aliquota_zerada(nfse):
    # A alíquota derivada (1.870,00 / 42.892,92 ≈ 4,36%) é plausível — a
    # guarda de "alíquota > 100%" não deve disparar aqui (o único aviso
    # possível nesta nota, "Dados do tomador não identificados", vem do
    # CNPJ do tomador — ver nota no teste da razão social abaixo — e é
    # ortogonal a este teste).
    assert "Alíquota/Valor do ISS não confiáveis" not in " ".join(nfse.avisos)


def test_tomador_razao_social_tolera_soclal_no_lugar_de_social(nfse):
    # "Nome/Razão Soclal:" ("i" lido como "l") não deve mais cair em
    # "Tomador Não Identificado".
    assert nfse.tomador.razao_social == "GUARAJUBA SHOPPING LTDA"
    # O CNPJ desta nota também sai corrompido no rótulo ("CPFI/CNPI:" em vez
    # de "CPF/CNPJ:", o "J" também virando "I" — não reconhecido pela
    # tolerância de rótulo `CPF[/I]CNPJ`). Recuperado pelo fallback SEM
    # rótulo introduzido para a nota nº 160 (busca o padrão de CNPJ
    # formatado em qualquer lugar do bloco já isolado do tomador, sem
    # depender do rótulo sobreviver) — antes caía no sentinela
    # `00000000000000` aqui (só recuperado em produção por
    # `_recuperar_cnpj_tomador_camacari`, um recorte à parte que re-OCRa a
    # imagem da página); agora extrai correto até no texto mockado.
    assert nfse.tomador.cnpj_cpf == "24890395000103"


def test_prestador_permanece_correto(nfse):
    assert nfse.prestador.cnpj_cpf == "59132742000113"
    assert nfse.prestador.razao_social == "AVANÇO GESTÃO E ADMINISTRAÇÃO LTDA"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
