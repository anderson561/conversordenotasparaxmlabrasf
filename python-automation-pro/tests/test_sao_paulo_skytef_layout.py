# -*- coding: utf-8 -*-
r"""Novo layout: São Paulo/SP - SKYTEF (`sp_skytef`), plataforma Qive
(www.qive.com.br).

Nota real nº 902735 (SKYTEF SOLUÇÕES EM CAPTURA DE TRANSAÇÕES LTDA, CNPJ
04.988.631/0001-11, Vila Olímpia/São Paulo-SP -> RG RESTAURANTE LTDA,
Camaçari/BA, R$ 86,80 - licenciamento de uso do aplicativo "TEF Nuvem").
Antes deste layout, a nota caía no fallback `generico`, que produzia dados
errados/zerados (entidades trocadas/garbladas, valores zerados).

Detectado só pelo CNPJ do emitente (nunca pela marca "Qive", plataforma
SaaS compartilhada por outros emitentes). Prestador FIXO (hardcoded do
próprio letterhead). Quirks próprios: a razão social do TOMADOR ("Nome /
Nome Empresarial") aparece ANTES do cabeçalho de seção "Dados do Tomador de
Serviços" (o resto do bloco vem depois, em ordem normal); a Competência sai
como um valor solto (MM/AAAA) antes do rótulo "Numero da NFS-e:", sem
nenhum rótulo "Competência" adjacente ao próprio valor.

Texto REAL extraído via pdfminer (`extract_text`), direto do PDF original -
nunca digitado à mão.
"""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_TEXT_SKYTEF = 'Data de Emissão\n\n12/02/2026 16:19:17\n\nCompetência\n\nCódigo de Verificação\n\n35503081204988631000111000000090273526023096351249\n\nNúmero RPS\n\nMunicípio da Prestação\n\n3550308 - São Paulo - SP\n\nNFS-e Substituída\n\n-\n\nNome / Nome Empresarial SKYTEF SOLUCOES EM CAPTURA DE TRANSACOES LTDA\n\nDados do Prestador de Serviços\n\n02/2026 Numero da NFS-e:\n902735\n\n902735\nSérie RPS: 1\nPag. 1/1\n\nCPF/CNPJ\n\n04.988.631/0001-11 Inscrição Municipal 49675869 Município 3550308 - São Paulo - SP\n\nEndereço e CEP\n\nSAO TOME, 119 - VILA OLIMPIA - 3550308 - São Paulo - SP - CEP: 04551-080\n\nComplemento\n\nSALA 21 A 24\n\nTelefone\n\n-\n\nE-mail\n\ncobranca@skytef.com\n\nNome / Nome Empresarial\n\nRG RESTAURANTE LTDA\n\nDados do Tomador de Serviços\n\nCPF/CNPJ\n\n23.918.316/0001-62\n\nInscrição Municipal\n\n- Município\n\n2905701 - Camaçari - BA\n\nEndereço e CEP\n\nBVD SHOPPING CAMACARI - Centro - 2905701 - Camaçari - BA - CEP: 00000-000\n\nComplemento\n\n-\n\nTelefone\n\n-\n\nE-mail\n\n-\n\nDiscriminação dos Serviços\n\n1.05-Licenciamento ou cessao de direito de uso de programas de computacao. LICENCIAMENTO DO USO DO APLICATIV\nO TEF NUVEM 03 PDV N ADQUIRENTES Valor Liquido a ser pago: 86,80 Data de Vencimento : 01/03/2\n026 Valor Aproximado dos Tributos/Fonte: R$ 14,59/IBPT Apos o vencimento cobranca de multa 2% cobranca de\njuros de mora de 0,03333% ao dia Nao retencao de impostos conforme 1 do art. 714 do Decreto 9.580 de 22/1\n1/2018 e art. 30 da Lei 10.833 de 29/12/2003. Conforme Previsto no Artigo 2 da Lei 12.741.DE 08/12/2012 o Va\nlor Aproximado dos Tributos: R$ 14,59(16,81%)Fonte:IBPT Inclusos nos precos dos bens/servicos acima discrimi\nnados: PIS/PASEP-Faturamento, COFINS-Faturamento e ISS-Imposto Sobre Servicos. Quaisquer outros tributos inc\nidentes/exigidos sobre esta operacao deverao ser acrescidos aos precos acima., Tributos Federais: 0.00\n\nCódigo do Serviço\n\n010501\n\nVALOR DO SERVIÇO = R$ 86,80\n\nPIS\n\nR$ 0,00\n\nCOFINS\n\nR$ 0,00\n\nIR\n\n-\n\nINSS\n\n-\n\nCSLL\n\nR$ 0,00\n\nB. Cálculo (R$)\nR$ 86,80\n\nAlíquota (%)\n2,90 %\n\nV. do ISS (R$)\nR$ 2,51\n\nV. Líquido (R$)\nR$ 86,80\n\nISS Retido\n2 - Não\n\nCódigo NBS\n\n111032200\n\nInformações IBS/CBS\n\nValor do IBS no Município(R$)\nR$ 0,00\n\nAlíquota do IBS Município (%)\n0,00 %\n\nValor do IBS da UF(R$)\nR$ 0,08\n\nAlíquota do IBS da UF (%)\n0,00 %\n\nValor total CBS(R$)\nR$ 0,75\n\nValor total da BC do IBS e da CBS (R$)\nR$ 84,28\n\nMunicípio de Incidência do IBS/CBS\n2905701 Camaçari\n\nNotas fiscais gerenciadas pela Qive - www.qive.com.br\n\n\x0c'


