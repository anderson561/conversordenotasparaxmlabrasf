"""Recortes dedicados da "FATURA / DUPLICATA" da Localiza Rent a Car escaneada.

Achado real 2026-10-21 (lote STAUMMAQ, scans de 16/10/2026: faturas
AGMTZ-11929076, AASSA-1517937 e AGMTZ-11998441). A leitura de pagina inteira
(zoom 3x) do `_ocr_page` perde, conforme a folha:

- o numero ("Nº: AASSA - 1517937" some por completo -> Numero 00000000);
- o "VALOR TOTAL" (a celula sai vazia e o valor da coluna VALOR vira
  "R$ 92443", sem virgula -> ValorServicos 0,00);
- a ordem das linhas da DESCRICAO (uma linha partida em dois pedacos, um deles
  despejado depois da placa), o que inviabiliza montar a discriminacao;
- letras do nome do cliente ("STAUMMAGQ" no lugar de "STAUMMAQ").

Os recortes abaixo sao ANCORADOS pela estrutura da propria fatura (palavras
"DUPLICATA", "CLIENTE:", "ENDERECO", "CODIGO", "VALOR TOTAL" achadas por
`image_to_data`, mais a faixa cinza do cabecalho "DESCRICAO | VALOR" e o fio
vertical que separa as duas colunas, achados por densidade de pixels) - nada
de coordenada fixa. Cada celula e relida em zoom 5x.

O resultado volta como linhas SINTETICAS `LOCALIZA_<CHAVE>: valor`, ANEXADAS
ao fim do texto da pagina (nunca substituem a leitura base): todos os regex
de primeira ocorrencia ja existentes do layout (prestador, CNPJ/endereco do
tomador, data) continuam lendo o mesmo texto de antes, e o extrator consulta
os marcadores so onde a leitura base falha ou e menos confiavel. Os valores
saem sem "R$" e sem rotulos reais da nota para nenhum regex legado casar
neles por acaso.

Tudo aqui e funcao pura sobre texto (testavel sem OCR), exceto
`recortar_template`.
"""

from __future__ import annotations

import difflib
import logging
import re
from typing import Dict, List, Optional

from .feira_nfse_nacional import _Pagina, _banda, _ler, _palavras

logger = logging.getLogger(__name__)

PREFIXO = 'LOCALIZA_'

_ZOOM_REF = 3.0
_ZOOM_CELULA = 5.0


def eh_template(texto: str) -> bool:
    """Pagina da fatura da Localiza (nao o boleto/Pix que a acompanha, nem a
    agencia franqueada de Petrolina, nem um DANFE de produto)."""
    if not re.search(r'LOCALIZA\s+RENT\s+A\s+CAR', texto or '', re.IGNORECASE):
        return False
    if not re.search(r'FATURA\s*/\s*DUPLICATA', texto, re.IGNORECASE):
        return False
    if re.search(r'MC\s+LOCADORA\s+PETROLINA|DANFE', texto, re.IGNORECASE):
        return False
    return True


def ler_marcadores(texto: str) -> Dict[str, List[str]]:
    """Linhas `LOCALIZA_<CHAVE>: <valor>` -> {CHAVE: [valores]} (ordem do texto)."""
    saida: Dict[str, List[str]] = {}
    for m in re.finditer(r'^LOCALIZA_([A-Z_]+):[ \t]*(.*)$', texto or '', re.MULTILINE):
        saida.setdefault(m.group(1), []).append(m.group(2).strip())
    return saida


# --- interpretacao das leituras (funcoes puras) -----------------------------

def numero_da_fatura(leitura: str) -> Optional[str]:
    """"Nº: AASSA - 1517937" -> "AASSA - 1517937" (codigo da agencia + numero)."""
    m = re.search(r'([A-Z]{3,6})\s*[-–—]\s*(\d{5,})', leitura or '')
    return f'{m.group(1)} - {m.group(2)}' if m else None


def valores_monetarios(leitura: str) -> List[str]:
    """Todos os "R$ 1.234,56" da leitura. Exige virgula + 2 casas: uma leitura
    sem a virgula ("R$ 92443") e descartada, nunca reinterpretada."""
    return re.findall(r'R\s*\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})(?!\d)', leitura or '')


_NAO_TEXTO_BORDA = re.compile(r'^[^0-9A-Za-zÀ-ÿ]+|[^0-9A-Za-zÀ-ÿ.)]+$')


def linhas_descricao(leitura: str) -> List[str]:
    """Linhas uteis da celula DESCRICAO (sem vazias e sem lixo de borda)."""
    saida = []
    for linha in (leitura or '').split('\n'):
        linha = _NAO_TEXTO_BORDA.sub('', linha.strip())
        linha = re.sub(r'\s+', ' ', linha).strip()
        if len(re.sub(r'[^A-Za-zÀ-ÿ0-9]', '', linha)) >= 2:
            saida.append(linha)
    return saida


