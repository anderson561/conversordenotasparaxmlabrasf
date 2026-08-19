# -*- coding: utf-8 -*-
r"""Novo layout: Santos/SP (`santos_sp`), plataforma Ginfes
(santos.ginfes.com.br - mesma plataforma do LAYOUT_GUARULHOS, mas nota
DIGITAL/pdfminer, não escaneada).

Nota real nº 16 (IN.OUT MOVEIS E DECORACOES LTDA -> NAUTICA INDUSTRIA E
COMERCIO DE MOVEIS LTDA, R$ 6.666,86). Antes deste layout, a nota caía no
fallback `generico`, que produzia vários dados errados: `valor_servicos`
zerado, `valor_iss` fabricado como 14.0 (número aleatório do documento),
UF do prestador e do tomador saindo "BA" em vez de "SP", município do
prestador caindo no fallback Salvador/BA (Santos não estava em
`KNOWN_CITIES`), e a razão social do TOMADOR saindo como o próprio
endereço dele ("Alameda Gabriel Monteiro da Silva") em vez do nome real.

Estrutura própria: cada campo é rótulo->valor adjacente, mas na ORDEM
VISUAL de 2 colunas do formulário (não top-to-bottom) - o cabeçalho de
seção "Tomador de Serviço" aparece deslocado no MEIO do próprio bloco do
tomador. Duas grades "rótulos em cima, valores embaixo" (Identificação
Prestação de Serviços / Detalhamento de Valores) - a de valores tem 13
rótulos fixos mas só 10 valores nesta nota, porque ISSQN/IBS/CBS saem
literalmente em branco (Simples Nacional, ISS pago via guia única).

Texto REAL extraído via pdfminer (`extract_text`), direto do PDF original -
nunca digitado à mão.
"""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_TEXT_SANTOS = 'PREFEITURA MUNICIPAL DE SANTOS\n\nSECRETARIA MUNICIPAL DE FINANÇAS E GESTÃO\n\nNOTA FISCAL DE SERVIÇO ELETRÔNICA - NFS-e\n\nRPS\n\nSérie RPS\n\nTipo RPS\n\nNFS-e\n16\nCódigo de Verificação\nAKBT3QZT1\nEmissão da NFS-e\n14/07/2026 11:13:33\nNFS-e Substituída\n\nPrestador de Serviço\n\nCPF/CNPJ:\n\n45.908.500/0001-64\n\nInscrição\n\n3028296\n\nNome/Razão Social:\n\nIN.OUT MOVEIS E DECORACOES LTDA\n\nEndereço\n\nSem tipo de logradouro Washington Luís\n\nComplemento:\n\n0000\n\nCEP:\n\n11050-200\n\nMunicípio:\n\nSANTOS\n\nE-mail:\n\ninayara@augecontabilidade.com.br\n\nNúmero:\n\n16\n\nBairro:\n\nVila Mathias\n\nUF: SP\n\nPaís:\n\nBrasil\n\nTelefone:\n\n(13)3877-4940\n\nCPF/CNPJ:\n\n16.699.869/0002-97\n\nInscrição Municipal:\n\nNIF:\n\nNome/Razão Social:\n\nNAUTICA INDUSTRIA E COMERCIO DE MOVEIS LTDA\n\nTomador de Serviço\n\nEndereço:\n\nAlameda Gabriel Monteiro da Silva\n\nComplemento:\n\nCEP:\n\n01442-001\n\nMunicípio: SAO PAULO\n\nE-mail:\n\nlorena@nauticamoveis.com\n\nNúmero:\n\n1480\n\nBairro:\n\nJardim América\n\nUF: SP\n\nPaís:\n\nBrasil\n\nTelefone:\n\n(71)3355-2526\n\nAtividade Econômica\n14.01 / 952910501 - reparação de artigos do mobiliário - em geral, exceto tapeçaria\n\nDiscriminação do Serviço\n\nReferente ao pedido 73-2026 IMOB Empreendimento.\nDados bancários:\nBanco Bradesco\nAgência: 0518\nConta Corrente: 001168-7\n\nTipo PIS\n\nTributos Federais (R$)\nTipo COFINS\n\nINSS\n\nCOFINS\n\nApuração Própria\n\n0,00\n\nApuração Própria\n\n0,00\n\nPIS\n\n0,00\n\nValor Aproximado dos Tributos\n\nIR\n\n0,00\n\nCSLL\n\n0,00\n\nFederal\n\nEstadual Municipal\n\nFonte\n\n0.00% 0.00%\n\n0.00%\n\nSimples\n\n0.00%\n\nIdentificação Prestação de Serviços\n\nDetalhamento de Valores (R$)\n\nCódigo da Obra\n\nCódigo A.R.T.\n\nExigibilidade ISSQN\n\nRegime Especial de Tributação\n\nSimples Nacional\n\nNomenclatura Brasileira de Serviços\n\nIndicador de Operação\n\nSituação Tributária\n\nClassificação Tributária\n\nCompetência\n\nMunicípio Prestação\n\nMunícipio Incidência\n\nISSQN a Reter\n\n1-Exigível\n\n0-Nenhum\n\n(X) Sim () Não\n\n1.2001.10.00\n\n50101\n\n000\n\n000001\n\n07/2026\n\nSANTOS - SP\n\nSANTOS - SP\n\n( ) Sim (X) Não\n\nValor do Serviço\n\nDesconto Incondicionado\n\nDesconto Condicionado\n\nRetenções Federais\n\nPIS/COFINS - Apuração Própria\n\nOutras Retenções\n\nDeduções Previstas em Lei\n\nBase de Cálculo\n\nAlíquota\n\nISSQN\n\nIBS\n\nCBS\n\nValor Líquido\n\n6.666,86\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n6.666,86\n\n2,01\n\n6.666,86\n\nUma via desta Nota Fiscal será enviada através do e-mail fornecido pelo Tomador dos Serviços.\nA autenticidade desta Nota Fiscal poderá ser verificada no site, santos.ginfes.com.br com a utilização do Código de Verificação.\n\nOutras Informações\n\n\x0c'


