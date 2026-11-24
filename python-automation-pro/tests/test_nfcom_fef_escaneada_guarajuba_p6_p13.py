# -*- coding: utf-8 -*-
r"""NFCom (DANFE-COM) ESCANEADA do Grupo FeF (F&F Comunicações, CNPJ
13.398.812/0001-89) -> Guarajuba Shopping Ltda, layout `telecom_comunicacao`:
páginas 6 (nota nº 26097) e 13 (nota nº 32934) do lote "GUARAJUBA MALLS -
NFSe.pdf". Texto REAL do OCR (Tesseract) da página inteira, na ordem em que
`_ocr_page` o devolve: recortes prependados + leitura 6x + leitura 3x.

Impresso nas duas notas: VALOR TOTAL NF 119,90 (itens 23,98 + 95,92), tomador
"Guarajuba Shopping Ltda" (CNPJ 24.890.395/0001-03), itens
"FeF_ULTRA_120_MEGA" e "Servico de Telecomunicacoes Top Full", chaves
2926 0613 3988 1200 0189 6200 1000 0260 9710 3041 9010 (nº 26097) e
2926 0813 3988 1200 0189 6200 1000 0329 3410 1636 4338 (nº 32934).

Antes da correção:
1. **Valor 8.057,28 / 47.976,00**: "VALOR TOTAL NF | 119,90]" (a borda da
   célula lida como "|") não casava no fallback de "VALOR TOTAL NF" e o valor
   caía na soma das linhas de item, com a vírgula perdida pelo OCR:
   "UN 2398 3,36" -> 2398 x 3,36 = 8.057,28 (pág. 6); "UN 1 23988" (nas 2
   cópias do texto) -> 2 x 23.988,00 = 47.976,00 (pág. 13).
2. **Chave da pág. 6 = sentinela "TELECOM"**: "CHAVE DE ACESSO:" seguido de
   linha vazia nas 2 leituras de página inteira. O recorte do bloco de
   identificação (`_ocr_recut_identificacao_telecom`) só disparava sem
   "NOTA FISCAL Nº"; agora dispara também sem chave válida no texto, e só é
   aproveitado se a chave do recorte fechar o DV mod-11.
3. **Tomador da pág. 13 = URL de consulta**: o QR Code lido como "[m]" colado
   no fim da linha do nome ("Guarajuba Shopping Ltda 1: [m]") derrubava a
   linha na guarda de dígitos.
4. **Discriminação "ia de Telecomunicacoes Top" / "E de ..."**: a 1ª palavra
   do 2º item é comida pelo OCR de página inteira; um recorte só da coluna de
   descrição (`_ocr_recut_descricao_itens_telecom`) traz a linha inteira.
"""
import os

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor

PDF_REAL = r"L:\USUARIOS\ANDERSON\ARQUIVOS DESKTOP\Notas\GUARAJUBA MALLS - NFSe.pdf"
CHAVE_P6 = "29260613398812000189620010000260971030419010"
CHAVE_P13 = "29260813398812000189620010000329341016364338"

DESCRICAO_P6 = r'''ITENS DA FATURA (recorte da coluna de descrição)
FeF ULTRA 120 MEGA
Servico de Telecomunicacoes Top
Full
FIM DO RECORTE DA DESCRIÇÃO DOS ITENS'''

IDENTIFICACAO_P6 = r'''NOTA FISCAL Nº 26097 - SÉRIE: 1
* DATA DE EMISSÃO: 16/06/2026

CONSULTE PELA CHAVE DE ACESSO EM:
1 https://dfe-portal.svrs.rs.gov.br/nfcom/consulta

CHAVE DE ACESSO:

= 2926 0613 3988 1200 0189 6200 1000 0260 9710 3041 9010
Protocolo de autorização:
3292600153228205 - 16/06/2026 às 16:27:58

meme

tra AMaALTPRIRI AIR.
'''

