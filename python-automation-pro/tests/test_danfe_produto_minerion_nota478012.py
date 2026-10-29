# -*- coding: utf-8 -*-
r"""DANFE (NF-e Modelo 55) DIGITAL emitido pelo sistema "Minerion" - nota nº
478012, STONE BUILDING SA INDUSTRIA E COMERCIO (CNPJ 03.918.238/0001-99,
Bragança Paulista/SP) -> H. Z. PATRIMONIAL LTDA. (CNPJ 10.791.569/0001-76,
Lauro de Freitas/BA), PEDRISCO LIMPO, R$ 1.498,00.

Antes (achado real 2026-10-28): detectada como LAYOUT_DANFE_PRODUTO, mas
`_parse_danfe_produto` (regex escritas para a GRAN COFFEE, nota 52.136)
devolvia nNF 1, Id "NFe" vazio, série 1, dhEmi = hora da conversão, emitente
com razão social "Mot.:ALCINO APARECIDO RAMOS" (o MOTORISTA do canhoto) e
endereço vazio, destinatário não identificado, totais zerados, sem itens e
modFrete 9. Causas: "Nº 0478012" (não "N. 52.136"), chave impressa com PONTOS
e longe do rótulo, data "21/07/2026" (não "15-01-2026"), " em " no protocolo,
letterhead depois de "Mot.:" + código de barras no canhoto, caixas
rótulo\nvalor numa ordem própria, grade CÁLCULO DO IMPOSTO com os rótulos em
outros pontos e itens com "NCM CST CFOP" numa linha só.

Textos REAIS extraídos por pdfminer (`extract_text`) dos PDFs digitais
(nº 478012 e nº 477985 - mesmo emitente/gerador), gerados por script (nunca
digitados à mão).
"""
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_DANFE_PRODUTO
from src.extractors import danfe_produto_texto as dt
from src.models.nfe_produto_models import NfeProduto
from src.transformers.nfe_produto_transformer import NfeProdutoTransformer

