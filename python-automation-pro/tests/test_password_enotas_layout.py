import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
import os

# Texto real extraído via pdfminer de uma NFS-e real emitida via eNotas Gateway
# pelo prestador PASSWORD - SISTEMAS ELETRONICOS LTDA, de Lauro de Freitas/BA
# (nota Controller 06-26.pdf, competência 06/2026). Preservado como veio do
# pdfminer, incluindo o "VALOR DO ISS" sem valor destacado (renderizado como
# "-", solto entre a alíquota e o rótulo "VALOR LÍQUIDO" — Simples Nacional
# recolhe o ISS via DAS, não na face da nota).
MOCK_TEXT = """NFS-e - NOTA FISCAL DE SERVIÇOS ELETRÔNICA  -  RPS 38591 Série SN, emitido em: 10/06/2026

PASSWORD - SISTEMAS ELETRONICOS LTDA

EVERALDINA B DA PAZ, 400

ITINGA - Lauro de Freitas - BA - 42738495

TELEFONE: 71987935510

EMAIL: controllerbafinanceiro@gmail.com

CNPJ: 04.021.023/0001-33

INSCRIÇÃO MUNICIPAL: 0000358975011

NÚMERO DA NOTA

202600000038558

COMPETÊNCIA

06/2026

CÓDIGO DE VERIFICAÇÃO

043BE7B2F

DATA DE EMISSÃO

10/06/2026 05:28:20

DADOS DO TOMADOR

NOME / RAZÃO SOCIAL

FOLHAS URBANAS LTDA

ENDEREÇO

PELICANO, 150 GALPAO

E-MAIL

administrativo@folhasurbanas.com.br

TELEFONE

7121065100

BAIRRO / DISTRITO

PITANGUEIRAS

CEP

42701340

MUNICÍPIO

Lauro de Freitas

UF

BA

PAÍS

Brasil

CPF / CNPJ / OUTROS

INSCRIÇÃO MUNICIPAL

INSCRIÇÃO ESTADUAL

43.886.789/0001-32

DISCRIMINAÇÃO DOS SERVIÇOS

1 Locação do Sistema de Alarme. 214,44

Locação de equipamentos de segurança eletrônica para monitoramento do sistema de alarme.

Cód. 2172

CÓDIGO DO SERVIÇO

15.03 / 1503 - Locação e manutenção de cofres particulares, de terminais eletrônicos, de terminais de atendimento e de bens e equipamentos em geral.

MUNICÍPIO ONDE O SERVIÇO FOI PRESTADO

2919207 / Lauro de Freitas

NATUREZA DA OPERAÇÃO

Tributação no municipio

REGIME ESPECIAL DE TRIBUTAÇÃO: ME EPP - Simples Nacional

VALOR DOS SERVIÇOS:

R$ 214,44

(-) DESCONTOS:

(-) RETENÇÕES FEDERAIS:

(-) ISS RETIDO NA FONTE:

R$ 0,00

R$ 0,00

R$ 0,00

(-) DEDUÇÕES:

R$ 0,00

(=) BASE DE CÁLCULO:

R$ 214,44

(x) ALÍQUOTA:

3,00 %

-

VALOR LÍQUIDO:

R$ 214,44

(=) VALOR DO ISS:

RETENÇÕES FEDERAIS

PIS: R$ 0,00   COFINS: R$ 0,00   IR: R$ 0,00   CSLL: R$ 0,00   INSS: R$ 0,00

OUTRAS INFORMAÇÕES

Documento emitido por ME ou EPP optante pelo simples nacional;

Trib aprox R$: 28,84 Federal, R$: 0,00 Estadual e R$: 10,72 Municipal Fonte: IBPT/empresometro.com.br   92589A

powered by eNotas Gateway

"""


