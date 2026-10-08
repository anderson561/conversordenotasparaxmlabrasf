# Achado real 2026-10-08: "NF 28203 MASSA.pdf" (VALESTRA NEGOCIOS E INVESTIMENTOS
# LTDA -> MASSA ALIMENTACAO E SERVICOS S/A, NFS-e de Sao Paulo ESCANEADA, 2
# paginas: a 1 e a nota, a 2 e o anexo IBS/CBS). O XML saia com
# <Numero>59920149</Numero>: a leitura de pagina inteira descartou a caixa
# "Numero da Nota / Data e Hora de Emissao" (a foto esta nitida; o Tesseract so
# nao a segmenta), o recorte do cabecalho nao achou o rotulo e escolheu, pela
# "assinatura" 6+ digitos no topo da regiao, a INSCRICAO MUNICIPAL do prestador
# ("Inscricao Municipal: 59920149"). O numero impresso e 00028203.
#
# Correcoes cobertas aqui:
#  1. recorte do cabecalho: relê SO a regiao do canto superior direito antes de
#     cair na assinatura numerica, e a assinatura nunca aceita um token que o
#     proprio documento rotula como Inscricao Municipal/CNPJ/CEP;
#  2. `_extrair_numero` (SP escaneada): o "Identificador" de 50 digitos do anexo
#     IBS/CBS (autoverificavel: DV modulo 11 + CNPJ do prestador + AAMM) vence a
#     leitura da caixa; sem chave valida, candidato = Inscricao Municipal vira
#     sentinela + aviso, NUNCA o numero do nome do arquivo.
#
# Os textos abaixo sao o OCR REAL (SPPdfExtractor._extract_via_ocr) da nota,
# antes (PRE: Numero errado = IM) e depois (POS) da correcao do recorte.
import os

import pytest

from src.extractors import sp_identificador as sp_ident
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_SAO_PAULO_2

PAG1_PRE = """IRRF (R$) CSLL (R$) COFINS (R$) PIS/PASEP (R$)
133,31 88,87 266,61 57,77
Código do Serviço
01899 - Planejamento, coordenacao, programacao ou organizacao tecnica, financeira ou administrativa.

Número da Nota
59920149
Código de Verificação
IPDT-SIPH

»

Volestrá

PIS/COFINS

Valor Aprox.

INSS (R$)

Código do Serviço

20260227U30646364000104

Município: Salvador

PREFEITURA DO MUNICÍPIO DE SÃO PAULO

SECRETARIA MUNICIPAL DA FAZENDA
27/02/2026 13:42:22
NOTA FISCAL ELETRÔNICA DE SERVIÇOS - NFS-e Código de Verificação
RPS Nº 28140 Série 1, emitido em 27/02/2026 IPDT-SIPH
PRESTADOR DE SERVIÇOS

CPF/CNPJ: 30.646.364/0001-04
Nome/Razão Social: -VALESTRA NEGOCIOS E INVESTIMENTOS LTDA - MATRIZ

Endereço: AVENIDA DAS NAÇÕES UNIDAS 12901 - BROOKLIN PAULISTA - CONJ NORTE BLOCO A SALA 3301 - CE...
UF: SP

Inscrição Municipal: 59920149

Município: São Paulo

TOMADOR DE SERVIÇOS

Nome/Razão Social: MASSA ALIMENTACAO E SERVICOS S/A

CPF/CNPJ: 09.033.381/0001-80
Endereço: R SENADOR THEOTONIO VILELA 110 - PARQUE BELA VISTA - SALAS 203 E 204 - CEP: 40279-435

Inscrição Municipal:

UF: BA E-mail: oriane.costaG)nwgroup.com.br
INTERMEDIÁRIO DE SERVIÇOS

CPF/CNPJ: Nome/Razão Social:

DISCRIMINAÇÃO DOS SERVIÇOS

Servicos Prestados
Vencimento: 06/03/2026
Valor Liquido: R$ 8340.51
AUDITORIA FEDERAL

O pagamento deverá ser realizado exclusivamente pelo BOLETO, que será enviado junto a NF-e.

Tributos: R$ 990,91 - 11,15%

VALOR TOTAL DO SERVIÇO = R$ 8.887,07

IRRF (R$) CSLL (R$) COFINS (R$) PIS/PASEP (R$) IPI(R$)
- 133,31 88,87 266,61 57,77 0,00

01899 - Planejamento, coordenacao, programacao ou organizacao tecnica, financeira ou administrativa.

0,00 8.887,07 5,00% 444,35 0,00
São Paulo - SP . R$ 990,91 (11,15%) [IBPT

(1) Esta NFS-e foi emitida com respaldo na Lei nº 14.097/2005; (2) O ISS desta NFS-e é devido DENTRO do Município de
São Paulo; (3) Esta NFS-e não gera crédito; (4) Esta NFS-e substitui o RPS Nº 28140 Série 1, emitido em 27/02/2026;

OUTRAS INFORMAÇÕES

Page 1 of 2

"""