MOCK_TEXT_478012 = "RECEBEMOS DE STONE BUILDING SA INDUSTRIA E COMERCIOOS PRODUTOS CONSTANTES NA NF-e.\n21/07/2026\n\nDestinatário:  H. Z. PATRIMONIAL LTDA.\n\nValor:  1.498,00\n\nDATA DE RECEBIMENTO\n\nIDENTIFICAÇÃO E ASSINATURA DO RECEBEDOR\n\nMot.:ALCINO APARECIDO RAMOS\n\nÊC:'#{rFÌ!ÄWÌÌÌOp,*'[CÌKËÍ\n\nNF-e\n\nNº 0478012\n\nSérie 0\n\nSTONE BUILDING SA INDUSTRIA E COMERCIO\n\nROD FERNAO DIAS, KM 13,5, SN\n\nGUARIPOCABA\n\nBRAGANCA PAULISTA-SP\n\nCEP: 12914970\n\nTel: 11965331100\n\nDANFE\nDocumento Auxiliar da\nNota Fiscal Eletrônica\n\n0 - ENTRADA\n1 - SAÍDA\n\n1\n\nCHAVE DE ACESSO\n\nNº 0478012\nSérie 0\n\nFL. 1/1\n\n35.2607.03918238000199.55.000.000478012.1.00759350.0\nÊC:'#{rFÌ!ÄWÌÌÌOp,*'[CÌKËÍ\n\n          Consulta de autenticidade no portal nacional da NF-e\n  www.nfe.fazenda.gov.br/portal ou no site da Sefaz Autorizadora\n\nNATUREZA DA OPERAÇÃO\nVDA. PROD .ESTAB.\n\nINSCRIÇÃO ESTADUAL\n225.185.878.112\n\nDESTINATÁRIO/REMETENTE\n\nNOME/RAZÃO SOCIAL\nH. Z. PATRIMONIAL LTDA.\n\nINSC. ESTADUAL DO SUBST. TRIBUTÁRIO\n\nPROTOCOLO DE AUTORIZAÇÃO DE USO\n\n135262915256739 em 21/07/2026 07:59:48\n\nCNPJ\n03.918.238/0001-99\n\nCNPJ/CPF\n10.791.569/0001-76\n\nDATA DE EMISSÃO\n21/07/2026\n\nENDEREÇO\nAV LUIZ TARQUINIO PONTES, 2580, SALA 311 EDF VILLAS\n\nBAIRRO/DISTRITO\nBURAQUINHO\n\nCEP\n42700130\n\nMUNICÍPIO\nLAURO DE FREITAS\n\nFATURA\n\nFONE/FAX\n822237695\n\nUF\nBA\n\nINSCRIÇÃO ESTADUAL\nISENTO\n\nDATA DA SAÍDA/ENTRADA\n21/07/2026\n\nHORA DA SAÍDA/ENTRADA\n07:59\n\nNÚMERO\n\nVENCIMENTO\n\nVALOR\n\nNÚMERO\n\nVENCIMENTO\n\nVALOR\n\nNÚMERO\n\nVENCIMENTO\n\nVALOR\n\n478012\n\n20/08/2026\n\n1.498,00\n\nCÁLCULO DO IMPOSTO\n\nBASE DE CÁLCULO DO ICMS\n\nVALOR DO ICMS\n\nBASE DE CÁLCULO DO ICMS S.T\n\nVALOR DO ICMS SUBSTITUIÇÃO\n\nVALOR TOTAL DOS PRODUTOS\n\n1.498,00\n\n104,86\n\n0,00\n\nVALOR DO FRETE\n\nVALOR DO SEGURO\n\nDESCONTO\n\nOUTRAS DESPESAS\n\nVALOR DO IPI\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\nVALOR TOTAL DA NOTA\n\n1.498,00\n\n1.498,00\n\nTRANSPORTADOR/VOLUMES TRANSPORTADOS\n\nRAZÃO SOCIAL\nALCINO APARECIDO RAMOS\n\nENDEREÇO\n\nQUANTIDADE\n\nESPÉCIE\nTONELADA\n\nDADOS DOS PRODUTOS/SERVIÇOS\n\nFRETE POR CONTA\n0-EMIT ENT E\n1-DEST /RE M\n\n2-T ERC.\n9-SEM FRET E\n\n1\n\nCÓDIGO A NT T\n\nPLACA\nHMM-0B71\n\nMUNICÍPIO\n\nUF\nSP\n\nUF\n\nCNPJ/CPF\n\nINSCRIÇÃO ESTADUAL\n\nMARCA\n\nNUMERAÇÃO\n\nPESO BRUTO\n\nPESO LÍQUIDO\n\n23.820kg\n\n14.000kg\n\nCÓDIGO\n\nDESCRIÇÃO DO PRODUTO/SERVIÇO\n\nNCM/SH CST CFOP UNID. QUANT.\n\nVR. UNIT.\n\nVALOR\n\nBC. ICMS\n\nV. ICMS\n\nV. IPI\n\nALIQ.\nICMS\n\nALIQ.\nIPI\n\n9\n\nPEDRISCO LIMPO\n\n25171000 000 6101\n\nT\n\n14,00\n\n107,00\n\n1.498,00\n\n1.498,00\n\n104,86\n\n7\n\nDADOS ADICIOINAIS\n\nRESERVADO AO FISCO\n\nCST 00 : 000 - TRIBUTACAO INTEGRAL\nValor Aproximado dos Tributos (19,85%) = 297,35   Fonte: IBPT\n\nPlacas: Cavalo: HMM-0B71\n\nPedido: 3667     Data do Pedido 20/07/2026\nRepresentante: MITSUO (3)\nNUMERO DE INSCRICAO DA OBRA: 90.029.45768/71...NOME DA OBRA:\nH.Z PATRIMONIAL...CADASTRO IMOBILIARIO: 0100051816505001...CNAE:\n4120400 CONSTRUCAO DE EDIFICIO // 4399103 OBRAS DE\nALVENARIA...NUMERO DO ALVARA: 224.617062026...ENDERECO:\nEXTREMA-MG / BAIRRO DOS TENENTES / RUA JOAO BATISTA CARDOSO\nS/N...RESPONSAVEL: H.Z PATRIMONIAL / CNPJ: 10.791.569/0001-\n76....ALEXANDRE:14 98223-7695\n\nCond.Pgto: 30 dias - Bancaria (20/08/2026)\n\n \n \n \n\x0c"

