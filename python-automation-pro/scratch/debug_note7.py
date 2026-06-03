import sys
import os
sys.path.append(os.getcwd())

from src.extractors.pdf_extractor import SPPdfExtractor
from unittest.mock import patch

with open("scratch/extracted_text.txt", "r", encoding="utf-8") as f:
    text = f.read()

extractor = SPPdfExtractor("fake.pdf")

with patch('src.extractors.pdf_extractor.extract_text', return_value=text):
    pages = text.split('\x0c')
    page6 = pages[5] # 6th page (0-indexed 5)
    print("=== PAGE 6 ORIGINAL ===")
    print(page6)
    print("=======================")
    
    # Process Page 6 split
    parts = page6.split('\n')
    sub_ext = SPPdfExtractor("fake.pdf")
    results = extractor.parse_multiple()
    for i, nfse in enumerate(results):
        if nfse.numero in ('168279', '529065321'):
            print(f"\n--- EXTRACTED NOTE {nfse.numero} ---")
            print(f"Prestador: {nfse.prestador.razao_social if nfse.prestador else 'N/A'}")
            print(f"Tomador: {nfse.tomador.razao_social if nfse.tomador else 'N/A'}")
            print(f"Valor: {nfse.valores.valor_servicos if nfse.valores else 0.0}")
            print(f"Competência: {nfse.competencia}")
