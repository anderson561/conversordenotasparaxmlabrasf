# -*- coding: utf-8 -*-
r"""DANFE (NF-e Modelo 55) DIGITAL de dois geradores novos, lidos pela
ESTRUTURA (rótulos do DANFE, tipos e identidades aritméticas), sem nada
condicionado ao emitente:

- nº 946, MUNDIAL INDUSTRIA METALURGICA LTDA (CNPJ 34.683.026/0002-84,
  Birigui/SP) -> H. Z. PATRIMONIAL LTDA. (Lauro de Freitas/BA), RESERVATORIO
  METALICO, R$ 30.818,00, natOp "FR-VENDA NAO CONTRIBUINTE";
- nº 44986, COMERCIAL CASA DA LAVOURA LTDA (CNPJ 02.768.118/0001-90,
  Extrema/MG) -> H. Z. PATRIMONIAL LTDA, CANALETA DE CIMENTO, R$ 6.102,00.

Antes (achado real 2026-10-29): a 946 saía com emitente "Emitente Não
Identificado", endereço vazio, cMun/cMunFG de Salvador, totais 0,00 e SEM
<det> - e o Domínio REJEITA o XML ("Erro processando arquivo XML. Tag 'det'
não encontrada."); a 44986 saía com dhEmi = hora da conversão, vNF 0,00, sem
itens, sem CNPJ do destinatário e letterhead incompleto. Causas: nome do
emitente da 946 desenhado (não é texto - só o endereço sai no pdfminer, no
INÍCIO da página), letterhead da 44986 com rótulo "IDENTIFICAÇÃO DO
EMITENTE" e endereço "<logr>, <nº> - <bairro> -" / "<MUN> - <UF> - <CEP> -
<fone>", grade CÁLCULO DO IMPOSTO com os valores numa ordem própria e
misturados com a caixa do transportador, tabela de itens com uma célula por
linha e o código despejado entre os rótulos, valores do destinatário (44986)
despejados longe dos rótulos e intercalados com a grade do local de retirada.

Textos REAIS extraídos por pdfminer (`extract_text`) dos PDFs digitais,
gerados por script (nunca digitados à mão).
"""
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_DANFE_PRODUTO
from src.extractors import danfe_produto_texto as dt
from src.models.nfe_produto_models import NfeProduto
from src.transformers.nfe_produto_transformer import NfeProdutoTransformer
from src.main import aviso_nfe_sem_itens

