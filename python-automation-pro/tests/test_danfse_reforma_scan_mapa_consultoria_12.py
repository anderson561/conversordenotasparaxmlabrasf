# -*- coding: utf-8 -*-
r"""DANFSe v2.0 (LAYOUT_NACIONAL_REFORMA) ESCANEADA em ~100 dpi — Lauro de
Freitas/BA, "Notas\092026\1°_QUINZENA\MAPA CONSULTORIA - 12.pdf": nota nº 12,
MAPA CONSULTORIA AMBIENTAL LTDA (08.282.412/0001-73, IM 10001598, Simples
Nacional ME/EPP) -> BONI TRANSPORTES, LOGISTICA E COMERCIO LTDA.
(04.555.283/0003-50), código 17.01.01, R$ 1.412,00, competência 01/09/2026.

Antes: a página caía na DANFSe v1.0 e o XML saía com o CNPJ da BONI como
PRESTADOR, razão social "MAPA ... LTDA Laura de Freitas / BA 29.19207 /
42.700-230", município Salvador, tomador "Enderaço Email", `<Intermediario>`
falso ("DA OPER O IDENTIFICADO NA NFS-o"), item 03115, discriminação genérica
e CodigoVerificacao com o município trocado ("2979207...").

Causas: (1) `_eh_danfse_v2` não reconhecia a página (o OCR come o "VALOR" de
"VALOR DA OPERAÇÃO / SERVIÇO" e estropia todos os rótulos IBS/CBS); (2) os
títulos de seção saem pela metade ("PRESTADOR /", "SERVIÇO ADO", "TRIBUT,") —
`_danfse_v2_titulos_parciais`; (3) a caixa do título "SERVIÇO PRESTADO" sobe
para dentro da tarja do intermediário; (4) "1.0101-" relido no recorte justo
(`_danfse_v2_codigo_quebrado`); (5) "Municipão / Sigla UF", "IBGE (CEP",
"Desenção do Serviço", "Naciona|Municipsl"; (6) chave do rodapé "121 <chave>"
(a "/" lida "1").

`OCR_ORIGINAL_12` é a leitura de página inteira; `OCR_CELULAS_12` é o retorno
REAL de `_ocr_page` depois do fix (texto reconstruído pela grade)."""
import os

from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_NACIONAL_REFORMA, _eh_danfse_v2
from src.transformers.abrasf_transformer import Abrasf201Transformer

