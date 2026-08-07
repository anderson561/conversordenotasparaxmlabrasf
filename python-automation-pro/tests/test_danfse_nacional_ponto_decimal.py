# -*- coding: utf-8 -*-
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_NACIONAL

# Texto REAL extraído via pdfminer (PDF digital, não escaneado) da DANFSe
# Nacional nº 730080 — Thomson Reuters Brasil -> Cafés Finos Vitória da
# Conquista Ltda, Prefeitura Municipal de Criciúma/SC, plataforma Domínio
# Sistemas. Bug real: TODOS os campos monetários estruturados da grade saem
# com PONTO decimal ("R$ 372.96") em vez da vírgula brasileira, ao contrário
# de toda outra DANFSe Nacional já vista (ex.: MOCK_OCR de
# test_danfse_nacional_layout.py, que usa vírgula). O regex antigo de
# _extrair_valores (LAYOUT_NACIONAL) exigia vírgula e por isso todo campo
# saía zerado ("valor zerado" reportado pelo usuário).
MOCK_TEXT = """DANFSEe v1.0
Documento Auxiliar da NFS-e

Prefeitura Municipal de Criciúma
Secretaria Municipal da Fazenda
(48) 3431-0074
tributos@criciuma.sc.gov.br

Chave de Acesso da NFS-e
NFS42046082200910509001305000000073008026078018292222

Número da NFS-e
730080

Número do DPS
705742

Competência da NFS-e
19/07/2026

Série da DPS
1

EMITENTE DA NFS-e
Prestador de Serviço

CNPJ / CPF / NIF
00.910.509/0013-05

Data e Hora da emissão da NFS-e
19/07/2026 22:06:43

Data e Hora de emissão da DPS
17/07/2026 10:52:42

Inscrição Municipal

Telefone
(048) 3461-1000

Nome / Nome Empresarial
THOMSON REUTERS BRASIL CONTEUDO E TECNOLOGIA

E-mail
faturamento@dominiosistemas.com.br

Endereço
AVENIDA CENTENARIO, 7405, NOSSA SENHORA

Simples Nacional na Data de Competência
Não Optante

TOMADOR DO SERVIÇO

CNPJ / CPF / NIF
42.221.481/0001-05

Nome / Nome Empresarial
CAFES FINOS VITORIA DA CONQUISTA LTDA

Endereço
ROD KM 1070, 0, FELICIA

Município
Criciuma - SC

CEP
88813-325

Regime de Apuração Tributária pelo SN
-

Inscrição Municipal

E-mail
cqscf@hotmail.com

Telefone
(77) 3423-3114

Município
VITORIA DA CONQUISTA -

CEP
45028-135

INTERMEDIÁRIO DO SERVIÇO NÃO IDENTIFICADO NA NFS-e

SERVIÇO PRESTADO
Código de Tributação Nacional
010701 - Suporte tecnico em informatica, inclusive
instalacao, configuracao e manutencao de
programas de computacao e bancos de dados.

Código de Tributação Municipal
-

Local da Prestação
Criciuma - SC

País da Prestação
-

Descrição do Serviço
DESCRICAO DO ITEM: (Dominio Personalizado conf. contrato(s): 193024 comp.: 7/2026. - Valor: R$ 372,96)
VENCIMENTOS: 10/08/2026 - 372,96
OBSERVACAO: (Valor dos tributos incidentes (Lei no 12.741/2012) R$0,00.)

TRIBUTAÇÃO MUNICIPAL

Tributação do ISSQN
Operação Tributável

Tipo de Imunidade
-

Valor do Serviço
R$ 372.96

BC ISSQN
R$ 372.96

TRIBUTAÇÃO FEDERAL

IRRF
R$ 0.00

País Resultado da Prestação do Serviço
-

Município de Incidência do ISSQN
Criciúma/SC

Regime Especial de Tributação
Nenhum

Suspensão Exigibilidade ISSQN
-

Número Processo Suspensão
-

Benefício Municipal
-

Desconto Incondicionado
-

Alíquota Aplicada
2.00%

Total Deduções/Reduções
R$ 0.00

Retenção do ISSQN
Não Retido

Cálculo do BM
-

ISSQN Apurado
R$ 7.46

Contribuição Previdenciária - Retida
-

Contribuições Sociais - Retidas
R$ 17.34

Descrição Contrib. Sociais Retidas
3 - PIS/COFINS/CSLL Retidos

PIS-Débito Apuração Própria
R$ 2.42

COFINS - Débito Apuração Própria
R$ 11.19

VALOR TOTAL DA NFS-e

Valor do Serviço
R$ 372.96

Desconto Condicionado
-

Desconto Incondicionado
-

ISSQN Retido
-

Total das Retenções Federais
R$ 17.34

PIS/COFINS  - Débito Apur. Própria
R$ 13.61

Valor Líquido da NFS-e
R$ 355.62

TOTAIS APROXIMADOS DOS TRIBUTOS

Federais
0,00

Estaduais
0,00

Municipais
0,00

INFORMAÇÕES COMPLEMENTARES

NBS: 115013000
"""


def test_detect_danfse_nacional_criciuma():
    dummy_path = "tests/dummy_danfse_criciuma.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    try:
        ex = SPPdfExtractor(dummy_path)
        ex.raw_text = MOCK_TEXT
        assert ex._detect_layout() == LAYOUT_NACIONAL
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_extract_danfse_nacional_valores_ponto_decimal(monkeypatch):
    """BUG: valores estruturados desta nota vêm com ponto decimal
    ("R$ 372.96"), não vírgula — antes do fix, toda a grade saía zerada."""
    dummy_path = "tests/dummy_danfse_criciuma_full.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    # PDF digital (não escaneado): pdfminer devolve o texto real diretamente.
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        assert nfse.numero == "730080"

        v = nfse.valores
        assert v.valor_servicos == pytest.approx(372.96)
        assert v.base_calculo == pytest.approx(372.96)
        assert v.valor_iss == pytest.approx(7.46)
        assert v.valor_liquido_nfse == pytest.approx(355.62)
        assert v.iss_retido is False
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