MOCK_TEXT_946 = 'RUA RUA MANOEL SEGUNDO \nCELICE, 540\nRESIDENCIAL JARDIM DO TREVO\nBIRIGUI-SP\nCEP: 16205-003\nFone: 1836592673\n\nINSC. EST. SUBST. TRIBUTÁRIO\n\nNATUREZA DA OPERAÇÃO\nFR-VENDA NAO CONTRIBUINTE\nINSCRIÇÃO ESTADUAL\n214295960119\n\nDESTINATÁRIO REMETENTE\n\nNOME RAZÃO SOCIAL\nH. Z. PATRIMONIAL LTDA.\nENDEREÇO\nAVEN LUIZ TARQUINIO PONTES, 2580 - SALA 311 EDF VILLAS EMPRE\nMUNICÍPIO\nLAURO DE FREITAS\n\nBAIRRO/DISTRITO\nBURAQUINHO\n\nUF\nFONE / FAX\nBA 14982237695\n\nDANFE\nDocumento Auxiliar\nda Nota Fiscal \nEletrônica\n0-ENTRADA\n1-SAIDA\nNº: 000.000.946\nSÉRIE: 1\nPágina: 1/1\n\n1\n\nCONTROLE DO FISCO\n\nCHAVE DE ACESSO\n\n3526.0834.6830.2600.0284.5500.1000.0009.4610.8181.0404\n\nConsulta de autenticidade no portal nacional da NF-e\nwww.nfe.fazenda.gov.br/portal\nou no site da Sefaz Autorizada\n\nPROTOCOLO DE AUTORIZAÇÃO DE USO\n\n135263392150101 18/08/2026 10:40\n\nCNPJ\n34.683.026/0002-84\n\nCNPJ/CPF\n10.791.569/0001-76\n\nCEP\n42700-130\n\nINSCRIÇÃO ESTADUAL\n\nDATA EMISSÃO\n18/08/2026\nDATA DA SAIDA\n18/08/2026\nHORA DE SAÍDA\n\n10:40\n\nFATURA\n\nN.:001 Vl.:R$ 9.328,20 Venc.:06/03/2026; N.:002 Vl.:R$ 9.328,20 Venc.:06/04/2026; N.:003 Vl.:R$ 12.161,60 Venc.:18/08/2026\n\nCALCULO DO IMPOSTO\n\nBASE DE CÁLCULO DO ICMS\n\nVALOR DO ICMS\n\nBASE DE CÁLC. DO ICMS SUBSTITUIÇÃO\n\nVALOR DO ICMS SUBSTITUIÇÃO\n\nVALOR TOTAL DOS PRODUTOS\n\n30.818,00\n\n3.698,16\n\nVALOR DO FRETE\n\nVALOR DO SEGURO\n\nDESCONTO\n\nOUTRAS DESPESAS ACESSÓRIAS\n\n0,00\n\n0,00\n\n0,00\n\nTRANSPORTADOR/VOLUMES TRANSPORTADOS\nRAZÃO SOCIAL\nMUNDIAL INDUSTRIA METALURGICA LTDA\n\nFRETE POR CONTA\n0-Remetente (CIF)\n\n0,00\n\n0,00\n\nVALOR IPI\n\nCÓDIGO ANTT\n\n0,00\n\n0,00\n\nUF\n\nVALOR TOTAL DA NOTA\n\n30.818,00\n\n30.818,00\n\nCNPJ/CPF\n34.683.026/0002-84\n\nENDEREÇO\nRUA  RUA MANOEL SEGUNDO CELICE, 540  RESIDENCIAL JARDIM DO T\nQUANTIDADE\n\nMUNICÍPIO\nBIRIGUI\nNUMERAÇÃO\n\nESPÉCIE\n\nMARCA\n\n1\n\nDADOS DO PRODUTO/SERVIÇOS\n\nUF\nSP\n\nINSCRIÇÃO ESTADUAL\n214295960119\nPESO LIQUIDO\n\nPESO BRUTO\n\n1.335,000\n\n1.335,000\n\nCÓDIGO\nPRODUTO\n\nTBL4001\n\nDESCRIÇÃO DO PRODUTO / SERVIÇOS\n\nNCM/SH\n\nCST\n\nCFOP\n\nUND\n\nQNT\n\nVALOR\nUNITÁRIO\n\nVALOR\nTOTAL\n\nB. CÁLCULO\nICMS\n\nVALOR\nICMS\n\nVALOR\nIPI\n\nALÍQ.\nICMS\n\nALÍQ.\nIPI\n\nRESERVATORIO METALICO TBL 40.000 \nLTS MOD. 4001 - DIAMETRO 2,54M X \nALTURA 8,00M\n\n73090090\n\n000\n\n6107\n\nUN\n\n1,0000\n\n30.818,0000\n\n30.818,00\n\n30.818,00\n\n3.698,16\n\n0,00 12,0000\n\n0,00\n\nCÁLCULO DO ISSQN\n\nINSCRIÇÃO MUNICIPAL\n\nDADOS ADICIONAIS\n\nINFORMAÇÕES COMPLEMENTARES\n\nVALOR TOTAL DOS SERVIÇOS\n\nBASE DE CÁLCULO DO ISSQN\n\nVALOR DO ISSQN\n\nICMS INTEREST. CONS.FINAL: DEST: 3.713,01 ; REMET.: 0,00 ; FCP: 0,00 . Nota Fiscal referente \nao pedido de vendas: FF-007883 - Vendedor: REGINALDO - Pedido de Compras:\nEndereço de entrega:RUA JOAO BATISTA CARDOSO, s/n - PROXIMO A  EMPRESA PONTUDOS \n- TENETES II - EXTREMA - MG - CNPJ (ENTREGA): 10791569000176\n\nRECEBEMOS DE MUNDIAL INDUSTRIA METALURGICA LTDA OS PRODUTOS CONSTANTES DA NOTAS FISCAL INDICADA AO LADO\n\nNF-e\n\nDATA DE RECEBIMENTO\n\nIDENTIFICAÇÃO E ASSINATURA DO RECEBEDOR\n\nN:\n\n946\nSÉRIE:\n\n1\n\n\x0c'

