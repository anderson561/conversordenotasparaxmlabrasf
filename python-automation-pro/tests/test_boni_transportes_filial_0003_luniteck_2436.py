# -*- coding: utf-8 -*-
"""Texto REAL do OCR (Tesseract) da NFS-e de Salvador/BA ESCANEADA nº 2436
(LUNITECK - SOLUÇÕES E DESENVOLVIMENTO EM TECNOLOGIA LTDA - ME -> BONI
TRANSPORTES, LOGISTICA E COMERCIO LTDA, R$397,14). Reportado pelo usuário
(2026-09-15) como "Luniteck tomador do serviço incorreto".

Causa raiz: a página desta nota sai IMPRESSA DUAS VEZES no OCR (2 passadas
concatenadas, achado já visto em outras notas Salvador). Na 1ª passada, o
CNPJ do tomador some a barra por completo ("04.555 28310003-50" — sem
nenhum "/", não casa o padrão de CNPJ formatado, gera ZERO candidatos). A
extração usa o bloco da 1ª ocorrência de "TOMADOR DE SERVIÇOS" (a passada
degradada), então cai direto no guard de contraparte conhecida da BONI
TRANSPORTES sem NENHUM candidato de CNPJ para comparar — e o guard, até
então, sempre devolvia a filial fixa "0001-99" (confirmada para uma nota
DIFERENTE, CONEX4 MULTIMÍDIA — ver `test_boni_transportes_cnpj_impresso_
errado.py`) independente de qual filial a nota realmente mostra.

Mas esta empresa (BONI TRANSPORTES) tem PELO MENOS 2 filiais reais válidas
neste corpus — "0001-99" e "0003-50" (esta última confirmada de forma
independente em 3 outras notas da MESMA sessão: INSTITUIÇÃO ASSISTENCIAL,
VALOR COMÉRCIO, SBS SOLUÇÕES, sempre com o mesmo endereço "RUA MARIA
QUITERIA ... Lauro de Freitas"). A 2ª passada de OCR desta MESMA nota traz
um candidato bem formado mas com 1 dígito trocado: "04.555.293/0003-50"
("8"→"9" em ".283"), só 1 dígito de distância de "0003-50" — MUITO mais
próximo dela que de "0001-99" (que difere em quase todos os dígitos finais).
O guard antigo, restrito ao bloco da 1ª passada, nunca via esse candidato e
sempre "corrigia" para a filial ERRADA. Fix: a busca do candidato passa a
varrer o TEXTO INTEIRO (não só o bloco da entidade), descarta o CNPJ já
extraído do prestador e usa o candidato mais próximo (por distância de
dígitos) de QUALQUER uma das 2 filiais conhecidas — só cai no default
"0001-99" quando nada bate perto o suficiente.

O texto abaixo é cópia literal (via `_extract_via_ocr`) das 2 passadas
concatenadas da nota real."""
import os

from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_SALVADOR

MOCK_TEXT = (
    'CPF/CNPJ:\n'
    '07.295.620/0001-44\n\n'
    'TOMADOR DE SERVIÇOS\n\n'
    'Norme/Razão Soo\n\n'
    'BONI TRANSPORTES. LOGISTICA E COMERCIO LTDA.\n\n'
    'CPFICNPU inscrição Municipal:\n'
    '04.555 28310003-50 —\n\n'
    'Endereço\n'
    'RUA IA QUITERIA 265, GALPÃO ITINGA - Lauro de Freitas « CEP: 42733-Z05/BA\n'
    'E-mail\n\n'
    'PISENIMNAÇÃO POR SENVIÇOS\n\n'
    'TELb. Aprox. tab. A. III - 8N, R$ 23,83\n\n'
    'VALOR TOTAL DA NOTA = R$397,14\n\n'
    'PREFEITURA MUNICIPAL DO SALVADOR 00002436\n'
    'NOTA FISCAL DE SERVIÇOS ELETRÔNICA - Nota Salvador\n'
    'PRESTADOR DE SERVIÇOS\n'
    'CPFACNPJ inserção Municipal\n'
    '07.295 .620/0001-44 00.384.869/001.50 EB\n'
    'Nomeirarão Soçial\n'
    'da - SOLUCOES E DESENVOLVIMENTO EM TECNOLOGIA LTDA - ME N a”\n'
    'TOMADOR DE SERVIÇOS\n'
    'NormeiRação Sociêl\n'
    'BONI TRANSPORTES. LOGISTICA E COMERCIO LTDA.\n'
    'CPEACNPJ Inscrição Municipal\n'
    '04,555 293/0003-50 —\n'
    'Endereço\n'
    'RUA MÁRIA QUITERIA 265, GALPAO ITINGA - Lauro de Freitas - CEP: 42738-Z05/BA\n'
    'E-mail\n'
    'PISSRIMINAÇÃO DOS SERVIÇOS\n'
    'VALOR TOTAL DA NOTA = R$397,14\n'
)


def _novo_extrator():
    dummy_path = "tests/dummy_luniteck_2436_boni_filial.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = MOCK_TEXT
    extractor.layout = LAYOUT_SALVADOR
    extractor._cnpj_prestador_extraido = "07295620000144"
    return extractor, dummy_path


def test_tomador_boni_transportes_resolve_para_a_filial_0003_50():
    extractor, dummy_path = _novo_extrator()
    try:
        tomador = extractor._extrair_entidade('Tomador')
        assert tomador.cnpj_cpf == "04555283000350"
    finally:
        os.remove(dummy_path)


def test_prestador_luniteck_nao_afetado_pelo_guard_da_boni():
    extractor, dummy_path = _novo_extrator()
    try:
        prestador = extractor._extrair_entidade('Prestador')
        assert prestador.cnpj_cpf == "07295620000144"
    finally:
        os.remove(dummy_path)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
