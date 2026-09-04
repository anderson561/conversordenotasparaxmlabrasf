# -*- coding: utf-8 -*-
"""Salvador/BA escaneado — nota real nº 00054394 (M ESCRITA COMERCIO E
SERVICOS LTDA -> GUARAJUBA SHOPPING LTDA, locação de bens móveis, R$391,57).

O CNPJ do TOMADOR (Guarajuba Shopping, real 24.890.395/0001-03) sai
consistentemente lido "24.890.396/0001-03" neste scan (o "5" de ".395" virou
"6") — um único dígito trocado que reprova o dígito verificador (a base
"...396..." fecha em "-58", não em "-03"). Sem nenhum outro CNPJ válido
sobrando no documento para o fallback de "scavenge" (`_scavenge_all_cnpjs`)
usar, o tomador caía no sentinela `00000000000100` mesmo com a razão social
"GUARAJUBA SHOPPING LTDA" extraída corretamente. Corrigido pela mesma
premissa já usada para BONI TRANSPORTES: quando o CNPJ capturado reprova o
checksum E a razão social bate com esta contraparte recorrente conhecida
(tomadora fixa num lote de 30 notas em municípios/layouts diferentes),
substitui pelo CNPJ real confirmado pelo usuário — nunca mascarando um CNPJ
genuinamente diferente de outra empresa."""
import os

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_OCR = """BASE_CALCULO_RECUPERADA: 0,00
CPF/CNPJ:
16.306.870/0001-23

TOMADOR DE SERVIÇOS

Nome/Razão Social:

GUARAJUBA SHOPPING LTDA
CPF/CNPJ: : Inscrição Municipal:
24.890.396/0001 -03 duma
Endereço:
AL MONTE DAS DUNAS SN GUARAJUBA - Camaçari - CEP: 42827 -000/BA
CIDA
DISCRIMIN
LOCACA

ÇÃO DOS SERVICOS
O DE MAQUINAS E EQUIPAMENTOS
- 63 - MÊS: DEZEMBRO/2025

- VENCIMENTO: 25/02/2026

TRIBUTOS 9,45% LEI 12.741 DE 2012

NÃO INCIDENCIA ISS CONFORME LC 116/2003 E LISTA DE SERVIÇO ANEXA À LEI 7.186/2006

-ass/2026

VALOR TOTAL DA NOTA = R$391,57

CNAE:
7733100 - ALUGUEL DE MÁQUINAS E EQUIPAMENTOS PARA ESCRITÓRIOS

item da Lista de Serviços:
00000 - Locação de bens móvels

Valor Total das Deduções (R$): Base de Cálculo (R$): Alíquota (9%): Crédito Nota Salvador (R$):
0,00 391,67 0,00% 0,00 0,00
Valor INSS (R$): Valor PIS (R$): Valor COFINS (R$): | Valor IR (R$): Valor CSLL (R$): Valor Líquido (R$):
0,00 0,00 0,00 0,00 0,00 0,00 391,57
“ “

OUTRAS INFORMAÇÕES

- Esta Nota Salvador foi emitida com respaldo na Lei 7.186/2006.

- O código de serviço referento a esta Nota Salvador não gera crédito.

- Esta Nota Salvador substitui O RPS Nº 70668 Sério 1, emitido em 02/02/2026.
- COMPETÊNCIA: 02/2026 (mês/ano)

- Código de Tributação do Municipio: 0000-0/01 - Locação de bens móveis

https:/nfse.salvador.ba.gov.br/site/contribuinte/nota/notaprint.as
Número da Nota:
00054394

E ii irem iii ii

-Infse.salvador.ba.gov.br/site/contribuinte/nota/notaprint.as

Número da Nota:
LVADOR 00054394

JA Data e Hora de Emissão:
02/02/2026 15:06:15
codigo de Verificação:
BWNVIZ-DVQA

- Nota Salvador

vador https://nfse.salvador.ba.gov.br/site/contribuinte/nota/notaprint.as
Poe Número da Nota:
Pa PREFEITURA MUNICIPAL DO SALVADOR 00054394
N N SECRETARIA MUNICIPAL DA FAZENDA Data e Hora de Emissão:
RS 02/02/2026 15:06:15
aa pa a Código de Verificação:
NOTA FISÇAL D VIÇOS RÔNICA -
CAM PR SERVIÇOS ELETRÔNICA: Nota salvador | EWMEDVOA
PRESTADOR DE SERVIÇOS
CPF/CNPJ: Inscrição Municipal: a
16.306.870/0001-23 00.061 .234/001-89 PEPE
Nome/Razão Social M
ESCRITA COMERCIO E SERVICOS LTDA e )
Endereço:
o dim Gonzaga 199 - ALPHAVILLE | - Salvador - CEP: 41701-016 - BA SCE
-mail.
notaggescrita-e.com.br
TOMADOR DE SERVIÇOS
Nome/Razão Social:
GUARAJUBA SHOPPING LTDA
CPF/CNPJ: E Inscrição Municipal:
24.890.396/0001-03 —
Endereço:
a MONTE DAS DUNAS SN GUARAJUBA - Camaçar! - CEP: 42827-000/BA
-mail:
FISCAL. CIDAGPGMAIL.COM
PISSRIMINAÇÃO, DOS SERMÇOS
- 63 - MÊS: DEZEMBRO/2025
- VENCIMENTO: 25/02/2026
TRIBUTOS 9,45% LEI 12.741 DE 2012
NÃO INCIDENCIA 15$ CONFORME LC 116/2003 E LISTA DE SERVIÇO ANEXA À LEI 7.186/2006
-ass/2026
VALOR TOTAL DA NOTA = R$391,57
CNAE:
7733100 - ALUGUEL DE MÁQUINAS E EQUIPAMENTOS PARA ESCRITÓRIOS
Item da Lista de Serviços:
00000 - Locação de bens móvels
0,00 391,67 0,00% 0,00 0,00
Valor INSS (R$): Valor PIS (R$): Valor COFINS (R$): | Valor IR (R$):
0,00 0,00 0,00 0,00 0,00 0,00 391,67
OUTRAS INFORMAÇÕES
— Esta Nota Salvador foi emitida com respaldo na Lei 7.186/2006.
- O código de serviço referente à esta Nota Salvador não gera crédito.
- Esta Nota Salvador substitui O RPS Nº 70668 Sório 1, emitido em 02/02/2026.
- COMPETÊNCIA: 02/2026 (môs/ano)
- Código de Tributação do Município: 0000-0/01 - Locação de bens móveis
"""


