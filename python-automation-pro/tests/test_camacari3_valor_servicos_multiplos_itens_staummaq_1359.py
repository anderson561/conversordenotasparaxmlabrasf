# -*- coding: utf-8 -*-
r"""Texto REAL do OCR (Tesseract) da NFS-e de Camaçari/BA ESCANEADA
(`LAYOUT_CAMACARI_3`) — pág. 3 do lote real "STAUMMAQ - NFSe TERCEIROS.pdf",
nota nº 1359, GRAFICA E EDITORA ITACIMIRIM LTDA -> STAUMMAQ SERVICOS
TECNICOS AUTOMACA MOTORES E MAQ LTDA. Reportado pelo usuário: o XML saiu com
`ValorServicos` = 500,00, mas o correto é R$ 2.700,00 (soma de 4 itens
impressos na grade: 500,00 + 500,00 + 750,00 + 950,00).

Causa raiz: esta nota discrimina QUATRO itens de serviço na mesma grade
"DISCRIMINAÇÃO DOS SERVIÇOS", não UM só (o caso já coberto pela nota nº 148 —
ver `test_camacari3_valor_dos_servicos_truncado_guarajuba.py`). O regex de
"linha do item" (`m_item`, formato "<qtd>,0000 <unitário> <total>") usava
`re.search`, que só acha a PRIMEIRA linha que casa por inteiro. Aqui a 1ª
linha quebra o padrão por ruído de OCR na coluna do unitário ("so,007" em vez
de "50,00") e a 4ª quebra por um "J" colado ("1,90 J" em vez de "1,90"), então
a primeira linha que de fato CASA é a 2ª ("10,0000 50,004 500,00") — e o
extrator usava o total dessa UMA linha isolada (500,00) como se fosse o valor
da nota inteira.

A CÉLULA da grade ("Valor dos Serviços (R$) 2.700,00") já vem correta — é o
próprio CPqD que soma os 4 itens ao imprimir a nota — e é justamente essa
célula que `BaseCalculo`/`ValorLiquidoNfse` já liam direto (regexes
independentes, nunca passavam pela lógica de "linha do item"), por isso os
dois já saíam certos (2.700,00) antes desta correção, só `ValorServicos`
saía errado (500,00).

Quirks deliberadamente preservados para travar as regressões:
 - a linha do 1º item sai com o unitário garbled ("so,007" em vez de "50,00")
   e por isso NÃO casa no regex de linha de item;
 - a linha do 4º item sai com um "J" colado no unitário ("1,90 J" em vez de
   "1,90") e por isso também NÃO casa;
 - a linha de "CONDIÇÕES DE PAGAMENTO" contém um "0,0000 0,00 2, 00" que
   CASARIA no regex de linha de item por acidente, mas o total capturado
   ("2,") não tem os 2 dígitos de centavo (`,\d{2}$`) — descartado pela
   validação de total "completo";
 - Base de Cálculo/Valor Líquido da Nota já saem corretos (2.700,00) mesmo
   sem a correção — a prova de que vêm de uma leitura independente da grade,
   não da lógica de "linha do item" que causava o bug.
"""
import os

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_TEXT = """
Número da Nota
1359 V
Data de Emissão
21/08/2026 11:51
Código de autenticidade ii
JMAUOFJM6
0006158001
Nº: 00001
UF: BA

Número da Nota
1359 V
Data de Emissão
21/08/2026 11:51
Código de autenticidade ii
JMAUOF JM6
3001
Nº: 00001
UF: BA

INnumETO da INota
1359 V
Data de Emissão
21/08/2026 11:51
Codigo de autenticidade a
JMAUOFJM6
0006158001
Nº: 00001
UF: BA

E ===
dee PREFEITURA MUNICIPAL DE CAMAÇARI 1359 V
e Secretaria da Fazenda e
o Neo E 21/08/2026 11:51
O aan NOTA FISCAL DE SERVIÇOS ELETRÔNICA Código de autenticidade
El ES aaa qu Po Mo Ba Og E pç TOR RL NU TO DO a O a Ri ll JMAUOFJM6
PRESTADOR DE SERVIÇOS PR OTA NA dede RN pegos ua?
Nome/Razão Social: GRAFICA E EDITORA ITACIMIRIM LTDA
CPF/CNPJ: 40.571.614/0001-48 Y Inscrição Municipal: 0006158001
Logradouro: RUA DO OURO Nº: 00001
Compl.:  QUADRA1 Bairro: POLO DE APOIO
o CEP: 42801729 Município: CAMAÇARI UF: BA
TOMADOR DESERVIÇOS
Nome/Razão Social: STAUMMAQ SERVICOS TECNICOS AUTOMACA MOTORES E MAQ LTDA
CPF/CNPJ: 02.370.080/0001-00 Inscrição Municipal:
Logradouro: VIA URBANA Nº: 01
Compl.: Bairro: CIA SUL
CEP: 43700000 Município: SIMÕES FILHO UF: BA
DISCRIMINAÇÃO DOS SERVIÇOS
DESCRIÇÃO QTD VALOR UNIT (R$) , VALOR TOTAL (R$)
BLOCOS RELATORIO DE BALANCEAMENTO F-25 10,0000 so,007 500,00
BLOCOS DADOS BOBINAGEM MOTORES DE BAIXA TENSAO 10,0000 50,004 500,00
BLOCOS DE PROGRAMAÇÃO DE SERVIÇOS (50X1, OFÍCIO) 10,0000 15,004 750,00
ETIQUETAS EQUIPAMENTOS LIBERACAO CONCLUIDA; 500,0000 1,90 J 950,00
CONDIÇÕES DE PAGAMENTO: 30 DD - BANCO DO GRASTL "AGÊNCIA: 1238-6 - 0,0000 0,00 2, 00
C/C: 10900-2 - CONFORME ORDEM DE COMPRA DE Nº 008298
rem ren
vs ;
o É Roso]
SSB x NU por gens
'
Retenções (R$) Totais (R$) /
PIS: Ao 0,00 | Valor dos Serviços (R$) 2.700,00
COFINS: 0,00 | Deduções (-) 0,00
INSS: ) 0,00 |Base de Cálculo (=) 2.700,00
IR: VIad 0,00 | Alíquota (%) 2,01
CSLL: b 0,00 |Valor do ISS (R$) 54,27
Outras: BUD 0,00 | Valor Líquido da Nota (=) 2.700,00
Total de Retenções: 0,00 .
Tipo de tributação: A RECOLHER PELO PRESTADOR Data da prestação do serviço: 21/08/2026
Município da prestação do serviço: 2905701 - CAMACARI
Município da tributação: 2905701 - CAMACARI
CNAE: o , :
Serviço: 001305 - COMPOSIÇÃO GRÁFICA, INCLUSIVE CONFECÇÃO DE IMPRESSOS GRÁFICOS, FOTOCOMPOSIÇÃO, CLICHERIA, |
ZINCOGRAFIA, LITOGRAFIA E FOTOLITOGRÁFIA, EXCETO SE DESTINADOS A POSTERIOR OPERAÇÃO DE COMERCIALIZAÇÃO OU
INDUSTRIALIZAÇÃO, AINDA QUE INCORPORADOS, DE QUALQUER FORMA, A OUTRA MERCADORIA QUE DEVA SER OBJETO DE
POSTERIOR CIRCULAÇÃO, TAIS COMO BULAS, ROTULOS, ETIQUETAS, CAIXAS, CARTUCHOS, EMBALAGENS E MANUAIS TÉCNICOS E
DE INSTRUÇÃO, QUANDO FICARÃO SUJEITOS AO ICMS.
CPqD -Gestão Pública Data Impressão: 21/08/2026 11:51
"""


