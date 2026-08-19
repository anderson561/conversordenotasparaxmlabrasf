# -*- coding: utf-8 -*-
r"""Novo layout: Vinhedo/SP (`vinhedo_sp`), plataforma Balker
(vinhedo.balker.com.br).

Nota real nº 139 (WEDO DECOR LTDA -> NAUTICA INDUSTRIA E COMERCIO DE MOVEIS
E SERVICOS LTDA, R$ 1.049,79). Antes deste layout, a nota caía no fallback
`generico`, que produzia vários dados errados: `valor_servicos` zerado,
`valor_iss` fabricado como 28.0 (não bate com nenhum valor real da nota -
o correto é 41,99), UF do prestador saindo "BA" em vez de "SP", município
do prestador caindo no fallback Salvador/BA (Vinhedo não estava em
`KNOWN_CITIES`), `servico_codigo` saindo "03115" (fallback genérico, não
bate com o item real "7.19" impresso na nota), e a razão social do TOMADOR
saindo como "País: BRASIL" em vez do nome real.

Estrutura própria: blocos "PRESTADOR DE SERVIÇOS"/"TOMADOR DE SERVIÇOS" com
rótulo->valor adjacente na MESMA linha, mas o cabeçalho de seção "TOMADOR DE
SERVIÇOS" aparece deslocado no MEIO do próprio bloco do tomador (mesmo
quirk do Santos/SP) - o fatiamento usa a 2ª ocorrência de "Razão
Social/Nome:" em vez do cabeçalho de seção. Data de Emissão em formato
"DD/MMM/AAAA - HH:MM:SS" com mês abreviado em PT-BR. Grade de Retenções
Federais + Base/Alíquota/ISS (2 linhas x 7 colunas sem linhas de separação)
onde o pdfminer emite cada valor defasado em 1 coluna em relação ao próprio
rótulo - mapeado por índice fixo. "Desc. Incondicional" nunca aparece
impresso nesta plataforma (nem "0,00" nem placeholder) - mantido em 0,00.

Texto REAL extraído via pdfminer (`extract_text`), direto do PDF original -
nunca digitado à mão.
"""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_TEXT_VINHEDO = 'PREFEITURA MUNICIPAL DE VINHEDO\n\nSECRETARIA MUNICIPAL DA FAZENDA\nNOTA FISCAL ELETRÔNICA DE SERVIÇO - NFS-e\nCódigo de Verificação\n\n1156785ZOC\n\nPRESTADOR DE SERVIÇOS\n\nNº Nota\n139\nSerie 2\nNº RPS:\n-\nData de Emissão\n28/JUL/2026 - 14:24:50\nCompetência\n28/07/2026\n\nRazão Social/Nome: WEDO DECOR LTDA\n\nCNPJ/CPF: 31.574.103/0001-99\n\nEndereço: Rua ANTONIO VON ZUBEN\n\nComplemento: null\n\nMunicípio: VINHEDO\n\nE-mail: financeiro@wedodecor.com.br\n\nInsc. Municipal: 000024638\n\nInsc. Estadual: 714154767113\n\nBairro: Sta. ROSA\n\nUF: SP\n\nTelefone: 26436400\n\nCEP: 13289-034\n\nPaís: BRASIL\n\nRazão Social/Nome: NAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA\n\nCNPJ/CPF: 16.699.869/0002-97\n\nInsc. Municipal:\n\nInsc. Estadual:\n\nTOMADOR DE SERVIÇOS\n\nEndereço: ALAMEDA GABRIEL MONTEIRO DA SILVA, 1480\nComplemento: Não Informado\nMunicípio: SÃO PAULO\n\nUF: SP\n\nE-mail: BIANCAYUMI@TIDELLI.COM.BR\n\nBairro: JARDIM AMÉRICA\nUF: SP\n\nCEP: 01442-001\nPaís: BRASIL\n\nTelefone:\n\nPrestação de Serviço\n\nDISCRIMINAÇÃO DOS SERVIÇOS\n\nDados bancários - Banco Itau - agencia 2978 - conta corrente 39656-8 - pix 31574103000199\n\nINFORMAÇÕES COMPLEMENTARES\n\nLocal de Prestação: VINHEDO - SP\nCódigo do Serviço: Ativ. Serviço: 7.19 - Acompanhamento e fiscalização da execução de obras de engenharia, arquitetura e urbanismo.\n\nLocal de Incidência: VINHEDO\n\nCódigo NBS: 114021500 - Serviços de arquitetura relativos ao acompanhamento e fiscalização da execução de projetos arquitetô...\n\nVALOR TOTAL DA NOTA =  R$ 1.049,79\n\nValor do INSS Retido\n(R$)\nDesc. Incondicional (R$)\n\n0,00\n\nValor do IRRF Retido\n(R$)\n0,00\nDeduções (R$)\n\nValor do CSLL Retido\n(R$)\n\n0,00\n\nValor do PIS Retido\n(R$)\n\n0,00\n\nValor do COFINS Retido\n(R$)\n\nOutras Retenções (R$)\n\n0,00\n\n0,00\n\nBase de Cálculo do ISS (R$)\n1.049,79\n\n0,00\nAlíquota\n4,00\n\nValor do IBS\n(RS)\n\nVlr ISS (R$)\n\n41,99\n\nValor do CBS\n(R$)\n\n0,01\n0,01\nVlr Líquido da Nota (R$)\n1.049,79\n\nO ISSQN desta NFS-e será recolhido pelo PRESTADOR.\n\nContribuinte enquadrado no Regime de ISS Variável.\n\nOUTRAS INFORMAÇÕES\n\nA autenticação da NFS-e pode ser confirmada no Site:\nhttps://vinhedo.balker.com.br/ords/vinhedo/f?p=2300:71 RECEBEMOS DO(A) WEDO DECOR LTDA\nOS SERVIÇOS CONSTANTES NA NFS-e\n\nLocal\n\nData\n\nAssinatura\n\nCódigo de Verificação:\n1156785ZOC\n\nNúmero da Nota:\n\n139\n\nChave Acesso:\nAguardando retorno do Ambiente Nacional\n\n\x0c'


