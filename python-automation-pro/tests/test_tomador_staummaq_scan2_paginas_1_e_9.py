# -*- coding: utf-8 -*-
r"""Tomador da Staummaq nas paginas 1 e 9 do lote "STAUMMAQ - SCAN 2.pdf".

Pedido do usuario (2026-09-14): "corrigir a extracao correta do tomador do
servico, que em ambos os casos, e a Staummaq Servicos. O problema encontra-se
somente nas paginas 1 e 9. Focar somente nesse problema."

CAUSA-RAIZ UNICA PARA AS DUAS PAGINAS, e ela nao esta na extracao e sim na
DETECCAO: `_detect_layout`/`_detect_layout_page` terminam com um fallback
solto `if re.search(r'Sim[oo]es Filho', t)` -> `LAYOUT_SIMOES_FILHO`. A
Staummaq, TOMADORA de todas as notas destes lotes, fica em Simoes Filho/BA —
entao o nome da cidade aparece em QUALQUER nota desses lotes, vinda de
qualquer emitente. As paginas 2 a 8 escapam porque casam antes o marcador do
Camacari/CPqD; as paginas 1 e 9 nao casam marcador nenhum e caem nesse
fallback, indo parar num layout municipal cujos rotulos elas nao tem — dai
"Tomador Nao Identificado" com CNPJ sentinela.

E o retrato da familia ja registrada no projeto: **deteccao por uma marca que
pertence a CONTRAPARTE, nao ao emitente**. Nenhuma das duas paginas e de
Simoes Filho:

  - pagina 1: "NOTA FISCAL FATURA DE SERVICOS" da SEM PARAR INSTITUICAO DE
    PAGAMENTOS LTDA (CNPJ 04.088.208/0001-65, Pinheiros/Sao Paulo-SP) — uma
    fatura de tag veicular/pedagio, que so cita "Cidade/UF: Simoes Filho - BA"
    porque esse e o endereco do CLIENTE;
  - pagina 9: NFS-e de Camacari/BA emitida pela plataforma GestaoClick — a
    TERCEIRA plataforma do municipio, ao lado do CPqD e do SISLOC/Benefix. Seu
    cabecalho e "PREFEITURA DE CAMACARI", SEM o "MUNICIPAL" que o marcador do
    CPqD exige, entao ela nao casa nem o proprio municipio.

CORRECAO, em duas frentes:

  (a) as duas plataformas passam a ser reconhecidas pelo marcador do EMITENTE,
      registradas ANTES do fallback solto — `gestaoclick` (marca exclusiva da
      plataforma, no rodape) e o CNPJ RAIZ `04.088.208` (convencao ja usada em
      toda a familia de faturas, casa qualquer filial);
  (b) o proprio fallback foi APERTADO: alem do nome da cidade passou a exigir
      um marcador ESTRUTURAL do template de Simoes Filho (Serie/Numero RPS,
      exigibilidade do ISS, servico nacional, desconto incondicional). Sem a
      segunda condicao, o proximo emitente novo cujo cliente seja a Staummaq
      cairia na mesma armadilha. A rede de seguranca continua de pe para as
      notas cujo cabecalho da prefeitura nao sobreviveu ao OCR — e' o que os
      testes de deteccao no fim deste arquivo fixam.

Varredura de seguranca do aperto: os dois detectores foram rodados sobre os
134 textos de nota reais ja versionados na suite; 8 citam "Simoes Filho" e
NENHUM alem destas duas paginas muda de layout.

ESCOPO: a primeira entrega corrigiu so' o TOMADOR; numa segunda passada, a
pedido do usuario, entraram tambem o PRESTADOR das duas paginas, os VALORES
e o aperto (b). Fica de fora, por decisao explicita dele, corrigir a razao
social que a fatura Sem Parar imprime com erro do proprio emitente
("Stammaq ... Automocao") — ela sai como o documento a imprime.
"""
import pytest

from src.extractors.pdf_extractor import SPPdfExtractor