def test_santos_sp_detecta_layout_proprio(monkeypatch):
    dummy_path = "tests/dummy_santos_sp.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT_SANTOS)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse = extractor.parse()
        assert extractor.layout == "santos_sp"
        assert nfse is not None
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_santos_sp_extrai_cabecalho_e_servico(monkeypatch):
    dummy_path = "tests/dummy_santos_sp.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT_SANTOS)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse = extractor.parse()

        assert nfse.numero == "16"
        assert nfse.codigo_verificacao == "AKBT3QZT1"
        assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "14/07/2026 11:13:33"
        assert nfse.competencia.strftime("%m/%Y") == "07/2026"
        assert nfse.servico_codigo == "1401"
        assert nfse.optante_simples_nacional is True
        assert nfse.regime_especial_tributacao is None
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_santos_sp_extrai_prestador_e_tomador_sem_troca(monkeypatch):
    """Regressão do bug do fallback `generico`: tomador saía com a razão
    social igual ao PRÓPRIO ENDEREÇO ("Alameda Gabriel Monteiro da Silva"),
    e ambas as entidades saíam com UF "BA" (default do IBGEResolver) e
    município caindo no fallback Salvador/BA (Santos não cadastrada em
    KNOWN_CITIES antes deste layout)."""
    dummy_path = "tests/dummy_santos_sp.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT_SANTOS)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse = extractor.parse()

        p = nfse.prestador
        assert p.cnpj_cpf == "45908500000164"
        assert p.inscricao_municipal == "3028296"
        assert p.razao_social == "IN.OUT MOVEIS E DECORACOES LTDA"
        assert p.endereco.logradouro == "Washington Luís"
        assert p.endereco.numero == "16"
        assert p.endereco.complemento == "0000"
        assert p.endereco.bairro == "Vila Mathias"
        assert p.endereco.cep == "11050200"
        assert p.endereco.municipio == "SANTOS"
        assert p.endereco.uf == "SP"
        assert p.endereco.codigo_municipio == "3548500"
        assert p.email == "inayara@augecontabilidade.com.br"
        assert p.telefone == "(13)3877-4940"

        t = nfse.tomador
        assert t.cnpj_cpf == "16699869000297"
        assert t.inscricao_municipal is None
        assert t.razao_social == "NAUTICA INDUSTRIA E COMERCIO DE MOVEIS LTDA"
        assert t.endereco.logradouro == "Alameda Gabriel Monteiro da Silva"
        assert t.endereco.numero == "1480"
        assert t.endereco.complemento is None
        assert t.endereco.bairro == "Jardim América"
        assert t.endereco.cep == "01442001"
        assert t.endereco.municipio == "SAO PAULO"
        assert t.endereco.uf == "SP"
        assert t.endereco.codigo_municipio == "3550308"
        assert t.email == "lorena@nauticamoveis.com"
        assert t.telefone == "(71)3355-2526"

        assert nfse.intermediario is None
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_santos_sp_extrai_valores_com_issqn_em_branco(monkeypatch):
    """Regressão do bug do fallback `generico`: `valor_servicos` saía 0.0 e
    `valor_iss` saía fabricado como 14.0 (número aleatório do documento).
    ISSQN/IBS/CBS saem literalmente em branco nesta nota (Simples Nacional)
    - mantidos em 0,00, nunca derivados de Base x Alíquota (decisão do
    usuário)."""
    dummy_path = "tests/dummy_santos_sp.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT_SANTOS)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse = extractor.parse()
        v = nfse.valores

        assert v.valor_servicos == pytest.approx(6666.86)
        assert v.desconto_incondicionado == pytest.approx(0.0)
        assert v.desconto_condicionado == pytest.approx(0.0)
        assert v.valor_deducoes == pytest.approx(0.0)
        assert v.outras_retencoes == pytest.approx(0.0)
        assert v.base_calculo == pytest.approx(6666.86)
        assert v.aliquota == pytest.approx(0.0201)
        assert v.valor_liquido_nfse == pytest.approx(6666.86)
        assert v.valor_iss == pytest.approx(0.0)
        assert v.iss_retido is False

        assert "Valor dos serviços extraído como zero" not in nfse.avisos
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
