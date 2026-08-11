# -*- coding: utf-8 -*-
"""Lauro de Freitas/BA escaneado — ISSQN devido em OUTRO município (LC 116/2003
art. 3º III), obra fora da sede do prestador.

Nota real nº 202645 (ADRIAN NASCIMENTO DE JESUS -> SAO PEDRO CONSTRUTORA),
arquivo "2026-07-17 15.16 TINY SCANNER.pdf". A nota indica explicitamente
"LOCAL DA PRESTAÇÃO DO(S) SERVIÇO(S): SALVADOR - BA" e "Competência: ... -
Tributado fora do Município de Lauro de Freitas - ...", mas o
`Servico/CodigoMunicipio`/`MunicipioIncidencia` saíam com o município do
PRESTADOR (Lauro de Freitas, 2919207) em vez de Salvador (2927408) — o
mecanismo de override (`_extrair_municipio_incidencia_override`) já existia
mas só cobria LAYOUT_GUARULHOS, cujo rótulo/frase-gatilho são ligeiramente
diferentes ("Tributação fora do município" / "Local da Prestação:" sem
"DO(S) SERVIÇO(S)" no meio).
"""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
from src.transformers.abrasf_transformer import Abrasf201Transformer

MOCK_OCR = 'Número da Nota\n202645\nData e Hora de Emissão\n10/07/2026 09:57:18\nCódigo de Verificação\nFFEFABO5O\n\nMUNICIPIO DE LAURO DE FREITAS\nSecretaria da Fazenda\nCoordenação Tributária\n\nNota Fiscal de Serviços Eletrônica - NFS-e\n\nA autenticidade desta VA de Serviços Eletrônica, poderá ser confirmada na página da MUNICIPIO DE LAURO DE FREITAS na Intemet, no\nendereço http:/mwwlaurodefreitas.ba.gov.br ou através da leitura do QR Code.\n\nPRESTADOR DE SERVIÇOS\nCPF/CNPJ: 55.725.847/0001-25\n\nInscrição Estadual\n\nInscrição 0010046860\nNome/Razão ADRIAN NASCIMENTO DE JESUS\n\nEndereço: Rua Mucugê, 133\n\nBairro: Centro Município: LAURO DE FREITAS UF: BA\n\nCEP: 42702-820 Email: exatacontabil83OOgmail.com\n\nTOMADOR DE SERVIÇOS\nCPFICNPJICRI: 03.051.741/0001-90\n\nInscrição 0000353043\n\nNome/Razão SAO PEDRO CONSTRUTORA LTDA\n\nEndereço: AVENIDA Praia De Pajussara, 554, QD. 28, LT. 09\nBairro: Vilas Do Atlântico Município: LAURO DE FREITAS\n\nInscrição Estadual:\n\nUF: BA\n\nEmail:\n\nCEP: 42708-720\nLOCAL DA PRESTAÇÃO DO(S) SERVIÇO(S): SALVADOR - BA\n\nDISCRIMINAÇÃO DOS SERVIÇOS\n\nReferente medicao final, quitacao do contrato de servicos de remocao de telha existente e instalacao de telhas novas tipo sanduiche, tratamento\nde estrutura e substituicao de calhas e rufos com decapoxil e posterior pintura com zarcao. Responsavel Bruna Dados bancarios Chave Pix CNPJ\n\n55725847000125 Instituicao Banco do Brasil\n\n4\nLA\n\nEng. Victor Hage Carmo\n\nCREA-BA 18166/D\n\nNeronte de Obra\n\nVALOR TOTAL DA NOTA FISCAL : R$ 15.000,00 e 1/0\n\nATIVIDADE\n0004399199 - Serviços Especializados Para Construção Não E\n\nITEM DA LISTA DE SERVIÇOS: (Lei Municipal 1572/2015 )\n070202 - Execução, por empreitada ou subempreltada, de obras de construção civil, hidráulica ou elétrica e de outras obras\nsemelhantes, inclusive sondagem, perfuração de poços, escavação, drenagem e Irrigação,\n\nValor Total Deduções (R$) Base de Cálculo (R$) Alíquota (%) Valor do ISS (R$) ISSQN Retido (R$)\nR$ 0,00 R$ 15.000,00 * * Não\n\nRETENÇÃO DE IMPOSTOS\n\n15.000,00\n\nVALOR Sica DA NOTA FISCAL : R$\n\nINFORMAÇÕES COMPLEMENTARES\nCompetência: 07/2026 - Tributado fora do Município de Lauro de Freitas - Não Retido\nNBS: 101012900 - Serviços de construção de edificações não residenciais não classificados em subposições anteriores\n\nBenefício Municipal: -\nOptante pelo Simples Nacional - Inutilização dos campos destinados à base de cálculo e ao imposto(art.57, 82º, | da\n\nResolução 94 do CGSN)\n\n'


def test_lauro_freitas_municipio_incidencia_fora_da_sede(monkeypatch):
    dummy_path = "tests/dummy_lauro_freitas_incidencia_fora.pdf"
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
        assert nfse.numero == "202645"

        # Endereços das entidades continuam Lauro de Freitas (sede de cada uma) —
        # só a INCIDÊNCIA do ISSQN muda para o local da obra.
        assert nfse.prestador.endereco.codigo_municipio == "2919207"
        assert nfse.tomador.endereco.codigo_municipio == "2919207"

        # BUG CORRIGIDO: incidência do ISSQN vai para Salvador (2927408), não
        # para a sede do prestador (Lauro de Freitas, 2919207).
        assert nfse.municipio_incidencia_override == "2927408"

        xml = Abrasf201Transformer().transform(nfse)
        assert xml.count("<CodigoMunicipio>2927408</CodigoMunicipio>") == 1
        assert "<MunicipioIncidencia>2927408</MunicipioIncidencia>" in xml
        # Endereços do prestador/tomador/órgão gerador continuam Lauro de Freitas.
        assert xml.count("<CodigoMunicipio>2919207</CodigoMunicipio>") == 3
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