PAGINA_P6 = r'''ra pena 00 A Ma a a e oa arts rms

DOCUMENTO AUXILIAR DA NOTA FISCAL DE FATURA DE SERVIÇO DE E COMUNICAÇÃO E ELETRÔNICA

Grupo FeF

Rua Senhor do Bonfim 544 Monte Gordo 42839852 Camacari - BA

(71) 4062-8609
13.398.812/0001-89
019.192.620

Guarajuba Shopping Ltda

Guarajuba Shopping 01 Guarajuba 42840310
Camacari - BA

CNPJ/CPF: 24.890.395/0001-03
INSCRIÇÃO ESTADUAL:
CÓD. DO CLIENTE: 2173
Nº TELEFONE: (71) 98149-5491
PERÍODO:

15/06/2026 á 14/07/2026

oem cenas coroas imetecasccoes seno asa miar AUDIO IMG ABOMNRG0 HU 060 ADONMNCR A CORE VA errar avo tr400 p csE pr 000 man eat Eae 00 OC orra ba remç vb eva reecenencemvoriestracnnr e coneesevessenoesr cnc rcereencseemenços

E: NOTA FISCAL Nº 26097 - SÉRIE: 1
* DATA DE EMISSÃO: 16/06/2026

CONSULTE PELA CHAVE DE ACESSO EM:

Protocolo de autorização:
3292600153228205 - 16/06/2026 às 16:27:58

armam asa pon

reasons vista rr e neegeremagraomano oronaeert

ÁREA CONTRIBUINTE:

| | VALOR VALOR VALOR | | PIS/COFINS VALOR |
ITENS DA FATURA cCinsã | UN | QUANT | unit (R$) | DESC. (R$) TOTAL(R$)| (R$) |
'FeF ULTRA 120 MEGA 0100201 UN 2398 3,36 |
ia de Telecomunicacoes Top 0600601 1 | UN | 95,92 0.00]
VALOR TOTAL NF | 119,90] | | INFORMAÇÃO DOS TRIBUTOS DO RESERVADO AO FISCO À E PERA
7 | TRIBUTO
TOTAL BASE DE CÁLCULO ] 16,98 | pisa:
VALOR ICMS | 9,96] [rmrmeen
VALOR ISENTO | 0, 00 | FUST |
| |- í ie Sb |
VALOR OUTROS | 0,00) TF FUNTTEL |
enem O A e tr sr a Tm
|

ID titulo referencia - 643601

O O att, A ear

ER rp a o a eccrmpecag cara mipeemnemgmam em rsrs crença sam or

* INFORMAÇÕES COMPLEMENTARES

eira ear si to esa

|
|
|
|

rara PRE 1

ÁREA DO CONTRIBUINTE E SERRANA ÇÕES DA ANATEL

er pa re prt a de te ams tr meire nt re cestas tomasse eneaç rs

Linha digitável

00000.00000 00000.000000 00000.000000 O 00000000000000

rev OMbIm RG von nc rim rp rm rr pe Map

Nº idorulicádor am débito automático

ONA VN nr rs a OO OA pOr

O

VON ar e nt ra pp press enc ana,

Avisos Regulatórios

1. Esta fatura é emitida conforme a Resolução ANATEL nº 765/2023.

2. Você pode contestar valores cobrados sem custo e receber resposta em até 30 dias.

3. Central de Atendimento do ISP (71) 4062-8609 e WhatsApp (71) 4062-8609.

4. Central de Atendimento da ANATEL: 1331 (ligação gratuita).

5. Fatura emitida com antecedência mínima de 5 dias do vencimento.

6. Dados pessoais tratados conforme LGPD - Lei nº 13.709/2018.

7. O não pagamento poderá acarretar suspensão do serviço, conforme regras da ANATEL,

nro par RS rir mi Orerr tempra pras nm rr nr cem rompem somam mrmmmssenço

Direito de contestação da cobrança

Você pode contestar valores desta fatura sem custo.

Entre em contato com nossa Central de Atendimento: Telefone (71) 4062-8609 e
WhatsApp (71) 4062-8609, ou pelo e-mail: financeiro O ffcomunicacoes.net.br.

A análise será concluída em até 30 dias, conforme a regra da ANATEL.
Enquanto sua contestação estiver em andamento, o serviço não será suspenso.

A e rir ris e rar e err na sr cs as nt al VON cit ini rr ari vir

é
Wma cr

]
E

2

DOCUMENTO AUXILIAR DA NOTA FISCAL DE FATURA DE SERVIÇO DE COMUNICAÇÃO ELETRÔNICA

Grupo FeF

Rua Senhor do Bonfim 544 Monte Gordo 42839852 Camacari - BA
(71) 4062-8609

13.398.812/0001-89

019.192.620

[m] NOTA FISCAL Nº 26097 - SÉRIE: 1
da” DATA DE EMISSÃO: 16/06/2026

trai CONSULTE PELA CHAVE DE ACESSO EM:
El
pe 7

Guarajuba Shopping Ltda

Guarajuba Shopping 01 Guarajuba 42840310
Camacari - BA

CNPJ/CPF: 24.890.395/0001-03
INSCRIÇÃO ESTADUAL:

CÓD. DO CLIENTE: 2173

Nº TELEFONE: (71) 98149-5491

PERÍODO: 15/06/2026 á 14/07/2026

https://dfe-portal.svrs.rs.gov.br/nfcom/consulta
CHAVE DE ACESSO:

Protocolo de autorização:
à 3292600153228205 - 16/06/2026 às 16:27:58

ÁREA CONTRIBUINTE: E

[ ” Ro RETA] 7
Ed VALOR | VALOR | VALOR | VALOR |PISICOFINS| BCICMS | ALÍQ | VALOR |
ITENS DA FATURA cassa a QUANT | UNIT (R$) | DESC. (R$) | ACR.(R$) | TOTAL(R$)| (R$) (R$) (6) | ICMS (RS) |
FeF. ULTRA 120 MEGA 0100201 | U Lo 2398) 0,00 0,00) 23,98 222) 16,38] 20.50 3,36 |
Eu Ja E E ra 000) dia MRI
1 i |
Esrtiaia de Telecomunicações Top | ssonggy | UN A 95,92 0,00 0,00 95,92 000] 000/ 0.00 0.00
z E E A SEEN fo UR, rota e De E ii dE e
VALOR TOTAL NF | 119,90 | | INFORMAÇÃO DOS TRIBUTOS | E RESERVADO AO FISCO
po “| TRIBUTO VALOR
TOTAL BASE DE CÁLCULO | Ages ps)
cm. PIS 0,40
L | Fies
e ad ço sa "| COFINS 1,82
VALOR ISENTO | 000) [FUST O [o
Í E ES EE
VALOR OUTROS | 0,00, | FUNTTEL 0,00
À a E ed mm nm
o INFORMAÇÕES COMPLEMENTARES
ID titulo referencia - 643601 E é ii

Linha digitável

00000.00000 00000.000000 00000.000000 0 00000000000000 -

1
|
1]
|]
|
]
|
|
|
|]
|
]

Avisos Regulatórios Direito de contestação da cobrança

1. Esta fatura é emitida conforme a Resolução ANATEL nº 765/2023. Você pode contestar valores desta fatura sem custo.

2. Você pode contestar valores cobrados sem custo e roceber resposta em até 30 dias. Entre em contato com nossa Central de Atendimento: Telefone (71) 4062-8609 e
3. Central de Atendimento do ISP (71) 4062-8609 e WhatsApp (71) 4062-8609. WihatsApp (71) 4062-8609, ou pelo e-mail: financeiro O ffcomunicacoes.net.br.

4. Central de Atendimento da ANATEL: 1331 (ligação gratuita). A análise será concluída em até 30 dias, conforme a regra da ANATEL.

5. Fatura emitida com antecedência mínima de 5 dias do vencimento. Enquanto sua contestação estiver em andamento, o serviço não será suspenso.

6. Dados pessoais tratados conforme LGPD - Lei nº 13.709/2018.
7. O não pagamento poderá acarretar suspensão do serviço, conforme regras da ANATEL.

res pe  ,

'''

