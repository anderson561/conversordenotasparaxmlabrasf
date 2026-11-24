# -*- coding: utf-8 -*-
"""Guarda — NFS-e de São Paulo ESCANEADA nº 00133661 (ESCRITORIO IMOBILIARIO
ADELINO ALVES -> MT PATRIMONIAL, "Digitalização em 6 de nov. de 2026,
09_54_25.pdf", pág. 1).

Na regressão da correção Salvador "5 lido 6" (GUARAJUBA MALLS pág. 4) esta
nota saiu com a discriminação "COMISSAO RET. IMP. RENDA: 79,43" em vez de
"COMISSAO | RET. IMP. RENDA: 79,43 | Es cabo ...". Investigação (2026-11-24):
NÃO é efeito do código Salvador — a nota é SP, nenhum caminho "5 lido 6"
roda nela (mesma sequência de chamadas ao Tesseract e mesmo texto na base e
na branch). A diferença vem da releitura da caixa de discriminação
(`_ocr_recut_discriminacao_sao_paulo`, render 4x ~131 Mpx) que, quando
falha (exceção engolida -> ""), deixa a leitura de página inteira — o que
já aconteceu também na main (execuções repetidas divergentes).

TEXTO_RECORTE_OK / TEXTO_RECORTE_FALHOU são cópias literais de
`SPPdfExtractor._ocr_page(0)` da nota real nas duas situações."""
import os

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor

TEXTO_RECORTE_OK = '* pet E mo e OND o a\n\nNúmero da Nota\n\nPREFEITURA DO MUNICÍPIO DE SÃO PAULO 00133661\nData e Hora de Emissão\nSECRETARIA MUNICIPAL DA FAZENDA 03/11/2026 11:57:50\nNOTA FISCAL ELETRÔNICA DE SERVIÇOS - NFS-e Código de Verificação\nRPS Nº 2667 Série RTNT, emitido em 30/10/2026 ICKV-MSRF\n\n0261103U61455523000117\n\n2\nIdentificador Nacional: 35503081261455523000117000000013366126112041862346\n\nPRESTADOR DE SERVIÇOS\nCPF/CNPJ: 61.455.523/0001-17 Inscrição Municipal: 1.148.750-0\n1 Nome/Razão Social: ESCRITORIO IMOBILIARIO ADELINO ALVES LTDA\n\n| | Endereço: R JOAQUIM FLORIANO 00888, 9 ANDAR - ITAIM BIBI - CEP: 04534-003\nADELINO ALVES Município: São Paulo UF: SP\n\nIMÓVEIS 4 CRECI 14\n\nTOMADOR DE SERVIÇOS\nNome/Razão Social: MT PATRIMONIAL S/C LTDA\nCPF/CNPJ: 01.523.437/0001-72 Inscrição Municipal: ----\nEndereço: RUA MARQUES DE CARAVELAS 376, 2 ANDAR - BARRA - CEP: 40140-240\nMunicípio: Salvador UF: BA E-mail: pglisboa(mterra.com.br\n\nINTERMEDIÁRIO DE SERVIÇOS\nCPF/CNPJ: ---- Nome/Razão Social: ----\n\nDISCRIMINAÇÃO DE SERVIÇOS\nCOMISSAO |\nRET. IMP. RENDA: 79,43 |\nEs cabo ho a cito E ES Sdurinado qm ao SRS o RES Te O ct do TODAS 5 O GA ar Ap de Re gi 17, SEBO Fa E qm o o\n| VALOR TOTAL DO SERVIÇO = R$ 5.295,24\nContribuição Previdenciária - Retida (R$) | IRRF (R$) COFINS (R$) PIS/PASEP (R$) IPI (R$)\n| 0,00 0,00 0,00 0,00 0,00\n\nContribuições Sociais - Retidas (R$) Descrição Contribuições Sociais - Retidas |\n\n(1) Esta NFS-e foi emitida com respaldo na Lei nº 14.097/2005; (2) Esta NFS-e substitui o RPS Nº 2667 Série RTNT, emitido em 30/10/2026; (3) Data\nde vencimento do ISS desta NFS-e: 10/11/2026; |\n\na | |\n\n0,00 O - PIS/COFINS/CSLL Não Retidos.\nCódigo do Serviço |\n03212 - Administração de imóveis, exceto se realizada via plataforma digital)!\n| Valor Total das Deduções (R$) Base de Cálculo (R$) | Alíquota (%) | Valor do ISS (R$) | Crédito Programa da NFP (R$)\nê 0,00 | 5.295,24 2,00% | 264,76 0,00.\n| Município de Prestação do Serviço Número Inscrição da Obra Valor Aproximado dos Tributos / Fonte |\nOUTRAS INFORMAÇÕES |\n\n|\n|\n|\n'

