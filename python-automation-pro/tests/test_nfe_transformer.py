import pytest
from datetime import datetime
from src.models.nfse_models import Nfse, Entidade, Endereco, Valores
from src.transformers.nfe_transformer import NfeTransformer
import xml.etree.ElementTree as ET

def test_nfe_transformer_generation():
    nfse = Nfse(
        numero="12345",
        codigo_verificacao="ABCDE",
        data_emissao=datetime(2023, 10, 27, 10, 0, 0),
        competencia=datetime(2023, 10, 1, 0, 0, 0),
        prestador=Entidade(
            cnpj_cpf="12345678000199",
            razao_social="Prestador Teste LTDA",
            endereco=Endereco(
                logradouro="Rua Teste",
                numero="100",
                bairro="Centro",
                codigo_municipio="3550308",
                uf="SP",
                cep="01001-000"
            )
        ),
        tomador=Entidade(
            cnpj_cpf="98765432000188",
            razao_social="Tomador Teste S.A.",
            endereco=Endereco(
                logradouro="Av Principal",
                numero="500",
                bairro="Industrial",
                codigo_municipio="3304557",
                uf="RJ",
                cep="20000-000"
            )
        ),
        discriminacao="Servico de Consultoria em TI",
        servico_codigo="0107",
        valores=Valores(
            valor_servicos=1000.0,
            base_calculo=1000.0,
            aliquota=0.05,
            valor_iss=50.0,
            valor_liquido_nfse=950.0
        )
    )
    
    transformer = NfeTransformer()
    xml_content = transformer.transform(nfse)
    
    assert 'xmlns="http://www.portalfiscal.inf.br/nfe"' in xml_content
    assert '<mod>55</mod>' in xml_content
    assert '<vNF>1000.00</vNF>' in xml_content
    assert 'Prestador Teste LTDA' in xml_content
    assert 'Tomador Teste S.A.' in xml_content
    
    # Valida estrutura básica
    root = ET.fromstring(xml_content)
    assert root.tag.endswith('nfeProc')
    nfe = root.find('{http://www.portalfiscal.inf.br/nfe}NFe')
    assert nfe is not None
    inf_nfe = nfe.find('{http://www.portalfiscal.inf.br/nfe}infNFe')
    assert inf_nfe is not None
    assert inf_nfe.get('Id').startswith('NFe')
    assert len(inf_nfe.get('Id')) == 47 # NFe + 44 digits