def test_vinhedo_sp_detecta_layout_proprio(monkeypatch):
    dummy_path = "tests/dummy_vinhedo_sp.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT_VINHEDO)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse = extractor.parse()
        assert extractor.layout == "vinhedo_sp"
        assert nfse is not None
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_vinhedo_sp_extrai_cabecalho_e_servico(monkeypatch):
    dummy_path = "tests/dummy_vinhedo_sp.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT_VINHEDO)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse = extractor.parse()

        assert nfse.numero == "139"
        assert nfse.codigo_verificacao == "1156785ZOC"
        assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "28/07/2026 14:24:50"
        assert nfse.competencia.strftime("%d/%m/%Y") == "28/07/2026"
        assert nfse.servico_codigo == "0719"
        assert nfse.optante_simples_nacional is False
        assert nfse.regime_especial_tributacao is None
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_vinhedo_sp_extrai_prestador_e_tomador_sem_troca(monkeypatch):
    """Regressão do bug do fallback `generico`: tomador saía com a razão
    social igual a "País: BRASIL" (rótulo vazando por causa do cabeçalho
    "TOMADOR DE SERVIÇOS" deslocado), e ambas as entidades saíam com UF "BA"
    (default do IBGEResolver) e o prestador caindo no fallback Salvador/BA
    (Vinhedo não cadastrada em KNOWN_CITIES antes deste layout)."""
    dummy_path = "tests/dummy_vinhedo_sp.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT_VINHEDO)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse = extractor.parse()

        p = nfse.prestador
        assert p.cnpj_cpf == "31574103000199"
        assert p.inscricao_municipal == "000024638"
        assert p.razao_social == "WEDO DECOR LTDA"
        assert p.endereco.logradouro == "Rua ANTONIO VON ZUBEN"
        assert p.endereco.numero == "S/N"
        assert p.endereco.complemento is None
        assert p.endereco.bairro == "Sta. ROSA"
        assert p.endereco.cep == "13289034"
        assert p.endereco.municipio == "VINHEDO"
        assert p.endereco.uf == "SP"
        assert p.endereco.codigo_municipio == "3556701"
        assert p.email == "financeiro@wedodecor.com.br"
        assert p.telefone == "26436400"

        t = nfse.tomador
        assert t.cnpj_cpf == "16699869000297"
        assert t.inscricao_municipal is None
        assert t.razao_social == "NAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA"
        assert t.endereco.logradouro == "ALAMEDA GABRIEL MONTEIRO DA SILVA"
        assert t.endereco.numero == "1480"
        assert t.endereco.complemento is None
        assert t.endereco.bairro == "JARDIM AMÉRICA"
        assert t.endereco.cep == "01442001"
        assert t.endereco.municipio == "SÃO PAULO"
        assert t.endereco.uf == "SP"
        assert t.endereco.codigo_municipio == "3550308"
        assert t.email == "BIANCAYUMI@TIDELLI.COM.BR"
        assert t.telefone is None

        assert nfse.intermediario is None
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_vinhedo_sp_extrai_valores_grade_defasada(monkeypatch):
    """Regressão do bug do fallback `generico`: `valor_servicos` saía 0.0 e
    `valor_iss` saía fabricado como 28.0 (não bate com o valor real 41,99).
    A grade de retenções/base/alíquota/ISS emite cada valor defasado em 1
    coluna em relação ao próprio rótulo - conferir que o mapeamento por
    índice fixo recupera o valor CORRETO de cada campo, não o do vizinho."""
    dummy_path = "tests/dummy_vinhedo_sp.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT_VINHEDO)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse = extractor.parse()
        v = nfse.valores

        assert v.valor_servicos == pytest.approx(1049.79)
        assert v.desconto_incondicionado == pytest.approx(0.0)
        assert v.valor_deducoes == pytest.approx(0.0)
        assert v.outras_retencoes == pytest.approx(0.0)
        assert v.base_calculo == pytest.approx(1049.79)
        assert v.aliquota == pytest.approx(0.04)
        assert v.valor_liquido_nfse == pytest.approx(1049.79)
        assert v.valor_iss == pytest.approx(41.99)
        assert v.iss_retido is False
        assert v.valor_inss == pytest.approx(0.0)
        assert v.valor_ir == pytest.approx(0.0)
        assert v.valor_csll == pytest.approx(0.0)
        assert v.valor_pis == pytest.approx(0.0)
        assert v.valor_cofins == pytest.approx(0.0)

        assert "Valor dos serviços extraído como zero" not in nfse.avisos
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
