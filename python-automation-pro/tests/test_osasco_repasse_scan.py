# -*- coding: utf-8 -*-
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
import os

# Texto REAL do OCR (Tesseract) da pagina 8 do PDF
# "Notas_Fiscais_Recebidas_05.2026_-_Guarajuba_Suites.pdf": NF-R de Repasse de
# Osasco/SP (layout osasco_nfr_repasse) ESCANEADA, IFOOD BENEFICIOS E SERVICOS
# LTDA -> PH GESTAO, nota no 2279456, R$ 484,53. A DETECCAO do layout ja
# funcionava no escaneado; o que quebrava eram as ancoras de extracao do ramo
# osasco (feitas para o NF-R DIGITAL) diante do ruido do OCR:
#  - numero "Nota No,: 2279456" (virgula no lugar do ponto) -> caia p/ 00000000
#  - tomador "CEF/CNPI: 25.311.856/0001-09" (rotulo CPF/CNPJ degradado) -> CNPJ zerado
#  - "UF; BA" (ponto-e-virgula) -> UF caia no default SP e Camacari/BA virava
#    Sao Paulo/SP (3550308); + faltava city_hint no resolver
#  - hora de emissao ("as 16:02:47", no rodape) nao era capturada
MOCK_TEXT = 'a EE\npa - sda + Pari Led\nEgo Prefeitura do Município de Osasco EAR\n[RE OR Secretaria de Finanças Da CR\nCd, don\nme e RR ER\n[Ob igia chi\nNota Fiscal Eletrônica de Repasse - NF-R\nSérie: RI Nota No,: 2279456 Emissão: 07/05/2026\nDi SD O PO O O qn\nEMITENTE\nRazão Social/Nome: IFOOD BENEFICIOS E SERVICOS LTDA.\nCPF/CNPJ: 33.157.312/0001-62 Inscrição Municipal: 0000145284\nEndereço: AV. das Autonomistas, 1496 - BLOCO-B,3º ANDAR, PARTE-Vila Yara - 06020012\nMunicípio: Osasco UF: SP\nEmail: tributariotifood.com.br Fone: (00)3498-8402\nLL LD DDD >> ——— TT\nRECEPTOR\nRazão Social/Nome: PHGESTAO ECONSULTORIA S.A.\nCEF/CNPI: 25.311.856/0001-09 Inscrição Municipal:\nEndereço: AALHUMAITA, O -GUARAJUBA 32840-562\nMunicípio: Camaçari UF; BA\nEmail: priscilabguarajubanegocios.com.br Fone: 3248-7400\nPat et ala ÉS AA O E a a a e O\nDISCRIMINAÇÃO\nSERVICO RECARGATFOOD BENEFICIOS. | Vencimento daCobranca: 09/05/2025 | Nota Fiscal emitida de acordo como Regime .\nEspacialobjeto do Processo [Administrativo No. 11.037/2020, que autoriza que o valor total danota | contemple o valor recebido\npeloiFoodBeneficios para a realizacao dos Iservicos de administracao em gerale o valor recebido para | disponibilizacao dos\nbenefícios ao consumidorna plataforma. A base de | calculo do ISS devido e 0 valorrecabidopelosservicos de administracao | em\ngeral, quando aplicavel. |Regra GeralSaldo Livre: R$ 484,53\nld >>> IT\nIMPOSTOS ADICIONAIS -Lei12.741/2012 (Os valoresinformados são deresponsabilidade exclusiva do emissor)\nINSS (R$): 0,00 IRRF (R$): 0,00 CSLL (R$): 0,00 COFINS (R$): 0,00 PIS/PASEP (R$): 0,00\nDo D>>—>——>> >> —>———>—N TT\nE\nReferência: 5/2026 Valor da Nota: 484,53 Valor do Repasse: 484,53\nDid.\nCódigo de autenticidade: CKIGTPTE\nverifique a autenticidade destanota no site http://www nfe-osasco.sp.gov.br\nNota Fiscal de Repasse (NF-R) emitida em 07/05/2026 às 16:02:47 conforme Decreto N, 13.377 de 03 de junho de 2022.\nRegime Especial -Proc.N. 10066/2022\nA emissão desta nota de repasse não desobrigao prestador de serviço de emitir o recibo ou notafiscalao tomados tampouco do\nrecolhimento do imposto devido.\n'


def test_extract_osasco_repasse_escaneado_pag8(monkeypatch):
    dummy_path = "tests/dummy_osasco_scan.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        # Numero: virgula no lugar do ponto ("Nota No,:") nao pode mais zerar.
        assert nfse.numero == "2279456"
        assert nfse.numero != "00000000"

        # Data de emissao COM hora (do rodape "emitida em ... as 16:02:47").
        assert nfse.data_emissao.year == 2026
        assert nfse.data_emissao.month == 5
        assert nfse.data_emissao.day == 7
        assert nfse.data_emissao.hour == 16
        assert nfse.data_emissao.minute == 2
        assert nfse.data_emissao.second == 47

        # Prestador (emitente iFood) — ja funcionava, trava contexto.
        assert nfse.prestador.cnpj_cpf == "33157312000162"
        assert "IFOOD" in nfse.prestador.razao_social.upper()

        # Tomador: CNPJ recuperado pelo fallback (rotulo "CEF/CNPI" degradado).
        assert nfse.tomador.cnpj_cpf == "25311856000109"

        # Municipio do tomador: Camacari/BA (2905701), NAO Sao Paulo/SP (3550308).
        assert nfse.tomador.endereco.codigo_municipio == "2905701"
        assert nfse.tomador.endereco.uf == "BA"

        # Valor do repasse.
        assert nfse.valores.valor_servicos == pytest.approx(484.53)

        # Codigo de autenticidade: real e "CKJGTPTE", mas o OCR le o "J" como "I"
        # (fonte fraca, ambiguidade J/I) — limitacao registrada, char-level, nao
        # corrigivel de forma confiavel. Travamos o comportamento atual.
        assert nfse.codigo_verificacao == "CKIGTPTE"
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
