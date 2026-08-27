# -*- coding: utf-8 -*-
"""DANFE Estadual (NF-e Modelo 55) da PENELI METAIS LTDA (CNPJ
19.799.753/0001-37, São Paulo/SP) -> SINDICATO DOS DELEGADOS DE POLICIA DO
ESTADO DA BAHIA - ADPE (Salvador/BA), nota real nº 764, R$9.000,00, item "PIN
POLÍCIA CIVIL BAHIA" (1.500 un x R$6,00) - 1ª nota ESCANEADA deste layout (a
anterior, nº 52.136/GRAN COFFEE, é PDF digital limpo - ver
`test_danfe_produto_layout.py`).

O cabeçalho do Modelo 55 funde 3 colunas na mesma faixa de Y (letterhead do
emitente | caixa "DANFE" | código de barras/chave de acesso) - a leitura de
página inteira derruba a palavra "DANFE" por completo (só sobrevive no modo
"sopa de palavras" PSM 11, não usado em produção), quebra "Documento Auxiliar
da Nota Fiscal Eletrônica" ao meio e embaralha "0-ENTRADA"/"1-SAÍDA" (vira
"Saída: 1\nEntrada: O", com o dígito "0" lido como letra "O") - sem
tratamento, a detecção falhava por completo e a nota caía no fallback
genérico de NFS-e/DANFSe, saindo com razão social "CÁLCULO DO IMPOSTO" (um
rótulo vazado), valor zerado e CNPJ do tomador cruzado com o do emitente.

IMPORTANTE (distinção de domínio, ver
https://suporte.dominioatendimento.com/central/faces/solucao.html?codigo=1195):
um DANFE Modelo 55 é um documento de PRODUTO/mercadoria tributado por
ICMS/IPI, estruturalmente DIFERENTE de uma NFS-e ABRASF (documento de
SERVIÇO, tributado por ISS) - por isso retorna um `NfeProduto`, nunca um
`Nfse`, e usa `NfeProdutoTransformer`, nunca o transformer ABRASF. Este
achado (e o extrator dedicado que o corrige, `_parse_danfe_produto_ocr`) foi
desenvolvido numa branch própria (`feature/layout-danfe-55`), separada da
branch do layout NFCom Rlgr (`feature/layout-nfcom-rlgr`, um documento de
SERVIÇO/ISS diferente) para não misturar os dois domínios.

Detecção: as 4 marcas do caminho digital ("DANFE" + "Documento Auxiliar da
Nota Fiscal Eletrônica" contígua + "0-ENTRADA" + "1-SAÍDA") não sobrevivem ao
OCR - corrigida com uma marca alternativa, tolerante a OCR e exclusiva do
Modelo 55 ("CHAVE DE ACESSO" + "portal nacional da NF-e" +
"DESTINATÁRIO/REMETENTE"), só ativa quando o texto já veio de OCR
(`from_ocr`), para não afrouxar a detecção do caminho digital já validado
(nota nº 52.136).

Extração: `_parse_danfe_produto_ocr` (dedicado, não reaproveita as regex do
caminho digital - o texto OCR sai em rótulo+valor na MESMA linha, ou
rótulos-dump/valores-dump, nunca rótulo\\nvalor de 1 coluna). 3 recortes
dedicados (`_ocr_recut_danfe_produto_emitente/_calculo/_item`, chamados de
dentro de `_ocr_page`, prependados a `best_text` separados por um marcador
exclusivo `<<<DANFE_PRODUTO_RECUT>>>`) recuperam: (1) o letterhead do
emitente (restrito à metade ESQUERDA da página, sem a caixa DANFE nem o
código de barras); (2) a grade "CÁLCULO DO IMPOSTO" em zoom 6x (a leitura de
página inteira comprime as 7 colunas e perde 1 dos vários "0,00" repetidos);
(3) a linha do item (código/descrição precisam de um recorte estreito e bem
alto - 10x -, separado das colunas numéricas). O VALOR TOTAL DOS
PRODUTOS/VALOR TOTAL DA NOTA saem truncados mesmo nos recortes dedicados
("9.00€" em vez de "9.000,00") - não usados diretamente; `valor_total_nota`
vem do "TOTAL: R$ 9.000,00" do canhoto (mais confiável), e
`valor_total_produtos` é derivado pela identidade contábil (produtos = nota +
desconto - frete - seguro - despesas - ipi). Como há só 1 item nesta nota,
BC ICMS/valor ICMS/valor total do item reaproveitam os mesmos números já
extraídos da grade "CÁLCULO DO IMPOSTO" (evita depender da leitura frágil
dessas mesmas colunas dentro da própria linha do item); para N>1 itens esse
atalho não vale (sinalizado via aviso, não implementado ainda).

Código do produto ("004") resiste a toda tentativa de recorte dedicada
(zoom até 10x, PSM 6/7/8/10, inclusive com whitelist numérico) - mantido em
"0001" com aviso, sem fabricar (mesmo racional de outros campos aceitos como
limitação física do scan em notas anteriores, ex. BDP de `salvador_ba`).

O texto abaixo é o resultado REAL de `_ocr_page` (Tesseract, zoom 3x, já com
os 3 recortes dedicados prependados) para a página 1 desta nota, usado como
fixture para travar a extração sem precisar rodar Tesseract no teste."""
import os
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_DANFE_PRODUTO
from src.models.nfe_produto_models import NfeProduto
from src.transformers.nfe_produto_transformer import NfeProdutoTransformer

