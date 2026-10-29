"""Helpers de texto do DACTE OS (CT-e OS, Modelo 67 - `LAYOUT_DACTE_OS`).

Dois geradores de DACTE OS vistos até agora, com templates estruturalmente
diferentes (ver os testes `test_dacte_os_*`):

* "Master CT-e" (www.officesystem.com.br) - notas CIATRANS nº 438 e nº 564:
  razão social em 2 linhas ANTES do "CNPJ: ... IE: ...", endereço DEPOIS;
  municípios de início/término impressos com o código IBGE
  ("2930709 - Simoes Filho"); grade federal "VALOR DO PIS / VALOR COFINS /
  VALOR DO IMPOSTO DE RENDA / VALOR DO INSS / VALOR DO CSLL"; a caixa
  "CLASSIFICAÇÃO TRIBUTÁRIA DO SERVIÇO" (CST) sai EM BRANCO.
* "CT-e Prático" (Bsoft Internetworks) - notas SIGMA nº 17268 e COOPERATIVA
  DE RADIO TAXI DE SIMOES FILHO nº 4035: razão social numa linha, endereço
  ANTES do CNPJ ("<logradouro>, <nº>[, <complemento>] - <bairro>" com quebra
  de linha livre, depois "CEP: <cep>, <MUNICÍPIO> - <UF>"); municípios só por
  nome ("Salvador - BA"); grade federal "INSS / PIS / COFINS / IR / CSLL"
  (ordem DIFERENTE do Master CT-e); CST impresso ("40 - ICMS ISENÇÃO").

Tudo aqui é função pura sobre texto (testável sem PDF nem OCR). Onde a
leitura não fecha, o chamador (`SPPdfExtractor._parse_dacte_os`) registra
aviso em vez de fabricar valor (princípio de integridade fiscal do projeto).
"""

from __future__ import annotations

import re
import unicodedata
from typing import Dict, List, Optional, Tuple

# Valor monetário COMPLETO impresso no DACTE OS ("6.950,87", "0,00",
# "100,00") - nunca casa um número solto de ruído ("7") nem um CST ("40").
_RE_MOEDA = re.compile(r'(?<![\d,.])\d{1,3}(?:\.\d{3})*,\d{2}(?![\d,])')
# Mesmo valor com o ÚLTIMO dígito cortado na margem direita do papel
# ("2.115,0" seguido de lixo de OCR) - achado real, nota SIGMA nº 17268.
_RE_MOEDA_TRUNCADA = re.compile(r'(?<![\d,.])(\d{1,3}(?:\.\d{3})*,\d)(?!\d)')

# Títulos do cabeçalho central que o OCR funde na MESMA linha da razão
# social do emitente ("SIGMA TRANSPORTES LTDA DACTE OS", "PASSAGEIROS LTDA
# Documento Auxiliar do Conhecimento...", "CIATRANS POOL TRANSPORTES DE
# DACTE OS MODAL").
_RE_TITULO_CABECALHO = re.compile(
    r'\s+(?:DACTE\s+OS|CT-?e\s+OS|Documento\s+Auxiliar|MODAL\b|RODOVI[ÁA]RIO\b).*$', re.IGNORECASE)


def sem_acento(s: str) -> str:
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode('ascii')


def moeda(s: str) -> float:
    return float(s.replace('.', '').replace(',', '.'))


def valores_monetarios(linha: str) -> List[float]:
    return [moeda(v) for v in _RE_MOEDA.findall(linha or '')]


def cortar_titulo_cabecalho(linha: str) -> str:
    return _RE_TITULO_CABECALHO.sub('', linha or '').strip()


def _parece_nome(linha: str) -> bool:
    """Linha de razão social: MAIÚSCULAS, maioria letras, sem vírgula de
    endereço nem grupo de 3+ dígitos, sem rótulo de campo."""
    if len(linha) < 4 or linha != linha.upper() or ',' in linha:
        return False
    if re.search(r'\d{3}', linha) or re.match(r'(?:CEP|CNPJ|FONE|IE)\b', linha, re.IGNORECASE):
        return False
    letras = sum(ch.isalpha() for ch in linha)
    return letras >= 0.7 * len(linha.replace(' ', '')) and len(linha.split()) >= 2


