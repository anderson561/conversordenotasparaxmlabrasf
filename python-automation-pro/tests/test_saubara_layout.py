# -*- coding: utf-8 -*-
r"""Novo layout: Saubara/BA (`saubara_ba` e `saubara_ba_2`), NFS-e da Prefeitura
Municipal de Saubara (plataforma Link3 Tecnologia), PDF DIGITAL (texto
embutido, sem OCR). Antes deste layout NENHUMA das duas notas tinha layout
reconhecido: caíam em LAYOUT_GENERICO, eram descartadas como "Layout não
reconhecido" e a conversão terminava sem XML, com a mensagem enganosa "parece
ser baseado em imagem/scan ou vazio".

Dois TEMPLATES diferentes (por isso dois layouts), ambos de "ESCUTA" (prestadores
diferentes) emitidos em 14/09/2026:

  1. `saubara_ba` - "Nota Fiscal Eletrônica de Serviços", blocos "DADOS DO
     EMITENTE"/"DADOS DO DESTINATÁRIO", grade de valores no rodapé. Nota
     202600000000351 (ASSOCIAÇÃO RELIOGIOSA E CULTURAL BABÁ OKÉ -> TEMIS
     Projetos de Meio Ambiente e Sustentabilidade, R$ 1.600,00, ISS 3%).
     Não imprime CEP nem competência.
  2. `saubara_ba_2` - "NOTA FISCAL ELETRÔNICA DE SERVIÇOS - NFS-e", blocos
     "PRESTADOR DE SERVIÇOS"/"TOMADOR DE SERVIÇOS", código IBGE impresso, CNAE,
     item LC 116, regime especial. Nota 202600000000080 (VIVA COMUNICAÇAO E
     SERVIÇOS LTDA -> TEMIS, R$ 120,00, ISS 2%, Simples/Microempresa Municipal).

Os textos abaixo são o `pdfminer.extract_text()` REAL dos dois PDFs, preservados
verbatim, inclusive os quirks que travam regressões:
  - rótulo e valor em linhas separadas e ordem de leitura que depende da
    geometria da caixa (na variante 1 o "Estado"/"Data Emissão"/"Bairro" do
    destinatário saem DEPOIS do cabeçalho "ITENS DOS SERVIÇOS"; na variante 2 as
    colunas da direita do prestador saem depois do cabeçalho "TOMADOR DE
    SERVIÇOS" e o telefone vem em 2 células "071" + "981235905");
  - o CNPJ do CABEÇALHO (13.040.233/0001-60) é o da PREFEITURA, nunca o do
    prestador/tomador;
  - o carimbo "14/09/2026 15:49:24 - MAURA R. XAVIER ROCHA" / "14/09/2026
    11:25:46" no topo é de impressão, não a emissão;
  - "99.99 Outros Serviços" (variante 1) não é item da LC 116.
"""
import os

import pytest

from src.extractors import saubara_nfse as sn
from src.extractors.pdf_extractor import (
    LAYOUT_GENERICO, LAYOUT_SAUBARA, LAYOUT_SAUBARA_2, SPPdfExtractor, _ibge_resolver,
)
from src.transformers.abrasf_transformer import Abrasf201Transformer

