# -*- coding: utf-8 -*-
r"""Camaçari/BA - NFS-e CPqD **reimpressa pelo ERP do prestador** (`camacari_cpqd`,
ampliação 2026-11-13).

Achado real: `Notas/2026.10.21 - NFS 6288 - AIR PRIME EQUIPAMENTOS DE SEGURANCA
LTDA - ME.pdf` (1 página, PDF digital). NFS-e nº 6288, RPS 39 série 1, emitida
em 21/10/2026 10:23:53, código W3RH01Z0L - AIR PRIME EQUIPAMENTOS DE SEGURANCA
LTDA - ME (09.198.683/0001-08, IM 0017892001) -> DELTALINE SERVICOS LTDA
(01.813.680/0001-25, Salvador/BA), locação de equipamentos R$ 12.717,98, ISS
"A RECOLHER PELO PRESTADOR" com alíquota 0,00, código de tributação municipal
"9901 - LOCAÇÃO DE BENS MÓVEIS", CNAE 7739-0/99.

Antes: a CLI abortava com "parece ser baseado em imagem/scan ou vazio" - o
impresso do ERP ("NFS-e impressa pelo ERP a partir dos dados gravados na
nota", rodapé blob:...toolgestao.com.br) tem a MESMA grade do CPqD, mas sem
"PREFEITURA MUNICIPAL DE CAMAÇARI" (brasão em imagem) nem "CPqD - Gestão
Pública", então nenhum layout casava e a página era descartada.

Textos REAIS do PDF: `MOCK_PDFMINER_CRU` é o que o `extract_text()` devolve;
`MOCK_RECONSTRUIDO` é o que `_reconstruir_texto_por_coordenadas()` devolve.
"""
import xml.etree.ElementTree as ET

import pytest

from src.extractors.pdf_extractor import (
    SPPdfExtractor, LAYOUT_CAMACARI, LAYOUT_CAMACARI_3, LAYOUT_GENERICO,
)
from src.transformers.abrasf_transformer import Abrasf201Transformer
from tests.test_camacari_cpqd_digital_ordem_leitura_ph_gestao import (
    MOCK_RECONSTRUIDO as MOCK_CPQD_PH_GESTAO,
)

MOCK_PDFMINER_CRU = '21/10/2026, 10:36\n\nNOTA FISCAL DE SERVIÇOS ELETRÔNICA - NFS-e 39\n\nNOTA FISCAL DE SERVIÇOS ELETRÔNICA - NFS-e\nRPS Nº 39 Série 1\nCompetência 21/10/2026\n\nNúmero da Nota\n\n6288\n\nData de Emissão\n\n21/10/2026 10:23:53\n\nCódigo de Verificação\n\nW3RH01Z0L\n\nNome/Razão Social: AIR PRIME EQUIPAMENTOS DE SEGURANCA LTDA - ME\n\nPRESTADOR DE SERVIÇOS\n\nCPF/CNPJ: 09.198.683/0001-08\n\nInscrição Municipal: 0017892001\n\nNome Fantasia: AIR PRIME\n\nRegime:\n\nNome/Razão Social: DELTALINE SERVICOS LTDA\n\nTOMADOR DE SERVIÇOS\n\nCPF/CNPJ: 01.813.680/0001-25\nLogradouro: RUA CAMBORIU\n\nE-mail:\n\nCEP: 40330533\nTelefone: 7132441400\n\nDESCRIÇÃO\n\nInscrição Municipal:\n\nBairro: IAPI\n\nMunicípio: Salvador\n\nNº:39\n\nUF: BA\n\nDISCRIMINAÇÃO DOS SERVIÇOS\n\nLOCAÇÃO DE EQUIPAMENTOS EPRS CONFORME BM 5035 E PROPOSTA COMERCIAL\n11899/2026 - CREDITAR ATÉ 10/11/2026 - BANCO DO BRASIL N° AGÊNCIA: 3884-9\nCONTA CORRENTE 38195-0 - PIX CNPJ 09.198.683/0001-08\n\nQTD\n\n1,0000\n\nVALOR UNIT (R$)\n\nVALOR TOTAL (R$)\n\n12.717,98\n\n12.717,98\n\nRetenções (R$)\n\nTotais (R$)\n\nPIS:\nCOFINS:\nINSS:\nIR:\nCSLL:\nOutras:\nTotal de Retenções:\n\nValor dos Serviços (R$)\nDeduções (-)\nBase de Cálculo (=)\nAlíquota (%)\nValor do ISS (R$)\nValor Líquido da Nota (=)\n\n0,00\n0,00\n0,00\n0,00\n0,00\n0,00\n0,00\n\nTipo de tributação: A RECOLHER PELO PRESTADOR\nMunicípio da prestação do serviço: 2905701 - Camaçari\nMunicípio de tributação: 2905701 - Camaçari\nCNAE - 7739-0/99 - ALUGUEL DE OUTRAS MÁQUINAS E EQUIPAMENTOS COMERCIAIS E INDUSTRIAIS\nNÃO ESPECIFICADOS ANTERIORMENTE, SEM OPERADOR\nServiço - 9901\nCódigo de tributação municipal: 9901 - LOCAÇÃO DE BENS MÓVEIS\n\n12.717,98\n0,00\n12.717,98\n0,00\n0,00\n12.717,98\n\nData da prestação do serviço: 21/10/2026\n\nNFS-e impressa pelo ERP a partir dos dados gravados na nota\n\nData Impressão: 21/10/2026 10:36\n\nblob:https://airprime-equipamento.toolgestao.com.br/02c973cd-f177-4fa1-946b-0c98f6e82bf2\n\n1/1\n\n\x0c'

