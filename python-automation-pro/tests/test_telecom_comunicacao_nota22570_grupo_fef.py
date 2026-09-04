# -*- coding: utf-8 -*-
r"""Texto REAL do OCR (Tesseract) da NF-e de Serviço de Comunicação
(`telecom_comunicacao`) — nota real nº 22570, Grupo FeF (F&F Comunicações,
CNPJ 13.398.812/0001-89) -> Guarajuba Shopping Ltda (5º PDF do lote Guarajuba
Shopping, "NFSe TOMADOS 5.pdf", página 1 de 6). Reportado pelo usuário: "o
valor foi extraído zerado" — a nota é corretamente roteada para o layout
`telecom_comunicacao` já existente (o número, 22570, já saía certo), mas 2
bugs pontuais dentro dele produziam dados errados:

1. **Valor zerado**: o regex de valor só procurava o rótulo "TOTAL A PAGAR"
   (caixa cinza no topo do documento). Nesta nota, essa caixa nunca é lida
   pelo OCR em NENHUMA das 2 tentativas de recorte (zoom padrão e zoom alto,
   ambas concatenadas neste texto) — mas o MESMO total aparece também na
   grade de itens, no campo "VALOR TOTAL NF" (aqui "VALOR TOTAL NF 11990",
   sem pontuação -> R$119,90), que a extração não usava como fallback.
2. **Razão social do prestador errada**: saía um trecho de ruído solto ("sr
   rent er rr ar e e rr...") em vez de "Grupo FeF". Ao contrário da nota F&F
   Comunicações nº 31696 (já coberta em `test_telecom_comunicacao_ff_layout.py`,
   onde o ruído do OCR sai colado NA MESMA linha do título "DOCUMENTO
   AUXILIAR..."), aqui o ruído é uma linha INTEIRA e SEPARADA, ANTES do
   título — a busca por nome (que só pulava a própria linha do título, sem
   exigir tê-lo visto primeiro) escolhia essa linha de ruído por já ter
   letras e mais de 3 caracteres, sem nunca chegar a "Grupo FeF" (2 linhas
   depois do título).
"""
import os

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_OCR = """sr rent er rr ar e e rr rr rara ensaia rats tan cmo RE a Um Pc e e

DOCUMENTO AUXILIAR DA NOTA FISCAL DE FATURA DE SERVIÇO DE COMUNICAÇÃO ELETRÔNICA

Grupo FeF

Rua Senhor do Bonfim 544 Monte Gordo 42839852 Camacarl - BA
(71) 4062-8609

13.398.812/0001-89

019.192.620

» |

Nic asi am me rc rt ts per rr mr rem rss ne: ace mass: rem em um. 11010 it a 4 mm erre em 0 pus rm vm mm as Ve 00 EPE HO 0. OO a ELOI O VS O nm a rr

[mM] NOTA FISCAL Nº 22570 - SÉRIE: 1
3" DATA DE EMISSÃO: 15/05/2026

Guarajuba Shopping Ltda

Guarajuba Shopping 01 Guarajuba 42840310
Camacari - BA

CNPJ/CPF: 24.890.395/0001-03
INSCRIÇÃO ESTADUAL:

CÓD. DO CLIENTE: 2173

Nº TELEFONE: (71) 98149-5491

PERÍODO: 15/05/2026 á 14/06/2026

Protocolo de autorização:
32926001 19802762 - 15/05/2026 às 14:54:15

aroma ea gata mn mapa 00 PATO A 8 A 8 0 A 0 O rr mn rr a ro og e pr ar ca a nr

OMES): 2026/05 ER ÁREA CONTRIBUINTE:

o A A ps O pg 9 q ms mr mr A o

Nº do Contrato: 2173

ARG MAMAS SANS AO REAR SINA PISCANDO: OA AA PRE A A AAA AA OA A A AS O A

VALOR VALOR VALOR VALOR | PIS/COFINS | BC ICMS VALOR
) ICMS (R$)

UNIT fia DESC. (R$) | ACR. (R$) | TOTAL (R$)

MUDAVA OG ana 8900 Das nm ag sema umemta Mme agnt VummrM ORE" Rm

promo me

ITENS DA FATURA

FeF ULTRA 120 MEGA
Servico de Telecomunicacoes Top.

VONPR PRA AT OCR MONO VA UTC Mm cem RD ee TD a mm sro a ia mm corar creme e recria MINS O POMPOPO SA MUMN PANE MAG TRAGO NAFOREN GU NTRVANONCTNAPVA VOA NPR AAA ASAP rm ra nn rm rr OR 0 O pr am pr rm mr rc

VALOR TOTAL NF | INFORMAÇÃO DOS TRIBUTOS | ata ae ai ER BR ANO ASREIBNO ii
Rg TRIBUTO VALOR

TOTAL BASE DE CÁLCULO à BR

VALOR ICMS

VALOR ISENTO

VALOR OUTROS

soh ro pera iron ce 4 a e ra PU AAA AP A O O | 4 PA AA PO 0 04 6 SD A Or nm

par ear cs rapa renas maratonas se mto mares rar. og O rm A a rs A a a pr A a a re pre mr

INFORMAÇÕES COMPLEMENTARES

a o ga A A A A AA O O

merares imo mamtm ementas preto is mams m

rn o on A MO ORA NA A AS 1 vm e Pr

= titulo referencia - "643600

oa temem 1 010 me tr 0 mm pp cm aa rp 0 ts cr mr error vu 9 em e pe cream ret em matt e a 1 a er rm mar verem rm mem

"ÁREA DO CONTRIBUINTE E DETERMINAÇÕES DA ANATEL
Linha digitável
00000.00000 00000.000000 00000.000000 O 00000000000000

e e a UC ONO EO O PEA O vt rr rr rr

Avisos Regulatórios Direito de contestação da cobrança

1. Esta fatura é emitida conforme a Resolução ANATEL nº 765/2023. Você pode contestar valores desta fatura sem custo.

2. Você pode contestar valores cobrados sem custo e receber resposta em até 30 dias. Entre em contato com nossa Central de Atendimento: Telefone (71) 4062-8609 e
3. Central de Atendimento do ISP (71) 4062-8609 e WhatsApp (71) 4062-8609. WhatsApp (71) 4062-8609, ou pelo e-mail: financeiro O ffcomunicacoes.net.br.

4, Central de Atendimento da ANATEL: 1331 (ligação gratuita). A análise será concluída em até 30 dias, conforme a regra da ANATEL.

5. Fatura emitida com antecedência mínima de 5 dias do vencimento, Enquanto sua contestação estiver em andamento, o serviço não será suspenso,
6, Dados pessoais tratados conforme LGPD - Lei nº 13.709/2018.

7. O não pagamento poderá acarretar suspensão do serviço, conforme regras da ANATEL.

asas AM, ASS MAMA BEEN e VASO VA O OO PF VE AGUA ANAE PPUO TO APT OPOR AA Ar A Mr AAA O a as A UV Anta VOA Rn Can mm + Aa PODA MA VA DA UA ara

DOCUMENTO AUXILIAR DA NOTA FISCAL DE FATURA DE SERVIÇO DE COMUNICAÇÃO ELETRÔNICA

Grupo FeF

Rua Senhor do Bonfim 544 Monte Gordo 42839852 Camacari - BA
(71) 4062-8609

13.398.812/0001-89

019.192.620

meme a pe ssa

"[m] NOTA FISCAL Nº 22570 - SÉRIE: 1
si DATA DE EMISSÃO: 15/05/2026

CONSULTE PELA CHAVE DE ACESSO EM:
| https://dfe-portal.svrs.rs.gov.br/nfcom/consulta

' CHAVE DE ACESSO:
E!" 2926 0513 3988 1200 0189 6200 1000 0225 7010 7559 3534

Protocolo de autorização:
3292600119802762 - 15/05/2026 às 14:54:15

ÁREA CONTRIBUINTE:

Nº do Contrato: 2173

Guarajuba Shopping Ltda

Guarajuba Shopping 01 Guarajuba 42840310
Camacari - BA

CNPJ/CPF: 24.890.395/0001-03
INSCRIÇÃO ESTADUAL:

CÓD. DO CLIENTE: 2173

Nº TELEFONE: (71) 98149-5491

PERÍODO: 15/05/2026 á 14/06/2026

VALOR VALOR VALOR VALOR PIS/COFINS | BCICMS ALÍQ VALOR

ITENS DA FATURA cClass | UN | QUANT) unir (R$) | DESC. (R$) | ACR. (R$) | TOTAL (R$) E (R$) (%) | icms (Rs)
FeF ULTRA 120 MEGA |o10201/UN| 1 | 2888] 000) 000] 2398 222] 16,38] 20.50 3,34
Perto de Telecomunicacoes Top | 500601 | UN | 1 95,92 000] 0,00 95,92 000) 0.00) 0.00 0.0
VALOR TOTAL NF 11990] [INFORMAÇÃO DOS TRIBUTOS | [  RESERVADOAOFISCO

Ras) Di TRIBUTO
TOTAL BASE DE CÁLCULO 16,96] Ear

PE ma) PIS
VALOR ICMS 8,96 | [==
negunbrtio Ret COFINS
VALOR ISENTO 000 [EysT [O

e pan
VALOR ouTROS 0,00] | FUNTTEL

INFORMAÇÕES C Coml

ID titulo referencia - 643600

ÁREA DO CONTRIBUINTE E DETERMINAÇÕES DA. ANATEL

1
Linha digitável Nº Identificador de débito automático

00000.00000 00000.000000 00000.000000 O 00000000000000 -

A

Avisos Regulatórios Direito de contestação da cobrança

1. Esta fatura é emitida conforme a Resolução ANATEL nº 765/2023. Você pode contestar valores desta fatura sem custo.

2. Você pode contestar valores cobrados sem custo é receber resposta em até 30 dias. Entre em contato com nossa Central de Atendimento: Telefone (71) 4062-8609 e
3. Central de Atendimento do ISP (71) 4062-8609 e WhatsApp (71) 4062-8609. WihatsApp (71) 4062-8609, ou pelo e-mail: financeiro O ffcomunicacoes.net.br.

4. Central de Atendimento da ANATEL: 1331 (ligação gratuita). A análise será concluída em até 30 dias, conforme a regra da ANATEL.

5. Fatura emitida com antecedência mínima de 5 dias do vencimento. Enquanto sua contestação estiver em andamento, O serviço não será suspenso.

6. Dados pessoais tratados conforme LGPD - Lei nº 13.709/2018.
7. O não pagamento poderá acarretar suspensão do serviço, conforme regras da ANATEL.
"""