MOCK_LANCHE = 'ESTADO DA BAHIA\nMUNICIPIO DE SAUBARA\nSecretaria Municipal de Administração\nCNPJ: 13040233000160\n\n14/09/2026 15:49:24 - MAURA R.  XAVIER ROCHA\n\nNÚMERO DA NOTA\n202600000000351\n\nCódigo de Verificação:\nANJAWMZUX\n\nNota Fiscal Eletrônica de Serviços\n\nDADOS DO EMITENTE\n\nNome\n\nASSOCIAÇÃO RELIOGIOSA E CULTURAL BABÁ OKÉ\n\nEndereço\nRUA DA PAZ  33,  ENTIDADE RELIGIOSA\n\nNatureza da Operação\nServiços\n\nBairro\nBOM JESUS DOS POBRES\n\nMunicipio\nSaubara\n\nCNPJ / CPF\n\n07.165.195/0001-79\n\nNome\n\nTEMIS Projetos de Meio Ambiente e Sustentabilidade\nEndereço\n\nRUA Território do Amapá 146,\nMunicipio\n\nSalvador\n\nCNPJ / CPF\n07.345.543/0001-90\n\nRG\n\n*\n\nDADOS DO DESTINATÁRIO\n\nRG\n\n069.725.483\n\nITENS DOS SERVIÇOS\n\nEstado\nBAHIA\n\nData Emissão\n14/09/2026\n\nBairro\n\nPituba\nEstado\nBAHIA\n\nCod\n\n99.99 Outros Serviços\n\nDescrição\n\nUN\n\nUN\n\nQTD\n1.0\n\nValor\n\n1.600,00\n\nValor Total\n1.600,00\n\nValor Total da Nota (R$):\n\n1.600,00\n\nBase de Cálculo da Nota:\n\n1.600,00\n\nDeduções:\n\n0,00\n\nvalor ISS:\n\n48,00\n\nISS Retido:\n\nNão\n\nAliq. Iss:\n\n3\n\n%\n\nValor IRRF:\n\n0,00\n\nValor INSS:\n\n0,00\n\nValor Liquido da Nota (R$):\n\n1.600,00\n\nServiços prestado com mobilização dos comunidades de terreiros de Bom Jesus dos Pobres  na organização e divulgação da Escuta social em parceria\ncom a TEMIS projeto e Meio ambiente  e Sustentabilidade.Prestando apoio logístico com objetivo de garantir a participação  da comunidade efetiva e o\ncomprimento do cronograma estabelecido.\n\nLink3 Tecnologia Ltda\n\n\x0c'
MOCK_COMUN = 'ESTADO DA BAHIA\nMUNICIPIO DE SAUBARA\nSecretaria Municipal de Administração e da Fazenda\nRUA ANANIAS REQUIÃO , 08 PREDIO  - CENTRO  - 44.220-000\nCNPJ: 13.040.233/0001-60\n\nNOTA FISCAL ELETRÔNICA DE SERVIÇOS - NFS-e\n\nPRESTADOR DE SERVIÇOS\nNOME/RAZÃO SOCIAL\nVIVA COMUNICAÇAO E SERVIÇOS LTDA\n\nNOME FANTASIA\nVIVA COMUNICAÇAO\n\nCNPJ/CPF\n52410209000127\n\nENDEREÇO\nRUA SANTO  ANTONIO , 14-A\n\nE-MAIL\nvivacomunicacao.oficial@gmail.com\n\nTOMADOR DE SERVIÇOS\nNOME/RAZÃO SOCIAL\nTEMIS Projetos de Meio Ambiente e Sustentabilidade\n\nUF\n\nBA\n\nCIDADE  -\n\n2929750\n\nSaubara\n\nBAIRRO\n\nCENTRO\n\nCEP\n\n44220000\n\nCOMPLEMENTO\n\nTELEFONE\n071\n\n981235905\n\nNOME FANTASIA\n\nENDEREÇO\n\nRUA Território do Amapá, 146\nE-MAIL\nkellyfontoura@temis-es.com.br\n\nINSC. ESTADUAL\n069.725.483\n\nTELEFONE\n71\n\n982791844\n\n14/09/2026 11:25:46\n\nNÚMERO DA NOTA\n202600000000080\nDATA E HORA DA EMISSÃO\n14/09/2026\n\nCÓDIGO DE VERIFICAÇÃO\nANJGWNTI0\n\nCOD. MUNICIPIO GERADOR\n2929750BA\n\nINSCRIÇÃO MUNICIPAL\n900337\n\nCNPJ/CPF\n\n07345543000190\n\nCEP\n\n41830540\n\nUF\n\nBA\n\nBAIRRO\n\nPituba\n\nCIDADE  - 2927408\nSalvador\n\nDISCRIMINAÇÃO DOS SERVIÇOS\n\nServiço de gravação de dois (02) spot institucional, realizados durante o mês de Setembro de 2026, para divulgação da Escuta Social sobre as atividades do Canteiro de Obras de São Roque do\nParaguaçu, no distrito de Bom Jesus dos Pobres. Serviço prestado para TEMIS Projetos de Meio Ambiente e Sustentabilidade – CNPJ nº 07.345.543/0001-90.\n\nDados para pagamento: Chave PIX (CNPJ): 52410209000127 | Favorecido: Viva Comunicação e Serviços | Banco: Banco do Brasil.\n\nCÓDIGO CNAE\n7319099\n\nDESCRIÇÃO CNAE\nOutras atividades de publicidade não especificadas anteriormente\n\nCODIGO / DESCRIÇÃO DO NBS\n1.1406.19.00 - Serviços de propaganda não classificados em subposições anteriores\n\nCODIGO / DESCRIÇÃO DO SERVIÇO LC 116/2003\n17.06 - Propaganda e publicidade, inclusive promoção de vendas, planejamento de campanhas ou sistemas de publicidade, elaboração de desenhos, textos e demais\nmateriais publicitários.\n\nVALOR TOTAL DO(S) SERVIÇO(S) (R$)\n\n120,00\n\nPIS (R$)\n\nCOFINS (R$)\n\nINSS (R$)\n\n0,00\n\n0,00\n\n0,00\n\nIR (R$)\n\n0,00\n\nCSLL (R$)\n\n0,00\n\nDeduções (R$)\n\nBase Cálculo (R$)\n\nAlíquota (%)\n\nISS (R$)\n\nRetenção ISS\n\nOutras Retenções (R$)\n\nValor Líquido (R$)\n\n0,00\n\n120,00\n\n2,00\n\n2,40\n\nNão\n\n0,00\n\n120,00\n\nTributação:\n\nIss Devido no Municipio de Saubara\n\nINFORMAÇÕES FISCAIS\nRegime Tributação Especial\n\nMicroempresa Municipal\n\n EMPRESA OPTANTE DO SIMPLES\n\nOUTRAS INFORMAÇÕES\nA autenticidade desta NFS-e esta sujeita a verificação.\n\nLink3 Tecnologia Ltda\n\nOperador da Empresa: VIVA COMUNICAÇAO E SERVIÇOS LTDA\n\nPágina 1 de 1\n\n\x0c'


