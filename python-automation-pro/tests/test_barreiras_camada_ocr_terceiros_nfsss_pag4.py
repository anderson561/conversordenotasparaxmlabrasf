# -*- coding: utf-8 -*-
r"""NFS-e de Barreiras/BA cujo PDF chega com uma camada de texto de OCR de
TERCEIROS já embutida (achado real 2026-09-11, lote "nfsss", pág. 4 de 4 —
nota nº 8965, CHAVES LOCACOES LTDA/LOKMAQ -> SAO PEDRO CONSTRUTORA LTDA,
R$196,00). Reportado pelo usuário: "corrigir a extração da página 4".

O XML saía com TUDO errado: `ValorServicos` 0,00 (a nota é de R$196,00),
`Numero` 00000000 (é 8965), `DataEmissao` = o INSTANTE DA CONVERSÃO (a nota é
de 24/08/2026), e o `<Cnpj>` do PRESTADOR preenchido com o CNPJ do TOMADOR.

CAUSA-RAIZ: o PDF é escaneado, mas alguém já rodou um OCR nele e embutiu o
resultado como camada de texto. Essa camada tem 2.318 caracteres — longa o
bastante para o portão de `parse_multiple` (`len < 200 or not has_keywords`)
concluir que há texto utilizável e NUNCA rodar o nosso Tesseract. E ela é
péssima: "MUNICIPIO" saiu "IIUNICIPIO", "Data Fato Gerador" saiu
"DIIIFMoGlradlf", "Nº da Nota Fiscal" saiu "WuNotaFJscal", "Razão Social:"
saiu "Razio Soclal:" e "~ Social.".

Com as DUAS marcas municipais destruídas ao mesmo tempo, a página caía no
check largo de "Chave de Acesso" e era parseada inteira como DANFSe Nacional.
As págs. 2 e 3 do mesmo lote têm a marca intacta e roteavam certo — só a 4
quebrou. `_detect_layout_page` ainda estava com 2 marcas enquanto
`_detect_layout` já tinha 3: a assimetria entre os dois detectores, que num
lote é ESTE quem decide.

O QUE NÃO FUNCIONA, e foi medido antes de escolher o caminho: trocar a camada
ruim pelo nosso próprio OCR. Nesta página a camada embutida pontua **44** em
`_score_ocr_text` e o nosso OCR de página inteira pontua **18** (1.256
caracteres, perde até "VALOR SERVIÇO"). As duas fontes são COMPLEMENTARES — a
camada tem a grade de valores, o nosso OCR tem as entidades limpas — e a
correção usa cada uma para o que ela sabe ler, com um recorte do cabeçalho
(zoom 5 + PSM 6) para número e data, que nenhuma das duas traz.

Verdade da página, conferida na imagem em zoom 4x:
    nº 8965 | Data Fato Gerador 24/08/2026 | Valor Serviço 196,00 |
    Base 196,00 | Alíquota 0.00 | ISS 0,00 | Líquido 196,00 |
    Prestador CHAVES LOCACOES LTDA, CNPJ 40.536.716/0001-22, Barreiras/BA |
    Tomador SAO PEDRO CONSTRUTORA LTDA, CNPJ 03.051.741/0001-90 |
    Código de Verificação 9fc25a24a (NÃO recuperável — ver teste dedicado)

Os 3 textos embutidos aqui são reais: a camada do pdfminer, o nosso OCR de
página inteira e o recorte do cabeçalho."""
import os

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_BARREIRAS


