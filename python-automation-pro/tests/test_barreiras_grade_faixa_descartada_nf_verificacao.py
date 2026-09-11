# -*- coding: utf-8 -*-
"""NFS-e de Barreiras/BA ESCANEADAS — lote real "NF VERIFICACAO" 08/2026, 6
notas, TODAS saindo com valor 0,00. Reportado pelo usuário a partir da nota da
pág. 3 (nº 4059, BETINA SANTROVITSCH POSSATO / OBRAMAX LOCACAO -> SÃO PEDRO
CONSTRUTORA, R$480,00): "extrair o valor correto da nota fiscal".

CAUSA-RAIZ DOS VALORES: a segmentação automática do Tesseract DESCARTA UMA
FAIXA HORIZONTAL INTEIRA de cada página — a faixa com o texto da discriminação,
a OBSERVAÇÃO, a GRADE PRINCIPAL DE VALORES, o VALOR LÍQUIDO e, em parte das
notas, a linha "Chave de acesso". O texto da pág. 3 pula direto de
"DISCRIMINAÇÃO DOS SERVIÇOS" para "DEMONSTRATIVO DOS TRIBUTOS FEDERAIS": não
existe nenhum "480" nem "VALOR SERVIÇO" ali, e `_extrair_valores` cai no
fallback ZERO.

É a mesma família das notas 201/160 de Camaçari, numa variante que o portão
existente NÃO cobria: lá a página falhava por COMPLETO (`score_angle_0 == 0`) e
o fallback de PSM 6 disparava; aqui o resto da página lê bem, a pontuação é
alta, e a perda é PARCIAL. Corrigido com um re-OCR de página inteira em zoom 5
+ PSM 6 (`_ocr_valores_barreiras`), do qual só a FATIA da grade é costurada de
volta no corpo da nota.

CAUSA-RAIZ DOS 4 COLATERAIS: `_detect_layout` (documento) aceitava só o rótulo
"Data Fato Gerador" como marca de Barreiras, enquanto `_detect_layout_page` já
aceitava também "MUNICIPIO DE BARREIRAS". Esse rótulo sobrevive ao OCR em
apenas 2 das 6 notas — nas outras 4, sem nenhuma marca municipal casando, a
nota caía no check LARGO de DANFSe Nacional ("Chave de Acesso"), porque o
portal de Barreiras é integrado ao ambiente nacional e imprime "Chave de acesso
Ambiente de Dados Nacional". Detectadas como Portal Nacional, essas 4 notas
recebiam o `<CodigoVerificacao>` da chave de 50 dígitos (comportamento do
LAYOUT_NACIONAL) enquanto as outras 2 recebiam o código curto — a
inconsistência que o usuário reportou — e o `<Numero>`, o município e os
valores todos saíam pelo caminho do layout errado.

Verdade estabelecida para as 6 notas do lote, conferida na imagem em zoom
9x-14x (número também conferido contra a decodificação da chave):

    pág | nº   | serviços  | alíquota | ISS    | Data Fato Gerador
      1 | 4060 |  1.500,00 |   0,00 % |   0,00 | 10/08/2026
      2 | 8809 |  1.874,40 |   0,00 % |   0,00 | 05/08/2026
      3 | 4059 |    480,00 |   3,33 % |  15,98 | 10/08/2026
      4 |  882 |  6.000,00 |   3,31 % | 198,60 | 06/08/2026
      5 |  883 |  2.600,00 |   3,31 % |  86,06 | 06/08/2026
      6 |  892 |    420,00 |   4,11 % |  17,26 | 11/08/2026

Os 3 textos embutidos aqui são o OCR REAL das páginas 1, 3 e 6, já com a fatia
da grade costurada como `_ocr_page` faz em produção, e cobrem os casos
distintos do lote:

- **pág. 3**: a nota reportada. Grade recuperada, ISS devido, e a linha "Chave
  de acesso" TAMBÉM caiu na faixa descartada (só o recut a traz).
- **pág. 6**: a alíquota sai TRUNCADA pelo OCR ("4" onde a nota imprime
  "4.11"), sobrando 5 números na linha em vez de 6.
- **pág. 1**: ISS legitimamente ZERO (nota do Simples — confirmado na imagem,
  a nota imprime "0.00" e "0,00" nas duas colunas), o cabeçalho de seção
  "TOMADOR" foi comido inteiro pelo OCR, e a linha de cidade do tomador saiu
  partida ("LAURO DE FREITAS -" / "E-mail:" / "BA-CEP: 42708720").

NOTA SOBRE O PDF DE ORIGEM: o arquivo saiu da pasta de rede durante o próprio
trabalho, então a verificação ponta a ponta contra o PDF não pôde ser repetida
depois disso — estes textos são o OCR real capturado antes, e é contra eles que
a extração é travada aqui."""
import os

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_BARREIRAS