# ---------------------------------------------------------------------------
# Infra
# ---------------------------------------------------------------------------

def _extractor(tmp_path, texto, nome="nota.pdf"):
    pdf = tmp_path / nome
    pdf.write_bytes(b"%PDF-1.4")
    ex = SPPdfExtractor(str(pdf))
    ex.raw_text = texto
    return ex


def _converter(monkeypatch, tmp_path, texto, nome="nota.pdf"):
    """Roda o caminho real de conversão (`parse_multiple`) sobre `texto`."""
    pdf = tmp_path / nome
    pdf.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: texto)
    return SPPdfExtractor(str(pdf)).parse_multiple()


def _uma_nota(monkeypatch, tmp_path, texto, nome="nota.pdf"):
    notas = _converter(monkeypatch, tmp_path, texto, nome)
    assert len(notas) == 1
    return notas[0]


# ---------------------------------------------------------------------------
# Detecção
# ---------------------------------------------------------------------------

def test_detecta_variante_1(tmp_path):
    ex = _extractor(tmp_path, MOCK_LANCHE)
    assert ex._detect_layout() == LAYOUT_SAUBARA
    assert ex._detect_layout_page(MOCK_LANCHE) == LAYOUT_SAUBARA
    assert sn.variante(MOCK_LANCHE) == sn.VARIANTE_1


def test_detecta_variante_2(tmp_path):
    ex = _extractor(tmp_path, MOCK_COMUN)
    assert ex._detect_layout() == LAYOUT_SAUBARA_2
    assert ex._detect_layout_page(MOCK_COMUN) == LAYOUT_SAUBARA_2
    assert sn.variante(MOCK_COMUN) == sn.VARIANTE_2


def test_dois_templates_sao_layouts_distintos():
    assert LAYOUT_SAUBARA != LAYOUT_SAUBARA_2
    assert sn.variante(MOCK_LANCHE) != sn.variante(MOCK_COMUN)


# NFS-e de OUTRO município que só CITA Saubara (endereço de prestador/tomador,
# local da obra): a palavra solta nunca pode virar o layout de Saubara.
TEXTO_CAMACARI_CITANDO_SAUBARA = (
    "PREFEITURA MUNICIPAL DE CAMAÇARI\nSecretaria da Fazenda\n"
    "Nota Fiscal Eletrônica de Serviços\nNúmero da Nota\n4495\n\n"
    "PRESTADOR DE SERVIÇOS\nNome/Razão Social: ALFA SERVICOS LTDA\n"
    "CNPJ: 11.222.333/0001-81\nEndereço: RUA DA PAZ 33, BOM JESUS DOS POBRES\n"
    "Município: Saubara  UF: BA\n\n"
    "TOMADOR DE SERVIÇOS\nNome/Razão Social: BETA LTDA\nMunicípio: SAUBARA\n"
    "Discriminação: serviço executado no MUNICIPIO DE SAUBARA, obra da Secretaria "
    "Municipal de Administração.\n"
)


def test_nfse_de_outro_municipio_que_cita_saubara_nao_vira_layout_saubara(tmp_path):
    ex = _extractor(tmp_path, TEXTO_CAMACARI_CITANDO_SAUBARA)
    assert ex._detect_layout() not in (LAYOUT_SAUBARA, LAYOUT_SAUBARA_2)
    assert ex._detect_layout_page(TEXTO_CAMACARI_CITANDO_SAUBARA) not in (LAYOUT_SAUBARA, LAYOUT_SAUBARA_2)
    assert sn.variante(TEXTO_CAMACARI_CITANDO_SAUBARA) is None


def test_municipio_de_saubara_em_linha_propria_sem_o_cabecalho_estadual_nao_conta():
    # Mesmo com CNPJ da prefeitura e título, "MUNICIPIO DE SAUBARA" solto (por
    # exemplo um campo "Local da prestação" de nota alheia) sem "ESTADO DA BAHIA"
    # logo acima não é o cabeçalho da prefeitura.
    texto = ("PREFEITURA MUNICIPAL DE CAMAÇARI\nNota Fiscal Eletrônica de Serviços\n"
             "Local da prestação:\nMUNICIPIO DE SAUBARA\nCNPJ: 13040233000160\n"
             "Secretaria Municipal de Administração\nDADOS DO EMITENTE\n")
    assert sn.variante(texto) is None


