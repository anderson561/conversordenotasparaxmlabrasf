# -*- coding: utf-8 -*-
r"""DANFE (NF-e Modelo 55) DIGITAL nº 35284 - DAC MATERIAIS DE CONSTRUCAO
(CNPJ 26.259.069/0001-28, Extrema/MG) -> H.Z. PATRIMONIAL LTDA. (Lauro de
Freitas/BA), R$ 11.645,00, 10 itens (CST 060 e 000), desconto por item.

Antes (achado real 2026-10-29): emitente xNome "NF-e" (valor ERRADO - a
linha do canhoto "NF-e / Nº 000.035.284 / Série 001" virava a razão social),
endereço do emitente vazio, cMunFG de Salvador, aviso de UF do destinatário
e ZERO itens -> o Domínio rejeita o XML ("Tag 'det' não encontrada").

Causas (estrutura, nada condicionado ao emitente):
- regex da GRAN COFFEE só conhecia "N." no canhoto; com "Nº" o 1º bloco
  "NF-e" virava o nome;
- endereço do emitente em UMA frase quebrada em linhas ("<logr>, <nº> -" /
  "<bairro> - <MUN> - <UF> - CEP:" / "<cep>");
- UF do destinatário impressa ANTES do rótulo ("BA\n\nUF");
- tabela de itens despejada pelo pdfminer COLUNA A COLUNA (10 códigos, 10
  descrições, 10 NCM, 10 CST, 10 "CFOP UNID.", 10 QTDE., ... BC/V.ICMS
  intercalados, "V.IPI ALÍQ.ICMS ALÍQ.IPI" numa linha por item).

E no transformer: CST 60 saía dentro de ICMS40 (inválido); agora o grupo
vem do CST impresso (ICMS60), com prod/vDesc por item.

Texto REAL extraído por pdfminer (`extract_text`) do PDF digital, gerado
por script (nunca digitado à mão).
"""
import re
import xml.etree.ElementTree as ET

import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_DANFE_PRODUTO
from src.extractors import danfe_produto_texto as dt
from src.models.nfe_produto_models import NfeProduto, ItemProduto
from src.transformers.nfe_produto_transformer import NfeProdutoTransformer
from src.main import aviso_nfe_sem_itens

NS = {'n': 'http://www.portalfiscal.inf.br/nfe'}

