# -*- coding: utf-8 -*-
r"""Extração de retenções federais (IRRF, INSS, Contribuições Sociais
Retidas) no Portal Nacional (`LAYOUT_NACIONAL`) - achado a partir de um
pedido do usuário pra analisar a viabilidade de extrair PIS/COFINS/CSLL/
Contribuições Sociais/INSS/ISS/IRRF Retidos. Antes deste fix, `LAYOUT_NACIONAL`
(um dos layouts mais usados) nunca extraía NENHUM desses campos, mesmo toda
nota nesse padrão trazendo uma seção "TRIBUTAÇÃO FEDERAL" com IRRF,
"Contribuição Previdenciária - Retida" (INSS) e um campo COMBINADO
"Contribuições Sociais - Retidas" (soma de PIS+COFINS+CSLL, sem abertura
individual - por isso vai para um campo próprio `valor_contribuicoes_sociais_
retidas`, não split arbitrariamente entre PIS/COFINS/CSLL, e é somado a
`OutrasRetencoes` no XML por não haver tag ABRASF dedicada).

IMPORTANTE: "Contribuições Sociais - Retidas" é DIFERENTE de "PIS - Débito
Apuração Própria"/"COFINS - Débito Apuração Própria" (rótulos vizinhos na
mesma seção) - estes últimos são o débito TRIBUTÁRIO PRÓPRIO do prestador,
não retenção feita pelo tomador, e continuam intencionalmente NÃO extraídos.

Extração usa adjacência ESTRITA rótulo->valor (rótulo, quebra de linha,
"-" ou "R$ n,nn"/"R$ n.nn") - quando o pdfminer despeja todos os rótulos
desta seção juntos e os valores nunca aparecem no texto (achado real, ver
2º texto/nota abaixo), a âncora propositalmente NÃO casa, mantendo os
campos em 0.0 em vez de atribuir errado.

Textos REAIS extraídos via pdfminer, reaproveitados de fixtures já
existentes (mesmas notas, mesmo texto - nunca digitado à mão).
"""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_TEXT_CRICIUMA = 'DANFSEe v1.0\nDocumento Auxiliar da NFS-e\n\nPrefeitura Municipal de Criciúma\nSecretaria Municipal da Fazenda\n(48) 3431-0074\ntributos@criciuma.sc.gov.br\n\nChave de Acesso da NFS-e\nNFS42046082200910509001305000000073008026078018292222\n\nNúmero da NFS-e\n730080\n\nNúmero do DPS\n705742\n\nCompetência da NFS-e\n19/07/2026\n\nSérie da DPS\n1\n\nEMITENTE DA NFS-e\nPrestador de Serviço\n\nCNPJ / CPF / NIF\n00.910.509/0013-05\n\nData e Hora da emissão da NFS-e\n19/07/2026 22:06:43\n\nData e Hora de emissão da DPS\n17/07/2026 10:52:42\n\nInscrição Municipal\n\nTelefone\n(048) 3461-1000\n\nNome / Nome Empresarial\nTHOMSON REUTERS BRASIL CONTEUDO E TECNOLOGIA\n\nE-mail\nfaturamento@dominiosistemas.com.br\n\nEndereço\nAVENIDA CENTENARIO, 7405, NOSSA SENHORA\n\nSimples Nacional na Data de Competência\nNão Optante\n\nTOMADOR DO SERVIÇO\n\nCNPJ / CPF / NIF\n42.221.481/0001-05\n\nNome / Nome Empresarial\nCAFES FINOS VITORIA DA CONQUISTA LTDA\n\nEndereço\nROD KM 1070, 0, FELICIA\n\nMunicípio\nCriciuma - SC\n\nCEP\n88813-325\n\nRegime de Apuração Tributária pelo SN\n-\n\nInscrição Municipal\n\nE-mail\ncqscf@hotmail.com\n\nTelefone\n(77) 3423-3114\n\nMunicípio\nVITORIA DA CONQUISTA -\n\nCEP\n45028-135\n\nINTERMEDIÁRIO DO SERVIÇO NÃO IDENTIFICADO NA NFS-e\n\nSERVIÇO PRESTADO\nCódigo de Tributação Nacional\n010701 - Suporte tecnico em informatica, inclusive\ninstalacao, configuracao e manutencao de\nprogramas de computacao e bancos de dados.\n\nCódigo de Tributação Municipal\n-\n\nLocal da Prestação\nCriciuma - SC\n\nPaís da Prestação\n-\n\nDescrição do Serviço\nDESCRICAO DO ITEM: (Dominio Personalizado conf. contrato(s): 193024 comp.: 7/2026. - Valor: R$ 372,96)\nVENCIMENTOS: 10/08/2026 - 372,96\nOBSERVACAO: (Valor dos tributos incidentes (Lei no 12.741/2012) R$0,00.)\n\nTRIBUTAÇÃO MUNICIPAL\n\nTributação do ISSQN\nOperação Tributável\n\nTipo de Imunidade\n-\n\nValor do Serviço\nR$ 372.96\n\nBC ISSQN\nR$ 372.96\n\nTRIBUTAÇÃO FEDERAL\n\nIRRF\nR$ 0.00\n\nPaís Resultado da Prestação do Serviço\n-\n\nMunicípio de Incidência do ISSQN\nCriciúma/SC\n\nRegime Especial de Tributação\nNenhum\n\nSuspensão Exigibilidade ISSQN\n-\n\nNúmero Processo Suspensão\n-\n\nBenefício Municipal\n-\n\nDesconto Incondicionado\n-\n\nAlíquota Aplicada\n2.00%\n\nTotal Deduções/Reduções\nR$ 0.00\n\nRetenção do ISSQN\nNão Retido\n\nCálculo do BM\n-\n\nISSQN Apurado\nR$ 7.46\n\nContribuição Previdenciária - Retida\n-\n\nContribuições Sociais - Retidas\nR$ 17.34\n\nDescrição Contrib. Sociais Retidas\n3 - PIS/COFINS/CSLL Retidos\n\nPIS-Débito Apuração Própria\nR$ 2.42\n\nCOFINS - Débito Apuração Própria\nR$ 11.19\n\nVALOR TOTAL DA NFS-e\n\nValor do Serviço\nR$ 372.96\n\nDesconto Condicionado\n-\n\nDesconto Incondicionado\n-\n\nISSQN Retido\n-\n\nTotal das Retenções Federais\nR$ 17.34\n\nPIS/COFINS  - Débito Apur. Própria\nR$ 13.61\n\nValor Líquido da NFS-e\nR$ 355.62\n\nTOTAIS APROXIMADOS DOS TRIBUTOS\n\nFederais\n0,00\n\nEstaduais\n0,00\n\nMunicipais\n0,00\n\nINFORMAÇÕES COMPLEMENTARES\n\nNBS: 115013000\n'