MOCK_CAMADA = (
    'i I \n'
    '\n'
    'DIIIFMoGlradlf \n'
    '\n'
    '1...-,m, \n'
    '\n'
    'TlpodeRitc:olN,MIIIO \n'
    '\n'
    'NloRalldo \n'
    '\n'
    'NOTA FISCAL DE s EFMÇOSELETRÔNICA-NFS. \n'
    'IIUNICIPIO DE BARREIRAS \n'
    '\n'
    '2llm01•a.llta•DA \n'
    '\n'
    'f11111Aac:8o M:lrmlf \n'
    '\n'
    'Loeal •  Racolhlmento \n'
    '\n'
    '2\'0Xl:01•11mà-.·BA \n'
    '\n'
    'PRESTADOR \n'
    '\n'
    '~ -2~ t t~46  \n'
    '\n'
    'WuNotaFJscal \n'
    '\n'
    '8965 \n'
    '\n'
    'Razio \n'
    '\n'
    'Soclal:CHAVESLOCACOESLTDA \n'
    'N \n'
    'omt Fantasia  LOKMAQ \n'
    'Endnço AVGnldl .a.i...a-u~RA DE MAQUINAS L TDA \n'
    '~,,..,., __,, \'122T. 0UAORA E LOTE 03 MJ 10 \n'
    'a . -\n'
    '~ras-BA-CEP. 47810-139 \n'
    'lnsaiçlo ~ con.br - Fa,e· (77)3tl\'J1..J383-C&w ~ • \n'
    '\n'
    'E.ltadull.  ,-. ..  - lnscriçlo Municipal: 000011431 - CPF/CNPJ  40.536 71~)1:22 \n'
    '\n'
    '-MlndaNobre \n'
    '\n'
    '. \n'
    '\n'
    'n--ª-\n'
    '~ Social. SAO PEDRO CONSTRUTORA L TOA \n'
    'Endereço· Rui AV. PRAIA DE PAJUSSARA \n'
    'LAURO DE FRElT AS· BA- CEP  42708720 \n'
    'E.fl\\3~  IP@saopedrocons1rutora \n'
    'lnscrlç6o Estadual·  ...... M \n'
    '\n'
    '_  1_  ~onepal·  -Celtâr (n) 98107-4727 \n'
    '\n'
    '353043-CPFICNPJ  03.051 741,0001-90 \n'
    '\n'
    '\' 55,4  QUADRA 28, LOTE og - VILAS DO A TLANTICO \n'
    '\n'
    'TOMADOR \n'
    '\n'
    '990101 - Servl\'"--r-• um a lncldancla de lSSQN t  lCMS \n'
    '\n'
    '00.00 • LOCAÇÃO DE BENS MÔVEIS \n'
    '\n'
    '_ SERVIÇO NACIONAL \n'
    '\n'
    'SERVIÇO \n'
    '\n'
    'LOCAÇAO DE ANDAIMES e ACESS  RIOS NO PE \n'
    '\n'
    'DISCRIMINAÇÃO DOS SERVIÇOS \n'
    '\n'
    'OOO DE 09/08  08I09  CONTRATO 3081/32778 \n'
    '\n'
    'PAGAMEHTO VIA BOLETO  VENCIMENTO EM 23/09/2026 \n'
    '\n'
    'OBSERVAÇÃO \n'
    '\n'
    ':--" \n'
    '\n'
    'arlo  enrique Caslro de OIIYe1ra \n'
    'Engenheiro Civil \n'
    'CREA 30.357-BA \n'
    '\n'
    'VALOR SERVIÇO  (RS} \n'
    '\n'
    'DEDUÇÕES \n'
    '\n'
    '(R$)  DESCONTO IHCONDICtONAL \n'
    '\n'
    '196,00 \n'
    '\n'
    '0,00 \n'
    '\n'
    'DEMONSTRATIVO DOS TRIBUTOS FEDERAIS \n'
    '\n'
    '(RS) \n'
    'o.oo \n'
    '\n'
    'INSS  (RS) \n'
    'º·ºº \n'
    '\n'
    'IR  (RS) \n'
    'o.ao \n'
    '\n'
    'CSU.  (R$) \n'
    '\n'
    'COFINS \n'
    '\n'
    '(R$) \n'
    '\n'
    '0,00 \n'
    '\n'
    '0,00 \n'
    '\n'
    'P1S  (R$) \n'
    '\n'
    '0,00 \n'
    '\n'
    'OUTRAS INFORMAÇÕES \n'
    '\n'
    'BASE CÃLCULO \n'
    '\n'
    '(RS) \n'
    '\n'
    '196,00 \n'
    '\n'
    'AUQUOTA  (\'l) \n'
    '\n'
    '0.00 \n'
    '\n'
    'ISS \n'
    '\n'
    '(RS) \n'
    '\n'
    '0,00 \n'
    '\n'
    'DESCONTO \n'
    'CONDICIONAL \n'
    '\n'
    '(RS) \n'
    '\n'
    'OUTRAS \n'
    'RETENÇÕES \n'
    '\n'
    '0,00 \n'
    '\n'
    '(RS) \n'
    '\n'
    '0,00 \n'
    '\n'
    'VALOR ÚQUIOO (RS) \n'
    '\n'
    '196,00 \n'
    '\n'
    'Chave de acesso Ambiente de Dados Naaonal: 29032011240536716000122260000()()08926080008845453 \n'
    '(Valor Liquido = Valor SeMço - INSS - IR - CSLL - Outras Retençõe5 -COFINS - PIS- Descontos Diversos - ISS Retido - [)eSCOflto tna,ndloonal) \n'
    'ESTE DOCUMENTO FOI EMmDO POR EMPRESA OPTANTE DO SIMPLES NACIONAL(Att. 23 da LC 123/290Gl, DEVENDO NESTA CONDIÇÃO O PRESTADOR \n'
    'INFORMAR A AÚQUOTA EIITRE 2 A 5%, CONFDRIIE TABBA DE ENQUADRAJIEIITO DO SIIIPLES NACIONAL DE ACORDO C0II O SEU FATURAIIEHTO. \n'
    '\n'
    'Consulte a autenticidade deste docUmento ecessand<> o Stle httpsJJwww.barreiras.ba.gov br/ \n'
    '\n'
    ''
)

