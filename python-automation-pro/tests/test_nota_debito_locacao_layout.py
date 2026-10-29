# -*- coding: utf-8 -*-
r"""Novo layout: impresso "NOTA DÉBITO / FATURA" de locação (`nota_debito_locacao`),
achado real 2026-10-23 (`Notas/092026/locacao.pdf`): ANA CELIA MOREIRA RIBEIRO
(CNPJ 45.282.926/0001-55, Salvador/BA) -> SINAL CONSTRUTORA LTDA (CNPJ
33.811.381/0001-48, Pojuca/BA), "NOTA DÉBITO Nº 36" / "FATURA 005-2026",
locação de caçamba truck (placas BXB3B34 e KHY9526), R$ 17.827,08.

O PDF é FOTO de celular de cabeça para baixo, sem camada de texto. O
`_ocr_page` já acertava a rotação de 180° (placar 12 contra 0 em 0°), mas a
leitura de página inteira não traz nenhuma caixa de valor e nenhum layout
reconhecia o impresso: a página caía em LAYOUT_GENERICO, era descartada e a
conversão abortava com "parece ser baseado em imagem/scan ou vazio".

`MOCK_REAL` é o texto REAL que o `_ocr_page` entrega para a página (Tesseract,
zoom 3, já girada 180°), preservado verbatim: as linhas sintéticas `NOTADEB_*`
dos recortes por caixa seguidas do texto de página inteira, com os quirks que
travam regressões:
  - o texto de página inteira NÃO traz datas, nome/CNPJ/município do tomador,
    valores dos itens nem o "TOTAL DA FATURA" (todas em caixas com borda);
  - o CNPJ do emitente sai sem pontuação ("452829260001-55") e o CEP com
    vírgula ("41.500,240");
  - o "TOTAL DA FATURA" está sob marca-texto e é ilegível em qualquer
    recorte/variante: o valor vem da soma dos itens, com aviso;
  - o "SEM" de "SEM FORNECIMENTO DE MÃO DE OBRA" está sob marca-texto (lido
    "Szfi"/vazio): vira "SEM" com aviso, nunca "COM".

Decisões do usuário (2026-10-23): Número = número da FATURA sem ano e sem
zeros à esquerda ("005-2026" -> "5"), não o "NOTA DÉBITO Nº 36"; competência
= mês da DATA DE EMISSÃO (02/10/2026 -> 2026-10-01), não o período da locação
(09/2026).
"""
import pytest

from src.extractors import nota_debito_locacao as nd
from src.extractors import nota_locacao as nl
from src.extractors.pdf_extractor import (
    LAYOUT_NOTA_DEBITO_LOCACAO, LAYOUT_NOTA_LOCACAO, SPPdfExtractor, _ibge_resolver,
)
from src.transformers.abrasf_transformer import Abrasf201Transformer

