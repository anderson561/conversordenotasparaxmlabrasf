"""
Testes do ContratoLocacaoTransformer.

Cobre:
  - Estrutura XML básica (CompNfse, InfNfse, DeclaracaoPrestacaoServico)
  - Locador mapeado como Tomador no XML
  - Locatário mapeado como Prestador no XML
  - Número = ano da data de emissão (2026)
  - Acumulador = 916
  - Data de emissão personalizada reflete no XML
  - Cálculo automático de ValorIss e ValorLiquidoNfse
  - CodigoVerificacao = "CONTRATO"
"""

import pytest
from datetime import datetime
import xml.etree.ElementTree as ET

from src.models.contrato_locacao_model import ContratoLocacao, EntidadeContrato
from src.transformers.contrato_transformer import ContratoLocacaoTransformer


# ---------------------------------------------------------------------------
# Fixture: contrato-modelo (baseado no contrato da imagem — Cruze LT 2013)
# ---------------------------------------------------------------------------

@pytest.fixture
def locador_fixture():
    return EntidadeContrato(
        cnpj_cpf="146.280.315-68",
        razao_social="Carlos Cesar Torres Santana",
        logradouro="Rua das Flores",
        numero="100",
        bairro="Centro",
        codigo_municipio="2927408",
        uf="BA",
        cep="40010-000",
    )


@pytest.fixture
def locatario_fixture():
    return EntidadeContrato(
        cnpj_cpf="13.709.910/0001-90",
        razao_social="Darcydias Representações Ltda",
        inscricao_municipal="1.663.242-72",
        logradouro="Av. Tancredo Neves",
        numero="1485",
        bairro="Caminho das Árvores",
        codigo_municipio="2927408",
        uf="BA",
        cep="41820-020",
    )


@pytest.fixture
def contrato_fixture(locador_fixture, locatario_fixture):
    return ContratoLocacao(
        locador=locador_fixture,
        locatario=locatario_fixture,
        valor_mensal=1100.00,
        discriminacao="Locação de veículo CRUZE LT 2013, placa OLG-4701",
        data_emissao=datetime(2026, 5, 29, 14, 0, 0),
        aliquota_iss=0.03,
        servico_codigo="0601",
    )


@pytest.fixture
def transformer():
    return ContratoLocacaoTransformer()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_xml(xml_str: str) -> ET.Element:
    """Remove declaração XML e parseia a raiz."""
    return ET.fromstring(xml_str.split('?>', 1)[-1].strip())


def find_text(root: ET.Element, path: str) -> str | None:
    """Busca tag pelo nome simples (ignora namespace)."""
    for elem in root.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag == path:
            return elem.text
    return None


def find_all_texts(root: ET.Element, tag_name: str) -> list[str]:
    """Retorna todos os textos de tags com o nome dado."""
    results = []
    for elem in root.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag == tag_name:
            results.append(elem.text)
    return results


# ---------------------------------------------------------------------------
# 1. Estrutura básica do XML
# ---------------------------------------------------------------------------

def test_xml_contrato_basico(transformer, contrato_fixture):
    """XML deve conter as tags obrigatórias do ABRASF."""
    xml_output = transformer.transform(contrato_fixture)

    assert '<?xml' in xml_output
    assert '<CompNfse' in xml_output
    assert '<InfDeclaracaoPrestacaoServico' in xml_output
    assert '<ValoresNfse' in xml_output
    assert '<PrestadorServico' in xml_output
    assert '<DeclaracaoPrestacaoServico' in xml_output


def test_xml_declaracao_xml_presente(transformer, contrato_fixture):
    """Deve iniciar com declaração XML e encoding utf-8."""
    xml_output = transformer.transform(contrato_fixture)
    assert xml_output.startswith("<?xml version='1.0' encoding='utf-8'?>")


# ---------------------------------------------------------------------------
# 2. Número = ano da data de emissão
# ---------------------------------------------------------------------------

def test_numero_e_ano_corrente(transformer, contrato_fixture):
    """<Numero> deve ser o ano da data de emissão (2026)."""
    xml_output = transformer.transform(contrato_fixture)
    root = parse_xml(xml_output)
    numero = find_text(root, 'Numero')
    assert numero == "2026", f"Esperado '2026', obtido '{numero}'"