MOCK_NOSSO_OCR = (
    'RR = mea\n'
    'Local de Prestação Local de Recolhimento\n'
    '\n'
    'Razão Social: CHAVES LOCAÇÕES LTDA\n'
    'Nome Fantasia: LOKMAQ LOCADORA DE MAQUINAS LTDA\n'
    'Enderaço: Avenida Ahylon Macedo, 2227, QUADRA E LOTE 03 AO 10 - Morada Nobre\n'
    '\n'
    'Barreiras - BA - CEP: 47810-139\n'
    '\n'
    'Inscrição Estadual: ........ - Inscrição Municipal: 000011431 - CPF/CNPJ: 40.536.716/0001-22\n'
    '\n'
    'Razão Social: SAO PEDRO CONSTRUTORA LTDA\n'
    'Endareço: Rua AV. roca beco 554, QUADRA 28, LOTE 09 - VILAS DO ATLANTICO\n'
    '\n'
    'LAURO DE FREITAS - BA - CEP:\n'
    'Ea sous con - Fone: - Celular: (77) 98107-4727\n'
    'Inscrição Estadual: ........ - Inscrição Municipal: 353043 - CPFICNPJ: 03.051.741/0001-90\n'
    '\n'
    'DISCRIMINAÇÃO DOS SERVIÇOS Z A Po\n'
    '\n'
    'arlos Henrique Castro de Oliveira\n'
    'Engenheiro Civil\n'
    'CREA 30.357-BA\n'
    '\n'
    'OBSERVAÇÃO\n'
    'PAGAMENTO VIA BOLETO. VENCIMENTO EM 23/09/2026\n'
    '\n'
    '(R$) ALÍQUOTA (%)\n'
    '\n'
    'E (R$) (R$) a (R$) a\n'
    'a 0.00\n'
    '(RS)\n'
    'O ETEXINO DOS E EETOS FEDERAIS DESCONTO, (R$) VALOR LÍQUIDO\n'
    'INSS (R$) IR (R$) COFINS (R$) PIS (R$) eu\n'
    '0,00 0,00 0,00\n'
    '\n'
    'OUTRAS ESESNCÕES\n'
    '5453\n'
    'Diversos - ISS Retido - Desconto Incondicional)\n'
    '\n'
    'DIÇÃO O PRESTADOR\n'
    '23 da LC 12312006), e OM O SEU FATURAMENTO.\n'
    '\n'
    'Nacional 290320112405367160001222600000006965\n'
    'dept DO o egos Fioaçõos COFINS - PIS - Descontos\n'
    '\n'
    'PRESA OPTANTE DO SIMPLES NACIONALIAS\n'
    'CONFORME TABELA DE ENQUADRAMENTO DO\n'
    '\n'
    ''
)