MOCK_REAL = 'NOTADEB_EMISSAO: 02/10/2026\nNOTADEB_VENCIMENTO: 15/10/2026\nNOTADEB_TOM_NOME: SINAL CONSTRUTORA LTDA\nNOTADEB_TOM_CNPJ: 33811381000148\nNOTADEB_TOM_CEP: 48120-000\nNOTADEB_TOM_ENDERECO: EVANGELINA SERQUEIRA DIAS 9995\nNOTADEB_TOM_BAIRRO: NOVA POJUCA\nNOTADEB_TOM_MUNICIPIO: POJUCA\nNOTADEB_TOM_UF: BA\nNOTADEB_ITEM_DESC: LOCAÇÃO DE CAÇAMBA TRUCK\nNOTADEB_ITEM_PLACA: BXB3B34\nNOTADEB_ITEM_PLACA: KHY9526\nNOTADEB_ITEM_MAO_DE_OBRA: Szfi FORNECIMENTO DE MÃO DE OBRA\nNOTADEB_ITEM_MAO_DE_OBRA: FORNECIMENTO DE MÃO DE OBRA\nNOTADEB_ITEM_PERIODO: 01/09/2026 A 30/09/2026\nNOTADEB_ITEM_VALOR: 7.327,08\nNOTADEB_ITEM_VALOR: 10.500,00\n\nNOTA DEBITO Nº 36\n\nANA CELIA MOREIRA RIBEIRO\nCNPJ 452829260001-55\n\nTRAVESSA SÃO JOSÉ 39 SÃO CRISTOVÃO\nSALVADOR, BA CEP: 41.500,240\n\nEMAIL: juilsonribeiro. boipbol combr - TEL: (71) 98196-2243\n\nFATURA 005-2026\n\nDATA EMISSAO VENCIMENTO\n\nNATUREZA DA OPERAÇÃO\n\nALUGUEL DE MÁQUINAS E EQUIPAMENTOS PARA CONSTRUÇÃO SEM OPERADOR\n\nTOMADOR DO SERVIÇO\nNOME/RAZÃO SOCIAL: CNPJ:\n\nENDEREÇO: BAIRRO: CEP\n\nNOVA POJUCA sEao nos\n\nMUNICIPIO UF: INSC, ESTADUAL INSC. MUNICIPAL A\nETEFPEEESS CP OO.\n\nDESCRIÇÃO QUANT. DIAS PERIODO\n\nLOCAÇÃO DE CAÇAMBA TRUCK\n\n01/09/2026\nA\n30/09/2026\n\nFEDERAL NP 116/2003 DE 31/07112003 E LEI\n04/12/2003 - D.O.M DE 04/12/2003\n\n'

# Texto de página inteira sozinho (recortes falharam / PDF digital).
MOCK_SEM_RECORTES = nd._sem_marcadores(MOCK_REAL)

# Texto da página LIDA EM 0° (sem girar) pelo mesmo `_ocr_page`: lixo invertido.
TRECHO_0_GRAUS = "E00Z/21/v0 20 IN'O'Q - E00Z/ZT/PO\n1/3713 EO0ZITLO/TE 3Q E00Z/9TT dN 1VBIGII\nVENLVA VA TVLOL\n"


def _validar(d):
    ex = SPPdfExtractor.__new__(SPPdfExtractor)
    return SPPdfExtractor._validate_cnpj_cpf(ex, d)


def _extrair(texto, via_ocr=True):
    return nd.extrair(texto, _ibge_resolver, _validar, via_ocr=via_ocr)


def _uma_nota(monkeypatch, tmp_path, texto):
    pdf = tmp_path / "locacao.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: texto)
    notas = SPPdfExtractor(str(pdf)).parse_multiple()
    assert len(notas) == 1
    return notas[0]


# ---------------------------------------------------------------------------
# Detecção e rotação
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("texto", [MOCK_REAL, MOCK_SEM_RECORTES])
def test_detecta_nos_dois_detectores(tmp_path, texto):
    pdf = tmp_path / "n.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    ex = SPPdfExtractor(str(pdf))
    ex.raw_text = texto
    assert ex._detect_layout() == LAYOUT_NOTA_DEBITO_LOCACAO
    assert ex._detect_layout_page(texto) == LAYOUT_NOTA_DEBITO_LOCACAO


def test_leitura_girada_vence_a_leitura_em_0_graus():
    """A rotação de 180° é achada pelo placar já existente do `_ocr_page`: a
    leitura invertida pontua 0, a girada passa do limiar de rotação."""
    assert SPPdfExtractor._score_ocr_text(TRECHO_0_GRAUS) == 0
    assert SPPdfExtractor._score_ocr_text(MOCK_SEM_RECORTES) >= SPPdfExtractor._OCR_ROTACAO_LIMIAR
    assert not nd.eh_nota_debito_locacao(TRECHO_0_GRAUS)


