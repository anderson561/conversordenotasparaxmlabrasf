import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
import os

# Texto REAL do OCR (Tesseract, zoom 4x + PSM 6 — ver SPPdfExtractor._ocr_armac)
# da Fatura de Locação escaneada da ARMAC (nota real 90109539, ARMAC -> SINAL
# CONSTRUTORA). Preservado verbatim, incluindo o ruído típico do OCR ("| ",
# "* ", "e ", "Es: -", "Valortotal" colado, "RUA Z", códigos de item
# "Eso1504"/"Rc0082s"). O mock alimenta o texto via extract_text (pdfminer),
# reproduzindo o que o _ocr_armac produziria, sem depender do Tesseract no CI.
MOCK_TEXT = """Fatura de Locação Número Fatura: | 90109539
a rm a C - Data Documento: | 10.07.2026
* Data Vencimento: 04.08.2026
Dados do Locador
Razão Social: * Armac Locação, Logística e Serviços
CNPJ: e 00.242.184/0001-04
IE CM 720.150.486.112
Endereço: | Estrada das Palmeira 430, Galpão 01
Endereço: |. 06730-000 Vargem Grande Paulista - SP
| Dados do Tomador |
Razão Social: | SINAL CONSTRUTORA LTDA
CNPJ/CPF: '-  33811381000148
Endereço: | Es: - RUA Z EVANGELINA SIQUEIRA DIAS 9995
Endereço: 48120-000 POJUCA - BA
ES01501 ESCAVADEIRA 207 SANY SY215H 15.05 2026 14062026 4 2400000 , 395,00 0.00 0,00 24 395.00 rd
Eso1504 ESCAVADEIRA 207 SANY SY215H 15.05.2026 14.06 2026 24.000,00 395,00 0,00 0.00 24 395.00
RC00824 SF PARTC. RC VBRT 107 XCMG 18.05.2026 14.06 2026 16.800,00 0,00 0.00 0,00 16.800,00
XS123PD
Rc0082s SF PARTC. RC VBRT 10T XCMG 18.05.2026 14.06 2026 16.800,00 0.00 0,00 0,00 16.800,00
XS123PD
MO00199 MOTONIVELADORA 167 CASE 8658 29.05.2026 14.06.2026 21.250,00 0,00 0,00 0,00 21.250,00
CC | cr PRateo!
Observações mem BRR
VISTO
Consultor: Total antes desc: 102.850,00
Condição pasto: 25 DDL Desconto: 0,00
Forma pagto: Boleto ARMAC - (CR) Seguro: E E 790,00
Vencimento: 04.08.2026 Avarias: 0,00
Mob/Desmob: 0,00
Valortotal: 103.640,00
* "OPERAÇÃO NÃO SUJEITA A RETENÇÃO DE ISSQN NOS TERMOS DA LEI
COMPLEMENTAR 116 DE 31/07/2003 QUE NÃO INCLUI LOCAÇÃO DE BENS MÓVEIS DA LISTA
DE SERVIÇOS."
"""


def test_extract_armac_locacao_layout(monkeypatch):
    dummy_path = "tests/dummy_armac_locacao.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        extractor.raw_text = MOCK_TEXT
        extractor.layout = extractor._detect_layout()

        assert extractor.layout == 'armac_locacao'

        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        assert nfse.numero == "90109539"
        assert nfse.codigo_verificacao == "FATURA"
        assert nfse.servico_codigo == "0601"
        assert nfse.data_emissao.strftime("%d/%m/%Y") == "10/07/2026"
        assert nfse.competencia.strftime("%m/%Y") == "07/2026"

        # Locador ARMAC (parseado do OCR, não hardcoded) — Vargem Grande
        # Paulista/SP não pode cair no fallback da capital (São Paulo).
        prest = nfse.prestador
        assert prest.cnpj_cpf == "00242184000104"
        assert prest.razao_social == "Armac Locação, Logística e Serviços"
        assert prest.endereco.logradouro == "Estrada das Palmeira"
        assert prest.endereco.numero == "430"
        assert prest.endereco.complemento == "Galpão 01"
        assert prest.endereco.municipio == "Vargem Grande Paulista"
        assert prest.endereco.codigo_municipio == "3556453"
        assert prest.endereco.uf == "SP"
        assert prest.endereco.cep == "06730000"

        # Tomador SINAL (Pojuca/BA) — não pode cair no fallback Salvador.
        tom = nfse.tomador
        assert tom.cnpj_cpf == "33811381000148"
        assert tom.razao_social == "SINAL CONSTRUTORA LTDA"
        assert tom.endereco.numero == "9995"
        assert tom.endereco.municipio == "POJUCA"
        assert tom.endereco.codigo_municipio == "2925303"
        assert tom.endereco.uf == "BA"
        assert tom.endereco.cep == "48120000"

        # Fatura de locação de bens móveis (não sujeita a ISS): Valor total
        # (com seguro) = 103.640,00; base/alíquota/ISS zerados.
        val = nfse.valores
        assert val.valor_servicos == pytest.approx(103640.00)
        assert val.valor_liquido_nfse == pytest.approx(103640.00)
        assert val.base_calculo == pytest.approx(0.00)
        assert val.aliquota == pytest.approx(0.00)
        assert val.valor_iss == pytest.approx(0.00)
        assert val.iss_retido is False

        # Discriminação = descrições dos equipamentos (deduplicadas).
        assert "ESCAVADEIRA 207 SANY SY215H" in nfse.discriminacao
        assert "MOTONIVELADORA 167 CASE 8658" in nfse.discriminacao

        assert nfse.avisos == []
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__])
