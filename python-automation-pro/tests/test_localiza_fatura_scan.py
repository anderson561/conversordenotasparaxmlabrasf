# -*- coding: utf-8 -*-
"""Fatura "FATURA / DUPLICATA" da Localiza ESCANEADA - recortes dedicados.

Achado real 2026-10-21, lote STAUMMAQ (scans de 16/10/2026):
  - AGMTZ-11929076 (Scan2026-10-16_110738.pdf, pag. 4): discriminacao generica
    e tomador "STAUMMAGQ" (impresso "STAUMMAQ");
  - AASSA-1517937 (Scan2026-10-16_110841.pdf, pag. 1): a caixa "Nº:" some da
    leitura de pagina inteira -> Numero 00000000;
  - AGMTZ-11998441 (Scan2026-10-16_110841.pdf, pag. 2): a celula "VALOR TOTAL"
    sai vazia (so "R$ 92443" sem virgula na coluna VALOR) -> ValorServicos
    0,00; bairro do tomador com o rotulo "INSC. ESTADUAL: 048137340" colado.

Fixtures = texto REAL devolvido por `_ocr_page` (leitura de pagina inteira +
as linhas sinteticas `LOCALIZA_*` anexadas pelos recortes de
localiza_fatura.py), verbatim. Sem PDF: `extract_text` e mockado.
"""
import os

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_LOCALIZA
from src.extractors import localiza_fatura as loc

# Pag. 4 de Scan2026-10-16_110738.pdf.
OCR_AGMTZ_11929076 = (
    'LOCALIZA RENT A CAR S/A ASSISTÊNCIA A CLIENTES\n'
    'AGENCIA MATRIZ\n'
    '\n'
    'TEL 0800 979 2020\n'
    'SLocaliza AV BERNARDO DE VASCONCELOS, 377 - CACHOEIRINHA\n'
    '\n'
    'assistenciaaclientes(Dlocaliza.com\n'
    '31150-000 - BELO HORIZONTE - MG\n'
    '\n'
    'CNPJ - 16.670.085/0001-55\n'
    '\n'
    'FATURA / DUPLICATA Nº: AGMTZ - 11929076\n'
    '\n'
    'CLIENTE: STAUMMAGQ SERVICOS TECNICOS AUTOMACAO MOTORES E CÓDIGO: 01945295\n'
    '\n'
    'MAQUINAS LTDA INSC. ESTADUAL: 048137340\n'
    'ENDEREÇO:URBANA, 1 CIA SUL - CIA SUL\n'
    '\n'
    'CEP/CID/UF:43721-450 - SIMOES FILHO - BA DATA DE EMISSÃO: 08/09/2026\n'
    'CNPJ: 02.370.080/0001-00\n'
    '\n'
    'RESSARCIMENTO DEADESPESA - MULTA DE TRÂNSITO, CONTRATO RLGA486217.\n'
    'CONFORME CONDIÇÕES GERAIS DO CONTRATO. PAGAMENTO DEVE SER\n'
    'EFETUADO PELA FATURA LOCALIZA, SENDO A GUIA DO ÓRGÃO APENAS PARA\n'
    'CONFERÊNCIA.\n'
    '. à R$ 136,67\n'
    'VALOR COBRADO PELA LOCALIZA SERÁ O VALOR DA INFRAÇÃO COM O »\n'
    'DESCONTO DE 20% CONCEDIDO PELO ÓRGÃO DE TRÂNSITO, ACRESCIDO DE TAXA\n'
    'ADMINISTRATIVA DE 25% SOBRE O VALOR ORIGINAL DA MULTA.\n'
    'PLACA(S): TYC7E19\n'
    '\n'
    '[O VENCIMENTO TT CONDIÇÕESDEPAGAMENTO VALOR TOTAL\n'
    '23/09/2026 A PRAZO R$ 136,67\n'
    '\n'
    'Não contribuinte de ISS s/locação cfe. LC n. 116/03\n'
    '\n'
    'Aceite:\n'
    '\n'
    '\n'
    'LOCALIZA_NUMERO: AGMTZ - 11929076\n'
    'LOCALIZA_TOMADOR: STAUMMAQ SERVICOS TECNICOS AUTOMACAO MOTORES E MAQUINAS LTDA\n'
    'LOCALIZA_DESCRICAO: RESSARCIMENTO o EA - MULTA DE TRÂNSITO, CONTRATO RLGA486217.\n'
    'LOCALIZA_DESCRICAO: CONFORME CONDICE ES GERAIS DO CONTRATO. PAGAMENTO DEVE SER\n'
    'LOCALIZA_DESCRICAO: EFETUADO PELA FATURA LOCALIZA, SENDO A GUIA DO ÓRGÃO APENAS PARA\n'
    'LOCALIZA_DESCRICAO: CONFERÊNCIA.\n'
    'LOCALIZA_DESCRICAO: O VALOR COBRADO PELA LOCALIZA SERÁ O VALOR DA INFRAÇÃO COM O\n'
    'LOCALIZA_DESCRICAO: DESCONTO DE 20% CONCEDIDO PELO ÓRGÃO DE TRÂNSITO, ACRESCIDO DE TAXA\n'
    'LOCALIZA_DESCRICAO: ADMINISTRATIVA DE 25% SOBRE O VALOR ORIGINAL DA MULTA.\n'
    'LOCALIZA_DESCRICAO: PLACA(S): TYC7E19\n'
    'LOCALIZA_ITEM_VALOR: 136,67\n'
    'LOCALIZA_VALOR_TOTAL: 136,67\n'
)

