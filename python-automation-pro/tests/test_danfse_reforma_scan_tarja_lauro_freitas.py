# -*- coding: utf-8 -*-
r"""DANFSe v2.0 (LAYOUT_NACIONAL_REFORMA) ESCANEADAS com TARJAS CINZA
RETICULADAS — Lauro de Freitas/BA, pasta "Notas\092026\1°_QUINZENA (1)":

* "DAVID SOUZA SANTANA JUNIOR - 103.pdf": nota nº 103, DAVID SOUZA SANTANA
  JUNIOR 85910720570 (MEI, CNPJ 26.159.018/0001-24) -> BONI TRANSPORTES,
  LOGISTICA E COMERCIO LTDA. (04.555.283/0003-50), item 07.11.02, R$ 706,00.
* "SBS - 39.pdf": nota nº 39, SBS SOLUCOES INTEGRADAS DE SEGURANCA
  ELETRONICA II LTDA (46.876.522/0001-52) -> BONI, código 99.01.01 ("Serviços
  sem a incidência de ISSQN e ICMS"), R$ 660,51.

Causa raiz: o título "DANFSe v2.0" e TODOS os títulos de seção da grade
("PRESTADOR / FORNECEDOR", "TOMADOR / ADQUIRENTE", "TRIBUTAÇÃO IBS/CBS"...)
vêm em tarja cinza reticulada, que o Tesseract não lê. Sem eles a página caía
na DANFSe v1.0 (`LAYOUT_NACIONAL`) e o parser da v1.0 montava prestador
"SÉRIE DA DPS", UF "SI", CEP = IBGE, município Salvador, tomador com o
endereço do prestador, `<Intermediario>` falso com a tarja "DA OPERAÇÃO NÃO
IDENTIFICADO NA NFS-e" e — na nº 39 — o PRESTADOR com o CNPJ da matriz da
BONI (04.555.283/0001-99, fallback de razão "BONI" do parser genérico).

Correção: (1) marca da v2.0 tolerante à perda dos títulos (`_eh_danfse_v2`);
(2) a reconstrução pela grade (`_ocr_celulas_danfse_v2`) acha os títulos numa
cópia sem retícula (`_danfse_v2_titulos_tarja`) e relê isolado o valor de
forma quebrada colado à tarja (`_danfse_v2_reler_valor_truncado`); (3) parser
da v2.0: CPF/CNPJ ancorado no rótulo, razão social com rótulo ilegível,
"Naclonal", MEI truncado ("Individua..."), código 99 -> "0000" + aviso.

`OCR_ORIGINAL_*` é a leitura de página inteira (o que a main parseava);
`OCR_CELULAS_*` é o retorno REAL de `_ocr_page` depois do fix (texto
reconstruído pela grade), preservado via `repr()` com os erros de OCR que
sobraram ("Naclonal", "Ecmalt", "drmaquinas2016Ogmail.com",
"financeiro)sbsgrupo.com.br", "SBS TEC Il", "PIX: CPF 859,107.205-70")."""
import os

from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_NACIONAL_REFORMA, _eh_danfse_v2
from src.transformers.abrasf_transformer import Abrasf201Transformer

OCR_ORIGINAL_103 = 'CHAVE DE ACESSO DA NFS-e\n\n29192072226159018000124000000000010326092224611770\n\nNÚMERO DA NFS-e\n103\n\nNÚMERO DA DPS\n90\n\n“EMITENTE\nid\n\nNome / Nome Empresarial\n\nCOMPETÊNCIA DA NFS-e\n04/09/2026\n\nSÉRIE DA DPS\n70000\n\n“ SITUAÇÃO DA NFS-o\n\nNFS-e MEI\n\nDATA E HORA DA EMISSÃO DA NFS-e\n04/09/2026 10:18:12\n\nDATA E HORA DA EMISSÃO DA DPS\n04/09/2026 10:18:12\n\nFINALIDADE\n\npela leitura deste código QR ou pela consulta da\nchave de acesso no portal nacional da NFS-e”\n\nCNPJ/CPF) NIF\n26.159.018/0001-24\n\nDAVID SOUZA SANTANA JUNIOR 85910720570\n\nEndereço\nRUA BOCA DA MATA, 19, PORTAO\n\nSimples :Naclonal na Data de Competência\nOptante - Microempreendedor Individua...\n\nRegime de Apuração Tributária pelo SN\n\nNome / Nome Empresarial\n\nCNPJ/CPF/NIF\n04.555.283/0003-50\n\nBONI TRANSPORTES, LOGISTICA E COMERCIO LTDA.\n\nEndereço\n\nMARIA QUITERIA, 263, GALPAO LOT DESMEMBRAMENTO DIAMANTE, ITINGA\n\nIndicador Municipal (Inscrição)\nMunicípio / Sigla UF\n\nLauro de Freitas / BA\n\nEcmalt\ndrmaquinas2016Ogmail.com\n\nIndicador Municipal (inscrição)\n\nMunicípio / Sigla UF\nLauro de Freitas / BA\n\nE-mail\n\nTelefone\n(71) 8321-9277\n\nCódigo IBGE / CEP\n29.19207 / 42.700-130\n\nTelefone\n\nCódigo IBGE / CEP\n29.19207 / 42.738-205\n\nDESTINATÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NANES:S\n\nINTERMEDIÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NES-e\n\nRê\n\nCódigo de Tributação Naclonal/Municipal\n07.11.02/-\n\nJardinagem, inclusive corte e poda de árvores.\n\nDescrição do Serviço\n\nCódigo da NBS\n\nLocal da Prestação / Sigla UF / País\nLauro de Freitas / BA/ -\n\nSERVIÇO DE MANUTENÇÃO EM LAVADORA KARCHER HD 585 O.S 8451. GARANTIA DE 90 DIAS. Caixa Agencia : 3462 Operação : 013 Numero : 17709-4 CPF 859.107.205-70\n\nPIX: CPF 859,107.205-70 David Souza Santana Junior\n\n TRIBUTAÇÃO:MUNICI! (ISSA!\n\nBC ISSQN\n\nTipo de Tributação do ISSQN\nOperação Tributável\n\nAlíquota Aplicada\n\nMunicípio / Sigla UF / País de Incidência do ISSQN\n\nLauro de Freitas / BA / -\n\nRetenção do ISSQN\nNão Retido\n\nCOFINS - Débito Apuração Própria\n\nExclusões e Reduções da Base de Cálculo\n\nR$ 0,00\nAlíg. Efetiva Municipal « IBS\n\nValor Total Apurado - IBS\n\nContribuição Previdenciária « Retida\n\nDescrição Contrib. Sociais - Retidas\n\nISSQN Apurado\n\nContribulções Sociais « Retidas\n\nCST/ cClassTrib\nJe\nBase de Cálculo Após Exclusões e Reduções\n\nValor Apurado Municipal - IBS\n\nAlíquota - CBS\n\nIndicador de Operação / Código IBGE Incidência / Município Incidência / Sigla UF\n\n=J=l=d-\n\nRed, Alíquota IBS / Red. Alíquota CBS\n-Jolo\n\nAlig, Efetiva Estadual - IBS\n\nAlíquota Efetiva - CBS\n\nAlíquota - IBS UF /IBS Mun\n\nValor Apurado Estadual - IBS\n\nValor Total Apurado « CBS\n\n“VALOR: Tt DA NF\n\nTotal das Retenções (ISSQN / Federais)\n\nVALOR DA OPERAÇÃO / SERVIÇO\nR$ 706,00\n\nVALOR LÍQUIDO DA NFS-e\nR$ 706,00\n\nINFORMAÇÕES COMPLEMENTARES\n\nf\n\nDesconto Incondicionado\n\nTotal do IBSICBS\nR$ 0,00\n\nDesconto Condicionado\n\nQUIDO DA NFS-e:-+ IBS/CBS.\n\nTotais aproximados dos Tributos cfe. Lei nº 12,741/2012: Federais: -; Estaduais: -; Municipais: -;\n\nDATA CIENTIFICAÇÃO: IDENTIFICAÇÃO E ASSINATURA Nº NFS-s / CHAVE NFS-s\n103 / 29192072226159018000124000000000010326092224611770\n\n'