DESCRICAO_P13 = r'''ITENS DA FATURA (recorte da coluna de descrição)
FeF ULTRA 120 MEGA
Servico de Telecomunicacoes Top
Full
FIM DO RECORTE DA DESCRIÇÃO DOS ITENS'''

PAGINA_P13 = r'''DOCUMENTO AUXILIAR DA

=», Grupo FeF

4 * Rua Senhor do Bonfim 544 Monte
(71) 4062-8609
13.398.812/0001-89

019.192.620

Guarajuba Shopping Ltda

Guarajuba Shopping 01 Guarajuba 42840310
Camacari - BA

CNPJ/CPF: 24.890.395/0001-03
INSCRIÇÃO ESTADUAL:

CÓD. DO CLIENTE: 2173

Nº TELEFONE: (71) 98149-5491

PERÍODO: 15/08/2026 á 14/09/2026

| Nº do Contrato: 2173

VALOR VALOR VALOR

| MR RT cClass , UN QUANT, uNT(A$) DESC.(R$) ACR.(R$) TOTAL(RS) (R$) | (R$) | (%)

|FeF. ULTRA. 120 MEGA 0100201 UN 1 23988 000 000. 23,98 222) 16,38! 2050

Servico de Telecomunioacoes To oggogo1 UNI 1 | 9582, 000, 000) 9582 000] 000, 000
red 44900" | INFORMAÇÃO DOS TRIBUTOS | | RESERVADO AO FISCO

VALOR TOTAL NF | 119,90 | INFOR! AG no | ab da É ci

pecar [TRIBUTO | VALOR ||

TOTAL BASE DE CÁLCULO | 16,08) Eis ala did citas ge |

'VALOR ICMS 3,36 | fre mememeda x

ças iai Ah “8. COFINS | 1,82

VALOR ISENTO 0,00 'FUST 011!

VALOR OUTROS 0,00 FUNTTEL 0,00

| INFORM
“OD titulo referencia - 643603

|

ÁREA DO CONTRIBUINTE E DETERMINAÇÕES DA ANATEL

: Linha digitável

em a arte Ne a vas

Avisos Regulatórios

1. Esta fatura é emitida conforme a Resolução ANATEL nº 765/2028.
2. Você pode contestar valores cobrados sem custo e receber resposta em até 30 dias.
3. Central de Atendimento do ISP (71) 4062-8609 e WhatsApp (71) 4062-8609.
| 4, Central de Atendimento da ANATEL: 1331 (ligação gratuita).
5. Fatura emitida com untecedência minima de 5 dias do vencimento.
6. Dados pessoais tratados conforme LGPD - Lei nº 13.709/2018.
7

NOTA FISCAL DE FATURA DE SERVIÇO DE CO
Gordo 42839852 Camacari - BA
NOTA FISCAL Nº 32934 - SÉRIE: 1

DATA DE EMISSÃO: 19/08/2026

CONSULTE PELA CHAVE DE ACESSO EM:
https://dfe-portal.svrs.rs.gov.br/nfcom/consulta

CHAVE DE ACESSO:

Protocolo de autorização:
3292600218321832 - 19/08/2026 às 15:55:34

ÁREA CONTRIBUINTE:

VALOR PIS/COFINS BCICMS | ALÍQ

AÇÕES COMPLEMENTARES

| Nº Identificador de débito automático

00000.00000 00000.000000 00000.000000 O 00000000000000 | |. |

Direito de contestação da cobrança

Você pode contestar valores desta fatura sem custo.

Entre em contato com nossa Central de Atendimento: Telefone (71) 4062-8609 e
WhatsApp (71) 4062-8609, ou pelo e-mail: financeiro O ffcomunicacoes.net.br.

A análise será concluída em até 30 dias, conforme a regra da ANATEL.
Enquanto sua contestação estiver em andamento, o serviço não será susponso.

. O não pagamento poderá acarretar suspensão do serviço, conforme regras da ANATEL.

MUNICAÇÃO ELETRÔNICA

]
!
|

2926 0813 3988 1200 0189 6200 1000 0329 3410 1636 4338

—
|

|

|

|

|

=

|

|

VALOR |

| ICMS (R$) |
| a
ml
0.00 |

|

|

|

|

|

|

a

|

|]

|]

|

|

|

|

DOCUMENTO AUXILIAR DA NOTA FISCAL DE FATURA DE SERVIÇO DE COMUNICAÇÃO ELETRÔNICA

Grupo FeF

Rua Senhor do Bonfim 544 Monte Gordo 42839852 Camacari - BA
(71) 4062-8609

13.398.812/0001-89

019.192.620

NOTA FISCAL Nº 32934 - SÉRIE: 1
DATA DE EMISSÃO: 19/08/2026

CONSULTE PELA CHAVE DE ACESSO EM:
https://dfe-portal.svrs.rs.gov.br/nfcom/consulta

CHAVE DE ACESSO:
2926 0813 3988 1200 0189 6200 1000 0329 3410 1636 4338

Protocolo de autorização:
3292600218321832 - 19/08/2026 às 15:55:34

Guarajuba Shopping Ltda 1: [m]

”

Guarajuba Shopping 01 Guarajuba 42840310
Camacari - BA

CNPJ/CPF: 24.890.395/0001-03
INSCRIÇÃO ESTADUAL:

CÓD. DO CLIENTE: 2173

Nº TELEFONE: (71) 98149-5491

PERÍODO: 15/08/2026 á 14/09/2026

ÁREA CONTRIBUINTE: |

Nº do Contrato: 2173

VALOR VALOR VALOR VALOR PIS/COFINS | BCICMS | ALÍQ | VALOR

ITENS DA FATURA cClass | UN QUANT UNIT (R$) DESC. (R$) ACR.(R$) TOTAL (R$) (R$) (R9 (%) | ICMS (R$) '
FoF ULTRA 120 MEGA 0100201 UN 1 23988 0,00 000 2398 222] 16,38| 2050 | |
E de Telecomunicacoes Top 0600601 UN! 1 95,92. 0,00, 0,00: 95,92 0,00 | 0.00, 0.00 | |
“VALOR TOTAL NF | 119,90 | INFORMAÇÃO DOS TRIBUTOS | RESERVADO AO FISCO |
a = nm 1 | TRIBUTO | VALOR |
TOTAL BASE DE CÁLCULO | 16,38! | Pó SE Cie | |
ga - -— APIS | 0,40, |

: VALOR ICMS 3,36 “ E )
Z ; tino | COFINS | 1,82) | |)
VALOR ISENTO | 0,00 FUST 0,11 ! |
VALOR OUTROS 0,00 FUNTTEL 0,00 |

INFORMAÇÕES COMPLEMENTARES
ID titulo referencia - 643603

j |

ÁREA DO CONTRIBUINTE E DETERMINAÇÕES DA ANATEL

: Linha digitável * | Nº Identificador de débito automático
1 00000.00000 00000.000000 00000.000000 O 00000000000000 | | - |
|
|
|
Í
|
|)
. '

Avisos Regulatórios Direito de contestação da cobrança

1. Esta fatura é emitida conforme a Resolução ANATEL nº 765/2023. Você pode contestar valores desta fatura sem custo. i
2. Você pode contestar valores cobrados sem custo e receber resposta em até 30 dias. Entre em contato com nossa Central de Atendimento: Telefone (71) 4062-8609 e f
3. Central de Atendimento do ISP (71) 4062-8609 e WhatsApp (71) 4062-8609. WhatsApp (71) 4062-8609, ou pelo e-mail: financeiro O ffcomunicacoes.net.br. |
4. Central de Atendimento da ANATEL: 1331 (ligação gratuita). A análise será concluída em até 30 dias, conforme a regra da ANATEL. i
5. Fatura emitida com antecedência minima de 5 dias do vencimento. Enquanto sua contestação estiver em andamento, o serviço não será suspenso. |

6. Dados pessoais tratados conforme LGPD - Lei nº 13.709/2018. |
7. O não pagamento poderá acarretar suspensão do serviço, conforme regras da ANATEL.
'''