MOCK_RECUT = (
    'Cocdigo de Venicação para Autenticação WcZSa24a quis nã\n'
    '\n'
    'Endereço Bampema Baia BA 47800-340 [Rs ASS\n'
    'CNPJ 1654 AOS 000108 E mal gerecantacão Write sos(Pharreiras ba gor ix Emitido em 24/08/2026 154 45\n'
    '| Data Fato Gerador Nº da Nota Fiscal\n'
    '\n'
    '24/08/7026\n'
    'Tipo de Recolhimento Local de Prestação Local de Recolhimento 8965\n'
    '| Não Retido 2903201 - Barreiras - BA 2903201 - Barreiras - BA\n'
    'PRESTADOR\n'
    ''
)

MOCK_ENRIQUECIDO = (
    'i I \n'
    '\n'
    'DIIIFMoGlradlf \n'
    '\n'
    '1...-,m, \n'
    '\n'
    'TlpodeRitc:olN,MIIIO \n'
    '\n'
    'NloRalldo \n'
    '\n'
    'NOTA FISCAL DE s EFMÇOSELETRÔNICA-NFS. \n'
    'IIUNICIPIO DE BARREIRAS \n'
    '\n'
    '2llm01•a.llta•DA \n'
    '\n'
    'f11111Aac:8o M:lrmlf \n'
    '\n'
    'Loeal •  Racolhlmento \n'
    '\n'
    '2\'0Xl:01•11mà-.·BA \n'
    '\n'
    'PRESTADOR \n'
    '\n'
    '~ -2~ t t~46  \n'
    '\n'
    'WuNotaFJscal \n'
    '\n'
    '8965 \n'
    '\n'
    'Razio \n'
    '\n'
    'Soclal:CHAVESLOCACOESLTDA \n'
    'N \n'
    'omt Fantasia  LOKMAQ \n'
    'Endnço AVGnldl .a.i...a-u~RA DE MAQUINAS L TDA \n'
    '~,,..,., __,, \'122T. 0UAORA E LOTE 03 MJ 10 \n'
    'a . -\n'
    '~ras-BA-CEP. 47810-139 \n'
    'lnsaiçlo ~ con.br - Fa,e· (77)3tl\'J1..J383-C&w ~ • \n'
    '\n'
    'E.ltadull.  ,-. ..  - lnscriçlo Municipal: 000011431 - CPF/CNPJ  40.536 71~)1:22 \n'
    '\n'
    '-MlndaNobre \n'
    '\n'
    '. \n'
    '\n'
    'n--ª-\n'
    '~ Social. SAO PEDRO CONSTRUTORA L TOA \n'
    'Endereço· Rui AV. PRAIA DE PAJUSSARA \n'
    'LAURO DE FRElT AS· BA- CEP  42708720 \n'
    'E.fl\\3~  IP@saopedrocons1rutora \n'
    'lnscrlç6o Estadual·  ...... M \n'
    '\n'
    '_  1_  ~onepal·  -Celtâr (n) 98107-4727 \n'
    '\n'
    '353043-CPFICNPJ  03.051 741,0001-90 \n'
    '\n'
    '\' 55,4  QUADRA 28, LOTE og - VILAS DO A TLANTICO \n'
    '\n'
    'TOMADOR \n'
    '\n'
    '990101 - Servl\'"--r-• um a lncldancla de lSSQN t  lCMS \n'
    '\n'
    '00.00 • LOCAÇÃO DE BENS MÔVEIS \n'
    '\n'
    '_ SERVIÇO NACIONAL \n'
    '\n'
    'SERVIÇO \n'
    '\n'
    'LOCAÇAO DE ANDAIMES e ACESS  RIOS NO PE \n'
    '\n'
    'DISCRIMINAÇÃO DOS SERVIÇOS \n'
    '\n'
    'OOO DE 09/08  08I09  CONTRATO 3081/32778 \n'
    '\n'
    'PAGAMEHTO VIA BOLETO  VENCIMENTO EM 23/09/2026 \n'
    '\n'
    'OBSERVAÇÃO \n'
    '\n'
    ':--" \n'
    '\n'
    'arlo  enrique Caslro de OIIYe1ra \n'
    'Engenheiro Civil \n'
    'CREA 30.357-BA \n'
    '\n'
    'VALOR SERVIÇO  (RS} \n'
    '\n'
    'DEDUÇÕES \n'
    '\n'
    '(R$)  DESCONTO IHCONDICtONAL \n'
    '\n'
    '196,00 \n'
    '\n'
    '0,00 \n'
    '\n'
    'DEMONSTRATIVO DOS TRIBUTOS FEDERAIS \n'
    '\n'
    '(RS) \n'
    'o.oo \n'
    '\n'
    'INSS  (RS) \n'
    'º·ºº \n'
    '\n'
    'IR  (RS) \n'
    'o.ao \n'
    '\n'
    'CSU.  (R$) \n'
    '\n'
    'COFINS \n'
    '\n'
    '(R$) \n'
    '\n'
    '0,00 \n'
    '\n'
    '0,00 \n'
    '\n'
    'P1S  (R$) \n'
    '\n'
    '0,00 \n'
    '\n'
    'OUTRAS INFORMAÇÕES \n'
    '\n'
    'BASE CÃLCULO \n'
    '\n'
    '(RS) \n'
    '\n'
    '196,00 \n'
    '\n'
    'AUQUOTA  (\'l) \n'
    '\n'
    '0.00 \n'
    '\n'
    'ISS \n'
    '\n'
    '(RS) \n'
    '\n'
    '0,00 \n'
    '\n'
    'DESCONTO \n'
    'CONDICIONAL \n'
    '\n'
    '(RS) \n'
    '\n'
    'OUTRAS \n'
    'RETENÇÕES \n'
    '\n'
    '0,00 \n'
    '\n'
    '(RS) \n'
    '\n'
    '0,00 \n'
    '\n'
    'VALOR ÚQUIOO (RS) \n'
    '\n'
    '196,00 \n'
    '\n'
    'Chave de acesso Ambiente de Dados Naaonal: 29032011240536716000122260000()()08926080008845453 \n'
    '(Valor Liquido = Valor SeMço - INSS - IR - CSLL - Outras Retençõe5 -COFINS - PIS- Descontos Diversos - ISS Retido - [)eSCOflto tna,ndloonal) \n'
    'ESTE DOCUMENTO FOI EMmDO POR EMPRESA OPTANTE DO SIMPLES NACIONAL(Att. 23 da LC 123/290Gl, DEVENDO NESTA CONDIÇÃO O PRESTADOR \n'
    'INFORMAR A AÚQUOTA EIITRE 2 A 5%, CONFDRIIE TABBA DE ENQUADRAJIEIITO DO SIIIPLES NACIONAL DE ACORDO C0II O SEU FATURAIIEHTO. \n'
    '\n'
    'Consulte a autenticidade deste docUmento ecessand<> o Stle httpsJJwww.barreiras.ba.gov br/ \n'
    '\n'
    '\n'
    'BARR_PREST_RS: CHAVES LOCAÇÕES LTDA\n'
    'BARR_PREST_CNPJ: 40536716000122\n'
    'BARR_PREST_CIDADE: Barreiras - BA - CEP: 47810139\n'
    'BARR_TOM_RS: SAO PEDRO CONSTRUTORA LTDA\n'
    'BARR_TOM_CNPJ: 03051741000190\n'
    'BARR_TOM_CIDADE: LAURO DE FREITAS - BA - CEP: \n'
    'BARR_NUMERO: 8965\n'
    'BARR_DATA_FG: 24/08/2026'
)