# Pag. 1 de Scan2026-10-16_110841.pdf (a pagina inteira nao le "Nº:").
OCR_AASSA_1517937 = (
    'LOCALIZA RENT A CAR S/A\n'
    '\n'
    'AGENCIA AEROPORTO SALVADOR\n'
    'SlLocaliza TV SANTOS DUMONT, 431 - CENTRO\n'
    '\n'
    '41311-546 - SALVADOR - BA\n'
    '\n'
    'CNPJ - 16.670.085/0316-20\n'
    '\n'
    'FATURA / DUPLICATA\n'
    '\n'
    'CLIENTE: STAUMMAQ SERVICOS TECNICOS AUTOMACAO MOTORES\n'
    '. E MAQUINAS LTDA\n'
    '\n'
    'ENDEREÇO: URBANA, 1 CIA SUL - CIA SUL\n'
    '\n'
    'CEP/CID/UF: 43721-450 - SIMOES FILHO - BA\n'
    '\n'
    'CNPJ: 02.370.080/0001-00\n'
    '\n'
    'DEPARTAMENTO: TRANSFORMADORES\n'
    '\n'
    'ALUGUEL CONFORME CONTRATO SSAB309436\n'
    '\n'
    'VALOR DO SEGURO\n'
    '\n'
    'ASSISTÊNCIA A CLIENTES\n'
    'TEL 0800 979 2020\n'
    '\n'
    'assistenciaaclientes(localiza.com\n'
    '\n'
    'CÓDIGO: 01945295\n'
    'INSC. ESTADUAL: 048137340\n'
    '\n'
    'DATA DE EMISSÃO:04/09/2026\n'
    '\n'
    'R$ 254,25\n'
    '\n'
    'R$ 17,95\n'
    '\n'
    'O NENCIMENTO— TT CONDIÇÕESDEPAGAMENTO VALOR TOTAL\n'
    '19/09/2026 A PRAZO R$272,20\n'
    '\n'
    'Não contribuinte de ISS s/locação cfe. LC n. 116/03\n'
    '\n'
    'Sacador:\n'
    '\n'
    '\n'
    'LOCALIZA_NUMERO: AASSA - 1517937\n'
    'LOCALIZA_TOMADOR: STAUMMAQ SERVICOS TECNICOS AUTOMACAO MOTORES E MAQUINAS LTDA\n'
    'LOCALIZA_DESCRICAO: ALUGUEL CONFORME CONTRATO SSAB309436\n'
    'LOCALIZA_DESCRICAO: VALOR DO SEGURO\n'
    'LOCALIZA_ITEM_VALOR: 254,25\n'
    'LOCALIZA_ITEM_VALOR: 17,95\n'
    'LOCALIZA_VALOR_TOTAL: 272,20\n'
)

