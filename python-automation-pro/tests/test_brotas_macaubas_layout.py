# -*- coding: utf-8 -*-
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
import os

# Texto REAL do OCR (Tesseract) da NFS-e escaneada de Brotas de Macaúbas/BA
# (mesma plataforma nfservico.com.br do Iaçu), nota real nº 70, M P C ARAUJO
# -> SÃO PEDRO CONSTRUTORA, R$ 10.091,13 (revitalização de cobertura de
# estacionamento). Preservado verbatim, incluindo:
#  - o cabeçalho recuperado pelo recorte dedicado (_ocr_header_box_iacu, agora
#    com suporte a ângulo de rotação -- esta nota vem de uma FOTO de cabeça
#    para baixo), prependido ao texto ("Número da nota: 70" com um caractere
#    de ruído solto antes do dígito, "6990d3ab9e");
#  - o "|" (OCR de "Nº") colado no endereço do prestador ("RUA DOM PEDRO |
#    26-B");
#  - o nome/CREA do engenheiro responsável colado na razão social do tomador
#    ("SAO PEDRO CONSTRUTORA LTDA Eng. VictoNHage Carmo");
#  - o artefato "rentenções" (com "n" extra) no rótulo "Outras retenções";
#  - ruído de anotações manuscritas entre a discriminação e a grade de
#    valores ("DADOS PARA PAGAMENTO... OBRA. E 0 STAÇÃO DOS SERVIÇOS...").
# O mock alimenta o texto via extract_text (pdfminer), reproduzindo o que o
# _ocr_page produziria, sem depender do Tesseract no CI (mesma convenção do
# teste do Iaçu).
MOCK_TEXT = 'Número da nota:\nÀ 70\nData e hora de Emissão:\n16/06/2026 17:43:22\nCódigo de Verificação:\n6990d3ab9e\nEI AgaRA E]\nEa\nE gr. 407\nEfe. [) 3: Ejs\n\nNota Fiscal Eletrônica de Serviços\n\nNúmero da nota:\n\nÚ - BA\nPREFEITURA DE BROTAS DE MACAÚBAS a e hora de Emissão:\n\nPRAÇA DOS PODERES, 95 - CENTRO 7:43:22\n738442152 16/06/2026 17:43:\nb brotasdemacaubas.ba.gov.br TEL:7 +\nCNPJ: 13797600000174 | e-mail:tributosO! Código de Verificação\n\n6990d3ab9e\nE\n\nNOTA FISCAL DE SERVIÇOS ELETRÔNICA\n\nPRESTADOR DE SERVIÇOS\n\nCPF/CNPJ Inscrição Municipal:\n\n17591540000190 000.000.202/001-38\n\nNome/Razão Social:\n\nM PC ARAUJO- ME AVANTHI CONSTRUTORA\n\nEndereço:\n\nRUA DOM PEDRO | 26-B, CASA - CENTRO - CEP: 47560000 - BROTAS DE MACAUBAS - BA\nE-mail:\n\nmarvan.camposOgmail.com\n\nTOMADOR DE SERVIÇOS $”\nNome/Razão Social:\n\nSAO PEDRO CONSTRUTORA LTDA Eng. VictoNHage Carmo\nCPF/CNPJ: Inscrição Municipal: CREA- BA 181 66/D\n03051741000190\n\nEndereço:\n\nAV PRAIA DE PAJUSSARA 554, - VILAS DO ATLANTICO - CEP: 42708720 - LAURO DE FREITAS - BA\nE-mail:\n\nSPGSAOPEDROCONSTRUTORA.COM.BR\n\nDISCRIMINAÇÃO DOS SERVIÇOS\nREVITALIZAÇÃO DA MALHA DE COBERTURA DO ESTACIONAMENTO\n\nDADOS PARA PAGAMENTO:\n\nSÃO PEDRO CONSTRUTORA\nOBRA. E 0\n\nSTAÇÃO DOS SERVIÇOS - RGiiidos —\nesc 22.06\n\nVALOR TOTAL DA NOTA = R$10.091,13\n\nBase de cálculo (R$): Alíquota (%): Valor do ISS (R$): Crédito (R$):\n10.091,13 5,00 504,56 0,00\n\nOUTRAS INFORMAÇÕES\n\nValor IR (R$): Valor CSLL (R$): Outras rentenções (R$): Valor líquido (R$):\n0,00 0,00 0,00 9.586,57\n\nValor COFINS (R$):\n0,00\n\nta himiéinata/47RO4EANANAA ON NIGAnA JA LAO\n\n'