def _novo(texto):
    dummy = "tests/dummy_barreiras_nfsss_p4.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy, "wb") as f:
        f.write(b"%PDF-1.4")
    ex = SPPdfExtractor(dummy)
    ex.raw_text = texto
    ex.from_ocr = False
    return ex, dummy


def _parse(texto):
    ex, dummy = _novo(texto)
    try:
        return ex, ex.parse()
    finally:
        os.remove(dummy)


# --------------------------------------------------------------------------
# Detecção — a assimetria entre os dois detectores
# --------------------------------------------------------------------------
def test_pagina_e_barreiras_e_nao_danfse_nacional():
    """`_detect_layout_page` é quem decide num lote, e estava com 2 marcas
    contra as 3 de `_detect_layout`. Sem marca municipal casando, a página caía
    no check largo de "Chave de Acesso" e era parseada como DANFSe Nacional."""
    ex, dummy = _novo(MOCK_CAMADA)
    try:
        assert ex._detect_layout_page(MOCK_CAMADA) == LAYOUT_BARREIRAS
        assert ex._detect_layout() == LAYOUT_BARREIRAS
    finally:
        os.remove(dummy)


def test_as_duas_marcas_antigas_estao_destruidas_nesta_camada():
    """Trava a premissa: é justamente por NÃO ter nenhuma das duas marcas
    antigas legíveis que esta página era roteada errado. O que sobrevive é o
    rodapé do domínio oficial — e SEM o ".br", porque o OCR leu
    "barreiras.ba.gov br" com espaço no lugar do ponto."""
    import re
    assert not re.search(r'MUNIC[IÍ]PIO\s+DE\s+BARREIRAS', MOCK_CAMADA, re.I)
    assert not re.search(r'Data\s+Fato\s+Gerador', MOCK_CAMADA, re.I)
    assert 'IIUNICIPIO DE BARREIRAS' in MOCK_CAMADA
    assert not re.search(r'barreiras\.ba\.gov\.br', MOCK_CAMADA, re.I)
    assert re.search(r'barreiras\.ba\.gov', MOCK_CAMADA, re.I)