PAG1_POS = """IRRF (R$) CSLL (R$) COFINS (R$) PIS/PASEP (R$)
133,31 88,87 266,61 57,77
Código do Serviço
01899 - Planejamento, coordenacao, programacao ou organizacao tecnica, financeira ou administrativa.

Número da Nota
00028203
Data e Hora de Emissão
27/02/2026 13:42:22
Código de Verificação
IPDT-SIPH

»

Volestrá

PIS/COFINS

Valor Aprox.

INSS (R$)

Código do Serviço

20260227U30646364000104

Município: Salvador

PREFEITURA DO MUNICÍPIO DE SÃO PAULO

SECRETARIA MUNICIPAL DA FAZENDA
27/02/2026 13:42:22
NOTA FISCAL ELETRÔNICA DE SERVIÇOS - NFS-e Código de Verificação
RPS Nº 28140 Série 1, emitido em 27/02/2026 IPDT-SIPH
PRESTADOR DE SERVIÇOS

CPF/CNPJ: 30.646.364/0001-04
Nome/Razão Social: -VALESTRA NEGOCIOS E INVESTIMENTOS LTDA - MATRIZ

Endereço: AVENIDA DAS NAÇÕES UNIDAS 12901 - BROOKLIN PAULISTA - CONJ NORTE BLOCO A SALA 3301 - CE...
UF: SP

Inscrição Municipal: 59920149

Município: São Paulo

TOMADOR DE SERVIÇOS

Nome/Razão Social: MASSA ALIMENTACAO E SERVICOS S/A

CPF/CNPJ: 09.033.381/0001-80
Endereço: R SENADOR THEOTONIO VILELA 110 - PARQUE BELA VISTA - SALAS 203 E 204 - CEP: 40279-435

Inscrição Municipal:

UF: BA E-mail: oriane.costaG)nwgroup.com.br
INTERMEDIÁRIO DE SERVIÇOS

CPF/CNPJ: Nome/Razão Social:

DISCRIMINAÇÃO DOS SERVIÇOS

Servicos Prestados
Vencimento: 06/03/2026
Valor Liquido: R$ 8340.51
AUDITORIA FEDERAL

O pagamento deverá ser realizado exclusivamente pelo BOLETO, que será enviado junto a NF-e.

Tributos: R$ 990,91 - 11,15%

VALOR TOTAL DO SERVIÇO = R$ 8.887,07

IRRF (R$) CSLL (R$) COFINS (R$) PIS/PASEP (R$) IPI(R$)
- 133,31 88,87 266,61 57,77 0,00

01899 - Planejamento, coordenacao, programacao ou organizacao tecnica, financeira ou administrativa.

0,00 8.887,07 5,00% 444,35 0,00
São Paulo - SP . R$ 990,91 (11,15%) [IBPT

(1) Esta NFS-e foi emitida com respaldo na Lei nº 14.097/2005; (2) O ISS desta NFS-e é devido DENTRO do Município de
São Paulo; (3) Esta NFS-e não gera crédito; (4) Esta NFS-e substitui o RPS Nº 28140 Série 1, emitido em 27/02/2026;

OUTRAS INFORMAÇÕES

Page 1 of 2

"""