# Texto REAL do Tesseract, verbatim (as duas paginas estao de cabeca para
# baixo no PDF; o que aparece aqui e a leitura ja corrigida por `_ocr_page`).
MOCK_P1 = """\
Av ra, Cain E2 nara AEAMENTO LTDA. NOTA FISCAL FATURA DE SERVIÇOS
05425-902 - Pinheiros - São Paulo/SP Nº DA FATURA: 26176766483

CNPJ/MF: 04.088.208/0001-65 - Insc. Municipal nº 6.486.165-1

Central de Relacionamento Página 1/5
4002 1552 (Capitais e regiões metropolitanas)
0800 015 02 52 (Demais Localidades)

EMPRESAS

Nome: Stammag Servicos Tecnicos Automocao Motores E Maq
CNPJ: 02.370.080/0001-00

Endereço: Via Urbana, 1
Bairro: Companhia Sul

CEP: 43700-000

Cidade/UF: Simoes Filho - BA

Nº da Fatura: 261 76766483

Nº da Nota Fiscal: 705320619
Código do Cliente: 2876948
E-Mail; sbrunoQstaummaq.com.br
CPF/CNPJ: 02.370.080/0001-00
Banco/Agência: 001/1223

Data de Emissão: 08/08/26

Data de Fechamento: 08/08/26
Débito em conta corrente

Banco Do Brasil

Agência: 1223

Data de Vencimento: 15/08/26
Prev. próx. Faturamento: 08/09/26

PAGUE AGORA.
É RÁPIDO, SEGURO E EM ATÉ 2X.

MANTENHA O IPVA DA SUA FROTA EM DIA,
SEM PARAR ENPRESAS SEM PARAR À OPERAÇÃO.

, Reu Qtd Estabelecimento td
NTUB674 0748423730 0 0,00 o 0,00 o
over” des a oO Do o ooo io 2000 0
PKJ3F66 | 0736905078 o 5370D  49280D 64 (o) 0,00 0 0,00 0
PkJ7438 0730451186. o 69,700 16800D 21. (o) 0,00 (o) 0,00 (o)
PKW7748 | 0731204546 S970D | 231,70D 29 0,00 o 0 0,00 º
PLH2J86 0755871861 61800 oo o 0,00 o o 0,00 o
RDR1H54 0740503362 6270D. 23 0,00 0 0 0,00 0
SKLOBBS 0745086120 sab a “49,00D 3 o) 000 O 1403460
o Subtotal R$ 3.817,56 D
' Impostosretidos OutrasArrec. Qtd OutrosServ. Qtd Demaisitensvp Qtd
0,00 2730D 7 0,00 0 0,00 0
Descritivo de Valores Cobrados ao Titular da Fatura
x Detalhamento de Plano Contratado
ad O * Período di * Descrição É Valor(R$)
NTUB674 PLANO CONTRATADO 01/08/2026 a 31/08/2026 ADESÃO ZERO EMPRESARIAL - SKL SPE 65,90 D
E E : 01/08/2026 a 31/08/2026 MONITORAMENTO DÉBITO VEICULAR 7,90 D
01/08/2026 a 31/08/2026 PARCERIA SERVIÇOS DE SAUDE 7,90D
OvB3F97 PLANO CONTRATADO 01/08/2026 a 31/08/2026 MONITORAMENTO DÉBITO VEICULAR 790D
01/08/2026 a 31/08/2026 PARCERIA SERVIÇOS DE SAUDE 7,90D
: 01/08/2026 a 31/08/2026 ADESÃO ZERO EMPRESARIAL - SKL SPE 6590D
PKJ3F66, PLANO CONTRATADO 01/08/2026 a 31/08/2026 MONITORAMENTO DÉBITO VEICULAR 7,90D
O : : 01/08/2026 a 31/08/2026 PARCERIA SERVIÇOS DE SAUDE 7,90D
01/08/2026 a 31/08/2026 EMPRESARIAL RODOVIAS SKL 2023 SPE 37,90 D
- PkoTa3s PLANO CONTRATADO 01/08/2026 à 31/08/2026 ADESÃO ZERO EMPRESARIAL -SKLSPE | 53,900
01/08/2026 a 31/08/2026 MONITORAMENTO DÉBITO VEICULAR 7,90D
01/08/2026 a 31/08/2026 PARCERIA SERVIÇOS DE SAUDE 7,90D

Cuidado com os golpes e fraudes! Contar com nossos canais digitais é a Forma mais Fácil de garantir sua segurança! Por isso, em caso de necessidade de um novo boleto, utilize
exclusivamente: portal Sem Parar Empresas e Portal de Negociação! . E .
Ao efetuar o pagamento de um boleto Sem Parar, confira se o beneficiário é SEM PARAR INSTITUIÇÃO DE PAGAMENTOS LTDA, com o CNPJ 04,088.208/0001-65. Atenção: Jamais
compartilhe suas senhas com terceiros.”

Central de Relacionamento SAC 0800 7232245 |
4002 1552 (Capitais e regiões metropolitanas) SAC (Deficiência auditiva ou de fala) 0800 722 0270
0800 015 02 52 (Demais localidades) Ouvidoria 0800 770 0686

Bv69/8Z
"""