MOCK_PAG1 = (
    'NOTA FISCAL DE SERVIÇOS ELETRÔNICA - NF So\n'
    'MUNICIPIO DE BARREIRAS\n'
    '\n'
    'Codigo de Verificação para Autenticação: 565734070\n'
    '\n'
    'Endereço: Barreiras, Baia, BA, 47800-300 [=]; ag?\n'
    'CNPJ 13.654.405/0001-05, E-mail memecadacaa tributosfDbarmeiras ba gos br Emitido em (omarxios 151739\n'
    '\n'
    'Regime Tributário AP Nº da Nota Fiscal\n'
    'Tributscão Normal\n'
    '\n'
    'Tocai do Recolhimento 4060\n'
    '2003201 - Barreiras - BA\n'
    '\n'
    'PRESTADOR\n'
    '\n'
    'Razão Social: BETINA SANTROVITSCH POSSATO LTDA\n'
    'Nome Fantasia: OBRAMAX LOCACAO E SERVICOS\n'
    '\n'
    '-BA- : 4781\n'
    'E ENS OCOGMAIL COM - Fone: (77)3611-8445 - Celular: (77)99835-4201 - Site:\n'
    'Inscrição Estadual: ........ - Inscrição Municipal: 2212 - CPF/CNPJ: 00.999.093/0001-00\n'
    '\n'
    'Razão Social: SAO PEDRO CONSTRUTORA LTDA\n'
    '\n'
    'te 2d ta dd EL\n'
    'LAURO DE FREITAS -\n'
    '\n'
    'E-mail:\n'
    '\n'
    'BA-CEP: 42708720\n'
    ': splDsaopedroconstrutora.com.br - Fone: (71) 3272-0733 - Celular:\n'
    'Inscrição Estadual: ........ - Inscrição Municipal: 353043 - CPF/CNPJ: 03.051.741/0001-90\n'
    'SERVIÇO NACIONAL\n'
    '\n'
    '00.00 - LOCAÇÃO DE BENS MÓVEIS\n'
    'DISCRIMINAÇÃO DOS SERVIÇOS\n'
    '\n'
    'OBSERVAÇÃO\n'
    '\n'
    'OUTRAS INFORMAÇÕES\n'
    'Chave de acesso Ambiente de Dados Nacional: 29032011200999093000100260000000406026080008401503\n'
    '(Valor Líquido = Valor Serviço - INSS - IR - CSLL - Outras Retenções - COFINS - PIS - Descontos Diversos - ISS Retido - Desconto Incondicional)\n'
    '\n'
    'ESTE DOCUMENTO FOI EMITIDO POR EMPRESA OPTANTE DO SIMPLES NACIONAL(Art. 23 da LC 123/2006), DEVENDO NESTA CONDIÇÃO O PRESTADOR\n'
    'INFORMAR A ALÍQUOTA ENTRE 2 A 5%, CONFORME TABELA DE ENQUADRAMENTO DO SIMPLES NACIONAL DE ACORDO COM O SEU FATURAMENTO.\n'
    '\n'
    'Consulte a autenticidade deste documento acessando o site https:/Awww.barreiras.ba.gov.br/\n'
    '\n'
    'VALOR SERVIÇO (R$)] DEDUÇÕES (R$) DESCONTO INCONDICIONAL (R$) BASE CÁLCULO (R$) ALÍQUOTA (%) ss (R$)\n'
    '1.500,00 0,00 0,00 1.500,00 0.00 0,00\n'
    'DEMONSTRATIVO DOS TRIBUTOS FEDERAIS DESCONTO (R$) OUTRAS (R$) VALOR LÍQUIDO (Rs)\n'
    'INSS (RS) IR (R$) CSLL (R$)| COFINS (R$) PIS (R$) CONTI ESTENÇÕES\n'
    '0,00 0,00 0,00 0,00 0,00 0,00 0,00 1.500,00\n'
    'OUTRAS INFORMAÇÕES\n'
    '(Valor Líquido = Valor Serviço - INSS - IR - CSLL - Outras Retenções - COFINS - PIS - Descontos Diversos - ISS Retido - Desconto Incondicional)\n'
    'BARR_CHAVE: 29032011200999093000100260000000406026080008401503\n'
    'BARR_DATA_FG: 10/08/2026\n'
    'BARR_COD: 565734070'
)

