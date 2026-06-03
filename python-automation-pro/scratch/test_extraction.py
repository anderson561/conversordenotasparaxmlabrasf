import sys
import os
sys.path.append(os.getcwd())

from src.extractors.pdf_extractor import SPPdfExtractor

pdf_path = r"L:\USUARIOS\ANDERSON\ARQUIVOS DESKTOP\Notas\042026\ANALISE DE NFS.pdf"
extractor = SPPdfExtractor(pdf_path)
results = extractor.parse_multiple()

print(f"Total de notas extraídas: {len(results)}")
for i, nfse in enumerate(results):
    print(f"Nota {i+1}: Número {nfse.numero}, Tomador: {nfse.tomador.razao_social}, Valor: {nfse.valores.valor_servicos}")
