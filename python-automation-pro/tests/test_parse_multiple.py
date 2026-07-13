import pytest
from unittest.mock import patch, MagicMock
from src.extractors.pdf_extractor import SPPdfExtractor


def _cuiaba_note(numero: str, cnpj_prestador: str, cnpj_tomador: str, valor: str) -> str:
    """Monta o texto completo de uma nota Cuiabá/MT válida (cabeçalho + valores)."""
    return f"""
    Prefeitura Municipal de Cuiabá
    Secretaria Municipal de Economia
    Nota Fiscal de Serviço Eletrônica - NFS-e
    Número da Nota Fiscal: {numero}
    Data de Geração da NFS-e: 01/04/2026 17:20:05
    Data de Competência: 01/04/2026
    Cód. de Autenticidade: COD{numero}

    Dados do Prestador de Serviço
    EMPRESA {numero} LTDA
    CPF/CNPJ: {cnpj_prestador}

    Dados do Tomador de Serviços
    CNPJ/CPF : {cnpj_tomador}
    Razão Social : CLIENTE {numero} LTDA

    Detalhamento dos Tributos
    Vl. Total dos Serviços: R$ {valor}
    Base de Cálculo: R$ {valor}
    Alíquota: 5,00
    Total do ISSQN: R$ 50,00
    Vl. Líquido da Nota Fiscal: R$ {valor}
    """


@patch('src.extractors.pdf_extractor.extract_text')
def test_parse_multiple_notas_distintas(mock_extract_text):
    """Um PDF com 2 páginas, cada uma contendo uma nota Cuiabá independente,
    deve resultar em 2 objetos Nfse, cada um com o pagina_origem correto."""
    page1 = _cuiaba_note("100", "12.345.678/0001-95", "98.765.432/0001-98", "1.000,00")
    page2 = _cuiaba_note("200", "11.222.333/0001-81", "55.666.777/0001-81", "2.000,00")

    mock_extract_text.return_value = f"{page1}\x0c{page2}"

    ext = SPPdfExtractor('dummy.pdf')
    results = ext.parse_multiple()

    assert len(results) == 2

    by_numero = {r.numero: r for r in results}
    assert set(by_numero.keys()) == {"100", "200"}
    assert by_numero["100"].pagina_origem == 1
    assert by_numero["200"].pagina_origem == 2
    assert by_numero["100"].valores.valor_servicos == pytest.approx(1000.00)
    assert by_numero["200"].valores.valor_servicos == pytest.approx(2000.00)


@patch('src.extractors.pdf_extractor.extract_text')
def test_parse_multiple_nota_dividida_em_duas_paginas(mock_extract_text):
    """Uma única nota cujo cabeçalho está na página 1 e os valores continuam
    na página 2 (sem novo cabeçalho de prefeitura/número) deve ser unida
    em um único Nfse, e não tratada como duas notas separadas."""
    page1 = """
    Prefeitura Municipal de Cuiabá
    Secretaria Municipal de Economia
    Nota Fiscal de Serviço Eletrônica - NFS-e
    Número da Nota Fiscal: 555
    Data de Geração da NFS-e: 01/04/2026 17:20:05
    Data de Competência: 01/04/2026
    Cód. de Autenticidade: COD555

    Dados do Prestador de Serviço
    RC CONSTRUCOES ELETRICAS LTDA
    CPF/CNPJ: 17.196.107/0001-50

    Dados do Tomador de Serviços
    CNPJ/CPF : 03.051.741/0001-90
    Razão Social : Sao Pedro Construtora Ltda
    """

    # Página de continuação: só tem "ISSNet" (suficiente para o layout ser
    # reconhecido e não descartado como página genérica), sem nenhum
    # marcador de início de nova nota (PREFEITURA/Número/CNPJ/Prestador).
    page2 = """
    ISSNet
    Detalhamento dos Tributos
    Vl. Total dos Serviços: R$ 17.955,00
    Deduções Base Cálculo: R$ 10.773,00
    Base de Cálculo: R$ 7.182,00
    Alíquota: 4,60
    Total do ISSQN: R$ 330,37
    ISSQN Retido: Não
    Vl. Líquido da Nota Fiscal: R$ 17.955,00
    """

    mock_extract_text.return_value = f"{page1}\x0c{page2}"

    ext = SPPdfExtractor('dummy.pdf')
    results = ext.parse_multiple()

    assert len(results) == 1
    assert results[0].numero == "555"
    assert results[0].pagina_origem == 1
    assert results[0].valores.valor_servicos == pytest.approx(17955.00)


@patch('src.extractors.pdf_extractor.extract_text')
def test_parse_multiple_filtra_lixo_e_pagina_generica(mock_extract_text):
    """Páginas de recibo bancário (TRASH_PATTERN) e páginas de layout não
    reconhecido, misturadas com uma nota válida, devem ser descartadas
    e registradas em self.invalid_pages, sem afetar o resultado final."""
    page1 = _cuiaba_note("700", "12.345.678/0001-95", "98.765.432/0001-98", "3.000,00")
    page2 = "Banco XYZ\nRecibo de Transferência Bancária\nValor: 50,00"
    page3 = ("Apenas um texto qualquer sem layout conhecido, sem relação "
             "com nota fiscal, apenas ruído de página solta sem cabeçalho.")

    mock_extract_text.return_value = f"{page1}\x0c{page2}\x0c{page3}"

    ext = SPPdfExtractor('dummy.pdf')
    results = ext.parse_multiple()

    assert len(results) == 1
    assert results[0].numero == "700"

    assert len(ext.invalid_pages) == 2
    reasons = {p["reason"] for p in ext.invalid_pages}
    assert "Lixo/Recibo detectado" in reasons
    assert "Layout não reconhecido" in reasons


@patch('src.extractors.pdf_extractor.SPPdfExtractor._ocr_page')
@patch('src.extractors.pdf_extractor.extract_text')
def test_parse_multiple_ocr_por_pagina_em_pdf_misto(mock_extract_text, mock_ocr_page):
    """PDFs mistos (uma página com texto normal mas irrelevante + uma página
    escaneada sem texto extraível) devem acionar OCR pontual apenas na página
    sem texto, sem depender de o documento inteiro "parecer" vazio."""
    # Página 1: texto extenso e com palavras-chave (CNPJ, NOTA, PRESTADOR) que
    # bastam para o documento inteiro passar no gate global de OCR — como uma
    # planilha de controle que apenas *lista* notas fiscais, sem ser uma.
    page1 = (
        "PLANILHA DE CONTROLE DE NOTAS FISCAIS EMITIDAS\n"
        "PRESTADOR / CNPJ\n" + ("Coluna de dados irrelevantes. " * 20)
    )
    # Página 2: PDF de imagem/scan, pdfminer não extrai nada.
    page2 = ""

    mock_extract_text.return_value = f"{page1}\x0c{page2}"
    mock_ocr_page.return_value = _cuiaba_note(
        "999", "12.345.678/0001-95", "98.765.432/0001-98", "4.000,00"
    )

    with patch('pymupdf.open') as mock_pymupdf_open:
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 2
        mock_pymupdf_open.return_value = mock_doc

        ext = SPPdfExtractor('dummy.pdf')
        results = ext.parse_multiple()

    mock_ocr_page.assert_called_once_with(1)
    assert len(results) == 1
    assert results[0].numero == "999"
    assert results[0].pagina_origem == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
