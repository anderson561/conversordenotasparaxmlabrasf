# -*- coding: utf-8 -*-
r"""DANFSe v2.0 (LAYOUT_NACIONAL_REFORMA) ESCANEADA — nota real nº
2600000000058, GERENCIAR TECNOLOGIA EM TRANSPORTES LTDA (CNPJ
25.302.805/0001-10, Simões Filho/BA) -> STAUMMAQ SERVICOS TECNICOS AUTOMACAO
MOTORES E MAQUINAS LTDA (CNPJ 02.370.080/0001-00, Simões Filho/BA), item
16.01.01 (transporte coletivo municipal), R$ 1.852,80, ISS retido R$ 55,58,
INSS retido R$ 61,14, líquido R$ 1.736,08. Página 8 do lote escaneado
"Scan2026-10-16_110738.pdf".

Defeitos do XML gerado antes do fix (conferidos contra a imagem renderizada):
1. Prestador e tomador "Não Identificado" com CNPJ zerado: a segmentação
   automática do Tesseract misturava as colunas da grade (linha de rótulos
   "PRESTADOR / FORNECEDOR CNPJ/CPF/NIF Indicador Municipal Telefone" e, na
   linha seguinte, os três valores), jogava o endereço do prestador e o
   CNPJ/razão do tomador para ANTES do bloco do prestador, e este gerador
   intitula o bloco "TOMADOR DO SERVIÇO" (não "TOMADOR / ADQUIRENTE").
2. Tomador com município São Paulo/SP (3550308) e CEP zerado.
3. Tomador com InscricaoMunicipal 104011119 — é o Código da NBS; o
   Indicador Municipal do tomador vem em branco ("-").
4. INSS (rótulo "Contribuição Previdenciária - Retido", masculino) em
   OutrasRetencoes em vez de ValorInss.
5. ValorLiquidoNfse 116,72 (o "Total das Retenções") em vez de 1.736,08.
6. Discriminação genérica.

`OCR_CELULAS` é o retorno REAL de `_ocr_page` (pág. 8) depois do fix — o
texto reconstruído pela grade (`_ocr_celulas_danfse_v2`), preservado via
`repr()`, com os erros de OCR que sobraram ("CNPJ/CPFTNIF", "TENTE DA NFS-E",
"viviane(Dstaummaa.com.br", a rubrica à caneta "fK= cseb tolos..." — que é
anotação manual, não dado da nota)."""
import os

from PIL import Image

from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_NACIONAL_REFORMA
from src.transformers.abrasf_transformer import Abrasf201Transformer