MOCK_TEXT_44986 = 'RECEBEMOS DE COMERCIAL CASA DA LAVOURA LTDA OS PRODUTOS / SERVIÇOS CONSTANTES DA NOTA FISCAL INDICADO AO LADO\n\nEMISSÃO: 29/06/2026  -  DEST. / REM.: H. Z. PATRIMONIAL LTDA  -  VALOR TOTAL: R$ 6.102,00\n\nDATA DE RECEBIMENTO\n\nIDENTIFICAÇÃO E ASSINATURA DO RECEBEDOR\n\nNF-e\nNº 000.044.986\nSÉRIE 001\n\nIDENTIFICAÇAO DO EMITENTE\n\nCOMERCIAL CASA DA LAVOURA LTDA\n\nESTRADA HORACIO MARINHO, 3  - JARDIM - \nEXTREMA - MG - 37640-000 - (35)3435-1586\nvendas@casadalavouraextrema.com.br\n\nDANFE\n\nDOCUMENTO AUXILIAR DA\nNOTA FISCAL ELETRÔNICA\n\n0 - ENTRADA\n1 - SAÍDA\nNº 000.044.986\n\n1\n\nfl. 1 /1\n\nSÉRIE 001\n\nNATUREZA DE OPERAÇÃO\n\nVENDAS DE MERCADORIAS ADQUIRIDAS OU RECEBIDAS DE TERCEIROS\nINSCRIÇÃO ESTADUAL\nINSCRIÇÃO ESTADUAL DO SUBST. TRIB.\n\nCHAVE DE ACESSO\n\n3126 0602 7681 1800 0190 5500 1000 0449 8612 5049 2030\n\nConsulta de autenticidade no portal nacional da NF-e\nwww.nfe.fazenda.gov.br/portal\nou no site da Sefaz Autorizadora\n\nPROTOCOLO DE AUTORIZAÇÃO DE USO\n\n131267676018031 29/06/2026 10:38:19\n\nCNPJ / CPF\n\n02.768.118/0001-90\n\n2519935230061\n\nDESTINATÁRIO / REMETENTE\n\nNOME / RAZÃO SOCIAL\n\nH. Z. PATRIMONIAL LTDA\nENDEREÇO\n\nAV. LUIZ TARQUINIO PONTES, 2580\nMUNICÍPIO\n\nLAURO DE FREITAS\n\nINFORMAÇÕES DO LOCAL DE RETIRADA\n\nNOME / RAZÃO SOCIAL\nCOMERCIAL CASA DA LAVOURA LTDA\n\nENDEREÇO\nESTRADA HORACIO MARINHO, 3\n\nMUNICÍPIO\nEXTREMA\n\nFATURA\n\nDADOS DA FATURA\n\nDUPLICATAS\n\nFONE / FAX\n\nBAIRRO / DISTRITO\n\nBURAQUINHO\nUF\n\n(71)99988-8081\n\nBA\n\nCNPJ / CPF\n\nDATA DA EMISSÃO\n\n10.791.569/0001-76\nCEP\n\n29/06/2026\nDATA SAÍDA / ENTRADA\n\n42700-130\n\nINSCRIÇÃO ESTADUAL\n\n29/06/2026\nHORA DA SAÍDA\n\n10:38:44\n\nCNPJ / CPF\n\n02.768.118/0001-90\n\nINSCRIÇÃO ESTADUAL\n2519935230061\n\nBAIRRO / DISTRITO\nJARDIM\n\nCEP\n37640-000\n\nTELEFONE / FAX\n\nUF\nMG\n\nNÚMERO\n\n000044986\n\nVALOR ORIGINAL\n\nVALOR DESCONTO\n\nVALOR LÍQUIDO\n\n6.102,00\n\n0,00\n\n6.102,00\n\nNº DUPLICATA\n\nVENC.\n\nVALOR\n\nNº DUPLICATA\n\nVENC.\n\nVALOR\n\nNº DUPLICATA\n\nVENC.\n\nVALOR\n\nNº DUPLICATA\n\nVENC.\n\nVALOR\n\n001\n\n30/07/2026\n\n6.102,00\n\nCÁLCULO DO IMPOSTO\nBASE DE CÁLCULO DO ICMS\n\nVALOR DO ICMS\n\nBASE CÁLC. ICMS SUBST.\n\nVALOR DO ICMS SUBST.\n\nVALOR APROX. DOS TRIBUTOS\n\nVALOR TOTAL DOS PRODUTOS\n\n6.102,00\n\n1.098,36\n\nVALOR DO FRETE\n\nVALOR DO SEGURO\n\nDESCONTO\n\n0,00\n\n0,00\n\nTRANSPORTADOR / VOLUMES TRANSPORTADOS\nRAZÃO SOCIAL\n\nENDEREÇO\n\n0,00\n\n0,00\n\nOUTRAS DESP. ACESS.\n\nVALOR DO IPI\n\nVALOR TOTAL DA NOTA\n\n0,00\n\n820,72\n\n0,00\n\n0,00\n\n6.102,00\n\n6.102,00\n\nFRETE POR CONTA\n\nCÓDIGO ANTT\n\nPLACA DO VEÍCULO\n\nUF\n\nCNPJ / CPF\n\n9 - SEM FRETE\n\nMUNICÍPIO\n\nUF\n\nINSCRIÇÃO ESTADUAL\n\nQUANTIDADE\n\nESPÉCIE\n\nMARCA\n\nNUMERAÇÃO\n\nPESO BRUTO (Kg)\n\nPESO LÍQUIDO (Kg)\n\n180\n\nVOLUMES\n\nDADOS DO PRODUTO / SERVIÇOS\n\nCÓDIGO DO \nPROD. / SERV.\n\n0000000004439\n\nDESCRIÇÃO DO PRODUTO / SERVIÇO\n\nNCM / SH\n\nCST\n\nCFOP UNID.\n\nQUANT.\n\nVALOR\nUNITÁRIO\n\nVALOR\nTOTAL\n\nDESCONTO\n\nBASE\nCÁLC. ICMS\n\nVALOR\nI.C.M.S.\n\nVALOR\nI.P.I.\n\nALÍQUOTAS\nIPI\nICMS\n\nCANALETA DE CIMENTO 030X100 (PONTA \nE BOLSA)\n\n68109100\n\n000\n\n5102 PC\n\n180,0000\n\n33,90\n\n6.102,00\n\n0,00\n\n6.102,00\n\n1.098,36\n\n0,00 18,00 0,00\n\nDADOS ADICIONAIS\n\nINFORMAÇÕES COMPLEMENTARES\n\nVENCIMENTO 30/07/2026\n\nRESERVADO AO FISCO\n\nIntellicash 3.0\n\n\x0c'


