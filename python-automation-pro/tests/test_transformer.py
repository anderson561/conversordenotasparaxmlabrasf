"""
Testes do transformer ABRASF 2.01 e do extrator multi-layout de NFS-e.

Cobre:
  - Geração XML básica (transformer)
  - Tag <Competencia> sempre presente e com data correta
  - Detecção de layout por município
  - Extração de competência/fato gerador por layout
  - Fallback quando competência não encontrada
  - PDF baseado em imagem (retorna None)
"""

import pytest
from datetime import datetime
from src.models.nfse_models import Nfse, Entidade, Endereco, Valores
from src.transformers.abrasf_transformer import Abrasf201Transformer
from src.extractors.pdf_extractor import (
    SPPdfExtractor,
    _parse_dmy,
    _extrair_competencia_generica,
    LAYOUT_CUIABA,
    LAYOUT_BARREIRAS,
    LAYOUT_CAMACARI,
    LAYOUT_NACIONAL,
    LAYOUT_GENERICO,
)


# ---------------------------------------------------------------------------
# Fixture: NFS-e de exemplo (APROAR – São Paulo)
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_nfse():
    return Nfse(
        numero="225",
        codigo_verificacao="HVDI-NXCB",
        data_emissao=datetime(2026, 3, 7, 13, 8, 11),
        competencia=datetime(2026, 3, 1),
        prestador=Entidade(
            cnpj_cpf="11.437.087/0001-85",
            inscricao_municipal="4.003.857-2",
            razao_social="APROAR PLANEJAMENTO PATRIMONIAL LTDA",
            endereco=Endereco(
                logradouro="AV REBOUCAS",
                numero="3970",
                bairro="PINHEIROS",
                codigo_municipio="3550308",
                uf="SP",
                cep="05402-918"
            )
        ),
        tomador=Entidade(
            cnpj_cpf="00.625.191/0001-87",
            razao_social="PATRICORP PATRIMONIAL LTDA",
            endereco=Endereco(
                logradouro="AVE TANCREDO NEVES",
                numero="1485",
                bairro="CAMINHO DAS ARVORES",
                codigo_municipio="2927408",
                uf="BA",
                cep="41820-020"
            )
        ),
        discriminacao="referente à consultoria do trimestre de fevereiro/26 a abril/26.",
        servico_codigo="03115",
        valores=Valores(
            valor_servicos=32656.00,
            base_calculo=32656.00,
            aliquota=0.05,
            valor_iss=1632.80,
            valor_ir=489.84,
            valor_csll=326.56,
            valor_cofins=979.68,
            valor_pis=212.26,
            valor_liquido_nfse=30647.66
        )
    )


# ---------------------------------------------------------------------------
# Testes do Transformer ABRASF
# ---------------------------------------------------------------------------

def test_xml_transformation_basic(sample_nfse):
    transformer = Abrasf201Transformer()
    xml_output = transformer.transform(sample_nfse)

    assert '<?xml' in xml_output
    assert '<CompNfse' in xml_output
    assert '<InfDeclaracaoPrestacaoServico' in xml_output
    assert '<Numero>225</Numero>' in xml_output
    assert 'APROAR PLANEJAMENTO PATRIMONIAL LTDA' in xml_output
    assert 'PATRICORP PATRIMONIAL LTDA' in xml_output
    assert '32656.00' in xml_output
    assert '03115' in xml_output


def test_xml_sempre_tem_competencia(sample_nfse):
    """A tag <Competencia> deve estar sempre presente no XML."""
    xml_output = Abrasf201Transformer().transform(sample_nfse)
    assert '<Competencia>' in xml_output


def test_xml_competencia_formato_correto(sample_nfse):
    """<Competencia> deve usar o formato YYYY-MM-DD."""
    xml_output = Abrasf201Transformer().transform(sample_nfse)
    assert '<Competencia>2026-03-01</Competencia>' in xml_output