MOCK_TEXT_477985 = "RECEBEMOS DE STONE BUILDING SA INDUSTRIA E COMERCIOOS PRODUTOS CONSTANTES NA NF-e.\n20/07/2026\n\nDestinatário:  H. Z. PATRIMONIAL LTDA.\n\nValor:  1.637,34\n\nDATA DE RECEBIMENTO\n\nIDENTIFICAÇÃO E ASSINATURA DO RECEBEDOR\n\nMot.:JOSE ROBERTO VICENTIN DE ALMEIDA\n\nÊC:'#{rFÌ!ÄWÌÌÌOou*'[?oFËÍ\n\nNF-e\n\nNº 0477985\n\nSérie 0\n\nSTONE BUILDING SA INDUSTRIA E COMERCIO\n\nROD FERNAO DIAS, KM 13,5, SN\n\nGUARIPOCABA\n\nBRAGANCA PAULISTA-SP\n\nCEP: 12914970\n\nTel: 11965331100\n\nDANFE\nDocumento Auxiliar da\nNota Fiscal Eletrônica\n\n0 - ENTRADA\n1 - SAÍDA\n\n1\n\nNº 0477985\nSérie 0\n\nFL. 1/1\n\nNATUREZA DA OPERAÇÃO\nVDA. PROD .ESTAB.\n\nINSCRIÇÃO ESTADUAL\n225.185.878.112\n\nDESTINATÁRIO/REMETENTE\n\nNOME/RAZÃO SOCIAL\nH. Z. PATRIMONIAL LTDA.\n\nCHAVE DE ACESSO\n35.2607.03918238000199.55.000.000477985.1.00759317.9\nÊC:'#{rFÌ!ÄWÌÌÌOou*'[?oFËÍ\n\n          Consulta de autenticidade no portal nacional da NF-e\n  www.nfe.fazenda.gov.br/portal ou no site da Sefaz Autorizadora\n\nPROTOCOLO DE AUTORIZAÇÃO DE USO\n\n135262904410536 em 20/07/2026 14:54:23\n\nINSC. ESTADUAL DO SUBST. TRIBUTÁRIO\n\nCNPJ\n03.918.238/0001-99\n\nCNPJ/CPF\n10.791.569/0001-76\n\nDATA DE EMISSÃO\n20/07/2026\n\nENDEREÇO\nAV LUIZ TARQUINIO PONTES, 2580, SALA 311 EDF VILLAS\n\nBAIRRO/DISTRITO\nBURAQUINHO\n\nCEP\n42700130\n\nMUNICÍPIO\nLAURO DE FREITAS\n\nFATURA\n\nFONE/FAX\n822237695\n\nUF\nBA\n\nINSCRIÇÃO ESTADUAL\nISENTO\n\nDATA DA SAÍDA/ENTRADA\n20/07/2026\n\nHORA DA SAÍDA/ENTRADA\n14:54\n\nNÚMERO\n\nVENCIMENTO\n\nVALOR\n\nNÚMERO\n\nVENCIMENTO\n\nVALOR\n\nNÚMERO\n\nVENCIMENTO\n\nVALOR\n\n477985\n\n19/08/2026\n\n1.637,34\n\nCÁLCULO DO IMPOSTO\n\nBASE DE CÁLCULO DO ICMS\n\nVALOR DO ICMS\n\nBASE DE CÁLCULO DO ICMS S.T\n\nVALOR DO ICMS SUBSTITUIÇÃO\n\nVALOR TOTAL DOS PRODUTOS\n\n1.637,34\n\n114,61\n\n0,00\n\nVALOR DO FRETE\n\nVALOR DO SEGURO\n\nDESCONTO\n\nOUTRAS DESPESAS\n\nVALOR DO IPI\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\nVALOR TOTAL DA NOTA\n\n1.637,34\n\n1.637,34\n\nTRANSPORTADOR/VOLUMES TRANSPORTADOS\n\nRAZÃO SOCIAL\nJOSE ROBERTO VICENTIN DE ALMEIDA\n\nENDEREÇO\n\nQUANTIDADE\n\nESPÉCIE\nTONELADA\n\nDADOS DOS PRODUTOS/SERVIÇOS\n\nFRETE POR CONTA\n0-EMIT ENT E\n1-DEST /REM\n\n2-T ERC.\n9-SEM FRET E\n\n1\n\nCÓDIGO ANT T\n\nPLACA\nAVF-2D87\n\nMUNICÍPIO\n\nUF\nSP\n\nUF\n\nCNPJ/CPF\n\nINSCRIÇÃO ESTADUAL\n\nMARCA\n\nNUMERAÇÃO\n\nPESO BRUTO\n\nPESO LÍQUIDO\n\n31.360kg\n\n18.820kg\n\nCÓDIGO\n\nDESCRIÇÃO DO PRODUTO/SERVIÇO\n\nNCM/SH CST CFOP UNID. QUANT.\n\nVR. UNIT.\n\nVALOR\n\nBC. ICMS\n\nV. ICMS\n\nV. IPI\n\nALIQ.\nICMS\n\nALIQ.\nIPI\n\n11\n\nBICA CORRIDA\n\n25171000 000 6101\n\nT\n\n18,82\n\n87,00\n\n1.637,34\n\n1.637,34\n\n114,61\n\n7\n\nDADOS ADICIOINAIS\n\nRESERVADO AO FISCO\n\nCST 00 : 000 - TRIBUTACAO INTEGRAL\nValor Aproximado dos Tributos (19,85%) = 325,01   Fonte: IBPT\n\nPlacas: Cavalo: AVF-2D87\n\nPedido: 3667     Data do Pedido 20/07/2026\nRepresentante: MITSUO (3)\nNUMERO DE INSCRICAO DA OBRA: 90.029.45768/71...NOME DA OBRA:\nH.Z PATRIMONIAL...CADASTRO IMOBILIARIO: 0100051816505001...CNAE:\n4120400 CONSTRUCAO DE EDIFICIO // 4399103 OBRAS DE\nALVENARIA...NUMERO DO ALVARA: 224.617062026...ENDERECO:\nEXTREMA-MG / BAIRRO DOS TENENTES / RUA JOAO BATISTA CARDOSO\nS/N...RESPONSAVEL: H.Z PATRIMONIAL / CNPJ: 10.791.569/0001-\n76....ALEXANDRE:14 98223-7695\n\nCond.Pgto: 30 dias - Bancaria (19/08/2026)\n\n \n \n \n\x0c"


