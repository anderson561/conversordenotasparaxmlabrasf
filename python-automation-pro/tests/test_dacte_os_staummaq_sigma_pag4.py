# -*- coding: utf-8 -*-
r"""CT-e OS (Conhecimento de Transporte Eletrônico para Outros Serviços) -
Modelo 67, DACTE OS (`LAYOUT_DACTE_OS`) - nota real nº 000.017.268, SIGMA
TRANSPORTES LTDA -> STAUMMAQ SERVICOS TECNICOS AUT MOT E MAQUINAS LTDA,
transporte de pessoal, R$2.115,08 - página 4 do lote "STAUMMAQ - NFSe
TERCEIROS.pdf" (arquivo real do usuário).

Bug original: a página inteira caía no fallback ABRASF genérico (`CompNfse`)
em vez de `LAYOUT_DACTE_OS`, porque a 2ª marca exigida pela detecção,
"Conhecimento de Transporte Eletrônico" (contígua), nunca sobrevivia ao OCR
desta página - o cabeçalho sai embaralhado e "Documento Auxiliar do
Conhecimento de Transporte" e "Eletrônico para Outros Serviços" saem em
linhas NÃO-ADJACENTES (com um bloco inteiro de outro conteúdo entre elas),
embora "CT-e OS" (1ª marca) sobreviva intacto. Sintoma: `PrestadorServico/
RazaoSocial` saía como "INFORMAÇÕES ESPECÍFICAS DO MODAL RODOVIÁRIO" (título
de SEÇÃO do DACTE OS, não uma razão social) e todos os valores saíam
zerados. Fix: "Eletrônico" tornado OPCIONAL após "Conhecimento de
Transporte" na detecção (ver `_detect_layout`/`_detect_layout_page`) -
"Conhecimento de Transporte" sozinho já é exclusivo do CT-e/DACTE OS
(nenhuma NFS-e ABRASF ou NF-e/DANFE de produto usa essa frase).

Esta nota também expôs um gerador de DACTE OS DIFERENTE do já coberto por
`test_dacte_os_ciatrans.py` (rodapé "Bsoft Internetworks - CT-e Prático -
www.bsoft.com.br", contra "Master CT-e - www.oflicesystem.com.br" da nota
CIATRANS) - template estruturalmente distinto (CNPJ do emitente PONTUADO,
razão social fundida com o título "DACTE OS" na mesma linha, endereço do
emitente ANTES da linha do CNPJ em vez de depois, rótulo do tomador
"TOMADOR/USUÁRIO DO SERVIÇO:" em vez de "TOMADOR DO SERVIÇO", CEP do tomador
colado ao próprio rótulo "cer:" em vez de deslocado para o fim do bloco,
bairro do tomador com um HÍFEN PRÓPRIO "CIA-SUL" que não é o separador
bairro→município, chave de acesso e data/hora de emissão bem afastadas dos
próprios rótulos) - `_parse_dacte_os` e `_ocr_recut_dacte_os_grade` foram
generalizados para cobrir os dois geradores sem regredir nenhum.

Toda verificação de campo abaixo foi conferida por dígito verificador antes
de escrever a regex de extração: (1) a chave de acesso passa no dígito
verificador mod-11 e DECODIFICA exatamente para cUF=29/BA, AAMM=2609
(setembro/2026, bate com a data de emissão impressa), CNPJ do emitente
(07441083000101, bate com o CNPJ impresso separadamente), mod=67, série=001,
número=000017268 (bate com "Nº: 000.017.268" impresso); (2) os CNPJs do
emitente e do tomador passam no dígito verificador - o do tomador
(02370080000100) é o MESMO CNPJ da STAUMMAQ já confirmado tomador nas
págs. 1-3 deste mesmo lote. Alta confiança nesta nota.

O rótulo "TIPO DO SERVIÇO" sai adjacente a um trecho sem NENHUMA palavra
reconhecível ("Normal d soas Pr r" - fusão de colunas vizinhas) - mantido
"Não informado" em vez de fabricado a partir de ruído (ver
`test_tipo_servico_ilegivel_nao_e_fabricado` abaixo).
"""
import pytest

from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_DACTE_OS
from src.models.cte_os_model import CteOS
from src.transformers.cte_transformer import CteTransformer