def test_cabecalho_de_saubara_no_meio_do_texto_nao_conta():
    # "MUNICIPIO DE SAUBARA" + título + Secretaria, mas muito depois do início
    # do texto (citado dentro de uma nota alheia): não é o cabeçalho.
    texto = ("PREFEITURA MUNICIPAL DE OUTRA CIDADE\n" + "linha de enchimento\n" * 60
             + "ESTADO DA BAHIA\nMUNICIPIO DE SAUBARA\nSecretaria Municipal de Administração\n"
             "CNPJ: 13040233000160\nNota Fiscal Eletrônica de Serviços\nDADOS DO EMITENTE\n")
    assert sn.variante(texto) is None


def test_cabecalho_sem_cnpj_nem_secretaria_da_prefeitura_nao_conta():
    texto = "ESTADO DA BAHIA\nMUNICIPIO DE SAUBARA\nNota Fiscal Eletrônica de Serviços\nDADOS DO EMITENTE\n"
    assert sn.variante(texto) is None


def test_cabecalho_sem_titulo_da_nfse_nao_conta():
    texto = ("ESTADO DA BAHIA\nMUNICIPIO DE SAUBARA\nSecretaria Municipal de Administração\n"
             "CNPJ: 13040233000160\nDADOS DO EMITENTE\n")
    assert sn.variante(texto) is None


def test_cabecalho_de_saubara_com_template_desconhecido_nao_e_adivinhado():
    # Sem "DADOS DO EMITENTE" nem "PRESTADOR DE SERVIÇOS": template novo. Melhor
    # "Layout não reconhecido" (ruidoso) do que ler campos pelo template errado.
    texto = ("ESTADO DA BAHIA\nMUNICIPIO DE SAUBARA\nSecretaria Municipal de Administração\n"
             "CNPJ: 13040233000160\nNota Fiscal Eletrônica de Serviços\nOUTRO BLOCO\n")
    assert sn.variante(texto) is None


# ---------------------------------------------------------------------------
# Variante 1 - nota 202600000000351
# ---------------------------------------------------------------------------

def test_variante_1_campos_completos(monkeypatch, tmp_path):
    nfse = _uma_nota(monkeypatch, tmp_path, MOCK_LANCHE)

    assert nfse.numero == "202600000000351"
    assert nfse.codigo_verificacao == "ANJAWMZUX"
    # Só a data rotulada "Data Emissão"; o carimbo do topo (15:49:24) é de impressão.
    assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "14/09/2026 00:00:00"
    # O template não imprime competência: mês da emissão.
    assert nfse.competencia.strftime("%d/%m/%Y") == "01/09/2026"
    # "99.99 Outros Serviços" não é item da LC 116 -> "0000" + aviso.
    assert nfse.servico_codigo == "0000"
    assert nfse.codigo_cnae is None
    assert nfse.optante_simples_nacional is False
    assert nfse.regime_especial_tributacao is None
    assert nfse.intermediario is None
    assert nfse.municipio_incidencia_override is None

    p = nfse.prestador
    assert p.cnpj_cpf == "07165195000179"
    assert p.razao_social == "ASSOCIAÇÃO RELIOGIOSA E CULTURAL BABÁ OKÉ"
    assert p.inscricao_municipal is None
    assert p.endereco.logradouro == "RUA DA PAZ"
    assert p.endereco.numero == "33"
    assert p.endereco.complemento == "ENTIDADE RELIGIOSA"
    assert p.endereco.bairro == "BOM JESUS DOS POBRES"
    assert p.endereco.municipio == "Saubara"
    assert p.endereco.codigo_municipio == "2929750"
    assert p.endereco.uf == "BA"
    assert p.endereco.cep == "00000000"  # não impresso neste template

    t = nfse.tomador
    assert t.cnpj_cpf == "07345543000190"
    assert t.razao_social == "TEMIS Projetos de Meio Ambiente e Sustentabilidade"
    assert t.endereco.logradouro == "RUA Território do Amapá"
    assert t.endereco.numero == "146"
    assert t.endereco.bairro == "Pituba"
    assert t.endereco.municipio == "Salvador"
    assert t.endereco.codigo_municipio == "2927408"
    assert t.endereco.uf == "BA"
    assert t.endereco.cep == "00000000"

    # O CNPJ do cabeçalho (13.040.233/0001-60) é o da PREFEITURA.
    assert "13040233000160" not in (p.cnpj_cpf, t.cnpj_cpf)
    assert p.cnpj_cpf != t.cnpj_cpf

    v = nfse.valores
    assert v.valor_servicos == pytest.approx(1600.00)
    assert v.valor_deducoes == pytest.approx(0.0)
    assert v.base_calculo == pytest.approx(1600.00)
    assert v.aliquota == pytest.approx(0.03)
    assert v.valor_iss == pytest.approx(48.00)
    assert v.iss_retido is False
    assert v.valor_iss_retido == pytest.approx(0.0)
    assert v.valor_ir == pytest.approx(0.0)
    assert v.valor_inss == pytest.approx(0.0)
    assert v.valor_liquido_nfse == pytest.approx(1600.00)

    assert nfse.discriminacao.startswith("Serviços prestado com mobilização dos comunidades de terreiros")
    assert nfse.discriminacao.endswith("o comprimento do cronograma estabelecido.")
    assert "Link3" not in nfse.discriminacao
    assert "\n" not in nfse.discriminacao

    # Avisos: o CEP e o item 99.99 (e só eles) - nada silencioso.
    assert len(nfse.avisos) == 2
    assert any("CEP" in a and "não são impressos" in a for a in nfse.avisos)
    assert any("99.99" in a and "LC 116" in a for a in nfse.avisos)


