import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
from src.models.nfse_models import Nfse
import os

def test_extract_cuiaba_layout():
    # Mock de texto extraído do layout de Cuiabá/MT
    mock_text = """
    Prefeitura Municipal de Cuiabá
    Secretaria Municipal de Economia
    Nota Fiscal de Serviço Eletrônica - NFS-e
    Número da Nota Fiscal: 205
    Data de Geração da NFS-e: 01/04/2026 17:20:05
    Data de Competência: 01/04/2026
    Cód. de Autenticidade: 09303F3E7
    
    Dados do Prestador de Serviço
    RC CONSTRUCOES ELETRICAS LTDA
    CPF/CNPJ: 17.196.107/0001-50
    
    Dados do Tomador de Serviços
    CNPJ/CPF : 03.051.741/0001-90
    Razão Social : Sao Pedro Construtora Ltda
    
    Detalhamento dos Tributos
    Vl. Total dos Serviços: R$ 17.955,00
    Deduções Base Cálculo: R$ 10.773,00
    Base de Cálculo: R$ 7.182,00
    Alíquota: 4,60
    Total do ISSQN: R$ 330,37
    ISSQN Retido: Não
    Vl. Líquido da Nota Fiscal: R$ 17.955,00
    """
    
    dummy_path = "tests/dummy_cuiaba.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f: f.write(b"%PDF-1.4")
        
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = mock_text
    extractor.layout = extractor._detect_layout()
    
    nfse = extractor.parse()
    
    assert nfse.numero == "205"
    assert nfse.codigo_verificacao == "09303F3E7"
    assert nfse.valores.valor_servicos == pytest.approx(17955.00)
    assert nfse.valores.valor_deducoes == pytest.approx(10773.00)
    assert nfse.valores.base_calculo == pytest.approx(7182.00)
    assert nfse.valores.aliquota == pytest.approx(0.046)
    assert nfse.valores.valor_iss == pytest.approx(330.37)
    assert nfse.valores.valor_liquido_nfse == pytest.approx(17955.00)
    assert nfse.valores.iss_retido is False
    
    if os.path.exists(dummy_path): os.remove(dummy_path)

if __name__ == "__main__":
    pytest.main([__file__])
