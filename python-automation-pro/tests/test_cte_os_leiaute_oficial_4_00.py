# -*- coding: utf-8 -*-
r"""CT-e OS (Modelo 67) no LEIAUTE OFICIAL 4.00 - as 3 notas reais do lote
STAUMMAQ (2026-10-16) que NÃO importavam no Domínio ("Sem dados para
importar. Nenhuma linha foi processada"):

* nº 000.017.268 - SIGMA TRANSPORTES LTDA, pág. 4 de "STAUMMAQ - NFSe
  TERCEIROS.pdf" (gerador CT-e Prático/Bsoft);
* nº 000.004.035 - COOPERATIVA DE RADIO TAXI DE SIMOES FILHO, pág. 1 de
  "STAUMMAQ - NFSe TERCEIROS 2.pdf" (CT-e Prático/Bsoft);
* nº 000000564 - CIATRANS POOL TRANSPORTES DE PASSAGEIROS LTDA, pág. 2 de
  "STAUMMAQ - NFSe TERCEIROS 2.pdf" (Master CT-e).

Causa: o `CteTransformer` emitia um XML "inspirado" no Modelo 57 (`cteProc`/
`CTe`, `tpServico` textual, grupo inventado `<retencoes>`, ICMS sempre
`ICMS00`, `nProt` no `ide`, municípios vazios) e o extrator perdia emitente,
valores, rota e tipo do serviço nestas notas. Agora: `cteOSProc`/`CTeOS` na
ordem e nos tipos do XSD oficial (pacote PL_CTe_400, Portal Nacional do CT-e
https://www.cte.fazenda.gov.br/portal/ - "Esquemas XML") e extração
corrigida na causa (recortes dedicados das caixas do cabeçalho, âncoras
estruturais da grade, rota pelos dois formatos de impressão).

Todos os textos abaixo são saída REAL do Tesseract sobre os PDFs reais
(`_ocr_page`, `_ocr_recut_dacte_os_grade`, `_ocr_recut_dacte_os_caixas`),
verbatim - o da nota 17268 é o mesmo já fixado em
`test_dacte_os_staummaq_sigma_pag4.py`. Cada valor esperado foi conferido
contra a imagem da página (evidência primária).
"""
import os
import re

import pytest
from lxml import etree

from src.extractors import dacte_os_texto as _dacte
from src.extractors.pdf_extractor import SPPdfExtractor
from src.models.cte_os_model import CteOS, ImpostoCte
from src.transformers.cte_transformer import CteTransformer, grupo_icms, _txt as _tstring
from tests.test_dacte_os_staummaq_sigma_pag4 import MOCK_PAGINA as MOCK_PAGINA_17268
from tests.test_dacte_os_staummaq_sigma_pag4 import MOCK_GRADE as MOCK_GRADE_17268

# Recortes dedicados das caixas do cabeçalho (`_ocr_recut_dacte_os_caixas`), reais.
CAIXAS_17268 = {
    'emitente': """\
SIGMA TRANSPORTES LTDA
AVENIDA TANCREDO NEVES, 274, ED CENTRO
EMPRESARIAL IGUATEM - BLOCO B - SALA 133 -
CAMINHO DAS ARVORES
CEP: 41820-907, SALVADOR - BA
Fone: (71)3014-6060
lidio.santos(Ogtpba.com.br
CNPJ: 07.441.083/0001-01 | 15B:066668363
""",
    'tipo_servico': """\
TIPO DO SERVIÇO
Transporte de Pessoas
""",
    'cfop': """\
“CFOP - NATUREZA DA OPERAÇÃO
5351 - TRANSPORTE ESTADUAL
""",
}

