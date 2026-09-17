# -*- coding: utf-8 -*-
r"""Endereco e codigo de autenticidade da NFS-e de Camacari/BA ESCANEADA
(`LAYOUT_CAMACARI_3`) — lote real "STAUMMAQ - SCAN 3.pdf", notas n 4497
(pag. 2) e n 4495 (pag. 4), ROSANA JULIAO CARDOSO & CIA LTDA - ME ->
STAUMMAQ SERVICOS TECNICOS.

Este lote so chegou ao extrator depois da correcao do portao de rotacao do
OCR (ver `test_ocr_rotacao_limiar_staummaq_scan3.py`): as duas paginas estavam
de cabeca para baixo e eram descartadas como "Layout nao reconhecido". Com as
notas finalmente lidas, quatro defeitos de campo ficaram visiveis — todos
aprovados pelo usuario como um lote so:

1. BAIRRO — estava FIXO em "Nao informado" no `_extrair_entidade_camacari3`,
   embora a nota imprima o campo rotulado ("Bairro: CASCALHEIRA (ABRANTES)",
   "Bairro: CIA SUL"). Ia "Nao informado" para o XML nas duas entidades.
2. CEP do prestador na pag. 2 — o OCR leu o rotulo como "GEP: 42820512" e o
   padrao exigia "CEP", entao o campo inteiro se perdia e o CEP saia zerado,
   apesar de legivel na nota. Mesma classe de defeito do rotulo "CEP/CID/UF"
   do `localiza_fatura`: UM rotulo maltratado derruba o dado que vem depois.
3. LOGRADOURO da pag. 2 — "Logradouro: — BA 522 - VIA CASCALHEIRA": o
   travessao da borda da celula ia grudado para o XML (o `.strip(' .:|')` do
   `_campo` nao cobre traco nem travessao).
4. CODIGO DE AUTENTICIDADE da pag. 2 — o cabecalho e lido tres vezes no fluxo
   escaneado; duas leituras deram "BZz68G363T" e a terceira deu o impresso,
   "BZ68G363T". Como o `.upper()` vinha ANTES da escolha, a primeira leitura
   virava "BZZ68G363T" (um caractere a mais) e era aceita de imediato.

TETO DE OCR ASSUMIDO (pag. 4): o codigo impresso e "ME5IPR77B", mas as tres
leituras de pagina concordam em "MESIPR77B" (S no lugar do 5) e um recorte
dedicado, varrendo 300/400/600 dpi x 2x/4x x PSM 6/7/8/13 x whitelist, nao
produziu o valor impresso em NENHUMA das 48 combinacoes. O extrator mantem o
que leu em vez de escrever um valor que nao consegue ler — vale a regra
padrao do projeto: nao inventar dado fiscal. O teste abaixo FIXA esse
comportamento, e o dia em que o OCR melhorar ele avisa.
"""
import os

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor

# Texto REAL do Tesseract, verbatim. Os tres blocos iniciais de cada pagina
# sao as releituras do recorte de cabecalho que o fluxo escaneado concatena
# antes da pagina inteira — e a razao de o mesmo codigo de autenticidade
# aparecer tres vezes, nem sempre igual.
MOCK_P2 = """\
Número da Nota

4497
Data de Emissão

24/07/2026 13:29
Código de autenticidade
BZz68G363T
021674001
Nº: SN

mero da Nota
4497
ta de Emissão
24/07/2026 13:29
digo de autenticidade
BZz68G363T
1
Nº: SN
UF: BA

Número da Nota
4497
Data de Emissão
24/07/2026 13:29
Código de autenticidade
BZ68G363T
0021674001
Nº: SN

Y RR Número da Nota
ah PREFEITURA MUNICIPAL DE CAMAÇARI
ma Ra a Data de Emissão
e Secretaria da Fazenda
pa NOTA FISCAL DE SERVIÇOS ELETRÔNICA
PRESTADOR DE SERVIÇOS
E 20 Nome/Razão Social: ROSANA JULIAO CARDOSO & CIA LTDA - ME
SEMIL CPF/CNPJ: 11.289.382/0001-31 Inscrição Municipal: 0021674001
Logradouro: — BA 522 - VIA CASCALHEIRA Nº: SN
Compl.: SALA 04 Bairro:  CASCALHEIRA (ABRANTES)
GEP: 42820512 Município: CAMAÇARI UF: BA
TOMADOR DE SERVIÇOS
Nome/Razão Social: STAUMMAQ SERVICOS TECNICOS AUTOMACA MOTORES E MAQ LTDA
CPF/CNPJ: 02.370.080/0001-00 Inscrição Municipal:
Logradouro: | VIA URBANA Nº: 01
Compl.: Bairro: CIA SUL
CEP: 43700000 Município: SIMÕES FILHO UF: BA
DISCRIMINAÇÃO DOS SERVIÇOS
DESCRIÇÃO QTD VALOR UNIT (R$) VALOR TOTAL (R$)
MANUTENÇÃO PREVENTIVA ATRAVÉS DOS TESTE EM ÓLEO ISOLANTE DE 1,0000 1.466,98 1.466,98
TRANSFORMADORES CONFORME PROPOSTA SEMIL295/2026
DOC EMITIDO POR EP NÃO GERA DIREITO A CREDITO FISCAL DE ICMS, ISS E 0,0000 0,00 0,00
IPI. EMPRESA OPTANTE DO SIMPLES NACIONAL. SERVIÇO REALIZADO NA
Ema 04/08/2026 ATRAVÉS DE BOLETO BANCÁRIO EMITIDO PELO 0,0000 0,00 0,00
BANCO ITAU
Ea ot mare ea
SR ga
Elia XML º PDF [offipsiAR
Retenções (R$) 4 Totais (R$)
PIS: LG 0,00 |Valor dos Serviços (R$) 1.466,98
COFINS: > 0,00 | Deduções (-) 0,00
INSS: 17074 0,00 | Base de Cálculo (=) 1.466,98
IR: "3 0,00 | Alíquota (%) 3,78
CSLL: 61 (19 0,00 | Valor do ISS (R$) 55,45
Outras: tg 0,00 | Valor Líquido da Nota (=) 1.466,98
Total de Retenções: |) lay 0,00
Tipo de tributação: A RECOLHER PELO PRESTADOR Data da prestação do serviço: 24/07/2026
Município da prestação do serviço: 2905701 - CAMACARI
Município da tributação: 2905701 - CAMACARI
CNAE:
Serviço: 001401 - LUBRIFICAÇÃO, LIMPEZA, LUSTRAÇÃO, REVISÃO, CARGA E RECARGA, CONSERTO, RESTAURAÇÃO, BLINDAGEM,
MANUTENÇÃO E CONSERVAÇÃO DE MÁQUINAS, VEÍCULOS, APARELHOS, EQUIPAMENTOS, MOTORES, ELEVADORES OU DE
QUALQUER OBJETO (EXCETO PEÇAS E PARTES EMPREGADAS, QUE FICAM SUJEITAS AO ICMS).
CPqD - Gestão Pública Data Impressão: 24/07/2026 13:29
"""