MOCK_RECONSTRUIDO = '21/10/2026, 10:36 NOTA FISCAL DE SERVIÇOS ELETRÔNICA - NFS-e 39\nNúmero da Nota\n6288\nNOTA FISCAL DE SERVIÇOS ELETRÔNICA - NFS-e Data de Emissão\nRPS Nº 39 Série 1 21/10/2026 10:23:53\nCompetência 21/10/2026\nCódigo de Verificação\nW3RH01Z0L\nPRESTADOR DE SERVIÇOS\nNome/Razão Social: AIR PRIME EQUIPAMENTOS DE SEGURANCA LTDA - ME\nCPF/CNPJ: 09.198.683/0001-08 Inscrição Municipal: 0017892001\nNome Fantasia: AIR PRIME Regime:\nTOMADOR DE SERVIÇOS\nNome/Razão Social: DELTALINE SERVICOS LTDA\nCPF/CNPJ: 01.813.680/0001-25 Inscrição Municipal:\nLogradouro: RUA CAMBORIU Nº:39\nE-mail: Bairro: IAPI\nCEP: 40330533 Município: Salvador UF: BA\nTelefone: 7132441400\nDISCRIMINAÇÃO DOS SERVIÇOS\nDESCRIÇÃO QTD VALOR UNIT (R$) VALOR TOTAL (R$)\nLOCAÇÃO DE EQUIPAMENTOS EPRS CONFORME BM 5035 E PROPOSTA COMERCIAL 1,0000 12.717,98 12.717,98\n11899/2026 - CREDITAR ATÉ 10/11/2026 - BANCO DO BRASIL N° AGÊNCIA: 3884-9\nCONTA CORRENTE 38195-0 - PIX CNPJ 09.198.683/0001-08\nRetenções (R$) Totais (R$)\nPIS: 0,00 Valor dos Serviços (R$) 12.717,98\nCOFINS: 0,00 Deduções (-) 0,00\nINSS: 0,00 Base de Cálculo (=) 12.717,98\nIR: 0,00 Alíquota (%) 0,00\nCSLL: 0,00 Valor do ISS (R$) 0,00\nOutras: 0,00 Valor Líquido da Nota (=) 12.717,98\nTotal de Retenções: 0,00\nTipo de tributação: A RECOLHER PELO PRESTADOR Data da prestação do serviço: 21/10/2026\nMunicípio da prestação do serviço: 2905701 - Camaçari\nMunicípio de tributação: 2905701 - Camaçari\nCNAE - 7739-0/99 - ALUGUEL DE OUTRAS MÁQUINAS E EQUIPAMENTOS COMERCIAIS E INDUSTRIAIS\nNÃO ESPECIFICADOS ANTERIORMENTE, SEM OPERADOR\nServiço - 9901\nCódigo de tributação municipal: 9901 - LOCAÇÃO DE BENS MÓVEIS\nNFS-e impressa pelo ERP a partir dos dados gravados na nota Data Impressão: 21/10/2026 10:36\nblob:https://airprime-equipamento.toolgestao.com.br/02c973cd-f177-4fa1-946b-0c98f6e82bf2 1/1'


@pytest.fixture
def dummy_path(tmp_path):
    p = tmp_path / "dummy_camacari_erp_6288.pdf"
    p.write_bytes(b"%PDF-1.4")
    return str(p)