# Nota 4035 - texto REAL de página inteira (pág. 1 de "STAUMMAQ - NFSe TERCEIROS 2.pdf").
MOCK_PAGINA_4035 = """\
DECLARO QUE RECEBI OS SERVIÇOS DESTE CONHECIMENTO EM PERFEITO ESTADO PELO QUE DOU POR CUMPRIDO O PRESENTE CONTRATO DE TRANSPORTE

Nº: 000.004.035

NOME:

| TÉRMINO DA PRESTAÇÃO - DATA/HORA

RG | INÍCIO DA PRESTAÇÃO - DATA / HORA
ASSINATURA / CARIMBO Série: 001
MODAL
COOPERATIVA DE RADIO TAXI DE SIMOES FILHO DACTE OS
Documento Auxiliar do Conhecimento de Transporte RODOVIÁRIO
Eletrônico para Outros Serviços

DATA E HORA EMISSÃO

02/09/2026 13:58:32

AV ELMO SEREJO FARIAS, 55 - CIA 1 pm 7)
CEP: 43700-000, SIMOES FILHO - BA
Fone: 71339-6210

financeirocoopercia(O gmail.com

CNPJ: 09.080.754/0001-73  1B:107746933

NÚMERO

000.004.035

SÉRIE
001

Chave de acesso

TIPO DO SERVIÇO 2926 0909 0807 5400 0173 6700 1000 0040 3510 0004 2842

Eiansporto Goi randes Consulta de autenticidade no portal nacional do CT-e, no site da Sefaz
Autorizadora, ou em http://www.cte.fazenda.gov.br/portal

TIPO DO CT-E
Normal

CFOP - NATUREZA DA OPERAÇÃO

5352 - TRANSPORTE ESTADUAL - INDUSTRIAL EDIDONLODSAUIOAGAÇÃO DEIRO
329260205216650 02/09/2026 14:00:40

INÍCIO DA PRESTAÇÃO PERCURSO DO VEÍCULO TÉRMINO DA PRESTAÇÃO

Simoes Filho - BA Salvador - BA

TOMADOR/USUÁRIO DO SERVIÇO: STAUMMAQ SERVICOS TECNICOS AUTOMACAO MOTORES E MAQUINAS MunIcÍPIO: Simoes Filho cer: 43700-000
ENDEREÇO: V URBANA , Nº 001 - SIMOES FILHO ur: BA País: Brasil

enpycrr: 02.370.080/0001-00 INSCEST.: 48137340 FONE: (71)2203-6320 EMAIL: marly()staummag.com.br

INFORMAÇÕES DA PRESTAÇÃO DO SERVIÇO

QUANTIDADE DESCRIÇÃO DO SERVIÇO PRESTADO
I TRANSPORTES DE PESSOAS

fio Wmo fito 232,85

COMPONENTES DO VALOR DA PRESTAÇÃO DE SERVIÇO

NOME VALOR [ NOME VALOR | NOME VALOR | NOME VALOR [VALOR TOTAL DA PRESTAÇÃO DO SERVIÇO
Frete Valor 3.760,90 3.760,90
VALOR À RECEBER
3.727,05
INFORMAÇÕES RELATIVAS AO IMPOSTO
CLASSIFICAÇÃO TRIBUTÁRIA DO SERVIÇO BASE DE CÁLCULO AL ICMS (%)| VALOR ICMS % RED.BC.CÁLC [ICMS ST
40 - ICMS ISENÇÃO 0,00 | 0,00 0,00 0,00 0,00
INSS PIS COFINS IR CSLL
0,00 0,00 0,00 33,85 0,00

OBSERVAÇÕES

SERVICOS TAXI INTERMUNICIPAL REFERENTE A AGOSTO/2026 DE CALCULO REDUZIDA PARA O IRRF 60% DO VALOR BRUTO DACT-e OS DE ACORDO COM O DECRETO
N 9.580 DE 22 DE NOVEMBRO DE 2018, ART.39, INCISO II. E CAP II, SECAO III, ART. 719, EM CONFORMIDADE COM O DISPOSITIVO NO ART. 55 DO RICMS - BA/12, ISENTO
DE ICMS CONFORME ARTIGO 265 XVIII RICMS/BA, CONVENIO ICMS99/8 VENCIMENTO 11/09/2026. PEDIDO 8408

SEGURO DA VIAGEM

NÚMERO DA APÓLICE

RESPONSÁVEL NOME DA SEGURADORA
Emitente
o INFORMAÇÕES ESPECÍFICAS DO MODAL RODOVIÁRIO

TERMO DE AUTORIZAÇÃO DE FRETAMENTO |Nº DO REGISTRO ESTADUAL PLACA DO VEÍCULO
0000000000000000000000000

USO EXCLUSIVO DO EMISSOR DO CT-e OS

RENAVAM DO VEÍCULO UF DE LICENCIAMENTO DO VEÍCULO [CNPJ/CPF
09.080.754/0001-73

RESERVADO AO FISCO

DATA E HORA DA IMPRESSÃO: 02/09/2026 14:06:18 Bsoft Internetworks - CT-e Prático - www.bsofl.com.br
"""

# Nota 4035 - recorte REAL da grade de valores/imposto.
MOCK_GRADE_4035 = """\
COMPONENTES DO VALOR DA PRESTAÇÃO DE SERVIÇO
NOME VALOR | NOME VALOR | NOME VALOR | NOME VALOR | VALOR TOTAL DA PRESTAÇÃO DO SERVIÇO
VALOR A RECEBER
CLASSIFICAÇÃO TRIBUTÁRIA DO SERVIÇO BASE DE CÁLCULO AL ICMS (%)| VALOR ICMS % RED.BC.CÁLC |ICMS ST
INSS PIS COFINS IR CSLL
"""

CAIXAS_4035 = {
    'emitente': """\
COOPERATIVA DE RADIO TAXI DE SIMOES FILHO
=) AV ELMO SEREJO FARIAS, 55 - CIA 1
CEP: 43700-000, SIMOES FILHO - BA
senda Fone: 71339-6210
custado financeirocoopercia(m gmail.com
CNPJ: 09.080.754/0001-73  1E:107746933
""",
    'tipo_servico': """\
TIPO DO SERVIÇO
Transporte de Pessoas
""",
    'cfop': """\
CFOP - NATUREZA DA OPERAÇÃO
5352 - TRANSPORTE ESTADUAL - INDUSTRIAL
""",
}
# Nota 564 - texto REAL de página inteira (pág. 2 de "STAUMMAQ - NFSe TERCEIROS 2.pdf").
MOCK_PAGINA_564 = """\
DECLARO QUE RECEBI OS SERVIÇOS DESTE CONHECIMENTO EM PERFEITO ESTADO PELO QUE DOU POR CUMPRIDO O PRESENTE CONTRATO DE TRANSPORTE

Nos TÉRMINO DA PRESTAÇÃO - DATA / HORA CT-e OS
xº. DOCUMENTO
E INÍCIO DA PRESTAÇÃO - DATA /HORA 000000564
ASSINATURA / CARIMBO str 001
D+ é “sosauu......“ =“... “.................... 0...“
CIATRANS POOL TRANSPORTES DE DACTE OS MODAL
PASSAGEIROS LTDA Documento Auxiliar do Conhecimento de Transporte Eletrônico po yTÁRIO

CNPJ: 30367671000156 IE: 149299655

para Outros Serviços

MODELO SÉRIE NÚMERO DATA E HORA EMISSÃO INSC. SUFRAMA DEST
Via das Torres, 646 - Complexo b 67 1 564 09/09/2026 09:11:12
Cia sul - Simoes Filho/BA - CEP: 43700000
e VI II IH] | WIN

TIPO DO CT-E

Normal
TIPO DO SERVIÇO

Transporte de Pessoas
CFOP- NATUREZA DA OPERAÇÃO
5352 - PRESTAÇÃO DE SERVIÇO DE TRANSPORTE

Ih AÇÃO

2930709 - Simoes Filho

PERCURSO DO VEÍCULO

CHAVE DE ACESSO

29260930367671000156670010000005641000005792
Consulta em https://dfe-portal.svrs.rs.gov.br/cte/consulta

PROTOCOLO DE AUTORIZAÇÃO DE USO
329260210669067 09/09/2026 09:17:26

TÉRMINO DA PRESTAÇÃO

2927408 - Salvador

TOMADOR DO SERVIÇO STAUMMAQ SERVICOS TECNICOS AUT MOT E MAQUINAS LTDA

Municírio: Simoes Filho

cer: 43700000

ENDEREÇO: Via URBANA, , Nº 01 - CIA SUL - Simões Filho ur: BA país: BRASIL
cnpycrr: 02.370.080/0001-00 16: 048137340 FONE: EMAIL:
INFORMAÇÕES DA PRESTAÇÃO DO SERVIÇO
QUANTIDADE DESCRIÇÃO DO SERVIÇO PRESTADO ER E E
0 Transporte de funcionários
a 2h)
709,?
o g h
58 Wo 050?
COMPONENTES DO VALOR DA PRESTAÇÃO DE SERVIÇO
NOME VALOR NOME VALOR NOME VALOR VALOR TOTAL DA PRESTAÇÃO DO SERVIÇO
TRANSPORTES 6.721,49
6.950,87
VALOR A RECEBER
6.721,49
INFORMAÇÕES RELATIVAS AO IMPOSTO

CLASSIFICAÇÃO TRIBUTÁRIA DO SERVIÇO BASE DE CÁLCULO AL ICMS (%) VALOR ICMS % RED.BC.CÁLC ICMS ST
0,00 20,50 0,00 100,00 0,00
VALOR DO PIS. VALOR COFINS VALOR DO IMPOSTO DE RENDA VALOR DO INSS VALOR DO CSLL
0,00 0,00 0,00 229,38 0,00

OBSERVAÇÕES

TRANSPORTE DE FUNCIONÁRIOS NO MÊS DE AGOSTO/VENCIMENTO: 14/09/2026
NUMERO DO PEDIDO: - 8411

SEGURO DA VIAGEM

RESPONSÁVEL. NÚMERO DA APÓLICE

NOME DA SEGURADORA

INFORMAÇÕES ESPECÍFICAS DO MODAL RODOVIÁRIO
PLACA DO VEÍCULO RENAVAN DO VEÍCULO UF DE LICENCIAMENTO DO VEÍCULO CNPJ/CPF

869471996 BA 03552115560
RESERVADO AO FISCO

TERMO DE AUTORIZAÇÃO DE FRETAMENTO Nº DO REGISTRO ESTADUAL
0000000000000000000043115  MQN2581

USO EXCLUSIVO DO EMISSOR DO CT-e OS

DATA E HORA DA IMPRESSÃO: 09/09/2026 09:17:48 Master CT-e - www.officesystem.com.br
"""

