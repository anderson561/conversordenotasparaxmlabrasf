# -*- coding: utf-8 -*-
r"""Lauro de Freitas/BA - o MESMO emitente emitindo por DOIS sistemas, e o
ruído de OCR entre as células da grade MEI/Simples.

Achado real: págs. 5 e 38 do lote `Notas_Fiscais_Recebidas_08.2026_-
_Guarajuba_Suites.pdf` - notas nº 20261879 (R$2.808,85) e nº 20261893
(R$1.500,00), ambas de TESSERA HOSPITALITY LTDA (03.814.827/0001-27) para
PH GESTAO E CONSULTORIA S.A. As duas saíam com **tudo zerado** (valor, base
e líquido em 0,00), código de verificação "A" e as duas entidades como "Não
Identificado" - apesar de o OCR da página estar impecável, com
"VALOR TOTAL DA NOTA FISCAL : R$ 2.808,85" legível no texto.

**(A) Causa-raiz - roteamento de layout.** O portão do `password_enotas`
casa pelo CNPJ do emitente e é avaliado ANTES do portão do município. O
TESSERA foi cadastrado ali a partir da nota RPS 988 de julho, que era mesmo
emitida via eNotas Gateway; estas de agosto saíram pelo sistema da PRÓPRIA
Prefeitura de Lauro de Freitas (cabeçalho "MUNICIPIO DE LAURO DE FREITAS /
Secretaria da Fazenda / Coordenação Tributária", rodapé
laurodefreitas.ba.gov.br). Um emitente, dois sistemas - a detecção por CNPJ,
escolhida justamente para não casar pela marca genérica da plataforma,
falha no sentido oposto. Corrigido com uma guarda pelo template da
Prefeitura (`_RE_MARCA_PREFEITURA_LAURO_FREITAS`) no portão do eNotas. A
nota de julho continua roteada para `password_enotas` - travado por
`test_password_enotas_tessera_hospitality_scan.py`, que segue verde.

**(B) Segundo defeito, exposto pela pág. 38.** Mesmo já com o layout certo,
a Base de Cálculo dela continuava 0,00: o OCR sujou a linha da grade
("R$.0,00 A R$ 1.500,00 e * Não" - ponto no lugar do espaço depois do "R$",
e um "A" solto entre as duas células). O padrão MEI/Simples não falhava de
forma limpa, casava ERRADO (dedução ".0,0", base "0"), produzindo um XML com
Base de Cálculo 0,00 e Valor dos Serviços R$1.500,00 - inconsistência que a
escrituração contabiliza torto. Corrigido tolerando esse ruído entre as
células.

Alíquota e ISS ficam em 0,00 nas duas notas e isso está CORRETO: são
optantes pelo Simples e a nota traz "*" nessas células (campos inutilizados
pelo art. 57 §2º I da Resolução 94 do CGSN, citado no rodapé) - conferido
contra a imagem renderizada das duas páginas.

Textos REAIS de produção, capturados via `SPPdfExtractor._ocr_page(0)` sobre
cada página recortada.
"""
import pytest
from src.extractors.pdf_extractor import (
    SPPdfExtractor, LAYOUT_LAURO_FREITAS, LAYOUT_PASSWORD_ENOTAS,
)