OCR_ORIGINAL_12 = "NFSe: é Município: Lauro de Freitas - BA\nCenvico; ese Me: e a a Eos\n\nCHAVE DE ACESSO DA NFS-a\n297920722082824 12000173000000000001226091731423270\n\nNUMERO DA NFS-e COMPETÊNCIA DA NFS-e DATA E HORA DA EMISSÃO DA NFS-s\n12 010982026 DW0SZ0Z6 15:54:49\n\nNUMERO DA DPS SÉRIE DA DPS DATA E HORA DA EMISSÃO DA DPS :\n\n12 70000 DW0W2026 16:54:49 A autentickinde desta NFS-e pode ser verificada\npela initura deste código OR ou pola consulta da\n\nEMITENTE DA NFS.e SITUAÇÃO DA NFS-s FINALIDADE Chave de acesso no portal nacional da NES-a\n\nPrestador : NFS-s Gerada .\n\nPRESTADOR / s CNPJ/CPF INF Indicador Municipal (inscrição) Teinfona\nD8.282.412/0001-73 10001598 (71) 9340-4088\nHome | Nome Empresarial Municipio | Sígia UF Código IBGE ÍCEP\nMAPA CONSULTORIA AMBIENTAL LTDA Laura de Freitas / BA 29.19207 / 42.700-230\nEndereço E-mail\nRUA CHILE, 241, LOTES 218, 219, 221 E 222, RECREIO IPITANGA MAPAGIMAPACONSULTORIA COM.BR\nSimples Nacional na Data do Competência Rogime de Apuração Tributária polo SN\nOptante - Microempresa ou Empresa da... Regime de apuração dos tributos federais e municipal pelo Simples Nacional\nTOMADOR / ADQUIRENTE o CNPJ/CPF (NF Indicador Municipal (inscrição) Teletona\n04.555.283/0003-50 - -\nNome / Nome Empresarial Municipão / Sigia UF Código IBGE [CEP\nBONI TRANSPORTES, LOGISTICA E COMERCIO LTDA, Lauro de Freitas / BA 29.19207 | 42.738-205\nEnderaço Email\nMARIA QUITERIA, 263, GALPÃO LOT DESMEMBRAMENTO DIAMANTE, ITINGA .\nDESTINATÁRIO DA OPERA IDENTIFICADO NA NFS -e\nmma INTERMEDIÁRIO DA OPER O IDENTIFICADO NA NFS-o\n\nSERVIÇO ADO Código de Tributação Naciona|Municipsl Código da NSS Locai da Prestação | Sigla UF / Pais\n1.0101- 1.1410.90.00 Lauro de Freitas / BA! -\n\nAssessora ou consultoria de qualquer natureza, não contida am outros itens desta lista,\n\nDesenção do Serviço\nCONTRATO No Te2024 PP 1722024 RV 00 Servico cadastro IBAMA, acompanhamento tecnico das condicionantes da LU No. 0112024, e regularização ETE. BANCO SANTANDER\n033 agencia 4674 conta corrente 13005186-9 chaves PIX (CNPJ) 08.282.4120001-73 Mapa Consultoria Ambiental Ltda\n\nTRIBUTAÇÃO Mi MUNICIPAL A ci Tipo de Tributação do ISSQN Municipio ' Sigis UF / Pais de Incidência do ISSQN\n\nOperação Tributável Lauro de Freites / BA / -\n\nBC ISS0N Aliquota Aplicada Retenção do ISSQN ISSQN Apurado\ng - Não Retido e\n\nTRIBUT, FEDERAL (EXCETO CBS) IRRF Contribuição Previdenciária - Retida Contribuições Sociais - Retidas\n\nPIS -Dabho Apuração Própria COFINS - Débito Apuração Própria Descrição Contrib. Sociais - Retidas\n\nTRIBUT; “e CST/icClaseTAb Indicador de Operação / Código IBGE Incidência / Municipio Incidência | Sigla UF\na afof=to\n\nExclusões e Reduções da Base de Cálculo ; Esse de Cálculo Após Exclusões = Reduções Red. Aliguota (BS | Red. Aliquots CES Alíquota - |BS UF /IBS Mun\n\nR$ 0,00 - =[-d- -I-\n\ndlig Efetiva Municipal - IES Valor Apurado Municipal - 155 Alig. Efetiva Estadual - 185 Valor Apurado Estadual - IES\n\nVator Total Apurado - BS Adiquota » CBS Aliquota Efetiva - CES Valor Total Apurado -CES\n\nVALOR TOTAL DA NFS-e x To A DA OPERAÇÃO | SERVIÇO Desconto incondicionado Desconto Condicionado\n1.412,00 - z\n\nTotal tos Retenções (ISSQN IFaderaia) — VALORLÍQUIDO DANFS-€ Total do EBSICES VALOR LÍQUIDO DA NFS-+ + IBSICBS\n- R$ 1.412,00 R$ 0,00 R$0,00\n\nINFORMAÇÕES COMPLEMENTARES\n\nTotais aproximados dos Tributos cfe, Lei nº 12.7412012: Federais: -; Estaduais; =; Municipais: =;\n\no IDENTIFICAÇÃO E ASSINATURA Nº NFS-a ) CHAVE NFS &\n121 29192072208282412000173000000000001226091731423270\n\n"