# Nota 564 - recorte REAL da grade de valores/imposto.
MOCK_GRADE_564 = """\
COMPONENTES DO VALOR DA PRESTAÇÃO DE SERVIÇO
NOME VALOR NOME VALOR NOME VALOR VALOR TOTAL DA PRESTAÇÃO DO SERVIÇO
TRANSPORTES 6.721,49
6.950,87
VALOR A RECEBER
6.721,49
INFORMAÇÕES RELATIVAS AO IMPOSTO

CLASSIFICAÇÃO TRIBUTÁRIA DO SERVIÇO BASE DE CÁLCULO AL ICMS (%) VALOR ICMS % RED.BC.CÁLC ICMS ST
0,00 20,50 0,00 100,00 0,00
VALOR DO PIS VALOR COFINS VALOR DO IMPOSTO DE RENDA VALOR DO INSS VALOR DO CSLL
0,00 0,00 0,00 229,38 0,00
"""

CAIXAS_564 = {
    'emitente': """\
a Ur
CIATRANS POOL TRANSPORTES DE
PASSAGEIROS LTDA

CNPJ: 30367671000156 IE: 149299655
Via das Torres, 646 - Complexo b
Cia sul - Simoes Filho/BA - CEP: 43700000
FONE: 7135947121
""",
    'tipo_servico': """\
TIPO DO SERVIÇO
Transporte de Pessoas
""",
    'cfop': """\
CFOP - NATUREZA DA OPERAÇÃO
5352 - PRESTAÇÃO DE SERVIÇO DE TRANSPORTE
""",
}


# =====================================================================
# Infra
# =====================================================================

NS = "http://www.portalfiscal.inf.br/cte"
DS = "http://www.w3.org/2000/09/xmldsig#"


def _q(tag):
    return f"{{{NS}}}{tag}"


def _parse(monkeypatch, tmp_path, pagina, grade, caixas, pagina_hint=1):
    pdf_path = tmp_path / "dacte_os.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 dummy")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: pagina)
    monkeypatch.setattr(SPPdfExtractor, "_ocr_recut_dacte_os_grade", lambda self: grade)
    monkeypatch.setattr(SPPdfExtractor, "_ocr_recut_dacte_os_caixas", lambda self: dict(caixas))
    ex = SPPdfExtractor(str(pdf_path))
    ex._pagina_hint = pagina_hint
    notas = ex.parse_multiple()
    assert len(notas) == 1
    assert isinstance(notas[0], CteOS)
    return notas[0]


NOTAS = {
    "17268": (MOCK_PAGINA_17268, MOCK_GRADE_17268, CAIXAS_17268),
    "4035": (MOCK_PAGINA_4035, MOCK_GRADE_4035, CAIXAS_4035),
    "564": (MOCK_PAGINA_564, MOCK_GRADE_564, CAIXAS_564),
}


@pytest.fixture(params=sorted(NOTAS))
def par(request, monkeypatch, tmp_path):
    """(número da nota, CteOS, XML de saída) para cada uma das 3 notas reais."""
    pagina, grade, caixas = NOTAS[request.param]
    cte = _parse(monkeypatch, tmp_path, pagina, grade, caixas)
    return request.param, cte, CteTransformer().transform(cte)


@pytest.fixture
def n17268(monkeypatch, tmp_path):
    return _parse(monkeypatch, tmp_path, *NOTAS["17268"])


@pytest.fixture
def n4035(monkeypatch, tmp_path):
    return _parse(monkeypatch, tmp_path, *NOTAS["4035"])


@pytest.fixture
def n564(monkeypatch, tmp_path):
    return _parse(monkeypatch, tmp_path, *NOTAS["564"])


def _xml(cte):
    return etree.fromstring(CteTransformer().transform(cte).encode("utf-8"))


