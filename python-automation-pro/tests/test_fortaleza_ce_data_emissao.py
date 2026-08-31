# -*- coding: utf-8 -*-
import os
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_FORTALEZA

# Texto REAL extraído por pdfminer (`extract_text`) da NFS-e nº 109 de
# Fortaleza/CE (RESCUE SOLUCOES AMBIENTAIS LTDA -> TEMIS PROJETOS DE MEIO
# AMBIENTE E SUSTENTABILIDADE LTDA, PDF digital, sem OCR). Preservado
# verbatim - o cabeçalho é uma grade multi-colunas que o pdfminer despeja
# fora de ordem visual: o valor "19/12/2025 13:02:43" sai logo após o
# título da nota (linha 4), ANTES de qualquer rótulo, enquanto "Data e
# Hora da Emissão" só aparece bem mais abaixo (perto de "Número do RPS"),
# sem nenhum valor colado depois dele. Sem uma âncora dedicada no título,
# o loop genérico de rótulos (que exige rótulo seguido do valor) não casa
# com nada e cai no fallback `datetime.now()` - achado real: a nota
# convertida saiu com a data de HOJE em vez de 19/12/2025.
MOCK_TEXT = 'PREFEITURA MUNICIPAL DE FORTALEZA\nSECRETARIA MUNICIPAL DAS FINANÇAS\nNOTA FISCAL ELETRÔNICA DE SERVIÇO - NFS-e\n19/12/2025 13:02:43\n\nCompetência\n\n12/2025\n\nCódigo de Verificação\n\nNúmero da\nNFS-e\n109\n\n488231688\n\nNo. NFS-e substituída\n\nLocal da Prestação\n\nFORTALEZA - CE\n\nData e Hora da Emissão\n\nNúmero do RPS\n\nDADOS DO PRESTADOR DE SERVIÇOS\n\nRazão Social/Nome\n\nRESCUE SOLUCOES AMBIENTAIS LTDA\n\nNome Fantasia\n\nRESCUE - RESGATE, LEVANTAMENTO E MONITORAMENTO DE FAUNA\n\nCPF/CNPJ\n\n34.372.812/0001-80\n\nInsc Municipal\n\n0509065-2\n\nMunicípio\n\nFORTALEZA - CE\n\nEndereço e CEP\n\nR MONTEVIDEU,513 - SERRINHA CEP:60.741-560\n\nComplemento\n\nLETRA B\n\nTelefone\n\nE-mail\n\nbiologo.danilo@gmail.com\n\nDADOS DO TOMADOR DE SERVIÇOS\n\nRazão Social/Nome\n\nTEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDA\n\nCPF/CNPJ\n\n07.345.543/0001-90\n\nInscrição Municipal\n\nMunicípio\n\nSALVADOR - BA\n\nEndereço e CEP\n\nR TERRITORIO DO AMAPA, 146 - Pituba CEP: 41.830-540\n\nComplemento\n\ncasa 2\n\nTelefone\n\n(71)9992-38232\n\nE-mail\n\nmarcelscarton@temis-es.com.br\n\nDISCRIMINAÇÃO DOS SERVIÇOS\n\nRelatório de Monitoramento de Fauna Alada no Complexo Eólico Ventos de São Clemente, PE\nCampanha: Novembro/2025\nParcela 2/2\nDADOS BANCÁRIOS\nBanco 0260 Nu pagamentos S.A\nAgência 0001\ncc 46244051-5\nChave pix (CNPJ): 34372812000180\n\n17.02 / 821999901 - PREPARAÇÃO DE DOCUMENTOS E SERVIÇOS ESPECIALIZADOS DE APOIO ADMINISTRATIVO NÃO ESPECIFICADOS\nANTERIORMENTE\n\nDETALHAMENTO ESPECÍFICO DA CONSTRUÇÃO CIVIL\n\nCÓDIGO DE ATIVIDADE CNAE\n\nCódigo da Obra\n\nCódigo ART\n\nTRIBUTOS FEDERAIS\n\nPIS\n\nCOFINS\n\nIR(R$)\n\nINSS(R$)\n\nCSLL(R$)\n\nDetalhamento de Valores - Prestador dos Serviços\n\nCálculo do ISSQN devido no Município\n\nValor dos Serviços R$\n\n8.000,00\n\nNatureza Operação\n\nValor dos Serviços R$\n\n8.000,00\n\n(-) Desconto Incondicionado\n\n1-Tributação no Município\n\n(-) Deduções Permitidas em Lei\n\n(-) Desconto Condicionado\n\nRegime especial Tributação\n\n(-) Desconto Incondicionado\n\n(-) Retenções Federais\n\n0,00\n\n6-Microempresário e Empresa de\n\nBase de Cálculo\n\nOutras Retenções\n\nOpção Simples Nacional\n\n(X) Alíquota %\n\n8.000,00\n\n2,93\n\n(-) ISS Retido\n\n0,00\n\n1 - Sim\n\nISS a reter\n\n( ) Sim (X) Não\n\n(=) Valor Líquido      R$\n\n8.000,00\n\nIncentivador Cultural\n\n2 - Não\n\n(=) Valor do ISS R$\n\n234,40\n\nAvisos\n\n1- Uma via desta Nota Fiscal será enviada através do e-mail fornecido pelo Tomador dos Serviços, no sítio http://iss.fortaleza.ce.gov.br\n2- A autenticidade desta Nota Fiscal poderá ser validada no site http://iss.fortaleza.ce.gov.br/, com a utilização do Código de Verificação.\n3- Documento emitido por ME ou EPP optante pelo Simples Nacional. Não gera direito a crédito fiscal de ISS e IPI.\n4- Serviço sujeito ao ANEXO 3.\n5- Serviços não sujeitos ao fator "r" e tributados pelo Anexo III, exceto para o exterior, sem retenção, com ISS devido ao próprio Município.\n\n\x0c'


def test_detect_layout_fortaleza():
    dummy_path = "tests/dummy_fortaleza_data_emissao.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    try:
        ex = SPPdfExtractor(dummy_path)
        ex.raw_text = MOCK_TEXT
        assert ex._detect_layout() == LAYOUT_FORTALEZA
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_extract_fortaleza_data_emissao_nfse_109(monkeypatch):
    """Achado real: a NFS-e nº 109 (Fortaleza/CE) saía com a DataEmissao do
    dia da conversão (fallback `datetime.now()`) em vez de 19/12/2025
    13:02:43, porque o cabeçalho multi-coluna faz o pdfminer despejar o
    valor da data ANTES do rótulo "Data e Hora da Emissão" (que fica sem
    nenhum valor colado depois). Os demais campos (número, competência,
    prestador/tomador, valores) já eram extraídos corretamente antes deste
    fix e ficam aqui como guarda de regressão."""
    dummy_path = "tests/dummy_fortaleza_data_emissao_full.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        assert nfse.numero == "109"
        assert nfse.codigo_verificacao == "488231688"
        assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "19/12/2025 13:02:43"
        assert nfse.competencia.year == 2025
        assert nfse.competencia.month == 12

        p = nfse.prestador
        assert p.cnpj_cpf == "34372812000180"
        assert p.razao_social == "RESCUE SOLUCOES AMBIENTAIS LTDA"

        t = nfse.tomador
        assert t.cnpj_cpf == "07345543000190"
        assert t.razao_social == "TEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDA"

        v = nfse.valores
        assert v.valor_servicos == 8000.00
        assert v.valor_iss == 234.40
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
