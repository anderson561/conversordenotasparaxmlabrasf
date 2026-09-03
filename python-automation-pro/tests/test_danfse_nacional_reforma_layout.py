# -*- coding: utf-8 -*-
r"""Layout `danfse_nacional_reforma` — DANFSe **v2.0**, o novo modelo do Portal
Nacional da NFS-e pós-reforma tributária (seções TRIBUTAÇÃO IBS/CBS, CST/
cClassTrib, "VALOR LÍQUIDO DA NFS-e + IBS/CBS").

Achado real (2026-09-03): nota nº 11, UNICA SEGURANCA PATRIMONIAL LTDA
(Lauro de Freitas/BA) -> CONDOMINIO EDIFICIO TK TOWER (Salvador/BA),
R$ 12.353,68 de vigilância patrimonial armada. PDF de 2 páginas, escaneado
(a nota em si é a página 2, via OCR); a página 1 é o demonstrativo de
faturamento do prestador.

A nota era capturada pelo detector genérico `DANFSe v\d` e roteada para o
parser da v1.0 (`LAYOUT_NACIONAL`), cujo vocabulário de rótulos é outro.
Consequências reais, todas cobertas aqui:

1. **Valor**: a v2.0 não tem "Valor do Serviço"; tem "BC ISSQN" e "VALOR DA
   OPERAÇÃO / SERVIÇO". Sem achar o rótulo antigo, o parser copiava o VALOR
   LÍQUIDO -> ValorServicos saía 9.817,41 em vez de 12.353,68. Regra definida
   pelo usuário: quando BC ISSQN e VALOR DA OPERAÇÃO / SERVIÇO divergem,
   prevalece o VALOR DA OPERAÇÃO / SERVIÇO (o BC fica só na BaseCalculo).
2. **Retenção do ISSQN**: a v1.0 tinha a coluna "ISSQN Retido: Sim/Não"; a
   v2.0 diz "Retenção do ISSQN: Retido pelo Tomador" -> a nota saía com
   IssRetido=2 (não retido) e sem <ValorIssRetido>, invertendo o sinal
   contábil de um ISS de R$ 617,68 efetivamente retido pelo tomador.
   As demais retenções (INSS e Contribuições Sociais) já vinham certas: os
   rótulos não mudaram da v1.0 para a v2.0, então a extração entregue no
   PR #44 (`test_danfse_nacional_retencoes_federais.py`) seguiu valendo.
3. **Entidades**: a v2.0 renomeou os blocos ("PRESTADOR / FORNECEDOR",
   "TOMADOR / ADQUIRENTE") e despeja as colunas da direita (Inscrição /
   Município / E-mail / Telefone / Código IBGE-CEP) DEPOIS dos dois blocos,
   em pares prestador-depois-tomador. O tomador saía com o e-mail, o telefone
   e o "CEP" (na verdade o código IBGE) do PRESTADOR, e com "LOTE 02"
   (complemento) no lugar do bairro PITUBA.
4. **Nota-fantasma**: no OCR da v2.0 o título "DANFSe v2.0" cai a ~230
   caracteres do início da página — passando do `DANFSE_HEADER_MIN_OFFSET`
   que protegia a v1.0 —, então a página única era fatiada em 2 notas.
5. **Intermediário fantasma**: "INTERMEDIÁRIO DA OPERAÇÃO NÃO IDENTIFICADO"
   (v1.0: "... DO SERVIÇO ...") virava um <Intermediario> com razão social
   "DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e".

Texto OCR REAL (Tesseract) do PDF, preservado verbatim via repr() — inclusive
os erros de leitura ("unicaDunicaseguranca.com" e "nf(Dtkpatrimonial.com.br"
para o "@", "R$617,68" sem espaço, o número da nota lido como uma aspa solta).
"""
import os
import pytest
from src.extractors.pdf_extractor import (
    SPPdfExtractor, LAYOUT_NACIONAL, LAYOUT_NACIONAL_REFORMA,
)