MOCK_TEXT = (
    'O aca aci e\n'
    'PENELI METAIS LTDA\n'
    'P) CRUZEIRO DO SUL, 602\n'
    'IATE CANINDE\n'
    'METAIS\n'
    'A São Paulo - SP\n'
    'CO 03.033-020 (11) 3313-5675\n'
    'contato(Dpanelli.com.br\n\n'
    '<<<DANFE_PRODUTO_RECUT>>>\n'
    'Salvador 71) 33292-6847 BA |2-Isento 15:45:00\n'
    '| CÁLCULO DO IMPOSTO\n'
    '9.000,00 630,00 0,00 0,00 0,00 0,00 9.00€\n'
    '0,00 0,00 0,00 0,00 0,00 0,00 9.00\n\n'
    '<<<DANFE_PRODUTO_RECUT>>>\n'
    'CUD. PROD. DESCRIÇÃO DO PRODUTO/\n'
    'PIN POLÍCIA CIVIL BAHIA\n\n'
    '<<<DANFE_PRODUTO_RECUT>>>\n'
    'TRANSPORTADOR/VOLUMES TRANSPORTADOS r\n\n'
    'FRETE POR CONTA\n\n'
    'b - Sem Frete\n\n'
    'DADOS DO PRODUTO/SERVIÇO\n\n'
    'ooo | DESCRIÇÃODOPRONNSEAVIGO | NOM | sr foros [UND] aro. [Vaz UN [ui Tomar [scrous fx sonsurr me\n'
    'DOS DN DAT CTA PAAT RANTA 71171900 Qui 6102 | PC |1.500,000 mu 9.000,00 9 000,00 630,00 0,00) 7,00\n\n'
    '<<<DANFE_PRODUTO_RECUT>>>\n'
    'S DE PENELI METAIS LTDA OS PRODUTOS/SERVIÇOS CONSTANTES NA NOTA FISCAL ELETRÔNICA INDICADA AO LADO - DESTINATÁRIO: N\n'
    'O DOS DELEGADOS DE POLICIA DO ESTADO DA BAHIA - ADPE - RUA DIREITA DA PIEDADE, 11 - BARRIS - Salvador - BA - EMISSÃO: 27/07/2026 - F-e\n\n'
    'TOTAL: R$ 9.000,00 Nº: 764\n'
    'TA DE RECEBIMENTO IDENTIFICAÇÃO E ASSINATURA DO RECEBEDOR\n'
    'Série: 1\n'
    'T Sine |\n'
    'Dae | A\n'
    'PENELI METAIS LTDA Documento auxiliar\n'
    'da Nota Fiscal\n'
    'CRUZEIRO DO SUL, 602 Eletrônica [CHAVE DE ACESSO\n'
    '3526 0719 7997 5300 0137 5500 1000 0007 6418 6892 3434\n'
    'CANINDE Saída: 1\n'
    'Entrada: O\n'
    'São Paulo - SP FL 1/1\n'
    'Consulta de autenticidade no portal nacional da NF-e\n'
    '03.033-020 (11) 3313-5675 Nº: 764 www.nfe. fazenda. gov.br ou no site da Sefaz Autorizadora\n'
    'contato(Dpanelli.com.br Série: 1\n'
    'NATUREZA DA OPERAÇÃO PROTOCOLO DE AUTORIZAÇÃO DE USO\n'
    '[Venda NF-e 135263013284539 27/07/2026 15:55:33\n'
    'INSCRIÇÃO ESTADUAL INSCRIÇÃO ESTADUAL SUB. TRIBUTÁRIA [CPF/CNPJ\n'
    '143282435113 19.799.753/0001-37\n'
    'DESTINATÁRIO/REMETENTE\n'
    '[NOME/RAZÃO SOCIAL [CNPJ/CPF DATADA EMISSÃO |\n'
    'SINDICATO DOS DELEGADOS DE POLICIA DO ESTADO DA BAHIA - ADPE [73.393.696/0001-37 27/07/2026\n'
    'ENDEREÇO [BAJRRO/DISTRITO CEP IDATA DA ENTRADA\'S4\n'
    '[RUA DIREITA DA PIEDADE, 11 BARRIS 40.070-190 27/07/2026\n'
    'MUNICIPIO FONE/FAX UF INDICADOR IE peetisÃo ESTADUAL HORA DA ENTRADAS!\n'
    'Salvador (71) 33292-6847 BA |2-Isento 15:45:00\n'
    'CÁLCULO DO IMPOSTO\n'
    'BASE DE CALC. DE ICMS [VALOR ICMS BASEDE CALC DEICMS SI|VALOR ICMS ST VALOR PIS VALOR COFINS [VALOR TOTAL DOS PRODI\n'
    '9.000,00 630,00 0,00 0,00 0,00) 9.00€\n'
    '[o DESCONTO [VALOR FRETE [VALOR SEGURO VALOR DESP. ACESSORIAS| VALOR IPI VALOR IMP. IMPORT. [VALOR TOTAL DA N\n'
    '0,00) 0,00 0,00) 0,00) 0,00 9.00€\n'
    'TRANSPORTADOR/VOLUMES TRANSPORTADOS\n'
    '[FRETE POR CONTA\n'
    '9 - Sem Frete\n'
    'DADOS DO PRODUTO/SERVIÇO\n'
    '[ cóp. PROD. | — DESCRIÇÃO DO PRODUTOISERVIÇO NCMIsH | CsT [CFOP|UNID] QTD. | VIR UNIT. [VIR TOTAL| BCICMS [VR ICMS|VLR. IPI HEge TE\n'
    '004 E POLÍCIA CIVIL BAHIA TIITIa0O 000 [6102] PÇ [1.500,000 9 060,00] 9.000,00 630,00 0,00] 7,00\n\n'
    'DADOS ADICIONAIS\n'
    'INFORMAÇÕES COMPLEMENTARES\n'
    'CONTA JURIDICA NURAN!\n\n'
    'P1X:11585075775;\n\n'
    'RESERVADO AO FISCO\n\n'
    ': AGÊNCIA:O ; CONTA CO\n\n'
    'm\n'
)


