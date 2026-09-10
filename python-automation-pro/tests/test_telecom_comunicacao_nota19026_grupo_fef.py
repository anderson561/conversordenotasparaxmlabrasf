# -*- coding: utf-8 -*-
r"""Texto REAL do OCR (Tesseract) da NF-e de Serviço de Comunicação
(`telecom_comunicacao`) — nota real nº 19026, Grupo FeF (F&F Comunicações,
CNPJ 13.398.812/0001-89) -> Guarajuba Shopping Ltda (6º PDF do lote Guarajuba
Shopping, "NFSe TOMADOS 6.pdf", página 1 de 4). Reportado pelo usuário: "o
valor foi extraído zerado, o correto é R$ 119,90", indicando que a coluna
VALOR UNIT (R$) da tabela de itens soma o VALOR TOTAL NF. 2 bugs, distintos
dos já corrigidos nas notas nº 31696 e nº 22570:

1. **Valor zerado**: nem "TOTAL A PAGAR" (caixa ilegível nas 2 tentativas de
   recorte, mesmo problema da nota 22570) NEM o fallback "VALOR TOTAL NF"
   (introduzido para a nota 22570) funcionam aqui — desta vez o próprio
   rótulo "VALOR **TOTAL** NF" sai com "TOTAL" comido pelo OCR ("VALOR O
   UNF 119,90"), quebrando a busca pela palavra literal. Corrigido com uma
   3ª camada de fallback: soma unitário×quantidade de cada linha de item da
   tabela "ITENS DA FATURA" (ancorada em "UN | <qtd> <valor unitário>",
   confirmada pelo usuário: 23,98 + 95,92 = 119,90).
2. **Tomador errado**: saía "TT CONSULTE PELA CHAVE DE ACESSO EM:" em vez de
   "Guarajuba Shopping Ltda". Causa dupla: (a) o nome do tomador sai colado
   NA MESMA linha do cabeçalho "NOTA FISCAL Nº 19026 - SÉRIE: 1" ("Guarajuba
   Shopping Ltda [E] NOTA FISCAL Nº 19026 - SÉRIE: 1"), então a guarda
   antiga (que rejeitava qualquer linha com dígito) nunca a considerava; (b)
   uma linha de ruído sem nenhum dígito ("TT CONSULTE PELA CHAVE DE ACESSO
   EM:") aparecia ANTES dela na busca reversa e satisfazia a heurística
   solta (sem dígito, tem letras, mais de 3 caracteres), sendo escolhida
   primeiro.
"""
import os

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_OCR = """DOCUMENTO AUXILIAR DA NOTA FISCAL DE FATURA DE SERVIÇO DE COMUNICAÇÃO ELETRÔNICA

Grupo FeF
Rua Senhor do Bonfim 544 Monte Gordo 42839852 Camacari - BA
(71) 4062-8609

13.398.812/0001-89

019.192.620

me omsrt creme

Guarajuba Shopping Ltda [m] NOTA FISCAL Nº 19026 - SÉRIE: 1
a Hr DATA DE EMISSÃO: 17/04/2026

CONSULTE PELA CHAVE DE ACESSO EM:
https://dfe-portal.svrs.rs.gov.br/nfcom/consulta

CHAVE DE ACESSO:

Guarajuba Shopping 01 Guarajuba 42840310
Camacari - BA

CNPJ/CPF: 24.890.395/0001-03
INSCRIÇÃO ESTADUAL:

CÓD. DO CLIENTE: 2173

Nº TELEFONE: (71) 98149-5491

PERÍODO: 15/04/2026 á 14/05/2026

Protocolo de autorização:
É 3292600096326014 - 17/04/2026 às 16:43:16

ÁREA CONTRIBUINTE:

ço moon me vt ineo cercar me res mera coma mr rm mam mm mr 1 e mc

Nº do Contrato: 2173

VALOR VALOR VALOR
[0100201 [UN] 1 | 2398] 000] 0,00]

VALOR |
ICMS (R$)

ITENS DA FATURA

VALOR | |PISICOFINS | BC ICMS
TOTAL (R$)| (R$) (R$)
98] 222] 16,38] 20.50

FeF ULTRA 120 MEGA |

Servico de Telecomunicacoes Top
Full

coma tas + im ve tm em rasarmeamarmrmam mem me "e ven enem

VALOR TOTAL NF

INFORMAÇÃO DOS TRIBUTOS

eme qa ovais

TRIBUTO | VALOR

O RR
E

INFORMAÇÕES COMPLEMENTARES

RESERVADO AO FISCO

ur enem

TOTAL BASE DE CÁLCULO

er entrem eta

VALOR ICMS

VALOR ISENTO

emma rem cancao mermo ter dota ma mm memos conrasrma

VALOR OUTROS

ÁREA DO CONTRIBUINTE E DETERMINAÇÕES DA ANATEL

Linha digitável Nº Identificador de débito automático

00000.00000 00000.000000 00000.000000 O 00000000000000

Avisos Regulatórios Direito de contestação da cobrança

1. Esta fatura é emitida conforme a Resolução ANATEL nº 765/2023. Você pode contestar valores desta fatura sem custo,

2. Você pode contestar valoros cobrados sem custo e receber resposta em até 30 dias. Entre em contato com nossa Central de Atendimento: Telefone (71) 4062-8609 e
3. Central de Atendimonto do ISP (71) 4062-8609 e WhatsApp (71) 4062-8609. WhatsApp (71) 4062-8609, ou pelo e-mail: financeiro ffcomunicacoes.net.br.

4. Central de Atendimento da ANATEL: 1331 (ligação gratuita). A análise será concluída em até 30 dias, conforme a regra da ANATEL.

5. Fatura emitida com antecedência mínima de 5 dias do vencimento. Enquanto sua contestação estiver em andamento, o serviço não será suspenso.

6. Dados pessoais tratados conforme LGPD - Lel nº 13.709/2018.

7. O não pagamento poderá acarretar suspensão do serviço, conforme regras da ANATEL. |

DOCUMENTO AUXILIAR DA NOTA FISCAL DE FATURA DE SERVIÇO DE COMUNICAÇÃO ELETRÔNICA

Grupo FeF

Rua Senhor do Bonfim 544 Monte Gordo 42839852 Camacari - BA
(71) 4062-8609

13.398.812/0001-89

019.192.620

Guarajuba Shopping Ltda [E] NOTA FISCAL Nº 19026 - SÉRIE: 1

ki Hr DATA DE EMISSÃO: 17/04/2026
TT CONSULTE PELA CHAVE DE ACESSO EM:
E

Guarajuba Shopping 01 Guarajuba 42840310
Camacari - BA

CNPJ/CPF: 24.890.395/0001-03
INSCRIÇÃO ESTADUAL:

CÓD. DO CLIENTE: 2173

Nº TELEFONE: (71) 98149-5491

PERÍODO: 15/04/2026 á 14/05/2026

; https://dfe-portal.svrs.rs.gov.br/nfcom/consulta
| E o] [o CHAVE DE ACESSO:
+ = 2926 0413 3988 1200 0189 6200 1000 0190 2610 2323 7868

Protocolo de autorização:
R 3292600096326014 - 17/04/2026 às 16:43:16

PREFERENCIA MES); 2026/04 ÁREA CONTRIBUINTE:

Nº do Contrato: 2173

é tica
j

VALOR VALOR VALOR VALOR PIS/COFINS | BC ICMS ALÍQ VALOR
ITENS DA FATURA cClass | UN | QUANT] unir (R$) | DESC. (R$) | ACR.(R$) | TOTAL (R| (RS) (R$) Cm | tems (R$)
FeF ULTRA 120 MEGA 0100201 | UN | 1 23,98 0,00 | 0,00 23,98 | 222] 1638] 20.50 3,36
ab de Telecomunicacoes Top 0600601 | UN 1 95,92 0.00 | 0,00 95,92 0,00 0.00] 0.00 0.00
VALOR O UNF 119,90] [INFORMAÇÃO DOS TRIBUTOS | [1 RESERVADO AO FISCO

re] [NRRTRIBUZO VALOR
TOTAL BASE DE CÁLCULO 16,38 pal EEE
ae Ei 1 |pIs 0,40
VALOR ICMS 3,36
a aa COFINS
po

VALOR ISENTO 0,00
li Ea FUST
VALOR OUTROS 0,00] [FUNTTEL
sara o PROA Ta A

pm ia

INFORMAÇÕES COMPLEMENTARES

ID titulo referencia - 043599

ÁREA DO CONTRIBUINTE E DETERMINAÇÕES DA ANATEL

Linha digitável Nº Identificador de débito automático
00000.00000 00000.000000 00000.000000 0 00000000000000 -

]
|
HE
Avisos Regulatórios Direito de contestação da cobrança
1. Esta fatura é emitida conforme a Resolução ANATEL nº 765/2023. Você pode contestar valores desta fatura sem custo.
2. Você pode contestar valoras cobrados sem custo e receber resposta em até 30 dias. Entre em contato com nossa Central de Atendimento: Telefone (71) 4062-8609 e
3. Central de Atendimonto do ISP (71) 4062-8609 e WhatsApp (71) 4062-8609. WihatsApp (71) 4062-8609, ou pelo e-mail: financeiroffcomunicacoes.net.br.
4. Central de Atendimento da ANATEL: 1331 (ligação gratuita). A análise será concluída em até 30 dias, conforme a regra da ANATEL.
5. Fatura emitida com antecedência mínima de 5 dias do vencimento. Enquanto sua contestação estiver em andamento, o serviço não será suspenso.

6. Dados pessoais tratados conforme LGPD - Lel nº 13.709/2018.
7. O não pagamento poderá acarretar suspensão do serviço, conforme regras da ANATEL.
"""


