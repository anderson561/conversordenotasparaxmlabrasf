# -*- coding: utf-8 -*-
r"""DANFSe v2.0 emitida pelo GissOnline (Município de Jundiaí/SP), nota real
nº 42, YANKATU DESIGN ARTE E PROJETOS CULTURAIS LTDA (Jundiaí/SP, Simples
Nacional) -> NAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA (São
Paulo/SP), decoração e design de interiores (7.11.01 / 366), R$ 4.800,00.
PDF DIGITAL de 1 página (`NF 042 - Tidelli.pdf`, arquivo real do usuário,
pasta 092026).

`RAW_DIGITAL` é o retorno REAL e verbatim de `extract_text()` (pdfminer) no
PDF original, via `repr()`.

Diferenças desta variante em relação à DANFSe v2.0 nacional já suportada
(`LAYOUT_NACIONAL_REFORMA`): sem chave de acesso de 50 dígitos (rótulo
vazio; o rodapé traz "42 / JGRENG0TO"); bloco "EMITENTE DA NFS-E" com o
CNPJ ANTES do título "DANFSe v2.0"; cabeçalhos "PRESTADOR" (sem
"/ FORNECEDOR"), "DESTINATÁRIO DA OPERAÇÃO" e "INTERMEDIÁRIO DO SERVIÇO"
(vazio); "INSCRIÇÃO MUNICIPAL" em vez de "Indicador Municipal
(Inscrição)"; "CÓDIGO IBGE / CEP" só com o CEP; valores sem "R$" e
alíquota sem "%"; "ISSQN APURADO" em branco (Simples Nacional).

Defeitos do XML gerado antes do fix (conferidos contra a imagem renderizada
da página): a página única virava DUAS notas (o split de multi-nota por
página cortava no título "DANFSe v2.0", porque o preâmbulo já trazia o CNPJ
do emitente); na nota principal ValorServicos 0,00, prestador "Prestador
Não Identificado", tomador com o telefone/e-mail do prestador, município
caindo em fallback, item 03115 e discriminação genérica."""
import os

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_NACIONAL_REFORMA
from src.transformers.abrasf_transformer import Abrasf201Transformer

