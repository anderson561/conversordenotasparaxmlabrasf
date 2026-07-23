import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
import os

# Texto real extraído via pdfminer de uma Fatura de Locação real emitida pela
# LOC BAHIA LOCACAO E MANUTENCAO DE EQUIPAMNTOS E FERRAMENTAS (locação de
# equipamento para a FOLHAS URBANAS LTDA, competência 06/2026). Layout
# genérico — cobre qualquer locadora de "Fatura de Locação" ainda não
# catalogada com detecção própria (ver LAYOUT_FATURA_LOCACAO_GENERICA).
# Preservado como veio do pdfminer, incluindo o vazamento de "Estado"/valor
# ("BA" solto entre "Estado:" e "E-mail:" na LOCADORA) e o typo de origem
# "EQUIPAMNTOS" (sem o "E").
MOCK_TEXT = """FATURA DE LOCAÇÃO

Data de emissão:

05/06/2026

Data de vencimento:

25/06/2026

NÚMERO:

788

CONTRATO: 702

LOCADORA

Razão Social: LOC BAHIA LOCACAO E MANUTENCAO DE EQUIPAMNTOS E FERRAMENTAS
Endereço: AV DORIVAL CAYMMI Nº 931  ITAPUA CEP: 41635-150
Cidade: SALVADOR
Telefone: (71) 3624-8320  (00) 0000-0000

Estado:

E-mail:

BA

CNPJ: 01.706.231/0002-69

LOCATÁRIO

Nome/Razão Social: FOLHAS URBANAS LTDA
Endereço: R PELICANO Nº 150 GALPAO PITANGUEIRAS CEP: 42701-340
Cidade: LAURO DE FREITAS
Telefone:

(71) 99219-0025

E-mail:

CNPJ:  43.886.789/0001-32

Estado: BA

QTDE - DESCRIÇÃO

EM DIÁRIAS

PERÍODO

VALOR

1 - CGB-0001   CORTADOR DE GRAMA A BATERIA

1

27/05/2026 a 28/05/2026

R$ 69,00

DESCONTO:

R$ 0,00

TOTAL: R$ 69,00

ACRÉSCIMO:

R$ 0,00

(Sessenta e Nove Reais)

DADOS ADICIONAIS:

Dados referentes ao contrato de locação Nº 702 com data de abertura em 27/05/2026

Endereço de entrega: R PELICANO 150 GALPAO PITANGUEIRAS LAURO DE FREITAS BA (71) 99219-0025

Endereço cobrança: R PELICANO 150 GALPAO PITANGUEIRAS LAURO DE FREITAS (71) 99219-0025

DADOS BANCÁRIOS: Banco SICREDI AG: 0903 Conta Corrente 99899-6. Se optar por utilizar o PIX: Chave PIX: 01.706.231/0002-69

Não é fato gerador do ISSQN a locação de bens móveis. Dispensado da emissão de notas fiscais. Conforme Lei Complementar 116 de 31/07/2003.

Natureza da operação: Locação de Bens Móveis

NÃO É VÁLIDO COMO RECIBO.

PROTOCOLO DE ENTREGA DA FATURA DE LOCAÇÃO Nº: 788
LOCADORA: LOC BAHIA LOCACAO E MANUTENCAO DE EQUIPAMNTOS E FERRAMENTAS  LOCATÁRIO: FOLHAS URBANAS LTDA

VENCIMENTO: 25/06/2026   VALOR: R$ 69,00

CONTRATO:  702

Data: _______/_____/_______ Assinatura: ___________________________________


"""


def test_extract_fatura_locacao_generica_layout(monkeypatch):
    dummy_path = "tests/dummy_fatura_locacao_generica.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        extractor.raw_text = MOCK_TEXT
        extractor.layout = extractor._detect_layout()

        assert extractor.layout == 'fatura_locacao_generica'

        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        assert nfse.numero == "788"
        assert nfse.codigo_verificacao == "FATURA"
        assert nfse.data_emissao.strftime("%d/%m/%Y") == "05/06/2026"
        assert nfse.competencia.strftime("%m/%Y") == "06/2026"
        assert nfse.servico_codigo == "0601"
        assert nfse.discriminacao == "CGB-0001 CORTADOR DE GRAMA A BATERIA"

        # Locadora: LOC BAHIA (Salvador/BA) — parseada do texto (sem hardcode).
        prest = nfse.prestador
        assert prest.cnpj_cpf == "01706231000269"
        assert prest.razao_social == "LOC BAHIA LOCACAO E MANUTENCAO DE EQUIPAMNTOS E FERRAMENTAS"
        assert prest.endereco.logradouro == "AV DORIVAL CAYMMI"
        assert prest.endereco.numero == "931"
        assert prest.endereco.complemento is None
        assert prest.endereco.bairro == "ITAPUA"
        assert prest.endereco.municipio == "SALVADOR"
        assert prest.endereco.codigo_municipio == "2927408"
        assert prest.endereco.uf == "BA"
        assert prest.endereco.cep == "41635150"
        assert prest.telefone == "(71) 3624-8320"

        # Locatário: FOLHAS URBANAS (Lauro de Freitas/BA) — "GALPAO" deve ser
        # reconhecido como complemento, não como parte do bairro (o bairro
        # real é PITANGUEIRAS, confirmado no layout PASSWORD/eNotas com a
        # mesma empresa).
        tom = nfse.tomador
        assert tom.cnpj_cpf == "43886789000132"
        assert tom.razao_social == "FOLHAS URBANAS LTDA"
        assert tom.endereco.logradouro == "R PELICANO"
        assert tom.endereco.numero == "150"
        assert tom.endereco.complemento == "GALPAO"
        assert tom.endereco.bairro == "PITANGUEIRAS"
        assert tom.endereco.municipio == "LAURO DE FREITAS"
        assert tom.endereco.codigo_municipio == "2919207"
        assert tom.endereco.uf == "BA"
        assert tom.endereco.cep == "42701340"
        assert tom.telefone == "(71) 99219-0025"

        val = nfse.valores
        assert val.valor_servicos == pytest.approx(69.0)
        assert val.valor_liquido_nfse == pytest.approx(69.0)
        assert val.base_calculo == pytest.approx(0.0)
        assert val.aliquota == pytest.approx(0.0)
        assert val.valor_iss == pytest.approx(0.0)

        assert nfse.avisos == []
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__])