@pytest.fixture
def nfse(monkeypatch):
    dummy_path = "tests/dummy_telecom_grupofef_19026.pdf"
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
    assert nfse.numero == "19026"


def test_valor_recuperado_da_soma_das_linhas_de_item(nfse):
    # Nem "TOTAL A PAGAR" nem "VALOR TOTAL NF" são legíveis nesta nota
    # ("VALOR O UNF", "TOTAL" comido pelo OCR) — cai no 3º fallback, soma
    # unitário×quantidade das 2 linhas de item: 23,98 + 95,92 = 119,90.
    assert nfse.valores.valor_servicos == pytest.approx(119.90)
    assert nfse.valores.valor_liquido_nfse == pytest.approx(119.90)


def test_prestador_razao_social_correta(nfse):
    assert nfse.prestador.razao_social == "Grupo FeF"


def test_tomador_razao_social_ignora_ruido_e_linha_fundida(nfse):
    # Antes: "TT CONSULTE PELA CHAVE DE ACESSO EM:" (ruído sem dígito que
    # satisfazia a heurística solta, antes de alcançar o nome real, que
    # sai colado na mesma linha de "NOTA FISCAL Nº 19026 - SÉRIE: 1").
    assert nfse.tomador.razao_social == "Guarajuba Shopping Ltda"


def test_tomador_cnpj_correto(nfse):
    assert nfse.tomador.cnpj_cpf == "24890395000103"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