OCR_CELULAS_12 = "NFSe:\nCenvico; ese Me:\nCHAVE DE ACESSO DA NFS-a\n297920722082824 12000173000000000001226091731423270\nNUMERO DA NFS-e\n12\nNUMERO DA DPS\n12\nEMITENTE DA NFS.e\n:\nPrestador\n\nCOMPETÊNCIA DA NFS-e\n010982026\nSÉRIE DA DPS\n70000\nSITUAÇÃO DA NFS-s\nNFS-s Gerada\n\né\ne a a\nDATA E HORA DA EMISSÃO DA NFS-s\nDW0SZ0Z6 15:54:49\nDATA E HORA DA EMISSÃO DA DPS\nDW0W2026 16:54:49\nFINALIDADE\n.\n\nMunicípio: Lauro de Freitas - BA\nEos\n:\nA autentickinde desta NFS-e pode ser verificada\npela initura deste código OR ou pola consulta da\nChave de acesso no portal nacional da NES-a\n\ns\nPRESTADOR / FORNECEDOR\nHome | Nome Empresarial\nMAPA CONSULTORIA AMBIENTAL LTDA\nEndereço\nRUA CHILE, 241, LOTES 218, 219, 221 E 222, RECREIO IPITANGA\nSimples Nacional na Data do Competência\nOptante - Microempresa ou Empresa da...\n\nCNPJ/CPF INF\nD8.282.412/0001-73\nRogime de Apuração Tributária polo SN\nRegime de apuração dos tributos federais e municipal pelo Simples Nacional\n\nIndicador Municipal (inscrição)\n10001598\nMunicipio | Sígia UF\nLaura de Freitas / BA\nE-mail\nMAPAGIMAPACONSULTORIA COM.BR\n\nTeiofona\n(71) 9340-4088\nCódigo IBGE /CEP\n29.19207 / 42.700-230\n\nTOMADOR / ADQUIRENTE\nNome / Nome Empresarial\nBONI TRANSPORTES, LOGISTICA E COMERCIO LTDA,\nEnderaço\nMARIA QUITERIA, 263, GALPÃO LOT DESMEMBRAMENTO DIAMANTE, ITINGA\n\no CNPJ/CPF (NF\n04.555.283/0003-50\n\nMunicipão / Sigla UF\nLauro de Freitas / BA\nEmail\n\nTelefona\nIBGE (CEP\n29.19207 | 42.738-205\n\nDESTINATÁRIO DA OPERACA;\n\nÃO NÃO IDENTIFICADO NA NFS-e\n\nINTERMEDIÁRIO DA OPERAÇCA\n\n“ÃO NÃO IDENTIFICADO NA NFS.\n\nmma\nSERVIÇO PRESTADO\nAssessora ou consultoria de qualquer natureza, não contida am outros itens desta lista,\nDesenção do Serviço\nCONTRATO No Te2024 PP 1722024 RV 00 Servico cadastro IBAMA, acompanhamento tecnico das condicionantes da LU No. 0112024, e regularização ETE. BANCO SANTANDER\n033 agencia 4674 conta corrente 13005186-9 chaves PIX (CNPJ) 08.282.4120001-73 Mapa Consultoria Ambiental Ltda\n\nCódigo de Tributação Naciona|Municipsl Código da NSS\n17.01.01/-\n\n1.1410.90.00\n\nLocai da Prestação | Sigla UF / Pais\nLauro de Freitas / BA! -\n\nTRIBUTAÇÃO MUNICIPAL (ISSQN)\nBC ISS0N\n\nTipo de Tributação do ISSQN\nOperação Tributável\nAliquota Apticada\n\nMunicipio ' Sigis UF / Pais de Incidência do ISSQN\nLauro de Freites / BA / -\nRetenção do ISSQN\nNão Retido\n\nISSQN Apurado\ne\n\nTRIBUTAÇÃO FEDERAL (EXCETO CBS)\nFEDERAL (EXCETO CBS) IRRF\nPIS -Dabho Apuração Própria\n\nCOFINS - Débito Apuração Própria\n\nContribuição Previdenciária - Retida\nDescrição Contrib. Sociais - Retidas\n\nContribuições Sociais - Retidas\n\nTRIBUTAÇÃO IBS / CBS\n“e\nExclusões e Reduções da Base de Cálculo ; Esse de Cálculo Após Exclusões = Reduções Red. Aliguota (BS | Red. Aliquots CES\nR$ 0,00\ndlig Efetiva Municipal - IES\nVator Total Apurado - BS\n\nCST/icClaseTAb\na\n-\nValor Apurado Municipal - 155\nAdiquota » CBS\n\nIndicador de Operação / Código IBGE Incidência / Municipio Incidência | Sigla UF\nafof=to\n=[-d-\nAlig. Efetiva Estadual - 185\nAliquota Efetiva - CES\n\nAlíquota - |BS UF /IBS Mun\n-I-\nValor Apurado Estadual - IES\nValor Total Apurado -CES\n\nVALOR TOTAL DA NFS-e\nTotal tas Rotenções (ISSQN | Faderais)\n\n— VALOR DA OPERAÇÃO | SERVIÇO\nR$ 1.412,00\nVALOR LÍQUIDO DA NFS-e\nR$ 1.412,00\n\nDesconto incondicionado\nTotal do BSICES\nR$0,00\n\nDesconto Condicionado\nVALOR LÍQUIDO DA NFS-e + IBSICES\nR$0,00\n\nINFORMAÇÕES COMPLEMENTARES\nTotais aproximados dos Tributos cfe, Lei nº 12.7412012: Federais: -; Estaduais; =; Municipais: =;\no\n\nIDENTIFICAÇÃO E ASSINATURA\n\nNº NFS-a ) CHAVE NFS &\n121 29192072208282412000173000000000001226091731423270"