RAW_DIGITAL = "CHAVE DE ACESSO DA NFS-E\n\nNÚMERO DA NFS-E\n42\n\nNÚMERO DA DPS\n\nCÓDIGO DE VERIFICAÇÃO\nJGRENG0TO\n\nDANFE EMITIDO POR (NOME DO SISTEMA/VERSÃO)\nGissOnline\n\nEMITENTE DA NFS-E\n\nCNPJ / CPF / NIF\n24.451.291/0001-00\n\nDANFSe v2.0\nDocumento Auxiliar da NFS-e\n\nMUNICÍPIO:\n\nAMBIENTE GERADOR:\n\nTIPO DE AMBIENTE:\n\nMunicípio de Jundiaí\n\nGissOnline\n\nPRODUÇÃO\n\nCOMPETÊNCIA DA NFS-E\n09/2026\n\nSÉRIE DA DPS\n\nDATA E HORA DA EMISSÃO DA NFS-E\n29/09/2026 15:14:14\n\nDATA E HORA DA EMISSÃO DA DPS\n29/09/2026 15:14:14\n\nRPS\n\nSÉRIE RPS\n\nTIPO RPS\n\nA autenticidade desta NFS-e pode ser verificada\npela leitura deste código QR ou pela consulta da\nchave de acesso no portal nacional da NFS-e\n\nINSCRIÇÃO MUNICIPAL\n149944\n\nTELEFONE\n(11)94019-7077\n\nNOME / NOME EMPRESARIAL\nYANKATU DESIGN ARTE E PROJETOS CULTURAIS LTDA\n\nENDEREÇO\nSem tipo de logradouro Professor Orlando Vicente D'Angieri, 175 -  - Chácara Malota\n\nMUNICÍPIO / SIGLA UF\nJUNDIAI/SP\n\nE-MAIL\neduardocolombo.contador@gmail.com\n\nCÓDIGO IBGE / CEP\n13211540\n\nSIMPLES NACIONAL NA DATA DE COMPETÊNCIA\nSim\n\nREGIME DE APURAÇÃO TRIBUTÁRIA PELO SN\nSimples Nacional\n\nREGIME REGULAR DO IBS/CBS\n\nPRESTADOR\n\nCNPJ / CPF / NIF\n24.451.291/0001-00\n\nINSCRIÇÃO MUNICIPAL\n149944\n\nTELEFONE\n(11)94019-7077\n\nNOME / NOME EMPRESARIAL\nYANKATU DESIGN ARTE E PROJETOS CULTURAIS LTDA\n\nENDEREÇO\nSem tipo de logradouro Professor Orlando Vicente D'Angieri, 175 -  - Chácara Malota\n\nMUNICÍPIO / SIGLA UF\nJUNDIAI/SP\n\nE-MAIL\neduardocolombo.contador@gmail.com\n\nCÓDIGO IBGE / CEP\n13211540\n\nTOMADOR / ADQUIRENTE\n\nCNPJ / CPF / NIF\n16.699.869/0002-97\n\nNOME / NOME EMPRESARIAL\nNAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA\n\nENDEREÇO\nAlameda Gabriel Monteiro da Silva, 1480 - casa terrea - Jardim América\n\nDESTINATÁRIO DA OPERAÇÃO\n\nCNPJ / CPF / NIF\n16.699.869/0002-97\n\nNOME / NOME EMPRESARIAL\nNAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA\n\nENDEREÇO\nAlameda Gabriel Monteiro da Silva, 1480 - casa terrea - Jardim América\n\nINSCRIÇÃO MUNICIPAL\n\nINSCRIÇÃO MUNICIPAL\n\nMUNICÍPIO / SIGLA UF\nSAO PAULO/SP\n\nE-MAIL\nLORENA@NAUTICAMOVEIS.COM\n\nMUNICÍPIO / SIGLA UF\nSAO PAULO/SP\n\nE-MAIL\nLORENA@NAUTICAMOVEIS.COM\n\nTELEFONE\n(71)3355-2526\n\nTELEFONE\n(71)3355-2526\n\nCÓDIGO IBGE / CEP\n01442001\n\nCÓDIGO IBGE / CEP\n01442001\n\nINTERMEDIÁRIO DO SERVIÇO\n\nCNPJ / CPF / NIF\n\nNOME / NOME EMPRESARIAL\n\nENDEREÇO\n\nSERVIÇO PRESTADO\n\nINSCRIÇÃO MUNICIPAL\n\nTELEFONE\n\nMUNICÍPIO / SIGLA UF\n\nCÓDIGO IBGE / CEP\n\nE-MAIL\n\nCÓDIGO DE TRIBUTAÇÃO NACIONAL / MUNICIPAL\n7.11.01 / 366\n\nCÓDIGO DA NBS\n1.1409.11.00\n\nLOCAL DA PRESTAÇÃO / SIGLA UF / PAÍS\nJUNDIAI - SP\n\nDESCRIÇÃO DO CÓDIGO DE TRIBUTAÇÃO NACIONAL / MUNICIPAL\nDECORAÇÃO E DESIGN INTERIORES\n\nDESCRIÇÃO DO SERVIÇO\nprestação de serviços de decoração\nreferente ao pedido 1720502 Rafaella.\ndados bancários:     Banco Inter 077    Ag 0001-9   C/C 4303520-5\n\nTIPO TRIBUTAÇÃO (ISSQN)\n\nTIPO DE TRIBUTAÇÃO DO ISSQN\n1-Exigível\n\nREGIME ESPECIAL DE TRIBUTAÇÃO DO ISSQN\n0-Nenhum\n\nTIPO DE IMUNIDADE DO ISSQN\n\nSUSPENSÃO DA EXIGIBILIDADE DO ISSQN\n\nNÚMERO PROCESSO SUSPENSÃO\n\nMUNICÍPIO / SIGLA UF / PAÍS DE INCIDÊNCIA DO ISSQN\nJUNDIAI - SP\n\nBENEFÍCIO MUNICIPAL\n\nCÁLCULO DO BM\n\nTOTAL DEDUÇÕES/REDUÇÕES\n0,00\n\nDESCONTO INCONDICIONADO\n0,00\n\nBC ISSQN\n4.800,00\n\nALÍQUOTA APLICADA\n5.00\n\nRETENÇÃO DO ISSQN\nNão\n\nISSQN APURADO\n\nTRIBUTAÇÃO FEDERAL (EXCETO CBS)\n\nIRRF\n0,00\n\nPIS - DÉBITO APURAÇÃO PRÓPRIA\n0,00\n\nTRIBUTAÇÃO IBS / CBS\n\nCST / CCLASSTRIB\n\nCONTRIBUIÇÃO PREVIDENCIÁRIA - RETIDA\n0,00\n\nCOFINS - DÉBITO APURAÇÃO PRÓPRIA\n0,00\n\nCONTRIBUIÇÕES SOCIAIS - RETIDAS\n0,00\n\nDESCRIÇÃO CONTRIB. SOCIAIS - RETIDAS\n\nINDICADOR DE OPERAÇÃO / CÓDIGO IBGE INCIDÊNCIA / MUNICÍPIO INCIDÊNCIA / SIGLA UF\n100301\n\nEXCLUSÕES E REDUÇÕES DA BASE DE CÁLCULO\n\nBASE DE CÁLCULO APÓS EXCLUSÕES E REDUÇÕES\n\nRED. ALÍQUOTA IBS / RED. ALÍQUOTA CBS\n\nALÍQUOTA - IBS UF / IBS MUN\n\nALÍQ. EFETIVA MUNICIPAL - IBS\n\nVALOR APURADO MUNICIPAL - IBS\n\nALÍQ. EFETIVA ESTADUAL - IBS\n\nVALOR APURADO ESTADUAL - IBS\n\nVALOR TOTAL APURADO - IBS\n\nALÍQUOTA - CBS\n\nALÍQ. EFETIVA / TOTAL CBS\n\nVALOR TOTAL APURADO - CBS\n\nVALOR TOTAL DA NFS-E\n\nVALOR DA OPERAÇÃO / SERVIÇO\n4.800,00\n\nTOTAL DAS RETENÇÕES (ISSQN / FEDERAIS)\n0,00\n\nTOTAIS APROXIMADOS DOS TRIBUTOS\n\nFEDERAIS (%)\n0.00%\n\nINFORMAÇÕES COMPLEMENTARES\n\nDESCONTO CONDICIONADO\n0,00\n\nTOTAL DO IBS/CBS\n0,00\n\nESTADUAIS (%)\n0.00%\n\nDESCONTO INCONDICIONADO\n0,00\n\nVALOR LÍQUIDO DA NFS-E + IBS/CBS\n4.800,00\n\nMUNICIPAIS (%)\n0.00%\n\nIMÓVEL (DADOS DO BLOCO OBRA)\n\nOBRA (DADOS DO BLOCO OBRA)\n\nEVENTO (DADOS DO BLOCO OBRA)\n\nINFOCOMPL (DADOS DO BLOCO OBRA)\n\nINFORMAÇÕES ESPECÍFICAS PARA DADOS ADICIONAIS DO MUNICÍPIO QUANDO EMITIDO PELO MUNICÍPIO COM BASE EM LEIAUTE PRÓPRIO\n\nDATA CIENTIFICAÇÃO:\n\nIDENTIFICAÇÃO E ASSINATURA\n\nNº NFS-E / CHAVE NFS-E\n42 / JGRENG0TO\n\n\x0c"