# --------------------------------------------------------------------------
# Valores — o que o usuário viu zerado
# --------------------------------------------------------------------------
def test_valor_recuperado_da_camada_embutida():
    """R$196,00. A grade sobrevive na camada de terceiros (é o nosso OCR que a
    perde nesta página), então basta a detecção acertar."""
    _, nfse = _parse(MOCK_CAMADA)
    v = nfse.valores
    assert v.valor_servicos == pytest.approx(196.00)
    assert v.base_calculo == pytest.approx(196.00)
    assert v.valor_liquido_nfse == pytest.approx(196.00)


def test_iss_zero_do_simples_nao_e_fabricado():
    """"Simples: Optante", "Tipo de Recolhimento: Não Retido" — alíquota 0.00 e
    ISS 0,00 são dado REAL, conferidos na imagem. Derivar qualquer coisa aqui
    inventaria imposto."""
    _, nfse = _parse(MOCK_CAMADA)
    assert nfse.valores.aliquota == pytest.approx(0.0)
    assert nfse.valores.valor_iss == pytest.approx(0.0)


# --------------------------------------------------------------------------
# Entidades — o erro mais grave do XML
# --------------------------------------------------------------------------
def test_prestador_nao_recebe_o_cnpj_do_tomador():
    """O XML trazia `<Cnpj>03051741000190</Cnpj>` no PRESTADOR — que é o CNPJ
    do TOMADOR — e a razão social `~ -2~ t t~46`."""
    _, nfse = _parse(MOCK_ENRIQUECIDO)
    assert nfse.prestador.cnpj_cpf == "40536716000122"
    assert nfse.tomador.cnpj_cpf == "03051741000190"
    assert nfse.prestador.cnpj_cpf != nfse.tomador.cnpj_cpf
    assert "CHAVES" in nfse.prestador.razao_social.upper()
    assert "SAO PEDRO" in nfse.tomador.razao_social.upper()


