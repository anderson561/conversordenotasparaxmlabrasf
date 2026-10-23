# -*- coding: utf-8 -*-
r"""Novo layout: impresso "NOTA DE LOCAÇÃO" (`nota_locacao`), achado real
2026-10-16 no lote STAUMMAQ (`Scan2026-10-16_110738.pdf`, pág. 10): ELEVAR
LOCACAO E TRANSPORTES LTDA (CNPJ 22.471.804/0001-01, Dias d'Ávila/BA) ->
STAUMMAQ SERV TEC AUT MOTORES E MAQ LTDA (Simões Filho/BA), nota 1245, locação
de caminhão munck, R$ 18.500,00. Antes deste layout a página caía em
LAYOUT_GENERICO, era descartada ("Layout não reconhecido") e NENHUM XML saía.

Não é NFS-e: a própria nota declara a não incidência de ISS (LC 116/2003) e a
dispensa de documento fiscal (Lei 8.846/94). Convenção das faturas de locação
(Localiza/ARMAC/genérica): item 0601, CodigoVerificacao "FATURA", ISS zerado.

`MOCK_ELEVAR` é o texto REAL que o `_ocr_page` entrega para a página
(Tesseract, zoom 3), preservado verbatim: as linhas sintéticas `NOTALOC_*` dos
recortes dedicados (caixa da direita do cabeçalho, grade de itens, grade
DESTINATÁRIO por coluna) seguidas do texto de página inteira, com os quirks que
travam regressões:
  - o texto de página inteira NÃO traz o CNPJ nem a I.E. do emitente, e o
    rótulo "DATA DE EMISSÃO" vira "audi";
  - o item sai sem QUANTIDADE e sem a coluna VALOR TOTAL ("... MUNCK 18.500,00");
  - "VIA URBANA I" vira "VIA URBANA |" (o "|" também é separador de coluna);
  - o carimbo "VENCIMENTO: 15/05/2026" e a rubrica são anotações sobre o
    documento (ficam fora do recorte de itens pelo vão vertical);
  - a placa impressa é "RPZ 0I95"; o OCR lê "RPZ 0195" em qualquer zoom/PSM
    (I x 1) - vai para a discriminação com aviso, nunca "corrigida" no chute.
"""
import pytest

from src.extractors import nota_locacao as nl
from src.extractors.pdf_extractor import (
    LAYOUT_GENERICO, LAYOUT_NOTA_LOCACAO, SPPdfExtractor, _ibge_resolver,
)
from src.transformers.abrasf_transformer import Abrasf201Transformer

