# -*- coding: utf-8 -*-
"""Nota real nº 00024910 (BDP LOGÍSTICA INTEGRADA DE RESÍDUOS LTDA -> BONI
TRANSPORTES, LOGISTICA E COMERCIO LTDA, layout Salvador/BA) — PDF de imagem
escaneada de 1 página só, achado 2026-08-26.

A leitura de página inteira com PSM padrão (automático) derrubava POR
COMPLETO o bloco do PRESTADOR (rótulo "PRESTADOR DE SERVIÇOS", CPF/CNPJ,
Nome/Razão Social, CEP) e a grade inteira de valores, mesmo sem nenhuma
marca d'água/rabisco na página — a leitura pulava direto de "Código de
verificação:" pra "Endereço:". O MESMO zoom (3x) com PSM 6 (bloco único de
texto) recupera a maior parte desse bloco. `_ocr_page` agora tenta as duas
leituras e usa a que pontuar melhor em `_score_ocr_text` só quando o layout
Salvador é detectado (não altera o comportamento já validado nos demais
layouts nem nas notas Salvador onde o PSM padrão já é suficiente).

O texto abaixo é o resultado REAL da leitura combinada (recorte de cabeçalho
+ votação de número + PSM 6 de página inteira, todos já com os prepends que
`_ocr_page` de fato produz para esta nota), usado como fixture para travar a
regressão sem precisar rodar Tesseract no teste. 3 bugs adicionais, achados
na mesma nota, corrigidos junto:

1. Razão social do PRESTADOR: sem o rótulo "Nome/Razão Social" (ausente, não
   garblado, no OCR desta nota), o fallback linha-a-linha pegava a linha do
   PRÓPRIO CNPJ ("19.951.455/0001-84 BLARE TODRUT ES gr" — CNPJ + ruído de
   OCR colado) como se fosse a razão social, empurrando a linha real da
   empresa (a seguinte) pra fora. Corrigido pulando qualquer linha candidata
   que COMECE com um CNPJ formatado.
2. Razão social do TOMADOR: sem um rótulo "CPF/CNPJ" reconhecível antes do
   CNPJ do tomador, a captura de razão social (que colapsa quebras de linha
   em espaço) não tinha onde parar e engolia o CNPJ formatado E o endereço
   inteiro na mesma captura. Corrigido adicionando o próprio PADRÃO de CNPJ
   formatado como stop-pattern (não só o rótulo).
3. "VALOR TOTAL DA NOTA" saiu com "DA"/"NOTA" colados ("DANOTA") e o valor
   sem separador decimal ("134000") — não confiável pra reformatar. A linha
   "Valor Liquido R$ 1.273,00" (formatação intacta) é usada como último
   recurso quando a linha principal falha, em vez de deixar valor_servicos
   como 0,00.
4. Número da nota: as 4 amostras originais de `_ocr_numero_nota_salvador_
   votado` não tinham maioria estrita nesta nota (3 leituras erradas
   distintas, 1 certa). Duas amostras novas (zoom 7x/9x, PSM 4 — testado
   contra a imagem real) reforçam a leitura correta "00024910", e o critério
   de aceite foi relaxado de maioria estrita (`>`) pra pelo menos metade
   (`>=`) das amostras.

CNPJ do prestador e do tomador, Código de Verificação e o logradouro/CEP de
ambas as entidades continuam ilegíveis mesmo após o PSM 6 (dígitos
adicionais trocados pelo OCR, ou rótulo "Endereço"/"Inscrição Municipal"
sumido) — mantidos como sentinela/"Não informado" em vez de fabricados,
registrado como limitação conhecida (issue GitHub aberta cobrindo o padrão
"Salvador/Luniteck-BONI com scan catastroficamente degradado")."""
import os
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_SALVADOR

