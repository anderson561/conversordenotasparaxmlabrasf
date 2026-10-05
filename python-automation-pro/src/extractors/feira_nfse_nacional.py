"""Helpers do template "NFS-e de Feira de Santana/BA com chave NFS-e Nacional".

Template tratado: foto de celular (PDF sem texto digital) da NOTA FISCAL DE
SERVICOS ELETRONICA da Prefeitura de Feira de Santana/BA com o cabecalho
"Departamento de Administracao Tributaria", "Periodo de Competencia",
"Exigibilidade do ISS" e a linha "NFS-e Nacional: <chave de 50 digitos>" em
"INFORMACOES COMPLEMENTARES". Achado real 2026-10-05 (cruz e cruz.pdf).

Tudo aqui e funcao pura sobre texto (testavel sem OCR) exceto
`recortar_template`, que faz os recortes dedicados via Tesseract e devolve
linhas SINTETICAS `FEIRANAC_*` para o extrator costurar no corpo da nota
(nunca o texto de um re-OCR inteiro: ver familia 3 da memoria de padroes OCR).

Principio de integridade fiscal: onde a borda da foto cortou o dado e nada o
autoverifica (checksum de CNPJ, chave de acesso), o campo fica em sentinela +
aviso, nunca num valor plausivel fabricado.
"""

from __future__ import annotations

import difflib
import io
import itertools
import logging
import os
import re
import unicodedata
from collections import Counter
from typing import Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

COD_IBGE_FEIRA = '2910800'
MUNICIPIO_FEIRA = 'Feira de Santana'
UF_FEIRA = 'BA'

UFS_BRASIL = frozenset(
    'AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO'.split())

# Contrapartes cuja identidade o USUARIO confirmou em conversa (nao e
# heuristica de OCR). So e consultada quando a propria nota fornece evidencia
# independente: o sufixo de CNPJ lido (dentre as completacoes validas por
# checksum, esta tem de estar) e o fim do nome lido. Formato:
# cnpj -> (razao social correta, regex do nome como a foto cortada o mostra).
CONTRAPARTES_CONFIRMADAS: Dict[str, Tuple[str, str]] = {
    # Nome com o inicio cortado pela borda da foto ("TAVIMANA"/"RAVIMANA");
    # CNPJ com os 2 primeiros digitos fora do enquadramento e o 3o cortado.
    '04904636000119': ('SARAVIMANA PATRIMONIAL LTDA', r'VIMANA\s+PATRIMONIAL\s+LTDA'),
}

_TIPOS_VIA = (
    'RUA', 'AVENIDA', 'AV', 'ALAMEDA', 'TRAVESSA', 'TV', 'PRACA', 'PRAÇA', 'PCA', 'ESTRADA',
    'EST', 'RODOVIA', 'ROD', 'LARGO', 'LOTEAMENTO', 'LOT', 'VIA', 'BECO', 'VILA', 'CONJUNTO',
    'CONJ', 'QUADRA', 'FAZENDA', 'SITIO', 'SÍTIO', 'PARQUE', 'CAMINHO', 'BR', 'LADEIRA',
)

_MARCAS_TEMPLATE = (
    r'Reg\.?\s*Especial\s+Tributa',
    r'Munic[ií]pio\s+de\s+Presta',
    r'Per[ií]odo\s+de\s+Compet',
    r'Exig[ií]vel\s+em',
    r'Exig[ií]bilidade\s+do',
    r'Departamento\s+de\s+Administra',
    r'NFS-e\s+Nacional\s*:',
    r'Incen\w*ivador\s+Cultural',
    r'ELETR[ÔO]NICA\s*-\s*NFS-e',
    r'FEIRANAC_',
)


def eh_template(texto: str) -> bool:
    """True para o template foto/NFS-e Nacional de Feira de Santana.

    Gate ESTRUTURAL (nao pela cidade sozinha, que e marca compartilhada com
    tomadores/filiais de outras notas): exige a cidade E ao menos 2 marcas do
    template, tolerantes a OCR."""
    if not re.search(r'FEIRA\s+DE\s+SANTANA', texto, re.IGNORECASE):
        return False
    marcas = sum(1 for p in _MARCAS_TEMPLATE if re.search(p, texto, re.IGNORECASE))
    return marcas >= 2