# ---------------------------------------------------------------------------
# Variante 2 - nota 202600000000080
# ---------------------------------------------------------------------------

def test_variante_2_campos_completos(monkeypatch, tmp_path):
    nfse = _uma_nota(monkeypatch, tmp_path, MOCK_COMUN)

    assert nfse.numero == "202600000000080"
    assert nfse.codigo_verificacao == "ANJGWNTI0"
    assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "14/09/2026 00:00:00"
    assert nfse.competencia.strftime("%d/%m/%Y") == "01/09/2026"
    assert nfse.servico_codigo == "1706"
    assert nfse.codigo_cnae == "7319099"
    assert nfse.optante_simples_nacional is True
    assert nfse.regime_especial_tributacao == "1"  # "Microempresa Municipal" (ABRASF 1)
    assert nfse.intermediario is None
    assert nfse.municipio_incidencia_override is None

    p = nfse.prestador
    assert p.cnpj_cpf == "52410209000127"
    assert p.razao_social == "VIVA COMUNICAÇAO E SERVIÇOS LTDA"
    assert p.inscricao_municipal == "900337"
    assert p.endereco.logradouro == "RUA SANTO ANTONIO"
    assert p.endereco.numero == "14-A"
    assert p.endereco.bairro == "CENTRO"
    assert p.endereco.municipio == "Saubara"
    assert p.endereco.codigo_municipio == "2929750"
    assert p.endereco.uf == "BA"
    assert p.endereco.cep == "44220000"
    assert p.email == "vivacomunicacao.oficial@gmail.com"
    assert p.telefone == "71981235905"  # "071" + "981235905": o 0 é prefixo de discagem

    t = nfse.tomador
    assert t.cnpj_cpf == "07345543000190"
    assert t.razao_social == "TEMIS Projetos de Meio Ambiente e Sustentabilidade"
    # "INSC. ESTADUAL 069.725.483" é do tomador e NÃO é inscrição municipal.
    assert t.inscricao_municipal is None
    assert t.endereco.logradouro == "RUA Território do Amapá"
    assert t.endereco.numero == "146"
    assert t.endereco.bairro == "Pituba"
    assert t.endereco.municipio == "Salvador"
    assert t.endereco.codigo_municipio == "2927408"
    assert t.endereco.uf == "BA"
    assert t.endereco.cep == "41830540"
    assert t.email == "kellyfontoura@temis-es.com.br"
    assert t.telefone == "71982791844"

    assert "13040233000160" not in (p.cnpj_cpf, t.cnpj_cpf)

    v = nfse.valores
    assert v.valor_servicos == pytest.approx(120.00)
    assert v.valor_deducoes == pytest.approx(0.0)
    assert v.base_calculo == pytest.approx(120.00)
    assert v.aliquota == pytest.approx(0.02)
    assert v.valor_iss == pytest.approx(2.40)
    assert v.iss_retido is False
    assert v.valor_iss_retido == pytest.approx(0.0)
    assert v.valor_pis == v.valor_cofins == v.valor_inss == v.valor_ir == v.valor_csll == 0.0
    assert v.outras_retencoes == pytest.approx(0.0)
    assert v.valor_liquido_nfse == pytest.approx(120.00)

    assert nfse.discriminacao.startswith("Serviço de gravação de dois (02) spot institucional")
    assert "Dados para pagamento: Chave PIX (CNPJ): 52410209000127" in nfse.discriminacao
    assert "CÓDIGO CNAE" not in nfse.discriminacao

    # Nota limpa e completa: nenhum aviso.
    assert nfse.avisos == []