def _parse(monkeypatch, tmp_path, texto):
    dummy = tmp_path / "danfe.pdf"
    dummy.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: texto)
    res = SPPdfExtractor(str(dummy)).parse_multiple()
    assert len(res) == 1
    assert isinstance(res[0], NfeProduto)
    return res[0]


def _xml(nfe):
    return NfeProdutoTransformer().transform(nfe)


@pytest.mark.parametrize("texto", [MOCK_TEXT_946, MOCK_TEXT_44986])
def test_detecta_danfe_produto(texto):
    ex = SPPdfExtractor("inexistente.pdf")
    ex.raw_text = texto
    assert ex._detect_layout() == LAYOUT_DANFE_PRODUTO


# --- nota nº 946 ---------------------------------------------------------

def test_946_cabecalho(monkeypatch, tmp_path):
    nfe = _parse(monkeypatch, tmp_path, MOCK_TEXT_946)
    assert nfe.avisos == []
    assert nfe.chave_acesso == "35260834683026000284550010000009461081810404"
    assert nfe.numero == "946"
    assert nfe.serie == "1"
    assert nfe.tipo_operacao == "1"
    assert nfe.natureza_operacao == "FR-VENDA NAO CONTRIBUINTE"
    assert nfe.data_emissao.strftime("%d/%m/%Y") == "18/08/2026"
    assert nfe.data_saida_entrada.strftime("%d/%m/%Y") == "18/08/2026"
    assert nfe.protocolo_autorizacao == "135263392150101"
    # "18/08/2026 10:40" - hora sem segundos
    assert nfe.protocolo_data_hora.strftime("%d/%m/%Y %H:%M:%S") == "18/08/2026 10:40:00"


