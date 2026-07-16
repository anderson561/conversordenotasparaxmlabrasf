import os

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_CAMPINAS

# Texto exatamente como o OCR (Tesseract, zoom 2x) extrai de uma NFSe Campinas
# real (PDF de imagem). Preserva os ruídos típicos deste layout: telefone com
# "s" no lugar de "9", e-mail com "@" mesclado ("GQgmail.com"), "Valor total"
# perdendo o dígito inicial ("00,00" no lugar de "700,00"), separador "/" lido
# como "|" em "SALVADOR | BA" e a grade "VALOR TOTAL" truncada pelo OCR.
MOCK_CAMPINAS = """Prefeitura Municipal Campinas
Secretaria Municipal de Finanças

Nota Fiscal de Serviços eletrônica de Campinas
NFSe Campinas - Prestador

DADOS DA NFSe Campinas Pode ver verticada pela Itura deste
Datae horade emissão Competência Número / Série idigo, OR
28/06/2026 16:52:29 06/2026 1712/E
Código de Verificação
JxBPMPRSP
EMITENTE PRESTADOR DO SERVIÇO
CPF / CNPJ/ NIF Inscrição Municipal Telefone
10.983.367/0001-26 00.165.107-2 (19) 9818-9401
Nome / Nome Empresarial E-mail
PRESTO COMUNICACAO E SOM LTDA - ME gabrielduarte2007 GQgmail.com
Endereço . Município CEP
AVENIDA CARLOS GRIMALDI 1171 D 22 JARDIM CONCEIÇÃO CAMPINAS / SP BRASIL 13091-000
TOMADOR DO SERVIÇO
CPF/CNPJ / NIF Inscrição Municipal Telefone
04.386.913/0001-49 - -
Nome / Nome Empresarial E-mail
Endereço Município cep
5º AVENIDA ALTO DO SALDANHA 2671 SALA-1202; BROTAS SALVADOR | BA BRASIL 40280-080

SERVIÇO PRESTADO

CNAE / CBO

5920-1/00-00 - ATIVIDADES DE GRAVACAO DE SOM E DE EDICAO DE MUSICA

Serviço

13.02 - FONOGRAFIA OU GRAVAÇÃO DE SONS, INCLUSIVE TRUCAGEM, DUBLAGEM, MIXAGEM E CONGÊNERES
Local da prestação do serviço País da prestação do serviço

CAMPINAS /SP BRASIL

DESCRIÇÃO DO SERVIÇO PRESTADO (EM ACORDO COM A CNAE/CBO IDENTIFICADA NO CAMPO SERVIÇO
PRESTADO, ESPECIFICANDO A QUANTIDADE E O PREÇO UNITÁRIO)

serviços prestados de locução - job 5718
LOCUTOR: GABRIEL DUARTE

DADOS BANCÁRIOS:
Cora SCD 403

Agência 0001

Conta 2533273-6

Pix (CNPJ) 10.983.367/0001-26

vencimento c/a

DOCUMENTO EMITIDO POR ME OU EPP OPTANTE PELO SIMPLES NACIONAL

TRIBUTAÇÃO MUNICIPAL

Exigibilidade do ISSQN Responsável pelo recolhimento do ISSQN
EXIGÍVEL CAMPINAS - SP PRESTADOR DO SERVIÇO
Retenção do ISSQN Situação do prestador do serviço perante o Simples Nacional Regime especial de tributação do ISSQN
NÃO RETIDO OPTANTE SIMPLES NACIONAL
CÁLCULO DO ISSQN
Valor total da NFSe Campinas (R$) Total das deduções (R$) Desc. incondicionado (R$) Base de cálculo do ISSQN (R$) Aliq. (%) — Valor do ISSQN (R$)
00,00 0,00 0,00 700,00 er e
RETENÇÕES
ISSQN (R$) IRRF (R$) PIS (R$) COFINS (R$) INSS (R$) CSLL (R$) Outras retenções (R$)
0,00 0,00 0,00 0,00 0,00 0,00 0,00
VALOR TOTAL
Base de cálculo do ISSQN (R$) Retenções (R$) Desc. incondicionado (R$) Desc. condicionado (R$) Valor Líquido da NFSe Campinas (R$)
700,00 0,00

INFORMAÇÕES COMPLEMENTARES
"""


