# -*- coding: utf-8 -*-
r"""DANFE Estadual (NF-e Modelo 55) da GRAN COFFEE COM. LOC. E SERVICOS S.A.
(CNPJ 08.736.011/0009-01, Lauro de Freitas/BA) -> SINDICATO DOS DELEGADOS DE
POLICIA DO ESTADO DA BAHIA (Salvador/BA), venda de café, nota nº 52.136,
R$ 595,00 - achado no pedido do usuário para verificar o "layout DANFE
estadual". Antes deste layout: a nota caía inteira em LAYOUT_LOCALIZA (o
rótulo genérico "FATURA/DUPLICATA", presente em qualquer DANFE, colidia com a
marca da locadora Localiza) e saía com tomador não identificado, valor
zerado, discriminação genérica e o prestador hardcoded errado ("LOCALIZA RENT
A CAR S/A" - nome de OUTRO emitente fixo). Este é o primeiro documento de
PRODUTO (NF-e Modelo 55/ICMS) tratado pelo conversor - retorna um `NfeProduto`
(não um `Nfse`).

Texto REAL extraído por pdfminer (`extract_text`) - PDF DIGITAL, sem OCR.
Gerado por script (nunca digitado à mão) para preservar acentos/quebras de
linha exatos, conforme convenção do projeto.
"""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_DANFE_PRODUTO
from src.models.nfe_produto_models import NfeProduto
from src.transformers.nfe_produto_transformer import NfeProdutoTransformer

MOCK_TEXT = 'RECEBEMOS DE GRAN COFFEE COM. LOC. E SERVICOS S.A. OS PRODUTOS CONSTANTES DA NOTA FISCAL INDICADA AO LADO 37396 - SINDICATOS DOS DELEGADOS DE POLICIA\nDO ESTADO DA BAHIA -ADPE - <SEM REGIAO> - (R$ 595,00)(quinhentos e noventa e cinco reais)\n\nDATA DE RECEBIMENTO\n\nIDENTIFICAÇÃO E ASSINATURA DO RECEBEDOR\n\nNF-e\n\nN. 52.136\nSÉRIE 1\n\nGRAN COFFEE COM. LOC. E SERVICOS\n\nR (Rua) Doutor Gerino de Souza Filho\nN.1297 - GALPAO 002\nBairro ITINGA,Lauro de Freitas, BA\nFone: (19) 3514-7500, CEP:42738200\n\nDANFE\nDocumento\nAuxiliar da Nota\nFiscal Eletrônica\n\n0 - ENTRADA\n1 - SAÍDA\n\n1\n\nN. 52.136\nSÉRIE 1\n\nFOLHA 1/\n\n1\n\nCHAVE DE ACESSO\n\n2926 0108 7360 1100 0901 5500 1000 0521 3610 9720 9884\n\nConsulta de autenticidade no portal nacional da NF-e\nwww.nfe.fazenda.gov.br/portal ou no site da Sefaz\nAutorizadora\n\nNATUREZA DA OPERAÇÃO\nVENDA MERC ADQ OU REC TERC\nINSCRIÇÃO ESTADUAL\n148261549\nDESTINATÁRIO/REMETENTE\n\nINSC. ESTADUAL DO SUBST. TRIBUTÁRIO\n\nPROTOCOLO DE AUTORIZAÇÃO DE USO\n129261580397578 15/01/2026 21:03:59\n\nCNPJ\n08.736.011/0009-01\n\nNOME/RAZÃO SOCIAL\nSINDICATOS DOS DELEGADOS DE POLICIA DO ESTADO DA BAHIA -\nENDEREÇO\nRUA DIREITA DA PIEDADE N. 11\nMUNICÍPIO\nSALVADOR\nFATURA/DUPLICATA\nBOLETO 10 DIAS  - ITAU| BOL=001 Venc=26/01/2026 Valor=595,00\n\nFONE/FAX\n\n37396\n\nCNPJ/CPF\n73.393.696/0001-37\n\nBAIRRO/DISTRITO\nBARRIS\n\nCEP\n40.070-190\n\nUF\nBA\n\nINSCRIÇÃO ESTADUAL\n\nDATA DA EMISSÃO\n15-01-2026\nDATA DA ENTRADA/SAÍDA\n15-01-2026\nHORA DA SAÍDA\n21:03:56\n\nCÁLCULO DE IMPOSTO\n\nBASE DE CÁLCULO DO ICMS\n\nVALOR DO ICMS\n\nBASE DE CÁLCULO DO ICMS ST\n\nVALOR DO ICMS ST\n\nVALOR TOTAL DOS PRODUTOS\n\n595,00\n\n121,98\n\n0,00\n\n0,00\n\nVALOR DO FRETE\n\nVALOR DO SEGURO\n\nDESCONTO\n\nOUTRAS DESPESAS ACESSÓRIAS\n\nVALOR DO IPI\n\nVALOR TOTAL DA NOTA\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n595,00\n\n595,00\n\nTRANSPORTADOR/VOLUMES TRANSPORTADOS\n\nRAZÃO SOCIAL\nGRAN COFFEE COMERCIO, LOCACAO E SERVICOS S.A -\nENDEREÇO\nR (Rua) Doutor Gerino de Souza Filho N. 1297\nQUANTIDADE\n\nESPÉCIE\n\nMARCA\n\n5,00\n\nDADOS DOS PRODUTOS/SERVIÇOS\n\nFRETE POR CONTA\n\n0 - Emitente\n\nCÓDIGO ANTT\n\nPLACA DO VEÍCULO\n\nUF\n\nMUNICÍPIO\nLauro de Freitas\nNÚMERO\n\nPESO BRUTO\n\nUF\nBA\n\nCNPJ/CPF\n08.736.011/0009-01\nINSCRIÇÃO ESTADUAL\n148261549\nPESO LÍQUIDO\n\n5,0000 Kg\n\n5,0000 Kg\n\nCÓD. PROD\n\nDESCRIÇÃO DOS PRODUTOS/SERVIÇOS\n\nNCM/SH\n\nCST\n\nCFOP\n\nUN.\n\nQUANT.\n\nV. UNITÁRIO\n\nV. DESC.\n\n% DESC.\n\nV. TOTAL\n\nBC ICMS\n\nV. ICMS\n\nVALOR\nIPI\n\nALÍQUOTA\nIPI\n\nICMS\n\n514859\n\nCAFE CDC BARISTA GOURMET GRAO 1KG\n\n09012100\n\n000\n\n5102\n\nKG\n\n5,00\n\n119,000\n\n0,00\n\n0,00\n\n595,00\n\n595,00\n\n121,98\n\n20,50\n\nCÁLCULO DO ISSQN\n\nINSCRIÇÃO MUNICIPAL\n\nDADOS ADICIONAIS\n\nVALOR TOTAL DOS SERVIÇOS\n\nBASE DE CÁLCULO DE ISSQN\n\nVALOR DO ISSQN\n\n0,00\n\n0,00\n\n0,00\n\nINFORMAÇÕES COMPLEMENTARES\nCLIENTE VAI RETIRAR EM00001018725 - administrativo@adpeb.com.br - das 08:30 as 16:30\n(segunda a sexta / Em frente a Loja Humanas | | Ped: 3200625 | ENTREGAR: RUA DIREITA DA\nPIEDADE,11 - BARRIS, SALVADOR - BA, 40070190\n\nRESERVADO AO FISCO\n\n\x0c'


