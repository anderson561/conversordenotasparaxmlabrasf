import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_CAMACARI
import os


def test_detect_camacari_layout():
    """Testa a detecção correta do layout Camaçari/BA (CPqD)"""
    mock_text = """
    CPqD - Gestão Pública
    Prefeitura Municipal de Camaçari
    Nota Fiscal de Serviço Eletrônica - NFS-e
    """

    dummy_path = "tests/dummy_camacari.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = mock_text
    layout = extractor._detect_layout()

    assert layout == LAYOUT_CAMACARI, f"Expected {LAYOUT_CAMACARI}, got {layout}"

    if os.path.exists(dummy_path):
        os.remove(dummy_path)


def test_extract_camacari_competencia():
    """A competência do layout Camaçari usa o rótulo 'Data da prestação do serviço'"""
    mock_text = """
    CPqD - Gestão Pública
    Prefeitura Municipal de Camaçari
    Data da prestação do serviço: 12/03/2026
    Data de Emissão: 12/03/2026 09:15:00
    """

    dummy_path = "tests/dummy_camacari_comp.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = mock_text
    extractor.layout = LAYOUT_CAMACARI

    data_emissao = extractor._extrair_data_emissao()
    competencia = extractor._extrair_competencia(data_emissao)

    assert competencia.day == 12
    assert competencia.month == 3
    assert competencia.year == 2026

    if os.path.exists(dummy_path):
        os.remove(dummy_path)


def test_extract_camacari_full_nfse():
    """Testa extração completa de uma NFS-e no layout Camaçari/BA"""
    mock_text = """
    CPqD - Gestão Pública
    Prefeitura Municipal de Camaçari
    Nota Fiscal de Serviço Eletrônica - NFS-e
    Número da Nota Fiscal: 4521
    Data da prestação do serviço: 12/03/2026
    Data de Emissão: 12/03/2026 09:15:00
    Código de Verificação: A1B2C3D4

    Dados do Prestador de Serviço
    CONSTRUTORA CAMACARI LTDA
    CPF/CNPJ: 12.345.678/0001-95

    Dados do Tomador de Serviços
    CNPJ/CPF: 98.765.432/0001-98
    Razão Social: EMPRESA TOMADORA LTDA

    DISCRIMINAÇÃO DOS SERVIÇOS
    DESCRIÇÃO QTD VALOR UNIT (R$) VALOR TOTAL (R$)
    SERVIÇOS DE CONSULTORIA 1,0000 8.500,00 8.500,00

    Retenções (R$) Totais (R$)
    PIS: 0,00 | Valor dos Serviços (R$) 8.500,00
    COFINS: 0,00 | Deduções (-) 0,00
    INSS: 0,00 | Base de Cálculo (=) 8.500,00
    IR: 0,00 |Aliquota (%) 3,00
    CSLL: 0,00 |Valor do ISS (R$) 255,00
    Outras: 0,00 |Valor Líquido da Nota (=) 8.500,00
    """

    dummy_path = "tests/dummy_camacari_full.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = mock_text
    extractor.layout = extractor._detect_layout()

    assert extractor.layout == LAYOUT_CAMACARI

    nfse = extractor.parse()

    assert nfse.numero == "4521"
    assert nfse.codigo_verificacao == "A1B2C3D4"
    assert nfse.prestador.cnpj_cpf == "12345678000195"
    assert nfse.tomador.cnpj_cpf == "98765432000198"
    assert nfse.valores.valor_servicos == pytest.approx(8500.00)
    assert nfse.valores.base_calculo == pytest.approx(8500.00)
    assert nfse.valores.aliquota == pytest.approx(0.03)
    assert nfse.valores.valor_iss == pytest.approx(255.00)
    assert nfse.valores.valor_liquido_nfse == pytest.approx(8500.00)

    if os.path.exists(dummy_path):
        os.remove(dummy_path)


def test_extract_camacari_valores_ocr_sem_pontuacao():
    """Regressão: o OCR do layout Camaçari costuma ler corretamente rótulos
    como 'Aliquota (%)', mas perde a pontuação (separador de milhar/decimal)
    dos valores na coluna 'Totais (R$)' (ex: "5.115,41" vira "511541").
    O extrator deve reconhecer esse padrão e tratar os 2 últimos dígitos
    como centavos, em vez de ler o número como se já estivesse em reais
    inteiros (o que gerava valores 100x maiores que o real)."""
    mock_text = """
    PREFEITURA MUNICIPAL DE CAMAÇARI
    CPqD - Gestão Pública
    Nota Fiscal de Serviço Eletrônica - NFS-e
    Número da Nota
    281
    Código de autenticidade
    OT34HJBZW

    PRESTADOR DE SERVIÇOS
    Nome/Razão Social: AVANÇO GESTÃO E ADMINISTRAÇÃO LTDA
    CPF/CNPJ: 59.132.742/0001-13

    TOMADOR DE SERVIÇOS
    Nome/Razão Social: PH GESTAO E CONSULTORIA S A
    CPF/CNPJ: 25.311.856/0001-09

    DISCRIMINAÇÃO DOS SERVIÇOS
    DESCRIÇÃO QTD VALOR UNIT (R$) VALOR TOTAL (R$)
    TAXA DE SERVIÇOS COMBINADOS 2,0000 5.115,41 5.115,41

    Retenções (R$) Totais (R$)
    PIS: 0,00 | Valor dos Serviços (R$) 511541
    COFINS: 0,00 | Deduções (-) 0,00
    INSS: 0,00 | Base de Cálculo (=) 511541
    IR: 0,00 |Aliquota (%) 5,00
    CSLL: 0,00 |Valor do ISS (R$) 25577
    Outras: 0,00 |Valor Líquido da Nota (=) 511541

    Data da prestação do serviço: 30/06/2026
    """

    dummy_path = "tests/dummy_camacari_ocr.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = mock_text
    extractor.layout = extractor._detect_layout()

    assert extractor.layout == LAYOUT_CAMACARI

    nfse = extractor.parse()

    assert nfse.numero == "281"
    assert nfse.valores.valor_servicos == pytest.approx(5115.41)
    assert nfse.valores.base_calculo == pytest.approx(5115.41)
    assert nfse.valores.aliquota == pytest.approx(0.05)
    assert nfse.valores.valor_iss == pytest.approx(255.77)
    assert nfse.valores.valor_liquido_nfse == pytest.approx(5115.41)

    if os.path.exists(dummy_path):
        os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