# Mesmo layout Campinas, mas em PDF DIGITAL (camada de texto). O pdfminer extrai
# a tabela de 2 colunas campo a campo: CNPJ/Nome/Endereço contíguos por entidade
# e os demais campos (IM, e-mail, município, telefone, CEP) num bloco posterior,
# com as colunas intercaladas. Aqui o tomador TEM razão social.
MOCK_CAMPINAS_DIGITAL = """Prefeitura Municipal Campinas
Secretaria Municipal de Finanças

Nota Fiscal de Serviços eletrônica de Campinas
NFSe Campinas - Prestador

DADOS DA NFSe Campinas
Data e hora de emissão
12/02/2026 21:16:33
Código de Verificação
tukNCwIRx

Competência
02/2026

Número / Série
1660 / E

EMITENTE PRESTADOR DO SERVIÇO
CPF / CNPJ / NIF
10.983.367/0001-26
Nome / Nome Empresarial
PRESTO COMUNICACAO E SOM LTDA - ME

Endereço
AVENIDA CARLOS GRIMALDI 1171 D 22 JARDIM CONCEIÇÃO

TOMADOR DO SERVIÇO
CPF / CNPJ / NIF
04.386.913/0001-49
Nome / Nome Empresarial
ELOS ESTUDIO E SERIÇOS LTDA
Endereço
5ª AVENIDA ALTO DO SALDANHA 2671 SALA:1202;   BROTAS

A  autenticidade  desta  NFSe  Campinas
pode  ser  verificada  pela  leitura  deste
código  QR.

Inscrição Municipal
00.165.107-2
E-mail
gabrielduarte2007@gmail.com

Município
CAMPINAS / SP BRASIL

Inscrição Municipal
-
E-mail
-

Telefone
(19) 9818-9401

CEP
13091-000

Telefone
-

Município
SALVADOR / BA BRASIL

CEP
40280-080

SERVIÇO PRESTADO
CNAE / CBO
5920-1/00-00 - ATIVIDADES DE GRAVACAO DE SOM E DE EDICAO DE MUSICA
Serviço
13.02 - FONOGRAFIA OU GRAVAÇÃO DE SONS, INCLUSIVE TRUCAGEM, DUBLAGEM, MIXAGEM E CONGÊNERES.
Local da prestação do serviço
CAMPINAS / SP

País da prestação do serviço
BRASIL

DESCRIÇÃO DO SERVIÇO PRESTADO (EM ACORDO COM A CNAE/CBO IDENTIFICADA NO CAMPO SERVIÇO
PRESTADO, ESPECIFICANDO A QUANTIDADE E O PREÇO UNITÁRIO)
Referente a gravação JOB 5542 - DIA DO VETERINÁRIO

LOCUTOR: GABRIEL DUARTE
DADOS BANCÁRIOS:
Cora SCD 403
Agência 0001
Conta 2533273-6
Pix (CNPJ) 10.983.367/0001-26

DOCUMENTO EMITIDO POR ME OU EPP OPTANTE PELO SIMPLES NACIONAL

TRIBUTAÇÃO MUNICIPAL
Exigibilidade do ISSQN
EXIGÍVEL
Retenção do ISSQN
NÃO RETIDO

Município da Incidência do ISSQN
CAMPINAS - SP

Situação do prestador do serviço perante o Simples Nacional
OPTANTE

Responsável pelo recolhimento do ISSQN
PRESTADOR DO SERVIÇO
Regime especial de tributação do ISSQN
SIMPLES NACIONAL

CÁLCULO DO ISSQN
Valor total da NFSe Campinas (R$)
600,00

RETENÇÕES

Total das deduções (R$)
0,00

Desc. incondicionado (R$)
0,00

Base de cálculo do ISSQN (R$)
600,00

Alíq. (%)
*****

Valor do ISSQN (R$)
*****

VALOR TOTAL

Base de cálculo do ISSQN (R$)
600,00

Retenções (R$)
0,00

Desc. incondicionado (R$)
0,00

Desc. condicionado (R$)
0,00

Valor Líquido da NFSe Campinas (R$)
600,00

INFORMAÇÕES COMPLEMENTARES
"""