MOCK_P4 = """\
Número da Nota

4495
Data de Emissão

23/07/2026 13:35
Código de autenticidade
MESIPR77B
021674001
Nº: SN

nero da Nota
4495
à de Emissão
23/07/2026 13:35
ligo de autenticidade
MESIPR77B
|
Nº: SN
UF: BA

Número da Nota
4495
Data de Emissão
23/07/2026 13:35
Código de autenticidade
MESIPR77B
021674001
Nº: SN

FT
e PREFEITURA MUNICIPAL DE CAMAÇARI 4495
ipa Secretaria da Fazenda
e 23/07/2026 13:35
ed NOTA FISCAL DE SERVIÇOS ELETRÔNICA
PRESTADOR DE SERVIÇOS
ema Nome/Razão Social: ROSANA JULIAO CARDOSO & CIA LTDA - ME

SEMIL CPF/CNPJ: 11.289.382/0001-31 Inscrição Municipal: 0021674001

Logradouro: BA 522 - VIA CASCALHEIRA Nº: SN

Compl.: SALA 04 Bairro: -CASCALHEIRA (ABRANTES)

CEP: 42820512 Município: CAMAÇARI UF: BA

TOMADOR DE SERVIÇOS
Nome/Razão Social: STAUMMAQ SERVICOS TECNICOS AUTOMACA MOTORES E MAQ LTDA
CPF/CNPJ: 02.370.080/0001-00 Inscrição Municipal:
Logradouro: VIA URBANA Nº: 01
Compl.: Bairro: CIA SUL
CEP: 43700000 Município: SIMÕES FILHO UF: BA
DISCRIMINAÇÃO DOS SERVIÇOS
DESCRIÇÃO QTD VALOR UNIT (R$) VALOR TOTAL (R$)
MANUTENÇÃO PREVENTIVA ATRAVÉS DOS TESTE EM ÓLEO ISOLANTE DE 1,0000 1.466,98 1.466,98
TRANSFORMADORES CONFORME PROPOSTA SEMIL293/2026
DOC EMITIDO POR EP NÃO GERA DIREITO A CREDITO FISCAL DE ICMS, ISS E 0,0000 0,00 0,00
IPI. EMPRESA OPTANTE DO SIMPLES NACIONAL. SERVIÇO REALIZADO NA
ca Pa 04/08/2026 ATRAVÉS DE BOLETO BANCÁRIO EMITIDO PELO 0,0000 0,00 0,00
BANCO ITAU E
[aldeuméra XML PDF [alftssides
Retenções (R$) Totais (R$)

PIS: /9 0,00 | Valor dos Serviços (R$) 1.466,98
COFINS: d) 0,00 | Deduções (-) 0,00
INSS: GAL 0,00 | Base de Cálculo (=) 1.466,98
IR: Ny " 0,00 |Alíquota (%) 3,78
CSLL: (% 0,00 | Valor do ISS (R$) 55,45
Outras: BIO 0,00 | Valor Líquido da Nota (=) 1.466,98
Total de Retenções: á 0,00
Tipo de tributação: A RECOLHER PELO PRESTADOR Data da prestação do serviço: 23/07/2026
Município da prestação do serviço: 2905701 - CAMACARI
Município da tributação: 2905701 - CAMACARI
CNAE:
Serviço: 001401 - LUBRIFICAÇÃO, LIMPEZA, LUSTRAÇÃO, REVISÃO, CARGA E RECARGA, CONSERTO, RESTAURAÇÃO, BLINDAGEM,
MANUTENÇÃO E CONSERVAÇÃO DE MÁQUINAS, VEÍCULOS, APARELHOS, EQUIPAMENTOS, MOTORES, ELEVADORES OU DE
QUALQUER OBJETO (EXCETO PEÇAS E PARTES EMPREGADAS, QUE FICAM SUJEITAS AO ICMS).
CPqD - Gestão Pública Data Impressão: 23/07/2026 13:35
"""


def _parse(monkeypatch, tmp_path, mock, numero):
    """Roda o extrator sobre UMA pagina do lote, como `parse_multiple` faz."""
    caminho = tmp_path / ("2026.07.%s - NF %s - ROSANA JULIAO CARDOSO.pdf" % (
        "24" if numero == "4497" else "23", numero))
    caminho.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: mock)

    extractor = SPPdfExtractor(str(caminho))
    notas = extractor.parse_multiple()
    assert len(notas) == 1
    return extractor, notas[0]