PAG2_ANEXO = """
»

IMPOSTO E CONTRIBUIÇÃO SOBRE BENS E SERVIÇOS (IBS E CBS)
Identificador: 35503081230646364000104000000002820326025462711812
CPF/CNPJ / NIF do Fornecedor Número da Nota Código de Verificação
DESTINATÁRIO
CPF/CNPJ: NÃO INFORMADO NIF: O
Nome/Razão Social:  ----
Endereço: ee Nº Compl.: ee
Bairro: E-mail: -—
INFORMAÇÕES DE ENDEREÇO NACIONAL
Município: -— CEP: -—
INFORMAÇÕES DE ENDEREÇO NO EXTERIOR
País: -— Cidade: ---
Estado/Província/Região: --— CEP: -—
ADQUIRENTE
CPF/CNPJ: 09.033.381/0001-80 NIF:
Nome/Razão Social: MASSA ALIMENTACAO E SERVICOS S/A
Endereço: R SENADOR THEOTONIO VILELA Nº: 110 Compl.: SALAS 203 E 204
Bairro: PARQUE BELA VISTA E-mail: oriane.costa(Qnwgroup.com.br
INFORMAÇÕES DE ENDEREÇO NACIONAL
Município: Salvador - BA CEP: 40279-435
INFORMAÇÕES DE ENDEREÇO NO EXTERIOR
País: -— Cidade: ---
Estado/Província/Região: -—— CEP: —
SERVIÇO PRESTADO
Localidade de incidência: 3550308 - Sao Paulo Código indicador da operação: 100301
Tipo de operação: - Operação de uso: Não
CLASSIFICAÇÃO TRIBUTÁRIA
Situação tributária: 000 - Tributação integral

Classificação tributária: 000001 - Situações tributadas integralmente pelo IBS e CBS.
OUTRAS CLASSIFICAÇÕES

NBS: 114012900 -
NCM: —

Valor das Deduções | Base de Cálculo do | Alíquota Estadual do | Alíquota Municipal do | Redução de Alíquota Alíquota Efetiva do Valor Diferido do IBS
de IBS e CBS (R$) IBS e CBS (R$) IBS (%) IBS (%) do IBS (%) IBS (%) (R$)

0,10% 0,00% 0,00% 0,00% 0,00

0,00 8.887,07 Alíquota da CBS (%) Redução de Alíquota | Alíquota Efetiva da Valor Diferido da
da CBS (%) CBS (%) CBS (R$)

0,90% 0,00% 0,00% 0,00
VALOR TOTAL COBRADO = R$ 8.887,07
INFORMAÇÕES ADICIONAIS

Page 2 of 2
"""

CHAVE_REAL = "35503081230646364000104000000002820326025462711812"
CNPJ_PRESTADOR = "30646364000104"


def _chave(cnpj=CNPJ_PRESTADOR, nnfse="0000000028203", aamm="2602", cmun="3550308", dv=None):
    """Forja uma chave de 50 digitos no mesmo formato da real (cod = 546271181)."""
    base = f"{cmun}12{cnpj}{nnfse}{aamm}546271181"
    soma = sum(int(c) * (2 + i % 8) for i, c in enumerate(reversed(base)))
    d = 0 if 11 - soma % 11 >= 10 else 11 - soma % 11
    return base + str(d if dv is None else dv)


def _converte(monkeypatch, tmp_path, paginas, nome="scan qualquer.pdf"):
    pdf = tmp_path / nome
    pdf.write_bytes(b"%PDF-1.4")
    texto = "\x0c".join(paginas)
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: texto)
    notas = SPPdfExtractor(str(pdf)).parse_multiple()
    assert len(notas) == 1
    return notas[0]