# Pag. 2 de Scan2026-10-16_110841.pdf ("VALOR TOTAL" vazio na pagina inteira).
OCR_AGMTZ_11998441 = (
    'LOCALIZA RENT A CAR S/A ASSISTÊNCIA A CLIENTES\n'
    'AGENCIA MATRIZ TEL 0800 979 2020\n'
    '\n'
    '“localiza AV BERNARDO DE VASCONCELOS, 377 - CACHOEIRINHA assistenciaaclientesQlocaliza.com\n'
    '31150-000 - BELO HORIZONTE - MG\n'
    '\n'
    'CNPJ - 16.670.085/0001-55\n'
    '\n'
    'FATURA / DUPLICATA Nº: AGMTZ - 11998441\n'
    '\n'
    'CLIENTE: STAUMMAQ SERVICOS TECNICOS AUTOMACAO MOTORES\n'
    '\n'
    '. E MAQUINAS LTDA CÓDIGO: 01945295\n'
    'ENDEREÇO: URBANA, 1 CIA SUL - CIA SUL INSC. ESTADUAL: 048137340\n'
    'CEP/CID/UF: 43721-450 - SIMOES FILHO - BA\n'
    '\n'
    'CNPJ: 02.370.080/0001-00 DATA DE EMISSÃO:22/09/2026\n'
    'DEPARTAMENTO: ANSFORMADORES\n'
    '\n'
    'RESSARCIMENTO DE, DESPESA - MULTA DE TRÂNSITO, CONTRATO SSAB309436.\n'
    '\n'
    'CONFORME CONDIÇÕES GERAIS DO CONTRATO. PAGAMENTO DEVE SER\n'
    '\n'
    'EFETUADO PELA FA\n'
    'CONFERÊNCIA.\n'
    '\n'
    'O VALOR COBRADO PELA LOCALIZA SERÁ O VALOR DA INFRAÇÃO COM O R$ 92443\n'
    'DESCONTO DE 20% CONCEDIDO PELO ÓRGÃO DE TRÂNSITO, ACRESCIDO DE TAXA ;\n'
    'ADMINISTRATIVA DE 25% SOBRE O VALOR ORIGINAL DA MULTA.\n'
    '\n'
    'PLACA(S): TEROCO2\n'
    '\n'
    'Nº SINISTRO: TRANSFORMADORES\n'
    '\n'
    'URA LOCALIZA, SENDO A GUIA DO ÓRGÃO APENAS PARA\n'
    '\n'
    'VENCIMENTO CONDIÇÕES DE PAGAMENTO VALOR TOTAL\n'
    '07/10/2026 A PRAZO\n'
    '\n'
    'Não contribuinte de ISS s/locação cfe. LC n. 116/03\n'
    '\n'
    'Sacador:\n'
    '\n'
    '\n'
    'LOCALIZA_NUMERO: AGMTZ - 11998441\n'
    'LOCALIZA_TOMADOR: STAUMMAQ SERVICOS TECNICOS AUTOMACAO MOTORES E MAQUINAS LTDA\n'
    'LOCALIZA_DESCRICAO: RESSARCIMENTO DE, DESPESA - MULTA DE TRÂNSITO, CONTRATO SSAB309436.\n'
    'LOCALIZA_DESCRICAO: CONFORME CONDICOES GERAIS DO CONTRATO. PAGAMENTO DEVE SER\n'
    'LOCALIZA_DESCRICAO: EFETUADO PELA FATURA LOCALIZA, SENDO A GUIA DO ÓRGÃO APENAS PARA\n'
    'LOCALIZA_DESCRICAO: CONFERÊNCIA.\n'
    'LOCALIZA_DESCRICAO: O VALOR COBRADO PELA LOCALIZA SERÁ O VALOR DA RO COM O\n'
    'LOCALIZA_DESCRICAO: DESCONTO DE 20% CONCEDIDO PELO ÓRGÃO DE TRÂNSITO, ACRESCIDO DE TAXA\n'
    'LOCALIZA_DESCRICAO: ADMINISTRATIVA DE 25% SOBRE O VALOR ORIGINAL DA MULTA.\n'
    'LOCALIZA_DESCRICAO: PLACA(S): TEROCO2\n'
    'LOCALIZA_DESCRICAO: Nº SINISTRO: TRANSFORMADORES\n'
    'LOCALIZA_ITEM_VALOR: 924,43\n'
    'LOCALIZA_VALOR_TOTAL: 924,43\n'
)