def test_946_emitente_nome_pelo_canhoto(monkeypatch, tmp_path):
    e = _parse(monkeypatch, tmp_path, MOCK_TEXT_946).emitente
    assert e.razao_social == "MUNDIAL INDUSTRIA METALURGICA LTDA"
    assert e.cnpj_cpf == "34.683.026/0002-84"
    assert e.inscricao_estadual == "214295960119"
    # logradouro quebrado em 2 linhas no letterhead ("RUA RUA MANOEL SEGUNDO"
    # / "CELICE, 540") - impresso assim, com "RUA" repetido
    assert e.endereco.logradouro == "RUA RUA MANOEL SEGUNDO CELICE"
    assert e.endereco.numero == "540"
    assert e.endereco.complemento is None
    assert e.endereco.bairro == "RESIDENCIAL JARDIM DO TREVO"
    assert e.endereco.municipio == "BIRIGUI"
    assert e.endereco.uf == "SP"
    assert e.endereco.codigo_municipio == "3506508"
    assert e.endereco.cep == "16205003"
    assert e.telefone == "1836592673"


def test_946_destinatario(monkeypatch, tmp_path):
    d = _parse(monkeypatch, tmp_path, MOCK_TEXT_946).destinatario
    assert d.razao_social == "H. Z. PATRIMONIAL LTDA."
    assert d.cnpj_cpf == "10.791.569/0001-76"
    # complemento NÃO fica junto do logradouro (decisão do usuário)
    assert d.endereco.logradouro == "AVEN LUIZ TARQUINIO PONTES"
    assert d.endereco.numero == "2580"
    assert d.endereco.complemento == "SALA 311 EDF VILLAS EMPRE"
    assert d.endereco.bairro == "BURAQUINHO"
    assert d.endereco.cep == "42700130"
    assert d.endereco.municipio == "LAURO DE FREITAS"
    assert d.endereco.codigo_municipio == "2919207"
    # "UF\nFONE / FAX\nBA 14982237695" - UF e fone numa linha só
    assert d.endereco.uf == "BA"
    assert d.telefone == "14982237695"


def test_946_item_totais_transporte_fatura_infcpl(monkeypatch, tmp_path):
    nfe = _parse(monkeypatch, tmp_path, MOCK_TEXT_946)
    assert len(nfe.itens) == 1
    it = nfe.itens[0]
    assert it.codigo == "TBL4001"
    assert it.descricao == "RESERVATORIO METALICO TBL 40.000 LTS MOD. 4001 - DIAMETRO 2,54M X ALTURA 8,00M"
    assert (it.ncm, it.cst_icms, it.cfop, it.unidade) == ("73090090", "000", "6107", "UN")
    assert (it.quantidade, it.valor_unitario, it.valor_total) == (1.0, 30818.0, 30818.0)
    assert (it.base_calculo_icms, it.aliquota_icms, it.valor_icms) == (30818.0, 12.0, 3698.16)
    assert (it.valor_ipi, it.aliquota_ipi) == (0.0, 0.0)
    v = nfe.valores
    assert (v.base_calculo_icms, v.valor_icms, v.valor_total_produtos, v.valor_total_nota) == (30818.0, 3698.16, 30818.0, 30818.0)
    assert (v.base_calculo_icms_st, v.valor_icms_st, v.valor_frete, v.valor_seguro, v.desconto,
            v.outras_despesas, v.valor_ipi) == (0.0,) * 7
    tr = nfe.transportador
    # impresso: o próprio remetente transporta, "0-Remetente (CIF)"
    assert tr.razao_social == "MUNDIAL INDUSTRIA METALURGICA LTDA"
    assert tr.cnpj_cpf == "34.683.026/0002-84"
    assert tr.frete_por_conta == "0"
    assert (tr.peso_bruto, tr.peso_liquido) == (1335.0, 1335.0)
    assert nfe.fatura_duplicata == "001 Venc=06/03/2026 Valor=9.328,20; 002 Venc=06/04/2026 Valor=9.328,20; 003 Venc=18/08/2026 Valor=12.161,60"
    assert nfe.informacoes_complementares.startswith("ICMS INTEREST. CONS.FINAL: DEST: 3.713,01")
    assert nfe.informacoes_complementares.endswith("CNPJ (ENTREGA): 10791569000176")
    assert "VALOR DO ISSQN" not in nfe.informacoes_complementares