MOCK_ELEVAR = 'NOTALOC_CAB: NOTADE LOCAÇÃO Nº 1245\nNOTALOC_CAB: VIA ÚNICA\nNOTALOC_CAB: 30/04/2026\nNOTALOC_CAB: CN.P.J\nNOTALOC_CAB: 22.471.804/0001-01\nNOTALOC_CAB: INSCR. EST.\nNOTALOC_CAB: 124719970\nNOTALOC_ITEM: LOCAÇÃO DE CAMINHÃO MUNCK 1 18.500,00 18.500,00\nNOTALOC_ITEM: PLACA: RPZ 0195\nNOTALOC_ITEM: PERÍODO: 25 E 26/04/2026\nNOTALOC_DEST_NOME: STAUMMAQ SERV TEC AUT MOTORES E MAQ LTDA\nNOTALOC_DEST_CNPJ: 02.370.080/0001-00\nNOTALOC_DEST_ENDERECO: VIA URBANA I\nNOTALOC_DEST_BAIRRO: CIA SUL\nNOTALOC_DEST_CEP: 43.700-000\nNOTALOC_DEST_MUNICIPIO: SIMOES FILHO\nNOTALOC_DEST_UF: BA\nNOTALOC_DEST_TELEFONE: O O-\n\n8 08 — VAR | NOTADE LOCAÇÃO Nº 1245\n\nSOLUÇÕES EM MDVIMENTAÇÃO DE CARGAS VIA ÚNICA\n\nELEVAR LOCACAO E TRANSPORTES LTDA\nVIA DE LIGAÇÃO 614 LOT JARDIM ALVORADA PARQUE PETROPOLIS\naudi 30/04/2026\n\nDIAS D AVILA-BA Cep:42.850-000\n\nTel: (71) 3625-1255 (71) 99165-5840\n\nDESTINATÁRIO\n\nNome / Razão Social CNPJ / CPF\n\nSTAUMMAQ SERV TEC AUT MOTORES E MAQ LTDA 02.370.080/0001-00\n\nEndereço Bairro CEP\n\nVIA URBANA | CIA SUL 43.700-000\n\nMunicípio UF Telefone / Fax INSCRIÇÃO ESTADUAL / RG.\n\nSIMOES FILHO BA O O-\n\nDADOS DO DOCUMENTO\n\nDESCRIÇÃO VLR.UNITÁRIO VALOR TOTAL\n\nLOCAÇÃO DE CAMINHÃO MUNCK 18.500,00\nPLACA: RPZ 0195\nPERÍODO: 25 E 26/04/2026\n\nVALOR TOTAL DA NOTA DE LOCAÇÃO\n18.500,00\n\nINFORMAÇÕES ADICIONAIS\n“OPERAÇÃO NÃO SUJEITA A EMISSÃO DE DOCUMENTO FISCAL CONFORME LEI 8.846/94”\n\n“NÃO INCIDÊNCIA DE ISS CONFORME LEI COMPLEMENTAR 116/2003 QUE A EXCLUI A LOCAÇÃO DE BENS MÓVEIS DA LISTA DE\nSERVIÇOS”\n\nEMPRESA OPTANTE PELO SIMPLES NACIONAL LEI COMPLEMENTAR 116/2003\n\nATESTAMOS QUE OS DADOS ACIMA CONFEREM COM OS BENS CEDIDOS EM LOCAÇÃO PELA ELEVAR LOCACAO NOTA DE\nRANSPOR DA LOCAÇÃO Nº\nDATA DO RECEBIMENTO IDENTIFICAÇÃO E ASSINATURA DO RECEBEDOR | NOME LEGÍVEL\n| | 1245\n\n'

# Texto de página inteira sozinho (sem os recortes): PDF digital do mesmo
# impresso, ou recortes que falharam.
MOCK_ELEVAR_SEM_RECORTES = nl._sem_marcadores(MOCK_ELEVAR)


# Palavras REAIS do `image_to_data` (zoom 3) no bloco DESTINATÁRIO desta página:
# (left, top, width, height, texto).
PALAVRAS_DESTINATARIO = [
    (67, 496, 178, 23, 'DESTINATÁRIO'),
    (66, 545, 54, 15, 'Nome'), (127, 544, 5, 16, '/'), (140, 544, 58, 16, 'Razão'),
    (206, 543, 55, 16, 'Social'), (1269, 540, 53, 16, 'CNPJ'), (1335, 539, 5, 17, '/'),
    (1353, 539, 40, 17, 'CPF'),
    (67, 569, 168, 24, 'STAUMMAQ'), (246, 569, 79, 23, 'SERV'), (335, 568, 58, 23, 'TEC'),
    (403, 568, 57, 23, 'AUT'), (471, 567, 148, 23, 'MOTORES'), (631, 567, 17, 22, 'E'),
    (659, 566, 64, 24, 'MAQ'), (734, 566, 75, 23, 'LTDA'), (1268, 570, 265, 23, '02.370.080/0001-00'),
    (67, 612, 87, 20, 'Endereço'), (1129, 602, 54, 28, 'Bairro'), (1507, 605, 42, 16, 'CEP'),
    (64, 660, 48, 22, 'VIA'), (121, 660, 121, 22, 'URBANA'), (252, 659, 3, 22, '|'),
    (1128, 654, 49, 22, 'CIA'), (1185, 654, 55, 21, 'SUL'), (1506, 652, 150, 22, '43.700-000'),
    (67, 713, 88, 29, 'Município'), (819, 710, 26, 16, 'UF'), (889, 710, 81, 16, 'Telefone'),
    (983, 709, 5, 16, '/'), (1002, 710, 33, 15, 'Fax'), (1271, 707, 113, 22, 'INSCRIÇÃO'),
    (1393, 709, 107, 16, 'ESTADUAL'), (1511, 709, 6, 15, '/'), (1530, 709, 34, 15, 'RG.'),
    (70, 749, 113, 24, 'SIMOES'), (196, 749, 84, 22, 'FILHO'), (824, 745, 39, 22, 'BA'),
    (957, 742, 69, 22, 'O'), (1075, 741, 68, 22, 'O-'),
    (66, 814, 84, 19, 'DADOS'), (160, 814, 33, 18, 'DO'), (202, 813, 155, 19, 'DOCUMENTO'),
]