MOCK_P9 = """\
Número da nota
2127
PREFEITURA DE CAMAÇARI Data e Hora da Emissão

NFS-E - NOTA FISCAL DE SERVIÇOS ELETRÔNICA 24/07/2026 14:15
Nota Nº 2127 Série 0, emitido em 24/07/2026

Código de Verificação
2Y495814N

PRESTADOR DE SERVIÇOS

Nome: SNB SOLUCAO EM INVERSORES DE FREQUENCIA E ELETRONICA INDUSTR
DV CNPJ: 14.377.249/0001-25 Inscrição Municipal: 0025726001

Á Endereço: Rua Arembepe, 488 (sala 101) - Bela Vista - 42809-326

soruções eminversores Município: Camaçari UF: BA

TOMADOR DE SERVIÇOS
Razão Social: STAUMMAQ SERVICOS TECNICOS AUTOMACAO MOTORES E MAQUINAS LTDA o
CNPJ: 02.370.080/0001-00 5 ra $)
Endereço: VIA URBANA, 01 (CIA-SUL) - SIMOES FILHO - 43700-000 al if e di ( I
Município: Simões Filho UF: BA E-mail:

DISCRIMINAÇÃO DOS SERVIÇOS

INVERSOR DE FREQUÊNCIA WEG CFW500 380/480V 6,1A /
NÚMERO DO ORÇAMENTO : 5214 PEDIDO: 008104
PAGAMENTO VIA BOLETO BANCÁRIO

VENCIMENTO: 14/08/2026

CÓDIGO DO SERVIÇO
1401 / MANUTENÇÃO E REPARAÇÃO DE APARELHOS E INSTRUMENTOS DE MEDIDA, TESTE E CONTROLE

COD/MUNICÍPIO DA INCIDÊNCIA DO ISSQN: NATUREZA DA OPERAÇÃO:
2905701 / CAMAÇARI (BA) TRIBUTAÇÃO NO MUNICÍPIO

DEDUÇÕES DESCONTOS B. CÁLCULO E) ISS RETIDO COFINS
R$ 0,00 R$ 0,00 R$ 2.500,00 R$ 113,00 (4,5200 %) NÃO R$ 0,00

PIS CSLL IR INSS VALOR DOS SERVIÇOS
R$ 0,00 R$ 0,00 R$ 0,00 R$ 0,00 R$ 2.500,00

VALOR LÍQUIDO DA NOTA: R$ 2.500,00
OUTRAS IN FORMAÇÕES Texto de responsabilidade do emitente

EMPRESA OPTANTE PELO SIMPLES NACIONAL.

Recebi(emos) do Prestador: SNB SOLUCAO EM INVERSORES DE FREQUENCIA E ELETRONICA INDUSTR CNPJ:
14.377.249/0001-25
Os serviços constantes da Nota Fiscal de Serviços Eletrônica n.º 2127 emitida em 24/07/2026 às 14:15

Ass: em
Assinatura do Destinatário/Tomador dos Serviços

; n Nota fiscal emitida no GestãoClick — www.gestaoclick. com.br
0 JH CNO END

"""


def _parse(monkeypatch, tmp_path, mock, nome_arquivo):
    """Roda o extrator sobre UMA pagina do lote, como `parse_multiple` faz."""
    caminho = tmp_path / nome_arquivo
    caminho.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: mock)

    extractor = SPPdfExtractor(str(caminho))
    notas = extractor.parse_multiple()
    assert len(notas) == 1
    return notas[0]


@pytest.fixture
def nota_p1(monkeypatch, tmp_path):
    return _parse(monkeypatch, tmp_path, MOCK_P1, "sem parar - fatura.pdf")


@pytest.fixture
def nota_p9(monkeypatch, tmp_path):
    return _parse(monkeypatch, tmp_path, MOCK_P9, "gestaoclick - nota.pdf")


CNPJ_STAUMMAQ = "02370080000100"
IBGE_SIMOES_FILHO = "2930709"


# ------------------------------------------------------- deteccao (causa-raiz)

