# -*- coding: utf-8 -*-
r"""BIO CONTROL DESINSETIZADORA LTDA (CNPJ 04.811.846/0001-62, Lauro de
Freitas/BA) -> BONI TRANSPORTES, LOGISTICA E COMERCIO LTDA, nota nº
202600000036345, R$5.200,00 (dedetização/controle de pragas urbanas) -
achado no pedido do usuário "criar plano de ação para o layout lauro de
freitas-biocontrol". Antes deste layout: a nota caía inteira em
LAYOUT_GENERICO (0 notas, "Layout não reconhecido") - já existiam 2 outros
sistemas diferentes para o MESMO município (LAYOUT_LAURO_FREITAS, a
Prefeitura oficial, e LAYOUT_PASSWORD_ENOTAS, a plataforma eNotas Gateway),
mas nenhum deles casa com o template próprio "DEMONSTRATIVO DA NOTA FISCAL
DE SERVIÇO" da BioControl.

PDF escaneado (OCR). A leitura de página inteira (zoom 3x) já extrai bem os
blocos de entidade e o resumo em texto livre, mas embaralha 2 grades densas
(linha "Tributação de Serviços" - Código LC 116 sai "743" em vez de "7.13";
e a dupla "Tributos Federais"/"Impostos sobre serviços ISSQN" - PIS/COFINS/
IR saem com os valores trocados, Alíquota/Valor ISS somem). Confirmado
visualmente contra o render real da página (render em zoom 3x): os valores
corretos são Outras Retenções=0,00, PIS=33,80, COFINS=156,00, IR=52,00,
INSS=572,00, CSLL=52,00, Alíquota ISS=5,00%, Valor ISS=260,00 - recuperados
por um recorte dedicado em zoom 8x de cada linha (`_ocr_recut_biocontrol`).

Texto OCR real capturado via `SPPdfExtractor._extract_via_ocr()` (mesmo
caminho usado em produção - já reflete o texto combinado zoom 3x + recorte
8x). Gerado por script (nunca digitado à mão) para preservar quirks de OCR
exatos, conforme convenção do projeto.
"""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_BIOCONTROL
from src.transformers.abrasf_transformer import Abrasf201Transformer

MOCK_OCR = 'Código LC 116: 7.13\nValor Outras Retenções: 0,00\nValor PIS: 33,80\nValor COFINS: 156,00\nValor IR: 52,00\nValor INSS: 572,00\nValor CSLL: 52,00\nValor Total dos Serviços: 5.200,00\nValor Descontos: 0,00\nDedução da Base de cálculo: 0,00\nBase de cálculo: 5.200,00\nAlíquota ISS: 5,00\nValor ISS: 260,00\nBioControl\n\nDEMONSTRATIVO DA NOTA FISCAL DE SERVIÇO Número da NFS-e\nEmitida em Lauro de Freitas (BA)\n202600000036345\nData de Emissão Competência Local da Prestação Código de Verificação Série | Número RPS\n06/07/2026 07:46:49 07/2026 Lauro de Freitas - BA B0416E1B5 NFSE - 40870\nDados do Prestador\nRazão Social CNPJ\nBIO CONTROL DESINSETIZADORA LTDA 04.811.846/0001-62\nNome Fantasia . Inscrição Municipal\nBIO CONTROL UNIPRAG 0000368040011\nEndereço Número Complemento\nRua Candido Rissut 99 Galpao 01\nBairro Município CEP Telefone\nRecreio Ipitanga Lauro de Freitas-BA 42700590 (71) 3283-4200\nE-mail\nadministrativoObiocontrolbahia.com.br E\nDados do Tomador\nRazão Social CNPJ\nBONI TRANSPORTES, LOGISTICA E COMERCIO LTDA 04.555.283/0003-50\n| Nome Fantasia Inscrição Municipal\n\nBONI LOGISTICA LTDA.\n\nEndereço Número Complemento\n\nRUA MARIA QUITERIA,263 00 GALPAO LOT DESMEMBRAMENTO\nBairro Município CEP Telefone\n\nITINGA Lauro de Freitas-BA 42738205 (71) 98199-5176\n\nE-mail E\n\nfoliveiraDbonialimentos.com.br\n\nDetalhamento dos Serviços\nTERMONEBULIZACAO, ATOMIZACAO, CONTROLE DE BARATAS, MOSCAS, FORMIGAS, TRACAS DE CEREAIS E ROEDORES\n\nRetencao para a Previdencia Social (11%): R$ 572,00\nRetencao IRRF (1%): R$ 52,00\nRetencao PIS/COFINS/CSLL (4,65%): R$ 241,80\n\nValor Liquido R$ 4.334,20\n\nInformações sobre os serviços prestados\nTributação de Serviços\n1 - Operação tributável / Tributado no município\n\nRegime Especial Tributação\n\nCódigo LC 116\n743\n\nSimples Nacional\nNão\nLei de Transparência de Impostos\n\nAlíquota IBPT Valor IBPT\n0,00 % 0,00\n\nValor IR (1,00%)\n\nCódigo do Serviço Código NBS\n\n8122200\n\nIncentivador Cultural\n\nRetem ISS\n\nNão Não\n\nConstrução Civil\n\nCódigo da Obra Código ART\n\nFonte / Chave\n\nValor INSS (11,00%) Valor CSLL (1,00%)\n572,00 52,00\n\nValor ISS\n\nTributos Federais\nValor Outras Retenções\n\nValor PIS (0,65%) Valor COFINS (3,00%)\n\n156,00 52,00\n\nBase de cálculo\n5.200,00\n\npostos sobre serviços ISSQN\nValor Total dos Serviços R$\n5.200,00\n\nValor Descontos Aliquota ISS\n\nDedução da Base de cálculo\n0,00\n\nValor líquido da NFS-e R$ 4.334,20\n\nObservações\nL |\n\n'


