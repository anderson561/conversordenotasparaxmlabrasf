import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
from src.models.nfse_models import Nfse
import os
from datetime import datetime

def test_extract_geracao_layout(monkeypatch):
    mock_text = 'CNPJ: 03.292.008/0001-67\n\nLOCAO BENS MVEIS\n\n008016\n\n51826503\n\n27/11/2025\n\nDELTALINE SERVICOS LTDA.\nRUA CAMBORIÚ, 39\n\nSALVADOR\nRUA CAMBORIÚ, 39 - IAPI - SALVADOR - BA - 40330-533\nCNPJ / CPF: 01.813.680/0001-25\n\nIAPI\n\nBA\n\n40330-533\n\nISENTO\n\nJOSE AUGUSTO SANTOS\n\n1\n1\n1\n\nLocao conforme contrato nº000381/2025 de 30/10/2025 a 14/11/2025\nBACIA DE CONTENO DE LEO  (BC 05)\nGRUPO GERADOR SILENCIADO DE 100KVA 380 VOLTS (GS-100-77)\n\n3.700,00\n\n3.700,00\n\n05/12/2025\n\n0,00\n\n3.700,00\n\nDELTALINE SERVICOS LTDA. - AV ATLANTICA KM 9, SN - KM 9 - POLO PETROQUIMICO - CAMAARI - BA - 42810-000\n\n008016\n\n\x0c'
    
    dummy_path = "tests/dummy_geracao.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f: f.write(b"%PDF-1.4")
        
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: mock_text)
        
    try:
        extractor = SPPdfExtractor(dummy_path)
        extractor.raw_text = mock_text
        extractor.layout = extractor._detect_layout()
        
        assert extractor.layout == 'geracao_energia'
        
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]
        
        assert nfse.numero == "8016"
        assert nfse.codigo_verificacao == "FATURA"
        assert nfse.prestador.cnpj_cpf == "03292008000167"
        assert "GERAÇÃO E ENERGIA" in nfse.prestador.razao_social
        assert nfse.tomador.cnpj_cpf == "01813680000125"
        assert nfse.tomador.razao_social == "DELTALINE SERVICOS LTDA."
        assert nfse.valores.valor_servicos == pytest.approx(3700.00)
        assert nfse.valores.valor_iss == pytest.approx(0.00)
        assert nfse.valores.aliquota == pytest.approx(0.00)
        assert "Locao conforme contrato nº000381/2025" in nfse.discriminacao
    finally:
        if os.path.exists(dummy_path): os.remove(dummy_path)

if __name__ == "__main__":
    pytest.main([__file__])
