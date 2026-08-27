# -*- coding: utf-8 -*-
"""Nota real nº 29377 (Rlgr Telefonia LTDA -> SINDICATO DOS DELEGADOS DE
POLICIA DO ESTADO DA BAHIA ADPE), achado 2026-08-26 — 1ª nota ESCANEADA
deste layout (as anteriores, nº 7271, eram PDF digital limpo).

O template imprime 2 blocos lado a lado no cabeçalho (esquerda: NOME/CPF-
CNPJ/ENDEREÇO/INSCRIÇÃO ESTADUAL/CÓDIGO DO CLIENTE do destinatário; direita:
NOTA FISCAL Nº/DATA DE EMISSÃO/PROTOCOLO/CHAVE DE ACESSO) — o OCR de página
inteira com PSM padrão (automático) FUNDE as 2 colunas linha a linha
("NOME: SINDICATO...DO ESTADO NOTA FISCAL Nº; 000029377"), vazando a coluna
direita pra dentro da razão social do tomador e quebrando CNPJ (1 dígito
trocado, "73353696000137" em vez de "73393696000137"), endereço ("Não
informado" em tudo) e Código de Verificação (cai no sentinela "NFCOM").

Corrigido com uma 2ª tentativa de OCR em `--psm 4` ("assume coluna única de
texto"), que separa as 2 colunas corretamente — trocada por
`_score_ocr_text` (empata com o PSM padrão nesta nota, então o critério é
"pelo menos empatar", não "pontuar estritamente melhor" — ver comentário em
`_ocr_page`). Efeito colateral do PSM 4: a palavra "FISCAL" do título sai
partida ao meio ("NOTA FI" numa banda, "SCAL FATURA DE SERVIÇOS..." bem mais
adiante), quebrando a marca de detecção original — corrigida tolerando
"NOTA FISCAL" ausente/deslocado antes de "FATURA DE SERVIÇOS...".

Validação de checksum do CNPJ do tomador adicionada como defesa extra
(`_validate_cnpj_cpf`, já existente no código): mesmo que uma leitura futura
ainda troque 1 dígito, cai no sentinela em vez de propagar um CNPJ inválido
silenciosamente.

Grade "TOTAL A PAGAR"/"VENCIMENTO"/"REFERÊNCIA (ANO/MÊS)" impressa em cinza
MUITO claro (achado real desta nota) — nenhuma leitura de página inteira (em
qualquer PSM/zoom) recupera esse texto porque a intensidade de pixel fica
ACIMA dos limiares de binarização usuais (120-180), mas o texto É legível a
olho nu na imagem renderizada. Recuperado com um recorte dedicado da faixa
(`_ocr_recut_total_pagar_rlgr`): `ImageOps.autocontrast` (estica o
histograma do recorte) seguido de binarização com limiar ALTO (230, não
baixo) — resultado prependado (não substitui) ao texto já lido, igual ao
padrão já usado em `_ocr_recut_telecom_comunicacao`/`_ocr_recut_biocontrol`.
"TOTAL À PAGAR: R$71,37" sai consistente em múltiplas leituras (PSM 4/6/11)
nesse limiar, corroborado pela nota anterior (nº 7271) ter o mesmo valor
para a mesma tarifa mensal recorrente de STTV. Competência também não sai
legível nesta leitura (rótulo "COMPETÊNCIA:" ausente do texto) — cai no
fallback já existente (mês da Data de Emissão), mesmo padrão usado em
outros layouts quando o rótulo real não está disponível.

O texto abaixo é o resultado REAL de `_ocr_page` (Tesseract, zoom 3x,
`--psm 4`, já com a troca de PSM e o recorte `_ocr_recut_total_pagar_rlgr`
prependado) para a página 1 desta nota, usado como fixture para travar a
extração sem precisar rodar Tesseract no teste."""
import os
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_NFCOM_RLGR