TEXTO_RECORTE_FALHOU = '* pet E mo e OND o a\n\nNúmero da Nota\n\nPREFEITURA DO MUNICÍPIO DE SÃO PAULO 00133661\nData e Hora de Emissão\nSECRETARIA MUNICIPAL DA FAZENDA 03/11/2026 11:57:50\nNOTA FISCAL ELETRÔNICA DE SERVIÇOS - NFS-e Código de Verificação\nRPS Nº 2667 Série RTNT, emitido em 30/10/2026 ICKV-MSRF\n\n0261103U61455523000117\n\n2\nIdentificador Nacional: 35503081261455523000117000000013366126112041862346\n\nPRESTADOR DE SERVIÇOS\nCPF/CNPJ: 61.455.523/0001-17 Inscrição Municipal: 1.148.750-0\n1 Nome/Razão Social: ESCRITORIO IMOBILIARIO ADELINO ALVES LTDA\n\n| | Endereço: R JOAQUIM FLORIANO 00888, 9 ANDAR - ITAIM BIBI - CEP: 04534-003\nADELINO ALVES Município: São Paulo UF: SP\n\nIMÓVEIS 4 CRECI 14\n\nTOMADOR DE SERVIÇOS\nNome/Razão Social: MT PATRIMONIAL S/C LTDA\nCPF/CNPJ: 01.523.437/0001-72 Inscrição Municipal: ----\nEndereço: RUA MARQUES DE CARAVELAS 376, 2 ANDAR - BARRA - CEP: 40140-240\nMunicípio: Salvador UF: BA E-mail: pglisboa(mterra.com.br\n\nINTERMEDIÁRIO DE SERVIÇOS\nCPF/CNPJ: ---- Nome/Razão Social: ----\n\nDISCRIMINAÇÃO DE SERVIÇOS\nCOMISSAO\nRET. IMP. RENDA: 79,43\n\n| VALOR TOTAL DO SERVIÇO = R$ 5.295,24\nContribuição Previdenciária - Retida (R$) | IRRF (R$) COFINS (R$) PIS/PASEP (R$) IPI (R$)\n| 0,00 0,00 0,00 0,00 0,00\n\nContribuições Sociais - Retidas (R$) Descrição Contribuições Sociais - Retidas |\n\n(1) Esta NFS-e foi emitida com respaldo na Lei nº 14.097/2005; (2) Esta NFS-e substitui o RPS Nº 2667 Série RTNT, emitido em 30/10/2026; (3) Data\nde vencimento do ISS desta NFS-e: 10/11/2026; |\n\na | |\n\n0,00 O - PIS/COFINS/CSLL Não Retidos.\nCódigo do Serviço |\n03212 - Administração de imóveis, exceto se realizada via plataforma digital)!\n| Valor Total das Deduções (R$) Base de Cálculo (R$) | Alíquota (%) | Valor do ISS (R$) | Crédito Programa da NFP (R$)\nê 0,00 | 5.295,24 2,00% | 264,76 0,00.\n| Município de Prestação do Serviço Número Inscrição da Obra Valor Aproximado dos Tributos / Fonte |\nOUTRAS INFORMAÇÕES |\n\n|\n|\n|\n'

DISC_MAIN = ("COMISSAO | RET. IMP. RENDA: 79,43 | Es cabo ho a cito E ES Sdurinado qm ao SRS o RES Te O "
             "ct do TODAS 5 O GA ar Ap de Re gi 17, SEBO Fa E qm o o")


def _parse(monkeypatch, texto):
    dummy_path = "tests/dummy_sp_00133661_guarda.pdf"
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: texto)
    try:
        notas = SPPdfExtractor(dummy_path).parse_multiple()
        assert len(notas) == 1
        return notas[0]
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_texto_real_sai_como_na_main(monkeypatch):
    n = _parse(monkeypatch, TEXTO_RECORTE_OK)
    assert n.numero == "00133661"
    assert n.discriminacao == DISC_MAIN
    assert n.prestador.cnpj_cpf == "61455523000117"
    assert n.tomador.cnpj_cpf == "01523437000172"
    # Nada da correção Salvador "5 lido 6" toca esta nota.
    assert not any('5' in a and '6' in a and ('troca' in a or 'lê o dígito' in a) for a in n.avisos)
    assert not any('1ª linha ilegível' in a for a in n.avisos)


def test_cnpjs_validos_nao_disparam_troca_5_6():
    e = SPPdfExtractor.__new__(SPPdfExtractor)
    assert e._cnpj_salvador_5_lido_6('61.455.523/0001-17') is None
    assert e._cnpj_salvador_5_lido_6('01.523.437/0001-72') is None
    assert 'SSA_' not in TEXTO_RECORTE_OK


def test_saida_curta_vem_so_da_falha_do_recorte_sp(monkeypatch):
    # O mesmo parser, com o recorte SP ausente, dá exatamente o valor visto
    # na "regressão" — a variação é do OCR, não da correção Salvador.
    n = _parse(monkeypatch, TEXTO_RECORTE_FALHOU)
    assert n.discriminacao == "COMISSAO RET. IMP. RENDA: 79,43"