def _parse_todas(monkeypatch, raw, nome="dummy_nf42_gissonline.pdf"):
    caminho = f"tests/{nome}"
    os.makedirs("tests", exist_ok=True)
    with open(caminho, "wb") as f:
        f.write(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: raw)
    try:
        return SPPdfExtractor(caminho).parse_multiple()
    finally:
        if os.path.exists(caminho):
            os.remove(caminho)


def _parse(monkeypatch, raw=None):
    notas = _parse_todas(monkeypatch, RAW_DIGITAL if raw is None else raw)
    assert len(notas) == 1
    return notas[0]


def test_layout_detectado_e_reforma_variante_gissonline():
    ex = SPPdfExtractor("x.pdf")
    ex.raw_text = RAW_DIGITAL
    assert ex._detect_layout() == LAYOUT_NACIONAL_REFORMA
    assert ex._detect_layout_page(RAW_DIGITAL) == LAYOUT_NACIONAL_REFORMA
    assert ex._reforma_variante_gissonline()


def test_pagina_unica_nao_vira_duas_notas(monkeypatch):
    """O preâmbulo com o CNPJ do EMITENTE antes do título "DANFSe v2.0" não
    pode ser fatiado como nota própria (antes: notas "42" e "09")."""
    notas = _parse_todas(monkeypatch, RAW_DIGITAL)
    assert [n.numero for n in notas] == ["42"]


