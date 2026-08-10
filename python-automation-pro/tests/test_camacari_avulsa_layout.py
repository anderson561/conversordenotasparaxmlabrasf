# -*- coding: utf-8 -*-
import pytest
from src.extractors.pdf_extractor import (
    SPPdfExtractor,
    LAYOUT_CAMACARI_AVULSA,
    LAYOUT_CAMACARI,
    LAYOUT_CAMACARI_2,
    LAYOUT_CAMACARI_3,
)
import os

# Texto REAL do OCR (Tesseract) da NOTA FISCAL DE PRESTAÇÃO DE SERVIÇOS (AVULSA)
# Série "A" da Prefeitura Municipal de Camaçari/BA, nota real nº 88462,
# ECO COLETA TUDO -> DELTALINE SERVICOS. Preservado verbatim, incluindo os
# quirks que travam regressões:
#  - o cabeçalho quebra "PREFEITURA MUNICIPAL DE" e "CAMAÇARI" em linhas
#    separadas (por isso a detecção casa AVULSA + CAMAÇARI, não a frase inteira);
#  - o VALOR TRIBUTÁVEL sai com o 1º dígito trocado ("14.685" -> "74.685") e o
#    VALOR LÍQUIDO fica em branco no OCR — por isso base/líquido vêm da camada
#    DIGITAL (ver DIGITAL_TEXT abaixo);
#  - o bairro do tomador sai "API" (o OCR comeu o "I" de "IAPI") — mantido fiel,
#    sem inventar a letra;
#  - a nota avulsa não tem código de verificação/autenticidade eletrônico.
MOCK_OCR = """PREFEITURA MUNICIPAL DE NOTA FISCAL DE PRESTAÇÃO | NOTA FISCAL
CAMAÇARI DE SERVIÇOS (AVULSA) 00000088462
SÉRIE "A"
SECRETARIA DA FAZENDA
IDENTIFICAÇÃO DO PRESTADOR
Nome / Razão ECO COLETA TUDO COMERCIO DE MATERIAIS RECICLAVEIS LTDA
CPF / CNPJ: 17.095.195/0001-01 Código Pessoa: 0000630812
CEP: 42802580 Município: CAMACARI UF: BA
Logradouro: RUA A3 Nº. SN
omplemento GALPAO Bairro: JARDIM LIMOEIRO
IDENTIFICAÇÃO DO TOMADOR =
Nome / Razão DELTALINE SERVICOS LTDA
CPF / CNPJ: 01.813.680/0001-25 Inscrição Municipal:
CEP: 40330533 Município: SALVADOR UF: BA
Logradouro: R CAMBORIU Nº: 39
[Complemento Bairro: API
NATUREZA DA OPERAÇÃO: PRESTACAO DE SERVIÇOS DATA DE PRESTAÇÃO: 12.06.2026
PE 000709 - VARRIÇãO, COLETA, REMOÇçãO, INCINERAçãO, TRATAMENTO, RECICLAGEM, Pao À
LIXO, REJEITOS E OUTROS RESIDUOS QUAISQUER
DESCRIÇÃO DOS SERVIÇOS
Qtd|Unidade Especificações Preço Unitário, Preço Tota
1 TRANSPORTE E DESTINAÇÃO FINAL DE RESIDUO CLASSE II B 16.500,00! 16.500,00

MATERIAL APLICADO
OBSERVAÇÕES qa] [VALOR TRIBUTÁVEL 74.685,00
ALÍQUOTA
ISS DEVIDO
RETENÇÃO IMP. RENDA
RETENÇÃO PARA INSS
OUTRAS RETENÇÕES Ecs oa o
VALOR LÍQUIDO

RECEBI RARE
ECEBI OS SERVIÇOS CONSTANTES DESTA NOTA FISCAL DE PRESTAÇÃO DE SERVIÇOS (AVULSA) SÉRIE "A' PREFEITURA WUNICIPAL DE
ASSINATURA CAMAÇARI

TIPO TRIBUTAÇÃO ISENTO TOTAL SERVIÇOS 16.500,00
NUMERO DO PROCESSO ]

NOTA FISCAL

00000088462

SECRETARIA DA FAZENDA

"""

# Camada de texto DIGITAL (pdfminer) da mesma nota: 94 chars, só números soltos,
# sem rótulos nem palavras-chave. É curta demais (< 200 chars) e sem keywords, o
# que dispara o OCR no parse_multiple — mas o ramo de valores a relê para pegar os
# valores EXATOS (16.500,00 = total de serviços; 14.685,00 = valor tributável =
# líquido), fugindo do 1º dígito trocado pelo OCR.
DIGITAL_TEXT = (
    "00000088462\n\n12.06.2026\n\n16.500,00\n\n16.500,00\n\n16.500,00\n\n"
    "14.685,00\n\n14.685,00\n\n00000088462\n\n\x0c"
)