def _parse(monkeypatch, texto):
    """Arquivo dummy sem numero no nome (ha um fallback que pesca o numero
    do nome do arquivo)."""
    dummy = "tests/dummy_localiza_fatura_scan.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy, "wb") as f:
        f.write(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: texto)
    try:
        ex = SPPdfExtractor(dummy)
        return ex, ex.parse()
    finally:
        if os.path.exists(dummy):
            os.remove(dummy)


def _sem_recortes(texto):
    """O mesmo texto SEM as linhas `LOCALIZA_*` (como saia antes da correcao)."""
    return "\n".join(l for l in texto.split("\n") if not l.startswith("LOCALIZA_"))


# --- AGMTZ-11929076 ---------------------------------------------------------

def test_11929076_layout_e_numero(monkeypatch):
    ex, nfse = _parse(monkeypatch, OCR_AGMTZ_11929076)
    assert ex.layout == LAYOUT_LOCALIZA
    assert nfse.numero == "11929076"


def test_11929076_tomador_pelo_recorte_do_cliente(monkeypatch):
    _, nfse = _parse(monkeypatch, OCR_AGMTZ_11929076)
    assert nfse.tomador.razao_social == "STAUMMAQ SERVICOS TECNICOS AUTOMACAO MOTORES E MAQUINAS LTDA"
    assert nfse.tomador.cnpj_cpf == "02370080000100"
    assert nfse.tomador.endereco.bairro == "CIA SUL"
    assert nfse.tomador.endereco.codigo_municipio == "2930709"


def test_11929076_discriminacao_e_a_descricao_impressa(monkeypatch):
    _, nfse = _parse(monkeypatch, OCR_AGMTZ_11929076)
    d = nfse.discriminacao
    assert d != "Serviços prestados conforme nota fiscal."
    assert "MULTA DE TRÂNSITO, CONTRATO RLGA486217." in d
    assert "EFETUADO PELA FATURA LOCALIZA, SENDO A GUIA DO ÓRGÃO APENAS PARA CONFERÊNCIA." in d
    assert "ACRESCIDO DE TAXA ADMINISTRATIVA DE 25% SOBRE O VALOR ORIGINAL DA MULTA." in d
    assert d.endswith("PLACA(S): TYC7E19")
    assert "\n" not in d and "LOCALIZA_" not in d


def test_11929076_valores_e_convencoes_do_layout(monkeypatch):
    _, nfse = _parse(monkeypatch, OCR_AGMTZ_11929076)
    assert nfse.valores.valor_servicos == pytest.approx(136.67)
    assert nfse.valores.valor_liquido_nfse == pytest.approx(136.67)
    assert nfse.valores.base_calculo == 0.0 and nfse.valores.valor_iss == 0.0
    assert nfse.servico_codigo == "0601"
    assert nfse.data_emissao.strftime("%d/%m/%Y") == "08/09/2026"
    assert nfse.prestador.cnpj_cpf == "16670085000155"
    assert nfse.prestador.endereco.codigo_municipio == "3106200"
    assert nfse.avisos == []


# --- AASSA-1517937 ----------------------------------------------------------

