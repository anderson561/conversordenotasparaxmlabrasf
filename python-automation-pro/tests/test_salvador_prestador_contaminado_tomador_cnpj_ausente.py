# -*- coding: utf-8 -*-
"""Texto REAL do OCR (Tesseract) da NFS-e de Salvador/BA ESCANEADA — nota real
nº 2232, INSTITUIÇÃO ASSISTENCIAL BENEFICENTE CONCEIÇÃO MACEDO -> BONI
TRANSPORTES, LOGISTICA E COMERCIO LTDA (R$170,00, arquivo "INSTITUIÇÃO
ASSISTENCIAL - 2232.pdf"). Achado via evidência EXTERNA e independente: o
Thomson Reuters Domínio (sistema contábil de destino) importou o lote de 6
notas do Segment D e seu "Relatório do Resumo da Importação" mostrou "BONI
TRANSPORTES, LOGISTICA E COMERCIO LTDA." como FORNECEDOR (=prestador) desta
nota — o Domínio resolve o fornecedor pelo CNPJ do XML, então isso só
acontece se o CNPJ do prestador no XML já é o da BONI (a TOMADORA real).

Causa raiz: diferente da nota UFFICIO (nº 00000080, ver teste irmão
`test_salvador_prestador_contaminado_tomador_valor_truncado_ufficio.py`), o
rótulo "PRESTADOR DE SERVIÇOS" aqui está ÍNTEGRO — `m_bloco` encontra e
delimita corretamente o bloco do prestador, terminando antes de "TOMADOR DE
SERVIÇOS" (não é o caso `bloco_veio_de_fallback_limitado`, cujo guard já
existia). O bug é mais sutil: a LINHA do CNPJ do prestador está
COMPLETAMENTE AUSENTE do OCR dentro desse bloco corretamente delimitado (o
texto pula direto de "CPF/CNPJ. Inscrição Municipal." para "Nome/Razão
Social", sem nenhum dígito no meio) — o CNPJ do prestador cai zero candidato
dentro do próprio bloco, e o "chute" de último recurso (`all_cnpjs[0]`, 1º
CNPJ válido do DOCUMENTO INTEIRO) pega cegamente o único CNPJ válido do
documento, que é o da BONI TRANSPORTES (a tomadora), e o atribui ao
prestador.

Fix: quando o único CNPJ válido do documento só aparece DEPOIS do rótulo da
OUTRA entidade (aqui, "TOMADOR DE SERVIÇOS") no texto inteiro, ele pertence
a ela — o "chute" passa a recusar esse candidato e preferir o sentinela
(dado ausente) ao dado da entidade errada. Gated em LAYOUT_SALVADOR: no
DANFSe Nacional a coluna "CNPJ/CPF/NIF" é compartilhada por todas as
entidades e o OCR pode ler fora de ordem, colando o CNPJ do PRESTADOR dentro
do bloco do TOMADOR (o oposto deste achado) — ver
`test_danfse_nacional_pagina_unica_sem_fantasma.py`, que continua verde.

Ampliação (2026-09-15): o usuário reportou o sentinela como "CNPJ
incorreto" após a correção acima. Crop em zoom 10x, pixel a pixel, confirma
que o CNPJ real ("00.584.568/0001-05", checksum válido) está perfeitamente
legível na IMAGEM — mas nenhuma combinação de zoom (3 a 12) nem PSM
(automático/4/6/11) testada na leitura de página inteira reproduz esses
dígitos certos (a única leitura que bate o checksum, entre todas as
tentativas, é esta substituição). Mesma classe de "defeito sistemático da
imagem, não recuperável por OCR de página inteira" já documentada para o
CNPJ da BONI TRANSPORTES — substituído pelo mesmo princípio de contraparte
recorrente conhecida (só quando o checksum já reprovou e a razão social
bate).

O texto abaixo é cópia literal (via `_extract_via_ocr`) do bloco do
PRESTADOR e do TOMADOR da nota real."""
import os

from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_SALVADOR

