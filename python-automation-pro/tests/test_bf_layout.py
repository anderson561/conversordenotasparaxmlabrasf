import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
from src.models.nfse_models import Nfse
import os
from datetime import datetime

def test_extract_bf_layout(monkeypatch):
    mock_text = """
CNPJ: 34.425.389/0001-39 | Inscrição Estadual: 029.708.347 NO | Inscrição Municipal: 77.456.001-50

R CARIPARE (LOT GJAS R P VARGAS), S/N - GRANJAS RURAIS PRESIDENTE VARGAS - GRANJAS RURAIS PRESIDENTE VARGAS
Salvador - BA - CEP: 41230-075
Telefone: (71) 3239-3501

B.F. SERVICOS AMBIENTAIS EIRELI

FATURA nº 0000003002

Emissão: 

 Salvador (BA), 5 de Dezembro de 2025.

Cliente: 

 DELTALINE SERVICOS LTDA.

CNPJ: 01.813.680/0001-25

 RUA CAMBORIU, 39 - IAPI

 rjcc51@hotmail.com
 deltaline.controle@gmail.com

 Salvador - BA - CEP: 40330-533
 Telefone: (71) 3244-1400

Objeto:  Descrição

Locação de sanitários químicos Luxo
CNAE: 77.39-0-99 - ALUGUEL DE OUTRAS MÁQUINAS E EQUIPAMENTOS COMERCIAIS
E INDUSTRIAIS NÃO ESPECIFICADOS ANTERIORMENTE SEM OPERADOR.

Valor Total

1.641,00

Total Bruto

Descontos

Total Líquido

1.641,00

0,00

1.641,00

Vencimento: 

 dia 22/12/2025 no valor de R$ 1.641,00

Observações: 

LOCAÇÃO DE 01 SANITÁRIO QUÍMICO MODELO LUXO
PERIODO: 29/09/2025 A 30/11/2025
LOCAL: CANTEIRO DA DELTALINE NO CIA / Lauro de Freitas
CONFORME BOLETIM DE MEDIÇÃO 011/2025

VENCIMENTO: 22/12/2025
BOLETO
    """
    
    dummy_path = "tests/dummy_bf.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f: f.write(b"%PDF-1.4")
        
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: mock_text)
        
    try:
        extractor = SPPdfExtractor(dummy_path)
        extractor.raw_text = mock_text
        extractor.layout = extractor._detect_layout()
        
        assert extractor.layout == 'bf_ambientais'
        
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]
        
        assert nfse.numero == "3002"
        assert nfse.codigo_verificacao == "FATURA"
        assert nfse.prestador.cnpj_cpf == "34425389000139"
        assert nfse.prestador.razao_social == "B.F. SERVICOS AMBIENTAIS EIRELI"
        assert nfse.tomador.cnpj_cpf == "01813680000125"
        assert nfse.tomador.razao_social == "DELTALINE SERVICOS LTDA."
        assert nfse.valores.valor_servicos == pytest.approx(1641.00)
        assert nfse.valores.valor_iss == pytest.approx(0.00)
        assert nfse.valores.aliquota == pytest.approx(0.00)
        assert "Locação de sanitários químicos Luxo" in nfse.discriminacao
    finally:
        if os.path.exists(dummy_path): os.remove(dummy_path)

if __name__ == "__main__":
    pytest.main([__file__])