# ---------------------------------------------------------------------------
# sp_identificador (puro)
# ---------------------------------------------------------------------------

def test_chave_real_do_anexo_valida_e_decodifica():
    assert sp_ident.extrair_identificadores(PAG2_ANEXO) == [CHAVE_REAL]
    assert sp_ident.dv_valido(CHAVE_REAL)
    assert _chave() == CHAVE_REAL  # o forjador reproduz a chave real
    dados = sp_ident.decodificar(CHAVE_REAL, CNPJ_PRESTADOR, "2602")
    assert dados and dados["nnfse"] == "0000000028203" and dados["cnpj"] == CNPJ_PRESTADOR
    assert sp_ident.formatar_numero(dados["nnfse"]) == "00028203"


@pytest.mark.parametrize("chave,cnpj,aamm", [
    (_chave(dv=3), CNPJ_PRESTADOR, "2602"),                                   # DV errado
    (_chave(cmun="3304557"), CNPJ_PRESTADOR, "2602"),                         # outro municipio
    (_chave(cnpj="30646364000105"), "30646364000105", "2602"),                # CNPJ sem checksum
    (_chave(cnpj="09033381000180"), CNPJ_PRESTADOR, "2602"),                  # CNPJ valido, mas nao o do prestador
    (CHAVE_REAL, None, "2602"),                                               # prestador ilegivel
    (CHAVE_REAL, CNPJ_PRESTADOR, "2603"),                                     # AAMM diferente da emissao
    (_chave(nnfse="0000000000000"), CNPJ_PRESTADOR, "2602"),                  # numero zerado
])
def test_decodificar_rejeita_chave_nao_verificavel(chave, cnpj, aamm):
    assert sp_ident.decodificar(chave, cnpj, aamm) is None


def test_decodificar_sem_emissao_legivel_nao_exige_aamm():
    assert sp_ident.decodificar(CHAVE_REAL, CNPJ_PRESTADOR, None) is not None


def test_pagina_de_anexo_so_e_anexo_sem_bloco_prestador():
    assert sp_ident.eh_pagina_anexo_ibs_cbs(PAG2_ANEXO)
    assert not sp_ident.eh_pagina_anexo_ibs_cbs(PAG1_PRE)


def test_valores_rotulados_como_outro_campo_pegam_inscricao_cnpj_e_cep():
    achados = sp_ident.valores_de_outros_campos(PAG1_PRE)
    assert "59920149" in achados                 # Inscricao Municipal do prestador
    assert "30646364000104" in achados           # CNPJ do prestador
    assert "40279435" in achados                 # CEP do tomador
    assert "28203" not in achados


# ---------------------------------------------------------------------------
# _extrair_numero (SP escaneada), via parse_multiple
# ---------------------------------------------------------------------------

def test_numero_vem_da_chave_mesmo_com_cabecalho_lido_como_inscricao_municipal(monkeypatch, tmp_path):
    """Reproduz o bug: o texto PRE traz "Numero da Nota 59920149" (a IM)."""
    nfse = _converte(monkeypatch, tmp_path, [PAG1_PRE, PAG2_ANEXO])
    assert nfse.numero == "00028203"
    assert nfse.prestador.cnpj_cpf == CNPJ_PRESTADOR
    assert nfse.prestador.inscricao_municipal == "59920149"  # a IM continua sendo a IM
    # A divergencia entre a caixa lida e a chave fica registrada.
    assert any("59920149" in a and "00028203" in a for a in nfse.avisos)


@pytest.mark.parametrize("nome", ["NF 28203 MASSA.pdf", "scan sem numero nenhum.pdf"])
def test_numero_certo_independe_do_nome_do_arquivo(monkeypatch, tmp_path, nome):
    """Familia 9: o numero sai do documento, nao do nome do PDF."""
    nfse = _converte(monkeypatch, tmp_path, [PAG1_PRE, PAG2_ANEXO], nome=nome)
    assert nfse.numero == "00028203"