def test_extract_password_enotas_layout(monkeypatch):
    dummy_path = "tests/dummy_password_enotas.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        extractor.raw_text = MOCK_TEXT
        extractor.layout = extractor._detect_layout()

        assert extractor.layout == 'password_enotas'

        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        assert nfse.numero == "202600000038558"
        assert nfse.codigo_verificacao == "043BE7B2F"
        assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "10/06/2026 05:28:20"
        assert nfse.competencia.strftime("%m/%Y") == "06/2026"
        assert nfse.servico_codigo == "1503"
        assert nfse.discriminacao == (
            "Locação do Sistema de Alarme. "
            "Locação de equipamentos de segurança eletrônica para monitoramento do sistema de alarme."
        )
        assert nfse.optante_simples_nacional is True
        assert nfse.regime_especial_tributacao == "6"

        prest = nfse.prestador
        assert prest.cnpj_cpf == "04021023000133"
        assert prest.inscricao_municipal == "0000358975011"
        assert prest.razao_social == "PASSWORD - SISTEMAS ELETRONICOS LTDA"
        assert prest.endereco.logradouro == "EVERALDINA B DA PAZ"
        assert prest.endereco.numero == "400"
        assert prest.endereco.complemento is None
        assert prest.endereco.bairro == "ITINGA"
        assert prest.endereco.municipio == "Lauro de Freitas"
        assert prest.endereco.codigo_municipio == "2919207"
        assert prest.endereco.uf == "BA"
        assert prest.endereco.cep == "42738495"
        assert prest.email == "controllerbafinanceiro@gmail.com"
        assert prest.telefone == "71987935510"

        tom = nfse.tomador
        assert tom.cnpj_cpf == "43886789000132"
        assert tom.razao_social == "FOLHAS URBANAS LTDA"
        assert tom.endereco.logradouro == "PELICANO"
        assert tom.endereco.numero == "150"
        assert tom.endereco.complemento == "GALPAO"
        assert tom.endereco.bairro == "PITANGUEIRAS"
        assert tom.endereco.municipio == "Lauro de Freitas"
        assert tom.endereco.codigo_municipio == "2919207"
        assert tom.endereco.uf == "BA"
        assert tom.endereco.cep == "42701340"
        assert tom.email == "administrativo@folhasurbanas.com.br"

        val = nfse.valores
        assert val.valor_servicos == pytest.approx(214.44)
        assert val.valor_deducoes == pytest.approx(0.0)
        assert val.base_calculo == pytest.approx(214.44)
        assert val.aliquota == pytest.approx(0.03)
        assert val.valor_iss == pytest.approx(0.0)
        assert val.iss_retido is False
        assert val.valor_liquido_nfse == pytest.approx(214.44)

        assert nfse.avisos == []
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


# Texto real extraído via pdfminer de uma NFS-e real emitida via eNotas
# Gateway pelo prestador INFOMIX SOLUÇÕES EM TECNOLOGIA LTDA — 2º emissor
# (também de Lauro de Freitas/BA) na MESMA plataforma do PASSWORD acima, mas
# com 2 diferenças estruturais que travam regressão:
#  - "CÓDIGO DO SERVIÇO\n\n01.07 / 107 -" — o "código interno" após a barra
#    tem só 3 dígitos (sem zero à esquerda), não 4 como na nota PASSWORD
#    ("15.03 / 1503"); usa-se o próprio item "01.07" (sem ponto) em vez do
#    código interno;
#  - "NOME / RAZÃO SOCIAL\n\nE-MAIL\n\n<razão>\n\n<email>" — os 2 rótulos do
#    tomador vêm despejados juntos ANTES dos 2 valores (diferente da nota
#    PASSWORD, onde cada rótulo é seguido imediatamente do próprio valor).
MOCK_TEXT_INFOMIX = 'NFS-e - NOTA FISCAL DE SERVIÇOS ELETRÔNICA  -  RPS 1639 Série 1, emitido em: 03/06/2026\n\nINFOMIX SOLUCOES EM TECNOLOGIA LTDA\n\nAVENIDA PREFEITO CELSO ALVES PINHEIRO DA SILVA, 103 SALA 105\n\nCENTRO - Lauro de Freitas - BA - 42702580\n\nTELEFONE: 71999031348\n\nEMAIL: financeiro@infomixtecnologia.com.br\n\nCNPJ: 29.869.622/0001-32\n\nINSCRIÇÃO MUNICIPAL: 0010029058011\n\nDADOS DO TOMADOR\n\nNOME / RAZÃO SOCIAL\n\nE-MAIL\n\nTEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDA\n\nfinanceiro@temis-es.com.br\n\nNÚMERO DA NOTA\n\n202600000001638\n\nCOMPETÊNCIA\n\n06/2026\n\nCÓDIGO DE VERIFICAÇÃO\n\n431E206D7\n\nDATA DE EMISSÃO\n\n03/06/2026 12:06:58\n\nTELEFONE\n\n --\n\nENDEREÇO\n\nRua Território do Amapá, 146 CASA 02\n\nBAIRRO / DISTRITO\n\nPituba\n\nCEP\n\n41830540\n\nMUNICÍPIO\n\nSalvador\n\nUF\n\nBA\n\nPAÍS\n\nBrasil\n\nCPF / CNPJ / OUTROS\n\nINSCRIÇÃO MUNICIPAL\n\nINSCRIÇÃO ESTADUAL\n\n07.345.543/0001-90\n\nDISCRIMINAÇÃO DOS SERVIÇOS\n\nNota fiscal da Fatura 800530705.\n\nDescrição dos Serviços: 01.07 - Suporte técnico em informática, inclusive instalação, configuração e manutenção de programas de computação e bancos de dados..\n\nPara mais informações acesse: https://www.asaas.com/i/5xsv7asb2q764l6c.\n\nCÓDIGO DO SERVIÇO\n\n01.07 / 107 - Suporte técnico em informática, inclusive instalação, configuração e manutenção de programas de computação e bancos de dados.\n\nMUNICÍPIO ONDE O SERVIÇO FOI PRESTADO\n\n2919207 / Lauro de Freitas\n\nNATUREZA DA OPERAÇÃO\n\nTributação no municipio\n\nREGIME ESPECIAL DE TRIBUTAÇÃO: ME EPP - Simples Nacional\n\n(-) DEDUÇÕES:\n\nR$ 0,00\n\n(=) BASE DE CÁLCULO:\n\nR$ 1459,00\n\n(x) ALÍQUOTA:\n\n3,00 %\n\n-\n\nVALOR DOS SERVIÇOS:\n\nR$ 1459,00\n\n(-) DESCONTOS:\n\n(-) RETENÇÕES FEDERAIS:\n\n(-) ISS RETIDO NA FONTE:\n\nR$ 0,00\n\nR$ 0,00\n\nR$ 0,00\n\nVALOR LÍQUIDO:\n\nR$ 1459,00\n\n(=) VALOR DO ISS:\n\nRETENÇÕES FEDERAIS\n\nPIS: R$ 0,00   COFINS: R$ 0,00   IR: R$ 0,00   CSLL: R$ 0,00   INSS: R$ 0,00\n\nOUTRAS INFORMAÇÕES\n\nDocumento emitido por ME ou EPP optante pelo simples nacional;\n\npowered by eNotas Gateway\n\n\x0c'


