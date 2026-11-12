# -*- coding: utf-8 -*-
r"""São Paulo/SP (LAYOUT_SAO_PAULO digital / LAYOUT_SAO_PAULO_2 escaneado) -
"VALOR TOTAL RECEBIDO" impresso MAIOR que o "VALOR TOTAL DO SERVIÇO".

Decisão do USUÁRIO (2026-11-12), notas da PLUXEE BENEFICIOS BRASIL S.A. (CNPJ
69.034.668/0001-56) no lote "Notas_Fiscais_emitidas_e_recebidas_10.2026_-_PH_
Gestao_SEDE.pdf" (pág. 9 = nota 08980330, pág. 11 = nota 08980332, escaneadas):

    VALOR TOTAL DO SERVIÇO = R$ 6,00
    VALOR TOTAL RECEBIDO = R$ 16,00     (R$ 10,00 = crédito de VR/VA repassado)
    Deduções 0,00 | Base 6,00 | Alíquota 2,00% | ISS 0,12

XML: ValorServicos = 16,00 (recebido); ValorDeducoes = 10,00 (recebido -
serviço, o repasse); Base/Alíquota/ISS como impressos (6,00 / 2% / 0,12);
ValorLiquidoNfse = recebido - retenções (16,00). Acionada pelo campo impresso,
não pelo CNPJ. Sem leitura segura ou com a conta incoerente: comportamento
anterior + aviso.

Textos = OCR REAL das páginas do lote (os mesmos do teste de regressão do lote,
`test_sao_paulo2_pluxee_lote_pagina_11.py`) e o retorno REAL do pdfminer das
notas digitais da Flash (`test_sao_paulo_flash_valor_recebido.py`). Os casos
negativos trocam UMA linha do texto real (marcada em cada teste)."""
import xml.etree.ElementTree as ET

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor
from src.transformers.abrasf_transformer import Abrasf201Transformer
from tests.test_sao_paulo2_pluxee_lote_pagina_11 import PAG9_NOTA_08980330, PAG11_NOTA_08980332
from tests.test_sao_paulo_flash_valor_recebido import NOTA_FLASH_05710445

RECEBIDO_16 = "VALOR TOTAL RECEBIDO = R$ 16,00"
SERVICO_6 = "VALOR TOTAL DO SERVIÇO = R$ 6,00"
GRADE_PAG11 = "0,00 6,00 2,00% 0,12 0,00"
AVISO_REGRA = ("Valor total recebido R$ 16,00 usado como ValorServicos; diferença de "
               "R$ 10,00 para o valor do serviço (R$ 6,00) lançada em ValorDeducoes (repasse)")


def _parse_ocr(monkeypatch, tmp_path, texto_ocr):
    pdf = tmp_path / "pluxee.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: texto_ocr)
    notas = SPPdfExtractor(str(pdf)).parse_multiple()
    assert len(notas) == 1
    return notas[0]


def _parse_digital(monkeypatch, tmp_path, texto):
    pdf = tmp_path / "digital.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: texto)
    notas = SPPdfExtractor(str(pdf)).parse_multiple()
    assert len(notas) == 1
    return notas[0]


def _secoes_xml(nfse):
    """Campos de valores das duas seções do XML (ValoresNfse e Servico/Valores)."""
    root = ET.fromstring(Abrasf201Transformer().transform(nfse))
    ns = {"n": root.tag.split("}")[0][1:]} if root.tag.startswith("{") else {}
    p = "n:" if ns else ""
    campos = ("ValorServicos", "ValorDeducoes", "BaseCalculo", "Aliquota", "ValorIss", "ValorLiquidoNfse")

    def _ler(sec):
        return {c: (sec.find(p + c, ns).text if sec.find(p + c, ns) is not None else None) for c in campos}

    return (_ler(root.find(f".//{p}ValoresNfse", ns)),
            _ler(root.find(f".//{p}Servico/{p}Valores", ns)))


def _sem_aviso_da_regra(nfse):
    return not any("usado como ValorServicos" in a for a in nfse.avisos)


# --- recebido > serviço: regra aplicada ------------------------------------