def _txt(root, caminho):
    el = root.find(caminho, {"c": NS})
    return None if el is None else el.text


def _filhos(el):
    return [etree.QName(c).localname for c in el]


# =====================================================================
# Estrutura do leiaute oficial 4.00 (TCTeOS) - vale para as 3 notas
# =====================================================================

# Ordem das sequências do XSD oficial (cteTiposBasico_v4.00.xsd, TCTeOS).
ORDEM_IDE = ["cUF", "cCT", "CFOP", "natOp", "mod", "serie", "nCT", "dhEmi", "tpImp", "tpEmis",
             "cDV", "tpAmb", "tpCTe", "procEmi", "verProc", "cMunEnv", "xMunEnv", "UFEnv", "modal",
             "tpServ", "indIEToma", "cMunIni", "xMunIni", "UFIni", "cMunFim", "xMunFim", "UFFim"]
ORDEM_INFCTE = ["ide", "compl", "emit", "toma", "vPrest", "imp", "infCTeNorm"]


def test_raiz_e_cteosproc_modelo_67_nao_cteproc_modelo_57(par):
    """Antes: `cteProc`/`CTe` (raízes do Modelo 57, CT-e de CARGA) - o
    Domínio não reconhecia nenhuma linha ("Sem dados para importar")."""
    _, cte, xml = par
    root = etree.fromstring(xml.encode("utf-8"))
    assert root.tag == _q("cteOSProc")
    assert root.get("versao") == "4.00"
    assert _filhos(root) == ["CTeOS", "protCTe"]
    assert root[0].get("versao") == "4.00"
    inf = root.find("c:CTeOS/c:infCte", {"c": NS})
    assert inf.get("Id") == "CTe" + cte.chave_acesso
    assert "<cteProc" not in xml and "<CTe " not in xml and "<CTe>" not in xml


def test_ordem_dos_grupos_do_infcte(par):
    _, cte, xml = par
    inf = etree.fromstring(xml.encode("utf-8")).find("c:CTeOS/c:infCte", {"c": NS})
    assert _filhos(inf) == ORDEM_INFCTE


def test_ide_completo_e_na_ordem_do_xsd(par):
    """Antes faltavam cCT, cMunEnv/xMunEnv/UFEnv, modal, indIEToma, UFIni/
    UFFim; o tipo do serviço era texto (`tpServico`) e nProt/dhRecbto
    estavam dentro do `ide` (só existem no `protCTe`)."""
    _, cte, xml = par
    ide = etree.fromstring(xml.encode("utf-8")).find("c:CTeOS/c:infCte/c:ide", {"c": NS})
    assert _filhos(ide) == ORDEM_IDE
    assert ide.find(_q("tpServ")).text == "6"  # "Transporte de Pessoas"
    assert ide.find(_q("modal")).text == "01"  # "MODAL RODOVIÁRIO"
    assert ide.find(_q("indIEToma")).text == "1"  # tomador com IE impressa
    assert ide.find(_q("mod")).text == "67"
    for proibido in ("tpServico", "nProt", "dhRecbto"):
        assert ide.find(_q(proibido)) is None


def test_campos_derivados_da_chave_de_acesso(par):
    """cUF, cCT, tpEmis e cDV saem DA CHAVE (conferida por DV mod-11)."""
    _, cte, xml = par
    ch = cte.chave_acesso
    ide = etree.fromstring(xml.encode("utf-8")).find("c:CTeOS/c:infCte/c:ide", {"c": NS})
    assert ide.find(_q("cUF")).text == ch[0:2]
    assert ide.find(_q("cCT")).text == ch[35:43]
    assert ide.find(_q("tpEmis")).text == ch[34]
    assert ide.find(_q("cDV")).text == ch[43]
    assert ide.find(_q("nCT")).text == str(int(ch[25:34]))
    assert ide.find(_q("serie")).text == str(int(ch[22:25]))


def test_retencoes_federais_em_inftribfed_nao_em_grupo_inventado(par):
    """Antes: grupo `<retencoes>` fora do `imp` (não existe no leiaute)."""
    _, cte, xml = par
    root = etree.fromstring(xml.encode("utf-8"))
    imp = root.find("c:CTeOS/c:infCte/c:imp", {"c": NS})
    assert _filhos(imp) == ["ICMS", "infTribFed"]
    assert _filhos(imp.find(_q("infTribFed"))) == ["vPIS", "vCOFINS", "vIR", "vINSS", "vCSLL"]
    assert "<retencoes>" not in xml and "<total>" not in xml


def test_infcte_norm_com_infservico_e_modal_rodoviario(par):
    """Antes: `infServico/qCarga` direto e `infModal` solto no `infCte`. No
    leiaute: `infCTeNorm/infServico[/infQ/qCarga]` e `infCTeNorm/infModal
    [@versaoModal]/rodoOS` (obrigatório para transporte de pessoas)."""
    _, cte, xml = par
    norm = etree.fromstring(xml.encode("utf-8")).find("c:CTeOS/c:infCte/c:infCTeNorm", {"c": NS})
    assert _filhos(norm) == ["infServico", "infModal"]
    assert norm.find(_q("infModal")).get("versaoModal") == "4.00"
    assert norm.find("c:infServico/c:qCarga", {"c": NS}) is None
    rodo = norm.find("c:infModal/c:rodoOS", {"c": NS})
    assert len(rodo.find(_q("NroRegEstadual")).text) == 25


def test_protocolo_so_no_protcte(par):
    _, cte, xml = par
    prot = etree.fromstring(xml.encode("utf-8")).find("c:protCTe/c:infProt", {"c": NS})
    assert _filhos(prot) == ["tpAmb", "verAplic", "chCTe", "dhRecbto", "nProt", "cStat", "xMotivo"]
    assert prot.find(_q("nProt")).text == cte.protocolo_autorizacao
    assert prot.find(_q("chCTe")).text == cte.chave_acesso
    assert prot.find(_q("cStat")).text == "100"
    # digVal vazio (antes `<digVal />`) não é emitido: não temos o digest.
    assert prot.find(_q("digVal")) is None