def test_detect_infomix_enotas():
    dummy_path = "tests/dummy_infomix_enotas.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    try:
        ex = SPPdfExtractor(dummy_path)
        ex.raw_text = MOCK_TEXT_INFOMIX
        assert ex._detect_layout() == 'password_enotas'
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_extract_infomix_enotas_layout(monkeypatch):
    dummy_path = "tests/dummy_infomix_full.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT_INFOMIX)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        assert nfse.numero == "202600000001638"
        assert nfse.codigo_verificacao == "431E206D7"
        assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "03/06/2026 12:06:58"
        assert nfse.competencia.strftime("%m/%Y") == "06/2026"
        # "01.07 / 107 -" (código interno de só 3 dígitos, sem zero à
        # esquerda) -> usa o item "01.07" (sem ponto) = "0107".
        assert nfse.servico_codigo == "0107"
        assert "Suporte técnico em informática" in nfse.discriminacao
        assert nfse.optante_simples_nacional is True

        prest = nfse.prestador
        assert prest.cnpj_cpf == "29869622000132"
        assert prest.inscricao_municipal == "0010029058011"
        assert prest.razao_social == "INFOMIX SOLUCOES EM TECNOLOGIA LTDA"
        assert prest.endereco.logradouro == "AVENIDA PREFEITO CELSO ALVES PINHEIRO DA SILVA"
        assert prest.endereco.numero == "103"
        assert prest.endereco.complemento == "SALA 105"
        assert prest.endereco.bairro == "CENTRO"
        assert prest.endereco.municipio == "Lauro de Freitas"
        assert prest.endereco.codigo_municipio == "2919207"
        assert prest.endereco.uf == "BA"
        assert prest.endereco.cep == "42702580"
        assert prest.email == "financeiro@infomixtecnologia.com.br"
        assert prest.telefone == "71999031348"

        # Tomador: rótulos "NOME/RAZÃO SOCIAL"+"E-MAIL" despejados juntos
        # antes dos 2 valores — sem o fix, razão social saía "E-MAIL".
        tom = nfse.tomador
        assert tom.cnpj_cpf == "07345543000190"
        assert tom.razao_social == "TEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDA"
        assert tom.endereco.logradouro == "Rua Território do Amapá"
        assert tom.endereco.numero == "146"
        assert tom.endereco.complemento == "CASA 02"
        assert tom.endereco.bairro == "Pituba"
        assert tom.endereco.municipio == "Salvador"
        assert tom.endereco.codigo_municipio == "2927408"
        assert tom.endereco.uf == "BA"
        assert tom.endereco.cep == "41830540"

        val = nfse.valores
        assert val.valor_servicos == pytest.approx(1459.00)
        assert val.valor_deducoes == pytest.approx(0.0)
        assert val.base_calculo == pytest.approx(1459.00)
        assert val.aliquota == pytest.approx(0.03)
        assert val.valor_liquido_nfse == pytest.approx(1459.00)

        assert nfse.avisos == []
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__])
