import sys
import os
sys.path.append(os.getcwd())

from src.extractors.pdf_extractor import SPPdfExtractor

from unittest.mock import patch

with open("scratch/extracted_text.txt", "r", encoding="utf-8") as f:
    text = f.read()

extractor = SPPdfExtractor("fake.pdf")

with patch('src.extractors.pdf_extractor.extract_text', return_value=text):
    results = extractor.parse_multiple()

print(f"Total de notas extraídas: {len(results)}")
for i, nfse in enumerate(results):
    print(f"Nota {i+1}: Número {nfse.numero}, Prestador: {nfse.prestador.razao_social if nfse.prestador else 'N/A'}, Tomador: {nfse.tomador.razao_social if nfse.tomador else 'N/A'}, Valor: {nfse.valores.valor_servicos if nfse.valores else 0.0}, Competência: {nfse.competencia.strftime('%d/%m/%Y') if nfse.competencia else 'N/A'}")