MOCK_OCR_PAG5 = 'MUNICIPIO DE LAURO DE FREITAS Número da Nota\n\nSecretaria da Fazenda 20261879\nCoordenação Tributária Data e Hora de Emissão\nNota Fiscal de Serviços Eletrônica - NFS-e 03/08/2026 16:46:16\nRPS Nº,1036, Série 01 |, emitida em 03/08/2026 Código de Verificação\nA autenticidade desta Nota Fiscal de Serviços Eletrônica, poderá ser confirmada na página da MUNICIPIO DE LAURO DE FREITAS na Internet, no E060574BD\nendereço http://www .laurodefreitas.ba.gov.br ou através da leitura do QR Code.\nPRESTADOR DE SERVIÇOS |\nCPF/CNPJ: 03.814.827/0001-27 Inscrição Estadual\nInscrição 0010034437\nNome/Razão TESSERA HOSPITALITY LTDA\nEndereço: AVN Avenida Santos Dumont, 1883, SALA 507 ESP AERO EMP KM 1,5\nBairro: Centro | Município: LAURO DE FREITAS UF: BA\n\nCEP: 42702-400 Email: RAFAELOINSPIREGESTAO.COM\n\nMUNICIPIO DE LAURO DE FREITAS\nSecretaria da Fazenda\nCoordenação Tributária\n\nNota Fiscal de Serviços Eletrônica - NFS-e\n\nRPS Nº.1036, Série 01 |, emitida em 03/08/2026\n\nNúmero da Nota\n20261879\nData e Hora de Emissão\n03/08/2026 16:46:16\n\nCódigo de Verificação\n\nA autenticidade desta Nota Fiscal de Serviços Eletrônica, poderá ser confirmada na página da MUNICIPIO DE LAURO DE FREITAS na Intemet, no E060574BD\n\nendereço http://www .laurodefreitas.ba.gov.br ou através da leitura do QR Code.\n\nPRESTADOR DE SERVIÇOS\nCPF/CNPJ: 03.814.827/0001-27 Inscrição Estadual\nInscrição 0010034437\n\nNome/Razão TESSERA HOSPITALITY LTDA\n\nEndereço: AVN Avenida Santos Dumont, 1883, SALA 507 ESP AERO EMP KM 1,5\nBairro: Centro Município: LAURO DE FREITAS UF: BA\nCEP: 42702-400 Email: RAFAELQINSPIREGESTAO.COM\n\nTOMADOR DE SERVIÇOS\nCPFICNPJ/CRI: 25,311.856/0001-09\n\nInscrição Inscrição Estadual:\n\nNome/Razão PH GESTAO E CONSULTORIA S.A.\n\nEndereço: HUMAITA, S/N, COND GUARAJUBA S PREMIUS\n\nBairro: GUARAJUBA (MONTE GORDO) Município: Camaçari UF: BA\n\nCEP: 42840-562 PAÍs: Email: PRISCILAGQGUARAJUBANEGOCIOS.\n\nLOCAL DA PRESTAÇÃO DO(S) SERVIÇO(S): LAURO DE FREITAS\n\nDISCRIMINAÇÃO DOS SERVIÇOS\nNFS REFERENTE A PRESTACAO DE SERVICO CONFORME CONTRATO MES E ANO DE REF. JULHO DE 2026 TESSERA HOSPITALITY\nLTDA. Trib aprox R$ 377,79 Federal, R$ 0,00 Estadual e R$ 140,44 Municipal Fonte IBPTempresometro.com.br 42CA5A\n\nVALOR TOTAL DA NOTA FISCAL : R$ 2.808,85\n\nATIVIDADE\n\n0007020400 - Atividades De Consultoria Em Gestão Empresari\nITEM DA LISTA DE SERVIÇOS: (Lei Municipal 1572/2015 )\n170201 - Datilografia, digitação, estenografia e congêneres.\n\nValor Total Deduções (R$) Base de Cálculo (R$) Alíquota (%) Valor do ISS (R$) ISSQN Retido (R$)\nR$ 0,00 R$ 2.808,85 ed * Não\nRETENÇÃO DE IMPOSTOS\n\nPIS (R$) COFINS (R$) INSS (R$) IRRF (R$): CSLL (R$): OUTRAS RETENÇÕES (R$);\n0,00 0,00 0,00 0,00 0,00\nVALOR LÍQUIDO DA NOTA FISCAL : R$ 2.808,85 :\n\nINFORMAÇÕES COMPLEMENTARES\n\nCompetência: 08/2026 - Tributado no Município de Lauro de Freitas - Não Retido\n\nNBS: 118064000 - Serviços combinados de escritório e apoio administrativo\n\nBenefício Municipal: -\n\nOptante pelo Simples Nacional - Inutilização dos campos destinados à base de cálculo e ao-imposto(art.57, 82º, | da\nResolução 94 do CGSN)\n\nAutentique\nVia QR Code\n\n'

