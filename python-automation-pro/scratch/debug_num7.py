import sys
import os
import re
sys.path.append(os.getcwd())

from src.extractors.pdf_extractor import SPPdfExtractor

# The exact text of note 7 block
text_block = """
a] Prefeitura Municipal de Cuiabá

Dados do Prestador de Serviço

Data de Geração da NFS-e
06/04/2026 18:57:39

HISMET-HIGIENE SEGURANÇA E MEDICINA DO TRABALHO LT Dois do Gompalâncio

HISMET

Avenida General Melo,227 TERREO - Campo Velho dE 104/2026
CEP 78065-290 - Fone: (6)5321-7051 - Cuiabá! MT (Cd de putenicidado
administrativoQhismet.com.br 31CD08391

Inscrição Municipal 44441 - CPF/CNPJ 36.894.418/0001-37 Responsável pela Retenção

Identificação da Nota Fiscal Eletrônica
Número do RPS

161920

Data de Emissão do RPS q
06/04/2026

Natureza da Operação Série do RPS
Exigível
Local dos Serviços

Cuiabá - Mato Grosso

Município Incidência
Cuiabá - Mato Grosso

Dados do Tomador de Serviços

CNPJICPF : 03.051.741/0001-90 IM: 1492591
Razão Social: SAO PEDRO CONSTRUTORA LTDA

Endereço : AVPROF MAGALHAES NETO Número: O
Complemento: QUADRA 28 LOTE 09 Bairro : PITUBA
CEP: 41810-011 Cidade/UF : Salvador/ BA
Telefone : E-mail :

Dados do Intermediário de Serviços
CNPJICPF Inscrição Municipal Razão Social

Descrição dos Serviços

Fatura n.º :68319 Valor R$ 1.170,00 Vencimento:15/04/2026 -
3-EXAME CLINICO/3-HEMOGRAMA COM CONTAGEM DE PLAQUETAS/3;GLICEMIA DE JEJUM;
SANGUINEA ABO E FATOR RH/3-EEG - ELETROENCEFALOGRAMA/3;ACUIDADE VISUAL/S-
ESPIROMETRIA/3-AVALIACAO PSICOSSOCIAL

- thra

MATRIA TONAL/3-TIPAGEM
RAMA/3-

Thiago Guedes São Pedro Construtora
Eng. Civil Obra MTi
CREA-BA 052233594-2 Sienge 2) 5 9

Detalhamento dos Tributos
Atividade do Município Alíquota | Item da LC 116/2003 | Cód. NBS Cód. CNAE
8630502 - [8630-5/02] Atividade médica ambulatorial com rec... |3,00 | 403 123012100 | 8630599
Vi. Total dos Serviços | Desconto Incondicionado | Deduções Base Cálculo | Base de Cálculo TotaldoISSON | [ISSQN Retido | Desconto Condicionado

R$ 1.170,00 R$ 0,00 R$ 0,00 R$ 1.170,00 R$ 35,10 | Não R$ 0,00
PIS COFINS INSS IRRF CSLL Outras Retenções MI. ISSQN Retido | VI. Líquido da Nota Fiscal

R$ 7,60 | R$ 35,10 R$ 0,00 | R$ 17,55 | R$ 11,70 R$ 0,00 R$ 0,00 R$ 1.098,05

Construção Civil [ Cód. Obra: | Art.:

Informações Adicionais
PROCON Municipal Cuiabá - Endereço: R. Joaquim Murtinho, 554 - Centro, Cuiabá - MT, 78020-290
Telefone: (65) 3632-6400

PROCON Estadual - MT - Endereço: Av. Gen. Ramiro de Noronha, 294 - 1º andar - Jardim Cuiaba, Cuiabá - MT, 78
043-180
Telefone: (65) 3613-2100/151

Chave de acesso no Ambiente de Dados Nacional: 510340312368944180001370000000168279260417755018
50.
"""

ext = SPPdfExtractor("fake.pdf")
ext.raw_text = text_block
ext.layout = ext._detect_layout()

print("Detected layout:", ext.layout)

# Trace _extrair_numero
t = ext.raw_text

# 1. Label patterns
label_patterns = [
    r'N[uú]mero\s+da\s+NFS-e', 
    r'N[uú]mero\s+da\s+Nota\s+Fiscal', 
    r'N[ºo]\s+da\s+Nota\s+Fiscal',
    r'N[uú]mero\s+da\s+Nota'
]
for lp in label_patterns:
    m_lab = re.search(lp, t, re.IGNORECASE)
    if m_lab:
        pos = m_lab.end()
        pos_end = min(pos + 100, len(t))
        m_prox = re.search(r'(\d+)', t[pos:pos_end])
        if m_prox:
            print("Matched label:", lp, "Value:", m_prox.group(1))

# 2. Chave de acesso
chave_pura = re.sub(r'\D', '', t)
m_chave = re.search(r'(\d{44,50})', chave_pura)
if m_chave:
    chave = m_chave.group(1)
    print("Found chave:", chave, "Length:", len(chave))
    if len(chave) == 44:
        n_nf = chave[25:34].lstrip('0')
        print("Chave 44 ->", n_nf)
    elif len(chave) >= 50:
        n_nf = chave[28:37].lstrip('0')
        print("Chave >= 50 ->", n_nf)

# 3. Traditional patterns
patterns = [
    r'N[uú]mero\s+da\s+Nota\s+Fiscal\s*[:\s\n]*(\d+)',
    r'N[ºo]\s+da\s+Nota\s+Fiscal\s*[:\s\n]*(\d+)',
    r'N[uú]mero\s+da\s+NFS-e\s*[:\s\n]*(\d+)',
    r'N[uú]mero\s+da\s+Nota\s*[:\s\n]*(\d+)',
    r'N[uú]mero[:\s]+(\d+)',
    r'NFS-e\s*n[uú]mero[:\s]+(\d+)',
    r'NFS-e\s*[:\s\n]*(\d+)',
    r'N[ºo]\s*[:\s\n]*(\d+)',
    r'Nota\s*n[ºo]\s*[:\s\n]*(\d+)',
]
for p in patterns:
    m = re.search(p, t, re.IGNORECASE)
    if m:
        print("Matched traditional pattern:", p, "Value:", m.group(1))
