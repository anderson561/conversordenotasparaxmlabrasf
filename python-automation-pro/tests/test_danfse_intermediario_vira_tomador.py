# -*- coding: utf-8 -*-
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
import os

# Texto REAL do OCR (Tesseract) da pagina 18 do PDF
# "Notas_Fiscais_Recebidas_05.2026_-_Guarajuba_Suites.pdf": DANFSe v1.0 (padrao
# nacional, Municipio do Salvador), layout danfse_nacional, nota no 44. O
# proprio documento imprime "TOMADOR DO SERVICO NAO IDENTIFICADO NA NFS-e" e
# lista a PH GESTAO como INTERMEDIARIO DO SERVICO. Regra de negocio (decisao do
# usuario 2026-08-04): quando o tomador vem nao identificado e ha intermediario,
# promover o intermediario a tomador e esvaziar o intermediario. Alem disso:
#  - municipio do intermediario/tomador: "Municipio" e cabecalho de coluna e o
#    valor real ("Camacari - BA") fica na linha de valores -> extraido pelo
#    padrao "<Cidade> - <UF> <CEP>" (Title Case pula os tokens de endereco em
#    caixa alta), resolvendo Camacari/BA 2905701 (nao Salvador 2927408).
#  - razao do intermediario limpa do " E" residual (inicial da coluna "E-mail").
MOCK_TEXT = 'HR MUNICIPIO DO SALVADOR\n- N ESe Mata Fiscal de DANFSe ví 0 (71)3202-8280\nServiço eletrônica Documento Auxiliar da NFS-e notasalvadorQsefaz.salvador.ba.gov.br\nChave de Acesso da NFS-e [Os 4]\n29274082249244210000114000000000004426057891821677 : dae\nNúmero da NFS-e Competência da NFS-e Data e Hora da emissão da NFS-e PESA\n44 12/05/2026 12/05/2026 16:58:01 RSS\nNúmero da DPS Série da DPS Data e Hora da emissão da DPS Eolhiyo pras\n5 70000 12/05/2026 16:58:01 A autenticidade desta NFS-e pode ser verificada\npela leitura deste código QR ou pela consulta da\nchave de acesso no portal nacional da NFS-e\nEMITENTE DA NFS-e CNPJ/CPF /NIF Inscrição Municipal Telefone\nPrestador do Serviço 49.244.210/0001-14 - (71) 9369-4457\nNome / Nome Empresarial E-mail\n49.244,210 THIAGO GUEDES DA SILVA THYAGO GUEDES 11QHOTMAIL.COM\nEndereço Município CEP\nRUA MARTACENIA, 70, AGUAS CLARAS Salvador - BA 41310-160\nSimples Nacional na Data de Competência Regime de Apuração Tributária pelo SN\nOptante - Microempreendedor Individual (MEI) -\nTOMADOR DO SERVIÇO NÃO IDENTIFICADO NA NFS-e\nINTERMEDIÁRIO DO SERVIÇO CNPJ /CPF/NIF Inscrição Municipal Telefone\n25.311.856/0001-09 - E\nNome / Nome Empresarial E-mail\nPH GESTAO E CONSULTORIA S.A. E\nEndereço ? Município CEP\nHUMAITA, S/N, COND GUARAJUBA S PREMIUS, GUARAJUBA (MONTE Camaçari - BA 42840-562\nGORDO)\nSERVIÇO PRESTADO\nCódigo de Tributação Nacional Código de Tributação Municipal Local da Prestação País da Prestação\n07.19.01 - Acompanhamento e - Camaçari - BA -\nfiscalização da execução de obras de\neng...\nDescrição do Serviço\nFRETES DE BOMBAS INCENDIO GUARAJUBA X SALVADOR X LAURO\n04 VIAGENS\nTRIBUTAÇÃO MUNICIPAL\nTributação do ISSQN País Resultado da Prestação do Serviço Município de Incidência do ISSQN Regime Especial de Tributação\nOperação Tributável - Camaçari - BA Nenhum\nTipo de Imunidade Suspensão da Exigibilidade do ISSQN Número Processo Suspensão Benefício Municipal\nz Não = E\nValor do Serviço Desconto Incondicionado Total Deduções/Reduções Cálculo do BM\nR$ 980,00 - - -\nBC ISSQN Alíquota Aplicada Retenção do ISSQN ISSQN Apurado\n= - Não Retido -\nTRIBUTAÇÃO FEDERAL\nIRRF Contribuição Previdenciária - Retida Contribuições Sociais - Retidas Descrição Contrib. Sociais - Retidas\nPIS - Débito Apuração Própria COFINS - Débito Apuração Própria\nVALOR TOTAL DA NFS-E\nValor do Serviço Desconto Condicionado Desconto Incondicionado ISSQN Retido\nR$ 980,00 - - -\nTotal das Retenções Federais PIS/COFINS - Débito Apur. Própria Valor Líquido da NFS-e\na 5 R$ 980,00\nTOTAIS APROXIMADOS DOS TRIBUTOS\nFederais Estaduais Municipais\nINFORMAÇÕES COMPLEMENTARES\nNBS: 101011200\n'


def test_danfse_intermediario_promovido_a_tomador(monkeypatch):
    dummy_path = "tests/dummy_danfse_interm.pdf"
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

        assert nfse.numero == "44"

        # Nucleo da regra: o tomador, que na nota vem "nao identificado", passa a
        # ser a PH GESTAO (que estava como intermediario).
        assert nfse.tomador.cnpj_cpf == "25311856000109"
        assert nfse.tomador.razao_social == "PH GESTAO E CONSULTORIA S.A."
        # Municipio do tomador promovido: Camacari/BA (2905701), NAO Salvador
        # (2927408, capital que o resolver pescava do cabecalho do documento).
        assert nfse.tomador.endereco.codigo_municipio == "2905701"
        assert nfse.tomador.endereco.uf == "BA"

        # Intermediario esvaziado (a mesma entidade nao fica nos dois papeis).
        assert nfse.intermediario is None

        # Prestador (emitente MEI) permanece; contexto.
        assert nfse.prestador.cnpj_cpf == "49244210000114"
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
