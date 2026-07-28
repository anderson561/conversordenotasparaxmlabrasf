# -*- coding: utf-8 -*-
import os
import pytest
from src.extractors.pdf_extractor import (
    SPPdfExtractor,
    LAYOUT_NACIONAL,
)

# Texto REAL do OCR (Tesseract) de uma DANFSe Nacional (Documento Auxiliar da
# NFS-e) do MUNICÍPIO DO SALVADOR — nota real nº 21, CLEUSON ARAUJO DE CARVALHO
# (MEI) -> SÃO PEDRO CONSTRUTORA. Preservado verbatim, incluindo os quirks que
# travam as regressões dos 3 bugs corrigidos + o código de serviço:
#  - "DANFSo vi" e "NFS-g"/"NFS-«": o OCR corrompe os rótulos de cabeçalho, então
#    a detecção do layout casa por "Chave de Acesso" (o único âncora legível);
#  - o Número da NFS-e sai "2" (o OCR comeu o "1" de "21") ao lado do rótulo —
#    por isso o número REAL (21) vem decodificado da Chave de Acesso de 50 dígitos
#    (posições 24-36), fonte de verdade imune ao OCR;
#  - o DANFSe não tem "Código de Verificação": a Chave de Acesso de 50 dígitos é a
#    identidade/autenticidade da nota e preenche o <CodigoVerificacao> do XML;
#  - a grade de valores é "rótulo em cima / valor embaixo" com campos vazios "-";
#    "R$ 400,00" só é capturado por proximidade do rótulo próprio (os padrões
#    genéricos pescavam o número da nota como ISS e deixavam o valor zerado);
#  - MEI => BC/alíquota/ISS em branco ("-") => tributação zero, não retido;
#  - o código de serviço vem de "Código de Tributação Nacional 16.02.01" -> 1602
#    (sem este ramo, caía no default genérico "03115").
MOCK_OCR = 'MUNICIPIO DO SALVADOR\nPA DANFSo vi E) cnaooe-g080\nns Documento Auxiliar da NFS-e notasalvadorGDestaz salvador. ba.gow.br\n\nChave de Acesso da NFS-«\n29274082264795306000164000000000002126035522825447\nNúmero da NFS-e Competência da NFS-g Data e Hora da amissão da NFS-e a\n2 31/03/2026 31/03/2026 17:42:20 jo\nEChcopndo\nNúmero da DPS Sério da DPS Data 6 Hora da emissão da DPS Eis\n15 70000 31/03/2026 17:42:20 A autenticidade desta NFS-e pode ser verificada\npela leitura deste código QR qu pela consulta da\nchave de acesso no portal necional da NFS-e\nEMITENTE DA NFS-8 CNPJI CPF /NIF Inscrição Municipal Telefone\nPrestador do Serviço 64.795.306/0001-64 - (71) 8700-4565\nNome / None Empresaria! E-mail\n64.795.306 CLEUSON ARAUJO DE CARVALHO CACTRANSPOHOTMAIL.COM\nEndereço Município CEP\nRUA CRISTIANE ROSE, 76, DORON Salvador - BA 41194-090\nSimples Nacional na Deta de Competência Regime de Apuração Tributária pelo SN\nOptante - Microempreendedor Individual (MEI) -\nTOMADOR DO SERVIÇO CNPJ/CPF/NIF Inscrição Municipal Telefone\n03.051.741/0001-90 - -\nNome / Nome Empresarial E-mail\nSAO PEDRO CONSTRUTORA LTDA SPESAOPEDROCONSTRUTORA.COM.BR\nEndereço Município CEP\nPRAIA DE PAJUSSARA, 554, QUADRA 28 LOTE 09, VILAS DO ATLANTICO Lauro de Freitas - BA 42708-720\n\nINTERMEDIÁRIO DO SERVIÇO NÃO IDENTIFICADO NA NFS-e\nSERVIÇO PRESTADO\n\nCódigo de Tributação Nacional Código de Tributação Municipal Local da Prestação Pais da Prestação\n16.02.01 - Outros serviços de - Salvador - BA -\ntransporte de natureza municipal.\n\no do Serviço\nSERVIÇO DE FRETES TRANSPORTANDO DIVERSOS MATERIAIS referente vale 114 CONFORME SOLICITAÇÃO\n\nDEPOSITO BRADESCO\nAG 3571-8 CIC 156903-1\nPIX CELULAR 71 992542316\n\nTRIBUTAÇÃO MUNICIPAL\n\nTributação do ISSQN País Resultado da Prestação do Serviço Município de incidência do ISSQN Regime Especial de Tributação\nOperação Tributével - Salvador - BA Nenhum\n\nTipo de Imunidade Suspensão ds Exigibilidade do ISSON Número Processo Suspensão Benefício Municipal\n\n- Não - -\n\nValor do Serviço Desconto incondicionado Total Deduções/Raduções Cálculo do BM\n\nR$ 400,00 - - -\n\nBC ISSQN Alíquota Aplicada Retenção do ISSQN ISSQN Apurado\n\n- - Não Retido -\n\nTRIBUTAÇÃO FEDERAL\n\nIRRF Contribuição Previdenciária - Retida Contribuições Sociais - Retidas Descrição Contrib. Sociais - Retidas\nPIS - Débito Apuração Própria COFINS - Débito Apuração Própria\n\nVALOR TOTAL DA NFS-E\n\nbird do Eta Desconto Condicionado Desconto Incondicionado ISSQN Retido\n\nR$ 400, « - .\n\nTotal das Retenções Federais PIS/COFINS - Dóbito Apur. Própria Valor Líquido da NFS-e\n\n. - R$ 400,00\n\nTOTAIS APROXIMADOS DOS TRIBUTOS\n\nFederais Estaduais Municipais\n\nINFORMAÇÕES COMPLEMENTARES\nNBS: 105011110\n\nrá Ricarin Marques Azevad)\nL\n\nSão Edy emma\nPaulo Ga: SÃO PEDRO CONSTRUTORA\n\nGerente Adm. Financeiro cera | .ALI pass\nac SÍ\n'

