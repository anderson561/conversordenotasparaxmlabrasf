# -*- coding: utf-8 -*-
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_SALVADOR

# Texto REAL do OCR (Tesseract) de uma Nota Salvador ESCANEADA (NFS-e eletrônica
# do MUNICÍPIO DO SALVADOR) — nota real nº 73, CAJADO ENGENHARIA -> SAO PEDRO
# CONSTRUTORA. Preservado verbatim. O quirk que trava a regressão do bug do
# tomador: esta variante escaneada NÃO tem cabeçalho "TOMADOR DE SERVIÇOS" — o
# bloco do tomador só se distingue pelo 2º "Nome/Razão Social", e vem com a ordem
# de campos INVERTIDA em relação ao prestador (Nome → CPF/CNPJ → Endereço, contra
# CPF/CNPJ → Nome → Endereço do prestador). Sem o recorte dedicado, a busca
# genérica pelo rótulo "TOMADOR" falhava, o bloco virava o texto inteiro e o
# tomador acabava copiando o 1º CNPJ/nome/endereço (os do PRESTADOR).
MOCK_OCR = 'Número da Nota:\nJOR 00000073\n\nData e Hora de Emissão:\n\n14/04/2026 08:28:33\nR Código de Verificação:\nalvador YRYSURMV\n\nNúmero da Nota:\n\nPREFEITURA MUNICIPAL DO SALVADOR 00000073\n\nSECRETARIA MUNICIPAL DA FAZENDA Data e Hora de Emissão:\n14/04/2026 08:28:33\n\nNOTA FISCAL DE SERVIÇOS ELETRÔNICA - Nota Salvador código dem ificação:\n\n-"URMV\n\nPRESTADOR DE SERVIÇOS\n\nCPF/CNPJ Inscrição Municipal\n41.003.287/0001-90 00.789.499/001 -42\nNome/Razão Social\n\nCAJADO ENGENHARIA E ARQUITETURA LTDA\n\nEndereço\nAve Luís Viana Filho 6462 , CONDOMINIO MANH - PATAMARES - Salvador - CEP: 41680-400 - BA\n\nNome/Razão Social\n\nSAO PEDRO CONSTRUTORA LTDA\n\nCPF/CNPJ Inscrição Municipal\n03.051.741/0001-90 ==\n\nEndereço\n\nAVE PRAIA DE PAJUSSARA 554, QUADRA 28 LOTE 09 VILAS DO ATLANTICO - Lauro de Freitas - CEP: 42708-720/BA\n(MSAOPEDROCONSTRUTORA. COM.BR\n\nDISCRIMINAÇÃO DOS SERVIÇOS .\nPRESTAÇÃO DE SERVIÇOS PROFISSIONAIS DE ENGENHARIA, RELATIVOS AO PERÍODO DE 1º/04/26 A 15/04/26.\n\nDADOS BANCÁRIOS: BANCO BRADESCO, AGÊNCIA 592; CONTA CORRENTE 87112-5;\nPIX: 041.003.287/0001-90\n\nALÍQUOTA DO ISS: 2,51%\nALÍQUOTA DA TRANSPARÊNCIA FISCAL DE ACORDO COM A LEI 12.741/2012 (PERCENTUAIS DO PIS/COFINS/155): 5,63%\n\nVALOR TOTAL DA NOTA = R$6.786,00\n\nCNAE:\n7112000 - Serviços de engenharia\n\nltem da Lista de Serviços:\n00719 - Acompanhamento e fiscalização da execução de obras de engenharia, arquitetura e urbanismo\n\nValor Total das Deduções (R$) Base de Cálculo (R$) Alíquota (%) Valor do ISS (R$) Crédito Nota Salvador (R$)\n0,00 Z z Z 0,00\n\nValor INSS (R$) Valor PIS (R$) Valor COFINS (R$) Valor IR (R$) Valor CSLL (R$): Outras Retenções (R$)] Valor Líquido (R$)\n0,00 0,00 0,00 0,00 0,00 0,00 6.786,00\nAlíquota IBS (%) Valor IBS (R$) Alíquota CBS (%)) Valor CBS (R$)\n\nOUTRAS INFORMAÇÕES\n\n- Esta Nota Salvador foi emitida com respaldo na Lei 7.186/2006\n- Documento emitido por ME ou EPP optante pelo Simples Nacional\n\n- COMPETÊNCIA: 04/2026 (mês/ano)\n- Código de Tributação do Município: 0719-0/01 - Acompanhamento e fiscalização da execução de obras de engenharia, arquitetura e urbanismo\n\nrealizados no local da obra\n\n'


def test_extract_salvador_scan_tomador(monkeypatch):
    dummy_path = "tests/dummy_salvador_scan.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    # PDF escaneado: pdfminer devolve ~nada -> parse_multiple cai no OCR
    # (_extract_via_ocr -> MOCK_OCR), como em produção.
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_OCR)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]
        assert extractor.from_ocr is True

        # Prestador (não deve regredir): CAJADO em Salvador/BA.
        p = nfse.prestador
        assert p.cnpj_cpf == "41003287000190"
        assert p.razao_social == "CAJADO ENGENHARIA E ARQUITETURA LTDA"
        assert p.endereco.municipio == "Salvador"
        assert p.endereco.codigo_municipio == "2927408"
        assert p.endereco.uf == "BA"

        # BUG CORRIGIDO — Tomador: antes vinha idêntico ao prestador (mesmo CNPJ
        # 41003287000190 / CAJADO), porque sem cabeçalho "TOMADOR" o bloco virava
        # o texto inteiro. Agora é o tomador REAL (SAO PEDRO, Lauro de Freitas).
        tm = nfse.tomador
        assert tm.cnpj_cpf == "03051741000190"
        assert tm.razao_social == "SAO PEDRO CONSTRUTORA LTDA"
        # Número separado do logradouro (fix 2026-08-10, nota 6508): antes o
        # número ficava colado no logradouro e o complemento vazava pro campo
        # "numero" do XML — agora ambos saem nos campos certos.
        assert tm.endereco.logradouro == "AVE PRAIA DE PAJUSSARA"
        assert tm.endereco.numero == "554"
        assert tm.endereco.complemento == "QUADRA 28 LOTE 09 VILAS DO ATLANTICO"
        assert tm.endereco.municipio == "Lauro de Freitas"
        assert tm.endereco.codigo_municipio == "2919207"
        assert tm.endereco.uf == "BA"
        assert tm.endereco.cep == "42708720"

        # Trava de regressão explícita: tomador NUNCA pode ser o prestador.
        assert tm.cnpj_cpf != p.cnpj_cpf
        assert tm.razao_social != p.razao_social
        assert tm.endereco.codigo_municipio != p.endereco.codigo_municipio
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
