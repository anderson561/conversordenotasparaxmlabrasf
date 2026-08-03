# -*- coding: utf-8 -*-
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
import os

# Texto REAL do OCR (Tesseract) da pagina 29 do PDF
# "Notas_Fiscais_emitidas_e_recebidas_05.2026_-_PH_Gestao_SEDE.pdf": NFS-e
# ESCANEADA de Camacari/BA (layout camacari_ba_scan), AVANCO GESTAO E
# ADMINISTRACAO LTDA -> PH Gestao, nota no 246, R$ 6.923,49. Regressao do bug
# real: a pagina esta LEVEMENTE TORTA (~-1 grau). A linha "Numero da Nota" e a
# mais alta da celula do canto superior direito; com a pagina inclinada ela
# sai do enquadramento dos dois recortes fixos (o largo le so "246" solto sem
# rotulo; o estreito corta o rotulo para "o da Nota") -> a ancora
# "...mero da Nota" nao casa e o numero desabava para o fallback "00000000".
# O 3o recorte ADITIVO desentorta a pagina pelo angulo estimado por pagina e
# reprocessa a celula, recuperando "Numero da Nota / 246". O texto abaixo
# contem os tres recortes do cabecalho concatenados + o corpo da nota.
MOCK_TEXT = '246\n27/05/2026 13:46\nCódigo de autenticidade\n2AI9RS657\n36628001\nNº: SN\nRODO)\n\no da Nota\n246\ne Emissão\n27/05/2026 13:46\n» de autenticidade\n2AI9RS657\nNº: SN\nUF: BA\n\nNúmero da Nota\n246\nData de Emissão\n27/05/2026 13:46\nCódigo de autenticidade\n2AI9RS657\n066628001\nNº: SN\n\nSs PREFEITURA MUNICIPAL DE CAMAÇARI 246\neba . Data de Emissão\nCR Secretaria da Fazenda .\nai] NOTA FISCAL DE SERVIÇOS ELETRÔNICA\nPRESTADOR DE SERVIÇOS\nNome/Razão Social: AVANÇO GESTÃO E ADMINISTRAÇÃO LTDA\nCPF/CNPJ: 59.132.742/0001-13 Inscrição Municipal: 0066628001\nLogradouro: RUA ALA DAS DUNAS Nº: SN\nCompl.: —:GUARAJUBA SHOPPING;LOJA:03;QUADRA:C-4 Bairro: GUARAJUBA (MONTE GORDO)\nCEP: 42840312 Município: CAMAÇARI UF: BA\nTOMADOR DE SERVIÇOS\nNome/Razão Social: PH GESTAO E CONSULTORIA S A\nCPF/CNPJ: 25.311.856/0001-09 Inscrição Municipal: 0032346001\nLogradouro: ALAMEDA HUMAITA Nº: SIN\nCompl.: COND GUARAJUBA S PREMIUS Bairro: GUARAJUBA (MONTE GORDO)\nCEP: 42840562 Município: CAMAÇARI UF: BA\nDISCRIMINAÇÃO DOS SERVIÇOS\nDESCRIÇÃO QTD VALOR UNIT (R$) VALOR TOTAL (R$)\nTAXA DE SERVIÇOS COMBINADOS DE ESCRITÓRIO E APOIO ADMINISTRATIVO 1,0000 6.923,49 6.923,49\neta ElgSsIEEl\nEE sd ta E po\nEles XML PDF [a)Eariprih\nRetenções (R$) Totais (R$)\nPIS: 0,00 | Valor dos Serviços (R$) 6.923,49\nCOFINS: 0,00 | Deduções (-) 0,00\nINSS: 0,00 |Base de Cálculo (=) 6.923,49\nIR: 0,00 |Alíquota (%) 5,00\nCSLL: 0,00 |Valor do ISS (R$) 346,17\nOutras: 0,00 | Valor Líquido da Nota (=) 6.923,49\nTotal de Retenções: 0,00\nTipo de tributação: A RECOLHER PELO PRESTADOR Data da prestação do serviço: 27/05/2026\nMunicípio da prestação do serviço: 2905701 - CAMACARI\nMunicípio da tributação: 2905701 - CAMACARI\nCNAE: 8211-3/00 - SERVIÇOS COMBINADOS DE ESCRITÓRIO E APOIO ADMINISTRATIVO\nServiço: 001703 - PLANEJAMENTO, COORDENAÇÃO, PROGRAMAÇÃO OU ORGANIZAÇÃO TÉCNICA, FINANCEIRA OU ADMINISTRATIVA.\nLO [WWW STD TS TT 2 0\nCPqD - Gestão Pública Data Impressão: 27/05/2026 13:46\n'


def test_extract_camacari2_numero_pag29_skew(monkeypatch):
    dummy_path = "tests/dummy_camacari2_pag29.pdf"
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

        # Nucleo do fix: numero NAO pode ser o fallback "00000000" -> deve ser
        # "246", recuperado do recorte deskewed onde o rotulo "Numero da Nota"
        # volta a casar com o valor.
        assert nfse.numero == "246"
        assert nfse.numero != "00000000"

        # Data de EMISSAO (27/05/2026 13:46), nao a da prestacao.
        assert nfse.data_emissao.year == 2026
        assert nfse.data_emissao.month == 5
        assert nfse.data_emissao.day == 27
        assert nfse.data_emissao.hour == 13
        assert nfse.data_emissao.minute == 46

        # Codigo de verificacao alfanumerico (letra+digito), nao a IM numerica.
        assert nfse.codigo_verificacao == "2AI9RS657"

        # Entidades/valor de apoio (travam contexto do layout).
        assert nfse.prestador.cnpj_cpf == "59132742000113"
        assert nfse.prestador.razao_social == "AVANÇO GESTÃO E ADMINISTRAÇÃO LTDA"
        assert nfse.tomador.cnpj_cpf == "25311856000109"
        assert nfse.valores.valor_servicos == pytest.approx(6923.49)
        assert nfse.servico_codigo == "1703"
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