def test_extract_brotas_macaubas_layout(monkeypatch):
    dummy_path = "tests/dummy_brotas_macaubas.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        extractor.raw_text = MOCK_TEXT
        extractor.layout = extractor._detect_layout()

        assert extractor.layout == "brotas_macaubas_ba"

        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        # Cabeçalho recuperado do recorte dedicado (não fica legível na
        # leitura de página inteira): número, código de verificação e data.
        assert nfse.numero == "70"
        assert nfse.codigo_verificacao == "6990d3ab9e"
        assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "16/06/2026 17:43:22"

        # Código de serviço fixo (decisão do usuário): a nota traz "Item da
        # lista de serviços: 0", que não é um código LC116 válido -- mapeado
        # do CNAE 4391600 (obras de fundações) para 0702.
        assert nfse.servico_codigo == "0702"

        # Prestador M P C ARAUJO (Brotas de Macaúbas/BA) — endereço com
        # complemento ("CASA") entre o número e o bairro, e o "|" colado no
        # número não pode quebrar o parsing nem vazar pro logradouro/número.
        prest = nfse.prestador
        assert prest.cnpj_cpf == "17591540000190"
        assert prest.razao_social == "M PC ARAUJO- ME AVANTHI CONSTRUTORA"
        assert prest.endereco.logradouro == "RUA DOM PEDRO"
        assert prest.endereco.numero == "26-B"
        assert prest.endereco.complemento == "CASA"
        assert prest.endereco.bairro == "CENTRO"
        assert prest.endereco.municipio == "BROTAS DE MACAUBAS"
        assert prest.endereco.codigo_municipio == "2904506"
        assert prest.endereco.uf == "BA"
        assert prest.endereco.cep == "47560000"

        # Tomador SÃO PEDRO CONSTRUTORA (Lauro de Freitas/BA) — a razão NÃO
        # pode vir colada ao nome/CREA do engenheiro responsável impresso à
        # direita na mesma linha.
        tom = nfse.tomador
        assert tom.cnpj_cpf == "03051741000190"
        assert tom.razao_social == "SAO PEDRO CONSTRUTORA LTDA"
        assert "Eng" not in tom.razao_social
        assert tom.endereco.logradouro == "AV PRAIA DE PAJUSSARA"
        assert tom.endereco.numero == "554"
        assert tom.endereco.bairro == "VILAS DO ATLANTICO"
        assert tom.endereco.municipio == "LAURO DE FREITAS"
        assert tom.endereco.codigo_municipio == "2919207"
        assert tom.endereco.uf == "BA"
        assert tom.endereco.cep == "42708720"

        # Grade de valores em 2 linhas + 1 rótulo isolado (SEM o campo "Valor
        # total das deduções" que o Iaçu tem na mesma linha da base/alíquota
        # /ISS -- regex própria, não a do Iaçu). "Outras retenções" tolera o
        # artefato de OCR "rentenções" (n extra).
        val = nfse.valores
        assert val.valor_servicos == pytest.approx(10091.13)
        assert val.base_calculo == pytest.approx(10091.13)
        assert val.aliquota == pytest.approx(0.05)
        assert val.valor_iss == pytest.approx(504.56)
        assert val.valor_deducoes == pytest.approx(0.0)
        assert val.valor_ir == pytest.approx(0.0)
        assert val.valor_csll == pytest.approx(0.0)
        assert val.outras_retencoes == pytest.approx(0.0)
        assert val.valor_cofins == pytest.approx(0.0)
        assert val.valor_liquido_nfse == pytest.approx(9586.57)
        assert val.iss_retido is False

        # Discriminação não pode vazar para o bloco de pagamento/anotações
        # manuscritas ("DADOS PARA PAGAMENTO...").
        assert nfse.discriminacao == "REVITALIZAÇÃO DA MALHA DE COBERTURA DO ESTACIONAMENTO"
        assert "DADOS PARA PAGAMENTO" not in nfse.discriminacao

        assert nfse.avisos == []
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__])