def test_numero_ano_diferente(transformer, locador_fixture, locatario_fixture):
    """<Numero> deve refletir o ano da data de emissão informada."""
    contrato = ContratoLocacao(
        locador=locador_fixture,
        locatario=locatario_fixture,
        valor_mensal=1100.00,
        discriminacao="Teste",
        data_emissao=datetime(2027, 1, 15),
        aliquota_iss=0.03,
    )
    xml_output = transformer.transform(contrato)
    root = parse_xml(xml_output)
    assert find_text(root, 'Numero') == "2027"


# ---------------------------------------------------------------------------
# 3. Locador → Tomador no XML
# ---------------------------------------------------------------------------

def test_locador_mapeado_como_tomador(transformer, contrato_fixture):
    """Razão social do locador deve aparecer dentro da tag <Tomador>."""
    xml_output = transformer.transform(contrato_fixture)

    # Encontrar bloco <Tomador> e verificar RazaoSocial
    root = parse_xml(xml_output)

    tomador_elem = None
    for elem in root.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag == 'Tomador':
            tomador_elem = elem
            break

    assert tomador_elem is not None, "Tag <Tomador> não encontrada no XML"

    razao_social_tomador = None
    for elem in tomador_elem.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag == 'RazaoSocial':
            razao_social_tomador = elem.text
            break

    assert razao_social_tomador == "Carlos Cesar Torres Santana", \
        f"RazaoSocial do Tomador incorreta: '{razao_social_tomador}'"


def test_locador_cpf_em_tomador(transformer, contrato_fixture):
    """CPF do locador deve aparecer no bloco <Tomador>."""
    xml_output = transformer.transform(contrato_fixture)
    root = parse_xml(xml_output)

    # Localiza elemento <Tomador>
    tomador_elem = None
    for elem in root.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag == 'Tomador':
            tomador_elem = elem
            break

    assert tomador_elem is not None

    # Busca CPF dentro do Tomador
    cpf_found = None
    for elem in tomador_elem.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag == 'Cpf':
            cpf_found = elem.text
            break

    assert cpf_found == "14628031568", f"CPF do locador no Tomador errado: '{cpf_found}'"


# ---------------------------------------------------------------------------
# 4. Locatário → Prestador no XML
# ---------------------------------------------------------------------------

def test_locatario_mapeado_como_prestador(transformer, contrato_fixture):
    """Razão social do locatário deve aparecer dentro de <PrestadorServico>."""
    xml_output = transformer.transform(contrato_fixture)
    root = parse_xml(xml_output)

    prestador_elem = None
    for elem in root.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag == 'PrestadorServico':
            prestador_elem = elem
            break

    assert prestador_elem is not None, "Tag <PrestadorServico> não encontrada no XML"

    razao_social_prestador = None
    for elem in prestador_elem.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag == 'RazaoSocial':
            razao_social_prestador = elem.text
            break

    assert razao_social_prestador == "Darcydias Representações Ltda", \
        f"RazaoSocial do Prestador incorreta: '{razao_social_prestador}'"


def test_locatario_cnpj_em_prestador(transformer, contrato_fixture):
    """CNPJ do locatário deve aparecer em <PrestadorServico>."""
    xml_output = transformer.transform(contrato_fixture)
    root = parse_xml(xml_output)

    prestador_elem = None
    for elem in root.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag == 'PrestadorServico':
            prestador_elem = elem
            break

    assert prestador_elem is not None

    cnpj_found = None
    for elem in prestador_elem.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag == 'Cnpj':
            cnpj_found = elem.text
            break

    assert cnpj_found == "13709910000190", f"CNPJ do locatário no Prestador errado: '{cnpj_found}'"


# ---------------------------------------------------------------------------
# 5. Acumulador 916
# ---------------------------------------------------------------------------

def test_acumulador_916(transformer, contrato_fixture):
    """<Acumulador>916</Acumulador> deve estar presente no XML."""
    xml_output = transformer.transform(contrato_fixture)
    assert '<Acumulador>916</Acumulador>' in xml_output, \
        "Tag <Acumulador>916</Acumulador> não encontrada no XML"


def test_acumulador_dentro_de_declaracao(transformer, contrato_fixture):
    """<Acumulador> deve estar dentro de <InfDeclaracaoPrestacaoServico>."""
    xml_output = transformer.transform(contrato_fixture)
    root = parse_xml(xml_output)

    inf_decl = None
    for elem in root.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag == 'InfDeclaracaoPrestacaoServico':
            inf_decl = elem
            break

    assert inf_decl is not None, "<InfDeclaracaoPrestacaoServico> não encontrada"

    acumulador = None
    for elem in inf_decl:
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag == 'Acumulador':
            acumulador = elem.text
            break

    assert acumulador == "916", f"<Acumulador> incorreto: '{acumulador}'"


