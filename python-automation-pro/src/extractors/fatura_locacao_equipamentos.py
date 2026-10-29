"""Impresso "Fatura de Locação" de equipamentos (locação de bens móveis, NÃO é NFS-e).

Achado real 2026-10-28 (`LOCACAO DE BANHEIRO QUIMICO - 16 DE JULHO.pdf`, 1
página, só imagem): IVAN BARBOZA CORREA (CNPJ 30.226.394/0001-61, logo "S&C
Locação de Máquinas", Bragança Paulista/SP) -> H. Z. PATRIMONIAL LTDA. (Lauro
de Freitas/BA), "Fatura de Locação: 15827", banheiro químico, R$ 2.250,00.
Antes deste módulo a página caía em LAYOUT_FATURA_LOCACAO_GENERICA (detectado só
pela frase "FATURA DE LOCAÇÃO", calibrado no template da LOC BAHIA, cujos
rótulos "LOCADORA"/"LOCATÁRIO"/"TOTAL: R$" não existem aqui): prestador
sentinela, tomador com o CNPJ do PRESTADOR, valor 0,00.

Estrutura do impresso (ERP de locadora, grades com fios):
  * cabeçalho: logo | razão social / "CNPJ: ... IE: ..." / endereço em 2
    linhas ("<logr>, <nº>- <compl> - <bairro> - <cidade> /<UF> - CEP <cep>")
    | caixa "Natureza de Operação:" (CFOP) | caixa "Fatura de Locação:" (nº);
  * "Destinatário / Remetente": grade rótulo-em-cima/valor-embaixo (Nome/Razão
    Social | CPF/CNPJ | Data Emissão; Endereço | Bairro | Cep | CONTRATO;
    Cidade | Tel./Fax | Inscrição Estadual);
  * grade "Fatura | Valor | Vencimento de Pagamento";
  * "Descrição do(s) Produto(s) / Equipamento(s) Locado(s)": Produto |
    Descrição | Número de Série | Período de Locação | Dias | Quantidade |
    Valor, depois "Taxa Entrega/Retirada" e "Total Locação";
  * texto de não incidência de ISS, "Dados Adicionais" e canhoto de
    recebimento ("FATURA DE LOCAÇÃO Nº <n>").

Detecção ESTRUTURAL (as caixas "Natureza de Operação"/"Fatura de Locação:" +
o bloco "Destinatário / Remetente" + "Total Locação"/"Período de Locação"),
nunca pelo nome ou CNPJ do emitente.

O OCR de página inteira deste modelo perde a grade "Fatura | Valor |
Vencimento" inteira (vira "EE E TeIo7i2024"), as colunas Dias/Quantidade do
item, lê "B123" como "B128" e o "I" de "DOM PEDRO I"/"EMPRESARIAL I" como "|"
(que na grade do destinatário também é borda de coluna). Por isso `recortar`
(chamado pelo `_ocr_page`) lê as grades CÉLULA A CÉLULA - colunas pelos fios
verticais, linhas pelos rótulos/fios horizontais achados na própria imagem - e
devolve linhas SINTÉTICAS `FATLOC_*` PREPENDIDAS ao texto (mesma técnica de
`nota_locacao.py`/`feira_nfse_nacional.py`):
  * `FATLOC_DEST_<CAMPO>:` valor de cada célula do bloco Destinatário;
  * `FATLOC_FATURA:` "<nº> ;; <valor> ;; <vencimento>" da grade da fatura;
  * `FATLOC_ITEM:` "CHAVE=valor ;; ..." de cada linha da grade de itens.
Nenhuma dessas linhas contém rótulo real que o split de notas do
`parse_multiple` reconheça. `extrair` é função pura sobre o texto; sem os
marcadores (PDF digital, recorte falhou) cai no texto de página inteira, e o
que não for legível vira sentinela + aviso.

Convenção das faturas de locação do projeto (Localiza/ARMAC/NOTA_LOCACAO):
item 0601, CodigoVerificacao "FATURA", ISS/base/alíquota zerados, competência =
mês da emissão; reaproveita `nota_locacao.NotaLocacao`/`ItemLocacao`.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from ..models.nfse_models import Endereco, Entidade, Valores
from . import nota_locacao as _nl

logger = logging.getLogger(__name__)

PREFIXO = 'FATLOC_'
SEP = ' ;; '

_SENTINELA_DOC = '00000000000000'
_SENTINELA_NUMERO = '00000000'

_MONEY = r'\d{1,3}(?:\.\d{3})*,\d{2}'
_LOCACAO = r'Loca\S{1,3}o'
_RE_CNPJ = re.compile(r'\d{2}\.?\d{3}\.?\d{3}\s*/\s*\d{4}\s*-?\s*\d{2}')
_RE_DATA = re.compile(r'\b(\d{2})/(\d{2})/(\d{4})\b')
_RE_DEST = re.compile(r'Destinat\S{1,2}rio\s*/\s*Remetente', re.IGNORECASE)
_RE_CEP = re.compile(r'\b(\d{2}\.?\d{3}-?\d{3})\b')

# Fios das grades: pixel "escuro" (< 245 - os fios internos da grade de itens
# são cinza-claro, ~232) em >= 90% da faixa.
_LIMIAR_PIXEL = 245
_FRACAO_FIO = 0.9


# ---------------------------------------------------------------------------
# Detecção
# ---------------------------------------------------------------------------

def eh_fatura_locacao(texto: str) -> bool:
    """True para o impresso "Fatura de Locação" de equipamentos (ver módulo).

    Exige as caixas do cabeçalho ("Natureza de Operação" e "Fatura de
    Locação:" com dois-pontos - o canhoto só imprime "FATURA DE LOCAÇÃO Nº"), o
    bloco "Destinatário / Remetente" e um rótulo da grade de itens ("Total
    Locação" ou "Período de Locação"). NFS-e/DANFE/nota fiscal ficam fora."""
    if not texto:
        return False
    if not re.search(r'Natureza\s+de\s+Opera', texto, re.IGNORECASE):
        return False
    if not re.search(r'Fatura\s+de\s+' + _LOCACAO + r'\s*:', texto, re.IGNORECASE):
        return False
    if not _RE_DEST.search(texto):
        return False
    if not re.search(r'(?:Total|Per\S{1,2}odo\s+de)\s+' + _LOCACAO, texto, re.IGNORECASE):
        return False
    if re.search(r'\bNFS-?e\b|DANF|Nota\s+Fiscal|Documento\s+Auxiliar', texto, re.IGNORECASE):
        return False
    return True


# ---------------------------------------------------------------------------
# Utilitários puros
# ---------------------------------------------------------------------------

def _colapsa(s: str) -> str:
    return re.sub(r'\s+', ' ', s or '').strip()


def _norm(s: str) -> str:
    return re.sub(r'[^A-Z0-9]', '', _nl._sem_acento(s or '').upper())


def _valor_br(s: str) -> float:
    return float(s.replace('.', '').replace(',', '.'))


def _data(s: str) -> Optional[datetime]:
    m = _RE_DATA.search(s or '')
    if not m:
        return None
    try:
        return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None


def ler_marcadores(texto: str) -> Dict[str, List[str]]:
    """Linhas `FATLOC_<CHAVE>: <valor>` -> {CHAVE: [valores]}."""
    saida: Dict[str, List[str]] = {}
    for m in re.finditer(r'^FATLOC_([A-Z_]+):[ \t]*(.*)$', texto or '', re.MULTILINE):
        saida.setdefault(m.group(1), []).append(m.group(2).strip())
    return saida


def sem_marcadores(texto: str) -> str:
    return re.sub(r'^FATLOC_[A-Z_]+:.*\n?', '', texto or '', flags=re.MULTILINE)


def agrupar(indices: Sequence[int], folga: int = 2) -> List[Tuple[int, int]]:
    """[3,4,5,9,10] -> [(3,5),(9,10)]: índices contíguos (fios de N px)."""
    grupos: List[List[int]] = []
    for i in indices:
        if grupos and i - grupos[-1][1] <= folga:
            grupos[-1][1] = i
        else:
            grupos.append([i, i])
    return [(a, b) for a, b in grupos]


def chave_dest(rotulo: str) -> Optional[str]:
    """Rótulo de uma célula do bloco Destinatário -> chave do marcador."""
    n = _norm(rotulo)
    if n.startswith('NOME') or 'RAZAO' in n:
        return 'NOME'
    if 'CNPJ' in n or n.startswith('CPF'):
        return 'CNPJ'
    if n.startswith('DATA') and 'EMISS' in n:
        return 'DATA'
    if n.startswith('ENDERE'):
        return 'ENDERECO'
    if n.startswith('BAIRRO'):
        return 'BAIRRO'
    if n.startswith('CEP'):
        return 'CEP'
    if n.startswith('CIDADE') or n.startswith('MUNIC'):
        return 'CIDADE'
    if n.startswith('TEL') or n.startswith('FONE'):
        return 'TELEFONE'
    if n.startswith('INSCRI'):
        return 'IE'
    if n.startswith('CONTRATO'):
        return 'CONTRATO'
    return None


def chave_coluna_item(rotulo: str) -> Optional[str]:
    """Cabeçalho de coluna da grade de itens -> chave."""
    n = _norm(rotulo)
    if 'SERIE' in n or n.startswith('NUMERO'):
        return 'SERIE'
    if n.startswith('PRODUTO'):
        return 'PRODUTO'
    if n.startswith('DESCRI'):
        return 'DESCRICAO'
    if n.startswith('PER') and 'LOCA' in n:
        return 'PERIODO'
    if n.startswith('DIAS'):
        return 'DIAS'
    if n.startswith('QUANT') or n.startswith('QTD'):
        return 'QUANTIDADE'
    if n.startswith('VALOR'):
        return 'VALOR'
    return None


def celulas_destinatario(linhas_por_celula: Sequence[Tuple[int, int, int, List[str]]]) -> List[str]:
    """Células OCR do bloco Destinatário -> linhas `FATLOC_DEST_*`.

    Cada item é (linha_da_grade, x0, x1, linhas_lidas). A 1ª linha lida é o
    rótulo, o resto o valor. A célula "CONTRATO" é mesclada nas 2 linhas de
    baixo da grade: o rótulo cai na faixa de uma linha e o número na da
    seguinte, numa célula SEM rótulo - atribuída ao CONTRATO pela sobreposição
    horizontal. Célula sem rótulo reconhecível e sem CONTRATO acima: descartada
    (nunca adivinhada). Função pura."""
    saida: List[str] = []
    contrato: Optional[Tuple[int, int, int]] = None
    contrato_ok = False
    for linha, x0, x1, lidas in linhas_por_celula:
        lidas = [_colapsa(l) for l in lidas if _colapsa(l)]
        if not lidas:
            continue
        chave = chave_dest(lidas[0])
        if chave is None:
            if contrato and not contrato_ok and linha == contrato[0] + 1 \
                    and min(x1, contrato[2]) - max(x0, contrato[1]) > 0.5 * (x1 - x0):
                saida.append(f'{PREFIXO}DEST_CONTRATO: {" ".join(lidas)}')
                contrato_ok = True
            continue
        valor = ' '.join(lidas[1:]).strip()
        if chave == 'CONTRATO':
            contrato = (linha, x0, x1)
            if valor:
                contrato_ok = True
        if valor:
            saida.append(f'{PREFIXO}DEST_{chave}: {valor}')
    return saida


def linha_fatura(texto: str) -> Optional[str]:
    """Leitura da grade "Fatura | Valor | Vencimento" -> "nº ;; valor ;; data"."""
    m = re.search(r'\b(\d{1,12})\s+(' + _MONEY + r')\s+(\d{2}/\d{2}/\d{4})\b', texto or '')
    return f'{m.group(1)}{SEP}{m.group(2)}{SEP}{m.group(3)}' if m else None


def linha_item(cabecalho: Sequence[Optional[str]], celulas: Sequence[str]) -> Optional[str]:
    """Uma linha da grade de itens -> "CHAVE=valor ;; ..." (só colunas com
    cabeçalho reconhecido e valor lido)."""
    partes = []
    for chave, cel in zip(cabecalho, celulas):
        cel = _colapsa(cel)
        if chave and cel:
            partes.append(f'{chave}={cel}')
    return SEP.join(partes) if partes else None


def ler_item(marcador: str) -> Dict[str, str]:
    campos = {}
    for parte in marcador.split(SEP.strip()):
        if '=' in parte:
            k, v = parte.split('=', 1)
            campos[k.strip()] = v.strip()
    return campos


# ---------------------------------------------------------------------------
# Recortes (OCR) - chamados por `SPPdfExtractor._ocr_page`
# ---------------------------------------------------------------------------

def _escuros(img):
    import numpy as np
    return np.asarray(img.convert('L')) < _LIMIAR_PIXEL


def _fios_verticais(esc, y0: int, y1: int) -> List[Tuple[int, int]]:
    if y1 - y0 < 15:
        return []
    frac = esc[y0:y1, :].mean(axis=0)
    return agrupar([x for x in range(esc.shape[1]) if frac[x] >= _FRACAO_FIO])


def _fios_horizontais(esc, y0: int, y1: int, x0: int, x1: int) -> List[Tuple[int, int]]:
    if x1 - x0 < 50:
        return []
    frac = esc[max(0, y0):y1, x0:x1].mean(axis=1)
    return [(max(0, y0) + a, max(0, y0) + b)
            for a, b in agrupar([i for i, f in enumerate(frac) if f >= _FRACAO_FIO])]


def _celulas(fios: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    return [(a[1] + 4, b[0] - 4) for a, b in zip(fios, fios[1:]) if b[0] - a[1] > 20]


def _ler_celula(img, x0: int, y0: int, x1: int, y1: int) -> List[str]:
    return _nl._ocr_linhas(img, (x0, y0, x1, y1), psm=6)


def _depois(palavras: List[dict], pred, top_min: int) -> Optional[dict]:
    for p in palavras:
        if p['top'] > top_min and pred(p['norm']):
            return p
    return None


def recortar(img, texto_base: str) -> str:
    """Linhas sintéticas `FATLOC_*` (ver docstring do módulo).

    `img` é a página renderizada (PIL, zoom 3), já na orientação vencedora do
    OCR. Cada recorte é independente: a falha de um só o omite."""
    try:
        palavras = _nl._palavras(img)
        esc = _escuros(img)
    except (OSError, RuntimeError, ValueError, ImportError) as exc:
        logger.warning('Fatura de locação: recortes indisponíveis (%s)', exc)
        return ''
    largura, altura = img.size
    saida: List[str] = []

    dest = _depois(palavras, lambda n: n.startswith('DESTINAT'), -1)
    if not dest:
        return ''
    nome = _depois(palavras, lambda n: n.startswith('NOME'), dest['top'])
    ender = _depois(palavras, lambda n: n.startswith('ENDERE'), dest['top'])
    cid = _depois(palavras, lambda n: n.startswith('CIDADE'), dest['top'])
    fim_dest = None
    try:
        if nome and ender and cid and nome['top'] < ender['top'] < cid['top']:
            passo = cid['top'] - ender['top']
            margem = int(passo * 0.25)
            faixas = [(nome['top'] - margem, ender['top'] - margem),
                      (ender['top'] - margem, cid['top'] - margem),
                      (cid['top'] - margem, cid['top'] + passo - margem)]
            fim_dest = faixas[-1][1]
            celulas = []
            for i, (y0, y1) in enumerate(faixas):
                for x0, x1 in _celulas(_fios_verticais(esc, y0 + 6, y1 - 6)):
                    celulas.append((i, x0, x1, _ler_celula(img, x0, y0 + 4, x1, y1 - 4)))
            saida.extend(celulas_destinatario(celulas))
    except (OSError, RuntimeError, ValueError) as exc:
        logger.warning('Fatura de locação: recorte do destinatário falhou (%s)', exc)

    prod = _depois(palavras, lambda n: n == 'PRODUTO', cid['top'] if cid else dest['top'])
    taxa = _depois(palavras, lambda n: n == 'TAXA' or n == 'TOTAL', prod['top'] if prod else altura)

    try:
        if fim_dest and prod:
            texto = '\n'.join(_nl._ocr_linhas(img, (0, fim_dest, largura, prod['top'] - 10), psm=6))
            fat = linha_fatura(texto)
            if fat:
                saida.append(f'{PREFIXO}FATURA: {fat}')
    except (OSError, RuntimeError, ValueError) as exc:
        logger.warning('Fatura de locação: recorte da grade da fatura falhou (%s)', exc)

    try:
        if prod and taxa:
            x_ini, x_fim = int(largura * 0.05), int(largura * 0.95)
            todos = _fios_horizontais(esc, prod['top'] - 150, taxa['top'], x_ini, x_fim)
            # Borda de cima = o ÚLTIMO fio acima do cabeçalho (acima dele fica
            # a faixa "Descrição do(s) Produto(s) / Equipamento(s)"), depois
            # cada fio entre o cabeçalho e a linha "Taxa Entrega/Retirada".
            acima = [h for h in todos if h[1] < prod['top']]
            hor = acima[-1:] + [h for h in todos if h[0] > prod['top']]
            if len(acima) >= 1 and len(hor) >= 3:
                cab_y0, cab_y1 = hor[0][1] + 3, hor[1][0] - 3
                verts = _fios_verticais(esc, hor[0][1] + 3, hor[-1][0] - 3)
                colunas = _celulas(verts)
                cabecalho = [chave_coluna_item(' '.join(_ler_celula(img, x0, cab_y0, x1, cab_y1)))
                             for x0, x1 in colunas]
                for a, b in zip(hor[1:], hor[2:]):
                    y0, y1 = a[1] + 3, b[0] - 3
                    if y1 - y0 < 20:
                        continue
                    lido = linha_item(cabecalho, [' '.join(_ler_celula(img, x0, y0, x1, y1))
                                                  for x0, x1 in colunas])
                    if lido:
                        saida.append(f'{PREFIXO}ITEM: {lido}')
    except (OSError, RuntimeError, ValueError, IndexError) as exc:
        logger.warning('Fatura de locação: recorte dos itens falhou (%s)', exc)

    return '\n'.join(saida) + ('\n' if saida else '')


# ---------------------------------------------------------------------------
# Extração (função pura sobre texto)
# ---------------------------------------------------------------------------

def _cabecalho(corpo: str) -> str:
    m = _RE_DEST.search(corpo)
    return corpo[:m.start()] if m else ''


def _numero(corpo: str, marc: Dict[str, List[str]], avisos: List[str]) -> str:
    """Nº da fatura: grade "Fatura" (recorte) e canhoto "FATURA DE LOCAÇÃO Nº"
    precisam concordar; só um legível vale sozinho; divergência -> sentinela."""
    leituras = []
    if marc.get('FATURA'):
        leituras.append(marc['FATURA'][0].split(SEP.strip())[0].strip())
    m = re.search(r'FATURA\s+DE\s+' + _LOCACAO + r'[\s\S]{0,160}?N\s*[º°o]\s*(\d{1,12})\b', corpo, re.IGNORECASE)
    if m:
        leituras.append(m.group(1))
    leituras = [l.lstrip('0') or '0' for l in leituras]
    if not leituras:
        avisos.append("Número da fatura de locação não legível - mantido sentinela; conferir no documento")
        return _SENTINELA_NUMERO
    if len(set(leituras)) > 1:
        avisos.append(f"Número da fatura de locação divergente entre leituras do OCR "
                      f"({' x '.join(leituras)}) - mantido sentinela; conferir no documento")
        return _SENTINELA_NUMERO
    return leituras[0]


def _data_emissao(corpo: str, marc: Dict[str, List[str]]) -> Optional[datetime]:
    if marc.get('DEST_DATA'):
        d = _data(marc['DEST_DATA'][0])
        if d:
            return d
    m = re.search(r'Data\s+Emiss\S{1,2}o[^\n]*\n+([^\n]*)', corpo, re.IGNORECASE)
    if m:
        datas = _RE_DATA.findall(m.group(1))
        if datas:
            d, mm, a = datas[-1]
            try:
                return datetime(int(a), int(mm), int(d))
            except ValueError:
                return None
    return None


_RE_END_LETTERHEAD = re.compile(
    r'^(?P<logr>.+?),\s*(?P<num>\d{1,6}[A-Z]?|S/?N)\b\s*-?\s*(?P<resto>.*?)\s*/\s*(?P<uf>[A-Z]{2})\s*-\s*'
    r'CEP\s*:?\s*(?P<cep>\d{2}\.?\d{3}-?\d{3})', re.IGNORECASE)


def _barra_como_i(s: str) -> str:
    """"DOM PEDRO |," -> "DOM PEDRO I,": no letterhead (texto corrido, sem
    colunas) um "|" isolado é o glifo "I" lido errado pelo OCR."""
    return re.sub(r'(?<=\s)\|(?=[\s,]|$)', 'I', s)


def _prestador(corpo: str, resolver, validar_doc, avisos: List[str]) -> Entidade:
    cab = _cabecalho(corpo)
    linhas = [l for l in cab.splitlines()]
    i_cnpj = next((i for i, l in enumerate(linhas) if re.search(r'CNPJ\s*:', l, re.IGNORECASE)), None)

    doc = _SENTINELA_DOC
    razao = ''
    endereco_raw = ''
    if i_cnpj is not None:
        m = _RE_CNPJ.search(linhas[i_cnpj])
        d = re.sub(r'\D', '', m.group(0)) if m else ''
        if d and validar_doc(d):
            doc = d
        razao = next((_colapsa(l) for l in reversed(linhas[:i_cnpj]) if _colapsa(l)), '')
        partes = []
        for l in linhas[i_cnpj + 1:]:
            l = _colapsa(l)
            if not l:
                continue
            # Valores das caixas da direita (CFOP + nº da fatura) colados ao fim
            # da 1ª linha do endereço na leitura de página inteira.
            l = re.sub(r'\s+\d{4}\s+\d{1,12}$', '', l)
            partes.append(l)
            if re.search(r'CEP\s*:?\s*\d', l, re.IGNORECASE):
                break
        endereco_raw = _barra_como_i(_colapsa(' '.join(partes)))
    if doc == _SENTINELA_DOC:
        avisos.append("CNPJ do emitente (locador) não legível com dígito verificador válido - "
                      "mantido sentinela; conferir no documento")
    if not razao or _RE_CNPJ.search(razao):
        avisos.append("Razão social do emitente (locador) não encontrada no cabeçalho - conferir no documento")
        razao = 'Prestador Não Identificado'

    logradouro, numero, bairro, compl, municipio, uf, cep = 'Não informado', 'S/N', '', None, '', '', ''
    m = _RE_END_LETTERHEAD.search(endereco_raw)
    if m:
        logradouro, numero = _colapsa(m.group('logr')), m.group('num').upper()
        uf, cep = m.group('uf').upper(), re.sub(r'\D', '', m.group('cep'))
        segs = [s for s in (_colapsa(x) for x in re.split(r'\s+-\s+|^-\s*', m.group('resto'))) if s]
        if segs:
            municipio = segs[-1]
        if len(segs) >= 2:
            bairro = segs[-2]
        if len(segs) >= 3:
            compl = ' - '.join(segs[:-2])
    else:
        avisos.append("Endereço do emitente (locador) fora do formato esperado no cabeçalho - conferir no documento")
    cod_mun = resolver.extract_and_validate(municipio, uf or 'BA', city_hint=municipio) if municipio else ''
    if not municipio:
        avisos.append("Município do emitente (locador) não encontrado no cabeçalho - conferir no documento")

    return Entidade(
        cnpj_cpf=doc, razao_social=razao,
        endereco=Endereco(
            logradouro=logradouro, numero=numero, complemento=compl, bairro=bairro or 'Não informado',
            codigo_municipio=cod_mun, municipio=municipio or None, uf=uf,
            cep=cep if len(cep) == 8 else '00000000'),
    )


def _tomador_texto(corpo: str) -> Dict[str, str]:
    """Fallback sem marcadores: grade Destinatário do texto de página inteira."""
    campos: Dict[str, str] = {}
    m = re.search(r'Nome\s*/\s*Raz\S{1,2}o\s+Social[^\n]*\n+([^\n]+)', corpo, re.IGNORECASE)
    if m:
        linha = m.group(1)
        m_doc = _RE_CNPJ.search(linha) or re.search(r'\d{3}\.?\d{3}\.?\d{3}-?\d{2}', linha)
        if m_doc:
            campos['CNPJ'] = m_doc.group(0)
            linha = linha[:m_doc.start()]
        campos['NOME'] = linha.strip(' |')
    m = re.search(r'Endere\S{1,2}o\s+Bairro\s+Cep[^\n]*\n+([^\n]+)', corpo, re.IGNORECASE)
    if m:
        linha = re.sub(r'\s*CONTRATO\s*$', '', m.group(1), flags=re.IGNORECASE)
        m_cep = re.search(r'(\d{2}\.?\d{3}-?\d{3})\s*$', linha)
        if m_cep:
            campos['CEP'] = m_cep.group(1)
            linha = linha[:m_cep.start()]
        segs = [s.strip() for s in linha.strip(' |').split('|') if s.strip()]
        if len(segs) >= 2:
            campos['ENDERECO'], campos['BAIRRO'] = ' '.join(segs[:-1]), segs[-1]
        elif segs:
            campos['ENDERECO'] = segs[0]
    m = re.search(r'Cidade\s+Tel[^\n]*\n+([^\n]+)', corpo, re.IGNORECASE)
    if m:
        campos['CIDADE'] = m.group(1)
    m = re.search(r'CONTRATO\s*\n[^\n]*?(\d{1,10})\s*$', corpo, re.IGNORECASE | re.MULTILINE)
    if m:
        campos['CONTRATO'] = m.group(1)
    return campos


def _tomador(corpo: str, marc: Dict[str, List[str]], resolver, validar_doc, cnpj_prestador: str,
             avisos: List[str]) -> Tuple[Entidade, Optional[str]]:
    campos = {k[5:]: v[0] for k, v in marc.items() if k.startswith('DEST_') and v}
    texto = _tomador_texto(corpo)
    if not campos.get('NOME') or not campos.get('CNPJ'):
        # Recorte ausente/incompleto: o texto de página inteira completa.
        for k, v in texto.items():
            campos.setdefault(k, v)

    razao = _colapsa(campos.get('NOME', '')).strip(' |')
    pagina = _colapsa(texto.get('NOME', '')).strip(' |')
    if pagina and razao != pagina and _norm(pagina) == _norm(razao):
        # Mesma razão social nas 2 leituras, só o espaçamento difere ("H.Z." x
        # "H. Z."): a leitura de página inteira preserva melhor os espaços.
        razao = pagina
    if not razao:
        avisos.append("Razão social do destinatário (tomador) não encontrada - conferir no documento")
        razao = 'Tomador Não Identificado'

    doc_raw = campos.get('CNPJ', '')
    doc = re.sub(r'\D', '', doc_raw)
    if len(doc) not in (11, 14) or doc == cnpj_prestador:
        avisos.append(f"CNPJ/CPF do destinatário ({doc_raw.strip() or 'ilegível'}) inválido ou igual ao "
                      "do emitente - mantido sentinela; conferir no documento")
        doc = _SENTINELA_DOC
    elif not validar_doc(doc):
        avisos.append(f"CNPJ/CPF do destinatário ({doc}) não passa na validação do dígito "
                      "verificador - mantido sentinela; conferir no documento")
        doc = _SENTINELA_DOC

    logradouro, numero, compl = 'Não informado', 'S/N', None
    # Dentro da célula do endereço não há borda de coluna: "|" é o glifo "I"
    # ("EDF VILLAS EMPRESARIAL I" lido "EMPRESARIAL |").
    end = _barra_como_i(_colapsa(campos.get('ENDERECO', '')))
    m = re.match(r'^(.+?),\s*(\d{1,6}[A-Z]?|S/?N)\b\s*-?\s*(.*)$', end, re.IGNORECASE)
    if m:
        logradouro, numero, compl = m.group(1).strip(), m.group(2).upper(), (m.group(3).strip(' ,-') or None)
    elif end:
        logradouro = end
    bairro = _colapsa(campos.get('BAIRRO', ''))
    if end and not bairro:
        avisos.append("Bairro do destinatário não lido - conferir no documento")

    municipio = uf = ''
    m = re.match(r'^\s*(.+?)\s*/\s*([A-Z]{2})\b', campos.get('CIDADE', ''))
    if m:
        municipio, uf = _colapsa(m.group(1)), m.group(2)
    cod_mun = resolver.extract_and_validate(municipio, uf or 'BA', city_hint=municipio) if municipio else ''
    if not municipio:
        avisos.append("Município do destinatário (tomador) não encontrado - conferir no documento")
    cep = re.sub(r'\D', '', campos.get('CEP', ''))

    tel = re.sub(r'\D', '', campos.get('TELEFONE', ''))
    contrato = re.sub(r'\D', '', campos.get('CONTRATO', '')) or None
    return Entidade(
        cnpj_cpf=doc, razao_social=razao, telefone=tel if 10 <= len(tel) <= 11 else None,
        endereco=Endereco(
            logradouro=logradouro, numero=numero, complemento=compl, bairro=bairro or 'Não informado',
            codigo_municipio=cod_mun, municipio=municipio or None, uf=uf,
            cep=cep if len(cep) == 8 else '00000000'),
    ), contrato


def _itens(marc: Dict[str, List[str]]) -> List[Tuple[_nl.ItemLocacao, Dict[str, str]]]:
    saida = []
    for bruto in marc.get('ITEM', []):
        c = ler_item(bruto)
        if not c.get('DESCRICAO'):
            continue
        valor = re.search(_MONEY, c.get('VALOR', ''))
        qtd = re.fullmatch(r'\d{1,6}', c.get('QUANTIDADE', '').strip())
        saida.append((_nl.ItemLocacao(
            descricao=c['DESCRICAO'],
            quantidade=float(qtd.group(0)) if qtd else None,
            valor_total=_valor_br(valor.group(0)) if valor else None), c))
    return saida


def _descricao_item(item: _nl.ItemLocacao, c: Dict[str, str]) -> str:
    partes = [f"{c['PRODUTO']} - {item.descricao}" if c.get('PRODUTO') else item.descricao]
    if c.get('SERIE'):
        partes.append(f"Série {c['SERIE']}")
    if c.get('PERIODO'):
        dias = f" ({c['DIAS']} dias)" if c.get('DIAS') else ''
        partes.append(f"Período de locação {c['PERIODO']}{dias}")
    if c.get('QUANTIDADE'):
        partes.append(f"Qtd {c['QUANTIDADE']}")
    if c.get('VALOR'):
        partes.append(f"Valor {c['VALOR']}")
    return ' - '.join(partes)


def extrair(texto: str, resolver, validar_doc: Callable[[str], bool]) -> _nl.NotaLocacao:
    """Extrai a fatura de locação. `resolver` é o `IBGEResolver` compartilhado
    do extrator; `validar_doc` valida o DV de CNPJ/CPF."""
    avisos: List[str] = []
    marc = ler_marcadores(texto)
    corpo = sem_marcadores(texto)

    numero = _numero(corpo, marc, avisos)
    data = _data_emissao(corpo, marc)
    prestador = _prestador(corpo, resolver, validar_doc, avisos)
    tomador, contrato = _tomador(corpo, marc, resolver, validar_doc, prestador.cnpj_cpf, avisos)

    fat_valor = fat_venc = None
    if marc.get('FATURA'):
        partes = [p.strip() for p in marc['FATURA'][0].split(SEP.strip())]
        if len(partes) == 3:
            fat_valor, fat_venc = _valor_br(partes[1]), partes[2]

    itens_c = _itens(marc)
    itens = [i for i, _ in itens_c]

    m_total = re.search(r'Total\s+' + _LOCACAO + r'\s*:?\s*(?:R\$\s*)?(' + _MONEY + r')', corpo, re.IGNORECASE)
    total = _valor_br(m_total.group(1)) if m_total else None
    m_taxa = re.search(r'Taxa\s+Entrega\s*/\s*Retirada\s*:?\s*(?:R\$\s*)?(' + _MONEY + r')', corpo, re.IGNORECASE)
    taxa = _valor_br(m_taxa.group(1)) if m_taxa else None

    if total is None and fat_valor is not None:
        total = fat_valor
        avisos.append("Rótulo \"Total Locação\" ilegível - valor tomado da grade \"Fatura | Valor\"; "
                      "conferir no documento")
    if total is not None and fat_valor is not None and abs(total - fat_valor) > 0.011:
        avisos.append(f"\"Total Locação\" ({total:.2f}) diverge do \"Valor\" da grade da fatura "
                      f"({fat_valor:.2f}) - mantido o Total Locação; conferir no documento")
    if total is not None and itens and all(i.valor_total is not None for i in itens):
        soma = round(sum(i.valor_total for i in itens) + (taxa or 0.0), 2)
        if abs(soma - total) > 0.011:
            avisos.append(f"Soma dos itens + taxa de entrega/retirada ({soma:.2f}) diverge do "
                          f"\"Total Locação\" ({total:.2f}) - mantido o total impresso; conferir no documento")
    if total is None:
        avisos.append("Valor total da fatura de locação não legível - conferir no documento")

    blocos = [_descricao_item(i, c) for i, c in itens_c]
    if not blocos:
        avisos.append("Itens da fatura de locação não lidos pelo recorte da grade - "
                      "discriminação sem o detalhe dos equipamentos; conferir no documento")
    if taxa is not None:
        blocos.append(f"Taxa Entrega/Retirada {m_taxa.group(1)}")
    if m_total:
        blocos.append(f"Total Locação {m_total.group(1)}")
    ref = [f"Fatura de Locação {numero}" if numero != _SENTINELA_NUMERO else "Fatura de Locação"]
    if contrato:
        ref.append(f"Contrato {contrato}")
    if fat_venc:
        ref.append(f"Vencimento {fat_venc}")
    blocos.append(' - '.join(ref))
    m_iss = re.search(r'N\S{1,2}o\s+incid\S{1,3}ncia\s+de\s+ISS[^\n]*', corpo, re.IGNORECASE)
    texto_iss = _colapsa(m_iss.group(0)) if m_iss else None
    if texto_iss:
        blocos.append(texto_iss)
    m_ad = re.search(r'Dados\s+Adicionais\s*\n([\s\S]*?)(?:\n\s*Recebi|\Z)', corpo, re.IGNORECASE)
    adicionais = '; '.join(_colapsa(l) for l in m_ad.group(1).splitlines() if _colapsa(l)) if m_ad else ''
    if adicionais:
        blocos.append(f"Dados adicionais: {adicionais}")
    discriminacao = ' | '.join(b for b in blocos if b)

    valor = total or 0.0
    valores = Valores(valor_servicos=valor, valor_liquido_nfse=valor,
                      base_calculo=0.0, aliquota=0.0, valor_iss=0.0)

    avisos.append(
        "Documento é FATURA DE LOCAÇÃO de bem móvel (não é NFS-e): XML gerado na convenção das faturas "
        "de locação - ISS/base/alíquota zerados, item 0601 e código de verificação \"FATURA\"; "
        "conferir o lançamento no Domínio antes de importar")
    if texto_iss:
        avisos.append(f"A fatura declara: \"{texto_iss}\" - mantida a convenção do projeto (item 0601, "
                      "ISS 0); o item citado na fatura não foi usado como código de serviço")
    if re.search(r'Endere\S{1,2}o\s+de\s+Entrega', adicionais, re.IGNORECASE):
        avisos.append("\"Endereço de Entrega\" dos Dados Adicionais é só o local de entrega do equipamento "
                      "(não é o endereço do tomador nem do prestador) - mantido apenas na discriminação")
    if re.search(_MONEY, adicionais):
        avisos.append("Dados Adicionais citam valor(es) (ex.: frete) que NÃO compõem o \"Total Locação\" "
                      "impresso - não somados ao valor dos serviços; conferir no documento")

    optante = bool(re.search(r'OPTANTE\s+(?:PELO|DO)\s+SIMPLES\s+NACIONAL', corpo, re.IGNORECASE))
    return _nl.NotaLocacao(
        numero=numero, data_emissao=data, discriminacao=discriminacao,
        prestador=prestador, tomador=tomador, valores=valores, itens=itens,
        optante_simples=optante, avisos=avisos,
    )
