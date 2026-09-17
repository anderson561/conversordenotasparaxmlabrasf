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


# Texto REAL do pdfminer (nota YUI/ACBUL-212176, filial Agência Centro Cabula)
# — DIGITAL, não OCR (fonte legível: pdfminer extraiu certo, sem passar pelo
# Tesseract). Variante estruturalmente diferente da OCR acima: tudo numa
# ÚNICA linha corrida, sem quebras — e a ORDEM dos campos também é distinta
# ("CLIENTE:" vem ANTES de "CÓDIGO:", com o nome completo já junto, só faltando
# espaço antes do sufixo societário colado: "SUSTENTABILIDADELTDA"; "CNPJ -"
# vem DEPOIS do CEP/UF da filial, não antes de "Localiza"; "TOTAL" cola direto
# na data seguinte: "VALOR TOTAL04/05/2026"). Travas de regressão desta nota:
#  - sem quebra de linha nenhuma: qualquer regex ancorado em "\n" quebra aqui;
#  - "TOTAL" colado à data faz um "\b" após "TOTAL" falhar (letra->dígito não
#    é fronteira de palavra) — por isso o regex de valor não usa mais "\b" ali;
#  - a razão social do tomador já vem completa após "CLIENTE:" (variante
#    "flat"), não deve concatenar com o fragmento de antes de "CÓDIGO:" (que
#    aqui pertenceria a uma nota diferente se usado, já que a ordem inverteu).
MOCK_DIGITAL_YUI = (
    "LOCALIZA RENT A CAR S/A AGENCIA CENTRO CABULA ROD BR 324, 1084 - CABULA"
    "41150-170 - SALVADOR - BA CNPJ - 16.670.085/0914-44 ASSISTÊNCIA A CLIENTES "
    "TEL 0800 979 2020 assistenciaaclientes@localiza.com   FATURA / DUPLICATAN"
    "º: ACBUL - 212176CLIENTE: TEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE"
    "LTDA ENDEREÇO: RUA TERRITORIO DO AMAPA, 146 CS 2 - PITUBA CEP/CID/UF: "
    "41830-540 - SALVADOR - BA CNPJ:  07.345.543/0001-90 CÓDIGO: 02640209 "
    "INSC. ESTADUAL:  069725483  DATA DE EMISSÃO: 19/04/2026  DESCRIÇÃO VALOR "
    "ALUGUEL CONFORME CONTRATO     BULF036105008  R$ 2.905,31 VALOR DO SEGURO "
    "R$ 178,50           VENCIMENTOCONDIÇÕES DE PAGAMENTOVALOR TOTAL04/05/2026 "
    "A PRAZO R$ 3.083,81 Não contribuinte de ISS s/locação cfe. LC n. 116/03 "
    "       Sacador: Aceite:  "
)


def test_extract_localiza_variante_digital_sem_quebras(monkeypatch):
    dummy_path = "tests/dummy_localiza_digital.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    # Aqui é o pdfminer (extract_text) que já devolve o texto certo — não passa
    # por OCR (tem "CNPJ" e > 200 chars).
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_DIGITAL_YUI)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        assert nfse.numero == "212176"

        # Prestador: filial "Agência Centro Cabula" — CNPJ/endereço diferentes
        # de qualquer outra amostra (raiz 16.670.085, sufixo 0914-44).
        assert nfse.prestador.cnpj_cpf == "16670085091444"
        assert nfse.prestador.endereco.logradouro == "ROD BR 324"
        assert nfse.prestador.endereco.numero == "1084"
        assert nfse.prestador.endereco.bairro == "CABULA"
        assert nfse.prestador.endereco.cep == "41150170"

        # Tomador: razão social já completa após "CLIENTE:" (variante "flat"),
        # com o sufixo colado separado corretamente.
        assert nfse.tomador.cnpj_cpf == "07345543000190"
        assert nfse.tomador.razao_social == "TEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDA"
        assert nfse.tomador.endereco.logradouro == "RUA TERRITORIO DO AMAPA"
        assert nfse.tomador.endereco.numero == "146"

        # Valor: rótulo colado direto na data seguinte, sem "R$" logo depois.
        assert nfse.valores.valor_servicos == pytest.approx(3083.81)

        assert nfse.avisos == []
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


