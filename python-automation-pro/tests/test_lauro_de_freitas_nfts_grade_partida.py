import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
import os

# Texto real obtido via OCR (Tesseract) de uma NFTS de Lauro de Freitas/BA
# (nota 2026326, LUNITECK -> BONI TRANSPORTES, pág. 2 de um PDF de 2 páginas
# cuja pág. 1 é a NFS-e original de Salvador/BA, emitida pelo prestador).
#
# Variação distinta da já coberta em test_lauro_de_freitas_nfts_layout.py:
# nesta digitalização a grade de valores sai PARTIDA em 3 pedaços não-
# contíguos ("Valor Total Deduções (R$) Base de Cálculo (R$) Alíquota (%)"
# com os 3 valores logo abaixo; "Valor do ISS (R$)" isolado, separado por
# "VALOR LÍQUIDO DA NOTA FISCAL"/"INFORMAÇÕES COMPLEMENTARES"/a linha de
# Competência; "ISSQN Retido (R$)" isolado mais abaixo ainda) — a regra
# antiga exigia os 5 rótulos contíguos numa linha só e caía no fallback
# zerado, perdendo Base de Cálculo/Alíquota/Valor do ISS mesmo eles estando
# presentes e legíveis. Também exercita o "UF;" (ponto-e-vírgula no lugar do
# ":", ruído de OCR) na linha "Bairro: Itinga Município: LAURO DE FREITAS
# UF; BA" do bloco do tomador — o lookahead antigo só tolerava ":" e vazava
# "UF; BA" inteiro para dentro do campo Município.
MOCK_TEXT = """MUNICIPIO DE LAURO DE FREITAS
Secretaria da Fazenda

Número da Nota
2026326
Data e Hora de Emissão

14/07/2026 09:48:05

Coordenação Tributária
Nota Fiscal Eletrônica do Tomador de Serviços - NFTS

Código de Verificação

A autenticidada desta Nota Fiscal Eletrônica do Tomador de Servigos, poderá ser confirmada na página da MUNICIPIO DE LAURO DE FREITAS na FE549A893

Internet, no endereço hitp:/fwww laurodefreitas. ba.gov.br

TOMADOR DE SERVIÇOS
CPF/CNPJ: 04.555.283/0003-50
Inscrição 0010035914
Nome/Razão BONI TRANSPORTES, LOGÍSTICA E COMÉRCIO LTDA
Endereço: Rua Maria Quitéria, 263, QD UNICA

Inscrição Estadual O

Bairro: Itinga Município: LAURO DE FREITAS UF; BA
CEP: 42738-205 Email:

PRESTADOR DE SERVIÇOS
CPF/CNPJICRI: 07.295.620/0001-44

Inscrição Inscrição Estadual:
Nome/Razão LUNITECK SOLUÇÕES E DESENVOLVIMENTO EM TECNOLOGIA LTDA ME

Endereço: AV ANTONIO CARLOS MAGALHÃES 2501 EDF PROFISSIONAL CEN » 2501,

Bairro: BROTAS Município: SALVADOR UF: BA
CEP: 40280-901 Email:

DISCRIMINAÇÃO DOS SERVIÇOS
SERVS. INFORMATICA MANT.ST.CAM.

VALOR TOTAL DA NOTA FISCAL : R$
CNAE

ITEM DA LISTA DE SERVIÇOS: (Lei Municipal 1572/2015)
14.02 - Assistência técnica

Valor Total Deduções (R$) Base de Cálculo (R$) Alíquota (%)
0,00 397,14 5,00

VALOR LÍQUIDO DA NOTA FISCAL : R$ 397,14

Valor do ISS (R$)
19,86
INFORMAÇÕES COMPLEMENTARES

Competência: 07/2026 - Tributado fora do Município de Lauro de Freitas - Responsável Recolhimento: Prestador

ISSQN Retido (R$)
Não

Documento Fiscal: Número: 2419.
Optante pelo Simples Nacional

Percentual de Total da Dedução:
"""


def test_extract_lauro_de_freitas_nfts_grade_partida(monkeypatch):
    dummy_path = "tests/dummy_lauro_freitas_nfts_grade_partida.pdf"
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

        assert nfse.numero == "2026326"
        assert nfse.codigo_verificacao == "FE549A893"

        prest = nfse.prestador
        assert prest.cnpj_cpf == "07295620000144"
        assert prest.razao_social == "LUNITECK SOLUÇÕES E DESENVOLVIMENTO EM TECNOLOGIA LTDA ME"
        assert prest.endereco.municipio == "SALVADOR"
        assert prest.endereco.codigo_municipio == "2927408"
        assert prest.endereco.uf == "BA"

        # Tomador: município vem com "UF;" (ponto-e-vírgula) na mesma linha —
        # sem o fix, "LAURO DE FREITAS UF; BA" inteiro vazava pro município.
        tom = nfse.tomador
        assert tom.cnpj_cpf == "04555283000350"
        assert tom.razao_social == "BONI TRANSPORTES, LOGÍSTICA E COMÉRCIO LTDA"
        assert tom.endereco.municipio == "LAURO DE FREITAS"
        assert tom.endereco.uf == "BA"
        assert tom.endereco.codigo_municipio == "2919207"
        assert tom.endereco.bairro == "Itinga"

        # Grade de valores partida em 3 pedaços não-contíguos: sem o fix,
        # tudo isso saía zerado (só valor_servicos/valor_liquido_nfse
        # sobreviviam, via os rótulos "VALOR TOTAL"/"VALOR LÍQUIDO" à parte).
        assert nfse.valores.valor_servicos == pytest.approx(397.14)
        assert nfse.valores.base_calculo == pytest.approx(397.14)
        assert nfse.valores.aliquota == pytest.approx(0.05)
        assert nfse.valores.valor_iss == pytest.approx(19.86)
        assert nfse.valores.iss_retido is False
        assert nfse.valores.valor_liquido_nfse == pytest.approx(397.14)

        assert nfse.avisos == []
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__])