def _parse(monkeypatch, texto, nome="dummy_v2_mapa_12.pdf"):
    caminho = f"tests/{nome}"
    with open(caminho, "wb") as f:
        f.write(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: texto)
    try:
        notas = SPPdfExtractor(caminho).parse_multiple()
    finally:
        if os.path.exists(caminho):
            os.remove(caminho)
    assert len(notas) == 1
    return notas[0]


def _xml(nota):
    xml = Abrasf201Transformer().transform(nota)
    return xml.decode("utf-8") if isinstance(xml, bytes) else str(xml)


# ---------------------------------------------------------------- detecção

def test_leitura_original_e_v2():
    """Sem "DANFSe v2", sem "VALOR DA OPERAÇÃO" inteiro e sem nenhum rótulo
    IBS/CBS legível: antes caía na v1.0."""
    t = OCR_ORIGINAL_12
    assert "DANFSe" not in t and "VALOR DA OPERA" not in t
    assert _eh_danfse_v2(t)
    ex = SPPdfExtractor("x.pdf")
    assert ex._detect_layout_page(t) == LAYOUT_NACIONAL_REFORMA


def test_marca_v2_rotulos_internos_ibs_cbs():
    assert _eh_danfse_v2("A DA OPERAÇÃO | SERVIÇO\nExclusões e Reduções da Base de Cálculo")
    assert _eh_danfse_v2("DA OPERAÇÃO / SERVIÇO\nIndicador de Operação / Código IBGE Incidência")
    # Santos: "Indicador de Operação" sem "/ Código IBGE" e sem o rótulo de valor.
    assert not _eh_danfse_v2("Indicador de Operação\nSituação Tributária\nValor do Serviço")
    assert not _eh_danfse_v2("DANFSe v1.0\nExclusões e Reduções da Base de Cálculo")


def test_celulas_trazem_titulos_canonicos_em_ordem():
    t = OCR_CELULAS_12
    assert t.count("PRESTADOR / FORNECEDOR") == 1
    assert t.index("PRESTADOR / FORNECEDOR") < t.index("TOMADOR / ADQUIRENTE") \
        < t.index("INTERMEDIÁRIO DA OPER") < t.index("SERVIÇO PRESTADO") \
        < t.index("TRIBUTAÇÃO MUNICIPAL") < t.index("TRIBUTAÇÃO FEDERAL") \
        < t.index("TRIBUTAÇÃO IBS / CBS") < t.index("VALOR TOTAL DA NFS-e")
    # "Prestador" (valor de "EMITENTE DA NFS-e") nunca vira título.
    assert "\nPrestador\n" in t


def test_titulos_parciais_estrutura():
    segs = [dict(x0=10, t="Prestador", yc=1), dict(x0=10, t="PRESTADOR /", yc=2),
            dict(x0=10, t="SERVIÇO ADO", yc=3), dict(x0=10, t="SERVIÇO DE MANUTENÇÃO", yc=4),
            dict(x0=10, t="TRIBUTAÇÃO MUNICIPAL Mi", yc=5), dict(x0=10, t="TRIBUT,", yc=6),
            dict(x0=10, t="TRIBUT;", yc=7), dict(x0=500, t="TOMADOR /", yc=8)]
    out = [s["t"] for s in SPPdfExtractor._danfse_v2_titulos_parciais(segs, lambda x: 0 if x < 100 else 1)]
    assert out == ["Prestador", "PRESTADOR / FORNECEDOR", "SERVIÇO PRESTADO", "SERVIÇO DE MANUTENÇÃO",
                   "TRIBUTAÇÃO MUNICIPAL Mi", "TRIBUTAÇÃO FEDERAL (EXCETO CBS)", "TRIBUTAÇÃO IBS / CBS",
                   "TOMADOR /"]
    # Sem "PRESTADOR" na 1ª coluna (DANFSe com tarjas reticuladas): nada muda.
    sem = [dict(x0=10, t="SERVIÇO ADO", yc=1)]
    assert SPPdfExtractor._danfse_v2_titulos_parciais(sem, lambda x: 0) is sem


def test_codigo_quebrado_forma():
    q = SPPdfExtractor._danfse_v2_codigo_quebrado
    assert q("1.0101-") and q("9.01.01/-")
    assert not q("17.01.01/-") and not q("70000") and not q("10001598")
    assert not q("29.19207 / 42.700-230") and not q("R$ 1.412,00")


