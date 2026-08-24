# -*- coding: utf-8 -*-
"""Layout Lauro de Freitas/BA (`lauro_de_freitas_ba`), variante NFTS — nota
real nº 20265323 (pág. 2 do mesmo PDF de 2 páginas da nota nº 122/VITORIOS
EMPILHADEIRAS -> BONI TRANSPORTES, ver `test_simoes_filho_layout.py` para a
pág. 1). 3 achados novos nesta nota, distintos dos já cobertos por
`test_lauro_de_freitas_*` anteriores:

1. Rótulo "Nome/Razão" do PRESTADOR sai "Noma/Razão" (OCR) — não reconhecido
   pela regex antiga, prestador caía em "Prestador Não Identificado" mesmo
   com o nome real presente no texto.
2. "Bairro: Itinga Município: LAURO DE FREITAS UF. BA" (ponto em vez de
   dois-pontos depois de "UF") — o lookahead antigo só tolerava "UF:",
   vazando "UF. BA" inteiro para dentro do valor de Município do TOMADOR.
3. A grade "Valor Total Deduções (R$) Base de Cálculo (R$) Alíquota (%)
   Valor do ISS (R$) ISSQN Retido (R$)" sai com o cabeçalho e os 3 últimos
   valores completamente ausentes da leitura (zoom 3/5/6, testado
   exaustivamente) — só "0,00" (Dedução) e "440,00" (Base) sobrevivem, sem
   nenhum "Sim"/"Não" para a coluna final. Nem o fallback "grade completa"
   nem o fallback "variante MEI com asterisco" (já existentes) casam; um 3º
   fallback busca os 2 últimos números em formato monetário na janela entre
   "ITEM DA LISTA DE SERVIÇOS" e "VALOR LÍQUIDO DA NOTA FISCAL".
"""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_LAURO_FREITAS

MOCK_TEXT = (
    'MUNICIPIO DE LAURO DE FREITAS Número da Nota\n'
    'Secretaria da Fazenda 20265323\n'
    'Coordenação Tributária Data e Hora de Emissão\n'
    'Nota Fiscal Eletrônica do Tomador de Serviços - NFTS 27/07/2026 09:30:18\n\n'
    'Código de Verificação\n'
    'A sutenfodade dasta Nota Fiscal Eletrônica do Tomador de Si Serços, poderá ser confemada na págne da MUNICIPIO DE LAURO DE FREITAS na B99959205\n'
    'Internet, no endereço hilp:iwww laurodefraites De qgov.br\n\n'
    'TOMADOR DE SERVIÇOS\n\n'
    'CPFICNPJ: 04.555.283/0001-99\n\n'
    'Inscrição 0000365211\n\n'
    'Nome/Razão BONI TRANSPORTES, LOGISTICA E COMERCIO LTDA\n'
    'Endereço: Rua Gerino De Souza Filho, 11, ACESSO PELA RUA JOELMA S MENDES LT 08 A 09 QD A\n'
    'Bairro: Itinga Município: LAURO DE FREITAS UF. BA\n'
    'CEP: 42738-200 Email.\n\n'
    'PRESTADOR DE SERVIÇOS\n\n'
    'CPFICNPJICRI. 50.949.432/0001-11\n\n'
    'inscrição Estadual 0\n\n'
    'Inscrição Inscrição Estadual:\n'
    'Noma/Razão VITORIOS EMPILHADEIRAS COMERCIO E SERVIÇOS LTDA\n'
    'Endereço: AVENIDA DA REPUBLICA, 126,\n\n'
    'Bairro: CIA Municipio: SIMOES FILHO\n'
    'CEP: 43700-000\n\n'
    'DISCRIMINAÇÃO DOS SERVIÇOS\n'
    'Serviço técnico realizado em empilhadeira.\n\n'
    'VALOR TOTAL DA NOTA FISCAL : R$\n'
    'CNAE\n\n'
    'ITEM DA LISTA DE SERVIÇOS: ( Lei Municipal 1572/2015 )\n\n'
    '14.01 - Lubrificação, limpeza, lustração, revisão, carga e recarga, conserto, restauração, blindagem, manutenção e conservação de\n'
    'máquinas, veículos, aparelhos, equipamentos, motores, elevadores ou de qualquer objeto\n\n'
    'a E e io\n'
    '0,00 440,00\n\n'
    'VALOR LÍQUIDO DA NOTA FISCAL : R$\n\n'
    'INFORMAÇÕES COMPLEMENTARES\n'
    'Competência: 07/2026 - Tributado fora do Município de Lauro de Freitas - Responsável Recolhimento: Prestador\n\n'
    'Documento Fiscal; Número: 122.\n'
    'Optante pelo Simples Nacional\n\n'
    'Percentual de Total da Dedução:\n'
)


def _novo_extrator():
    dummy_path = "tests/dummy_lauro_freitas_nfts_20265323.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = MOCK_TEXT
    extractor.layout = LAYOUT_LAURO_FREITAS
    return extractor, dummy_path


def test_prestador_recuperado_apesar_do_rotulo_noma_razao():
    extractor, dummy_path = _novo_extrator()
    try:
        prestador = extractor._extrair_entidade('Prestador')
        # BUG CORRIGIDO: "Nome"->"Noma" não era reconhecido, caía em
        # "Prestador Não Identificado" mesmo com o nome real presente.
        assert prestador.razao_social != "Prestador Não Identificado"
        assert "VITORIOS EMPILHADEIRAS" in prestador.razao_social
        assert prestador.cnpj_cpf == "50949432000111"
    finally:
        os.remove(dummy_path)


def test_tomador_municipio_nao_engole_uf_com_ponto():
    extractor, dummy_path = _novo_extrator()
    try:
        tomador = extractor._extrair_entidade('Tomador')
        # BUG CORRIGIDO: "UF." (ponto) não era reconhecido pelo lookahead
        # (só "UF:"), então "LAURO DE FREITAS UF. BA" inteiro virava o
        # Município.
        assert tomador.endereco.municipio == "LAURO DE FREITAS"
        assert tomador.endereco.uf == "BA"
        assert tomador.endereco.codigo_municipio == "2919207"
    finally:
        os.remove(dummy_path)


def test_valores_recupera_deducao_e_base_quando_grade_degrada_por_completo():
    extractor, dummy_path = _novo_extrator()
    try:
        valores = extractor._extrair_valores()
        # BUG CORRIGIDO: nem o cabeçalho da grade nem o "Sim"/"Não" da
        # coluna ISSQN Retido sobrevivem nesta leitura — sem o 3º fallback,
        # tudo caía em 0,00, inclusive a Base de Cálculo (que É recuperável).
        assert valores.valor_deducoes == 0.0
        assert valores.base_calculo == 440.0
        assert valores.valor_servicos == 440.0
        # Alíquota/ISS ficam no sentinela nesta página específica (não são
        # recuperáveis nesta leitura) — a nota irmã (Simões Filho, pág. 1)
        # tem os valores completos para a mesma transação.
        assert valores.aliquota == 0.0
        assert valores.valor_iss == 0.0
    finally:
        os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