OCR_CELULAS_103 = 'CHAVE DE ACESSO DA NFS-e\n29192072226159018000124000000000010326092224611770\nNÚMERO DA NFS-e\n103\nNÚMERO DA DPS\n90\n“EMITENTE\nid\n\nCOMPETÊNCIA DA NFS-e\n04/09/2026\nSÉRIE DA DPS\n70000\n“ SITUAÇÃO DA NFS-o\nNFS-e MEI\n\nDATA E HORA DA EMISSÃO DA NFS-e\n04/09/2026 10:18:12\nDATA E HORA DA EMISSÃO DA DPS\n04/09/2026 10:18:12\nFINALIDADE\n\npela leitura deste código QR ou pela consulta da\nchave de acesso no portal nacional da NFS-e”\n\nPRESTADOR / FORNECEDOR\nNome / Nome Empresarial\nDAVID SOUZA SANTANA JUNIOR 85910720570\nEndereço\nRUA BOCA DA MATA, 19, PORTAO\nSimples :Naclonal na Data de Competência\nOptante - Microempreendedor Individua...\n\nCNPJ/CPF) NIF\n26.159.018/0001-24\nRegime de Apuração Tributária pelo SN\n\nIndicador Municipal (Inscrição)\nMunicípio / Sigla UF\nLauro de Freitas / BA\nEcmalt\ndrmaquinas2016Ogmail.com\n\nTelefone\n(71) 8321-9277\nCódigo IBGE / CEP\n29.19207 / 42.700-130\n\nTOMADOR / ADQUIRENTE\nNome / Nome Empresarial\nBONI TRANSPORTES, LOGISTICA E COMERCIO LTDA.\nEndereço\nMARIA QUITERIA, 263, GALPAO LOT DESMEMBRAMENTO DIAMANTE, ITINGA\n\nCNPJ/CPF/NIF\n04.555.283/0003-50\n\nIndicador Municipal (inscrição)\nMunicípio / Sigla UF\nLauro de Freitas / BA\nE-mail\n\nTelefone\nCódigo IBGE / CEP\n29.19207 / 42.738-205\n\nDESTINATÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NANES:S\n\nINTERMEDIÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NES-e\n\nSERVIÇO PRESTADO\nRê\nJardinagem, inclusive corte e poda de árvores.\nDescrição do Serviço\nSERVIÇO DE MANUTENÇÃO EM LAVADORA KARCHER HD 585 O.S 8451. GARANTIA DE 90 DIAS. Caixa Agencia : 3462 Operação : 013 Numero : 17709-4 CPF 859.107.205-70\nPIX: CPF 859,107.205-70 David Souza Santana Junior\n\nCódigo de Tributação Naclonal/Municipal\n07.11.02/-\n\nCódigo da NBS\n\nLocal da Prestação / Sigla UF / País\nLauro de Freitas / BA/ -\n\nTRIBUTAÇÃO MUNICIPAL (ISSQN)\nBC ISSQN\n\n* Tipo de Tributação do ISSQN\n- Operação Tributável\nAlíquota Aplicada\n\nMunicípio / Sigla UF / País de Incidência do ISSQN\nLauro de Freitas / BA / -\nRetenção do ISSQN\nNão Retido\n\nISSQN Apurado\n\nTRIBUTAÇÃO FEDERAL (EXCETO CBS)\n\nIRRF\nCOFINS - Débito Apuração Própria\n\nContribuição Previdenciária « Retida\nDescrição Contrib. Sociais - Retidas\n\nContribulções Sociais « Retidas\n\nTRIBUTAÇÃO IBS / CBS\nExclusões e Reduções da Base de Cálculo\nR$ 0,00\nAlíg. Efetiva Municipal « IBS\nValor Total Apurado - IBS\n\nCSTI cClassTrib\n1.\nBase de Cálculo Após Exclusões e Reduções\nValor Apurado Municipal - IBS\nAlíquota - CBS\n\nIndicador de Operação / Código IBGE Incidência / Município Incidência / Sigla UF\n=J=l=d-\nRed, Alíquota IBS / Red. Alíquota CBS\n-Jolo\nAlig, Efetiva Estadual - IBS\nAlíquota Efetiva - CBS\n\nAlíquota - IBS UF /IBS Mun\nValor Apurado Estadual - IBS\nValor Total Apurado « CBS\n\nVALOR TOTAL DA NFS-e\nTotal das Retenções (ISSQN / Federais)\n\nVALOR DA OPERAÇÃO | SERVIÇO\nR$ 706,00\nVALOR LÍQUIDO DA NFS-e\nR$ 706,00\n\nDesconto Incondicionado\nTotal do IBSICBS\nR$ 0,00\n\nDesconto Condicionado\nLÍQUIDO DA NFS:6 + IBSICES\n\nINFORMAÇÕES COMPLEMENTARES\nf\nTotais aproximados dos Tributos cfe. Lei nº 12,741/2012: Federais: -; Estaduais: -; Municipais: -;\n\nDATA CIENTIFICAÇÃO:\n\nIDENTIFICAÇÃO E ASSINATURA\n\nNº NFS-s / CHAVE NFS-s\n103 / 29192072226159018000124000000000010326092224611770'