OCR_CELULAS = 'a\nNota Fiscal de\nServiço Eletrônica\nCHAVE DE ACESSO DA NFS-E\n29307091225302805000110260000000005826100004351532\nNÚMERO DA NFS-E\n2600000000058\nNÚMERO DA DPS\nra\nTENTE DA NFS-E\nPrestador\n\nCOMPETÊNCIA DA NFS-E\n06/10/2026\nSÉRIE DA DPS\n70000\nSITUAÇÃO DA NFS-E\nNFS-e Gerada\n\nDANFSe v2.0\nDocumento Auxiliar da NFS-e\n\nBATA E HORA DA EMISSÃO DA NFS-\n06/10/2026 13:03:43\nDATA E HORA DA EMISSÃO DA DPS\n06/10/2026 13:03:43\nFINA\nLIDADE\nNFS-e regular\n\nMunicípio: Simões Filho - |\nBA\nAmbiente Gerador: 1\nTre de Ambiente:\nj\no\nA autenticidade desta NFS-e pode ser\nSenna pois elura cesto cód\nligo QR ou pela\npsi E pa de pd\n\nPRESTADOR / FORNECEDOR\nNome / Nome Empresarial\nGERENCIAR TECNOLOGIA EM TRANSPORTES LTDA\nEndereço\nRua D, 00079, QUADRA:04;LOTE:15;:LOT. SOL NASCENTE, Centro\nSimples Nacional na Data de Competência\nNão Optante\n\nCNPJ/CPFTNIF\n25.302.805/0001-10\nRegime de Apuração Tributária pelo SN\nE\n\nIndicador Municipal (Inscrição)\n16735\nMunicípio / Sigla UF\nSimões Filho / BA\nE-mail\nangelo. pintoDplanus.cnt.br\n\nnacional da NFS-e.\nTelefone\n(71) 9904-8839\nCódigo IBGE / CEP\n2930709 / 43700-000\n\nTOMADOR DO SERVIÇO\nNome / Nome Empresarial\nSTAUMMAQ SERVICOS TECNICOS AUTOMACAO MOTORES E MAQUINAS LTDA\nEndereço\nUrbana, 01, CIA SUL\n\nCNPJ/CPFTNIF\n02.370.080/0001-00\n\nIndicador Municipal (inscrição)\nMunicípio / Sigla UF\nSimões Filho / BA\nE-mail\nviviane(Dstaummaa.com.br\n\nTelefone\n(71) 2203-6300\nCódigo IBGE / CEP\n2930709 / 43700-000\n\nDE:\nSTINATÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e\n\nÃ\nÃO NÃ\n\nINTERMEDIÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e\n\nSERVIÇO PRESTADO\nServiços de transporte coletivo municipal rodoviário, metroviário, ferroviário e aquaviário de passageiros.\nDescrição do Serviço\nViagens extras realizadas no período de 01 a 31 Setembro VENCIMENTO 15/10/2026 Segue dados bancários: Titular: Gerenciar Tecnologia em Transportes Banco 336 - C6 S.A\nChave Pix: 25.302.805/0001-10 Agência: 0001 Conta-corrente: 9405534-3 ORDEM DE COMPRA.: pedido: 8715\n\nCódigo de Tributação Nacional / Municipal\n16.01.01/-\n\nCódigo da NBS\n104011119\n\nLocal da Prestação / Sigla UF / Pais\nSimões Filho / BA / BR\n\nTRIBUTAÇÃO MUNICIPAL (ISSQN)\nRegime Especial de Tributação do ISSQN\nNenhum\nBenefício Municipal\nBC ISSQN\nR$ 1.852,80\n\nTipo de Tributação do ISSQN\nOperação tributável\nTipo de Imunidade do ISSQN\n-\nCálculo do BM\nR$ 0,00\nAlíquota Aplicada\n3,00%\n\nMunicípio / Sigla UF / País de Incidência do ISSQN\nSimões Filho / BA / BR\nSuspensão da Exigibilidade do ISSQN\nNão\nTotal Deduções/Reduções\nR$ 0,00\nRetenção do ISSQN\nRetido pelo Tomador\n\nIN\nNúmero Processo Suspensão\nDesconto Incondicionado\nISSQN Apurado\nR$ 55,58\n\nTRIBUTAÇÃO FEDERAL (EXCETO\ncBSs)\nPIS - Débito Apuração Própria\n\nIRRF\nCOFINS - Débito Apuração Própria\n\nContribuição Previdenciária - Retido\nR$61,14\nDescrição Contrib. Sociais - Retidas\n\n- Retidas\nContribuições Sos\n\nTRIBUTAÇÃO IBS / CBS\nExclusões e Reduções da Base de Cálculo\nR$ 55,58\nAlíq. Efetiva Municipal - IBS\n0,00%\nValor Total Apurado - IBS\nR$ 0,00\n\nCST/ cClassTrib\n200 / 200021\nBase de Cálculo Após Exclusões e\nReduções\nR$ 1.797,22\nValor Apurado Municipal - IBS\nR$ 0,00\nAlíquota - CBS\n0,90%\n\nIndicador de Operação / Código IBGE Incidência / Município Incidência / Sigla UF\n060101 / 2930709 / Simões Filho / BA\nRed. Alíquota IBS / Red. Alíquota CBS\n= | 100,00% / 100,00%\nAlíg. Efetiva Estadual - IBS\n0,00%\nAlíquota Efetiva - CBS\n0,00%\n\nAlíquota - IBS UF /IBS Mun\n0,10% / 0,00%\nValor Apurado Estadual - IBS\nR$ 0,00\nValor Total Apurado - CBS\nR$ 0,00\nDesconto Condicionado\n\nVALOR TOTAL DA NFS-E\nTotal das Retenções (ISSQN / Federais)\nR$ 116,72\n\nVALOR DA OPERAÇÃO | SERVIÇO\nR$ 1.852,80\nVALOR LÍQUIDO DA NFS-e\nR$ 1.736,08\n\nDesconto ncondicvnavo\nTotal do IBS/CBS\nR$ 0,00\n\nO a Cien\nVALOR LÍQUIDO DA NFS-e + IBS/CBS\nR$ 1.736,08\n\nINFORMAÇÕES COMPLEMENTARES\nInf. Cont.: Retenção previdenciária Base de cálculo: R$555,84 Alíquota: 11% Valor: R$ 61,14 | Totais Aproximados dos Tributos cfe. Lei nº 12.741/2012: Federais: -; Estaduais: -;\nMunicipais: -;\nfK= cseb tolos, Ja WD Carré\n\nDATA CIENTIFICAÇÃO\n\nIDENTIFICAÇÃO\n\nE ASSINATURA\n\nNº NFS-E / CHAVE NFS-E\n2600000000058 / 29307091225302805000110260000000005826100004351532'


def _parse(monkeypatch, texto=None, nome="dummy_danfse_v2_scan_gerenciar.pdf"):
    """Caminho real desta nota: pdfminer não acha texto (PDF escaneado) e o
    extrator cai no OCR."""
    texto = OCR_CELULAS if texto is None else texto
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


def _xml(monkeypatch):
    return Abrasf201Transformer().transform(_parse(monkeypatch))


def test_layout_reforma():
    ex = SPPdfExtractor("x.pdf")
    ex.raw_text = OCR_CELULAS
    assert ex._detect_layout() == LAYOUT_NACIONAL_REFORMA


def test_identificacao(monkeypatch):
    nota = _parse(monkeypatch)
    assert nota.numero == "2600000000058"
    assert nota.codigo_verificacao == "29307091225302805000110260000000005826100004351532"
    assert nota.data_emissao.strftime("%Y-%m-%d %H:%M:%S") == "2026-10-06 13:03:43"
    assert nota.competencia.strftime("%Y-%m-%d") == "2026-10-06"


