import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_LOCALIZA
import os


# Texto real extraído (pdfminer) de uma fatura real da Localiza Rent A Car
# ("LOCALIZA TERESA 03.06.pdf", cliente TEMIS PROJETOS DE MEIO AMBIENTE E
# SUSTENTABILIDADE LTDA, fatura 216421). O PDF não tem quebras de linha entre
# os rótulos do cabeçalho (tudo em um único bloco de texto corrido), e alguns
# sufixos societários vêm colados à palavra anterior sem espaço (ex.:
# "SUSTENTABILIDADELTDA") — ambos os problemas já causaram bugs reais no
# extrator (ver correções em pdf_extractor.py).
REAL_MOCK_TEXT = (
    "LOCALIZA RENT A CAR S/A AGENCIA CENTRO CABULA ROD BR 324, 1084 - "
    "CABULA41150-170 - SALVADOR - BA CNPJ - 16.670.085/0914-44 "
    "ASSISTÊNCIA A CLIENTES TEL 0800 979 2020 assistenciaaclientes@localiza.com   "
    "FATURA / DUPLICATANº: ACBUL - 216421CLIENTE: TEMIS PROJETOS DE MEIO AMBIENTE E "
    "SUSTENTABILIDADELTDA ENDEREÇO: RUA TERRITORIO DO AMAPA, 146 CS 2 - PITUBA "
    "CEP/CID/UF: 41830-540 - SALVADOR - BA CNPJ:  07.345.543/0001-90 "
    "CÓDIGO: 02640209 INSC. ESTADUAL:  069725483  DATA DE EMISSÃO: 22/05/2026  "
    "DESCRIÇÃO VALOR ALUGUEL CONFORME CONTRATO     BULF041739  R$ 6.002,22 "
    "VALOR DO SEGURO R$ 178,50           "
    "VENCIMENTOCONDIÇÕES DE PAGAMENTOVALOR TOTAL06/06/2026 A PRAZO R$ 6.180,72 "
    "Não contribuinte de ISS s/locação cfe. LC n. 116/03        "
    "Sacador: Aceite:  Valor da faturaValor da faturaR$ 6.180,72"
    "Data de Vencimento06/06/2026 "
    "CNPJ/CPF do beneficiário 16.670.085/0001-55 "
    "Data do documento 22/05/2026"
    "Número do documento EPR000647A59Nosso número. Uso do banco"
)


def _novo_extractor(mock_text: str, dummy_name: str) -> SPPdfExtractor:
    dummy_path = f"tests/{dummy_name}"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = mock_text
    return extractor


def _limpar(dummy_name: str):
    dummy_path = f"tests/{dummy_name}"
    if os.path.exists(dummy_path):
        os.remove(dummy_path)


def test_detect_localiza_layout():
    """Testa a detecção correta do layout Localiza (fatura de locação)."""
    extractor = _novo_extractor(REAL_MOCK_TEXT, "dummy_localiza_detect.pdf")
    try:
        layout = extractor._detect_layout()
        assert layout == LAYOUT_LOCALIZA, f"Expected {LAYOUT_LOCALIZA}, got {layout}"
    finally:
        _limpar("dummy_localiza_detect.pdf")


def test_extract_localiza_full_fatura_real_document():
    """Regressão: a extração completa contra o texto real de uma fatura
    Localiza estava totalmente quebrada (o bloco do prestador usava um campo
    inexistente 'endereco=' em vez de 'logradouro=' no modelo Endereco,
    lançando ValidationError; e os regexes do tomador exigiam quebra de linha
    literal entre rótulos que, no PDF real, ficam todos na mesma linha)."""
    extractor = _novo_extractor(REAL_MOCK_TEXT, "dummy_localiza_full.pdf")
    try:
        extractor.layout = extractor._detect_layout()
        assert extractor.layout == LAYOUT_LOCALIZA

        nfse = extractor.parse()

        assert nfse.numero == "216421"
        assert nfse.data_emissao.day == 22
        assert nfse.data_emissao.month == 5
        assert nfse.data_emissao.year == 2026
        # Fatura de aluguel de carro, não NFS-e — não há código de autenticidade
        # real a extrair; mantemos apenas o placeholder padrão.
        assert nfse.codigo_verificacao == "FATURA"

        assert nfse.prestador.razao_social == "LOCALIZA RENT A CAR S/A"
        assert nfse.prestador.cnpj_cpf == "16670085091444"
        assert nfse.prestador.endereco.municipio == "SALVADOR"
        assert nfse.prestador.endereco.uf == "BA"

        assert nfse.tomador.razao_social == "TEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDA"
        assert nfse.tomador.cnpj_cpf == "07345543000190"
        assert nfse.tomador.endereco.logradouro == "RUA TERRITORIO DO AMAPA"
        assert nfse.tomador.endereco.bairro == "PITUBA"
        assert nfse.tomador.endereco.municipio == "SALVADOR"
        assert nfse.tomador.endereco.uf == "BA"
        assert nfse.tomador.endereco.cep == "41830540"

        assert nfse.valores.valor_servicos == pytest.approx(6180.72)
        assert nfse.valores.valor_liquido_nfse == pytest.approx(6180.72)

        assert nfse.avisos == []
    finally:
        _limpar("dummy_localiza_full.pdf")