def test_pagina_1_nao_e_mais_lida_como_nota_de_simoes_filho(monkeypatch, tmp_path):
    """A fatura Sem Parar e de Sao Paulo/SP; so citava Simoes Filho porque e a
    cidade do CLIENTE. Roteada pelo CNPJ RAIZ do emitente."""
    ex = SPPdfExtractor.__new__(SPPdfExtractor)
    ex.raw_text = MOCK_P1
    ex.from_ocr = True
    ex.layout = None
    ex.pdf_path = "x.pdf"
    assert ex._detect_layout_page(MOCK_P1) == "sem_parar_fatura"


def test_pagina_9_nao_e_mais_lida_como_nota_de_simoes_filho(monkeypatch, tmp_path):
    """A NFS-e da pagina 9 e de Camacari, plataforma GestaoClick."""
    ex = SPPdfExtractor.__new__(SPPdfExtractor)
    ex.raw_text = MOCK_P9
    ex.from_ocr = True
    ex.layout = None
    ex.pdf_path = "x.pdf"
    assert ex._detect_layout_page(MOCK_P9) == "camacari_gestaoclick"


def test_o_nome_da_cidade_da_contraparte_esta_mesmo_nas_duas_paginas():
    """Ancora a causa-raiz: o texto das duas paginas CONTEM "Simoes Filho" —
    era so isso que bastava para desviar as duas. Se um dia sumir, os dois
    testes de deteccao acima passariam por motivo errado."""
    assert "Simoes Filho" in MOCK_P1
    assert "Simões Filho" in MOCK_P9


def test_camacari_gestaoclick_nao_exige_o_marcador_do_cpqd():
    """O cabecalho desta plataforma e "PREFEITURA DE CAMACARI" — sem o
    "MUNICIPAL" que o marcador do Camacari/CPqD exige. E por isso que a
    deteccao tem de ser pela marca da PLATAFORMA, e nao pelo municipio."""
    assert "PREFEITURA DE CAMAÇARI" in MOCK_P9
    assert "PREFEITURA MUNICIPAL DE CAMAÇARI" not in MOCK_P9
    assert "gestaoclick" in MOCK_P9.lower()


# ---------------------------------------------------- tomador: pagina 1

def test_p1_tomador_deixa_de_ser_nao_identificado(nota_p1):
    """O sintoma relatado: antes da correcao as duas paginas devolviam
    "Tomador Nao Identificado" com CNPJ sentinela."""
    assert nota_p1.tomador.razao_social != "Tomador Não Identificado"
    assert nota_p1.tomador.cnpj_cpf != "00000000000000"


def test_p1_tomador_e_a_staummaq_pelo_cnpj(nota_p1):
    """O CNPJ e a identificacao confiavel do tomador — passa no checksum e e o
    mesmo das outras sete paginas do lote."""
    assert nota_p1.tomador.cnpj_cpf == CNPJ_STAUMMAQ


def test_p1_tomador_endereco_completo(nota_p1):
    end = nota_p1.tomador.endereco
    assert end.logradouro == "Via Urbana"
    assert end.numero == "1"
    assert end.bairro == "Companhia Sul"
    assert end.cep == "43700000"
    assert end.codigo_municipio == IBGE_SIMOES_FILHO


def test_p1_razao_social_sai_como_o_documento_imprime(nota_p1):
    """LIMITACAO REGISTRADA, nao escondida: a fatura Sem Parar imprime o nome
    do cliente com erro DO PROPRIO EMITENTE — "Stammaq ... Automocao", nao
    "Staummaq ... Automacao" (conferido no pixel, recorte a 300 dpi). O OCR
    ainda troca o "q" final por "g". O extrator entrega o que esta escrito; a
    identificacao confiavel e o CNPJ, testado acima. Corrigir o nome pelo CNPJ
    seria uma substituicao de contraparte conhecida — decisao do usuario,
    ainda nao pedida."""
    assert nota_p1.tomador.razao_social.lower().startswith("stamma")
    assert "Servicos Tecnicos" in nota_p1.tomador.razao_social


# ---------------------------------------------------- tomador: pagina 9

def test_p9_tomador_deixa_de_ser_nao_identificado(nota_p9):
    assert nota_p9.tomador.razao_social != "Tomador Não Identificado"
    assert nota_p9.tomador.cnpj_cpf != "00000000000000"