def test_datas_no_formato_utc_do_leiaute(par):
    _, cte, xml = par
    root = etree.fromstring(xml.encode("utf-8"))
    dh = _txt(root, "c:CTeOS/c:infCte/c:ide/c:dhEmi")
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}-03:00", dh)


# =====================================================================
# Nota 17268 - SIGMA TRANSPORTES (gerador CT-e Prático/Bsoft)
# =====================================================================

def test_17268_rota_salvador_para_simoes_filho(n17268):
    """Antes: cMunIni/xMunIni/cMunFim/xMunFim vazios (o CT-e Prático
    imprime só "Salvador - BA Simoes Filho - BA", sem código IBGE)."""
    root = _xml(n17268)
    ide = "c:CTeOS/c:infCte/c:ide/c:"
    assert (_txt(root, ide + "cMunIni"), _txt(root, ide + "xMunIni"), _txt(root, ide + "UFIni")) == \
        ("2927408", "Salvador", "BA")
    assert (_txt(root, ide + "cMunFim"), _txt(root, ide + "xMunFim"), _txt(root, ide + "UFFim")) == \
        ("2930709", "Simoes Filho", "BA")
    # Município de envio = do emitente (Salvador).
    assert _txt(root, ide + "cMunEnv") == "2927408"


def test_17268_tipo_do_servico_lido_do_recorte_da_caixa(n17268):
    """Texto de página inteira: "Normal d soas Pr r" (ilegível). Recorte
    dedicado da caixa "TIPO DO SERVIÇO": "Transporte de Pessoas"."""
    assert n17268.tipo_servico == "Transporte de Pessoas"
    assert n17268.tipo_servico_codigo == "6"
    assert not any("Tipo do serviço" in a for a in n17268.avisos)


def test_17268_emitente_endereco_completo_com_bairro(n17268):
    """Antes: xCpl "ED CENTRO" (truncado) e xBairro "BAIRRO" (placeholder) -
    o bairro impresso "CAMINHO DAS ARVORES" saía ANTES da razão social no
    texto de página inteira."""
    e = n17268.emitente
    assert e.razao_social == "SIGMA TRANSPORTES LTDA"
    assert e.cnpj_cpf == "07441083000101"
    assert e.inscricao_estadual == "066668363"
    end = e.endereco
    assert (end.logradouro, end.numero) == ("AVENIDA TANCREDO NEVES", "274")
    assert end.complemento == "ED CENTRO EMPRESARIAL IGUATEM - BLOCO B - SALA 133"
    assert end.bairro == "CAMINHO DAS ARVORES"
    assert (end.municipio, end.uf, end.cep, end.codigo_municipio) == ("SALVADOR", "BA", "41820907", "2927408")
    assert e.telefone == "7130146060"
    assert _txt(_xml(n17268), "c:CTeOS/c:infCte/c:emit/c:enderEmit/c:xBairro") == "CAMINHO DAS ARVORES"


def test_17268_icms_cst_40_vai_para_icms45(n17268):
    """"40 - ICMS ISENÇÃO" impresso. Antes: sempre `ICMS00` (tributação
    normal) - errado para isenção."""
    root = _xml(n17268)
    icms = root.find("c:CTeOS/c:infCte/c:imp/c:ICMS", {"c": NS})
    assert _filhos(icms) == ["ICMS45"]
    assert _txt(icms, "c:ICMS45/c:CST") == "40"


def test_17268_tributos_federais_na_ordem_do_gerador_bsoft(n17268):
    """Colunas do CT-e Prático: INSS / PIS / COFINS / IR / CSLL = 69,80 /
    13,75 / 63,45 / 0,00 / 0,00. Antes: tudo 0.00 no XML."""
    imp = n17268.imposto
    assert (imp.valor_inss, imp.valor_pis, imp.valor_cofins, imp.valor_ir, imp.valor_csll) == \
        (pytest.approx(69.80), pytest.approx(13.75), pytest.approx(63.45), 0.0, 0.0)
    root = _xml(n17268)
    trib = "c:CTeOS/c:infCte/c:imp/c:infTribFed/c:"
    assert [_txt(root, trib + t) for t in ("vPIS", "vCOFINS", "vIR", "vINSS", "vCSLL")] == \
        ["13.75", "63.45", "0.00", "69.80", "0.00"]


def test_17268_valor_a_receber_com_ultimo_digito_cortado_na_margem(n17268):
    """O "8" final de 2.115,08 sai cortado na margem direita do papel nas
    duas linhas (total e a receber) - o OCR lê "2.115,0%". Antes: vRec
    2115.00. O total vem íntegro do recorte (2.115,08, igual ao componente
    "Frete Valor"); o a receber só é completado porque EXATAMENTE uma
    identidade do documento casa o prefixo "2.115,0": a receber = total
    (2.115,08). Total - retenções (1.968,08) não casa. Aviso registrado."""
    assert n17268.valor_total_prestacao == pytest.approx(2115.08)
    assert n17268.valor_a_receber == pytest.approx(2115.08)
    assert any("Último dígito do Valor a Receber cortado" in a for a in n17268.avisos)
    root = _xml(n17268)
    assert _txt(root, "c:CTeOS/c:infCte/c:vPrest/c:vRec") == "2115.08"


def test_17268_aviso_de_retencoes_nao_deduzidas_do_valor_a_receber(n17268):
    """Nesta nota as retenções impressas (R$147,00) NÃO foram deduzidas do
    valor a receber - a identidade vRec = vTPrest - retenções não fecha e
    isso é avisado (não corrigido)."""
    assert any("não bate com Valor Total" in a for a in n17268.avisos)


def test_17268_observacoes_completas(n17268):
    """Antes: sem `compl/xObs` (o bloco terminava em "NOME DA SEGURADORA" no
    início de linha, que neste gerador sai depois de "RESPONSÁVEL")."""
    assert n17268.observacoes.startswith("PRESTACAO DE SERVICO NO TRANSPORTE DE PESSOAL REF. AGOSTO/2026")
    assert "SEGURO DA VIAGEM" not in n17268.observacoes
    assert _txt(_xml(n17268), "c:CTeOS/c:infCte/c:compl/c:xObs").startswith("PRESTACAO DE SERVICO")