def test_split_preserva_duas_danfse_coladas_na_mesma_pagina(monkeypatch):
    """Não regressão do split de multi-nota por página: esta nota seguida,
    na MESMA página, de uma DANFSe v2.0 nacional (texto real da nota nº 73,
    título no topo) continua virando 2 notas — o trecho antes do 2º título
    traz o bloco do TOMADOR da 1ª."""
    from tests.test_danfse_reforma_nota73_wmk_cnpj_sem_pontuacao import RAW_DIGITAL as RAW_73
    colado = RAW_DIGITAL.rstrip("\x0c") + "\n" + RAW_73.split("\x0c")[0]
    notas = _parse_todas(monkeypatch, colado)
    assert [n.numero for n in notas] == ["42", "73"]
    assert notas[0].prestador.cnpj_cpf == "24451291000100"
    assert notas[1].prestador.cnpj_cpf == "08058923000106"


def test_cabecalho_numero_datas_e_codigo_verificacao(monkeypatch):
    nota = _parse(monkeypatch)
    assert nota.numero == "42"
    assert nota.codigo_verificacao == "JGRENG0TO"
    assert nota.data_emissao.strftime("%Y-%m-%dT%H:%M:%S") == "2026-09-29T15:14:14"
    assert nota.competencia.strftime("%Y-%m-%d") == "2026-09-01"


def test_prestador_do_bloco_prestador(monkeypatch):
    p = _parse(monkeypatch).prestador
    assert p.cnpj_cpf == "24451291000100"
    assert p.razao_social == "YANKATU DESIGN ARTE E PROJETOS CULTURAIS LTDA"
    assert p.inscricao_municipal == "149944"
    assert p.telefone == "(11)94019-7077"
    assert p.email == "eduardocolombo.contador@gmail.com"
    e = p.endereco
    # "Sem tipo de logradouro" é filler do gerador, não parte do nome.
    assert e.logradouro == "Professor Orlando Vicente D'Angieri"
    assert e.numero == "175"
    assert e.complemento is None
    assert e.bairro == "Chácara Malota"
    assert e.municipio == "JUNDIAI"
    assert e.uf == "SP"
    assert e.codigo_municipio == "3525904"  # Jundiaí/SP (API IBGE)
    assert e.cep == "13211540"


def test_prestador_cai_no_emitente_quando_bloco_prestador_ausente(monkeypatch):
    """Sem o bloco PRESTADOR, o EMITENTE é o prestador."""
    i = RAW_DIGITAL.index("\nPRESTADOR\n")
    j = RAW_DIGITAL.index("TOMADOR / ADQUIRENTE")
    sem_prestador = RAW_DIGITAL[:i] + "\n\n" + RAW_DIGITAL[j:]
    p = _parse(monkeypatch, sem_prestador).prestador
    assert p.cnpj_cpf == "24451291000100"
    assert p.razao_social == "YANKATU DESIGN ARTE E PROJETOS CULTURAIS LTDA"
    assert p.endereco.codigo_municipio == "3525904"


