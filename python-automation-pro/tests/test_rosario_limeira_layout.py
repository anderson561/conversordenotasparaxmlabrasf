# -*- coding: utf-8 -*-
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_ROSARIO_LIMEIRA
import os

# Texto REAL do pdfminer (PDF DIGITAL, sem OCR) da NFS-e da Prefeitura de
# Rosário da Limeira/MG (plataforma FUTURIZE), nota real nº 72/2026
# (LOFTS PARAISO -> DELTALINE). Preservado verbatim, incluindo os quirks:
#  - número "72/2026" (a parte antes da "/" é o número; o resto é o ano);
#  - o tomador usa o rótulo "Nome:" (não "Razão Social:") e há um "Nome
#    Fantasia:" vazio logo depois que NÃO pode ser confundido com ele;
#  - endereço em linha única "logradouro, nº - [extras] - bairro - CEP -
#    município - UF"; o tomador tem um segmento "SC" extra entre logradouro e
#    bairro; o bairro do prestador vem com letra-espaçada
#    ("F R A N C I S C O B E R T O N I", todas com espaço simples);
#  - Simples via "Simples Nac/MEI/Outros: Simples Nacional" (não "optante");
#  - "TRIBUTAÇÃO FORA DO MUNICÍPIO" (prestação em Luís Eduardo Magalhães/BA),
#    mas a incidência mantém o município do prestador (decisão do usuário).
MOCK_TEXT = """PREFEITURA MUNICIPAL DE ROSARIO DA LIMEIRA
SECRETARIA MUNICIPAL DE FAZENDA
SETOR TRIBUTÁRIO

PRAÇA NOSSA SENHORA DE FÁTIMA, 232 - CENTRO

ROSARIO DA LIMEIRA - MG - 36.878-000 - Tel.: (32)3723-1263

NOTA FISCAL DE SERVIÇOS ELETRÔNICA - NFS-e

Nº da Nota
72/2026
Nº Integral: 202600000000072

Código Verificação

D2Q2DCVTUN
Código QR

Município de Prestação: LUÍS EDUARDO MAGALHÃES - BA

Natureza da Operação:  TRIBUTAÇÃO FORA DO MUNICÍPIO

Data da Nota Fiscal:  26/06/2026

Período de Competência: 06/2026

Reg. Especial Tributação:

Nº da RPS:

PRESTADOR DE SERVIÇOS

Razão Social: LOFTS PARAISO SOLUCOES EM HOSPEDAGENS LTDA

CPF/CNPJ: 61.127.194/0001-85

Nome Fantasia: LOFTS PARAISO

Regime Especial:

Simples Nac/MEI/Outros: Simples Nacional

Inscrição Municipal:

Inscrição Estadual:

Fone/Fax:

(77)9845-1000

Endereço: RUA VICENTE FRANCISCO VITAL, 194 - F R A N C I S C O B E R T O N I - 36.878-000 - ROSARIO DA LIMEIRA - MG

TOMADOR DE SERVIÇOS

Nome: DELTALINE SERVICOS LTDA

CPF/CNPJ: 01.813.680/0001-25

Nome Fantasia:

E-mail:

Fone/Fax:

Inscrição Municipal:

Inscrição Estadual:

Endereço: R CAMBORIU, 39 - SC - IAPI - 40.330-533 - SALVADOR - BA

CNAE: 5510-8/02 - APART-HOTÉIS(PRINCIPAL)

DADOS COMPLEMENTARES

Código de Trib. Nacional: 09.01.04 - HOSPEDAGEM EM APART-SERVICE CONDOMINIAIS, FLAT, APART-HOTEIS, HOTEIS RESIDENCIA, RESIDENCE-SERVICE, ...

NBS: 1.0303.11.00 - SERVICOS DE HOSPEDAGEM EM QUARTOS OU UNIDADES DE HOSPEDAGEM PARA VISITANTES, COM SERVICOS DIARIOS DE...

Código da Obra:

ART:

HOSPEDAGEM

DISCRIMINAÇÃO DOS SERVIÇOS

PIS (R$)
0,00

COFINS (R$)
0,00

VALOR TOTAL DE SERVIÇOS = R$ 158,40
IR (R$)
0,00

CSLL (R$)
0,00

INSS (R$)
0,00

SEST SENAT (R$)
0,00

Outras Retenções (R$)
0,00

Deduções (R$) Desc. Incond + Cond(R$)
0,00

0,00

Base de Cálculo (R$)
158,40

Alíquota (%)
2,00

Valor do ISS (R$)
3,17

ISS Retido (R$)
0,00

ISS Devido (R$)
0,00

Valor Líquido (R$)
158,40

Página: 1/1

FUTURIZE - Tecnologia em Sistemas da Informação
"""