MOCK_TEXT_SEM_RETENCAO = 'HR MUNICIPIO DO SALVADOR\n- N ESe Mata Fiscal de DANFSe ví 0 (71)3202-8280\nServiço eletrônica Documento Auxiliar da NFS-e notasalvadorQsefaz.salvador.ba.gov.br\nChave de Acesso da NFS-e [Os 4]\n29274082249244210000114000000000004426057891821677 : dae\nNúmero da NFS-e Competência da NFS-e Data e Hora da emissão da NFS-e PESA\n44 12/05/2026 12/05/2026 16:58:01 RSS\nNúmero da DPS Série da DPS Data e Hora da emissão da DPS Eolhiyo pras\n5 70000 12/05/2026 16:58:01 A autenticidade desta NFS-e pode ser verificada\npela leitura deste código QR ou pela consulta da\nchave de acesso no portal nacional da NFS-e\nEMITENTE DA NFS-e CNPJ/CPF /NIF Inscrição Municipal Telefone\nPrestador do Serviço 49.244.210/0001-14 - (71) 9369-4457\nNome / Nome Empresarial E-mail\n49.244,210 THIAGO GUEDES DA SILVA THYAGO GUEDES 11QHOTMAIL.COM\nEndereço Município CEP\nRUA MARTACENIA, 70, AGUAS CLARAS Salvador - BA 41310-160\nSimples Nacional na Data de Competência Regime de Apuração Tributária pelo SN\nOptante - Microempreendedor Individual (MEI) -\nTOMADOR DO SERVIÇO NÃO IDENTIFICADO NA NFS-e\nINTERMEDIÁRIO DO SERVIÇO CNPJ /CPF/NIF Inscrição Municipal Telefone\n25.311.856/0001-09 - E\nNome / Nome Empresarial E-mail\nPH GESTAO E CONSULTORIA S.A. E\nEndereço ? Município CEP\nHUMAITA, S/N, COND GUARAJUBA S PREMIUS, GUARAJUBA (MONTE Camaçari - BA 42840-562\nGORDO)\nSERVIÇO PRESTADO\nCódigo de Tributação Nacional Código de Tributação Municipal Local da Prestação País da Prestação\n07.19.01 - Acompanhamento e - Camaçari - BA -\nfiscalização da execução de obras de\neng...\nDescrição do Serviço\nFRETES DE BOMBAS INCENDIO GUARAJUBA X SALVADOR X LAURO\n04 VIAGENS\nTRIBUTAÇÃO MUNICIPAL\nTributação do ISSQN País Resultado da Prestação do Serviço Município de Incidência do ISSQN Regime Especial de Tributação\nOperação Tributável - Camaçari - BA Nenhum\nTipo de Imunidade Suspensão da Exigibilidade do ISSQN Número Processo Suspensão Benefício Municipal\nz Não = E\nValor do Serviço Desconto Incondicionado Total Deduções/Reduções Cálculo do BM\nR$ 980,00 - - -\nBC ISSQN Alíquota Aplicada Retenção do ISSQN ISSQN Apurado\n= - Não Retido -\nTRIBUTAÇÃO FEDERAL\nIRRF Contribuição Previdenciária - Retida Contribuições Sociais - Retidas Descrição Contrib. Sociais - Retidas\nPIS - Débito Apuração Própria COFINS - Débito Apuração Própria\nVALOR TOTAL DA NFS-E\nValor do Serviço Desconto Condicionado Desconto Incondicionado ISSQN Retido\nR$ 980,00 - - -\nTotal das Retenções Federais PIS/COFINS - Débito Apur. Própria Valor Líquido da NFS-e\na 5 R$ 980,00\nTOTAIS APROXIMADOS DOS TRIBUTOS\nFederais Estaduais Municipais\nINFORMAÇÕES COMPLEMENTARES\nNBS: 101011200\n'