def test_prestador(monkeypatch):
    p = _parse(monkeypatch).prestador
    assert p.cnpj_cpf == "25302805000110"
    assert p.razao_social == "GERENCIAR TECNOLOGIA EM TRANSPORTES LTDA"
    assert p.inscricao_municipal == "16735"
    assert p.endereco.logradouro == "Rua D"
    assert p.endereco.numero == "00079"
    assert p.endereco.bairro == "Centro"
    assert p.endereco.codigo_municipio == "2930709"
    assert p.endereco.uf == "BA"
    assert p.endereco.cep == "43700000"
    assert p.telefone and "9904" in p.telefone


def test_tomador_titulo_tomador_do_servico(monkeypatch):
    tm = _parse(monkeypatch).tomador
    assert tm.cnpj_cpf == "02370080000100"
    assert tm.razao_social == "STAUMMAQ SERVICOS TECNICOS AUTOMACAO MOTORES E MAQUINAS LTDA"
    assert tm.endereco.logradouro == "Urbana"
    assert tm.endereco.numero == "01"
    assert tm.endereco.bairro == "CIA SUL"
    assert tm.endereco.codigo_municipio == "2930709"
    assert tm.endereco.uf == "BA"
    assert tm.endereco.cep == "43700000"
    assert tm.telefone and "2203" in tm.telefone


def test_tomador_sem_inscricao_municipal_nbs_nao_vira_im(monkeypatch):
    tm = _parse(monkeypatch).tomador
    assert not tm.inscricao_municipal
    assert "104011119" not in _xml(monkeypatch).split("<Tomador>")[1]


def test_valores_inss_retido_e_liquido(monkeypatch):
    v = _parse(monkeypatch).valores
    assert v.valor_servicos == 1852.80
    assert v.base_calculo == 1852.80
    assert abs(v.aliquota - 0.03) < 1e-9
    assert v.valor_iss == 55.58
    assert v.iss_retido is True
    assert v.valor_inss == 61.14
    assert v.outras_retencoes == 0.0
    assert v.valor_liquido_nfse == 1736.08
    xml = _xml(monkeypatch)
    assert "<ValorInss>61.14</ValorInss>" in xml
    assert "<OutrasRetencoes>0.00</OutrasRetencoes>" in xml
    assert "<ValorLiquidoNfse>1736.08</ValorLiquidoNfse>" in xml
    assert "<IssRetido>1</IssRetido>" in xml


def test_item_e_discriminacao(monkeypatch):
    nota = _parse(monkeypatch)
    assert nota.servico_codigo == "1601"
    d = nota.discriminacao
    assert d.startswith("Viagens extras realizadas no período de 01 a 31 Setembro VENCIMENTO 15/10/2026")
    assert d.endswith("ORDEM DE COMPRA.: pedido: 8715")
    # Anotação à caneta no rodapé do scan não é dado da nota.
    assert "cseb" not in d and "INSS" not in d


def test_municipios(monkeypatch):
    xml = _xml(monkeypatch)
    assert "3550308" not in xml
    assert "<MunicipioIncidencia>2930709</MunicipioIncidencia>" in xml


# ----------------------------------------------------------------------
# Reconstrução pela grade (`_ocr_celulas_danfse_v2`) — Tesseract simulado
# com as caixas de palavra de uma DANFSe v2.0 torta, na ordem "errada"
# (linha a linha, misturando colunas), como a segmentação automática faz.
# ----------------------------------------------------------------------

def _palavras_grade():
    """(x, y, texto) de cada palavra; a página está inclinada 0,01 (y cresce
    10 px a cada 1000 px de x)."""
    W = 2000
    cols = [40, 520, 1000, 1480]
    linhas = [
        (100, [(0, "CHAVE DE ACESSO DA NFS-E"), (2, "DANFSe v2.0")]),
        (140, [(0, "29307091225302805000110260000000005826100004351532")]),
        (300, [(0, "PRESTADOR / FORNECEDOR"), (1, "CNPJ / CPF / NIF"), (2, "Telefone")]),
        (340, [(1, "25.302.805/0001-10"), (2, "(71) 9904-8839")]),
        (380, [(0, "Nome / Nome Empresarial"), (2, "Município / Sigla UF")]),
        (420, [(0, "GERENCIAR TRANSPORTES"), (2, "Simões Filho / BA")]),
        (500, [(0, "TOMADOR DO SERVIÇO"), (1, "CNPJ / CPF / NIF"), (2, "Telefone")]),
        (540, [(1, "02.370.080/0001-00"), (2, "(71) 2203-6300")]),
        (580, [(0, "Nome / Nome Empresarial"), (2, "Município / Sigla UF")]),
        (620, [(0, "STAUMMAQ LTDA"), (2, "Simões Filho / BA")]),
        (700, [(0, "SERVIÇO PRESTADO"), (1, "Código da NBS")]),
        (740, [(1, "104011119")]),
    ]
    palavras = []
    for y, celulas in linhas:
        for c, texto in celulas:
            x = cols[c]
            for p in texto.split():
                palavras.append((x, int(y + 0.01 * x), p, y))
                x += 18 * len(p) + 12
    return W, palavras