def test_municipios_das_duas_entidades():
    _, nfse = _parse(MOCK_ENRIQUECIDO)
    assert nfse.prestador.endereco.codigo_municipio == "2903201"
    assert nfse.tomador.endereco.codigo_municipio == "2919207"


def test_marcadores_de_entidade_saem_do_nosso_ocr():
    """A fonte das entidades é o NOSSO OCR, não a camada: nela os rótulos estão
    destruídos ("Razio Soclal:", "~ Social.") e não há o que ancorar."""
    import re
    assert len(re.findall(r'Raz[ãa]o\s+Social\s*:', MOCK_CAMADA, re.I)) == 0
    assert len(re.findall(r'Raz[ãa]o\s+Social\s*:', MOCK_NOSSO_OCR, re.I)) == 2

    ex, dummy = _novo(MOCK_CAMADA)
    try:
        marc = ex._marcadores_entidades_barreiras(MOCK_NOSSO_OCR)
    finally:
        os.remove(dummy)
    assert "BARR_PREST_CNPJ: 40536716000122" in marc
    assert "BARR_TOM_CNPJ: 03051741000190" in marc
    assert marc.index("BARR_PREST_RS:") < marc.index("BARR_TOM_RS:")


def test_cnpj_com_digito_corrompido_nao_vira_marcador():
    """Cada CNPJ passa pelo dígito verificador antes de virar marcador — sem
    isso um dígito comido pelo OCR viraria um CNPJ plausível e errado, que é
    exatamente a classe de bug já vista em Salvador/GUARAJUBA."""
    mutado = MOCK_NOSSO_OCR.replace("40.536.716/0001-22", "40.536.717/0001-22")
    assert mutado != MOCK_NOSSO_OCR
    ex, dummy = _novo(MOCK_CAMADA)
    try:
        marc = ex._marcadores_entidades_barreiras(mutado)
    finally:
        os.remove(dummy)
    assert "BARR_PREST_CNPJ:" not in marc
    assert "BARR_PREST_RS:" in marc  # a razão social continua válida


# --------------------------------------------------------------------------
# Número e data — o recorte do cabeçalho
# --------------------------------------------------------------------------
def test_numero_8965():
    _, nfse = _parse(MOCK_ENRIQUECIDO)
    assert nfse.numero == "8965"
    assert nfse.numero != "00000000"


def test_data_real_em_vez_do_instante_da_conversao():
    _, nfse = _parse(MOCK_ENRIQUECIDO)
    assert nfse.data_emissao.strftime("%d/%m/%Y") == "24/08/2026"


def test_numero_exige_concordancia_entre_as_duas_fontes():
    """O número só vira marcador quando a camada embutida (ancorada no rótulo
    corrompido "WuNotaFJscal") e o recorte do cabeçalho leem o MESMO token —
    duas passagens independentes sobre a mesma tinta. Sem isso, uma leitura só
    viraria número da nota."""
    marc = SPPdfExtractor._marcadores_cabecalho_barreiras(MOCK_CAMADA, MOCK_RECUT)
    assert "BARR_NUMERO: 8965" in marc

    recut_sem_numero = MOCK_RECUT.replace("8965", "1234")
    marc2 = SPPdfExtractor._marcadores_cabecalho_barreiras(MOCK_CAMADA, recut_sem_numero)
    assert "BARR_NUMERO:" not in marc2


