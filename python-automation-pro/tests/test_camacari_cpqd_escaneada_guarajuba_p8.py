import os

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor

# Texto REAL do OCR (Tesseract) da pág. 8 de "GUARAJUBA MALLS - NFSe.pdf":
# NFS-e CPqD de Camaçari/BA ESCANEADA, AVANÇO GESTÃO E ADMINISTRAÇÃO LTDA ->
# GUARAJUBA MALLS S/A, emitida 31/07/2026 11:56, R$ 2.795,21. O topo da
# página foi CORTADO no scan: a linha "Número da Nota" ficou fora da imagem
# (só a metade de baixo dos dígitos impressos sobrou, ilegível) e há o número
# "307" anotado a caneta azul acima da caixa do cabeçalho. Rabiscos de caneta
# sobre a coluna "Retenções" desmontaram as células "Alíquota (%)" ("am") e
# "Valor do ISS (R$)" ("o") na leitura de página inteira. Preservado verbatim
# (o pipeline entrega com quebras CRLF; `_parse` as restaura).
#
# OCR_BASE: o que a main produz para a página (página inteira + recortes do
# cabeçalho). RECORTES_NOVOS: as linhas que os recortes desta correção
# prependam (`_ocr_topo_cortado_camacari` + `_ocr_grade_totais_camacari`),
# lidas da imagem real da página.
OCR_BASE = """Data de Emissão” il
31/07/2026 11:56
Código de autenticidade
8XY380683
0066628001
Nº; SN
: GORDO)
UF: BA

Data de Emissão” si
31/07/2026 11:56
Código de autenticidade
8XY380683
001
Nº; SN
UF: BA

Data de Emissão
31/07/2026 11:56
Código de autenticidade
8XY380683
)066628001
Nº: SN
GORDO)
UF: BA

- - Umas ni SENA ETURD E TENDEL Sh hal ham NO PREVIA NE our Oo
EE e Data de Emissão
| o Secretaria da Fazenda 31/07/2026 11:56
Eus NOTA FISCAL DE SERVIÇOS ELETRÔNICA pa
PRESTADOR DE SERVIÇOS
Nome/Razão Social: AVANÇO GESTÃO E ADMINISTRAÇÃO LTDA
CPF/CNPJ: 59.132.742/0001-13 Inscrição Municipal: | 0066628001
Logradouro: RUA ALA DAS DUNAS Nº: SN
Compl.: —:GUARAJUBA SHOPPING;LOJA:03:QUADRA:C-4 Bairro: GUARAJUBA (MONTE GORDO)
CEP: 42840312 Município: CAMAÇARI UF: BA
TOMADOR DE SERVIÇOS
Nome/Razão Social: GUARAJUBA MALLS S/A
CPF/CNPJ: 24.890.395/0001-03 Inscrição Municipal: 0032035001
Logradouro: RODOVIA BA 099 ESTRADA DO Coco Nº: SN
Compl.: ALAMEDA DAS DUNAS GUARAJUBA SHOPPING Bairro: GUARAJUBA (MONTE GORDO)
CEP: 42840310 Município: CAMAÇARI UF: BA
DISCRIMINAÇÃO DOS SERVIÇOS
DESCRIÇÃO QTD VALOR UNIT (R$) VALOR TOTAL (R$)
TAXA DE SERVIÇOS COMBINADOS DE ESCRITÓRIO E APOIO ADMINISTRATIVO 1,0000 2.795,21 2.795,21
[e] psi [8] ua
[RE Eq des
a TSE ad
por (ajtgfehis
ae Retenções (R$) Totais (R$) f
ad us to 0,00 | Valor dos Serviços (R$) 2.795,21
e A () 0,00 |Deduções (-) 0.00
Ea ! 0,00 | Base de Cálculo (=) 2.795,21
um estro 0,00 |Aliquota (%) am
LL: ? 0,00 | Valor do ISS (R$) o
Outras: RO 0,00 |Valor Líquido da Nota (=) dois
Total de Retenções: q NU 0.00 2.795,21
Tipo de tributação; A RECOLHER PELO PRESTADOR = i
a Data da prest d :
Município da Prestação do serviço: 2905701 - CAMACARI ic
Município da tributação: 2905701 - CAMACARI
CNAE: 8211-3/00 - SERVIÇOS COMBINADOS DE ESCRITÓRIO E APOIO ADMINISTRATIVO
Serviço: 001 - É
erviço: 001703 - PLANEJAMENTO, COORDENAÇÃO, PROGRAMAÇÃO OU ORGANIZAÇÃO TÉCNICA, FINANCEIRA OU ADMINISTRATIVA.
CPqD - Gestão Pública Data Impressão: 31/07/2026 11:56 Ra
"""

RECORTES_NOVOS = """Código de autenticidade
8XY38Q683
[[CAMACARI_MANUSCRITO=307]]
Aliquota (%) 5,00
Valor do ISS (R$) 139,76
"""


