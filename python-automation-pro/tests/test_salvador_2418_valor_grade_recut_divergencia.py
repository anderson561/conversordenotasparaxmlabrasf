# -*- coding: utf-8 -*-
"""Nota real nº 2418 (LUNITECK SOLUÇÕES E DESENVOLVIMENTO EM TECNOLOGIA LTDA
- ME -> BONI TRANSPORTES, LOGISTICA E COMERCIO LTDA), pág.1 (Salvador/BA) —
PDF irmão da nota nº 2419 (`test_salvador_lauro_freitas_2419_razao_e_codigo_
servico.py`), mesmo prestador/template, só 1 nota de diferença, 6 dias antes.

Achado real 2026-08-25: a heurística "confiar na grade de Base de Cálculo
recuperada por `_ocr_recut_base_calculo_grade_salvador` quando diverge da
linha isolada 'VALOR TOTAL DA NOTA'" (introduzida pra corrigir a nota nº
00000061/MCLA CONSTRUÇÕES, onde a linha isolada saía consistentemente ERRADA
por R$0,03) troca, NESTA nota, um valor CORRETO por um ERRADO — "VALOR TOTAL
DA NOTA = R$397,14" está certo e bem legível aqui (confirmado batendo com a
pág.2/NFTS), mas a mesma grade densamente corrompida ("Velor'Totaldes
Dedupdes (R$) [Easede Catulo iai [usa va yo dolSS (R$) | Credito Nota
Salvador (RA / e 0 = 8,00") faz o recut ler "8,00" em vez de "397,14" —
zoom único validado numa nota não generaliza pra uma nota irmã. Corrigido
exigindo que a divergência entre a grade e o cabeçalho seja PEQUENA (≤10%,
plausível como 1 dígito trocado) antes de confiar na grade; divergência
grande (aqui, ~98%) mantém o valor do cabeçalho e deriva a Base dele
(Base = Serviços - Deduções, Deduções = 0 aqui)."""
import os
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_SALVADOR

MOCK_TEXT = (
    'PRESTADOR DE SERVIÇOS\n'
    'CPF/CNPJ\n'
    '07.295.620/0001-44\n'
    'Nome/Razão Social\n'
    'LUNITECK - SOLUCOES E DESENVOLVIMENTO EM TECNOLOGIA LTDA - ME RG Er\n'
    'Endereço\n\n'
    'BASE_CALCULO_RECUPERADA: 8,00\n'
    'TOMADOR DE SERVICOS:\n\n'
    'Norns/Razão Sonia maio Es\n\n'
    'BONI: TRANSRORTES, ; LÓGISTICA ECOMERCIO LTIA.\n\n'
    '"GREYCNPJ:. Inserção: Municipal;\n'
    '4.565. 283/0003:50 dim\n\n'
    'Eridoreço: ELO RS ii o rm\n'
    'E DARIA: QUÍTERIA. 263; GALPADITINGA -iburoido Freitas. "CEP::42738.205/BA\n\n'
    '. JUPOSTOSGNO RTEÉ CONTABILIDADE: COM: BR\n\n'
    '| BSSRUINAÇÃO DOS SERVIÇOS\n'
    'E RÚE9%. tabe A. IEI\' - "SN: RS 23, BS\n\n'
    'doido. Reparação: ER "manutenção. de: computadores: » dé: equipamentos. periféricos\n\n'
    'tem dajLista de: Serviços;\n\n'
    '-OT4Q es esistência Téchica.. =\n\n'
    '| Valor Total das De Heduções( R$) |\n'
    '| 0,00\n\n'
    'aa Ar matas a a a rm\n\n'
    'E AR RE E\n\n'
    '; a quo np va\n\n'
    'rim tram errei reuni a ia\n\n'
    '"VadrPSRS: Valor conste Taro\n'
    "'0,00:|\n\n"
    '[AigiiEs na. FAESA\n\n'
    'CARDS TES Da\n\n'
    '| OUTRAS INFORMAÇÕES\n'
    'Esta Nota Salvador: foemitiga: gem respaldo. na Let 7, t88/2006:\n\n'
    'a Documento: e tido: ou EPP: ontante-pelo Simples. Nacional;\n\n'
    'ue COMPET ENC AN "7/2026. Imésianos:\n\n'
    'e fódigo de: Tributação. do Municl) pior. 1402: 0/94 Assistén dia técnica:\n\n'
    'Número da Nota:\n'
    '00002448\n\n'
    'PS apa Número da Nóta:\n'
    'fADOR 00002418\n'
    'Data-e:Hora de Emissão:\n'
    '13/07/2026 16:00:06:\n'
    'ei mes CGódicao de Verficarãe-.\n\n'
    'PREFEITURA MUNICIPAL DO SALVADOR DOneR a Nota:\n'
    'SECRETARIA MUNICIPAL DA FAZENDA Data:e:Hora de.\n\n'
    'NOTA FISCAL DE SERVIÇOS ELETRÔNICA -Notá salvador | Código de Verificação:\n\n'
    'ERESTADOR DE SERVIÇOS\n\n'
    'Inserição:Miihicipar.\n'
    ':D0/384:869/001-60\n\n'
    'TOMADOR BE SERVIÇOS.\n\n'
    'Norma/Razab Sonia\n'
    'BONI. TRANSRORTES, LOGISTICA E-COMERCÍO LTDA. .\n'
    '"CPREYCNPJ Insenção Municipal;\n'
    'Da. 66.263/0003:50 cime o\n'
    'Endereço:\n'
    'udãs MARIA QUITERIA. 1268; GALPAO. TINHA, » \'Ldurode Freitas  «CEP::42738-205/BA\n\n'
    '= mail;\n\n'
    'jRação Pe seus\n\n'
    'VALOR TOTAL DA NOTA = R$397,14\n\n'
    'RE 800-= Reparação: ecmaniitenção- de computadores e -dé equipamentos periféricos\n\n'
    'item da Lista de Serviços;\n'
    '01402: Assistência Téchica.\n\n'
    'Velor\'Totaldes Dedupdes (R$) [Easede Catulo iai [usa va yo dolSS (R$) | Credito Nota Salvador (RA\n'
    'e 0 = 8,00\n\n'
    'ValoriNOS (8% quares (RS Valor COFINS ( ria tesy Evalar TE Giitias Retenções (R$)] Valdr Liquido (RS)\n'
    '0,90: 2,00 0:06 0,00) 0,00 307;14;\n\n'
    'Aliguatá BS DA,\n\n'
    'ai\n\n'
    'Valor BS (RE. Aliquola CRS (AJ o Valor CBS (RS.\n\n'
    '" 6.\n'
    '- Código, de; Tributação. do" Municibio: t402:0/07- Assistência técnica:\n'
)


def _novo_extrator():
    dummy_path = "tests/dummy_salvador_2418_pag1.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = MOCK_TEXT
    extractor.layout = LAYOUT_SALVADOR
    return extractor, dummy_path


def test_valor_total_nao_e_trocado_por_leitura_errada_da_grade_recuperada():
    extractor, dummy_path = _novo_extrator()
    try:
        valores = extractor._extrair_valores()
        assert valores.valor_servicos == 397.14
        assert valores.valor_liquido_nfse == 397.14
    finally:
        os.remove(dummy_path)


def test_base_calculo_acompanha_o_valor_de_servicos_quando_a_grade_diverge_demais():
    extractor, dummy_path = _novo_extrator()
    try:
        valores = extractor._extrair_valores()
        assert valores.base_calculo == 397.14
    finally:
        os.remove(dummy_path)
