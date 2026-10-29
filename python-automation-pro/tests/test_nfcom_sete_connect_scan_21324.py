# -*- coding: utf-8 -*-
"""NFCom ESCANEADA da SETE CONNECT (nota nº 21324 -> NORDESTE TUBETES
EMBALAGENS LTDA, R$109,99) - achado real 2026-10-26, pág. 3 de
Scan2026-10-26_095859.pdf.

`OCR_REAL` é o texto EXATO da leitura de página inteira do Tesseract
(`_ocr_page`, zoom 3x) desta página, sem edição. O OCR troca o 6 por 8 no
CNPJ do emitente ("13.080.537/0001-99") e na chave ("0913 0805 3700"), e lê
o endereço do tomador "148 - 146 G" (impresso "146 - 146 C"). Antes desta
correção o gate do layout exigia o CNPJ impresso exato e a nota caía no
fallback LAYOUT_NACIONAL: prestador sentinela 00000000000100, Valor dos
Serviços 0,00, Código de Verificação "XXXX-XXXX" e o Número do endereço do
tomador com ~250 caracteres de lixo (data, chave, protocolo, URL...).

`RECUT_ENDERECO` é o que a votação do recorte do bloco do tomador
(`_ocr_recut_tomador_nfcom_sete_connect`) devolve nesta página; `_ocr_page`
o prepende ao texto (fixture `OCR_COM_RECUT`)."""
import io

import pytest
from PIL import Image

from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_NFCOM_SETE_CONNECT

OCR_REAL = (
    'CS DOCUMENTO AUXILIAR DA NOTA FISCAL FATURA DE SERVIÇOS DE COMUNICAÇÃO ELETRÔNICA\n'
    '\n'
    'SETE CONNECT TECNOLOGIA DA INFORMACAO LTDA\n'
    'CNPJ: 13.080.537/0001-99\n'
    'IE: 82082280\n'
    'RUA DA MANGUEIRA, SN - SALA 02 - CENTRO\n'
    "Dias d'Avila - BA - 42850000\n"
    '| Telefone: 7136258577\n'
    '\n'
    'CLIENTE:\n'
    '\n'
    'NORDESTE TUBETES EMBALAGENS LTDA\n'
    'CNPJ: 11.474.414/0001-79 IE: 85352601\n'
    '\n'
    'ENDEREÇO:\n'
    '\n'
    'RUA BOA VIAGEM, 148 - 146 G - PARQUE PETROPOLIS\n'
    "Dias d'Avila / BA - 42850000\n"
    '\n'
    'DATA DE EMISSÃO: 03/09/2026 às 15:03:11\n'
    '\n'
    'CHAVE DE ACESSO:\n'
    '2926 0913 0805 3700 0199 6200 1000 0213 2410 1909 9216\n'
    '\n'
    'Protocolo de Autorização: 3292600232456708\n'
    '03/09/2026 às 15:03:12-0300\n'
    '\n'
    'hitps://dte-portal.svre.rs.gov.br/Nfcom/QrCode?chNFComs=2926\n'
    '091 7000199620010000213241019099216&tpAmbs1\n'
    '\n'
    'INFORMAÇÕES:\n'
    '\n'
    'Cod. Assinante: 2369 Contrato: 2369\n'
    'Telefone: 7136446346\n'
    '\n'
    'Período: 10/09/2026 à 10/10/2026\n'
    '\n'
    '] ONTRIBUINTE:\n'
    'REFERÊNCIA (ANO/MÊS): 09/2026 | AREA DOG E\n'
    '\n'
    'VENCIMENTO: 10/09/2026 APÓS VENCIMENTO COBRAR MULTA DE R$ 2,20 E JUROS DE R$ 0,04 AO DIA,\n'
    '\n'
    'TOTAL A PAGAR: R$ 109,99 |\n'
    'COD. ITENS crop UN arm V.UNIT. TOTAL PISICOFINS BC.ICMS ALIQ V.IGMS V.IBSUF V.cBs\n'
    '\n'
    '0100201 SERVICO COMUNICACAO MULTIMIDIA 5303 UN 1.0000 R$109,99 R$ 109,99 R$4,01 R$75,11 20,50%  R$1540  R$011 R$0,99\n'
    '\n'
    'CESAR\n'
    'TOTAL BC ICMS ES e\n'
    '\n'
    'VALOR ICMS\n'
    '\n'
    'IMPOSTO E CONTRIBUI O SOBRE BENS E SERVIÇOS (IBS E CBS)\n'
    '\n'
    'Alíquota IBS UF Redução Alíquota IBS UF Alíquota Efetiva IBS Valor Diterido IBS UF Valor BS\n'
    '0,10% . - . R$0,11\n'
    '0,90% E - - R$ 0,99\n'
    'INFORMAÇÕES COMPLEMENTARES\n'
    '= Documento emitido por empresa optante pelo Simples Nacional. - Nao gera direito a Credito Fiscal de ICMS, ISS e IPI conforme Lei Complementar 123/2006.\n'
    '\n'
    'Base de Cálculo IBS e CBS\n'
    '\n'
    'Ea oeTeIçAl Ros CÓDIGO DE BARRAS PIX\n'
    '03399.06661 40600.0000! | HI\n'
    '\n'
    '00 32833.201018 4 15650000010999\n'
    '\n'
    'REA DO CONTRIBUINTE E DETERMINAÇÕES DA ANATEL\n'
    '\n'
)

