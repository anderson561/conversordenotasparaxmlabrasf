# -*- coding: utf-8 -*-
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
import os

# Texto REAL do OCR (Tesseract) da pagina 15 do PDF
# "Notas_Fiscais_Recebidas_07.2026_-_Guarajuba_Suites.pdf": DANFSe v1.0 (padrao
# nacional, Municipio de Camacari/BA), layout danfse_nacional, nota no 4,
# prestador MEI (ANA PAULA RIBEIRO DA SILVA). RazaoSocial do prestador saia
# ERRADA (o proprio endereco: "RUA ITAIPU, S/N, MONTE GORDO (MONTE GORDO)
# Camacari - BA 42840-178") porque a linha "Nome / Nome Empresarial" e
# "E-mail" vem colada na mesma linha da grade com o nome do MEI e o e-mail
# ("ANA PAULA RIBEIRO DA SILVA 77853423500 ANAPAULAENEO1 (OGMAIL.COM"), e o
# OCR corrompeu o "@" em " (O" (com espaco espurio antes do parenteses) em
# vez das corrupcoes ja toleradas (Q/O/. colados sem espaco) -- a limpeza de
# e-mail nao reconhecia esse padrao, a linha inteira era descartada como
# invalida, e o fallback linha-a-linha acabava aceitando a linha de
# Endereco/Municipio/CEP (que nao tem nenhum rotulo reconhecido como ruido)
# como se fosse a razao social. Corrigido tolerando "(O"/"QO" (com espaco
# opcional antes) como forma corrompida do "@" na limpeza de e-mail.
MOCK_TEXT = "Prefeitura Municipal de Camaçari\nMunicípio de Camaçari\n(71)3621-6860\natendimento.cfis.sefaz(Ocamacari.ba.gov.br\nDisso\n— ar q E rh\nElisa\nA autenticidade desta NFS-e pode ser verificada\npela leitura deste código QR ou pela consulta da\nchave de acesso no portal nacional da NFS-e\n\na Municipal de Camaçari\n\ne Camaçari\n\n360\n\nD.cfis.sefaz(Dcamacari.ba.gov.br\nDisso\n— ar q E rh\nDesde\n\nade desta NFS-e pode ser verificada\n\ndeste código QR ou pela consulta da\n\nesso no portal nacional da NFS-e\n\n” non\n\nPrefeitura Municipal de Camaçari\nMunicípio de Camaçari\n(71)3621-6860\natendimento.cfis.sefazQOcamacari.ba.gov.br\nep a A eÉ o\n\nDA Raia\nA autenticidade desta NFS-e pode ser verificada\npela leitura deste código QR ou pela consulta da\nchave de acesso no portal nacional da NFS-e\n\npro a Prefeitura Municipal de Camaçari\nN FSo Nata Fiscal do DANFSe v1.0 É Município de Camaçari\ne e. ii 71)3621-6860\nPu SEPIÇO pigtrónica Documento Auxiliar da NFS-e pa\n\nmia sp me E MRE tee\nChave de Acesso da NFS-e Elias E]\n29057012237565722000101000000000000426074970943648 ES\n\nNúmero da NFS-e Competência da NFS-e Data e Hora da emissão da NFS-e PEA dino\n\n4 07/07/2026 07/07/2026 23:46:52 a\n\nNúmero da DPS Série da DPS Data e Hora da emissão da DPS Elisio\n\n4 70000 07/07/2026 23:46:52 A autenticidade desta NFS-e pode ser verificada\n\npela leitura deste código QR ou pela consulta da\nchave de acesso no portal nacional da NFS-e\n\nEMITENTE DA NFS-e CNPJ/CPF / NIF Inscrição Municipal Telefone\n\nPrestador do Serviço 37.565.722/0001-01 - (71) 8226-3080\n\nNome / Nome Empresarial E-mail\n\nANA PAULA RIBEIRO DA SILVA 77853423500 ANAPAULAENEO1 (OGMAIL.COM\n\nEndereço Município CEP\n\nRUA ITAIPU, S/N, MONTE GORDO (MONTE GORDO) Camaçari - BA 42840-178\n\nSimples Nacional na Data de Competência Regime de Apuração Tributária pelo SN\n\nOptante - Microempreendedor Individual (MEI) -\n\nTOMADOR DO SERVIÇO NÃO IDENTIFICADO NA NFS-e\nINTERMEDIÁRIO DO SERVIÇO CNPJ/CPF / NIF - Inscrição Municipal Telefone\n25.311.856/0001-09 - -\n\nNome / Nome Empresarial E-mail\n\nPH GESTAO E CONSULTORIA S.A. -\n\nEndereço Município CEP\n\nHUMAITA, S/N, COND GUARAJUBA S PREMIUS, GUARAJUBA (MONTE Camaçari - BA 42840-562\n\nGORDO)\n\nSERVIÇO PRESTADO\n\nCódigo de Tributação Nacional Código de Tributação Municipal Local da Prestação País da Prestação\n\n40.01.01 - Obras de arte sob - Camaçari - BA -\n\nencomenda.\n\nDescrição do Serviço .\n\nserviços de artesã\n\nTRIBUTAÇÃO MUNICIPAL\n\nTributação do ISSQN País Resultado da Prestação do Serviço Município de Incidência do ISSQN Regime Especial de Tributação\nOperação Tributável - Camaçari - BA Nenhum\n\nTipo de Imunidade Suspensão da Exigibilidade do ISSQN Número Processo Suspensão Benefício Municipal\n\n- Não : - - .\n\nValor do Serviço Desconto Incondicionado Total Deduções/Reduções Cálculo do BM\n\nR$ 1.574,25 - “ &\n\nBC ISSQN Alíquota Aplicada Retenção do ISSQN ISSQN Apurado\n\n- - Não Retido -\nTRIBUTAÇÃO FEDERAL\n\nIRRF Contribuição Previdenciária - Retida Contribuições Sociais - Retidas Descrição Contrib. Sociais - Retidas\nPIS - Débito Apuração Própria COFINS - Débito Apuração Própria\nVALOR TOTAL DA NFS-E\nValor do Serviço Desconto Condicionado Desconto Incondicionado ISSQN Retido\nR$ 1.574,25 - ' - -\nTotal das Retenções Federais PIS/COFINS - Débito Apur. Própria Valor Líquido da NFS-e\nw as R$ 1.574,25\nTOTAIS APROXIMADOS DOS TRIBUTOS\nFederais Estaduais Municipais\n\nINFORMAÇÕES COMPLEMENTARES\n"


def test_danfse_nacional_razao_social_prestador_nao_pega_endereco(monkeypatch):
    dummy_path = "tests/dummy_danfse_razao_endereco.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        assert nfse.numero == "4"
        assert nfse.prestador.cnpj_cpf == "37565722000101"

        # Nucleo do bug: a razao social do prestador (MEI) NAO pode ser o
        # endereco/municipio/CEP dele - tem que ser o nome real da grade
        # "Nome / Nome Empresarial", mesmo com o e-mail colado na mesma linha
        # e o "@" corrompido em " (O" pelo OCR.
        assert nfse.prestador.razao_social == "ANA PAULA RIBEIRO DA SILVA 77853423500"
        assert "RUA ITAIPU" not in nfse.prestador.razao_social
        assert "42840-178" not in nfse.prestador.razao_social
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