def test_xml_data_emissao_formato_correto(sample_nfse):
    """<DataEmissao> deve usar o formato YYYY-MM-DDTHH:MM:SS."""
    xml_output = Abrasf201Transformer().transform(sample_nfse)
    assert '<DataEmissao>2026-03-07T13:08:11</DataEmissao>' in xml_output


def test_xml_prestador_tem_razao_social(sample_nfse):
    """RazaoSocial do prestador deve constar no XML."""
    xml_output = Abrasf201Transformer().transform(sample_nfse)
    assert '<RazaoSocial>APROAR PLANEJAMENTO PATRIMONIAL LTDA</RazaoSocial>' in xml_output


def test_xml_valor_liquido_nfse_usa_valor_real(sample_nfse):
    """Bug #1 regressão: ValorLiquidoNfse deve usar valor_liquido_nfse (30647.66),
    NÃO valor_servicos (32656.00). São valores distintos quando há retenções."""
    xml_output = Abrasf201Transformer().transform(sample_nfse)
    # Valor bruto NÃO deve aparecer em ValorLiquidoNfse
    assert '<ValorLiquidoNfse>32656.00</ValorLiquidoNfse>' not in xml_output
    # Valor líquido correto DEVE aparecer
    assert '<ValorLiquidoNfse>30647.66</ValorLiquidoNfse>' in xml_output


# ---------------------------------------------------------------------------
# Testes de detecção de layout
# ---------------------------------------------------------------------------

def _make_extractor(texto: str) -> SPPdfExtractor:
    """Cria um extrator com texto já injetado (sem ler PDF real)."""
    ext = SPPdfExtractor.__new__(SPPdfExtractor)
    ext.pdf_path = 'fake.pdf'
    ext.raw_text = texto
    ext.layout = None
    return ext


def test_detect_layout_cuiaba():
    ext = _make_extractor("Prefeitura Municipal de Cuiabá\nData de Competência\n04/03/2026")
    assert ext._detect_layout() == LAYOUT_CUIABA


def test_detect_layout_barreiras():
    ext = _make_extractor("MUNICIPIO DE BARREIRAS\nData Fato Gerador\n02/03/2026")
    assert ext._detect_layout() == LAYOUT_BARREIRAS


def test_detect_layout_camacari():
    ext = _make_extractor("CPqD - Gestão Pública\nData da prestação do serviço: 05/03/2026")
    assert ext._detect_layout() == LAYOUT_CAMACARI


def test_detect_layout_nacional():
    ext = _make_extractor("DANFSe v1.0\nCompetência da NFS-e\n28/02/2026")
    assert ext._detect_layout() == LAYOUT_NACIONAL


def test_detect_layout_generico():
    ext = _make_extractor("Algum texto sem marcas específicas de prefeitura")
    assert ext._detect_layout() == LAYOUT_GENERICO


# ---------------------------------------------------------------------------
# Testes de extração de competência por layout
# ---------------------------------------------------------------------------

def test_competencia_layout_cuiaba():
    texto = (
        "Prefeitura Municipal de Cuiabá\n"
        "Nota Fiscal de Serviço Eletrônica - NFS-e\n"
        "Número da Nota Fiscal\n170\n"
        "Data de Competência\n04/03/2026\n"
        "Data de Geração da NFS-e\n04/03/2026 10:27:23\n"
    )
    ext = _make_extractor(texto)
    ext.layout = LAYOUT_CUIABA
    data_emissao = datetime(2026, 3, 4)
    comp = ext._extrair_competencia(data_emissao)
    assert comp == datetime(2026, 3, 4)  # dia 4 conforme PDF


def test_competencia_layout_barreiras():
    texto = (
        "NOTA FISCAL DE SERVIÇOS ELETRÔNICA - NFSe\n"
        "MUNICIPIO DE BARREIRAS\n"
        "Data Fato Gerador\n02/03/2026\nExigível\n"
        "Emitido em\n02/03/2026 13:45:27\n"
    )
    ext = _make_extractor(texto)
    ext.layout = LAYOUT_BARREIRAS
    data_emissao = datetime(2026, 3, 2)
    comp = ext._extrair_competencia(data_emissao)
    assert comp == datetime(2026, 3, 2)