# Texto REAL do pdfminer (nota ACFSA-237512, filial Agência Centro Feira de
# Santana) — DIGITAL, 4 páginas (fatura + boleto/Pix + contrato de aluguel +
# resumo de carros utilizados), unidas por "\x0c". Travas de regressão desta
# nota:
#  - o endereço da FILIAL emissora ("R MARIA QUITÉRIA, 1197 - FEIRA DE
#    SANTANA - BA") faz o município do PRESTADOR colidir com o check solto e
#    genérico `FEIRA DE SANTANA` do LAYOUT_FEIRA, que rodava ANTES do check
#    (mais específico) do Localiza na cadeia de detecção — a nota inteira
#    caía no layout errado. O check do Localiza precisa vir antes;
#  - a pág. 4 (resumo de carros) reintroduz "Localiza Rent a Car S.A." (com
#    PONTO, não a barra "S/A" das págs. 1-2) — a exclusão de nota fantasma em
#    `is_new_invoice` que só reconhecia a grafia com barra deixava passar
#    essa página como nota nova;
#  - o município do prestador ("FEIRA DE SANTANA") e do tomador ("SALVADOR")
#    estão cadastrados em KNOWN_CITIES por nome, mas só são resolvidos por
#    nome quando `city_hint` é passado explicitamente — sem isso, cai
#    silenciosamente no código da capital padrão da UF;
#  - código do serviço (locação de bens móveis) precisa ser "0601", não o
#    "03115" genérico de fallback.
MOCK_DIGITAL_ACFSA = (
    "LOCALIZA RENT A CAR S/A AG CENTRO FEIRA DE SANTANA R MARIA QUITÉRIA, 1197 - BRASILIA"
    "44088-000 - FEIRA DE SANTANA - BA CNPJ - 16.670.085/0893-85 ASSISTÊNCIA A CLIENTES "
    "TEL 0800 979 2020 assistenciaaclientes@localiza.com   FATURA / DUPLICATANº: ACFSA - "
    "237512CLIENTE: TEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADELTDA ENDEREÇO: RUA "
    "TERRITORIO DO AMAPA, 146 CS 2 - PITUBA CEP/CID/UF: 41830-540 - SALVADOR - BA CNPJ:  "
    "07.345.543/0001-90 CÓDIGO: 02640209 INSC. ESTADUAL:  069725483  DATA DE EMISSÃO: "
    "01/06/2026  DESCRIÇÃO VALOR ALUGUEL CONFORME CONTRATO     FSAF116902  R$ 848,10 VALOR "
    "DO SEGURO R$ 53,85           VENCIMENTOCONDIÇÕESDE PAGAMENTOVALOR TOTAL16/06/2026 A "
    "PRAZO R$ 901,95 Não contribuinte de ISS s/locação cfe. LC n. 116/03        Sacador: "
    "Aceite:  "
    "\x0c"
    "16/06/202616/06/20262938 / 57004-72938 / 57004-7109061074492109061074492R$ "
    "901,95R$ 901,95R$ 0,00R$ 0,00R$ 901,95R$ 901,95Valor da faturaValor da faturaR$ "
    "901,95Data de VencimentoData de Vencimento16/06/2026DescriçãoDescriçãoFatura "
    "237512BeneficiárioBeneficiárioLOCALIZA RENT A CAR S/AAv. Bernardo de Vasconcelos, "
    "377 -Cachoeirinha - BELO HORIZONTE/MGCNPJ: 16.670.085/0001-55 Agência / Código do "
    "beneficiárioAgência / Código do beneficiário2938 / 57004-7 Olá, Olá, TEMIS PROJETOS "
    "DE MEIO AMBIENTE E SUSTENTABILIDADE LTDATEMIS PROJETOS DE MEIO AMBIENTE E "
    "SUSTENTABILIDADE LTDA  !!"
    "\x0c"
    "Contrato de Aluguel de Carros/Proposta de SeguroN° FSAF116902FechadoACFSA-237512"
    "Empresa:02640209TEMIS PROJETOS DE MEIOAMBIENTE E SUSTENTABILUsuário:17337981MARIANA "
    "SANTOS DE JESUSVeículo:TEL1G59      Onix Plus LT 1.0 Custo Pré-fixado de Limite de "
    "Danos: Grupo Reservado: CS - Economico C/Ar Sedan Grupo Cobrado: CS - Economico C/Ar "
    "Sedan   TOTAL GERAL 901,95  FATURADO PARA EMPRESA 901,95  SALDO DEVIDO 901,95"
    "\x0c"
    "17337981 - MARIANA SANTOS DE JESUSUsuárioRESUMO DE CARROS UTILIZADOS DO CONTRATONo. "
    "FSAF116902R. Maria Quitéria, 1197 - Brasilia44088-000 - Feira de Santana - BACNPJ: "
    "16670085089385Telefone 08009792020Assistência a Clientes: 0800 979 2020Localiza Rent "
    "a Car S.A.AG CENTRO FEIRA DE SANTANALocatárioCNPJ: 0734554300019002640209 - TEMIS "
    "PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDAR: Territorio do Amapa n.146 - "
    "Pituba41830540 Salvador - BA - BrasilPC9PBUC5G5DIReservaUtilizadaDia   "
    "Hora310822454223460TEL1G59Onix Sedan 1.029/05/2026 15:5401/06/2026 15:56"
    "\x0c"
)


