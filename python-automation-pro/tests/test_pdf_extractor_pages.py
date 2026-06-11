import pytest
from unittest.mock import patch
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_CUIABA, LAYOUT_BARREIRAS, LAYOUT_GENERICO

def test_detect_layout_page():
    ext = SPPdfExtractor('dummy.pdf')
    
    # Valid layout (Cuiaba)
    page_cuiaba = "Prefeitura Municipal de Cuiabá\nISSNet\nAlgum texto da nota"
    assert ext._detect_layout_page(page_cuiaba) == LAYOUT_CUIABA
    
    # Valid layout (Barreiras)
    page_barreiras = "Prefeitura de Barreiras\nData Fato Gerador: 10/10/2023"
    assert ext._detect_layout_page(page_barreiras) == LAYOUT_BARREIRAS
    
    # Invalid/Generic layout (random text)
    page_random = "Comprovante de pagamento\nValor: R$ 100,00"
    assert ext._detect_layout_page(page_random) == LAYOUT_GENERICO

@patch('src.extractors.pdf_extractor.extract_text')
def test_extract_raw_text_filters_trash_and_generic(mock_extract_text):
    # Simulate a PDF with 3 pages:
    # Page 1: A valid NFS-e page (Cuiaba)
    # Page 2: A page matching TRASH_PATTERN (e.g. Recibo de Transferência)
    # Page 3: A generic page that doesn't match any layout (e.g. pure junk)
    
    page1 = "Prefeitura Municipal de Cuiabá\nISSNet\nNota 12345"
    page2 = "Banco XYZ\nRecibo de Transferência Bancária\nValor: 50,00"
    page3 = "Apenas um texto qualquer sem layout conhecido"
    
    # \x0c is the page separator used by pdfminer
    mock_extract_text.return_value = f"{page1}\x0c{page2}\x0c{page3}"
    
    ext = SPPdfExtractor('dummy.pdf')
    result = ext.extract_raw_text()
    
    # Only page1 should survive the filtering
    assert page1 in result
    assert page2 not in result
    assert page3 not in result
    assert result == page1.strip()

@patch('src.extractors.pdf_extractor.extract_text')
def test_extract_raw_text_multiple_valid_pages(mock_extract_text):
    # Simulate a PDF with 2 valid NFS-e pages
    page1 = "Prefeitura Municipal de Cuiabá\nISSNet\nNota 1"
    page2 = "Prefeitura Municipal de Cuiabá\nISSNet\nNota 2"
    
    mock_extract_text.return_value = f"{page1}\x0c{page2}"
    
    ext = SPPdfExtractor('dummy.pdf')
    result = ext.extract_raw_text()
    
    # Both pages should survive and be joined by \n\x0c\n
    assert page1 in result
    assert page2 in result
    assert "\x0c" in result
