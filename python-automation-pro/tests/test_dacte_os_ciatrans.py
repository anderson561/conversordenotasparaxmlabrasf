# -*- coding: utf-8 -*-
r"""CT-e OS (Conhecimento de Transporte Eletrônico para Outros Serviços) -
Modelo 67, DACTE OS (`LAYOUT_DACTE_OS`) - nota real nº 438, CIATRANS POOL
TRANSPORTES DE PASSAGEIROS LTDA -> STAUMMAQ SERVICOS TECNICOS AUT MOT E
MAQUINAS LTDA, transporte de funcionários, R$6.739,50 (arquivo "ciatrans
82026.pdf").

Documento estruturalmente DISTINTO tanto da NFS-e ABRASF (tributado por
ICMS, não ISS) quanto da NF-e de produto Modelo 55 (não tem tabela de itens/
NCM/CFOP - o "produto" é o SERVIÇO de transporte) - retorna um `CteOS`, com
seu próprio transformer (`CteTransformer`, XML `cteProc`/`CTe`/`infCte`,
`mod=67`, namespace `.../cte`). Ver LAYOUT_DACTE_OS para o histórico completo
da detecção e das degradações de OCR.

Toda verificação de campo abaixo foi conferida PIXEL A PIXEL contra o PDF
real antes de escrever a regex de extração (zoom nativo do PyMuPDF, sem
upscaling de raster já borrado) e por três checagens estruturais
independentes: (1) a chave de acesso passa no dígito verificador mod-11 e
DECODIFICA exatamente para cUF=29/BA, AAMM=2608, CNPJ do emitente, mod=67,
série=001, número=000000438; (2) os CNPJs do emitente e do tomador passam no
dígito verificador; (3) Valor Total da Prestação (R$6.739,50) menos Valor do
INSS retido (R$222,40) bate exatamente com o Valor a Receber impresso
(R$6.517,10). Alta confiança nesta nota rara de justificar tanta verificação
cruzada - documento novo, sem precedente no repositório.
"""
import pytest

from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_DACTE_OS
from src.models.cte_os_model import CteOS
from src.transformers.cte_transformer import CteTransformer