def test_detect_localiza_nao_colide_com_feira_de_santana():
    """Regressão de produção (nota real ACFSA-237512): o endereço da própria
    filial emissora ("...FEIRA DE SANTANA - BA") não pode fazer a nota cair
    no LAYOUT_FEIRA — o check do Localiza precisa vir antes na cadeia."""
    dummy_path = "tests/dummy_localiza_feira.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    try:
        ex = SPPdfExtractor(dummy_path)
        ex.raw_text = ("LOCALIZA RENT A CAR S/A AG CENTRO FEIRA DE SANTANA "
                        "44088-000 - FEIRA DE SANTANA - BA "
                        "FATURA / DUPLICATANº: ACFSA - 237512")
        assert ex._detect_layout() == LAYOUT_LOCALIZA
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_extract_localiza_variante_feira_de_santana_4_paginas(monkeypatch):
    dummy_path = "tests/dummy_localiza_acfsa.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_DIGITAL_ACFSA)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()

        # As págs. 2-4 (boleto/Pix, contrato, resumo de carros) são
        # continuação da mesma fatura — inclusive a pág. 4, que reintroduz
        # "Localiza Rent a Car S.A." (com ponto) como nome da filial.
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        assert nfse.numero == "237512"
        assert nfse.data_emissao.strftime("%d/%m/%Y") == "01/06/2026"
        assert nfse.codigo_verificacao == "FATURA"
        assert nfse.servico_codigo == "0601"

        # Prestador: município "FEIRA DE SANTANA" resolvido por nome (não o
        # fallback de capital da UF, que seria Salvador).
        assert nfse.prestador.cnpj_cpf == "16670085089385"
        assert nfse.prestador.razao_social == "LOCALIZA RENT A CAR S/A"
        assert nfse.prestador.endereco.municipio == "FEIRA DE SANTANA"
        assert nfse.prestador.endereco.codigo_municipio == "2910800"
        assert nfse.prestador.endereco.uf == "BA"

        # Tomador: município "SALVADOR" também resolvido por nome.
        assert nfse.tomador.cnpj_cpf == "07345543000190"
        assert nfse.tomador.razao_social == "TEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDA"
        assert nfse.tomador.endereco.municipio == "SALVADOR"
        assert nfse.tomador.endereco.codigo_municipio == "2927408"
        assert nfse.tomador.endereco.uf == "BA"

        val = nfse.valores
        assert val.valor_servicos == pytest.approx(901.95)
        assert val.valor_liquido_nfse == pytest.approx(901.95)

        assert nfse.avisos == []
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


