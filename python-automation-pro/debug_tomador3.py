import re
from src.extractors.pdf_extractor import SPPdfExtractor
import glob

f = glob.glob(r'L:\USUARIOS\ANDERSON\ARQUIVOS DESKTOP\Notas\052026\*BARBARA TREINAMENTO*.pdf')[0]
ext = SPPdfExtractor(f)
t = ext.extract_raw_text()

def relax(p): return "".join([re.escape(c) + r"\s*" for c in p]) if p else p

labels = sorted(['Tomador', 'Dados do Tomador', 'Identificação do Tomador', 'Tomador do Serviço', 'Dados do Cliente', 'TOMADOR DO SERVIÇO', 'TOMADOR DE SERVIÇOS', 'Tomador de Serviço', 'Dados do Tomador de Serviço', 'Tomador de Serviços', 'Cliente'], key=len, reverse=True)
other_labels = ['Prestador', 'Emitente', 'Dados do Prestador', 'Dados do Emitente', 'Identificação do Prestador', 'Prestador do Serviço', 'EMITENTE DA NFS-e', 'PRESTADOR DE SERVIÇOS', 'Prestador de Serviço', 'Dados do Prestador de Serviço', 'Prestador de Serviços', 'PRESTADOR DE SERVIÇO', 'Fornecedor']

pattern_labels = "|".join([relax(l) for l in labels])
pattern_other_labels = "|".join([relax(l) for l in other_labels])

delimiters = rf'{pattern_other_labels}|{relax("Discrimina")}|{relax("VALOR TOTAL")}|{relax("DADOS COMPLEMENTARES")}|{relax("OUTRAS INFORMAÇÕES")}|$'

pattern_bloco = rf'(?:{pattern_labels}).*?(?={delimiters})'
m_bloco = re.search(pattern_bloco, t, re.IGNORECASE | re.DOTALL)
print("Bloco Tomador:")
print(m_bloco.group(0) if m_bloco else "None")