def _novo_extrator():
    dummy_path = "tests/dummy_danfe_produto_escaneado.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = MOCK_TEXT
    extractor.from_ocr = True
    return extractor, dummy_path


def test_deteccao_tolerante_a_ocr_reconhece_danfe_produto_escaneado():
    extractor, dummy_path = _novo_extrator()
    try:
        assert extractor._detect_layout() == LAYOUT_DANFE_PRODUTO
        assert extractor._detect_layout_page(MOCK_TEXT) == LAYOUT_DANFE_PRODUTO
    finally:
        os.remove(dummy_path)


def test_extract_danfe_produto_escaneado_nota_764():
    """Regressão: garante que a nota vira exatamente 1 `NfeProduto` (não cai
    mais no fallback genérico de NFS-e) com chave de acesso, entidades, item
    e valores REAIS do documento."""
    extractor, dummy_path = _novo_extrator()
    try:
        nfe = extractor.parse()

        assert isinstance(nfe, NfeProduto)

        assert nfe.numero == "764"
        assert nfe.serie == "1"
        assert nfe.chave_acesso == "35260719799753000137550010000007641868923434"
        assert nfe.natureza_operacao == "Venda NF-e"
        assert nfe.tipo_operacao == "1"
        assert nfe.data_emissao.strftime("%d/%m/%Y") == "27/07/2026"
        assert nfe.protocolo_autorizacao == "135263013284539"
        assert nfe.protocolo_data_hora.strftime("%d/%m/%Y %H:%M:%S") == "27/07/2026 15:55:33"

        assert nfe.emitente.cnpj_cpf == "19.799.753/0001-37"
        assert nfe.emitente.inscricao_estadual == "143282435113"
        assert nfe.emitente.razao_social == "PENELI METAIS LTDA"
        assert nfe.emitente.endereco.logradouro == "CRUZEIRO DO SUL"
        assert nfe.emitente.endereco.numero == "602"
        assert nfe.emitente.endereco.bairro == "CANINDE"
        assert nfe.emitente.endereco.municipio == "São Paulo"
        assert nfe.emitente.endereco.uf == "SP"
        assert nfe.emitente.endereco.cep == "03033020"

        assert nfe.destinatario.cnpj_cpf == "73.393.696/0001-37"
        assert nfe.destinatario.razao_social == "SINDICATO DOS DELEGADOS DE POLICIA DO ESTADO DA BAHIA - ADPE"
        assert nfe.destinatario.endereco.logradouro == "RUA DIREITA DA PIEDADE"
        assert nfe.destinatario.endereco.numero == "11"
        assert nfe.destinatario.endereco.bairro == "BARRIS"
        assert nfe.destinatario.endereco.municipio == "Salvador"
        assert nfe.destinatario.endereco.uf == "BA"
        assert nfe.destinatario.endereco.cep == "40070190"

        assert len(nfe.itens) == 1
        item = nfe.itens[0]
        assert item.descricao == "PIN POLÍCIA CIVIL BAHIA"
        assert item.ncm == "71171900"
        assert item.cst_icms == "000"
        assert item.cfop == "6102"
        assert item.unidade == "PC"
        assert item.quantidade == 1500.0
        assert item.valor_unitario == 6.0
        assert item.valor_total == 9000.0
        assert item.base_calculo_icms == 9000.0
        assert item.valor_icms == 630.0
        assert item.aliquota_icms == 7.0

        assert nfe.valores.base_calculo_icms == 9000.0
        assert nfe.valores.valor_icms == 630.0
        assert nfe.valores.valor_total_produtos == 9000.0
        assert nfe.valores.valor_total_nota == 9000.0
        assert nfe.valores.valor_frete == 0.0
        assert nfe.valores.desconto == 0.0

        xml = NfeProdutoTransformer().transform(nfe)
        assert "35260719799753000137550010000007641868923434" in xml
        assert "<vICMS>630.00</vICMS>" in xml or "<vICMS>630.0</vICMS>" in xml
        assert "<CNPJ>73393696000137</CNPJ>" in xml
    finally:
        os.remove(dummy_path)