def test_946_xml_tem_det_e_municipio_do_emitente(monkeypatch, tmp_path):
    xml = _xml(_parse(monkeypatch, tmp_path, MOCK_TEXT_946))
    assert xml.count('<det nItem=') == 1
    assert "<cMunFG>3506508</cMunFG>" in xml
    assert "<cMun>3506508</cMun>" in xml and "2927408" not in xml
    assert "<xNome>MUNDIAL INDUSTRIA METALURGICA LTDA</xNome>" in xml
    assert "<vNF>30818.00</vNF>" in xml and "<vProd>30818.00</vProd>" in xml
    assert "<pICMS>12.00</pICMS>" in xml and "<vICMS>3698.16</vICMS>" in xml
    assert "<modFrete>0</modFrete>" in xml
    assert "<idDest>2</idDest>" in xml
    assert "<dhEmi>2026-08-18T00:00:00-03:00</dhEmi>" in xml


# --- nota nº 44986 -------------------------------------------------------

def test_44986_cabecalho(monkeypatch, tmp_path):
    nfe = _parse(monkeypatch, tmp_path, MOCK_TEXT_44986)
    assert nfe.avisos == []
    assert nfe.chave_acesso == "31260602768118000190550010000449861250492030"
    assert nfe.numero == "44986"
    assert nfe.serie == "001"  # impresso "SÉRIE 001"; no XML vai "1"
    assert nfe.tipo_operacao == "1"
    # "NATUREZA DE OPERAÇÃO" (não "DA")
    assert nfe.natureza_operacao == "VENDAS DE MERCADORIAS ADQUIRIDAS OU RECEBIDAS DE TERCEIROS"
    # data impressa (despejada longe do rótulo), não a hora da conversão
    assert nfe.data_emissao.strftime("%d/%m/%Y %H:%M") == "29/06/2026 00:00"
    assert nfe.data_saida_entrada.strftime("%d/%m/%Y") == "29/06/2026"
    assert nfe.protocolo_autorizacao == "131267676018031"
    assert nfe.protocolo_data_hora.strftime("%d/%m/%Y %H:%M:%S") == "29/06/2026 10:38:19"


def test_44986_emitente_letterhead_identificacao(monkeypatch, tmp_path):
    e = _parse(monkeypatch, tmp_path, MOCK_TEXT_44986).emitente
    assert e.razao_social == "COMERCIAL CASA DA LAVOURA LTDA"
    assert e.cnpj_cpf == "02.768.118/0001-90"
    assert e.inscricao_estadual == "2519935230061"
    assert e.endereco.logradouro == "ESTRADA HORACIO MARINHO"
    assert e.endereco.numero == "3"
    assert e.endereco.complemento is None
    assert e.endereco.bairro == "JARDIM"
    assert e.endereco.municipio == "EXTREMA"
    assert e.endereco.uf == "MG"
    assert e.endereco.codigo_municipio == "3125101"
    assert e.endereco.cep == "37640000"
    assert e.telefone == "(35)3435-1586"


def test_44986_destinatario_valores_fora_de_ordem(monkeypatch, tmp_path):
    d = _parse(monkeypatch, tmp_path, MOCK_TEXT_44986).destinatario
    assert d.razao_social == "H. Z. PATRIMONIAL LTDA"
    # CNPJ do local de retirada (= emitente) não pode virar o do destinatário
    assert d.cnpj_cpf == "10.791.569/0001-76"
    assert d.endereco.logradouro == "AV. LUIZ TARQUINIO PONTES"
    assert d.endereco.numero == "2580"
    assert d.endereco.bairro == "BURAQUINHO"
    assert d.endereco.cep == "42700130"
    assert d.endereco.uf == "BA"
    assert d.endereco.municipio == "LAURO DE FREITAS"
    assert d.endereco.codigo_municipio == "2919207"
    assert d.telefone == "(71)99988-8081"


def test_44986_item_totais_transporte_fatura_infcpl(monkeypatch, tmp_path):
    nfe = _parse(monkeypatch, tmp_path, MOCK_TEXT_44986)
    assert len(nfe.itens) == 1
    it = nfe.itens[0]
    assert it.codigo == "0000000004439"
    assert it.descricao == "CANALETA DE CIMENTO 030X100 (PONTA E BOLSA)"
    assert (it.ncm, it.cst_icms, it.cfop, it.unidade) == ("68109100", "000", "5102", "PC")
    assert (it.quantidade, it.valor_unitario, it.valor_total) == (180.0, 33.9, 6102.0)
    # cabeçalho "ALÍQUOTAS / IPI / ICMS": a de ICMS é a que fecha BC x ALÍQ.
    assert (it.base_calculo_icms, it.aliquota_icms, it.valor_icms) == (6102.0, 18.0, 1098.36)
    v = nfe.valores
    assert (v.base_calculo_icms, v.valor_icms, v.valor_total_produtos, v.valor_total_nota) == (6102.0, 1098.36, 6102.0, 6102.0)
    assert (v.valor_frete, v.desconto, v.valor_ipi, v.valor_icms_st) == (0.0, 0.0, 0.0, 0.0)
    assert nfe.transportador.frete_por_conta == "9"
    assert nfe.transportador.razao_social is None and nfe.transportador.cnpj_cpf is None
    assert nfe.fatura_duplicata == "001 Venc=30/07/2026 Valor=6.102,00"
    assert nfe.informacoes_complementares == "VENCIMENTO 30/07/2026"