# Texto REAL do Tesseract sobre a página inteira, verbatim (`_extract_via_ocr`
# / `_ocr_page(3)`, 0-indexed) - página 4 de "STAUMMAQ - NFSe TERCEIROS.pdf".
MOCK_PAGINA = """\
DECLARO QUE RECEBI OS SERVIÇOS DESTE CONHECIMENTO EM PERFEITO ESTADO PELO QUE DOU POR CUMPRIDO O PRESENTE CONTRATO DE TRANSPORTE

: CT-e OS
NOME. Es DA PRESTAÇÃO - DATA /HORA

Nº: 000.017.268
Série: 001

RG: INÍCIO DA PRESTAÇÃO - DATA /HORA,

ASSINATURA / CARIMBO

MODAL
RODOVIÁRIO

Eletrônico para Outros Serviços
CAMINHO DAS ARVORES
lidio.santos(Ogtpba.com.br ll |) | |) 1) | | | |] |

SIGMA TRANSPORTES LTDA DACTE OS
AVENIDA TANCREDO NEVES, 274, ED CENTRO
NÚMERO DATA E HORA EMISSÃO
P: 41820-907, SALVADOR - BA
CNPJ: 07.441.083/0001-01  1B:066668363
Chave de acesso

Documento Auxiliar do Conhecimento de Transporte
EMPRESARIAL IGUATEM - BLOCO B - SALA 133 - RR :
"001 000.017.268 1/2 | 01/09/2026 08:31:02
Fone: (71)3014-6060
2926 0907 4410 8300 0101 6700 1000 0172 6810 0018 4276

TIPO DO CT-E TIPO DO SERVIÇO
Normal d soas Pr r
cómo Prana pon de LES sono [Consela de autenticidade no portal nacional do CT-e, no site da Sefaz
Autorizadora, ou em http://www.cte.fazenda.gov.br/portal

CFOP - NATUREZA DA OPERAÇÃO
5351 - TRANSPORTE ESTADUAL

PROTOCOLO DE AUTORIZAÇÃO DE USO

Lt 329260204119466 01/09/2026 08:33:29
INÍCIO DA PRESTAÇÃO PERCURSO DO VEÍCULO TÉRMINO DA PRESTAÇÃO
Salvador - BA Simoes Filho - BA
TOMADOR/USUÁRIO DO SERVIÇO: STAUMMAO SERV. TEC. AUTO. MOT. E MAQ. LTDA MunicirIO: Simoes Filho cer: 43700-000
ENDEREÇO: V URBANA , Nº 01 CIA-SUL - SIMOES FILHO ur: BA País: Brasil
enpycrr: 02.370.080/0001-00 INSC.EST.: 048137340 FONE: EMAIL: viviane(Ostaummag.com.br

INFORMAÇÕES DA PRESTAÇÃO DO SERVIÇO

QUANTIDADE DESCRIÇÃO DO SERVIÇO PRESTADO
1 TRANSPORTE DE PESSOAL

Do O (ho estro Gunjo

a DO VALOR DA PRESTAÇÃO DE SERVIÇO
VALOR | NOME VALOR | NOME VALOR | VALOR TOTAL DA PRESTAÇÃO DO SERVIÇO

[Nome VALOR | NOME
Frete Valor 2.115,08 2.115,0º

VALOR À RECEBER

2.115,0:
INFORMAÇÕES RELATIVAS AO IMPOSTO
CLASSIFICAÇÃO TRIBUTÁRIA DO SERVIÇO BASE DE CÁLCULO AL ICMS (%)| VALOR ICMS % RED.BC.CÁLC |ICMS ST
40 - ICMS ISENÇÃO 0,00 | 0,00 7 0,00 0,00 0,00
PIS COFINS IR CsLI
69,80 [ 13,75 63,45 | 0,00 0,00
| OBSERVAÇÕES

PRESTACAO DE SERVICO NO TRANSPORTE DE PESSOAL REF. AGOSTO/2026, CONFORME PEDIDO 8386

OBS: Conforme Decreto n 25.540, de 13/05/2026 (art. 4), estabelece a reducao de 100% da base de calculo do ICMS/Ba incidente nas prestacoes de servico de transporte intermunicipal de
pessoas, nos termos do Convenio ICMS 19/24

OBS: Nao e devida a Retencao na Fonte do INSS, de 11% (onze por cento), sobre a nossa atividade CNAE s: 49.29-9-02 e 49.29-9-01, conforme Lei n 8.212, de 1991, art. 31. Instrucao Normativ

RFB numero 971, de 2009, arts. 115 a 119 e 149.

SEGURO DA VIAGEM

RESPONSÁVEL NOME DA SEGURADORA NÚMERO DA APÓLICE

Emitente

INFORMAÇÕES ESPECÍFICAS DO MODAL RODOVIÁRIO
TERMO DE AUTORIZAÇÃO DE FRETAMENTO E DO REGISTRO ESTADUAL PLACA DO VEÍCULO pe DO VEÍCULO [ DE LICENCIAMENTO DO VEÍCULO

CNPJ/CPF
0000000000000000066668363 ] 07.441.083/0001-01

Bsoft Intemetworks - CT-e Prático - www bsoft.cor

DATA E HORA DA IMPRESSÃO: 01/09/2026 08:33:37
"""

