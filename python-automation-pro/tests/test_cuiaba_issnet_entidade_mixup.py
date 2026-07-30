# -*- coding: utf-8 -*-
"""Cuiabá/MT (ISSNet) escaneado — vazamento do TOMADOR para o bloco do PRESTADOR
quando o cabeçalho "Dados do Tomador de Serviços" some do OCR (página 14 da
nota real ANDERSON FAUSTINO DE OLIVEIRA/FA TELAS -> SÃO PEDRO CONSTRUTORA, no
PDF consolidado "NFS PRESTADORES MTI 03-2026").

Sem cabeçalho de tomador, o bloco do PRESTADOR (delimitado genericamente até o
próximo rótulo reconhecido) engolia também o CNPJ/Razão/Endereço do TOMADOR —
CNPJ saía certo (1º a validar), mas razão social e município saíam do TOMADOR
(prestador aparecia como "Sao Pedro Construtora Ltda" em "Lauro de Freitas" em
vez de "ANDERSON FAUSTINO DE OLIVEIRA" em "Cuiabá"). O número também saía
errado (`554`, pescado do campo "Número:" do ENDEREÇO do tomador) — corrigido
para cair no fallback honesto (placeholder + aviso) em vez de fabricar um
número plausível-porém-errado, já que este scan não tem nenhuma âncora
confiável para o número real.
"""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_CUIABA

MOCK_OCR = 'Prefeitura Municipal de Cuiabá «8 | oia laço di Blnrviço\nSecretaria Municipal de Economia NOTA Eletrônica - NFS-e\nFone: () - http:/Awww.cuiaba.mt.gov.br/ CLHABANA\n\nDados do Prestador de Serviço\n\nData de Geração da NFS-e\n\n01/04/2026 14:40:03\n\nData de Competência\n\nANDERSON FAUSTINO DE OLIVEIRA\nFA TELAS\n\nRua O,5 - Parque Atalaia 01/04/2026\neis ads at (65)91015-1240 - Cuiabá! MT Cód. de Autenticidade\nandersonfaustino325(Dgmail.com ECBEA3768\nInscrição Municipal 281090 - CPF/CNPJ 54.640.319/0001-00 Responsável pela Retenção\n\nIdentificação da Nota Fiscal Eletrônica\n\nNúmero do RPS Série do RPS Data de Emissão do RPS\nExghel inRaaod 25 s-R Sod  —— TM,\nCuiabá - Mato Grosso Cuiabá - Mato Grosso\n\nCNPJICPF:  03.051.741/0001-90 IM: 1492591\n\nRazão Social: Sao Pedro Construtora Ltda\n\nEndereço : Avenida Praia de Pajussara Número: 554\n\nComplemento : QD 28, LOTE 9 Bairro : Vilas do Atlântico\n\nCEP: 42708-720 Cidade/UF : Lauro de Freitas/ BA\n\nTelefone : (71)3272-0733 E-mail : sp(Osaopedroconstrutora.com.br\n\nDados do Intermediário de Serviços\n\nCNPJICPF Inscrição Municipal Razão Social\n\nDescrição dos Serviços\n\nMão de obra de instalação de gradil e retirada de grade.\n\n81.30 de gradil instalado\n\n53.90 de grade retirada\n\npix para pagamento cnpj 54.640.319/0001-00 Anderson faustino de oliveira\n\nAtividade do Município Alíquota [item da LC116/2003 Cód. CNAÉ\n\n2542000 - [2542-0/00] Fabricação de artigos de serralheria, e... 2,00 101075000 | 2542000\n\nVi. Total dos Serviços [Desconto Incondicionado [Deduções Base Cálculo Base de Cálculo Total do ISSQN ISSQN Retido Desconto Condicionado\nR$443,80 | R$000\n\nR$ 0,00\n\nPIS COFINS ES TRRF TSIL Outras Relenções VL ISSQN Reido | Vi Liquido da Nota Fiscal\nR$ 0,00 R$ 0,00 R$0,00 | R$0,00 | R$ 0,00 R$ 0,00 R$ 0,00 R$ 4.113,50\n\nConstrução Civil 5d. Obra: E renal\n\nInformações Adicionais\nT- "DOCUMENTO EMITIDO POR ME OU EPP OPTANTE PELO SIMPLES NACIONAL"; e Il -\n'


def test_cuiaba_prestador_nao_herda_tomador(monkeypatch):
    dummy_path = "tests/dummy_cuiaba_mixup.pdf"
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

        # Prestador: ANDERSON FAUSTINO/FA TELAS em Cuiabá — antes vinha com a
        # razão e o município do TOMADOR (bloco vazava até "Dados do
        # Intermediário" por falta do cabeçalho "Dados do Tomador").
        p = nfse.prestador
        assert p.cnpj_cpf == "54640319000100"
        assert p.razao_social == "ANDERSON FAUSTINO DE OLIVEIRA"
        assert "SAO PEDRO" not in p.razao_social.upper()
        assert p.endereco.municipio == "Cuiabá"
        assert p.endereco.codigo_municipio == "5103403"

        # Tomador: São Pedro Construtora em Lauro de Freitas (IBGE 2919207) —
        # não pode ser igual ao prestador.
        tm = nfse.tomador
        assert tm.cnpj_cpf == "03051741000190"
        assert tm.razao_social == "Sao Pedro Construtora Ltda"
        assert tm.endereco.codigo_municipio == "2919207"
        assert tm.cnpj_cpf != p.cnpj_cpf
        assert tm.razao_social != p.razao_social

        # Número: sem âncora confiável neste scan (o "554" é o nº do endereço
        # do tomador) — cai no fallback honesto (placeholder + aviso), nunca
        # fabrica um número plausível-porém-errado.
        assert nfse.numero == "00000000"
        assert nfse.numero != "554"
        assert "Número da nota não encontrado" in nfse.avisos
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