def test_pag11_recebido_maior_que_servico_vai_para_valor_servicos(monkeypatch, tmp_path):
    nfse = _parse_ocr(monkeypatch, tmp_path, PAG11_NOTA_08980332)
    assert nfse.numero == "08980332"
    assert nfse.prestador.cnpj_cpf == "69034668000156"
    v = nfse.valores
    assert v.valor_servicos == 16.00
    assert v.valor_deducoes == 10.00
    assert v.base_calculo == 6.00          # como impressa, não recalculada
    assert v.aliquota == pytest.approx(0.02)
    assert v.valor_iss == 0.12             # como impresso, não 2% de 16,00
    assert v.valor_liquido_nfse == 16.00
    assert AVISO_REGRA in nfse.avisos


def test_pag11_xml_sai_igual_nas_duas_secoes(monkeypatch, tmp_path):
    nfse = _parse_ocr(monkeypatch, tmp_path, PAG11_NOTA_08980332)
    valores_nfse, servico_valores = _secoes_xml(nfse)
    assert valores_nfse == {
        "ValorServicos": "16.00", "ValorDeducoes": "10.00", "BaseCalculo": "6.00",
        "Aliquota": valores_nfse["Aliquota"], "ValorIss": "0.12", "ValorLiquidoNfse": "16.00"}
    assert float(valores_nfse["Aliquota"]) in (2.0, 0.02)
    assert {k: v for k, v in servico_valores.items() if k != "ValorLiquidoNfse"} == {
        k: v for k, v in valores_nfse.items() if k != "ValorLiquidoNfse"}


def test_pag9_regra_aplicada_com_a_grade_ilegivel(monkeypatch, tmp_path):
    """Pág. 9: o OCR lê a grade "0,00 6,00 2,00% | 0,12 0,00" e o "|" no meio
    impede a leitura (fora do escopo desta regra): Alíquota/ISS saem 0 e a
    Base cai no fallback = serviço (6,00). Os dois totais impressos são lidos
    limpos, então a regra se aplica sobre eles."""
    nfse = _parse_ocr(monkeypatch, tmp_path, PAG9_NOTA_08980330)
    v = nfse.valores
    assert (v.valor_servicos, v.valor_deducoes, v.base_calculo, v.valor_liquido_nfse) == (16.00, 10.00, 6.00, 16.00)
    assert (v.aliquota, v.valor_iss) == (0.0, 0.0)
    assert AVISO_REGRA in nfse.avisos


def test_regra_e_disparada_pelo_campo_e_nao_pelo_cnpj(monkeypatch, tmp_path):
    texto = (PAG11_NOTA_08980332.replace("69.034.668/0001-56", "11.222.333/0001-81")
             .replace("PLUXEE BENEFICIOS BRASIL S.A.", "OUTRA EMPRESA DE BENEFICIOS LTDA"))
    nfse = _parse_ocr(monkeypatch, tmp_path, texto)
    assert nfse.prestador.cnpj_cpf == "11222333000181"
    assert (nfse.valores.valor_servicos, nfse.valores.valor_deducoes) == (16.00, 10.00)


# --- recebido ausente: inalterado, sem aviso --------------------------------

def test_recebido_ausente_mantem_comportamento(monkeypatch, tmp_path):
    texto = PAG11_NOTA_08980332.replace(RECEBIDO_16 + "\n", "")
    assert "RECEBIDO" not in texto
    nfse = _parse_ocr(monkeypatch, tmp_path, texto)
    v = nfse.valores
    assert (v.valor_servicos, v.valor_deducoes, v.base_calculo, v.valor_iss, v.valor_liquido_nfse) == (
        6.00, 0.0, 6.00, 0.12, 6.00)
    assert _sem_aviso_da_regra(nfse)
    assert not any("VALOR TOTAL RECEBIDO" in a for a in nfse.avisos)


def test_recebido_ilegivel_mantem_e_avisa(monkeypatch, tmp_path):
    texto = PAG11_NOTA_08980332.replace(RECEBIDO_16, "VALOR TOTAL RECEBIDO = R$ 1G,O0")
    nfse = _parse_ocr(monkeypatch, tmp_path, texto)
    assert (nfse.valores.valor_servicos, nfse.valores.valor_deducoes) == (6.00, 0.0)
    assert _sem_aviso_da_regra(nfse)
    assert any("VALOR TOTAL RECEBIDO impresso" in a and "não foi lido com segurança" in a
               for a in nfse.avisos)