def test_detect_layout_danfe_produto():
    dummy_path = "tests/dummy_danfe_produto.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    try:
        ex = SPPdfExtractor(dummy_path)
        ex.raw_text = MOCK_TEXT
        assert ex._detect_layout() == LAYOUT_DANFE_PRODUTO
        assert ex._detect_layout_page(MOCK_TEXT) == LAYOUT_DANFE_PRODUTO
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_extract_danfe_produto_nota_52136(monkeypatch):
    """Regressão: garante que a nota vira exatamente 1 `NfeProduto` (não cai
    mais em LAYOUT_LOCALIZA) com chave de acesso, entidades, item e valores
    REAIS do documento - nenhum campo fabricado/zerado por engano."""
    dummy_path = "tests/dummy_danfe_produto_full.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        resultados = extractor.parse_multiple()
        assert len(resultados) == 1
        nfe = resultados[0]

        assert isinstance(nfe, NfeProduto)
        assert nfe.avisos == []

        assert nfe.numero == "52136"
        assert nfe.serie == "1"
        assert nfe.chave_acesso == "29260108736011000901550010000521361097209884"
        assert nfe.natureza_operacao == "VENDA MERC ADQ OU REC TERC"
        assert nfe.data_emissao.strftime("%d/%m/%Y") == "15/01/2026"
        assert nfe.protocolo_autorizacao == "129261580397578"
        assert nfe.protocolo_data_hora.strftime("%d/%m/%Y %H:%M:%S") == "15/01/2026 21:03:59"

        assert nfe.emitente.cnpj_cpf == "08.736.011/0009-01"
        assert nfe.emitente.razao_social == "GRAN COFFEE COM. LOC. E SERVICOS"
        assert nfe.emitente.endereco.municipio == "Lauro de Freitas"
        assert nfe.emitente.endereco.uf == "BA"
        assert nfe.emitente.endereco.codigo_municipio == "2919207"

        assert nfe.destinatario.cnpj_cpf == "73.393.696/0001-37"
        assert nfe.destinatario.razao_social == "SINDICATOS DOS DELEGADOS DE POLICIA DO ESTADO DA BAHIA"
        assert nfe.destinatario.endereco.municipio == "SALVADOR"
        assert nfe.destinatario.endereco.codigo_municipio == "2927408"

        assert len(nfe.itens) == 1
        item = nfe.itens[0]
        assert item.codigo == "514859"
        assert item.ncm == "09012100"
        assert item.cfop == "5102"
        assert item.quantidade == 5.0
        assert item.valor_total == 595.0
        assert item.valor_icms == 121.98
        assert item.aliquota_icms == 20.5

        assert nfe.valores.valor_total_produtos == 595.0
        assert nfe.valores.valor_total_nota == 595.0
        assert nfe.valores.valor_icms == 121.98

        assert nfe.transportador is not None
        assert nfe.transportador.cnpj_cpf == "08.736.011/0009-01"
        assert nfe.transportador.peso_liquido == 5.0

        xml = NfeProdutoTransformer().transform(nfe)
        assert "29260108736011000901550010000521361097209884" in xml
        assert "<vICMS>121.98</vICMS>" in xml
        assert "<vNF>595.00</vNF>" in xml
        assert "<CNPJ>73393696000137</CNPJ>" in xml
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