# Linhas REAIS (topo, altura, texto) do `image_to_data` PSM 6 do recorte da
# grade de itens: as 3 linhas da descrição e, depois de um vão, o carimbo de
# vencimento (o oval vira "palavra" de 190px) e o ruído da rubrica.
LINHAS_ITENS = [
    (92, 23, 'LOCAÇÃO DE CAMINHÃO MUNCK 1 18.500,00 18.500,00'),
    (141, 20, 'PLACA: RPZ 0195'),
    (180, 21, 'PERÍODO: 25 E 26/04/2026'),
    (488, 189, 'C rue 15/05/2026'),
    (681, 19, 'o a'),
    (786, 145, '|'),
]


def _palavras(tuplas):
    return [{'txt': t, 'norm': nl._sem_acento(t).upper().strip(':.;,'),
             'left': l, 'top': tp, 'width': w, 'height': h} for l, tp, w, h, t in tuplas]


def _converter(monkeypatch, tmp_path, texto, nome="nota.pdf"):
    pdf = tmp_path / nome
    pdf.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: texto)
    return SPPdfExtractor(str(pdf)).parse_multiple()


def _uma_nota(monkeypatch, tmp_path, texto, nome="nota.pdf"):
    notas = _converter(monkeypatch, tmp_path, texto, nome)
    assert len(notas) == 1
    return notas[0]


def _extrair(texto, via_ocr=True):
    ex = SPPdfExtractor.__new__(SPPdfExtractor)
    return nl.extrair(texto, _ibge_resolver, lambda d: SPPdfExtractor._validate_cnpj_cpf(ex, d), via_ocr=via_ocr)


# ---------------------------------------------------------------------------
# Detecção
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("texto", [MOCK_ELEVAR, MOCK_ELEVAR_SEM_RECORTES])
def test_detecta_nos_dois_detectores(tmp_path, texto):
    pdf = tmp_path / "n.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    ex = SPPdfExtractor(str(pdf))
    ex.raw_text = texto
    assert ex._detect_layout() == LAYOUT_NOTA_LOCACAO
    assert ex._detect_layout_page(texto) == LAYOUT_NOTA_LOCACAO


def test_sem_o_layout_a_pagina_era_generica():
    """Âncora do bug: sem nenhuma das 3 marcas o texto não é deste layout."""
    texto = MOCK_ELEVAR_SEM_RECORTES.replace('VALOR TOTAL DA NOTA DE LOCAÇÃO', 'VALOR TOTAL')
    assert not nl.eh_nota_locacao(texto)


@pytest.mark.parametrize("trecho, troca", [
    ('NOTADE LOCAÇÃO Nº 1245', 'NOTA DE COBRANÇA 1245'),     # sem o título
    ('DESTINATÁRIO', 'CLIENTE'),                             # sem o bloco do destinatário
])
def test_falta_de_ancora_estrutural_nao_detecta(trecho, troca):
    assert not nl.eh_nota_locacao(MOCK_ELEVAR_SEM_RECORTES.replace(trecho, troca))