def test_p9_tomador_e_a_staummaq_com_razao_social_completa(nota_p9):
    """Aqui o OCR le o nome legal inteiro — so acrescenta um "o" solto no fim
    da linha, que o corte de ruido remove."""
    assert nota_p9.tomador.cnpj_cpf == CNPJ_STAUMMAQ
    assert nota_p9.tomador.razao_social == (
        "STAUMMAQ SERVICOS TECNICOS AUTOMACAO MOTORES E MAQUINAS LTDA")


def test_p9_razao_social_nao_carrega_a_letra_solta_do_ocr(nota_p9):
    """Regressao exata: a linha lida termina em "...MAQUINAS LTDA o"."""
    assert "LTDA o" in MOCK_P9
    assert not nota_p9.tomador.razao_social.endswith(" o")


def test_p9_endereco_de_uma_linha_so_e_desmontado(nota_p9):
    """O GestaoClick imprime o endereco inteiro numa linha:
    "VIA URBANA, 01 (CIA-SUL) - SIMOES FILHO - 43700-000", com ruido de OCR
    colado no fim ("al if e di ( I") que nao pode vazar para nenhum campo."""
    end = nota_p9.tomador.endereco
    assert end.logradouro == "VIA URBANA"
    assert end.numero == "01"
    assert end.bairro == "CIA-SUL"
    assert end.cep == "43700000"
    for campo in (end.logradouro, end.numero, end.bairro, end.cep):
        assert "al if" not in campo


def test_p9_municipio_vem_do_rotulo_proprio_e_nao_do_endereco(nota_p9):
    """A linha de endereco traz "SIMOES FILHO" sem acento e grudado no CEP; o
    rotulo "Municipio: Simoes Filho UF: BA" e a fonte mais firme."""
    end = nota_p9.tomador.endereco
    assert end.codigo_municipio == IBGE_SIMOES_FILHO
    assert end.uf == "BA"


# ------------------------------------------------- prestador (item 2)

def test_p1_prestador_e_a_sem_parar(nota_p1):
    """O emitente da fatura, que antes saia no sentinela. Razao social, CNPJ
    (com checksum), inscricao municipal, bairro, CEP e municipio saem todos do
    texto de pagina; so' o logradouro depende do recorte dedicado (abaixo)."""
    p = nota_p1.prestador
    assert p.cnpj_cpf == "04088208000165"
    assert p.razao_social.startswith("SEM PARAR INSTITUI")
    assert p.inscricao_municipal == "6.486.165-1"
    assert p.endereco.bairro == "Pinheiros"
    assert p.endereco.cep == "05425902"
    assert p.endereco.codigo_municipio == "3550308"   # Sao Paulo/SP
    assert p.endereco.uf == "SP"


def test_p1_razao_social_do_prestador_vem_do_proprio_documento(nota_p1):
    """Sem o recorte (caso deste teste, que usa um PDF dummy) a razao social
    cai na RESERVA, que tambem esta no documento: a frase antifraude do rodape
    ("...o beneficiario e SEM PARAR ..., com o CNPJ ..."). Com o PDF real o
    recorte le o cabecalho e vence essa reserva."""
    assert "o beneficiário é SEM PARAR" in MOCK_P1
    assert nota_p1.prestador.razao_social != "Prestador Não Identificado"


def test_p1_logradouro_do_prestador_depende_do_recorte(nota_p1):
    """LIMITACAO CONHECIDA, registrada: as duas primeiras linhas do cabecalho
    saem ilegiveis no OCR de pagina inteira — na nota real o logradouro
    "Av. Dra. Ruth Cardoso, 7221, Andares 17, 18, 19 e 26 parte" virou
    "Av ra, Cain E2 nara AEAMENTO LTDA.". Quem o recupera e
    `_ocr_cabecalho_sem_parar`, que precisa do PDF real; aqui, com um PDF
    dummy, ele devolve "" e o campo fica honestamente "Nao informado" em vez
    de receber o lixo da linha fundida."""
    assert "Av ra, Cain E2 nara" in MOCK_P1          # a linha ilegivel existe
    assert nota_p1.prestador.endereco.logradouro == "Não informado"
    assert "AEAMENTO" not in nota_p1.prestador.endereco.logradouro


def test_p9_prestador_e_a_snb(nota_p9):
    p = nota_p9.prestador
    assert p.cnpj_cpf == "14377249000125"
    assert p.razao_social.startswith("SNB SOLUCAO EM INVERSORES")
    assert p.inscricao_municipal == "0025726001"
    assert p.endereco.codigo_municipio == "2905701"   # Camacari/BA