OCR_ORIGINAL_39 = "CHAVE DE ACESSO DA NFS-e\n29192072246876522000152000000000003926095791415453\n\nNÚMERO DA NFS-e COMPETÊNCIA DA NFS-e\n39 06/09/2026\n\nNÚMERO DA DPS SÉRIE DA DPS\n40 70000\n\nSITUAÇÃO DA NFS-e\nFS-e Gerada\n\nNPJ / CPF /NIF\n6.876.522/0001-52\n\nme pi\nSBS SOLUCOES INTEGRADAS DE SEGURANCA ELETRONICA II LTDA\n\nEndereço '\nAVN PRAIA DE ITAPOAN, 131, VILAS DO ATLANTICO\n\nSimples Nacional na Data de Competência Regime de Apuração Tributária pelo SN\nNão optante -\n\nDATA E HORA DA EMISSÃO DA NFS-e\n06/09/2026 16:20:57\n\nDATA E HORA DA EMISSÃO DA DPS\n06/09/2026 16:20:57\n\nFINALIDADE\n\nA autenticidade desta NFS-e pode ser verificada\npela leitura deste código QR ou pela consulta da\nchave de acesso no portal nacional da NFS-e\n\nIndicador Municipal (inscrição)\n10041979\n\nMunicípio / Sigla UF\n\nLauro de Freitas / BA\n\nE-mail\nfinanceiro)sbsgrupo.com.br\n\nTelefone\n(71) 99632-1095\n\nCódigo IBGE / CEP\n29.19207 / 42.707-650\n\nCNPJ/CPF /NIF\n4.555.283/0003-50\n\nome / Nome Empresarial\nBONI TRANSPORTES, LOGISTICA E COMERCIO LTDA.\n\nEndereço\nMARIA QUITERIA, 263, GALPAO LOT DESMEMBRAMENTO DIAMANTE, ITINGA\n\nindicador Municipal (Inscrição) *\n\nMunicípio / Sigla UF\nLauro de Freitas /BA\n\nE-mail\n\nTelefone v\n\nCódigo IBGE / CEP\n29.19207 / 42.738-205\n\nDESTINATÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e\n\nINTERMEDIÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NF S-e\n\nCódigo de Tributação Nacional/Municipal\n9.01.01/-\n\nDescrição do Serviço\n\nCódigo da NBS\n\nLocal da Prestação / Sigla UF / País\nLauro de Freitas / BA / -\n\n'\n\nCONTRATO Nº [TS BTLC 014/2024 SBS TEC Il] COMPETÊNCIA: 09/2026 LOCAÇÃO DE EQUIPAMENTOS E MONITORAMENTO - R$ 660,51 VENCIMENTO: 05/10/2026 FORMA\n\nDE PAGAMENTO: BOLETO BANCÁRIO - BANCO DO BRASIL\n\nTRIBUTAÇÃO MUNICIPAL (ISSQN) - OPERAÇÃO NÃO SUJEITA AO ISSQN\n\nIRRF\n\nCOFINS - Débito Apuração Própria\n\nContribuição Previdenciária - Retida\n\nDescrição Contrib. Sociais - Retidas\n\nContribuições Sociais - Retidas\n\nCST/cClassTrib\n\nBase de Cálculo Após Exclusões e Reduções\n\nAlig. Efetiva Municipal - IBS Valor Apurado Municipal - IBS\n\nValor Total Apurado - IBS Alíquota - CBS\n\nVALOR DA OPERAÇÃO / SERVIÇO\nR$ 660,51\n\n“tal das Retenções (ISSQN / Federais) VALOR LÍQUIDO DA NFS-e\n- R$ 660,51\n\nIndicador de Operação / Código IBGE Incidência / Município Incidência / Sigla UF\n\nNANA\nRed. Alíquota IBS / Red. Alíquota CBS\n\nAlíg. Efetiva Estadual - IBS\n\nAlíquota Efetiva - CBS\n\nAlíquota - IBS UF /IBS Mun\n\nValor Apurado Estadual - IBS\n\nValor Total Apurado - CBS\n\nDesconto Incondicionado\n\n* Total do IBS/CBS\n\nR$ 0,00\n\nDesconto Condicionado a\n\nINFORMAÇÕES COMPLEMENTARES\n\nTotais aproximados dos Tributos cfe. Lei nº 12.741/2012: Federais: R$ 0,00; Estaduais: R$ 0,00; Municipais: R$ 0,00;\n\ngs\n\nDATA CIENTIFICAÇ, IDENTIFICAÇÃO E ASSINATURA Nº NFS-e / CHAVE NFS-e\n39 / 29192072246876522000152000000000003926095791415453\n\n"

