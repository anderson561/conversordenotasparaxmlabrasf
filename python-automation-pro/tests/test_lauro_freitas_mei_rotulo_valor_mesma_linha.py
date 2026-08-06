# -*- coding: utf-8 -*-
"""Lauro de Freitas/BA escaneado — rótulo e valor na MESMA linha (MEI/Simples
com Alíquota/ISS "inutilizados") quebrava valor, razão social e município.

Nota real nº 20264631 (ALFA MEDICAL MEDICINA E SEGURANÇA DO TRABALHO LTDA MEI
-> SÃO PEDRO CONSTRUTORA), pág. 6 do lote "NFS HJHJ.pdf". Duas causas
independentes, ambas no mesmo layout `lauro_de_freitas_ba`:

1) VALOR ZERO: a nota é MEI/Simples Nacional com Alíquota (%) e Valor do ISS
   "inutilizados" (art. 57 §2º I da Resolução 94 do CGSN) — a face imprime "*"
   nessas 2 células em vez de "0,00". O OCR colapsa os DOIS asteriscos em UM só
   ao linearizar a grade ("0,00 283,39 * Não"), e a regex estrita (que exige 4
   grupos NUMÉRICOS) nunca casa — a extração cai no fallback zero para TUDO,
   inclusive a Base de Cálculo (283,39, um número real). Além disso, a âncora
   "VALOR TOTAL DA NOTA FISCAL" (linha própria, seção "ATIVIDADE") não
   sobrevive a este OCR. Fix: fallback tolerante que exige só Dedução/Base
   (sempre numéricos) e trata Alíquota/ISS ausentes da região intermediária
   como 0,00 (fiel à face — inutilizado, não erro de leitura); com Base
   correta, o fallback já existente (val_serv = base quando o total não é
   encontrado) resolve o valor sozinho.

2) RAZÃO/ENDEREÇO/MUNICÍPIO CORROMPIDOS (silencioso para o prestador — o aviso
   só existe para o tomador): esta variante do scan imprime rótulo+valor na
   MESMA linha ("Nome/Razão SAO PEDRO CONSTRUTORA LTDA", sem quebra), mas as
   regexes de Nome/Razão, Endereço e Inscrição exigiam `\n+` (quebra
   obrigatória) — caíam nos sentinelas "Prestador/Tomador Não Identificado" e
   "Não informado" com o valor real presente no texto. Bairro/Município também
   compartilham LINHA com o rótulo seguinte ("Bairro: Centro Município: LAURO
   DE FREITAS UF: BA") — a captura genérica até fim-de-linha vazava o rótulo
   seguinte inteiro para dentro do valor, e o município corrompido
   ("LAURO DE FREITAS UF: BA") não casava `KNOWN_CITIES`, caindo no fallback
   de capital (Salvador, 2927408) em vez de Lauro de Freitas (2919207) — Forma
   B do gotcha de colisões. Fix: `\n+` -> `\n*` (tolera rótulo+valor na
   mesma linha) e captura de Bairro/Município não-greedy com lookahead pro
   próximo rótulo conhecido.

Baseline-vs-fix no PDF completo (8 notas): só esta nota difere; as outras 7
são byte-idênticas.
"""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_OCR = 'MUNICIPIO DE LAURO DE FREITAS Número da Nota\nSecretaria da Fazenda 20264631\n\nCoordenação Tributária Data e Hora de Emissão\n\nNota Fiscal de Serviços Eletrônica - NFS-e 07/07/2026 14:43:08\n\nCódigo de Verificação\n\nA autenticidade desta Nota Fiscal de Serviços Eletrônica, poderá ser confirmada na página da MUNICIPIO DE LAURO DE FREITAS na Internet, no 1B24A47C1\nendereço http:/Anww.laurodefreitas.ba.gov.br ou através da leitura do QR Code.\n\nPRESTADOR DE SERVIÇOS\n\nCPF/CNPJ: 03.731.506/0001-69 Inscrição Estadual\n\nInscrição 0010027464\n\nNome/Razão ALFA MEDICAL MEDICINA E SEGURANÇA DO TRABALHO LTDA\n\nEndereço: Rua Maria Isabel Dos Santos, 222, 2 ANDAR\n\nBairro: Centro Município: LAURO DE FREITAS UF: BA\nCEP: 42700-130 Email: ALFAMEDICINADOTRABALHOGGMAIL.\nTOMADOR DE SERVIÇOS\n\nCPF/CNPJ/CRI: 03.051.741/0001-90\n\nInscrição 0000353043 Inscrição Estadual:\nNome/Razão SAO PEDRO CONSTRUTORA LTDA\n\nEndereço: AVENIDA Praia De Pajussara, 554, QD. 28, LT. 09\n\nBairro: Vilas Do Atlântico Município: LAURO DE FREITAS\n\nCEP: 42708-720 Email:\n\nLOCAL DA PRESTAÇÃO DO(S) SERVIÇO(S): LAURO DE FREITAS - BA\n\nDISCRIMINAÇÃO DOS SERVIÇOS\nSERVICOS EM SAUDE\n\nSão Pedro Construtora\n(0) is ]\nSienge\n\nATIVIDADE\n\n0008630599 - Atividades De Atenção Ambulatorial Não Especi\nITEM DA LISTA DE SERVIÇOS: (Lei Municipal 1572/2015 )\n040101 - Medicina.\n\nValor Total Deduções (R$) Base de Cálculo (R$) Alíquota (%) Valor do ISS (R$) ISSQN Retido (R$)\n0,00 283,39 * Não\n\nRETENÇÃO DE IMPOSTOS\n\nPIS (R$) COFINS (R$) INSS (R$) IRRF (R$): CSLL (R$): OUTRAS RETENÇ\n0,00 0,00 0,00 0,00 0,00\n\nVALOR LÍQUIDO DA NOTA FISCAL : R$ 283,39\n\nINFORMAÇÕES COMPLEMENTARES\n\nCompetência: 07/2026 - Tributado no Município de Lauro de Freitas - Não Retido\nNBS: 123012100 - Serviços de clínica médica\n\nBenefício Municipal: -\n\nOptante pelo Simples Nacional - Inutilização dos campos destinados à base de cálculo e ao imposto(art.57, 82º, | da\nResolução 94 do CGSN)\n\n'