def test_sem_anexo_candidato_igual_a_inscricao_municipal_vira_sentinela_sem_usar_o_nome(monkeypatch, tmp_path):
    """Sem a pagina 2 nao ha chave: 59920149 e a IM do prestador -> sentinela +
    aviso, e o "28203" do nome do arquivo NAO pode ser adotado."""
    nfse = _converte(monkeypatch, tmp_path, [PAG1_PRE], nome="NF 28203 MASSA.pdf")
    assert nfse.numero == "00000000"
    assert "Número da nota não encontrado" in nfse.avisos


@pytest.mark.parametrize("anexo", [
    PAG2_ANEXO.replace(CHAVE_REAL, _chave(cnpj="09033381000180")),   # CNPJ de OUTRA empresa
    PAG2_ANEXO.replace(CHAVE_REAL, _chave(dv=3)),                    # DV invalido
    PAG2_ANEXO.replace(CHAVE_REAL, _chave(aamm="2603")),             # outro mes de emissao
], ids=["cnpj_de_outra_empresa", "dv_invalido", "aamm_de_outro_mes"])
def test_chave_que_nao_valida_e_ignorada_e_a_trava_da_inscricao_continua(monkeypatch, tmp_path, anexo):
    nfse = _converte(monkeypatch, tmp_path, [PAG1_PRE, anexo], nome="NF 28203 MASSA.pdf")
    assert nfse.numero == "00000000"


def test_chave_ausente_ou_invalida_mantem_a_leitura_boa_do_cabecalho(monkeypatch, tmp_path):
    """Comportamento anterior preservado: cabecalho legivel (texto POS, o recorte
    corrigido ja leu 00028203) e sem chave valida -> o numero lido."""
    assert _converte(monkeypatch, tmp_path, [PAG1_POS]).numero == "00028203"
    anexo_ruim = PAG2_ANEXO.replace(CHAVE_REAL, _chave(cnpj="09033381000180"))
    assert _converte(monkeypatch, tmp_path, [PAG1_POS, anexo_ruim]).numero == "00028203"


def test_texto_pos_correcao_completo_tem_numero_data_e_codigo_corretos(monkeypatch, tmp_path):
    nfse = _converte(monkeypatch, tmp_path, [PAG1_POS, PAG2_ANEXO])
    assert nfse.numero == "00028203"
    assert nfse.codigo_verificacao == "IPDT-SIPH"
    assert nfse.avisos == [] or all("diverge" not in a for a in nfse.avisos)


def test_anexo_nao_vaza_para_a_nota_seguinte_sem_anexo(monkeypatch, tmp_path):
    """Pagina seguinte que e OUTRA nota (tem bloco PRESTADOR) nunca fornece a
    chave: a nota 1 (sem anexo, cabecalho = IM) nao pode herdar o numero da 2."""
    nota2 = PAG1_POS.replace("00028203", "00028299").replace(
        "PRESTADOR DE SERVIÇOS\n",
        f"Identificador Nacional: {_chave(nnfse='0000000028299')}\n\nPRESTADOR DE SERVIÇOS\n", 1)
    assert "Identificador Nacional" in nota2
    pdf = tmp_path / "lote.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr",
                        lambda self: "\x0c".join([PAG1_PRE, nota2]))
    notas = SPPdfExtractor(str(pdf)).parse_multiple()
    assert {n.pagina_origem: n.numero for n in notas} == {1: "00000000", 2: "00028299"}


# ---------------------------------------------------------------------------
# _ocr_header_box_sao_paulo (tokens reais do image_to_data, Tesseract mockado)
# ---------------------------------------------------------------------------