OCR_CELULAS_39 = "CHAVE DE ACESSO DA NFS-e\n29192072246876522000152000000000003926095791415453\nNÚMERO DA NFS-e\n39\nNÚMERO DA DPS\n40\n\nCOMPETÊNCIA DA NFS-e\n06/09/2026\nSÉRIE DA DPS\n70000\nSITUAÇÃO DA NFS-e\nFS-e Gerada\n\nDATA E HORA DA EMISSÃO DA NFS-e\n06/09/2026 16:20:57\nDATA E HORA DA EMISSÃO DA DPS\n06/09/2026 16:20:57\nFINALIDADE\n\nA autenticidade desta NFS-e pode ser verificada\npela leitura deste código QR ou pela consulta da\nchave de acesso no portal nacional da NFS-e\n\nPRESTADOR / FORNECEDOR\nme\npi\nSBS SOLUCOES INTEGRADAS DE SEGURANCA ELETRONICA II LTDA\nEndereço\n'\nAVN PRAIA DE ITAPOAN, 131, VILAS DO ATLANTICO\nSimples Nacional na Data de Competência\nNão optante\n\nNPJ / CPF /NIF\n46.876.522/0001-52\nRegime de Apuração Tributária pelo SN\n-\n\nIndicador Municipal (inscrição)\n10041979\nMunicípio / Sigla UF\nLauro de Freitas / BA\nE-mail\nfinanceiro)sbsgrupo.com.br\n\nTelefone\n(71) 99632-1095\nCódigo IBGE / CEP\n29.19207 / 42.707-650\n\nTOMADOR / ADQUIRENTE\nome / Nome Empresarial\nBONI TRANSPORTES, LOGISTICA E COMERCIO LTDA.\nEndereço\nMARIA QUITERIA, 263, GALPAO LOT DESMEMBRAMENTO DIAMANTE, ITINGA\n\nCNPJ/CPF /NIF\n04.555.283/0003-50\n\nindicador Municipal (Inscrição) *\nMunicípio / Sigla UF\nLauro de Freitas /BA\nE-mail\n\nTelefone v\nCódigo IBGE / CEP\n29.19207 / 42.738-205\n\nDESTINATÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e\n\nINTERMEDIÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NF S-e\n\nSERVIÇO PRESTADO\nDescrição do Serviço\nCONTRATO Nº [TS BTLC 014/2024 SBS TEC Il] COMPETÊNCIA: 09/2026 LOCAÇÃO DE EQUIPAMENTOS E MONITORAMENTO - R$ 660,51 VENCIMENTO: 05/10/2026 FORMA\nDE PAGAMENTO: BOLETO BANCÁRIO - BANCO DO BRASIL\n\nCódigo de Tributação Nacional/Municipal\n99.01.01/-\nTRIBUTAÇÃO MUNICIPAL (ISSQN) - OPERAÇÃO NÃO SUJEITA AO ISSQN\n\nCódigo da NBS\n\nLocal da Prestação / Sigla UF / País\nLauro de Freitas / BA / -\n'\n\nTRIBUTAÇÃO FEDERAL (EXCETO CBS)\nDébito Apuração\n\n“ COFINS - Débito Apuração Própria\n\nContribuição Previdenciária - Retida\nDescrição Contrib. Sociais - Retidas\n\nContribuições Sociais - Retidas\n\nTRIBUTAÇÃO IBS / CBS\n“Exclusões e Reduções da Base de Cálculo\nR$ 0,00\nAlig. Efetiva Municipal - IBS\nValor Total Apurado - IBS\n\n7 CST/ cClassTrib\n“1\nBase de Cálculo Após Exclusões e Reduções\nValor Apurado Municipal - IBS\nAlíquota - CBS\n\nIndicador de Operação / Código IBGE Incidência / Município Incidência / Sigla UF\nNANA\nRed. Alíquota IBS / Red. Alíquota CBS\nAlíg. Efetiva Estadual - IBS\nAlíquota Efetiva - CBS\n\nAlíquota - IBS UF /IBS Mun\nValor Apurado Estadual - IBS\nValor Total Apurado - CBS\n\nVALOR TOTAL DA NFS-e\nAR\nTotal das Retenções (I5SQ\nN / Federais)\n\nVALOR DA OPERAÇÃO / SERVIÇO\nR$ 660,51\nVALOR LÍQUIDO DA NFS-e\nR$ 660,51\n\nDesconto Incondicionado\n“ Total do IBS/CBS\nR$ 0,00\n\nDesconto Condicionado -;-\n\nINFORMAÇÕES COMPLEMENTARES\nTotais aproximados dos Tributos cfe. Lei nº 12.741/2012: Federais: R$ 0,00; Estaduais: R$ 0,00; Municipais: R$ 0,00;\n\ngs\n\nDATA CIENTIFICAÇ,\n\nIDENTIFICAÇÃO E ASSINATURA\n\nNº NFS-e / CHAVE NFS-e\n39 / 29192072246876522000152000000000003926095791415453"


