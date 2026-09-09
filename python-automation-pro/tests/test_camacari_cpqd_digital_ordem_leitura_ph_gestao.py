# -*- coding: utf-8 -*-
r"""Camaçari/BA via CPqD, PDF **DIGITAL** (`camacari_cpqd`) - ordem de leitura
quebrada e página digital classificada como escaneada num lote misto.

Achado real: pág. 8 do lote `Notas_Fiscais_emitidas_e_recebidas_08.2026_-
_PH_Gestao_SEDE.pdf`, nota nº 52 - RAFFA GLASS VIDRACARIA LTDA
(29.997.663/0001-04) -> PH GESTAO E CONSULTORIA S A (25.311.856/0001-09),
serviços R$288,00, base R$288,00, alíquota 3,00%, ISS R$8,64, emitida em
03/08/2026 17:21, código de autenticidade 6UTVQW43O.

O XML gerado saía inteiro errado - `Numero 00000000`, `CodigoVerificacao
DATADEEMISS`, `ValorServicos 0.00`, `ValorCofins 288.00` (o valor dos
SERVIÇOS caindo na retenção de COFINS), `ValorCsll 3.00` (a alíquota),
`BaseCalculo 8.64` (o ISS) e as duas razões sociais como colagens de
rótulos - por DOIS defeitos encadeados:

1. **Ordem de leitura quebrada** (a mesma classe de bug do
   `camacari_sisloc`/`goiania_go`): o gerador do PDF desenha rótulos e
   valores como blocos de texto separados, e o `pdfminer.high_level.
   extract_text()` devolve TODOS os rótulos antes de TODOS os valores
   ("...Código de autenticidadeData de EmissãoNúmero da Nota6UTVQW43O
   Secretaria da FazendaPREFEITURA MUNICIPAL DE CAMAÇARINOTA FISCAL DE
   SERVIÇOS ELETRÔNICA5203/08/2026 17:21..."). Qualquer leitura por
   proximidade pega o rótulo vizinho em vez do valor. Corrigido
   reconstruindo o texto por COORDENADA de caractere
   (`_reconstruir_texto_por_coordenadas`), técnica que já existia no
   projeto para os outros dois layouts.

2. **Página digital tratada como escaneada**: `from_ocr` é uma flag do
   DOCUMENTO inteiro; como 30 das 41 páginas deste lote exigiram OCR, a
   pág. 8 (100% digital, 1493 caracteres embutidos) era roteada para o
   `LAYOUT_CAMACARI_3` (variante de foto/scan). Corrigido com a origem por
   PÁGINA (`_pagina_e_escaneada`), propagada por `parse_multiple()`.

Textos REAIS capturados do PDF: `MOCK_PDFMINER_CRU` é o que o
`extract_text()` devolve para esta página; `MOCK_RECONSTRUIDO` é o que
`_reconstruir_texto_por_coordenadas()` devolve para a mesma página.
"""
import pytest
from src.extractors.pdf_extractor import (
    SPPdfExtractor, LAYOUT_CAMACARI, LAYOUT_CAMACARI_3,
)