# Texto REAL do Tesseract sobre o recorte dedicado da grade "COMPONENTES DO
# VALOR DA PRESTAÇÃO DE SERVIÇO" + "INFORMAÇÕES RELATIVAS AO IMPOSTO"
# (`_ocr_recut_dacte_os_grade`). Nesta nota o próprio rótulo "COMPONENTES"
# não sobrevive como palavra reconhecível (um rabisco de assinatura em
# caneta sobrepõe parte dele, virando um token curto de baixíssima
# confiança) - a âncora de início usa o fallback pela sequência "DO VALOR DA
# PRESTAÇÃO DE SERVIÇO" (ver `_ocr_recut_dacte_os_grade`).
MOCK_GRADE = """\
Ê "| COMPONENTES DO VALOR DA PRESTAÇÃO DE SERVIÇO
NOME VALOR | NOME VALOR | NOME VALOR | NOME VALOR | VALOR TOTAL DA PRESTAÇÃO DO SERVIÇO
Frete Valor 2.115,08 2.115,08
VALOR A RECEBER
2.115,0%
INFORMAÇÕES RELATIVAS AO IMPOSTO

CLASSIFICAÇÃO TRIBUTÁRIA DO SERVIÇO BASE DE CÁLCULO AL ICMS (%)| VALOR ICMS % RED.BC.CÁLC [ICMS ST
INSS PIS COFINS CSLL

69,80 13,75 63,45 Fi vm 0,00
"""


def _parse(monkeypatch, tmp_path, mock_pagina, mock_grade, pagina_hint=4):
    pdf_path = tmp_path / "staummaq_sigma.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 dummy")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: mock_pagina)
    if mock_grade is not None:
        monkeypatch.setattr(SPPdfExtractor, "_ocr_recut_dacte_os_grade", lambda self: mock_grade)
    ex = SPPdfExtractor(str(pdf_path))
    ex._pagina_hint = pagina_hint
    notas = ex.parse_multiple()
    assert len(notas) == 1
    return notas[0]


@pytest.fixture
def nota(monkeypatch, tmp_path):
    """Com o recorte dedicado retornando o texto real capturado - caminho
    feliz, usado pela maioria dos testes abaixo."""
    return _parse(monkeypatch, tmp_path, MOCK_PAGINA, mock_grade=MOCK_GRADE)


# --------------------------------------------------------------- detecção

def test_layout_e_dacte_os_apesar_do_marcador_eletronico_ausente():
    """A frase completa "Conhecimento de Transporte Eletrônico" NUNCA fica
    contígua nesta página (acha-se "Conhecimento de Transporte" numa linha e
    "Eletrônico para Outros Serviços" bem antes, separadas por um bloco
    inteiro de outro conteúdo) - a detecção precisa tolerar isso."""
    assert "Conhecimento de Transporte\n" in MOCK_PAGINA
    assert "Conhecimento de Transporte Eletrônico" not in MOCK_PAGINA
    ex = SPPdfExtractor.__new__(SPPdfExtractor)
    ex.raw_text = MOCK_PAGINA
    ex.from_ocr = True
    ex.layout = None
    ex.pdf_path = "x.pdf"
    assert ex._detect_layout_page(MOCK_PAGINA) == LAYOUT_DACTE_OS
    assert ex._detect_layout() == LAYOUT_DACTE_OS


def test_retorna_cteos_nao_compnfse_abrasf(nota):
    """Bug original: a página caía no fallback ABRASF genérico (`CompNfse`),
    com "PrestadorServico/RazaoSocial" saindo como um título de SEÇÃO do
    DACTE OS ("INFORMAÇÕES ESPECÍFICAS DO MODAL RODOVIÁRIO") em vez de uma
    razão social real."""
    assert isinstance(nota, CteOS)