# A Chave de Acesso de 50 dígitos codifica: IBGE (2927408=Salvador) + ambiente +
# tipo inscr. + CNPJ do emitente (64795306000164=Cleuson) + Número (posições
# 24-36 = "0000000000021" -> 21) + resto. É a fonte de verdade do número.
CHAVE = '29274082264795306000164000000000002126035522825447'


def test_detect_danfse_nacional():
    """A DANFSe é detectada como layout nacional mesmo com os rótulos de cabeçalho
    corrompidos pelo OCR ("DANFSo vi", "NFS-g"), casando pela âncora "Chave de
    Acesso"."""
    dummy_path = "tests/dummy_danfse_nacional.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    try:
        ex = SPPdfExtractor(dummy_path)
        ex.raw_text = MOCK_OCR
        ex.from_ocr = True
        assert ex._detect_layout() == LAYOUT_NACIONAL
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_extract_danfse_nacional_layout(monkeypatch):
    dummy_path = "tests/dummy_danfse_nacional_full.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    # PDF escaneado: pdfminer devolve ~nada, então o parse_multiple cai no OCR
    # (_extract_via_ocr -> MOCK_OCR), exatamente como em produção.
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_OCR)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        # BUG 1 — Número: o OCR ao lado do rótulo sai "2"; o número REAL (21) vem
        # decodificado da Chave de Acesso (posições 24-36). Bate com o nome do
        # arquivo original ("NFS 21").
        assert nfse.numero == "21"

        # BUG 3 — Chave de Acesso: o DANFSe não tem "Código de Verificação"; a
        # chave de 50 dígitos é a identidade da nota e preenche o
        # <CodigoVerificacao> (antes saía o placeholder "XXXX-XXXX").
        assert nfse.codigo_verificacao == CHAVE

        # Código de serviço a partir de "Código de Tributação Nacional 16.02.01"
        # (item LC 116 16.02) -> "1602" (antes caía no default "03115").
        assert nfse.servico_codigo == "1602"

        assert nfse.data_emissao.strftime("%d/%m/%Y") == "31/03/2026"
        assert nfse.competencia.strftime("%m/%Y") == "03/2026"

        # BUG 2 — Valores: R$ 400,00 (serviço = líquido). MEI => BC/alíquota/ISS
        # em branco ("-") => tributação zero, não retido. Antes: tudo zerado e
        # ISS pescava o "2" do número.
        v = nfse.valores
        assert v.valor_servicos == pytest.approx(400.00)
        assert v.valor_liquido_nfse == pytest.approx(400.00)
        assert v.base_calculo == pytest.approx(400.00)
        assert v.aliquota == pytest.approx(0.0)
        assert v.valor_iss == pytest.approx(0.0)
        assert v.iss_retido is False

        # Emitente (MEI) em Salvador/BA — IBGE 2927408 (registrado no resolver).
        assert nfse.prestador.cnpj_cpf == "64795306000164"
        assert nfse.prestador.endereco.codigo_municipio == "2927408"

        # Tomador em Lauro de Freitas/BA.
        assert nfse.tomador.cnpj_cpf == "03051741000190"

        # Nenhum aviso de baixa confiança: número, valor e chave agora extraídos
        # corretamente (antes havia "Valor dos serviços extraído como zero" e
        # "Código de verificação/autenticidade não encontrado").
        assert nfse.avisos == []
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