MOCK_OCR_PAG38 = 'MUNICIPIO DE LAURO DE FREITAS\nSecretaria da Fazenda\n\nCoordenação Tributária\n\nRPS Nº,1050, Série 01 |, emitida em 03/08/2026\n\nendereço http://www .laurodefreitas.ba.gov.br ou através da leitura do QR Code.\n\nNota Fiscal de Serviços Eletrônica - NFS-e\n\nA autenticidade desta Nota Fiscal de Serviços Eletrônica, poderá ser confirmada na página da MUNICIPIO DE LAURO DE FREITAS na Intemet, no\n\nNúmero da Nota\n20261893\n\nData e Hora de Emissão\n\n03/08/2026 21:04:13\n\nCódigo de Verificação\nEF4DF3F5E\n\nPRESTADOR DE SERVIÇOS\n\nCPF/CNPJ: 03.814.827/0001-27 Inscrição Estadual\n\nInscrição * 0010034437\n\nNome/Razão TESSERA HOSPITALITY LTDA\n\nEndereço: AVN Avenida Santos Dumont, 1883, SALA 507 ESP AERO EMP KM 1,5\n\nBairro: Centro : Município: LAURO DE FREITAS UF: BA\n\nCEP: 42702-400\n\nEmail: RAFAELQINSPIREGESTAO.COM\n\nMUNICIPIO DE LAURO DE FREITAS\nSecretaria da Fazenda\nCoordenação Tributária\n\nNota Fiscal de Serviços Eletrônica - NFS-e\n\nRPS Nº.1050, Série 01 |, emitida em 03/08/2026\n\nNúmero da Nota\n20261893\nData e Hora de Emissão\n03/08/2026 21:04:13\n\nCódigo de Verificação\n\nA autenticidade desta Nota Fiscal de Serviços Eletrônica, poderá ser confirmada na página da MUNICIPIO DE LAURO DE FREITAS na Intemet, no EF4DF3F5E\n\nendereço http://www. laurodefreitas.ba.gov.br ou através da leitura do QR Code.\n\nPRESTADOR DE SERVIÇOS\nCPF/CNPJ: 03.814.827/0001-27 Inscrição Estadual\nInscrição 0010034437\n\nNome/Razão TESSERA HOSPITALITY LTDA\n\nEndereço: AVN Avenida Santos Dumont, 1883, SALA 507 ESP AERO EMP KM 1,5\nBairro: Centro Município: LAURO DE FREITAS UF: BA\nCEP: 42702-400 Email: RAFAELQINSPIREGESTAO.COM\n\nTOMADOR DE SERVIÇOS\nCPFICNPJ/CRI: 25,311.856/0001-09\nInscrição é Inscrição Estadual:\nNome/Razão PH GESTAO E CONSULTORIA S.A.\n\nEndereço: HUMAITA, S/N, COND GUARAJUBA S PREMIUS\n\nBairro: GUARAJUBA (MONTE GORDO) Município: Camaçari UF: BA\n\n(o) 42840-562 PAÍS: Email: PRISCILAQGUARAJUBANEGOCIOS.\n\nEP.\nLOCAL DA PRESTAÇÃO DO(S) SERVIÇO(S): LAURO DE FREITAS\n\nDISCRIMINAÇÃO DOS SERVIÇOS\n\nReferente a fase inicial de conversao. Parcela 01. Trib aprox R$ 201,75 Federal, R$ 0,00 Estadual e R$ 75,00 Municipal Fonte\nIBPTempresometro.com.br 42CA5SA a\n\nVALOR TOTAL DA NOTA FISCAL : R$ 1.500,00\n\nATIVIDADE\n\n0007020400 - Atividades De Consultoria Em Gestão Empresari\nITEM DA LISTA DE SERVIÇOS: (Lei Municipal 1572/2015 )\n170201 - Datilografia, digitação, estenografia e congêneres.\n\nValor Total Deduções (R$) Base de Cálculo (R$) Alíquota (%) Valor do ISS (R$) ISSQN Retido (R$)\nR$.0,00 A R$ 1.500,00 e * Não\nRETENÇÃO DE IMPOSTOS di\nPIS (R$) “| COFINS (R$) INSS (R$) IRRF (R$): CSLL (R$): OUTRAS RETENÇÕE:\n0,00 7: E ora =: 0,00 0,00 0,00 0,00\nVALOR LÍQUIDO DA NOTA FISCAL : R$ 1.500,00 a\n\nINFORMAÇÕES COMPLEMENTARES\nCompetência: 08/2026 - Tributado no Município de Lauro de Freitas - Não Retido\nMotivo: Cliente desistiu do serviço. - Data: 06/08/2026 NBS: 118064000 - Serviços combinados de escritório e apoio administrativo\n\nOptante pelo Simples Nacional - Inutilização dos campos destinados à base de cálculo e ao imposto(art.57, 82º, Ida\nResolução 94 do CGSN)\n\nAutentique\nVia QR Code\n\n'


