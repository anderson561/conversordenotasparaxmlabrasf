import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
from src.models.nfse_models import Nfse
import os

def test_extract_barreiras_fields():
    # Simula duas páginas (notas diferentes)
    mock_text = """
    MUNICIPIO DE BARREIRAS
    Nº da Nota Fiscal : 23
    Emitido em 29/04/2026 10:31:06
    VALOR SERVIÇO (R$)
    16.473,00
    CNPJ: 26.791.663/0001-65
    \x0c
    MUNICIPIO DE BARREIRAS
    Nº da Nota Fiscal : 24
    CNPJ: 26.791.663/0001-65
    VALOR TOTAL DA NOTA = R$ 2.000,00
    """
    
    dummy_path = "tests/dummy_barreiras_multi.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f: f.write(b"%PDF-1.4")
        
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = mock_text
    
    # Mockando o extract_text interno
    import src.extractors.pdf_extractor as pdf_ext
    original_extract = pdf_ext.extract_text
    pdf_ext.extract_text = lambda path: mock_text
    
    try:
        # Teste 1: Duas notas diferentes (uma com VALOR SERVIÇO na linha seguinte)
        invoices = extractor.parse_multiple()
        assert len(invoices) == 2
        assert invoices[0].numero == "23"
        assert invoices[0].data_emissao.day == 29
        assert invoices[0].data_emissao.month == 4
        assert invoices[0].data_emissao.year == 2026
        assert invoices[0].valores.valor_servicos == 16473.00
        assert invoices[1].numero == "24"
        assert invoices[1].valores.valor_servicos == 2000.00
        
        # Teste 2: Mesma nota em duas páginas (agrupamento)
        mock_merge = """
        MUNICIPIO DE BARREIRAS
        Nº da Nota Fiscal : 50
        CNPJ: 12.345.678/0001-00
        VALOR TOTAL DA NOTA = R$ 5.000,00
        \x0c
        MUNICIPIO DE BARREIRAS
        Nº da Nota Fiscal : 50
        DISCRIMINAÇÃO: Continuação do serviço...
        """
        pdf_ext.extract_text = lambda path: mock_merge
        invoices_merge = extractor.parse_multiple()
        
        assert len(invoices_merge) == 1
        assert invoices_merge[0].numero == "50"
    finally:
        pdf_ext.extract_text = original_extract
        if os.path.exists(dummy_path): os.remove(dummy_path)

if __name__ == "__main__":
    pytest.main([__file__])