def test_lauro_freitas_mei_rotulo_valor_mesma_linha(monkeypatch):
    dummy_path = "tests/dummy_lauro_freitas_mei.pdf"
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
        assert nfse.numero == "20264631"

        # BUG CORRIGIDO 1 — valor: antes 0.0 (fallback zero em cascata).
        assert nfse.valores.valor_servicos == 283.39
        assert nfse.valores.base_calculo == 283.39
        assert nfse.valores.valor_liquido_nfse == 283.39
        assert nfse.valores.aliquota == 0.0  # inutilizado (MEI), não erro
        assert nfse.valores.valor_iss == 0.0

        # BUG CORRIGIDO 2 — prestador: antes "Prestador Não Identificado".
        p = nfse.prestador
        assert p.cnpj_cpf == "03731506000169"
        assert p.razao_social.startswith("ALFA MEDICAL")
        assert p.inscricao_municipal == "0010027464"
        assert p.endereco.logradouro == "Rua Maria Isabel Dos Santos"
        assert p.endereco.numero == "222"
        assert p.endereco.bairro == "Centro"
        # Município não pode vazar o rótulo "UF:" colado na mesma linha.
        assert p.endereco.municipio == "LAURO DE FREITAS"
        assert p.endereco.codigo_municipio == "2919207"  # antes 2927408 (Salvador)
        assert p.endereco.uf == "BA"

        # BUG CORRIGIDO 3 — tomador: antes "Tomador Não Identificado".
        tm = nfse.tomador
        assert tm.cnpj_cpf == "03051741000190"
        assert tm.razao_social == "SAO PEDRO CONSTRUTORA LTDA"
        assert tm.endereco.codigo_municipio == "2919207"

        # Sem avisos de dado não identificado / valor zero.
        assert nfse.avisos == []
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
