import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
import os

# Texto real extraído via pdfminer.high_level.extract_text() da nota de
# cobrança "Loc Macedo 12366.pdf" (SUL&SEG - locação de equipamento de
# alarme). Preservada a ordem exata produzida pelo pdfminer, incluindo a
# inversão em que o item da tabela ("LOCAÇÃO DO EQUIPAMENTO DE ALARME")
# aparece ANTES do cabeçalho da tabela ("DESCRIÇÃO QUANTIDADE...").
MOCK_TEXT = """SUL&SEG SERVICOS DE MANUT ELET EIRELI - ME
Endereço:

AV.BRIGADEIRO ALBERTO COSTA MATOS 103

Bairro:

ARACUI

Fone/Fax:

(71)  3378-7661

DESTINATÁRIO

NOME/RAZÃO SOCIAL

Município: LAURO DE FREITAS/BA
CEP:
42702-010

NOTA DE COBRANÇA  Nº

20260000012366

PG                  1 / 1

VIA UNICA

CNPJ

Data da Emissão

18.294.792/0001-10

INSCRIÇÃO ESTADUAL

146758009

14/07/2026

VENCIMENTO

C.N.P.J./C.P.F.

00001004

MACEDO COMERCIAL DE CALCADOS LTDA

05/08/2026

04.074.648/0003-25

ENDEREÇO

RUA SAO CRISTOVAO

LOT. JARDIM METROPOLE QD-G

MUNICÍPIO

LAURO DE FREITAS

DADOS DO DOCUMENTO

NÚMERO

1241

BAIRRO

ITINGA

CEP

42700-000

FONE/FAX

(71) 98212-6107

UF

BA

INSCRIÇÃO ESTADUAL

ISENTO

LOCAÇÃO DO EQUIPAMENTO DE ALARME

1

R$ 40,00

R$ 40,00

DESCRIÇÃO

QUANTIDADE

VALOR UNITÁRIO

VALOR TOTAL

INFORMAÇÕES ADICIONAIS

VALOR LIQUIDO DA NOTA DE COBRANÇA

R$ 40,00

OPERAÇÃO NÃO SUJEITA AO I.S.S. DE ACORDO COM A LEI COMPLEMENTAR 116/03.

ATESTAMOS QUE OS DADOS ACIMA CONFEREM COM OS BENS CEDIDOS EM LOCAÇÃO.

DATA DO RECEBIMENTO

IDENTIFICAÇÃO E ASSINATURA DO RECEBEDOR

NOME LEGÍVEL

NOTA DE COBRANÇA Nº

___ / ____ / ______

_______________________________________

________________________________

20260000012366

"""


def test_extract_sulseg_cobranca_layout(monkeypatch):
    dummy_path = "tests/dummy_sulseg_cobranca.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        extractor.raw_text = MOCK_TEXT
        extractor.layout = extractor._detect_layout()

        assert extractor.layout == 'sulseg_cobranca'

        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        assert nfse.numero == "20260000012366"
        assert nfse.codigo_verificacao == "FATURA"
        assert nfse.data_emissao.strftime("%d/%m/%Y") == "14/07/2026"
        assert nfse.competencia.strftime("%m/%Y") == "07/2026"
        assert nfse.servico_codigo == "0601"
        assert nfse.discriminacao == "LOCAÇÃO DO EQUIPAMENTO DE ALARME"

        prest = nfse.prestador
        assert prest.cnpj_cpf == "18294792000110"
        assert prest.inscricao_municipal == "0010030574"
        assert prest.razao_social == "SUL&SEG SERVICOS DE MANUT ELET EIRELI - ME"
        assert prest.endereco.logradouro == "AV. BRIGADEIRO ALBERTO COSTA MATOS"
        assert prest.endereco.numero == "103"
        assert prest.endereco.bairro == "Aracuí"
        assert prest.endereco.codigo_municipio == "2919207"
        assert prest.endereco.uf == "BA"
        assert prest.endereco.cep == "42702010"

        tom = nfse.tomador
        assert tom.cnpj_cpf == "04074648000325"
        assert tom.razao_social == "MACEDO COMERCIAL DE CALCADOS LTDA"
        assert tom.endereco.logradouro == "RUA SAO CRISTOVAO"
        assert tom.endereco.complemento == "LOT. JARDIM METROPOLE QD-G"
        assert tom.endereco.bairro == "ITINGA"
        assert tom.endereco.codigo_municipio == "2919207"
        assert tom.endereco.uf == "BA"
        assert tom.endereco.cep == "42700000"

        val = nfse.valores
        assert val.valor_servicos == pytest.approx(40.00)
        assert val.valor_liquido_nfse == pytest.approx(40.00)
        assert val.base_calculo == pytest.approx(0.00)
        assert val.aliquota == pytest.approx(0.00)
        assert val.valor_iss == pytest.approx(0.00)
        assert val.iss_retido is False

        assert nfse.avisos == []
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__])
