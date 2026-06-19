from src.extractors.pdf_extractor import SPPdfExtractor
ext = SPPdfExtractor(r'L:\USUARIOS\ANDERSON\ARQUIVOS DESKTOP\Notas\062026\NF S - 2026702 - CUIABA.pdf')
try:
    ext.parse_multiple()
except Exception:
    pass
open('cuiaba_ocr.txt', 'w', encoding='utf-8').write(ext.raw_text)
