# -*- coding: utf-8 -*-
"""Texto REAL do OCR (Tesseract) da NFS-e de Salvador/BA ESCANEADA — nota real
nº 2436, LUNITECK - SOLUÇÕES E DESENVOLVIMENTO EM TECNOLOGIA LTDA - ME ->
BONI TRANSPORTES, LOGISTICA E COMERCIO LTDA (Data de Emissão 13/08/2026).
Achado via evidência EXTERNA: o Domínio importou o XML gerado com
`Competencia = 7025-04-01` e mostrou "01/04/7025" na coluna Data do relatório
de importação.

Causa raiz: o `raw_text` real (pipeline completo, com recorte de página
prependado à leitura de página inteira — ambos casam o rótulo "COMPETÊNCIA")
tem DUAS ocorrências:
  1. "COMPETÊNCIA: 0/2025" — mês "0" (inválido, só 1 dígito).
  2. "COMPETÊNCIA 04/7025" — mês "04" plausível, mas "2025" virou "7025"
     ("2"→"7").
O regex específico do `LAYOUT_SALVADOR` exige exatamente 2 dígitos de mês
(`\\d{2}/\\d{4}`) — a 1ª ocorrência não casa (só 1 dígito), então `re.search`
(que para no 1º match) casa a 2ª, produzindo `datetime(7025, 4, 1)`. O guard
de "ano com 1 dígito trocado" já existente só dispara quando o MÊS extraído
bate com o mês da Data de Emissão (aqui, mês "04" ≠ mês "08" da nota) —
então o ano absurdo escapava incorrigido.

Fix: novo guard, mais amplo, que dispara sempre que o ano capturado se
afasta da Data de Emissão por mais de 1 ano (não só quando o mês bate) —
nenhuma competência legítima de NFS-e fica a 5000 anos de distância da
própria emissão. Quando isso acontece, usa ano/mês da Data de Emissão em vez
do valor absurdo.

O texto abaixo é cópia literal (via `_extract_via_ocr`, com o recorte de
página real já prependado) do trecho ao redor de "COMPETÊNCIA" na nota
real."""
import os
from datetime import datetime

from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_SALVADOR

MOCK_TEXT = (
    'com respaldo na Lai 7.186/2006\n'
    '- Documento emitido por RE ou EPP onterto pelo Surplos Necrorel\n'
    '- COMPETÊNCIA: 0/2025 (mêsigro)\n\n'
    '- Código de Tributação do Municipio 1402-001 - Assestência técmica\n\n'
    'Simples Necional\n'
    '- COMPETÊNCIA 04/7025 (mêsigros\n'
    '- Código de Tributação do Municipio 1402-001 - Assestência técmica\n'
)


def _novo_extrator(texto):
    dummy_path = "tests/dummy_luniteck_2436_competencia.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = texto
    extractor.layout = LAYOUT_SALVADOR
    return extractor, dummy_path


def test_competencia_ano_absurdo_corrigido_para_ano_da_emissao():
    extractor, dummy_path = _novo_extrator(MOCK_TEXT)
    try:
        data_emissao = datetime(2026, 8, 13, 15, 19, 46)
        competencia = extractor._extrair_competencia(data_emissao)
        assert competencia == datetime(2026, 8, 1)
    finally:
        os.remove(dummy_path)


def test_competencia_legitima_proxima_da_emissao_nao_e_afetada():
    # Guard não deve regredir uma competência legítima, ainda que de mês
    # diferente do da emissão (ex. serviço faturado no mês seguinte),
    # contanto que o ano esteja plausível (a até 1 ano de distância).
    texto = 'Alguma coisa\n- COMPETÊNCIA 12/2025\n- Código de Tributação\n'
    extractor, dummy_path = _novo_extrator(texto)
    try:
        data_emissao = datetime(2026, 1, 10)
        competencia = extractor._extrair_competencia(data_emissao)
        assert competencia == datetime(2025, 12, 1)
    finally:
        os.remove(dummy_path)


def test_ano_trocado_por_1_digito_com_mesmo_mes_continua_corrigido():
    # Regressão do guard já existente (nota CONEX4 nº 00003327): mês igual
    # ao da emissão, ano com 1 dígito trocado — continua usando o ano da
    # emissão.
    texto = 'Alguma coisa\n- COMPETÊNCIA 07/2926\n- Código de Tributação\n'
    extractor, dummy_path = _novo_extrator(texto)
    try:
        data_emissao = datetime(2026, 7, 15)
        competencia = extractor._extrair_competencia(data_emissao)
        assert competencia == datetime(2026, 7, 1)
    finally:
        os.remove(dummy_path)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