# image_to_data de PAGINA INTEIRA (zoom 3x, 1785x2526) da nota real: a caixa
# "Numero da Nota / Data e Hora" nao aparece; so a Inscricao Municipal.
DATA_PAGINA_INTEIRA = {
    "text": ["PAULO", "27/02/2026", "13:42:22", "Inscrição", "Municipal:", "59920149", "IPDT-SIPH"],
    "left": [1163, 1430, 1558, 1126, 1228, 1359, 1484],
    "top": [111, 198, 198, 357, 356, 356, 269],
    "width": [122, 119, 94, 93, 105, 105, 115],
    "height": [27, 20, 19, 24, 23, 19, 19],
}
# image_to_data so da regiao do canto superior direito (x0 = 892): ali o rotulo
# "Número" e reconhecido (coordenadas relativas ao recorte).
DATA_REGIAO = {
    "text": ["Número", "da", "Nota", "Inscrição", "Municipal:", "59920149"],
    "left": [487, 560, 600, 234, 336, 467],
    "top": [95, 95, 95, 357, 356, 356],
    "width": [70, 30, 50, 93, 105, 105],
    "height": [19, 19, 19, 24, 23, 19],
}


def _mock_tesseract(monkeypatch, data_regiao, texto_ocr):
    import pytesseract
    from PIL import Image as PILImage

    def fake_data(img, **k):
        return data_regiao if k.get("config") == "--psm 6" else DATA_PAGINA_INTEIRA

    caixas = []
    orig_crop = PILImage.Image.crop

    def tracking_crop(self, box):
        caixas.append(box)
        return orig_crop(self, box)

    monkeypatch.setattr(pytesseract, "image_to_data", fake_data)
    monkeypatch.setattr(pytesseract, "image_to_string", lambda img, **k: texto_ocr)
    monkeypatch.setattr(PILImage.Image, "crop", tracking_crop)
    return caixas


def test_recorte_acha_rotulo_na_regiao_quando_a_pagina_inteira_perdeu_a_caixa(monkeypatch):
    import pymupdf
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    caixas = _mock_tesseract(monkeypatch, DATA_REGIAO, "00028203")

    resultado = SPPdfExtractor._ocr_header_box_sao_paulo(page, 0)

    assert resultado.startswith("Número da Nota\n00028203\n")
    # Leu a linha logo abaixo do rotulo (y0 = (95 + 19*1.1) * 2), nao a IM (y0 = 356*2*0.9).
    assert any(b[1] == int((95 + 19 * 1.1) * 2) for b in caixas)
    assert not any(b[1] == int(356 * 2 * 0.9) for b in caixas)
    doc.close()


def test_recorte_sem_rotulo_nunca_adota_a_inscricao_municipal(monkeypatch):
    import pymupdf
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    regiao_sem_rotulo = {k: [] for k in DATA_REGIAO}
    caixas = _mock_tesseract(monkeypatch, regiao_sem_rotulo, "")

    resultado = SPPdfExtractor._ocr_header_box_sao_paulo(page, 0)

    assert "59920149" not in resultado
    # O ramo "valor pela assinatura" nao recortou o token da IM (y0 = 356*2*0.9).
    assert not any(b[1] == int(356 * 2 * 0.9) for b in caixas)
    doc.close()


def test_recorte_assinatura_numerica_continua_valendo_sem_rotulo_na_regiao(monkeypatch):
    """Nao-regressao do ramo FLASH 05114339/PLUXEE 08336055: rotulo quebrado, valor
    solto -> localizado pela propria assinatura (ele NAO e rotulado como outro campo)."""
    import pymupdf
    import pytesseract
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    mock_data = {
        "text": ["N�", "daN", "05114339", "PREFEITURA"],
        "left": [1373, 1464, 1390, 941],
        "top": [95, 95, 98, 110],
        "width": [40, 90, 250, 400],
        "height": [19, 19, 53, 30],
    }
    monkeypatch.setattr(pytesseract, "image_to_data", lambda *a, **k: mock_data)
    monkeypatch.setattr(pytesseract, "image_to_string", lambda img, **k: "05114339")

    assert SPPdfExtractor._ocr_header_box_sao_paulo(page, 0) == "Número da Nota\n05114339\n"
    doc.close()