def _parse(monkeypatch, tmp_path, texto):
    dummy = tmp_path / "danfe_minerion.pdf"
    dummy.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: texto)
    res = SPPdfExtractor(str(dummy)).parse_multiple()
    assert len(res) == 1
    assert isinstance(res[0], NfeProduto)
    return res[0]


def test_detecta_danfe_produto():
    ex = SPPdfExtractor("inexistente.pdf")
    ex.raw_text = MOCK_TEXT_478012
    assert ex._detect_layout() == LAYOUT_DANFE_PRODUTO


def test_nota_478012_cabecalho_e_chave(monkeypatch, tmp_path):
    nfe = _parse(monkeypatch, tmp_path, MOCK_TEXT_478012)
    assert nfe.avisos == []
    assert nfe.chave_acesso == "35260703918238000199550000004780121007593500"
    assert nfe.numero == "478012"
    assert nfe.serie == "0"
    assert nfe.tipo_operacao == "1"
    assert nfe.natureza_operacao == "VDA. PROD .ESTAB."
    assert nfe.data_emissao.strftime("%d/%m/%Y %H:%M") == "21/07/2026 00:00"
    assert nfe.data_saida_entrada.strftime("%d/%m/%Y") == "21/07/2026"
    assert nfe.protocolo_autorizacao == "135262915256739"
    assert nfe.protocolo_data_hora.strftime("%d/%m/%Y %H:%M:%S") == "21/07/2026 07:59:48"


def test_nota_478012_emitente_nao_e_o_motorista(monkeypatch, tmp_path):
    e = _parse(monkeypatch, tmp_path, MOCK_TEXT_478012).emitente
    assert e.razao_social == "STONE BUILDING SA INDUSTRIA E COMERCIO"
    assert "Mot." not in e.razao_social
    assert e.cnpj_cpf == "03.918.238/0001-99"
    assert e.inscricao_estadual == "225185878112"
    assert e.endereco.logradouro == "ROD FERNAO DIAS, KM 13,5"
    assert e.endereco.numero == "SN"
    assert e.endereco.bairro == "GUARIPOCABA"
    assert e.endereco.municipio == "BRAGANCA PAULISTA"
    assert e.endereco.uf == "SP"
    assert e.endereco.codigo_municipio == "3507605"
    assert e.endereco.cep == "12914970"
    assert e.telefone == "11965331100"