def razao_do_cliente(leitura: str) -> Optional[str]:
    """Recorte "CLIENTE: <nome em 1-2 linhas>\\nENDERECO: ..." -> nome numa
    linha so.

    O recorte vai ate a linha do ENDERECO (inclusive): cortar logo acima dela
    decepava a base da 2a linha do nome ("LTDA" lido "ITDA"). Essa linha e
    descartada aqui, assim como o rotulo "CLIENTE:" - que o OCR as vezes
    estropia ("CUENTE:", "subtE:"), por isso o rotulo e reconhecido pelo
    ":" logo no inicio ou por semelhanca com "CLIENTE". A 2a linha do nome
    chega com sujeira de borda no inicio (".", ",", "'", aspas) - nunca
    parte de uma razao social."""
    linhas = [l.strip() for l in (leitura or '').split('\n') if l.strip()]
    for i, linha in enumerate(linhas):
        if re.match(r'\W*ENDERE', linha, re.IGNORECASE):
            linhas = linhas[:i]
            break
    else:
        return None  # sem a linha do endereco o recorte nao fechou o bloco
    if not linhas:
        return None
    primeira = linhas[0]
    m = re.match(r'\s*\S{0,10}:\s*', primeira)
    if m:
        primeira = primeira[m.end():]
    else:
        tok = primeira.split(' ', 1)
        if difflib.SequenceMatcher(None, re.sub(r'\W', '', tok[0].upper()), 'CLIENTE').ratio() >= 0.5:
            primeira = tok[1] if len(tok) > 1 else ''
    partes = [_NAO_TEXTO_BORDA.sub('', l) for l in [primeira] + linhas[1:]]
    nome = re.sub(r'\s+', ' ', ' '.join(p for p in partes if p)).strip()
    if len(nome.split()) < 2 or not re.search(r'[A-Za-z]{3}', nome):
        return None
    return nome


def razao_confiavel(recortada: Optional[str], pagina_inteira: str) -> bool:
    """O recorte so substitui o nome da pagina inteira quando os dois sao a
    MESMA razao social com poucas letras trocadas pelo OCR (ou quando a
    pagina inteira nao leu nada) - um recorte que caiu na celula errada nunca
    troca o tomador."""
    if not recortada:
        return False
    if not pagina_inteira or pagina_inteira == 'Não Identificado':
        return True
    a = re.sub(r'[^A-Z0-9]', '', recortada.upper())
    b = re.sub(r'[^A-Z0-9]', '', pagina_inteira.upper())
    return difflib.SequenceMatcher(None, a, b).ratio() >= 0.85


# Placa: formato antigo AAA9999 ou Mercosul AAA9A99. O OCR troca O<->0 nas
# posicoes de digito ("TEROCO2" impresso "TER0C02"); como a posicao de cada
# digito e FIXA no formato, a correcao e deterministica - so e aplicada se o
# resultado fechar um dos 2 formatos.
_PARA_DIGITO = str.maketrans({'O': '0', 'Q': '0', 'D': '0', 'I': '1', 'L': '1', 'Z': '2', 'S': '5', 'B': '8', 'G': '6'})
_PARA_LETRA = str.maketrans({'0': 'O', '1': 'I', '2': 'Z', '5': 'S', '8': 'B', '6': 'G'})


def normalizar_placa(placa: str) -> str:
    p = placa.upper()
    if len(p) != 7:
        return placa
    cand = p[:3].translate(_PARA_LETRA) + p[3].translate(_PARA_DIGITO) + p[4] + p[5:].translate(_PARA_DIGITO)
    if re.fullmatch(r'[A-Z]{3}\d[A-Z0-9]\d{2}', cand):
        return cand
    return placa


def montar_discriminacao(linhas: List[str], valores_itens: List[str]) -> Optional[str]:
    """Discriminacao = a descricao impressa, linhas unidas.

    Quando cada linha e um item com o seu valor (mesma quantidade de linhas e
    de valores na coluna VALOR, >= 2 - ex.: "ALUGUEL CONFORME CONTRATO ..." /
    "VALOR DO SEGURO"), os itens sao separados por " | "; um texto corrido
    (ressarcimento de multa: varias linhas, 1 valor) vira um paragrafo so."""
    if not linhas:
        return None
    sep = ' | ' if len(valores_itens) >= 2 and len(linhas) == len(valores_itens) else ' '
    texto = re.sub(r'\s+', ' ', sep.join(linhas)).strip()
    texto = re.sub(r'(PLACA\(S\)\s*:\s*)([A-Z0-9]{7})\b',
                   lambda m: m.group(1) + normalizar_placa(m.group(2)), texto, flags=re.IGNORECASE)
    return texto or None


# --- recortes (OCR) ---------------------------------------------------------