def _parse(monkeypatch, texto, nome):
    """Caminho real: pdfminer não acha texto (PDF escaneado) e o extrator cai
    no OCR."""
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


def _n103(monkeypatch):
    return _parse(monkeypatch, OCR_CELULAS_103, "dummy_v2_tarja_103.pdf")


def _n39(monkeypatch):
    return _parse(monkeypatch, OCR_CELULAS_39, "dummy_v2_tarja_39.pdf")


# ---------------------------------------------------------------- detecção

def test_leitura_original_sem_titulos_ja_e_v2():
    """Sem "DANFSe v2.0" nem "TRIBUTAÇÃO IBS/CBS" na leitura de página
    inteira: antes caía na v1.0 (`danfse_nacional`)."""
    for t in (OCR_ORIGINAL_103, OCR_ORIGINAL_39):
        assert "DANFSe v2" not in t and "PRESTADOR / FORNECEDOR" not in t
        ex = SPPdfExtractor("x.pdf")
        ex.raw_text = t
        assert ex._detect_layout() == LAYOUT_NACIONAL_REFORMA
        assert ex._detect_layout_page(t) == LAYOUT_NACIONAL_REFORMA


def test_marca_v2_exige_valor_da_operacao():
    assert _eh_danfse_v2("VALOR DA OPERAÇÃO | SERVIÇO\nR$ 1,00\nCST/ cClassTrib")
    assert _eh_danfse_v2("VALOR DA OPERAÇÃO / SERVIÇO\nTotal do IBSICBS")
    # cClassTrib sozinho (sem o rótulo de valor exclusivo da v2.0) não basta.
    assert not _eh_danfse_v2("DANFSe v1.0\nCST/ cClassTrib\nValor do Serviço")


def test_celulas_trazem_titulos_canonicos():
    for t in (OCR_CELULAS_103, OCR_CELULAS_39):
        assert t.index("PRESTADOR / FORNECEDOR") < t.index("TOMADOR / ADQUIRENTE") \
            < t.index("SERVIÇO PRESTADO") < t.index("VALOR TOTAL DA NFS-e")


# ----------------------------------------------------------- nota nº 103

def test_103_identificacao(monkeypatch):
    nota = _n103(monkeypatch)
    assert nota.numero == "103"
    assert nota.codigo_verificacao == "29192072226159018000124000000000010326092224611770"
    assert nota.data_emissao.strftime("%Y-%m-%d %H:%M:%S") == "2026-09-04 10:18:12"
    # Convenção da v2.0: competência = data impressa completa.
    assert nota.competencia.strftime("%Y-%m-%d") == "2026-09-04"


def test_103_prestador_cnpj_do_rotulo_nao_cpf_da_razao(monkeypatch):
    p = _n103(monkeypatch).prestador
    # Antes: CPF 85910720570 tirado da razão social do MEI.
    assert p.cnpj_cpf == "26159018000124"
    # Confere com o emitente da chave de acesso (posições 10-23).
    assert OCR_CELULAS_103.count("2919207" + "2" + "2" + p.cnpj_cpf) >= 1
    assert p.razao_social == "DAVID SOUZA SANTANA JUNIOR 85910720570"
    e = p.endereco
    assert (e.logradouro, e.numero, e.bairro) == ("RUA BOCA DA MATA", "19", "PORTAO")
    assert (e.codigo_municipio, e.uf, e.cep) == ("2919207", "BA", "42700130")


def test_103_tomador(monkeypatch):
    t = _n103(monkeypatch).tomador
    assert t.cnpj_cpf == "04555283000350"
    assert t.razao_social == "BONI TRANSPORTES, LOGISTICA E COMERCIO LTDA."
    e = t.endereco
    assert (e.logradouro, e.numero, e.bairro) == ("MARIA QUITERIA", "263", "ITINGA")
    assert (e.codigo_municipio, e.uf, e.cep) == ("2919207", "BA", "42738205")


def test_103_servico_mei_e_valores(monkeypatch):
    nota = _n103(monkeypatch)
    assert nota.intermediario is None
    assert nota.servico_codigo == "0711"  # "Naclonal" no rótulo
    assert nota.discriminacao.startswith(
        "SERVIÇO DE MANUTENÇÃO EM LAVADORA KARCHER HD 585 O.S 8451. GARANTIA DE 90 DIAS.")
    assert nota.valores.valor_servicos == 706.0
    assert nota.valores.valor_liquido_nfse == 706.0
    assert not nota.valores.iss_retido
    xml = Abrasf201Transformer().transform(nota)
    xml = xml.decode("utf-8") if isinstance(xml, bytes) else str(xml)
    # "Optante - Microempreendedor Individua..." (truncado na grade).
    assert "<OptanteSimplesNacional>1</OptanteSimplesNacional>" in xml
    assert "<RegimeEspecialTributacao>5</RegimeEspecialTributacao>" in xml
    assert "<Intermediario>" not in xml
    assert "2927408" not in xml  # Salvador


# ------------------------------------------------------------ nota nº 39

def test_39_prestador_nunca_recebe_cnpj_da_boni(monkeypatch):
    p = _n39(monkeypatch).prestador
    assert p.cnpj_cpf == "46876522000152"
    assert "2919207" + "2" + "2" + p.cnpj_cpf in OCR_CELULAS_39
    assert p.razao_social == "SBS SOLUCOES INTEGRADAS DE SEGURANCA ELETRONICA II LTDA"
    assert p.inscricao_municipal == "10041979"
    e = p.endereco
    assert (e.logradouro, e.numero, e.bairro) == ("AVN PRAIA DE ITAPOAN", "131", "VILAS DO ATLANTICO")
    assert (e.codigo_municipio, e.uf, e.cep) == ("2919207", "BA", "42707650")
    assert p.email == "financeiro@sbsgrupo.com.br"


