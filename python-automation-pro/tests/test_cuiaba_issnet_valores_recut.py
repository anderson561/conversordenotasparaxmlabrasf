# -*- coding: utf-8 -*-
"""Cuiabá/MT (ISSNet) escaneado — grade de valores truncada no zoom 3 padrão.

Na página 14 do PDF consolidado "NFS PRESTADORES MTI 03-2026" (ANDERSON
FAUSTINO DE OLIVEIRA/FA TELAS -> SÃO PEDRO CONSTRUTORA), a leitura padrão
(zoom 3) quebra a linha de valores da grade "Detalhamento dos Tributos" no
meio: "R$443,80 | R$000" numa linha e "R$ 0,00" isolado bem abaixo, fora do
alcance do regex de captura por linha (`_extrair_valores`). Isso fazia sair:
  - valor_servicos = 443,80 (real: 4.113,50)
  - aliquota = 0,00 e valor_iss = 0,00 (reais: 2% e R$ 82,27 = base×2%)
  - servico_codigo = "03115" default (real: "1413", item da LC116/2003)
  - um <Intermediario> FANTASMA: a tabela "Dados do Intermediário de
    Serviços" desta nota está vazia, mas o bloco genérico (sem delimitador
    para "Descrição DOS Serviços", só tinha o singular "Descrição do
    Serviço") vazava para o texto de "Descrição dos Serviços" seguinte e
    pescava o CNPJ do PRESTADOR (linha "pix para pagamento cnpj
    54.640.319/0001-00") como se fosse do intermediário.

`_ocr_page` agora detecta a grade truncada (menos de 4 tokens "R$" na linha
logo após "Vl. Total dos Serviços") e reprocessa a página inteira em zoom 5 +
PSM 6 (`_ocr_valores_cuiaba`), prependando o texto limpo — validado nos zooms
4/5/6/8 contra a imagem real (zoom 6 também recompõe a grade, mas nesse zoom
específico a alíquota "2,00" cai do texto; por isso zoom 5). Este teste
simula o texto JÁ com o recut prependado (mesma convenção dos demais testes
de OCR-zoom deste projeto — não invoca Tesseract/pymupdf de verdade)."""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_CUIABA

# Recorte limpo (zoom 5 + PSM 6, página inteira) que o `_ocr_page` agora
# prependa ao texto original quando detecta a grade de valores truncada.
CLEAN_RECUT = (
    'wd Prefeitura Municipal de Cuiabá Ny da Fiscal d Servi\n'
    'E SE - mito) ota Fiscal de Serviço\n'
    'FW Secretaria Municipal de Economia NOTA Eletrônica - NFS-e\n'
    'Fone: () - http://wmww.cuiaba.mt.gov.br/ CLEAPANA\n'
    'Dados do Prestador de Serviço |\n'
    'rs\n'
    'ANDERSON FAUSTINO DE OLIVEIRA 01/04/2026 14:40:03 | fl Es ngotis O]\n'
    'Rua 0,5 - Parque Atalaia 01/04/2026 pos is\n'
    'CEP 78095-150 - Fone: (65)91015-1240 - Cuiabá! MT ie Sair o aa\n'
    'ardarnorau atado cem ECBEA3768 Ea er vê\n'
    'nscrição Municipal 281090 - CPF/CNPJ 54.640.319/0001-00 Responsável pela Retenção dr dio RE?\n'
    '[Ms EA Lda\n'
    'Identificação da Nota Fiscal Eletrônica\n'
    'Cuiabá - Mato Grosso Cuiabá - Mato Grosso\n'
    'Dados do Tomador de Serviços\n'
    'CNPJ/CPF : 03.051.741/0001-90 IM : 1492591\n'
    'Razão Social: Sao Pedro Construtora Ltda\n'
    'Endereço : Avenida Praia de Pajussara Número: 554\n'
    'Complemento : QD 28, LOTE 9 Bairro : Vilas do Atlântico\n'
    'CEP: 42708-720 Cidade/UF : Lauro de Freitas/ BA\n'
    'Telefone : (71)3272-0733 E-mail : spúDsaopedroconstrutora.com.br\n'
    'Dados do Intermediário de Serviços\n'
    'Descrição dos Serviços\n'
    'Mão de obra de instalação de gradil e retirada de grade.\n'
    '81,30 de gradil instalado\n'
    '53.90 de grade retirada\n'
    'pix para pagamento cnpj 54.640.319/0001-00 Anderson faustino de oliveira\n'
    'Detalhamento dos Tributos\n'
    'Atividade do Município Aliquota |ltem da LC116/2003 Cód. NBS Cód, CNAE\n'
    '2542000 - [2542-0/00] Fabricação de artigos de serralheria, e... 2,00 | 1413 101075000 | 2542000\n'
    'Vi. Total dos Serviços [Desconto Incondicionado Deduções Base Cálculo Base de Cálculo Total do ISSON ISSQN Retido Desconto Condicionado\n'
    'R$ 4.113,50 R$ 0,00 R$ 0,00 R$ 4.113,50 R$ 82,27 | Não R$ 0,00\n'
    'PIS COFINS INSS IRRF CSLL Outras Reienções VL ISSQN Rendo [Vi Liquido da Nota Fiscal\n'
    'R$ 0,00 R$ 0,00 R$ 0,00 R$ 0,00 | R$0,00 R$ 0,00 R$ 0,00 R$ 4.113,50\n'
    'Construção Civil E a\n'
    'informações Adicionais\n'
)