@pytest.mark.parametrize("trecho, troca", [
    ("NOTA DEBITO Nº 36", "NOTA 36"),                      # sem o título
    ("FATURA 005-2026", "FATURA"),                          # sem o número da fatura
    ("NATUREZA DA OPERAÇÃO", "OPERAÇÃO"),                   # sem a natureza da operação
    ("TOMADOR DO SERVIÇO", "CLIENTE"),                      # sem o bloco do tomador
])
def test_falta_de_ancora_estrutural_nao_detecta(trecho, troca):
    assert trecho in MOCK_SEM_RECORTES
    assert not nd.eh_nota_debito_locacao(MOCK_SEM_RECORTES.replace(trecho, troca))


def test_nfse_que_cita_nota_de_debito_nao_vira_este_layout():
    assert not nd.eh_nota_debito_locacao("NFS-e - Nota Fiscal de Serviços Eletrônica\n" + MOCK_SEM_RECORTES)


def test_nota_de_locacao_elevar_continua_no_layout_dela(tmp_path):
    from tests.test_nota_locacao_elevar_layout import MOCK_ELEVAR
    assert not nd.eh_nota_debito_locacao(MOCK_ELEVAR)
    pdf = tmp_path / "e.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    ex = SPPdfExtractor(str(pdf))
    ex.raw_text = MOCK_ELEVAR
    assert ex._detect_layout() == LAYOUT_NOTA_LOCACAO


# ---------------------------------------------------------------------------
# Nota real completa
# ---------------------------------------------------------------------------

def test_campos_da_fatura_005_2026(monkeypatch, tmp_path):
    nf = _uma_nota(monkeypatch, tmp_path, MOCK_REAL)
    assert nf.numero == "5"  # decisão do usuário: FATURA 005-2026 -> 5 (não a NOTA DÉBITO 36)
    assert nf.codigo_verificacao == "FATURA"
    assert nf.data_emissao.strftime('%Y-%m-%dT%H:%M:%S') == "2026-10-02T00:00:00"
    # decisão do usuário: competência = mês da emissão, não o período 09/2026
    assert nf.competencia.strftime('%Y-%m-%d') == "2026-10-01"

    p = nf.prestador
    assert p.cnpj_cpf == "45282926000155"
    assert p.razao_social == "ANA CELIA MOREIRA RIBEIRO"
    assert p.endereco.logradouro == "TRAVESSA SÃO JOSÉ"
    assert p.endereco.numero == "39"
    assert p.endereco.bairro == "SÃO CRISTOVÃO"
    assert p.endereco.codigo_municipio == "2927408"  # Salvador/BA
    assert p.endereco.uf == "BA"
    assert p.endereco.cep == "41500240"
    assert p.telefone == "71981962243"

    t = nf.tomador
    assert t.cnpj_cpf == "33811381000148"
    assert t.razao_social == "SINAL CONSTRUTORA LTDA"
    assert t.endereco.logradouro == "EVANGELINA SERQUEIRA DIAS"
    assert t.endereco.numero == "9995"
    assert t.endereco.bairro == "NOVA POJUCA"
    assert t.endereco.codigo_municipio == "2925204"  # Pojuca/BA
    assert t.endereco.uf == "BA"
    assert t.endereco.cep == "48120000"

    v = nf.valores
    assert v.valor_servicos == pytest.approx(17827.08)
    assert v.valor_liquido_nfse == pytest.approx(17827.08)
    assert v.base_calculo == 0.0 and v.aliquota == 0.0 and v.valor_iss == 0.0
    assert v.iss_retido is False

    assert nf.servico_codigo == "0601"
    assert nf.optante_simples_nacional is False  # não impresso: não presumido
    assert nf.discriminacao == (
        "LOCAÇÃO DE CAÇAMBA TRUCK - PLACAS BXB3B34 R$ 7.327,08 / KHY9526 R$ 10.500,00"
        " - PERÍODO 01/09/2026 A 30/09/2026 - SEM FORNECIMENTO DE MÃO DE OBRA")
    for anotacao in ("TRANSPORTE", "Rateio", "VISTO", "018", "SICOOB", "PIX"):
        assert anotacao not in nf.discriminacao
    assert any("NOTA DÉBITO / FATURA" in a and "não é NFS-e" in a for a in nf.avisos)
    assert any("FATURA" in a and "NOTA DÉBITO Nº 36" in a for a in nf.avisos)
    assert any("TOTAL DA FATURA" in a and "17.827,08" in a for a in nf.avisos)
    # placas lidas por OCR: aviso só quando a página veio do OCR
    assert any("Placas" in a and "BXB3B34" in a for a in _extrair(MOCK_REAL, via_ocr=True).avisos)
    assert not any("Placas" in a for a in _extrair(MOCK_REAL, via_ocr=False).avisos)