def test_39_tomador_e_sem_intermediario(monkeypatch):
    nota = _n39(monkeypatch)
    t = nota.tomador
    assert t.cnpj_cpf == "04555283000350"
    assert t.razao_social == "BONI TRANSPORTES, LOGISTICA E COMERCIO LTDA."
    assert (t.endereco.codigo_municipio, t.endereco.uf, t.endereco.cep) == ("2919207", "BA", "42738205")
    assert nota.intermediario is None


def test_39_codigo_99_vira_0000_com_aviso(monkeypatch):
    nota = _n39(monkeypatch)
    assert nota.servico_codigo == "0000"
    assert any("99.01.01" in a for a in nota.avisos)
    assert nota.discriminacao.startswith("CONTRATO Nº [TS BTLC 014/2024 SBS TEC")
    assert "COMPETÊNCIA: 09/2026" in nota.discriminacao
    assert nota.valores.valor_servicos == 660.51
    assert nota.valores.valor_liquido_nfse == 660.51
    assert nota.competencia.strftime("%Y-%m") == "2026-09"


# ------------------------------------------------- releitura de valor quebrado

def test_reler_valor_integro_nao_chama_ocr(monkeypatch):
    import pytesseract

    def _nao(*a, **k):
        raise AssertionError("valor íntegro não pode ser relido")
    monkeypatch.setattr(pytesseract, "image_to_string", _nao)
    seg = dict(t="04.555.283/0003-50", x0=10, x1=200, y0=10, y1=30, alt=20)
    assert SPPdfExtractor._danfse_v2_reler_valor_truncado(None, seg, 0.0) == "04.555.283/0003-50"
    seg = dict(t="07.11.02/-", x0=10, x1=200, y0=10, y1=30, alt=20)
    assert SPPdfExtractor._danfse_v2_reler_valor_truncado(None, seg, 0.0) == "07.11.02/-"


def test_reler_valor_truncado_so_aceita_forma_valida(monkeypatch):
    import pytesseract
    from PIL import Image

    img = Image.new("L", (400, 100), 255)
    seg = dict(t="6.876.522/0001-52", x0=50, x1=250, y0=40, y1=60, alt=20)
    # Releitura com DV inválido é rejeitada: fica o texto original.
    monkeypatch.setattr(pytesseract, "image_to_string", lambda *a, **k: "46.876.522/0001-53")
    assert SPPdfExtractor._danfse_v2_reler_valor_truncado(img, seg, 0.0) == "6.876.522/0001-52"
    monkeypatch.setattr(pytesseract, "image_to_string", lambda *a, **k: "| 46.876.522/0001-52")
    assert SPPdfExtractor._danfse_v2_reler_valor_truncado(img, seg, 0.0) == "46.876.522/0001-52"
    seg = dict(t="9.01.01/-", x0=50, x1=250, y0=40, y1=60, alt=20)
    monkeypatch.setattr(pytesseract, "image_to_string", lambda *a, **k: "99.01.01/-")
    assert SPPdfExtractor._danfse_v2_reler_valor_truncado(img, seg, 0.0) == "99.01.01/-"


# ------------------------------------------- colaterais da regressão em lote
# Textos REAIS de `_ocr_page` de outras DANFSe v2.0 do corpus que passaram a
# ser lidas como v2.0 (pipe "|" no rótulo de valor; "cClassTrib").