def test_recebido_com_leituras_divergentes_mantem_e_avisa(monkeypatch, tmp_path):
    texto = PAG11_NOTA_08980332.replace(RECEBIDO_16, RECEBIDO_16 + "\nVALOR TOTAL RECEBIDO = R$ 18,00")
    nfse = _parse_ocr(monkeypatch, tmp_path, texto)
    assert (nfse.valores.valor_servicos, nfse.valores.valor_deducoes) == (6.00, 0.0)
    assert any("leituras divergentes" in a for a in nfse.avisos)


# --- recebido <= serviço -----------------------------------------------------

def test_recebido_igual_ao_servico_nao_muda_nada_nem_avisa(monkeypatch, tmp_path):
    texto = PAG11_NOTA_08980332.replace(RECEBIDO_16, "VALOR TOTAL RECEBIDO = R$ 6,00")
    nfse = _parse_ocr(monkeypatch, tmp_path, texto)
    v = nfse.valores
    assert (v.valor_servicos, v.valor_deducoes, v.valor_liquido_nfse) == (6.00, 0.0, 6.00)
    assert not any("RECEBIDO" in a.upper() for a in nfse.avisos)


def test_recebido_menor_que_servico_mantem_e_avisa(monkeypatch, tmp_path):
    texto = PAG11_NOTA_08980332.replace(RECEBIDO_16, "VALOR TOTAL RECEBIDO = R$ 5,00")
    nfse = _parse_ocr(monkeypatch, tmp_path, texto)
    assert (nfse.valores.valor_servicos, nfse.valores.valor_deducoes) == (6.00, 0.0)
    assert _sem_aviso_da_regra(nfse)
    assert any("menor que o do serviço" in a for a in nfse.avisos)


# --- incoerência -------------------------------------------------------------

def test_deducoes_impressas_diferentes_de_zero_mantem_e_avisa(monkeypatch, tmp_path):
    # grade com dedução de 1,00 (base 5,00 = 6,00 - 1,00; ISS 0,10)
    texto = PAG11_NOTA_08980332.replace(GRADE_PAG11, "1,00 5,00 2,00% 0,10 0,00")
    nfse = _parse_ocr(monkeypatch, tmp_path, texto)
    v = nfse.valores
    assert (v.valor_servicos, v.valor_deducoes, v.base_calculo) == (6.00, 1.00, 5.00)
    assert _sem_aviso_da_regra(nfse)
    assert any("já imprime deduções" in a for a in nfse.avisos)


def test_base_impressa_incoerente_com_o_servico_mantem_e_avisa(monkeypatch, tmp_path):
    texto = PAG11_NOTA_08980332.replace(GRADE_PAG11, "0,00 8,00 2,00% 0,16 0,00")
    nfse = _parse_ocr(monkeypatch, tmp_path, texto)
    v = nfse.valores
    assert (v.valor_servicos, v.valor_deducoes, v.base_calculo) == (6.00, 0.0, 8.00)
    assert _sem_aviso_da_regra(nfse)
    assert any("não confere com a base de cálculo impressa" in a for a in nfse.avisos)


def test_digital_base_impressa_zero_e_incoerente(monkeypatch, tmp_path):
    """Digital (pdfminer real da Flash 05710445) com o serviço trocado para
    500,00: a grade imprime Base 0,00, que `_extrair_valores` troca pelo
    serviço - a conferência usa a Base COMO IMPRESSA e não aplica a regra."""
    texto = NOTA_FLASH_05710445.replace("VALOR TOTAL DO SERVIÇO = R$ 0,00", "VALOR TOTAL DO SERVIÇO = R$ 500,00")
    nfse = _parse_digital(monkeypatch, tmp_path, texto)
    assert (nfse.valores.valor_servicos, nfse.valores.valor_deducoes) == (500.00, 0.0)
    assert any("não confere com a base de cálculo impressa (R$ 0,00)" in a for a in nfse.avisos)


def test_flash_com_servico_zero_continua_na_regra_propria(monkeypatch, tmp_path):
    """Serviço impresso 0,00 (Flash): a regra própria do prestador roda antes
    e esta não lança dedução nenhuma."""
    nfse = _parse_digital(monkeypatch, tmp_path, NOTA_FLASH_05710445)
    v = nfse.valores
    assert (v.valor_servicos, v.valor_deducoes, v.base_calculo, v.valor_liquido_nfse) == (1113.00, 0.0, 0.0, 1113.00)
    assert _sem_aviso_da_regra(nfse)