# Texto REAL do Tesseract sobre a página inteira, verbatim (`_extract_via_ocr`).
# Muito embaralhado por proximidade visual de colunas vizinhas (ex.: o rótulo
# do canhoto "TÉRMINO DA PRESTAÇÃO - DATA / HORA" funde com o título da caixa
# ao lado, "CT-e OS") - a maior parte dos campos ainda sai extraível por
# âncora textual tolerante; a grade de valores/imposto não (ver MOCK_GRADE).
MOCK_PAGINA = """\
DECLARO QUE RECEBI OS SERVIÇOS DESTE CONHECIMENTO EM PERFEITO ESTADO PELO QUE DOU POR CUMPRIDO O PRESENTE CONTRATO DE TRANSPORTE

NOME:

ASSINATURA / CARIMBO

TÉRMINO DA PRESTAÇÃO - DATA / HORA CT-e OS
Nº, DOCUMENTO
INÍCIO DA PRESTAÇÃO - DATA / HORA 000000438
SÉRIE 001

CIATRANS POOL TRANSPORTES DE
PASSAGEIROS LTDA
CNPJ: 3036767 1000156 IE: 149299655

Via das Torres, 646 - Complexo b
Cia sul - Simoes Filho/BA - CEP: 43700000
FONE: 7135947121

TIPO DO CT-E

Normal
TIPO DO SERVIÇO

Transporte de Pessoas

CFOP- NATUREZA DA OPERAÇÃO
5352 - PRESTAÇÃO DE SERVIÇO DE TRANSPORTE

INÍCIO DA PRESTAÇÃO

2930709 - Simoes Filho

DACTE OS

Documento Auxiliar do Conhecimento de Transporte Eletrônico
para Outros Serviços

MODELO SÉRIE NÚMERO

67 1 438

O

CHAVE DE ACESSO

29260830367671000156670010000004381000004533

DATA E HORA EMISSÃO

04/08/2026 08:04:44

INSC. SUFRAMA DEST

Consulta em https://dfe-portal.svrs.rs.gov.br/cte/consulta

PROTOCOLO DE AUTORIZAÇÃO DE USO
329260179200437 04/08/2026 08:09:27
TÉRMINO DA PRESTAÇÃO

PERCURSO DO VEÍCULO

2927408 - Salvador

TOMADOR DO seRvIÇO STAUMMAQ SERVICOS TECNICOS AUT MOT E MAQUINAS LTDA

ENDEREÇO: Via URBANA, , Nº 01 - CIA SUL - Simões Filho
enpycrr: 02.370.080/0001-00 IE

: 048137340

FONE:

Municirio: Simoes Filho CEP;

ur: BA país: BRASIL

EMAIL:

43700000

INFORMAÇÕES DA PRESTAÇÃO DO SERVIÇO

QUANTIDADE DESCRIÇÃO DO SERVIÇO PRESTADO
0 Transporte de funcionários

NOME VALOR NOME
R$ 6.739,50 6.517,10

CLASSIFICAÇÃO TRIBUTÁRIA DO SERVIÇO

VALOR DO PIS
0,00

Cio ho cagro fuyo 2220

COMPONENTES DO VALOR DA PRESTAÇÃO DE SERVIÇO

VALOR NOME

INFORMAÇÕES RELATIVAS AO IMPOSTO

VALOR COFINS

0,00

VALOR DO IMPOSTO DE RENDA

OBSERVAÇÕES

TRANSPORTE DE FUNCIONÁRIOS NO MÊS DE JULHO/VENCIMENTO: 14/08/2026

NUMERO DO PEDIDO: - 8171

NOME DA SEGURADORA

TERMO DE AUTORIZAÇÃO DE FRETAMENTO Nº DO REGISTRO ESTADUAL

DATA E HORA DA IMPRESSÃO: 04/08/2026 08:09:49

BASE DE CÁLCULO AL ICMS (%)

0,00

SEGURO DA VIAGEM
RESPONSÁVEL

0,00 20,50

INFORMAÇÕES ESPECÍFICAS DO MODAL RODOVIÁRIO
PLACA DO VEÍCULO RENAVAN DO VEÍCULO

0000000000000000000043115  MQN2581 869471996
USO EXCLUSIVO DO EMISSOR DO CT-e OS

VALOR VALOR TOTAL DA PRESTAÇÃO DO

VALOR A RECEBER

VALOR ICMS % RED.BC.CÁLC
0,00 100,00
VALOR DO INSS

222,40

NÚMERO DA APÓLICE

UF DE LICENCIAMENTO DO VEÍCULO CNPJ/CPF

BA 03552115560
RESERVADO AO FISCO

SERVIÇO

6.739,50

6.517,10

ICMS ST
0,00
VALOR DO CSLL

0,00

Master CT-e - www.oflicesystem.com.br
"""

# Texto REAL do Tesseract sobre o recorte dedicado da grade "COMPONENTES DO
# VALOR DA PRESTAÇÃO DE SERVIÇO" + "INFORMAÇÕES RELATIVAS AO IMPOSTO"
# (`_ocr_recut_dacte_os_grade`, ancorado via `image_to_data` nos rótulos
# "COMPONENTES"/"OBSERVAÇÕES" - nunca frações fixas de altura -, `--psm 6`).
# A MESMA faixa, isolada e numa resolução maior, sai em ordem de leitura
# correta - ao contrário do texto de página inteira acima.
MOCK_GRADE = """\
COMPONENTES DO VALOR DA PRESTAÇÃO DE SERVIÇO
NOME VALOR NOME VALOR NOME VALOR VALOR TOTAL DA PRESTAÇÃO DO SERVIÇO
R$ 6.739,50 6.517,10
6.739,50
VALOR A RECEBER
6.517,10
INFORMAÇÕES RELATIVAS AO IMPOSTO

CLASSIFICAÇÃO TRIBUTÁRIA DO SERVIÇO BASE DE CÁLCULO AL ICMS (%) VALOR ICMS % RED.BC.CÁLC ICMS ST
0,00 20,50 0,00 100,00 0,00
VALOR DO PIS VALOR COFINS VALOR DO IMPOSTO DE RENDA VALOR DO INSS VALOR DO CSLL
0,00 0,00 0,00 222,40 0,00
"""