# "nfs 16.10.pdf" pág. 3 (foto): nota nº 2600000000944, RENATO ANDRE
# GIARETTON (Barreiras/BA) -> SÃO PEDRO CONSTRUTORA. Na main a página era lida
# como v1.0 e fundida à pág. 2 (nota nº 75 saía com os valores desta, e esta
# nota sumia). A chave do topo sai com lixo; a do rodapé, inteira.
OCR_RENATO_944 = 'Ei\nNota\nota Flical cle\nCHA\nE ha Serviço Eletrônica\n200320112332\nmiiarona 80186000 196280000000094428 1000 10220688\n280000000006 "E\nua\nRO DA DPS\nças\nTENTE DA NFS.E\nbh\n\nDANFSo v2.0\nDocumento Auxiliar da NFS-o\nobumento Avoilhar tha\nCOMPETÊNCIA DA NFS-E\n02/10/2026\nSÉRIE DA DPS\n70000\nhelio a E NFS-E\nGerad\n\nDATA E HORA DA EMISSÃO DA NFS-\nE\n02/10/2026 08:09:43\nDATA E HORA DA EMISSÃO DA DPS\n02/10/2026 08:09:43\nFINALIDADE\n\nMunicípio; Barreiras - BA\nA mierticidada desta NF S-a poda ser\nverificada pela leitura dente código OR ou\nconsulta da chave de acesso no portal an\nnacional da NFS -a\n\n! PRESTADOR / FORNECEDOR\nNome / Nome Empresarial\nRENATO ANDRE GIARETTON\nEndereço\nRua BÉLGICA, 211, CASA, Boa Sorte\nSimples Nacional na Data de Competência\nOptante - MEJEPP\n\n33.250.186/0001-96\nRegime de Apuração Tributária pelo SN\nRegime de apuração dos tributos\nfederais e municipal pelo SN\n\nindicador Municipaifinserição,\n000018899\nMunicipio / Sigia UF\nBarreiras / BA\nE-mail\nRENATOGIARETTONQHOTMAIL.COM\n\nO\n(77) 99993-0733\nCódigo IBGE (CEP\n2903201 / 47807-225\n\nTOMADOR DO SERVIÇO\nNome / Nome Empresarial\nSÃO PEDRO CONSTRUTORA LTDA\nEndereço\nRUA 554, QUADRA 28, LOTE 09, VILAS DO ATLANTICO\n\nPJTCPFI\n03.051.741/0001-90\n\nIndicador Municipal (inscrição)\nMunicípio / Sigla UF\nLauro de Freitas / BA\nE-mail\nso(Dsaopedroconstrutora.com.br\n\nCódigo IBGE (CEP\n2919207 / 42708-720\n\nDESTINATÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-o\n\nINTERMEDIÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-9\n\nSERVIÇO PRESTADO\nGuincho intramunicipal. guindaste e Içamento.\nDescrição do Serviço\nDIÁRIA DE GUINDATE R$5.500,00 HORAS DE MUNCK R$1.280,00 SERVIÇOS REALIZADOS EM 01/10/2026\nTRIBUT/ O MUNICIPAL (ISSQN)\nRegime Especial de Tributação do ISSQN\nNenhum\nBenefício Municipal\n-\nBC ISSQN\nR$ 6.760,00\n\nde Tributação Nacional / Municipal\n14.14.02/-\ndo ISSQN\nTipo\nOperação tributável\nTipo de Imunidade do ISSQN\n-\nCálculo do BM\nR$ 0,00\nAliquota Aplicada\n4,28%\n\nCódigo da NES\n106019000\ndo\nMunicípio 7 Sígia UF / Pais de |\nBarreiras / BA / BR\nSuspensão da Exigibilidade do ISSQN\nNão\nTotal Deduções/Reduções\nR$ 0,00\nRetenção do ISSQN\nNão Retido\n\nLocal da Prestação | Sígia UF / Pais\nBarreiras / BA / BR\nNúmero Processo Suspensão\nDesconto Incondicionado\nISSQN Apurado\nR$ 28933\n\nTRIBUTAÇÃO FEDERAL (EXCETO\ncBs)\nPIS - Débito Apuração Própria\n\nIRRF\nCOFINS - Débito Apuração Própria\n\nContribuição Previdenciária - Retido\nDescrição Contrib. Sociais - Retidas\n\nContribuições Sociais - Retidas\n=\n\nTRIBUTAÇÃO IBS/CBS\nExciusões e Reduções da Base de Cálculo\nR$ 289.33\nAliq. Efetiva Municipal - BS\n0,00%\nValor Total Apurado - IBS\nR$ 0,00\n\nCST/cClassTrib\nfia\nBase de Cálculo Após Exclusões e\nReduções\nR$ 0,00\nValor Apurado Municipal - IBS\nR$ 0,00\nAliquota - CBS\n0,00%\n\nIndicador de Operação | Código IBGE incidência / Município Incidência | Sígia UF\nefefs\nRed. Aliquota IBS | Red. Alíquota CBS\neli\nAlig. Efetiva Estadual - BS\n0,00%\nAlíquota Efetiva - CBS\n0,00%\n\nAliquota - IBS UF /IBS Mun\n0,00% / 0,00%\nValor Apurado Estadual - IBS\nR$ 0,00\nValor Total Apurado - CBS\nR$ 0,00\n\nVALOR TOTAL DANFSE |\nTotal das Retenções (ISSQN / Federais)\n\nVALOR DA OPERAÇÃO / SERVIÇO\nR$ 6.760,00\nVALOR LÍQUIDO DA NFS-9\nR$ 6.760,00\n\nDesconto Incondicionado\nTotal do IBS/CBS\nR$ 0,00\n\nDesconto Condicionado\nVALOR LÍQUIDO DA NFS-e + IBSICBS\nR$ 0,00\n\nINFORMAÇÕES COMPLEMENTARES\nInf. Cont: BOLETO COM VENCIMENTO EM 19/10/2026. | Totais Aproximados dos Tributos cfe, Lei nº 12.741/2012: Federais: -; Estaduais: -; Municipais: -;\nPor CMN tos\nDALIS-Lo Jd\n\nCantos Hentigfé Castro de Qineitã\nEngenheito Civil\nCREA 30.357-BA\nNº NFS-E / CHAVE NFS-E\n2600000000944 | 29032011233250186000196260000000094426100010220688'