def _parse(monkeypatch, texto):
    dummy_path = "tests/dummy_camacari_cpqd_guarajuba_p8.pdf"
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr",
                        lambda self: texto.replace("\n", "\r\n"))
    try:
        notas = SPPdfExtractor(dummy_path).parse_multiple()
    finally:
        os.remove(dummy_path)
    assert len(notas) == 1
    return notas[0]


def test_numero_da_anotacao_manuscrita_com_aviso(monkeypatch):
    nfse = _parse(monkeypatch, RECORTES_NOVOS + OCR_BASE)
    assert nfse.numero == "307"
    assert ("Número da nota lido de anotação manuscrita (impresso cortado no "
            "scan): 307 — confira") in nfse.avisos
    assert "Número da nota não encontrado" not in nfse.avisos


def test_sem_leitura_do_manuscrito_mantem_sentinela(monkeypatch):
    # Manuscrito ilegível/descartado pelo recorte (sem marcador): sentinela + aviso.
    texto = RECORTES_NOVOS.replace("[[CAMACARI_MANUSCRITO=307]]\n", "") + OCR_BASE
    nfse = _parse(monkeypatch, texto)
    assert nfse.numero == "00000000"
    assert "Número da nota não encontrado" in nfse.avisos
    assert not any("manuscrita" in a for a in nfse.avisos)


def test_impresso_legivel_vence_o_manuscrito(monkeypatch):
    texto = RECORTES_NOVOS + "Número da Nota\n306\n" + OCR_BASE
    nfse = _parse(monkeypatch, texto)
    assert nfse.numero == "306"
    assert not any("manuscrita" in a for a in nfse.avisos)


def test_codigo_autenticidade_com_q(monkeypatch):
    nfse = _parse(monkeypatch, RECORTES_NOVOS + OCR_BASE)
    assert nfse.codigo_verificacao == "8XY38Q683"


def test_grade_aliquota_iss_e_item(monkeypatch):
    nfse = _parse(monkeypatch, RECORTES_NOVOS + OCR_BASE)
    v = nfse.valores
    assert v.valor_servicos == pytest.approx(2795.21)
    assert v.valor_deducoes == pytest.approx(0.0)
    assert v.base_calculo == pytest.approx(2795.21)
    assert v.aliquota == pytest.approx(0.05)
    assert v.valor_iss == pytest.approx(139.76)
    assert v.valor_liquido_nfse == pytest.approx(2795.21)
    assert v.iss_retido is False
    for ret in (v.valor_pis, v.valor_cofins, v.valor_inss, v.valor_ir,
                v.valor_csll, v.outras_retencoes):
        assert ret == pytest.approx(0.0)
    assert nfse.servico_codigo == "1703"


def test_item_sem_s_inicial_vem_do_ocr_base(monkeypatch):
    # "erviço: 001703 - PLANEJAMENTO..." ("S" comido pelo OCR) -> item 17.03;
    # não depende dos recortes novos.
    nfse = _parse(monkeypatch, OCR_BASE)
    assert nfse.servico_codigo == "1703"


def test_entidades_e_endereco_tomador_caixa_alta(monkeypatch):
    nfse = _parse(monkeypatch, RECORTES_NOVOS + OCR_BASE)
    assert nfse.prestador.cnpj_cpf == "59132742000113"
    assert nfse.prestador.razao_social == "AVANÇO GESTÃO E ADMINISTRAÇÃO LTDA"
    t = nfse.tomador
    assert t.cnpj_cpf == "24890395000103"
    assert t.razao_social == "GUARAJUBA MALLS S/A"
    assert t.endereco.logradouro == "RODOVIA BA 099 ESTRADA DO COCO"
    assert t.endereco.cep == "42840310"


def test_recortes_sao_no_op_quando_campos_ja_lidos():
    ext = SPPdfExtractor.__new__(SPPdfExtractor)
    # Âncora do número presente -> nenhum recorte do topo (a página nem é tocada).
    assert ext._ocr_topo_cortado_camacari(None, 0, "Número da Nota\n159\n") == ""
    # Alíquota e ISS já lidos -> a grade não é relida.
    assert ext._ocr_grade_totais_camacari(
        None, 0, "Aliquota (%) 5,00\nValor do ISS (R$) 139,76\n") == ""


PDF_REAL = os.path.join(r"L:\USUARIOS\ANDERSON\ARQUIVOS DESKTOP\Notas", "GUARAJUBA MALLS - NFSe.pdf")


@pytest.mark.skipif(not os.path.exists(PDF_REAL), reason="PDF real fora do corpus local")
def test_recortes_na_imagem_real_da_pagina_8():
    import pymupdf
    ext = SPPdfExtractor.__new__(SPPdfExtractor)
    doc = pymupdf.open(PDF_REAL)
    try:
        page = doc[7]
        topo = ext._ocr_topo_cortado_camacari(page, 0, OCR_BASE)
        grade = ext._ocr_grade_totais_camacari(page, 0, OCR_BASE)
    finally:
        doc.close()
    assert "[[CAMACARI_MANUSCRITO=307]]" in topo
    assert "Código de autenticidade\n8XY38Q683" in topo
    assert grade == "Aliquota (%) 5,00\nValor do ISS (R$) 139,76"