MOCK_PAG3 = (
    'NOTA FISCAL DE SERVIÇOS ELETRÔNICA - NFSo\n'
    'MUNICIPIO DE BARREIRAS\n'
    'Codigo de Verificação para Autenticação: C6h46049\n'
    '\n'
    'Endereço: Barreiras, Bahia, BA, 47800-390\n'
    'CNPJ: 13.654.405/0001-98, Email: srmecadacao tributosfBbarreiras ba gov br am Joias 18:19 15\n'
    '\n'
    'Data Fato Gerador Exigibilidade de ISS Regime Tributário Nº da Nota\n'
    'CEE ema oa\n'
    '\n'
    'Tipo de Recolhimento Tocal de P to 4059\n'
    '[Es | Tomem [ommcomemm | tema\n'
    '\n'
    'PRESTADOR\n'
    '\n'
    'Razão Social: BETINA SANTROVITSCH POSSATO LTDA\n'
    '\n'
    'Nome Fantasia: OBRAMAX LOCACAO E SERVICOS\n'
    '\n'
    'Barreiras - BA - CEP: 47810-704\n'
    '\n'
    'E-mail: PER COOL Fone: (77)3611-8445 - Celular: (77)99835-4201 - Site:\n'
    'Inscrição Estadual: ....... - Inscrição Municipal: 2212 - CPF/CNPJ: 00.999.093/0001-00\n'
    '\n'
    'TOMADOR\n'
    'Razão Social: SAO PEDRO CONSTRUTORA LTDA\n'
    '\n'
    'Endereço: Rua RUA, 554, QUADRA 28, LOTE 09 - VILAS DO ATLANTICO\n'
    'LAURO DE FREITAS - BA - CEP: 42708720\n'
    '\n'
    'E-mail: ça Fone: (71) 3272-0733 - Celular:\n'
    'Inscrição Estadual: ........ - Inscrição Municipal: 353043 - CPF/CNPJ: 03.051.741/0001-90\n'
    '\n'
    'SERVIÇO NACIONAL\n'
    '030501 - Cessão de andaimes, palcos, coberturas e outras estruturas de uso temporário.\n'
    '\n'
    'SERVIÇO NBS\n'
    'NBS: 1.0105.70.00 - Serviços de andaimes\n'
    '\n'
    '03.05 - CESSÃO DE ANDAIMES, PALCOS, COBERTURAS E OUTRAS ESTRUTURAS DE USO TEMPORÁRIO.\n'
    '\n'
    'DISCRIMINAÇÃO DOS SERVIÇOS\n'
    '\n'
    'VALOR SERVIÇO (R$)] DEDUÇÕES (R$)| DESCONTO INCONDICIONAL (R$) BASE CÁLCULO (R$) ALÍQUOTA (%) ss (R$)\n'
    '480,00 0,00 0,00 480,00 3.33 15,98\n'
    'DEMONSTRATIVO DOS TRIBUTOS FEDERAIS DESCONTO (R$) ouTRAS (R$) VALOR LÍQUIDO (R$)\n'
    'INSS (R$) IR (R$) CSLL (R$)| COFINS (R$)] PIS (R$) ERRA FETENÇÕES\n'
    '0,00 0,00 0,00 0,00 0,00 0,00 0,00 480,00\n'
    'OUTRAS INFORMAÇÕES\n'
    '(Valor Líguido = Valor Serviço - INSS - IR - CSLL - Outras Retenções - COFINS - PIS - Descontos Diversos - ISS Retido - Desconto Incondicional)\n'
    'BARR_CHAVE: 29032011200999093000100260000000405926080008401090\n'
    'BARR_DATA_FG: 10/08/2026\n'
    'BARR_COD: c6b480n49\n'
    'DEMONSTRATIVO DOS TRIBUTOS FEDERAIS\n'
    'INSS (RS) IR (R$) CSLL (R$)| COFINS (R$) PIS (R$)\n'
    '0,00 0,00 0,00 0,00 0,00\n'
    '\n'
    '(Valor Líquido = Valor Serviço - INSS - IR - CSLL - Outras Retenções - COFINS - PIS - Descontos Diversos - ISS Retido - Desconto Incondicional)\n'
    '\n'
    'ESTE DOCUMENTO FOI EMITIDO POR EMPRESA OPTANTE DO SIMPLES NACIONAL(Art, 23 da LC 123/2006), DEVENDO NESTA CONDIÇÃO O PRESTADOR\n'
    'INFORMAR A ALÍQUOTA ENTRE 2 A 5%, CONFORME TABELA DE ENQUADRAMENTO DO SIMPLES NACIONAL DE ACORDO COM O SEU FATURAMENTO.\n'
    '\n'
    'Consulte a autenticidade deste documento acessando o site https:/Avww.barreiras.ba.gov.br/\n'
    ''
)

