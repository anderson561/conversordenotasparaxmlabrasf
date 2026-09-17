# -*- coding: utf-8 -*-
"""Nota real nº 33908 (VALOR COMÉRCIO E SERVIÇOS DE INFORMÁTICA LTDA -> BONI
TRANSPORTES LOGÍSTICA E COMÉRCIO LTDA, layout Salvador/BA, mesma nota de
`test_salvador_valor_comercio_razao_e_valores_zerados.py`) — reportado pelo
usuário (2026-09-15), após a correção da razão social/valores, como "número
da nota fiscal incorreto": o XML saía com `Numero=46345` em vez do real
"33908" (o próprio nome do arquivo do PDF).

Causa raiz: o OCR desta nota lê o título como "PREFEITURA MUNICIPAL DE
SALVADOR" (preposição "DE"). O gate que decide se `_ocr_page` roda os
recortes dedicados do layout Salvador (caixa de cabeçalho via
`_ocr_header_box_salvador`, votação do Número da Nota via
`_ocr_numero_nota_salvador_votado`, recuts de tomador/prestador/CNPJ)
exigia "PREFEITURA MUNICIPAL DO SALVADOR" (preposição "DO") ou "Nota
Salvador" — nenhum dos dois aparece nesta nota. TODO o bloco de recortes
Salvador-específicos era pulado por completo, mesmo a página já tendo sido
roteada para `LAYOUT_SALVADOR` pela detecção de layout (que usa o padrão
bem mais tolerante `PREFEITURA.*SALVADOR`, sem exigir uma preposição
específica). Sem o recorte de cabeçalho, o texto nunca ganha uma ocorrência
de "Número da Nota" reconhecível, e `_extrair_numero` (LAYOUT_SALVADOR)
nunca encontra o rótulo — o número final do XML então vinha de outro lugar
inteiramente (não investigado nesta correção, mas o valor observado,
"46345", corresponde ao "Pedido Numero:" impresso dentro da discriminação
do serviço, um identificador interno do prestador, não o número da nota).

Fix: o gate que ativa os recortes passou a tolerar "DE" e "DO" (mesma
tolerância já usada na detecção de layout). A troca do texto de página
inteira por uma releitura em PSM 6 (mecanismo distinto, dentro do mesmo
bloco, motivado pela nota BDP LOGÍSTICA — ver
`test_salvador_bdp_psm_pagina_inteira.py`) continua restrita à condição
ORIGINAL ("DO"/"Nota Salvador"): testada contra esta mesma nota, aquela
releitura introduz ruído de uma marca d'água/carimbo de fundo na célula
"Nome/Razão Social" e uma 5ª coluna espúria na grade de Alíquota/ISS que
nenhum parser reconhece, zerando valores que a leitura padrão já extraía
certos — sem esse gate mais estreito, a correção do Número da Nota
regrediria a Razão Social e a grade de valores desta mesma nota.

O texto abaixo reproduz o texto final composto que `_ocr_page` produz
DEPOIS da correção (com o bloco "Número da Nota:\n33908" prependado pelo
recorte de cabeçalho/votação, como confirmado contra o PDF real) — mesmo
padrão de fixture usado em `test_salvador_bdp_psm_pagina_inteira.py`, que
trava o resultado da extração sem precisar rodar Tesseract no teste."""
import os

from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_SALVADOR

MOCK_TEXT_COM_RECUT_DE_CABECALHO = (
    'Número da Nota:\n'
    '33908\n\n'
    'PREFEITURA MUNICIPAL DE SALVADOR\n\n'
    'SECRETARIA MUNICIPAL DA FAZENDA\n\n'
    '03/08/2026 12:02:24\n'
    'NOTA FISCAL DE SERVIÇOS ELETRÔNICA - NFS-e Código de Verificação\n\n'
    'RPSNº 41048 Série: 1 Emitidoem: 03/08/2026 12:02:24 HLKJTGCY\n\n'
    'PRESTADOR DE SERVIÇOS\n\n'
    'CPFICNPJ: Inscrição Municipal:\n'
    '07.227.674/0001-72 2564471001-78\n'
    'Nome/Razão Social:\n\n'
    'VALOR COMERCIO E SERVICOS DE INFORMATICA LTDA\n\n'
    'Endereço:\n\n'
    'LADEIRA DO ACUPE/SUBSOLO 104 ACUPE DE BROTAS Salvador BA\n'
    'TOMADOR DE SERVIÇOS\n\n'
    'CPFICNPJ: Inscrição Municipal:\n'
    '04.555.283/0003-50\n\n'
    'Nome/Razão Social:\n\n'
    'BONI TRANSPORTES LOGISTICA E COMÉRCIO LTDA\n'
    'DISCRIMINAÇÃO DOS SERVIÇOS\n\n'
    'ASSESSORIA EM INFORMATICA REFERENTE MES AGOSTO 2026 Quantidade 1 Unit R$ 583.00 Total R$ 583.00\n\n'
    'Pedido Numero: 46345\n\n'
    'VALOR TOTAL DA NOTA FISCAL R$ 583,00\n\n'
)

MOCK_TEXT_SEM_RECUT_DE_CABECALHO = MOCK_TEXT_COM_RECUT_DE_CABECALHO.replace(
    'Número da Nota:\n33908\n\n', ''
)


def _novo_extrator(texto):
    dummy_path = "tests/dummy_valor_comercio_numero_gate.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = texto
    extractor.layout = LAYOUT_SALVADOR
    return extractor, dummy_path


def test_numero_da_nota_prefere_o_recorte_de_cabecalho_ao_pedido_numero_interno():
    extractor, dummy_path = _novo_extrator(MOCK_TEXT_COM_RECUT_DE_CABECALHO)
    try:
        assert extractor._extrair_numero() == "33908"
    finally:
        os.remove(dummy_path)


def test_sem_o_recorte_de_cabecalho_o_pedido_numero_interno_vaza_para_o_numero_da_nota():
    # Documenta o sintoma exato do bug (2026-09-15): sem o prepend do
    # recorte dedicado (o efeito do gate "DO"-apenas nunca disparar para
    # esta nota), não sobra nenhuma ocorrência reconhecível de "Número da
    # Nota" no texto - `_extrair_numero` cai no sentinela, não no valor
    # errado "46345" (que exigiria uma âncora própria de "Pedido Numero",
    # inexistente no LAYOUT_SALVADOR - o valor errado observado no XML real
    # vinha de outro extrator/fallback, fora do escopo desta correção).
    extractor, dummy_path = _novo_extrator(MOCK_TEXT_SEM_RECUT_DE_CABECALHO)
    try:
        assert extractor._extrair_numero() != "33908"
    finally:
        os.remove(dummy_path)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