def _make_extractor(mock_text=MOCK_CAMPINAS):
    dummy_path = "tests/dummy_campinas.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = mock_text
    extractor.layout = extractor._detect_layout()
    return extractor, dummy_path


def _cleanup(path):
    if os.path.exists(path):
        os.remove(path)


def test_detect_campinas_layout():
    """Detecção do layout Campinas/SP pela marca 'NFSe Campinas'."""
    extractor, path = _make_extractor()
    try:
        assert extractor.layout == LAYOUT_CAMPINAS
    finally:
        _cleanup(path)


def test_campinas_numero_e_codigo_verificacao():
    """Número vem de 'Número / Série' no formato NNNN/L; código de verificação limpo."""
    extractor, path = _make_extractor()
    try:
        assert extractor._extrair_numero() == "1712"
        assert extractor._extrair_codigo_verificacao() == "JXBPMPRSP"
    finally:
        _cleanup(path)


def test_campinas_item_lista_servico():
    """Item da LC 116/03 '13.02 - FONOGRAFIA...' -> '1302' (e não o CNAE 5920-1/00)."""
    extractor, path = _make_extractor()
    try:
        assert extractor._extrair_codigo_servico() == "1302"
    finally:
        _cleanup(path)


def test_campinas_datas():
    """Emissão 28/06/2026 16:52:29 e competência 06/2026."""
    extractor, path = _make_extractor()
    try:
        emissao = extractor._extrair_data_emissao()
        competencia = extractor._extrair_competencia(emissao)
        assert (emissao.day, emissao.month, emissao.year) == (28, 6, 2026)
        assert (emissao.hour, emissao.minute) == (16, 52)
        assert (competencia.month, competencia.year) == (6, 2026)
    finally:
        _cleanup(path)


def test_campinas_prestador():
    """Prestador: CNPJ/IM/razão/e-mail e endereço em Campinas/SP (IBGE 3509502)."""
    extractor, path = _make_extractor()
    try:
        p = extractor._extrair_entidade("Prestador")
        assert p.cnpj_cpf == "10983367000126"
        assert p.inscricao_municipal == "001651072"
        assert p.razao_social == "PRESTO COMUNICACAO E SOM LTDA - ME"
        assert p.email == "gabrielduarte2007@gmail.com"
        assert p.endereco.logradouro == "AVENIDA CARLOS GRIMALDI"
        assert p.endereco.numero == "1171"
        assert p.endereco.bairro == "JARDIM CONCEIÇÃO"
        assert p.endereco.municipio == "CAMPINAS"
        assert p.endereco.uf == "SP"
        assert p.endereco.codigo_municipio == "3509502"
        assert p.endereco.cep == "13091000"
    finally:
        _cleanup(path)


def test_campinas_tomador():
    """Tomador: CNPJ válido e endereço em Salvador/BA (IBGE 2927408).

    O documento não traz razão social do tomador, então é esperado o rótulo
    de não-identificado (flag de baixa confiança), sem inventar um nome.
    """
    extractor, path = _make_extractor()
    try:
        tm = extractor._extrair_entidade("Tomador")
        assert tm.cnpj_cpf == "04386913000149"
        assert tm.razao_social == "Tomador Não Identificado"
        assert tm.endereco.numero == "2671"
        assert tm.endereco.bairro == "BROTAS"
        assert tm.endereco.municipio == "SALVADOR"
        assert tm.endereco.uf == "BA"
        assert tm.endereco.codigo_municipio == "2927408"
        assert tm.endereco.cep == "40280080"
    finally:
        _cleanup(path)