MOCK_PDFMINER_CRU = 'Código de autenticidadeData de EmissãoNúmero da Nota6UTVQW43OSecretaria da FazendaPREFEITURA MUNICIPAL DE CAMAÇARINOTA FISCAL DE SERVIÇOS ELETRÔNICA5203/08/2026 17:21DESCRIÇÃOQTDVALOR UNIT (R$)VALORTOTAL(R$)MANUTENÇÃO1,0000288,00288,00PRESTADOR DE SERVIÇOSRAFFA GLASS VIDRACARIA LTDALogradouro:Bairro:Compl.:Município:Nº:CEP:UF:RUAAGATAAREMBEPE (ABRANTES)COND LOT.FONTE DAS PEDRASQUADRA03CAMAÇARI42830562BAS/NNome/Razão Social:CPF/CNPJ:004731300129.997.663/0001-04TOMADOR DE SERVIÇOSPH GESTAO E CONSULTORIA S ABairro:Município:Nº:UF:ALAMEDA HUMAITAGUARAJUBA (MONTE GORDO)COND GUARAJUBA S PREMIUSCAMAÇARIBAS/N003234600125.311.856/0001-09Logradouro:Compl.:CEP:42840562Nome/Razão Social:CPF/CNPJ:DISCRIMINAÇÃO DOS SERVIÇOSRetenções (R$)Totais (R$)PIS:INSS:COFINS:CSLL:Outras:TotaldeRetenções:Valor dos Serviços (R$)Deduções (-)Base de Cálculo (=)Alíquota (%)Valor do ISS (R$)Valor Líquido da Nota (=)0,000,00288,003,000,000,000,008,640,000,00288,00288,00Tipo de tributação: A RECOLHER PELO PRESTADORMunicípiodaprestaçãodoserviço:2905701-CAMACARICNAE: 4330-4/99 - OUTRAS OBRAS DE ACABAMENTO DA CONSTRUÇÃOServiço: 000706 - COLOCAÇÃO E INSTALAÇÃO DE TAPETES, CARPETES, ASSOALHOS, CORTINAS, REVESTIMENTOS DE PAREDE,VIDROS, DIVISÓRIAS, PLACAS DE GESSO E CONGÊNERES, COM MATERIAL FORNECIDO PELO TOMADOR DO SERVIÇO.Inscrição Municipal:Inscrição Municipal:Data da prestação do serviço: 03/08/2026IR:0,00XMLPDFMunicípio da tributação: 2905701 - CAMACARIData Impressão:03/08/2026 17:21CPqD - Gestão Pública'

MOCK_RECONSTRUIDO = 'Número da Nota\nPREFEITURA MUNICIPAL DE CAMAÇARI 52\nData de Emissão\nSecretaria da Fazenda\n03/08/2026 17:21\nCódigo de autenticidade\nNOTA FISCAL DE SERVIÇOS ELETRÔNICA\n6UTVQW43O\nPRESTADOR DE SERVIÇOS\nNome/Razão Social: RAFFA GLASS VIDRACARIA LTDA\nCPF/CNPJ: 29.997.663/0001-04 Inscrição Municipal: 0047313001\nLogradouro: RUA AGATA Nº: S/N\nCompl.: COND LOT.FONTE DAS PEDRASQUADRA03 Bairro: AREMBEPE (ABRANTES)\nCEP: 42830562 Município: CAMAÇARI UF: BA\nTOMADOR DE SERVIÇOS\nNome/Razão Social: PH GESTAO E CONSULTORIA S A\nCPF/CNPJ: 25.311.856/0001-09 Inscrição Municipal: 0032346001\nLogradouro: ALAMEDA HUMAITA Nº: S/N\nCompl.: COND GUARAJUBA S PREMIUS Bairro: GUARAJUBA (MONTE GORDO)\nCEP: 42840562 Município: CAMAÇARI UF: BA\nDISCRIMINAÇÃO DOS SERVIÇOS\nDESCRIÇÃO QTD VALOR UNIT (R$) VALOR TOTAL (R$)\nMANUTENÇÃO 1,0000 288,00 288,00\nXML PDF\nRetenções (R$) Totais (R$)\nPIS: 0,00 Valor dos Serviços (R$) 288,00\nCOFINS: 0,00 Deduções (-) 0,00\nINSS: 0,00 Base de Cálculo (=) 288,00\nIR: 0,00 Alíquota (%) 3,00\nCSLL: 0,00 Valor do ISS (R$) 8,64\nOutras: 0,00 Valor Líquido da Nota (=) 288,00\nTotal de Retenções: 0,00\nTipo de tributação: A RECOLHER PELO PRESTADOR Data da prestação do serviço: 03/08/2026\nMunicípio da prestação do serviço: 2905701 - CAMACARI\nMunicípio da tributação: 2905701 - CAMACARI\nCNAE: 4330-4/99 - OUTRAS OBRAS DE ACABAMENTO DA CONSTRUÇÃO\nServiço: 000706 - COLOCAÇÃO E INSTALAÇÃO DE TAPETES, CARPETES, ASSOALHOS, CORTINAS, REVESTIMENTOS DE PAREDE,\nVIDROS, DIVISÓRIAS, PLACAS DE GESSO E CONGÊNERES, COM MATERIAL FORNECIDO PELO TOMADOR DO SERVIÇO.\nCPqD - Gestão Pública Data Impressão: 03/08/2026 17:21'


