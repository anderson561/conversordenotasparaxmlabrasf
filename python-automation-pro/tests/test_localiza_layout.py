# -*- coding: utf-8 -*-
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_LOCALIZA
import os

# Texto REAL do OCR (Tesseract, zoom 3x) da fatura de locação da Localiza Rent A
# Car S/A (filial Trade Center Pituba/Salvador-BA), tomador TEMIS PROJETOS DE
# MEIO AMBIENTE E SUSTENTABILIDADE LTDA. A camada de texto embutida (pdfminer)
# deste PDF é ILEGÍVEL (fonte com codificação customizada/cifra de substituição
# — nem "CNPJ" nem "LOCALIZA" aparecem, mesmo o documento tendo 25k+ caracteres
# de texto extraído), por isso o parse_multiple sempre cai no OCR aqui.
# Preservado verbatim, incluindo os quirks que travam regressões:
#  - o CNPJ do prestador (filial emissora) e seu endereço/CEP NÃO podem ser
#    fixos no código: a Localiza usa 1 CNPJ por filial (raiz 16.670.085,
#    sufixo do estabelecimento) — esta nota é de uma filial diferente de
#    qualquer amostra anterior;
#  - a razão social do tomador vem quebrada em 2 fragmentos por colunas
#    intercaladas do OCR: "...SUSTENTABILIDADE CÓDIGO: 02640209\nCLIENTE: LTDA";
#  - o CNPJ do tomador só pode ser buscado numa janela DEPOIS do endereço —
#    buscar no texto inteiro pega o 1º "CNPJ:" do documento, que é o do
#    PRESTADOR (Localiza), não o do cliente;
#  - "VALOR TOTAL" e o "R$ valor" não ficam colados (rótulo, vencimento e
#    condição de pagamento entre os dois);
#  - o logradouro do prestador vem com um e-mail colado pelo OCR, sem "@"
#    legível (virou "O"): "CAMINHO ARVORES assistenciaaclientesOlocaliza.com";
#  - a pág. 2 (boleto/Pix) repete "LOCALIZA RENT A CAR S/A" só como nome do
#    beneficiário do pagamento — não é uma fatura nova, e deve ser descartada
#    como continuação (a mesma fatura não pode virar 2 XMLs).
PAGE1 = """LOCALIZA RENT A CAR S/A ASSISTÊNCIA A CLIENTES
TRADE CENTER PITUBA

TEL 0800 979 2020
AV TANCREDO NEVES, 1632 - CAMINHO ARVORES assistenciaaclientesOlocaliza.com
41820-915 - SALVADOR - BA

Localiza

CNPJ - 16.670.085/0381-28

FATURA / DUPLICATA Nº: ACPIT - 311630

. —TEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE CÓDIGO: 02640209
CLIENTE: LTDA

INSC. ESTADUAL: 069725483
ENDEREÇO:RUA TERRITORIO DO AMAPA, 146 CS 2 - PITUBA
CEP/CID/UF:41830-540 - SALVADOR - BA DATA DE EMISSÃO:31/03/2026
CNPJ: 07.345.543/0001-90

ALUGUEL CONFORME CONTRATO UBHF030772005

R$ 2.990,20
VALOR DO SEGURO

R$ 178,50

VENCIMENTO CONDIÇÕES DE PAGAMENTO VALOR TOTAL
15/04/2026 A PRAZO

R$ 3.168,70
Não contribuinte de ISS s/locação cfe. LC n. 116/03

OBSERVAÇÕES

Sacador:
"""

# Pág. 2: boleto/Pix da MESMA fatura — deve ser descartada como continuação,
# não gerar uma 2ª nota.
PAGE2 = """
« Localiza

Olá, TEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDA !

Valor da fatura Agora você pode realizar o pagamento de forma prática e rápida com o Pix.
R$ 3.168,70 Fácil, né?

Beneficiário

LOCALIZA RENT A CAR S/A

Av. Bernardo de Vasconcelos, 377 -

Cachoeirinha - BELO HORIZONTE/MG
CNPJ: 16.670.085/0001-55

Data do documento Número do documento Espécie doc. Aceite Nosso número.
31/03/2026 EPROO05CBB42 DM N 109054864461

Pagador

TEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDA - CPF/CNP]): 07345543000190 -
RUA TERRITORIO DO AMAPA, 146, CS 2
"""