def test_campinas_valores():
    """Base de cálculo é a âncora (700,00); Simples => ISS/alíquota zerados.

    O 'Valor total' vem corrompido pelo OCR ('00,00'), então o valor dos
    serviços é derivado da base de cálculo, e o líquido é reconstruído.
    """
    extractor, path = _make_extractor()
    try:
        v = extractor._extrair_valores()
        assert v.valor_servicos == 700.0
        assert v.base_calculo == 700.0
        assert v.valor_liquido_nfse == 700.0
        assert v.valor_iss == 0.0
        assert v.aliquota == 0.0
    finally:
        _cleanup(path)


def test_campinas_discriminacao():
    """Discriminação real do serviço, não o fallback genérico."""
    extractor, path = _make_extractor()
    try:
        d = extractor._extrair_discriminacao()
        assert "locução" in d.lower()
        assert "5718" in d
    finally:
        _cleanup(path)


def test_campinas_optante_simples():
    """Documento de ME/EPP optante do Simples Nacional (estrutura OCR)."""
    extractor, path = _make_extractor()
    try:
        nfse = extractor.parse()
        assert nfse.optante_simples_nacional is True
        assert nfse.regime_especial_tributacao == "6"
    finally:
        _cleanup(path)


# ---------------------------------------------------------------------------
# Estrutura DIGITAL (pdfminer) — colunas intercaladas, tomador com razão social
# ---------------------------------------------------------------------------

def test_campinas_digital_detecta_layout():
    extractor, path = _make_extractor(MOCK_CAMPINAS_DIGITAL)
    try:
        assert extractor.layout == LAYOUT_CAMPINAS
    finally:
        _cleanup(path)


def test_campinas_digital_prestador_completo():
    """No PDF digital os campos do prestador vêm espalhados; a 1ª ocorrência de
    cada rótulo é do prestador. Todos os campos fiscais devem sair corretos."""
    extractor, path = _make_extractor(MOCK_CAMPINAS_DIGITAL)
    try:
        p = extractor._extrair_entidade("Prestador")
        assert p.cnpj_cpf == "10983367000126"
        assert p.inscricao_municipal == "001651072"
        assert p.email == "gabrielduarte2007@gmail.com"
        assert p.telefone == "1998189401"
        assert p.endereco.municipio == "CAMPINAS"
        assert p.endereco.uf == "SP"
        assert p.endereco.codigo_municipio == "3509502"
        assert p.endereco.cep == "13091000"
        assert p.endereco.bairro == "JARDIM CONCEIÇÃO"
    finally:
        _cleanup(path)


def test_campinas_digital_tomador_com_razao():
    """A 2ª ocorrência de cada rótulo é do tomador (Salvador/BA), e aqui o
    tomador TEM razão social, que não pode ser trocada pela do prestador."""
    extractor, path = _make_extractor(MOCK_CAMPINAS_DIGITAL)
    try:
        tm = extractor._extrair_entidade("Tomador")
        assert tm.cnpj_cpf == "04386913000149"
        assert tm.razao_social == "ELOS ESTUDIO E SERIÇOS LTDA"
        assert tm.endereco.municipio == "SALVADOR"
        assert tm.endereco.uf == "BA"
        assert tm.endereco.codigo_municipio == "2927408"
        assert tm.endereco.cep == "40280080"
        assert tm.endereco.bairro == "BROTAS"
    finally:
        _cleanup(path)


def test_campinas_digital_valores_e_optante():
    extractor, path = _make_extractor(MOCK_CAMPINAS_DIGITAL)
    try:
        nfse = extractor.parse()
        assert nfse.numero == "1660"
        assert nfse.valores.valor_servicos == 600.0
        assert nfse.valores.valor_liquido_nfse == 600.0
        # "OPTANTE" e "SIMPLES NACIONAL" ficam em linhas separadas no digital.
        assert nfse.optante_simples_nacional is True
        assert nfse.regime_especial_tributacao == "6"
    finally:
        _cleanup(path)
