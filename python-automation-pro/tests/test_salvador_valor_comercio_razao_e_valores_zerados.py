# -*- coding: utf-8 -*-
"""Texto REAL do OCR (Tesseract) da NFS-e de Salvador/BA ESCANEADA — nota real
nº 46345 (arquivo "VALOR COMERCIO - 33908.pdf"), VALOR COMÉRCIO E SERVIÇOS DE
INFORMÁTICA LTDA -> BONI TRANSPORTES LOGÍSTICA E COMÉRCIO LTDA (R$583,00).
Reportado pelo próprio Thomson Reuters Domínio (Relatório do Resumo da
Importação, mesmo lote de 6 notas do Segment D): "Valor contábil zerado para
nota com situação diferente de cancelada" — evidência externa de que o
Valor dos Serviços saía 0,00 apesar de estar limpo e legível no próprio
documento. Uma 2ª causa, não reportada pelo Domínio mas encontrada na mesma
investigação, corrompia a RazãoSocial do prestador com o próprio endereço.

Causa raiz nº 1 — razão social: o regex primário de captura (compartilhado
por ~30 layouts) acerta em cheio ("VALOR COMERCIO E SERVICOS DE INFORMATICA
LTDA"), mas o guard de ruído `_LABELS_NOISE` rejeita qualquer candidato que
COMECE com a palavra "Valor" (pensado para rejeitar rótulos vazados como
"Valor Total"/"Valor Líquido") — e a própria razão social real desta empresa
começa com essa palavra. O candidato válido era descartado, caindo no
fallback seguinte, que capturava a linha de Endereço em vez do nome.
**Fix:** o guard passa a exigir uma continuação típica de RÓTULO monetário
depois de "Valor" (Total/Líquido/Bruto/Unit/dos Serviços/ISS/Retido/"("/":"
/fim de linha) — nenhuma dessas aparece logo após "Valor" no início de uma
razão social real deste corpus.

Causa raiz nº 2 — valores zerados: esta nota imprime "VALOR TOTAL DA NOTA
FISCAL R$ 583,00" (com a palavra "FISCAL" no meio e SEM "=" nem ":" antes de
"R$") — o regex do LAYOUT_SALVADOR exigia um desses 2 separadores logo após
"NOTA", então a linha inteira não casava e Valor dos Serviços/Base de
Cálculo caíam pra 0,00. **Fix:** "FISCAL" tolerado como opcional e o
separador ("=", ":" ou nada) tornado opcional.

Causa raiz colateral (achado ao investigar a nº 2, corrigida na mesma
sessão): a grade de Alíquota/ISS desta nota tem só 4 colunas ("Valor Total
Deduções (R$); Base de Cálculo (R$): Alíquota (%) Valor ISS (R$):"), sem a
coluna "Crédito" que o regex de 5 colunas (`m_grid5`) exige, e a própria
Alíquota sai sem a vírgula decimal ("415" em vez de "4,15"). **Fix:** novo
regex de 4 colunas (`m_grid4`), com a Alíquota sem vírgula só aceita quando
a identidade Base × Alíquota = ISS bate (583,00 × 4,15% ≈ 24,19, exatamente
o valor de ISS lido na mesma linha) — evita reinterpretar um percentual
inteiro legítimo como se faltasse vírgula.

O texto abaixo é cópia literal (via `_extract_via_ocr`) da nota real."""
import os

from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_SALVADOR

MOCK_TEXT = (
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
    'E-mail:\n'
    'liliaBpainformatica.com.br\n\n'
    'TOMADOR DE SERVIÇOS\n\n'
    'CPFICNPJ: Inscrição Municipal:\n'
    '04.555.283/0003-50\n\n'
    'Nome/Razão Social:\n\n'
    'BONI TRANSPORTES LOGISTICA E COMÉRCIO LTDA\n'
    'Endereço:\n\n'
    'RUA MARIA QUITERIA 253 ITINGA Lauro de Freitas BA\n\n'
    'E-mail\n'
    'financeiro3Bbonialimentos.com.br\n\n'
    'DESDE vias\n\n'
    'DISCRIMINAÇÃO DOS SERVIÇOS\n\n'
    'ASSESSORIA EM INFORMATICA REFERENTE MES AGOSTO 2026 Quantidade 1 Unit R$ 583.00 Total R$ 583.00\n\n'
    'EMPRESA OPTANTE PELO SIMPLES NOVO TELEFONE: (71) 3357-4000\n'
    'Pedido Numero: 46345\n\n'
    'VALOR TOTAL DA NOTA FISCAL R$ 583,00\n\n'
    'CNAE:\n'
    '6204000 Consultoria em tecnologia da informação\n\n'
    'Item da Lista de Serviço:\n'
    '106 Assessoria e consultoria em informática,\n\n'
    'Valor Total Deduções (R$); |Base de Cálculo (RS): Alíquota (%) Valor ISS (R$):\n'
    '0,00 583,00 415 24,19\n\n'
    'OUTRAS INFORMAÇÕES\n\n'
    'Valor INSS (R$ | |Valor PIS (R$): Valor COFINS Valor IR (R$): Valor CSLL (R$): [Outras Retenções (RS). [Valor Liquido (R$): |\n'
    '0,00 0,00 0,00 0,00 0,00 0,00 583,00\n\n'
    'Competência - 08/2026 (mês/ano)\n\n'
    'Valor ISS Retdo (R$):\n\n'
    'Código Tributação do Municipio: 106001\n'
    'Optante pelo Simples Nacional"\n'
)