def test_xml_final_da_fatura_005_2026(monkeypatch, tmp_path):
    xml = Abrasf201Transformer().transform(_uma_nota(monkeypatch, tmp_path, MOCK_REAL))
    for trecho in (
        "<Numero>5</Numero>", "<CodigoVerificacao>FATURA</CodigoVerificacao>",
        "<DataEmissao>2026-10-02T00:00:00</DataEmissao>", "<Competencia>2026-10-01</Competencia>",
        "<ValorServicos>17827.08</ValorServicos>", "<ValorLiquidoNfse>17827.08</ValorLiquidoNfse>",
        "<ValorIss>0.00</ValorIss>", "<BaseCalculo>0.00</BaseCalculo>", "<Aliquota>0.00</Aliquota>",
        "<IssRetido>2</IssRetido>", "<ItemListaServico>0601</ItemListaServico>",
        "<Cnpj>45282926000155</Cnpj>", "<Cnpj>33811381000148</Cnpj>",
        "<CodigoMunicipio>2927408</CodigoMunicipio>", "<CodigoMunicipio>2925204</CodigoMunicipio>",
        "<OptanteSimplesNacional>2</OptanteSimplesNacional>",
        "<MunicipioIncidencia>2927408</MunicipioIncidencia>",
    ):
        assert trecho in xml, trecho
    assert "<Numero>36</Numero>" not in xml


# ---------------------------------------------------------------------------
# Decisões, coerência e sentinelas
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("impresso, numero", [
    ("FATURA 005-2026", "5"), ("FATURA 0120-2026", "120"), ("FATURA 7", "7"),
])
def test_numero_e_o_da_fatura_sem_ano_e_sem_zeros(impresso, numero):
    assert _extrair(MOCK_REAL.replace("FATURA 005-2026", impresso)).numero == numero


def test_competencia_segue_a_emissao_e_nao_o_periodo(monkeypatch, tmp_path):
    texto = MOCK_REAL.replace("NOTADEB_EMISSAO: 02/10/2026", "NOTADEB_EMISSAO: 28/11/2026")
    nf = _uma_nota(monkeypatch, tmp_path, texto)
    assert nf.competencia.strftime('%Y-%m-%d') == "2026-11-01"


def test_total_legivel_igual_a_soma_nao_gera_aviso_de_total():
    nota = _extrair(MOCK_REAL.replace("NOTADEB_ITEM_PERIODO", "NOTADEB_TOTAL: 17.827,08\nNOTADEB_ITEM_PERIODO"))
    assert nota.valores.valor_servicos == pytest.approx(17827.08)
    assert not any("TOTAL DA FATURA" in a for a in nota.avisos)


def test_total_legivel_divergente_mantem_o_impresso_com_aviso():
    nota = _extrair(MOCK_REAL.replace("NOTADEB_ITEM_PERIODO", "NOTADEB_TOTAL: 17.000,00\nNOTADEB_ITEM_PERIODO"))
    assert nota.valores.valor_servicos == pytest.approx(17000.00)
    assert any("diverge da soma dos itens" in a for a in nota.avisos)