MOCK_TEXT_35284 = 'Recebemos de DAC MATERIAIS DE CONSTRUCAO os produtos e/ou serviços constantes da Nota Fiscal Eletrônica indicada ao lado. \nEmissão: 02/07/2026  Dest/Reme: H.Z. PATRIMONIAL LTDA.  Valor Total: 11.645,00\n\nDATA DO RECEBIMENTO\n\nIDENTIFICAÇÃO E ASSINATURA DO RECEBEDOR\n\nNF-e\nNº 000.035.284\nSérie 001\n\nDAC MATERIAIS DE CONSTRUCAO\n\nAV NICOLAU CESARINO, 4175 -\nTENENTES - EXTREMA - MG - CEP:\n37645-002\n Fone: (35)3435-1836\n\nDANFE\nDocumento Auxiliar da\nNota Fiscal Eletrônica\n0 - ENTRADA\n1 - SAÍDA\nNº 000.035.284\nSérie 001\nFolha 1/1\n\n1\n\nCHAVE DE ACESSO\n\n3126 0726 2590 6900 0128 5500 1000 0352 8410 0635 2849\n\nConsulta de autenticidade no portal nacional da NF-e\nwww.nfe.fazenda.gov.br/portal ou no site da Sefaz autorizadora\n\nPROTOCOLO DE AUTORIZAÇÃO DE USO\n\n131267687731278 02/07/2026 13:56:27\n\nNATUREZA DA OPERAÇÃO\nVENDA MERC. ADQ. OU RECEB. DE TERC.\n\nINSCRIÇÃO ESTADUAL\n2516540640019\n\nINSCRIÇÃO ESTADUAL DO SUBSTITUTO TRIBUTÁRIO\n\nCNPJ / CPF\n26.259.069/0001-28\n\nDESTINATÁRIO / REMETENTE\nNOME / RAZÃO SOCIAL\nH.Z. PATRIMONIAL LTDA.\nENDEREÇO\nAV LUIZ TARQUINIO PONTES, 2580  SALA 311 EDF VILLAS EMPRESARIAL I\nMUNICÍPIO\nLAURO DE FREITAS\n\nBA\n\nUF\n\nBAIRRO / DISTRITO\nBURAQUINHO\nTELEFONE / FAX\n(71)3183-9000\n\nCNPJ / CPF\n10.791.569/0001-76\n\nCEP\n42700-130\n\nDATA DA EMISSÃO\n\n02/07/2026\n\nDATA DA SAÍDA\n\n02/07/2026\n\nINSCRIÇÃO ESTADUAL\n\nHORA DA SAÍDA\n\n13:42:32\n\nFATURA\n\nDADOS DA FATURA  \n\n  Número:   35284     -   Valor Original: R$ 11.645,05    -   Valor Desconto:  R$ 0,05    -   Valor Líquido: R$ 11.645,00\n\nPARCELAS\nNúmero\nVencimento\nValor\n\n:\n:\n:\n\n001\n03/08/2026\nR$ 11.645,00\n\nCÁLCULO DO IMPOSTO\n\nBASE DE CÁLCULO DO ICMS\n\nVALOR DO ICMS\n\nBASE DE CÁLCULO DO ICMS SUBST.\n\nVALOR DO ICMS SUBST.\n\nV.APROX. TRIBUTOS \n\nVALOR TOTAL DOS PRODUTOS\n\n10.354,98\n\n1.863,89\n\nVALOR DO FRETE\n\nVALOR DO SEGURO\n\nDESCONTO\n\n0,00\nOUTRAS DESPESAS ACESSÓRIAS\n\n0,00\n\n3.913,72 (33,61 %)\n\nVALOR DO IPI\n\nVALOR TOTAL DA NOTA\n\n0,00\n\n0,00\n\n0,05\n\n0,00\n\n0,00\n\n11.645,05\n\n11.645,00\n\nTRANSPORTADOR / VOLUMES TRANSPORTADOS\nNOME / RAZÃO SOCIAL\n\nENDEREÇO\n\nFRETE POR CONTA\n9 - SEM FRETE\nMUNICÍPIO\n\nCÓDIGO ANTT\n\nPLACA DO VEÍCULO\n\nUF\n\nCNPJ / CPF\n\nUF\n\nINSCRIÇÃO ESTADUAL\n\nQUANTIDADE\n\nESPÉCIE\n\nMARCA\n\nNUMERAÇÃO\n\nPESO BRUTO (KG)\n\nPESO LÍQUIDO (KG)\n\nDADOS DOS PRODUTOS / SERVIÇOS\n\nCÓDIGO\nPRODUTO\n\n117494\n\n119723\n\n124001\n\n124325\n\n16950\n\n1390\n\n16146\n\n1971\n\n1976\n\n1633\n\nDESCRIÇÃO DO PRODUTO / SERVIÇO\n\nNCM/SH\n\nCST\n\nCFOP UNID.\n\nQTDE.\n\nVALOR\nUNITÁRIO\n\nVALOR\nDESCONTO\n\nVALOR\nTOTAL\n\nBASE DE \nCÁLC. ICMS\n\nVALOR\nICMS\n\nVALOR\nIPI\n\nALÍQ. %\n\nICMS\n\nIPI\n\nARAME RECOZIDO CAIXA 14\n\nDISCO CORTE FERRO 4 1/2 TELSTAR\n\nDISCO MAD 4.5 24 DENTES - CORTAG\n\nDISCO MAD 9 1/4 36 DENTES CORTAG\n\nMADEIRIT 10 MM\n\nMADEIRIT 10 MM NAVAL\n\nPONTALETE PINUS 7X7 / 3 MT\n\nPREGO 17 X 21\n\nPREGO 18 X 27\n\nSARRAFO PINUS 10\n\n72171090\n\n68042211\n\n82023100\n\n82023100\n\n44129900\n\n44129900\n\n44013900\n\n73170090\n\n73170090\n\n73142000\n\n060\n\n060\n\n060\n\n060\n\n000\n\n000\n\n000\n\n060\n\n060\n\n000\n\n5405 KG\n\n5405 UN\n\n5405 UN\n\n5405 UN\n\n5102 UN\n\n5102 UN\n\n5102 UN\n\n5405 KG\n\n5405 KG\n\n5102 MT\n\n32,00\n\n10,00\n\n2,00\n\n1,00\n\n30,00\n\n70,00\n\n90,00\n\n10,00\n\n15,00\n\n180,00\n\n19,50\n\n7,50\n\n21,00\n\n89,00\n\n59,00\n\n86,00\n\n19,50\n\n18,00\n\n18,67\n\n4,50\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n0,02\n\n0,00\n\n0,00\n\n0,03\n\n0,00\n\n624,00\n\n75,00\n\n42,00\n\n89,00\n\n1.770,00\n\n6.020,00\n\n1.755,00\n\n180,00\n\n280,05\n\n810,00\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n1.770,00\n\n318,60\n\n6.019,98\n\n1.083,59\n\n1.755,00\n\n315,90\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n810,00\n\n145,80\n\n0,00 0,00 0,00\n\n0,00 0,00 0,00\n\n0,00 0,00 0,00\n\n0,00 0,00 0,00\n\n0,00 18,00 0,00\n\n0,00 18,00 0,00\n\n0,00 18,00 0,00\n\n0,00 0,00 0,00\n\n0,00 0,00 0,00\n\n0,00 18,00 0,00\n\nDADOS ADICIONAIS\n\nINFORMAÇÕES COMPLEMENTARES\nValor aproximado dos impostos, corresponde a totalidade dos tributos federais, estaduais e municipais, conforme disposto na lei numero 12.741/12:\nR$ 3.913,78 Fonte: Tabela IBPT. \n MERCADORIA ENTREGUE NO CANTEIRO DE OBRAS DO DESTINATARIO. NFE EMITIDA DE ACORDO COM O ART. 129 ANEXO VIII\nDO RICMS/MG 2023.\nOBRA: RUA JOAO BATISTA CARDOSO - EXTREMA-MG - BOLETO PARA 03/08/2026 - Venda para consumidor final, "NAO\nCONTRIBUINTE", porem com a mercadoria entregue em canteiro de obras em EXTREMA, dentro do estado de MG, ICMS para OUTRO ESTADO\n= R$ 1.863,89\nA PARTIR DO 1 DIA APOS O VENCIMENTO SEM O DEVIDO PAGAMENTO, V.S . JA ESTARA SUJEITA AOS ENCARGOS DEVIDOS EM\nVIRTUDE DA MORA"EX-RE", CONF ART 395 DA LEI 10406/2022: ATUAL. MONETARIA PELO INPC, JUROS DE 1% A.M. HONORARIOS\nDE ADVOGADO DE ATE 20% EM CASO DE NECESSIDADE DE INTERVENCAO DESTE (MESMO DE FORMA EXTRAJUDICIAL) E\nAINDA POR FORCA DO ART 52 1 DA LEI 8.078/90, MULTA DE 2%\n\nRESERVADO AO FISCO\n\nDATA E HORA DA IMPRESSÃO: 02/07/2026 13:55:15 \n\nPassarella Sistemas - Contato: (035) 3435-5824\n\n\x0c'


