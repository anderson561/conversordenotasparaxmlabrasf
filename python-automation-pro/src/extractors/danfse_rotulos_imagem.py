"""DANFSe v1.0 DIGITAL cuja camada de texto traz só os VALORES.

Achado real 2026-11-19 (Notas/Nova pasta/05-Mai-2026_NF_48_RAIMUNDA.pdf,
DANFSe v1.0 emitida pela Prefeitura de São Paulo, RAIMUNDA REGIS ALMEIDA DE
SOUZA (MEI) -> NAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA,
R$ 2.950,00): o gerador do PDF desenhou os rótulos em negrito ("Valor do
Serviço", "Nome / Nome Empresarial", "EMITENTE DA NFS-e"...) como curvas.
O `extract_text()` devolve só os valores, sem relação nenhuma com o rótulo,
e o parser da DANFSe saía com ValorServicos 0,00 e a razão social do
prestador e do tomador = o telefone.

Correção: monta um texto "como o de uma DANFSe normal" juntando as duas
fontes pela POSIÇÃO na página:

* os VALORES vêm da camada digital (pdfminer, caractere a caractere) — exatos,
  nunca OCR;
* os RÓTULOS vêm do OCR da página renderizada (`image_to_data`), descartando
  toda palavra do OCR que caia em cima de texto digital (lá o valor digital
  prevalece).

As palavras das duas fontes são agrupadas em linhas visuais (centro vertical)
e ordenadas por X, reproduzindo a grade "linha de rótulos / linha de
valores" que o parser da DANFSe já lê (mesmo formato do OCR de página
inteira das DANFSe escaneadas, ver `tests/test_danfse_nacional_layout.py`).

O OCR puro da página foi descartado como solução: o Tesseract lê esta
grade coluna a coluna, separa rótulo do valor nas caixas da direita
(Município/CEP/Inscrição/E-mail), engole os "-" de campo vazio e lê o "@" do
e-mail como "Q" — o bairro do prestador saía com os rótulos seguintes
colados e o endereço do tomador virava "Inscrição Municipal".

`mesclar` é PURA (testável sem PDF nem Tesseract); `ler_pagina` faz a I/O.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Sequence, Tuple

_log = logging.getLogger(__name__)

# Fragmento posicionado: (topo, base, x0, x1, texto), em pontos PDF com a
# origem no canto SUPERIOR esquerdo da página.
Fragmento = Tuple[float, float, float, float, str]

# Distância máxima (pt) entre o centro vertical de um fragmento e o da linha
# em formação para entrar nela. Na DANFSe v1.0 a linha de rótulos e a de
# valores da mesma caixa ficam a ~8 pt uma da outra; dentro da mesma linha
# visual o rótulo (fonte menor, negrito) e o valor variam < 1,5 pt.
_TOLERANCIA_LINHA = 3.0

# Lacuna horizontal (pt) que separa duas palavras digitais na mesma linha.
_LACUNA_PALAVRA = 1.5

# Zoom da renderização para o OCR (mesmo de `_ocr_page`).
_ZOOM = 3.0


def palavras_digitais(chars: Sequence[Tuple[float, float, float, float, str]]) -> List[Fragmento]:
    """Agrupa caracteres digitais (topo, base, x0, x1, ch) em palavras."""
    linhas: List[List[Tuple[float, float, float, float, str]]] = []
    for c in sorted(chars, key=lambda c: ((c[0] + c[1]) / 2, c[2])):
        centro = (c[0] + c[1]) / 2
        if linhas:
            ult = linhas[-1]
            centro_ult = sum((x[0] + x[1]) / 2 for x in ult) / len(ult)
            if abs(centro - centro_ult) <= 1.5:
                ult.append(c)
                continue
        linhas.append([c])

    palavras: List[Fragmento] = []
    for linha in linhas:
        linha.sort(key=lambda c: c[2])
        atual: List[Tuple[float, float, float, float, str]] = []
        for c in linha:
            if c[4].isspace():
                if atual:
                    palavras.append(_junta(atual))
                    atual = []
                continue
            if atual and c[2] - atual[-1][3] > _LACUNA_PALAVRA:
                palavras.append(_junta(atual))
                atual = []
            atual.append(c)
        if atual:
            palavras.append(_junta(atual))
    return palavras


def _junta(cs) -> Fragmento:
    return (min(c[0] for c in cs), max(c[1] for c in cs),
            cs[0][2], cs[-1][3], ''.join(c[4] for c in cs))


def _sobrepoe(a: Fragmento, b: Fragmento) -> bool:
    """`a` (palavra do OCR) cobre o centro de `b` (palavra digital)?"""
    cy = (b[0] + b[1]) / 2
    cx = (b[2] + b[3]) / 2
    return a[0] - 1 <= cy <= a[1] + 1 and a[2] - 1 <= cx <= a[3] + 1 \
        or b[0] - 1 <= (a[0] + a[1]) / 2 <= b[1] + 1 and b[2] - 1 <= (a[2] + a[3]) / 2 <= b[3] + 1


def mesclar(digitais: Sequence[Fragmento], ocr: Sequence[Fragmento]) -> str:
    """Texto por linha visual: valores digitais + rótulos do OCR que não
    estão em cima de nenhum texto digital."""
    rotulos = [o for o in ocr if o[4].strip() and not any(_sobrepoe(o, d) for d in digitais)]
    frags = sorted(list(digitais) + rotulos, key=lambda f: (f[0] + f[1]) / 2)

    linhas: List[List[Fragmento]] = []
    for f in frags:
        centro = (f[0] + f[1]) / 2
        if linhas:
            ult = linhas[-1]
            centro_ult = sum((x[0] + x[1]) / 2 for x in ult) / len(ult)
            if abs(centro - centro_ult) <= _TOLERANCIA_LINHA:
                ult.append(f)
                continue
        linhas.append([f])
    return '\n'.join(' '.join(f[4] for f in sorted(l, key=lambda f: f[2])) for l in linhas)


def ler_pagina(pdf_path: str, page_idx: int) -> Optional[str]:
    """Lê a página `page_idx` (0-based): caracteres digitais via pdfminer +
    palavras do OCR via Tesseract, e devolve `mesclar(...)`. `None` se
    qualquer uma das duas fontes falhar (o chamador cai no OCR puro)."""
    try:
        from pdfminer.high_level import extract_pages
        from pdfminer.layout import LTChar
        import io
        import os
        import pymupdf
        import pytesseract
        from PIL import Image

        chars = []
        topo_pagina = x0_pagina = None
        for pagina in extract_pages(pdf_path, page_numbers=[page_idx]):
            x0_pagina, topo_pagina = pagina.bbox[0], pagina.bbox[3]

            def _walk(obj):
                if isinstance(obj, LTChar):
                    chars.append((topo_pagina - obj.y1, topo_pagina - obj.y0,
                                  obj.x0 - x0_pagina, obj.x1 - x0_pagina, obj.get_text()))
                elif hasattr(obj, '__iter__'):
                    for filho in obj:
                        _walk(filho)
            _walk(pagina)
        if not chars:
            return None

        from ..utils.tesseract_config import configurar_pytesseract
        configurar_pytesseract(pytesseract)
        doc = pymupdf.open(pdf_path)
        try:
            pix = doc.load_page(page_idx).get_pixmap(matrix=pymupdf.Matrix(_ZOOM, _ZOOM))
            img = Image.open(io.BytesIO(pix.tobytes('png')))
        finally:
            doc.close()
        dados = pytesseract.image_to_data(img, lang='por', output_type=pytesseract.Output.DICT)
        ocr = []
        for i, txt in enumerate(dados['text']):
            if not txt or not txt.strip():
                continue
            topo = dados['top'][i] / _ZOOM
            esq = dados['left'][i] / _ZOOM
            ocr.append((topo, topo + dados['height'][i] / _ZOOM,
                        esq, esq + dados['width'][i] / _ZOOM, txt.strip()))
        if not ocr:
            return None
        return mesclar(palavras_digitais(chars), ocr)
    except Exception as exc:  # noqa: BLE001 - sem Tesseract/PDF ilegível: chamador cai no OCR puro
        _log.warning('DANFSe sem rótulos: mescla rótulos(OCR)+valores(digitais) falhou na '
                     'página %d (%s); usando OCR puro da página', page_idx + 1, exc)
        return None