@pytest.fixture
def nfse(monkeypatch):
    dummy_path = "tests/dummy_telecom_grupofef_22570.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_OCR)

    try:
        nfse_list = SPPdfExtractor(dummy_path).parse_multiple()
        assert len(nfse_list) == 1
        yield nfse_list[0]
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_numero_da_nota(nfse):
    assert nfse.numero == "22570"


def test_valor_recuperado_do_campo_valor_total_nf(nfse):
    # "TOTAL A PAGAR" nunca é lido pelo OCR nesta nota (nas 2 tentativas de
    # recorte) — antes, isso zerava o valor. Agora cai no fallback "VALOR
    # TOTAL NF" da grade de itens ("11990" sem pontuação -> R$119,90).
    assert nfse.valores.valor_servicos == pytest.approx(119.90)
    assert nfse.valores.valor_liquido_nfse == pytest.approx(119.90)


def test_prestador_razao_social_ignora_ruido_antes_do_titulo(nfse):
    # Antes: "sr rent er rr ar e e rr..." (linha de ruído inteira ANTES do
    # título "DOCUMENTO AUXILIAR...", nunca vista pela extração antiga).
    assert nfse.prestador.razao_social == "Grupo FeF"


def test_prestador_cnpj_correto(nfse):
    assert nfse.prestador.cnpj_cpf == "13398812000189"


def test_tomador_correto(nfse):
    assert nfse.tomador.cnpj_cpf == "24890395000103"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