def test_p9_o_parentese_do_endereco_muda_de_significado_entre_as_entidades(nota_p9):
    """A armadilha deste template: a MESMA forma de endereco de uma linha so'
    ("<via>, <n> (<X>) - <Y> - <CEP>") quer dizer coisas DIFERENTES nas duas
    entidades da mesma nota —

        VIA URBANA, 01 (CIA-SUL) - SIMOES FILHO - 43700-000    (tomador)
        Rua Arembepe, 488 (sala 101) - Bela Vista - 42809-326  (prestador)

    No tomador o parentese e o BAIRRO e o campo seguinte e o MUNICIPIO; no
    prestador o parentese e o COMPLEMENTO e o campo seguinte e o BAIRRO. Ler
    por posicao poria "sala 101" como bairro do prestador e "Bela Vista" como
    municipio. O desempate e o rotulo "Municipio:" do proprio bloco."""
    p, tom = nota_p9.prestador, nota_p9.tomador
    assert p.endereco.complemento == "sala 101"
    assert p.endereco.bairro == "Bela Vista"
    assert p.endereco.municipio.upper().startswith("CAMA")
    assert tom.endereco.bairro == "CIA-SUL"
    assert tom.endereco.codigo_municipio == IBGE_SIMOES_FILHO


# --------------------------------------------------- valores (item 3)

def test_p9_grade_de_valores_completa(nota_p9):
    """A nota traz grade limpa: DEDUCOES/DESCONTOS/B.CALCULO/ISS/ISS RETIDO/
    COFINS e PIS/CSLL/IR/INSS/VALOR DOS SERVICOS."""
    v = nota_p9.valores
    assert v.valor_servicos == pytest.approx(2500.00)
    assert v.base_calculo == pytest.approx(2500.00)
    assert v.valor_iss == pytest.approx(113.00)
    assert v.aliquota == pytest.approx(0.0452)
    assert v.valor_liquido_nfse == pytest.approx(2500.00)
    assert v.iss_retido is False


def test_p9_identidade_contabil_fecha(nota_p9):
    """Conferencia independente do que foi lido: base x aliquota tem de dar o
    ISS impresso. 2.500,00 x 4,52% = 113,00."""
    v = nota_p9.valores
    assert v.base_calculo * v.aliquota == pytest.approx(v.valor_iss, abs=0.01)


def test_p9_o_rotulo_do_iss_nao_sobrevive_ao_ocr(nota_p9):
    """Por que a grade NAO e lida por posicao de coluna: o rotulo "ISS" saiu
    do OCR como "E)" (conferido no pixel que e mesmo ISS). O valor e ancorado
    no percentual entre parenteses, que e' proprio dele."""
    assert "B. CÁLCULO E) ISS RETIDO" in MOCK_P9
    assert nota_p9.valores.valor_iss == pytest.approx(113.00)


def test_p9_nao_herda_o_iss_fabricado_do_extrator_generico(nota_p9):
    """Guarda contra uma regressao MEDIDA durante a investigacao: sob o
    extrator generico esta pagina produzia `valor_iss = 2905701.00` — o codigo
    IBGE do municipio ("COD/MUNICIPIO DA INCIDENCIA DO ISSQN: 2905701") lido
    como se fosse dinheiro."""
    assert nota_p9.valores.valor_iss != 2905701.0
    assert "2905701" in MOCK_P9


def test_p1_valor_e_composto_das_rubricas_impressas(nota_p1):
    """A fatura nao imprime "valor dos servicos": imprime um Subtotal das
    linhas de uso das tags e uma rubrica "Outras Arrec.", fechando num TOTAL
    que o OCR NAO recupera (fica sobre faixa cinza; conferido no pixel:
    R$ 3.844,86). O valor entregue e a soma das duas rubricas que a nota
    declara — 3.817,56 + 27,30 — e bate exatamente com o TOTAL impresso."""
    v = nota_p1.valores
    assert v.valor_servicos == pytest.approx(3844.86)
    assert v.valor_liquido_nfse == pytest.approx(3844.86)
    assert "3.817,56" in MOCK_P1      # Subtotal, impresso
    assert "2730D" in MOCK_P1         # Outras Arrec., impresso (27,30 D)
    assert "3.844,86" not in MOCK_P1  # o TOTAL, esse o OCR perde


