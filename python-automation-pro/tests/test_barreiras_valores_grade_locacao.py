# -*- coding: utf-8 -*-
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
import os

# Texto REAL do pdfminer (nota nº 1162, OLIVEIRA & CHAVES SERVIÇOS E LOCAÇÕES
# LTDA -> SÃO PEDRO CONSTRUTORA LTDA - locação de caminhão guindauto, NÃO
# sujeita a ISS, emitida pelo portal municipal de Barreiras/BA). PDF digital
# (texto embutido), preservado verbatim.
#
# Regressão travada aqui: o campo "VALOR SERVIÇO (R$)" nesta nota vem numa
# grade de 3 colunas - "VALOR SERVIÇO (R$) DEDUÇÕES (R$) DESCONTO
# INCONDICIONAL" com os 3 rótulos primeiro, só depois os valores ("4.755,00
# 0,00"). O genérico assumia o valor colado ao próprio rótulo (variante
# "VALOR SERVIÇO (R$)\n16.473,00", já coberta por test_barreiras_layout.py) e
# caía no fallback zero nesta estrutura - o ERP contábil rejeitava a
# importação ("Valor contábil zerado para nota com situação diferente de
# cancelada").
#
# Quirk preservado: o valor da alíquota (2º valor do grupo "BASE CÁLCULO /
# ALÍQUOTA / ISS") vem com PONTO em vez de vírgula decimal ("0.00" em vez de
# "0,00") - nesta nota é sempre 0, então não afeta o resultado, mas é uma
# inconsistência do próprio PDF-fonte, não do extrator.
MOCK_TEXT = """NOTA FISCAL DE SERVIÇOS ELETRÔNICA - NFSe

MUNICIPIO DE BARREIRAS

Codigo de Verificação para Autenticação: acc8cde89

Endereço: Barreiras, Bahia, BA, 47800-390

CNPJ: 13.654.405/0001-95, E-mail: arrecadacao.tributos@barreiras.ba.gov.br

Data Fato Gerador

Exigibilidade de ISS

Regime Tributário

Número RPS

Serie RPS

19/05/2026

Exigível

Tributacao Normal

-

-

Tipo de Recolhimento

Simples

Local de Prestação

Local de Recolhimento

Não Retido

Optante

2903201 - Barreiras - BA

2903201 - Barreiras - BA

Emitido em

19/05/2026 08:26:56

Nº da Nota Fiscal

1162

PRESTADOR

Razão Social: OLIVEIRA & CHAVES SERVIÇOS E LOCAÇÕES LTDA
Nome Fantasia: LOKMAQ COMERCIO E ENGENHARIA
Endereço: Avenida VIRGÍNIA, 85,  ........  - Buritis
Barreiras - BA - CEP:  47804-512
E-mail: compras@lokmaq.com.br - Fone: (77)3611-2252 - Celular: (77)99908-4658 - Site:  ........
Inscrição Estadual:  ........  - Inscrição Municipal: 000023154 -  CPF/CNPJ: 45.258.583/0001-93

TOMADOR

Razão Social: SAO PEDRO CONSTRUTORA LTDA
Endereço: Rua RUA, 554, QUADRA 28, LOTE 09 - VILAS DO ATLANTICO
LAURO DE FREITAS - BA - CEP:  42708720
E-mail: sp@saopedroconstrutora.com.br - Fone: (77) 9810-7472 - Celular: (77) 99810-7472
Inscrição Estadual:  ........  - Inscrição Municipal: 353043 - CPF/CNPJ: 03.051.741/0001-90

990101 - Serviços sem a incidência de ISSQN e ICMS

00.00 - LOCAÇÃO DE BENS MÓVEIS

SERVIÇO NACIONAL

SERVIÇO

LOCAÇÃO DE CAMINHÃO GUINDAUTO PLACA PLY5C24 EM 14/05/2026/ 15/05/2026/ 16/05/2026 E 18/05/2026 OS N 311236121/2639.

DISCRIMINAÇÃO DOS SERVIÇOS

PAGAMENTO VIA BOLETO BANCÁRIO VENCIMENTO EM 03/06/2026.

OBSERVAÇÃO

VALOR SERVIÇO

(R$)

DEDUÇÕES

(R$)

DESCONTO INCONDICIONAL

4.755,00

0,00

DEMONSTRATIVO DOS TRIBUTOS FEDERAIS

INSS

(R$)

IR

(R$)

CSLL

(R$)

COFINS

(R$)

PIS

(R$)

(R$)

0,00

BASE CÁLCULO

(R$)

ALÍQUOTA

(%)

ISS

(R$)

4.755,00

0.00

0,00

DESCONTO
CONDICIONAL

(R$)

OUTRAS
RETENÇÕES

(R$)

VALOR LÍQUIDO

(R$)

0,00

0,00

0,00

0,00

0,00

0,00

0,00

4.755,00

Chave de acesso Ambiente de Dados Nacional: 29032011245258583000193260000000116226050004663799
(Valor Líquido = Valor Serviço - INSS - IR - CSLL - Outras Retenções - COFINS - PIS - Descontos Diversos - ISS Retido - Desconto Incondicional)

OUTRAS INFORMAÇÕES

ESTE DOCUMENTO FOI EMITIDO POR EMPRESA OPTANTE DO SIMPLES NACIONAL(Art. 23 da LC 123/2006), DEVENDO NESTA CONDIÇÃO O PRESTADOR
INFORMAR A ALÍQUOTA ENTRE 2 A 5%, CONFORME TABELA DE ENQUADRAMENTO DO SIMPLES NACIONAL DE ACORDO COM O SEU FATURAMENTO.

Consulte a autenticidade deste documento acessando o site https://www.barreiras.ba.gov.br/
"""


def test_extract_barreiras_valores_grade_locacao(monkeypatch):
    dummy_path = "tests/dummy_barreiras_grade.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        assert nfse.numero == "1162"
        assert nfse.codigo_verificacao == "ACC8CDE89"
        # Item "00.00 - LOCAÇÃO DE BENS MÓVEIS" -> 0000 (não é item real da
        # LC116, é o próprio portal sinalizando não-tributação).
        assert nfse.servico_codigo == "0000"

        assert nfse.prestador.cnpj_cpf == "45258583000193"
        assert nfse.prestador.razao_social == "OLIVEIRA & CHAVES SERVIÇOS E LOCAÇÕES LTDA"
        assert nfse.tomador.cnpj_cpf == "03051741000190"
        assert nfse.tomador.razao_social == "SAO PEDRO CONSTRUTORA LTDA"

        # Regressão principal: valor não pode mais cair no fallback zero.
        val = nfse.valores
        assert val.valor_servicos == pytest.approx(4755.00)
        assert val.base_calculo == pytest.approx(4755.00)
        assert val.aliquota == pytest.approx(0.0)
        assert val.valor_iss == pytest.approx(0.0)
        assert val.valor_liquido_nfse == pytest.approx(4755.00)

        assert "Valor dos serviços extraído como zero" not in nfse.avisos
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