def test_nota_478012_destinatario(monkeypatch, tmp_path):
    d = _parse(monkeypatch, tmp_path, MOCK_TEXT_478012).destinatario
    assert d.razao_social == "H. Z. PATRIMONIAL LTDA."
    assert d.cnpj_cpf == "10.791.569/0001-76"
    assert d.endereco.logradouro == "AV LUIZ TARQUINIO PONTES"
    assert d.endereco.numero == "2580"
    assert d.endereco.complemento == "SALA 311 EDF VILLAS"
    assert d.endereco.bairro == "BURAQUINHO"
    assert d.endereco.cep == "42700130"
    assert d.endereco.municipio == "LAURO DE FREITAS"
    assert d.endereco.uf == "BA"
    assert d.endereco.codigo_municipio == "2919207"
    assert d.inscricao_estadual == "ISENTO"
    assert d.telefone == "822237695"


def test_nota_478012_item_totais_transporte_fatura(monkeypatch, tmp_path):
    nfe = _parse(monkeypatch, tmp_path, MOCK_TEXT_478012)
    assert len(nfe.itens) == 1
    it = nfe.itens[0]
    assert (it.codigo, it.descricao, it.ncm, it.cst_icms, it.cfop, it.unidade) == (
        "9", "PEDRISCO LIMPO", "25171000", "000", "6101", "T")
    assert (it.quantidade, it.valor_unitario, it.valor_total) == (14.0, 107.0, 1498.0)
    assert (it.base_calculo_icms, it.valor_icms, it.aliquota_icms) == (1498.0, 104.86, 7.0)

    v = nfe.valores
    assert (v.base_calculo_icms, v.valor_icms, v.base_calculo_icms_st, v.valor_icms_st) == (1498.0, 104.86, 0.0, 0.0)
    assert (v.valor_total_produtos, v.valor_total_nota) == (1498.0, 1498.0)
    assert (v.valor_frete, v.valor_seguro, v.desconto, v.outras_despesas, v.valor_ipi) == (0.0,) * 5

    tr = nfe.transportador
    assert tr.razao_social == "ALCINO APARECIDO RAMOS"
    assert tr.frete_por_conta == "1"
    assert tr.placa_veiculo == "HMM-0B71"
    assert tr.uf is None  # "SP" impresso é a UF da PLACA, não do transportador
    assert tr.cnpj_cpf is None
    assert tr.especie == "TONELADA"
    assert (tr.peso_bruto, tr.peso_liquido) == (23820.0, 14000.0)

    assert nfe.fatura_duplicata == "478012 Venc=20/08/2026 Valor=1.498,00"
    assert nfe.informacoes_complementares.startswith("CST 00 : 000 - TRIBUTACAO INTEGRAL")
    assert "Pedido: 3667" in nfe.informacoes_complementares
    assert nfe.informacoes_complementares.endswith("Cond.Pgto: 30 dias - Bancaria (20/08/2026)")


def test_nota_478012_xml(monkeypatch, tmp_path):
    xml = NfeProdutoTransformer().transform(_parse(monkeypatch, tmp_path, MOCK_TEXT_478012))
    for trecho in (
        'Id="NFe35260703918238000199550000004780121007593500"',
        "<cUF>35</cUF>", "<cNF>00759350</cNF>", "<serie>0</serie>", "<nNF>478012</nNF>",
        "<dhEmi>2026-07-21T00:00:00-03:00</dhEmi>", "<idDest>2</idDest>", "<cMunFG>3507605</cMunFG>",
        "<cDV>0</cDV>", "<xNome>STONE BUILDING SA INDUSTRIA E COMERCIO</xNome>",
        "<CNPJ>10791569000176</CNPJ>", "<cMun>2919207</cMun>", "<NCM>25171000</NCM>",
        "<CFOP>6101</CFOP>", "<pICMS>7.00</pICMS>", "<vICMS>104.86</vICMS>",
        "<vProd>1498.00</vProd>", "<vNF>1498.00</vNF>", "<modFrete>1</modFrete>",
        "<nFat>478012</nFat>", "<nProt>135262915256739</nProt>",
    ):
        assert trecho in xml, trecho
    assert "Mot.:" not in xml


def test_nota_477985_mesmo_gerador(monkeypatch, tmp_path):
    """Não-regressão: 2ª nota do mesmo emitente/gerador (chave impressa num
    ponto diferente do texto)."""
    nfe = _parse(monkeypatch, tmp_path, MOCK_TEXT_477985)
    assert nfe.avisos == []
    assert nfe.numero == "477985"
    assert nfe.chave_acesso == "35260703918238000199550000004779851007593179"
    assert nfe.emitente.razao_social == "STONE BUILDING SA INDUSTRIA E COMERCIO"
    assert nfe.destinatario.cnpj_cpf == "10.791.569/0001-76"
    assert len(nfe.itens) == 1 and nfe.itens[0].descricao == "BICA CORRIDA"
    assert nfe.itens[0].quantidade == 18.82
    assert nfe.valores.valor_total_nota == 1637.34
    assert nfe.valores.valor_icms == 114.61
    assert nfe.transportador.razao_social == "JOSE ROBERTO VICENTIN DE ALMEIDA"
    assert nfe.transportador.frete_por_conta == "1"


