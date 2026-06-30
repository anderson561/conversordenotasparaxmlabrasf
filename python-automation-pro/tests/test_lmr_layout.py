import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
from src.models.nfse_models import Nfse
import os
from datetime import datetime

def test_extract_lmr_layout(monkeypatch):
    mock_text = """RUA JOSÉ ERMÍRIO DE MORAES Nº 310, DISTRITO INDUSTRIAL  
CAMPINA GRANDE-PB - CEP: 58.411-570 

Fone: (83) 2154-7188 

CNPJ: 25.177.534/0002-08 
FATURA/DUPLICATA Nº 070/2025 

DATA DA EMISSÃO: 28/11/2025 

Cliente: DELTALINE SERVIÇOS LTDA 
Endereço: Rua Camboriu, 39 – IAPI – SALVADOR-BA 
CNPJ: 01.813.680/0001-25 

DESCRIÇÃO 

VALOR 

Locação dos equipamentos abaixo descriminados no período 
de 10/11 à 22/11/2025 (13 dias): 

1,00- Prensa Hidráulica 120t 
1,00- Matriz DA-08 

R$ 2.383,34 
R$     216,66 

DADOS DA CONTA PARA PAGAMENTO: 

LMR ENGENHARIA E CONSTRUÇÃO EIRELI 

CNPJ: 25.177.534/0002-08 
BANCO SANTANDER (033) 
AGÊNCIA: 0974 
CONTA: 13001992-1 

VENCIMENTO 
28/11/2025 

VALOR TOTAL 
R$ 2.600,00 

Não contribuinte de ISS s/ locação de LCN 116/03 
"""
    
    dummy_path = "tests/dummy_lmr.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f: f.write(b"%PDF-1.4")
        
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: mock_text)
        
    try:
        extractor = SPPdfExtractor(dummy_path)
        extractor.raw_text = mock_text
        extractor.layout = extractor._detect_layout()
        
        assert extractor.layout == 'lmr_engenharia'
        
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]
        
        assert nfse.numero == "70"
        assert nfse.codigo_verificacao == "FATURA"
        assert nfse.prestador.cnpj_cpf == "25177534000208"
        assert nfse.prestador.razao_social == "LMR ENGENHARIA E CONSTRUÇÃO EIRELI"
        assert nfse.tomador.cnpj_cpf == "01813680000125"
        assert nfse.tomador.razao_social == "DELTALINE SERVIÇOS LTDA"
        assert nfse.valores.valor_servicos == pytest.approx(2600.00)
        assert nfse.valores.valor_iss == pytest.approx(0.00)
        assert nfse.valores.aliquota == pytest.approx(0.00)
        assert "Prensa Hidráulica 120t" in nfse.discriminacao
    finally:
        if os.path.exists(dummy_path): os.remove(dummy_path)

if __name__ == "__main__":
    pytest.main([__file__])