OCR_P6 = DESCRICAO_P6 + "\n" + IDENTIFICACAO_P6 + "\n" + PAGINA_P6
OCR_P13 = DESCRICAO_P13 + "\n" + PAGINA_P13


def _converter(monkeypatch, tmp_path, texto):
    pdf = tmp_path / "dummy_nfcom_fef_guarajuba.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: texto)
    notas = SPPdfExtractor(str(pdf)).parse_multiple()
    assert len(notas) == 1
    return notas[0]


@pytest.fixture(params=[(6, "26097", CHAVE_P6, "2026-06-16"), (13, "32934", CHAVE_P13, "2026-08-19")],
                ids=["pag6_nf26097", "pag13_nf32934"])
def caso(request, monkeypatch, tmp_path):
    pagina, numero, chave, emissao = request.param
    texto = OCR_P6 if pagina == 6 else OCR_P13
    return _converter(monkeypatch, tmp_path, texto), numero, chave, emissao


def test_numero_e_data(caso):
    nota, numero, _, emissao = caso
    assert nota.numero == numero
    assert nota.data_emissao.strftime("%Y-%m-%d") == emissao


def test_valor_e_o_valor_total_nf_impresso(caso):
    nota = caso[0]
    v = nota.valores
    assert v.valor_servicos == pytest.approx(119.90)
    assert v.valor_liquido_nfse == pytest.approx(119.90)
    # Convenção do layout: sem BC ICMS legível, a base reflete o valor total;
    # ISS zerado (NFCom é ICMS) e PIS/COFINS não são retenções.
    assert v.base_calculo == pytest.approx(119.90)
    assert v.valor_iss == 0.0
    assert v.valor_pis == 0.0
    assert v.valor_cofins == 0.0


