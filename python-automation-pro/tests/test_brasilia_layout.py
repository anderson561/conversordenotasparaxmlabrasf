import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_BRASILIA
from src.models.nfse_models import Nfse
import os

def test_detect_brasilia_layout():
    """Testa a detecção correta do layout Brasília/DF"""
    mock_text = """
    Governo do Distrito Federal
    Secretária de Estado de Economia do Distrito Federal
    Coordenação do ISS
    Nota Fiscal de Serviço Eletrônica - NFS-e
    """
    
    dummy_path = "tests/dummy_brasilia.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = mock_text
    layout = extractor._detect_layout()
    
    assert layout == LAYOUT_BRASILIA, f"Expected {LAYOUT_BRASILIA}, got {layout}"
    
    if os.path.exists(dummy_path):
        os.remove(dummy_path)


def test_extract_brasilia_codigo_autenticidade():
    """
    Testa a extração do Código de Autenticidade no layout Brasília/DF
    Baseado na NFS-e real do GDF fornecida
    """
    mock_text = """
    Governo do Distrito Federal
    Secretária de Estado de Economia do Distrito Federal
    Coordenação do ISS
    
    Data de Geração de NFS-e: 21/05/2026 22:53:10
    Data de Competência: 21/05/2026
    Código de Autenticidade: 5300010812249298570001590000000001182260517794 14799
    
    Dados do Prestador
    RC CONSTRUCOES ELETRICAS LTDA
    CNPJ/CPF: 24.929.857/0001-59
    
    Dados do Tomador
    SINAL CONSTRUTORA LTDA
    CNPJ/CPF: 33.811.381/0001-48
    
    Detalhamento
    Valor Total Serviços: R$ 27.796,65
    Base de Cálculo: R$ 27.796,65
    Alíquota: 5,00%
    Total ISS: R$ 1.389,83
    Valor Líquido: R$ 27.796,65
    """
    
    dummy_path = "tests/dummy_brasilia_auth.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = mock_text
    extractor.layout = LAYOUT_BRASILIA
    
    # Testa extração do código de autenticidade
    codigo = extractor._extrair_codigo_autenticidade_brasilia()
    
    # Remove espaços e caracteres especiais do código esperado
    expected_code = "530001081224929857000159000000000118226051779414799"
    
    assert codigo == expected_code, f"Expected {expected_code}, got {codigo}"
    assert len(codigo) >= 20, f"Código deve ter pelo menos 20 dígitos, got {len(codigo)}"
    
    if os.path.exists(dummy_path):
        os.remove(dummy_path)


def test_extract_brasilia_full_nfse():
    """
    Testa extração completa de uma NFS-e no layout Brasília/DF
    """
    mock_text = """
    Governo do Distrito Federal
    Secretária de Estado de Economia do Distrito Federal
    Coordenação do ISS
    
    Nota Fiscal de Serviço Eletrônica - NFS-e
    Número da Nota: 1162
    Data de Geração: 21/05/2026 22:53:10
    Data de Competência: 21/05/2026
    Código de Autenticidade: 5300010812249298570001590000000001182260517794 14799
    
    IDENTIFICAÇÃO DO PRESTADOR
    CNPJ: 24.929.857/0001-59
    Nome: MENNDEL & MELO ADVOCACIA
    Inscrição Municipal: 0771119001 00
    Telefone: (61)9649-6252
    CEP: 71655-040
    
    IDENTIFICAÇÃO DO TOMADOR
    CNPJ: 33.811.381/0001-48
    Nome: SINAL CONSTRUTORA LTDA
    Inscrição Municipal: -
    Telefone: (71)3273-2450
    CEP: 48120-000
    
    DADOS DO SERVIÇO PRESTADO
    Código: 17.14.01
    Descrição: Advocacia
    Valor Serviço: R$ 27.796,65
    
    IMPOSTOS
    Base Cálculo: R$ 27.796,65
    Alíquota ISS: 5,00%
    Valor ISS: R$ 1.389,83
    Valor Deduções: R$ 0,00
    Valor Líquido: R$ 27.796,65
    """
    
    dummy_path = "tests/dummy_brasilia_full.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = mock_text
    extractor.layout = extractor._detect_layout()
    
    assert extractor.layout == LAYOUT_BRASILIA
    
    nfse = extractor.parse()
    
    # Validações gerais
    assert nfse.numero == "1162"
    assert nfse.codigo_verificacao == "530001081224929857000159000000000001182260517794 14799"
    assert nfse.prestador.cnpj_cpf == "24929857000159"
    assert nfse.tomador.cnpj_cpf == "33811381000148"
    assert nfse.valores.valor_servicos == pytest.approx(27796.65)
    assert nfse.valores.base_calculo == pytest.approx(27796.65)
    assert nfse.valores.aliquota == pytest.approx(0.05)
    assert nfse.valores.valor_iss == pytest.approx(1389.83)
    assert nfse.valores.valor_liquido_nfse == pytest.approx(27796.65)
    
    if os.path.exists(dummy_path):
        os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
