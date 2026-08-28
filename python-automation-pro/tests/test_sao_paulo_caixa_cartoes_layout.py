# -*- coding: utf-8 -*-
r"""Novo layout: São Paulo/SP - CAIXA CARTÕES (`sp_caixa_cartoes`), MESMA
plataforma Qive (www.qive.com.br) do LAYOUT_SP_SKYTEF, outro emitente.

Nota real nº 27723844 (CAIXA CARTÕES PRÉ-PAGOS S.A., CNPJ 39.459.331/0006-34,
Vila Olímpia/São Paulo-SP -> RG RESTAURENTE LTDA - EPP, Camaçari/BA, R$ 6,30 -
"Taxa de Serviço" de reembolso/adquirência de cartões pré-pagos). Detectado só
pelo CNPJ do emitente (nunca pela marca "Qive", mesmo critério do SKYTEF, para
não colidir com outros emitentes na mesma plataforma).

Prestador FIXO (hardcoded do letterhead). Extratores de tomador/valores/data
mantidos SEPARADOS dos do SKYTEF (mesma decisão já tomada entre
LAYOUT_NFCOM_SALVADOR/LAYOUT_NFCOM_RLGR), apesar da estrutura quase idêntica.

Diferenças notadas em relação ao SKYTEF:
- Competência sai LIMPA ("Competência\n\n03/2026", rótulo adjacente ao
  valor) - ao contrário do SKYTEF, onde o valor sai órfão antes do rótulo
  "Numero da NFS-e:" (aqui o fallback genérico já resolve, sem precisar de
  branch dedicada).
- A razão social do tomador vem COLADA na mesma linha do rótulo ("Nome /
  Nome Empresarial RG RESTAURENTE LTDA - EPP"), não em 2 linhas como no
  SKYTEF.
- A discriminação cita um valor de IRRF explícito e com base legal própria
  ("IRRF 1,5%... conforme I.N. 153/87 e Lei 7450/85, art. 53 - R$ 0,09"),
  mesmo com o campo estruturado "IR" da grade mostrando só "-" - extraído
  dali (valor real declarado na nota, não fabricado), diferente do SKYTEF
  (sem nenhum valor real citado, mantido em 0,00).
- Discriminação não começa com "N.NN-" (item LC116 não vem no texto livre);
  o item ("17.12") é derivado do campo "Código do Serviço\n\n171201"
  (6 dígitos: item + desdobro municipal da Qive).

Texto REAL extraído via pdfminer (`extract_text`), direto do PDF original -
nunca digitado à mão.
"""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_TEXT_CAIXA_CARTOES = 'Data de Emissão\n\n02/03/2026 04:19:07\n\nCompetência\n\n03/2026\n\nCódigo de Verificação\n\n35503081239459331000634000002772384426030055284234\n\nNúmero RPS\n\n27723844\n\nMunicípio da Prestação\n\n3550308 - São Paulo - SP\n\nNFS-e Substituída\n\n-\n\nNumero da NFS-e:\n27723844\nSérie RPS: 1\nPag. 1/1\n\nNome / Nome Empresarial CAIXA CARTOES PRE-PAGOS S.A.\n\nDados do Prestador de Serviços\n\nCPF/CNPJ\n\n39.459.331/0006-34 Inscrição Municipal 72114592 Município 3550308 - São Paulo - SP\n\nEndereço e CEP\n\nGOMES DE CARVALHO, 1629 - VILA OLIMPIA - 3550308 - São Paulo - SP - CEP: 04547-006\n\nComplemento\n\nANDAR 5\n\nTelefone\n\n-\n\nE-mail\n\nfiscal@caixaprepagos.com.br\n\nNome / Nome Empresarial RG RESTAURENTE LTDA - EPP\n\nDados do Tomador de Serviços\n\nCPF/CNPJ\n\n23.918.316/0001-62\n\nInscrição Municipal\n\n- Município\n\n2905701 - Camaçari - BA\n\nEndereço e CEP\n\nBOULEVARD SHOPPING CAMACARI, SN - INDUSTRIAL - 2905701 - Camaçari - BA - CEP: 42800-970\n\nComplemento\n\nLOJA 2002\n\nTelefone\n\n-\n\nE-mail\n\ngilbertossantana@gmail.com\n\nDiscriminação dos Serviços\n\nTaxa de Servico: R$ 6,30 Esta nota fiscal compõe a Guia de Reembolso 695799791 IRRF 1,5% Sob Responsabilidade\nde CAIXA CARTÕES PRÉ-PAGOS S.A. conforme I.N. 153/87 e Lei 7450/85, art. 53 - R$ 0,09 Trib aprox. Lei nº 12.7\n41/12: R$0,85 Federal, R$0,26 Municipal e R$5,19 pelos serviços Fonte:IBPT/empresometro.com.br 3CA397 26.1.E,\nTributos Federais: 0.00\n\nCódigo do Serviço\n\n171201\n\nVALOR DO SERVIÇO = R$ 6,30\n\nPIS\n\nR$ 0,00\n\nCOFINS\n\nR$ 0,00\n\nIR\n\n-\n\nINSS\n\n-\n\nCSLL\n\nR$ 0,00\n\nB. Cálculo (R$)\nR$ 6,30\n\nAlíquota (%)\n2,00 %\n\nV. do ISS (R$)\nR$ 0,12\n\nV. Líquido (R$)\nR$ 6,30\n\nISS Retido\n2 - Não\n\nCódigo NBS\n\n114012100\n\nInformações IBS/CBS\n\nValor do IBS no Município(R$)\nR$ 0,00\n\nAlíquota do IBS Município (%)\n0,00 %\n\nValor do IBS da UF(R$)\nR$ 0,00\n\nAlíquota do IBS da UF (%)\n0,00 %\n\nValor total CBS(R$)\nR$ 0,05\n\nValor total da BC do IBS e da CBS (R$)\nR$ 6,17\n\nMunicípio de Incidência do IBS/CBS\n2905701 Camaçari\n\nNotas fiscais gerenciadas pela Qive - www.qive.com.br\n\n\x0c'


