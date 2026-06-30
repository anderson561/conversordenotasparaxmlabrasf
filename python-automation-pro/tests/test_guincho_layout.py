import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
from src.models.nfse_models import Nfse
import os
from datetime import datetime

def test_extract_guincho_layout(monkeypatch):
    mock_text = """
              GUINCHO CIDADE EIRELI         
          RUA PORTO DA VITORIA Nº 18         

       NOVO HORIZONTE – FEIRA DE SANTANA – BA         

           CNPJ: 14.318.419.0001/09         
            TELEFONE:(75)99920-3505         

FATURA DE LOCAÇÃO    

Nº:09  

Emissão: 11.12.2025       

DESTINATÁRIO         

RAZAO SOCIAL:  DELTALINE SERVIÇOS LTDA         CNPJ: 01.813.680/0001-25  

Endereço: RUA CAMBURIU Nº 39  

CEP: 40.330-533  

                                                 Bairro:   

Cidade:  SALVADOR                    UF: BA       

DESCRIMINAÇÃO:      

Referente a Locação da Máquina Escavadeira CAT 320 Período 01/11/25 até 12/11/25, Desmobilização e Material de 
Desgaste. 

OBSERVAÇÃO:         
PAGAMENTO VIA BOLETO BANCÁRIO       

VALOR TOTAL DA FATURA: R$ 9.700,00   

RECEBI(EMOS) DE EMPRESA. AS LOCAÇÕES CONSTANTES NESSA FATURA INDICA AO LADO          

FATURA DE LOCAÇÃO         

DATA DO RECEBIMENTO           

IDENTIFICAÇÃO E ASSINATURA DO RECEBEDOR         

Nº: 09 
    """
    
    dummy_path = "tests/dummy_guincho.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f: f.write(b"%PDF-1.4")
        
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: mock_text)
        
    try:
        extractor = SPPdfExtractor(dummy_path)
        extractor.raw_text = mock_text
        extractor.layout = extractor._detect_layout()
        
        assert extractor.layout == 'guincho_cidade'
        
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]
        
        assert nfse.numero == "09"
        assert nfse.codigo_verificacao == "FATURA"
        assert nfse.prestador.cnpj_cpf == "14318419000109"
        assert nfse.prestador.razao_social == "GUINCHO CIDADE EIRELI"
        assert nfse.tomador.cnpj_cpf == "01813680000125"
        assert nfse.tomador.razao_social == "DELTALINE SERVIÇOS LTDA"
        assert nfse.valores.valor_servicos == pytest.approx(9700.00)
        assert nfse.valores.valor_iss == pytest.approx(0.00)
        assert nfse.valores.aliquota == pytest.approx(0.00)
        assert "Locação da Máquina Escavadeira CAT 320" in nfse.discriminacao
    finally:
        if os.path.exists(dummy_path): os.remove(dummy_path)

if __name__ == "__main__":
    pytest.main([__file__])
