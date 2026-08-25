# -*- coding: utf-8 -*-
"""Nota real nº 00000061 (MCLA CONSTRUÇÕES LTDA -> BONI TRANSPORTES,
LOGISTICA E COMERCIO LTDA, layout Salvador/BA): o PSM automático do
Tesseract (leitura de página inteira, sem `--psm` explícito) derruba POR
COMPLETO a linha "Nome/Razão Social: MCLA CONSTRUÇÕES LTDA" do prestador E
corrompe o cabeçalho "TOMADOR DE SERVIÇOS" a ponto da palavra "TOMADOR" não
sobreviver nem corrompida (vira "vVIÇOS") — sem esses dois sinais, o bloco
genérico do prestador não tem onde parar e vaza a razão/CNPJ do TOMADOR
(BONI) para as DUAS entidades; a guarda existente de CNPJ de BONI TRANSPORTES
(que corrige o CNPJ crônico mal-impresso dessa contraparte) então dispara
para as duas, reforçando o erro. O CNPJ do PRESTADOR também sai com o
separador "," em vez de "." ("61,235 .378/0001-69") e com um espaço espúrio
extra antes dele — dígitos corretos (checksum válido), mas rejeitados pelo
regex antigo, que só aceitava ".".

Simula o texto já com os recortes dedicados prependados/emendados por
`_ocr_page` (mesma convenção dos demais testes de OCR-zoom deste projeto —
não invoca Tesseract/pymupdf de verdade): o recut do TOMADOR
(`_ocr_tomador_salvador`) prependado à frente, a razão do PRESTADOR
(`_ocr_recut_prestador_razao_salvador`) emendada antes do 1º "Endereço", e o
marcador da Base de Cálculo (`_ocr_recut_base_calculo_grade_salvador`)
prependado. Confirmado por imagem real (zoom até 20x): CNPJ do prestador =
"61.235.378/0001-69", CNPJ do tomador = "04.555.283/0001-99" (mesma raiz já
tratada pela guarda existente), valor real = R$6.878,81 (a linha "VALOR
TOTAL DA NOTA" imprime consistentemente "R$6.875,81", com defeito
irrecuperável mesmo em releitura ultra-zoom dedicada da própria linha — só a
grade de "Base de Cálculo", lida à parte, bate com a imagem)."""
import os
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_SALVADOR

MOCK_TEXT = (
    'BASE_CALCULO_RECUPERADA: 6.878,81\n'
    'TOMADOR DE SERVIÇOS\n'
    'NormeiRezão Social;\n\n'
    'BONI TRANSPORTES, LOGISTICA E COMERCIO LTDA.\n\n'
    'CPF/CNPJ. inserção Municizal\n'
    '04,555.203/00D1-53\n\n'
    'Endereço\n\n'
    'RUA DOUTOR GERINO DE SOUZA FILHO 1028,\n'
    'ACESSO PELA RUA MINGA - Lauro de Freitas - CEP: 42738-200/B A\n\n'
    'EMPRESA OETANTE PELO SIMELES NACIONAL -\n\n'
    'VALOR TOTAL DA NOTA = R$6.875,81\n\n'
    'CNE\n'
    '4330459 - Outras obras de acabamento da construção\n\n'
    'PREFEITURA MUNICIPAL DO SALVADOR\n'
    'SECRETARIA MUNICIPAL DA FAZENDA\n'
    'Número da Nota:\n00000061\n\n'
    'Data e Hora de Emissão:\n22/07/2026 16:12:02\n\n'
    'NOTA FISCAL DE SERVIÇOS ELETRÔNICA - Nota Salvador\n\n'
    'PRESTADOR DE SERVIÇOS\n\n'
    'CPEICNPJ Inscrição Municipal\n'
    '61,235 .378/0001-69 01.021.787/001-20\n\n'
    'Nome/Razão Social\n'
    'MCLA CONSTRUÇÕES LTDA\n'
    'Enderaço:\n\n'
    'ge ie ia Simões 000055, EDIF:EMPRESARIAL SIMONSEN;SALA - CAMINHO DAS ARVORES - Salvador - CEP: <1B20I74 - BA\n\n'
    'vVIÇOS\n'
    'NomeiRazão Social:\n'
    'BONI TRANSPORTES, LOGISTICA E COMERCIO LTDA.\n'
    'Inserção Municizal\n\n'
    'Endereço”\n'
    'UTOR GERINO DE SOUZA FILHO 1025, ACESSO PELA RUA IMINGA - Lauro de Freitas - CEP: 42738-200/BA\n\n'
    'EMPRESA OFTANTE PELO SIMELES NACIONAL -\n\n'
    'VALOR TOTAL DA NOTA = R$6.875,81\n\n'
    'Valor Total das Decuções (R$) Baso de Cáicuo [R$ mu Valar do ISS (R$ Crédio Nota Salvador (R$)\n\n'
    '2,00 343, 2,09\n\n'
    'Valor INSS (R$7 T valor PIS (R$ (28) Outras Retenções (FS 1| Valor Liquico (R$k\n'
    '0,00 | 0,00 0,00 5.878,81\n\n'
    'OUTRAS INFORMAÇÕES\n'
    '- Esta Neta Samador foi ormitida com respaldo na Lei 7 185/2006.\n'
    '- COMPETÊNCIA 07/2026 (mês/ano)\n'
)