def test_xml_final_das_duas_notas(monkeypatch, tmp_path):
    tr = Abrasf201Transformer()
    xml1 = tr.transform(_uma_nota(monkeypatch, tmp_path, MOCK_LANCHE))
    assert "<Numero>202600000000351</Numero>" in xml1
    assert 'Id="NFSe202600000000351"' in xml1
    assert "<CodigoMunicipio>2929750</CodigoMunicipio>" in xml1  # OrgaoGerador/incidência = Saubara
    assert "<Aliquota>0.03</Aliquota>" in xml1
    assert "<ValorIss>48.00</ValorIss>" in xml1
    assert "<IssRetido>2</IssRetido>" in xml1
    assert "<ItemListaServico>0000</ItemListaServico>" in xml1
    assert "<OptanteSimplesNacional>2</OptanteSimplesNacional>" in xml1

    xml2 = tr.transform(_uma_nota(monkeypatch, tmp_path, MOCK_COMUN))
    assert "<Numero>202600000000080</Numero>" in xml2
    assert "<RegimeEspecialTributacao>1</RegimeEspecialTributacao>" in xml2
    assert "<ItemListaServico>1706</ItemListaServico>" in xml2
    assert "<CodigoCnae>7319099</CodigoCnae>" in xml2
    assert "<OptanteSimplesNacional>1</OptanteSimplesNacional>" in xml2
    assert "<Telefone>71981235905</Telefone>" in xml2


def test_lote_com_as_duas_variantes_gera_duas_notas(monkeypatch, tmp_path):
    """Uma nota por página, cada uma pelo seu template, sem se contaminarem."""
    notas = _converter(monkeypatch, tmp_path, MOCK_LANCHE + MOCK_COMUN)
    assert [n.numero for n in notas] == ["202600000000351", "202600000000080"]
    assert [n.prestador.cnpj_cpf for n in notas] == ["07165195000179", "52410209000127"]
    assert [n.valores.valor_servicos for n in notas] == [pytest.approx(1600.0), pytest.approx(120.0)]


def test_iss_impresso_bate_com_base_x_aliquota_nas_duas_notas(monkeypatch, tmp_path):
    for texto in (MOCK_LANCHE, MOCK_COMUN):
        v = _uma_nota(monkeypatch, tmp_path, texto).valores
        assert v.valor_iss == pytest.approx(round(v.base_calculo * v.aliquota, 2))


# ---------------------------------------------------------------------------
# IBGE
# ---------------------------------------------------------------------------

def test_saubara_esta_na_tabela_ibge():
    # 2929750 conferido na API oficial do IBGE (municipios/2929750 -> "Saubara", BA).
    assert _ibge_resolver.extract_and_validate("Saubara", "BA", city_hint="Saubara") == "2929750"
    assert sn.COD_IBGE_SAUBARA == "2929750"


# ---------------------------------------------------------------------------
# Casos degradados / variações que a amostra não cobre
# ---------------------------------------------------------------------------

def test_variante_1_sem_numero_vira_sentinela_e_nunca_vem_do_nome_do_arquivo(monkeypatch, tmp_path):
    texto = MOCK_LANCHE.replace("NÚMERO DA NOTA\n202600000000351\n", "NÚMERO DA NOTA\n")
    assert texto != MOCK_LANCHE
    nfse = _uma_nota(monkeypatch, tmp_path, texto, nome="NF 351 ESCUTA.pdf")
    assert nfse.numero == "00000000"
    assert "Número da nota não encontrado" in nfse.avisos


def test_variante_1_sem_codigo_de_verificacao_vira_sentinela(monkeypatch, tmp_path):
    texto = MOCK_LANCHE.replace("Código de Verificação:\nANJAWMZUX\n", "Código de Verificação:\n")
    nfse = _uma_nota(monkeypatch, tmp_path, texto)
    assert nfse.codigo_verificacao == "XXXX-XXXX"
    assert "Código de verificação/autenticidade não encontrado" in nfse.avisos


def test_variante_1_sem_data_emissao_usa_aviso_e_nao_o_carimbo_do_topo(monkeypatch, tmp_path):
    texto = MOCK_LANCHE.replace("Data Emissão\n14/09/2026\n", "Data Emissão\n")
    assert texto != MOCK_LANCHE
    nfse = _uma_nota(monkeypatch, tmp_path, texto)
    assert nfse.data_emissao.strftime("%d/%m/%Y") != "14/09/2026" or any(
        "Data de emissão não encontrada" in a for a in nfse.avisos)
    assert any("Data de emissão não encontrada" in a for a in nfse.avisos)


def test_variante_1_sem_grade_de_valores_nao_inventa_numero(monkeypatch, tmp_path):
    texto = MOCK_LANCHE.replace("valor ISS:\n\n48,00\n\n", "")
    assert texto != MOCK_LANCHE
    nfse = _uma_nota(monkeypatch, tmp_path, texto)
    assert nfse.valores.valor_iss == 0.0  # não derivado de base x alíquota
    assert any("valor ISS" in a for a in nfse.avisos)


def test_variante_1_iss_divergente_do_impresso_so_gera_aviso(monkeypatch, tmp_path):
    texto = MOCK_LANCHE.replace("valor ISS:\n\n48,00", "valor ISS:\n\n49,00")
    assert texto != MOCK_LANCHE
    nfse = _uma_nota(monkeypatch, tmp_path, texto)
    assert nfse.valores.valor_iss == pytest.approx(49.00)  # como impresso, sem "corrigir"
    assert any("ISS impresso (49.00) diverge de Base x Alíquota (48.00)" in a for a in nfse.avisos)


