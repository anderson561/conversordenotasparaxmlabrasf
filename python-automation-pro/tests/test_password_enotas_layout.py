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


if __name__ == "__main__":
    pytest.main([__file__])