def test_mao_de_obra_com_nunca_vira_sem():
    texto = MOCK_REAL.replace("NOTADEB_ITEM_MAO_DE_OBRA: FORNECIMENTO", "NOTADEB_ITEM_MAO_DE_OBRA: COM FORNECIMENTO")
    nota = _extrair(texto)
    assert "COM FORNECIMENTO DE MÃO DE OBRA" in nota.discriminacao
    assert "SEM FORNECIMENTO" not in nota.discriminacao


def test_mao_de_obra_ilegivel_fica_fora_da_discriminacao():
    texto = "\n".join(l for l in MOCK_REAL.splitlines() if "MAO_DE_OBRA" not in l)
    assert "FORNECIMENTO" not in _extrair(texto).discriminacao


def test_sem_recortes_campos_ilegiveis_viram_sentinela_com_aviso():
    nota = _extrair(MOCK_SEM_RECORTES)
    # o que o texto de página inteira traz continua certo
    assert nota.numero == "5"
    assert nota.prestador.cnpj_cpf == "45282926000155"
    assert nota.prestador.endereco.codigo_municipio == "2927408"
    # o resto não é inventado
    assert nota.data_emissao is None
    assert nota.tomador.cnpj_cpf == "00000000000000"
    assert nota.tomador.razao_social == "Tomador Não Identificado"
    assert nota.valores.valor_servicos == 0.0
    assert any("CNPJ do tomador" in a for a in nota.avisos)


def test_cnpj_do_emitente_com_dv_invalido_vira_sentinela():
    nota = _extrair(MOCK_REAL.replace("CNPJ 452829260001-55", "CNPJ 452829260001-56"))
    assert nota.prestador.cnpj_cpf == "00000000000000"
    assert any("CNPJ do emitente" in a for a in nota.avisos)


# ---------------------------------------------------------------------------
# Funções puras dos recortes
# ---------------------------------------------------------------------------

def test_votacao_posicional_dos_valores_dos_itens():
    """Leituras REAIS das 6 variantes da coluna TOTAL: as binarizadas 90/110
    leem "10.500,09"; a votação fica com "10.500,00"."""
    leituras = [nd.valores_moeda(t) for t in (
        "7.327,08] * // 10.500,001 -", "7.327,08] * // 10.500,0014 *", "7.327,08) * // 10.500,00] -",
        "7.327,08 // 10.500,09", "7.327,08) - // 10.500,09] -", "7.327,08] * // 10.500,00] *")]
    assert nd.votar_listas(leituras) == ["7.327,08", "10.500,00"]


def test_normalizadores_de_caixa():
    assert nd.norm_data("[ 02/10/2026") == "02/10/2026"
    assert nd.norm_data("31/02/2026") is None
    assert nd.norm_uf("BAI") == "BA" and nd.norm_uf("Ea // BA") == "BA"
    assert nd.norm_cnpj("811.381/0001.48 ]", _validar) is None  # truncado
    assert nd.norm_cnpj("33.811.381/0001.48", _validar) == "33811381000148"
    assert nd.placas("BXB3B34 — // KHY9526 —") == ["BXB3B34", "KHY9526"]
    assert nd._corta_apos_sufixo("SINAL CONSTRUTORA LTDA TR") == "SINAL CONSTRUTORA LTDA"


def test_colunas_da_grade_pelo_vao_entre_caixas():
    """Palavras REAIS (zoom 3) da linha ENDEREÇO | BAIRRO | CEP do tomador."""
    ws = [{'txt': t, 'left': l, 'width': w, 'height': 22} for l, w, t in (
        (131, 160, 'EVANGELINA'), (301, 158, 'SERQUEIRA'), (469, 66, 'DIAS'), (545, 64, '9995'),
        (734, 79, 'NOVA'), (821, 107, 'POJUCA'), (1366, 150, '48120-000'))]
    assert nd._colunas_por_vao(ws) == ["EVANGELINA SERQUEIRA DIAS 9995", "NOVA POJUCA", "48120-000"]


def test_nota_debito_reaproveita_o_modelo_da_nota_de_locacao():
    assert isinstance(_extrair(MOCK_REAL), nl.NotaLocacao)