def test_variante_1_iss_retido_com_retencoes_coerentes_nao_gera_aviso_de_valores(monkeypatch, tmp_path):
    texto = (MOCK_LANCHE.replace("ISS Retido:\n\nNão", "ISS Retido:\n\nSim")
             .replace("Valor INSS:\n\n0,00", "Valor INSS:\n\n176,00")
             .replace("Valor Liquido da Nota (R$):\n\n1.600,00", "Valor Liquido da Nota (R$):\n\n1.376,00"))
    nfse = _uma_nota(monkeypatch, tmp_path, texto)
    v = nfse.valores
    assert v.iss_retido is True
    assert v.valor_iss_retido == pytest.approx(48.00)
    assert v.valor_inss == pytest.approx(176.00)
    assert v.valor_liquido_nfse == pytest.approx(1376.00)  # 1600 - 48 (ISS retido) - 176 (INSS)
    assert not any("diverge" in a for a in nfse.avisos)


def test_variante_1_liquido_que_nao_fecha_gera_aviso(monkeypatch, tmp_path):
    texto = MOCK_LANCHE.replace("ISS Retido:\n\nNão", "ISS Retido:\n\nSim")  # líquido continua 1.600,00
    nfse = _uma_nota(monkeypatch, tmp_path, texto)
    assert nfse.valores.valor_liquido_nfse == pytest.approx(1600.00)  # como impresso
    assert any("Valor líquido impresso (1600.00) diverge" in a for a in nfse.avisos)


def test_variante_1_segundo_bloco_de_entidade_ausente_nao_copia_o_prestador(monkeypatch, tmp_path):
    # Destinatário sem "Nome"/"Município"/"CNPJ" (ordem inesperada do PDF): o
    # tomador NÃO pode virar cópia do emitente - sentinela + aviso.
    texto = MOCK_LANCHE.replace("Nome\n\nTEMIS Projetos de Meio Ambiente e Sustentabilidade\n", "")
    texto = texto.replace("CNPJ / CPF\n07.345.543/0001-90\n", "")
    assert texto != MOCK_LANCHE
    nfse = _uma_nota(monkeypatch, tmp_path, texto)
    assert nfse.tomador.razao_social == "Tomador Não Identificado"
    assert nfse.tomador.cnpj_cpf.startswith("00000000000")
    assert nfse.tomador.cnpj_cpf != nfse.prestador.cnpj_cpf
    assert "Dados do tomador não identificados" in nfse.avisos
    assert any("encontrado 1x (esperado 2" in a for a in nfse.avisos)


def test_variante_1_tomador_pessoa_fisica(monkeypatch, tmp_path):
    # CPF no lugar do CNPJ do destinatário (válido: 529.982.247-25).
    texto = MOCK_LANCHE.replace("07.345.543/0001-90", "529.982.247-25")
    nfse = _uma_nota(monkeypatch, tmp_path, texto)
    assert nfse.tomador.cnpj_cpf == "52998224725"
    assert not any("dígito verificador" in a for a in nfse.avisos)


def test_variante_1_cnpj_invalido_impresso_e_mantido_com_aviso(monkeypatch, tmp_path):
    texto = MOCK_LANCHE.replace("07.165.195/0001-79", "07.165.195/0001-78")
    nfse = _uma_nota(monkeypatch, tmp_path, texto)
    assert nfse.prestador.cnpj_cpf == "07165195000178"
    assert any("prestador" in a and "dígito verificador" in a for a in nfse.avisos)


def test_variante_1_municipio_fora_da_tabela_avisa_em_vez_de_cair_na_capital_em_silencio(monkeypatch, tmp_path):
    texto = MOCK_LANCHE.replace("Municipio\n\nSalvador", "Municipio\n\nVila Imaginaria")
    assert texto != MOCK_LANCHE
    nfse = _uma_nota(monkeypatch, tmp_path, texto)
    assert nfse.tomador.endereco.municipio == "Vila Imaginaria"
    assert any("Vila Imaginaria" in a for a in nfse.avisos)  # aviso de fallback de capital


def test_variante_2_grade_de_tributos_ilegivel_aproveita_so_o_total(monkeypatch, tmp_path):
    # Remove um valor da grade (11 em vez de 12): atribuição posicional insegura.
    texto = MOCK_COMUN.replace("2,00\n\n2,40\n\n", "2,40\n\n")
    assert texto != MOCK_COMUN
    nfse = _uma_nota(monkeypatch, tmp_path, texto)
    assert nfse.valores.valor_servicos == pytest.approx(120.00)
    assert nfse.valores.valor_iss == 0.0
    assert nfse.valores.aliquota == 0.0
    assert any("Grade de tributos" in a for a in nfse.avisos)