# Texto real de outra fatura Localiza ("LOCALIZA MARIANA 15.06.pdf"), emitida
# pela agência de FEIRA DE SANTANA (em vez de Salvador/Cabula). O cabeçalho
# contém literalmente o texto "FEIRA DE SANTANA", que era verificado (e
# casava) ANTES da verificação do layout Localiza em _detect_layout/
# _detect_layout_page — fazendo o documento ser detectado como o layout
# municipal de Feira de Santana em vez de Localiza, e prestador/tomador
# saírem como "Não Identificado".
REAL_MOCK_TEXT_FEIRA_DE_SANTANA_AGENCY = (
    "LOCALIZA RENT A CAR S/A AG CENTRO FEIRA DE SANTANA R MARIA QUITÉRIA, 1197 - "
    "BRASILIA44088-000 - FEIRA DE SANTANA - BA CNPJ - 16.670.085/0893-85 "
    "ASSISTÊNCIA A CLIENTES TEL 0800 979 2020 assistenciaaclientes@localiza.com   "
    "FATURA / DUPLICATANº: ACFSA - 237512CLIENTE: TEMIS PROJETOS DE MEIO AMBIENTE E "
    "SUSTENTABILIDADELTDA ENDEREÇO: RUA TERRITORIO DO AMAPA, 146 CS 2 - PITUBA "
    "CEP/CID/UF: 41830-540 - SALVADOR - BA CNPJ:  07.345.543/0001-90 "
    "CÓDIGO: 02640209 INSC. ESTADUAL:  069725483  DATA DE EMISSÃO: 01/06/2026  "
    "DESCRIÇÃO VALOR ALUGUEL CONFORME CONTRATO     FSAF116902  R$ 848,10 "
    "VALOR DO SEGURO R$ 53,85           "
    "VENCIMENTOCONDIÇÕES DE PAGAMENTOVALOR TOTAL16/06/2026 A PRAZO R$ 901,95 "
    "Não contribuinte de ISS s/locação cfe. LC n. 116/03        "
    "Sacador: Aceite:  Valor da faturaValor da faturaR$ 901,95"
    "Data de Vencimento16/06/2026 "
    "CNPJ/CPF do beneficiário 16.670.085/0001-55 "
    "Data do documento 01/06/2026"
)


def test_localiza_agencia_feira_de_santana_nao_detecta_layout_municipal():
    """Regressão: a agência da Localiza em Feira de Santana faz o cabeçalho da
    fatura conter o texto "FEIRA DE SANTANA", que colidia com a detecção do
    layout municipal LAYOUT_FEIRA (verificado antes de LAYOUT_LOCALIZA). O
    resultado era prestador e tomador "Não Identificado" e todos os valores
    zerados, mesmo com "LOCALIZA RENT A CAR S/A" presente no texto."""
    extractor = _novo_extractor(REAL_MOCK_TEXT_FEIRA_DE_SANTANA_AGENCY, "dummy_localiza_feira.pdf")
    try:
        extractor.layout = extractor._detect_layout()
        assert extractor.layout == LAYOUT_LOCALIZA

        nfse = extractor.parse()

        assert nfse.numero == "237512"
        assert nfse.data_emissao.day == 1
        assert nfse.data_emissao.month == 6
        assert nfse.data_emissao.year == 2026

        assert nfse.tomador.razao_social == "TEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDA"
        assert nfse.tomador.cnpj_cpf == "07345543000190"
        assert nfse.tomador.endereco.municipio == "SALVADOR"
        assert nfse.tomador.endereco.cep == "41830540"

        assert nfse.valores.valor_servicos == pytest.approx(901.95)
        assert nfse.avisos == []
    finally:
        _limpar("dummy_localiza_feira.pdf")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
