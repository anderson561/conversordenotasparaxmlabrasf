# -*- coding: utf-8 -*-
"""LUNITECK - SOLUÇÕES E DESENVOLVIMENTO EM TECNOLOGIA LTDA - ME (CNPJ real
07.295.620/0001-44, checksum válido) é prestadora recorrente em Salvador/BA,
confirmada por recorte em zoom 4x, pixel a pixel, em DUAS notas
independentes (LUNITECK 2436 e 2437): mesma razão social, mesmo endereço,
letra por letra idênticos nas duas imagens.

Achado real (lote reportado pelo Domínio — "Relatório do Resumo da
Importação"): (1) nota 2437 tem a linha inteira do CNPJ AUSENTE do texto OCR
entre o rótulo "Inscrição Municipal" e "Nome/Razão Social" — sem nenhum
dígito para o `_scavenge_all_cnpjs` recuperar, o campo cai no sentinela
`00000000000100` (Domínio: "CNPJ do fornecedor inválido, conteúdo
'00000000000100'"); (2) nota 2436 tem o CNPJ correto, mas a captura de razão
social gruda no resto da linha de Inscrição Municipal em vez de pular para a
linha seguinte com o nome real ("da - SOLUCOES E DESENVOLVIMENTO EM
TECNOLOGIA LTDA - ME N aç", sem o prefixo "LUNITECK" e com ruído de OCR no
fim) — a raiz é a própria Inscrição Municipal impressa nesta nota
("00.384.869/001.50") ter formato parecido com CNPJ, confundindo a
heurística de "primeira linha que não é o rótulo". Mesmo princípio já usado
para BONI TRANSPORTES/GUARAJUBA SHOPPING: substitui CNPJ + razão social +
endereço completo (também pixel-confirmado) quando o CNPJ já é exatamente o
real OU quando o checksum reprovou e a razão social bate com esta
contraparte conhecida — nunca mascarando um CNPJ genuinamente diferente de
outra empresa.

Textos OCR abaixo são cópia literal (via `_extract_via_ocr`) do bloco do
PRESTADOR das duas notas reais."""
import os

from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_SALVADOR

MOCK_TEXT_2436 = (
    'PRESTADOR DE SERVIÇOS\n'
    'CPFACNPJ inserção Municipal\n'
    '07.295 .620/0001-44 00.384.869/001.50 EB\n'
    'Nomeirarão Soſial\n'
    'da - SOLUCOES E DESENVOLVIMENTO EM TECNOLOGIA LTDA - ME N aç\n'
    'Tidereço ª\n'
    'ro. Alta Coari AGpiNdica 2801 – EDIF PROFISSIONAL CENTER SALA - BROTAS - Salvador - CEF: 40280-801 -\n'
    'Tua\n'
    'efbluniteck com\n'
    'TOMADOR DE SERVIÇOS\n'
    'NormeiRação Social\n'
    'BONI TRANSPORTES. LOGISTICA E COMERCIO LTDA.\n'
    'CPEACNPJ Inscrição Municipal\n'
    '04,555 293/0003-50 º\n'
    'Endereço\n'
    'RUA MÁRIA QUITERIA 265, GALPAO ITINGA - Lauro de Freitas - CEP: 42738-Z05/BA\n'
    'E-mail\n'
    'POSTOS(NORTECCONTABILIDADE. COM.BR\n'
    'PISSRIMINAÇÃO DOS SERVIÇOS\n'
    'TEib. Aprox. tab. A. III - 8H, R$ 73,83\n'
    'VALOR TOTAL DA NOTA = R$397,14\n'
    'CNAE:\n'
    '9511800 - Reparação e manutenção\n'
)

