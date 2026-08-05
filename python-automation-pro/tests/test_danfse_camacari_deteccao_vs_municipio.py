# -*- coding: utf-8 -*-
"""DANFSe Nacional emitida pela Prefeitura de Camaçari era roteada para o layout
municipal (Forma A do gotcha de colisões).

Nota real nº 3 (ANA PAULA RIBEIRO DA SILVA MEI -> PH GESTÃO como INTERMEDIÁRIO,
tomador "NÃO IDENTIFICADO"), pág. 11 do lote Guarajuba Suítes 06/2026. A DANFSe
traz "Prefeitura Municipal de Camaçari" no cabeçalho, que casava o check
`PREFEITURA MUNICIPAL DE CAMAÇARI` (em _detect_layout) ANTES do check da DANFSe
Nacional → a nota virava `camacari_ba_scan`/`camacari_cpqd`, o parser DANFSe e a
regra intermediário→tomador (ambos gated em LAYOUT_NACIONAL) não rodavam, e o
tomador não era extraído.

Fix (aditivo): check estreito e inequívoco (DANFSe v\\d | Documento Auxiliar da
NFS-e) no TOPO de _detect_layout e _detect_layout_page. Com a detecção correta, a
regra existente promove o intermediário (PH GESTÃO) a tomador.
"""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_NACIONAL

MOCK_OCR = 'Prefeitura Municipal de Camaçari\nMunicípio de Camaçari\n(71)3621-6860\natendimento.cfis.sefaz(Dcamacari.ba.gov.br\nsean a is o —\n[gr Eee [8]\nPESOS Ee RE\nGORETE\n[elias gas\nA autenticidade desta NFS-e pode ser verificada\npela leitura deste código QR ou pela consulta da\nchave de acesso no portal nacional da NFS-e\n\nra Municipal de Camaçari\nje Camaçari\n860\no.cfis.sefaz(Dcamacari.ba.gov.br\n[Jg Eee [8]\nEE o me\nRo\nGems E faN a\nElba rss\njade desta NFS-e pode ser verificada\ndeste código QR ou pela consulta da\ncesso no portal nacional da NFS-e\ne onon\n\nPrefeitura Municipal de Camaçari\nMunicípio de Camaçari\n(71)3621-6860\natendimento.cfis.sefaz(Ocamacari.ba.gov.br\nElisio E]\nRES Er E\nElba Eras\nA autenticidade desta NFS-e pode ser verificada\npela leitura deste código QR ou pela consulta da\nchave de acesso no portal nacional da NFS-e\n\n? e e" união Prefeitura Municipal de Camaçari\nFSe Mota Fiscold DANFSe v1.0 Município de Camaçari\nEa Cod cioia Fistuídio ali EB 71)3621-6860\né Sa Ns Serviço eletrônica Documento Auxiliar da NFS-e : rola carmen gor\nO LN [NO >>> &fmimemo sis selozGcamacanbagovd\nChave de Acesso da NFS-e Elias E]\n29057012237565722000101000000000000326066635033002 EE qi\nNúmero da NFS-e Competência da NFS-e Data e Hora da emissão da NFS-e PEA e :\n3 05/06/2026 05/06/2026 22:06:04 ON CEE ja\nTR E\nNúmero da DPS Série da DPS Data e Hora da emissão da DPS Elas será\n3 70000 05/06/2026 22:06:04 A autenticidade desta NFS-e pode ser verificada\npela leitura deste código QR ou pela consulta da\nchave de acesso no portal nacional da NFS-e\nEMITENTE DA NFS-e CNPJ/CPF /NIF Inscrição Municipal Telefone\nPrestador do Serviço 37.565.722/0001-01 - - (71) 8226-3080\nNome / Nome Empresarial E-mail\nANA PAULA RIBEIRO DA SILVA 77853423500 ANAPAULAENEO1 OGMAIL.COM\nEndereço Município CEP\nRUA ITAIPU, S/N, MONTE GORDO (MONTE GORDO) Camaçari - BA 42840-178\nSimples Nacional na Data de Competência Regime de Apuração Tributária pelo SN\nOptante - Microempreendedor Individual (MEI) -\nTOMADOR DO SERVIÇO NÃO IDENTIFICADO NA NFS-e\nINTERMEDIÁRIO DO SERVIÇO CNPJ/CPF/NIF Inscrição Municipal Telefone\n25.311.856/0001-09 - -\nNome / Nome Empresarial E-mail\nPH GESTAO E CONSULTORIA S.A. -\nEndereço Município CEP\nHUMAITA, S/N, COND GUARAJUBA S PREMIUS, GUARAJUBA (MONTE Camaçari - BA 42840-562\nGORDO)\nSERVIÇO PRESTADO\nCódigo de Tributação Nacional Código de Tributação Municipal Local da Prestação País da Prestação\n40.01.01 - Obras de arte sob - Camaçari - BA , -\nencomenda.\nDescrição do Serviço :\nserviços de artesã, peças em crochê.\nTRIBUTAÇÃO MUNICIPAL , É\nTributação do ISSQN País Resultado da Prestação do Serviço Município de Incidência do ISSQN Regime Especial de Tributação\nOperação Tributável - Camaçari - BA Vo Nenhum\nTipo de Imunidade Suspensão da Exigibilidade do ISSQN Número Processo Suspensão - Benefício Municipal\n- Não | - ER\nValor do Serviço Desconto Incondicionado Total Deduções/Reduções Cálculo do BM\nR$ 2.105,00 - o - -\nBC ISSQN Alíquota Aplicada Retenção do ISSQN ISSQN Apurado\n- - Não Retido -\nTRIBUTAÇÃO FEDERAL\nIRRF Contribuição Previdenciária - Retida Contribuições Sociais - Retidas Descrição Contrib. Sociais - Retidas\nPIS - Débito Apuração Própria COFINS - Débito Apuração Própria\nVALOR TOTAL DA NFS-E\nValor do Serviço Desconto Condicionado Desconto Incondicionado ISSQN Retido\nR$ 2.105,00 - À - -\nTotal das Retenções Federais PIS/COFINS - Débito Apur. Própria * Valor Líquido da NFS-e\n- - R$ 2.105,00\nTOTAIS APROXIMADOS DOS TRIBUTOS\nFederais Estaduais Municipais\nINFORMAÇÕES COMPLEMENTARES\n'