def test_variante_2_retencao_de_iss_sim_e_valores_federais_posicionais(monkeypatch, tmp_path):
    # INSS 6,00 (3ª coluna da 1ª linha), IR 1,80 (4ª), ISS retido "Sim",
    # líquido = 120 - 6 - 1,80 - 2,40 (ISS retido) = 109,80.
    texto = (MOCK_COMUN
             .replace("INSS (R$)\n\n0,00\n\n0,00\n\n0,00\n\nIR (R$)\n\n0,00\n\nCSLL (R$)\n\n0,00",
                      "INSS (R$)\n\n0,00\n\n0,00\n\n6,00\n\nIR (R$)\n\n1,80\n\nCSLL (R$)\n\n0,00")
             .replace("Não\n\n0,00\n\n120,00", "Sim\n\n0,00\n\n109,80"))
    assert texto != MOCK_COMUN
    nfse = _uma_nota(monkeypatch, tmp_path, texto)
    v = nfse.valores
    assert v.valor_pis == 0.0 and v.valor_cofins == 0.0
    assert v.valor_inss == pytest.approx(6.00)
    assert v.valor_ir == pytest.approx(1.80)
    assert v.valor_csll == 0.0
    assert v.iss_retido is True
    assert v.valor_iss_retido == pytest.approx(2.40)
    assert v.valor_liquido_nfse == pytest.approx(109.80)
    assert nfse.avisos == []


def test_variante_2_rodape_com_outro_prestador_denuncia_ordem_de_leitura_trocada(monkeypatch, tmp_path):
    texto = MOCK_COMUN.replace("Operador da Empresa: VIVA COMUNICAÇAO E SERVIÇOS LTDA",
                               "Operador da Empresa: TEMIS Projetos de Meio Ambiente e Sustentabilidade")
    nfse = _uma_nota(monkeypatch, tmp_path, texto)
    assert any("possível inversão prestador/tomador" in a for a in nfse.avisos)


def test_variante_2_iss_devido_em_outro_municipio_avisa_sem_mudar_a_incidencia(monkeypatch, tmp_path):
    texto = MOCK_COMUN.replace("Iss Devido no Municipio de Saubara", "Iss Devido no Municipio de Salvador")
    nfse = _uma_nota(monkeypatch, tmp_path, texto)
    assert nfse.municipio_incidencia_override is None
    assert any("ISS devido em outro município (Salvador)" in a for a in nfse.avisos)


def test_variante_2_data_com_hora_impressa_e_respeitada(monkeypatch, tmp_path):
    texto = MOCK_COMUN.replace("DATA E HORA DA EMISSÃO\n14/09/2026\n", "DATA E HORA DA EMISSÃO\n14/09/2026 11:20:05\n")
    assert texto != MOCK_COMUN
    nfse = _uma_nota(monkeypatch, tmp_path, texto)
    assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "14/09/2026 11:20:05"


def test_variante_2_telefone_do_prestador_em_branco_nao_desloca_o_do_tomador(monkeypatch, tmp_path):
    texto = MOCK_COMUN.replace("TELEFONE\n071\n\n981235905\n\n", "TELEFONE\n\n")
    assert texto != MOCK_COMUN
    nfse = _uma_nota(monkeypatch, tmp_path, texto)
    assert nfse.prestador.telefone is None
    assert nfse.tomador.telefone == "71982791844"


# ---------------------------------------------------------------------------
# Unidades puras
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw, esperado", [
    ("RUA DA PAZ  33,  ENTIDADE RELIGIOSA", ("RUA DA PAZ", "33", "ENTIDADE RELIGIOSA")),
    ("RUA Território do Amapá 146,", ("RUA Território do Amapá", "146", None)),
    ("RUA Território do Amapá, 146", ("RUA Território do Amapá", "146", None)),
    ("RUA SANTO  ANTONIO , 14-A", ("RUA SANTO ANTONIO", "14-A", None)),
    ("RUA 7 DE SETEMBRO 12, SALA 3", ("RUA 7 DE SETEMBRO", "12", "SALA 3")),
    ("AVENIDA CENTRAL, S/N", ("AVENIDA CENTRAL", "S/N", None)),
    ("AVENIDA CENTRAL SN", ("AVENIDA CENTRAL", "SN", None)),
    ("RUA SEM NUMERO", ("RUA SEM NUMERO", "S/N", None)),
    ("", ("Não informado", "S/N", None)),
])
def test_separar_endereco(raw, esperado):
    assert sn.separar_endereco(raw) == esperado


@pytest.mark.parametrize("ddd, numero, esperado", [
    ("071", "981235905", "71981235905"),
    ("71", "982791844", "71982791844"),
    ("71", "32393501", "7132393501"),
    ("1", "23", None),
])
def test_telefone_normaliza_ddd_e_descarta_o_invalido(ddd, numero, esperado):
    assert sn._telefone(ddd, numero) == esperado


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
