# -*- coding: utf-8 -*-
"""`_extrair_competencia`: quando o OCR troca 1 dígito do ANO da Competência
mas o MÊS bate com a Data de Emissão (já confiável), usar o ano da Data de
Emissão em vez do ano lido errado — guard que só existia gated a
`LAYOUT_SALVADOR` (achado original: nota nº 00003327/CONEX4 MULTIMÍDIA,
"COMPETÊNCIA 07/2926" em vez de "07/2026", "0"→"9").

Achado real 2026-08-25 (nota nº 202600000016746, layout Lauro de Freitas/BA
3ª variante, MAG COMERCIO VAREJISTA → BONI LOGISTICA): o MESMO padrão de
erro ("Competência: 24/07/2025" em vez de "24/07/2026") saiu incorreto no
XML final (`<Competencia>2025-07-24</Competencia>`) porque o guard nunca
rodava fora de `LAYOUT_SALVADOR` — `LAYOUT_LAURO_FREITAS` não tem branch
próprio em `_extrair_competencia`, cai direto no fallback genérico
(`_extrair_competencia_generica`), que não tem nenhuma validação cruzada
contra a Data de Emissão. Generalizado: o guard agora roda incondicionalmente
no fim de `_extrair_competencia`, depois de QUALQUER branch específica de
layout (inclusive o fallback genérico) já ter tentado, não só em Salvador.
"""
import os
import pytest
from datetime import datetime
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_LAURO_FREITAS


def _novo_extrator(raw_text):
    dummy_path = "tests/dummy_competencia_ano_trocado.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = raw_text
    return extractor, dummy_path


def test_competencia_usa_ano_da_data_emissao_fora_de_salvador():
    """Layout SEM branch próprio em `_extrair_competencia` (cai no fallback
    genérico) — o guard de ano trocado precisa rodar mesmo assim."""
    extractor, dummy_path = _novo_extrator(
        "LFV3_DATA_EMISSAO: 24/07/2026 10:27:01\n"
        "Competência: 24/07/2025\n"
    )
    try:
        extractor.layout = LAYOUT_LAURO_FREITAS
        data_emissao = extractor._extrair_data_emissao()
        assert data_emissao.year == 2026 and data_emissao.month == 7
        competencia = extractor._extrair_competencia(data_emissao)
        # BUG CORRIGIDO: saía 2025-07-24 (ano lido errado do OCR), mesmo com
        # a Data de Emissão já confiável mostrando 2026 no mesmo mês.
        assert competencia.year == 2026
        assert competencia.month == 7
    finally:
        os.remove(dummy_path)


def test_competencia_ano_genuinamente_diferente_nao_e_sobrescrita():
    """Guard só corrige quando MÊS bate — uma competência de um mês
    genuinamente diferente (ex. nota de janeiro para dezembro do ano
    anterior) não deve ser mexida."""
    extractor, dummy_path = _novo_extrator("Competência: 15/12/2025\n")
    try:
        extractor.layout = LAYOUT_LAURO_FREITAS
        data_emissao = datetime(2026, 1, 10, 9, 0, 0)
        competencia = extractor._extrair_competencia(data_emissao)
        assert competencia.year == 2025
        assert competencia.month == 12
    finally:
        os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