def test_1517937_numero_vem_do_recorte_quando_a_pagina_perde_a_caixa(monkeypatch):
    texto_antigo = _sem_recortes(OCR_AASSA_1517937)
    assert "Nº:" not in texto_antigo  # a pagina inteira perdeu a caixa mesmo
    _, nfse = _parse(monkeypatch, OCR_AASSA_1517937)
    assert nfse.numero == "1517937"


def test_1517937_campos(monkeypatch):
    _, nfse = _parse(monkeypatch, OCR_AASSA_1517937)
    assert nfse.data_emissao.strftime("%d/%m/%Y") == "04/09/2026"
    assert nfse.valores.valor_servicos == pytest.approx(272.20)
    assert nfse.prestador.cnpj_cpf == "16670085031620"
    assert nfse.tomador.razao_social == "STAUMMAQ SERVICOS TECNICOS AUTOMACAO MOTORES E MAQUINAS LTDA"
    assert nfse.discriminacao == "ALUGUEL CONFORME CONTRATO SSAB309436 | VALOR DO SEGURO"
    assert nfse.avisos == []


# --- AGMTZ-11998441 ---------------------------------------------------------

def test_11998441_valor_total_vem_do_recorte(monkeypatch):
    _, antes = _parse(monkeypatch, _sem_recortes(OCR_AGMTZ_11998441))
    assert antes.valores.valor_servicos == 0.0  # o defeito relatado
    assert any("VALOR TOTAL" in a for a in antes.avisos)  # agora ao menos avisa
    _, nfse = _parse(monkeypatch, OCR_AGMTZ_11998441)
    assert nfse.valores.valor_servicos == pytest.approx(924.43)
    assert nfse.valores.valor_liquido_nfse == pytest.approx(924.43)
    assert nfse.avisos == []


def test_11998441_bairro_sem_o_rotulo_da_coluna_direita(monkeypatch):
    for texto in (OCR_AGMTZ_11998441, _sem_recortes(OCR_AGMTZ_11998441)):
        _, nfse = _parse(monkeypatch, texto)
        assert nfse.tomador.endereco.bairro == "CIA SUL"
        assert nfse.tomador.endereco.logradouro == "URBANA"
        assert nfse.tomador.endereco.numero == "1"


def test_11998441_razao_sem_ponto_solto_mesmo_sem_recorte(monkeypatch):
    _, nfse = _parse(monkeypatch, _sem_recortes(OCR_AGMTZ_11998441))
    assert nfse.tomador.razao_social == "STAUMMAQ SERVICOS TECNICOS AUTOMACAO MOTORES E MAQUINAS LTDA"


def test_11998441_numero_data_e_discriminacao(monkeypatch):
    _, nfse = _parse(monkeypatch, OCR_AGMTZ_11998441)
    assert nfse.numero == "11998441"
    assert nfse.data_emissao.strftime("%d/%m/%Y") == "22/09/2026"
    d = nfse.discriminacao
    assert d.startswith("RESSARCIMENTO DE, DESPESA - MULTA DE TRÂNSITO, CONTRATO SSAB309436.")
    # Placa impressa "TER0C02": o OCR le "TEROCO2"; posicoes de digito do
    # formato Mercosul sao fixas -> correcao deterministica.
    assert "PLACA(S): TER0C02" in d
    assert d.endswith("Nº SINISTRO: TRANSFORMADORES")


# --- conferencias cruzadas (integridade) ------------------------------------

def test_total_divergente_da_pagina_inteira_gera_aviso(monkeypatch):
    texto = OCR_AASSA_1517937.replace("LOCALIZA_VALOR_TOTAL: 272,20", "LOCALIZA_VALOR_TOTAL: 272,90")
    _, nfse = _parse(monkeypatch, texto)
    assert nfse.valores.valor_servicos == pytest.approx(272.90)
    assert any("diverge do recorte" in a for a in nfse.avisos)
    assert any("Soma dos valores da coluna VALOR" in a for a in nfse.avisos)


