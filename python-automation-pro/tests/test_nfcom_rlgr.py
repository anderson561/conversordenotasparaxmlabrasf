# -*- coding: utf-8 -*-
"""Nota real nº 7271 (Rlgr Telefonia LTDA -> SINDICATO DOS DELEGADOS DE
POLICIA DO ESTADO DA BAHIA ADPE, R$71,37 de Serviço de Terminação de
Tráfego de Voz/STTV), achado 2026-08-26.

NFCom (Nota Fiscal Fatura de Serviços de Comunicação Eletrônica) da Rlgr
Telefonia, PDF DIGITAL, MESMO template nacional do portal SVRS já usado por
LAYOUT_NFCOM_SALVADOR, mas de um emitente diferente (sem layout dedicado
até este achado). Sem detecção própria, a nota caía no fallback genérico e
saía com o CNPJ do tomador IGUAL ao do prestador, a razão social do tomador
vazada do rótulo "REFERÊNCIA (ANO/MÊS)", todos os valores zerados e o
Código de Verificação em branco.

O texto abaixo é o resultado REAL de `pdfminer.high_level.extract_text()`
para a página 1 desta nota (PDF digital, sem OCR), usado como fixture para
travar a extração sem precisar do PDF real no teste."""
import os
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_NFCOM_RLGR

MOCK_TEXT = (
    'DOCUMENTO AUXILIAR DA NOTA FISCAL FATURA DE SERVIÇOS DE COMUNICAÇÃO ELETRÔNICA\n'
    'Rlgr Telefonia LTDA\n'
    'Alameda Rio Negro, 503, Sala 2020 Alphaville Centro Industrial e Empresarial/Alphaville., 06454000 - Barueri, SP\n'
    'CNPJ: 57.675.896/0001-26\n'
    'Inscrição Estadual: 206985784118\n\n'
    'DADOS DO DESTINATÁRIO\n\n'
    'QRCODE NF\n\n'
    'DADOS FISCAIS\n\n'
    'NOME: SINDICATO DOS DELEGADOS DE POLICIA DO ESTADO DA\n'
    'BAHIA ADPE\n\n'
    'CPF/CNPJ: 73393696000137\n\n'
    'ENDEREÇO: Rua Direita da Piedade 11 Barris , 40070190 -\n'
    'Salvador, BA\n\n'
    'INSCRIÇÃO ESTADUAL:\n\n'
    'CÓDIGO DO CLIENTE: 74440\n\n'
    'TELEFONE: 71991213156\n\n'
    'COMPETÊNCIA: 12/2025\n\n'
    'NOTA FISCAL Nº: 000007271\n\n'
    'SÉRIE: 00000\n\n'
    'DATA DE EMISSÃO: 05/01/2026 11:10:01\n\n'
    'PROTOCOLO DE AUTORIZAÇÃO: 3352600011423285\n\n'
    'DATA DA AUTORIZAÇÃO: 05/01/2026 11:10:10\n\n'
    'CHAVE DE ACESSO:\n'
    '35260157675896000126620000000072711085447594\n\n'
    'PERÍODO: 01/12/2025 a 31/12/2025\n\n'
    'PÁGINA: 1 / 1\n\n'
    'REFERÊNCIA (ANO/MÊS):\n'
    '2025/12\n\n'
    'VENCIMENTO:\n'
    '25/01/2026\n\n'
    'TOTAL A PAGAR:\n'
    'R$ 71,37\n\n'
    'ITEM\n\n'
    'CFOP\n\n'
    'UN\n\n'
    'QUANT\n\n'
    'PREÇO UNIT\n\n'
    'VALOR TOTAL\n\n'
    'PIS/COFINS\n\n'
    'BC ICMS e FCP\n\n'
    'ALÍQ ICMS + FCP\n\n'
    'VALOR ICMS + FCP\n\n'
    'S e r v i c o   d e   Te r m i n a c a o   d e   Tra f e g o   d e   Vo z\n'
    '( S TT V )\n\n'
    '6307\n\n'
    'UN\n\n'
    '1,00\n\n'
    'R$ 71,37\n\n'
    'R$ 71,37\n\n'
    'R$ 0,00\n\n'
    'R$ 0,00\n\n'
    '0,00%\n\n'
    'R$ 0,00\n\n'
    'ITENS DA NOTA FISCAL\n\n'
    'TOTAIS\n\n'
    'INFORMAÇÕES DOS TRIBUTOS\n\n'
    'RESERVADO AO FISCO\n\n'
    'TOTAL DA NF:\n\n'
    'R$ 71,37\n\n'
    'TRIBUTO\n\n'
    'VALOR\n\n'
    'BASE DE CALCULO:\n\n'
    'R$ 0,00\n\n'
    'VALOR ICMS + FCP:\n\n'
    'R$ 0,00\n\n'
    'VALOR ISENTO:\n\n'
    'VALOR OUTROS:\n\n'
    'R$ 0,00\n\n'
    'R$ 0,00\n\n'
    'INFORMAÇÕES COMPLEMENTARES\n\n'
    'PIS:\n\n'
    'COFINS:\n\n'
    'FUST:\n\n'
    'FUNTTEL:\n\n'
    'R$ 0,00\n\n'
    'R$ 0,00\n\n'
    'R$ 0,00\n\n'
    'R$ 0,00\n\n'
    'Dids: (71) 3329-2684\n'
    'Empresa ME/EPP optante pelo simples nacional.\n'
    'Não gera direito a crédito de IPI.\n'
    'Nota Fiscal emitida exclusivamente referente aos serviços de Numeração Pública (DID) e Terminação de Tráfego de Voz (STTV – pacote mensal fechado).\n'
    'Não contempla infraestrutura física, acesso IP ou plataforma tecnológica.\n\n'
    'ÁREA CONTRIBUINTE: MENSAGENS PRIORITÁRIAS / AVISOS AO CONSUMIDOR\n\n'
    'ÁREA DO CONTRIBUINTE E DETERMINAÇÕES DA ANATEL\n\n'
    'Consulte pela Chave de Acesso em https://dfe-portal.svrs.rs.gov.br/NFCom/QRCode?chNFCom=35260157675896000126620000000072711085447594&tpAmb=1'
)


