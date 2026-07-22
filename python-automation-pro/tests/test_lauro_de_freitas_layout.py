import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
import os

# Texto real extraído via pdfminer de uma NFS-e real de Lauro de Freitas/BA
# (nota Macedo/Sul&Seg, 2026-07-14). Preservado como veio do pdfminer,
# incluindo o vazamento de Município/UF/Email do PRESTADOR para depois do
# cabeçalho "TOMADOR DE SERVIÇOS" — ver _extrair_entidade_lauro_freitas.
MOCK_TEXT = """MUNICIPIO DE LAURO DE FREITAS
Secretaria da Fazenda

Coordenação Tributária

Nota Fiscal de Serviços Eletrônica - NFS-e

RPS Nº.12365, Série RPS

, emitida em 14/07/2026

Número da Nota

202612549

Data e Hora de Emissão

14/07/2026

08:31:55

Código de Verificação

A autenticidade desta Nota Fiscal de Serviços Eletrônica, poderá ser confirmada na página da MUNICIPIO DE LAURO DE FREITAS na Internet, no
endereço http://www.laurodefreitas.ba.gov.br ou através da leitura do QR Code.

579312F9A

PRESTADOR DE SERVIÇOS

CPF/CNPJ:

18.294.792/0001-10

Inscrição

0010030574

Inscrição Estadual

Nome/Razão

SUL&SEG COMERCIO E SERVICOS DE MANUTENCAO ELETRICOS EIRELI

Endereço:

AVN Brigadeiro Alberto Costa Matos, 1184, CENTRO

Bairro: Aracuí

CEP:

42702-010

TOMADOR DE SERVIÇOS

CPF/CNPJ/CRI :

04.074.648/0001-63

Inscrição

Município: LAURO DE FREITAS

UF: BA

Email: JDANTAS@SULESEG.COM.BR

Inscrição Estadual:

Nome/Razão

MACEDO COMERCIAL DE CALCADOS LTDA

Endereço:

RUA MELLO MORAES FILHO, 214, TERREO DE 187 A 547 - LADO IMPAR

Bairro:

FAZENDA GRANDE DO RETIRO

Município: SALVADOR

UF: BA

CEP:

40352-000

PAÍS:

Email:

maxcalcados@hotmail.com

LOCAL DA PRESTAÇÃO DO(S) SERVIÇO(S): SALVADOR

DISCRIMINAÇÃO DOS SERVIÇOS
SERVICOS DE MONITORAMENTO REF. A JULHO2026 Valor aproximado dos tributos R$ 16,50 Fonte IBPT

VALOR TOTAL DA NOTA FISCAL :  R$

100,00

ATIVIDADE

0003313901

-

Manutenção E Reparação De Geradores, Transfor

ITEM DA LISTA DE SERVIÇOS:

( Lei Municipal 1572/2015 )

110201 - Vigilância, segurança ou monitoramento de bens, pessoas e semoventes.

Valor Total Deduções (R$)

Base de Cálculo (R$)

Alíquota (%)

Valor do ISS (R$)

ISSQN Retido (R$)

R$ 0,00

R$ 100,00

3,00

3,00

Não

RETENÇÃO DE IMPOSTOS

PIS (R$)

COFINS (R$)

INSS (R$)

IRRF (R$):

CSLL (R$):

OUTRAS RETENÇÕES (R$):

0,00

0,00

0,00

0,00

0,00

VALOR LÍQUIDO DA NOTA FISCAL : R$

100,00

INFORMAÇÕES COMPLEMENTARES
Competência: 07/2026 - Tributado no Município de Lauro de Freitas - Não Retido
 NBS: 118022000 - Serviços de consultoria em segurança
 Benefício Municipal: -

Autentique
Via QR Code
"""


def test_extract_lauro_de_freitas_layout(monkeypatch):
    dummy_path = "tests/dummy_lauro_freitas.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        extractor.raw_text = MOCK_TEXT
        extractor.layout = extractor._detect_layout()

        assert extractor.layout == 'lauro_de_freitas_ba'

        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        assert nfse.numero == "202612549"
        assert nfse.codigo_verificacao == "579312F9A"
        assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "14/07/2026 08:31:55"
        assert nfse.competencia.strftime("%m/%Y") == "07/2026"
        assert nfse.servico_codigo == "1102"
        assert nfse.discriminacao == "SERVICOS DE MONITORAMENTO REF. A JULHO2026"

        # Prestador: Sul&Seg (Lauro de Freitas) — CNPJ/Município/Email vazados
        # para depois do cabeçalho do tomador no texto do pdfminen precisam
        # continuar associados ao PRESTADOR, não ao tomador.
        prest = nfse.prestador
        assert prest.cnpj_cpf == "18294792000110"
        assert prest.inscricao_municipal == "0010030574"
        assert prest.razao_social == "SUL&SEG COMERCIO E SERVICOS DE MANUTENCAO ELETRICOS EIRELI"
        assert prest.endereco.logradouro == "AVN Brigadeiro Alberto Costa Matos"
        assert prest.endereco.numero == "1184"
        assert prest.endereco.bairro == "Aracuí"
        assert prest.endereco.municipio == "LAURO DE FREITAS"
        assert prest.endereco.codigo_municipio == "2919207"
        assert prest.endereco.cep == "42702010"
        assert prest.email == "JDANTAS@SULESEG.COM.BR"

        # Tomador: Macedo (Salvador) — não deve herdar o município/email
        # vazados do prestador.
        tom = nfse.tomador
        assert tom.cnpj_cpf == "04074648000163"
        assert tom.razao_social == "MACEDO COMERCIAL DE CALCADOS LTDA"
        assert tom.endereco.logradouro == "RUA MELLO MORAES FILHO"
        assert tom.endereco.numero == "214"
        assert tom.endereco.bairro == "FAZENDA GRANDE DO RETIRO"
        assert tom.endereco.municipio == "SALVADOR"
        assert tom.endereco.codigo_municipio == "2927408"
        assert tom.endereco.cep == "40352000"
        assert tom.email == "maxcalcados@hotmail.com"

        assert nfse.valores.valor_servicos == pytest.approx(100.0)
        assert nfse.valores.base_calculo == pytest.approx(100.0)
        assert nfse.valores.aliquota == pytest.approx(0.03)
        assert nfse.valores.valor_iss == pytest.approx(3.0)
        assert nfse.valores.iss_retido is False
        assert nfse.valores.valor_liquido_nfse == pytest.approx(100.0)
        assert nfse.valores.valor_pis == pytest.approx(0.0)
        assert nfse.valores.valor_inss == pytest.approx(0.0)

        assert nfse.avisos == []
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__])