# --------------------------------------------------------------------------
# CNPJ / chave de acesso
# --------------------------------------------------------------------------

def cnpj_valido(doc: str) -> bool:
    d = re.sub(r'\D', '', doc)
    if len(d) != 14 or d == d[0] * 14:
        return False
    for i in (12, 13):
        pesos = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2] if i == 12 else [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        resto = sum(int(d[n]) * pesos[n] for n in range(i)) % 11
        dv = 0 if 11 - resto >= 10 else 11 - resto
        if dv != int(d[i]):
            return False
    return True


def completar_cnpj_por_sufixo(sufixo: str) -> List[str]:
    """Todas as completacoes de 14 digitos, validas por checksum, de um sufixo
    confiavel (os digitos iniciais ficaram fora do enquadramento da foto)."""
    sufixo = re.sub(r'\D', '', sufixo)
    faltam = 14 - len(sufixo)
    if faltam < 0 or faltam > 4:
        return []
    if faltam == 0:
        return [sufixo] if cnpj_valido(sufixo) else []
    return [
        ''.join(pref) + sufixo
        for pref in itertools.product('0123456789', repeat=faltam)
        if cnpj_valido(''.join(pref) + sufixo)
    ]


def resolver_cnpj_por_sufixo(sufixo: str, razao_ocr: str = '') -> Tuple[Optional[str], Optional[str]]:
    """(cnpj, origem) a partir do sufixo lido.

    - exatamente UMA completacao valida -> aceita ('checksum_unico');
    - varias -> so aceita se EXATAMENTE UMA delas for contraparte confirmada
      pelo usuario E o nome lido casar o fim do nome dela ('contraparte_confirmada');
    - caso contrario (None, None): o chamador usa sentinela + aviso."""
    completacoes = completar_cnpj_por_sufixo(sufixo)
    if len(completacoes) == 1:
        return completacoes[0], 'checksum_unico'
    confirmadas = [
        c for c in completacoes
        if c in CONTRAPARTES_CONFIRMADAS
        and re.search(CONTRAPARTES_CONFIRMADAS[c][1], razao_ocr or '', re.IGNORECASE)
    ]
    if len(confirmadas) == 1:
        return confirmadas[0], 'contraparte_confirmada'
    return None, None


def corrigir_razao_confirmada(cnpj: str, razao_ocr: str) -> str:
    """Razao correta de contraparte confirmada, gated pelo CNPJ ja resolvido
    (familia 19: nunca heuristica generica de caracteres)."""
    if cnpj in CONTRAPARTES_CONFIRMADAS and re.search(
            CONTRAPARTES_CONFIRMADAS[cnpj][1], razao_ocr or '', re.IGNORECASE):
        return CONTRAPARTES_CONFIRMADAS[cnpj][0]
    return razao_ocr


def decodificar_chave(chave: str, emissao_aamm: Optional[str] = None) -> Optional[Dict[str, str]]:
    """Decodifica e VALIDA a chave NFS-e Nacional de 50 digitos.

    cMun(7) | amb(1) | tpInsc(1) | CNPJ(14) | nNFSe(13) | AAMM(4) | cod+DV(10).
    Valida: cMun de Feira de Santana, CNPJ com checksum, mes valido e, quando
    conhecido, AAMM igual ao mes/ano da emissao impressa."""
    chave = re.sub(r'\D', '', chave or '')
    if len(chave) != 50 or chave[:7] != COD_IBGE_FEIRA:
        return None
    cnpj, numero, aamm = chave[9:23], chave[23:36], chave[36:40]
    if not cnpj_valido(cnpj):
        return None
    if not 1 <= int(aamm[2:]) <= 12:
        return None
    if emissao_aamm and aamm != emissao_aamm:
        return None
    return {'chave': chave, 'cnpj': cnpj, 'numero': numero, 'aamm': aamm}


def extrair_chaves_de_texto(texto: str) -> List[str]:
    """Corridas de 50 digitos (tolerando espacos soltos do OCR) no texto."""
    chaves: List[str] = []
    for m in re.finditer(r'\d(?:[ \t]?\d){49,}', texto or ''):
        digitos = re.sub(r'\D', '', m.group(0))
        if len(digitos) == 50:
            chaves.append(digitos)
    return chaves


def votar_chave(leituras: Sequence[str], emissao_aamm: Optional[str] = None) -> Optional[str]:
    """Chave vencedora entre leituras independentes: so conta leitura que passa
    na validacao estrutural, e o vencedor precisa de >= 2 votos e de mais votos
    que o segundo colocado (empate -> None = sentinela)."""
    validas = [c for c in leituras if decodificar_chave(c, emissao_aamm)]
    if not validas:
        return None
    ranking = Counter(validas).most_common()
    if ranking[0][1] < 2:
        return None
    if len(ranking) > 1 and ranking[1][1] == ranking[0][1]:
        return None
    return ranking[0][0]


def aamm_da_emissao(texto: str) -> Optional[str]:
    """AAMM da primeira data+hora "dd/mm/aaaa hh:mm" da nota."""
    m = re.search(r'(\d{2})/(\d{2})/(\d{4})\s+\d{2}:\d{2}', texto or '')
    return (m.group(3)[2:] + m.group(2)) if m else None


# --------------------------------------------------------------------------
# Marcadores sinteticos e campos do corpo
# --------------------------------------------------------------------------

def ler_marcadores(texto: str) -> Dict[str, List[str]]:
    """Linhas `FEIRANAC_<CHAVE>: <valor>` -> {CHAVE: [valores]}."""
    saida: Dict[str, List[str]] = {}
    for m in re.finditer(r'^FEIRANAC_([A-Z_]+):[ \t]*(.*)$', texto or '', re.MULTILINE):
        saida.setdefault(m.group(1), []).append(m.group(2).strip())
    return saida


def sem_acento(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


_ROTULOS_RAZAO = re.compile(
    r'^(?:Nome\s*Fantasia|CNPJ|CPF|Inscri|Email|E-mail|Fone|Endere|\W*$)', re.IGNORECASE)


def extrair_razoes(texto: str) -> List[str]:
    """Razao social (1a linha util apos cada rotulo "Razao Social"), na ordem
    do documento: [0] prestador, [1] tomador. Corta no fim da LINHA: o rotulo
    da linha seguinte ("Nome Fantasia / Email") nao entra no nome."""
    razoes: List[str] = []
    linhas = (texto or '').split('\n')
    for i, linha in enumerate(linhas):
        if not re.search(r'Raz[ãa]o\s+Social', linha, re.IGNORECASE):
            continue
        for prox in linhas[i + 1:i + 4]:
            prox = prox.strip()
            if not prox or _ROTULOS_RAZAO.match(prox):
                continue
            razoes.append(re.sub(r'\s+', ' ', prox).strip(' .,;|'))
            break
    return razoes


def parse_endereco_prefixo(prefixo: str) -> Dict[str, Optional[str]]:
    """"<logradouro>, <numero>[, <complemento>][, | - ]<bairro>" -> campos."""
    prefixo = re.sub(r'\s+', ' ', (prefixo or '').replace('|', ' ')).strip(' -,.;:')
    m = re.match(r'^(?P<log>.+?),\s*(?P<num>\d+[A-Za-z]?|S/?N)\b(?P<resto>.*)$', prefixo, re.IGNORECASE)
    if not m:
        return {'logradouro': prefixo or None, 'numero': None, 'complemento': None, 'bairro': None}
    resto = m.group('resto').strip(' ,-')
    partes = [p.strip() for p in re.split(r'\s*,\s*|\s+-\s+', resto) if p.strip()]
    bairro = partes[-1] if partes else None
    complemento = ', '.join(partes[:-1]) if len(partes) > 1 else None
    numero = m.group('num').upper()
    return {
        'logradouro': m.group('log').strip(' .'),
        'numero': 'S/N' if re.fullmatch(r'S/?N', numero) else numero,
        'complemento': complemento,
        'bairro': bairro,
    }


def logradouro_sem_fragmento_cortado(logradouro: str) -> Tuple[str, bool]:
    """(logradouro, cortado). A borda esquerda da foto corta o tipo de via
    ("RUA"/"AVENIDA" viram "UA"/"ida"). Sem tipo de via reconhecivel, um 1o
    token de <= 4 letras e resto de palavra cortada: descartado (nao se
    completa o que a foto nao mostra). `cortado` sinaliza o aviso."""
    texto = (logradouro or '').strip()
    if not texto:
        return texto, False
    primeiro, _, resto = texto.partition(' ')
    if sem_acento(primeiro).upper().strip('.') in {sem_acento(t).upper() for t in _TIPOS_VIA}:
        return texto, False
    if resto and len(primeiro) <= 4 and (primeiro.isalpha() or len(primeiro) == 1):
        return resto.strip(), True
    return texto, True


def descricao_sem_inicio_cortado(linhas: Sequence[str]) -> List[str]:
    """Remove o 1o token de cada linha de descricao (palavra cortada pela borda)."""
    saida = []
    for linha in linhas:
        _, _, resto = linha.strip().partition(' ')
        saida.append(resto.strip() if resto else linha.strip())
    return saida


def parse_valor_br(s: str) -> float:
    return float(s.replace('.', '').replace(',', '.'))


_RE_MONEY = re.compile(r'^\d{1,3}(?:\.\d{3})*,\d{2}$')


# --------------------------------------------------------------------------
# Recortes OCR dedicados
# --------------------------------------------------------------------------

def _ocr_libs():
    import pymupdf
    import pytesseract
    from PIL import Image
    tess = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    if os.path.exists(tess):
        pytesseract.pytesseract.tesseract_cmd = tess
    return pymupdf, pytesseract, Image


def _render(page, zoom: float, angle: int):
    pymupdf, _, Image = _ocr_libs()
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
    img = Image.open(io.BytesIO(pix.tobytes('png')))
    if angle:
        img = img.rotate(-angle, expand=True)
    return img.convert('L')


class _Pagina:
    """Pagina + orientacao ja corrigida, com cache de renders por zoom (o mesmo
    zoom e reaproveitado entre recortes - renderizar domina o custo)."""

    def __init__(self, page, angle: int) -> None:
        self.page = page
        self.angle = angle
        self._cache: Dict[float, object] = {}

    def render(self, zoom: float):
        if zoom not in self._cache:
            self._cache[zoom] = _render(self.page, zoom, self.angle)
        return self._cache[zoom]


def _palavras(img) -> List[dict]:
    _, pytesseract, _ = _ocr_libs()
    d = pytesseract.image_to_data(img, lang='por', output_type=pytesseract.Output.DICT)
    return [
        {'t': (d['text'][i] or '').strip(), 'l': d['left'][i], 'top': d['top'][i],
         'w': d['width'][i], 'h': d['height'][i]}
        for i in range(len(d['text'])) if (d['text'][i] or '').strip()
    ]


def _ler(img, psm: int) -> str:
    _, pytesseract, _ = _ocr_libs()
    return pytesseract.image_to_string(img, lang='por', config=f'--psm {psm}')


def _banda(pg: _Pagina, zoom: float, zoom_ref: float, x0: float, y0: float, x1: Optional[float], y1: float):
    """Recorte [x0..x1] x [y0..y1] (coordenadas do render de referencia
    `zoom_ref`) renderizado em `zoom`. x1 None = largura inteira."""
    img = pg.render(zoom)
    s = zoom / zoom_ref
    largura = img.size[0]
    return img.crop((
        int(max(0, x0) * s), int(max(0, y0) * s),
        int(x1 * s) if x1 is not None else largura, min(img.size[1], int(y1 * s))))


def _voto_distinto_zoom(candidatos: Sequence[Tuple[float, str]]) -> Optional[str]:
    """Valor com >= 2 votos de ZOOMS DISTINTOS e mais votos que o 2o colocado
    (familia 4: so e evidencia a concordancia entre leituras independentes)."""
    if not candidatos:
        return None
    zooms_por_valor: Dict[str, set] = {}
    contagem: Counter = Counter()
    for zoom, valor in candidatos:
        zooms_por_valor.setdefault(valor, set()).add(zoom)
        contagem[valor] += 1
    ranking = contagem.most_common()
    vencedor, votos = ranking[0]
    if len(zooms_por_valor[vencedor]) < 2:
        return None
    if len(ranking) > 1 and ranking[1][1] == votos:
        return None
    return vencedor


def _recorte_chave(pg, palavras, h_pagina, texto_base) -> List[str]:
    aamm = aamm_da_emissao(texto_base)
    ancoras = [p for p in palavras
               if p['top'] > 0.5 * h_pagina
               and (re.search(r'MA[ÇC][ÕO]ES$', p['t']) or p['t'] == 'IBPT' or p['t'].lower() == 'federal')]
    if not ancoras:
        return []
    y_ancora = min(a['top'] for a in ancoras)
    leituras = list(extrair_chaves_de_texto(texto_base))
    for zoom in (2.5, 3.0):
        for recuo in (0, 20, 60):
            img = _banda(pg, zoom, 3.0, 0, y_ancora - recuo, None, h_pagina)
            for psm in (6, 4):
                leituras.extend(extrair_chaves_de_texto(_ler(img, psm)))
    vencedora = votar_chave(leituras, aamm)
    return [f'FEIRANAC_CHAVE: {vencedora}'] if vencedora else []


def _sufixo_cnpj_da_linha(pg, palavras, token_cep, y_piso) -> Optional[str]:
    """Sufixo confiavel do CNPJ impresso logo acima da linha de endereco.

    O 1o digito visivel fica clipado na borda esquerda e o Tesseract o troca
    ("9"->"2"/"1"/"7"): so os digitos depois dele entram no sufixo."""
    rotulos = [p for p in palavras
               if re.match(r'Inscri', p['t'], re.IGNORECASE)
               and y_piso < p['top'] < token_cep['top'] - 0.5 * token_cep['h']]
    if not rotulos:
        return None
    ref = max(rotulos, key=lambda p: p['top'])
    y0 = ref['top'] + ref['h'] + 2
    y1 = token_cep['top'] - 2
    if y1 - y0 < 20:
        return None
    candidatos: List[Tuple[float, str]] = []
    for zoom in (3.0, 3.5, 4.0, 5.0):
        img = _banda(pg, zoom, 3.0, 0, y0, 0.4 * max(p['l'] + p['w'] for p in palavras), y1)
        for psm in (6,):
            m = re.search(r'([\d.,]{3,14})/(\d{4})-(\d{2})', _ler(img, psm))
            if not m:
                continue
            esq = re.sub(r'\D', '', m.group(1))
            if len(esq) < 8:
                esq = esq[1:]
            sufixo = esq + m.group(2) + m.group(3)
            if len(sufixo) >= 9:
                candidatos.append((zoom, sufixo))
    return _voto_distinto_zoom(candidatos)


def _recorte_enderecos_e_cnpjs(pg, palavras) -> List[str]:
    saida: List[str] = []
    ancora_prest = [p for p in palavras if p['t'] == 'PRESTADOR']
    if not ancora_prest:
        return saida
    y_prest = min(p['top'] for p in ancora_prest)
    ceps = sorted((p for p in palavras if re.fullmatch(r'CEP[:;.]?', p['t']) and p['top'] > y_prest),
                  key=lambda p: p['top'])
    for rotulo, token in zip(('PREST', 'TOM'), ceps[:2]):
        leituras: List[Tuple[str, str, str]] = []
        for zoom in (3.0, 3.5, 4.0, 5.0):
            h = token['h']
            img = _banda(pg, zoom, 3.0, 0, token['top'] - 0.7 * h, None, token['top'] + 1.9 * h)
            txt = _ler(img, 7).strip().replace('\n', ' ')
            m = re.match(r'^(.*?)\s*[-–]?\s*CEP\s*[:;.]?\s*(\d{5})\s*-?\s*(\d{3})(.*)$', txt)
            if m:
                leituras.append((m.group(1), m.group(2) + m.group(3), m.group(4)))
        ceps_lidos = Counter(c for _, c, _ in leituras)
        if not ceps_lidos or ceps_lidos.most_common(1)[0][1] < 2:
            continue
        cep = ceps_lidos.most_common(1)[0][0]
        prefixos = [p for p, c, _ in leituras if c == cep]
        # medoide: o prefixo mais parecido com os demais (um unico erro de
        # leitura nao decide, e nenhum texto e inventado - sempre uma leitura real)
        prefixo = max(prefixos, key=lambda a: sum(
            difflib.SequenceMatcher(None, sem_acento(a).upper(), sem_acento(b).upper()).ratio()
            for b in prefixos))
        caudas: Counter = Counter()
        for _, c, cauda in leituras:
            mm = re.search(r'-\s*([A-Za-zÀ-ú][A-Za-zÀ-ú ]{2,40}?)\s*-\s*([A-Z]{2})\s*$', cauda.strip())
            if c == cep and mm and mm.group(2) in UFS_BRASIL:
                caudas[f'{mm.group(1).strip()}|{mm.group(2)}'] += 1
        municipio, uf = '', ''
        if caudas and caudas.most_common(1)[0][1] >= 2:
            municipio, uf = caudas.most_common(1)[0][0].split('|')
        prefixo_limpo = prefixo.replace('|', ' ').strip()
        saida.append(f'FEIRANAC_END_{rotulo}: {prefixo_limpo}|{cep}|{municipio}|{uf}')
        sufixo = _sufixo_cnpj_da_linha(pg, palavras, token, y_prest)
        if sufixo:
            saida.append(f'FEIRANAC_CNPJ_{rotulo}_SUFIXO: {sufixo}')
    return saida


# Subclasses CNAE 2.3 do grupo 69 (atividades juridicas): so servem para
# descartar leitura IMPOSSIVEL (ex.: "6911704" nao existe) - nao e tabela
# completa de CNAE.
_CNAE_GRUPO_69 = frozenset({'6911701', '6911702', '6911703', '6912500'})


def cnae_plausivel(cnae: str) -> bool:
    return cnae in _CNAE_GRUPO_69 if cnae[:2] == '69' else True


def _recorte_cnae(pg, palavras) -> List[str]:
    ancoras = [p for p in palavras if re.fullmatch(r'CNAE:?', p['t'])]
    if not ancoras:
        return []
    a = ancoras[0]
    candidatos: List[Tuple[float, str]] = []
    for zoom in (3.0, 3.25, 3.5, 3.75, 4.0, 4.5, 5.0):
        img = _banda(pg, zoom, 3.0, a['l'], a['top'] - 0.6 * a['h'],
                     a['l'] + 6 * a['w'], a['top'] + 1.7 * a['h'])
        m = re.search(r'CNAE\W*(\d{7})\b', _ler(img, 7))
        if m and cnae_plausivel(m.group(1)):
            candidatos.append((zoom, m.group(1)))
    cnae = _voto_distinto_zoom(candidatos)
    return [f'FEIRANAC_CNAE: {cnae}'] if cnae else []


def _recorte_valores(pg, palavras) -> List[str]:
    liq = [p for p in palavras if re.fullmatch(r'L[ií]quido', p['t'], re.IGNORECASE)]
    if not liq:
        return []
    ref = max(liq, key=lambda p: p['top'])
    _, pytesseract, _ = _ocr_libs()
    votos: Dict[str, List[Tuple[float, str]]] = {'SERVICOS': [], 'LIQUIDO': [], 'ISS': []}
    for zoom in (3.0, 3.5, 4.0):
        s = zoom / 3.0
        img = _banda(pg, zoom, 3.0, 0, ref['top'] - 5, None, ref['top'] + 4.5 * ref['h'])
        d = pytesseract.image_to_data(img, lang='por', config='--psm 6', output_type=pytesseract.Output.DICT)
        toks = [{'t': (d['text'][i] or '').strip(), 'cx': (d['left'][i] + d['width'][i] / 2) / s,
                 'l': d['left'][i] / s, 'top': d['top'][i] / s, 'h': d['height'][i] / s}
                for i in range(len(d['text'])) if (d['text'][i] or '').strip()]
        liq_b = [t for t in toks if re.fullmatch(r'L[ií]quido', t['t'], re.IGNORECASE)]
        if not liq_b:
            continue
        lb = liq_b[0]
        mesma_linha = [t for t in toks if abs(t['top'] - lb['top']) <= 15]
        colunas = {'LIQUIDO': lb['cx']}
        serv = [t for t in mesma_linha if re.fullmatch(r'Servi[çc]os', t['t'], re.IGNORECASE)]
        if serv:
            colunas['SERVICOS'] = serv[0]['cx']
        iss = sorted((t for t in mesma_linha if t['t'] == 'ISS'), key=lambda t: t['l'])
        if iss:
            colunas['ISS'] = iss[0]['cx'] + 25
        dinheiro = [t for t in toks if _RE_MONEY.match(t['t']) and t['top'] > lb['top'] + 0.9 * lb['h']]
        for nome, cx in colunas.items():
            proximos = [(abs(t['cx'] - cx), t['t']) for t in dinheiro if abs(t['cx'] - cx) <= 90]
            if proximos:
                votos[nome].append((zoom, min(proximos)[1]))
    saida = []
    for nome, v in votos.items():
        lido = _voto_distinto_zoom(v)
        if lido:
            saida.append(f'FEIRANAC_VALOR_{nome}: {lido}')
    return saida


def _recorte_descricao(pg, palavras) -> List[str]:
    prest = [p for p in palavras if p['t'] == 'PRESTADO']
    fim = [p for p in palavras if re.fullmatch(r'F?EDERAIS', p['t'])]
    if not prest or not fim:
        return []
    y0 = prest[0]['top'] - 3
    y1 = min(f['top'] for f in fim if f['top'] > y0) - 3 if any(f['top'] > y0 for f in fim) else None
    if y1 is None:
        return []
    texto = _ler(_banda(pg, 3.0, 3.0, 0, y0, None, y1), 6)
    linhas = [re.sub(r'\s+', ' ', ln).strip() for ln in texto.split('\n')]
    saida: List[str] = []
    em_descricao = False
    cortado = True
    for ln in linhas:
        letras = len(re.findall(r'[A-Za-zÀ-ú]', ln))
        if re.search(r'[ÇC][ÃA]O\s+DOS\s+SERVI', ln, re.IGNORECASE) and letras < 30:
            em_descricao = True
            cortado = not re.search(r'DESCRI[ÇC][ÃA]O', ln, re.IGNORECASE)
            continue
        if re.search(r'PRESTADO\b', ln) and letras < 15:
            continue
        if letras < 12 or letras < 0.5 * len(ln.replace(' ', '')):
            continue
        saida.append(f"FEIRANAC_{'DESC' if em_descricao else 'SERVICO'}: {ln}")
    if em_descricao:
        saida.append(f'FEIRANAC_DESC_CORTADO: {1 if cortado else 0}')
    return saida


def recortar_template(page, angle: int, texto_base: str) -> str:
    """Recortes dedicados do template; linhas sinteticas `FEIRANAC_*`.

    Cada sub-leitura e independente: a falha de uma (Tesseract/E-S) apenas a
    omite e o extrator cai no texto base ou em sentinela + aviso."""
    saida: List[str] = []
    try:
        _ocr_libs()
        pg = _Pagina(page, angle)
        img_ref = pg.render(3.0)
        palavras = _palavras(img_ref)
        h_pagina = img_ref.size[1]
    except (OSError, ValueError, RuntimeError, ImportError) as exc:
        logger.warning('Feira NFS-e Nacional: recortes indisponiveis (%s)', exc)
        return ''
    for nome, leitor in (
        ('chave', lambda: _recorte_chave(pg, palavras, h_pagina, texto_base)),
        ('enderecos/cnpj', lambda: _recorte_enderecos_e_cnpjs(pg, palavras)),
        ('cnae', lambda: _recorte_cnae(pg, palavras)),
        ('valores', lambda: _recorte_valores(pg, palavras)),
        ('descricao', lambda: _recorte_descricao(pg, palavras)),
    ):
        try:
            saida.extend(leitor())
        except (OSError, ValueError, RuntimeError, IndexError, KeyError) as exc:
            logger.warning('Feira NFS-e Nacional: recorte "%s" falhou (%s)', nome, exc)
    return '\n'.join(saida) + ('\n' if saida else '')