def test_nfse_que_cita_nota_de_locacao_nao_vira_este_layout():
    assert not nl.eh_nota_locacao("NFS-e - Nota Fiscal de Serviços Eletrônica\n" + MOCK_ELEVAR_SEM_RECORTES)


def test_fatura_cpe_com_numero_da_nota_de_locacao_continua_cpe(tmp_path):
    """A fatura CPE cita "Número da Nota de Locação:" - não é o título deste impresso."""
    texto = ("CPE BAHIA COM DE APARELHOS TOP\ncpe tecnologia\nFATURA DE LOCAÇÃO\nNº 002023358\n"
             "Insc. Estadual: 67702460  CNPJ / CPF: 07.712.781/0001-96\nDados do Cliente\n"
             "Nome / Razão Social: DELTALINE SERVICOS LTDA.\nNúmero da Nota de Locação: 002023358\n"
             "Valor: 300,00\n")
    assert not nl.eh_nota_locacao(texto)
    pdf = tmp_path / "c.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    ex = SPPdfExtractor(str(pdf))
    ex.raw_text = texto
    assert ex._detect_layout() == 'cpe_locacao'


# ---------------------------------------------------------------------------
# Nota real completa
# ---------------------------------------------------------------------------

def test_campos_da_nota_1245(monkeypatch, tmp_path):
    nf = _uma_nota(monkeypatch, tmp_path, MOCK_ELEVAR)
    assert nf.numero == "1245"
    assert nf.codigo_verificacao == "FATURA"
    assert nf.data_emissao.strftime('%Y-%m-%dT%H:%M:%S') == "2026-04-30T00:00:00"
    assert nf.competencia.strftime('%Y-%m-%d') == "2026-04-01"

    p = nf.prestador
    assert p.cnpj_cpf == "22471804000101"
    assert p.razao_social == "ELEVAR LOCACAO E TRANSPORTES LTDA"
    assert p.endereco.logradouro == "VIA DE LIGAÇÃO"
    assert p.endereco.numero == "614"
    assert p.endereco.bairro == "LOT JARDIM ALVORADA PARQUE PETROPOLIS"
    assert p.endereco.codigo_municipio == "2910057"  # Dias d'Ávila/BA (API IBGE)
    assert p.endereco.uf == "BA"
    assert p.endereco.cep == "42850000"
    assert p.telefone == "7136251255"
    assert p.inscricao_municipal is None  # 124719970 é a INSCRIÇÃO ESTADUAL

    t = nf.tomador
    assert t.cnpj_cpf == "02370080000100"
    assert t.razao_social == "STAUMMAQ SERV TEC AUT MOTORES E MAQ LTDA"
    assert t.endereco.logradouro == "VIA URBANA I"
    assert t.endereco.bairro == "CIA SUL"
    assert t.endereco.codigo_municipio == "2930709"  # Simões Filho/BA
    assert t.endereco.uf == "BA"
    assert t.endereco.cep == "43700000"

    v = nf.valores
    assert v.valor_servicos == pytest.approx(18500.00)
    assert v.valor_liquido_nfse == pytest.approx(18500.00)
    assert v.base_calculo == 0.0 and v.aliquota == 0.0 and v.valor_iss == 0.0
    assert v.iss_retido is False

    assert nf.servico_codigo == "0601"
    assert nf.optante_simples_nacional is True
    assert nf.discriminacao == "LOCAÇÃO DE CAMINHÃO MUNCK PLACA: RPZ 0195 PERÍODO: 25 E 26/04/2026"
    assert "VENCIMENTO" not in nf.discriminacao and "15/05/2026" not in nf.discriminacao
    assert any("NOTA DE LOCAÇÃO" in a and "não é NFS-e" in a for a in nf.avisos)
    assert not any("prestador não identificados" in a for a in nf.avisos)