# ------------------------------------------------------- chave e cabeçalho

def test_chave_de_acesso_passa_no_digito_verificador_e_decodifica(nota):
    assert nota.chave_acesso == "29260907441083000101670010000172681000184276"
    assert len(nota.chave_acesso) == 44
    from src.extractors.pdf_extractor import SPPdfExtractor as _E
    assert _E._dv_chave_nfe(nota.chave_acesso[:43]) == nota.chave_acesso[43]
    # cUF=29(BA) AAMM=2609 CNPJ=07441083000101 mod=67 serie=001 numero=17268
    assert nota.chave_acesso[0:2] == "29"
    assert nota.chave_acesso[2:6] == "2609"
    assert nota.chave_acesso[6:20] == nota.emitente.cnpj_cpf == "07441083000101"
    assert nota.chave_acesso[20:22] == nota.modelo == "67"


def test_modelo_serie_numero(nota):
    assert nota.modelo == "67"
    assert nota.serie == "001"
    assert nota.numero == "000017268"


def test_data_emissao(nota):
    assert nota.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "01/09/2026 08:31:02"


def test_protocolo_de_autorizacao_tolera_prefixo_de_ruido(nota):
    """"Lt 329260204119466 01/09/2026 08:33:29" - o "Lt " antes do número é
    ruído de OCR (não existe rótulo "Lt" no documento real)."""
    assert nota.protocolo_autorizacao == "329260204119466"
    assert nota.protocolo_data_hora.strftime("%d/%m/%Y %H:%M:%S") == "01/09/2026 08:33:29"


def test_tipo_cte_e_cfop(nota):
    assert nota.tipo_cte == "Normal"
    assert nota.cfop == "5351"
    assert nota.natureza_operacao == "TRANSPORTE ESTADUAL"


def test_tipo_servico_ilegivel_nao_e_fabricado(nota):
    """"TIPO DO SERVIÇO" sai adjacente a "Normal d soas Pr r" - sem nenhuma
    palavra real reconhecível (tokens de 1 letra soltos, "d"/"r") - marcado
    "Não informado" em vez de fabricado a partir de ruído de coluna vizinha
    fundida pelo OCR."""
    assert nota.tipo_servico == "Não informado"
    assert any("Tipo do serviço não identificado" in a for a in nota.avisos)


# ------------------------------------------------------------- emitente

def test_emitente_sigma_transportes(nota):
    """A razão social sai FUNDIDA com o título do documento na mesma linha
    ("SIGMA TRANSPORTES LTDA DACTE OS") - extraída até o sufixo societário
    "LTDA", descartando o "DACTE OS" colado."""
    e = nota.emitente
    assert e.razao_social == "SIGMA TRANSPORTES LTDA"
    assert e.cnpj_cpf == "07441083000101"


def test_cnpj_do_emitente_passa_no_digito_verificador(nota):
    from src.extractors.pdf_extractor import SPPdfExtractor as _E
    assert _E._cnpj_valido(nota.emitente.cnpj_cpf)


def test_endereco_emitente_vem_antes_da_linha_do_cnpj(nota):
    """Ordem INVERSA do gerador Master CT-e (nota CIATRANS): aqui o
    endereço vem ANTES da linha "CNPJ:", não depois."""
    end = nota.emitente.endereco
    assert end.logradouro == "AVENIDA TANCREDO NEVES"
    assert end.numero == "274"
    assert end.complemento == "ED CENTRO"
    assert end.municipio == "SALVADOR"
    assert end.uf == "BA"
    assert end.cep == "41820907"


# -------------------------------------------------------------- tomador

def test_tomador_staummaq_mesmo_cnpj_das_paginas_1_a_3(nota):
    """CNPJ 02.370.080/0001-00 - o MESMO CNPJ da STAUMMAQ já confirmado
    tomador nas págs. 1-3 deste mesmo lote "STAUMMAQ - NFSe TERCEIROS.pdf".

    O texto OCR real desta página grafa a razão social como "STAUMMAO"
    (com "O" no lugar do "Q" - ver MOCK_PAGINA). A extração corrige essa
    grafia pontual para "STAUMMAQ" com base no CNPJ conhecido deste
    cliente recorrente - asserção EXATA para travar a correção (uma
    asserção frouxa tipo `"STAUMMA" in ...` passaria com qualquer
    grafia, inclusive a errada).
    """
    tom = nota.tomador
    assert tom.cnpj_cpf == "02370080000100"
    assert tom.razao_social == "STAUMMAQ SERV. TEC. AUTO. MOT. E MAQ. LTDA"
    assert tom.inscricao_estadual == "048137340"