# ----------------------------------------------------------------------
# 3a VARIANTE DO BLOCO DO TOMADOR (achado real 2026-09-14, nota AAMCZ-529060,
# filial AGENCIA AEROPORTO MACEIO -> STAUMMAQ SERVICOS TECNICOS AUTOMACAO
# MOTORES E MAQUINAS LTDA, Simoes Filho/BA, R$ 3.517,61).
#
# Relatado pelo usuario como "tomador extraido incorreto". Sao DOIS defeitos
# independentes nesta mesma nota:
#
# 1. RAZAO SOCIAL FUNDIDA COM A COLUNA DA DIREITA. O discriminador entre os
#    formatos usava a ORDEM dos rotulos: se "CLIENTE:" vinha antes de
#    "CODIGO:", assumia que o nome ja estava completo. Nesta nota "CLIENTE:"
#    vem antes MESMO o nome estando quebrado em 2 fragmentos, com a coluna da
#    direita intercalada. Saia:
#      "—STAUMMAQ SERVICOS TECNICOS AUTOMACAO MOTORES E CODIGO: 01945295
#       "MAQUINAS LTDA INSC. ESTADUAL: 048137340"
#
# 2. ROTULO "CEP/CID/UF:" ILEGIVEL NO SCAN -> UMA causa-raiz, CINCO campos
#    errados. O OCR leu as barras como "I" ("CEPICID/UF:"), o regex ancora
#    exigia as barras literais, e sem esse match caem juntos: CNPJ (sentinela
#    00000000000000), endereco, bairro, municipio (fallback silencioso de
#    Salvador, sendo a nota de Simoes Filho) e CEP (zerado).
#
# Texto REAL do OCR (Tesseract via _ocr_page), verbatim.
MOCK_OCR_AAMCZ_STAUMMAQ = (
    "LOCALIZA RENT A CAR S/A ASSISTÊNCIA A CLIENTES\n"
    "AGENCIA AEROPORTO MACEIO TEL 0800 979 2020\n"
    "SlLocaliza HALL AEROPORTO ZUMBI DOS PALMARES, S/N - AEROPORTO assistenciaaclientesQlocaliza com\n"
    "51700-000 - RIO LARGO - AL\n"
    "CNPJ - 16.670.085/0028-75\n"
    "\n"
    "FATURA / DUPLICATA Nº: AAMCZ - 529060\n"
    "\n"
    "CLIENTE: —STAUMMAQ SERVICOS TECNICOS AUTOMACAO MOTORES E CÓDIGO: 01945295\n"
    "\"MAQUINAS LTDA INSC. ESTADUAL: 048137340\n"
    "\n"
    "ENDEREÇO:URBANA, 1 CIA SUL - CIA SUL\n"
    "\n"
    "CEPICID/UF:43721-450 - SIMOES FILHO - BA DATA DE EMISSÃO:18/08/2026\n"
    "\n"
    "CNPJ: 02.370.080/0001-00\n"
    "\n"
    "ALUGUEL CONFORME CONTRATO RLGA486217 R$ 3.481,71\n"
    "\n"
    "VALOR DO SEGURO R$ 35,90\n"
    "\n"
    "| VENCIMENTO TT CONDIÇÕESDE PAGAMENTO VALOR TOTAL\n"
    "02/09/2026 A PRAZO R$ 3.517,61\n"
    "\n"
    "Não contribuinte de ISS s/locação cfe. LC n. 116/03\n"
    "\n"
    "Aceite:\n"
)


def _parse_staummaq(monkeypatch, texto=None):
    """Nome do arquivo dummy sem o numero da nota de proposito: existe um
    fallback que pesca o numero do nome do arquivo."""
    dummy = "tests/dummy_localiza_scan.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy, "wb") as f:
        f.write(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text",
                        lambda path: texto if texto is not None else MOCK_OCR_AAMCZ_STAUMMAQ)
    try:
        ex = SPPdfExtractor(dummy)
        return ex, ex.parse()
    finally:
        if os.path.exists(dummy):
            os.remove(dummy)


def test_staummaq_layout_localiza(monkeypatch):
    ex, _ = _parse_staummaq(monkeypatch)
    assert ex.layout == LAYOUT_LOCALIZA


def test_staummaq_razao_social_do_tomador_reconstruida(monkeypatch):
    """O defeito relatado: os 2 fragmentos do nome saiam fundidos com os
    rotulos da coluna da direita."""
    _, nfse = _parse_staummaq(monkeypatch)
    assert nfse.tomador.razao_social == (
        "STAUMMAQ SERVICOS TECNICOS AUTOMACAO MOTORES E MAQUINAS LTDA"
    )