def test_danfse_de_camacari_detecta_nacional_nao_municipal():
    ext = SPPdfExtractor("x")
    ext.raw_text = MOCK_OCR
    ext.from_ocr = True
    # Antes do fix: caía em camacari_ba_scan/camacari_cpqd (marca do município
    # no cabeçalho). O check estreito de DANFSe no topo tem prioridade.
    assert ext._detect_layout() == LAYOUT_NACIONAL
    assert ext._detect_layout_page(MOCK_OCR) == LAYOUT_NACIONAL


def test_tomador_promovido_do_intermediario_apos_deteccao_correta(monkeypatch):
    dummy_path = "tests/dummy_danfse_camacari.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_OCR)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]
        assert nfse.numero == "3"

        # Tomador vem do INTERMEDIÁRIO promovido (regra de negócio de 08-04),
        # possível só porque a detecção agora acerta o layout nacional.
        tm = nfse.tomador
        assert tm.cnpj_cpf == "25311856000109"
        assert tm.razao_social.startswith("PH GESTAO E CONSULTORIA")
        assert tm.endereco.codigo_municipio == "2905701"  # Camaçari
        assert tm.endereco.uf == "BA"
        # Intermediário esvaziado (a mesma entidade não fica nos dois papéis).
        assert nfse.intermediario is None
        # Trava de regressão do bug: NUNCA o sentinela de tomador não identificado.
        assert tm.cnpj_cpf != "00000000000100"
        assert "IDENTIFICADO" not in tm.razao_social.upper()
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