@pytest.fixture
def nfse(monkeypatch, dummy_path):
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_PDFMINER_CRU)
    monkeypatch.setattr(SPPdfExtractor, "_reconstruir_texto_por_coordenadas", lambda self: MOCK_RECONSTRUIDO)
    notas = SPPdfExtractor(dummy_path).parse_multiple()
    assert len(notas) == 1
    return notas[0]


@pytest.fixture
def xml(nfse):
    return ET.fromstring(Abrasf201Transformer().transform(nfse).encode("utf-8"))


def _txt(root, caminho):
    el = root.find(caminho)
    assert el is not None, caminho
    return el.text


# --- detecção -------------------------------------------------------------

def test_detectado_como_camacari_cpqd_digital(dummy_path):
    ex = SPPdfExtractor(dummy_path)
    ex._pagina_veio_de_ocr = False
    assert ex._detect_layout_page(MOCK_PDFMINER_CRU) == LAYOUT_CAMACARI
    assert ex._detect_layout_page(MOCK_RECONSTRUIDO) == LAYOUT_CAMACARI
    ex.raw_text = MOCK_PDFMINER_CRU
    assert ex._detect_layout() == LAYOUT_CAMACARI


def test_deteccao_exige_as_tres_ancoras(dummy_path):
    """Sem tributação em Camaçari (2905701), sem a marca do ERP ou sem o rótulo
    do código municipal, o impresso NÃO é puxado para o layout de Camaçari."""
    ex = SPPdfExtractor(dummy_path)
    ex._pagina_veio_de_ocr = False
    outro_municipio = MOCK_PDFMINER_CRU.replace("Município de tributação: 2905701", "Município de tributação: 2927408")
    sem_marca = MOCK_PDFMINER_CRU.replace("NFS-e impressa pelo ERP", "NFS-e impressa")
    sem_rotulo = MOCK_PDFMINER_CRU.replace("Código de tributação municipal:", "Código:")
    for texto in (outro_municipio, sem_marca, sem_rotulo):
        assert ex._detect_layout_page(texto) != LAYOUT_CAMACARI
        assert not ex._camacari_impressa_erp(texto)


def test_camacari_cpqd_existente_continua_no_layout_de_antes(dummy_path):
    """Guarda de regressão: a nota CPqD real (nº 52, PH Gestão) segue em
    `camacari_cpqd`/`camacari_ba_scan_v3` e NÃO é tratada como impressa pelo ERP."""
    ex = SPPdfExtractor(dummy_path)
    ex._pagina_veio_de_ocr = False
    assert ex._detect_layout_page(MOCK_CPQD_PH_GESTAO) == LAYOUT_CAMACARI
    ex._pagina_veio_de_ocr = True
    assert ex._detect_layout_page(MOCK_CPQD_PH_GESTAO) == LAYOUT_CAMACARI_3
    assert not ex._camacari_impressa_erp(MOCK_CPQD_PH_GESTAO)


# --- campos extraídos -----------------------------------------------------

def test_cabecalho(nfse):
    assert nfse.numero == "6288"
    assert nfse.codigo_verificacao == "W3RH01Z0L"
    assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "21/10/2026 10:23:53"
    assert nfse.competencia.strftime("%d/%m/%Y") == "21/10/2026"


def test_prestador_sem_endereco_inventado(nfse):
    p = nfse.prestador
    assert p.razao_social == "AIR PRIME EQUIPAMENTOS DE SEGURANCA LTDA - ME"
    assert p.cnpj_cpf == "09198683000108"
    assert p.inscricao_municipal == "0017892001"
    # A nota não imprime endereço do prestador: nada de logradouro/CEP fabricado.
    assert p.endereco.logradouro == "Não informado"
    assert p.endereco.cep.replace("-", "") == "00000000"


def test_tomador(nfse):
    t = nfse.tomador
    assert t.razao_social == "DELTALINE SERVICOS LTDA"
    assert t.cnpj_cpf == "01813680000125"
    assert t.endereco.logradouro == "RUA CAMBORIU"  # antes: "RUA CAMBORIU Nº:39"
    assert t.endereco.numero == "39"                # antes: "S/N"
    assert t.endereco.bairro == "IAPI"
    assert t.endereco.cep == "40330533"
    assert t.endereco.municipio == "Salvador"
    assert t.endereco.uf == "BA"
    assert t.endereco.codigo_municipio == "2927408"
    assert t.telefone == "7132441400"


