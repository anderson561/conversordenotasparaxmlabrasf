import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
import os

# Texto real obtido via OCR (Tesseract) da NFTS de Lauro de Freitas/BA da
# nota 2026327 (LUNITECK -> BONI TRANSPORTES, pág. 2 de "LUNITECK_-_2418.pdf",
# 2 páginas — pág. 1 é a NFS-e original de Salvador/BA, muito degradada).
#
# Duas variações novas frente ao mock já coberto em
# test_lauro_de_freitas_nfts_grade_partida.py:
# 1) O separador do CNPJ do prestador sai "07,295.620/0001-44" — o 1º ponto
#    vira VÍRGULA no OCR (o resto da pontuação, inclusive a barra e o
#    hífen, sai correto). O regex antigo exigia "." literal nos 2
#    separadores e não casava NADA, caindo no sentinela "00000000000000".
# 2) Os campos finais do bloco do PRESTADOR ("Inscrição Estadual"/"Email:")
#    saem fisicamente DESLOCADOS para DEPOIS do cabeçalho "DISCRIMINAÇÃO DOS
#    SERVIÇOS" — sem parar antes deles, a discriminação engolia
#    "Inscrição Estadual O Erail:" junto com a descrição real do serviço.
MOCK_TEXT = """MUNICIPIO DE LAURO DE FREITAS
Secretaria da Fazenda

Número da Nota

2026327

Data e Hora de Emissão
14/07/2026 09:49:35

Coordenação Tributária
Nota Fiscal Eletrônica do Tomador de Serviços - NFTS

Código de Verificação
G6E3D7EC3

A autenticidade desta Nota Fiscal Eletrônica do Tomador de Serviços, podorá ser confirmada na página da MUNICIPIO DE LAURO DE FREITAS na
Internet, no endereço http:/Mww laurodefreitas,ba.gov.br

TOMADOR DE SERVIÇOS
CPF/CNPJ: 04.555.283/0003-50
inscrição 0010035914
Nome/Razão BONI TRANSPORTES, LOGÍSTICA E COMÉRCIO LTDA

Endereço: Rua Maria Quitéria, 263, QD UNICA

Bairro: Itinga Município: LAURO DE FREITAS UF: BA
CEP: 42738-205
PRESTADOR DE SERVIÇOS
CPF/CNPJICRI: 07,295.620/0001-44

Inscrição Inscrição Estadual:
Nome/Razão LUNITECK SOLUÇÕES E DESENVOLVIMENTO EM TECNOLOGIA LTDA ME

Endereço: AV ANTONIO CARLOS MAGALHÃES 25014 EDF PROFISSIONAL CEN, 2501,

Bairro: BROTAS Município: SALVADOR UF: BA
CEP: 40280-901

DISCRIMINAÇÃO DOS SERVIÇOS
SERVS.INFORMATICA MANT.ST.TEL.

Inscrição Estadual O

Erail:

VALOR TOTAL DA NOTA FISCAL : R$
CNAE

397,14

ITEM DA LISTA DE SERVIÇOS: (Lei Municipal 1572/2015 )

14,02 - Assistência técnica
Valor Total Deduções (R$) Base de Cálculo (R$) Alíquota (%)
0,00 397,14 5,00
397,14

VALOR LÍQUIDO DA NOTA FISCAL : R$

Valor do ISS (R$)
19,86
INFORMAÇÕES COMPLEMENTARES

Competência: 07/2026 - Tributado fora do Municipio de Lauro de Freitas - Responsável Recolhimento: Prestador

ISSQN Retido (R$)
Não

Documento Fiscal: Número: 2418.
Optante pelo Simples Nacional

Percentual de Totai da Dedução:
"""


def test_extract_lauro_de_freitas_cnpj_virgula_e_discriminacao_vazada(monkeypatch):
    dummy_path = "tests/dummy_lauro_freitas_2418.pdf"
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

        assert nfse.numero == "2026327"
        assert nfse.codigo_verificacao == "G6E3D7EC3"

        # BUG CORRIGIDO — CNPJ com vírgula no lugar do 1º ponto não pode
        # cair no sentinela "00000000000000".
        prest = nfse.prestador
        assert prest.cnpj_cpf == "07295620000144"
        assert prest.razao_social == "LUNITECK SOLUÇÕES E DESENVOLVIMENTO EM TECNOLOGIA LTDA ME"

        # BUG CORRIGIDO — discriminação não pode engolir os rótulos vazados
        # do bloco do prestador.
        assert nfse.discriminacao == "SERVS.INFORMATICA MANT.ST.TEL."
        assert "Inscri" not in nfse.discriminacao
        assert "Erail" not in nfse.discriminacao

        assert nfse.valores.base_calculo == pytest.approx(397.14)
        assert nfse.valores.aliquota == pytest.approx(0.05)
        assert nfse.valores.valor_iss == pytest.approx(19.86)

        assert nfse.avisos == []
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__])