MOCK_OCR = 'OJÚNICA\n\nAo\nCONDOMINIO EDIFICIO TK TOWER\n\nREF: DEMONSTRATIVO DE FATURAMENTO\n\nFATURA N.º 2026011\nAT: Srº Catia\n\nDEMONSTRATIVO\n\nQuantitativo\n\nValor unitário) Valor Total\nde postos\n\nDescrição\nPV 12H 12X36\n\nR$ 7.127,12 |R$ 12.353,68\n\nValor Total faturado R$ 12.353,68\nValor Total faturado 06 a 31/07/2026 R$ 12.353,68\n\n(B) CUSTO COM TRANSPORTE R$ 134,26\n(C) VALOR TOTAL (A-B) R$ 12.219,42\n(D) 11% PREVIDÊNCIA SOCIAL = (C X 11%) R$ 1.344,14\n(E) 5% REF. A RETENÇÃO DO ISS = A X 5%) R$ 617,68\n(F) 1% IRRF (A X 1%) R$ 0,00\n(G) 4.65% MP N.º 135 (A X 4,65%) R$ 574,45\n(G) VALOR TOTAL = (A-D-E-F-G) R$ 9.817,41\n\nTOTAL LIQUIDO A RECEBER R$ 9.817,41\n\nLauro de Freitas (Ba), 05 de agosto de 2026.\nBárbara Costa / Assistente Financeiro\n\nAtenciosamente,\n\nRua Jardim Ipanema, nº 500 - Lotes 39 e 40 — Pitangueiras - Lauro de Freitas/ Bahia - CEP: 42.701-830  Tel.: (71) 3378-9186\nE-mail: unicaQDunicaseguranca.com\n\n\x0c\nServiço eletrônica\n\nCHAVE DE ACESSO DA NFS-e\n2919207220303769800010800000000000112608 1682049850\n\nNÚMERO DA NFS-e COMPETÊNCIA DA NFS-e\n“ 03/08/2026\n\nNÚMERO DA DPS SÉRIE DA DPS\n1 70000\n\nEMITENTE DA NFS-e SITUAÇÃO DA NFS-e\nPrestador 101\n\nDANFSe v2.0\nDocumento Auxiliar da NFS-e\n\nDATA E HORA DA EMISSÃO DA NFS-e\n05/08/2026 16:11:07\n\nDATA E HORA DA EMISSÃO DA DPS\n05/08/2026 16:11:07\n\nFINALIDADE\n\nMunicípio: Lauro de Freitas - BA\nAmbiente Gerador: 2\n\npela leitura deste código QR ou pela consulta da\nchave de acesso no portal nacional da NFS-e\n\nPRESTADOR / FORNECEDOR CNPJ/CPF /NIF\n03.037.698/0001-08\n\nNome / Nome Empresarial\n\nUNICA SEGURANCA PATRIMONIAL LTDA\n\nEndereço\nRUA JARDIM IPANEMA, 500, PORTAO, PITANGUEIRAS\n\nSimples Nacional na Data de Competência\nNão optante r\n\nTOMADOR / ADQUIRENTE CNPJ/CPF /NIF\n07.834.816/0001-60\n\nNome / Nome Empresarial\nCONDOMINIO EDIFICIO TK TOWER\n\nEndereço\nPROFESSOR MAGALHAES NETO, 1856, LOTE 02, PITUBA\n\nRegime de Apuração Tributária pelo SN\n\nIndicador Municipal (Inscrição)\n10000480\n\nMunicípio / Sigla UF\nLauro de Freitas /BA\n\nE-mail\nunicaDunicaseguranca.com\n\nIndicador Municipal (Inscrição)\nMunicípio / Sigla UF\n\nSalvador / BA\n\nE-mail\nnf(Dtkpatrimonial.com.br\n\nTelefone\n(71) 3378-9186\n\nCódigo IBGE / CEP\n29.19207 / 42.701-830\n\nTelefone\n\n(71) 98806-9829\nCódigo IBGE / CEP\n29.27408 / 41.810-012\n\nDESTINATÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e\n\nINTERMEDIÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e\n\nSERVIÇO PRESTADO\n11.02.01/-\n\nVigilância, segurança ou monitoramento de bens, pessoas e semoventes.\nDescrição do Serviço\n\nCódigo de Tributação Nacional/Municipal\n\nCódigo da NBS\n1.1802.50.00\n\nLocal da Prestação / Sigla UF / País\nSalvador / BA / -\n\nVALOR REFERENTE AOS SERVIÇOS DE VIGILÂNCIA PATRIMONIAL ARMADA SENDO: (01 PV 12 HORA NOTURNO) EXECUTADOS NO PREDIO DO EDIFICIO TK TOWER\nLOCALIZADO NA AV. PROF. MAGALHAES NETO , 1856 PITUBA SSA BA NO PERÍODO DE 06 A 31.07.2026.\n\nCUSTO C TRANSPORTE R$ 154,92\nCUSTO C MÃO DE OBRA R$ 14.099,34\n\nPAGAMENTO NO BANCO ITAÚ AG. 5430 C.C 60000-6\nVALOR APROXIMADO DOS IMPOSTOS = 30,65% = R$ 4.368,93\n\nTRIBUTAÇÃO MUNICIPAL (ISSQN) Tipo de Tributação do ISSQN\n\nOperação Tributável\n\nBC ISSQN Alíquota Aplicada\nR$ 12.353,68 5,00 %\n\nMunicípio / Sigla UF / País de Incidência do ISSQN\n\nSalvador / BA / -\n\nRetenção do ISSQN\nRetido pelo Tomador\n\nISSQN Apurado\nR$617,68\n\nTRIBUTAÇÃO FEDERAL (EXCETO CBS) | IRRF\n\nPIS - Débito Apuração Própria COFINS - Débito Apuração Própria\nR$ 80,30 R$ 370,61\n\nContribuição Previdenciária - Retida\nR$ 1.344,14\n\nDescrição Contrib. Sociais - Retidas\n3-PIS/COFINS/CSLL Retidos\n\nContribuições Sociais - Retidas\nR$574,45\n\nTRIBUTAÇÃO IBS/CBS CST/ cClassTrib\n2\n\nExclusões e Reduções da Base de Cálculo\nR$ 1.068,59 -\nAliq. Efetiva Municipal - IBS Valor Apurado Municipal - IBS\n\nValor Total Apurado - IBS Alíquota - CBS\n\nVALOR TOTAL DA NFS-e VALOR DA OPERAÇÃO / SERVIÇO\nR$ 12.353,68\n\nVALOR LÍQUIDO DA NFS-e\nR$ 9.817,41\n\nTotal das Retenções (ISSQN / Federais)\nR$ 2.536,27\n\nBase de Cálculo Após Exclusões e Reduções\n\nIndicador de Operação / Código IBGE Incidência / Município Incidência / Sigla UF\n\n=[=d=d-\n\nRed. Alíquota IBS / Red. Alíquota CBS\nEA\n\nAliq. Efetiva Estadual - IBS\n\nAlíquota Efetiva - CBS\n\nDesconto Incondicionado\n\nTotal do IBS/CBS\nR$ 0,00\n\nAlíquota - IBS UF /IBS Mun\nEfe\nValor Apurado Estadual - IBS\n\nValor Total Apurado - CBS\n\nDesconto Condicionado\n\nVALOR LÍQUIDO DA NFS-e + IBSICBS\nR$ 0,00\n\nINFORMAÇÕES COMPLEMENTARES\nNFS-e Subst.: 29192072203037698000108000000000000126087285776132\n\nTotais aproximados dos Tributos cfe. Lei nº 12.741/2012: Federais: R$ 1.918,58; Estaduais: R$ 0,00; Municipais: R$ 617,68;\n\nDATA CIENTIFICAÇÃO: IDENTIFICAÇÃO E ASSINATURA Nº NFS-e / CHAVE NFS-e\n11/ 29192072203037698000108000000000001126081682049850\n\n'


