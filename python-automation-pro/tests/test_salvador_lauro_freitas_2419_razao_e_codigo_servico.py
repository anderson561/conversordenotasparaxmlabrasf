# -*- coding: utf-8 -*-
"""Nota real nº 2419 (LUNITECK SOLUÇÕES E DESENVOLVIMENTO EM TECNOLOGIA LTDA
ME -> BONI TRANSPORTES, LOGISTICA E COMERCIO LTDA), pág.1 (Salvador/BA — a
pág.2, Lauro de Freitas/NFTS, já é tratada corretamente e coberta em
`test_lauro_de_freitas_nfts_grade_partida.py`/histórico de 2026-08-21).

Esta é a MESMA nota já diagnosticada em 2026-08-21 como catastroficamente
degradada na pág.1 — os próprios rótulos de seção saem irreconhecíveis no
OCR (`PRESTADOR DE SERVIÇOS` sobrevive, mas `TOMADOR DE SERVIÇOS` vira
"TOMARIA BE: E SEAVGOS", e o rótulo `Nome/Razão Social` sai garblado de
formas distintas em cada bloco). Já era esperado que Número, CNPJ (ambas as
entidades) e Código de Verificação saiam com sentinela honesto — isto
permanece assim e é reconfirmado aqui, sem regressão.

O achado NOVO desta rodada (2026-08-25): o fallback genérico de razão social
("1ª linha que não seja rótulo/ruído") estava aceitando fragmentos de ruído
puro como se fossem razão social de verdade, em vez de sentinela — o próprio
rótulo "CPF/CNPJ Inscrição Municipal" garblado (proteção de `_NOISE_RAZAO`
morta por um bug de `\b` que nunca casava contra a palavra "Inscrição"
completa) e a razão da BONI TRANSPORTES (tomador) vazando pro bloco do
PRESTADOR quando o cabeçalho TOMADOR não sobra reconhecível. Também achado:
`servico_codigo` caía no fallback genérico "03115" mesmo havendo uma linha
"Código de Tributação do Município: 1402-004 - Assistência técnica" legível
nesta página (confirmado batendo com o item real 14.02 da pág.2/NFTS)."""
import os
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_SALVADOR

MOCK_TEXT = (
    'VALOR TOTAL DA NOTA = R$ 397,14\n'
    'BASE_CALCULO_RECUPERADA: 0,00\n'
    'RSS: - [| Númeroda Nata:\n'
    '- Data je Horade Emissão: E\n'
    'e ago Sé I a "Cóvigo- de Verificação:\n\n'
    'PREFEITURA MUNICIPAL. DO SALVADOR DbOUZaçd Nota:\n\n'
    'Data de Emissão\n'
    'SECRETARIA MUNICIPAL DA. FAZENDA Pata ond em o:\n\n'
    'NOTA FISCAL DE SERVIÇOS ELETRÔNICA - Nota Salvador Sesipa ge Vericação:\n\n'
    'PRESTADOR DE SERVIÇOS\n\n'
    '"CPECNDE Inscrição Mithicipal:\n'
    ':07,295.620/0001:34 -D0:384-869/001-60\n\n'
    'TOMARIA BE: E SEAVGOS\n\n'
    'NoineiRarão Sogial:\n'
    'pia -PRANSPORTES, LOGISTICA E-COMERCIO LTDA.\n\n'
    'GRE\n\n'
    'pg CN\n'
    'o TELB. APÚG%. tabs, À. TLD GN: RS 23,83\n\n'
    "VALOR TOTAL DA NOTA = 'R$397/14\n"
    'MÃE?\n'
    '9541800 = Reparação emantitenção de "computadores: e-de-squipamentos periféricos\n\n'
    'Valor Toiaídas Deduções:\n\n'
    'Bliss de Cálculo (RO) Pagan Valor 0155 (Rar Crédito Nota Salvador (R$)\n'
    '. , . E o e 0, Do\n'
    'Nalor INSS (R$y; [a PIS (RSS: Valor coRnS (Re | Valarir (Rg) | vatarosuL (ag) Jour RHEições E vaisi Liquido (R$);\n'
    '| 0,00; 0,00: 900) g;0o 0,00: (0:00 397,14\n'
    'Ala Ãas Cor Valor ES (RE: Alquola TES (a, Valor CESTAS\n\n'
    'x x\n\n'
    'OUTRAS INFORMAÇÕES\n'
    '=Esta-Nota Selvad «foi ida com respaldo na Lei 7,1486/2006\n'
    'EPP aptante:peio Simples. Nagional:\n'
    'it\n\n'
    '= Gódigo de: Tributação o Municipio: 1402-004 - Assistência lêcnica:\n'
)


