# -*- coding: utf-8 -*-
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
import os

# Texto REAL do OCR (Tesseract, via _extract_via_ocr) da nota "ISBET - 1799.pdf":
# "NOTA DE CONTRIBUIÇÃO SOLIDÁRIA" do Instituto Brasileiro Pró Educação, Trabalho
# e Desenvolvimento (ISBET, Rio de Janeiro/RJ) - documento de repasse do programa
# Jovem Aprendiz, cobrando de BONI TRANSPORTES (o "USUÁRIO DOS SERVIÇOS") a
# receita institucional de agosto/2026. Preservado verbatim, incluindo os quirks
# que travam regressões:
#  - o CNPJ do ISBET sai ERRADO nesta leitura de página inteira ("43.125.366",
#    dígito 5 no lugar do 6) - só um crop em zoom 4x da própria caixa do CNPJ
#    revelou o valor real ("43.126.366/0001-14", validado por checksum); o
#    prestador é FIXO e usa o valor CORRETO, não o que este texto mostra;
#  - o "Nº:SAL-2026-01799" aparece duas vezes, mas por decisão EXPLÍCITA do
#    usuário o Número da Nota vem do "Boleto Nº" ("656956");
#  - a "Relação de Jovens Aprendizes" no fim do documento é só referência (não é
#    a discriminação do serviço, e não deve vazar para o campo Discriminacao);
#  - a linha do item (quantidade/valores unitário e total) sai como puro lixo no
#    OCR de página inteira ("Ds feememenremcoscommmamo | too) 005") - o valor
#    real só é recuperável via `_ocr_recut_instituto_valor` (recorte dedicado em
#    zoom 10x), nunca deste texto de página inteira.
MOCK_TEXT = 'Instituto Brasileiro Pró Educação, Trabalho e\nDesenvolvimento\n\nAv. Embaixador Abelardo Bueno 1111 Bloco 02,\nloja 109 - Rio de Janeiro - Tel: (21) 2122153066\n\nNOTA DE CONTRIBUIÇÃO SOLIDÁRIA\n\nNº:SAL-2026-01799\n\nNatureza dos Jovem Aprendiz\nserviços:\n\nData de Emissão: 19/08/2026 10:12:15\nBoleto Nº:.656956\n\nCNPJ 43.125.366/0001-14\nCNAS R0268/2003 ! CEBAS Portaria nº 248, 20.09.18 - D.O.U, 28.09.2018.\nRegistro Civil Pessoas Jurídicas 86705 LA nº 27\n\nUSUÁRIO DOS SERVIÇOS\n\nNome: BONI TRANSPORTES LOGISTICA E COMERCIO LTDA,\n\nEnd.: Rua Maria Quiteria 263 Galpão Desmembramento Diamante\n\nCEP: 42738205 Bairro: Itinga Município:Lauro de Freitas UF: BA\n\nCNPJ: 04555283000350 IE: 159096901 NO | IM: 10035914 Cond. Pagto: No vencimento contratado\n\nDiscriminação dos serviços | Unitário R$ |\nEM Referente a receita institucional do mês 08/2026 [13000\n\nValor total da\nNota: R$\n\nAtestamos que os serviços constantes nesta Nota de Contribuição Solidária foram executados.\nOs valores desta nota referente a receita institucional, são dedutíveis do IR, conforme art. 13, da Lei 9.249/95,\ncombinado com a Instrução Normativa da Secretaria da Receita Federal 11/1996.\n\nNo:SAL-2026-01799\n\nRelação de Jovens Aprendizes\n\ntania tado HR iai nei sites io bi SS\nNome Fantasia CNPJ Início Fim Ref. VLSalário VLRI Total\nContrato Contrato\n\n———————————————————————eeeeeeeeeeeee es\nREBEKA SENA DA SILVA BONI TRANSPORTES 045552830003 17/07/2025 15/07/2027 08/2026 759,00 130,00 130,00\nJUNQUEIRA LOGISTICA E so\n\nCOMERCIO LTDA\n'

# Texto REAL do recorte dedicado `_ocr_recut_instituto_valor` (zoom 10x, --psm 6,
# faixa "Discriminação" -> "Nota:") para a MESMA nota: a linha do item ainda sai
# parcialmente degradada ("Ds feememenremcoscommmamo | too) 005"), mas o valor
# "130,00" da célula "Valor total da Nota" sobrevive - é dele que o extrator lê,
# pegando o ÚLTIMO número no formato R$ da faixa (nunca o primeiro).
MOCK_RECUT_VALOR = 'Unid | Quant. Discriminação dos serviços Unitário R$ Total R$\nDs feememenremcoscommmamo | too) 005\nValor total da 130,00\nNota: R$\n'