def test_data_exige_dia_e_mes_repetidos_no_recorte():
    """O recorte lê a data duas vezes ("Emitido em 24/08/2026" e "Data Fato
    Gerador 24/08/7026" — o ano de uma delas sai corrompido). Aceita-se o
    dia/mês que se repete, com o ano da leitura plausível."""
    marc = SPPdfExtractor._marcadores_cabecalho_barreiras(MOCK_CAMADA, MOCK_RECUT)
    assert "BARR_DATA_FG: 24/08/2026" in marc

    uma_so = "Emitido em 24/08/2026 e nada mais 8965"
    marc2 = SPPdfExtractor._marcadores_cabecalho_barreiras(MOCK_CAMADA, uma_so)
    assert "BARR_DATA_FG:" not in marc2


def test_chave_corrompida_nao_e_usada():
    """O OCR de terceiros comeu dígitos da chave ("260000()()0892"), que sai com
    48 dígitos em vez de 50. Ela precisa REPROVAR a validação estrutural em vez
    de devolver um número decodificado errado — é por isso que o número e a
    data desta página vêm do recorte, e não dela."""
    ex, dummy = _novo(MOCK_ENRIQUECIDO)
    try:
        ex.layout = LAYOUT_BARREIRAS
        assert ex._chave_barreiras() is None
    finally:
        os.remove(dummy)
    assert "()()" in MOCK_CAMADA


def test_codigo_de_verificacao_nao_e_chutado():
    """O código impresso é "9fc25a24a" e NÃO é recuperável: o recorte devolve
    leituras diferentes a cada tentativa ("WcZSa24a", "Hc25a24a", "9c25aZ4a").
    Sentinela + aviso, nunca um dos chutes."""
    _, nfse = _parse(MOCK_ENRIQUECIDO)
    assert nfse.codigo_verificacao == "XXXX-XXXX"
    assert any("digo de verifica" in a.lower() or "autenticidade" in a.lower()
               for a in nfse.avisos)


# --------------------------------------------------------------------------
# Portão do resgate
# --------------------------------------------------------------------------
def test_resgate_so_entra_quando_os_rotulos_estao_destruidos():
    """Portão por conteúdo: as duas linhas "Razão Social:" que todo documento
    deste template imprime. Medido no lote: dispara nas págs. 3 e 4 (rótulos
    destruídos) e não nas 1 e 2. Uma página sadia não paga o custo de um OCR
    extra nem corre risco de mudança."""
    sadia = ("MUNICIPIO DE BARREIRAS\nRazão Social: FULANO LTDA\n"
             "Razão Social: BELTRANO LTDA\n")
    ex, dummy = _novo(sadia)
    try:
        assert ex._resgate_barreiras_ocr_terceiros(0, sadia) == sadia
    finally:
        os.remove(dummy)


def test_marcadores_nao_reintroduzem_separador_de_bloco():
    """Os marcadores não podem conter as marcas que `is_new_invoice` usa para
    fatiar notas (`MUNICIPIO`, `Chave de acesso`, `Nº da Nota Fiscal`) — foi
    essa armadilha que, no lote anterior de Barreiras, transformou 6 notas em
    5. Mesma razão de serem sintéticos."""
    import re
    extra = MOCK_ENRIQUECIDO[len(MOCK_CAMADA):]
    assert extra.strip()
    assert not re.search(r'MUNIC[IÍ]PIO|Chave\s+de\s+acesso|N[ºo°]\s*da\s+Nota',
                         extra, re.IGNORECASE)