def _nota(monkeypatch, tmp_path, mock, nome):
    dummy = tmp_path / nome
    dummy.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: mock)
    notas = SPPdfExtractor(str(dummy)).parse_multiple()
    assert len(notas) == 1
    return notas[0]


@pytest.fixture
def nfse_20261879(monkeypatch, tmp_path):
    return _nota(monkeypatch, tmp_path, MOCK_OCR_PAG5, "dummy_lf_20261879.pdf")


@pytest.fixture
def nfse_20261893(monkeypatch, tmp_path):
    return _nota(monkeypatch, tmp_path, MOCK_OCR_PAG38, "dummy_lf_20261893.pdf")


# --------------------------------------------------------------------------
# (A) roteamento de layout
# --------------------------------------------------------------------------

@pytest.mark.parametrize("mock", [MOCK_OCR_PAG5, MOCK_OCR_PAG38])
def test_template_da_prefeitura_vence_o_cnpj_do_emitente(mock, tmp_path):
    """O CNPJ do TESSERA está no texto e casaria o portão do eNotas; o
    template da Prefeitura tem de prevalecer."""
    dummy = tmp_path / "dummy_lf_layout.pdf"
    dummy.write_bytes(b"%PDF-1.4")
    ex = SPPdfExtractor(str(dummy))
    ex.from_ocr = True
    assert "03.814.827/0001-27" in mock          # o gatilho do eNotas está presente
    assert ex._detect_layout_page(mock) == LAYOUT_LAURO_FREITAS
    ex.raw_text = mock
    assert ex._detect_layout() == LAYOUT_LAURO_FREITAS
    assert ex._detect_layout() != LAYOUT_PASSWORD_ENOTAS


# --------------------------------------------------------------------------
# nota nº 20261879 (pág. 5) - R$ 2.808,85
# --------------------------------------------------------------------------

def test_20261879_valor_nao_sai_zerado(nfse_20261879):
    v = nfse_20261879.valores
    # Antes: 0,00 nos três, com o valor legível no texto o tempo todo.
    assert v.valor_servicos == 2808.85
    assert v.base_calculo == 2808.85
    assert v.valor_liquido_nfse == 2808.85


def test_20261879_identificacao(nfse_20261879):
    n = nfse_20261879
    assert n.numero == "20261879"
    assert n.codigo_verificacao == "E060574BD"   # antes: "A"
    assert n.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "03/08/2026 16:46:16"