def test_17268_registro_estadual(n17268):
    assert n17268.modal_rodoviario.registro_estadual == "0000000000000000066668363"


# =====================================================================
# Nota 4035 - COOPERATIVA DE RADIO TAXI DE SIMOES FILHO (CT-e Prático)
# =====================================================================

def test_4035_emitente_sem_sufixo_societario(n4035):
    """Antes: "Emitente Não Identificado" (a busca exigia LTDA/EIRELI/S/A/ME
    e a cooperativa não tem nenhum) e endereço "Não informado"/CEP zerado."""
    e = n4035.emitente
    assert e.razao_social == "COOPERATIVA DE RADIO TAXI DE SIMOES FILHO"
    assert e.cnpj_cpf == "09080754000173"
    assert e.inscricao_estadual == "107746933"
    end = e.endereco
    assert (end.logradouro, end.numero, end.complemento) == ("AV ELMO SEREJO FARIAS", "55", None)
    # Impresso "CIA I"; o OCR lê "CIA 1" em qualquer zoom/psm (teto de OCR,
    # campo não fiscal) - fixado como lido, sem correção por nota.
    assert end.bairro == "CIA 1"
    assert (end.municipio, end.uf, end.cep, end.codigo_municipio) == ("SIMOES FILHO", "BA", "43700000", "2930709")
    assert e.telefone == "713396210"


def test_4035_valores_e_ir_retido(n4035):
    """Antes: vTPrest/vRec 0.00 (o recorte da grade sai SEM nenhum valor
    nesta nota; o texto de página inteira traz a grade íntegra e agora é
    aceito por âncora estrutural estrita). 3.760,90 - 33,85 = 3.727,05."""
    assert n4035.valor_total_prestacao == pytest.approx(3760.90)
    assert n4035.valor_a_receber == pytest.approx(3727.05)
    assert n4035.imposto.valor_ir == pytest.approx(33.85)
    assert n4035.imposto.valor_inss == 0.0
    assert not any("não bate com Valor Total" in a for a in n4035.avisos)
    root = _xml(n4035)
    assert _txt(root, "c:CTeOS/c:infCte/c:vPrest/c:vTPrest") == "3760.90"
    assert _txt(root, "c:CTeOS/c:infCte/c:imp/c:infTribFed/c:vIR") == "33.85"
    assert _txt(root, "c:CTeOS/c:infCte/c:imp/c:ICMS/c:ICMS45/c:CST") == "40"


def test_4035_protocolo_com_rotulo_destruido(n4035):
    """O rótulo "PROTOCOLO DE AUTORIZAÇÃO DE USO" sai destruído e colado à
    natureza da operação; o número vem da linha "<15 dígitos> <data>
    <hora>" validada pela estrutura (2º/3º dígitos = cUF da chave)."""
    assert n4035.protocolo_autorizacao == "329260205216650"
    assert n4035.protocolo_data_hora.strftime("%d/%m/%Y %H:%M:%S") == "02/09/2026 14:00:40"


def test_4035_natureza_da_operacao_sem_lixo_de_ocr(n4035):
    """Antes: "TRANSPORTE ESTADUAL - INDUSTRIAL EDIDONLODSAUIOAGAÇÃO DEIRO"."""
    assert n4035.cfop == "5352"
    assert n4035.natureza_operacao == "TRANSPORTE ESTADUAL - INDUSTRIAL"


def test_4035_servico_e_quantidade(n4035):
    """Quantidade impressa "1" sai "I" no OCR; descrição "TRANSPORTES DE
    PESSOAS" (antes "Não informado"/qCarga 0)."""
    assert n4035.quantidade_servico == 1.0
    assert n4035.descricao_servico == "TRANSPORTES DE PESSOAS"
    root = _xml(n4035)
    assert _txt(root, "c:CTeOS/c:infCte/c:infCTeNorm/c:infServico/c:infQ/c:qCarga") == "1.0000"


def test_4035_tomador_endereco_sem_bairro(n4035):
    """"V URBANA , Nº 001 - SIMOES FILHO" - sem bairro impresso. Antes: todo
    o endereço "Não informado" e xMun vazio."""
    tom = n4035.tomador
    assert tom.razao_social == "STAUMMAQ SERVICOS TECNICOS AUTOMACAO MOTORES E MAQUINAS"
    assert tom.inscricao_estadual == "48137340"
    end = tom.endereco
    assert (end.logradouro, end.numero, end.municipio, end.uf, end.cep, end.codigo_municipio) == \
        ("V URBANA", "001", "SIMOES FILHO", "BA", "43700000", "2930709")
    assert end.bairro == "Não informado"
    assert any("Bairro do tomador não impresso" in a for a in n4035.avisos)
    assert tom.telefone == "7122036320"


def test_4035_rota_simoes_filho_para_salvador(n4035):
    assert (n4035.codigo_municipio_inicio, n4035.municipio_inicio_prestacao) == ("2930709", "Simoes Filho")
    assert (n4035.codigo_municipio_fim, n4035.municipio_fim_prestacao) == ("2927408", "Salvador")


def test_4035_registro_estadual_todo_zero_e_o_impresso(n4035):
    assert n4035.modal_rodoviario.registro_estadual == "0" * 25


# =====================================================================
# Nota 564 - CIATRANS (gerador Master CT-e)
# =====================================================================

def test_564_emitente_razao_social_de_duas_linhas(n564):
    """Antes: "PASSAGEIROS LTDA" (só a 2ª linha) e endereço "Não informado"."""
    e = n564.emitente
    assert e.razao_social == "CIATRANS POOL TRANSPORTES DE PASSAGEIROS LTDA"
    end = e.endereco
    assert (end.logradouro, end.numero, end.complemento, end.bairro) == \
        ("Via das Torres", "646", "Complexo b", "Cia sul")
    assert (end.municipio, end.uf, end.cep, end.codigo_municipio) == ("Simoes Filho", "BA", "43700000", "2930709")


