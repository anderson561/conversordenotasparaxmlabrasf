import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
from src.models.nfse_models import Nfse
import os
from datetime import datetime

def test_extract_cpe_layout(monkeypatch):
    mock_text = """
    CPE BAHIA COM DE APARELHOS TOP
    cpe tecnologia
    RUA A, COND. EMPRESARIAL LIT.NORTE CELNOR, GP-13B ITINGA
    CEP: 42700000 Lauro de Freitas - BA
    Telefone: 71 3345 6789
    Cobrança: (31) 3025-4001
    
    FATURA DE LOCAÇÃO
    Nº 002023358
    1º VIA CLIENTE
    Insc. Estadual: 67702460  CNPJ / CPF: 07.712.781/0001-96
    
    Natureza da Operação: FATURA DE LOCAÇÃO
    Data de: 19/12/2025
    Incrição: 001001798011
    
    Dados do Cliente
    Nome / Razão Social: DELTALINE SERVICOS LTDA.
    CNPJ / CPF: 01.813.680/0001-25
    Endereço: CAMBORIU, 39
    Bairro: IAPI
    Insc. Estadual: ISENTO
    Cep: 40330533
    Município: Salvador
    U.F.: BA
    Fone / Fax: 71 981277086
    
    Número da Nota de Locação: 002023358
    Vencimento: 29/12/2025
    Valor: 300,00
    
    Código e Descrição  NCM  Quantidade  Valor Unitário  Valor Total
    ESTAÇAO TOTAL GD2I8 NAC2  90152010  1  300,00  300,00
    BASTAO 3/3,60M NAC2  90159090  1  0,00  0,00
    PRISMA C/SUPORTE BOLSA P/TRANSP NAC2  90029090  1  0,00  0,00
    TRIPE ALUM P/ ET(M1N-QR/QR2) NAC2  90159090  1  0,00  0,00
    BOLSA NYLON LONA P/ESTOJO ET  42022900  1  0,00  0,00
    UMBRELA  66011000  1  0,00  0,00
    """
    
    dummy_path = "tests/dummy_cpe.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f: f.write(b"%PDF-1.4")
        
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: mock_text)
        
    try:
        extractor = SPPdfExtractor(dummy_path)
        extractor.raw_text = mock_text
        extractor.layout = extractor._detect_layout()
        
        assert extractor.layout == 'cpe_locacao'
        
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]
        
        assert nfse.numero == "002023358"
        assert nfse.codigo_verificacao == "FATURA"
        assert nfse.prestador.cnpj_cpf == "07712781000196"
        assert nfse.prestador.razao_social == "CPE BAHIA COM DE APARELHOS TOP"
        assert nfse.tomador.cnpj_cpf == "01813680000125"
        assert nfse.tomador.razao_social == "DELTALINE SERVICOS LTDA."
        assert nfse.valores.valor_servicos == pytest.approx(300.00)
        assert nfse.valores.valor_iss == pytest.approx(0.00)
        assert nfse.valores.aliquota == pytest.approx(0.00)
        assert "ESTAÇAO TOTAL GD2I8" in nfse.discriminacao
    finally:
        if os.path.exists(dummy_path): os.remove(dummy_path)

if __name__ == "__main__":
    pytest.main([__file__])
