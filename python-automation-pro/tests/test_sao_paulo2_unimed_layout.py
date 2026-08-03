# -*- coding: utf-8 -*-
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
import os

# Texto REAL do OCR (Tesseract, zoom 3x) da NFS-e de São Paulo/SP ESCANEADA
# (nota real nº 19766093, UNIMED CNU - COOPERATIVA CENTRAL -> PH GESTÃO E
# CONSULTORIA S.A., mensalidade de plano de saúde, scan de boa qualidade sem
# rotação). Preservado verbatim, incluindo os quirks que travam regressões:
#  - endereço do prestador em LINHA ÚNICA sem rótulo "Bairro:" separado:
#    "Endereço: R FREI CANECA 1355 - CONSOLACAO - CEP: 01307-003" (número
#    colado ao nome da rua por um espaço, sem vírgula);
#  - endereço do tomador também em linha única, mas com vírgula separando a
#    rua de um COMPLEMENTO (não um número real): "Endereço: RODOVIA BA 099
#    ESTRADA DO COCO, GUARAJUBA SHOPPING - GUARAJUBA (MONTE GORDO) - CEP:
#    42840-310";
#  - bloco "INTERMEDIÁRIO DE SERVIÇOS" com "CPF/CNPJ: ---- Nomey/Razão
#    Social: ----" (todo vazio, "Nomey" é o próprio OCR corrompendo "Nome") -
#    não é um intermediário de verdade.
MOCK_TEXT = """f x lúmero da Nota
PREFEITURA DO MUNICÍPIO DE SÃO PAULO 9766093

SECRETARIA MUNICIPAL DA FAZENDA Data e Hora de Emissão
à 26/05/2026 13:16:43
NOTA FISCAL ELETRÔNICA DE SERVIÇOS - NFS-e Código de Verificação
20260615U02812468000106 RPS Nº 19754129 Série 00001, emitido em 26/05/2026 IARU-BUZD

Identificador Nacional: 35503081 202812468000106000001976609326052638958222

PRESTADOR DE SERVIÇOS
CPF/CNPJ: 02.812.468/0001-06 Inscrição Municipal: 2.735.686-8
o -. Nome/Razão Social: UNIMED CNU - COOPERATIVA CENTRAL
Endereço: R FREI CANECA 1355 - CONSOLACAO - CEP: 01307-003
: Município: São Paulo UF: SP

TOMADOR DE SERVIÇOS
Nome/Razão Social: PH GESTAO E CONSULTORIA S.A.
CPF/CNPJ: 25.311.856/0001-09 Inscrição Municipal: ----
Endereço: RODOVIA BA 099 ESTRADA DO COCO, GUARAJUBA SHOPPING - GUARAJUBA (MONTE GORDO) - CEP: 42840-310
Município: Camaçari UF: BA E-mail: ----

INTERMEDIÁRIO DE SERVIÇOS
CPF/CNPJ: ---- Nomey/Razão Social: ----

DISCRIMINAÇÃO DE SERVIÇOS
Mensalidade R$ 6.261,18
TOTAL R$ 6.261,18
Tributo incluso no produto de 1,6625%,que perfaz o valor bruto na fatura de R$ 104,09-Lei Federal nº12.741/12
Retenções Tributárias na Fonte: NÃO SE APLICA.
Data de vencimento: 20/06/2026

VALOR TOTAL DO SERVIÇO = R$ 6.261,18

Contribuição Previdenciária - Retida (R$) IRRF (R$) COFINS (R$) PIS/PASEP (R$) IPI(R$)
0,00 0,00 0,00 0,00 -
Contribuições Sociais - Retidas (R$) Descrição Contribuições Sociais - Retidas
0,00 -

Código do Serviço

05312 - Planos de saúde que se cumpram através de serviços de terceiros contratados e credenciados.

Valor Total das Deduções (R$) Base de Cálculo (R$) Alíquota (%) Valor do ISS (R$) Crédito Programa da NFP (R$)
0,00 6.261,18 2,00% 125,22 0,00
Município de Prestação do Serviço Número Inscrição da Obra Valor Aproximado dos Tributos / Fonte
OUTRAS INFORMAÇÕES

(1) Esta NFS-e foi emitida com respaldo na Lei nº 14.097/2005; (2) O código de serviço referente a esta NFS-e não gera crédito no Programa da Nota
Fiscal Paulistana; (3) Esta NFS-e substitui o RPS Nº 19754129 Série 00001, emitido em 26/05/2026; (4) Data de vencimento do ISS desta NFS-e:
10/06/2026;
"""


def test_extract_sao_paulo2_unimed_layout(monkeypatch):
    dummy_path = "tests/dummy_sao_paulo2_unimed.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        assert nfse.numero == "19766093"
        assert nfse.codigo_verificacao == "IARU-BUZD"
        assert nfse.servico_codigo == "05312"

        # Prestador: endereço em linha única sem rótulo "Bairro:" - o número
        # (colado ao nome da rua por espaço, sem vírgula) precisa ser
        # separado do logradouro, e o bairro não pode carregar ruído final.
        assert nfse.prestador.cnpj_cpf == "02812468000106"
        assert nfse.prestador.razao_social == "UNIMED CNU - COOPERATIVA CENTRAL"
        assert nfse.prestador.endereco.logradouro == "R FREI CANECA"
        assert nfse.prestador.endereco.numero == "1355"
        assert nfse.prestador.endereco.bairro == "CONSOLACAO"
        assert nfse.prestador.endereco.municipio == "São Paulo"
        assert nfse.prestador.endereco.codigo_municipio == "3550308"
        assert nfse.prestador.endereco.uf == "SP"
        assert nfse.prestador.endereco.cep == "01307003"

        # Tomador: endereço com vírgula, mas o texto após ela é COMPLEMENTO
        # (não um número real) - não pode vazar inteiro pro campo "numero".
        assert nfse.tomador.cnpj_cpf == "25311856000109"
        assert nfse.tomador.razao_social == "PH GESTAO E CONSULTORIA S.A"
        assert nfse.tomador.endereco.logradouro == "RODOVIA BA 099 ESTRADA DO COCO"
        assert nfse.tomador.endereco.numero == "S/N"
        assert nfse.tomador.endereco.complemento == "GUARAJUBA SHOPPING"
        assert nfse.tomador.endereco.bairro == "GUARAJUBA (MONTE GORDO)"
        assert nfse.tomador.endereco.municipio == "Camaçari"
        assert nfse.tomador.endereco.codigo_municipio == "2905701"
        assert nfse.tomador.endereco.uf == "BA"
        assert nfse.tomador.endereco.cep == "42840310"

        # Intermediário vazio ("----" em tudo) não pode virar um intermediário
        # fantasma com razão social fabricada do próprio rótulo da seção.
        assert nfse.intermediario is None

        val = nfse.valores
        assert val.valor_servicos == pytest.approx(6261.18)
        assert val.base_calculo == pytest.approx(6261.18)
        assert val.aliquota == pytest.approx(0.02)
        assert val.valor_iss == pytest.approx(125.22)
        assert val.valor_liquido_nfse == pytest.approx(6261.18)

        assert nfse.avisos == []
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