@pytest.fixture
def nfse(monkeypatch):
    dummy_path = "tests/dummy_salvador_guarajuba_54394.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_OCR)

    try:
        nfse_list = SPPdfExtractor(dummy_path).parse_multiple()
        assert len(nfse_list) == 1
        yield nfse_list[0]
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_numero_da_nota(nfse):
    assert nfse.numero == "00054394"


def test_tomador_cnpj_digito_trocado_corrigido_por_contraparte_conhecida(nfse):
    # "24.890.396/0001-03" (checksum inválido) -> "24.890.395/0001-03" (real,
    # confirmado pelo usuário) só porque a razão social bate com a contraparte
    # recorrente GUARAJUBA SHOPPING — nunca aplicado a outra empresa.
    assert nfse.tomador.cnpj_cpf == "24890395000103"
    assert nfse.tomador.razao_social == "GUARAJUBA SHOPPING LTDA"


def test_prestador_cnpj_permanece_inalterado(nfse):
    # Blindagem: a correção da contraparte conhecida não deve afetar o
    # prestador, cujo CNPJ já é legível e válido nesta nota.
    assert nfse.prestador.cnpj_cpf == "16306870000123"


def test_valor_dos_servicos(nfse):
    assert nfse.valores.valor_servicos == pytest.approx(391.57)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
