import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
from src.models.nfse_models import Nfse
import os
from datetime import datetime

def test_extract_locontainers_layout(monkeypatch):
    mock_text = """VIDAL LOCAO E COMRCIO DE CONTAINERS LTDA
AVENIDA PAULO VI, 1984, LOJA 02, PARTE, PITUBA

SALVADOR- BA CEP: 41810001Tel.(71) 3355-0157/0909/0398

Inscrio Munic. 37776300172 CNPJ 00.111.704/0001-31

Srie nica

DATA DA EMISSO
19/11/2025

NATUREZA DA OPERAO
LOCAO DE BENS MVEIS

Nota Fatura N

022489

DADOS DO CLIENTE

NOME / RAZO SOCIAL
DELTALINE SERVICOS LTDA

ENDEREO

RUA CAMBORIU

MUNICIPIO

SALVADOR

DETALHAMENTO DOS ITENS

ITEM

CDIGO

QUANT. DESCRIO

BAIRRO / DISTRITO

IAPI

CNPJ / CPF

01.813.680/0001-25

CEP

40330533

FONE / FAX

7132441400

U.F.

INSCRIO MUNICIPAL

INSCRIO ESTADUAL

BA

01

02

03

04

05

06

600130

601327

600503

601328

1

1

1

1

1

1

LOCAO DE AR CONDICIONADO DE 21/10 AT 18/11

LOCAO DE CONTAINERS SANITRIO

LOCAO DE CONTAINERS LOC 600P-FORRADO POLIURETANO

LOCAO DE AR CONDICIONADO DE 21/10 AT 18/11

LOCAO DE CONTAINERS LOC 600

LOCAO DE CONTAINERS LOC 600P-FORRADO POLIURETANO

VALOR UNITRIO

VALOR TOTAL

ISS

676,67

2.300,00

1.300,00

676,67

900,00

1.300,00

676,67

2.300,00

1.300,00

676,67

900,00

1.300,00

0

0

0

0

0

0

CLCULO DO IMPOSTO (ISS)

CLCULO DO IMPOSTO (ISS)

NOTA FATURA NO TEM VALOR COMO RECIBO

NO INCIDNCIA DE ISS CONFORME LEI 

VALOR DOS 

OUTROS ENCARGOS

VALOR DO ISS

7.153,34

0,00

0,00

TOTAL DESTA NOTA

7.153,34

DADOS ADICIONAIS

CONTRATO: 5796 - LOCAL: RUA HIDROGNIO - PERODO DE  21/10/2025 AT 20/11/2025
PRAA DE PAGAMENTO: SALVADOR-BA - VENCIMENTO: 19/12/2025
\x0c"""

    dummy_path = "tests/dummy_locontainers.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f: f.write(b"%PDF-1.4")
        
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: mock_text)
        
    try:
        extractor = SPPdfExtractor(dummy_path)
        extractor.raw_text = mock_text
        extractor.layout = extractor._detect_layout()
        
        assert extractor.layout == 'locontainers'
        
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]
        
        assert nfse.numero == "22489"
        assert nfse.codigo_verificacao == "FATURA"
        assert nfse.prestador.cnpj_cpf == "00111704000131"
        assert "VIDAL LOCAÇÃO" in nfse.prestador.razao_social
        assert nfse.tomador.cnpj_cpf == "01813680000125"
        assert nfse.tomador.razao_social == "DELTALINE SERVICOS LTDA"
        assert nfse.valores.valor_servicos == pytest.approx(7153.34)
        assert nfse.valores.valor_iss == pytest.approx(0.00)
        assert nfse.valores.aliquota == pytest.approx(0.00)
        assert "LOCAO DE CONTAINERS SANITRIO" in nfse.discriminacao
    finally:
        if os.path.exists(dummy_path): os.remove(dummy_path)

if __name__ == "__main__":
    pytest.main([__file__])
