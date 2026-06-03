import sys
import os
sys.path.append(os.getcwd())

from src.extractors.pdf_extractor import SPPdfExtractor

pdf_path = r"L:\USUARIOS\ANDERSON\ARQUIVOS DESKTOP\Notas\042026\ANALISE DE NFS.pdf"
extractor = SPPdfExtractor(pdf_path)
text = extractor._extract_via_ocr()

with open("scratch/extracted_text.txt", "w", encoding="utf-8") as f:
    f.write(text)

print(f"Texto extraído salvo em scratch/extracted_text.txt")
