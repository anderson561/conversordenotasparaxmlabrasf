# -*- coding: utf-8 -*-
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_FF_LOCACAO
import os

# Texto REAL do OCR (Tesseract, zoom 3x, recut via SPPdfExtractor._ocr_recut_ff_locacao
# — ver docstring do método) da fatura de locação de CFTV emitida pela F&F
# Comércio e Serviços de Telecomunicações de Segurança Eletrônica LTDA para a
# Boutique Guarajuba (PH Gestão). Preservado verbatim, incluindo os quirks que
# travam regressões:
#  - o layout de 2 colunas do OCR quebra a frase "FATURA DE LOCAÇÃO" em duas
#    linhas, intercalada com o nome da empresa — a detecção genérica de fatura
#    de locação nunca casa aqui, por isso a detecção é pelo CNPJ do emissor;
#  - o rótulo "RAZÃO SOCIAL" vem quebrado em 2 linhas ("RAZÃO ...\nSOCIAL"),
#    com o valor colado ao "RAZÃO";
#  - o rótulo "CNPJ/CPF:" da coluna vizinha cola direto no fim do endereço do
#    tomador, e a continuação do endereço (bairro) é empurrada pra linha
#    seguinte pela mesma intercalação de colunas;
#  - o campo "VALOR TOTAL DA FATURA" traz um PLACEHOLDER DE TEMPLATE não
#    substituído pela própria nota-fonte ("R$ gvenda valor totalf" — o OCR lê
#    "g" e "f" em vez dos delimitadores "#" do template quebrado
#    "#venda_valor_total#", confirmado na imagem renderizada) — o valor real
#    vem da tabela de itens (coluna "Valor Liquido").
MOCK_OCR = (
    "« am +, F&F COMERCIO E SERVIÇOS DE TELECOMUNICAÇÕES DE SEGURANÇA FATURA DE\n"
    "[aí ELETRONICA LTDA LOCAÇÃO\n"
    "ENDEREÇO: Rua Senhor do Bomfim, 544, Loja 02, Monte Gordo - Camaçari / Ba Nº: 520366\n"
    "CEP: 42839-852\n"
    "CNPJ: 13.398.812/0001-89 Telefone: 4062-8609 Emissão:\n"
    "18/04/2026\n"
    "\n"
    "DESTINATARIO\n"
    "\n"
    "RAZÃO 7396 - Boutique Guarajuba PH Gestão\n"
    "SOCIAL\n"
    "ENDEREÇO: GUARAJUBA, O Pousada Boutique Guarajuba - CNPJ/CPF: 25.311.856/0001-09\n"
    "Guarajuba\n"
    "CIDADE: Camaçari CEP: 42840-310 UF: BA\n"
    "PERIODO DE 2026-04\n"
    "LOCAÇÃO:\n"
    "Descrição Valor Total:\n"
    "Descrição Contrato Valor Unitário Qtde. Valor Liquido\n"
    "CONTRATO DE R$ 2.605,29 1,00 R$ 2.605,29\n"
    "LOCAÇÃO DE CFTV -\n"
    "GUARAJUBA\n"
    "SAUITES\n"
    "VALOR TOTAL DA FATURA R$ gvenda valor totalf\n"
    "\n"
    "OPERAÇÃO NÃO SUJEITA A NOTA FISCAL DE SERVIÇO NOS TERMOS DA LEI COMPLEMENTAR 116/2003\n"
    "\n"
    "RECEBI(EMOS) DA EMPRESA F&F COMERCIO E SERVIÇOS DE TELECOMUNICAÇÕES DE FATURA DE LOCAÇÃO\n"
    "SEGURANÇA ELETRÔNICA LTDA AS LOCAÇÕES CONSTANTES NESSA FATURA INDICADA\n"
    "AO LADO\n"
    "\n"
    "DATA DO RECEBIMENTO IDENTIFICAÇÃO E ASSINATURA DO Nº 520366\n"
    "RECEBEDOR\n"
)

# Texto curto/sem palavras-chave para forçar o fallback de OCR em parse_multiple
# (o PDF real desta nota é escaneado, sem camada de texto embutida).
DIGITAL_TEXT = "\x0c"


def test_detect_ff_locacao():
    dummy_path = "tests/dummy_ff_locacao.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    try:
        ex = SPPdfExtractor(dummy_path)
        ex.raw_text = "CNPJ: 13.398.812/0001-89 Telefone: 4062-8609"
        assert ex._detect_layout() == LAYOUT_FF_LOCACAO
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_extract_ff_locacao_layout(monkeypatch):
    dummy_path = "tests/dummy_ff_locacao_full.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: DIGITAL_TEXT)
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_OCR)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()

        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        assert nfse.numero == "520366"
        assert nfse.data_emissao.strftime("%d/%m/%Y") == "18/04/2026"
        # Não é NFS-e municipal (operação não sujeita a ISS) — mesmo
        # placeholder usado pelos demais layouts de locação.
        assert nfse.codigo_verificacao == "FATURA"
        assert nfse.servico_codigo == "0601"

        # Prestador (locadora F&F): dados fixos no código, mesmo padrão dos
        # demais locadores de filial única (LMR/Geração/Locontainers).
        assert nfse.prestador.cnpj_cpf == "13398812000189"
        assert nfse.prestador.razao_social == "F&F COMÉRCIO E SERVIÇOS DE TELECOMUNICAÇÕES DE SEGURANÇA ELETRÔNICA LTDA"
        assert nfse.prestador.endereco.logradouro == "Rua Senhor do Bomfim"
        assert nfse.prestador.endereco.numero == "544"
        assert nfse.prestador.endereco.complemento == "Loja 02"
        assert nfse.prestador.endereco.bairro == "Monte Gordo"
        assert nfse.prestador.endereco.municipio == "Camaçari"
        assert nfse.prestador.endereco.codigo_municipio == "2905701"
        assert nfse.prestador.endereco.uf == "BA"
        assert nfse.prestador.endereco.cep == "42839852"

        # Tomador (locatário): extraído do bloco "DESTINATARIO" - razão social
        # mantém o código de cliente ("7396 -") tal como impresso na nota.
        assert nfse.tomador.cnpj_cpf == "25311856000109"
        assert nfse.tomador.razao_social == "7396 - Boutique Guarajuba PH Gestão"
        assert nfse.tomador.endereco.logradouro == "GUARAJUBA, Pousada Boutique Guarajuba"
        assert nfse.tomador.endereco.bairro == "Guarajuba"
        assert nfse.tomador.endereco.municipio == "Camaçari"
        assert nfse.tomador.endereco.codigo_municipio == "2905701"
        assert nfse.tomador.endereco.uf == "BA"
        assert nfse.tomador.endereco.cep == "42840310"

        # Valor: vem da tabela de itens, já que o campo "VALOR TOTAL DA
        # FATURA" traz o placeholder de template quebrado da nota-fonte.
        val = nfse.valores
        assert val.valor_servicos == pytest.approx(2605.29)
        assert val.valor_liquido_nfse == pytest.approx(2605.29)

        assert nfse.avisos == []
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
