# -*- coding: utf-8 -*-
"""Texto REAL do OCR (Tesseract) da NFS-e de Camaçari/BA ESCANEADA — nota real
nº 258, AVANÇO GESTÃO E ADMINISTRAÇÃO LTDA -> GUARAJUBA MALLS S/A (4º PDF do
lote Guarajuba Shopping, "NFSe TOMADOS 4.pdf", página 7 de 7). Reportado pelo
usuário: "a página 7 foi extraída com o número da nota incorreto: 9, o número
correto é: 258".

`_ocr_header_box_camacari` faz várias tentativas redundantes de ler a caixa
"Número da Nota / Data de Emissão / Código de autenticidade". Nesta nota:
 - na ÚNICA tentativa em que o RÓTULO sai limpo ("Número da Nota"), o VALOR
   logo abaixo saiu ilegível ("PaACnno um", nenhum dígito) — a extração
   genérica de proximidade "vazava" para a linha seguinte ("Data de Emissão
   \\n09/06/2026") e devolvia "09" (a data, não o número);
 - o valor real ("258") sobrevive limpo noutra tentativa, onde é o RÓTULO que
   sai ilegível ("INUMMGTO OA Feia RA MO ea DR O") — nunca reconhecido pelo
   regex de rótulo.

Regressão travada: a nota nº 20335 (PADUA COMÉRCIO, `test_camacari3_padua_layout.py`)
NUNCA deve acionar o novo ramo — lá o rótulo "Número da Nota" nunca bate limpo
em nenhuma tentativa, e a correção já existente (nome do arquivo) depende
exatamente disso.
"""
import os

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_TEXT = """INUMMGTO OA Feia RA MO ea DR O

258 PURO ll o

Data de Emissão ed) NE EE
09/06/2026 11:01. Ci ta:

Código de autenticidade | | Vi |
0H60HVVSQ |, PER

166628001 1 Na apto dl
ur: BA dt hip tp ldil

Kero 04 reuia RO DD NM LT
à de Emissão Ra AN |
09/06/2026 11:01, + bd.
igo de autenticidade | E N

OHGOHVVSQ 4 gy
eu hd
| vtd)
ur: BA dit LM iil

Número da Nota PaACnno um

Data de Emissão Poa NE |
09/06/2026 11:01 it tj

Código de autenticidade | E HE
OH60HVVSQ |, da it

seem quero eahoo pi y bi

Ê H [

0066628001 Ri Ni
* GORDO) É: Hi) MI:
UF: BA di lh "4

di Número da Nota Fatal % gs
nc PREFEITURA MUNICIPAL DE CAMAÇARI ass
Nie Secretaria da Fazenda SANS rca TEM dl HI
TAI LEAR 9106/2026 11:01. pH q:
Cano NOTA FISCAL DE SERVIÇOS ELETRÔNICA ea area EAR
A oHGoHVVSa fi
PRESTADOR DE SERVIÇOS a
Nome/Razão Social: AVANÇO GESTÃO E ADMINISTRAÇÃO LTDA PR | | um
CPF/CNPJ: 59.132.742/0001-13 Inscrição Municipal: 0066628001 UE | | |
Logradouro: RUA ALA DAS DUNAS Nº: SN! id 1)
Compl: :GUARAJUBA SHOPPING;LOJA:03;QUADRA:C-4 Bairro: GUARAJUBA (MONTE GORDO) ni || dl,
CEP: 42840312 Município: CAMAÇARI ve: a dê fi |
TOMADOR DE SERVIÇOS Al)
Nome/Razão Social: GUARAJUBA MALLS S/A TRAIN Hi
CPFICNPJ: 24.890.395/0001-03 Inscrição Municipal: 0032035001 | MET
Logradouro: RODOVIA BA 099 ESTRADA DO COCO ne sn it
Compl.: ALAMEDA DAS DUNAS GUARAJUBA SHOPPING — Bairro: GUARAJUBA (MONTE GORDO) ML o]
CEP: 42840310 Município: CAMAÇARI PA oh
ur: BA ih)
DISCRIMINAÇÃO DOS SERVIÇOS | VE Hom
ra mg a QTD VALOR UNIT (R$) VALOR TOTAL, ln$) [Ui
TAXA DE SERVIÇOS COMBINADOS DE ESCRITÓRIO E APOIO ADMINISTRATIVO 1,0000 512,28 512,48!) HI)

Digi E
[Elbgmesca XML PDF [o)pgiiaii |
Retenções (R$) Totais (R$) V
PIS: 0,00 | Valor dos Serviços (R$) 512,28: 1]
COFINS: 0,00 |Deduções (-) 0,00)
INSS: 0,00 | Base de Cálculo (=) 512,28 |
IR: 0,00 | Alíquota (%) 5,00
CSLL: 0,00 |Valor do ISS (R$) 2561 |.
a Outras: 0,00 | Valor Líquido da Nota (=) 512,28
o Total de Retenções: 0,00 A
Tipo de tributação: A RECOLHER PELO PRESTADOR Data da prestação do serviço: 09/06/2026 é
À Município da prestação do serviço: 2905701 - CAMACARI
Município da tributação: 2905701 - CAMACARI ;
CNAE: 8211-3/00 - SERVIÇOS COMBINADOS DE ESCRITÓRIO E APOIO ADMINISTRATIVO
Serviço: 001703 - PLANEJAMENTO, COORDENAÇÃO, PROGRAMAÇÃO OU ORGANIZAÇÃO TÉCNICA, FINANCEIRA OU ADMINISTRATIVA.
CPqD - Gestão Pública Data Impressão: 09/06/2026 11:01 NR
"""


@pytest.fixture
def nfse(monkeypatch):
    dummy_path = "tests/dummy_camacari3_nota258.pdf"
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


def test_numero_nao_cai_na_data_contaminada(nfse):
    # Antes do fix: o rótulo "Número da Nota" bate limpo, mas o valor logo
    # abaixo é ilegível — a busca vazava para "Data de Emissão\n09/06/2026" e
    # devolvia "09" (virando "9" na serialização). O valor real ("258")
    # sobrevive numa tentativa de recorte anterior, com o RÓTULO ilegível.
    assert nfse.numero == "258"


def test_demais_campos_permanecem_corretos(nfse):
    assert nfse.prestador.cnpj_cpf == "59132742000113"
    assert nfse.tomador.cnpj_cpf == "24890395000103"


def test_valor_dos_servicos_ignora_total_da_linha_do_item_com_digito_trocado(nfse):
    # A linha do item leu "1,0000 512,28 512,48" (total com um dígito de
    # centavo trocado, "2"->"4"); como a quantidade é "1", unitário e total
    # deveriam ser idênticos — a divergência descarta o total da linha do
    # item, e as 3 células da grade (consistentes em "512,28") prevalecem.
    val = nfse.valores
    assert val.valor_servicos == pytest.approx(512.28)
    assert val.base_calculo == pytest.approx(512.28)
    assert val.valor_liquido_nfse == pytest.approx(512.28)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