def _mock_tesseract(monkeypatch, palavras):
    import pytesseract
    d = {k: [] for k in ("text", "left", "top", "width", "height",
                         "block_num", "par_num", "line_num")}
    # Uma "linha" do Tesseract por Y de origem, atravessando as colunas.
    for x, y, p, linha in palavras:
        d["text"].append(p)
        d["left"].append(x)
        d["top"].append(y)
        d["width"].append(18 * len(p))
        d["height"].append(24)
        d["block_num"].append(1)
        d["par_num"].append(1)
        d["line_num"].append(linha)
    monkeypatch.setattr(pytesseract, "image_to_data", lambda *a, **k: d)
    # Recortes de coluna: devolvem vazio -> mantém os segmentos da página.
    monkeypatch.setattr(pytesseract, "image_to_string", lambda *a, **k: "")


def test_celulas_rotulo_seguido_do_valor_por_secao(monkeypatch):
    W, palavras = _palavras_grade()
    for i in range(6):  # colunas só valem com X repetido pela página
        palavras.append((40, 900 + 40 * i, "x", 900 + 40 * i))
        palavras.append((520, 900 + 40 * i, "x", 900 + 40 * i))
        palavras.append((1000, 900 + 40 * i, "x", 900 + 40 * i))
    _mock_tesseract(monkeypatch, palavras)
    texto = SPPdfExtractor._ocr_celulas_danfse_v2(Image.new("L", (W, 1200), 255))
    linhas = [l for l in texto.split("\n") if l.strip()]

    def depois(rotulo, ocorrencia=0):
        idx = [i for i, l in enumerate(linhas) if l == rotulo][ocorrencia]
        return linhas[idx + 1]

    assert depois("CNPJ / CPF / NIF", 0) == "25.302.805/0001-10"
    assert depois("CNPJ / CPF / NIF", 1) == "02.370.080/0001-00"
    assert depois("Nome / Nome Empresarial", 0) == "GERENCIAR TRANSPORTES"
    assert depois("Nome / Nome Empresarial", 1) == "STAUMMAQ LTDA"
    assert depois("Telefone", 0) == "(71) 9904-8839"
    assert depois("Telefone", 1) == "(71) 2203-6300"
    assert depois("Código da NBS") == "104011119"
    # Seções na ordem do documento: tudo do prestador antes do tomador, e o
    # NBS (seção SERVIÇO PRESTADO) depois de todo o tomador.
    assert texto.index("25.302.805/0001-10") < texto.index("TOMADOR DO SERVIÇO") \
        < texto.index("(71) 2203-6300") < texto.index("SERVIÇO PRESTADO") < texto.index("104011119")


def test_celulas_sem_secao_prestador_devolve_vazio(monkeypatch):
    W, palavras = _palavras_grade()
    palavras = [p for p in palavras if p[2] not in ("PRESTADOR",)]
    _mock_tesseract(monkeypatch, palavras)
    assert SPPdfExtractor._ocr_celulas_danfse_v2(Image.new("L", (W, 1200), 255)) == ""


# ----------------------------------------------------------------------
# Regressão em lote (2026-10-21): outras DANFSe v2.0 escaneadas do mesmo
# corpus, agora também reconstruídas pela grade. Textos REAIS de `_ocr_page`.
# ----------------------------------------------------------------------

