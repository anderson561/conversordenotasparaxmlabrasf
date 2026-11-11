"""Guarda de pixels antes do render de página inteira (`_render_excede_limite_pil`).

Achado real 2026-11-11 (scan "Digitalização em 6 de nov. de 2026", página
declarada 2336x3520 pt): recortes de zoom fixo renderizavam pixmaps de até
1,9 GB que depois morriam no `Image.open` (DecompressionBombError) e caíam no
`except` do recorte. A guarda pula o render e devolve o MESMO valor de falha.
"""
import io

import pymupdf
import pytest
from PIL import Image

from src.extractors import pdf_extractor as pe
from src.extractors.pdf_extractor import SPPdfExtractor, _render_excede_limite_pil


def _pagina(largura, altura):
    doc = pymupdf.open()
    return doc, doc.new_page(width=largura, height=altura)


def test_pagina_gigante_do_achado_real_excede_so_nos_zooms_altos():
    # 2336x3520 pt: 3x = 7008x10560 (74 Mpx, passa); 6x = 14016x21120 (296 Mpx)
    # e 9x passam do limite de erro do PIL (2 x 89.478.485 px).
    _doc, page = _pagina(2336, 3520)
    assert _render_excede_limite_pil(page, 3.0) is False
    assert _render_excede_limite_pil(page, 6.0) is True
    assert _render_excede_limite_pil(page, 9.0) is True


def test_pagina_a4_nunca_excede_nos_zooms_usados():
    _doc, page = _pagina(595, 842)
    for zoom in (3.0, 6.0, 10.0, 12.0):
        assert _render_excede_limite_pil(page, zoom) is False


def test_fronteira_bate_com_o_pixmap_real_e_com_o_pil(monkeypatch):
    # Tamanho fracionário: o arredondamento tem de ser o do pymupdf.
    _doc, page = _pagina(143.0653, 581.0818)
    pix = page.get_pixmap(matrix=pymupdf.Matrix(0.37, 0.37))
    pixels = pix.width * pix.height
    png = pix.tobytes("png")

    # No limite de erro: o PIL abre (só avisa), a guarda não pula.
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", (pixels + 1) // 2)
    assert pixels <= 2 * Image.MAX_IMAGE_PIXELS
    assert _render_excede_limite_pil(page, 0.37) is False
    with pytest.warns(Image.DecompressionBombWarning):
        Image.open(io.BytesIO(png))

    # Um pixel acima: o PIL recusa, a guarda pula.
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", (pixels - 1) // 2)
    assert pixels > 2 * Image.MAX_IMAGE_PIXELS
    assert _render_excede_limite_pil(page, 0.37) is True
    with pytest.raises(Image.DecompressionBombError):
        Image.open(io.BytesIO(png))


def test_limite_desligado_ou_pagina_sem_rect_nao_pula(monkeypatch):
    _doc, page = _pagina(2336, 3520)
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", None)
    assert _render_excede_limite_pil(page, 9.0) is False
    monkeypatch.undo()
    assert _render_excede_limite_pil(object(), 9.0) is False


@pytest.fixture
def renders(monkeypatch):
    chamadas = []

    def _get_pixmap(self, *a, **k):
        chamadas.append(k.get("matrix"))
        raise RuntimeError("render não deveria acontecer")

    monkeypatch.setattr(pymupdf.Page, "get_pixmap", _get_pixmap)
    return chamadas


def test_recorte_guardado_devolve_valor_de_falha_sem_renderizar(renders):
    _doc, page = _pagina(2336, 3520)  # 6x/8x/10x excedem
    assert SPPdfExtractor._ocr_numero_box_cuiaba(page) == ""
    assert SPPdfExtractor('x.pdf')._ocr_recut_prestador_cnpj_salvador(page) is None
    assert renders == []


def test_recorte_de_metodo_com_pdf_gigante_devolve_dict_vazio(renders, tmp_path):
    doc, _page = _pagina(5000, 5000)  # até o zoom 3 (225 Mpx) excede
    caminho = tmp_path / "gigante.pdf"
    doc.save(str(caminho))
    ext = SPPdfExtractor(str(caminho))
    ext._pagina_hint = 1
    assert ext._ocr_recut_dacte_os_caixas() == {}
    assert ext._ocr_recut_dacte_os_grade() == ''
    assert renders == []


def test_pagina_normal_continua_renderizando(renders):
    # Controle: abaixo do limite a guarda não interfere — o render acontece
    # (aqui ele falha de propósito e o recorte cai no mesmo valor de falha).
    _doc, page = _pagina(595, 842)
    assert SPPdfExtractor._ocr_numero_box_cuiaba(page) == ""
    assert len(renders) == 1


def test_modulo_tem_logger():
    assert pe.logger.name == "src.extractors.pdf_extractor"
