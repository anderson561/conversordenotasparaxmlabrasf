# -*- coding: utf-8 -*-
"""Nota real nº 00003327 (CONEX4 MULTIMÍDIA LIMITADA -> BONI TRANSPORTES,
LOGISTICA E COMERCIO LTDA, R$ 690,00, layout Salvador/BA): o CPF/CNPJ do
PRESTADOR ("09.034.217/0001-97", confirmado pelo usuário e batendo com a
nota irmã — pág. 2 do mesmo PDF, que já extrai esse CNPJ corretamente) sai
como ruído sem nenhum dígito reconhecível na leitura de página inteira — só
a Inscrição Municipal vizinha sobrevive ("00.291.063/001-70"). O próprio
rótulo "PRESTADOR DE SERVIÇOS" sai corrompido ("BRESTADOR DE SERVIÇOS", "B"
no lugar de "P"), então nem o fatiamento genérico de bloco reconhece onde
o prestador começa — cai no fallback de sentinela compartilhado por
prestador E tomador quando nenhum CNPJ válido sobra em lugar nenhum.

Corrigido com `_ocr_recut_prestador_cnpj_salvador`, que reprocessa em zoom
alto só a coluna esquerda da linha do CNPJ; `_ocr_page` prepende o valor
recuperado (já validado por checksum) ANTES do resto do texto, para que a
extração genérica de CNPJ (1º candidato válido vence) encontre esta leitura
limpa primeiro."""
import os
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_SALVADOR

MOCK_TEXT = (
    'CPF/CNPJ:\n09.034.217/0001-97\n\n'
    'PREFEITURA MUNICIPAL DO SALVADOR\n'
    'NOTA FISCAL DE SERVIÇOS ELETRÔNICA - Nota Salvador\n'
    'BRESTADOR DE SERVIÇOS\n'
    'CPF/CNPJ Inscrição Municipal.\n'
    'coisa 00.291.063/001-70 <>\n'
    'Nome/Razão Social\n'
    'CONEX4 MULTIMÍDIA LIMITADA CONEX+\n'
    'Endereço\n'
    'Ala Benevento 106 - PITUBA - Salvador - CEP: 41830-595 - BA\n'
    'E-mail\n'
    'notafiscal@conex4.com.br\n'
    'TOMADOR DE SERVIÇOS\n'
    'Nome/Razão Social\n'
    'BONI TRANSPORTES, LOGISTICA E COMERCIO LTDA.\n'
    'CNPJ/CPF Inscrição Municipal-\n'
    '04.565.293/0001-99 -\n'
    'Endereço\n'
    'RUA DOUTOR GERINO DE SOUZA FILHO 1025 - Lauro de Freitas - CEP; 42738-200/BA\n'
    'DISCRIMINAÇÃO DOS SERVIÇOS\n'
    'Locação de equipamento áudio e vídeo\n'
    'VALOR TOTAL DA NOTA = R$690,00\n'
)


def _novo_extrator():
    dummy_path = "tests/dummy_salvador_cnpj_prestador_ilegivel.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = MOCK_TEXT
    extractor.layout = LAYOUT_SALVADOR
    return extractor, dummy_path


def test_cnpj_prestador_recuperado_do_recorte_dedicado():
    extractor, dummy_path = _novo_extrator()
    try:
        prestador = extractor._extrair_entidade('Prestador')
        assert prestador.cnpj_cpf == "09034217000197"
        assert "CONEX4" in prestador.razao_social.upper()
    finally:
        os.remove(dummy_path)


def test_tomador_nao_herda_cnpj_do_recorte_do_prestador():
    extractor, dummy_path = _novo_extrator()
    try:
        tomador = extractor._extrair_entidade('Tomador')
        assert tomador.cnpj_cpf != "09034217000197"
    finally:
        os.remove(dummy_path)