def test_danfse_nacional_extrai_retencoes_federais_nota_730080(monkeypatch):
    """Nota real nº 730080 (Thomson Reuters -> Cafés Finos Vitória da
    Conquista, Criciúma/SC): IRRF e INSS saem "-" (zero, sem retenção), mas
    "Contribuições Sociais - Retidas" traz R$ 17,34 (PIS+COFINS+CSLL
    somados) - antes deste fix, saía 0.0 silenciosamente."""
    dummy_path = "tests/dummy_danfse_retencoes_730080.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT_CRICIUMA)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        v = nfse_list[0].valores

        assert v.valor_ir == pytest.approx(0.0)
        assert v.valor_inss == pytest.approx(0.0)
        assert v.valor_contribuicoes_sociais_retidas == pytest.approx(17.34)
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_danfse_nacional_retencoes_ficam_zero_quando_rotulos_sem_valor_no_texto(monkeypatch):
    """Regressão: em notas onde o pdfminer despeja TODOS os rótulos da seção
    "TRIBUTAÇÃO FEDERAL" juntos numa linha, sem NENHUM valor aparecendo logo
    depois (nem "-" nem "R$..."), os 3 campos devem ficar em 0.0 - nunca
    atribuir o valor de um rótulo vizinho (ex.: "Valor Líquido da NFS-e")
    por engano."""
    dummy_path = "tests/dummy_danfse_retencoes_sem_valor.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT_SEM_RETENCAO)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        v = nfse_list[0].valores

        assert v.valor_ir == pytest.approx(0.0)
        assert v.valor_inss == pytest.approx(0.0)
        assert v.valor_contribuicoes_sociais_retidas == pytest.approx(0.0)
        # Confere que o valor real da nota (não-zero) NÃO vazou pra esses campos
        assert v.valor_servicos == pytest.approx(980.00)
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_abrasf_transformer_soma_contribuicoes_sociais_em_outras_retencoes():
    """`OutrasRetencoes` (XML ABRASF) não tem tag própria para o valor
    combinado "Contribuições Sociais Retidas" - o transformer soma
    `outras_retencoes` + `valor_contribuicoes_sociais_retidas`."""
    from datetime import datetime
    from src.models.nfse_models import Nfse, Entidade, Endereco, Valores
    from src.transformers.abrasf_transformer import Abrasf201Transformer

    endereco = Endereco(logradouro="Rua X", numero="1", bairro="Centro",
                         codigo_municipio="4204202", municipio="Criciuma", uf="SC", cep="88800000")
    entidade = Entidade(cnpj_cpf="12345678000199", razao_social="Teste LTDA", endereco=endereco)
    valores = Valores(valor_servicos=100.0, base_calculo=100.0, aliquota=0.02,
                       valor_liquido_nfse=100.0, outras_retencoes=5.0,
                       valor_contribuicoes_sociais_retidas=17.34)
    nfse = Nfse(numero="1", codigo_verificacao="ABC", data_emissao=datetime(2026, 1, 1),
                competencia=datetime(2026, 1, 1), prestador=entidade, tomador=entidade,
                discriminacao="Teste", servico_codigo="0101", valores=valores)

    xml = Abrasf201Transformer().transform(nfse)
    assert "<OutrasRetencoes>22.34</OutrasRetencoes>" in xml