def _parse(monkeypatch, tmp_path, mock_pagina, mock_grade):
    pdf_path = tmp_path / "ciatrans.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 dummy")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: mock_pagina)
    if mock_grade is not None:
        monkeypatch.setattr(SPPdfExtractor, "_ocr_recut_dacte_os_grade", lambda self: mock_grade)
    ex = SPPdfExtractor(str(pdf_path))
    notas = ex.parse_multiple()
    assert len(notas) == 1
    return notas[0]


@pytest.fixture
def nota_recut_real(monkeypatch, tmp_path):
    """`_ocr_recut_dacte_os_grade` NÃO mockado - roda de verdade contra o PDF
    dummy do fixture (arquivo existe mas não é um PDF válido). Cobre a
    implementação real do recorte (não só o texto que ele devolveria): abre
    `pymupdf.open` sobre um arquivo sem estrutura de PDF, que levanta
    exceção, capturada pelo próprio método - devolve "" honestamente, mesmo
    comportamento de qualquer outro recorte dedicado do projeto quando não
    há página real por trás (ver `_ocr_cabecalho_sem_parar`)."""
    return _parse(monkeypatch, tmp_path, MOCK_PAGINA, mock_grade=None)


@pytest.fixture
def nota_sem_recut(monkeypatch, tmp_path):
    """Sem o recorte dedicado (retorna vazio, como aconteceria com um PDF sem
    página real por trás - `_ocr_recut_dacte_os_grade` é aditivo e devolve
    "" em qualquer falha). Cobre o caminho de fallback: valores/imposto ficam
    zerados, com aviso, em vez de fabricados a partir do texto de página
    inteira (que sai posicionalmente inutilizável para esta grade)."""
    return _parse(monkeypatch, tmp_path, MOCK_PAGINA, mock_grade="")


@pytest.fixture
def nota(monkeypatch, tmp_path):
    """Com o recorte dedicado retornando o texto real capturado - caminho
    feliz, usado pela maioria dos testes abaixo."""
    return _parse(monkeypatch, tmp_path, MOCK_PAGINA, mock_grade=MOCK_GRADE)


# --------------------------------------------------------------- detecção

def test_layout_e_dacte_os():
    ex = SPPdfExtractor.__new__(SPPdfExtractor)
    ex.raw_text = MOCK_PAGINA
    ex.from_ocr = True
    ex.layout = None
    ex.pdf_path = "x.pdf"
    assert ex._detect_layout_page(MOCK_PAGINA) == LAYOUT_DACTE_OS


def test_retorna_cteos_nao_nfse_nem_nfeproduto(nota):
    assert isinstance(nota, CteOS)


# ------------------------------------------------------- chave e cabeçalho

def test_chave_de_acesso_e_a_impressa(nota):
    assert nota.chave_acesso == "29260830367671000156670010000004381000004533"
    assert len(nota.chave_acesso) == 44


def test_modelo_serie_numero(nota):
    assert nota.modelo == "67"
    assert nota.serie == "1"
    assert nota.numero == "438"


def test_data_emissao_e_protocolo(nota):
    assert nota.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "04/08/2026 08:04:44"
    assert nota.protocolo_autorizacao == "329260179200437"
    assert nota.protocolo_data_hora.strftime("%d/%m/%Y %H:%M:%S") == "04/08/2026 08:09:27"


