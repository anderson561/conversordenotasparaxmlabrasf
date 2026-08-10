# -*- coding: utf-8 -*-
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_NACIONAL

# Texto REAL do OCR (Tesseract) da pagina 3 do PDF "analise de notas SP-iss
# retido - inss retido.pdf" (062026) — DANFSe Nacional, Prefeitura Municipal
# de Varzea Grande/MT, nota real no 175 (ARMANDO CACAMBA LTDA -> SAO PEDRO
# CONSTRUTORA LTDA, locacao de cacambas, R$1.650,00). Preservado verbatim via
# repr() (inclusive os erros de OCR: "N?mero da NFS-e", "Servi?o eletr?nica").
#
# BUG real: toda DANFSe Nacional imprime o PROPRIO titulo "DANFSe v1.0" nos
# primeiros ~70 caracteres da pagina (logo apos o rotulo "Chave de Acesso da
# NFS-e") — mesmo com UMA UNICA nota na pagina. O split de multi-nota-por-
# pagina de `parse_multiple` (`headers_regex`) cortava nesse 1o "DANFSe",
# fatiando esse preambulo de boilerplate (sem CNPJ/valor nenhum) como uma
# nota-FANTASMA propria (numero "00000000", prestador/tomador = fragmento
# garbage "Servico eletronica") ANTES da nota real 175 — dando a impressao
# de "numero zero" para quem olha a 1a entrada da pagina.
MOCK_TEXT_PAGINA3 = 'ta\nNFSe Nota Fiscal de\nServiço eletrônica\n\nChave de Acesso da NFS-e\n\nDANFSe v1.0\nDocumento Auxiliar da NFS-e\n\n51084022202488708000169000000000017526050597242327\n\nNúmero da NFS-e\n175\n\nNúmero da DPS\nns\n\nEMITENTE DA NFS-e\nPrestador do Serviço\n\nNome / Nome Empresarial\nARMANDO CACAMBA LTDA\n\nEndereço\n\nAVENIDA DOUTOR ALEIXO RAMOS DA CONCEIÇÃO, 500, 23 DE\n\nSETEMBRO\nSimples Nacional na Data de Competência\n\nOptante - Microempresa ou Empresa de Pequeno Porte (ME/EPP)\nCNPJ/CPF/NIF\n\nTOMADOR DO SERVIÇO\n\nNome / Nome Empresarial\nSAO PEDRO CONSTRUTORA LTDA\n\nEndereço\n\nCompetência da NFS-e\n22/05/2026\n\nSério da DPS\n70000\n\nCNPJ/CPF / NIF\n02.488.708/0001-69\n\nData e Hora da emissão da NFS-e\n\n22/05/2026 16:18:47\n\nData e Hora da emissão da DPS\n\n22/05/2026 16:18:47\n\nInscrição Municipal\n117160\n\nE-mail\n\nvendas2Darmandocacamba.com.br\n\nMunicípio\nVárzea Grande - MT\n\nRegime de Apuração Tributária pelo SN\nRegime de apuração dos tributos federais e municipal pelo Simples Nacional\n\n03.051.741/0001-90\n\nInscrição Municipal\n\nE-mail\n\nMunicif\n\nplo\nPRAIA DE PAJUSSARA, 554, QUADRA 28 LOTE 09, VILAS DO ATLANTICO Lauro de Freitas - BA\nINTERMEDIÁRIO DO SERVIÇO NÃO IDENTIFICADO NA NFS-e\n\nSERVIÇO PRESTADO\n\nCódigo de Tributação Nacional\n07.09.01 - Varrição, coleta e remoção\nde lixo, rejeitos e outros res...\n\nDescrição do Serviço\n\nCódigo de Tributação Municipal\n\nSERVIÇO DE LOCAÇÃO DE CAÇAMBAS (3 X R$ 550,00)\n\nCEP: 78.049-005, CUIABA - MT\n\nLocal da Prestação\nCuiabá - MT\n\nPREFEITURA MUNICIPAL DE\n\nVÁRZEA GRANDE\n(65)3688-8230\ncentraldeissqnvg Ogmail. com\n\nA autenticidade desta NFS-e pode ser verificada\npela leitura deste código QR ou pela consulta da\nchave de acesso no portal nacional da NFS-e\n\nTelefone\n(00) 00000-0000\n\nCEP\n78110-703\n\nTelefone\n\nCEP\n42708-720\n\nPais da Prestação\n\nR$ 1.650,00. OBRA: CENTRO POLITICO ADMINISTRATIVO RUA TRÊS N 1271,\n\nTRIBUTAÇÃO MUNICIPAL\n\nTributação do ISSQN\nOperação Tributável\n\nTipo de Imunidade\n\nValor do Serviço\nRS 1.650,00\n\nBC ISSQN\n\nPaís Resultado da Prestação do Serviço Município de Incidência do ISSQN\n\nSuspensão da Exigibilidade do ISSQN\n\nNão\nDesconto Incondicionado\n\nAlíquota Aplicada\n\nCuiabá - MT\nNúmero Processo Suspensão\n\nTotal Deduções/Reduções\n\nRetenção do ISSQN\nNão Retido\n\nRegime Especial de Tributação\nNenhum\n\nBenefício Municipal\n\nCálculo do BM\n\nISSQN Apurado\n\nTRIBUTAÇÃO FEDERAL\nIRRF\n\nPIS - Débito Apuração Própria\n\nContribuição Previdenciária - Retida\n\nContribuições Sociais - Retidas\n\nCOFINS - Débito Apuração Própria\n\nVALOR TOTAL DA NFS-E\n\nValor do Serviço\nR$ 1.650,00\n\nTotal das Retenções Federais\n\nDesconto Condicionado\n\nDesconto Incondicionado\n\nPIS/COFINS - Débito Apur. Própria\n\nDescrição Contrib. Sociais - Retidas\n\nISSQN Retido\n\nValor Liquido da NFS-e\nR$ 1.650,00\n\nTOTAIS APROXIMADOS DOS TRIBUTOS\n\nFederais\n\nINFORMAÇÕES COMPLEMENTARES\n\nEstaduais\n\nSão Pedro Construtora\nObra MTI\n\nMunicipais\n\nSienge\n\nThiagó Guedes\nEng. Civil\nCREA-BA 052233594-2\n\n: Scanned with |:\nCamsScanner”;\n\n'