@pytest.fixture
def dummy_path(tmp_path):
    p = tmp_path / "dummy_camacari_cpqd_pag8.pdf"
    p.write_bytes(b"%PDF-1.4")
    return str(p)


@pytest.fixture
def nfse(monkeypatch, dummy_path):
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_PDFMINER_CRU)
    monkeypatch.setattr(SPPdfExtractor, "_reconstruir_texto_por_coordenadas", lambda self: MOCK_RECONSTRUIDO)
    notas = SPPdfExtractor(dummy_path).parse_multiple()
    assert len(notas) == 1
    return notas[0]


def test_pagina_digital_em_lote_misto_nao_e_classificada_como_escaneada(dummy_path):
    """`from_ocr` do documento não pode arrastar uma página digital para a
    variante de scan - quem decide é a origem DESTA página."""
    ex = SPPdfExtractor(dummy_path)
    ex.from_ocr = True  # outras páginas do lote precisaram de OCR

    ex._pagina_veio_de_ocr = False
    assert ex._detect_layout_page(MOCK_RECONSTRUIDO) == LAYOUT_CAMACARI

    ex._pagina_veio_de_ocr = True
    assert ex._detect_layout_page(MOCK_RECONSTRUIDO) == LAYOUT_CAMACARI_3

    # Sem informação por página, mantém o comportamento histórico (documento).
    ex._pagina_veio_de_ocr = None
    assert ex._detect_layout_page(MOCK_RECONSTRUIDO) == LAYOUT_CAMACARI_3


def test_numero_da_nota(nfse):
    # Antes: "00000000" (ou "6", o 1º dígito de "6UTVQW43O" colado no rótulo).
    assert nfse.numero == "52"


def test_codigo_de_autenticidade(nfse):
    # Antes: "DATADEEMISS" (o rótulo seguinte, capturado pelo padrão genérico).
    assert nfse.codigo_verificacao == "6UTVQW43O"


def test_data_de_emissao_com_hora(nfse):
    # Antes: 03/08/2026 00:00 (vinha de "Data da prestação do serviço", sem hora).
    assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M") == "03/08/2026 17:21"
    assert nfse.competencia.strftime("%Y-%m") == "2026-08"


def test_prestador(nfse):
    p = nfse.prestador
    # Antes: "Bairro:Compl.:Município:Nº:CEP:UF:RUAAGATAAREMBEPE (ABRANTES)..."
    assert p.razao_social == "RAFFA GLASS VIDRACARIA LTDA"
    assert p.cnpj_cpf == "29997663000104"


def test_tomador(nfse):
    t = nfse.tomador
    # Antes: "Município:Nº:UF:ALAMEDA HUMAITAGUARAJUBA (MONTE GORDO)..."
    assert t.razao_social == "PH GESTAO E CONSULTORIA S A"
    assert t.cnpj_cpf == "25311856000109"
    assert t.cnpj_cpf != nfse.prestador.cnpj_cpf


def test_valores_da_grade(nfse):
    v = nfse.valores
    # Antes: serviços 0,00; COFINS 288,00; CSLL 3,00; base 8,64; ISS 0,00 -
    # a grade inteira deslocada de uma célula.
    assert v.valor_servicos == 288.00
    assert v.base_calculo == 288.00
    assert v.aliquota == 0.03
    assert v.valor_iss == 8.64
    assert v.valor_cofins == 0.00
    assert v.valor_csll == 0.00


def test_texto_cru_do_pdfminer_sozinho_nao_resolve(monkeypatch, dummy_path):
    """Fixa a causa-raiz: sem a reconstrução por coordenadas, o MESMO PDF
    volta a produzir os campos errados que motivaram este teste."""
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_PDFMINER_CRU)
    monkeypatch.setattr(SPPdfExtractor, "_reconstruir_texto_por_coordenadas", lambda self: "")
    notas = SPPdfExtractor(dummy_path).parse_multiple()
    assert len(notas) == 1
    ruim = notas[0]
    assert ruim.numero != "52"
    assert ruim.codigo_verificacao != "6UTVQW43O"
    assert ruim.valores.valor_servicos != 288.00