# "nf 54.pdf" (foto, CamScanner): ULISSES SANTANA FILHO 79601839534 (MEI,
# Lauro de Freitas/BA) -> S.P. INCORPORADORA LTDA, R$ 2.000,00. "VALOR DA
# OPERAÇÃO | SERVIÇO" (barra lida "|"), "2919207 1 42.713-810", "Código do
# Tributação NaclonalMunicipal".
OCR_ULISSES_54 = 'Serviço eletrônica\nCHAVE DE ACESSO DA NFS-o\n29192072227019664000159000000000005426105796140537\n| NÚMERO DA NFS-o\n54\nNÚMERO DA DPS\n20\nEMITENTE DA NFS-e\nPrestador\n\nDANFSo v2.0\nDocumento Auxiliar da NFS-o\nCOMPETÊNCIA DA NFS-o\n15/10/2026\nSÉRIE DA DPS\n70000\nSITUAÇÃO DA NFS-o\nNFS-e MEI\n\nDATA E HORA DA EMISSÃO DA NF 8-9\n16/10/2026 11:01:12\nDATA E HORA DA EMISSÃO DA DPS\n16/10/2026 11:01:11\nFINALIDADE\n\nMunicípio: Lauro da Freitas - BA\nAmblento Gorador; 2\nTipo da Ambienta; 1\npela leitura dosto cídigo OR ou pela consulta da\nchava do acosso no portal nacional da NFS-o\n\nPRESTADOR / FORNECEDOR\nNome / Nomo Empresarial\nULISSES SANTANA FILHO 79601839534\nEndereço\nRUA JOSEBIAS DA SILVA, 28, PORTAO\nSimples Nacional na Data de Competência\nOptante - Microempreendedor Individua... -\n\nCNPJ [CPF /NIF\n27.019.664/0001-59\nRegime de Apuração Tributária pelo SN\n\nIndicador Municipal (Inscrição)\nMunicípio / Sigla UF\nLauro de Freitas / BA\nE-mail\nsantanafilhoulisses(Ogmail.com\n\nTolafona\n(71) 9908-1069\nCódigo IBGE | CEP\n2919207 1 42.713-810\n\nTOMADOR | ADQUIRENTE\nNome / Nome Empresarial\nS.P. INCORPORADORA LTDA\nEndereço\nJOSE PEDREIRA, 000041, EDIF CANDEAL\n\nCNPJ/CPF | NIF\n06.017.614/0001-62\nAL 41 LOJA 03, CANDEAL\n\nIndicador Municipal (Inscrição)\nMunicípio / Sigla UF\nSalvador / BA\nE-mail\nSPGSAOPEDROCONSTRUTORA.COM.BF\n\nBR\nTelefone\n(71) 3272-0733\nCódigo IBGE / CEP\n29.27408 / 40.296-260\n\n] JOSE PEDREIRA, 000041, EDIF CANDEAL 41 LOJA 03, CANDEAL\n\nDESTINATÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e\n\nINTERMEDIÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e\n\nSERVIÇO PRESTADO\nÀ Execução, por empreitada ou subempreitada, de obras de construção civil, hidráulica ou elétrica e de outras obras semelhantes, inclusive sondagem, perfuração de poços...\nDescrição do Serviço\nPrestação de serviços de construção civil\n\nCódigo do Tributação NaclonalMunicipal\n07.02.02 /-\n\nCódigo da NBS\n1.0102.20.00\n\nLocal da Prestação / Sigla UF / País\nSalvador / BA / -\n\nTRIBUTAÇÃO MUNICIPAL (ISSQN)\n: BCISSQN\n\nTipo de Tributação do ISSQN\nOperação Tributável\nAliquota Aplicada\n\nMunicípio / Sigla UF | País de Incidência do ISSQN\nSalvador / BA / -\nRetenção do ISSQN\nNão Retido\n\nISSQN Apurado\n:\n\nTRIBUTAÇÃO FEDERAL (EXCETO CBS)\n| PIS - Débito Apuração Própria\n\n) IRRF\nCOFINS - Débito Apuração Própria\n\nContribuição Previdenciária - Retida\nDescrição Contrib. Sociais - Retidas\n\nContribuições Sociais - Ratidas\n\nTRIBUTAÇÃO IBS / CBS\nExclusões e Reduções da Base de Cálculo\nR$ 0,00\nAliq. Efetiva Municipal - IBS\nValor Total Apurado - IBS\n\nCSTIcClassTrib\n-1-\nBase de Cálculo Após Exclusões e Reduções\nValor Apurado Municipal - IBS\nAlíquota - CBS\n\nIndicador de Operação / Código IBGE Incidência | Município Incldôncia / Sigla UF\n=[=1-1-\nRed. Aliquota IBS | Red. Aliquota CBS\najaça\nAlig. Efetiva Estadual - IBS\nAlíquota Efetiva - CBS\n\nAlíquota - IBS UF /IBS Mun\nE\nValor Apurado Estadual -IBS\nValor Total Apurado - CBS\n\nVALOR TOTAL DA NFS-e\nTotal das Retenções (ISSQN | Federais)\n\nVALOR DA OPERAÇÃO | SERVIÇO\nR$ 2.000,00\nVALOR LÍQUIDO DA NFS-o\nR$ 2.000,00\n\nDesconto Incondicionado\nTotal do IBSICBS\nR$ 0,00\n\nDesconto Condicionado\nVALOR LÍQUIDO DA NFS-a + IBS/CBS\nR$000\n\nINFORMAÇÕES COMPLEMENTARES\nTotais aproximados dos Tributos cfe. Lei nº 12.741/2012: Federais: -; Estaduais: -; Municipais: -;\n\nE ASSINATURA\nIDENTIFICAÇÃO\n\nNº NFS-e / CHAVE NFS-e\n\nDigitalizado com CamScanner'


def test_renato_numero_e_chave_pelo_rodape_autoverificado(monkeypatch):
    nota = _parse(monkeypatch, OCR_RENATO_944, "dummy_v2_renato_944.pdf")
    assert nota.numero == "2600000000944"
    assert nota.codigo_verificacao == "29032011233250186000196260000000094426100010220688"
    assert nota.prestador.cnpj_cpf == "33250186000196"
    assert (nota.prestador.endereco.codigo_municipio, nota.prestador.endereco.cep) == ("2903201", "47807225")
    assert nota.servico_codigo == "1414"
    assert nota.valores.valor_servicos == 6760.0


def test_chave_rodape_exige_numero_igual_ao_da_chave():
    ex = SPPdfExtractor("x.pdf")
    ex.raw_text = "Nº NFS-E / CHAVE NFS-E\n2600000000945 |29032011233250186000196260000000094426100010220688"
    assert ex._danfse_chave_rodape_confirmada() is None


def test_ulisses_valor_com_pipe_e_ibge_cep_com_barra_lida_1(monkeypatch):
    nota = _parse(monkeypatch, OCR_ULISSES_54, "dummy_v2_ulisses_54.pdf")
    assert nota.valores.valor_servicos == 2000.0
    assert nota.valores.valor_liquido_nfse == 2000.0
    p = nota.prestador
    assert p.cnpj_cpf == "27019664000159"
    assert (p.endereco.codigo_municipio, p.endereco.cep) == ("2919207", "42713810")
    # O IBGE da linha "Código IBGE / CEP" não é Inscrição Municipal.
    assert not p.inscricao_municipal and not nota.tomador.inscricao_municipal
    assert nota.servico_codigo == "0702"
    assert nota.discriminacao == "Prestação de serviços de construção civil"