def test_codigo_verificacao_e_a_chave_com_dv(caso):
    nota, _, chave, _ = caso
    assert nota.codigo_verificacao == chave
    assert SPPdfExtractor._dv_chave_nfe(chave[:43]) == chave[43]


def test_partes(caso):
    nota = caso[0]
    assert nota.prestador.cnpj_cpf == "13398812000189"
    assert nota.prestador.razao_social == "Grupo FeF"
    assert nota.tomador.cnpj_cpf == "24890395000103"
    assert nota.tomador.razao_social == "Guarajuba Shopping Ltda"


def test_discriminacao_limpa(caso):
    assert caso[0].discriminacao == "FeF ULTRA 120 MEGA | Servico de Telecomunicacoes Top | Full"


def test_aviso_nfcom_icms(caso):
    assert any("Documento tributado por ICMS (NFCom" in a for a in caso[0].avisos)
    assert not any("zero" in a for a in caso[0].avisos)


# --- portões dos recortes (dentro de `_ocr_page`) ---------------------------------

def test_sem_recorte_a_chave_da_pag6_nao_existe_no_texto():
    # Portão do recorte de identificação: nenhuma chave válida na leitura de
    # página inteira; o recorte traz a chave que fecha o DV.
    assert SPPdfExtractor._localizar_chave_nfcom(PAGINA_P6) is None
    assert SPPdfExtractor._localizar_chave_nfcom(IDENTIFICACAO_P6) == (CHAVE_P6, True)