def test_xml_final_da_nota_1245(monkeypatch, tmp_path):
    xml = Abrasf201Transformer().transform(_uma_nota(monkeypatch, tmp_path, MOCK_ELEVAR))
    for trecho in (
        "<Numero>1245</Numero>", "<CodigoVerificacao>FATURA</CodigoVerificacao>",
        "<DataEmissao>2026-04-30T00:00:00</DataEmissao>", "<Competencia>2026-04-01</Competencia>",
        "<ValorServicos>18500.00</ValorServicos>", "<ValorIss>0.00</ValorIss>",
        "<Aliquota>0.00</Aliquota>", "<IssRetido>2</IssRetido>",
        "<ItemListaServico>0601</ItemListaServico>", "<Cnpj>22471804000101</Cnpj>",
        "<Cnpj>02370080000100</Cnpj>", "<CodigoMunicipio>2910057</CodigoMunicipio>",
        "<CodigoMunicipio>2930709</CodigoMunicipio>", "<OptanteSimplesNacional>1</OptanteSimplesNacional>",
        "<RegimeEspecialTributacao>6</RegimeEspecialTributacao>",
        "<MunicipioIncidencia>2910057</MunicipioIncidencia>",
    ):
        assert trecho in xml, trecho


def test_placa_lida_por_ocr_gera_aviso_e_nao_e_corrigida_no_chute():
    nota = _extrair(MOCK_ELEVAR, via_ocr=True)
    assert "RPZ 0195" in nota.discriminacao
    assert any("Placa" in a and "RPZ 0195" in a for a in nota.avisos)
    assert not any("Placa" in a for a in _extrair(MOCK_ELEVAR, via_ocr=False).avisos)


def test_item_recortado_traz_quantidade_unitario_e_total():
    nota = _extrair(MOCK_ELEVAR)
    assert len(nota.itens) == 1
    item = nota.itens[0]
    assert item.quantidade == 1
    assert item.valor_unitario == pytest.approx(18500.0)
    assert item.valor_total == pytest.approx(18500.0)
    assert not any("diverge" in a for a in nota.avisos)


# ---------------------------------------------------------------------------
# Sem os recortes (texto de página inteira só)
# ---------------------------------------------------------------------------

def test_sem_recortes_cnpj_do_emitente_vira_sentinela_com_aviso():
    nota = _extrair(MOCK_ELEVAR_SEM_RECORTES)
    assert nota.prestador.cnpj_cpf == "00000000000000"
    assert any("CNPJ do emitente" in a for a in nota.avisos)
    # o resto que o texto de página inteira traz continua certo
    assert nota.numero == "1245"
    assert nota.data_emissao.strftime('%d/%m/%Y') == "30/04/2026"  # única data do cabeçalho
    assert nota.valores.valor_servicos == pytest.approx(18500.0)
    assert nota.tomador.cnpj_cpf == "02370080000100"
    assert nota.tomador.endereco.codigo_municipio == "2930709"
    assert nota.discriminacao == "LOCAÇÃO DE CAMINHÃO MUNCK PLACA: RPZ 0195 PERÍODO: 25 E 26/04/2026"


def test_sem_recortes_endereco_e_bairro_do_tomador_nao_sao_adivinhados():
    nota = _extrair(MOCK_ELEVAR_SEM_RECORTES)
    assert nota.tomador.endereco.bairro == "Não informado"
    assert any("Bairro do destinatário" in a for a in nota.avisos)


def test_data_nunca_vem_do_periodo_nem_do_vencimento():
    texto = MOCK_ELEVAR_SEM_RECORTES.replace("audi 30/04/2026\n", "")
    nota = _extrair(texto)
    assert nota.data_emissao is None  # sem data no cabeçalho -> fallback com aviso no extrator


# ---------------------------------------------------------------------------
# Coerência e sentinelas
# ---------------------------------------------------------------------------

