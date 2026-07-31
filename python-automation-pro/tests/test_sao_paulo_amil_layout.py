# -*- coding: utf-8 -*-
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_SAO_PAULO
import os

# Texto REAL do pdfminer (nota São Paulo/SP digital, prestador AMIL ASSISTÊNCIA
# MÉDICA INTERNACIONAL SA, tomador TEMIS PROJETOS DE MEIO AMBIENTE E
# SUSTENTABILIDADE LTDA). Preservado verbatim, incluindo o quirk que travava
# tudo: o pdfminer extraiu esta nota numa ordem física DIFERENTE da visual —
# os cabeçalhos "PRESTADOR DE SERVIÇOS"/"TOMADOR DE SERVIÇOS" ficam deslocados
# no MEIO dos próprios dados da entidade (o CNPJ do prestador chega a vazar
# sozinho, antes de qualquer cabeçalho; "TOMADOR DE SERVIÇOS" só aparece
# DEPOIS de Nome/Razão + CPF/CNPJ + Endereço do tomador já terem passado).
# O extrator genérico (usado por ~30 layouts, delimita bloco por cabeçalho de
# seção) erra o alvo nesse caso:
#  - CNPJ do prestador saía = CNPJ do tomador (07345543000270 em vez de
#    29309127000179) — o bloco do prestador nunca alcançava o CNPJ real;
#  - razão social do tomador saía "MORADA DA SERRA" (na verdade é o BAIRRO
#    dele) — o bloco do tomador começava depois do "Nome/Razão" real;
#  - logradouro vazio ("Não informado") em AMBAS as entidades;
#  - alíquota e valor do ISS zerados: a grade "Valor Total das Deduções /
#    Desconto Incond. / Base de Cálculo / Alíquota (%) / Valor ISS / Crédito
#    p/ Abatimento do IPTU" vem em 2 blocos separados (rótulos, depois
#    valores, mesma ordem) — mesmo efeito já tratado em LAYOUT_CAMACARI_2.
MOCK_TEXT = """PREFEITURA DO MUNICÍPIO DE SÃO PAULO
SECRETARIA MUNICIPAL DE FINANÇAS
NOTA FISCAL DE SERVIÇOS ELETRÔNICA - NFS-e

Número da Nota:
68372315
Data e Hora de Emissão:

07/04/2026 07:03:35

Código de Verificação:

CTIAMUQN

29.309.127/0001-79

PRESTADOR DE SERVIÇOS
Inscrição municipal:

39569896

AMIL ASSISTÊNCIA MÉDICA INTERNACIONAL SA

AV AV DOUTOR CHUCRI ZAIDAN - S/N 0 AND 6 A 23 TORRE EZ

CPF/CNPJ
Nome/Razão
Endereço
Bairro:

VILA SAO FRANCISCO (ZONA SUL)

Município:

SAO PAULO

UF

SP

CEP

04711-130

Nome/Razão

TEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDA

CPF/CNPJ

07.345.543/0002-70

Inscrição municipal:

Endereço

AVENIDA BRASIL 19 SALA 3 QDA A 47

TOMADOR DE SERVIÇOS

Bairro:

MORADA DA SERRA

Município:

CUIABA

UF:

MT

CEP:

78055-508

E-mail:

COBERTURA DE CUSTOS DE ASSISTÊNCIA MÉDICA E HOSPITALAR

REFERENTE AO PERÍODO DE: 22/04/2026 À 21/05/2026

DISCRIMINAÇÃO DOS SERVIÇOS

R$ 24.488,88

Vencto:

22/04/2026

158275400/0

Compe: Abril/2026

Código do Serviço

05312 - Planos de saúde que se cumpram através de serviços de terceiros contratados e credenciados.

VALOR TOTAL DA NOTA =

R$ 24.488,88

Valor Total das Deduções

Desconto Incond.

Base de Cálculo

Alíquota (%)

Valor ISS

Crédito p/ Abatimento do IPTU

0,00

0,00

24.488,88

2,00

489,78

0,00

- Esta NFS-e foi emitida com respaldo na Lei n. 14.097/2005
- Esta NFS-e substitui o RPS No.24261902 Série PJSPS, emitido em 07/04/2026

OUTRAS INFORMAÇÕES

Autenticação Mecânica
"""


def test_detect_sao_paulo_amil():
    dummy_path = "tests/dummy_sao_paulo_amil.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    try:
        ex = SPPdfExtractor(dummy_path)
        ex.raw_text = MOCK_TEXT
        assert ex._detect_layout() == LAYOUT_SAO_PAULO
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_extract_sao_paulo_amil_layout(monkeypatch):
    dummy_path = "tests/dummy_sao_paulo_amil_full.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        assert nfse.numero == "68372315"
        assert nfse.codigo_verificacao == "CTIAMUQN"

        # Prestador: CNPJ correto (não o do tomador, que ficava preso dentro
        # do bloco delimitado por cabeçalho).
        assert nfse.prestador.cnpj_cpf == "29309127000179"
        assert nfse.prestador.inscricao_municipal == "39569896"
        assert nfse.prestador.razao_social == "AMIL ASSISTÊNCIA MÉDICA INTERNACIONAL SA"
        assert nfse.prestador.endereco.logradouro == "AV AV DOUTOR CHUCRI ZAIDAN - S/N 0 AND 6 A 23 TORRE EZ"
        assert nfse.prestador.endereco.bairro == "VILA SAO FRANCISCO (ZONA SUL)"
        assert nfse.prestador.endereco.municipio == "SAO PAULO"
        assert nfse.prestador.endereco.codigo_municipio == "3550308"
        assert nfse.prestador.endereco.uf == "SP"
        assert nfse.prestador.endereco.cep == "04711130"

        # Tomador: razão social correta (não o bairro "MORADA DA SERRA").
        assert nfse.tomador.cnpj_cpf == "07345543000270"
        assert nfse.tomador.razao_social == "TEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDA"
        assert nfse.tomador.endereco.logradouro == "AVENIDA BRASIL 19 SALA 3 QDA A 47"
        assert nfse.tomador.endereco.bairro == "MORADA DA SERRA"
        assert nfse.tomador.endereco.municipio == "CUIABA"
        assert nfse.tomador.endereco.codigo_municipio == "5103403"
        assert nfse.tomador.endereco.uf == "MT"
        assert nfse.tomador.endereco.cep == "78055508"

        # Valores: grade em 2 blocos (rótulos, depois valores) — alíquota e
        # ISS não podem mais zerar.
        val = nfse.valores
        assert val.valor_servicos == pytest.approx(24488.88)
        assert val.base_calculo == pytest.approx(24488.88)
        assert val.aliquota == pytest.approx(0.02)
        assert val.valor_iss == pytest.approx(489.78)
        assert val.valor_liquido_nfse == pytest.approx(24488.88)

        assert nfse.avisos == []
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