def _dummy(nome):
    caminho = f"tests/{nome}"
    os.makedirs("tests", exist_ok=True)
    with open(caminho, "wb") as f:
        f.write(b"%PDF-1.4")
    return caminho


def _parse(monkeypatch, texto, nome):
    """Reproduz o caminho real desta nota: pdfminer não acha texto (PDF
    escaneado) e o extrator cai no OCR."""
    caminho = _dummy(nome)
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: texto)
    try:
        return SPPdfExtractor(caminho).parse_multiple()
    finally:
        if os.path.exists(caminho):
            os.remove(caminho)


def test_detect_layout_danfse_v2_reforma():
    caminho = _dummy("dummy_danfse_reforma_detect.pdf")
    try:
        ex = SPPdfExtractor(caminho)
        ex.raw_text = MOCK_OCR
        assert ex._detect_layout() == LAYOUT_NACIONAL_REFORMA
    finally:
        if os.path.exists(caminho):
            os.remove(caminho)


def test_danfse_v1_continua_roteando_para_layout_nacional():
    r"""Regressão: a v2.0 é interceptada ANTES do check genérico `DANFSe v\d`,
    que precisa continuar entregando a v1.0 ao parser de sempre (texto real
    reaproveitado da fixture da nota nº 175, Várzea Grande/MT)."""
    from tests.test_danfse_nacional_pagina_unica_sem_fantasma import MOCK_TEXT_PAGINA3
    caminho = _dummy("dummy_danfse_v1_regressao.pdf")
    try:
        ex = SPPdfExtractor(caminho)
        ex.raw_text = MOCK_TEXT_PAGINA3
        assert ex._detect_layout() == LAYOUT_NACIONAL
    finally:
        if os.path.exists(caminho):
            os.remove(caminho)