def test_numero_divergente_gera_aviso(monkeypatch):
    texto = OCR_AGMTZ_11929076.replace("LOCALIZA_NUMERO: AGMTZ - 11929076", "LOCALIZA_NUMERO: AGMTZ - 11929078")
    _, nfse = _parse(monkeypatch, texto)
    assert nfse.numero == "11929078"
    assert any("diverge do recorte dedicado da caixa" in a for a in nfse.avisos)


def test_recorte_de_nome_de_outra_entidade_nao_substitui_o_tomador(monkeypatch):
    texto = OCR_AASSA_1517937.replace(
        "LOCALIZA_TOMADOR: STAUMMAQ SERVICOS TECNICOS AUTOMACAO MOTORES E MAQUINAS LTDA",
        "LOCALIZA_TOMADOR: TEMIS PROJETOS DE MEIO AMBIENTE LTDA")
    _, nfse = _parse(monkeypatch, texto)
    assert nfse.tomador.razao_social == "STAUMMAQ SERVICOS TECNICOS AUTOMACAO MOTORES E MAQUINAS LTDA"


# --- funcoes puras do modulo ------------------------------------------------

def test_valores_monetarios_rejeita_leitura_sem_virgula():
    assert loc.valores_monetarios("R$ 92443") == []
    assert loc.valores_monetarios("VALOR TOTAL\nR$ 924,43\n") == ["924,43"]
    assert loc.valores_monetarios("R$ 1.234,56 R$17,95") == ["1.234,56", "17,95"]


def test_numero_da_fatura():
    assert loc.numero_da_fatura("Nº: AASSA - 1517937") == "AASSA - 1517937"
    assert loc.numero_da_fatura("") is None


@pytest.mark.parametrize("lido,esperado", [
    ("TEROCO2", "TER0C02"), ("TYC7E19", "TYC7E19"), ("ABC1234", "ABC1234"), ("XYZ", "XYZ"),
])
def test_normalizar_placa(lido, esperado):
    assert loc.normalizar_placa(lido) == esperado


@pytest.mark.parametrize("leitura", [
    "CLIENTE: STAUMMAQ SERVICOS TECNICOS AUTOMACAO MOTORES\nE MAQUINAS LTDA\nENDEREÇO: URBANA, 1 CIA SUL - CIA SUL\n",
    "subtE: STAUMMAQ SERVICOS TECNICOS AUTOMACAO MOTORES\nE MAQUINAS LTDA\nENDEREÇO: URBANA, 1 CIA SUL - CIA SUL\n",
    "cuENTÊ STAUMMAQ SERVICOS TECNICOS AUTOMACAO MOTORES\nE MAQUINAS LTDA\nENDEREÇO: URBANA, 1 CIA SUL - CIA SUL\n",
    "CLIENTE: STAUMMAQ SERVICOS TECNICOS AUTOMACAO MOTORES E\n“MAQUINAS LTDA\nENDEREÇO:URBANA., 1 CIA SUL - CIA SLI\n",
])
def test_razao_do_cliente_leituras_reais_do_recorte(leitura):
    assert loc.razao_do_cliente(leitura) == "STAUMMAQ SERVICOS TECNICOS AUTOMACAO MOTORES E MAQUINAS LTDA"


def test_razao_do_cliente_sem_linha_do_endereco_e_descartada():
    assert loc.razao_do_cliente("CLIENTE: STAUMMAQ SERVICOS TECNICOS\nE MAQUINAS ITDA\n") is None


def test_eh_template():
    assert loc.eh_template(OCR_AGMTZ_11929076)
    assert not loc.eh_template("LOCALIZA RENT A CAR S/A\nBeneficiário\nPix")  # boleto
    assert not loc.eh_template("MC LOCADORA PETROLINA LTDA LOCALIZA RENT A CAR FATURA / DUPLICATA")