def test_p1_tributacao_fica_zerada_e_avisada(nota_p1):
    """A fatura nao imprime base, aliquota nem ISS em lugar nenhum — deriva-los
    do total seria inventar a tributacao."""
    v = nota_p1.valores
    assert v.base_calculo == 0.0
    assert v.aliquota == 0.0
    assert v.valor_iss == 0.0
    assert any("ZERADOS propositalmente" in a for a in nota_p1.avisos)
    assert any("COMPOSTO" in a for a in nota_p1.avisos)


def test_p1_avisa_que_so_uma_das_cinco_paginas_esta_no_pdf(nota_p1):
    """A fatura se declara "Pagina 1/5" e as demais nao estao no PDF do
    usuario; retencoes, se houver, moram nelas."""
    assert "Página 1/5" in MOCK_P1
    assert any("página 1 de 5" in a for a in nota_p1.avisos)


# ------------------------------- regra apertada de Simoes Filho (item 4)

# Template do Simoes Filho SEM a linha "Data Fato Gerador": esse rotulo e' o
# marcador do BARREIRAS, checado ANTES (as duas prefeituras usam a mesma
# plataforma; a precedencia ja esta documentada no detector). A rede de
# seguranca que estes testes exercitam so' alcanca as notas que nao casam
# Barreiras primeiro.
TEMPLATE_SIMOES = (
    "PREFEITURA MUNICIPAL DE SIMÕES FILHO\n"
    "NOTA FISCAL DE SERVIÇOS ELETRÔNICA - NFSe\n"
    "Exigibilidade de 155 Regime Tributário Numero RPS Serie RPS\n"
    "Razão Social: FORNECEDOR EXEMPLO LTDA\n"
    "Simões Filho - BA - CEP: 43700-000\n"
    "SERVIÇO NACIONAL\n"
    "VALOR SERVIÇO (R$) DEDUÇÕES (R$) DESCONTO INCONDICIONAL (R$)\n"
)


def _layout_de(texto):
    ex = SPPdfExtractor.__new__(SPPdfExtractor)
    ex.raw_text = texto
    ex.from_ocr = True
    ex.layout = None
    ex.pdf_path = "x.pdf"
    return ex._detect_layout_page(texto)


def test_nota_verdadeira_de_simoes_filho_continua_no_layout_dela():
    """O aperto nao pode fechar a rede de seguranca: uma nota cujo cabecalho
    da prefeitura tenha morrido no OCR ainda cai aqui, porque os marcadores
    ESTRUTURAIS do template (RPS, exigibilidade do ISS, servico nacional,
    desconto incondicional) sobrevivem."""
    sem_cabecalho = TEMPLATE_SIMOES.replace("PREFEITURA MUNICIPAL DE SIMÕES FILHO\n", "")
    assert "Simões Filho" in sem_cabecalho
    assert _layout_de(sem_cabecalho) == "simoes_filho_ba"


def test_so_o_nome_da_cidade_nao_basta_mais():
    """O defeito exato: um documento de outro emitente que apenas MENCIONA a
    cidade — porque e o endereco da contraparte — nao pode mais ser
    sequestrado para o layout municipal."""
    alheio = ("FATURA DE PRESTACAO DE SERVICOS\n"
              "Cliente: EMPRESA EXEMPLO LTDA\n"
              "Cidade/UF: Simoes Filho - BA\n")
    assert _layout_de(alheio) != "simoes_filho_ba"


@pytest.mark.parametrize("marcador", [
    "Serie RPS", "Numero RPS", "Exigibilidade de ISS",
    "Exigibilidade de 155", "SERVIÇO NACIONAL", "DESCONTO INCONDICIONAL",
])
def test_cada_marcador_estrutural_sozinho_sustenta_a_rede(marcador):
    """Cada ancora vale por si — inclusive o garble real "Exigibilidade de
    155" ("ISS" lido como "155")."""
    texto = "Simões Filho - BA - CEP: 43700-000\n%s\n" % marcador
    assert _layout_de(texto) == "simoes_filho_ba"


# ------------------------------------------------- escopo que segue de fora

@pytest.mark.parametrize("fixture", ["nota_p1", "nota_p9"])
def test_sem_intermediario_fantasma(fixture, request):
    """Nenhum dos dois documentos tem intermediario; o bloco nao pode ser
    preenchido com uma segunda copia do tomador."""
    nota = request.getfixturevalue(fixture)
    assert nota.intermediario is None