def parse_emitente_recorte(texto: str) -> Dict[str, Optional[str]]:
    """Lê o bloco do emitente a partir do RECORTE dedicado da caixa do
    emitente (`_ocr_recut_dacte_os_caixas`, `--psm 6`), que devolve as
    linhas na ordem visual - ao contrário do texto de página inteira, em que
    o endereço do gerador CT-e Prático sai espalhado (achado real, nota
    17268: o bairro "CAMINHO DAS ARVORES" saía ANTES da razão social e o
    complemento DEPOIS do CNPJ). Cobre os dois geradores (ver docstring do
    módulo). Campos não encontrados ficam `None`."""
    r: Dict[str, Optional[str]] = dict.fromkeys(
        ('razao_social', 'cnpj', 'ie', 'logradouro', 'numero', 'complemento',
         'bairro', 'municipio', 'uf', 'cep', 'fone'))
    linhas = [l.strip() for l in (texto or '').split('\n') if l.strip()]
    if not linhas:
        return r

    idx_cnpj = next((i for i, l in enumerate(linhas) if re.search(r'CNPJ\s*:', l, re.IGNORECASE)), None)
    if idx_cnpj is not None:
        lc = linhas[idx_cnpj]
        m = re.search(r'CNPJ\s*:\s*(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}|[\d\s]{14,18}?)(?=\s|\||$)', lc, re.IGNORECASE)
        if m:
            r['cnpj'] = re.sub(r'\D', '', m.group(1))
            m_ie = re.search(r'(\d{6,14})', lc[m.end():])
            r['ie'] = m_ie.group(1) if m_ie else None

    # Razão social: 1ª sequência de linhas "com cara de nome" (pode ocupar 2
    # linhas no Master CT-e), já sem o título do cabeçalho fundido.
    nome: List[str] = []
    fim_nome = None
    for i, l in enumerate(linhas[:idx_cnpj] if idx_cnpj is not None else linhas):
        limpa = cortar_titulo_cabecalho(l)
        if _parece_nome(limpa):
            nome.append(limpa)
            fim_nome = i
        elif nome:
            break
    if nome:
        r['razao_social'] = ' '.join(nome)

    # Endereço - gerador Master CT-e: DEPOIS do CNPJ, em 2 linhas
    # ("<lgr>, <nº> - <compl>" / "<bairro> - <município>/<UF> - CEP: <cep>").
    if idx_cnpj is not None:
        depois = '\n'.join(linhas[idx_cnpj + 1:])
        m = re.search(
            r'^(.+?),\s*(\d+[A-Za-z]?)\s*-\s*(.+?)\s*\n(.+?)\s*-\s*(.+?)/([A-Z]{2})\s*-\s*CEP:\s*(\d{5})-?(\d{3})',
            depois, re.IGNORECASE | re.MULTILINE)
        if m:
            r.update(logradouro=m.group(1).strip(), numero=m.group(2), complemento=m.group(3).strip(),
                     bairro=m.group(4).strip(), municipio=m.group(5).strip(), uf=m.group(6).upper(),
                     cep=m.group(7) + m.group(8))
            m_f = re.search(r'FONE\s*:\s*([\d()\s-]{6,20})', depois, re.IGNORECASE)
            r['fone'] = re.sub(r'\D', '', m_f.group(1)) if m_f else None
            return r

    # Endereço - gerador CT-e Prático: ENTRE a razão social e o CNPJ.
    inicio = (fim_nome + 1) if fim_nome is not None else 0
    fim = idx_cnpj if idx_cnpj is not None else len(linhas)
    bloco = linhas[inicio:fim]
    idx_cep = next((i for i, l in enumerate(bloco) if re.search(r'\bCEP\s*:', l, re.IGNORECASE)), None)
    if idx_cep is not None:
        m = re.search(r'CEP\s*:\s*(\d{5})-?(\d{3})\s*,\s*(.+?)\s*-\s*([A-Z]{2})\b', bloco[idx_cep], re.IGNORECASE)
        if m:
            r.update(cep=m.group(1) + m.group(2), municipio=m.group(3).strip(), uf=m.group(4).upper())
        end = ' '.join(re.sub(r'^[^A-Za-zÀ-ÿ0-9]+', '', l) for l in bloco[:idx_cep])
        m = re.match(r'(.+?),\s*(\d+[A-Za-z]?|S/?N)\b\s*(?:,\s*(.+)|-\s*(.+))?$', end.strip(), re.IGNORECASE)
        if m:
            r['logradouro'], r['numero'] = m.group(1).strip(), m.group(2)
            if m.group(3):
                resto = m.group(3).strip(' -')
                if ' - ' in resto:
                    r['complemento'], r['bairro'] = (p.strip() for p in resto.rsplit(' - ', 1))
                else:
                    r['complemento'] = resto
            elif m.group(4):
                r['bairro'] = m.group(4).strip(' -')
        m_f = re.search(r'FONE\s*:\s*([\d()\s-]{6,20})', '\n'.join(bloco[idx_cep:]), re.IGNORECASE)
        r['fone'] = re.sub(r'\D', '', m_f.group(1)) if m_f else None
    return r