def test_tipo_cte_tipo_servico_cfop(nota):
    assert nota.tipo_cte == "Normal"
    assert nota.tipo_servico == "Transporte de Pessoas"
    assert nota.cfop == "5352"
    assert nota.natureza_operacao == "PRESTAÇÃO DE SERVIÇO DE TRANSPORTE"


def test_rota_inicio_termino_prestacao(nota):
    assert nota.codigo_municipio_inicio == "2930709"
    assert nota.municipio_inicio_prestacao == "Simoes Filho"
    assert nota.codigo_municipio_fim == "2927408"
    assert nota.municipio_fim_prestacao == "Salvador"


def test_sem_avisos_com_o_recorte_disponivel(nota):
    assert nota.avisos == []


# ------------------------------------------------------------- emitente

def test_emitente_ciatrans(nota):
    e = nota.emitente
    assert e.razao_social == "CIATRANS POOL TRANSPORTES DE PASSAGEIROS LTDA"
    assert e.cnpj_cpf == "30367671000156"
    assert e.inscricao_estadual == "149299655"
    assert e.telefone == "7135947121"


def test_cnpj_do_emitente_passa_no_digito_verificador(nota):
    from src.extractors.pdf_extractor import SPPdfExtractor as _E
    assert _E._cnpj_valido(nota.emitente.cnpj_cpf)


def test_endereco_emitente(nota):
    end = nota.emitente.endereco
    assert end.logradouro == "Via das Torres"
    assert end.numero == "646"
    assert end.complemento == "Complexo b"
    assert end.bairro == "Cia sul"
    assert end.municipio == "Simoes Filho"
    assert end.uf == "BA"
    assert end.cep == "43700000"
    assert end.codigo_municipio == "2930709"


# -------------------------------------------------------------- tomador

def test_tomador_staummaq(nota):
    tom = nota.tomador
    assert tom.razao_social == "STAUMMAQ SERVICOS TECNICOS AUT MOT E MAQUINAS LTDA"
    assert tom.cnpj_cpf == "02370080000100"
    assert tom.inscricao_estadual == "048137340"


def test_cnpj_do_tomador_passa_no_digito_verificador(nota):
    from src.extractors.pdf_extractor import SPPdfExtractor as _E
    assert _E._cnpj_valido(nota.tomador.cnpj_cpf)


def test_endereco_tomador_de_uma_linha_so(nota):
    """"ENDEREÇO: Via URBANA, , Nº 01 - CIA SUL - Simões Filho" - endereço de
    uma linha só, com rótulos vizinhos degradados pelo OCR ("enpycrr:" para
    "CNPJ/CPF:", "Municirio" para "Município", "ur:" para "UF:") - extraído
    por padrão posicional tolerante, não pelo rótulo em si."""
    end = nota.tomador.endereco
    assert end.logradouro == "Via URBANA"
    assert end.numero == "01"
    assert end.bairro == "CIA SUL"
    assert end.municipio == "Simões Filho"
    assert end.uf == "BA"


def test_cep_do_tomador_sai_deslocado_para_o_fim_do_bloco(nota):
    """O CEP do tomador ("43700000") não fica perto do rótulo "CEP;" (que
    sai sem valor nenhum ao lado) - sai isolado no FIM do bloco, depois do
    rótulo "EMAIL:", logo antes da próxima seção "INFORMAÇÕES DA PRESTAÇÃO DO
    SERVIÇO" - mesma família de "valor deslocado para o fim do bloco" já
    vista no LAYOUT_DANFE_PRODUTO."""
    assert "CEP;" in MOCK_PAGINA
    assert "CEP; 43700000" not in MOCK_PAGINA
    assert nota.tomador.endereco.cep == "43700000"