def _novo_extrator():
    dummy_path = "tests/dummy_salvador_prestador_tomador_colisao.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = MOCK_TEXT
    extractor.layout = LAYOUT_SALVADOR
    return extractor, dummy_path


def test_prestador_nao_colide_com_tomador_quando_tomador_label_some():
    extractor, dummy_path = _novo_extrator()
    try:
        prestador = extractor._extrair_entidade('Prestador')
        assert prestador.razao_social.strip().upper().startswith('MCLA')
        assert prestador.cnpj_cpf == "61235378000169"
    finally:
        os.remove(dummy_path)


def test_tomador_continua_boni_transportes_com_cnpj_correto():
    extractor, dummy_path = _novo_extrator()
    try:
        extractor._extrair_entidade('Prestador')  # popula _cnpj_prestador_extraido
        tomador = extractor._extrair_entidade('Tomador')
        assert 'BONI TRANSPORTES' in tomador.razao_social.upper()
        assert tomador.cnpj_cpf == "04555283000199"
    finally:
        os.remove(dummy_path)


def test_prestador_e_tomador_nunca_saem_com_o_mesmo_cnpj():
    extractor, dummy_path = _novo_extrator()
    try:
        prestador = extractor._extrair_entidade('Prestador')
        extractor._cnpj_prestador_extraido = prestador.cnpj_cpf
        tomador = extractor._extrair_entidade('Tomador')
        assert prestador.cnpj_cpf != tomador.cnpj_cpf
    finally:
        os.remove(dummy_path)


def test_valor_total_usa_base_de_calculo_quando_linha_do_cabecalho_diverge():
    extractor, dummy_path = _novo_extrator()
    try:
        valores = extractor._extrair_valores()
        assert valores.valor_servicos == 6878.81
        assert valores.base_calculo == 6878.81
        assert valores.valor_liquido_nfse == 6878.81
    finally:
        os.remove(dummy_path)


# ---------------------------------------------------------------------------
# Nota real nº 00000006 (RC INFORMÁTICA E ACESSÓRIOS LTDA -> BONI
# TRANSPORTES, layout Salvador/BA): o próprio rótulo "Nome/Razão Social"
# sai garblado a ponto de nenhum filtro reconhecer ("NomeiRazão Socia'" — a
# "/" vira "i" e o "l" final de "Social" some), mas ainda "parece" texto
# normal o bastante pra passar como razão social de verdade — roubando a
# linha real (a empresa) que vem logo depois no bloco do prestador.
# ---------------------------------------------------------------------------
MOCK_TEXT_RC = (
    'PRESTADOR DE SERVICOS\n\n'
    'CPF/CNPJ E Municipal\n\n'
    '54.654.057/0001-33 00.485.340/001-05\n'
    'NomeiRazão Socia\'\n'
    'RC INFORMATICA E ACESSORIOS LTDA\n\n'
    'Endereço\n\n'
    'Rua Barros Reis 000350, LOJA 09 - PAU MIÚDO - Salvador - CEP: 40310-010 - BA\n\n'
    'TOMADOR DE SERVICOS\n\n'
    'NomeiRazão Socia!\n\n'
    'BONI TRANSPORTES, LOGISTICA E COMERCIO LTDA.\n\n'
    'CPF/CNPJ Inscrição Municipal\n\n'
    '04.555.283/0001-93\n\n'
    'Endereço.\n'
    'RUA DOUTOR GERINO DE SOUZA FILHO 1025, ACESSO PELA RUA ITINGA - Lauro de Freitas - CEP: 42738-200/BA\n\n'
    'DISCRIMINAÇÃO DOS SERVIÇOS\n'
    'MANUTENÇÃO PREVENTIVA E CORRETIVA COM SUBSTITUIÇÃO DE PEÇAS DIVERSAS R$ 2.000,00\n\n'
    'VALOR TOTAL DA NOTA = R$2.000,00\n'
)


def _novo_extrator_rc():
    dummy_path = "tests/dummy_salvador_razao_label_leak.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = MOCK_TEXT_RC
    extractor.layout = LAYOUT_SALVADOR
    return extractor, dummy_path


def test_razao_social_nao_captura_o_rotulo_garblado_como_se_fosse_a_empresa():
    extractor, dummy_path = _novo_extrator_rc()
    try:
        prestador = extractor._extrair_entidade('Prestador')
        assert prestador.razao_social.strip().upper() == 'RC INFORMATICA E ACESSORIOS LTDA'
        assert 'NOME' not in prestador.razao_social.upper()
    finally:
        os.remove(dummy_path)