MOCK_PAG6 = (
    'NOTA FISCAL DE SERVIÇOS ELETRÔNICA - NFSe\n'
    'MUNICIPIO DE BARREIRAS\n'
    'Codigo de Verificação para Autenticação: 713315cc8\n'
    '\n'
    'Endereço Barreiras, Bahia BA, 47800-300\n'
    'CNPJ, 13.854 405/0001-05, E-mail armecadacão tributosfQbarreiras ba gor tr\n'
    '\n'
    'PRESTADOR\n'
    '\n'
    'Razão Social: RENATO ANDRE GIARETTON\n'
    'Nome Fantasia: GUINDASTE BARREIRAS\n'
    'Endereço: Rua BÉLGICA, 211, CASA - Boa Sorte\n'
    'Barreiras - BA - CEP: 47807-225\n'
    '\n'
    'E-mai: RENATOGIARETTONGQHOTMAIL.COM - Fone: - Celular: (77)99993-0733 - Site: .......»\n'
    'Inscrição Estadual: ........ = Inscrição Municipal: 000018899 - CPF/CNPJ: 33.250.186/0001-96\n'
    '\n'
    'TOMADOR\n'
    '\n'
    'Razão Social: SAO PEDRO CONSTRUTORA LTDA\n'
    '\n'
    'Endereço: Rua RUA, 554, QUADRA 28, LOTE 09 - VILAS DO ATLANTICO\n'
    'LAURO DE FREITAS - BA - CEP: 42708720\n'
    '\n'
    'E-mail: sp()saopedroconstrutora.com.br - Fone: - Celular:\n'
    'Inscrição Estadual: ........ - Inscrição Municipal: 353043 - CPF/CNPJ: 03.051.741/0001-90\n'
    '\n'
    'SERVIÇO NACIONAL\n'
    '\n'
    '14.14 - GUINCHO INTRAMUNICIPAL, GUINDASTE E IÇAMENTO.\n'
    '\n'
    'DISCRIMINAÇÃO DOS SERVIÇOS\n'
    '\n'
    'SERVIÇO DE MUNCK PARA IÇAMENTO DE TANQUE\n'
    '\n'
    'BOLETO COM VENCIMENTO PARA 25/08/2026\n'
    '\n'
    'genheire Civil\n'
    'CREA 30.457-BA\n'
    '\n'
    'OBSERVAÇÃO\n'
    '\n'
    'VALOR SERVIÇO (R$)] DEDUÇÕES (R$)] DESCONTO INCONDICIONAL (R$) BASE CÁLCULO (R$) ALÍQUOTA (%) ss (R$\n'
    '420,00 0,00 0,00 A é\n'
    'OUTRAS\n'
    '\n'
    'VALOR SERVIÇO (R$)] DEDUÇÕES (R$) DESCONTO INCONDICIONAL (R$) BASE CÁLCULO (R$) ALÍQUOTA (%) ss (R$)\n'
    '420,00 0,00 0,00 420,00 4 17,26\n'
    'DEMONSTRATIVO DOS TRIBUTOS FEDERAIS Desconto (R$) ouTRAS (R$) VALOR LÍQUIDO (R$)\n'
    'INSS (R$) IR (R$) CSLL (R$)| COFINS (R$) PIS (R$) OMONCHOINAL, RETENÇOER\n'
    '0,00 0,00 0,00 0,00 0,00 0,00 0,00 420,00\n'
    'OUTRAS INFORMAÇÕES\n'
    '(Valor Líquido = Valor Serviço - INSS - IR - CSLL - Outras Retenções - COFINS - PIS - Descontos Diversos - ISS Retido - Desconto Incondicional)\n'
    'BARR_CHAVE: 29032011233250186000196260000000089226080008427935\n'
    'BARR_COD: 713315c08\n'
    'DEMONSTRATIVO DOS TRIBUTOS FEDERAIS\n'
    'INSS (R$) IR (R$) CSLL (R$)| COFINS (R$) PIS (R$)\n'
    '0,00 0,00 0,00 0,00 0,00\n'
    '\n'
    'OUTRAS INFORMAÇÕES\n'
    '\n'
    'Chave de acesso Ambiente de Dados Nacional: 29032011233250186000196260000000089226080008427935 o\n'
    '(Valor Líquido = Valor Serviço - INSS - IR - CSLL - Outras Retenções - COFINS - PIS - Descontos Diversos - ISS Retido - Desconto Incondicional)\n'
    '\n'
    'DESCONTO (R$)\n'
    'CONDICIONAL\n'
    '\n'
    '0,00\n'
    '\n'
    'ESTE DOCUMENTO FOI EMITIDO POR EMPRESA OPTANTE DO SIMPLES NACIONAL(Art. 23 da LC 123/2006), DEVENDO NESTA CONDIÇÃO O PRESTADOR\n'
    'INFORMAR A ALÍQUOTA ENTRE 2 A 5%, CONFORME TABELA DE ENQUADRAMENTO DO SIMPLES NACIONAL DE ACORDO COM O SEU FATURAMENTO.\n'
    '\n'
    'Consulte a autenticidade deste documento acessando o site https:/Awwbarreiras.ba.gov.br/\n'
    '\n'
    'e\n'
    ''
)



MOCKS = {"pag1": MOCK_PAG1, "pag3": MOCK_PAG3, "pag6": MOCK_PAG6}


def _novo_extrator(texto):
    dummy_path = "tests/dummy_barreiras_nf_verificacao.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = texto
    extractor.from_ocr = True
    return extractor, dummy_path


def _parse(texto):
    extractor, dummy_path = _novo_extrator(texto)
    try:
        return extractor, extractor.parse()
    finally:
        os.remove(dummy_path)