def test_tomador_e_emitente_compartilham_o_mesmo_municipio(nota):
    """Ambos em Simões Filho/BA - o código IBGE do tomador reaproveita o
    mesmo código já impresso (e validado) para "Início da Prestação", em vez
    de uma nova resolução via IBGEResolver."""
    assert nota.tomador.endereco.codigo_municipio == nota.emitente.endereco.codigo_municipio == "2930709"


# -------------------------------------------------------------- serviço

def test_quantidade_e_descricao_do_servico(nota):
    assert nota.quantidade_servico == 0.0
    assert nota.descricao_servico == "Transporte de funcionários"


# --------------------------------------------------------------- valores

def test_valor_total_e_valor_a_receber(nota):
    assert nota.valor_total_prestacao == pytest.approx(6739.50)
    assert nota.valor_a_receber == pytest.approx(6517.10)


def test_grade_de_icms(nota):
    imp = nota.imposto
    assert imp.base_calculo_icms == pytest.approx(0.0)
    assert imp.aliquota_icms == pytest.approx(20.50)
    assert imp.valor_icms == pytest.approx(0.0)
    assert imp.percentual_reducao_bc == pytest.approx(100.0)
    assert imp.valor_icms_st == pytest.approx(0.0)


def test_retencoes_federais(nota):
    imp = nota.imposto
    assert imp.valor_pis == pytest.approx(0.0)
    assert imp.valor_cofins == pytest.approx(0.0)
    assert imp.valor_ir == pytest.approx(0.0)
    assert imp.valor_inss == pytest.approx(222.40)
    assert imp.valor_csll == pytest.approx(0.0)


def test_identidade_valor_total_menos_inss_bate_com_a_receber(nota):
    """Conferência (não preenchimento): Valor Total - retenções federais deve
    bater com o Valor a Receber impresso. 6.739,50 - 222,40 = 6.517,10,
    exato."""
    imp = nota.imposto
    retencoes = imp.valor_pis + imp.valor_cofins + imp.valor_ir + imp.valor_inss + imp.valor_csll
    assert nota.valor_total_prestacao - retencoes == pytest.approx(nota.valor_a_receber, abs=0.01)


# ---------------------------------------------------------- observações

def test_observacoes_e_numero_do_pedido(nota):
    assert "TRANSPORTE DE FUNCIONÁRIOS NO MÊS DE JULHO" in nota.observacoes
    assert "NUMERO DO PEDIDO" in nota.observacoes
    assert nota.numero_pedido == "8171"


# ------------------------------------------------------- modal rodoviário

def test_modal_rodoviario(nota):
    modal = nota.modal_rodoviario
    assert modal is not None
    assert modal.registro_estadual == "0000000000000000000043115"
    assert modal.placa_veiculo == "MQN2581"
    assert modal.renavam == "869471996"
    assert modal.uf_licenciamento == "BA"
    assert modal.cnpj_cpf_responsavel == "03552115560"


# --------------------------------------- recorte dedicado indisponível

def test_sem_o_recorte_valores_ficam_zerados_com_aviso(nota_sem_recut):
    """`_ocr_recut_dacte_os_grade` é ADITIVO: quando falha (ex.: sem página
    real por trás, como um PDF dummy), devolve "" e o chamador NÃO cai de
    volta no texto de página inteira para estes campos (que sai
    posicionalmente inutilizável) - zera e avisa, nunca fabrica."""
    assert nota_sem_recut.valor_total_prestacao == 0.0
    assert nota_sem_recut.valor_a_receber == 0.0
    assert nota_sem_recut.imposto.base_calculo_icms == 0.0
    assert nota_sem_recut.imposto.valor_inss == 0.0
    assert any("Valor total da prestação" in a for a in nota_sem_recut.avisos)