# "DANFSe v1.pdf" (apesar do nome, v2.0): nota nº 2600000000034, PROJECT OBRAS
# LTDA (Barreiras/BA) -> SAO PEDRO CONSTRUTORA LTDA (Lauro de Freitas/BA).
# O OCR perdeu o rótulo "Município / Sigla UF" do PRESTADOR.
OCR_PROJECT_OBRAS = 'Nota Fiscal de\nServiço Eletrônica\nCHAVE DE ACESSO DA NFS-E\n29032011226791663000165260000000003426100010630818\nNÚMERO DA NFS-E\n2600000000034\nNÚMERO DA DPS\n260000000000003\nEMITENTE DA NFS-E\nPrestador\n\nDANFSe v2.0\nDocumento Auxiliar da NFS-e\nCOMPETÊNCIA DA NFS-E\n16/10/2026\nSÉRIE DA DPS\n70000\nSITUAÇÃO DA NFS-E\nNFS-e Gerada\n\nDATA E HORA DA EMISSÃO DA NFS-\nE\n16/10/2026 17:13:26\nDATA E HORA DA EMISSÃO DA DPS\n16/10/2026 17:13:26\nFINALIDADE\nNFS-e regular\n\nMunicípio: Barreiras - BA\nAmbiente Gerador: 1\nTipo de Ambiente: 1\nA autenticidade desta NFS-e pode ser\nverificada pela leitura deste código QR ou pela\nconsulta da chave de acesso no portal\nnacional da NFS-e.\n\nPRESTADOR / FORNECEDOR\nNome / Nome Empresarial\nPROJECT OBRAS LTDA\nEndereço\nRua Gersino Francisco de Amorim, 440, CASA, Bandeirantes\nSimples Nacional na Data de Competência\nNão Optante\n\nCNPJ/CPF /NIF\n26.791.663/0001-65\nRegime de Apuração Tributária pelo SN\n\nIndicador Municipal (Inscrição)\n000016492\nBarreiras / BA\nE-mail\nprojectobras.barreiras(Ogmail.com\n\nTelefone\n(77) 3611-1828\nCódigo IBGE / CEP\n2903201 / 47802-460\n\nTOMADOR DO SERVIÇO\nNome / Nome Empresarial\nSAO PEDRO CONSTRUTORA LTDA\nEndereço\nRUA, 554, QUADRA 28, LOTE 09, VILAS DO ATLANTICO\n\nCNPJ/CPF / NIF\n03.051.741/0001-90\n\nIndicador Municipal (Inscrição)\nMunicípio / Sigla UF\nLauro de Freitas / BA\nE-mail\nsp(Osaopedroconstrutora.com.br\n\nTelefone\nCódigo IBGE / CEP\n2919207 / 42708-720\n\nDESTINATÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e\n\nINTERMEDIÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e\n\nSERVIÇO PRESTADO\nExecução, por administração, empreitada ou subempreitada, de obras de construção civil, hidráulica ou elétrica e de outras obras semelhantes, inclusive sondagem, perfu...\nDescrição do Serviço\nPRESTAÇÃO DE SERVIÇOS - OBRA SESI BARREIRAS MEDIÇÃO 02 DATA - 14/10/2026 60% Material - R$ 7.712,10 40% Mão de Obra - R$ 5.141,40\n\nCódigo de Tributação Nacional / Municipal\n07.02.01 /-\n\nCódigo da NBS\n101011100\n\nLocal da Prestação / Sigla UF / País\nBarreiras /BA/ BR\n\nTRIBUTAÇÃO MUNICIPAL (ISSQN)\nRegime Especial de Tributação do ISSQN\nNenhum\nBenefício Municipal\nBC ISSQN\nR$ 12.853,50\n\nTipo de Tributação do ISSQN\nOperação tributável\nTipo de Imunidade do ISSQN\nCálculo do BM\nR$ 0,00\nAlíquota Aplicada\n5,00%\n\nMunicípio / Sigla UF / País de Incidência do ISSQN\nBarreiras /BA/ BR\nSuspensão da Exigibilidade do ISSQN\nNão\nTotal Deduções/Reduções\nR$ 0,00\nRetenção do ISSQN\nNão Retido\n\nIN\nNúmero Processo Suspensão\nDesconto Incondicionado\nISSQN Apurado\nR$ 642,68\n\nTRIBUTAÇÃO FEDERAL (EXCETO\nCBS)\nPIS - Débito Apuração Própria\nR$ 83,55\n\nIRRF\nR$ 128,54\nCOFINS - Débito Apuração Própria\nR$ 385,61\n\nContribuição Previdenciária - Retido\nR$ 565,55\nDescrição Contrib. Sociais - Retidas\nPIS/COFINS/CSLL Retidos\n\nContribuições Sociais - Retidas\nR$ 128,54\n\nTRIBUTAÇÃO IBS / CBS\nExclusões e Reduções da Base de Cálculo\nR$ 1.111,84\nAlíq. Efetiva Municipal - IBS\n0,00%\nValor Total Apurado - IBS\nR$ 11,74\n\nCST/ cClassTrib\n000 / 000001\nBase de Cálculo Após Exclusões e\nReduções\nR$ 11.741,66\nValor Apurado Municipal - IBS\nR$ 0,00\nAlíquota - CBS\n0,90%\n\nIndicador de Operação / Código IBGE Incidência / Município Incidência / Sigla UF\n020201 / 2903201 / Barreiras / BA\nRed. Alíquota IBS / Red. Alíquota CBS\n-[--\nAlíq. Efetiva Estadual - IBS\n0,10%\nAlíquota Efetiva - CBS\n0,90%\n\nAlíquota - IBS UF /IBS Mun\n0,10% / 0,00%\nValor Apurado Estadual - IBS\nR$ 11,74\nValor Total Apurado - CBS\nR$ 105,67\n\nVALOR TOTAL DA NFS-E\nTotal das Retenções (ISSQN / Federais)\nR$ 822,63\n\nVALOR DA OPERAÇÃO / SERVIÇO\nR$ 12.853,50\nVALOR LÍQUIDO DA NFS-e\nR$ 12.030,87\n\nDesconto Incondicionado\nTotal do IBSICBS\nR$ 117,41\n\nDesconto Condicionado\nVALOR LÍQUIDO DA NFS-e + IBS/CBS\nR$ 12.030,87\n\nINFORMAÇÕES COMPLEMENTARES\nTotais Aproximados dos Tributos cfe. Lei nº 12.741/2012: Federais: -; Estaduais: -; Municipais: -;\n\nDATA CIENTIFICAÇÃO\n\nIDENTIFICAÇÃO E ASSINATURA\n\nNº NFS-E / CHAVE NFS-E\n2600000000034 / 29032011226791663000165260000000003426100010630818'