@pytest.fixture
def nota_4497(monkeypatch, tmp_path):
    return _parse(monkeypatch, tmp_path, MOCK_P2, "4497")


@pytest.fixture
def nota_4495(monkeypatch, tmp_path):
    return _parse(monkeypatch, tmp_path, MOCK_P4, "4495")


@pytest.mark.parametrize("mock, numero", [("MOCK_P2", "4497"), ("MOCK_P4", "4495")])
def test_as_duas_paginas_usam_o_extrator_dedicado_do_camacari_escaneado(
        monkeypatch, tmp_path, mock, numero):
    """Pre-condicao de tudo o que vem depois: quem responde por estas notas e
    o `_extrair_entidade_camacari3` — nao o generico compartilhado por ~30
    layouts, nem o CAMACARI_2. E por isso que os quatro campos foram
    corrigidos LA, e nao no CAMACARI_2 (que o proprio codigo documenta como
    duplicado de proposito, para nao mexer no que ja esta validado)."""
    vistos = []
    original = SPPdfExtractor._extrair_entidade_camacari3

    def espiao(self, is_prestador):
        vistos.append(self.layout)
        return original(self, is_prestador)

    monkeypatch.setattr(SPPdfExtractor, "_extrair_entidade_camacari3", espiao)
    _parse(monkeypatch, tmp_path, globals()[mock], numero)
    assert vistos and set(vistos) == {"camacari_ba_scan_v3"}


def test_nota_4497_identificacao(nota_4497):
    """Ancora o resto do arquivo: e mesmo a nota 4497 que esta sendo lida."""
    _, n = nota_4497
    assert n.numero == "4497"
    assert n.data_emissao.strftime("%d/%m/%Y") == "24/07/2026"
    assert n.prestador.cnpj_cpf == "11289382000131"
    assert n.tomador.cnpj_cpf == "02370080000100"


# --------------------------------------------------------------- 1. BAIRRO

def test_bairro_do_prestador_sai_da_nota_e_nao_mais_fixo(nota_4497):
    """Defeito 1: o campo existe impresso, so nao era lido."""
    _, n = nota_4497
    assert n.prestador.endereco.bairro == "CASCALHEIRA (ABRANTES)"


def test_bairro_do_tomador_sai_da_nota(nota_4497):
    """Mesmo defeito na outra entidade — "Compl.: Bairro: CIA SUL", com o
    complemento vazio, entao o bairro e a unica coisa na linha."""
    _, n = nota_4497
    assert n.tomador.endereco.bairro == "CIA SUL"


def test_bairro_com_hifen_colado_na_pagina_4(nota_4495):
    """Na pag. 4 o mesmo bairro sai "Bairro: -CASCALHEIRA (ABRANTES)": o
    hifen e borda de celula, nao parte do nome."""
    _, n = nota_4495
    assert n.prestador.endereco.bairro == "CASCALHEIRA (ABRANTES)"
    assert not n.prestador.endereco.bairro.startswith("-")


def test_bairro_nao_engole_o_complemento(nota_4497):
    """Bairro e complemento dividem a MESMA linha; ler um nao pode estragar o
    outro (o complemento ja era extraido antes deste fix)."""
    _, n = nota_4497
    assert n.prestador.endereco.complemento == "SALA 04"


# ------------------------------------------------------------------ 2. CEP

def test_cep_do_prestador_com_rotulo_lido_como_gep(nota_4497):
    """Defeito 2: "GEP: 42820512" — o dado depois do rotulo estava legivel o
    tempo todo; quem falhava era o casamento do rotulo."""
    _, n = nota_4497
    assert n.prestador.endereco.cep == "42820512"


def test_cep_do_prestador_na_pagina_4_continua_igual(nota_4495):
    """A pag. 4 imprime o rotulo certo ("CEP:") e o MESMO CEP — prova de que
    a tolerancia nova nao mudou o caminho que ja funcionava, e de que o valor
    recuperado na pag. 2 confere com o da nota irma."""
    _, n = nota_4495
    assert n.prestador.endereco.cep == "42820512"


