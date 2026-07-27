# -*- coding: utf-8 -*-
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_MATA_SAO_JOAO
import os

# Texto REAL do OCR (Tesseract, zoom 3, sem rotação) da NFS-e de Mata de São
# João/BA (plataforma SAATRI — matadesaojoao.saatri.com.br), nota real nº 18,
# AURORA COMUNICACAO -> NAUTICA INDUSTRIA. É um scan de boa qualidade (OCR
# limpo), diferente das fotos degradadas de Camaçari/SP2. Preservado verbatim,
# incluindo os quirks que travam regressões:
#  - o número vem zero-preenchido ("00000018") e precisa perder os zeros;
#  - a coluna de rótulos ("Nome/Razão Social:", "CPF/CNPJ:"...) é dumpada em
#    bloco separado no fim e deve ser ignorada pelo parser de entidades;
#  - o "Simples Nacional" aparece como "optante DO simples nacional" (não
#    "pelo"), e a classificação "01.01.01" traz um 3º par (desdobro municipal).
MOCK_TEXT = """Recebemos de AURORA COMUNICACAO E MIDIA DIGITAL LTDA - CPF/CNPJ: 58.679.822/0001-20 a
prestação dos serviços da nota fiscal indicada ao lado
Nº 00000018

Data de Recebimento Identificação e assinatura do recebedor

Prefeitura Municipal de Mata de São João

RUA LUIZ ANTONIO GARCEZ, 140
CENTRO - MATA DE SÃO JOÃO/BA

CNPJ: 13.805.528/0001-80
MATA DE

CEP: 48280-000

Número da Nota [ElTuE ri [E]

00000018

Data e Hora de Emissão

Raros

25/05/2026 12:23:13
Data do Fato Gerador
25/05/2026

Município Emissor

MATA DE SÃO JOÃO/BA

SÃO JOÃO

Código de Verificação
29210051258679822000120000000000001826050766886458

Dados do(s) Serviço(s)
Local da Prestação
MATA DE SÃO JOÃO/BA - BRASIL

Prestador do(s) Serviço(s)

AURORA COMUNICACAO E MIDIA DIGITAL LTDA

REVISTA AURORA

CON PRAIA BELLA, Empreendimento Praia Bela - F

PRAIA DO FORTE - MATA DE SÃO JOÃO/BA CEP: 48280-000

58.679.822/0001-20 Insc. Municipal: 552967

(00) 3819-6044 E-mail: COMERCIALSPOTIDELLI.COM.BR
Tomador do(s) Serviço(s)

NAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA

NAUTICA INDUSTRIA E COMERCIO

AL GABRIEL MONTEIRO DA SILVA, 1480 CASA TERREA

JARDIM AMERICA - SÃO PAULO/SP CEP: 01442-001

16.699.869/0002-97 Insc. Municipal:

Exigibilidade do ISS / Natureza da Operação
Exigível

Local da Incidência
MATA DE SÃO JOÁO/BA

Nome/Razão Social:
Nome Fantasia:

Endereco:

CPF/CNPJ:
Telefone:

Nome/Razão Social:
Nome Fantasia:

Endereço:

CPF/CNPJ:

Telefone: E-mail: nautica(QOnauticamoveis.com

Discriminação do(s) Serviço(s)
SERVIÇOS DE MARKETING DIGITAL

Classificação do Serviço (LEI 116/2003) + Desdobro

01.01.01 - Análise e desenvolvimento de sistemas.

NBS

115021000 - Serviços de projeto, desenvolvimento e instalação de aplicativos e programas não personalizados (não custom

Valor do(s) Serviço(s) Valor Dedução Desconto Incondicionado Base de Cálculo ISS
10.000,00 0,00 0,00 10.000,00
Alíquota ISS (%) Valor do ISS Valor ISS Retido Desconto Condicionado
0,00 0,00 0,00 0,00
0,00

Retenções Federais
0,00
Doo motas

COFINS CSLL INSS
0,00 0,00 0,00
Alíquota IBS Valor IBS Alíquota CBS Valor CBS Total do(s) Serviço(s) Total Líquido
- - - - 10.000,00 10.000,00

Outros Impostos Federais
Outras Informações

*** Empresa prestadora de serviços optante do simples nacional ***
O prestador do(s) serviço(s) possui regime especial de tributação: Microempresário e Empresa de Pequeno Porte (ME - EPP)

Favor verificar a autenticidade deste documento fiscal no site https://matadesaojoao.saatri.com.br
"""