def test_pdf_de_uma_nota_nao_vira_duas(monkeypatch):
    """O PDF tem 1 nota (pág. 2); a pág. 1 é o demonstrativo de faturamento.
    Antes do fix saíam 2 notas — o preâmbulo do cabeçalho (com a chave e o
    número certos, sem entidade nenhuma) e o corpo (com as entidades, mas com
    número/chave decodificados do "NFS-e Subst." do rodapé)."""
    notas = _parse(monkeypatch, MOCK_OCR, "dummy_danfse_reforma_fantasma.pdf")
    assert len(notas) == 1
    assert notas[0].numero == "11"


def test_identificacao_e_datas(monkeypatch):
    notas = _parse(monkeypatch, MOCK_OCR, "dummy_danfse_reforma_ident.pdf")
    nota = notas[0]
    assert nota.numero == "11"
    # Chave de Acesso do CABEÇALHO — não a do "NFS-e Subst." do rodapé
    # (…0126087285776132), que é a chave da nota SUBSTITUÍDA.
    assert nota.codigo_verificacao == "29192072203037698000108000000000001126081682049850"
    assert nota.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "05/08/2026 16:11:07"
    assert nota.servico_codigo == "1102"  # "11.02.01" -> item 11.02 da LC 116
    assert "VIGILÂNCIA PATRIMONIAL ARMADA" in nota.discriminacao


def test_valor_usa_valor_da_operacao_e_nunca_o_liquido(monkeypatch):
    """Requisito central: `ValorServicos` vem de "VALOR DA OPERAÇÃO /
    SERVIÇO" (12.353,68), nunca do "VALOR LÍQUIDO DA NFS-e" (9.817,41)."""
    notas = _parse(monkeypatch, MOCK_OCR, "dummy_danfse_reforma_valor.pdf")
    v = notas[0].valores
    assert v.valor_servicos == pytest.approx(12353.68)
    assert v.base_calculo == pytest.approx(12353.68)
    assert v.valor_liquido_nfse == pytest.approx(9817.41)
    assert v.aliquota == pytest.approx(0.05)