def test_44986_xml(monkeypatch, tmp_path):
    xml = _xml(_parse(monkeypatch, tmp_path, MOCK_TEXT_44986))
    assert xml.count('<det nItem=') == 1
    assert "<cMunFG>3125101</cMunFG>" in xml
    assert "<serie>1</serie>" in xml
    assert "<CNPJ>10791569000176</CNPJ>" in xml
    assert "<vNF>6102.00</vNF>" in xml and "<pICMS>18.00</pICMS>" in xml
    assert "<modFrete>9</modFrete>" in xml and "<transporta>" not in xml
    assert "<dhEmi>2026-06-29T00:00:00-03:00</dhEmi>" in xml
    assert aviso_nfe_sem_itens(_parse(monkeypatch, tmp_path, MOCK_TEXT_44986)) is None


# --- integridade: o que não fecha não vira dado --------------------------

def test_item_que_nao_fecha_qtd_x_unit_nao_vira_det_e_avisa_rejeicao(monkeypatch, tmp_path):
    # VR. UNIT adulterado: 180 x 33,80 != 6.102,00
    texto = MOCK_TEXT_44986.replace("\n33,90\n", "\n33,80\n")
    nfe = _parse(monkeypatch, tmp_path, texto)
    assert nfe.itens == []
    assert any("QUANT x VR.UNIT" in a for a in nfe.avisos)
    assert "Nenhum item de produto identificado na tabela" in nfe.avisos
    # sem itens a grade não é atribuída (as identidades dependem deles)
    assert nfe.valores.valor_total_nota == 0.0
    msg = aviso_nfe_sem_itens(nfe)
    assert msg.startswith("[ERRO]") and "<det>" in msg and "REJEITADO" in msg and "Domínio" in msg
    assert "<det nItem" not in _xml(nfe)


def test_grade_ambigua_por_ordem_nao_e_atribuida():
    itens, _ = dt.itens_colunas(MOCK_TEXT_946)
    assert dt.grade_por_identidade(MOCK_TEXT_946, itens)["valor_total_nota"] == 30818.0
    # um valor não nulo a mais na grade (frete? desconto? seguro?) não tem
    # posição confiável no texto -> nada atribuído
    texto = MOCK_TEXT_946.replace("OUTRAS DESPESAS ACESSÓRIAS\n\n0,00", "OUTRAS DESPESAS ACESSÓRIAS\n\n10,00")
    assert dt.grade_por_identidade(texto, itens) is None


def test_cnpj_destinatario_por_exclusao_ambiguo_devolve_none():
    assert dt.cnpj_destinatario_por_exclusao(MOCK_TEXT_44986, "02768118000190") == "10.791.569/0001-76"
    # um 2º CNPJ válido em linha própria na zona do destinatário -> ambíguo
    texto = MOCK_TEXT_44986.replace("BURAQUINHO\nUF", "BURAQUINHO\n34.683.026/0002-84\nUF")
    assert dt.cnpj_destinatario_por_exclusao(texto, "02768118000190") is None


def test_cep_confere_uf():
    assert dt.cep_confere_uf("16205003", "SP") is True
    assert dt.cep_confere_uf("37640000", "MG") is True
    assert dt.cep_confere_uf("42700130", "BA") is True
    assert dt.cep_confere_uf("42700130", "MG") is False
    assert dt.cep_confere_uf(None, "BA") is None


def test_letterhead_sem_nome_e_sem_canhoto_nao_chuta():
    # sem a frase do canhoto não há fonte para o nome -> None (sentinela)
    texto = MOCK_TEXT_946.replace("RECEBEMOS DE MUNDIAL INDUSTRIA METALURGICA LTDA OS PRODUTOS", "XX")
    assert dt.emitente_letterhead_livre(texto) is None