def test_pag13_ja_tem_chave_e_nao_dispara_o_recorte_de_identificacao():
    assert SPPdfExtractor._localizar_chave_nfcom(PAGINA_P13) == (CHAVE_P13, True)


@pytest.mark.parametrize("pagina", [PAGINA_P6, PAGINA_P13], ids=["pag6", "pag13"])
def test_descricao_truncada_dispara_o_recorte_da_coluna(pagina):
    assert SPPdfExtractor._descricao_itens_telecom_truncada(pagina)


@pytest.mark.parametrize("bloco", [DESCRICAO_P6, DESCRICAO_P13], ids=["pag6", "pag13"])
def test_bloco_do_recorte_nao_e_truncado(bloco):
    assert not SPPdfExtractor._descricao_itens_telecom_truncada(bloco)
    assert SPPdfExtractor._discriminacao_telecom(bloco) == (
        "FeF ULTRA 120 MEGA | Servico de Telecomunicacoes Top | Full")


def test_item_com_palavra_inteira_nao_dispara():
    t = ("ITENS DA FATURA\nFeF ULTRA 120 MEGA 0100201 | UN | 1 23,98\n"
         "Servico de Telecomunicacoes Top | 0600601 | UN | 1 95,92\nVALOR TOTAL NF 119,90")
    assert not SPPdfExtractor._descricao_itens_telecom_truncada(t)


def test_valor_total_nf_sem_barra_continua_igual(monkeypatch, tmp_path):
    texto = OCR_P13.replace("VALOR TOTAL NF | 119,90", "VALOR TOTAL NF 119,90")
    assert _converter(monkeypatch, tmp_path, texto).valores.valor_servicos == pytest.approx(119.90)


# --- recortes reais no PDF (só no corpus local) -----------------------------------

@pytest.mark.skipif(not os.path.exists(PDF_REAL), reason="PDF real fora do corpus local")
@pytest.mark.parametrize("pagina, chave", [(6, CHAVE_P6), (13, CHAVE_P13)], ids=["pag6", "pag13"])
def test_recortes_no_pdf_real(pagina, chave):
    import pymupdf
    doc = pymupdf.open(PDF_REAL)
    try:
        page = doc.load_page(pagina - 1)
        ident = SPPdfExtractor._ocr_recut_identificacao_telecom(page)
        bloco = SPPdfExtractor._ocr_recut_descricao_itens_telecom(page)
    finally:
        doc.close()
    assert SPPdfExtractor._localizar_chave_nfcom(ident) == (chave, True)
    assert SPPdfExtractor._discriminacao_telecom(bloco) == (
        "FeF ULTRA 120 MEGA | Servico de Telecomunicacoes Top | Full")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