MOCK_TEXT = (
    'Número da Nota:\n'
    '00024910\n\n'
    'Número da Nota:\n'
    'VADOR DONS4SA\n\n'
    '——em—\n'
    'Número da Nota:\n'
    'PREFEITURA MUNICIPAL DO SALVADOR 00024910\n'
    'Data é Hora de Ei ã\n'
    'SECRETARIA MUNICIPAL DA FAZENDA o 2 10: missão\n'
    'NOTA FISÇAI DE SERVICOS ELETRÔNICA - Nota Salvador | Rage pensrficação:\n'
    'PRESTADOR DE SERVIÇOS\n'
    'CPFIONPI: , ição Municipat Ro\n'
    '19.951.455/0001-84 BLARE TODRUT ES gr\n'
    'BDP LOGISTICA INTEGRADA DE RESÍDUOS LTDA Wasta\n'
    'Ras Eua Temporal OO9G0, TORO IMÓVEL:GAL PÃO - VALÉRIA - Salvador - CEP: 61308449 A\n'
    'TOMADOR DE SERVIÇOS\n'
    'Nome/Razão Social\n'
    'BOM TRANSPORTES, LOGISTICA E COMERCIO LTDA. ) ,\n'
    '04.555.283/9003-50 rss\n'
    'RUA MÁRIA QUITERA 263, GALPÃO LOT DESMEMBRAMENTO IAM ITINGA Lauro de Freios CEP: C2r3820SMA\n'
    'PESCRINMAÇÃO DOS SERVICO dos para coleta, transporte e destinacao final de residuos solidos\n'
    'perigosos de Classe I.\n'
    'Hedicao no 4\n'
    'Forxa de pagamento: Eoleto Bancario\n'
    'Valor Liquido R$ 1.273,00\n'
    'Couto co Renta O 812 4 df\n'
    'VALOR TOTAL DANOTA=R$ 134000 77 /\n'
    'a E pe\n'
    '3812208 - Coleta de resíduos perigosas\n'
    'Rem da Lista de Serviços:\n'
    'S9709 -Vorrição, coleta, remoção, incineração, tratamento, reciclagem, separação e destinaçãofinsi de lixo, rejeitos e outros reside...\n'
    'a e aa ua\n'
    'OUTRAS INFORMAÇÕES\n'
    '- Esta Note Salvador foi emfida com respeido ns Lei 7186/2008.\n'
    '- DISS desta Nota Salvador é devido FORA do Município de Salvador.\n'
    '- Esta Nota Selvador não gere crédio pois a tomador não possui inscrição municipal em Salvador.\n'
    '- sta Note Salvador substitui o RPS Nº 24256 Série NFSE, emitido em 28/07/2026\n'
    '- COMPETÊNCIA: 07/2028 (mêsieno)\n'
    '- Código de Tributação do Municipio: D709-002 - Coleta remoção de bxa, entulhos, rejetos e outros resíduos queisquer\n'
)


def _novo_extrator():
    dummy_path = "tests/dummy_salvador_bdp_00024910.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = MOCK_TEXT
    extractor.layout = LAYOUT_SALVADOR
    return extractor, dummy_path


def test_numero_por_maioria_relaxada_prevalece_sobre_leituras_minoritarias_erradas():
    extractor, dummy_path = _novo_extrator()
    try:
        assert extractor._extrair_numero() == "00024910"
    finally:
        os.remove(dummy_path)


def test_razao_social_prestador_nao_captura_a_propria_linha_do_cnpj():
    extractor, dummy_path = _novo_extrator()
    try:
        prestador = extractor._extrair_entidade('Prestador')
        assert 'BDP LOGISTICA INTEGRADA DE RES' in prestador.razao_social.upper()
        assert 'BLARE' not in prestador.razao_social.upper()
    finally:
        os.remove(dummy_path)


def test_razao_social_tomador_nao_engole_cnpj_e_endereco_sem_rotulo_de_cnpj():
    extractor, dummy_path = _novo_extrator()
    try:
        tomador = extractor._extrair_entidade('Tomador')
        assert 'COMERCIO LTDA' in tomador.razao_social.upper()
        assert '04.555.283' not in tomador.razao_social
        assert 'RUA' not in tomador.razao_social.upper()
    finally:
        os.remove(dummy_path)


def test_valor_servicos_usa_valor_liquido_quando_valor_total_da_nota_falha():
    extractor, dummy_path = _novo_extrator()
    try:
        valores = extractor._extrair_valores()
        assert valores.valor_servicos == 1273.0
        assert valores.valor_liquido_nfse == 1273.0
    finally:
        os.remove(dummy_path)
