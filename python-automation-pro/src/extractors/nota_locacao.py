"""Helpers do impresso "NOTA DE LOCAÇÃO" (locação de bens móveis, NÃO é NFS-e).

Achado real 2026-10-16 (lote STAUMMAQ, `Scan2026-10-16_110738.pdf`, pág. 10):
ELEVAR LOCACAO E TRANSPORTES LTDA (CNPJ 22.471.804/0001-01, Dias d'Ávila/BA)
-> STAUMMAQ SERV TEC AUT MOTORES E MAQ LTDA (Simões Filho/BA), "NOTA DE
LOCAÇÃO Nº 1245", locação de caminhão munck, R$ 18.500,00. Antes deste módulo a
página caía em LAYOUT_GENERICO e era descartada ("Layout não reconhecido"):
nenhum XML.

Estrutura do impresso (modelo de gráfica, sem prefeitura nem plataforma):
  * letterhead do emitente (razão social / endereço / "<CIDADE>-<UF> Cep:" /
    "Tel:") à esquerda; caixa "NOTA DE LOCAÇÃO Nº <n>" + "C.N.P.J" + "INSCR.
    EST." + "DATA DE EMISSÃO" à direita;
  * bloco "DESTINATÁRIO" em grade (rótulos numa linha, valores na linha de
    baixo, colunas por posição horizontal);
  * "DADOS DO DOCUMENTO": DESCRIÇÃO | QUANTIDADE | VLR.UNITÁRIO | VALOR TOTAL;
  * "VALOR TOTAL DA NOTA DE LOCAÇÃO" e "INFORMAÇÕES ADICIONAIS" (a própria
    nota declara: operação não sujeita a documento fiscal - Lei 8.846/94 - e
    não incidência de ISS - LC 116/2003 não lista locação de bens móveis).

A detecção é ESTRUTURAL (título + bloco DESTINATÁRIO + rótulo do total), não
pelo nome da ELEVAR: outra locadora que use o mesmo modelo de impresso cai aqui
e tem o emitente lido do próprio letterhead.

O OCR de página inteira deste scan perde campos inteiros: o CNPJ e a I.E. do
emitente (a caixa da direita some), o rótulo "DATA DE EMISSÃO" (vira "audi"),
as colunas QUANTIDADE/VALOR TOTAL do item, e lê o "I" de "VIA URBANA I" como
"|" (que também é separador de coluna). Por isso `recortar` (chamado pelo
`_ocr_page`) devolve linhas SINTÉTICAS `NOTALOC_*` - mesma técnica do
`feira_nfse_nacional.py` - que são PREPENDIDAS ao texto da página:
  * `NOTALOC_CAB:`  linhas do recorte da caixa da direita do cabeçalho;
  * `NOTALOC_ITEM:` linhas do recorte da grade "DADOS DO DOCUMENTO";
  * `NOTALOC_DEST_<CAMPO>:` valores do bloco DESTINATÁRIO, atribuídos à coluna
    pela posição horizontal do rótulo (`image_to_data`), não pela ordem do
    texto.
Nenhuma dessas linhas contém rótulo real que o split de notas do
`parse_multiple` reconheça. `extrair` é função pura sobre o texto (testável
sem PDF nem OCR); sem os marcadores (PDF digital, recorte falhou) cai no texto
de página inteira, e o que não for legível vira sentinela + aviso.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple

from ..models.nfse_models import Endereco, Entidade, Valores

logger = logging.getLogger(__name__)

PREFIXO = 'NOTALOC_'

# Convenções do projeto para faturas/notas de locação de bens móveis (mesmas
# da família LAYOUT_LOCALIZA/LAYOUT_FATURA_LOCACAO_GENERICA/ARMAC/...): item
# "0601" e código de verificação "FATURA" (documento sem código de
# verificação); base/alíquota/ISS zerados.
ITEM_LOCACAO = '0601'
CODIGO_VERIFICACAO = 'FATURA'

_SENTINELA_DOC = '00000000000000'
_SENTINELA_NUMERO = '00000000'

_MONEY = r'\d{1,3}(?:\.\d{3})*,\d{2}'
_RE_TITULO = re.compile(r'NOTA\s*DE\s*LOCA[ÇC][ÃA]O\s*N\s*[º°oO.]{0,2}\s*(\d{1,10})\b', re.IGNORECASE)
_RE_TOTAL = re.compile(
    r'VALOR\s+TOTAL\s+DA\s+NOTA\s+DE\s+LOCA[ÇC][ÃA]O\s*:?\s*\n?\s*(?:R\$\s*)?(' + _MONEY + r')', re.IGNORECASE)
_RE_CNPJ = re.compile(r'\d{2}\.?\d{3}\.?\d{3}\s*/\s*\d{4}\s*-?\s*\d{2}')
_RE_DATA = re.compile(r'\b(\d{2})/(\d{2})/(\d{4})\b')
_RE_DESTINATARIO = re.compile(r'DESTINAT[ÁA]RIO', re.IGNORECASE)
# Sufixo societário que fecha a linha da razão social no letterhead.
_RE_RAZAO = re.compile(
    r'^[ \t]*([A-ZÀ-Ú0-9&][A-ZÀ-Ú0-9&.,\'/ -]{3,}?\b(?:LTDA|S\.?\s?/?\s?A\.?|EIRELI|EPP|ME|MEI)\.?)[ \t]*$',
    re.MULTILINE)
_RE_CIDADE_CEP = re.compile(
    r'^[ \t]*(?P<cidade>[A-ZÀ-Ú][A-ZÀ-Ú\' .]+?)\s*-\s*(?P<uf>[A-Z]{2})\b\s*Cep\s*:?\s*(?P<cep>\d{2}\.?\d{3}-?\d{3})',
    re.IGNORECASE | re.MULTILINE)
_RE_TELEFONE = re.compile(r'Tel\w*\s*:?\s*\(?(\d{2})\)?\s*(\d{4,5})\s*-?\s*(\d{4})', re.IGNORECASE)
_RE_ANOTACAO = re.compile(r'VENCIMENTO', re.IGNORECASE)


@dataclass
class ItemLocacao:
    descricao: str
    quantidade: Optional[float] = None
    valor_unitario: Optional[float] = None
    valor_total: Optional[float] = None


@dataclass
class NotaLocacao:
    numero: str
    data_emissao: Optional[datetime]
    discriminacao: str
    prestador: Entidade
    tomador: Entidade
    valores: Valores
    itens: List[ItemLocacao] = field(default_factory=list)
    optante_simples: bool = False
    avisos: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Detecção
# ---------------------------------------------------------------------------

def eh_nota_locacao(texto: str) -> bool:
    """True para o impresso "NOTA DE LOCAÇÃO".

    Exige as 3 âncoras estruturais do modelo: o título "NOTA DE LOCAÇÃO Nº
    <número>", o bloco "DESTINATÁRIO" e o rótulo "VALOR TOTAL DA NOTA DE
    LOCAÇÃO". Uma NFS-e/nota fiscal que só CITE uma "nota de locação" (ex.:
    "Número da Nota de Locação:" da fatura CPE) não tem as três; e qualquer
    documento que se declare NFS-e/Nota Fiscal Eletrônica fica fora."""
    if not texto:
        return False
    if not _RE_TITULO.search(texto):
        return False
    if not _RE_DESTINATARIO.search(texto):
        return False
    if not re.search(r'VALOR\s+TOTAL\s+DA\s+NOTA\s+DE\s+LOCA[ÇC][ÃA]O', texto, re.IGNORECASE):
        return False
    if re.search(r'\bNFS-?e\b|Nota\s+Fiscal\s+(?:Eletr|de\s+Servi)|DANFS', texto, re.IGNORECASE):
        return False
    return True


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def _sem_acento(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', s or '') if unicodedata.category(c) != 'Mn')


def _colapsa(s: str) -> str:
    return re.sub(r'\s+', ' ', s or '').strip()


def _valor_br(s: str) -> float:
    return float(s.replace('.', '').replace(',', '.'))


def ler_marcadores(texto: str) -> Dict[str, List[str]]:
    """Linhas `NOTALOC_<CHAVE>: <valor>` -> {CHAVE: [valores]}."""
    saida: Dict[str, List[str]] = {}
    for m in re.finditer(r'^NOTALOC_([A-Z_]+):[ \t]*(.*)$', texto or '', re.MULTILINE):
        saida.setdefault(m.group(1), []).append(m.group(2).strip())
    return saida


def _sem_marcadores(texto: str) -> str:
    return re.sub(r'^NOTALOC_[A-Z_]+:.*\n?', '', texto or '', flags=re.MULTILINE)


def _cabecalho(texto: str) -> str:
    """Texto antes do bloco DESTINATÁRIO (letterhead + caixa do número)."""
    m = _RE_DESTINATARIO.search(texto)
    return texto[:m.start()] if m else ''


def separar_endereco(raw: str) -> Tuple[str, str, Optional[str]]:
    """"VIA DE LIGAÇÃO 614 LOT JARDIM ALVORADA PARQUE PETROPOLIS" ->
    ("VIA DE LIGAÇÃO", "614", "LOT JARDIM ALVORADA PARQUE PETROPOLIS").

    O letterhead não separa número/bairro por vírgula: o 1º número isolado é o
    número do imóvel e o resto vai como bairro (sem tentar adivinhar onde
    termina um complemento - nada se perde). Sem número: "S/N"."""
    norm = _colapsa(raw).strip(' ,-')
    if not norm:
        return 'Não informado', 'S/N', None
    m = re.match(r'^(.+?)[\s,]+(\d{1,6}[A-Za-z]?|S/?N)\b[\s,-]*(.*)$', norm, re.IGNORECASE)
    if not m:
        return norm, 'S/N', None
    return m.group(1).strip(' ,'), m.group(2).upper(), (m.group(3).strip(' ,-') or None)


# ---------------------------------------------------------------------------
# Recortes (OCR) - chamados por `SPPdfExtractor._ocr_page`
# ---------------------------------------------------------------------------

def _palavras(img) -> List[dict]:
    import pytesseract
    d = pytesseract.image_to_data(img, lang='por', output_type=pytesseract.Output.DICT)
    saida = []
    for i, txt in enumerate(d['text']):
        txt = (txt or '').strip()
        if not txt:
            continue
        saida.append({
            'txt': txt, 'norm': _sem_acento(txt).upper().strip(':.;,'),
            'left': d['left'][i], 'top': d['top'][i],
            'width': d['width'][i], 'height': d['height'][i],
        })
    return saida


def _primeira(palavras: List[dict], norm: str, top_min: int = -1, prefixo: bool = False) -> Optional[dict]:
    for p in palavras:
        if p['top'] > top_min and (p['norm'].startswith(norm) if prefixo else p['norm'] == norm):
            return p
    return None


def _ocr_linhas(img, caixa: Tuple[int, int, int, int], psm: int) -> List[str]:
    import pytesseract
    x0, y0, x1, y1 = caixa
    if x1 - x0 < 20 or y1 - y0 < 10:
        return []
    texto = pytesseract.image_to_string(img.crop(caixa), lang='por', config=f'--psm {psm}')
    return [_colapsa(l) for l in texto.splitlines() if _colapsa(l)]


def _ocr_linhas_com_y(img, caixa: Tuple[int, int, int, int]) -> List[Tuple[int, int, str]]:
    """(topo, altura, texto) de cada linha do recorte (PSM 6)."""
    import pytesseract
    x0, y0, x1, y1 = caixa
    if x1 - x0 < 20 or y1 - y0 < 10:
        return []
    d = pytesseract.image_to_data(img.crop(caixa), lang='por', config='--psm 6',
                                  output_type=pytesseract.Output.DICT)
    linhas: Dict[Tuple[int, int, int], List[int]] = {}
    for i, txt in enumerate(d['text']):
        if (txt or '').strip():
            linhas.setdefault((d['block_num'][i], d['par_num'][i], d['line_num'][i]), []).append(i)
    saida = []
    for idxs in linhas.values():
        topo = min(d['top'][i] for i in idxs)
        alturas = sorted(d['height'][i] for i in idxs)
        saida.append((topo, alturas[len(alturas) // 2], ' '.join(d['text'][i].strip() for i in idxs)))
    return sorted(saida)


def linhas_contiguas(linhas: List[Tuple[int, int, str]], fator: float = 2.5) -> List[str]:
    """Só o bloco de texto CONTÍGUO do topo da grade de itens.

    A descrição do item é um parágrafo compacto logo abaixo do cabeçalho da
    grade; o que vem depois de um vão vertical grande (> `fator` x a altura da
    linha) é anotação feita sobre o documento (carimbo "VENCIMENTO: ...",
    rubrica), nunca dado da nota. Função pura."""
    saida: List[str] = []
    fundo_anterior = altura_anterior = None
    for topo, altura, txt in sorted(linhas):
        # O vão é medido pela altura da linha ANTERIOR (texto normal): a da
        # linha corrente pode ser enorme (o oval do carimbo vira "palavra").
        if fundo_anterior is not None and topo - fundo_anterior > fator * max(altura_anterior, 1):
            break
        saida.append(_colapsa(txt))
        fundo_anterior, altura_anterior = topo + altura, altura
    return [l for l in saida if l]


# Rótulos de cada linha de rótulos do bloco DESTINATÁRIO -> campo.
_GRADE_DEST = (
    (('NOME', 'NOME'), ('CNPJ', 'CNPJ')),
    (('ENDERECO', 'ENDERECO'), ('BAIRRO', 'BAIRRO'), ('CEP', 'CEP')),
    (('MUNICIPIO', 'MUNICIPIO'), ('UF', 'UF'), ('TELEFONE', 'TELEFONE'), ('INSCRICAO', 'IE')),
)


def destinatario_por_colunas(palavras: List[dict], largura: int) -> List[str]:
    """Valores do bloco DESTINATÁRIO atribuídos por COLUNA.

    Cada linha de rótulos ("Nome / Razão Social | CNPJ / CPF", "Endereço |
    Bairro | CEP", "Município | UF | Telefone / Fax | INSCRIÇÃO ESTADUAL")
    define o x inicial de cada coluna; as palavras entre essa linha e a
    próxima vão para a coluna cujo início é o maior x <= x da palavra. Um "|"
    solto colado à borda de uma coluna é a linha da grade (descartado); dentro
    da coluna é o glifo "I" (ex.: "VIA URBANA I"), lido como "|" pelo OCR.
    Função pura sobre a lista de palavras do `image_to_data`."""
    ancora = _primeira(palavras, 'DESTINATARIO')
    if not ancora:
        return []
    fim_bloco = _primeira(palavras, 'DOCUMENTO', ancora['top'])
    y_fim = fim_bloco['top'] if fim_bloco else None
    tol = max(8, int(largura * 0.012))

    linhas_rotulo = []
    for grupo in _GRADE_DEST:
        cols = []
        for norm, campo in grupo:
            p = next((w for w in palavras if w['norm'] == norm and w['top'] > ancora['top']
                      and (y_fim is None or w['top'] < y_fim)), None)
            if p:
                cols.append((p['left'], campo, p))
        if cols:
            topo = min(c[2]['top'] for c in cols)
            base = max(c[2]['top'] + c[2]['height'] for c in cols)
            linhas_rotulo.append((topo, base, sorted(cols, key=lambda c: c[0])))
    linhas_rotulo.sort(key=lambda l: l[0])

    rotulos_ids = {id(c[2]) for l in linhas_rotulo for c in l[2]}
    saida: List[str] = []
    for i, (_topo, base, cols) in enumerate(linhas_rotulo):
        limite = linhas_rotulo[i + 1][0] if i + 1 < len(linhas_rotulo) else (y_fim or base + 4 * (base - _topo))
        valores: Dict[str, List[dict]] = {}
        for w in palavras:
            if id(w) in rotulos_ids or not (base - 2 <= w['top'] < limite - 2):
                continue
            cand = [c for c in cols if c[0] <= w['left'] + tol]
            if not cand:
                continue
            col = cand[-1]
            if w['txt'] == '|' and any(c[0] - 3 * tol <= w['left'] < c[0] - 1 for c in cols):
                continue  # borda vertical da grade, logo à esquerda do rótulo da coluna
            valores.setdefault(col[1], []).append(w)
        for _x, campo, _p in cols:
            ws = sorted(valores.get(campo, []), key=lambda w: (round(w['top'] / max(1, tol)), w['left']))
            txt = ' '.join('I' if w['txt'] == '|' else w['txt'] for w in ws).strip()
            if txt:
                saida.append(f'{PREFIXO}DEST_{campo}: {txt}')
    return saida


def recortar(img, texto_base: str) -> str:
    """Linhas sintéticas `NOTALOC_*` (ver docstring do módulo).

    `img` é a página renderizada (PIL), já na orientação vencedora do OCR.
    Cada recorte é independente: a falha de um só o omite (o extrator cai no
    texto de página inteira ou em sentinela + aviso)."""
    try:
        palavras = _palavras(img)
    except (OSError, RuntimeError, ValueError, ImportError) as exc:
        logger.warning('Nota de locação: recortes indisponíveis (%s)', exc)
        return ''
    largura, altura = img.size
    saida: List[str] = []

    dest = _primeira(palavras, 'DESTINATARIO')
    nota = next((p for p in palavras if p['norm'].startswith('NOTA')
                 and (dest is None or p['top'] < dest['top'])), None)
    try:
        if dest and nota:
            x0 = max(0, nota['left'] - int(largura * 0.02))
            # PSM 4 (colunas de texto variável): o PSM 6 junta "I.E. + data"
            # numa linha e às vezes perde a data; o 4 lê rótulo e valor soltos.
            for linha in _ocr_linhas(img, (x0, 0, largura, dest['top']), psm=4):
                saida.append(f'{PREFIXO}CAB: {linha}')
    except (OSError, RuntimeError, ValueError) as exc:
        logger.warning('Nota de locação: recorte do cabeçalho falhou (%s)', exc)

    try:
        doc = _primeira(palavras, 'DOCUMENTO', dest['top'] if dest else -1)
        y_ini = doc['top'] + doc['height'] if doc else None
        total = None
        if y_ini is not None:
            for i, p in enumerate(palavras):
                if p['norm'] == 'VALOR' and p['top'] > y_ini and i + 2 < len(palavras) \
                        and palavras[i + 1]['norm'] == 'TOTAL' and palavras[i + 2]['norm'] == 'DA':
                    total = p
                    break
        if y_ini is not None and total:
            for linha in linhas_contiguas(_ocr_linhas_com_y(img, (0, y_ini, largura, total['top'] - 2))):
                saida.append(f'{PREFIXO}ITEM: {linha}')
    except (OSError, RuntimeError, ValueError) as exc:
        logger.warning('Nota de locação: recorte dos itens falhou (%s)', exc)

    saida.extend(destinatario_por_colunas(palavras, largura))
    return '\n'.join(saida) + ('\n' if saida else '')


# ---------------------------------------------------------------------------
# Extração (função pura sobre texto)
# ---------------------------------------------------------------------------

def _numero(corpo: str, marc: Dict[str, List[str]], avisos: List[str]) -> str:
    m = _RE_TITULO.search(corpo)
    principal = m.group(1) if m else None
    m_cab = _RE_TITULO.search('\n'.join(marc.get('CAB', [])))
    recorte = m_cab.group(1) if m_cab else None
    if principal and recorte and principal != recorte:
        avisos.append(f"Número da nota de locação divergente entre leituras do OCR "
                      f"({principal} x {recorte}) - mantido sentinela; conferir no documento")
        return _SENTINELA_NUMERO
    return principal or recorte or _SENTINELA_NUMERO


def _data_emissao(corpo: str, marc: Dict[str, List[str]]) -> Optional[datetime]:
    """Rótulo "DATA DE EMISSÃO" -> data; sem rótulo legível, a ÚNICA data da
    caixa do cabeçalho (o modelo não imprime outra data ali). Datas distintas
    sem rótulo: None (o extrator usa o fallback com aviso)."""
    for fonte in ('\n'.join(marc.get('CAB', [])), _cabecalho(corpo)):
        if not fonte:
            continue
        m = re.search(r'DATA\s+DE\s+EMISS[ÃA]O[\s:]*(\d{2}/\d{2}/\d{4})', fonte, re.IGNORECASE)
        datas = {m.group(1)} if m else {f'{d}/{mm}/{a}' for d, mm, a in _RE_DATA.findall(fonte)}
        if len(datas) == 1:
            d, mm, a = next(iter(datas)).split('/')
            try:
                return datetime(int(a), int(mm), int(d))
            except ValueError:
                return None
        if len(datas) > 1:
            return None
    return None


def _prestador(corpo: str, marc: Dict[str, List[str]], resolver, validar_doc,
               cnpj_tomador: str, avisos: List[str]) -> Entidade:
    cab = _cabecalho(corpo)

    doc = None
    for fonte in ('\n'.join(marc.get('CAB', [])), cab):
        for m in _RE_CNPJ.finditer(fonte):
            d = re.sub(r'\D', '', m.group(0))
            if d != cnpj_tomador and validar_doc(d):
                doc = d
                break
        if doc:
            break
    if not doc:
        avisos.append("CNPJ do emitente (locador) não legível no OCR com dígito verificador válido - "
                      "mantido sentinela; conferir no documento")
        doc = _SENTINELA_DOC

    m_razao = _RE_RAZAO.search(cab)
    razao = _colapsa(m_razao.group(1)) if m_razao else ''
    if not razao:
        avisos.append("Razão social do emitente (locador) não encontrada no letterhead - conferir no documento")
        razao = 'Prestador Não Identificado'

    endereco_raw = ''
    if m_razao:
        for linha in cab[m_razao.end():].splitlines():
            linha = _colapsa(linha)
            if not linha:
                continue
            if _RE_CIDADE_CEP.match(linha) or re.match(r'Tel', linha, re.IGNORECASE):
                break
            # Corta o que a leitura em linha inteira cola da caixa da direita.
            linha = re.split(r'\s+(?:\d{2}/\d{2}/\d{4}|INSCR)', linha, maxsplit=1)[0]
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
    cod_mun = ''
    if municipio:
        cod_mun = resolver.extract_and_validate(municipio, uf or 'BA', city_hint=municipio)
    else:
        avisos.append("Município do emitente (locador) não encontrado no letterhead - conferir no documento")

    m_tel = _RE_TELEFONE.search(cab)
    telefone = ''.join(m_tel.groups()) if m_tel else None

    return Entidade(
        cnpj_cpf=doc, razao_social=razao, telefone=telefone,
        endereco=Endereco(
            logradouro=logradouro, numero=numero, bairro=bairro or 'Não informado',
            codigo_municipio=cod_mun, municipio=municipio or None, uf=uf,
            cep=cep if len(cep) == 8 else '00000000'),
    )


def _tomador_texto(corpo: str) -> Dict[str, str]:
    """Fallback sem marcadores: grade DESTINATÁRIO do texto de página inteira."""
    campos: Dict[str, str] = {}
    m = re.search(r'Nome\s*/\s*Raz[ãa]o\s+Social[^\n]*\n+\s*([^\n]+)', corpo, re.IGNORECASE)
    if m:
        linha = m.group(1)
        m_doc = _RE_CNPJ.search(linha) or re.search(r'\d{3}\.?\d{3}\.?\d{3}-?\d{2}', linha)
        if m_doc:
            campos['CNPJ'] = m_doc.group(0)
            linha = linha[:m_doc.start()]
        campos['NOME'] = linha
    m = re.search(r'Endere[çc]o\s+Bairro\s+CEP[^\n]*\n+\s*([^\n]+)', corpo, re.IGNORECASE)
    if m:
        linha = m.group(1)
        m_cep = re.search(r'(\d{2}\.?\d{3}-?\d{3})\s*$', linha)
        if m_cep:
            campos['CEP'] = m_cep.group(1)
            linha = linha[:m_cep.start()]
        # Endereço e bairro na mesma linha, sem separador confiável: tudo no
        # logradouro (o bairro fica "Não informado" + aviso).
        campos['ENDERECO'] = linha
    m = re.search(r'Munic[íi]pio\s+UF[^\n]*\n+\s*([^\n]+?)\s+([A-Z]{2})\b', corpo)
    if m:
        campos['MUNICIPIO'], campos['UF'] = m.group(1), m.group(2)
    return campos


def _tomador(corpo: str, marc: Dict[str, List[str]], resolver, validar_doc, avisos: List[str]) -> Entidade:
    campos = {k[5:]: v[0] for k, v in marc.items() if k.startswith('DEST_') and v}
    if not campos:
        campos = _tomador_texto(corpo)
    razao = _colapsa(campos.get('NOME', '')).strip(' |')
    if not razao:
        avisos.append("Razão social do destinatário (tomador) não encontrada - conferir no documento")
        razao = 'Tomador Não Identificado'

    doc_raw = campos.get('CNPJ', '')
    doc = re.sub(r'\D', '', doc_raw)
    if len(doc) not in (11, 14):
        if doc:
            avisos.append(f"CNPJ/CPF do destinatário ({doc_raw.strip()}) com tamanho inválido - "
                          "mantido sentinela; conferir no documento")
        doc = _SENTINELA_DOC
    elif not validar_doc(doc):
        avisos.append(f"CNPJ/CPF do destinatário ({doc}) não passa na validação do dígito "
                      "verificador - mantido como lido; conferir no documento")

    logradouro, numero, compl = separar_endereco(campos.get('ENDERECO', ''))
    if compl:
        logradouro = f'{logradouro} {numero} {compl}' if numero != 'S/N' else f'{logradouro} {compl}'
        numero = 'S/N'
    bairro = _colapsa(campos.get('BAIRRO', ''))
    if campos.get('ENDERECO') and not bairro:
        avisos.append("Bairro do destinatário não separado do endereço na leitura - conferir no documento")
    municipio = _colapsa(campos.get('MUNICIPIO', ''))
    uf = _colapsa(campos.get('UF', '')).upper()[:2]
    cod_mun = resolver.extract_and_validate(municipio, uf or 'BA', city_hint=municipio) if municipio else ''
    if not municipio:
        avisos.append("Município do destinatário (tomador) não encontrado - conferir no documento")
    cep = re.sub(r'\D', '', campos.get('CEP', ''))

    return Entidade(
        cnpj_cpf=doc, razao_social=razao,
        endereco=Endereco(
            logradouro=logradouro, numero=numero, bairro=bairro or 'Não informado',
            codigo_municipio=cod_mun, municipio=municipio or None, uf=uf,
            cep=cep if len(cep) == 8 else '00000000'),
    )


_RE_LINHA_ITEM = re.compile(
    r'^(?P<desc>.*?)\s*(?:(?P<qtd>\d{1,6}(?:,\d{1,4})?)\s+)?(?P<unit>' + _MONEY + r')(?:\s+(?P<total>' + _MONEY + r'))?\s*$')


def _linha_util(linha: str) -> bool:
    """Linha de descrição do item - descarta cabeçalho da grade, carimbo
    "VENCIMENTO: dd/mm/aaaa" (anotação, não dado da nota) e ruído de rubrica."""
    if re.search(r'DESCRI[ÇC][ÃA]O|QUANTIDADE|VLR\.?\s*UNIT|VALOR\s+TOTAL|DADOS\s+DO\s+DOCUMENTO', linha, re.IGNORECASE):
        return False
    if _RE_ANOTACAO.search(linha):
        return False
    return len(re.findall(r'[A-Za-zÀ-ú]{3,}', linha)) >= 1 and len(linha) >= 5


def _itens(linhas: List[str]) -> List[ItemLocacao]:
    itens: List[ItemLocacao] = []
    for bruta in linhas:
        linha = _colapsa(bruta.replace('|', ' ').replace('"', ' '))
        m = _RE_LINHA_ITEM.match(linha)
        if m and m.group('desc') and re.search(r'[A-Za-zÀ-ú]{3,}', m.group('desc')):
            qtd = m.group('qtd')
            itens.append(ItemLocacao(
                descricao=_colapsa(m.group('desc')),
                quantidade=_valor_br(qtd) if qtd and ',' in qtd else (float(qtd) if qtd else None),
                valor_unitario=_valor_br(m.group('unit')),
                valor_total=_valor_br(m.group('total')) if m.group('total') else None,
            ))
            continue
        if itens and _linha_util(linha) and not re.search(_MONEY, linha):
            itens[-1].descricao = f'{itens[-1].descricao} {linha}'
    return itens


def _linhas_itens_texto(corpo: str) -> List[str]:
    m_ini = re.search(r'^[^\n]*DESCRI[ÇC][ÃA]O[^\n]*$', corpo, re.IGNORECASE | re.MULTILINE)
    m_fim = re.search(r'VALOR\s+TOTAL\s+DA\s+NOTA\s+DE\s+LOCA', corpo, re.IGNORECASE)
    if not (m_ini and m_fim and m_fim.start() > m_ini.end()):
        return []
    return [l for l in corpo[m_ini.end():m_fim.start()].splitlines() if l.strip()]


def extrair(texto: str, resolver, validar_doc: Callable[[str], bool], via_ocr: bool = False) -> NotaLocacao:
    """Extrai a nota de locação. `resolver` é o `IBGEResolver` compartilhado do
    extrator; `validar_doc` valida o DV de CNPJ/CPF; `via_ocr` liga o aviso de
    placa lida por OCR."""
    avisos: List[str] = []
    marc = ler_marcadores(texto)
    corpo = _sem_marcadores(texto)

    numero = _numero(corpo, marc, avisos)
    data = _data_emissao(corpo, marc)

    tomador = _tomador(corpo, marc, resolver, validar_doc, avisos)
    prestador = _prestador(corpo, marc, resolver, validar_doc, tomador.cnpj_cpf, avisos)

    itens = _itens(marc.get('ITEM', [])) or _itens(_linhas_itens_texto(corpo))
    if not itens:
        # Sem nenhuma linha com valor: aproveita só as linhas de descrição.
        desc = ' '.join(_colapsa(l) for l in _linhas_itens_texto(corpo) if _linha_util(_colapsa(l)))
        if desc:
            itens = [ItemLocacao(descricao=desc)]
    discriminacao = ' | '.join(i.descricao for i in itens if i.descricao)
    if not discriminacao:
        avisos.append("Descrição do item da nota de locação não encontrada - conferir no documento")
        discriminacao = 'NOTA DE LOCAÇÃO'

    m_total = _RE_TOTAL.search(corpo)
    total = _valor_br(m_total.group(1)) if m_total else None
    soma_itens = None
    if itens and all(i.valor_total is not None for i in itens):
        soma_itens = round(sum(i.valor_total for i in itens), 2)
    for i in itens:
        if i.quantidade and i.valor_unitario is not None and i.valor_total is not None \
                and abs(i.quantidade * i.valor_unitario - i.valor_total) > 0.011:
            avisos.append(f"Item \"{i.descricao[:40]}\": quantidade x unitário "
                          f"({i.quantidade * i.valor_unitario:.2f}) diverge do total impresso "
                          f"({i.valor_total:.2f}) - conferir no documento")
    if total is not None and soma_itens is not None and abs(total - soma_itens) > 0.011:
        avisos.append(f"Valor total da nota de locação ({total:.2f}) diverge da soma dos itens "
                      f"({soma_itens:.2f}) - mantido o total impresso; conferir no documento")
    if total is None and soma_itens is not None:
        total = soma_itens
        avisos.append("Rótulo \"VALOR TOTAL DA NOTA DE LOCAÇÃO\" ilegível - valor tomado da soma "
                      "dos totais dos itens; conferir no documento")
    valor = total or 0.0
    valores = Valores(valor_servicos=valor, valor_liquido_nfse=valor,
                      base_calculo=0.0, aliquota=0.0, valor_iss=0.0)

    optante = bool(re.search(r'OPTANTE\s+(?:PELO|DO)\s+SIMPLES\s+NACIONAL', corpo, re.IGNORECASE))

    avisos.append(
        "Documento é NOTA DE LOCAÇÃO de bem móvel (não é NFS-e): operação fora do campo de incidência "
        "do ISS (a própria nota declara a não incidência - LC 116/2003 - e a dispensa de documento "
        "fiscal - Lei 8.846/94). XML gerado na convenção das faturas de locação: ISS/base/alíquota "
        "zerados, item 0601 e código de verificação \"FATURA\"; conferir o lançamento no Domínio")
    if via_ocr:
        m_placa = re.search(r'PLACA\s*:?\s*([A-Z0-9]{3}\s?-?[A-Z0-9]{4})', discriminacao, re.IGNORECASE)
        if m_placa:
            avisos.append(f"Placa do veículo na discriminação lida por OCR (\"{m_placa.group(1)}\") - "
                          "o OCR confunde I/1 e O/0 em placas; conferir no documento")

    return NotaLocacao(
        numero=numero, data_emissao=data, discriminacao=discriminacao,
        prestador=prestador, tomador=tomador, valores=valores, itens=itens,
        optante_simples=optante, avisos=avisos,
    )