@pytest.fixture
def nfse(monkeypatch):
    dummy_path = "tests/dummy_camacari3_staummaq_1359.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_TEXT)

    try:
        nfse_list = SPPdfExtractor(dummy_path).parse_multiple()
        assert len(nfse_list) == 1
        yield nfse_list[0]
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_identificacao_nota_1359(nfse):
    assert nfse.numero == "1359"
    assert nfse.prestador.cnpj_cpf == "40571614000148"
    assert nfse.tomador.cnpj_cpf == "02370080000100"


def test_valor_dos_servicos_soma_os_quatro_itens_da_grade(nfse):
    """Núcleo do fix: 500 + 500 + 750 + 950 = 2.700,00 — vindo da célula da
    grade (já correta), não de uma única linha de item isolada (500,00)."""
    val = nfse.valores
    assert val.valor_servicos == pytest.approx(2700.00)


def test_base_calculo_e_valor_liquido_continuam_corretos_sem_regressao(nfse):
    """Estes dois campos já liam certo ANTES da correção (vêm de regexes
    próprios, direto da grade, nunca passaram pela lógica de "linha de
    item") — a correção não pode alterar esse comportamento já validado."""
    val = nfse.valores
    assert val.base_calculo == pytest.approx(2700.00)
    assert val.valor_liquido_nfse == pytest.approx(2700.00)


def test_aliquota_e_iss_seguem_a_base_corrigida(nfse):
    val = nfse.valores
    assert val.aliquota == pytest.approx(0.0201, abs=0.0001)
    assert val.valor_iss == pytest.approx(54.27)


def test_nenhum_aviso_de_aliquota_zerada(nfse):
    # A alíquota derivada (54,27 / 2.700,00 ≈ 2,01%) é plausível — a guarda
    # de "alíquota > 100%" não deve disparar aqui.
    assert nfse.avisos == []


def test_quatro_linhas_de_item_existem_no_texto_mas_apenas_duas_casam_no_regex():
    """Ancora a premissa do fix: das 4 linhas de item impressas na nota, só a
    2ª e a 3ª casam por inteiro no regex de "linha do item" (a 1ª tem o
    unitário garbled "so,007", a 4ª tem um "J" colado no unitário "1,90 J").
    Se o OCR melhorar e todas as 4 passarem a casar, este teste avisa —
    mas o valor final (soma via célula da grade) não deve mudar."""
    import re
    linhas_com_qtd_decimal = re.findall(r'\d+,\d{4}\s+[\d\.,]+\s+[\d\.,]+', MOCK_TEXT)
    # 2 linhas de item completas (500,00 e 750,00) + 1 falso-positivo da
    # linha de "CONDIÇÕES DE PAGAMENTO" ("0,0000 0,00 2, 00" -> captura só
    # "0,0000 0,00 2," pelo regex, sem o " 00" final).
    assert len(linhas_com_qtd_decimal) == 3
    assert "500,00" in linhas_com_qtd_decimal[0]
    assert "750,00" in linhas_com_qtd_decimal[1]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
