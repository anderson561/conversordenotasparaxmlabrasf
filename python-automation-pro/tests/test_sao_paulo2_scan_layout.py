import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_SAO_PAULO, LAYOUT_SAO_PAULO_2
import os

# Texto REAL do OCR (Tesseract) da NFS-e de São Paulo ESCANEADA (JPG fotografado,
# convertido em PDF e rotacionado 180° — nota real nº 00331020, BOM NEGOCIO ->
# PORTO UNO). Preservado verbatim, incluindo:
#  - a linha limpa "Número da Nota\n00331020" vinda do recorte dedicado do
#    cabeçalho (_ocr_header_box_sao_paulo), prependida ao texto — na página
#    inteira o número sai corrompido (vira "5");
#  - o ruído de 2 colunas ("|", "a ” ;", "Es: -"), os valores-isca do COFINS
#    ("Valor ISS: 137,06" que na verdade é 7,60% de COFINS) e o texto da Lei
#    12.741 misturado na discriminação.
# O mock alimenta o texto via _extract_via_ocr, ativando o caminho from_ocr=True
# (que é o que distingue o SP escaneado do SP digital), sem depender do Tesseract.
MOCK_TEXT = """Número da Nota
00331020

Número da Nota

“PREFEITURA DO MUNICÍPIO DE SÃO PAULO a

Data e Hora de Emissão

SECRETARIA MUNICIPAL DA FAZENDA
5 25/06/2026 11:47:50
NOTA FISCAL ELETRÔNICA DE SERVIÇOS - NFS-e Código de Verificação
RPS Nº 320839 Série NF, emitido em 25/06/2026 PQHZ-BYVT

20260629U13673743000255
Identificador Nacional: 3550308121 3673743000417000000033102026066239391145)

PRESTADOR DE SERVIÇOS |
Inscrição Municipal: 5.134.892-6 |

CPF/CNPJ: 13.673.743/0004-17
Nome/Razão Social: BOM NEGOCIO ATIVIDADES DE INTERNET LTDA
Endereço: AV PAULISTA 1106, CONJ 151 152 E 153 - BELA VISTA = CEP: 01310-914

Município: São Paulo UF: SP

TOMADOR DE SERVIÇOS

Nome/Razão Social: PORTO UNO AGENCIA DE IMOVEIS LTDA

CPF/CNPJ: 04.022.897/0001-05
| Endereço: R Alameda Salvador 1057 - Caminho das Árvores - CEP: 41820-790 |
Município: Salvador UF: BA E-mail: anaritaGportouno.com.br, |
: |

INTERMEDIÁRIO DE SERVIÇOS

o
| CPF/CNPJ: =. Nome/Razão Social: ----
DISCRIMINAÇÃO DE SERVIÇOS

Inscrição Municipal: ----

|
| IMC - PLANO ZAP+ (ZAP+VIVA+OLX)
| Valor Bruto: 1803.45

NTES - REF. A LEI 12.741 de 08/12/2012 |

R$ 52.30 PERC. PIS: 1.65% VALOR PIS: R$ 29.76 PERC.

| ALIQUOTAS DOS TRIBUTOS INCIDE
| PERC. ISS 2.90% Valor ISS:
137,06

COFINS: 7.60% VALOR COFINS: R$

VALOR TOTAL DO SERVIÇO = R$ 1.803,45
Contribuição Previdenciária - Retida (R$) IRRF (R$) COFINS (R$) PIS/PASEP (R$) IPL(RS)
b 0,00 0,00 0,00 0,00 0,00

Código do Serviço a ” ;

02498 - Inserção de textos, desenhos e outros materiais de propaganda e publicidade, em qualquer meio.

Valor Total das Deduções (R$) Base de Cálculo (R$) | Alíquota (%) Valor do ISS (R$) crédito Programa da NEP(RS)
0,00 1.803,45 2,90% 52,30 0,00

OUTRAS INFORMAÇÕES
"""


def test_sao_paulo_digital_nao_vira_sp2():
    """Blindagem: o SP DIGITAL (texto embutido, from_ocr=False) continua sendo
    detectado como LAYOUT_SAO_PAULO. O layout digital não pode regredir por
    causa do novo layout escaneado."""
    dummy_path = "tests/dummy_sp_digital.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = "PREFEITURA DO MUNICÍPIO DE SÃO PAULO\nNúmero da Nota: 7788"
    extractor.from_ocr = False  # texto embutido (pdfminer), não OCR

    assert extractor._detect_layout() == LAYOUT_SAO_PAULO

    if os.path.exists(dummy_path):
        os.remove(dummy_path)


def test_extract_sao_paulo2_scan_layout(monkeypatch):
    dummy_path = "tests/dummy_sao_paulo2.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    # extract_text vazio força o caminho de OCR do parse_multiple, que seta
    # self.from_ocr=True; _extract_via_ocr devolve o texto real capturado.
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        # Número (00331020) e código de verificação (PQHZ-BYVT) vêm do recorte
        # dedicado / do fim da linha do RPS — na página inteira saíam "5"/"RPSN".
        assert nfse.numero == "00331020"
        assert nfse.codigo_verificacao == "PQHZ-BYVT"
        # Item de serviço do cadastro paulistano (não o fallback 03115).
        assert nfse.servico_codigo == "02498"
        assert nfse.data_emissao.strftime("%d/%m/%Y") == "25/06/2026"
        assert nfse.competencia.strftime("%m/%Y") == "06/2026"

        # Prestador em São Paulo/SP; tomador em Salvador/BA (Caminho das Árvores).
        assert nfse.prestador.cnpj_cpf == "13673743000417"
        assert nfse.prestador.razao_social == "BOM NEGOCIO ATIVIDADES DE INTERNET LTDA"
        assert nfse.prestador.endereco.codigo_municipio == "3550308"
        assert nfse.tomador.cnpj_cpf == "04022897000105"
        assert nfse.tomador.razao_social == "PORTO UNO AGENCIA DE IMOVEIS LTDA"
        assert nfse.tomador.endereco.codigo_municipio == "2927408"
        assert nfse.tomador.endereco.uf == "BA"

        # NFS-e tributada: ISS real de 2,90% = 52,30 sobre a base — NÃO o
        # valor-isca do COFINS (137,06 = 7,60%) que aparece no corpo do texto.
        val = nfse.valores
        assert val.valor_servicos == pytest.approx(1803.45)
        assert val.base_calculo == pytest.approx(1803.45)
        assert val.aliquota == pytest.approx(0.029)
        assert val.valor_iss == pytest.approx(52.30)
        assert val.valor_liquido_nfse == pytest.approx(1803.45)

        # Discriminação limpa (sem os rótulos/lei/PIS vazados).
        assert nfse.discriminacao == "IMC - PLANO ZAP+ (ZAP+VIVA+OLX)"

        assert nfse.avisos == []
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