# --------------------------------------------------------------------------
# Detecção de layout — a causa-raiz dos 4 colaterais
# --------------------------------------------------------------------------
@pytest.mark.parametrize("pag", ["pag1", "pag3", "pag6"])
def test_layout_e_barreiras_e_nao_danfse_nacional(pag):
    """`_detect_layout` aceitava só "Data Fato Gerador", que sobrevive ao OCR
    em 2 das 6 notas. Sem marca municipal, a nota caía no check largo de DANFSe
    Nacional por causa da "Chave de acesso Ambiente de Dados Nacional" que este
    portal imprime — e todo o resto (valores, número, código, município) saía
    pelo parser errado."""
    extractor, _ = _novo_extrator(MOCKS[pag])
    try:
        assert extractor._detect_layout() == LAYOUT_BARREIRAS
    finally:
        os.remove("tests/dummy_barreiras_nf_verificacao.pdf")


def test_pagina_1_nao_tem_o_rotulo_que_a_deteccao_antiga_exigia():
    """Trava a premissa da correção: é justamente por NÃO ter "Data Fato
    Gerador" legível que esta nota era roteada para o layout errado. Se um dia
    o fixture passar a ter o rótulo, este teste avisa que ele deixou de cobrir
    o caso."""
    assert "Data Fato Gerador" not in MOCK_PAG1
    assert "MUNICIPIO DE BARREIRAS" in MOCK_PAG1
    assert "Chave de acesso" in MOCK_PAG1


# --------------------------------------------------------------------------
# Valores — o que o usuário reportou
# --------------------------------------------------------------------------
def test_nota_4059_valor_recuperado_da_faixa_descartada():
    """R$480,00 com ISS de R$15,98 a 3,33%. Sem o recut, nada disso existe no
    texto e a nota saía inteira zerada."""
    _, nfse = _parse(MOCK_PAG3)
    v = nfse.valores
    assert v.valor_servicos == 480.00
    assert v.valor_deducoes == 0.00
    assert v.desconto_incondicionado == 0.00
    assert v.base_calculo == 480.00
    assert round(v.aliquota * 100, 2) == 3.33
    assert v.valor_iss == 15.98
    assert v.valor_liquido_nfse == 480.00
    # A identidade contábil que valida a grade fecha nesta nota.
    assert abs(v.base_calculo * v.aliquota - v.valor_iss) < 0.01


def test_aliquota_truncada_pelo_ocr_e_derivada_do_iss():
    """A nota da pág. 6 imprime "4.11" e o OCR devolve "4" — que não casa o
    padrão de número com 2 decimais e desaparece da linha, deixando 5 tokens
    em vez de 6. O token ambíguo restante é desempatado pela plausibilidade da
    alíquota (o ISS municipal é limitado a 5% pela LC 116/2003, art. 8º, II, e
    esta nota imprime no rodapé "INFORMAR A ALÍQUOTA ENTRE 2 A 5%"): lê-lo
    como ISS dá 4,11%, o valor impresso; como alíquota daria 17,26%,
    impossível."""
    _, nfse = _parse(MOCK_PAG6)
    v = nfse.valores
    assert v.valor_servicos == 420.00
    assert v.valor_iss == 17.26
    assert round(v.aliquota * 100, 2) == 4.11
    assert abs(v.base_calculo * v.aliquota - v.valor_iss) < 0.01


def test_iss_zero_do_simples_nao_e_reescrito():
    """A guarda essencial da identidade contábil: alíquota 0 COM ISS 0 é dado
    REAL nas notas do Simples deste portal (confirmado na imagem em zoom 9x —
    a nota imprime "0.00" e "0,00" nas duas colunas). A derivação só entra
    quando há DIVERGÊNCIA; se entrasse para "preencher" o zero, fabricaria uma
    alíquota que a nota não tem."""
    _, nfse = _parse(MOCK_PAG1)
    v = nfse.valores
    assert v.valor_servicos == 1500.00
    assert v.aliquota == 0.0
    assert v.valor_iss == 0.0
    assert v.valor_liquido_nfse == 1500.00


def test_coluna_de_percentual_com_ponto_decimal():
    """A nota usa PONTO na coluna de alíquota ("3.33", "4.11", "0.00") e
    vírgula nas monetárias — convenção do próprio documento, confirmada na
    imagem. `_parse_valor` trata ponto como separador de milhar, então sem
    conversão própria "3.33" viraria 333."""
    assert "3.33" in MOCK_PAG3
    _, nfse = _parse(MOCK_PAG3)
    assert round(nfse.valores.aliquota * 100, 2) == 3.33
    assert nfse.valores.aliquota < 1


# --------------------------------------------------------------------------
# Colateral 1 — número da nota
# --------------------------------------------------------------------------
@pytest.mark.parametrize("pag,numero", [
    ("pag1", "4060"), ("pag3", "4059"), ("pag6", "892")])
def test_numero_decodificado_da_chave_de_acesso(pag, numero):
    """O número saía `00000000` (pág. 3, onde a linha da chave também caiu na
    faixa descartada) ou com 13 dígitos crus (`2600000004059`) nas outras.

    O campo nNFSe da chave NÃO é um sequencial zero-preenchido como no DANFSe
    Nacional, onde `chave[23:36].lstrip('0')` acerta: esta prefeitura prefixa o
    ANO ("26"), então não sobra zero à esquerda e o slice genérico devolvia os
    13 dígitos. O número real vem DEPOIS da corrida de zeros.

    Conferido contra o valor impresso nas 2 notas cuja célula o OCR conseguiu
    ler (pág. 4 -> 882; pág. 3 -> 4059, também confirmada na imagem) e
    corroborado pelo lote: prestadores repetidos têm números consecutivos
    (BETINA 4059/4060, ATRIO 882/883)."""
    _, nfse = _parse(MOCKS[pag])
    assert nfse.numero == numero
    assert nfse.numero != "00000000"
    assert len(nfse.numero) <= 6


