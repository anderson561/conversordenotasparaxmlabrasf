import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
import os

# Texto real extraído via pdfminer de uma NFTS real (Nota Fiscal Eletrônica
# do TOMADOR de Serviços) de Lauro de Freitas/BA (nota 2026302, 2026-05-11).
# Variante distinta da NFS-e regular já coberta em
# test_lauro_de_freitas_layout.py: aqui o cabeçalho "TOMADOR DE SERVIÇOS"
# vem ANTES de "PRESTADOR DE SERVIÇOS", e cada bloco sai completo/
# autocontido, sem vazamento — ver _extrair_entidade_lauro_freitas.
MOCK_TEXT = """MUNICIPIO DE LAURO DE FREITAS
Secretaria da Fazenda

Coordenação Tributária

Nota Fiscal Eletrônica do Tomador de Serviços - NFTS

Número da Nota

2026302

Data e Hora de Emissão

11/05/2026

09:37:09

Código de Verificação

A autenticidade desta Nota Fiscal Eletrônica do Tomador de Serviços, poderá ser confirmada na página da MUNICIPIO DE LAURO DE FREITAS na
Internet, no endereço http://www.laurodefreitas.ba.gov.br

549CB4D54

TOMADOR DE SERVIÇOS

CPF/CNPJ:

04.555.283/0003-50

Inscrição

0010035914

Inscrição Estadual

0

Nome/Razão

BONI TRANSPORTES, LOGÍSTICA E COMÉRCIO LTDA

Endereço:

Rua Maria Quitéria, 263, QD UNICA

Bairro:

Itinga

CEP:

42738-205

Município: LAURO DE FREITAS

UF: BA

Email:

PRESTADOR DE SERVIÇOS

CPF/CNPJ/CRI :

19.951.456/0001-65

Inscrição

Inscrição Estadual:

Nome/Razão

BDP LOGISTICA INTEGRADA DE RESIDUOS LTDA-ME

Endereço:

Rua Rua Da Matriz, 200, GALPAO 04

Bairro:

Valéria

CEP:

41300-600

Município: SALVADOR

UF: BA

Email:

DISCRIMINAÇÃO DOS SERVIÇOS
PRESTAÇÃO DE SERVIÇO ESPECIALIZADA PARA COLETA, TRANSPORTE E DESTINAÇÃO FIMAL DE RESIDUO SOLIDOS PERIGOSOS
DE CLASSE 1

VALOR TOTAL DA NOTA FISCAL :  R$

1.340,00

CNAE

ITEM DA LISTA DE SERVIÇOS:

( Lei Municipal 1572/2015 )

07.09  - Varrição, coleta, remoção, incineração, tratamento, reciclagem, separação e destinação final de lixo, rejeitos e outros resíduos
quaisquer

Valor Total Deduções (R$)

Base de Cálculo (R$)

Alíquota (%)

Valor do ISS (R$)

ISSQN Retido (R$)

0,00

1.340,00

5,00

67,00

Sim

VALOR LÍQUIDO DA NOTA FISCAL : R$

1.273,00

INFORMAÇÕES COMPLEMENTARES

Competência: 04/2026 - Tributado fora do Município de Lauro de Freitas - Responsável Recolhimento: Tomador

Documento Fiscal: Número: 23988.

Percentual de Total da Dedução:
"""


def test_extract_lauro_de_freitas_nfts_layout(monkeypatch):
    dummy_path = "tests/dummy_lauro_freitas_nfts.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        extractor.raw_text = MOCK_TEXT
        extractor.layout = extractor._detect_layout()

        assert extractor.layout == 'lauro_de_freitas_ba'

        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        assert nfse.numero == "2026302"
        assert nfse.codigo_verificacao == "549CB4D54"

        # Prestador: BDP LOGISTICA (Salvador). Cabeçalho "PRESTADOR DE
        # SERVIÇOS" vem DEPOIS de "TOMADOR DE SERVIÇOS" nesta variante NFTS
        # — sem esse tratamento, o bloco do prestador vira vazio e todo o
        # CNPJ/razão/endereço/município some.
        prest = nfse.prestador
        assert prest.cnpj_cpf == "19951456000165"
        assert prest.razao_social == "BDP LOGISTICA INTEGRADA DE RESIDUOS LTDA-ME"
        assert prest.endereco.logradouro == "Rua Rua Da Matriz"
        assert prest.endereco.numero == "200"
        assert prest.endereco.complemento == "GALPAO 04"
        assert prest.endereco.bairro == "Valéria"
        assert prest.endereco.municipio == "SALVADOR"
        assert prest.endereco.codigo_municipio == "2927408"
        assert prest.endereco.uf == "BA"
        assert prest.endereco.cep == "41300600"

        # Tomador: BONI TRANSPORTES (Lauro de Freitas) — não deve regredir.
        tom = nfse.tomador
        assert tom.cnpj_cpf == "04555283000350"
        assert tom.razao_social == "BONI TRANSPORTES, LOGÍSTICA E COMÉRCIO LTDA"
        assert tom.endereco.municipio == "LAURO DE FREITAS"
        assert tom.endereco.codigo_municipio == "2919207"
        assert tom.endereco.bairro == "Itinga"

        # Grade de valores sem o prefixo "R$" antes dos 2 primeiros números
        # (variação desta nota frente ao mock original de Lauro de Freitas).
        assert nfse.valores.valor_servicos == pytest.approx(1340.0)
        assert nfse.valores.base_calculo == pytest.approx(1340.0)
        assert nfse.valores.aliquota == pytest.approx(0.05)
        assert nfse.valores.valor_iss == pytest.approx(67.0)
        assert nfse.valores.iss_retido is True
        assert nfse.valores.valor_liquido_nfse == pytest.approx(1273.0)

        assert nfse.avisos == []
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__])