def test_extract_instituto_isbet_layout(monkeypatch):
    dummy_path = "tests/dummy_instituto_isbet.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_TEXT)
    monkeypatch.setattr(SPPdfExtractor, "_ocr_recut_instituto_valor", lambda self: MOCK_RECUT_VALOR)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        # Número da nota: decisão EXPLÍCITA do usuário - "Boleto Nº", NÃO o
        # "Nº:SAL-2026-01799" impresso duas vezes no documento.
        assert nfse.numero == "656956"
        assert nfse.servico_codigo == "0000"
        assert nfse.data_emissao.year == 2026
        assert nfse.data_emissao.month == 8
        assert nfse.data_emissao.day == 19
        assert nfse.data_emissao.hour == 10
        assert nfse.data_emissao.minute == 12
        assert nfse.competencia.year == 2026
        assert nfse.competencia.month == 8

        # Prestador FIXO (ISBET). CNPJ é o valor REAL confirmado por crop de
        # pixel (43.126.366), NÃO o que a página inteira leu (43.125.366) -
        # trava a lição do crop-and-LOOK aplicada a um prestador fixo.
        assert nfse.prestador.cnpj_cpf == "43126366000114"
        assert nfse.prestador.razao_social == "Instituto Brasileiro Pró Educação, Trabalho e Desenvolvimento"
        assert nfse.prestador.endereco.logradouro == "Av. Embaixador Abelardo Bueno"
        assert nfse.prestador.endereco.numero == "1111"
        assert nfse.prestador.endereco.complemento == "Bloco 02, loja 109"
        assert nfse.prestador.endereco.municipio == "Rio de Janeiro"
        assert nfse.prestador.endereco.codigo_municipio == "3304557"
        assert nfse.prestador.endereco.uf == "RJ"
        # CEP não é impresso no letterhead - sentinela, nunca inventado.
        assert nfse.prestador.endereco.cep == "00000000"
        assert nfse.prestador.telefone == "2122153066"

        # Tomador DINÂMICO, extraído do bloco "USUÁRIO DOS SERVIÇOS".
        assert nfse.tomador.cnpj_cpf == "04555283000350"
        assert nfse.tomador.razao_social == "BONI TRANSPORTES LOGISTICA E COMERCIO LTDA"
        assert nfse.tomador.inscricao_municipal == "10035914"
        assert nfse.tomador.endereco.logradouro == "Rua Maria Quiteria"
        assert nfse.tomador.endereco.numero == "263"
        assert nfse.tomador.endereco.complemento == "Galpão Desmembramento Diamante"
        assert nfse.tomador.endereco.bairro == "Itinga"
        assert nfse.tomador.endereco.municipio == "Lauro de Freitas"
        assert nfse.tomador.endereco.uf == "BA"
        assert nfse.tomador.endereco.cep == "42738205"

        assert nfse.intermediario is None

        # Discriminação real (não a tabela "Relação de Jovens Aprendizes").
        assert nfse.discriminacao == "Referente a receita institucional do mês 08/2026"

        # Valor recuperado do recorte dedicado (não sobrevive na página inteira).
        val = nfse.valores
        assert val.valor_servicos == pytest.approx(130.00)
        assert val.valor_liquido_nfse == pytest.approx(130.00)
        assert val.valor_iss == 0.0
        assert val.aliquota == 0.0
        assert val.base_calculo == 0.0

        assert not any("zero" in a.lower() for a in nfse.avisos)
        assert any("dedutíveis do IR" in a for a in nfse.avisos)
        assert any("CEP do prestador" in a for a in nfse.avisos)
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_detect_layout_page_instituto():
    """`_detect_layout_page` (usado na divisão de lotes multi-página) precisa
    da MESMA marca de detecção de `_detect_layout` - testado em separado
    porque o teste principal, de uma nota isolada, nunca exercita o
    detector por-página."""
    dummy_path = "tests/dummy_instituto_page_detect.pdf"
    import os as _os
    _os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    try:
        extractor = SPPdfExtractor(dummy_path)
        from src.extractors.pdf_extractor import LAYOUT_ISBET
        assert extractor._detect_layout_page(MOCK_TEXT) == LAYOUT_ISBET
    finally:
        if _os.path.exists(dummy_path):
            _os.remove(dummy_path)


def test_instituto_recut_falha_silenciosamente_sem_pagina_real(monkeypatch):
    """`_ocr_recut_instituto_valor` precisa de uma página PDF real renderizável
    (pymupdf + Tesseract) para provar o caminho de SUCESSO - infraestrutura
    pesada demais para rodar na suíte. O que É testável sem isso é o caminho de
    FALHA: contra um PDF inválido, o método nunca lança exceção nem inventa um
    valor - devolve string vazia, e quem chama mantém 0,00 + aviso. Mesma
    limitação aceita e documentada já usada em `_ocr_recut_dacte_os_grade`
    (ver DOCUMENTACAO_CONVERSAO.md)."""
    dummy_path = "tests/dummy_instituto_recut.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"not a real pdf")

    try:
        extractor = SPPdfExtractor(dummy_path)
        resultado = extractor._ocr_recut_instituto_valor()
        assert resultado == ''
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