def _make_extractor(monkeypatch):
    dummy_path = "tests/dummy_sp_caixa_cartoes.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT_CAIXA_CARTOES)
    return dummy_path


def test_sp_caixa_cartoes_detecta_layout_proprio(monkeypatch):
    dummy_path = _make_extractor(monkeypatch)
    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse = extractor.parse()
        assert extractor.layout == "sp_caixa_cartoes"
        assert nfse is not None
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_sp_caixa_cartoes_extrai_cabecalho_e_servico(monkeypatch):
    dummy_path = _make_extractor(monkeypatch)
    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse = extractor.parse()

        assert nfse.numero == "27723844"
        assert nfse.codigo_verificacao == "35503081239459331000634000002772384426030055284234"
        assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "02/03/2026 04:19:07"
        # Competência sai LIMPA ("Competência\n\n03/2026"), sem quirk -
        # resolvida pelo fallback genérico.
        assert nfse.competencia.strftime("%m/%Y") == "03/2026"
        # "Código do Serviço\n\n171201" -> item LC116 "17.12" (desdobro "01").
        assert nfse.servico_codigo == "1712"
        assert nfse.optante_simples_nacional is False
        assert nfse.regime_especial_tributacao is None
        assert nfse.municipio_incidencia_override is None
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_sp_caixa_cartoes_extrai_prestador_fixo_e_tomador_dinamico(monkeypatch):
    """Prestador fixo (hardcoded do letterhead); tomador dinâmico com o
    mesmo quirk de rótulo deslocado do SKYTEF ("Nome / Nome Empresarial"
    aparece 2x - prestador e tomador -, e a busca tem de pegar a ÚLTIMA
    ocorrência, antes do cabeçalho "Dados do Tomador de Serviços"), embora
    aqui o valor venha colado na mesma linha do rótulo, não em 2 linhas."""
    dummy_path = _make_extractor(monkeypatch)
    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse = extractor.parse()

        p = nfse.prestador
        assert p.cnpj_cpf == "39459331000634"
        assert p.inscricao_municipal == "72114592"
        assert p.razao_social == "CAIXA CARTOES PRE-PAGOS S.A."
        assert p.endereco.logradouro == "GOMES DE CARVALHO"
        assert p.endereco.numero == "1629"
        assert p.endereco.complemento == "ANDAR 5"
        assert p.endereco.bairro == "VILA OLIMPIA"
        assert p.endereco.codigo_municipio == "3550308"
        assert p.endereco.municipio == "São Paulo"
        assert p.endereco.uf == "SP"
        assert p.endereco.cep == "04547006"
        assert p.email == "fiscal@caixaprepagos.com.br"

        t = nfse.tomador
        assert t.cnpj_cpf == "23918316000162"
        assert t.inscricao_municipal is None
        assert t.razao_social == "RG RESTAURENTE LTDA - EPP"
        assert t.endereco.logradouro == "BOULEVARD SHOPPING CAMACARI, SN"
        assert t.endereco.numero == "S/N"
        assert t.endereco.bairro == "INDUSTRIAL"
        assert t.endereco.codigo_municipio == "2905701"
        assert t.endereco.municipio == "Camaçari"
        assert t.endereco.uf == "BA"
        assert t.endereco.cep == "42800970"

        assert nfse.intermediario is None
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_sp_caixa_cartoes_extrai_valores(monkeypatch):
    dummy_path = _make_extractor(monkeypatch)
    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse = extractor.parse()
        v = nfse.valores

        assert v.valor_servicos == pytest.approx(6.30)
        assert v.base_calculo == pytest.approx(6.30)
        assert v.aliquota == pytest.approx(0.02)
        assert v.valor_iss == pytest.approx(0.12)
        assert v.valor_liquido_nfse == pytest.approx(6.30)
        # Campo estruturado "IR" sai "-" (grade), mas a discriminação cita
        # um valor de IRRF real com base legal própria (I.N. 153/87, Lei
        # 7450/85 art. 53) - extraído dali, não fabricado nem zerado.
        assert v.valor_ir == pytest.approx(0.09)
        assert v.valor_inss == pytest.approx(0.0)
        assert v.valor_pis == pytest.approx(0.0)
        assert v.valor_cofins == pytest.approx(0.0)
        assert v.valor_csll == pytest.approx(0.0)
        # "ISS Retido\n2 - Não"
        assert v.iss_retido is False
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