def _make_extractor(monkeypatch):
    dummy_path = "tests/dummy_sp_skytef.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT_SKYTEF)
    return dummy_path


def test_sp_skytef_detecta_layout_proprio(monkeypatch):
    dummy_path = _make_extractor(monkeypatch)
    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse = extractor.parse()
        assert extractor.layout == "sp_skytef"
        assert nfse is not None
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_sp_skytef_extrai_cabecalho_e_servico(monkeypatch):
    dummy_path = _make_extractor(monkeypatch)
    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse = extractor.parse()

        assert nfse.numero == "902735"
        assert nfse.codigo_verificacao == "35503081204988631000111000000090273526023096351249"
        assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "12/02/2026 16:19:17"
        # Competência sai como valor solto "02/2026" antes do rótulo
        # "Numero da NFS-e:", sem rótulo "Competência" próprio adjacente.
        assert nfse.competencia.strftime("%m/%Y") == "02/2026"
        assert nfse.servico_codigo == "0105"
        assert nfse.optante_simples_nacional is False
        assert nfse.regime_especial_tributacao is None
        assert nfse.municipio_incidencia_override is None
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_sp_skytef_extrai_prestador_fixo_e_tomador_dinamico(monkeypatch):
    """Regressão do fallback `generico`: entidades saíam trocadas/garbladas.
    O prestador é fixo (hardcoded do letterhead); o tomador precisa vir do
    bloco correto - o mesmo rótulo "Nome / Nome Empresarial"/"Endereço e
    CEP"/"CPF/CNPJ" aparece 2x no documento (prestador e tomador), e a busca
    tem de pegar a ocorrência do TOMADOR, não a do prestador (que aparece
    antes no texto)."""
    dummy_path = _make_extractor(monkeypatch)
    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse = extractor.parse()

        p = nfse.prestador
        assert p.cnpj_cpf == "04988631000111"
        assert p.inscricao_municipal == "49675869"
        assert p.razao_social == "SKYTEF SOLUCOES EM CAPTURA DE TRANSACOES LTDA"
        assert p.endereco.logradouro == "SAO TOME"
        assert p.endereco.numero == "119"
        assert p.endereco.complemento == "SALA 21 A 24"
        assert p.endereco.bairro == "VILA OLIMPIA"
        assert p.endereco.codigo_municipio == "3550308"
        assert p.endereco.municipio == "São Paulo"
        assert p.endereco.uf == "SP"
        assert p.endereco.cep == "04551080"
        assert p.email == "cobranca@skytef.com"

        t = nfse.tomador
        assert t.cnpj_cpf == "23918316000162"
        assert t.inscricao_municipal is None
        assert t.razao_social == "RG RESTAURANTE LTDA"
        assert t.endereco.logradouro == "BVD SHOPPING CAMACARI"
        assert t.endereco.numero == "S/N"
        assert t.endereco.bairro == "Centro"
        assert t.endereco.codigo_municipio == "2905701"
        assert t.endereco.municipio == "Camaçari"
        assert t.endereco.uf == "BA"
        assert t.endereco.cep == "00000000"

        assert nfse.intermediario is None
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_sp_skytef_extrai_valores(monkeypatch):
    dummy_path = _make_extractor(monkeypatch)
    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse = extractor.parse()
        v = nfse.valores

        assert v.valor_servicos == pytest.approx(86.80)
        assert v.base_calculo == pytest.approx(86.80)
        assert v.aliquota == pytest.approx(0.029)
        assert v.valor_iss == pytest.approx(2.51)
        assert v.valor_liquido_nfse == pytest.approx(86.80)
        # IR/INSS saem impressos como "-" (sem retenção), não "R$ 0,00" -
        # tratados como 0.0, não fabricados.
        assert v.valor_ir == pytest.approx(0.0)
        assert v.valor_inss == pytest.approx(0.0)
        assert v.valor_pis == pytest.approx(0.0)
        assert v.valor_cofins == pytest.approx(0.0)
        assert v.valor_csll == pytest.approx(0.0)
        # "ISS Retido\n2 - Não"
        assert v.iss_retido is False
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