def test_chave_exige_prefixo_ibge_de_barreiras():
    """A chave só é aceita com validação ESTRUTURAL — 50 dígitos começando pelo
    código IBGE do município (2903201). Sem isso qualquer corrida longa de
    dígitos do documento passaria por chave."""
    extractor, dummy = _novo_extrator(MOCK_PAG3)
    try:
        chave = extractor._chave_barreiras()
        assert chave is not None
        assert len(chave) == 50
        assert chave.startswith("2903201")
        # CNPJ do prestador (posições 10-23) e AAMM (37-40) conferem.
        assert chave[9:23] == "00999093000100"
        assert chave[36:40] == "2608"
    finally:
        os.remove(dummy)

    # O prefixo é exigido nos DOIS caminhos. Nesta nota a linha do rótulo real
    # caiu na faixa descartada, então o único portador da chave é o marcador
    # sintético — e quem o escreve é o recut, que só confere o COMPRIMENTO da
    # corrida de dígitos; sem esta validação uma chave de outro município
    # entraria por ele e o número da nota sairia decodificado dela.
    mutado = MOCK_PAG3.replace("BARR_CHAVE: 2903201", "BARR_CHAVE: 1234567")
    assert mutado.count("1234567") == 1
    extractor, dummy = _novo_extrator(mutado)
    try:
        assert extractor._chave_barreiras() is None
    finally:
        os.remove(dummy)

    # E pelo rótulo real, o caminho usado nas notas em que a linha sobrevive.
    extractor, dummy = _novo_extrator(
        "MUNICIPIO DE BARREIRAS\nChave de acesso Ambiente de Dados Nacional: "
        "12345671200999093000100260000000405926080008401090\n")
    try:
        assert extractor._chave_barreiras() is None
    finally:
        os.remove(dummy)


# --------------------------------------------------------------------------
# Colateral 2 — data de emissão
# --------------------------------------------------------------------------
def test_data_de_emissao_real_em_vez_do_instante_da_conversao():
    """O XML da nota nº 4059 registrava como emissão o INSTANTE DA CONVERSÃO
    (`datetime.now()`), para uma nota emitida em 10/08/2026 — data fabricada, e
    sem aviso nenhum."""
    _, nfse = _parse(MOCK_PAG3)
    assert nfse.data_emissao.strftime("%d/%m/%Y") == "10/08/2026"
    assert not any("Data de emiss" in a for a in nfse.avisos)


def test_ano_e_mes_vem_da_chave_e_o_dia_do_cabecalho():
    """Ano e mês não dependem de OCR: são as posições 37-40 da chave (AAMM).
    O dia é a única parte que precisa do cabeçalho."""
    _, nfse = _parse(MOCK_PAG3)
    assert (nfse.data_emissao.year, nfse.data_emissao.month) == (2026, 8)


def test_dia_ilegivel_cai_no_mes_correto_com_aviso():
    """Quando o dia não é recuperável, o resultado é o 1º do mês CORRETO (o da
    chave) COM aviso — não um dia inventado em silêncio, e não mais a data da
    conversão. Aqui o marcador do recut é removido para simular a nota em que
    o cabeçalho não sobrevive em leitura nenhuma."""
    import re
    texto = re.sub(r'BARR_DATA_FG:[^\n]*\n?', '', MOCK_PAG3)
    _, nfse = _parse(texto)
    assert nfse.data_emissao.strftime("%d/%m/%Y") == "01/08/2026"
    assert any("Data de emiss" in a for a in nfse.avisos)


# --------------------------------------------------------------------------
# Colateral 3 — código de verificação
# --------------------------------------------------------------------------
@pytest.mark.parametrize("pag", ["pag1", "pag3", "pag6"])
def test_codigo_de_verificacao_consistente_nas_notas_do_lote(pag):
    """Antes: 4 das 6 notas recebiam a chave de 50 dígitos (porque caíam no
    LAYOUT_NACIONAL por erro de detecção) e 2 recebiam o código curto mal
    lido — dois formatos no mesmo lote.

    O código curto impresso (9 caracteres misturando letras MINÚSCULAS e
    dígitos, ex.: "c6b460a49" na pág. 3, confirmado na imagem em zoom 12x) não
    é recuperável nestes scans: seis tentativas independentes deram seis
    respostas diferentes e todas erradas. Quando as duas leituras
    independentes (página inteira e recut) discordam, o campo recebe a chave,
    que é estruturalmente verificável."""
    _, nfse = _parse(MOCKS[pag])
    assert len(nfse.codigo_verificacao) == 50
    assert nfse.codigo_verificacao.startswith("2903201")