# "NF 15 PAULO ROBERTO.pdf" (foto): MEI 65.777.853 PAULO ROBERTO ALVES
# (Barreiras/BA) -> SAO PEDRO CONSTRUTORA. Rótulos degradados ("Código IBGE
# CEP", "2903201 [47813-150", "País do Incidência do ISSQ").
OCR_PAULO_ROBERTO = 'meça\nN FSe fio\nA\nServiço eletrônica\nCHAVE DE ACESSO DA NFS.\n29032012265777853000180000000000001526101229619123\nNÚMERO DA NFS-o\n15\nNÚMERO DA DPS\n15\nEMITENTE DA NFS e\nPrestador\n\nDANFSe v2.0\nDocumento Auxiliar da NFS-o\nCOMPETÊNCIA DA NFS-0\n13/10/2026\nSÉRIE DA DPS\n70000\nSITUAÇÃO DA NFS é\nNFS.e MEI\n\nDATA E HORA DA EMISSÃO DA NFS-6\n13/10/2026 16:18:12\nDATA E HORA DA EMISSÃO DA DPS\n13/10/2026 16:18:12\nFINALIDADE\n\ns\nA autenticidade desta NFS-s poda ser vorficada\npota leitura dasta código GR ou pola consulta da\nchave de acosso no portal nacional da NFS\n\nPRESTADOR / FORNECEDOR\nNome / Nome Empresarial\n65.777.853 PAULO ROBERTO ALVES\nEndereço\nRUA ANTONIA VENANCIO DE ARAUJO, 43, VILA RICA\nSimples Nacional na Data de Competência Regime de Apuração Tributária pelo SN\nOptante - Microempreendedor Individua...\n\nCNPJ/CPF NIF\n65.777.853/0001-80\n-\n\nIndie: Municipal (Inscrição)\nMuntelpio / Sigia UF\nBarreiras /BA\nE-mail\nMULTI CONTABILGOHOTMAIL.COM\n\nTolofono\n(77) 9858-0304\nCódigo IBGE CEP\n2903201 [47813-150\n\nTOMADOR / ADQUIRENTE\nNome / Nome Empresarial\nSAO PEDRO CONSTRUTORA LTDA\nE\nndereço\nPRAIA DE PAJUSSARA, 554, QUADRA 28 LOTE 09, VILAS DO ATLANTICO\n\nCNPJ/CPF NIF\n03.051.741/0001-90\n\nIndicador Municipal (Inscrição)\nMunicípio / Sigla UF\nLauro de Freitas / BA\nE-mail\n\nTelefone\nCódigo IBGE [CEP\n2919207 /42.708-720\n\nDESTINATÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e\n\nemma\n\nINTERMEDIÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NE S-e\n\na\npsi\nEd\n\nSERVIÇO PRESTADO\nPlanejamento, coordenação, programação ou organização administrativa.\nDescrição do Serviço\nREFERENTE A HORAS EXTRAS COM SERVIÇOS DE ALMOXARIFE NA OBRA SESI BARREIRAS CNO: 90.025.09029/79 PERIODO 01/09/2026 A 30/09/2026.\n\nCódigo de Tributação Nacional/Municipal\n17.03.03/-\n\nCódigo da NBS\n1.2606.00.00\n\nTocal da Prestação / Sigla UF / País\nBarreiras / BA / -\n\nTRIBUTAÇÃO MUNICIPAL (ISSQN)\nBCISSQN\n\nTipo de Tributação do ISSQN\nOperação Tributável\nAliquota Aplicada\n\ne\nMunicípio / Sigla UF / País do Incidência do ISSQ\nBarreiras / BA / -\nRetenção do ISSQN\nNão Retido\n\nISSQN Apurado\n\nTRIBUTAÇÃO FEDERAL (EXCETO CBS) IRRF\nPIS - Débito Apuração Própria\nMR\n\nCOFINS - Débito Apuração Própria\nss\nTA O O adia\n\nContribuição Previdenciária - Retida\nDescrição Contrib. Sociais - Retidas\n\nContribuições Sociais - Retidas\n\nTRIBUTAÇÃO IBS/CBS\nExclusões e Reduções da Base de Cálculo\nR$ 0,00\nAli. Efetiva Municipal -IBS\nValor Total Apurado - IBS\n\nCST/cClassTrib\njo\nBase de Cálculo Após Exclusões e Reduções\nValor Apurado Municipal - IBS\nAlíquota -CBS\n\nIndicador de Operação / Código IBGE Incidência / Município Incidência / Sigla UF\nSPTRE\nRed. Alíquota IBS / Red. Alíquota CBS\nIE\nAli. Efetiva Estadual - IBS\nAlíquota Efetiva - CBS\n\nAlíquota - IBS UF / IBS Mum\nEra\nValor Apurado Estadual - BS\nValor Total Apurado - CBS\n\nVALOR TOTAL DA NFS-e\nTotal das Retenções (ISSQN / Federais)\n\nVALOR DA OPERAÇÃO / SERVIÇO\nR$ 735,13\nVALOR LÍQUIDO DA NFS-e\nR$ 735,13\n\nDesconto Incondicionado\nTotal do IBS/CBS\nR$ 0,00\n\nDesconto Condicionado\nVALOR LÍQUIDO DA NFS-e + IBS/ICES\nR$ 0,00\n\nINFORMAÇÕES COMPLEMENTARES\nTotais aproximados dos Tributos cfe. Lei nº 12.741/2012: Federais: -; Estaduais: -; Municipais: -;\n\nSÃO PEDRO CONSTRUTORA\nOBRA Ponuinoh. Sem\nSENGE 65834\nMaria R epa\n\nDATA CIENTIFICAÇÃO:\n\nIDENTIFICAÇÃO E ASSINATURA\n\nNº NFS-e / CHAVE NFS -e\n15/29032012265777853000180000000000001526101229619123\n'