def test_numero_divergente_entre_leituras_vira_sentinela():
    texto = MOCK_ELEVAR.replace("NOTALOC_CAB: NOTADE LOCAÇÃO Nº 1245", "NOTALOC_CAB: NOTADE LOCAÇÃO Nº 1246")
    nota = _extrair(texto)
    assert nota.numero == "00000000"
    assert any("divergente" in a for a in nota.avisos)


def test_total_que_nao_fecha_com_os_itens_mantem_o_impresso_e_avisa():
    texto = MOCK_ELEVAR.replace("VALOR TOTAL DA NOTA DE LOCAÇÃO\n18.500,00", "VALOR TOTAL DA NOTA DE LOCAÇÃO\n18.600,00")
    nota = _extrair(texto)
    assert nota.valores.valor_servicos == pytest.approx(18600.0)
    assert any("diverge da soma dos itens" in a for a in nota.avisos)


def test_cnpj_do_emitente_com_dv_invalido_nao_e_aceito():
    texto = MOCK_ELEVAR.replace("NOTALOC_CAB: 22.471.804/0001-01", "NOTALOC_CAB: 22.471.804/0001-07")
    nota = _extrair(texto)
    assert nota.prestador.cnpj_cpf == "00000000000000"
    assert any("CNPJ do emitente" in a for a in nota.avisos)


# ---------------------------------------------------------------------------
# Recortes (funções puras sobre a geometria real)
# ---------------------------------------------------------------------------

def test_destinatario_por_colunas_com_palavras_reais():
    linhas = nl.destinatario_por_colunas(_palavras(PALAVRAS_DESTINATARIO), largura=1735)
    campos = dict(l.split(': ', 1) for l in linhas)
    assert campos['NOTALOC_DEST_NOME'] == "STAUMMAQ SERV TEC AUT MOTORES E MAQ LTDA"
    assert campos['NOTALOC_DEST_CNPJ'] == "02.370.080/0001-00"
    assert campos['NOTALOC_DEST_ENDERECO'] == "VIA URBANA I"   # "|" no meio da coluna = glifo I
    assert campos['NOTALOC_DEST_BAIRRO'] == "CIA SUL"
    assert campos['NOTALOC_DEST_CEP'] == "43.700-000"
    assert campos['NOTALOC_DEST_MUNICIPIO'] == "SIMOES FILHO"
    assert campos['NOTALOC_DEST_UF'] == "BA"


def test_barra_na_borda_da_coluna_e_linha_da_grade_nao_letra():
    palavras = PALAVRAS_DESTINATARIO + [(1118, 655, 3, 22, '|')]  # borda à esquerda de "Bairro"
    campos = dict(l.split(': ', 1) for l in nl.destinatario_por_colunas(_palavras(palavras), largura=1735))
    assert campos['NOTALOC_DEST_BAIRRO'] == "CIA SUL"
    assert campos['NOTALOC_DEST_ENDERECO'] == "VIA URBANA I"


def test_linhas_contiguas_corta_carimbo_e_rubrica():
    assert nl.linhas_contiguas(LINHAS_ITENS) == [
        'LOCAÇÃO DE CAMINHÃO MUNCK 1 18.500,00 18.500,00',
        'PLACA: RPZ 0195',
        'PERÍODO: 25 E 26/04/2026',
    ]


def test_dias_d_avila_com_apostrofo_lido_como_espaco_esta_na_tabela_ibge():
    assert _ibge_resolver.KNOWN_CITIES["DIAS D AVILA"] == "2910057"


def test_pagina_generica_continua_descartada(monkeypatch, tmp_path):
    """Não regressão: texto sem as âncoras continua sem XML."""
    texto = "DOCUMENTO QUALQUER\nCLIENTE: FULANO\nVALOR 18.500,00\n" * 3
    pdf = tmp_path / "g.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    ex = SPPdfExtractor(str(pdf))
    assert ex._detect_layout_page(texto) == LAYOUT_GENERICO