def test_20261879_entidades(nfse_20261879):
    n = nfse_20261879
    # Antes: "Prestador Não Identificado" / "Tomador Não Identificado".
    assert n.prestador.razao_social == "TESSERA HOSPITALITY LTDA"
    assert n.prestador.cnpj_cpf == "03814827000127"
    assert n.tomador.razao_social == "PH GESTAO E CONSULTORIA S.A."
    assert n.tomador.cnpj_cpf == "25311856000109"


def test_20261879_simples_nacional_nao_fabrica_aliquota_nem_iss(nfse_20261879):
    """A nota traz "*" nessas 2 células (campos inutilizados pelo Simples) -
    0,00 aqui é a face do documento, não leitura falha."""
    v = nfse_20261879.valores
    assert v.aliquota == 0.0
    assert v.valor_iss == 0.0
    assert v.iss_retido is False


def test_20261879_sem_avisos(nfse_20261879):
    # Antes: 'Valor dos serviços extraído como zero' e 'Dados do tomador
    # não identificados'.
    assert nfse_20261879.avisos == []


# --------------------------------------------------------------------------
# nota nº 20261893 (pág. 38) - R$ 1.500,00, com o ruído na grade
# --------------------------------------------------------------------------

def test_20261893_base_de_calculo_sobrevive_ao_ruido_de_ocr(nfse_20261893):
    """A linha sai como "R$.0,00 A R$ 1.500,00 e * Não". Antes, o padrão
    casava errado e devolvia base "0" ao lado de um valor de R$1.500,00."""
    assert "R$.0,00 A R$ 1.500,00" in MOCK_OCR_PAG38   # o ruído continua no texto
    v = nfse_20261893.valores
    assert v.valor_servicos == 1500.00
    assert v.base_calculo == 1500.00
    assert v.valor_liquido_nfse == 1500.00
    assert v.valor_deducoes == 0.00


def test_20261893_identificacao_e_entidades(nfse_20261893):
    n = nfse_20261893
    assert n.numero == "20261893"
    assert n.codigo_verificacao == "EF4DF3F5E"
    assert n.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "03/08/2026 21:04:13"
    assert n.prestador.razao_social == "TESSERA HOSPITALITY LTDA"
    assert n.tomador.cnpj_cpf == "25311856000109"


def test_20261893_e_cancelada_valores_continuam_reais_mas_com_aviso(nfse_20261893):
    """A nota traz uma marca d'água diagonal "CANCELADA" (que não sobrevive
    ao OCR - conferido: zero ocorrências de "CANCELAD" neste próprio texto)
    e a linha "Motivo: Cliente desistiu do serviço. - Data: 06/08/2026",
    essa sim legível. Corrigir a extração por si só faria a nota sair com
    R$1.500,00 pleno e SEM nenhum aviso - pior do que o zero+aviso de antes,
    porque um valor plausível passa despercebido na conferência mais
    facilmente que um zero. O documento continua fiscalmente legível (os
    valores não são fabricados), mas precisa de um aviso explícito para não
    ser escriturado sem revisão."""
    assert "CANCELAD" not in MOCK_OCR_PAG38            # a marca d'água não sobrevive ao OCR
    assert "Motivo: Cliente desistiu" in MOCK_OCR_PAG38  # o sinal real está aqui
    v = nfse_20261893.valores
    assert v.valor_servicos == 1500.00                 # não fabricado/zerado por causa do cancelamento
    assert any("CANCELAMENTO" in a for a in nfse_20261893.avisos)


def test_20261879_nao_e_cancelada_sem_aviso_falso_positivo(nfse_20261879):
    """A pág. 5 (mesmo emitente, mês diferente) é uma nota válida - garante
    que o padrão de cancelamento não dispara por acaso em texto comum."""
    assert "Motivo" not in MOCK_OCR_PAG5
    assert "CANCELAD" not in MOCK_OCR_PAG5
    assert not any("CANCELAMENTO" in a for a in nfse_20261879.avisos)