# "TDR COMERCIO - 1.pdf": a reconstrução NÃO se aplica (título "PRESTADOR
# FORNECEDOR" sem a barra no OCR) e o texto é a leitura original, com o rótulo
# "Descrição do Serviço" seguido de outro rótulo da grade.
OCR_TDR = 'CHAVE DE ACESSO DA NFS-e\n29192072235802249000103000000000000126090271311020\n\nNÚMERO DA NFS-e COMPETÊNCIA DA NFS-e\n1 02/09/2026\n\nSÉRIE DA DPS\n70000\n\n* SITUAÇÃO DA NFS-e\nNFS-e Gerada\n\nNÚMERO DA DPS\n\nEMITENTE DA NFS-s.\nPrestador\n\nDATA E HORA DA EMISSÃO DA NFS-e\n02/09/2026 10:44:13\n\nDATA E HORA DA EMISSÃO DA DPS\n02/09/2026 10:44:12\n\nFINALIDADE\n\nCNPJ/CPF | NIF\n35.802.249/0001-03\n\n“PRESTADOR FORNECEDOR Z\n\nNome / Nome Empresarial\nTDR COMERCIO E SERVICOS LTDA\n\nEndereço\nAVN AMARILIO THIAGO DOS SANTOS, 1566, GALPAO 30, VILA PRAIANA\n\nSimples Nacional na Data de Competência\nOptante - Microempresa ou Empresa de ...\n\nRegime de Apuração Tributária pelo SN\n\nIndicador Municipal (Inscrição)\n10038627\n\nMunicípio / Sigla UF\nLauro de Freitas /BA\n\nE-mail\nfinanceiroQDtdrservices.com.br\n\nRegime de apuração dos tributos federais e municipal pelo Simples Nacional\n\nA autenticidade desta NFS-e pode ser verificada\npela leitura deste código QR ou pela consulta da\nchave de acesso no portal nacional da NFS-e\n\nTelefone\n(71) 98112-8882\n\nCódigo IBGE / CEP\n29.19207 / 42.704-550\n\nCNPJ/CPF /NIF\n\nTOMADOR. ADQUIRENTE, Ê\nE » 04.555.283/0001-99\n\nNome / Nome Empresarial”\n\nBONI TRANSPORTES, LOGISTICA E COMERCIO LTDA.\n\nEndereço\nDOUTOR GERINO DE SOUZA FILHO, 1025, ACESSO PELA RUA JOELMA S. MENDES\n- LOTES 04 A 08 QUADRA A, ITINGA\n\nIndicador Municipal (Inscrição)\n\nMunicípio / Sigla UF\n\nLauro de Freitas / BA\n\nE-mail\n\nadm bonialimentos.com.br\n\nTelefone\n\nCódigo IBGE / CEP\n29.19207 / 42.738-200\n\nDESTINATÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e\n\nINTERMEDIÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e\n\n“SERVIÇO PRESTADO Código de Tributação NacionallMunicipal\nREC pn 14.01.01/-\n\nLubrificação, limpeza, lus\n\nDescrição do Serviço\n\nCódigo da NBS\n1.2001.50.00\n\nLocal da Prestação / Sigla UF / Pais\nLauro de Freitas / BA /-\n\n, Carga e recarga, conserto, restauração, blindagem, manutenção e conservação de máquinas, veículos, aparelhos, equipamentos, ...\n\nMANUTENÇÃO MENSAL EM EQUIPAMENTOS DE REFRIGERAÇÃO, REFERENTE AO MÊS 08 2026. FAVOR CREDITAR: BANCO BRADESCO AGÊNCIA 2472-4 C.C 76370-5.\nPIX CNPJ: 35.802.249/0001-03. FAVORECIDO: TDR COMERCIO E SERVIÇOS LTDA. VENCIMENTO: 05 DE SETEMBRO, DE 2026.\n\nTRIRUTAÇÃO. MUNICIPAL: tssoN Ê Tipo de Tributação do ISSQN\n\nOperação Tributável\n\nBC ISSQN “ Alíquota Aplicada\n\nMunicípio / Sigla UF / País de Incidência do ISSQN\n\nLauro de Freitas / BA / -\n\nRetenção do ISSQN\nNão Retido\n\nISSQN Apurado\n\nIRRF\n\nTRIBUTAÇÃO FEDERAL (E:\n\nPIS - Débito Apuração Própi “ COFINS - Débito Apuração Própria\n\nContribuição Previdenciária - Retida\n\nDescrição Contrib. Sociais - Retidas\n\nContribuições Sociais - Retidas\n\nCST/ cClassTrib\n\nTRIBUTAÇÃO IBS/CBS:\n\nExclusões e Reduções da Base de Cálculo Base de Cálculo Após Exclusões e Reduções\nR$ 0,00 -\n\nAlig. Efetiva Municipal - IBS Valor Apurado Municipal - IBS\n\nValor Total Apurado - IBS Alíquota - CBS\n\nIndicador de Operação / Código IBGE Incidência / Município Incidência / Sigla UF\n\n-Pd-d-\n\nRed. Alíquota IBS / Red. Alíquota CBS\n-J-d-\n\nAlig. Efetiva Estadual - IBS\n\nAlíquota Efetiva - CBS\n\nAliquota - IBS UF /IBS Mun\n-1-\n\nValor Apurado Estadual - IBS\n\nValor Total Apurado - CBS\n\nVALOR DA OPERAÇÃO / SERVIÇO\nR$ 8.265,00\n\nTotal das Retenções (ISSQN / Federais) VALOR LÍQUIDO DA NFS-e\n. R$ 8.265,00\n\nVALOR TOTALD;\n\nDesconto Incondicionado\n\nTotal do IBSICBS\nR$ 0,00\n\nDesconto Condicionado\n\n“INFORMAÇÕES COMPLEMENTARES\n\nTotais aproximados dos Tributos cfe. Lei nº 12.741/2012: Federais: R$ 0,00; Estaduais: R$ 0,00; Municipais: R$ 413,25:\n\nDATA CIENTIFICAÇÃO: IDENTIFICAÇÃO E ASSINATURA Nº NFS-e / CHAVE NFS-e\n1/29192072235802249000103000000000000126090271311020\n\n'


