# -*- coding: utf-8 -*-
"""Texto REAL do OCR (Tesseract) da DANFSe Nacional v2.0 (pós-reforma
tributária) nº 5, SBS SOLUÇÕES INTEGRADAS DE SEGURANÇA ELETRÔNICA LTDA ->
BONI TRANSPORTES, LOGÍSTICA E COMÉRCIO LTDA (Lauro de Freitas/BA), PDF
escaneado. Reportado pelo usuário (2026-09-15) como "um prestador não
identificado" — o XML saía com CNPJ `00000000000000` e RazãoSocial
"Prestador Não Identificado" para AMBAS as entidades, apesar de CNPJ/razão/
endereço de prestador e tomador estarem perfeitamente legíveis na imagem.

Causa raiz nº 1 — separador degradado do rótulo do tomador: o OCR lê a barra
de "TOMADOR / ADQUIRENTE" como "TOMADOR |! ADQUIRENTE" (o "/" vira dois
caracteres de ruído). O rótulo exigia a barra literal, então `m_tom` nunca
casava — e, como o bloco do PRESTADOR usa `m_tom.start()` como limite e o do
TOMADOR usa `m_tom.end()` como início, as DUAS entidades saíam com bloco
vazio de uma vez só. **Fix:** o separador passa a tolerar qualquer sequência
curta de pontuação/ruído entre as duas palavras.

Causa raiz nº 2 — colunas fundidas numa única linha: em vez das colunas
"Nome / Nome Empresarial", "Município / Sigla UF" e "Código IBGE / CEP"
caírem em linhas separadas (padrão de uma nota já validada, nº 11), aqui o
OCR funde TUDO numa única linha de rótulos, seguida de uma única linha de
valores ("<razão> <município> / <UF> <IBGE> <sep> <CEP>"). **Fix:** quando
falta razão OU município, tenta recuperar de uma linha "fundida" —
usando o próprio código IBGE já impresso na linha como prova de onde a
razão termina e o nome do município começa (testado contra o resolver de
IBGE, não por contagem de palavras: nomes de município têm de 1 a 4+
palavras e um corte por regex puro é ambíguo — aqui "Freitas"/"de Freitas"
sozinhos resolveriam, errado, para Salvador; só "Lauro de Freitas" completo
bate o código "2919207" impresso na nota).

Causa raiz nº 3 — fim de bloco do tomador nunca reconhecido: a palavra
"OPERAÇÃO" sai tão degradada ("O) ÃO", "OPER O") que nem "DESTINATÁRIO DA
OPERAÇÃO" nem "INTERMEDIÁRIO DA OPERAÇÃO" batem o padrão original — sem um
fim de bloco reconhecido, a busca do CNPJ do tomador vazava para o RESTO do
documento inteiro e encontrava 11 dígitos da própria Chave de Acesso
(impressa de novo no rodapé), aceitando-os como se fossem o CNPJ do tomador
— um valor plausível-porém-ERRADO, pior que o sentinela. **Fix:** "IDENTIFICADO
NA NFS" (frase de status que sobrevive íntegra em ambas as linhas
degradadas) foi adicionada como marcador de fim mais resiliente.

Causa raiz nº 4 — dígito trocado no início do CNPJ do tomador: o "0" inicial
de "04.555.283/0003-50" sai como a letra "D" ("D4.555.283/0003-50"). **Fix:**
tolerância pontual "D"/"O" -> "0" só na posição inicial, aceita apenas se o
checksum do CNPJ corrigido for válido (nunca aceita lixo sem essa validação).

O texto abaixo é cópia literal (via `_extract_via_ocr`) da nota real."""
import os

from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_NACIONAL_REFORMA