def test_competencia_layout_camacari():
    texto = (
        "PREFEITURA MUNICIPAL DE CAMAÇARI\n"
        "Secretaria da Fazenda\n"
        "Data da prestação do serviço: 05/03/2026\n"
        "CPqD - Gestão Pública\n"
    )
    ext = _make_extractor(texto)
    ext.layout = LAYOUT_CAMACARI
    data_emissao = datetime(2026, 3, 5)
    comp = ext._extrair_competencia(data_emissao)
    assert comp == datetime(2026, 3, 5)


def test_competencia_layout_nacional():
    """Formato DD/MM/YYYY com newline (mantém retro-compatibilidade)."""
    texto = (
        "DANFSe v1.0\n"
        "Competência da NFS-e\n28/02/2026\n"
        "Data e Hora da emissão da NFS-e\n02/03/2026 19:24:23\n"
    )
    ext = _make_extractor(texto)
    ext.layout = LAYOUT_NACIONAL
    data_emissao = datetime(2026, 3, 2)
    comp = ext._extrair_competencia(data_emissao)
    assert comp == datetime(2026, 2, 28)


def test_competencia_layout_nacional_mm_yyyy():
    """BUG FIX: Portal nacional usa MM/YYYY — deve retornar primeiro dia do mês."""
    texto = (
        "DANFSe v1.0\n"
        "Competência da NFS-e\n02/2026\n"
        "Data e Hora da emissão da NFS-e\n05/03/2026 09:10:00\n"
    )
    ext = _make_extractor(texto)
    ext.layout = LAYOUT_NACIONAL
    data_emissao = datetime(2026, 3, 5)
    comp = ext._extrair_competencia(data_emissao)
    assert comp == datetime(2026, 2, 1), f"Esperado 2026-02-01, obtido {comp}"


def test_competencia_layout_nacional_com_dois_pontos():
    """BUG FIX: Separador ':' em vez de newline deve ser aceito."""
    texto = (
        "DANFSe v1.0\n"
        "Competência da NFS-e: 03/2026\n"
        "Data e Hora da emissão da NFS-e: 07/03/2026 13:08:11\n"
    )
    ext = _make_extractor(texto)
    ext.layout = LAYOUT_NACIONAL
    data_emissao = datetime(2026, 3, 7)
    comp = ext._extrair_competencia(data_emissao)
    assert comp == datetime(2026, 3, 1), f"Esperado 2026-03-01, obtido {comp}"


def test_razao_social_layout_nacional_prestador_plural():
    """BUG FIX: Header 'Prestador de Serviços' (plural) deve ser reconhecido."""
    texto = (
        "DANFSe v1.0\n"
        "Competência da NFS-e: 03/2026\n"
        "Prestador de Serviços\n"
        "CNPJ: 11.437.087/0001-85\n"
        "Razão Social: APROAR PLANEJAMENTO PATRIMONIAL LTDA\n"
        "Inscrição Municipal: 4.003.857-2\n"
        "Tomador de Serviços\n"
        "CNPJ: 00.625.191/0001-87\n"
        "Razão Social: PATRICORP PATRIMONIAL LTDA\n"
    )
    ext = _make_extractor(texto)
    ext.layout = LAYOUT_NACIONAL
    prestador = ext._extrair_entidade("Prestador")
    tomador = ext._extrair_entidade("Tomador")
    assert prestador.razao_social == "APROAR PLANEJAMENTO PATRIMONIAL LTDA", \
        f"Razão Social Prestador errada: '{prestador.razao_social}'"
    assert tomador.razao_social == "PATRICORP PATRIMONIAL LTDA", \
        f"Razão Social Tomador errada: '{tomador.razao_social}'"


def test_competencia_generica_mm_yyyy():
    resultado = _extrair_competencia_generica("Competência: 03/2026")
    assert resultado == datetime(2026, 3, 1)