def test_sem_o_recorte_os_demais_campos_continuam_ok(nota_sem_recut):
    """A falha do recorte é isolada aos campos da grade - cabeçalho,
    emitente, tomador e modal rodoviário (todos lidos do texto de página
    inteira) continuam corretos."""
    assert nota_sem_recut.chave_acesso == "29260830367671000156670010000004381000004533"
    assert nota_sem_recut.emitente.cnpj_cpf == "30367671000156"
    assert nota_sem_recut.tomador.cnpj_cpf == "02370080000100"
    assert nota_sem_recut.modal_rodoviario.placa_veiculo == "MQN2581"


def test_recorte_dedicado_real_devolve_vazio_sem_pagina_por_tras(nota_recut_real):
    """A implementação REAL de `_ocr_recut_dacte_os_grade` (não mockada) -
    contra o PDF dummy do fixture, que não é um PDF válido - levanta exceção
    dentro do próprio método e devolve "" honestamente, resultando no mesmo
    comportamento de fallback de `nota_sem_recut`."""
    assert nota_recut_real.valor_total_prestacao == 0.0
    assert any("Valor total da prestação" in a for a in nota_recut_real.avisos)


# ------------------------------------------------------------ transformer

def test_xml_e_um_cte_mod67_nao_uma_nfe_mod55(nota):
    """O XML deve se identificar como CT-e (mod=67, raiz `CTe`/`infCte`,
    namespace `.../cte`) - NUNCA como NF-e (mod=55, `NFe`/`infNFe`,
    `.../nfe`). Usar as tags de NF-e para representar um CT-e seria uma
    inverdade estrutural equivalente a fabricar dado fiscal."""
    xml = CteTransformer().transform(nota)
    assert "http://www.portalfiscal.inf.br/cte" in xml
    assert "http://www.portalfiscal.inf.br/nfe" not in xml
    assert "<mod>67</mod>" in xml
    assert "<infCte " in xml
    assert "<infNFe" not in xml


def test_xml_traz_os_valores_reais(nota):
    xml = CteTransformer().transform(nota)
    assert "<vTPrest>6739.50</vTPrest>" in xml
    assert "<vRec>6517.10</vRec>" in xml
    assert "<vINSS>222.40</vINSS>" in xml
    assert "CIATRANS POOL TRANSPORTES DE PASSAGEIROS LTDA" in xml
    assert "STAUMMAQ SERVICOS TECNICOS AUT MOT E MAQUINAS LTDA" in xml


def test_xml_traz_o_modal_rodoviario(nota):
    xml = CteTransformer().transform(nota)
    assert "<placa>MQN2581</placa>" in xml
    assert "<renavam>869471996</renavam>" in xml


# ------------------------------------------------- não colide com outros

def test_nao_colide_com_layout_simoes_filho():
    """A nota cita "Simoes Filho" como município do tomador e do emitente -
    exatamente o que capturava LAYOUT_SIMOES_FILHO antes do aperto do
    fallback solto (ver a família de achados de 2026-09-14). A detecção do
    DACTE OS vem ANTES na cadeia e intercepta primeiro."""
    ex = SPPdfExtractor.__new__(SPPdfExtractor)
    ex.raw_text = MOCK_PAGINA
    ex.from_ocr = True
    ex.layout = None
    ex.pdf_path = "x.pdf"
    assert ex._detect_layout_page(MOCK_PAGINA) != "simoes_filho_ba"


def test_nao_colide_com_danfe_produto():
    """A nota traz "CHAVE DE ACESSO" (marca genérica de qualquer documento
    nacional) mas NÃO traz "Documento Auxiliar da Nota Fiscal Eletrônica"
    nem "0-ENTRADA"/"1-SAÍDA" - não deve casar LAYOUT_DANFE_PRODUTO."""
    ex = SPPdfExtractor.__new__(SPPdfExtractor)
    ex.raw_text = MOCK_PAGINA
    ex.from_ocr = True
    ex.layout = None
    ex.pdf_path = "x.pdf"
    assert ex._detect_layout_page(MOCK_PAGINA) != "danfe_produto"