MOCK_OCR = PAGE1 + "\n\x0c\n" + PAGE2

# Camada digital (pdfminer): texto embaralhado por fonte customizada, sem
# nenhuma keyword reconhecível — dispara o OCR em produção (< 200 chars OU sem
# keyword; aqui garantimos via ambos, com um texto curto e sem rótulos).
DIGITAL_TEXT = "(cid:0)(cid:1)(cid:2)(cid:3) garbled font text"


def test_detect_localiza():
    dummy_path = "tests/dummy_localiza.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    try:
        ex = SPPdfExtractor(dummy_path)
        ex.raw_text = "LOCALIZA RENT A CAR S/A\nFATURA / DUPLICATA Nº: ACPIT - 311630"
        assert ex._detect_layout() == LAYOUT_LOCALIZA
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_numero_localiza_apenas_digitos():
    """Regressão de produção (nota real YUI/ACBUL): o número precisa ser só
    dígitos (o ERP contábil rejeita "Número da NFS-e" não numérico), mesmo
    quando o rótulo seguinte ("CLIENTE") vem colado sem espaço ao número."""
    dummy_path = "tests/dummy_localiza_numero.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    try:
        ex = SPPdfExtractor(dummy_path)
        ex.layout = LAYOUT_LOCALIZA
        ex.raw_text = "FATURA / DUPLICATA Nº: ACBUL - 212176CLIENTE: LTDA"
        assert ex._extrair_numero() == "212176"
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_extract_localiza_layout(monkeypatch):
    dummy_path = "tests/dummy_localiza_full.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: DIGITAL_TEXT)
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_OCR)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()

        # A pág. 2 (boleto) é continuação da mesma fatura, não uma nota nova.
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        # Só o número, sem o código da filial ("ACPIT -") — o ERP contábil
        # rejeita "Número da NFS-e" não numérico.
        assert nfse.numero == "311630"
        assert nfse.data_emissao.strftime("%d/%m/%Y") == "31/03/2026"
        # Documento não-municipal (fatura de locação): mesmo placeholder usado
        # pelos demais layouts de locação (ARMAC, LMR, etc.), sem aviso falso.
        assert nfse.codigo_verificacao == "FATURA"

        # Prestador: CNPJ/endereço da FILIAL emissora, extraídos do texto (não
        # fixos no código) — filial diferente de qualquer amostra anterior.
        assert nfse.prestador.cnpj_cpf == "16670085038128"
        assert nfse.prestador.razao_social == "LOCALIZA RENT A CAR S/A"
        assert nfse.prestador.endereco.logradouro == "AV TANCREDO NEVES"
        assert nfse.prestador.endereco.numero == "1632"
        # E-mail colado pelo OCR (sem "@" legível) não pode vazar pro bairro.
        assert nfse.prestador.endereco.bairro == "CAMINHO ARVORES"
        assert nfse.prestador.endereco.municipio == "SALVADOR"
        assert nfse.prestador.endereco.codigo_municipio == "2927408"
        assert nfse.prestador.endereco.uf == "BA"
        assert nfse.prestador.endereco.cep == "41820915"

        # Tomador: razão social reconstituída dos 2 fragmentos intercalados;
        # CNPJ correto (não o do prestador, que aparece primeiro no texto).
        assert nfse.tomador.cnpj_cpf == "07345543000190"
        assert nfse.tomador.razao_social == "TEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDA"
        assert nfse.tomador.endereco.logradouro == "RUA TERRITORIO DO AMAPA"
        assert nfse.tomador.endereco.numero == "146"
        assert nfse.tomador.endereco.complemento == "CS 2"
        assert nfse.tomador.endereco.bairro == "PITUBA"
        assert nfse.tomador.endereco.municipio == "SALVADOR"
        assert nfse.tomador.endereco.codigo_municipio == "2927408"
        assert nfse.tomador.endereco.uf == "BA"
        assert nfse.tomador.endereco.cep == "41830540"

        # Valor total: rótulo e valor não ficam colados no texto real.
        val = nfse.valores
        assert val.valor_servicos == pytest.approx(3168.70)
        assert val.valor_liquido_nfse == pytest.approx(3168.70)

        assert nfse.avisos == []
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