RECUT_ENDERECO = (
    "ENDEREÇO:\n"
    "RUA BOA VIAGEM, 146 - 146 C - PARQUE PETROPOLIS\n"
    "Dias d'Avila / BA - 42850000\n"
)
OCR_COM_RECUT = RECUT_ENDERECO + "\n" + OCR_REAL

CHAVE_IMPRESSA = "29260913060537000199620010000213241019099216"


def _parse(monkeypatch, tmp_path, texto):
    dummy = tmp_path / "scan_sete_connect_21324.pdf"
    dummy.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: texto)
    notas = SPPdfExtractor(str(dummy)).parse_multiple()
    assert len(notas) == 1
    return notas[0]


@pytest.fixture
def nfse(monkeypatch, tmp_path):
    return _parse(monkeypatch, tmp_path, OCR_COM_RECUT)


def test_ocr_real_traz_os_erros_que_derrubavam_o_gate():
    assert "13.080.537/0001-99" in OCR_REAL
    assert "13.060.537" not in OCR_REAL
    assert "0913 0805 3700" in OCR_REAL


def test_layout_detectado_mesmo_com_cnpj_lido_errado(tmp_path):
    dummy = tmp_path / "d.pdf"
    dummy.write_bytes(b"%PDF-1.4")
    ex = SPPdfExtractor(str(dummy))
    assert ex._detect_layout_page(OCR_REAL) == LAYOUT_NFCOM_SETE_CONNECT
    assert SPPdfExtractor._eh_nfcom_sete_connect(OCR_REAL)


def test_gate_nao_captura_outro_emitente():
    outro = OCR_REAL.replace("13.080.537/0001-99", "13.080.537/0002-80")
    assert not SPPdfExtractor._eh_nfcom_sete_connect(outro)
    sem_titulo = OCR_REAL.replace("FATURA DE SERVIÇOS DE COMUNICAÇÃO ELETRÔNICA", "")
    assert not SPPdfExtractor._eh_nfcom_sete_connect(sem_titulo)


def test_chave_reparada_pelo_cnpj_fixo_e_confirmada_pelo_dv():
    assert SPPdfExtractor._dv_chave_nfe(CHAVE_IMPRESSA[:43]) == CHAVE_IMPRESSA[43]
    assert SPPdfExtractor._chave_nfcom_sete_connect(OCR_REAL) == CHAVE_IMPRESSA
    # Outro dígito errado FORA do CNPJ: o DV não fecha -> nada é inventado.
    corrompida = OCR_REAL.replace("0213 2410", "0213 2419")
    assert SPPdfExtractor._chave_nfcom_sete_connect(corrompida) is None


def test_prestador(nfse):
    p = nfse.prestador
    assert p.cnpj_cpf == "13060537000199"
    assert p.razao_social == "SETE CONNECT TECNOLOGIA DA INFORMACAO LTDA"
    assert p.endereco.logradouro == "RUA DA MANGUEIRA"
    assert p.endereco.numero == "SN"
    assert p.endereco.complemento == "SALA 02"
    assert p.endereco.bairro == "CENTRO"
    assert p.endereco.codigo_municipio == "2910057"
    assert p.endereco.cep == "42850000"
    assert p.telefone == "7136258577"


def test_tomador(nfse):
    t = nfse.tomador
    assert t.cnpj_cpf == "11474414000179"
    assert t.razao_social == "NORDESTE TUBETES EMBALAGENS LTDA"
    e = t.endereco
    assert e.logradouro == "RUA BOA VIAGEM"
    assert e.numero == "146"
    assert e.complemento == "146 C"
    assert e.bairro == "PARQUE PETROPOLIS"
    assert e.codigo_municipio == "2910057"
    assert e.uf == "BA"
    assert e.cep == "42850000"
    assert t.telefone == "7136446346"