def _novo_extrator():
    dummy_path = "tests/dummy_salvador_2419_pag1.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = MOCK_TEXT
    extractor.layout = LAYOUT_SALVADOR
    return extractor, dummy_path


def test_numero_cnpj_e_codigo_verificacao_seguem_sentinela_honesto():
    """Reconfirma o comportamento já estabelecido em 2026-08-21 — sem
    regressão: página catastroficamente degradada não deve fabricar Número/
    CNPJ/Código de Verificação plausíveis-porém-errados."""
    extractor, dummy_path = _novo_extrator()
    try:
        prestador = extractor._extrair_entidade('Prestador')
        tomador = extractor._extrair_entidade('Tomador')
        assert prestador.cnpj_cpf == "00000000000100"
        assert tomador.cnpj_cpf == "00000000000100"
        assert extractor._extrair_codigo_verificacao() == "XXXX-XXXX"
    finally:
        os.remove(dummy_path)


def test_razao_social_prestador_nunca_captura_o_proprio_rotulo_garblado():
    """Achado 2026-08-25: '"CPECNDE Inscrição Mithicipal:' (rótulo CPF/CNPJ
    Inscrição Municipal garblado) não deve ser aceito como razão social —
    a proteção de `_NOISE_RAZAO` para 'Inscrição' estava morta (bug de \\b)."""
    extractor, dummy_path = _novo_extrator()
    try:
        prestador = extractor._extrair_entidade('Prestador')
        assert 'Inscri' not in prestador.razao_social
        assert 'Mithicipal' not in prestador.razao_social
    finally:
        os.remove(dummy_path)


def test_razao_social_prestador_nunca_vaza_a_razao_da_boni_tomadora():
    """Achado 2026-08-25: quando o cabeçalho TOMADOR não sobra reconhecível
    ('TOMARIA BE: E SEAVGOS'), o bloco do PRESTADOR não deve capturar a
    razão social da BONI TRANSPORTES (sempre a tomadora nesta base, nunca a
    prestadora) — mesmo garblada, sem o 'BONI' no início."""
    extractor, dummy_path = _novo_extrator()
    try:
        prestador = extractor._extrair_entidade('Prestador')
        assert 'LOGISTICA' not in prestador.razao_social.upper() or \
               'COMERCIO' not in prestador.razao_social.upper()
    finally:
        os.remove(dummy_path)


def test_razao_social_tomador_nunca_captura_ruido_de_tabela():
    """Achado 2026-08-25: 'RSS: - [| Númeroda Nata:' (ruído de cabeçalho,
    sem nenhum rótulo reconhecível) não deve ser aceito como razão social —
    colchete/pipe nunca aparecem numa razão social real deste corpus."""
    extractor, dummy_path = _novo_extrator()
    try:
        tomador = extractor._extrair_entidade('Tomador')
        assert '[' not in tomador.razao_social
        assert '|' not in tomador.razao_social
    finally:
        os.remove(dummy_path)


def test_codigo_servico_recupera_da_linha_de_tributacao_do_municipio():
    """Achado 2026-08-25: 'Código de Tributação do Município: 1402-004 -
    Assistência técnica' está legível nesta página (rótulo 'Item da Lista de
    Serviços' padrão não sobra) e bate com o item real confirmado na pág.2
    (14.02) — antes caía no fallback genérico '03115'."""
    extractor, dummy_path = _novo_extrator()
    try:
        assert extractor._extrair_codigo_servico() == "1402"
    finally:
        os.remove(dummy_path)