def test_staummaq_razao_social_sem_rotulos_da_coluna_vizinha(monkeypatch):
    _, nfse = _parse_staummaq(monkeypatch)
    razao = nfse.tomador.razao_social
    for lixo in ("CÓDIGO", "CODIGO", "INSC", "ESTADUAL", "01945295", "048137340", '"', "—"):
        assert lixo not in razao, "razao social ainda carrega %r" % lixo


def test_staummaq_cnpj_do_tomador(monkeypatch):
    """Saia sentinela: o CNPJ so e' procurado DEPOIS do match do endereco, que
    falhava pelo rotulo CEP/CID/UF ilegivel."""
    _, nfse = _parse_staummaq(monkeypatch)
    assert nfse.tomador.cnpj_cpf == "02370080000100"
    assert not nfse.tomador.cnpj_cpf.startswith("00000000000")


def test_staummaq_tomador_nao_herda_cnpj_do_prestador(monkeypatch):
    _, nfse = _parse_staummaq(monkeypatch)
    assert nfse.tomador.cnpj_cpf != nfse.prestador.cnpj_cpf


def test_staummaq_municipio_do_tomador_nao_cai_em_salvador(monkeypatch):
    """Fallback silencioso: sem o match do endereco o municipio ia para
    Salvador/BA (2927408), sendo a nota de Simoes Filho/BA."""
    _, nfse = _parse_staummaq(monkeypatch)
    end = nfse.tomador.endereco
    assert end.municipio == "SIMOES FILHO"
    assert end.codigo_municipio == "2930709"
    assert end.codigo_municipio != "2927408"
    assert end.uf == "BA"


def test_staummaq_endereco_e_cep_do_tomador(monkeypatch):
    _, nfse = _parse_staummaq(monkeypatch)
    end = nfse.tomador.endereco
    assert end.logradouro == "URBANA"
    assert end.numero == "1"
    assert end.bairro == "CIA SUL"
    assert end.cep == "43721450"
    assert end.cep != "00000000"


def test_staummaq_rotulo_cep_cid_uf_tolerante_ao_ocr(monkeypatch):
    """A ancora tem que aceitar as barras lidas como I, | ou 1 -- e continuar
    aceitando o rotulo limpo."""
    for variante in ("CEPICID/UF:", "CEP/CID/UF:", "CEP|CID|UF:", "CEP/CID/UF :"):
        texto = MOCK_OCR_AAMCZ_STAUMMAQ.replace("CEPICID/UF:", variante)
        _, nfse = _parse_staummaq(monkeypatch, texto)
        assert nfse.tomador.cnpj_cpf == "02370080000100", "falhou com %r" % variante
        assert nfse.tomador.endereco.codigo_municipio == "2930709", "falhou com %r" % variante


def test_staummaq_campos_da_nota(monkeypatch):
    _, nfse = _parse_staummaq(monkeypatch)
    assert nfse.numero == "529060"
    assert nfse.data_emissao.strftime("%d/%m/%Y") == "18/08/2026"
    assert nfse.valores.valor_servicos == pytest.approx(3517.61)
    assert nfse.valores.valor_liquido_nfse == pytest.approx(3517.61)
    # Locacao de bens moveis: a propria nota diz "Nao contribuinte de ISS
    # s/locacao cfe. LC n. 116/03".
    assert nfse.valores.base_calculo == 0.0
    assert nfse.valores.valor_iss == 0.0
    assert nfse.servico_codigo == "0601"


def test_staummaq_prestador_e_a_filial_de_maceio(monkeypatch):
    """O CNPJ da filial nao pode ser fixo no codigo: a Localiza usa 1 CNPJ por
    estabelecimento sobre a raiz 16.670.085."""
    _, nfse = _parse_staummaq(monkeypatch)
    assert nfse.prestador.cnpj_cpf == "16670085002875"
    assert nfse.prestador.razao_social == "LOCALIZA RENT A CAR S/A"
    assert nfse.prestador.endereco.uf == "AL"


def test_staummaq_sem_aviso_de_entidade_nao_identificada(monkeypatch):
    _, nfse = _parse_staummaq(monkeypatch)
    assert not any("tomador" in a.lower() for a in nfse.avisos), nfse.avisos


