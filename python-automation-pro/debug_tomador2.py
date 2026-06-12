from src.extractors.pdf_extractor import SPPdfExtractor
import glob
f = glob.glob(r'L:\USUARIOS\ANDERSON\ARQUIVOS DESKTOP\Notas\052026\*BARBARA TREINAMENTO*.pdf')[0]
ext = SPPdfExtractor(f)
text = ext.extract_raw_text()
ext.raw_text = text
print(ext._extrair_entidade("Tomador"))
