# -*- coding: utf-8 -*-
"""Cuiabá/MT (ISSNet) escaneado — número recuperado via recorte dedicado da
caixa "Número da Nota Fiscal".

Na página 14 do PDF consolidado "NFS PRESTADORES MTI 03-2026" (ANDERSON
FAUSTINO DE OLIVEIRA/FA TELAS -> SÃO PEDRO CONSTRUTORA) nenhuma das duas
âncoras de `_extrair_numero` (rótulo limpo "Número da Nota Fiscal: N" e o
dígito imediatamente antes de "Dados do Prestador") sobrevive ao OCR — o
número saía "00000000" com aviso. O usuário confirmou contra o documento
real que o número correto é **16**.

`_ocr_page` agora, quando as duas âncoras falham, recorta em zoom alto (6x/
8x/10x) só a caixa "Número da Nota Fiscal" do canto superior direito (exclui
o logo/QR "NOTA CUIABANA" ao lado, que confunde o OCR e faz o dígito variar
entre zooms — ex.: "16" virando "18"), com PSM 7 + whitelist de dígitos, e só
aceita quando pelo menos 2 dos 3 zooms concordam. Este teste simula o texto
JÁ com o recorte prependado (mesma convenção dos demais testes de OCR-zoom
deste projeto — não invoca Tesseract/pymupdf de verdade)."""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_CUIABA

# Recorte dedicado (zoom 6/8/10 + PSM 7, votação) que o `_ocr_page` agora
# prependa quando nenhuma âncora de número sobrevive.
NUMERO_RECUT = 'Número da Nota Fiscal\n16\n'

# Texto original (zoom 3 padrão) — mesma nota usada nos demais testes desta
# página (grade de valores já truncada, sem âncora de número).
ORIGINAL_TEXT = 'Prefeitura Municipal de Cuiabá «8 | oia laço di Blnrviço\nSecretaria Municipal de Economia NOTA Eletrônica - NFS-e\nFone: () - http:/Awww.cuiaba.mt.gov.br/ CLHABANA\n\nDados do Prestador de Serviço\n\nData de Geração da NFS-e\n\n01/04/2026 14:40:03\n\nData de Competência\n\nANDERSON FAUSTINO DE OLIVEIRA\nFA TELAS\n\nRua O,5 - Parque Atalaia 01/04/2026\neis ads at (65)91015-1240 - Cuiabá! MT Cód. de Autenticidade\nandersonfaustino325(Dgmail.com ECBEA3768\nInscrição Municipal 281090 - CPF/CNPJ 54.640.319/0001-00 Responsável pela Retenção\n\nIdentificação da Nota Fiscal Eletrônica\n\nNúmero do RPS Série do RPS Data de Emissão do RPS\nExghel inRaaod 25 s-R Sod  —— TM,\nCuiabá - Mato Grosso Cuiabá - Mato Grosso\n\nCNPJICPF:  03.051.741/0001-90 IM: 1492591\n\nRazão Social: Sao Pedro Construtora Ltda\n\nEndereço : Avenida Praia de Pajussara Número: 554\n\nComplemento : QD 28, LOTE 9 Bairro : Vilas do Atlântico\n\nCEP: 42708-720 Cidade/UF : Lauro de Freitas/ BA\n\nTelefone : (71)3272-0733 E-mail : sp(Osaopedroconstrutora.com.br\n\nDados do Intermediário de Serviços\n\nCNPJICPF Inscrição Municipal Razão Social\n\nDescrição dos Serviços\n\nMão de obra de instalação de gradil e retirada de grade.\n\n81.30 de gradil instalado\n\n53.90 de grade retirada\n\npix para pagamento cnpj 54.640.319/0001-00 Anderson faustino de oliveira\n\nAtividade do Município Alíquota [item da LC116/2003 Cód. CNAÉ\n\n2542000 - [2542-0/00] Fabricação de artigos de serralheria, e... 2,00 101075000 | 2542000\n\nVi. Total dos Serviços [Desconto Incondicionado [Deduções Base Cálculo Base de Cálculo Total do ISSQN ISSQN Retido Desconto Condicionado\nR$443,80 | R$000\n\nR$ 0,00\n\nPIS COFINS ES TRRF TSIL Outras Relenções VL ISSQN Reido | Vi Liquido da Nota Fiscal\nR$ 0,00 R$ 0,00 R$0,00 | R$0,00 | R$ 0,00 R$ 0,00 R$ 0,00 R$ 4.113,50\n\nConstrução Civil 5d. Obra: E renal\n\nInformações Adicionais\nT- "DOCUMENTO EMITIDO POR ME OU EPP OPTANTE PELO SIMPLES NACIONAL"; e Il -\n'

MOCK_OCR = NUMERO_RECUT + "\n" + ORIGINAL_TEXT


def test_cuiaba_numero_recut_recupera_numero_real(monkeypatch):
    dummy_path = "tests/dummy_cuiaba_numero_recut.pdf"
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

        # Número real (confirmado pelo usuário contra o documento): 16.
        assert nfse.numero == "16"
        assert nfse.numero != "00000000"
        assert "Número da nota não encontrado" not in nfse.avisos

        # Entidades e valores seguem corretos (não regride os fixes anteriores).
        assert nfse.prestador.cnpj_cpf == "54640319000100"
        assert nfse.prestador.razao_social == "ANDERSON FAUSTINO DE OLIVEIRA"
        assert nfse.tomador.cnpj_cpf == "03051741000190"
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