# Texto original (zoom 3 padrão), com a grade de valores truncada — mesma
# nota usada em test_cuiaba_issnet_entidade_mixup.py.
ORIGINAL_TEXT = 'Prefeitura Municipal de Cuiabá «8 | oia laço di Blnrviço\nSecretaria Municipal de Economia NOTA Eletrônica - NFS-e\nFone: () - http:/Awww.cuiaba.mt.gov.br/ CLHABANA\n\nDados do Prestador de Serviço\n\nData de Geração da NFS-e\n\n01/04/2026 14:40:03\n\nData de Competência\n\nANDERSON FAUSTINO DE OLIVEIRA\nFA TELAS\n\nRua O,5 - Parque Atalaia 01/04/2026\neis ads at (65)91015-1240 - Cuiabá! MT Cód. de Autenticidade\nandersonfaustino325(Dgmail.com ECBEA3768\nInscrição Municipal 281090 - CPF/CNPJ 54.640.319/0001-00 Responsável pela Retenção\n\nIdentificação da Nota Fiscal Eletrônica\n\nNúmero do RPS Série do RPS Data de Emissão do RPS\nExghel inRaaod 25 s-R Sod  —— TM,\nCuiabá - Mato Grosso Cuiabá - Mato Grosso\n\nCNPJICPF:  03.051.741/0001-90 IM: 1492591\n\nRazão Social: Sao Pedro Construtora Ltda\n\nEndereço : Avenida Praia de Pajussara Número: 554\n\nComplemento : QD 28, LOTE 9 Bairro : Vilas do Atlântico\n\nCEP: 42708-720 Cidade/UF : Lauro de Freitas/ BA\n\nTelefone : (71)3272-0733 E-mail : sp(Osaopedroconstrutora.com.br\n\nDados do Intermediário de Serviços\n\nCNPJICPF Inscrição Municipal Razão Social\n\nDescrição dos Serviços\n\nMão de obra de instalação de gradil e retirada de grade.\n\n81.30 de gradil instalado\n\n53.90 de grade retirada\n\npix para pagamento cnpj 54.640.319/0001-00 Anderson faustino de oliveira\n\nAtividade do Município Alíquota [item da LC116/2003 Cód. CNAÉ\n\n2542000 - [2542-0/00] Fabricação de artigos de serralheria, e... 2,00 101075000 | 2542000\n\nVi. Total dos Serviços [Desconto Incondicionado [Deduções Base Cálculo Base de Cálculo Total do ISSQN ISSQN Retido Desconto Condicionado\nR$443,80 | R$000\n\nR$ 0,00\n\nPIS COFINS ES TRRF TSIL Outras Relenções VL ISSQN Reido | Vi Liquido da Nota Fiscal\nR$ 0,00 R$ 0,00 R$0,00 | R$0,00 | R$ 0,00 R$ 0,00 R$ 0,00 R$ 4.113,50\n\nConstrução Civil 5d. Obra: E renal\n\nInformações Adicionais\nT- "DOCUMENTO EMITIDO POR ME OU EPP OPTANTE PELO SIMPLES NACIONAL"; e Il -\n'

MOCK_OCR = CLEAN_RECUT + "\n" + ORIGINAL_TEXT


def test_cuiaba_valores_recut_corrige_grade_truncada(monkeypatch):
    dummy_path = "tests/dummy_cuiaba_valores_recut.pdf"
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

        # Valores: antes saía serviços=443,80/base=443,80/aliq=0/iss=0 (grade
        # truncada). Com o recut prependado, sai fiel à face: 4.113,50 (base
        # e serviços coincidem, sem retenção), aliquota 2%, ISS 82,27 (=
        # base×aliquota, bate com a grade).
        v = nfse.valores
        assert v.valor_servicos == pytest.approx(4113.50)
        assert v.base_calculo == pytest.approx(4113.50)
        assert v.aliquota == pytest.approx(0.02)
        assert v.valor_iss == pytest.approx(82.27)
        assert v.iss_retido is False
        assert v.valor_liquido_nfse == pytest.approx(4113.50)

        # Código de serviço: item LC116 "1413" (antes caía no default "03115").
        assert nfse.servico_codigo == "1413"

        # Trava de regressão explícita do bug antigo.
        assert v.valor_servicos != pytest.approx(443.80)

        # Intermediário: a tabela desta nota está vazia (só cabeçalho) — não
        # pode aparecer um intermediário fantasma com o CNPJ do prestador
        # (pescado da linha "pix para pagamento cnpj ...").
        assert nfse.intermediario is None

        # Entidades seguem corretas (não regride o fix anterior).
        p = nfse.prestador
        assert p.cnpj_cpf == "54640319000100"
        assert p.razao_social == "ANDERSON FAUSTINO DE OLIVEIRA"
        tm = nfse.tomador
        assert tm.cnpj_cpf == "03051741000190"
        assert tm.cnpj_cpf != p.cnpj_cpf
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