# ----------------------------------------------------------------------
# COLATERAIS aprovados pelo usuario em 2026-09-14, achados ao corrigir o
# tomador da nota AAMCZ-529060.
# ----------------------------------------------------------------------

def test_staummaq_sem_intermediario_fantasma(monkeypatch):
    """Uma fatura da Localiza nao tem intermediario. O extrator do TOMADOR
    rodava de novo para esse papel e o XML saia com um <Intermediario>
    repetindo o tomador inteiro -- pior depois da correcao do tomador, porque
    o bloco duplicado passa a ter dados corretos e parece legitimo."""
    _, nfse = _parse_staummaq(monkeypatch)
    assert nfse.intermediario is None


def test_intermediario_none_tambem_na_variante_digital(monkeypatch):
    """O mesmo defeito existia em todas as notas do layout, nao so' na scan."""
    dummy = "tests/dummy_localiza_sem_interm.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy, "wb") as f:
        f.write(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text",
                        lambda path: MOCK_DIGITAL_ACFSA)
    try:
        nfse = SPPdfExtractor(dummy).parse()
        assert nfse.intermediario is None
    finally:
        if os.path.exists(dummy):
            os.remove(dummy)


def test_staummaq_municipio_do_prestador_e_rio_largo(monkeypatch):
    """O Aeroporto Zumbi dos Palmares fica em Rio Largo/AL, nao em Maceio.
    Ausente do KNOWN_CITIES, a cidade caia na capital da UF (2704302) -- o que
    desloca tambem OrgaoGerador e MunicipioIncidencia."""
    _, nfse = _parse_staummaq(monkeypatch)
    end = nfse.prestador.endereco
    assert end.municipio == "RIO LARGO"
    assert end.codigo_municipio == "2707701"
    assert end.codigo_municipio != "2704302"
    assert end.uf == "AL"


def test_rio_largo_registrada_no_resolver_ibge():
    from src.utils.ibge_resolver import IBGEResolver
    assert IBGEResolver.KNOWN_CITIES.get("RIO LARGO") == "2707701"


def test_staummaq_endereco_do_prestador_filial_de_aeroporto(monkeypatch):
    """"HALL AEROPORTO ..." nao comeca por nenhum prefixo de via (AV/RUA/ROD),
    entao o casamento por prefixo falhava e o endereco saia "Nao informado".
    O "S/N" tambem precisa ser aceito como numero, senao o bairro se perde."""
    _, nfse = _parse_staummaq(monkeypatch)
    end = nfse.prestador.endereco
    assert end.logradouro == "HALL AEROPORTO ZUMBI DOS PALMARES"
    assert end.numero == "S/N"
    assert end.bairro == "AEROPORTO"


def test_staummaq_logradouro_do_prestador_sem_logotipo_nem_email(monkeypatch):
    """A linha do endereco vem entre o logotipo ("SlLocaliza") e o e-mail que o
    OCR cola no fim ("assistenciaaclientesQlocaliza com")."""
    _, nfse = _parse_staummaq(monkeypatch)
    log = nfse.prestador.endereco.logradouro
    assert "ocaliza" not in log
    assert "assistencia" not in log.lower()


def test_staummaq_cep_do_prestador_preserva_o_que_a_nota_imprime(monkeypatch):
    """A NOTA imprime "51700-000", que e' faixa de Recife/PE -- Rio Largo/AL e'
    57100-xxx. Conferido na imagem da nota: o erro e' do emitente, o OCR esta
    fiel. O CEP impresso e' preservado como esta; corrigi-lo seria inventar
    dado que o documento nao declara (ver o municipio, esse sim resolvido pelo
    nome da cidade, que a nota imprime corretamente)."""
    _, nfse = _parse_staummaq(monkeypatch)
    assert nfse.prestador.endereco.cep == "51700000"


def test_split_endereco_aceita_numero_e_sn(monkeypatch):
    """Guarda do formato ja coberto: endereco COM numero nao pode mudar de
    comportamento por causa do "S/N" novo."""
    _, nfse = _parse_staummaq(monkeypatch)
    # Tomador desta mesma nota usa numero real.
    assert nfse.tomador.endereco.numero == "1"
    assert nfse.prestador.endereco.numero == "S/N"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