# ---------------------------------------------------------------------------
# 6. Data de Emissão personalizada
# ---------------------------------------------------------------------------

def test_data_emissao_customizada(transformer, contrato_fixture):
    """DataEmissao no XML deve refletir a data informada pelo usuário."""
    xml_output = transformer.transform(contrato_fixture)
    assert '<DataEmissao>2026-05-29T14:00:00</DataEmissao>' in xml_output, \
        "DataEmissao incorreta no XML"


def test_competencia_igual_data_emissao(transformer, contrato_fixture):
    """<Competencia> deve ser a data de emissão no formato YYYY-MM-DD."""
    xml_output = transformer.transform(contrato_fixture)
    assert '<Competencia>2026-05-29</Competencia>' in xml_output, \
        "Competencia incorreta no XML"


# ---------------------------------------------------------------------------
# 7. Cálculos de valores
# ---------------------------------------------------------------------------

def test_valor_iss_calculado_corretamente(transformer, contrato_fixture):
    """ValorIss = valor_mensal * aliquota_iss = 1100.00 * 0.03 = 33.00."""
    xml_output = transformer.transform(contrato_fixture)
    assert '<ValorIss>33.00</ValorIss>' in xml_output, \
        "ValorIss calculado incorretamente"


def test_valor_liquido_nfse(transformer, contrato_fixture):
    """ValorLiquidoNfse = valor_mensal - valor_iss = 1100.00 - 33.00 = 1067.00."""
    xml_output = transformer.transform(contrato_fixture)
    assert '<ValorLiquidoNfse>1067.00</ValorLiquidoNfse>' in xml_output, \
        "ValorLiquidoNfse calculado incorretamente"


def test_valor_servicos_correto(transformer, contrato_fixture):
    """ValorServicos deve ser 1100.00."""
    xml_output = transformer.transform(contrato_fixture)
    # Verifica a primeira ocorrência (dentro de ValoresNfse)
    assert '<ValorServicos>1100.00</ValorServicos>' in xml_output


# ---------------------------------------------------------------------------
# 8. CodigoVerificacao
# ---------------------------------------------------------------------------

def test_codigo_verificacao_e_contrato(transformer, contrato_fixture):
    """<CodigoVerificacao> deve ser 'CONTRATO'."""
    xml_output = transformer.transform(contrato_fixture)
    assert '<CodigoVerificacao>CONTRATO</CodigoVerificacao>' in xml_output


# ---------------------------------------------------------------------------
# 9. Código de serviço e Acumulador
# ---------------------------------------------------------------------------

def test_item_lista_servico(transformer, contrato_fixture):
    """ItemListaServico deve ser '0601' (código LC 116 para locação de bens móveis)."""
    xml_output = transformer.transform(contrato_fixture)
    assert '<ItemListaServico>0601</ItemListaServico>' in xml_output


def test_natureza_operacao(transformer, contrato_fixture):
    """NaturezaOperacao deve ser '1' (tributação no município)."""
    xml_output = transformer.transform(contrato_fixture)
    assert '<NaturezaOperacao>1</NaturezaOperacao>' in xml_output


# ---------------------------------------------------------------------------
# 10. Integração com run_contrato_conversion
# ---------------------------------------------------------------------------

def test_run_contrato_conversion_gera_arquivo(contrato_fixture, tmp_path):
    """run_contrato_conversion deve gerar arquivo XML no diretório informado."""
    from src.main import run_contrato_conversion

    output_dir = str(tmp_path)
    output_path = run_contrato_conversion(contrato_fixture, output_dir)

    assert os.path.exists(output_path), f"Arquivo não gerado: {output_path}"
    assert output_path.endswith("CONTRATO_LOCACAO_2026.xml"), \
        f"Nome do arquivo incorreto: {output_path}"


def test_run_contrato_xml_valido(contrato_fixture, tmp_path):
    """O arquivo gerado deve ser um XML bem formado e conter <CompNfse>."""
    from src.main import run_contrato_conversion

    output_path = run_contrato_conversion(contrato_fixture, str(tmp_path))
    with open(output_path, encoding="utf-8") as f:
        conteudo = f.read()

    assert '<CompNfse' in conteudo
    assert '<Acumulador>916</Acumulador>' in conteudo
    assert '<Numero>2026</Numero>' in conteudo


import os  # noqa: E402 — importado no final para não poluir o topo do arquivo