def _novo_extrator(texto):
    dummy_path = "tests/dummy_valor_comercio_46345.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = texto
    extractor.layout = LAYOUT_SALVADOR
    return extractor, dummy_path


def test_razao_social_do_prestador_nao_e_o_endereco():
    extractor, dummy_path = _novo_extrator(MOCK_TEXT)
    try:
        prestador = extractor._extrair_entidade('Prestador')
        assert prestador.razao_social == "VALOR COMERCIO E SERVICOS DE INFORMATICA LTDA"
    finally:
        os.remove(dummy_path)


def test_valor_dos_servicos_nao_fica_zerado_com_fiscal_no_meio_do_rotulo():
    extractor, dummy_path = _novo_extrator(MOCK_TEXT)
    try:
        valores = extractor._extrair_valores()
        assert valores.valor_servicos == 583.0
        assert valores.base_calculo == 583.0
        assert valores.valor_liquido_nfse == 583.0
    finally:
        os.remove(dummy_path)


def test_aliquota_e_iss_recuperados_da_grade_de_4_colunas_sem_credito():
    extractor, dummy_path = _novo_extrator(MOCK_TEXT)
    try:
        valores = extractor._extrair_valores()
        assert abs(valores.aliquota - 0.0415) < 1e-6
        assert valores.valor_iss == 24.19
    finally:
        os.remove(dummy_path)


def test_razao_social_iniciada_em_valor_mas_realmente_rotulo_ainda_e_rejeitada():
    # Não deve regredir o caso que o guard original protegia: um rótulo
    # vazado de verdade ("Valor Total ...") continua sendo rejeitado como
    # razão social.
    texto = MOCK_TEXT.replace(
        'Nome/Razão Social:\n\n'
        'VALOR COMERCIO E SERVICOS DE INFORMATICA LTDA\n\n'
        'Endereço:\n\n'
        'LADEIRA DO ACUPE/SUBSOLO 104 ACUPE DE BROTAS Salvador BA\n',
        'Nome/Razão Social:\n\n'
        'Valor Total: R$ 999,00\n\n'
        'Endereço:\n\n'
        'RUA GENUINA 100 CENTRO Salvador BA\n',
    )
    extractor, dummy_path = _novo_extrator(texto)
    try:
        prestador = extractor._extrair_entidade('Prestador')
        assert prestador.razao_social != "Valor Total: R$ 999,00"
    finally:
        os.remove(dummy_path)


def test_grade_de_5_colunas_com_credito_continua_prioritaria_sobre_a_de_4():
    # Regressão: uma nota com a grade de 5 colunas ("...Crédito...")
    # completa e bem formada não deve ser desviada pra `m_grid4`.
    texto = (
        'PREFEITURA MUNICIPAL DO SALVADOR\n'
        'PRESTADOR DE SERVIÇOS\n'
        'Nome/Razão Social:\n\nEMPRESA TESTE LTDA\n'
        'CPF/CNPJ: 11.222.333/0001-81\n'
        'Endereço: RUA TESTE 1 - CENTRO - Salvador - CEP: 40000-000 - BA\n'
        'TOMADOR DE SERVIÇOS\n'
        'Nome/Razão Social:\n\nTOMADOR TESTE LTDA\n'
        'CPF/CNPJ: 22.333.444/0001-90\n'
        'DISCRIMINAÇÃO DOS SERVIÇOS\n'
        'VALOR TOTAL DA NOTA = R$1.000,00\n'
        'Valor Total das Deduções (R$) Base de Cálculo (R$) Alíquota (%) Valor do ISS (R$) Crédito (R$)\n'
        '0,00 1.000,00 5,00 50,00 0,00\n'
    )
    extractor, dummy_path = _novo_extrator(texto)
    try:
        valores = extractor._extrair_valores()
        assert valores.aliquota == 0.05
        assert valores.valor_iss == 50.0
        assert valores.base_calculo == 1000.0
    finally:
        os.remove(dummy_path)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