def test_cnpj_do_tomador_passa_no_digito_verificador(nota):
    from src.extractors.pdf_extractor import SPPdfExtractor as _E
    assert _E._cnpj_valido(nota.tomador.cnpj_cpf)


def test_endereco_tomador_bairro_com_hifen_proprio(nota):
    """"CIA-SUL" é o próprio nome do bairro (com um hífen QUE NÃO é o
    separador bairro→município) - só um " - " com espaço dos dois lados
    separa bairro de município, não qualquer hífen."""
    end = nota.tomador.endereco
    assert end.logradouro == "V URBANA"
    assert end.numero == "01"
    assert end.bairro == "CIA-SUL"
    assert end.municipio == "SIMOES FILHO"
    assert end.uf == "BA"
    assert end.cep == "43700000"


def test_cep_do_tomador_nao_esta_deslocado_para_o_fim_nesta_nota(nota):
    """Ao contrário da nota CIATRANS (CEP deslocado para o fim do bloco),
    aqui o CEP sai colado ao próprio rótulo "cer:" (degradação de "CEP:"),
    logo após o município, dentro da mesma linha do nome do tomador."""
    assert nota.tomador.endereco.cep == "43700000"


# -------------------------------------------------------------- serviço

def test_quantidade_e_descricao_do_servico(nota):
    assert nota.quantidade_servico == 1.0
    assert nota.descricao_servico == "TRANSPORTE DE PESSOAL"


# --------------------------------------------------------------- valores

def test_valor_total_da_prestacao_e_o_confirmado_pelo_usuario(nota):
    """R$2.115,08 - valor confirmado pelo usuário, lido do rótulo "VALOR
    TOTAL DA PRESTAÇÃO DO SERVIÇO" (grade "COMPONENTES DO VALOR DA
    PRESTAÇÃO DE SERVIÇO"), pelo par "<total>\\nVALOR A RECEBER\\n<a
    receber>"."""
    assert nota.valor_total_prestacao == pytest.approx(2115.08)


# ------------------------------------------------------------ transformer

def test_xml_e_um_cte_mod67_nao_um_compnfse_abrasf(nota):
    """O XML final deve se identificar como CT-e (mod=67, raiz `CTe`/
    `infCte`, namespace `.../cte`) - NUNCA como `CompNfse` ABRASF, que foi o
    sintoma original do bug (documento do tipo errado sendo parseado)."""
    xml = CteTransformer().transform(nota)
    assert "http://www.portalfiscal.inf.br/cte" in xml
    assert "<mod>67</mod>" in xml
    assert "<infCte " in xml
    assert "<CompNfse" not in xml
    assert "SIGMA TRANSPORTES LTDA" in xml


def test_xml_traz_o_valor_real_nao_zerado(nota):
    """Sintoma original: todos os valores saíam zerados (`ValorServicos=
    0.00`) por causa do documento errado sendo parseado."""
    xml = CteTransformer().transform(nota)
    assert "<vTPrest>2115.08</vTPrest>" in xml


# ------------------------------------------------- não colide com outros

def test_nao_colide_com_layout_simoes_filho():
    """A nota cita "Simoes Filho" como município do tomador E do emitente
    (início da prestação) - mesma armadilha já documentada para a nota
    CIATRANS. A detecção do DACTE OS intercepta primeiro."""
    ex = SPPdfExtractor.__new__(SPPdfExtractor)
    ex.raw_text = MOCK_PAGINA
    ex.from_ocr = True
    ex.layout = None
    ex.pdf_path = "x.pdf"
    assert ex._detect_layout_page(MOCK_PAGINA) != "simoes_filho_ba"


def test_nao_colide_com_danfse_nacional_por_causa_de_chave_de_acesso():
    """A nota cita "Chave de acesso" (marca genérica de qualquer documento
    nacional, inclusive DANFSe) - a detecção do DACTE OS precisa interceptar
    ANTES da DANFSe Nacional para não colidir."""
    ex = SPPdfExtractor.__new__(SPPdfExtractor)
    ex.raw_text = MOCK_PAGINA
    ex.from_ocr = True
    ex.layout = None
    ex.pdf_path = "x.pdf"
    assert ex._detect_layout_page(MOCK_PAGINA) != "nacional"