def test_564_sem_aviso_falso_de_numero_divergente(n564):
    """Impresso "000000564" = 564 da chave. Antes: "Número lido (00000000)
    divergente da chave de acesso (564)" - o número simplesmente não era
    lido (a linha de valores começa com o endereço do emitente)."""
    assert n564.numero == "564"
    assert not any("divergente" in a for a in n564.avisos)


def test_564_tomador_xmun_sem_rotulos_colados(n564):
    """Antes: xMun "Simões Filho ur: BA país: BRASIL"."""
    end = n564.tomador.endereco
    assert end.municipio == "Simões Filho"
    assert n564.tomador.inscricao_estadual == "048137340"  # rótulo "IE:" lido "16:"


def test_564_descricao_do_servico(n564):
    """Antes: "Não informado" (lixo "ER E E" à direita da linha de rótulos)."""
    assert n564.descricao_servico == "Transporte de funcionários"
    assert n564.quantidade_servico == 0.0


def test_564_icms_com_reducao_de_100_vai_para_icms20(n564):
    """CST não impresso; BC 0,00, alíquota 20,50, redução 100,00 -> grupo
    `ICMS20` (redução de BC), derivado SÓ da grade impressa, com aviso."""
    root = _xml(n564)
    g = root.find("c:CTeOS/c:infCte/c:imp/c:ICMS/c:ICMS20", {"c": NS})
    assert _filhos(g) == ["CST", "pRedBC", "vBC", "pICMS", "vICMS"]
    assert [c.text for c in g] == ["20", "100.00", "0.00", "20.50", "0.00"]
    assert any(a.startswith("CST do ICMS não impresso") for a in n564.avisos)


def test_564_valores_e_inss(n564):
    """6.950,87 - 229,38 = 6.721,49."""
    assert n564.valor_total_prestacao == pytest.approx(6950.87)
    assert n564.valor_a_receber == pytest.approx(6721.49)
    assert n564.imposto.valor_inss == pytest.approx(229.38)
    assert not any("não bate com Valor Total" in a for a in n564.avisos)


def test_564_veiculo_no_rodoos(n564):
    root = _xml(n564)
    veic = root.find("c:CTeOS/c:infCte/c:infCTeNorm/c:infModal/c:rodoOS/c:veic", {"c": NS})
    assert [(etree.QName(c).localname, c.text) for c in veic] == \
        [("placa", "MQN2581"), ("RENAVAM", "869471996"), ("UF", "BA")]


def test_564_rota_com_codigo_impresso_e_rotulo_destruido(n564):
    """"INÍCIO DA PRESTAÇÃO" sai "Ih AÇÃO" no OCR; o código impresso
    "2930709 - Simoes Filho" ainda é o 1º da ordem de leitura."""
    assert (n564.codigo_municipio_inicio, n564.uf_inicio_prestacao) == ("2930709", "BA")
    assert (n564.codigo_municipio_fim, n564.municipio_fim_prestacao) == ("2927408", "Salvador")


# =====================================================================
# Degradados: campo ilegível -> sentinela documentada + aviso
# =====================================================================

def test_valor_a_receber_truncado_sem_identidade_unica_nao_e_completado(monkeypatch, tmp_path):
    """Prefixo cortado que não casa com nenhuma identidade do documento ->
    NÃO escolhe um dígito: zera e avisa."""
    grade = MOCK_GRADE_17268.replace("VALOR A RECEBER\n2.115,0", "VALOR A RECEBER\n2.000,0")
    pagina = MOCK_PAGINA_17268.replace("2.115,0:", "2.000,0:")
    cte = _parse(monkeypatch, tmp_path, pagina, grade, CAIXAS_17268)
    assert cte.valor_a_receber == 0.0
    assert any("Valor total da prestação de serviço não encontrado" in a for a in cte.avisos)
    assert not any("completado" in a for a in cte.avisos)


def test_municipio_sem_codigo_ibge_conhecido_vira_sentinela_com_aviso(monkeypatch, tmp_path):
    """Nunca o fallback silencioso da capital (Salvador) - sentinela
    0000000 + aviso."""
    caixas = dict(CAIXAS_4035)
    caixas["emitente"] = caixas["emitente"].replace("SIMOES FILHO - BA", "VILA INEXISTENTE - BA")
    cte = _parse(monkeypatch, tmp_path, MOCK_PAGINA_4035, MOCK_GRADE_4035, caixas)
    assert cte.emitente.endereco.municipio == "VILA INEXISTENTE"
    assert cte.emitente.endereco.codigo_municipio == ""
    assert any("VILA INEXISTENTE" in a and "0000000" in a for a in cte.avisos)
    root = _xml(cte)
    assert _txt(root, "c:CTeOS/c:infCte/c:emit/c:enderEmit/c:cMun") == "0000000"
    assert _txt(root, "c:CTeOS/c:infCte/c:ide/c:cMunEnv") == "0000000"


def test_sem_os_recortes_das_caixas_tipo_do_servico_ilegivel_e_avisado(monkeypatch, tmp_path):
    """Sem o recorte da caixa (PDF sem página real), o texto de página
    inteira "Normal d soas Pr r" NÃO vira tipo de serviço: "Não informado" +
    tpServ inferido da descrição "TRANSPORTE DE PESSOAL" com aviso."""
    cte = _parse(monkeypatch, tmp_path, MOCK_PAGINA_17268, MOCK_GRADE_17268, {})
    assert cte.tipo_servico == "Não informado"
    assert cte.tipo_servico_codigo == "6"
    assert any("inferido da descrição" in a for a in cte.avisos)


def test_cst_ausente_sem_reducao_nem_icms_vai_para_icms90():
    """Grade zerada e CST em branco: não afirma isenção (ICMS45) nem
    tributação normal (ICMS00) - usa ICMS90 ("Outros")."""
    assert ImpostoCte().cst_derivado() == "90"
    assert ImpostoCte(percentual_reducao_bc=100.0).cst_derivado() == "20"
    assert ImpostoCte(base_calculo_icms=100.0, aliquota_icms=12.0, valor_icms=12.0).cst_derivado() == "00"
    assert grupo_icms("41") == grupo_icms("51") == "ICMS45"
    assert grupo_icms("90") == grupo_icms(None) == "ICMS90"