def test_discriminacao_variante_digital_sem_recorte(monkeypatch):
    """Variante digital (pdfminer, sem OCR e sem recortes): mesma regra, a
    partir do cabecalho "DESCRIÇÃO VALOR"."""
    from tests.test_localiza_layout import MOCK_DIGITAL_YUI
    dummy = "tests/dummy_localiza_fatura_digital.pdf"
    with open(dummy, "wb") as f:
        f.write(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_DIGITAL_YUI)
    try:
        nfse = SPPdfExtractor(dummy).parse_multiple()[0]
    finally:
        os.remove(dummy)
    assert nfse.discriminacao == "ALUGUEL CONFORME CONTRATO BULF036105008 | VALOR DO SEGURO"


# Grade do texto REAL (pdfminer) de "LOCALIZA KELLY2  21.09.pdf" (AACMC-232040):
# blocos separados por linha em branco, nº do contrato num bloco proprio e
# os 2 valores so depois de todas as descricoes.
GRADE_DIGITAL_BLOCOS = (
    "DESCRI\u00c7\u00c3O \n\nVALOR \n\nALUGUEL CONFORME CONTRATO \n\n    BULF043459\n\n"
    "VALOR DO SEGURO \n\nR$ 1.122,10 \n\nR$ 59,50 \n\nVENCIMENTO"
)

# Grade do texto REAL de "LOCALIZA MULTA CAROL 21.09.pdf": paragrafos de
# texto corrido, 1 valor so -> um paragrafo unico.
GRADE_DIGITAL_MULTA = (
    "DESCRI\u00c7\u00c3O \n\nVALOR \n\nRESSARCIMENTO DE DESPESA - MULTA DE TR\u00c2NSITO, CONTRATO PITF145489.\n"
    "CONFORME CONDI\u00c7\u00d5ES GERAIS DO CONTRATO. PAGAMENTO DEVE SER\n"
    "EFETUADO PELA FATURA LOCALIZA, SENDO A GUIA DO \u00d3RG\u00c3O APENAS PARA\n"
    "CONFER\u00caNCIA.\n\nO VALOR COBRADO PELA LOCALIZA SER\u00c1 O VALOR DA INFRA\u00c7\u00c3O COM O\n"
    "DESCONTO DE 20% CONCEDIDO PELO \u00d3RG\u00c3O DE TR\u00c2NSITO, ACRESCIDO DE TAXA\n"
    "ADMINISTRATIVA DE 25% SOBRE O VALOR ORIGINAL DA MULTA.\n\nPLACA(S): TYS2E96  \n\n"
    "R$ 136,67 \n\nVENCIMENTO"
)


@pytest.mark.parametrize("grade,esperado", [
    (GRADE_DIGITAL_BLOCOS, "ALUGUEL CONFORME CONTRATO BULF043459 | VALOR DO SEGURO"),
    (GRADE_DIGITAL_MULTA,
     "RESSARCIMENTO DE DESPESA - MULTA DE TR\u00c2NSITO, CONTRATO PITF145489. CONFORME CONDI\u00c7\u00d5ES "
     "GERAIS DO CONTRATO. PAGAMENTO DEVE SER EFETUADO PELA FATURA LOCALIZA, SENDO A GUIA DO "
     "\u00d3RG\u00c3O APENAS PARA CONFER\u00caNCIA. O VALOR COBRADO PELA LOCALIZA SER\u00c1 O VALOR DA "
     "INFRA\u00c7\u00c3O COM O DESCONTO DE 20% CONCEDIDO PELO \u00d3RG\u00c3O DE TR\u00c2NSITO, ACRESCIDO "
     "DE TAXA ADMINISTRATIVA DE 25% SOBRE O VALOR ORIGINAL DA MULTA. PLACA(S): TYS2E96"),
])
def test_discriminacao_variante_digital_em_blocos(grade, esperado):
    ex = SPPdfExtractor.__new__(SPPdfExtractor)
    ex.layout = LAYOUT_LOCALIZA
    ex.raw_text = grade
    assert ex._extrair_discriminacao_localiza() == esperado
