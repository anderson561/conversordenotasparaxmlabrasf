# -*- coding: utf-8 -*-
"""São Paulo/SP, PLUXEE BENEFICIOS BRASIL S.A. (CNPJ 69.034.668/0001-56):
a nota NÃO tem deduções - ValorDeducoes sai sempre como IMPRESSO (0,00).

Decisão do usuário (2026-11-13): "Não há deduções na nota fiscal. [...] caso o
valor do serviço seja menor que o valor recebido, também considera o valor
recebido." Sempre que o valor recebido (ou, sem ele, o crédito EMV da
discriminação) vira ValorServicos, ValorDeducoes fica com as deduções
impressas na grade (0,00), nunca com a diferença recebido - serviço nem com o
próprio crédito. Base de Cálculo/Alíquota/ISS seguem como impressos e o
líquido = ValorServicos - retenções.

Trava os três cenários com texto REAL:
- serviço 0,00 + recebido (nota 08969996, pdfminer real, digital);
- serviço 0,00 sem recebido, crédito EMV (nota 08937118, OCR real pág. 23);
- serviço < recebido (notas 08980330/08980332, OCR real págs. 9 e 11 do lote
  PH Gestão; nota 09125393, OCR real págs. 33/34 do lote Guarajuba).
"""
import xml.etree.ElementTree as ET

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor
from src.transformers.abrasf_transformer import Abrasf201Transformer
from tests.test_sao_paulo2_pluxee_lote_pagina_11 import PAG9_NOTA_08980330, PAG11_NOTA_08980332
from tests.test_sao_paulo_pagina_continuacao_valores import (
    ANEXO_33, PAG33_NOTA_09125393_TOPO, PAG34_NOTA_09125393_VALORES)
from tests.test_sao_paulo_pluxee_credito_emv import PAG23_NOTA_08937118, PAG24_ANEXO_DA_08937118
from tests.test_sao_paulo_pluxee_recebido_servico_zero import NOTA_PLUXEE_08969996

CAMPOS = ("ValorServicos", "ValorDeducoes", "BaseCalculo", "Aliquota", "ValorIss")


def _ocr(monkeypatch, tmp_path, paginas):
    pdf = tmp_path / "lote.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: "\x0c".join(paginas))
    notas = SPPdfExtractor(str(pdf)).parse_multiple()
    assert len(notas) == 1
    return notas[0]


def _digital(monkeypatch, tmp_path, texto):
    pdf = tmp_path / "digital.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: texto)
    notas = SPPdfExtractor(str(pdf)).parse_multiple()
    assert len(notas) == 1
    return notas[0]


def _xml(nota):
    root = ET.fromstring(Abrasf201Transformer().transform(nota))
    ns = {"n": root.tag.split("}")[0][1:]} if root.tag.startswith("{") else {}
    p = "n:" if ns else ""
    secoes = [root.find(f".//{p}ValoresNfse", ns), root.find(f".//{p}Servico/{p}Valores", ns)]
    lidos = [{c: s.find(p + c, ns).text for c in CAMPOS} for s in secoes]
    assert lidos[0] == lidos[1]
    return dict(lidos[0], ValorLiquidoNfse=secoes[0].find(p + "ValorLiquidoNfse", ns).text)


CENARIOS = {
    "servico_zero_com_recebido_08969996": (
        lambda mp, tp: _digital(mp, tp, NOTA_PLUXEE_08969996),
        ("9867.48", "0.00", "0.00", "0.02", "0.00", "9867.48")),
    "servico_zero_credito_emv_08937118": (
        lambda mp, tp: _ocr(mp, tp, [PAG23_NOTA_08937118, PAG24_ANEXO_DA_08937118]),
        ("1620.00", "0.00", "0.00", "0.02", "0.00", "1620.00")),
    "servico_menor_que_recebido_08980330": (
        lambda mp, tp: _ocr(mp, tp, [PAG9_NOTA_08980330]),
        ("16.00", "0.00", "6.00", "0.02", "0.12", "16.00")),
    "servico_menor_que_recebido_08980332": (
        lambda mp, tp: _ocr(mp, tp, [PAG11_NOTA_08980332]),
        ("16.00", "0.00", "6.00", "0.02", "0.12", "16.00")),
    "servico_menor_que_recebido_09125393": (
        lambda mp, tp: _ocr(mp, tp, [PAG33_NOTA_09125393_TOPO, PAG34_NOTA_09125393_VALORES] + ANEXO_33),
        ("16.00", "0.00", "6.00", "0.02", "0.12", "16.00")),
}


@pytest.mark.parametrize("cenario", sorted(CENARIOS))
def test_pluxee_valor_recebido_sem_deducoes(monkeypatch, tmp_path, cenario):
    parse, esperado = CENARIOS[cenario]
    nota = parse(monkeypatch, tmp_path)
    assert nota.prestador.cnpj_cpf == "69034668000156"
    xml = _xml(nota)
    assert (xml["ValorServicos"], xml["ValorDeducoes"], xml["BaseCalculo"], xml["ValorIss"],
            xml["ValorLiquidoNfse"]) == (esperado[0], esperado[1], esperado[2], esperado[4], esperado[5])
    assert float(xml["Aliquota"]) in (2.0, 0.02)
    # O aviso diz o novo mapeamento e não fala mais em "repasse" nas deduções.
    avisos = [a for a in nota.avisos if "usado como ValorServicos" in a]
    assert len(avisos) == 1, nota.avisos
    assert "sem deduções" in avisos[0]
    assert "ValorDeducoes como impresso na nota" in avisos[0] and "R$ 0,00" in avisos[0]
    assert "repasse" not in avisos[0]