def test_codigo_do_produto_cai_no_generico_com_aviso_quando_ilegivel():
    # O código impresso ("004") resiste a toda tentativa de recorte dedicada
    # (achado real, testado até zoom 10x/PSM 6-7-8-10 com whitelist
    # numérico) - mantido em "0001" com aviso explícito, sem fabricar.
    extractor, dummy_path = _novo_extrator()
    try:
        nfe = extractor.parse()
        assert nfe.itens[0].codigo == "0001"
        assert any("ódigo do produto" in a for a in nfe.avisos)
    finally:
        os.remove(dummy_path)


def test_nao_regride_caminho_digital_do_danfe_produto():
    """`from_ocr=False` deve continuar usando `_parse_danfe_produto` (o
    parser digital, validado contra a nota nº 52.136/GRAN COFFEE) - nunca
    `_parse_danfe_produto_ocr`, mesmo que o texto (por acidente) contenha as
    marcas OCR-tolerantes."""
    extractor, dummy_path = _novo_extrator()
    try:
        extractor.from_ocr = False
        # Sem `from_ocr`, a detecção volta a exigir as 4 marcas do caminho
        # digital (ausentes neste texto OCR) - cai no fallback genérico, não
        # em LAYOUT_DANFE_PRODUTO.
        assert extractor._detect_layout() != LAYOUT_DANFE_PRODUTO
    finally:
        os.remove(dummy_path)
