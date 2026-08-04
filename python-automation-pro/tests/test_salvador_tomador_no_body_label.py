# -*- coding: utf-8 -*-
"""Salvador/BA escaneado — o rótulo "TOMADOR" aparece só no CORPO da discriminação.

Nota real nº 624, GEOLINER MONTAGENS -> DELTALINE SERVICOS (lote 06/2026,
"NF 624- DELTALINE- MOBILIZAÇÃO E DESMOBILIZAÇÃO.pdf"). Esta variante escaneada
NÃO tem cabeçalho "TOMADOR DE SERVIÇOS" — o tomador só se distingue pelo 2º
"Nome/Razão Social". O quirk que travava o recorte dedicado: a discriminação
contém "-I8S RETIDO PELO TOMADOR 5% = R$450,00 (DEVIDO NA CIDADE DE CAMAÇARI-
BA)", e essa palavra "TOMADOR" do CORPO fazia a heurística `tem_label_tomador`
(que varria o texto inteiro) pular o recorte do 2º Nome/Razão. A extração
genérica então ancorava naquele "TOMADOR" da discriminação e o tomador saía com
razão "5% = R$450,00 (DEVIDO...)" e CNPJ sentinela 00000000000100.

Correção (aditiva, gated em LAYOUT_SALVADOR): `tem_label_tomador` passou a só
considerar o rótulo ANTES da DISCRIMINAÇÃO (região de cabeçalho). As variantes
com cabeçalho "TOMADOR DE SERVIÇOS" real continuam intactas (ver os outros 3
testes de Salvador).
"""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_OCR = 'Número da Nota:\nJOR 00000624\n\nData e Hora de Emissão:\n\n21/07/2026 14:46:11\nalvador Cano io ilicação:\n\nPREFEITURA MUNICIPAL DO SALVADOR 00000624 o\n\nSECRETARIA MUNICIPAL DA FAZENDA Data e Hora de Emissão:\n21/07/2026 14:46:11\n\nNOTA FISCAL DE SERVIÇOS ELETRÔNICA - Nota Salvador cánigo do Werificação:\n\nPRESTADOR DE SERVIÇOS\n\nCPF/CNPJ Inscrição Municipal\n\n00.659.859/0001-07 00.113.799/001 -42\n\nNome/Razão Social\n\nGEOLINER MONTAGENS SERVIÇOS E COMERCIO LTDA\n\nEndereço\n\nAve Sete de Setembro 000174, EDIF:SANTA RITA;SALA:404 - DOIS DE JULHO - Salvador - CEP: 40060-001 - BA\n\nNome/Razão Social\nDELTALINE SERVICOS LTDA.\nCPF/CNPJ Inscrição Municipal\n\n01.813.680/0001-25 00.140.282/001-12\n\nEndereço\n\nRua Camboriú 39 IAPI - Salvador - CEP: 40330-533/BA\n\nE-mail\n\nrjcc51 GDhotmail. com\n\nDISCRIMINAÇÃO DOS SERVI 23 « « . .\n\nADIANTAMENTO PARA A MOBILIZAÇÃO/ DEMOBILIZAÇÃO NA IMPLANTAÇÃO DE ESTRUTUTAS METÁLICAS, ATRAVES DE PROCESSO\nNÃO DESTRUTIVOS SISTEMA TUNNEL LINER DN 1,80 M, ESP 2,70MM, GALVANIZADO NA OBRA: TRAV. MND TUNNEL LINER/OBRA\nPOLO PETROQUIMICO DE CAMAÇARI- POÇOS.\n\n-MÃO DE OBRA 60%: R$5.400,00\n\n-“EQUIPAMENTOS 40% R$3.600,00\n\n-RETENÇÃO PARA SEGURIDADE SOCIAL (INSS SOB MÃO DE OBRA) 3,5% = R$189,00\n-I8S RETIDO PELO TOMADOR 5% = R$450,00 (DEVIDO NA CIDADE DE CAMAÇARI- BA)\n-*DADOS BANCÁRIO: ITAU 5/A AG: 0665 C/C 02619-1*\n\n- FAVORECIDO: TADEU ALBERTO PEREIRA LIMA\n\n- PIX (CELULAR: (71) 9 9983-0834- BANCO ITAÚ\n\nVALOR TOTAL DA NOTA = R$9.000,00\n\nCNAE:\n4292801 - Montagem de estruturas metálicas\n\nltem da Lista de Serviços:\n00702 - Execução, por administração, empreitada ou subempreitada, de obras de construção civil, hidráulica ou elétrica e de outras o...\nValor Total das Deduções (R$) Base de Cálculo (R$) Alíquota (%) Valor do ISS (R$) Crédito Nota Salvador (R$)\n0,00 9.000,00 5,00% 450,00 0,00\nValor INSS (R$) Valor PIS (R$) Valor COFINS (R$) Valor IR (R$) Valor CSLL (R$): Outras Retenções (R$)] Valor Líquido (R$)\n189,00 58,50 270,00 135,00 90,00 0,00 8.257,50\nAlíquota IBS (%) Valor IBS (R$) Alíquota CBS (%)) Valor CBS (R$)\n\nOUTRAS INFORMAÇÕES\n\n- Esta Nota Salvador foi emitida com respaldo na Lei 7.186/2006\n\n- O ISS desta Nota Salvador é devido FORA do Município de Salvador. Tributação devida para Camaçari-BA,\n\n- Esta Nota Salvador não gera crédito\n\n- COMPETÊNCIA: 07/2026 (mês/ano)\n\n- Código de Tributação do Município: 0702-1/16 - Montagem de estruturas metálicas permanentes em obras de construção civil (Por Empreitada\n\nou Subempreitada)\n\n'


def test_salvador_tomador_com_label_so_no_corpo(monkeypatch):
    dummy_path = "tests/dummy_salvador_nf624.pdf"
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
        assert nfse.numero == "00000624"

        # Prestador (não regride): GEOLINER em Salvador/BA.
        p = nfse.prestador
        assert p.cnpj_cpf == "00659859000107"
        assert p.razao_social == "GEOLINER MONTAGENS SERVIÇOS E COMERCIO LTDA"
        assert p.endereco.municipio == "Salvador"
        assert p.endereco.codigo_municipio == "2927408"
        assert p.endereco.uf == "BA"

        # BUG CORRIGIDO — Tomador REAL (DELTALINE), não o lixo da discriminação.
        tm = nfse.tomador
        assert tm.cnpj_cpf == "01813680000125"
        assert tm.razao_social.startswith("DELTALINE SERVICOS LTDA")
        assert tm.endereco.municipio == "Salvador"
        assert tm.endereco.codigo_municipio == "2927408"
        assert tm.endereco.uf == "BA"
        assert tm.endereco.cep == "40330533"

        # Travas de regressão explícitas do bug antigo.
        assert tm.cnpj_cpf != "00000000000100"
        assert "450,00" not in tm.razao_social
        assert "DEVIDO" not in tm.razao_social.upper()
        # Tomador nunca pode ser o prestador.
        assert tm.cnpj_cpf != p.cnpj_cpf
        assert tm.razao_social != p.razao_social
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