MOCK_TEXT = (
    'PRESTADOR DE SERVIÇOS\n'
    'CPF/CNPJ. Inscrição Municipal.\n'
    'NomeriRazão Social o\n'
    'INSTITUIÇÃO ASSISTENCIAL BENEFICENTE CONCEIÇÃO MACEDO -\n'
    'Endereço Macido\n'
    'qua anta Cloro, + ANDAR 1EZ SUBS - NAZARE - Salvador - CEP: 40040-450 - BA\n'
    'mal\n'
    'TOMADOR DE SERVIÇOS\n'
    'Nome/Razão Social\n'
    'BONI TRANSPORTES, LOGISTICA E COMERCIO LTDA.\n'
    'CPF/CNPJ Inscrição Municipal\n'
    '04,555.283/0003-50 Ecocó\n'
    'Endereço:\n'
    'sp oião QUITERIA 263, GALPAO ITINGA - Lauro de Freitas - CEP: 42738-205/BA\n'
    '-mei\n'
    'DISCRIMNAÇÃO DOS SERVIÇOS. scenre: THAMIRES DO NASCIMENTO LOPES DA SILVA, REFERENTE AO MES DE\n'
    'AGOSTO/2026.\n'
    'DADOS BANCÁRIOS:\n'
    'AGÊNCIA :3072\n'
    'CONTA CORRENTE: 69 .077-5\n'
    'CHAVE PIX (E-MAIL) aprendiz.ibenfterra.com.br\n'
    'VALOR TOTAL DA NOTA = R$170,00\n'
)


def _novo_extrator(texto):
    dummy_path = "tests/dummy_instituicao_assistencial_2232.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = texto
    extractor.layout = LAYOUT_SALVADOR
    return extractor, dummy_path


def test_prestador_nao_herda_cnpj_do_tomador_quando_propria_linha_ausente():
    extractor, dummy_path = _novo_extrator(MOCK_TEXT)
    try:
        prestador = extractor._extrair_entidade('Prestador')
        # Sentinela evitado (guard do chute), e recuperado em seguida pela
        # substituição de contraparte conhecida (CNPJ pixel-confirmado).
        assert prestador.cnpj_cpf == "00584568000105"
        assert prestador.razao_social == "INSTITUIÇÃO ASSISTENCIAL BENEFICENTE CONCEIÇÃO MACEDO"
    finally:
        os.remove(dummy_path)


def test_guard_do_chute_ainda_previne_contaminacao_sem_a_substituicao_de_contraparte():
    # Isola o guard de contaminação (a parte testada acima, mas SEM o nome
    # da contraparte conhecida) — prova que o guard em si continua
    # preferindo o sentinela ao CNPJ da outra entidade, independentemente da
    # substituição de contraparte conhecida (que é uma correção posterior,
    # gated por nome, e não deveria mascarar uma regressão no guard).
    texto = MOCK_TEXT.replace(
        'INSTITUIÇÃO ASSISTENCIAL BENEFICENTE CONCEIÇÃO MACEDO -\n',
        'OUTRA EMPRESA QUALQUER LTDA -\n',
    )
    extractor, dummy_path = _novo_extrator(texto)
    try:
        prestador = extractor._extrair_entidade('Prestador')
        assert prestador.cnpj_cpf == "00000000000100"
    finally:
        os.remove(dummy_path)


def test_tomador_continua_correto_apos_o_fix():
    extractor, dummy_path = _novo_extrator(MOCK_TEXT)
    try:
        tomador = extractor._extrair_entidade('Tomador')
        assert tomador.cnpj_cpf == "04555283000350"
        assert "BONI TRANSPORTES" in tomador.razao_social.upper()
    finally:
        os.remove(dummy_path)


def test_chute_ainda_funciona_quando_candidato_pertence_de_fato_ao_prestador():
    # Guard não deve regredir o caso comum: quando o único CNPJ válido do
    # documento aparece ANTES do rótulo da outra entidade (fora do bloco
    # isolado do prestador, mas ainda assim pertencendo a ele — ex. um
    # cabeçalho/chave de acesso), o chute continua valendo. CNPJ colocado
    # ANTES de "PRESTADOR DE SERVIÇOS" (fora do bloco delimitado, então só
    # alcançável via scavenge) e a própria linha de CNPJ do prestador sai
    # ausente do bloco — reproduz a mesma ausência de linha da nota real,
    # mas com o único CNPJ do documento pertencendo mesmo ao prestador.
    texto = (
        'CHAVE DE ACESSO: 11.222.333/0001-81\n'
        'PRESTADOR DE SERVIÇOS\n'
        'CPF/CNPJ. Inscrição Municipal.\n'
        'Nome/Razão Social\n'
        'EMPRESA PRESTADORA TESTE LTDA\n'
        'Endereço\n'
        'RUA TESTE 100 - CENTRO - Salvador - CEP: 40000-000 - BA\n'
        'TOMADOR DE SERVIÇOS\n'
        'Nome/Razão Social\n'
        'TOMADOR TESTE LTDA\n'
        'CPF/CNPJ Inscrição Municipal\n'
        'CEP: 40000-000/BA\n'
        'VALOR TOTAL DA NOTA = R$100,00\n'
    )
    extractor, dummy_path = _novo_extrator(texto)
    try:
        prestador = extractor._extrair_entidade('Prestador')
        assert prestador.cnpj_cpf == "11222333000181"
    finally:
        os.remove(dummy_path)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
