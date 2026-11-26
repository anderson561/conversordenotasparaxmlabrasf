# -*- coding: utf-8 -*-
"""Fatura Sem Parar nº 714633808 (fatura 26228882949), "Scan2026-11-25_081510.pdf"
(1 página escaneada, "Página 1/2") - achado real 2026-11-26, layout
`sem_parar_fatura`, variante SEM rótulo "Subtotal", cliente Nordeste Tubetes.

Impresso (conferido no recorte da página): placas 46,20 D + 207,90 D +
909,20 D, Outras Arrec. 0,00, TOTAL 1.163,30 D (com um "✓" de caneta ao lado).
Antes: ValorServicos/Base/Líquido 0,00. O OCR perde a vírgula e lê o "D" como
"0" no TOTAL ("TOTAL 1.163300 7") e na coluna TOTAL de duas placas
("207900", "909200"); um "|" espúrio separa placa e tag na 1ª linha. Nenhuma
leitura vale sozinha: o TOTAL só é aceito porque bate ao centavo com a soma
de TODAS as placas lida pela mesma convenção.

MOCK é o texto REAL do Tesseract para a página (verbatim).
"""
import pytest

from src.extractors.pdf_extractor import SPPdfExtractor

MOCK = """\
SEM*

SEM PARAR INSTITUIÇÃO DE PAGAMENTO LTDA.
Av. Dra. Ruth Cardoso, 7221, Andares 17, 18, 19€ 25 parte -
05425-902 - Pinheiros - São ?auio/SP

CNPJ/MF: 04.088.208/0001-65 - Insc.

NOTA FISCAL FATURA DE SERVIÇOS
Nº DA FATURA: 26228882949

Página 1/2

Central de Relacionamento
4002 1552 (Capitais e regiões metropolitanas)
0800 01502 52 (Desnais | ocalidades)

PARAR

EMPRESAS

Nome: Nordeste Tubetes Embalagens Ltda Me
CNPJ: 11.474,414/0001-79

Endereço: Boa Viagem, 146 0

Bairro; Parque Petropolis

CEP: 42850-000

Cidade/UF; Dias D'avila - BA

Nº da Fatura: 26228882949
Nº da Nota Fiscal: 714633808

Código do Cliente: 4611706

E-Mail: rodrigonordestetubetes.com.br
CPF/CNPJ: 11.474,414/0001-79
Banco/Agência: 341/9658

Data de Emissão: 13/10/26

Data de Fechamento: 13/10/26
Débito em conta corrente

Banco Itau

Agência: 9658

Data de Vencimento: 20/10/26
Prev. próx. faturamento: 13/11/26

PAGUE AGORA.
É RÁPIDO, SEGURO E EM ATÉ DX,

MANTENHA O IPVA DA SUA FROTA EM DIA,

SEM PARAR EMPRESAS SEM PARAR À OPERAÇÃO.

APAGAR AGORA À

Aproveite nossas condições especiais e Faça a inclusão de novos veículos através do portal Sem Parar Empresas.

Acesse: www.sempararempresas.com.br/login 1% HD 0 MNA id) 7

Extrato de Uso
Resumo da sua Fatura
Placa Tag Pref. Plano Contratado Passagens Qtd Estacionamento Qtd Estabelecimento Qtd ValePedágio Qtd TOTAL
GHFSGA8 | 0746771722 0,00 46200 6 0,00 o 0,00 o 0,00 0 4620D
PDCZIAS 0736697948 0,00 20790D 27 0,00 º 0,00 o 0,00 o 207900
SIW4B44 0742130710 000 102200 13 807,00 D 4 0,00 o 0,00 o 909200
Adesão Qtd Crédito Qtd Encargos Impostosretidos OutrasArrec. Qtd QutrosServ. Qtd Demais itens VP Qtd
0,00 (o) 0,00 0 0,00 0,00 0,00 o 0,00 º 0,00 o
TOTAL 1.163300 7
Descritivo: GHFSGA4S - Plana: PAGAMENTO COM CARGA PROGRAMADA
Detalhamento das Passagens por Pedágios
Data Concessionária Praça Cat Valor(R$)
20/09/26 BAHIA NORTE BAS39, KM016+000, NORTE, VIA PARAFUSO 1 770D
20/09/26 BAHIA NORTE BAS29, KMO16+000, SUL, VIA PARAFUSO 1 7100
27/09/26 BAHIA NORTE BAS39, KM008+000, NORTE, SIMOES FILHO 1 710D
27/09/26 BAHIA NORTE BAS39, KM008+000, SUL, SIMOES FILHO a] 7100
30/09/26 BAHIA NORTE BAS39, KM016+000, NORTE, VIA PARAFUSO 1 770D
30/09/26 15:04:34 BAHIA NORTE BAS39, KM008+000, SUL, SIMOES FILHO 1 770D
TOTAL PEDÁGIO 46,20 D
Descritivo: PDC2148 - Plano: PAGAMENTO COM CARGA PROGRAMADA
Detalhamento das Passagens por Pedágios
Data Concessionária Praça cat Valor(R$)
14/09/26 BAHIA NORTE BAS39, KM016+000, NORTE, VIA PARAFUSO 1 7700
14/09/26 BAHIA NORTE BAS39, KM016+000, SUL, VIA PARAFUSO 1 7,700
17/09/26 BAHIA NORTE BAS39, KM016+000, NORTE, VIA PARAFUSO 1 770D
17/09/26 BAHIA NORTE BAS39, KMO16+000, SUL, VIA PARAFUSO 1 7100
18/09/26 BAHIA NORTE BAS39, KM016+000, NORTE, VIA PARAFUSO 1 7700
18/09/26 BAHIA NORTE BAS539, KM008+000, SUL, SIMÕES FILHO f 770D
21/09/26 BAHIA NORTE BAS39, KMO16+000, NORTE, VIA PARAFUSO 1 770D

Cuidado com os golpes e fraudes! Contar com nossos canais digitais é a Forma mais Fácil de garantir sua segurança! Por isso, em caso de necessidade de um novo boleto, utilize
exclusivamente: portal Sem Parar Empresas e Portal de Negociação!

Ao efetuar o pagamento de um boleto Sem Parar, confira se o beneficiário é SEM PARAR INSTITUIÇÃO DE PAGAMENTOS LTDA, com o CNPS 04.058.208/0001-65. Atenção: Jamais
compartilhe suas senhas com terceiros.”

Central de Relacionamento
4002 1552 (Capitais e regiões metropolitanas)
0800 015 02 52 (Demais localidades)

SAC 0800 723 2245
SAC (Deficiência auditiva ou de fala) 0800 722 0270
Ouvidoria 0800 770 0686

90ZLL9%
"""


