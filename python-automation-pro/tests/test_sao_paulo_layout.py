import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_SAO_PAULO
import os


def test_detect_sao_paulo_layout():
    """Testa a detecção correta do layout São Paulo/SP"""
    mock_text = """
    PREFEITURA DO MUNICÍPIO DE SÃO PAULO
    NOTA FISCAL DE SERVIÇOS ELETRÔNICA - NFS-e
    """

    dummy_path = "tests/dummy_sao_paulo.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = mock_text
    layout = extractor._detect_layout()

    assert layout == LAYOUT_SAO_PAULO, f"Expected {LAYOUT_SAO_PAULO}, got {layout}"

    if os.path.exists(dummy_path):
        os.remove(dummy_path)


def test_extract_sao_paulo_numero():
    """O número da nota do layout São Paulo usa o rótulo 'Número da Nota'"""
    mock_text = """
    PREFEITURA DO MUNICÍPIO DE SÃO PAULO
    Número da Nota: 7788
    """

    dummy_path = "tests/dummy_sao_paulo_num.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = mock_text
    extractor.layout = LAYOUT_SAO_PAULO

    assert extractor._extrair_numero() == "7788"

    if os.path.exists(dummy_path):
        os.remove(dummy_path)


def test_extract_sao_paulo_competencia():
    """A competência do layout São Paulo usa o rótulo 'Compe:' em formato mês/ano (ex: Jan/2026)"""
    mock_text = """
    PREFEITURA DO MUNICÍPIO DE SÃO PAULO
    Compe: Jan/2026
    Data de Emissão: 15/03/2026 10:00:00
    """

    dummy_path = "tests/dummy_sao_paulo_comp.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = mock_text
    extractor.layout = LAYOUT_SAO_PAULO

    data_emissao = extractor._extrair_data_emissao()
    competencia = extractor._extrair_competencia(data_emissao)

    # "Compe: Jan/2026" deve resultar em competência de Janeiro/2026,
    # independentemente do mês da Data de Emissão (Março).
    assert competencia.month == 1
    assert competencia.year == 2026

    if os.path.exists(dummy_path):
        os.remove(dummy_path)


def test_extract_sao_paulo_full_nfse():
    """Testa extração completa de uma NFS-e no layout São Paulo/SP"""
    mock_text = """
    PREFEITURA DO MUNICÍPIO DE SÃO PAULO
    NOTA FISCAL DE SERVIÇOS ELETRÔNICA - NFS-e
    Número da Nota: 7788
    Compe: Jan/2026
    Data de Emissão: 15/03/2026 10:00:00
    Código de Verificação: SP998877

    Dados do Prestador de Serviços
    CONSTRUTORA SP LTDA
    CPF/CNPJ: 11.222.333/0001-81

    Dados do Tomador de Serviços
    CNPJ/CPF: 55.666.777/0001-81
    Razão Social: CLIENTE SP LTDA

    Discriminação dos Serviços
    Vl. Total dos Serviços: R$ 12.000,00
    Base de Cálculo: R$ 12.000,00
    Alíquota: 5,00
    Total do ISSQN: R$ 600,00
    Vl. Líquido da Nota Fiscal: R$ 12.000,00
    """

    dummy_path = "tests/dummy_sao_paulo_full.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = mock_text
    extractor.layout = extractor._detect_layout()

    assert extractor.layout == LAYOUT_SAO_PAULO

    nfse = extractor.parse()

    assert nfse.numero == "7788"
    assert nfse.codigo_verificacao == "SP998877"
    assert nfse.prestador.cnpj_cpf == "11222333000181"
    assert nfse.tomador.cnpj_cpf == "55666777000181"
    assert nfse.valores.valor_servicos == pytest.approx(12000.00)
    assert nfse.valores.base_calculo == pytest.approx(12000.00)
    assert nfse.valores.aliquota == pytest.approx(0.05)
    assert nfse.valores.valor_iss == pytest.approx(600.00)
    assert nfse.valores.valor_liquido_nfse == pytest.approx(12000.00)

    if os.path.exists(dummy_path):
        os.remove(dummy_path)


def test_extract_sao_paulo_valor_com_separador_igual():
    """Regressão: algumas notas de São Paulo usam 'VALOR TOTAL DO SERVIÇO = R$ ...'
    (separador '=' em vez de ':'), rótulo que o padrão genérico não reconhecia."""
    mock_text = """
    PREFEITURA DO MUNICÍPIO DE SÃO PAULO
    Número da Nota: 19867979
    Data de Emissão: 25/06/2026 15:22:06

    DISCRIMINAÇÃO DE SERVIÇOS
    Mensalidade R$ 6.261,18
    TOTAL R$ 6.261,18

    VALOR TOTAL DO SERVIÇO = R$ 6.261,18
    """

    dummy_path = "tests/dummy_sao_paulo_igual.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = mock_text
    extractor.layout = LAYOUT_SAO_PAULO

    valores = extractor._extrair_valores()

    assert valores.valor_servicos == pytest.approx(6261.18)

    if os.path.exists(dummy_path):
        os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
