# -*- coding: utf-8 -*-
"""Cuiabá/MT (ISSNet) ESCANEADO — variante em grade degradada pelo OCR.

Complementa `test_cuiaba_layout.py` (formato com rótulos limpos). Aqui a nota
real nº 134 (ID LOCAÇÃO DE MÁQUINAS → SÃO PEDRO CONSTRUTORA, pág. de um PDF
consolidado escaneado) chega com o cabeçalho e a grade de valores garbleados.
Antes dos ramos dedicados, saíam errados: número `554` (nº do endereço do
tomador), código de serviço `03115` (default), município do prestador com IBGE
`2950330` (dígitos da Inscrição Municipal), e alíquota/ISS zerados.
"""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_CUIABA

MOCK_OCR = 'Prefeitura Municipal de Cuiabá “Nota Fiscal de Serviço\n\nSecretaria Municipal de Economia NOTA Eletrônica - NFS-e\nFone: () - http:/Avuw.cuiaba.mt.gov.br/ Cridabási\npe asbnéo a Do pos np an ee E um 134\nDados do Prestador de Serviço\n\nData de Geração da NFS-e\nID LOCACAO DE MAQUINAS LTDA 31/03/2026 16:27:20\nAvenida Brasil,17 - Morada da Serra 31/03/2026\nCEP 78055-508 - Fone: (65)98165-0410 - Cuiabá! MT Emauea apena\njonathanfdeluquiGOgmail.com 3B3DC3576\nInscrição Municipal 295033 - CPF/CNPJ 57.717.414/0001-53\n\nIdentificação da Nota Fiscal Eletrônica\n\nLocal dos Serviços Mi Í !\n\nCuiabá - Mato Grosso Cuiabá - Mato Grosso\nDados do Tomador de Serviços\nCNPJICPF:  03.051.741/0001-90 IM: 1492591\nRazão Social: Sao Pedro Construtora Ltda\nEndereço : Avenida Praia de Pajussara Número: 554\nComplemento : QD 28, LOTE 9 Bairro : Vilas do Atlântico\nCEP: 42708-720 Cidade/UF : Lauro de Freitas/ BA\nTelefone : (71)3272-0733 E-mail : Qsaopedroconstrutora.com.br\n\nDados do Intermediário de Serviços\nCNPJ/CPF Inscrição Municipal Razão Social\n\nDescrição dos Serviços\nServiço de Içamento\n\nSegue dados bancários\n\nBANCO 756 - SICOOB\nAG 4425\n\nCC 91273-5\n\nPix CNPJ\n57717414000153\n\niD Maq locações Ltda\n\nDetalhamento dos Tributos\nAtividade do Município Aliquota [item da LC116/2003 Cód. NBS Cód. CNAE\n\n7112000 - [7112-0/00] Serviços de engenharia - 5,00 | 701 114031000 | 7112000\n\nVi. Total dos Serviços |Desconto Incondicionado [Deduções Base Cálculo Base de Cálculo Total do ISSQN ISSQN Retido Desconto Condicionado\n\nR$ 560,00 R$ 0,00 R$ 0,00 R$ 560,00 R$ 28,00 | Não R$ 0,00\n\nPIS COFINS INSS IRRF CSLL Outras Retenções VI. ISSQN Retido |VI. Liquido da Nota Fiscal\nR$ 0,00 R$ 0,00 R$ 0,00 R$ 0,00 | R$ 0,00 R$ 0,00 R$ 0,00 R$ 560,00\n\nConstrução Civil Cód Obra: mo\n\nInformações Adi\nT="DOCUMENTO EMITIDO POR ME OU EPP OPTANTE PELO SIMPLES NACIONAL"; e Il\n\nNota gerada em 31/03/2026 16:27:20, substitui a nota nº 133\n'


def test_extract_cuiaba_issnet_scan(monkeypatch):
    dummy_path = "tests/dummy_cuiaba_scan.pdf"
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

        # Número: antes vinha "554" (nº do endereço do tomador). O número real vem
        # antes de "Dados do Prestador"; confirmado pelo rodapé "substitui a nº 133".
        assert nfse.numero == "134"
        assert nfse.numero != "554"

        # Código de serviço: item LC116 "701" (após a alíquota, antes do NBS) -> 0701.
        assert nfse.servico_codigo == "0701"

        # Código de autenticidade ISSNet (primeiro token alfanumérico misto).
        assert nfse.codigo_verificacao == "3B3DC3576"

        # Prestador em Cuiabá/MT — IBGE 5103403 (antes vinha 2950330, dígitos da IM).
        p = nfse.prestador
        assert p.cnpj_cpf == "57717414000153"
        assert p.razao_social == "ID LOCACAO DE MAQUINAS LTDA"
        assert p.endereco.municipio == "Cuiabá"
        assert p.endereco.codigo_municipio == "5103403"
        assert p.endereco.uf == "MT"

        # Tomador em Lauro de Freitas/BA (IBGE 2919207).
        tm = nfse.tomador
        assert tm.cnpj_cpf == "03051741000190"
        assert tm.endereco.codigo_municipio == "2919207"

        # Valores fiéis à face (decisão do usuário): serviço 560, base 560,
        # alíquota 5% e ISS R$ 28,00 (= base×alíquota), não retido, líquido 560.
        v = nfse.valores
        assert v.valor_servicos == pytest.approx(560.00)
        assert v.base_calculo == pytest.approx(560.00)
        assert v.aliquota == pytest.approx(0.05)
        assert v.valor_iss == pytest.approx(28.00)
        assert v.iss_retido is False
        assert v.valor_liquido_nfse == pytest.approx(560.00)
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