# (codigo, descricao, ncm, cst, cfop, un, qtd, unit, desc, total, bc, icms, aliq)
ITENS_IMPRESSOS = [
    ("117494", "ARAME RECOZIDO CAIXA 14", "72171090", "060", "5405", "KG", 32.0, 19.50, 0.00, 624.00, 0.0, 0.0, 0.0),
    ("119723", "DISCO CORTE FERRO 4 1/2 TELSTAR", "68042211", "060", "5405", "UN", 10.0, 7.50, 0.00, 75.00, 0.0, 0.0, 0.0),
    ("124001", "DISCO MAD 4.5 24 DENTES - CORTAG", "82023100", "060", "5405", "UN", 2.0, 21.00, 0.00, 42.00, 0.0, 0.0, 0.0),
    ("124325", "DISCO MAD 9 1/4 36 DENTES CORTAG", "82023100", "060", "5405", "UN", 1.0, 89.00, 0.00, 89.00, 0.0, 0.0, 0.0),
    ("16950", "MADEIRIT 10 MM", "44129900", "000", "5102", "UN", 30.0, 59.00, 0.00, 1770.00, 1770.00, 318.60, 18.0),
    ("1390", "MADEIRIT 10 MM NAVAL", "44129900", "000", "5102", "UN", 70.0, 86.00, 0.02, 6020.00, 6019.98, 1083.59, 18.0),
    ("16146", "PONTALETE PINUS 7X7 / 3 MT", "44013900", "000", "5102", "UN", 90.0, 19.50, 0.00, 1755.00, 1755.00, 315.90, 18.0),
    ("1971", "PREGO 17 X 21", "73170090", "060", "5405", "KG", 10.0, 18.00, 0.00, 180.00, 0.0, 0.0, 0.0),
    ("1976", "PREGO 18 X 27", "73170090", "060", "5405", "KG", 15.0, 18.67, 0.03, 280.05, 0.0, 0.0, 0.0),
    ("1633", "SARRAFO PINUS 10", "73142000", "000", "5102", "MT", 180.0, 4.50, 0.00, 810.00, 810.00, 145.80, 18.0),
]