MOCK_TEXT_2437 = (
    'PRESTADOR DE SERVIÇOS\n'
    'CPFANPJ inserção Municipal!\n'
    'NomelRerão Social &\n'
    'LUNITECK - SOLUCOES E DESENVOLVIMENTO TECNOLOGIA LTDA - ME Geª\n'
    'Erders!\n'
    'Ave Ariônio Carlos Magalhães 2501 – EDIF PROFISSIONAL CENTER SALA - BROTAS - Salvador - CEP: 40280-901 -\n'
    'ii\n'
    'nfefyluniteck com\n'
    'TOMADOR DE SERVIÇOS\n'
    'Norme/Razão Social\n'
    'BONI TRANSPORTES, LOGISTICA E COMERCIO LTDA.\n'
    'GPEICNPJ Insorição Municipal\n'
    '04.565 .283/0003-50 EA\n'
    'Enderoço\n'
    'RUA MÁs QUITERIA 253, GALPÃO ITINGA - Lauro de Freltas – CEP: 42738-Z05/BA\n'
    'E-mesl\n'
    'IMPOSTOSGBNORTECCONTABIL IDADE. COM.BR\n'
    'PISSRININAÇÃO POS SERVICOS\n'
    'Teib. Aprox. tab, A. III SN. R$ 23,53\n'
    'VALOR TOTAL DA NOTA = R$397,14\n'
    'CNAE\n'
    '9511800 - Reparação e manutenção de computadores e de equipamentos\n'
)


def _novo_extrator(texto, nome):
    dummy_path = f"tests/dummy_{nome}.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = texto
    extractor.layout = LAYOUT_SALVADOR
    return extractor, dummy_path


def test_luniteck_2436_cnpj_correto_apesar_de_razao_social_garblada():
    # CNPJ já sai correto do OCR nesta nota (a linha sobrevive); o bug era só
    # na razão social, que grudava no resto da linha de Inscrição Municipal.
    extractor, dummy_path = _novo_extrator(MOCK_TEXT_2436, "luniteck_2436")
    try:
        prestador = extractor._extrair_entidade('Prestador')
        assert prestador.cnpj_cpf == "07295620000144"
        assert prestador.razao_social == "LUNITECK - SOLUÇÕES E DESENVOLVIMENTO EM TECNOLOGIA LTDA - ME"
    finally:
        os.remove(dummy_path)


def test_luniteck_2437_cnpj_recuperado_quando_linha_ausente_do_ocr():
    # A linha inteira do CNPJ está ausente do OCR nesta nota — sem a
    # correção, cai no sentinela 00000000000100 (erro reportado pelo Domínio:
    # "CNPJ do fornecedor inválido, conteúdo '00000000000100'").
    extractor, dummy_path = _novo_extrator(MOCK_TEXT_2437, "luniteck_2437")
    try:
        prestador = extractor._extrair_entidade('Prestador')
        assert prestador.cnpj_cpf == "07295620000144"
        assert prestador.razao_social == "LUNITECK - SOLUÇÕES E DESENVOLVIMENTO EM TECNOLOGIA LTDA - ME"
    finally:
        os.remove(dummy_path)


def test_luniteck_endereco_completo_restaurado():
    # Endereço também pixel-confirmado (idêntico nas duas notas reais) —
    # o texto OCR sozinho não é confiável o bastante para reconstruí-lo
    # (ex.: nota 2436 lê "ro. Alta Coari AGpiNdica 2801", nada parecido
    # com "Ave Antônio Carlos Magalhães 2501").
    extractor, dummy_path = _novo_extrator(MOCK_TEXT_2436, "luniteck_end")
    try:
        prestador = extractor._extrair_entidade('Prestador')
        assert prestador.endereco.logradouro == "Ave Antônio Carlos Magalhães"
        assert prestador.endereco.numero == "2501"
        assert prestador.endereco.bairro == "Brotas"
        assert prestador.endereco.municipio == "Salvador"
        assert prestador.endereco.uf == "BA"
        assert prestador.endereco.cep == "40280901"
    finally:
        os.remove(dummy_path)


def test_correcao_nao_sobrescreve_cnpj_ja_valido_de_outra_empresa():
    # Guard não deve disparar para um CNPJ já válido de outra empresa
    # qualquer (nunca sobrescreve um valor que já passou no checksum e não
    # é o da LUNITECK).
    texto = MOCK_TEXT_2436.replace(
        '07.295 .620/0001-44 00.384.869/001.50 EB\n'
        'Nomeirarão Soſial\n'
        'da - SOLUCOES E DESENVOLVIMENTO EM TECNOLOGIA LTDA - ME N aç\n',
        '11.222.333/0001-81\nNome/Razão Social\nOUTRA EMPRESA QUALQUER LTDA\n',
    )
    extractor, dummy_path = _novo_extrator(texto, "luniteck_outra_empresa")
    try:
        prestador = extractor._extrair_entidade('Prestador')
        assert prestador.cnpj_cpf == "11222333000181"
        assert prestador.razao_social == "OUTRA EMPRESA QUALQUER LTDA"
    finally:
        os.remove(dummy_path)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
