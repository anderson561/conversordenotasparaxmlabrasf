# -*- coding: utf-8 -*-
"""Nota real nº 00003327 (CONEX4 MULTIMÍDIA LIMITADA -> BONI TRANSPORTES,
LOGISTICA E COMERCIO LTDA, R$ 690,00, layout Salvador/BA): diferente de
todos os outros achados de CNPJ corrompido desta base (sempre um erro de
LEITURA de um valor impresso certo), aqui o CNPJ do tomador está ERRADO NA
PRÓPRIA IMAGEM da nota — "04.565.293/0001-99" impresso, confirmado em zoom
alto, reprova o dígito verificador do CNPJ. O usuário confirmou o CNPJ real
como "04.555.283/0001-99" — mesma raiz "04.555.283" já vista em várias
outras notas desta base como tomador fixo/recorrente (ex. notas 6508 e
2150, filiais "0001"/"0003" da MESMA empresa).

Nenhum recorte/zoom recupera esse valor (a sequência "04.555.283" nunca
esteve impressa nesta nota) — corrigido apenas quando o CNPJ extraído já
reprova o checksum E a razão social bate com esta contraparte recorrente,
para não mascarar CNPJs genuinamente diferentes de outras empresas com nome
parecido."""
import os
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_SALVADOR

MOCK_TEXT = (
    'PREFEITURA MUNICIPAL DO SALVADOR\n'
    'NOTA FISCAL DE SERVIÇOS ELETRÔNICA - Nota Salvador\n'
    'TOMADOR DE SERVIÇOS\n'
    'Nome/Razão Social:\n'
    'BONI TRANSPORTES, LOGISTICA E COMERCIO LTDA.\n'
    'CPF/CNPJ:\n'
    '04.565.293/0001-99\n'
    'Endereço:\n'
    'RUA DOUTOR GERINO DE SOUZA FILHO 1025 - Lauro de Freitas - CEP; 42738-200/BA\n'
    'DISCRIMINAÇÃO DOS SERVIÇOS\n'
    'Locação de equipamento áudio e vídeo\n'
    'VALOR TOTAL DA NOTA = R$690,00\n'
)


def _novo_extrator():
    dummy_path = "tests/dummy_boni_cnpj_impresso_errado.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = MOCK_TEXT
    extractor.layout = LAYOUT_SALVADOR
    return extractor, dummy_path


def test_cnpj_de_boni_transportes_corrigido_quando_impresso_errado():
    extractor, dummy_path = _novo_extrator()
    try:
        tomador = extractor._extrair_entidade('Tomador')
        assert tomador.cnpj_cpf == "04555283000199"
    finally:
        os.remove(dummy_path)


def test_correcao_nao_mascara_cnpj_valido_de_outra_empresa_parecida():
    # Guard não deve disparar quando o CNPJ já é válido, mesmo com o mesmo
    # nome (nunca sobrescreve um valor que já passou no checksum).
    texto = MOCK_TEXT.replace('04.565.293/0001-99', '04.555.283/0001-99')
    dummy_path = "tests/dummy_boni_cnpj_ja_correto.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    try:
        extractor = SPPdfExtractor(dummy_path)
        extractor.raw_text = texto
        extractor.layout = LAYOUT_SALVADOR
        tomador = extractor._extrair_entidade('Tomador')
        assert tomador.cnpj_cpf == "04555283000199"
    finally:
        os.remove(dummy_path)