def test_reler_codigo_sem_ponto(monkeypatch):
    import pytesseract
    from PIL import Image

    img = Image.new("RGB", (400, 100), "white")
    seg = dict(t="1.0101-", x0=50, x1=150, y0=40, y1=58, alt=17)
    monkeypatch.setattr(pytesseract, "image_to_string", lambda *a, **k: "17.0101/-")
    assert SPPdfExtractor._danfse_v2_reler_valor_truncado(img, seg, 0.0) == "17.01.01/-"
    # Sem nenhum ponto (pode ser outro número) ou sem a "/": fica o original.
    monkeypatch.setattr(pytesseract, "image_to_string", lambda *a, **k: "170101/-\n17.0101-")
    assert SPPdfExtractor._danfse_v2_reler_valor_truncado(img, seg, 0.0) == "1.0101-"


def test_chave_rodape_com_barra_lida_1():
    ex = SPPdfExtractor("x.pdf")
    chave = "29192072208282412000173000000000001226091731423270"
    ex.raw_text = f"Nº NFS-a ) CHAVE NFS &\n121 {chave}"
    assert ex._danfse_chave_rodape_confirmada() == chave
    # Número que não é o da chave (nem com o "1" a mais) não vale.
    ex.raw_text = f"Nº NFS-a ) CHAVE NFS &\n131 {chave}"
    assert ex._danfse_chave_rodape_confirmada() is None
    # Com "/" legível o número tem de ser exato.
    ex.raw_text = f"121 / {chave}"
    assert ex._danfse_chave_rodape_confirmada() is None


# ------------------------------------------------------------ nota nº 12

def test_12_identificacao_e_chave_do_rodape(monkeypatch):
    nota = _parse(monkeypatch, OCR_CELULAS_12)
    assert nota.numero == "12"
    # Cabeçalho lido "297920722082824 1200...", rodapé "121 2919207...".
    assert nota.codigo_verificacao == "29192072208282412000173000000000001226091731423270"
    # Data/hora de emissão ilegível no scan: dia 1 do mês da chave + aviso.
    assert nota.data_emissao.strftime("%Y-%m-%d %H:%M:%S") == "2026-09-01 00:00:00"
    assert any("Data/hora de emissão" in a for a in nota.avisos)
    assert nota.competencia.strftime("%Y-%m-%d") == "2026-09-01"


def test_12_prestador_mapa(monkeypatch):
    p = _parse(monkeypatch, OCR_CELULAS_12).prestador
    # Antes: 04555283000350 (CNPJ do TOMADOR).
    assert p.cnpj_cpf == "08282412000173"
    assert "29192072208282412000173" in OCR_CELULAS_12
    assert p.razao_social == "MAPA CONSULTORIA AMBIENTAL LTDA"
    assert p.inscricao_municipal == "10001598"
    e = p.endereco
    assert (e.logradouro, e.numero, e.bairro) == ("RUA CHILE", "241", "RECREIO IPITANGA")
    assert (e.codigo_municipio, e.uf, e.cep) == ("2919207", "BA", "42700230")


def test_12_tomador_boni(monkeypatch):
    t = _parse(monkeypatch, OCR_CELULAS_12).tomador
    assert t.cnpj_cpf == "04555283000350"
    assert t.razao_social.startswith("BONI TRANSPORTES, LOGISTICA E COMERCIO LTDA")
    e = t.endereco
    assert (e.logradouro, e.numero, e.bairro) == ("MARIA QUITERIA", "263", "ITINGA")
    # "Municipão / Sigla UF" e "IBGE (CEP" no OCR.
    assert (e.codigo_municipio, e.uf, e.cep) == ("2919207", "BA", "42738205")


def test_12_servico_valores_e_xml(monkeypatch):
    nota = _parse(monkeypatch, OCR_CELULAS_12)
    assert nota.intermediario is None
    assert nota.servico_codigo == "1701"
    assert nota.discriminacao.startswith("CONTRATO No ")
    assert "Servico cadastro IBAMA" in nota.discriminacao
    assert nota.discriminacao.endswith("Mapa Consultoria Ambiental Ltda")
    assert nota.valores.valor_servicos == 1412.0
    assert nota.valores.valor_liquido_nfse == 1412.0
    assert not nota.valores.iss_retido
    xml = _xml(nota)
    assert "<Intermediario>" not in xml
    assert "2927408" not in xml  # Salvador
    assert "<ValorIss>0.00</ValorIss>" in xml  # Simples Nacional, ISSQN "-"
    assert "<OptanteSimplesNacional>1</OptanteSimplesNacional>" in xml
    assert "<RegimeEspecialTributacao>6</RegimeEspecialTributacao>" in xml
    assert "<ItemListaServico>1701</ItemListaServico>" in xml
