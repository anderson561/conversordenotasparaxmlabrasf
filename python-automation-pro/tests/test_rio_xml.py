import sys
import os
sys.path.insert(0, os.getcwd()) # Adiciona raiz ao path

import pytest
from datetime import datetime
import xml.etree.ElementTree as ET
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_RIO
from src.transformers.abrasf_transformer import Abrasf201Transformer, NS_ABRASF

if __name__ == "__main__":
    xml_out = "N/A"
    try:
        def test_logic():
            global xml_out
            texto = """
            PREFEITURA DA CIDADE DO RIO DE JANEIRO
            Número da Nota: 00001234
            Data e Hora de Emissão: 10/05/2026 14:30:00
            Mês de Competência: 05/2026
            Código de Verificação: A1B2-C3D4
            
            PRESTADOR DE SERVIÇOS
            CNPJ: 12.345.678/0001-90
            Nome/Razão Social: EMPRESA TESTE LTDA
            Endereço: RUA TESTE, 123 - CENTRO - RIO DE JANEIRO - RJ
            Inscrição Municipal: 123456
            
            TOMADOR DE SERVIÇOS
            CNPJ: 98.765.432/0001-10
            Nome/Razão Social: CLIENTE TESTE SA
            Endereço: AVENIDA CLIENTE, 999 - BARRA - RIO DE JANEIRO - RJ

            Discriminação dos Serviços
            SERVICOS DE CONSULTORIA EM TI E SUPORTE TECNICO REALIZADOS NO MES DE MAIO.
            
            Item da Lista de Serviços: 1.07
            VALOR TOTAL DA NOTA = R$ 1.000,00
            Base de Cálculo = R$ 1.000,00
            Alíquota = 5,00 %
            Valor do ISS = R$ 50,00
            """
            ext = SPPdfExtractor.__new__(SPPdfExtractor)
            ext.pdf_path = 'fake.pdf'
            ext.raw_text = texto
            ext.layout = LAYOUT_RIO
            nfse = ext.parse()
            
            assert nfse is not None
            assert nfse.numero == "00001234"
            assert "CONSULTORIA" in nfse.discriminacao
            assert nfse.servico_codigo == "107"
            
            transformer = Abrasf201Transformer()
            xml_out = transformer.transform(nfse)
            
            import re
            def check_tag(tag, content):
                # Using regex to account for potential whitespace from pretty-printing
                pattern = rf'<{tag}>\s*{re.escape(content)}\s*</{tag}>'
                found = re.search(pattern, xml_out) is not None
                print(f"CHECK {tag}: {found}")
                if not found:
                    # check for what's actually there
                    m = re.search(rf'<{tag}>(.*?)</{tag}>', xml_out, re.DOTALL)
                    print(f"Actual {tag} tag content: '{m.group(1) if m else 'NOT FOUND'}'")
                assert found
                
            check_tag('Numero', '00001234')
            check_tag('CodigoVerificacao', 'A1B2C3D4')
            check_tag('DataEmissao', '2026-05-10T14:30:00')
            check_tag('Cnpj', '12345678000190')
            check_tag('Discriminacao', 'SERVICOS DE CONSULTORIA EM TI E SUPORTE TECNICO REALIZADOS NO MES DE MAIO.')
            check_tag('ItemListaServico', '0107')
            
            xml_has_ns = f'xmlns="{NS_ABRASF}"' in xml_out or f"xmlns='{NS_ABRASF}'" in xml_out
            print(f"CHECK 6 (xmlns):  {xml_has_ns}")
            assert xml_has_ns
            
        test_logic()
        print("SUCCESS: Rio full flow test passed with dynamic fields!")
    except Exception as e:
        print("\n--- ERROR OCCURRED ---")
        try:
            with open(r'c:\Temp\rio_debug.xml', 'w', encoding='utf-8') as f:
                f.write(xml_out)
            print(f"XML saved to c:\\Temp\\rio_debug.xml for analysis (utf-8)")
        except:
            print("Failed to save XML debug file")
        
        import traceback
        traceback.print_exc()
        sys.exit(1)