def test_cep_do_tomador_nas_duas_paginas(nota_4497, nota_4495):
    assert nota_4497[1].tomador.endereco.cep == "43700000"
    assert nota_4495[1].tomador.endereco.cep == "43700000"


# ----------------------------------------------------------- 3. LOGRADOURO

def test_logradouro_do_prestador_sem_travessao_colado(nota_4497):
    """Defeito 3: "Logradouro: — BA 522 - VIA CASCALHEIRA"."""
    _, n = nota_4497
    assert n.prestador.endereco.logradouro == "BA 522 - VIA CASCALHEIRA"


def test_o_hifen_interno_do_logradouro_e_preservado(nota_4497, nota_4495):
    """A limpeza e so a ESQUERDA: o "-" que separa "BA 522" de "VIA
    CASCALHEIRA" e parte do endereco e tem de sobreviver — nas duas paginas,
    inclusive na que ja vinha limpa."""
    for _, n in (nota_4497, nota_4495):
        assert " - " in n.prestador.endereco.logradouro


def test_logradouro_do_tomador_com_barra_colada(nota_4497):
    """"Logradouro: | VIA URBANA" — a barra ja era limpa pelo `_campo`; o
    teste existe para que a limpeza nova nao a desfaca."""
    _, n = nota_4497
    assert n.tomador.endereco.logradouro == "VIA URBANA"
    assert n.tomador.endereco.numero == "01"


# --------------------------------------------- 4. CODIGO DE AUTENTICIDADE

def test_codigo_de_autenticidade_prefere_a_leitura_em_caixa_alta(nota_4497):
    """Defeito 4: das tres leituras do cabecalho, duas dizem "BZz68G363T" e
    uma diz "BZ68G363T". O "z" minusculo denuncia a leitura ruim — e a boa
    nao e a maioria, entao voto nao serviria aqui."""
    _, n = nota_4497
    assert n.codigo_verificacao == "BZ68G363T"


def test_codigo_de_autenticidade_nao_ganha_caractere_a_mais(nota_4497):
    """Regressao exata do sintoma: o `.upper()` aplicado antes da escolha
    transformava "BZz68G363T" em "BZZ68G363T"."""
    _, n = nota_4497
    assert n.codigo_verificacao != "BZZ68G363T"
    assert len(n.codigo_verificacao) == 9


def test_as_tres_leituras_do_cabecalho_da_4497_estao_no_texto():
    """Ancora a premissa do fix: a leitura boa EXISTE no texto, so nao era a
    escolhida. Se o OCR mudar e ela sumir, este teste avisa antes dos outros."""
    assert MOCK_P2.count("BZz68G363T") == 2   # leituras ruins (z minusculo)
    assert MOCK_P2.count("BZ68G363T") == 1    # a leitura boa, uma so vez


def test_codigo_da_4495_mantem_o_que_o_ocr_leu(nota_4495):
    """TETO DE OCR: o impresso e "ME5IPR77B", mas as tres leituras concordam
    em "MESIPR77B" e nenhum recorte dedicado recupera o "5". O extrator
    mantem o que leu — nao inventa o valor que sabe que nao consegue ler."""
    _, n = nota_4495
    assert n.codigo_verificacao == "MESIPR77B"
    assert MOCK_P4.count("ME5IPR77B") == 0


def test_nenhuma_leitura_limpa_ainda_preenche_o_campo(nota_4495):
    """Quando NENHUM candidato vem integralmente em caixa alta+digitos o
    comportamento antigo continua valendo (primeira leitura), em vez de o
    campo cair no sentinela "XXXX-XXXX"."""
    _, n = nota_4495
    assert n.codigo_verificacao != "XXXX-XXXX"
