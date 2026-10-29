"""Helpers do impresso "NOTA DÉBITO / FATURA" de locação de bens móveis (NÃO é NFS-e).

Achado real 2026-10-23 (`Notas/092026/locacao.pdf`): ANA CELIA MOREIRA RIBEIRO
(CNPJ 45.282.926/0001-55, Salvador/BA) -> SINAL CONSTRUTORA LTDA (CNPJ
33.811.381/0001-48, Pojuca/BA), "NOTA DÉBITO Nº 36" / "FATURA 005-2026",
locação de caçamba truck (2 placas), R$ 17.827,08. Antes deste módulo a página
caía em LAYOUT_GENERICO, era descartada ("Layout não reconhecido") e a
conversão abortava com "parece ser baseado em imagem/scan ou vazio".

Estrutura do impresso (modelo próprio do emitente, sem prefeitura/plataforma):
  * letterhead (logo, razão social, "CNPJ", endereço, "<CIDADE>, <UF> CEP:",
    "EMAIL: ... - TEL:") e, à direita, "NOTA DÉBITO Nº <n>" + "FATURA <n>-<ano>";
  * "DATA EMISSÃO" | "VENCIMENTO" e "NATUREZA DA OPERAÇÃO";
  * bloco "TOMADOR DO SERVIÇO" em grade (rótulos numa linha, valores em caixas
    na linha de baixo): NOME/RAZÃO SOCIAL | CNPJ; ENDEREÇO | BAIRRO | CEP;
    MUNICIPIO | UF | INSC. ESTADUAL | INSC. MUNICIPAL;
  * grade de itens DESCRIÇÃO | QUANT. DIAS | PERIODO | TOTAL e "TOTAL DA FATURA";
  * dados bancários (não são campos do XML) e "OBSERVAÇÕES COMPLEMENTARES"
    ("NÃO SUJEITO A I.S.S. CONFORME [LEI] COMPLEMENTAR FEDERAL Nº 116/2003 ...").

A detecção é ESTRUTURAL (título "NOTA DÉBITO Nº" + "FATURA <n>" + "NATUREZA DA
OPERAÇÃO" + "TOMADOR DO SERVIÇO", e nada de NFS-e), não pelo nome do emitente.

A página real é FOTO de celular, de cabeça para baixo: o `_ocr_page` já acha a
rotação de 180° (o placar da leitura invertida bate o limiar), mas a leitura de
página inteira perde TODAS as caixas de valor (datas, nome/CNPJ/município do
tomador, valores dos itens, "TOTAL DA FATURA"). Por isso `recortar` (chamado
pelo `_ocr_page`, na imagem já girada) lê cada caixa num recorte próprio,
ancorado nos rótulos via `image_to_data`, com várias variantes de imagem e
VOTAÇÃO por validador (data, CNPJ com DV, UF, moeda, placa), e devolve linhas
sintéticas `NOTADEB_*` PREPENDIDAS ao texto da página (mesma técnica de
`nota_locacao.py`/`feira_nfse_nacional.py`). `extrair` é função pura sobre o
texto; o que não for legível vira sentinela + aviso.

Decisões do usuário (2026-10-23): Número = número da FATURA sem o ano e sem
zeros à esquerda ("FATURA 005-2026" -> "5"), NÃO o "NOTA DÉBITO Nº 36";
competência = mês da DATA DE EMISSÃO (não o período da locação).
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple

from ..models.nfse_models import Endereco, Entidade, Valores
from .nota_locacao import (
    CODIGO_VERIFICACAO, ITEM_LOCACAO, ItemLocacao, NotaLocacao,
    _colapsa, _sem_acento, _valor_br, separar_endereco,
)

logger = logging.getLogger(__name__)

__all__ = ['ITEM_LOCACAO', 'CODIGO_VERIFICACAO', 'PREFIXO', 'eh_nota_debito_locacao',
           'recortar', 'extrair', 'ler_marcadores']

PREFIXO = 'NOTADEB_'

_SENTINELA_DOC = '00000000000000'
_SENTINELA_NUMERO = '00000000'

_MONEY = r'\d{1,3}(?:\.\d{3})*,\d{2}'
_RE_NOTA_DEBITO = re.compile(r'NOTA\s*(?:DE\s*)?D[ÉE]BITO\s*N\s*[º°oO.�]{0,2}\s*(\d{1,10})\b', re.IGNORECASE)
_RE_FATURA = re.compile(r'\bFATURA\s*(?:N\s*[º°oO.]{0,2}\s*)?(\d{1,10})(?:\s*[-/]\s*(\d{4}))?\b', re.IGNORECASE)
_RE_NATUREZA = re.compile(r'NATUREZA\s+DA\s+OPERA', re.IGNORECASE)
_RE_TOMADOR = re.compile(r'TOMADOR\s+DO\s+SERVI', re.IGNORECASE)
_RE_DATA = re.compile(r'(\d{2})\s*/\s*(\d{2})\s*/\s*(\d{4})')
_RE_CNPJ_SOLTO = re.compile(r'\d{2}[.,]?\d{3}[.,]?\d{3}\s*/?\s*\d{4}\s*[-.,]?\s*\d{2}')
_RE_PLACA = re.compile(r'\b([A-Z]{3})\s?-?(\d[A-Z0-9]\d{2})\b')
_UFS = {'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB',
        'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'}


# ---------------------------------------------------------------------------
# Detecção
# ---------------------------------------------------------------------------

def eh_nota_debito_locacao(texto: str) -> bool:
    """True para o impresso "NOTA DÉBITO / FATURA" de locação.

    Exige as 4 âncoras estruturais: "NOTA DÉBITO Nº <n>", "FATURA <n>",
    "NATUREZA DA OPERAÇÃO" e "TOMADOR DO SERVIÇO". Documento que se declare
    NFS-e/Nota Fiscal Eletrônica/DANFS fica fora (uma NFS-e pode citar
    "nota de débito" na discriminação, mas não tem as quatro)."""
    if not texto:
        return False
    if not _RE_NOTA_DEBITO.search(texto):
        return False
    if not _RE_FATURA.search(texto):
        return False
    if not (_RE_NATUREZA.search(texto) and _RE_TOMADOR.search(texto)):
        return False
    if re.search(r'\bNFS-?e\b|Nota\s+Fiscal\s+(?:Eletr|de\s+Servi)|DANFS', texto, re.IGNORECASE):
        return False
    return True


def ler_marcadores(texto: str) -> Dict[str, List[str]]:
    """Linhas `NOTADEB_<CHAVE>: <valor>` -> {CHAVE: [valores]}."""
    saida: Dict[str, List[str]] = {}
    for m in re.finditer(r'^NOTADEB_([A-Z_]+):[ \t]*(.*)$', texto or '', re.MULTILINE):
        saida.setdefault(m.group(1), []).append(m.group(2).strip())
    return saida


def _sem_marcadores(texto: str) -> str:
    return re.sub(r'^NOTADEB_[A-Z_]+:.*\n?', '', texto or '', flags=re.MULTILINE)


# ---------------------------------------------------------------------------
# Validadores/normalizadores de leitura de caixa (funções puras)
# ---------------------------------------------------------------------------

def norm_data(txt: str) -> Optional[str]:
    m = _RE_DATA.search(txt or '')
    if not m:
        return None
    d, mm, a = m.groups()
    try:
        datetime(int(a), int(mm), int(d))
    except ValueError:
        return None
    return f'{d}/{mm}/{a}'


def norm_uf(txt: str) -> Optional[str]:
    for tok in re.findall(r'[A-Z]{2,3}', (txt or '').upper()):
        if tok[:2] in _UFS and (len(tok) == 2 or tok == 'BAI'):
            return tok[:2]
    return None


def norm_cnpj(txt: str, validar_doc: Callable[[str], bool]) -> Optional[str]:
    for m in _RE_CNPJ_SOLTO.finditer(txt or ''):
        d = re.sub(r'\D', '', m.group(0))
        if len(d) == 14 and validar_doc(d):
            return d
    return None


def valores_moeda(txt: str) -> List[str]:
    return re.findall(_MONEY, txt or '')


def placas(txt: str) -> List[str]:
    return [a + b for a, b in _RE_PLACA.findall((txt or '').upper())]


def votar(leituras: List[Optional[str]]) -> Optional[str]:
    """Valor mais lido entre as leituras válidas (empate: o primeiro lido)."""
    validas = [l for l in leituras if l]
    if not validas:
        return None
    contagem = Counter(validas)
    melhor = max(contagem.values())
    return next(l for l in validas if contagem[l] == melhor)


def votar_listas(leituras: List[List[str]]) -> List[str]:
    """Votação POSIÇÃO a posição entre as leituras com o número de valores mais
    frequente (ex.: [7.327,08, 10.500,00] x [7.327,08, 10.500,09] ...)."""
    nao_vazias = [l for l in leituras if l]
    if not nao_vazias:
        return []
    tam = Counter(len(l) for l in nao_vazias).most_common(1)[0][0]
    alinhadas = [l for l in nao_vazias if len(l) == tam]
    return [votar([l[i] for l in alinhadas]) for i in range(tam)]


# ---------------------------------------------------------------------------
# Recortes (OCR) - chamados por `SPPdfExtractor._ocr_page`
# ---------------------------------------------------------------------------

def _palavras(img, config: str = '', dy: int = 0, dx: int = 0) -> List[dict]:
    import pytesseract
    d = pytesseract.image_to_data(img, lang='por', config=config, output_type=pytesseract.Output.DICT)
    saida = []
    for i, txt in enumerate(d['text']):
        txt = (txt or '').strip()
        if not txt:
            continue
        saida.append({'txt': txt, 'norm': _sem_acento(txt).upper().strip(':.;,'),
                      'left': d['left'][i] + dx, 'top': d['top'][i] + dy,
                      'width': d['width'][i], 'height': d['height'][i]})
    return saida


def _ancora(palavras: List[dict], *prefixos: str, top_min: int = -1) -> Optional[dict]:
    for p in palavras:
        if p['top'] > top_min and any(p['norm'].startswith(px) for px in prefixos):
            return p
    return None


def _variantes(img):
    """Variantes da caixa recortada: tons de cinza em 1x/2x/3x e binarizações
    (a foto tem sombra e as caixas têm borda grossa - nenhuma variante sozinha
    lê todas as caixas; o validador + a votação escolhem)."""
    from PIL import Image, ImageOps
    g = ImageOps.grayscale(img)
    yield g
    yield g.resize((g.width * 2, g.height * 2), Image.LANCZOS)
    yield g.resize((g.width * 3, g.height * 3), Image.LANCZOS)
    for limiar in (90, 110, 130):
        yield g.point(lambda v, lim=limiar: 255 if v > lim else 0)


def _ler_caixa(img, caixa: Tuple[int, int, int, int], psm: int = 6) -> List[str]:
    """Texto de cada variante da caixa (lista, uma leitura por variante)."""
    import pytesseract
    x0, y0, x1, y1 = (int(v) for v in caixa)
    largura, altura = img.size
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(largura, x1), min(altura, y1)
    if x1 - x0 < 20 or y1 - y0 < 10:
        return []
    recorte = img.crop((x0, y0, x1, y1))
    return [pytesseract.image_to_string(v, lang='por', config=f'--psm {psm}') for v in _variantes(recorte)]


def _fmt_br(valor: float) -> str:
    """17827.08 -> "17.827,08"."""
    return f'{valor:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')


def _corta_apos_sufixo(razao: str) -> str:
    """Corta o ruído que o OCR cola DEPOIS do sufixo societário ("SINAL
    CONSTRUTORA LTDA TR" -> "SINAL CONSTRUTORA LTDA"; o "TR" é a borda da
    caixa). Sem sufixo, devolve como lido. Função pura."""
    m = re.search(r'^(.*?\b(?:LTDA|S\.?/?A|EIRELI|EPP|ME|MEI)\b\.?)', razao or '')
    return m.group(1).strip() if m else (razao or '').strip()


def _colunas_por_vao(palavras: List[dict]) -> List[str]:
    """Agrupa as palavras de UMA linha da grade em colunas, quebrando onde o vão
    horizontal entre palavras passa de 2x a altura da letra (vão de borda de
    caixa, não de espaço entre palavras). Função pura."""
    ws = sorted(palavras, key=lambda w: w['left'])
    if not ws:
        return []
    alt = sorted(w['height'] for w in ws)[len(ws) // 2]
    grupos: List[List[dict]] = [[ws[0]]]
    for w in ws[1:]:
        ant = grupos[-1][-1]
        if w['left'] - (ant['left'] + ant['width']) > 2 * max(alt, 8):
            grupos.append([w])
        else:
            grupos[-1].append(w)
    return [' '.join(w['txt'] for w in g if w['txt'] not in ('|', '[', ']')).strip() for g in grupos]


def recortar(img, texto_base: str, validar_doc: Optional[Callable[[str], bool]] = None) -> str:
    """Linhas sintéticas `NOTADEB_*` (ver docstring do módulo). `img` é a página
    renderizada (PIL), já na orientação vencedora do OCR. Cada caixa é
    independente: a falha de uma só a omite."""
    validar_doc = validar_doc or (lambda d: len(d) == 14)
    try:
        palavras = _palavras(img)
    except (OSError, RuntimeError, ValueError, ImportError) as exc:
        logger.warning('Nota débito/fatura: recortes indisponíveis (%s)', exc)
        return ''
    largura, _altura = img.size
    saida: List[str] = []

    def _add(chave: str, valor: Optional[str]) -> None:
        if valor:
            saida.append(f'{PREFIXO}{chave}: {valor}')

    data = _ancora(palavras, 'DATA')
    venc = _ancora(palavras, 'VENCIMENTO')
    natureza = _ancora(palavras, 'NATUREZA')
    nome = _ancora(palavras, 'NOME/RAZ', 'NOME')
    cnpj = _ancora(palavras, 'CNPJ', top_min=nome['top'] - 30) if nome else None
    endereco = _ancora(palavras, 'ENDERE', top_min=nome['top'] if nome else -1)
    municipio = _ancora(palavras, 'MUNICIPIO', top_min=endereco['top'] if endereco else -1)
    uf = _ancora(palavras, 'UF', top_min=municipio['top'] - 30) if municipio else None
    descricao = _ancora(palavras, 'DESCRI', top_min=municipio['top'] if municipio else -1)

    try:
        if data and natureza:
            y0, y1 = data['top'] + data['height'] + 2, natureza['top'] - 2
            corte = (venc['left'] - 250) if venc else largura // 2
            _add('EMISSAO', votar([norm_data(t) for t in _ler_caixa(img, (0, y0, corte, y1))]))
            if venc:
                _add('VENCIMENTO', votar([norm_data(t) for t in _ler_caixa(img, (venc['left'] - 200, y0, largura, y1))]))
    except (OSError, RuntimeError, ValueError) as exc:
        logger.warning('Nota débito/fatura: recorte das datas falhou (%s)', exc)

    try:
        if nome and cnpj and endereco:
            y0, y1 = nome['top'] + nome['height'] + 2, endereco['top'] - 2
            nomes = []
            for t in _ler_caixa(img, (0, y0, cnpj['left'] - 220, y1)):
                linha = _corta_apos_sufixo(_colapsa(' '.join(l for l in t.splitlines() if l.strip())).strip(' |[]'))
                if len(re.findall(r'[A-Z]{3,}', linha)) >= 2 and linha == linha.upper():
                    nomes.append(linha)
            _add('TOM_NOME', votar(nomes))
            _add('TOM_CNPJ', votar([norm_cnpj(t, validar_doc) for t in _ler_caixa(img, (cnpj['left'] - 250, y0, largura, y1))]))
    except (OSError, RuntimeError, ValueError) as exc:
        logger.warning('Nota débito/fatura: recorte do nome/CNPJ do tomador falhou (%s)', exc)

    try:
        if endereco and municipio:
            y0, y1 = endereco['top'] + endereco['height'] + 2, municipio['top'] - 2
            from PIL import ImageOps
            faixa = ImageOps.grayscale(img.crop((0, y0, largura, y1)))
            colunas = _colunas_por_vao(_palavras(faixa, config='--psm 6'))
            colunas = [c for c in colunas if c]
            if colunas:
                m_cep = re.fullmatch(r'(\d{2}\.?\d{3}-?\d{3})', colunas[-1])
                if m_cep:
                    _add('TOM_CEP', m_cep.group(1))
                    colunas = colunas[:-1]
                if colunas:
                    _add('TOM_ENDERECO', colunas[0])
                if len(colunas) >= 2:
                    _add('TOM_BAIRRO', ' '.join(colunas[1:]))
    except (OSError, RuntimeError, ValueError) as exc:
        logger.warning('Nota débito/fatura: recorte do endereço do tomador falhou (%s)', exc)

    try:
        if municipio and uf and descricao:
            y0 = uf['top'] + uf['height'] + 6
            y1 = min(y0 + 3 * uf['height'], descricao['top'] - 2)
            muns = []
            for t in _ler_caixa(img, (0, y0, uf['left'] - 25, y1)):
                linha = _colapsa(t).strip(' |[]')
                if re.fullmatch(r"[A-ZÀ-Ú][A-ZÀ-Ú' .-]{2,}", linha):
                    muns.append(linha)
            _add('TOM_MUNICIPIO', votar(muns))
            _add('TOM_UF', votar([norm_uf(t) for t in _ler_caixa(img, (uf['left'] - 20, y0, uf['left'] + 120, y1))]))
    except (OSError, RuntimeError, ValueError) as exc:
        logger.warning('Nota débito/fatura: recorte do município do tomador falhou (%s)', exc)

    try:
        if descricao:
            y_ini = descricao['top'] + descricao['height'] + 4
            from PIL import ImageOps
            inferior = _palavras(ImageOps.grayscale(img.crop((0, descricao['top'] - 20, largura, img.size[1]))),
                                 config='--psm 6', dy=descricao['top'] - 20)
            quant = _ancora(palavras, 'QUANT', top_min=descricao['top'] - 30) or _ancora(inferior, 'QUANT')
            periodo = _ancora(palavras, 'PERIODO', top_min=descricao['top'] - 30) or _ancora(inferior, 'PERIODO')
            total = next((p for p in inferior if p['norm'].replace(' ', '').startswith('TOTALDAFATURA')
                          or (p['norm'] == 'FATURA' and p['top'] > y_ini)), None)
            y_fim = total['top'] - 4 if total else y_ini + 10 * descricao['height']
            if quant:
                descs = _ler_caixa(img, (0, y_ini, quant['left'] - 15, y_fim))
                primeiras = [next((_colapsa(l) for l in t.splitlines() if re.search(r'[A-Z]{3,}', l)), None)
                             for t in descs]
                _add('ITEM_DESC', votar(primeiras))
                for placa in votar_listas([placas(t) for t in descs]):
                    _add('ITEM_PLACA', placa)
                # A frase da mão de obra fica no pé da caixa, sob marca-texto:
                # um recorte só do terço inferior a lê melhor que a caixa toda.
                pe = _ler_caixa(img, (0, y_ini + int((y_fim - y_ini) * 0.6), quant['left'] - 15, y_fim))
                for t in descs + pe:
                    m = re.search(r'(\w*)[ \t]*FORNEC\w*[\s-]*DE[\s-]*M[ÃA]O[\s-]*DE[\s-]*\w*BRA', t, re.IGNORECASE)
                    if m and f'{PREFIXO}ITEM_MAO_DE_OBRA: {_colapsa(m.group(0))}' not in saida:
                        _add('ITEM_MAO_DE_OBRA', _colapsa(m.group(0)))
            if periodo:
                datas = votar_listas([[norm_data(d) for d in re.findall(r'\d{2}/\d{2}/\d{4}', t) if norm_data(d)]
                                      for t in _ler_caixa(img, (periodo['left'] - 200, y_ini, periodo['left'] + periodo['width'] + 100, y_fim))])
                if len(datas) == 2:
                    _add('ITEM_PERIODO', f'{datas[0]} A {datas[1]}')
                x_val = periodo['left'] + periodo['width'] + 200
                for v in votar_listas([valores_moeda(t) for t in _ler_caixa(img, (x_val, y_ini, largura, y_fim))]):
                    _add('ITEM_VALOR', v)
            if total:
                x_tot = total['left'] + total['width']
                y0 = total['top'] - total['height'] // 2
                _add('TOTAL', votar([(valores_moeda(t) or [None])[-1]
                                     for t in _ler_caixa(img, (x_tot, y0, largura, y0 + 2 * total['height']))]))
    except (OSError, RuntimeError, ValueError, IndexError) as exc:
        logger.warning('Nota débito/fatura: recorte dos itens falhou (%s)', exc)

    return '\n'.join(saida) + ('\n' if saida else '')


# ---------------------------------------------------------------------------
# Extração (função pura sobre texto)
# ---------------------------------------------------------------------------

def _numero(corpo: str, avisos: List[str]) -> str:
    """Decisão do usuário: número da FATURA sem o ano e sem zeros à esquerda."""
    m = _RE_FATURA.search(corpo)
    m_nd = _RE_NOTA_DEBITO.search(corpo)
    if not m or not m.group(1).strip('0'):
        avisos.append("Número da FATURA não legível - mantido sentinela; conferir no documento")
        return _SENTINELA_NUMERO
    numero = str(int(m.group(1)))
    impresso = m.group(0).split(None, 1)[-1] if m else ''
    nd = f" (o documento também imprime \"NOTA DÉBITO Nº {m_nd.group(1)}\", não usado)" if m_nd else ''
    avisos.append(f"Número da nota = número da FATURA \"{_colapsa(impresso)}\" sem ano/zeros à esquerda "
                  f"-> {numero}{nd}; conferir no Domínio")
    return numero


def _data(marc: Dict[str, List[str]], chave: str, corpo: str, rotulo: str) -> Optional[datetime]:
    valor = (marc.get(chave) or [None])[0]
    if not valor:
        m = re.search(rotulo + r'[^\n]*\n+\s*[\[|]?\s*(\d{2}/\d{2}/\d{4})', corpo, re.IGNORECASE)
        valor = norm_data(m.group(1)) if m else None
    if not valor:
        return None
    d, mm, a = valor.split('/')
    return datetime(int(a), int(mm), int(d))


def _cabecalho(corpo: str) -> str:
    m = re.search(r'DATA\s+EMISS|NATUREZA\s+DA\s+OPERA|TOMADOR\s+DO\s+SERVI', corpo, re.IGNORECASE)
    return corpo[:m.start()] if m else corpo


_RE_EMITENTE = re.compile(
    r"^[ \t]*(?P<razao>[A-ZÀ-Ú][A-ZÀ-Ú0-9&.' -]{3,}?)[ \t]*\n+[ \t]*CNPJ\s*:?\s*(?P<doc>[\d.,/ -]{14,22})",
    re.MULTILINE)
_RE_CIDADE_CEP = re.compile(
    r'^[ \t]*(?P<cidade>[A-ZÀ-Ú][A-ZÀ-Ú\' .]+?)\s*[,-]\s*(?P<uf>[A-Z]{2})\b\s*CEP\s*:?\s*(?P<cep>\d{2}[.,]?\d{3}[-.,]?\d{3})',
    re.IGNORECASE | re.MULTILINE)
_RE_TELEFONE = re.compile(r'TEL\w*\s*:?\s*\(?(\d{2})\)?\s*(\d{4,5})\s*-?\s*(\d{4})', re.IGNORECASE)


def _prestador(corpo: str, resolver, validar_doc, cnpj_tomador: str, avisos: List[str]) -> Entidade:
    cab = _cabecalho(corpo)
    m = _RE_EMITENTE.search(cab)
    razao = _colapsa(m.group('razao')) if m else ''
    doc = re.sub(r'\D', '', m.group('doc')) if m else ''
    if len(doc) != 14 or doc == cnpj_tomador or not validar_doc(doc):
        avisos.append("CNPJ do emitente não legível no OCR com dígito verificador válido - "
                      "mantido sentinela; conferir no documento")
        doc = _SENTINELA_DOC
    if not razao:
        avisos.append("Razão social do emitente não encontrada no letterhead - conferir no documento")
        razao = 'Prestador Não Identificado'

    endereco_raw = ''
    if m:
        for linha in cab[m.end():].splitlines():
            linha = _colapsa(linha)
            if not linha:
                continue
            if _RE_CIDADE_CEP.match(linha) or re.match(r'(?:E-?MAIL|TEL)', linha, re.IGNORECASE):
                break
            if re.search(r'\d', linha) and len(re.findall(r'[A-Za-zÀ-ú]{3,}', linha)) >= 2:
                endereco_raw = linha
                break
    logradouro, numero, bairro = separar_endereco(endereco_raw)

    m_cid = _RE_CIDADE_CEP.search(cab)
    municipio = uf = cep = ''
    if m_cid:
        municipio = _colapsa(m_cid.group('cidade'))
        uf = m_cid.group('uf').upper()
        cep = re.sub(r'\D', '', m_cid.group('cep'))
    cod_mun = resolver.extract_and_validate(municipio, uf or 'BA', city_hint=municipio) if municipio else ''
    if not municipio:
        avisos.append("Município do emitente não encontrado no letterhead - conferir no documento")
    m_tel = _RE_TELEFONE.search(cab)

    return Entidade(
        cnpj_cpf=doc, razao_social=razao, telefone=''.join(m_tel.groups()) if m_tel else None,
        endereco=Endereco(logradouro=logradouro, numero=numero, bairro=bairro or 'Não informado',
                          codigo_municipio=cod_mun, municipio=municipio or None, uf=uf,
                          cep=cep if len(cep) == 8 else '00000000'))


def _tomador(marc: Dict[str, List[str]], resolver, validar_doc, avisos: List[str]) -> Entidade:
    def campo(chave: str) -> str:
        return _colapsa((marc.get('TOM_' + chave) or [''])[0])

    razao = campo('NOME').strip(' |[]')
    if not razao:
        avisos.append("Razão social do tomador não legível no OCR - conferir no documento")
        razao = 'Tomador Não Identificado'
    doc = re.sub(r'\D', '', campo('CNPJ'))
    if len(doc) != 14 or not validar_doc(doc):
        avisos.append("CNPJ do tomador não legível no OCR com dígito verificador válido - "
                      "mantido sentinela; conferir no documento")
        doc = _SENTINELA_DOC
    logradouro, numero, compl = separar_endereco(campo('ENDERECO'))
    if compl:
        logradouro = f'{logradouro} {numero} {compl}' if numero != 'S/N' else f'{logradouro} {compl}'
        numero = 'S/N'
    bairro = campo('BAIRRO')
    municipio = campo('MUNICIPIO')
    uf = campo('UF').upper()[:2]
    if municipio and not uf:
        avisos.append("UF do tomador não legível no OCR - assumida BA; conferir no documento")
    cod_mun = resolver.extract_and_validate(municipio, uf or 'BA', city_hint=municipio) if municipio else ''
    if not municipio:
        avisos.append("Município do tomador não legível no OCR - conferir no documento")
    cep = re.sub(r'\D', '', campo('CEP'))
    return Entidade(
        cnpj_cpf=doc, razao_social=razao,
        endereco=Endereco(logradouro=logradouro, numero=numero, bairro=bairro or 'Não informado',
                          codigo_municipio=cod_mun, municipio=municipio or None, uf=uf or ('BA' if municipio else ''),
                          cep=cep if len(cep) == 8 else '00000000'))


def _mao_de_obra(marc: Dict[str, List[str]], corpo: str) -> Tuple[Optional[str], Optional[str]]:
    """Frase fixa "SEM/COM FORNECIMENTO DE MÃO DE OBRA" da grade de itens ->
    (frase, aviso). A marcação de marca-texto sobre o impresso cobre o "SEM"
    no OCR (lido como "", "e", "em" ou lixo). Regra: qualquer leitura "COM"
    -> COM; senão, uma leitura com fragmento compatível com "SEM" (vazio,
    "E", "EM", "SE", "SEM") -> SEM, com aviso quando o "SEM" não foi lido por
    inteiro. Sem nenhuma leitura decisiva: None (a frase fica fora)."""
    prefixos = []
    for txt in marc.get('ITEM_MAO_DE_OBRA', []) + [corpo]:
        for m in re.finditer(r'(\w*)[ \t]*FORNEC\w*[\s-]*DE[\s-]*M[ÃA]O[\s-]*DE[\s-]*\w*BRA', txt or '', re.IGNORECASE):
            prefixos.append(_sem_acento(m.group(1)).upper())
    if 'COM' in prefixos:
        return 'COM FORNECIMENTO DE MÃO DE OBRA', None
    if 'SEM' in prefixos:
        return 'SEM FORNECIMENTO DE MÃO DE OBRA', None
    if any(p in ('', 'E', 'EM', 'SE', 'M') for p in prefixos):
        return 'SEM FORNECIMENTO DE MÃO DE OBRA', (
            "Frase \"SEM FORNECIMENTO DE MÃO DE OBRA\": o \"SEM\" está sob marca-texto e não foi lido "
            "por inteiro pelo OCR (lido só \"... FORNECIMENTO DE MÃO DE OBRA\") - conferir no documento")
    return None, None


def extrair(texto: str, resolver, validar_doc: Callable[[str], bool], via_ocr: bool = False) -> NotaLocacao:
    """Extrai a nota débito/fatura. Devolve o mesmo `NotaLocacao` do layout
    irmão (`nota_locacao.py`), consumido pelos mesmos pontos do extrator."""
    avisos: List[str] = []
    marc = ler_marcadores(texto)
    corpo = _sem_marcadores(texto)

    numero = _numero(corpo, avisos)
    data = _data(marc, 'EMISSAO', corpo, r'DATA\s+EMISS[ÃA]O')
    tomador = _tomador(marc, resolver, validar_doc, avisos)
    prestador = _prestador(corpo, resolver, validar_doc, tomador.cnpj_cpf, avisos)

    desc = (marc.get('ITEM_DESC') or [''])[0]
    if not desc:
        m = re.search(r'DESCRI[ÇC][ÃA]O[^\n]*\n+\s*([^\n]+)', corpo, re.IGNORECASE)
        desc = _colapsa(m.group(1)) if m else ''
    placas_lidas = marc.get('ITEM_PLACA', [])
    valores_itens = [_valor_br(v) for v in marc.get('ITEM_VALOR', [])]
    itens = [ItemLocacao(descricao=f'{desc} {p}'.strip(),
                         valor_total=valores_itens[i] if len(valores_itens) == len(placas_lidas) else None)
             for i, p in enumerate(placas_lidas)] or ([ItemLocacao(descricao=desc)] if desc else [])

    partes = [desc] if desc else []
    if placas_lidas:
        if len(valores_itens) == len(placas_lidas):
            partes.append('PLACAS ' + ' / '.join(f'{p} R$ {_fmt_br(v)}' for p, v in zip(placas_lidas, valores_itens)))
        else:
            partes.append('PLACAS ' + ' / '.join(placas_lidas))
    periodo = (marc.get('ITEM_PERIODO') or [''])[0]
    if periodo:
        partes.append(f'PERÍODO {periodo}')
    mao, aviso_mao = _mao_de_obra(marc, corpo)
    if mao:
        partes.append(mao)
    if aviso_mao:
        avisos.append(aviso_mao)
    discriminacao = ' - '.join(partes)
    if not desc:
        avisos.append("Descrição do item não encontrada - conferir no documento")
        discriminacao = discriminacao or 'NOTA DÉBITO / FATURA DE LOCAÇÃO'

    total_txt = (marc.get('TOTAL') or [None])[0]
    if not total_txt:
        m_tot = re.search(r'TOTAL\s+DA\s+FATURA\s*:?\s*(?:R\$\s*)?(' + _MONEY + r')', corpo, re.IGNORECASE)
        total_txt = m_tot.group(1) if m_tot else None
    total = _valor_br(total_txt) if total_txt else None
    soma = round(sum(valores_itens), 2) if valores_itens else None
    if total is not None and soma is not None and abs(total - soma) > 0.011:
        avisos.append(f"TOTAL DA FATURA ({_fmt_br(total)}) diverge da soma dos itens ({_fmt_br(soma)}) - "
                      "mantido o total impresso; conferir no documento")
    if total is None and soma is not None:
        total = soma
        avisos.append("\"TOTAL DA FATURA\" ilegível no OCR (marca-texto sobre o valor) - valor "
                      f"tomado da soma dos totais dos itens ({_fmt_br(soma)}); conferir no documento")
    valor = total or 0.0
    valores = Valores(valor_servicos=valor, valor_liquido_nfse=valor,
                      base_calculo=0.0, aliquota=0.0, valor_iss=0.0)

    optante = bool(re.search(r'OPTANTE\s+(?:PELO|DO)\s+SIMPLES\s+NACIONAL', corpo, re.IGNORECASE))

    avisos.append(
        "Documento é NOTA DÉBITO / FATURA de locação de bem móvel (não é NFS-e): operação fora do "
        "campo de incidência do ISS (a própria nota declara \"NÃO SUJEITO A I.S.S.\" - LC 116/2003). "
        "XML gerado na convenção das faturas de locação: ISS/base/alíquota zerados, item 0601 e "
        "código de verificação \"FATURA\"; conferir o lançamento no Domínio")
    if via_ocr and placas_lidas:
        avisos.append(f"Placas na discriminação lidas por OCR ({', '.join(placas_lidas)}) - o OCR "
                      "confunde letra/dígito em placas (B/8, I/1, O/0); conferir no documento")

    return NotaLocacao(numero=numero, data_emissao=data, discriminacao=discriminacao,
                       prestador=prestador, tomador=tomador, valores=valores, itens=itens,
                       optante_simples=optante, avisos=avisos)