def test_detect_camacari_avulsa():
    """A detecção casa AVULSA + CAMAÇARI e PRECEDE o bloco Camaçari CPqD. Como
    guarda de regressão, uma nota Camaçari CPqD SEM 'AVULSA' deve continuar
    roteada para os layouts CPqD (digital -> CAMACARI, OCR -> CAMACARI_3, o
    SUPERSET de topo do CAMACARI_2 desde a nota nº 20335/PADUA COMÉRCIO)."""
    dummy_path = "tests/dummy_camacari_avulsa.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    try:
        ex = SPPdfExtractor(dummy_path)
        ex.raw_text = ("PREFEITURA MUNICIPAL DE\nNOTA FISCAL DE PRESTAÇÃO DE "
                       "SERVIÇOS (AVULSA)\nCAMAÇARI")
        ex.from_ocr = True
        assert ex._detect_layout() == LAYOUT_CAMACARI_AVULSA

        # Guarda: Camaçari CPqD (sem AVULSA) não pode cair no avulsa.
        ex2 = SPPdfExtractor(dummy_path)
        ex2.raw_text = "PREFEITURA MUNICIPAL DE CAMAÇARI"
        ex2.from_ocr = False
        assert ex2._detect_layout() == LAYOUT_CAMACARI
        ex2.from_ocr = True
        assert ex2._detect_layout() == LAYOUT_CAMACARI_3
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_extract_camacari_avulsa_layout(monkeypatch):
    dummy_path = "tests/dummy_camacari_avulsa_full.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    # extract_text devolve a camada digital curta (com os valores). Por ser < 200
    # chars e sem keywords, o parse_multiple cai no OCR (_extract_via_ocr ->
    # MOCK_OCR) para o texto — exatamente como em produção. O ramo de valores
    # relê extract_text e usa os números exatos da camada digital.
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: DIGITAL_TEXT)
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_OCR)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        # Número zero-preenchido ("00000088462") -> "88462".
        assert nfse.numero == "88462"
        assert nfse.data_emissao.strftime("%d/%m/%Y") == "12/06/2026"
        assert nfse.competencia.strftime("%m/%Y") == "06/2026"
        # "PE 000709" (item 7.09 da LC 116) -> "0709".
        assert nfse.servico_codigo == "0709"
        assert nfse.discriminacao == "TRANSPORTE E DESTINAÇÃO FINAL DE RESIDUO CLASSE II B"
        # Nota avulsa física não tem código de verificação eletrônico -> cai no
        # placeholder de fallback (e gera o aviso honesto, verificado no fim).
        assert nfse.codigo_verificacao == "XXXX-XXXX"

        # Prestador em Camaçari/BA — IBGE 2905701 (registrado no resolver).
        assert nfse.prestador.cnpj_cpf == "17095195000101"
        assert nfse.prestador.razao_social == "ECO COLETA TUDO COMERCIO DE MATERIAIS RECICLAVEIS LTDA"
        assert nfse.prestador.endereco.logradouro == "RUA A3"
        assert nfse.prestador.endereco.numero == "SN"
        assert nfse.prestador.endereco.bairro == "JARDIM LIMOEIRO"
        assert nfse.prestador.endereco.municipio == "CAMACARI"
        assert nfse.prestador.endereco.codigo_municipio == "2905701"
        assert nfse.prestador.endereco.uf == "BA"
        assert nfse.prestador.endereco.cep == "42802580"

        # Tomador em Salvador/BA — IBGE 2927408. Bairro "API" (OCR comeu o "I"
        # de "IAPI") mantido fiel, sem fabricar a letra.
        assert nfse.tomador.cnpj_cpf == "01813680000125"
        assert nfse.tomador.razao_social == "DELTALINE SERVICOS LTDA"
        assert nfse.tomador.endereco.logradouro == "R CAMBORIU"
        assert nfse.tomador.endereco.numero == "39"
        assert nfse.tomador.endereco.bairro == "API"
        assert nfse.tomador.endereco.municipio == "SALVADOR"
        assert nfse.tomador.endereco.codigo_municipio == "2927408"
        assert nfse.tomador.endereco.uf == "BA"
        assert nfse.tomador.endereco.cep == "40330533"

        # Nota ISENTA (alíquota 0 / ISS 0 / sem retenção). Decisão do usuário:
        # ValorServicos = TOTAL SERVIÇOS (16.500, bruto); BaseCalculo = VALOR
        # TRIBUTÁVEL (14.685). Ambos vêm da camada digital (o OCR corrompe o
        # tributável). Líquido = base (sem retenção).
        val = nfse.valores
        assert val.valor_servicos == pytest.approx(16500.00)
        assert val.base_calculo == pytest.approx(14685.00)
        assert val.aliquota == pytest.approx(0.0)
        assert val.valor_iss == pytest.approx(0.0)
        assert val.iss_retido is False
        assert val.valor_liquido_nfse == pytest.approx(14685.00)

        # Sem marca de Simples Nacional (tipo tributação ISENTO).
        assert nfse.optante_simples_nacional is False
        assert nfse.regime_especial_tributacao is None

        # Aviso honesto: nota avulsa não traz código de verificação.
        assert "Código de verificação/autenticidade não encontrado" in nfse.avisos
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