def test_detect_layout_biocontrol():
    dummy_path = "tests/dummy_biocontrol.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    try:
        ex = SPPdfExtractor(dummy_path)
        ex.raw_text = MOCK_OCR
        assert ex._detect_layout() == LAYOUT_BIOCONTROL
        assert ex._detect_layout_page(MOCK_OCR) == LAYOUT_BIOCONTROL
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_extract_biocontrol_nota_36345(monkeypatch):
    """Regressão: garante que a nota vira exatamente 1 `Nfse` (não cai mais
    em LAYOUT_GENERICO) com entidades/valores REAIS do documento - inclusive
    os campos que a leitura de página inteira embaralha (PIS/COFINS/IR/
    Alíquota-Valor ISS), corrigidos pelo recorte dedicado."""
    dummy_path = "tests/dummy_biocontrol_full.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_OCR)

    try:
        nfse_list = SPPdfExtractor(dummy_path).parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        assert nfse.avisos == []
        assert nfse.numero == "202600000036345"
        assert nfse.codigo_verificacao == "B0416E1B5"
        assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "06/07/2026 07:46:49"
        assert nfse.competencia.strftime("%m/%Y") == "07/2026"
        assert nfse.servico_codigo == "0713"
        assert "TERMONEBULIZACAO" in nfse.discriminacao
        assert "ROEDORES" in nfse.discriminacao
        assert nfse.municipio_incidencia_override is None

        assert nfse.prestador.cnpj_cpf == "04811846000162"
        assert nfse.prestador.inscricao_municipal == "0000368040011"
        assert nfse.prestador.razao_social == "BIO CONTROL DESINSETIZADORA LTDA"
        assert nfse.prestador.endereco.logradouro == "Rua Candido Rissut"
        assert nfse.prestador.endereco.numero == "99"
        assert nfse.prestador.endereco.complemento == "Galpao 01"
        assert nfse.prestador.endereco.bairro == "Recreio Ipitanga"
        assert nfse.prestador.endereco.municipio == "Lauro de Freitas"
        assert nfse.prestador.endereco.uf == "BA"
        assert nfse.prestador.endereco.codigo_municipio == "2919207"
        assert nfse.prestador.endereco.cep == "42700590"
        # OCR lê o "@" como uma letra maiúscula solta ("administrativoO..."):
        # confirma que o e-mail sai corrigido, não com a letra de ruído.
        assert nfse.prestador.email == "administrativo@biocontrolbahia.com.br"

        assert nfse.tomador.cnpj_cpf == "04555283000350"
        assert nfse.tomador.razao_social == "BONI TRANSPORTES, LOGISTICA E COMERCIO LTDA"
        assert nfse.tomador.endereco.logradouro == "RUA MARIA QUITERIA,263"
        assert nfse.tomador.endereco.numero == "00"
        assert nfse.tomador.endereco.complemento == "GALPAO LOT DESMEMBRAMENTO"
        assert nfse.tomador.endereco.bairro == "ITINGA"
        assert nfse.tomador.endereco.municipio == "Lauro de Freitas"
        assert nfse.tomador.endereco.codigo_municipio == "2919207"
        assert nfse.tomador.endereco.cep == "42738205"
        assert nfse.tomador.email == "foliveira@bonialimentos.com.br"

        v = nfse.valores
        assert v.valor_servicos == pytest.approx(5200.00)
        assert v.base_calculo == pytest.approx(5200.00)
        assert v.valor_deducoes == pytest.approx(0.0)
        assert v.desconto_incondicionado == pytest.approx(0.0)
        # Antes do recorte dedicado, a leitura de página inteira trocava
        # PIS/COFINS com IR/INSS entre si (grade densa "Tributos Federais").
        assert v.valor_pis == pytest.approx(33.80)
        assert v.valor_cofins == pytest.approx(156.00)
        assert v.valor_ir == pytest.approx(52.00)
        assert v.valor_inss == pytest.approx(572.00)
        assert v.valor_csll == pytest.approx(52.00)
        assert v.outras_retencoes == pytest.approx(0.0)
        assert v.iss_retido is False
        assert v.valor_iss == pytest.approx(260.00)
        assert v.valor_iss_retido == pytest.approx(0.0)
        assert v.aliquota == pytest.approx(0.05)
        assert v.valor_liquido_nfse == pytest.approx(4334.20)
        # Confere a soma: 5.200,00 - (572+52+33,80+156+52) = 4.334,20
        assert v.valor_servicos - (v.valor_inss + v.valor_ir + v.valor_pis + v.valor_cofins + v.valor_csll) == pytest.approx(v.valor_liquido_nfse)

        xml = Abrasf201Transformer().transform(nfse)
        assert "<Numero>202600000036345</Numero>" in xml
        assert "<Cnpj>04811846000162</Cnpj>" in xml
        assert "<ItemListaServico>0713</ItemListaServico>" in xml
        assert "<ValorPis>33.80</ValorPis>" in xml
        assert "<ValorIss>260.00</ValorIss>" in xml
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
