# -*- coding: utf-8 -*-
import os

from src.extractors.pdf_extractor import SPPdfExtractor

# Texto REAL do OCR (Tesseract) da pagina 1 do PDF "NF 6013.pdf" (3 paginas;
# so a 1a e a NFS-e, as outras duas sao a fatura anexa do prestador): NFS-e
# ESCANEADA de Camacari/BA (layout camacari_cpqd), CLINICA MEDICINA HUMANA
# LTDA -> MASSA ALIMENTACAO E SERVICOS S/A, nota no 6013, R$ 477,45.
#
# Regressao do bug real: o XML saia com <Numero>3</Numero> / Id="NFSe3". Das
# varias tentativas de leitura da caixa "Numero da Nota / Data de Emissao /
# Codigo de autenticidade", so UMA tem o rotulo limpo ("e Numero da Nota",
# colado ao icone "e" do OCR), e logo depois dele o texto traz a faixa
# "PREFEITURA MUNICIPAL DE CAMACARI" e o rotulo vizinho "3 Data de Emissao" -
# o "3" e o fragmento do icone colado ao rotulo da PROXIMA celula, nao o valor
# deste rotulo. O valor real "6013" sobrevive em outras duas leituras: a linha
# sintetica de abertura (antes de qualquer rotulo) e "mero da Nota" seguido de "6013" na linha
# de baixo (rotulo degradado - perdeu o "Nu", por isso o regex de rotulo limpo nao casa).
MOCK_TEXT = '6013\nData de Emissão\nCódigo de autenticidade\n058126001\nNº 76\n\nmero da Nota\n6013\na de Emissão\n13/01/2026 09:19\nligo de autenticidade\nY665T5W64\n1\nNº: 76\n\né Número da Nota\nPREFEITURA MUNICIPAL DE CAMAÇARI\n3 Data de Emissão\n|\nNOTA FISCAL DE SERVIÇOS ELETRÔNICA\nY665T5W64\nPRESTADOR DE SERVIÇOS\nNome/Razão Social: CLINICA MEDICINA HUMANA LTDA\nCPF/CNPJ: 50.091.585/0001-70 Inscrição Municipal: 0058126001\nLogradouro: | RUA DO ALECRIM Nº: 76\nCompl.: Bairro: CENTRO\nCEP: 42800025 Município: CAMAÇARI UF: BA\nTOMADOR DE SERVIÇOS\nNome/Razão Social: MASSA ALIMENTAÇÃO E SERVIÇOS S/A\nCPF/CNPJ: 09.033.381/0005-03 Inscrição Municipal:\nLogradouro: | VIA MANTOIM Nº S/N\nCompl.: Bairro: DISTRITO INDUSTRIAL\nCEP! 43813000 Município: CANDEIAS UF: BA\nDISCRIMINAÇÃO DOS SERVIÇOS\nDESCRIÇÃO QTD VALOR UNIT (R$) VALOR TOTAL (R$)\nREF. Á SERVIÇOS MÉDICOS PRESTADOS NO MÊS DE DEZEMBRO/2025 1,0000 477,45 477,45\nVENCIMENTO: 13/02/2026\nAp ES E frete o\na Eae\n[does XML PDF [of\nRetenções (R$) Totais (R$)\nPIS: 3,10 | Valor dos Serviços (R$) 477,45\nCOFINS: 14,32 |Deduções (-) 0,00\nINSS: 0,00 | Base de Cálculo (=) 477,45\nIR: 0,00 |Alíquota (%) 3,00\nCSLL: 4,77 | Valor do ISS (R$) 14,32\nOutras: 0,00 | Valor Líquido da Nota (=) 455,26\nTotal de Retenções: 22,19\nTipo de tributação: A RECOLHER PELO PRESTADOR Data da prestação do serviço: 13/01/2026\nMunicípio da prestação do serviço: 2905701 - CAMACARI\nMunicípio da tributação: 2905701 - CAMACARI\nCNAE:\nServiço: 000403 - HOSPITAIS, CLÍNICAS, LABORATÓRIOS, SANATÓRIOS, MANICÔMIOS, CASAS DE SAÚDE, PRONTOS-SOCORROS,\nAMBULATÓRIOS E CONGÊNERES.\nCPqD - Gestão Pública Data Impressão: 13/01/2026 09:19\n\n'


def _converter(monkeypatch, nome_arquivo):
    caminho = os.path.join("tests", nome_arquivo)
    os.makedirs("tests", exist_ok=True)
    with open(caminho, "wb") as f:
        f.write(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_TEXT)
    try:
        lista = SPPdfExtractor(caminho).parse_multiple()
    finally:
        if os.path.exists(caminho):
            os.remove(caminho)
    return lista


def test_camacari_numero_nao_vira_fragmento_colado_ao_rotulo_vizinho(monkeypatch):
    lista = _converter(monkeypatch, "dummy_camacari_6013.pdf")
    assert len(lista) == 1
    nfse = lista[0]
    assert nfse.numero == "6013"
    assert nfse.data_emissao.day == 13
    assert nfse.data_emissao.month == 1
    assert nfse.data_emissao.year == 2026
    assert nfse.codigo_verificacao == "Y665T5W64"
    assert nfse.prestador.cnpj_cpf == "50091585000170"


def test_camacari_numero_nao_depende_do_nome_do_arquivo(monkeypatch):
    # Nome com outro numero que NAO pode ser usado como fallback do numero.
    lista = _converter(monkeypatch, "copia_qualquer_777.pdf")
    assert lista[0].numero == "6013"