def _parse(monkeypatch, tmp_path, texto=MOCK_TEXT_35284):
    dummy = tmp_path / "danfe.pdf"
    dummy.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: texto)
    res = SPPdfExtractor(str(dummy)).parse_multiple()
    assert len(res) == 1
    assert isinstance(res[0], NfeProduto)
    return res[0]


def _xml(nfe):
    return NfeProdutoTransformer().transform(nfe)


def _troca(texto, de, para):
    assert texto.count(de) == 1, de
    return texto.replace(de, para)


def test_detecta_danfe_produto():
    ex = SPPdfExtractor("inexistente.pdf")
    ex.raw_text = MOCK_TEXT_35284
    assert ex._detect_layout() == LAYOUT_DANFE_PRODUTO


def test_cabecalho(monkeypatch, tmp_path):
    nfe = _parse(monkeypatch, tmp_path)
    assert nfe.avisos == []
    assert nfe.chave_acesso == "31260726259069000128550010000352841006352849"
    assert nfe.numero == "35284"
    assert nfe.serie == "001"
    assert nfe.tipo_operacao == "1"
    assert nfe.natureza_operacao == "VENDA MERC. ADQ. OU RECEB. DE TERC."
    assert nfe.data_emissao.strftime("%d/%m/%Y") == "02/07/2026"
    assert nfe.data_saida_entrada.strftime("%d/%m/%Y") == "02/07/2026"
    assert nfe.protocolo_autorizacao == "131267687731278"
    assert nfe.protocolo_data_hora.strftime("%d/%m/%Y %H:%M:%S") == "02/07/2026 13:56:27"


def test_emitente_pelo_canhoto_e_letterhead_corrido(monkeypatch, tmp_path):
    e = _parse(monkeypatch, tmp_path).emitente
    # Antes: "NF-e" (linha do canhoto lida como razão social)
    assert e.razao_social == "DAC MATERIAIS DE CONSTRUCAO"
    assert e.cnpj_cpf == "26.259.069/0001-28"
    assert e.inscricao_estadual == "2516540640019"
    end = e.endereco
    assert (end.logradouro, end.numero, end.complemento, end.bairro) == ("AV NICOLAU CESARINO", "4175", None, "TENENTES")
    assert (end.municipio, end.uf, end.cep, end.codigo_municipio) == ("EXTREMA", "MG", "37645002", "3125101")
    assert e.telefone == "(35)3435-1836"


