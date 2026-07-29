# -*- coding: utf-8 -*-
"""Salvador/BA escaneado — recuperação do TOMADOR via re-OCR em zoom alto.

Em scans de baixa qualidade, o zoom 3 padrão corrompe o CNPJ e a razão do
tomador (ex.: "03.051.741/0001-90" -> "05051.74110001.00"; "SÃO PEDRO" ->
"es EO"), fazendo o CNPJ cair no sentinela "00000000000100". O `_ocr_page`
dispara um recut do bloco do tomador em zoom 5 (`_ocr_tomador_salvador`) e
PREPENDA o recorte limpo, de modo que a extração genérica ache o CNPJ/razão
corretos primeiro. Este teste usa o OCR REAL já pós-recut da nota nº 46
(BALUARTE ENGENHARIA -> SÃO PEDRO CONSTRUTORA, PDF consolidado MTI 03-2026).
"""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_SALVADOR

# OCR REAL da página 1 já com o recut aplicado: o bloco LIMPO do tomador (zoom 5)
# aparece PREPENDADO no topo — "SAO PEDRO CONSTRUTORA LTDA" + "03.051.741/0001-90"
# — e o bloco original CORROMPIDO ("es EO CONSTRUTORA LTDA", "05051.74110001.00")
# permanece mais abaixo. A extração genérica usa a 1ª ocorrência (a limpa).
MOCK_OCR = 'TOMADOR DE SERVIÇOS\n\nNome/Razão Social\nSAO PEDRO CONSTRUTORA LTDA\n\nCPFICNP: Inscrição Municipal\n\n03.051.741/0001-90 suas\n\nEndereço:\n\nAVE PRAIA DE PAJUSSARA 554, QUADRA 28 LOTE 09 VILAS DO ATLANTICO - Lauro de Freitas - CEP: 42708-720/BA\nE-mail\nSPESAOPEDROCONSTRUTORA. COM.BR\n\nNúmero da Nota:\nDOR 00000046\n\nData e Hora de Emissão:\n\n02/04/2026 17:27:54\nSalsnardiar Código de Verificação:\n\nPREFEITURA MUNICIPAL DO SALVADOR DOGUUGAS Nota\n\nSECRETARIA MUNICIPAL DA FAZENDA Data e Hora de Emissão:\n02/04/2026 17:27:54\n\nNOTA FISCAL DE SERVIÇOS ELETRÔNICA - Nota Salvador era iicação:\n\nPRESTADOR DE SERVIÇOS\n\nCPF/CNPJ. Inscrição Municipal.\n00.184.928/001 -90\n\n54.234.565/0001-62\n\nNome/Razão Social\n\nBALUARTE ENGENHARIA LTDA\nEndereço\n\npus amador 001057, FEDIF:SALVADOR SHOPPING BUSINE - CAMINHO DAS ÁRVORES - Salvador - CEP: 41820-790 - BA\n\nTOMADOR DE SERVIÇOS\n\nNome/Razão Social\nes EO CONSTRUTORA LTDA\nICNPJ à\n05051.74110001.00 Insorição Municipal\nEndereço\nEE IA DE PAJUSSARA 554, QUADRA 28 LOTE 09 VILAS DO ATLANTICO - Lauro de Freitas - CEP: 42708-720/BA\nSPESAOP STR RA.CO\nDISCRIMINAÇÃO DOS SERVIÇOS\nAcompan MINA: e execução VIÇOS, iços - segunda quinzena 03/26\nChave PIX: 54.234.565/0001-62\nBanco Inter\n\nVALOR TOTAL DA NOTA = R$5.000,00\n\nCNAE\n\nitem da Lista de Serviços\n00702 - Execução, por administração, empreitada ou subempreitada, de obras de construção civil, hidráulica ou elétrica e de outras 0...\n\nValor Total das Deduções (R$): Base de Cálculo (R$) Alíquota (%) Valor do ISS (R$) Crédito Nota Salvador (R$).\n0,00 5.000,00 5,00% 250,00 0,00\n\nValor INSS (R$) Valor PIS (R$) Valor COFINS (R$) ] Valor IR (R$) Valor CSLL (R$): Outras Retenções Valor Liquido (R$)\n0,00 0,00 0,00 “0,00 0,00 0,00 5.000,00\n\nOUTRAS INFORMAÇÕES\n\n- COMPETÊNCIA: 04/2026 (més/ano)\n- Código de Tributação do Município: 0702-0/61 - Construção de edificações residenciais\n'


def test_salvador_tomador_recut_zoom(monkeypatch):
    dummy_path = "tests/dummy_salvador_tomador_ocr.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_OCR)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]
        assert extractor.from_ocr is True
        assert nfse.numero == "00000046"

        # Prestador (não regride): BALUARTE em Salvador/BA.
        p = nfse.prestador
        assert p.cnpj_cpf == "54234565000162"
        assert p.razao_social == "BALUARTE ENGENHARIA LTDA"
        assert p.endereco.codigo_municipio == "2927408"

        # BUG CORRIGIDO — Tomador: antes o CNPJ caía no sentinela 00000000000100
        # (OCR "05051.74110001.00") e a razão saía "es EO CONSTRUTORA LTDA". Com o
        # recut em zoom alto prependado, agora vem o tomador REAL.
        tm = nfse.tomador
        assert tm.cnpj_cpf == "03051741000190"
        assert tm.razao_social == "SAO PEDRO CONSTRUTORA LTDA"
        assert tm.endereco.municipio == "Lauro de Freitas"
        assert tm.endereco.codigo_municipio == "2919207"
        assert tm.endereco.uf == "BA"
        assert tm.endereco.cep == "42708720"

        # Travas de regressão explícitas.
        assert tm.cnpj_cpf != "00000000000100"          # não é o sentinela "não identificado"
        assert tm.cnpj_cpf != p.cnpj_cpf                 # tomador != prestador
        assert "EO CONSTRUTORA" not in tm.razao_social   # não pegou a razão corrompida
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