def test_discriminacao_so_a_descricao(nfse):
    # Antes: a nota inteira (grade de retenções, CNAE, rodapé blob:...).
    assert nfse.discriminacao == (
        "LOCAÇÃO DE EQUIPAMENTOS EPRS CONFORME BM 5035 E PROPOSTA COMERCIAL "
        "11899/2026 - CREDITAR ATÉ 10/11/2026 - BANCO DO BRASIL N° AGÊNCIA: 3884-9 "
        "CONTA CORRENTE 38195-0 - PIX CNPJ 09.198.683/0001-08"
    )


def test_item_9901_segue_convencao_sisloc_com_aviso(nfse):
    assert nfse.servico_codigo == "0000"  # antes: "03115" (lixo)
    assert any("9901 - LOCAÇÃO DE BENS MÓVEIS" in a and "0000" in a for a in nfse.avisos)


def test_cnae(nfse):
    assert nfse.codigo_cnae == "7739099"


def test_valores(nfse):
    v = nfse.valores
    assert v.valor_servicos == 12717.98
    assert v.valor_deducoes == 0.0
    assert v.base_calculo == 12717.98
    assert v.aliquota == 0.0  # 0,00 impresso: sem piso
    assert v.valor_iss == 0.0
    assert v.valor_liquido_nfse == 12717.98
    assert v.iss_retido is False
    for campo in ("valor_pis", "valor_cofins", "valor_inss", "valor_ir", "valor_csll", "outras_retencoes"):
        assert getattr(v, campo) == 0.0, campo


# --- XML final --------------------------------------------------------------

def test_xml_final(xml):
    inf = "Nfse/InfNfse"
    dec = inf + "/DeclaracaoPrestacaoServico/InfDeclaracaoPrestacaoServico"
    srv = dec + "/Servico"
    assert _txt(xml, inf + "/Numero") == "6288"
    assert _txt(xml, inf + "/CodigoVerificacao") == "W3RH01Z0L"
    assert _txt(xml, inf + "/DataEmissao") == "2026-10-21T10:23:53"
    assert _txt(xml, dec + "/Competencia") == "2026-10-21"
    assert _txt(xml, srv + "/Valores/ValorServicos") == "12717.98"
    assert _txt(xml, srv + "/Valores/ValorDeducoes") == "0.00"
    assert _txt(xml, srv + "/Valores/BaseCalculo") == "12717.98"
    assert _txt(xml, srv + "/Valores/Aliquota") == "0.00"
    assert _txt(xml, srv + "/Valores/ValorIss") == "0.00"
    assert _txt(xml, srv + "/Valores/IssRetido") == "2"
    for tag in ("ValorPis", "ValorCofins", "ValorInss", "ValorIr", "ValorCsll", "OutrasRetencoes"):
        assert _txt(xml, srv + "/Valores/" + tag) == "0.00", tag
    assert _txt(xml, inf + "/ValoresNfse/ValorLiquidoNfse") == "12717.98"
    assert _txt(xml, srv + "/ItemListaServico") == "0000"
    assert _txt(xml, srv + "/CodigoTributacaoMunicipio") == "0000"
    assert _txt(xml, srv + "/CodigoCnae") == "7739099"
    assert _txt(xml, srv + "/CodigoMunicipio") == "2905701"
    assert _txt(xml, srv + "/MunicipioIncidencia") == "2905701"
    assert _txt(xml, srv + "/Discriminacao").startswith("LOCAÇÃO DE EQUIPAMENTOS EPRS")
    assert _txt(xml, dec + "/Prestador/CpfCnpj/Cnpj") == "09198683000108"
    assert _txt(xml, dec + "/Prestador/InscricaoMunicipal") == "0017892001"
    tom = dec + "/Tomador"
    assert _txt(xml, tom + "/IdentificacaoTomador/CpfCnpj/Cnpj") == "01813680000125"
    assert _txt(xml, tom + "/RazaoSocial") == "DELTALINE SERVICOS LTDA"
    assert _txt(xml, tom + "/Endereco/Endereco") == "RUA CAMBORIU"
    assert _txt(xml, tom + "/Endereco/Numero") == "39"
    assert _txt(xml, tom + "/Endereco/Bairro") == "IAPI"
    assert _txt(xml, tom + "/Endereco/CodigoMunicipio") == "2927408"
    assert _txt(xml, tom + "/Endereco/Uf") == "BA"
    assert _txt(xml, tom + "/Endereco/Cep") == "40330533"
    assert _txt(xml, tom + "/Contato/Telefone") == "7132441400"