def test_detect_mata_sao_joao():
    """Detecção ancorada no município (SAATRI). Diferente de Camaçari/SP2, este
    layout NÃO é gated por from_ocr — não há digital concorrente a proteger, e
    a marca 'Mata de São João' já é específica do município."""
    dummy_path = "tests/dummy_mata.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    try:
        extractor = SPPdfExtractor(dummy_path)
        extractor.raw_text = "Prefeitura Municipal de Mata de São João\nmatadesaojoao.saatri.com.br"
        extractor.from_ocr = True
        assert extractor._detect_layout() == LAYOUT_MATA_SAO_JOAO
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_extract_mata_sao_joao_layout(monkeypatch):
    dummy_path = "tests/dummy_mata_full.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    # extract_text vazio força o caminho de OCR do parse_multiple, que seta
    # self.from_ocr=True; _extract_via_ocr devolve o texto canônico capturado.
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        # Número zero-preenchido ("00000018") -> "18".
        assert nfse.numero == "18"
        assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M") == "25/05/2026 12:23"
        assert nfse.competencia.strftime("%m/%Y") == "05/2026"
        # Item da LC 116 "01.01.01" (3º par = desdobro municipal) -> "0101".
        assert nfse.servico_codigo == "0101"
        assert nfse.discriminacao == "SERVIÇOS DE MARKETING DIGITAL"
        # Código de verificação presente e legível (scan de boa qualidade).
        assert nfse.codigo_verificacao == "29210051258679822000120000000000001826050766886458"

        # Prestador em Mata de São João/BA — IBGE 2921005 (registrado no resolver;
        # sem essa entrada cairia no default Salvador/2927408).
        assert nfse.prestador.cnpj_cpf == "58679822000120"
        assert nfse.prestador.razao_social == "AURORA COMUNICACAO E MIDIA DIGITAL LTDA"
        assert nfse.prestador.inscricao_municipal == "552967"
        assert nfse.prestador.endereco.municipio == "MATA DE SÃO JOÃO"
        assert nfse.prestador.endereco.codigo_municipio == "2921005"
        assert nfse.prestador.endereco.uf == "BA"
        assert nfse.prestador.endereco.bairro == "PRAIA DO FORTE"

        # Tomador em São Paulo/SP — IBGE 3550308.
        assert nfse.tomador.cnpj_cpf == "16699869000297"
        assert nfse.tomador.razao_social == "NAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA"
        assert nfse.tomador.endereco.municipio == "SÃO PAULO"
        assert nfse.tomador.endereco.codigo_municipio == "3550308"
        assert nfse.tomador.endereco.uf == "SP"

        # NFS-e com ISS não destacado (alíquota 0): grade rótulo-em-cima/valor-embaixo.
        val = nfse.valores
        assert val.valor_servicos == pytest.approx(10000.00)
        assert val.base_calculo == pytest.approx(10000.00)
        assert val.aliquota == pytest.approx(0.0)
        assert val.valor_iss == pytest.approx(0.0)
        assert val.iss_retido is False
        assert val.valor_liquido_nfse == pytest.approx(10000.00)

        # "optante DO simples nacional" (não "pelo") + regime ME/EPP.
        assert nfse.optante_simples_nacional is True
        assert nfse.regime_especial_tributacao == "6"

        # Scan legível: nenhum aviso de baixa confiança.
        assert nfse.avisos == []
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