def _achar(palavras, pred, depois_de: int = -1):
    for w in palavras:
        if w['top'] > depois_de and pred(w['t'].upper()):
            return w
    return None


def _faixa_cinza(img, y_ini: int, y_fim: int):
    """1a faixa horizontal escura (cabecalho cinza "DESCRICAO | VALOR") entre
    y_ini e y_fim -> (topo, base) ou None."""
    import numpy as np
    a = np.asarray(img) < 160
    largura = a.shape[1]
    frac = a[:, int(largura * 0.05):int(largura * 0.95)].mean(axis=1)
    linhas = [y for y in range(max(0, y_ini), min(len(frac), y_fim)) if frac[y] > 0.4]
    if not linhas:
        return None
    topo = base = linhas[0]
    while base + 1 < y_fim and max(frac[base + 1:base + 4]) > 0.4:
        base += 1
    return topo, base


def _fio_vertical(img, y0: int, y1: int) -> Optional[int]:
    """x do fio que separa as colunas DESCRICAO e VALOR."""
    import numpy as np
    a = np.asarray(img) < 160
    if y1 - y0 < 20:
        return None
    frac = a[y0:y1, :].mean(axis=0)
    largura = a.shape[1]
    xs = [x for x in range(int(largura * 0.55), int(largura * 0.9)) if frac[x] > 0.6]
    return xs[0] if xs else None


def recortar_template(page, angle: int) -> str:
    """Recortes da fatura -> linhas `LOCALIZA_*` (vazio se a estrutura nao for
    achada; cada recorte que falhar e so omitido)."""
    saida: List[str] = []
    try:
        pg = _Pagina(page, angle)
        ref = pg.render(_ZOOM_REF)
        palavras = _palavras(ref)
    except (OSError, ValueError, RuntimeError, ImportError) as exc:
        logger.warning('Localiza: recortes indisponiveis (%s)', exc)
        return ''
    largura, altura = ref.size

    dup = _achar(palavras, lambda t: 'DUPLICATA' in t)
    cli = _achar(palavras, lambda t: t.startswith('CLIENTE'), dup['top'] if dup else -1)
    if not dup or not cli:
        return ''
    end = _achar(palavras, lambda t: t.startswith('ENDERE'), cli['top'])
    vt = None
    for i, w in enumerate(palavras[:-1]):
        if w['t'].upper() == 'VALOR' and palavras[i + 1]['t'].upper().startswith('TOTAL') and w['top'] > cli['top']:
            vt = w

    def _celula(x0, y0, x1, y1, psm):
        return _ler(_banda(pg, _ZOOM_CELULA, _ZOOM_REF, x0, y0, x1, y1), psm)

    try:
        num = numero_da_fatura(_celula(dup['l'] + dup['w'] + 20, dup['top'] - 30, None, cli['top'] - 5, 7))
        if num:
            saida.append(f'{PREFIXO}NUMERO: {num}')
    except (OSError, ValueError, RuntimeError) as exc:
        logger.warning('Localiza: recorte do numero falhou (%s)', exc)

    if end:
        try:
            cod = _achar(palavras, lambda t: t.startswith(('CÓDIGO', 'CODIGO')), cli['top'] - 15)
            x1 = cod['l'] - 10 if cod and cod['l'] > largura * 0.4 and cod['top'] < end['top'] + 20 else largura * 0.6
            nome = razao_do_cliente(_celula(0, cli['top'] - cli['h'] // 2, x1, end['top'] + end['h'] + 3, 6))
            if nome:
                saida.append(f'{PREFIXO}TOMADOR: {nome}')
        except (OSError, ValueError, RuntimeError) as exc:
            logger.warning('Localiza: recorte do cliente falhou (%s)', exc)

    if vt and end:
        try:
            faixa = _faixa_cinza(ref, end['top'] + end['h'], vt['top'])
            if faixa:
                y0, y1 = faixa[1] + 5, vt['top'] - 8
                xdiv = _fio_vertical(ref, y0, y1)
                if xdiv:
                    for linha in linhas_descricao(_celula(0, y0, xdiv - 5, y1, 6)):
                        saida.append(f'{PREFIXO}DESCRICAO: {linha}')
                    for v in valores_monetarios(_celula(xdiv + 8, y0, None, y1, 6)):
                        saida.append(f'{PREFIXO}ITEM_VALOR: {v}')
                    total = valores_monetarios(_celula(xdiv + 8, vt['top'] - 5, None, vt['top'] + vt['h'] * 4, 6))
                    if total:
                        saida.append(f'{PREFIXO}VALOR_TOTAL: {total[-1]}')
        except (OSError, ValueError, RuntimeError, IndexError) as exc:
            logger.warning('Localiza: recorte da descricao/valores falhou (%s)', exc)

    return '\n'.join(saida) + ('\n' if saida else '')