MOCK_TEXT_PAGINA_ANTERIOR = 'PREFEITURA MUNICIPAL DE OUTRA CIDADE\nNota Fiscal de Servicos\nNumero da Nota Fiscal: 1\nCNPJ: 11.111.111/0001-11\nPrestador: OUTRO PRESTADOR LTDA\nValor Total: R$ 100,00\n'


def test_detect_danfse_nacional_varzea_grande():
    dummy_path = "tests/dummy_danfse_varzea_grande.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    try:
        ex = SPPdfExtractor(dummy_path)
        ex.raw_text = MOCK_TEXT_PAGINA3
        assert ex._detect_layout() == LAYOUT_NACIONAL
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_parse_multiple_nao_gera_nota_fantasma_pagina_unica(monkeypatch):
    """Pagina com UMA UNICA DANFSe nao deve virar 2 notas (fantasma +
    real) — so a nota real (numero 175) deve sair, sem numero "00000000"."""
    dummy_path = "tests/dummy_danfse_varzea_grande_full.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    full_text = MOCK_TEXT_PAGINA_ANTERIOR + "\x0c" + MOCK_TEXT_PAGINA3

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: full_text)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()

        numeros = [n.numero for n in nfse_list]
        assert "00000000" not in numeros, (
            "Nota fantasma (numero 00000000) nao deveria existir para uma "
            f"pagina com uma unica DANFSe. Numeros extraidos: {numeros}"
        )

        varzea = [n for n in nfse_list if n.numero == "175"]
        assert len(varzea) == 1
        nota = varzea[0]
        assert nota.prestador.razao_social == "ARMANDO CACAMBA LTDA"
        assert nota.prestador.cnpj_cpf == "02488708000169"
        assert nota.tomador.razao_social == "SAO PEDRO CONSTRUTORA LTDA"
        # BUG 2 (mesma nota): a grade OCR intercalada vazava o CNPJ do
        # PRESTADOR pro bloco do TOMADOR (rotulo "CNPJ/CPF/NIF" comum a
        # ambas as entidades, linha fora de ordem) - tomador saia com o
        # MESMO CNPJ do prestador em vez do seu proprio (03.051.741/0001-90).
        assert nota.tomador.cnpj_cpf == "03051741000190"
        assert nota.tomador.cnpj_cpf != nota.prestador.cnpj_cpf
        assert nota.valores.valor_servicos == pytest.approx(1650.00)
        assert nota.valores.valor_liquido_nfse == pytest.approx(1650.00)
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