def test_destinatario(monkeypatch, tmp_path):
    d = _parse(monkeypatch, tmp_path).destinatario
    assert d.razao_social == "H.Z. PATRIMONIAL LTDA."
    assert d.cnpj_cpf == "10.791.569/0001-76"
    assert d.inscricao_estadual is None
    end = d.endereco
    # complemento NÃO vai junto ao logradouro
    assert (end.logradouro, end.numero, end.complemento) == (
        "AV LUIZ TARQUINIO PONTES", "2580", "SALA 311 EDF VILLAS EMPRESARIAL I")
    assert (end.bairro, end.cep, end.municipio, end.codigo_municipio) == (
        "BURAQUINHO", "42700130", "LAURO DE FREITAS", "2919207")
    # "BA\n\nUF": valor antes do rótulo, conferido pelo CEP
    assert end.uf == "BA"
    assert d.telefone == "(71)3183-9000"


def test_dez_itens_coluna_a_coluna(monkeypatch, tmp_path):
    itens = _parse(monkeypatch, tmp_path).itens
    assert len(itens) == 10
    for it, (cod, desc, ncm, cst, cfop, un, qtd, vun, vdesc, vtot, bc, vicms, aliq) in zip(itens, ITENS_IMPRESSOS):
        assert (it.codigo, it.descricao, it.ncm, it.cst_icms, it.cfop, it.unidade) == (cod, desc, ncm, cst, cfop, un)
        assert (it.quantidade, it.valor_unitario, it.valor_desconto, it.valor_total) == pytest.approx((qtd, vun, vdesc, vtot))
        assert (it.base_calculo_icms, it.valor_icms, it.aliquota_icms) == pytest.approx((bc, vicms, aliq))
        assert (it.valor_ipi, it.aliquota_ipi) == (0.0, 0.0)


def test_totais_fatura_transporte_infcpl(monkeypatch, tmp_path):
    nfe = _parse(monkeypatch, tmp_path)
    v = nfe.valores
    assert (v.base_calculo_icms, v.valor_icms, v.base_calculo_icms_st, v.valor_icms_st) == pytest.approx(
        (10354.98, 1863.89, 0.0, 0.0))
    assert (v.valor_total_produtos, v.valor_frete, v.valor_seguro, v.desconto, v.outras_despesas, v.valor_ipi,
            v.valor_total_nota) == pytest.approx((11645.05, 0.0, 0.0, 0.05, 0.0, 0.0, 11645.00))
    # Σ itens = grade
    assert round(sum(i.valor_total for i in nfe.itens), 2) == 11645.05
    assert round(sum(i.valor_desconto for i in nfe.itens), 2) == 0.05
    assert round(sum(i.base_calculo_icms for i in nfe.itens), 2) == 10354.98
    assert round(sum(i.valor_icms for i in nfe.itens), 2) == 1863.89
    assert nfe.fatura_duplicata == "001 Venc=03/08/2026 Valor=11.645,00"
    assert nfe.transportador.frete_por_conta == "9"
    assert nfe.informacoes_complementares.startswith("Valor aproximado dos impostos")
    assert "ART. 129 ANEXO VIII" in nfe.informacoes_complementares
    assert nfe.informacoes_complementares.endswith("MULTA DE 2%")
    assert aviso_nfe_sem_itens(nfe) is None


# --- XML -------------------------------------------------------------------

def test_xml_emitente_destinatario_ide(monkeypatch, tmp_path):
    root = ET.fromstring(_xml(_parse(monkeypatch, tmp_path)).encode("utf-8"))
    g = lambda p: root.find(p, NS).text
    assert g(".//n:ide/n:nNF") == "35284"
    assert g(".//n:ide/n:cMunFG") == "3125101"  # antes: 2927408 (Salvador)
    assert g(".//n:ide/n:idDest") == "1"  # CFOP 5xxx: operação interna (entrega em MG)
    assert g(".//n:emit/n:xNome") == "DAC MATERIAIS DE CONSTRUCAO"
    assert g(".//n:emit/n:IE") == "2516540640019"
    assert g(".//n:enderEmit/n:xLgr") == "AV NICOLAU CESARINO"
    assert g(".//n:enderEmit/n:xMun") == "EXTREMA"
    assert g(".//n:enderEmit/n:CEP") == "37645002"
    assert g(".//n:enderDest/n:UF") == "BA"
    assert g(".//n:enderDest/n:xCpl") == "SALA 311 EDF VILLAS EMPRESARIAL I"
    assert [c.tag.split('}')[1] for c in root.find(".//n:enderDest", NS)][:4] == ["xLgr", "nro", "xCpl", "xBairro"]