def parse_rota(texto: str) -> Tuple[Optional[Tuple[Optional[str], str, Optional[str]]],
                                    Optional[Tuple[Optional[str], str, Optional[str]]]]:
    """Municípios de início e término da prestação, como (código IBGE ou
    None, nome, UF ou None).

    Master CT-e: impressos com o código IBGE ("2930709 - Simoes Filho") -
    o rótulo "INÍCIO DA PRESTAÇÃO" pode sair destruído pelo OCR (achado real,
    nota 564: "Ih AÇÃO"), então valem as linhas "<7 dígitos> - <nome>" na
    ordem de leitura (1ª = início, 2ª = término), antes do bloco do tomador.
    CT-e Prático: só o nome, na linha de valores logo abaixo da linha de
    rótulos "INÍCIO DA PRESTAÇÃO PERCURSO DO VEÍCULO TÉRMINO DA PRESTAÇÃO"
    ("Salvador - BA Simoes Filho - BA") - 1º par "<nome> - <UF>" = início,
    último = término."""
    t = texto or ''
    corte = re.search(r'TOMADOR', t, re.IGNORECASE)
    cabeca = t[:corte.start()] if corte else t
    codigos = re.findall(r'(?m)^\s*(\d{7})\s*-\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\' ]*?)\s*$', cabeca)
    if len(codigos) >= 2:
        return (codigos[0][0], codigos[0][1].strip(), None), (codigos[1][0], codigos[1][1].strip(), None)

    m = re.search(r'IN[ÍI]CIO\s+DA\s+PRESTA[ÇC][ÃA]O[^\n]*T[ÉE]RMINO\s+DA\s+PRESTA[ÇC][ÃA]O[^\n]*\n+\s*([^\n]+)',
                  t, re.IGNORECASE)
    if m:
        pares = re.findall(r'([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\' ]*?)\s+-\s+([A-Z]{2})\b', m.group(1))
        if len(pares) >= 2:
            return (None, pares[0][0].strip(), pares[0][1]), (None, pares[-1][0].strip(), pares[-1][1])
    if len(codigos) == 1:
        return (codigos[0][0], codigos[0][1].strip(), None), None
    return None, None


def codigo_tipo_servico(texto: Optional[str]) -> Optional[str]:
    """`ide/tpServ` do leiaute 4.00 a partir do texto impresso em "TIPO DO
    SERVIÇO" (6 = Transporte de Pessoas, 7 = Transporte de Valores, 8 =
    Excesso de Bagagem)."""
    n = sem_acento(texto or '').upper()
    if re.search(r'\bPESSOAS?\b', n):
        return '6'
    if re.search(r'\bVALORES\b', n):
        return '7'
    if re.search(r'\bBAGAGEM\b', n):
        return '8'
    return None


def codigo_modal(texto: str) -> Optional[str]:
    """`ide/modal` (01 rodoviário, 02 aéreo, 03 aquaviário, 04 ferroviário)
    pelo título "MODAL <nome>" / "INFORMAÇÕES ESPECÍFICAS DO MODAL <nome>"."""
    n = sem_acento(texto or '').upper()
    for padrao, codigo in ((r'MODAL\s+RODOVIARIO|^\s*RODOVIARIO\s*$', '01'), (r'MODAL\s+AEREO', '02'),
                           (r'MODAL\s+AQUAVIARIO', '03'), (r'MODAL\s+FERROVIARIO', '04')):
        if re.search(padrao, n, re.MULTILINE):
            return codigo
    return None


def _linha_seguinte_nao_vazia(linhas: List[str], i: int) -> str:
    for l in linhas[i + 1:]:
        if l.strip():
            return l
    return ''


def parse_totais(texto: str) -> Tuple[Optional[str], Optional[str]]:
    """(valor total, valor a receber) como TEXTO bruto - pelo par
    "<total>\\nVALOR A RECEBER\\n<a receber>" (o rótulo "VALOR TOTAL DA
    PRESTAÇÃO DO SERVIÇO" tem o valor deslocado; "À" com crase é leitura
    comum do OCR para o "A" do rótulo). O chamador decide se o valor saiu
    completo ou truncado na margem."""
    m = re.search(r'([\d.,]+)[^\n\d]*\n+\s*VALOR\s+[AÀ]\s+RECEBER\s*\n+\s*([\d.,]+)', texto or '', re.IGNORECASE)
    return (m.group(1), m.group(2)) if m else (None, None)


