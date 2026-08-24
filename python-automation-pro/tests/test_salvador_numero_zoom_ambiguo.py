# -*- coding: utf-8 -*-
"""Nota real nº 00003327 (CONEX4 MULTIMÍDIA LIMITADA -> BONI TRANSPORTES,
LOGISTICA E COMERCIO LTDA, R$ 690,00, layout Salvador/BA): o recorte dedicado
do cabeçalho (`_ocr_header_box_salvador`, zoom 4.5x) lê consistentemente
"09003327" (dígito "0"->"9" trocado, confirmado contra a imagem real) em todo
PSM testado (4, 6, 11) — artefato de renderização daquele zoom específico
para esta nota, não ruído de amostra única: nos zooms 3x/6x/8x/10x o valor
sai correto ("00003327") em todos.

Corrigido com `_ocr_numero_nota_salvador_votado`, que reamostra a mesma caixa
em zooms distintos e usa maioria simples; `_ocr_page` prepende o valor
apurado ANTES do recorte de cabeçalho de zoom único, para que
`_extrair_numero` (1º match vence) prefira o valor por maioria."""
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_SALVADOR


def _make_extractor(texto: str) -> SPPdfExtractor:
    ext = SPPdfExtractor.__new__(SPPdfExtractor)
    ext.pdf_path = 'fake.pdf'
    ext.raw_text = texto
    ext.layout = LAYOUT_SALVADOR
    return ext


def test_numero_por_maioria_prevalece_sobre_recorte_de_zoom_unico_ambiguo():
    # Simula `_ocr_page` já com o valor apurado por maioria (via
    # `_ocr_numero_nota_salvador_votado`) prependido antes do recorte de
    # cabeçalho de zoom único (que aqui leu o dígito errado).
    texto = (
        'Número da Nota:\n00003327\n\n'
        'Número da Nota:\n\nADOR 09003327\n'
        'Data e Hora de Emissão. *\n22/07/2026 09:43:32\n\n'
        'aC dee Código de Verificação:\n\n'
        'PREFEITURA MUNICIPAL DO SALVADOR\n'
        'NOTA FISCAL DE SERVIÇOS ELETRÔNICA - Nota Salvador\n'
    )
    ext = _make_extractor(texto)
    assert ext._extrair_numero() == "00003327"


def test_numero_sem_valor_votado_mantem_comportamento_anterior():
    # Sem o prepend do valor apurado por maioria (recut indisponível/exceção),
    # o comportamento permanece o mesmo de antes: 1ª ocorrência do rótulo.
    texto = (
        'Número da Nota:\n\nADOR 00004852\n'
        'Data e Hora de Emissão:\n21/07/2026 10:00:00\n\n'
        'PREFEITURA MUNICIPAL DO SALVADOR\n'
    )
    ext = _make_extractor(texto)
    assert ext._extrair_numero() == "00004852"