def test_xml_grupo_icms_pelo_cst_impresso(monkeypatch, tmp_path):
    root = ET.fromstring(_xml(_parse(monkeypatch, tmp_path)).encode("utf-8"))
    dets = root.findall(".//n:det", NS)
    assert len(dets) == 10
    for det, it in zip(dets, ITENS_IMPRESSOS):
        grupo = det.find("n:imposto/n:ICMS", NS)[0]
        filhos = [(c.tag.split('}')[1], c.text) for c in grupo]
        if it[3] == "060":
            # ICMS60 (antes: ICMS40 com CST 60, inválido); opcionais não impressos omitidos
            assert grupo.tag.endswith("ICMS60")
            assert filhos == [("orig", "0"), ("CST", "60")]
        else:
            assert grupo.tag.endswith("ICMS00")
            assert filhos == [("orig", "0"), ("CST", "00"), ("modBC", "3"), ("vBC", f"{it[10]:.2f}"),
                              ("pICMS", "18.00"), ("vICMS", f"{it[11]:.2f}")]


def test_xml_vdesc_por_item_e_totais(monkeypatch, tmp_path):
    nfe = _parse(monkeypatch, tmp_path)
    root = ET.fromstring(_xml(nfe).encode("utf-8"))
    assert nfe.avisos == []  # nenhuma incoerência de totais no transformer
    descs = []
    for det in root.findall(".//n:det", NS):
        prod = det.find("n:prod", NS)
        tags = [c.tag.split('}')[1] for c in prod]
        vd = prod.find("n:vDesc", NS)
        if vd is not None:
            # leiaute 4.00: ... vUnTrib, [vFrete, vSeg,] vDesc, [vOutro,] indTot
            assert tags.index("vDesc") == tags.index("vUnTrib") + 1 == tags.index("indTot") - 1
            descs.append((prod.find("n:cProd", NS).text, vd.text))
    assert descs == [("1390", "0.02"), ("1976", "0.03")]
    tot = {c.tag.split('}')[1]: c.text for c in root.find(".//n:ICMSTot", NS)}
    assert (tot["vBC"], tot["vICMS"], tot["vProd"], tot["vDesc"], tot["vNF"]) == (
        "10354.98", "1863.89", "11645.05", "0.05", "11645.00")


def test_transformer_avisa_vnf_incoerente(monkeypatch, tmp_path):
    nfe = _parse(monkeypatch, tmp_path)
    nfe.valores.valor_total_nota = 11645.05  # sem descontar o vDesc
    _xml(nfe)
    assert any("vNF (11645.05) diferente" in a for a in nfe.avisos)


@pytest.mark.parametrize("cst_impresso,grupo,cst", [("041", "ICMS40", "41"), ("040", "ICMS40", "40"),
                                                   ("050", "ICMS40", "50"), ("160", "ICMS60", "60"),
                                                   ("000", "ICMS00", "00")])
def test_transformer_mapeia_grupo_pelo_cst(monkeypatch, tmp_path, cst_impresso, grupo, cst):
    nfe = _parse(monkeypatch, tmp_path)
    nfe.itens = [nfe.itens[0].model_copy(update={"cst_icms": cst_impresso})]
    root = ET.fromstring(_xml(nfe).encode("utf-8"))
    g = root.find(".//n:det/n:imposto/n:ICMS", NS)[0]
    assert g.tag.endswith(grupo)
    assert g.find("n:orig", NS).text == cst_impresso[0]
    assert g.find("n:CST", NS).text == cst


@pytest.mark.parametrize("cst_impresso", ["010", "020", "090", "0102"])
def test_transformer_cst_sem_grupo_avisa_sem_grupo_errado(monkeypatch, tmp_path, cst_impresso):
    nfe = _parse(monkeypatch, tmp_path)
    nfe.itens = [nfe.itens[0].model_copy(update={"cst_icms": cst_impresso})]
    xml = _xml(nfe)
    assert "<ICMS40>" not in xml and "<ICMS00>" not in xml and "<ICMS60>" not in xml
    assert any("sem grupo implementado" in a for a in nfe.avisos)