def test_tomador_nao_confunde_com_prestador_nem_destinatario(monkeypatch):
    nota = _parse(monkeypatch)
    t = nota.tomador
    assert t.cnpj_cpf == "16699869000297"
    assert t.cnpj_cpf != nota.prestador.cnpj_cpf
    assert t.razao_social == "NAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA"
    assert not t.inscricao_municipal  # impresso em branco
    assert t.telefone == "(71)3355-2526"
    assert t.email == "LORENA@NAUTICAMOVEIS.COM"
    e = t.endereco
    assert e.logradouro == "Alameda Gabriel Monteiro da Silva"
    assert e.numero == "1480"
    assert e.complemento == "casa terrea"
    assert e.bairro == "Jardim América"
    assert e.municipio == "SAO PAULO"
    assert e.uf == "SP"
    assert e.codigo_municipio == "3550308"
    assert e.cep == "01442001"
    assert nota.intermediario is None


def test_valores_simples_nacional_issqn_apurado_em_branco(monkeypatch):
    nota = _parse(monkeypatch)
    v = nota.valores
    assert v.valor_servicos == pytest.approx(4800.00)
    assert v.base_calculo == pytest.approx(4800.00)
    assert v.aliquota == pytest.approx(0.05)
    # "ISSQN APURADO" vem em branco: nunca fabricar 240,00 (BC x alíquota).
    assert v.valor_iss == 0.0
    assert v.iss_retido is False
    assert v.valor_iss_retido == 0.0
    assert v.valor_deducoes == 0.0
    assert (v.valor_ir, v.valor_inss, v.valor_pis, v.valor_cofins, v.valor_csll) == (0, 0, 0, 0, 0)
    assert v.valor_contribuicoes_sociais_retidas == 0.0
    assert v.valor_liquido_nfse == pytest.approx(4800.00)
    assert nota.optante_simples_nacional is True
    assert any("ISSQN APURADO" in a for a in nota.avisos)
    assert any("CNAE" in a for a in nota.avisos)


def test_servico_codigo_discriminacao_e_incidencia(monkeypatch):
    nota = _parse(monkeypatch)
    assert nota.servico_codigo == "0711"
    assert not nota.codigo_cnae
    assert nota.discriminacao == (
        "prestação de serviços de decoração referente ao pedido 1720502 Rafaella. "
        "dados bancários: Banco Inter 077 Ag 0001-9 C/C 4303520-5")


def test_xml_final(monkeypatch):
    xml = Abrasf201Transformer().transform(_parse(monkeypatch))
    for trecho in (
        "<Numero>42</Numero>",
        "<CodigoVerificacao>JGRENG0TO</CodigoVerificacao>",
        "<DataEmissao>2026-09-29T15:14:14</DataEmissao>",
        "<Competencia>2026-09-01</Competencia>",
        "<ValorServicos>4800.00</ValorServicos>",
        "<BaseCalculo>4800.00</BaseCalculo>",
        "<Aliquota>0.05</Aliquota>",
        "<ValorIss>0.00</ValorIss>",
        "<IssRetido>2</IssRetido>",
        "<ValorLiquidoNfse>4800.00</ValorLiquidoNfse>",
        "<Cnpj>24451291000100</Cnpj>",
        "<Cnpj>16699869000297</Cnpj>",
        "<ItemListaServico>0711</ItemListaServico>",
        "<CodigoTributacaoMunicipio>0711</CodigoTributacaoMunicipio>",
        "<CodigoCnae>0000000</CodigoCnae>",
        "<MunicipioIncidencia>3525904</MunicipioIncidencia>",
        "<OptanteSimplesNacional>1</OptanteSimplesNacional>",
        "<CodigoMunicipio>3550308</CodigoMunicipio>",
    ):
        assert trecho in xml, trecho
    assert "2927408" not in xml  # nunca o default Salvador/BA
    assert "Não Identificado" not in xml


def test_danfse_v2_nacional_nao_e_tratada_como_gissonline():
    """Não regressão de detecção: a variante GissOnline é marcada pela
    ESTRUTURA (cabeçalho "PRESTADOR" sozinho / "INSCRIÇÃO MUNICIPAL"), então
    uma DANFSe v2.0 do leiaute nacional segue no caminho já validado."""
    from tests.test_danfse_reforma_nota73_wmk_cnpj_sem_pontuacao import RAW_DIGITAL as RAW_73
    ex = SPPdfExtractor("x.pdf")
    ex.raw_text = RAW_73
    assert ex._detect_layout() == LAYOUT_NACIONAL_REFORMA
    assert not ex._reforma_variante_gissonline()