def test_projeto_obras_cada_entidade_le_a_propria_secao(monkeypatch):
    nota = _parse(monkeypatch, OCR_PROJECT_OBRAS, "dummy_v2_project.pdf")
    p, tm = nota.prestador, nota.tomador
    assert (p.cnpj_cpf, p.razao_social) == ("26791663000165", "PROJECT OBRAS LTDA")
    assert (p.endereco.codigo_municipio, p.endereco.uf, p.endereco.cep) == ("2903201", "BA", "47802460")
    assert (tm.cnpj_cpf, tm.razao_social) == ("03051741000190", "SAO PEDRO CONSTRUTORA LTDA")
    # Antes: UF do tomador vazia -> o transformer completava com SP.
    assert (tm.endereco.codigo_municipio, tm.endereco.uf, tm.endereco.cep) == ("2919207", "BA", "42708720")
    # O Código da NBS (101011100) não é a IM do tomador (impressa "-").
    assert not tm.inscricao_municipal
    assert nota.valores.valor_inss == 565.55
    assert nota.valores.valor_liquido_nfse == 12030.87
    assert nota.servico_codigo == "0702"


def test_paulo_roberto_mei_rotulos_degradados(monkeypatch):
    nota = _parse(monkeypatch, OCR_PAULO_ROBERTO, "dummy_v2_paulo.pdf")
    p = nota.prestador
    assert p.cnpj_cpf == "65777853000180"
    # Nome empresarial do MEI como impresso (raiz do CNPJ incluída) - mesma
    # grafia que as notas digitais deste MEI já geram.
    assert p.razao_social == "65.777.853 PAULO ROBERTO ALVES"
    assert (p.endereco.codigo_municipio, p.endereco.uf, p.endereco.cep) == ("2903201", "BA", "47813150")
    assert nota.tomador.endereco.cep == "42708720"
    xml = Abrasf201Transformer().transform(nota)
    assert "<MunicipioIncidencia>2903201</MunicipioIncidencia>" in xml
    assert nota.discriminacao.startswith("REFERENTE A HORAS EXTRAS")


def test_tdr_discriminacao_nao_pega_rotulo_vizinho(monkeypatch):
    nota = _parse(monkeypatch, OCR_TDR, "dummy_v2_tdr.pdf")
    assert "NBS" not in nota.discriminacao
    assert "1.2001.50.00" not in nota.discriminacao


def test_codigo_nbs_nao_vira_item_lc116():
    ex = SPPdfExtractor("x.pdf")
    ex.layout = LAYOUT_NACIONAL_REFORMA
    ex.raw_text = ("SERVIÇO PRESTADO\n\nCÓDIGO DE TRIBUTAÇÃO NACIONAL / MUNICIPAL\n7.11.01 / 366\n\n"
                   "CÓDIGO DA NBS\n1.1409.11.00\n")
    assert ex._extrair_codigo_servico() != "0911"


def test_duas_notas_reconstruidas_no_mesmo_pdf_nao_se_fundem(monkeypatch):
    """Texto reconstruído por coluna põe "NÚMERO DA NFS-E" sozinho na linha;
    o número heurístico de continuação caía no "Lei nº 12.741/2012" do
    rodapé (igual nas duas notas) e a 2ª página era engolida pela 1ª
    (achado real no lote: "nfs 16.10", NF 2600000000917 sumia)."""
    caminho = "tests/dummy_v2_duas_paginas.pdf"
    with open(caminho, "wb") as f:
        f.write(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr",
                        lambda self: OCR_CELULAS + "\n\x0c\n" + OCR_PROJECT_OBRAS)
    try:
        notas = SPPdfExtractor(caminho).parse_multiple()
    finally:
        if os.path.exists(caminho):
            os.remove(caminho)
    assert sorted(n.numero for n in notas) == ["2600000000034", "2600000000058"]


def test_rotulo_abaixo_de_endereco_nao_vira_logradouro(monkeypatch):
    """OCR perdeu a linha do logradouro: a linha seguinte ao rótulo
    "Endereço" é outro rótulo da grade (achado real no lote: "nfs 16.10",
    pág. 5, ATRIO CONTAINERS)."""
    texto = OCR_CELULAS.replace(
        "Endereço\nRua D, 00079, QUADRA:04;LOTE:15;:LOT. SOL NASCENTE, Centro\n", "Endereço\n")
    assert texto != OCR_CELULAS
    p = _parse(monkeypatch, texto, "dummy_v2_sem_logradouro.pdf").prestador
    assert p.cnpj_cpf == "25302805000110"
    assert p.endereco.logradouro == "Não informado"