def _novo_extrator():
    dummy_path = "tests/dummy_nfcom_rlgr_7271.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = MOCK_TEXT
    extractor.layout = LAYOUT_NFCOM_RLGR
    return extractor, dummy_path


def test_deteccao_por_cnpj_do_emitente_rlgr():
    extractor, dummy_path = _novo_extrator()
    try:
        assert extractor._detect_layout() == LAYOUT_NFCOM_RLGR
    finally:
        os.remove(dummy_path)


def test_prestador_fixo_rlgr_telefonia():
    extractor, dummy_path = _novo_extrator()
    try:
        prestador = extractor._extrair_entidade('Prestador')
        assert prestador.cnpj_cpf == '57675896000126'
        assert prestador.razao_social == 'RLGR TELEFONIA LTDA'
        assert prestador.endereco.municipio == 'BARUERI'
        assert prestador.endereco.uf == 'SP'
        assert prestador.endereco.codigo_municipio == '3505708'
    finally:
        os.remove(dummy_path)


def test_tomador_dinamico_com_nome_em_duas_linhas_e_cep_embutido():
    extractor, dummy_path = _novo_extrator()
    try:
        tomador = extractor._extrair_entidade('Tomador')
        assert tomador.cnpj_cpf == '73393696000137'
        assert 'SINDICATO DOS DELEGADOS DE POLICIA' in tomador.razao_social.upper()
        assert 'BAHIA ADPE' in tomador.razao_social.upper()
        assert tomador.endereco.logradouro == 'Rua Direita da Piedade'
        assert tomador.endereco.numero == '11'
        assert tomador.endereco.bairro == 'Barris'
        assert tomador.endereco.municipio == 'Salvador'
        assert tomador.endereco.uf == 'BA'
        assert tomador.endereco.cep == '40070190'
    finally:
        os.remove(dummy_path)


def test_valores_usa_total_a_pagar_sem_parenteses_e_zera_iss():
    extractor, dummy_path = _novo_extrator()
    try:
        valores = extractor._extrair_valores()
        assert valores.valor_servicos == 71.37
        assert valores.valor_liquido_nfse == 71.37
        assert valores.base_calculo == 0.0
        assert valores.aliquota == 0.0
        assert valores.valor_iss == 0.0
    finally:
        os.remove(dummy_path)


def test_codigo_verificacao_usa_chave_de_acesso_de_44_digitos():
    extractor, dummy_path = _novo_extrator()
    try:
        assert extractor._extrair_codigo_verificacao() == '35260157675896000126620000000072711085447594'
    finally:
        os.remove(dummy_path)


def test_codigo_servico_fica_zero_por_nao_incidencia_de_iss():
    extractor, dummy_path = _novo_extrator()
    try:
        assert extractor._extrair_codigo_servico() == '0000'
    finally:
        os.remove(dummy_path)


def test_data_emissao_ignora_periodo_e_usa_so_o_rotulo_data_de_emissao():
    # MOCK_TEXT traz "PERÍODO: 01/12/2025 a 31/12/2025" (intervalo de
    # faturamento) poucas linhas acima de "DATA DE EMISSÃO: 05/01/2026
    # 11:10:01" - datas de fato diferentes nesta nota real, então se o
    # extrator pegasse a data errada (início/fim do período) o teste
    # pegaria a divergência.
    extractor, dummy_path = _novo_extrator()
    try:
        data_emissao = extractor._extrair_data_emissao()
        assert data_emissao.strftime('%d/%m/%Y %H:%M:%S') == '05/01/2026 11:10:01'
        assert data_emissao.strftime('%d/%m/%Y') not in ('01/12/2025', '31/12/2025')
    finally:
        os.remove(dummy_path)
