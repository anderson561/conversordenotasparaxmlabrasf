# -*- coding: utf-8 -*-
"""Texto REAL do OCR (Tesseract) da NFS-e de Camaçari/BA ESCANEADA — nota real
nº 256, AVANÇO GESTÃO E ADMINISTRAÇÃO LTDA -> GUARAJUBA MALLS S/A (5º PDF do
lote Guarajuba Shopping, "NFSe TOMADOS 5.pdf", página 2 de 6). Reportado pelo
usuário: "o número da nota fiscal saiu incorreto: 9, o correto é 256".

Ao contrário da nota nº 258 (`test_camacari3_numero_contaminado_por_data_guarajuba.py`,
onde a ÚNICA ocorrência limpa do rótulo "Número da Nota" tinha o valor
contaminado), aqui é o INVERSO: a PRIMEIRA ocorrência do rótulo é que está
contaminada (o valor vaza para a data seguinte, "09/06/2026" -> "09"), mas uma
tentativa de recorte POSTERIOR no mesmo texto repete o rótulo com o valor
limpo ("Número da Nota\n256"). A extração original só olhava a PRIMEIRA
ocorrência do rótulo (via `re.search`) e nunca chegava a ver a tentativa boa
mais adiante.
"""
import os

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_TEXT = """Número da Nota PR Eid
Data de Emissão E! WU ta
09/06/2026 09:09 [a
Código de autenticidade es RR )
088015735 dita
66628001 DR
Nº: SN Poti
ORDO) hi RE
UF: BA E dk

RS
ero da Nota AN m
de Emissão Po pi
09/06/2026 09:09 UM o | v É
go de autenticidade HR
088015735 nl | o
Nº: SN pot)
UF: BA õ N

Número da Nota dk fui É
256 PE RR
Data de Emissão Po (Uta
09/06/2026 09:09 [a
Código de autenticidade gs RR A
088015735 pia
0066628001 a É
Nº: SN Poti
GORDO) pd

! E E Número da Nota ka 4
FE PREFEITURA MUNICIPAL DE CAMAÇARI 256 il:
| fas! Data de Emissão Ra Rd
: qi Secretaria da Fazenda ogoBizoz6osos | Li
. ei NOTA FISCAL DE SERVIÇOS ELETRÔNICA Código de autenticidade id
(iii, 088015735 Uta
PRESTADOR DE SERVIÇOS EM
" Nome/Razão Social: AVANÇO GESTÃO E ADMINISTRAÇÃO LTDA pa
* CPF/CNPJ: 59.132.742/0001-13 Inscrição Municipal: 0066628001 E SA
Logradouro: RUA ALA DAS DUNAS Nº: SN po :
Compl.: —:GUARAJUBA SHOPPING;LOJA:03;QUADRA:C-4 Bairro: GUARAJUBA (MONTE GORDO) ) | !
CEP: 42840312 Município: CAMAÇARI UF: BA Pao ! lt
TOMADOR DE SERVIÇOS dd
Nome/Razão Social: GUARAJUBA MALLS S/A OR ||
CPF/CNPJ: 24.890.395/0001-03 Inscrição Municipal: 0032035001 col tdi
Logradouro: — RODOVIA BA 099 ESTRADA DO COCO Nº SN EE
Compl.: ALAMEDA DAS DUNAS GUARAJUBA SHOPPING Bairro: GUARAJUBA (MONTE GORDO) Vo Ro
CEP: 42840310 Município: CAMAÇARI UF: BA À j | E
DISCRIMINAÇÃO DOS SERVIÇOS | |
DESCRIÇÃO QTD VALOR UNIT (R$) VALOR TOTAL (R%) É
TAXA DE SERVIÇOS COMBINADOS DE ESCRITÓRIO E APOIO ADMINISTRATIVO 1,0000 2.350,90 2. 38,90 '
EE A f/ 5) lh o (mM) PDF ELSA |
Retenções (R$) Totais (R$) pol
PIS: 0,00 | Valor dos Serviços (R$) 2.350,90. | 1:
COFINS: 0,00 | Deduções (-) 0,00 |
INSS: 0,00 | Base de Cálculo (=) 2.350,90. |
IR: 0,00 | Alíquota (%) 500, |,
CSLL: 0,00 | Valor do ISS (R$) 17,544 |
Outras: 0,00 | Valor Líquido da Nota (=) 2.350,90 |
Total de Retenções: 0,00 Ro |
Tipo de tributação: A RECOLHER PELO PRESTADOR Data da prestação do serviço: 09/06/2026 |
Município da prestação do serviço: 2905701 - CAMACARI
Município da tributação: 2905701 - CAMACARI E
CNAE: 8211-3/00 - SERVIÇOS COMBINADOS DE ESCRITÓRIO E APOIO ADMINISTRATIVO
Serviço: 001703 - PLANEJAMENTO, COORDENAÇÃO, PROGRAMAÇÃO OU ORGANIZAÇÃO TÉCNICA, FINANCEIRA OU ADMINISTRATIVA.
"""


@pytest.fixture
def nfse(monkeypatch):
    dummy_path = "tests/dummy_camacari3_nota256.pdf"
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


def test_numero_nao_para_na_primeira_ocorrencia_contaminada(nfse):
    # A 1ª ocorrência de "Número da Nota" vaza para a data seguinte ("09"); a
    # 3ª ocorrência do mesmo rótulo, mais adiante, tem o valor limpo ("256").
    assert nfse.numero == "256"


def test_demais_campos_permanecem_corretos(nfse):
    assert nfse.prestador.cnpj_cpf == "59132742000113"
    assert nfse.tomador.cnpj_cpf == "24890395000103"
    assert nfse.valores.valor_servicos == pytest.approx(2350.90)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