def test_tomador_sem_recut_nao_vaza_bloco_da_direita(monkeypatch, tmp_path):
    # Sem o recorte (votação sem maioria), fica a leitura de página inteira:
    # campos curtos e sem lixo, nunca o blob de data/chave/protocolo.
    e = _parse(monkeypatch, tmp_path, OCR_REAL).tomador.endereco
    assert e.logradouro == "RUA BOA VIAGEM"
    assert e.bairro == "PARQUE PETROPOLIS"
    assert e.codigo_municipio == "2910057"
    assert len(e.numero) <= 5 and "CHAVE" not in e.numero


def test_numero_datas_e_codigo(nfse):
    assert nfse.numero == "21324"
    assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "03/09/2026 15:03:11"
    assert nfse.competencia.strftime("%Y-%m") == "2026-09"
    assert nfse.codigo_verificacao == CHAVE_IMPRESSA
    assert nfse.servico_codigo == "0000"


def test_valores(nfse):
    v = nfse.valores
    assert v.valor_servicos == pytest.approx(109.99)
    assert v.valor_liquido_nfse == pytest.approx(109.99)
    assert v.base_calculo == 0.0 and v.aliquota == 0.0 and v.valor_iss == 0.0
    assert not any("divergem" in a for a in nfse.avisos)


def test_valores_de_conferencia():
    lidos = SPPdfExtractor._valores_conferencia_nfcom_sete_connect(OCR_REAL)
    assert lidos["TOTAL A PAGAR"] == pytest.approx(109.99)
    assert lidos["TOTAL dos itens"] == pytest.approx(109.99)
    assert lidos["VALOR NFF"] == 0.0   # quadro some da leitura de página inteira


def test_divergencia_de_valores_vira_aviso(monkeypatch, tmp_path):
    texto = OCR_COM_RECUT.replace("TOTAL A PAGAR: R$ 109,99", "TOTAL A PAGAR: R$ 199,99")
    n = _parse(monkeypatch, tmp_path, texto)
    assert n.valores.valor_servicos == pytest.approx(199.99)
    assert any("divergem" in a for a in n.avisos)


def test_valor_pelo_item_quando_total_a_pagar_ilegivel(monkeypatch, tmp_path):
    texto = OCR_COM_RECUT.replace("TOTAL A PAGAR: R$ 109,99 |", "")
    n = _parse(monkeypatch, tmp_path, texto)
    assert n.valores.valor_servicos == pytest.approx(109.99)


def test_discriminacao_e_simples(nfse):
    assert nfse.discriminacao == (
        "SERVICO COMUNICACAO MULTIMIDIA - Período: 10/09/2026 à 10/10/2026 - Referência: 09/2026")
    assert nfse.optante_simples_nacional is True


class _Pix:
    def __init__(self):
        buf = io.BytesIO()
        Image.new("RGB", (10, 10), "white").save(buf, format="PNG")
        self._png = buf.getvalue()

    def tobytes(self, fmt):
        return self._png


class _Page:
    class rect:
        x0, y0, width, height = 0.0, 0.0, 578.16, 824.4

    def get_pixmap(self, matrix=None, clip=None):
        return _Pix()


def _fake_tesseract(monkeypatch, linhas):
    seq = iter(linhas)
    monkeypatch.setattr(
        "pytesseract.image_to_string",
        lambda img, lang=None, config=None: (
            "NORDESTE TUBETES EMBALAGENS LTDA\nCNPJ: 11.474.414/0001-79\n\nENDEREÇO:\n\n"
            + next(seq) + "\nDias d'Avila / BA - 42850000\n"))


def test_votacao_do_recorte_maioria_por_campo(monkeypatch):
    # As 10 leituras reais variam entre "146"/"148" e "C"/"G" - vence a
    # maioria absoluta de cada campo.
    linhas = (["RUA BOA VIAGEM, 146 - 146 C - PARQUE PETROPOLIS"] * 6
              + ["RUA BOA VIAGEM, 148 - 146 C - PARQUE PETROPOLIS"] * 2
              + ["RUA BOA VIAGEM, 146 - 146 G - PARQUE PETROPOLIS"] * 2)
    _fake_tesseract(monkeypatch, linhas)
    assert SPPdfExtractor._ocr_recut_tomador_nfcom_sete_connect(_Page()) == RECUT_ENDERECO


def test_votacao_sem_maioria_devolve_vazio(monkeypatch):
    linhas = (["RUA BOA VIAGEM, 146 - 146 C - PARQUE PETROPOLIS"] * 5
              + ["RUA BOA VIAGEM, 148 - 146 C - PARQUE PETROPOLIS"] * 5)
    _fake_tesseract(monkeypatch, linhas)
    assert SPPdfExtractor._ocr_recut_tomador_nfcom_sete_connect(_Page()) == ""