def test_codigo_curto_legivel_nao_e_descartado():
    """O outro lado da regra: há notas deste layout em que o código curto sai
    perfeitamente legível (nota nº 1162, "ACC8CDE89", coberta em
    test_barreiras_valores_grade_locacao.py). Com uma leitura só, ou com as
    duas concordando, o código curto é mantido — trocá-lo pela chave seria
    descartar o valor certo. Aqui as duas leituras concordam."""
    import re
    texto = re.sub(r'BARR_COD:[^\n]*', 'BARR_COD: c6b460a49', MOCK_PAG3)
    texto = re.sub(r'(Autentica[çc][ãa]o:\s*)[0-9A-Za-z]{6,12}',
                   r'\g<1>c6b460a49', texto)
    _, nfse = _parse(texto)
    assert nfse.codigo_verificacao == "C6B460A49"


def test_token_de_digitos_puros_nao_passa_por_codigo():
    """O formato deste campo MISTURA letra e dígito. Um token de dígitos puros
    é outro número que o OCR arrastou para o lado do rótulo — achado real na
    nota da pág. 1, onde as DUAS leituras repetiam "565734070". Concordância
    entre leituras não basta se o formato está errado."""
    assert "565734070" in MOCK_PAG1
    _, nfse = _parse(MOCK_PAG1)
    assert nfse.codigo_verificacao != "565734070"
    assert len(nfse.codigo_verificacao) == 50


# --------------------------------------------------------------------------
# Colateral 4 — município das entidades
# --------------------------------------------------------------------------
@pytest.mark.parametrize("pag", ["pag1", "pag3", "pag6"])
def test_municipio_do_tomador_e_lauro_de_freitas(pag):
    """O tomador (SÃO PEDRO CONSTRUTORA, "LAURO DE FREITAS - BA - CEP:
    42708720") era gravado em SALVADOR (2927408), o fallback da capital: este
    template não tem rótulo "Cidade"/"Município" e o caminho genérico não achava
    município nenhum no bloco. Isso desloca o município no cadastro do tomador
    e, com ele, a referência de incidência do ISS no XML."""
    _, nfse = _parse(MOCKS[pag])
    assert nfse.tomador.endereco.municipio.upper().startswith("LAURO DE FREITAS")
    assert nfse.tomador.endereco.codigo_municipio == "2919207"
    assert nfse.tomador.endereco.uf == "BA"


@pytest.mark.parametrize("pag", ["pag1", "pag3", "pag6"])
def test_municipio_do_prestador_e_barreiras(pag):
    """O prestador também caía em SALVADOR. Quando a linha de cidade dele fica
    ilegível (caso da pág. 1, onde sai "-BA- : 4781"), o default do layout é
    Barreiras — o emitente é contribuinte DESTE município, que a nota declara
    em "Local de Prestação/Recolhimento: 2903201 - Barreiras - BA". Mesmo
    padrão do default de UF já usado por este layout."""
    _, nfse = _parse(MOCKS[pag])
    assert nfse.prestador.endereco.codigo_municipio == "2903201"


def test_tomador_nao_herda_os_dados_do_prestador_sem_o_cabecalho_da_secao():
    """Na pág. 1 o cabeçalho de seção "TOMADOR" foi comido inteiro pelo OCR
    (presente na pág. 3, ausente aqui). Sem ele, o bloco do tomador caía no
    fallback delimitado pelo rótulo do PRESTADOR — que contém só os dados dele
    — e Prestador e Tomador saíam IDÊNTICOS. Mesma família do vazamento já
    documentado em Cuiabá, com outra âncora: cada entidade começa por uma
    linha "Razão Social:", então o bloco do tomador é o trecho da SEGUNDA até
    "SERVIÇO NACIONAL"."""
    assert "TOMADOR" not in MOCK_PAG1
    _, nfse = _parse(MOCK_PAG1)
    assert nfse.prestador.razao_social == "BETINA SANTROVITSCH POSSATO LTDA"
    assert nfse.tomador.razao_social == "SAO PEDRO CONSTRUTORA LTDA"
    assert nfse.tomador.cnpj_cpf == "03051741000190"
    assert nfse.prestador.cnpj_cpf == "00999093000100"
    assert nfse.tomador.cnpj_cpf != nfse.prestador.cnpj_cpf


def test_prestador_nao_vaza_para_dentro_do_bloco_do_tomador():
    """O limite SIMÉTRICO: sem o cabeçalho "TOMADOR", o bloco do PRESTADOR
    (cujo cabeçalho sobreviveu) perdia o delimitador da direita e se estendia
    por cima dos dados do tomador — o município do prestador saía "LAURO DE
    FREITAS", a cidade do TOMADOR."""
    _, nfse = _parse(MOCK_PAG1)
    assert nfse.prestador.endereco.municipio == "Barreiras"
    assert nfse.tomador.endereco.municipio.upper().startswith("LAURO DE FREITAS")