def test_chave_ilegivel_vira_sentinela_de_zeros(n4035):
    cte = n4035.model_copy(update={"chave_acesso": "", "protocolo_autorizacao": None})
    root = _xml(cte)
    # Sem protocolo, a raiz é o próprio CTeOS (o cteOSProc exige protCTe).
    assert root.tag == _q("CTeOS")
    assert root.find(_q("infCte")).get("Id") == "CTe" + "0" * 44


def test_texto_fora_do_latin1_e_normalizado_para_tstring():
    """TString do leiaute só aceita caracteres de "!" a "ÿ" - aspas/
    travessões tipográficos do OCR viram ASCII."""
    assert _tstring("  “A” – B\n C  ", 60) == '"A" - B C'


# =====================================================================
# Helpers puros (dacte_os_texto)
# =====================================================================

def test_ordem_das_colunas_federais_por_gerador():
    master = "VALOR DO PIS VALOR COFINS VALOR DO IMPOSTO DE RENDA VALOR DO INSS VALOR DO CSLL\n1,00 2,00 3,00 4,00 5,00"
    bsoft = "INSS PIS COFINS IR CSLL\n1,00 2,00 3,00 4,00 5,00"
    assert _dacte.parse_federais(master) == {"pis": 1.0, "cofins": 2.0, "ir": 3.0, "inss": 4.0, "csll": 5.0}
    assert _dacte.parse_federais(bsoft) == {"inss": 1.0, "pis": 2.0, "cofins": 3.0, "ir": 4.0, "csll": 5.0}
    # 4 valores (um ilegível) -> não confiável.
    assert _dacte.parse_federais("INSS PIS COFINS CSLL\n69,80 13,75 63,45 Fi vm 0,00") is None


def test_completar_truncado_so_com_candidato_unico():
    assert _dacte.completar_truncado("2.115,0", [2115.08, 1968.08]) == pytest.approx(2115.08)
    assert _dacte.completar_truncado("2.115,0", [2115.08, 2115.01]) is None
    assert _dacte.completar_truncado("2.115,0", [1968.08]) is None


# =====================================================================
# Validação contra o XSD OFICIAL (PL_CTe_400)
# =====================================================================
# O pacote de schemas oficial NÃO é versionado neste repositório (não há
# convenção de guardar XSD aqui, e ele é republicado pela SEFAZ a cada
# Nota Técnica). Para rodar: baixar o "Pacote de Liberação 4.00" em
# https://www.cte.fazenda.gov.br/portal/ -> "Esquemas XML", descompactar e
# apontar a variável de ambiente CTE_OS_XSD_DIR para a pasta que contém
# procCTeOS_v4.00.xsd. Sem ela, os testes abaixo são pulados.

XSD_DIR = os.environ.get("CTE_OS_XSD_DIR", "")
precisa_xsd = pytest.mark.skipif(
    not os.path.isfile(os.path.join(XSD_DIR, "procCTeOS_v4.00.xsd")),
    reason="XSD oficial do CT-e 4.00 indisponível (defina CTE_OS_XSD_DIR)")


def _assinatura_ficticia(chave):
    """ds:Signature ESTRUTURALMENTE válida para o xmldsig-core-schema_v1.01
    do pacote (valores sem significado criptográfico) - usada SÓ neste teste,
    nunca no XML de saída."""
    s = etree.Element(f"{{{DS}}}Signature", nsmap={None: DS})
    si = etree.SubElement(s, f"{{{DS}}}SignedInfo")
    etree.SubElement(si, f"{{{DS}}}CanonicalizationMethod", Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
    etree.SubElement(si, f"{{{DS}}}SignatureMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1")
    ref = etree.SubElement(si, f"{{{DS}}}Reference", URI=f"#CTe{chave}")
    tr = etree.SubElement(ref, f"{{{DS}}}Transforms")
    etree.SubElement(tr, f"{{{DS}}}Transform", Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature")
    etree.SubElement(tr, f"{{{DS}}}Transform", Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
    etree.SubElement(ref, f"{{{DS}}}DigestMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#sha1")
    etree.SubElement(ref, f"{{{DS}}}DigestValue").text = "AAAAAAAAAAAAAAAAAAAAAAAAAAA="
    etree.SubElement(s, f"{{{DS}}}SignatureValue").text = "AAAA"
    ki = etree.SubElement(s, f"{{{DS}}}KeyInfo")
    etree.SubElement(etree.SubElement(ki, f"{{{DS}}}X509Data"), f"{{{DS}}}X509Certificate").text = "AAAA"
    return s


@precisa_xsd
def test_xsd_oficial_unico_erro_e_a_assinatura_ausente(par):
    _, cte, xml = par
    schema = etree.XMLSchema(etree.parse(os.path.join(XSD_DIR, "procCTeOS_v4.00.xsd")))
    doc = etree.fromstring(xml.encode("utf-8"))
    assert not schema.validate(doc)
    erros = [e.message for e in schema.error_log]
    assert len(erros) == 1
    assert "CTeOS': Missing child element(s)" in erros[0] and "Signature" in erros[0]


@precisa_xsd
def test_xsd_oficial_valida_com_assinatura_ficticia(par):
    _, cte, xml = par
    schema = etree.XMLSchema(etree.parse(os.path.join(XSD_DIR, "procCTeOS_v4.00.xsd")))
    doc = etree.fromstring(xml.encode("utf-8"))
    inf = doc.find("c:CTeOS/c:infCte", {"c": NS})
    inf.addnext(_assinatura_ficticia(cte.chave_acesso))
    assert schema.validate(doc), [e.message for e in schema.error_log]


@precisa_xsd
def test_xsd_oficial_do_modal_rodoviario_os(par):
    _, cte, xml = par
    schema = etree.XMLSchema(etree.parse(os.path.join(XSD_DIR, "cteModalRodoviarioOS_v4.00.xsd")))
    rodo = etree.fromstring(xml.encode("utf-8")).find(".//c:rodoOS", {"c": NS})
    assert schema.validate(etree.ElementTree(rodo)), [e.message for e in schema.error_log]