def valor_completo_ou_truncado(bruto: Optional[str]) -> Tuple[Optional[float], Optional[str]]:
    """(valor, None) se `bruto` é um valor monetário completo; (None,
    prefixo) se saiu com o último dígito cortado ("2.115,0")."""
    if not bruto:
        return None, None
    m = _RE_MOEDA.match(bruto)
    if m and m.group(0) == bruto.rstrip('.'):
        return moeda(m.group(0)), None
    m = _RE_MOEDA_TRUNCADA.match(bruto)
    if m:
        return None, m.group(1)
    return None, None


def completar_truncado(prefixo: str, candidatos: List[float]) -> Optional[float]:
    """Completa um valor com o último dígito cortado SÓ quando exatamente um
    dos `candidatos` (valores que uma identidade do próprio documento torna
    possíveis) começa com o prefixo lido - nunca escolhe um dígito."""
    alvo = prefixo.replace('.', '').replace(',', '.')
    casam = sorted({round(c, 2) for c in candidatos if f"{c:.2f}".startswith(alvo)})
    return casam[0] if len(casam) == 1 else None


def parse_icms(texto: str) -> Optional[Dict[str, object]]:
    """Linha de valores sob o cabeçalho "... BASE DE CÁLCULO AL ICMS (%)
    VALOR ICMS % RED.BC.CÁLC ICMS ST": CST opcional no início ("40 - ICMS
    ISENÇÃO") e exatamente 5 valores (BC, alíquota, ICMS, % redução, ICMS
    ST). Menos/mais de 5 = linha não confiável -> None."""
    linhas = (texto or '').split('\n')
    for i, l in enumerate(linhas):
        if re.search(r'BASE\s+DE\s+C[ÁA]LCULO', l, re.IGNORECASE) and re.search(r'ICMS\s*ST', l, re.IGNORECASE):
            prox = _linha_seguinte_nao_vazia(linhas, i)
            vals = valores_monetarios(prox)
            if len(vals) != 5:
                return None
            m_cst = re.match(r'\s*(\d{2})\s*-', prox)
            cst = m_cst.group(1) if m_cst else None
            if cst is None and re.search(r'SIMPLES\s+NACIONAL', prox, re.IGNORECASE):
                cst = 'SN'
            return {'cst': cst, 'bc': vals[0], 'aliquota': vals[1], 'icms': vals[2],
                    'reducao': vals[3], 'icms_st': vals[4]}
    return None


_NOMES_FEDERAIS = (r'\bPIS\b', r'\bCOFINS\b', r'\bINSS\b', r'\bIR\b|IMPOSTO\s+DE\s+RENDA', r'\bCS[LI1]{2}\b')


def parse_federais(texto: str) -> Optional[Dict[str, float]]:
    """Linha dos 5 tributos federais retidos, sob um cabeçalho com pelo
    menos 3 dos 5 nomes. Ordem das colunas depende do gerador: Master CT-e
    "VALOR DO PIS / COFINS / IMPOSTO DE RENDA / INSS / CSLL"; CT-e Prático
    "INSS / PIS / COFINS / IR / CSLL" (o cabeçalho às vezes perde o "INSS"
    no OCR - achado real 17268 "PIS COFINS IR CsLI" com 5 valores abaixo -,
    por isso a ordem é decidida pela marca "VALOR DO" do Master CT-e, não
    pela posição do "INSS"). Exige exatamente 5 valores."""
    linhas = (texto or '').split('\n')
    for i, l in enumerate(linhas):
        if sum(bool(re.search(p, l, re.IGNORECASE)) for p in _NOMES_FEDERAIS) < 3:
            continue
        vals = valores_monetarios(_linha_seguinte_nao_vazia(linhas, i))
        if len(vals) != 5:
            continue
        if re.search(r'VALOR\s+DO\s+PIS', l, re.IGNORECASE):
            pis, cofins, ir, inss, csll = vals
        else:
            inss, pis, cofins, ir, csll = vals
        return {'pis': pis, 'cofins': cofins, 'ir': ir, 'inss': inss, 'csll': csll}
    return None


def parse_registro_estadual(texto: str) -> Optional[str]:
    """Nº do Registro Estadual (25 dígitos, `rodoOS/NroRegEstadual`) do bloco
    "INFORMAÇÕES ESPECÍFICAS DO MODAL RODOVIÁRIO"."""
    m = re.search(r'ESPEC[ÍI]FICAS\s+DO\s+MODAL', texto or '', re.IGNORECASE)
    trecho = (texto or '')[m.start():] if m else (texto or '')
    m = re.search(r'(?<!\d)(\d{25})(?!\d)', trecho)
    return m.group(1) if m else None