def test_competencia_generica_mes_extenso():
    resultado = _extrair_competencia_generica("Competência: março/2026")
    assert resultado == datetime(2026, 3, 1)


def test_competencia_generica_fato_gerador():
    resultado = _extrair_competencia_generica("Fato Gerador: 02/2026")
    assert resultado == datetime(2026, 2, 1)


def test_competencia_fallback_usa_emissao():
    """Quando competência não encontrada, deve usar mês/ano da emissão."""
    ext = _make_extractor("Texto sem nenhuma data de competência aqui.")
    ext.layout = LAYOUT_GENERICO
    data_emissao = datetime(2026, 3, 7, 13, 8, 11)
    comp = ext._extrair_competencia(data_emissao)
    # Deve retornar mês/ano da emissão, dia = 1 (nunca datetime.now())
    assert comp.year == 2026
    assert comp.month == 3


def test_competencia_nunca_usa_datetime_now():
    """Garante que competência não usa mês/ano atual se emissão for diferente."""
    ext = _make_extractor("Texto sem competência nenhuma.")
    ext.layout = LAYOUT_GENERICO
    data_emissao = datetime(2025, 6, 15)  # data passada
    comp = ext._extrair_competencia(data_emissao)
    assert comp.year == 2025
    assert comp.month == 6


# ---------------------------------------------------------------------------
# Testes do auxiliar _parse_dmy
# ---------------------------------------------------------------------------

def test_parse_dmy_sem_hora():
    dt = _parse_dmy("28/02/2026")
    assert dt == datetime(2026, 2, 28)


def test_parse_dmy_com_hora():
    dt = _parse_dmy("07/03/2026", "13:08:11")
    assert dt == datetime(2026, 3, 7, 13, 8, 11)


def test_parse_dmy_com_hora_sem_segundos():
    dt = _parse_dmy("05/03/2026", "16:10")
    assert dt == datetime(2026, 3, 5, 16, 10, 0)


# ---------------------------------------------------------------------------
# Teste: PDF baseado em imagem retorna None
# ---------------------------------------------------------------------------

def test_parse_retorna_none_para_pdf_imagem():
    ext = _make_extractor("   \n\n ")  # texto vazio / só espaços
    result = ext.parse()
    assert result is None


# ---------------------------------------------------------------------------
# Testes regressão: cenários reais do Portal Nacional (DANFSe)
# ---------------------------------------------------------------------------

def test_competencia_nacional_multilinha_com_data():
    """BUG FIX: No DANFSe, 'Competência da NFS-e' pode estar em uma linha
    e a data em outra, às vezes com a palavra 'Data' no meio.
    Deve capturar 31/12/2025 integralmente."""
    texto = (
        "Documento Auxiliar da NFS-e (DANFSe)\n"
        "Competência da NFS-e\n"
        "Data\n"
        "31/12/2025\n"
    )
    ext = _make_extractor(texto)
    # Simula detecção de layout
    ext.layout = LAYOUT_NACIONAL
    comp = ext._extrair_competencia(datetime(2025, 12, 31))
    assert comp.day == 31
    assert comp.month == 12
    assert comp.year == 2025

def test_competencia_nacional_sem_separador_tabela():
    """BUG FIX: pdfminer lê tabelas sem separador (NFS-e31/12/2025).
    Separador *? (zero ou mais) deve resolver."""
    texto = (
        "DANFSe v1.0\n"
        "Competência da NFS-e31/12/2025\n"  # sem newline/colon entre label e data
        "Data e Hora de Emissão01/12/2025 10:30:00\n"
    )
    ext = _make_extractor(texto)
    ext.layout = LAYOUT_NACIONAL
    data_emissao = datetime(2025, 12, 1)
    comp = ext._extrair_competencia(data_emissao)
    assert comp == datetime(2025, 12, 31), f"Esperado 2025-12-31, obtido {comp}"