# --- integridade fiscal: valor que não fecha vira aviso, nunca chute ---

def test_chave_com_digito_trocado_e_recusada(monkeypatch, tmp_path):
    texto = MOCK_TEXT_478012.replace(
        "35.2607.03918238000199.55.000.000478012.1.00759350.0",
        "35.2607.03918238000199.55.000.000478012.1.00759351.0")
    assert texto != MOCK_TEXT_478012
    nfe = _parse(monkeypatch, tmp_path, texto)
    assert nfe.chave_acesso == ""
    assert "Chave de acesso não encontrada ou incompleta" in nfe.avisos
    assert nfe.numero == "478012"  # ainda lido do "Nº" impresso


def test_grade_que_nao_fecha_zera_totais_com_aviso(monkeypatch, tmp_path):
    # VALOR TOTAL DA NOTA adulterado: nenhuma atribuição fecha a identidade.
    texto = MOCK_TEXT_478012.replace(
        "VALOR TOTAL DA NOTA\n\n1.498,00\n\n1.498,00",
        "VALOR TOTAL DA NOTA\n\n1.498,00\n\n1.598,00")
    assert texto != MOCK_TEXT_478012
    nfe = _parse(monkeypatch, tmp_path, texto)
    assert nfe.valores.valor_total_nota == 0.0
    assert any("não fecha" in a for a in nfe.avisos)


def test_item_com_icms_que_nao_fecha_gera_aviso(monkeypatch, tmp_path):
    texto = MOCK_TEXT_478012.replace("1.498,00\n\n104,86\n\n7\n", "1.498,00\n\n105,86\n\n7\n")
    assert texto != MOCK_TEXT_478012
    nfe = _parse(monkeypatch, tmp_path, texto)
    assert any("Item 9: BC ICMS x ALÍQ." in a for a in nfe.avisos)


# --- funções puras ---

@pytest.mark.parametrize("linha,esperado", [
    ("AV LUIZ TARQUINIO PONTES, 2580, SALA 311 EDF VILLAS", ("AV LUIZ TARQUINIO PONTES", "2580", "SALA 311 EDF VILLAS")),
    ("ROD FERNAO DIAS, KM 13,5, SN", ("ROD FERNAO DIAS, KM 13,5", "SN", None)),
    ("AV LUIZ TARQUINIO PONTES, 2580  SALA 311", ("AV LUIZ TARQUINIO PONTES", "2580", "SALA 311")),
    ("AVEN LUIZ TARQUINIO PONTES, 2580 - SALA 311", ("AVEN LUIZ TARQUINIO PONTES", "2580", "SALA 311")),
    ("RUA SEM NUMERO", ("RUA SEM NUMERO", None, None)),
])
def test_separar_logradouro(linha, esperado):
    assert dt.separar_logradouro(linha) == esperado


def test_rotulo_seguido_de_rotulo_nao_vira_valor():
    sec = "ENDEREÇO\n\nQUANTIDADE\n\nUF\n(71)99988-8081\nBA\n"
    assert dt.valor_do_rotulo(sec, r"ENDERE[ÇC]O", dt.val_texto) is None
    assert dt.valor_do_rotulo(sec, r"UF", dt.val_uf) is None  # valor de outro tipo


def test_destinatario_ignora_bloco_local_de_retirada():
    texto = ("DESTINATÁRIO / REMETENTE\nNOME / RAZÃO SOCIAL\nCLIENTE X\nCNPJ / CPF\nDATA DA EMISSÃO\n"
             "INFORMAÇÕES DO LOCAL DE RETIRADA\nCNPJ / CPF\n02.768.118/0001-90\nUF\nMG\n"
             "CÁLCULO DO IMPOSTO\n")
    d = dt.destinatario_por_rotulos(texto)
    assert d["razao_social"] == "CLIENTE X"
    assert d["cnpj_cpf"] is None and d["uf"] is None