def test_razao_social_do_tomador_sem_ruido_da_linha_seguinte():
    """A busca genérica de razão social roda sobre o bloco com as quebras de
    linha achatadas em espaços, então o ruído da linha SEGUINTE entrava no
    nome: nesta nota a linha de endereço do tomador saiu "te 2d ta dd EL" e a
    razão vinha "SAO PEDRO CONSTRUTORA LTDA te 2d ta dd EL". Neste template a
    razão ocupa a linha inteira e só ela."""
    assert "te 2d ta dd EL" in MOCK_PAG1
    _, nfse = _parse(MOCK_PAG1)
    assert nfse.tomador.razao_social == "SAO PEDRO CONSTRUTORA LTDA"


# --------------------------------------------------------------------------
# Helpers do recut — o portão e a costura
# --------------------------------------------------------------------------
def test_grade_completa_ignora_a_frase_do_rodape():
    """O portão do recut NÃO pode usar a presença do rótulo "Valor Serviço"
    como sinal: essa expressão também aparece na frase de rodapé "(Valor
    Líquido = Valor Serviço - INSS - IR - ...)", que sobrevive ao OCR mesmo
    quando a grade inteira foi descartada — nas 6 notas do lote ela estava
    presente e a grade não."""
    rodape = ("(Valor Líquido = Valor Serviço - INSS - IR - CSLL - Outras "
              "Retenções - COFINS - PIS - Descontos Diversos - ISS Retido)")
    assert not SPPdfExtractor._grade_barreiras_completa(rodape)


def test_grade_completa_exige_cabecalho_seguido_de_valores():
    cab = ("VALOR SERVIÇO (R$)| DEDUÇÕES (R$)| DESCONTO INCONDICIONAL (R$) "
           "BASE CÁLCULO (R$) ALÍQUOTA (%) ss (R$)")
    assert not SPPdfExtractor._grade_barreiras_completa(cab)
    assert SPPdfExtractor._grade_barreiras_completa(
        cab + "\n480,00 0,00 0,00 480,00 3.33 15,98")
    # A grade das 3 notas embutidas aqui já vem completa (a fatia foi costurada
    # por `_ocr_page`), senão nada disto seria extraível.
    for texto in (MOCK_PAG1, MOCK_PAG3, MOCK_PAG6):
        assert SPPdfExtractor._grade_barreiras_completa(texto)


def test_fatia_usa_marcador_sintetico_e_nao_o_rotulo_real_da_chave():
    """A fatia carrega a chave como `BARR_CHAVE:`, nunca com o rótulo real
    "Chave de acesso": esse rótulo é ao mesmo tempo separador de bloco em
    `parse_multiple` e marca de detecção do LAYOUT_NACIONAL, então
    reintroduzi-lo fazia a própria fatia virar um bloco órfão detectado como
    DANFSe Nacional — e a nota voltava a sair zerada."""
    recut = (
        "Codigo de Verificação para Autenticação: c6b480n49\n"
        "Data Fato Gerador Exigibilidade de ISS\n"
        "10/08/2026 Exigivel Tributação Normal\n"
        "VALOR SERVIÇO (R$)| DEDUÇÕES (R$)| BASE CÁLCULO (R$) ALÍQUOTA (%) ISS\n"
        "480,00 0,00 0,00 480,00 3.33 15,98\n"
        "Chave de acesso Ambiente de Dados Nacional: "
        "29032011200999093000100260000000405926080008401090\n")
    fatia = SPPdfExtractor._fatia_grade_barreiras(recut)
    assert "BARR_CHAVE: 29032011200999093000100260000000405926080008401090" in fatia
    assert "BARR_DATA_FG: 10/08/2026" in fatia
    assert "BARR_COD: c6b480n49" in fatia
    assert "Chave de acesso" not in fatia
    assert "480,00 0,00 0,00 480,00 3.33 15,98" in fatia


def test_costura_entra_dentro_do_corpo_da_nota():
    """A fatia é costurada ANTES do "DEMONSTRATIVO DOS TRIBUTOS FEDERAIS", que
    sobrevive ao OCR degradado e está no MESMO bloco das entidades. Colada na
    FRENTE do texto, ela cairia num bloco separado do corpo da nota — medido:
    só 2 das 6 notas saíam com valor, embora o texto de cada página estivesse
    correto quando lido isoladamente."""
    corpo = ("MUNICIPIO DE BARREIRAS\nRazão Social: X\n"
             "DEMONSTRATIVO DOS TRIBUTOS FEDERAIS\n0,00 0,00\n")
    saida = SPPdfExtractor._insere_grade_barreiras(corpo, "FATIA")
    assert saida.index("MUNICIPIO DE BARREIRAS") < saida.index("FATIA")
    assert saida.index("FATIA") < saida.index("DEMONSTRATIVO")
    # Sem a âncora, anexa no fim (ainda dentro do último bloco).
    assert SPPdfExtractor._insere_grade_barreiras("SEM ANCORA\n", "FATIA") == \
        "SEM ANCORA\n\nFATIA"