def test_detect_rosario_limeira():
    """Detecção ancorada no município (não na plataforma FUTURIZE). Layout
    digital — from_ocr=False."""
    dummy_path = "tests/dummy_rosario.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    try:
        extractor = SPPdfExtractor(dummy_path)
        extractor.raw_text = "PREFEITURA MUNICIPAL DE ROSARIO DA LIMEIRA\nFUTURIZE"
        extractor.from_ocr = False
        assert extractor._detect_layout() == LAYOUT_ROSARIO_LIMEIRA
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_extract_rosario_limeira_layout(monkeypatch):
    dummy_path = "tests/dummy_rosario_full.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    # PDF digital: extract_text devolve o texto do pdfminer diretamente
    # (não passa por OCR — from_ocr permanece False).
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        # Número "72/2026" -> "72"; código de verificação alfanumérico presente.
        assert nfse.numero == "72"
        assert nfse.codigo_verificacao == "D2Q2DCVTUN"
        assert nfse.data_emissao.strftime("%d/%m/%Y") == "26/06/2026"
        assert nfse.competencia.strftime("%m/%Y") == "06/2026"
        # Item LC116 "09.01.04" (3º par = desdobro) -> "0901".
        assert nfse.servico_codigo == "0901"
        assert nfse.discriminacao == "HOSPEDAGEM"

        # Prestador em Rosário da Limeira/MG — IBGE 3156452 (registrado no
        # resolver; sem essa entrada cairia no default MG Belo Horizonte/3106200).
        assert nfse.prestador.cnpj_cpf == "61127194000185"
        assert nfse.prestador.razao_social == "LOFTS PARAISO SOLUCOES EM HOSPEDAGENS LTDA"
        assert nfse.prestador.endereco.municipio == "ROSARIO DA LIMEIRA"
        assert nfse.prestador.endereco.codigo_municipio == "3156452"
        assert nfse.prestador.endereco.uf == "MG"
        # Bairro com letra-espaçada colapsado (sem inventar o espaço entre palavras).
        assert nfse.prestador.endereco.bairro == "FRANCISCOBERTONI"
        assert nfse.prestador.endereco.numero == "194"

        # Tomador em Salvador/BA — IBGE 2927408. O rótulo é "Nome:" (não "Razão
        # Social:"); o "Nome Fantasia:" vazio logo abaixo não pode vazar aqui.
        assert nfse.tomador.cnpj_cpf == "01813680000125"
        assert nfse.tomador.razao_social == "DELTALINE SERVICOS LTDA"
        assert nfse.tomador.endereco.municipio == "SALVADOR"
        assert nfse.tomador.endereco.codigo_municipio == "2927408"
        assert nfse.tomador.endereco.uf == "BA"
        assert nfse.tomador.endereco.bairro == "IAPI"

        # NFS-e tributada: ISS 2% sobre a base de 158,40 = 3,17.
        val = nfse.valores
        assert val.valor_servicos == pytest.approx(158.40)
        assert val.base_calculo == pytest.approx(158.40)
        assert val.aliquota == pytest.approx(0.02)
        assert val.valor_iss == pytest.approx(3.17)
        assert val.iss_retido is False
        assert val.valor_liquido_nfse == pytest.approx(158.40)

        # Simples Nacional via "Simples Nac/MEI/Outros: Simples Nacional" (o campo
        # "Reg. Especial Tributação:" vem vazio -> regime especial ausente).
        assert nfse.optante_simples_nacional is True
        assert nfse.regime_especial_tributacao is None

        # PDF digital limpo: nenhum aviso de baixa confiança.
        assert nfse.avisos == []
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