MOCK_TEXT = (
    'REFERÊNCIA (ANO/MÊsy:\n'
    '2028, D6\n\n'
    'VENCIMENTO:\n\n'
    'TOTAL À PAGAR:\n'
    '25/07/2026\n\n'
    'R$71,37\n\n\n'
    'dá\n\n'
    'DOCUMENTO AUXILIAR DA NOTA F:\n'
    'Rigr Telefonia LTDA\n\n'
    'Alameda Rio Negro, 503, Sala 2020 A!\n'
    'CNPJ: 57.675.896/0001-26\n'
    'Inscrição Estadual: 206985784118\n\n'
    'ISCAL FATURA DE SERVIÇOS DE COMUNICAÇÃO ELETRÔNICA\n\n'
    'phaville Centro Industrial e Empresarial/Alphaville., 06454000 - Barueri, SP\n\n'
    'DADOS DO DESTINATÁRIO\n\n'
    'QRCODE NF DADOS FISCAIS\n\n'
    'NOME: SINDICATO DOS DELEGADOS DE POLICIA DO ESTADO\n'
    'DA BAHIA ADPE\n\n'
    'CPF/CNPJ: 73393696000137\n\n'
    'ENDEREÇO: Rua Direita da Piedade 11 Barris, 40070190 -\n'
    'Salvador, BA\n\n'
    'INSCRIÇÃO ESTADUAL:\n'
    'cópico DO CLIENTE: 74440\n\n'
    'NOTA FISCAL Nº; 000029377\n\n'
    'SÉRIE: 00000\n\n'
    'DATA DE EMISSÃO: 05/07/2026 12:00:15\n'
    'PROTOCOLO DE AUTORIZAÇÃO: 3352600566516054\n'
    'DATA DA AUTORIZAÇÃO: 05/07/2026 12:00:33\n\n'
    'CHAVE DE ACESSO:\n'
    '3526075767589600012662000000029377101209 1894\n\n'
    'PERÍODO: 01/06/2026 a 30/05/2026\n'
    'PÁGINA: 1/1\n\n'
    'TELEFONE: 71991213156\n\n'
    'PREÇO UNIT VALOR TOTAL\n\n'
    'PIS/COFINS BCICMSe FCP ALÍQ ICMS + FCP\n\n'
    'RR RR\n\n'
    'o\n'
    '[escore [ço ———]\n'
    'CEE CO\n'
    '[uistiero fuis |\n\n'
    '[em |\n\n'
    'VALOR OUTROS:\n\n'
    'INFORMAÇÕES COMPLEMENTARES\n\n'
    'Pública (DID) e Ter\n\n'
    'ção de Tráfego de Voz (STTV — ps\n\n'
    'mensal fechado).\n'
    'nensal fechado).\n\n'
    'ÁREA CONTRIBUINTE: MENSAGENS PRIORITÁRIAS / AVISOS AO CONSUMIDOR\n\n'
    'ÁREA DO CONTRIBUINTE E DETERMINAÇÕES DA ANATEL\n\n'
    'Consulte peia Chave de Aces:\n\n'
    'so em https://dfe-portal swrs.rs.gow.br/NFCom/QRCode?chNFCom=3525\n\n'
    '266 20000006\n\n'
    "'29377101209\n\n"
    '8948tpâmb=1'
)


def _novo_extrator():
    dummy_path = "tests/dummy_nfcom_rlgr_29377.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = MOCK_TEXT
    extractor.layout = LAYOUT_NFCOM_RLGR
    return extractor, dummy_path


def test_deteccao_tolera_titulo_com_fiscal_partido_pelo_psm4():
    extractor, dummy_path = _novo_extrator()
    try:
        assert extractor._detect_layout() == LAYOUT_NFCOM_RLGR
    finally:
        os.remove(dummy_path)


def test_tomador_nao_vaza_coluna_direita_do_cabecalho_na_razao_social():
    extractor, dummy_path = _novo_extrator()
    try:
        tomador = extractor._extrair_entidade('Tomador')
        assert tomador.razao_social == 'SINDICATO DOS DELEGADOS DE POLICIA DO ESTADO DA BAHIA ADPE'
        assert 'NOTA FISCAL' not in tomador.razao_social.upper()
        assert 'SÉRIE' not in tomador.razao_social.upper()
    finally:
        os.remove(dummy_path)


def test_tomador_cnpj_correto_com_validacao_de_checksum():
    extractor, dummy_path = _novo_extrator()
    try:
        tomador = extractor._extrair_entidade('Tomador')
        assert tomador.cnpj_cpf == '73393696000137'
    finally:
        os.remove(dummy_path)


def test_tomador_endereco_completo_apos_separacao_de_colunas():
    extractor, dummy_path = _novo_extrator()
    try:
        tomador = extractor._extrair_entidade('Tomador')
        assert tomador.endereco.logradouro == 'Rua Direita da Piedade'
        assert tomador.endereco.numero == '11'
        assert tomador.endereco.bairro == 'Barris'
        assert tomador.endereco.municipio == 'Salvador'
        assert tomador.endereco.uf == 'BA'
        assert tomador.endereco.cep == '40070190'
    finally:
        os.remove(dummy_path)


def test_codigo_verificacao_recupera_chave_de_acesso_apos_separacao_de_colunas():
    extractor, dummy_path = _novo_extrator()
    try:
        assert extractor._extrair_codigo_verificacao() == '35260757675896000126620000000293771012091894'
    finally:
        os.remove(dummy_path)


def test_valores_recuperados_da_grade_em_cinza_claro_via_recorte_dedicado():
    extractor, dummy_path = _novo_extrator()
    try:
        valores = extractor._extrair_valores()
        assert valores.valor_servicos == 71.37
        assert valores.valor_liquido_nfse == 71.37
    finally:
        os.remove(dummy_path)


def test_tomador_cnpj_invalido_cai_no_sentinela_em_vez_de_propagar_digito_trocado():
    # Simula um dígito trocado no MEIO do CNPJ (achado real desta nota antes
    # do fix de PSM 4 - "73353696000137" em vez de "73393696000137") para
    # travar a defesa de checksum independentemente da separação de colunas.
    extractor, dummy_path = _novo_extrator()
    try:
        texto_com_cnpj_invalido = MOCK_TEXT.replace('73393696000137', '73353696000137')
        extractor.raw_text = texto_com_cnpj_invalido
        tomador = extractor._extrair_entidade('Tomador')
        assert tomador.cnpj_cpf == '00000000000000'
    finally:
        os.remove(dummy_path)