# --- casos que NÃO fecham: nenhum item + aviso com motivo ------------------

def _sem_itens(nfe, trecho):
    assert nfe.itens == []
    assert "Nenhum item de produto identificado na tabela" in nfe.avisos
    assert any(trecho in a for a in nfe.avisos), nfe.avisos
    assert aviso_nfe_sem_itens(nfe) is not None


def test_qtd_x_unit_nao_fecha(monkeypatch, tmp_path):
    texto = _troca(MOCK_TEXT_35284, "\n18,67\n", "\n18,76\n")
    _sem_itens(_parse(monkeypatch, tmp_path, texto), "nenhuma montagem das colunas")


def test_bc_diferente_de_total_menos_desconto(monkeypatch, tmp_path):
    texto = _troca(MOCK_TEXT_35284, "\n6.019,98\n", "\n6.020,00\n")
    _sem_itens(_parse(monkeypatch, tmp_path, texto), "nenhuma montagem das colunas")


def test_bc_x_aliquota_nao_fecha(monkeypatch, tmp_path):
    texto = _troca(MOCK_TEXT_35284, "\n318,60\n", "\n318,90\n")
    _sem_itens(_parse(monkeypatch, tmp_path, texto), "nenhuma montagem das colunas")


def test_soma_dos_itens_nao_fecha_com_a_grade(monkeypatch, tmp_path):
    texto = _troca(MOCK_TEXT_35284, "\n10.354,98\n", "\n10.354,99\n")
    _sem_itens(_parse(monkeypatch, tmp_path, texto), "soma dos itens não fecha com a grade")


def test_descricao_quebrada_nao_e_chutada(monkeypatch, tmp_path):
    texto = _troca(MOCK_TEXT_35284, "\nMADEIRIT 10 MM NAVAL\n", "\nMADEIRIT 10 MM\nNAVAL\n")
    _sem_itens(_parse(monkeypatch, tmp_path, texto), "descrição quebrada")


def test_codigo_a_mais_nao_associa(monkeypatch, tmp_path):
    texto = _troca(MOCK_TEXT_35284, "\n1633\n", "\n1633\n\n9999\n")
    nfe = _parse(monkeypatch, tmp_path, texto)
    assert nfe.itens == []
    assert aviso_nfe_sem_itens(nfe) is not None


# --- funções puras -----------------------------------------------------------

def test_letterhead_corrido_recusa_cep_fora_da_uf():
    assert dt.emitente_letterhead_corrido(MOCK_TEXT_35284)["municipio"] == "EXTREMA"
    texto = _troca(MOCK_TEXT_35284, "\n37645-002\n", "\n42700-130\n")
    assert dt.emitente_letterhead_corrido(texto) is None


def test_letterhead_corrido_exige_canhoto():
    texto = _troca(MOCK_TEXT_35284, "Recebemos de DAC MATERIAIS DE CONSTRUCAO os produtos",
                   "Declaro ter recebido os produtos")
    assert dt.emitente_letterhead_corrido(texto) is None


def test_uf_antes_do_rotulo_conferida_pelo_cep():
    sec = dt.secao(MOCK_TEXT_35284, dt._SEC_DEST_INI, dt._SEC_DEST_FIM_ENTIDADE)
    assert dt.uf_antes_do_rotulo(sec, "42700130") == "BA"
    assert dt.uf_antes_do_rotulo(sec, "37645002") is None
    assert dt.uf_antes_do_rotulo(sec, None) is None


def test_bc_icms_intercalados_resolvidos_por_identidade():
    """BC ICMS e V.ICMS saem intercalados (1.770,00 / 318,60 / 6.019,98 /
    1.083,59 ...): a montagem coluna-sobre-coluna não fecha; só a
    intercalada fecha, e é a única aceita."""
    itens, motivos = dt.itens_por_coluna(MOCK_TEXT_35284)
    assert motivos == []
    assert [(i['bc_icms'], i['valor_icms']) for i in itens if i['bc_icms']] == [
        (1770.0, 318.6), (6019.98, 1083.59), (1755.0, 315.9), (810.0, 145.8)]