MOCK_TEXT = (
    ': DANFSe v2.0\n'
    'NFSe Duo etnia Documento Auxiliar da NFS-e\n\n'
    'CHAVE DE ACESSO DA NFS-e\n'
    '29192072246875522000152000000000000526086097254953\n\n'
    'NÚMERO DA NFS-e COMPETÊNCIA DA NFS-e DATA E HORA DA EMISSÃO DA NFS-e\n'
    '5 06/08/2026 06/08/2026 16:02:10\n\n'
    'NÚMERO DA DPS SÉRIE DA DPS DATA E HORA DA EMISSÃO DA DPS\n\n'
    '5 70000 06/08/2026 16:02:10\n\n'
    'pela isitura deste código OR ou pels consulta da\n'
    'EMITENTE DA NFS-e SITUAÇÃO DA NFS-s FINALIDADE chave de acesso no portal nacional da NFS-e\n'
    'Prestador NFS-g Gerada .\n\n'
    'PRESTADOR / FORNECEDOR CNPJ/CPF NIE Indicador Municipal (Inscrição) Telefona\n'
    '46.876.522/0001-52 10041978 (71) 99632-1095\n\n'
    'Nome / Nome Empresarial Município / Sigla UF Código IBGE | CEP\n\n'
    'SBS SOLUCOES INTEGRADAS DE SEGURANCA ELETRONICA ll LTDA Lauro de Freitas / BA 29.19207 ! 42.707-650\n\n'
    'Enderaço Email\n\n'
    'AVN PRAIA DE ITAPOAN, 131, VILAS DO ATLANTICO financoirogisbsgrupo.com.br\n\n'
    'Simples Nacional na Data de Competência Regime de Apuração Tributária pelo SN\n\n'
    'Não optante -\n\n'
    'TOMADOR |! ADQUIRENTE CNPJ/CPF INF Indicador Municipal (Inscrição) Telefone\n'
    'D4.555.283/0003-50 - E\n\n'
    'Nome / Nome Empresarial Municipio | Sigla UF Código IBGE | CEP\n'
    'BONI TRANSPORTES, LOGISTICA E COMERCIO LTDA. Lauro de Freitas / BA 29.19207 | 42.738-205\n\n'
    'Endereço E-mall\n'
    'MARIA QUITERIA, 263, GALPÃO LOT DESMEMBRAMENTO DIAMANTE, [TINGA «\n\n'
    'DESTINATÁRIO DA O) ÃO NÃO IDENTIFICADO NA NFS-€\n'
    'INTERMEDIÁRIO DA OPER O IDENTIFICADO NA NFS-e\n'
    'RVIÇO Código de Tributação Nacional/Municipal Código da NES Local da Prestação | Sigla UF / Pais\n'
    '99.01,01/- - Lauro de Freitas / BA) -\n\n'
    'Serviços sem a incidência de ISSQN e ICMS\n\n'
    'Descrição do Serviço\n\n'
    'CONTRATO Nº [TS BTLC. 014/2024 SBS TEC II]\n\n'
    'COMPETÊNCIA: 09/2025\n\n'
    'LOCAÇÃO DE EQUIPAMENTOS E MONITORAMENTO - R$ 560,51\n\n'
    'VENCIMENTO: 05/09/2026\n\n'
    'FORMA DE PAGAMENTO: BOLETO BANCÁRIO - BANCO DO BRASIL\n\n'
    'DATA CIENTIFI O E ASSINATURA NO NFS / CHAVE NFS-e\n'
    '5 / 29192072246876522000152000000000000526085097254953\n'
)


def _novo_extrator():
    dummy_path = "tests/dummy_sbs_solucoes_5.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = MOCK_TEXT
    extractor.layout = LAYOUT_NACIONAL_REFORMA
    return extractor, dummy_path


def test_prestador_identificado_com_cnpj_e_razao_corretos():
    extractor, dummy_path = _novo_extrator()
    try:
        prestador = extractor._extrair_entidade('Prestador')
        assert prestador.cnpj_cpf == "46876522000152"
        assert prestador.razao_social == "SBS SOLUCOES INTEGRADAS DE SEGURANCA ELETRONICA ll LTDA"
        assert prestador.endereco.municipio == "Lauro de Freitas"
        assert prestador.endereco.uf == "BA"
        assert prestador.endereco.codigo_municipio == "2919207"
    finally:
        os.remove(dummy_path)


def test_tomador_identificado_com_cnpj_corrigido_e_razao_correta():
    extractor, dummy_path = _novo_extrator()
    try:
        tomador = extractor._extrair_entidade('Tomador')
        # CNPJ real "04.555.283/0003-50" (o "0" inicial saiu como "D" no OCR).
        assert tomador.cnpj_cpf == "04555283000350"
        assert "BONI TRANSPORTES" in tomador.razao_social.upper()
        assert tomador.endereco.municipio == "Lauro de Freitas"
        assert tomador.endereco.codigo_municipio == "2919207"
    finally:
        os.remove(dummy_path)


def test_tomador_cai_no_sentinela_quando_cnpj_corrigido_reprova_checksum():
    # Não deve aceitar QUALQUER letra solta antes de um CNPJ mal formatado
    # como se fosse sempre um "0" -- só quando o checksum resultante bate.
    texto = MOCK_TEXT.replace('D4.555.283/0003-50 - E', 'D4.555.283/0003-51 - E')
    extractor, dummy_path = _novo_extrator()
    extractor.raw_text = texto
    try:
        tomador = extractor._extrair_entidade('Tomador')
        assert tomador.cnpj_cpf == "00000000000000"
    finally:
        os.remove(dummy_path)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