def test_valor_da_operacao_prevalece_quando_diverge_da_bc_issqn(monkeypatch):
    """Nesta nota BC ISSQN e VALOR DA OPERAÇÃO / SERVIÇO coincidem (não há
    exclusão nem redução de base). Mutação do texto real para o caso em que
    DIVERGEM: o valor da operação vai para `valor_servicos` e o BC ISSQN fica
    apenas na `base_calculo` (regra definida pelo usuário)."""
    texto = MOCK_OCR.replace(
        "BC ISSQN Alíquota Aplicada\nR$ 12.353,68 5,00 %",
        "BC ISSQN Alíquota Aplicada\nR$ 11.285,09 5,00 %",
    )
    assert "11.285,09" in texto, "a mutação do mock precisa casar o texto real"
    notas = _parse(monkeypatch, texto, "dummy_danfse_reforma_divergente.pdf")
    v = notas[0].valores
    assert v.valor_servicos == pytest.approx(12353.68)
    assert v.base_calculo == pytest.approx(11285.09)


def test_retencoes(monkeypatch):
    """ISSQN retido pelo tomador + as retenções federais entregues no PR #44
    (cujos rótulos a v2.0 preservou). PIS/COFINS "Débito Apuração Própria"
    (80,30 / 370,61) são débito do prestador, não retenção — continuam fora,
    como decidido no PR #44."""
    notas = _parse(monkeypatch, MOCK_OCR, "dummy_danfse_reforma_retencoes.pdf")
    v = notas[0].valores
    assert v.iss_retido is True          # "Retenção do ISSQN: Retido pelo Tomador"
    assert v.valor_iss == pytest.approx(617.68)
    assert v.valor_iss_retido == pytest.approx(617.68)
    assert v.valor_inss == pytest.approx(1344.14)
    assert v.valor_contribuicoes_sociais_retidas == pytest.approx(574.45)
    assert v.valor_ir == pytest.approx(0.0)      # IRRF em branco na nota
    assert v.valor_pis == pytest.approx(0.0)
    assert v.valor_cofins == pytest.approx(0.0)
    # "Exclusões e Reduções da Base de Cálculo" (R$ 1.068,59) é da base do
    # IBS/CBS, não do ISSQN — não pode virar dedução do ISS.
    assert v.valor_deducoes == pytest.approx(0.0)


def test_totais_da_nota_fecham(monkeypatch):
    """Conferência com os totais impressos na própria nota:
    "Total das Retenções (ISSQN / Federais)" = R$ 2.536,27 e
    VALOR DA OPERAÇÃO - retenções = VALOR LÍQUIDO."""
    notas = _parse(monkeypatch, MOCK_OCR, "dummy_danfse_reforma_totais.pdf")
    v = notas[0].valores
    total_retencoes = v.valor_iss_retido + v.valor_inss + v.valor_contribuicoes_sociais_retidas
    assert total_retencoes == pytest.approx(2536.27)
    assert v.valor_servicos - total_retencoes == pytest.approx(v.valor_liquido_nfse)
    assert v.base_calculo * v.aliquota == pytest.approx(v.valor_iss, abs=0.01)


def test_prestador(monkeypatch):
    notas = _parse(monkeypatch, MOCK_OCR, "dummy_danfse_reforma_prestador.pdf")
    p = notas[0].prestador
    assert p.cnpj_cpf == "03037698000108"
    assert p.razao_social == "UNICA SEGURANCA PATRIMONIAL LTDA"
    assert p.inscricao_municipal == "10000480"
    assert p.email == "unica@unicaseguranca.com"   # OCR: "unicaDunicaseguranca.com"
    assert p.telefone == "(71) 3378-9186"
    assert p.endereco.logradouro == "RUA JARDIM IPANEMA"
    assert p.endereco.numero == "500"
    assert p.endereco.complemento == "PORTAO"
    assert p.endereco.bairro == "PITANGUEIRAS"
    assert p.endereco.municipio == "Lauro de Freitas"
    assert p.endereco.uf == "BA"
    assert p.endereco.codigo_municipio == "2919207"   # IBGE impresso na nota
    assert p.endereco.cep == "42701830"