def test_razao_social_nacional_label_fornecedor_e_nome_nome_empresarial():
    """BUG FIX: Portal Nacional usa 'Fornecedor' como seção e
    'Nome / Nome Empresarial' como label de razão social."""
    texto = (
        "DANFSe v1.0\n"
        "Competência da NFS-e31/12/2025\n"
        "Fornecedor\n"
        "CNPJ: 11.437.087/0001-85\n"
        "Nome / Nome Empresarial: APROAR PLANEJAMENTO PATRIMONIAL LTDA\n"
        "Inscrição Municipal: 4.003.857-2\n"
        "Tomador\n"
        "CNPJ: 00.625.191/0001-87\n"
        "Nome / Nome Empresarial: BIO MEDS PHARMACEUTICA LTDA\n"
    )
    ext = _make_extractor(texto)
    ext.layout = LAYOUT_NACIONAL
    prestador = ext._extrair_entidade("Prestador")
    tomador = ext._extrair_entidade("Tomador")
    assert prestador.razao_social == "APROAR PLANEJAMENTO PATRIMONIAL LTDA", \
        f"Prestador errado: '{prestador.razao_social}'"
    assert tomador.razao_social == "BIO MEDS PHARMACEUTICA LTDA", \
        f"Tomador errado: '{tomador.razao_social}'"


def test_razao_social_nao_captura_nome_da_nfse():
    """BUG FIX: relax('Nome') capturava 'Nome da NFS-e Prestador do Serviço...'
    quando o bloco não era detectado. Com relax('Nome') removido de p_extra,
    o fallback deve retornar 'Prestador Não Identificado' em vez de lixo."""
    texto = (
        "Documento Auxiliar da NFS-e\n"
        "Nome da NFS-e Prestador do Serviço são 31/12/25\n"
        "Sem seção de Fornecedor nem Prestador aqui\n"
    )
    ext = _make_extractor(texto)
    ext.layout = LAYOUT_NACIONAL
    prestador = ext._extrair_entidade("Prestador")
    assert "NFS-e Prestador do Serviço" not in prestador.razao_social, \
        f"Capturou lixo: '{prestador.razao_social}'"


def test_razao_social_pdfminer_colunas_intercaladas():
    """BUG FIX: pdfminer lê tabela DANFSe por colunas, produzindo:
    'Nome / Nome Empresarial\\nE-mail\\nBIO MEDS PHARMACEUTICA LTDA'
    O stop_pattern 'E-mail' impedia a captura no bloco_clean.
    O fallback linha-a-linha deve pular E-mail e retornar o nome correto."""
    texto = (
        "EMITENTE DA NFS-e\n"
        "Prestador do Serviço\n"
        "CNPJ / CPF / NIF\n"
        "42.291.155/0001-74\n"
        "Inscrição Municipal\n"
        "-\n"
        "Telefone\n"
        "(48) 3995-0139\n"
        "Nome / Nome Empresarial\n"
        "E-mail\n"
        "BIO MEDS PHARMACEUTICA LTDA\n"
        "BIOMEDSPHARMACEUTICA@GMAIL.COM\n"
        "Endereço\n"
        "JOSE CARLOS DAUX, 8600, SANTO ANTONIO DE LISBOA\n"
        "Município\n"
        "Florianópolis - SC\n"
        "CEP\n"
        "88050-001\n"
        "Tomador\n"
        "CNPJ: 00.625.191/0001-87\n"
        "Nome / Nome Empresarial\n"
        "PATRICORP PATRIMONIAL LTDA\n"
    )
    ext = _make_extractor(texto)
    ext.layout = LAYOUT_NACIONAL
    prestador = ext._extrair_entidade("Prestador")
    tomador = ext._extrair_entidade("Tomador")
    assert prestador.razao_social == "BIO MEDS PHARMACEUTICA LTDA", \
        f"Prestador errado: '{prestador.razao_social}'"
    assert tomador.razao_social == "PATRICORP PATRIMONIAL LTDA", \
        f"Tomador errado: '{tomador.razao_social}'"