def _parse(monkeypatch, tmp_path, mock):
    caminho = tmp_path / "Scan2026-11-25_081510.pdf"
    caminho.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: mock)
    notas = SPPdfExtractor(str(caminho)).parse_multiple()
    assert len(notas) == 1
    return notas[0]


@pytest.fixture
def nota(monkeypatch, tmp_path):
    return _parse(monkeypatch, tmp_path, MOCK)


def test_texto_real_tem_as_leituras_degradadas():
    assert "Subtotal" not in MOCK
    assert "TOTAL 1.163300 7" in MOCK
    assert "207900" in MOCK and "909200" in MOCK


def test_numero(nota):
    assert nota.numero == "714633808"


def test_valor_servicos_e_liquido_igual_total_impresso(nota):
    v = nota.valores
    assert v.valor_servicos == pytest.approx(1163.30)
    assert v.valor_liquido_nfse == pytest.approx(1163.30)


def test_base_aliquota_iss_seguem_convencao_zerada(nota):
    v = nota.valores
    assert v.base_calculo == 0.0
    assert v.aliquota == 0.0
    assert v.valor_iss == 0.0
    assert any("ZERADOS propositalmente" in a for a in nota.avisos)


def test_aviso_de_total_conferido_e_sem_aviso_de_zerado(nota):
    assert any("bater ao centavo" in a for a in nota.avisos)
    assert not any("Valor dos serviços ZERADO" in a for a in nota.avisos)


def test_total_degradado_sem_conferencia_das_placas_fica_zerado(monkeypatch, tmp_path):
    """Placa adulterada (207900 -> 207800): a soma não bate com o TOTAL
    degradado, então nada é aceito - sentinela 0,00 + aviso."""
    n = _parse(monkeypatch, tmp_path, MOCK.replace("207900", "207800"))
    assert n.valores.valor_servicos == 0.0
    assert any("Valor dos serviços ZERADO" in a for a in n.avisos)


def test_placa_ilegivel_descarta_conferencia(monkeypatch, tmp_path):
    n = _parse(monkeypatch, tmp_path, MOCK.replace("909200", "9O92OO"))
    assert n.valores.valor_servicos == 0.0