def test_tomador_nao_herda_dados_do_prestador(monkeypatch):
    """As colunas da direita são pareadas por ORDINAL (1ª ocorrência =
    prestador, 2ª = tomador). Antes do fix o tomador saía com o e-mail e o
    telefone do prestador e com o CEP "2919207" — que é o código IBGE de
    Lauro de Freitas, a cidade do PRESTADOR."""
    notas = _parse(monkeypatch, MOCK_OCR, "dummy_danfse_reforma_tomador.pdf")
    tom = notas[0].tomador
    assert tom.cnpj_cpf == "07834816000160"
    assert tom.razao_social == "CONDOMINIO EDIFICIO TK TOWER"
    assert tom.email == "nf@tkpatrimonial.com.br"   # OCR: "nf(Dtkpatrimonial.com.br"
    assert tom.telefone == "(71) 98806-9829"
    assert tom.endereco.logradouro == "PROFESSOR MAGALHAES NETO"
    assert tom.endereco.numero == "1856"
    assert tom.endereco.complemento == "LOTE 02"
    assert tom.endereco.bairro == "PITUBA"
    assert tom.endereco.municipio == "Salvador"
    assert tom.endereco.uf == "BA"
    assert tom.endereco.codigo_municipio == "2927408"
    assert tom.endereco.cep == "41810012"
    # Indicador Municipal do tomador vem em branco na nota: precisa sair
    # vazio, não com o do prestador escorregando para a posição dele.
    assert not tom.inscricao_municipal


def test_sem_intermediario_fantasma(monkeypatch):
    notas = _parse(monkeypatch, MOCK_OCR, "dummy_danfse_reforma_interm.pdf")
    assert notas[0].intermediario is None


def test_incidencia_do_issqn_segue_a_nota_e_nao_a_sede_do_prestador(monkeypatch):
    """Prestador em Lauro de Freitas (2919207), ISSQN devido em Salvador
    (2927408) conforme o campo "Município / Sigla UF / País de Incidência do
    ISSQN" da própria nota. Sem o override, a incidência iria para o
    município do prestador."""
    notas = _parse(monkeypatch, MOCK_OCR, "dummy_danfse_reforma_incidencia.pdf")
    assert notas[0].municipio_incidencia_override == "2927408"


def test_xml_abrasf_da_nota_11(monkeypatch):
    """Saída final: os campos que o importador do usuário consome."""
    from src.transformers.abrasf_transformer import Abrasf201Transformer
    notas = _parse(monkeypatch, MOCK_OCR, "dummy_danfse_reforma_xml.pdf")
    xml = Abrasf201Transformer().transform(notas[0])

    assert "<Numero>11</Numero>" in xml
    assert "<ValorServicos>12353.68</ValorServicos>" in xml
    assert "<ValorLiquidoNfse>9817.41</ValorLiquidoNfse>" in xml
    assert "<Aliquota>0.05</Aliquota>" in xml
    assert "<ValorIssRetido>617.68</ValorIssRetido>" in xml
    assert "<IssRetido>1</IssRetido>" in xml
    assert "<ValorInss>1344.14</ValorInss>" in xml
    # Contribuições Sociais Retidas somadas em OutrasRetencoes (PR #44)
    assert "<OutrasRetencoes>574.45</OutrasRetencoes>" in xml
    assert "<ItemListaServico>1102</ItemListaServico>" in xml
    assert "<MunicipioIncidencia>2927408</MunicipioIncidencia>" in xml
    # ValorServicos NUNCA pode ser o líquido
    assert "<ValorServicos>9817.41</ValorServicos>" not in xml
