# -*- coding: utf-8 -*-
r"""Camaçari/BA escaneado - a MESMA nota impressa duas vezes no lote não pode
virar dois XMLs.

Achado real: págs. 13 e 17 do lote `Notas_Fiscais_emitidas_e_recebidas_
08.2026_-_PH_Gestao_SEDE.pdf` são o MESMO documento fiscal - nota nº 268,
JAILSON ARGOLO SANTOS ME (23.807.349/0001-35) -> PH GESTAO E CONSULTORIA
S A, R$1.000,00, emitida em 05/08/2026 14:16 - digitalizado duas vezes (as
imagens diferem byte a byte, o conteúdo é idêntico).

Reportado como "a página 17 não gerou XML". Não é defeito: a nota É
extraída, a partir da pág. 13, e a segunda ocorrência é descartada pela
deduplicação de `parse_multiple()` (chave `numero_cnpjPrestador`). Emitir
os dois geraria nota em duplicidade na escrituração. Este teste fixa esse
comportamento com os dois textos OCR REAIS das duas páginas.
"""
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_OCR_PAG13 = 'Número da Nota\n268\nData de Emissão\n05/08/2026 14:16\nCódigo de autenticidade\n62X8L9R5R\n0032066001\nNº: SN\n\nNúmero da Nota\n268\nData de Emissão\n05/08/2026 14:16\nCódigo de autenticidade\n62X8L9R5R\n\n001\n\nNº: SN\n\nUF: BA\n\nNúmero da Nota\n268\nData de Emissão\n05/08/2026 14:16\nCódigo de autenticidade\n6Z2X8L9R5R\n0032066001\nNº: SN\n\nE Número da Nota\ne z Data de Emissão\nMa Secretaria da Fazenda\nea NOTA FISCAL DE SERVIÇOS ELETRÔNICA\no 6ZX8L9R5R\nPRESTADOR DE SERVIÇOS\nNome/Razão Social: JAILSON ARGOLO SANTOS ME\nCPF/CNPJ: 23.807.349/0001-35 Inscrição Municipal: 0032066001\nLogradouro: RUA OVIDIO ARANHA Nº: SN\nCompl.: Bairro: BARRA DO POJUCA\nCEP: 42841504 Município: CAMAÇARI UF: BA\nTOMADOR DE SERVIÇOS\nNome/Razão Social: PH GESTAO E CONSULTORIA S A\nCPF/CNPJ: 25.311.856/0001-09 Inscrição Municipal: 0032346001\nLogradouro: ALAMEDA HUMAITA Nº: SIN\nCompl.: COND GUARAJUBA S PREMIUS Bairro: GUARAJUBA (MONTE GORDO)\nCEP: 42840562 Município: CAMAÇARI UF: BA\nDISCRIMINAÇÃO DOS SERVIÇOS\nDESCRIÇÃO QTD VALOR UNIT (R$) VALOR TOTAL (R$)\nMANUTENÇÃO DE COMANDO PARA ATIVAÇÃO DAS ELEVATORIAS. PIX PARA 1,0000 1.000,00 1.000,00\nPAGAMENTO: 71997046832, FAVORECIDO ARGOLO INSTALAÇÕES BANCO NU\nPAGAMENTOS S.A\nERR fed\nBIRSRSES XML PDF [a Estas\nRetenções (R$) Totais (R$)\nPIS: 0,00 |Valor dos Serviços (R$) 1.000,00\nCOFINS: 0,00 | Deduções (-) 0,00\nINSS: 0,00 | Base de Cálculo (=) 1.000,00\nIR: 0,00 |Alíquota (%) 2,00\nCSLL: 0,00 | Valor do ISS (R$) 20,00\nOutras: 0,00 | Valor Líquido da Nota (=) 1.000,00\nTotal de Retenções: 0,00\nTipo de tributação: A RECOLHER PELO PRESTADOR Data da prestação do serviço: 05/08/2026\nMunicípio da prestação do serviço: 2905701 - CAMACARI\nMunicípio da tributação: 2905701 - CAMACARI\nCNAE:\nServiço: 001401 - LUBRIFICAÇÃO, LIMPEZA, LUSTRAÇÃO, REVISÃO, CARGA E RECARGA, CONSERTO, RESTAURAÇÃO, BLINDAGEM,\nMANUTENÇÃO E CONSERVAÇÃO DE MÁQUINAS, VEÍCULOS, APARELHOS, EQUIPAMENTOS, MOTORES, ELEVADORES OU DE\nQUALQUER OBJETO (EXCETO PEÇAS E PARTES EMPREGADAS, QUE FICAM SUJEITAS AO ICMS). sÁ\nCPqD - Gestão Pública Data Impressão: 05/08/2026 14:16\n'

MOCK_OCR_PAG17 = 'Número da Nota\n268\nData de Emissão\n05/08/2026 14:16\nCódigo de autenticidade\n62X8L9R5R\n0032066001\nNº: SN\nIP. BA\n\nNúmero da Nota\n268\nData de Emissão\n05/08/2026 14:16\nCódigo de autenticidade\n62X8L9R5R\n001\nNº: SN\nUF: BA\n\nEe] Número da Nota\nad PREFEITURA MUNICIPAL DE CAMAÇARI\nPastas a Data de Emissão\npe NOTA FISCAL DE SERVIÇOS ELETRÔNICA\nE 67X8LOR5R\nPRESTADOR DE SERVIÇOS\nNome/Razão Social: JAILSON ARGOLO SANTOS ME\nCPF/CNPJ: 23.807.349/0001-35 Inscrição Municipal: 0032066001\nLogradouro: RUA OVIDIO ARANHA Nº: SN\nCompl.: Bairro: BARRA DO POJUCA\nCEP: 42841504 Município: CAMAÇARI UF: BA\nTOMADOR DE SERVIÇOS\nNome/Razão Social: PH GESTAO E CONSULTORIA S A\nCPF/CNPJ: 25.311.856/0001-09 Inscrição Municipal: 0032346001\nLogradouro: ALAMEDA HUMAITA Nº: SIN\nCompl.: COND GUARAJUBA S PREMIUS Bairro: GUARAJUBA (MONTE GORDO)\nCEP: 42840562 Município: CAMAÇARI UF: BA\nDISCRIMINAÇÃO DOS SERVIÇOS\nDESCRIÇÃO QTD VALOR UNIT (R$) VALOR TOTAL (R$)\nMANUTENÇÃO DE COMANDO PARA ATIVAÇÃO DAS ELEVATORIAS. PIX PARA 1,0000 1.000,00 1.000,00\nPAGAMENTO: 71997046832, FAVORECIDO ARGOLO INSTALAÇÕES BANCO NU\nPAGAMENTOS S.A\nao Es a\nEn) 2 cão\nDESSES XML PDF [nEtBhs\nRetenções (R$) Totais (R$)\nPIS: 0,00 | Valor dos Serviços (R$) 1.000,00\nCOFINS: 0,00 | Deduções (-) 0,00\nINSS: 0,00 | Base de Cálculo (=) 1.000,00\nIR: 0,00 |Alíquota (%) 2,00\nCSLL: 0,00 | Valor do ISS (R$) 20,00\nOutras: 0,00 | Valor Líquido da Nota (=) 1.000,00\nTotal de Retenções: 0,00\nTipo de tributação: A RECOLHER PELO PRESTADOR Data da prestação do serviço: 05/08/2026\nMunicípio da prestação do serviço: 2905701 - CAMACARI\nMunicípio da tributação: 2905701 - CAMACARI\nCNAE:\nServiço: 001401 - LUBRIFICAÇÃO, LIMPEZA, LUSTRAÇÃO, REVISÃO, CARGA E RECARGA, CONSERTO, RESTAURAÇÃO, BLINDAGEM,\nMANUTENÇÃO E CONSERVAÇÃO DE MÁQUINAS, VEÍCULOS, APARELHOS, EQUIPAMENTOS, MOTORES, ELEVADORES OU DE\nQUALQUER OBJETO (EXCETO PEÇAS E PARTES EMPREGADAS, QUE FICAM SUJEITAS AO ICMS). DP aa\nCPqD - Gestão Pública Data Impressão: 05/08/2026 14:16\n'


@pytest.fixture
def notas(monkeypatch, tmp_path):
    dummy = tmp_path / "dummy_camacari_268_duplicada.pdf"
    dummy.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(
        SPPdfExtractor, "_extract_via_ocr",
        lambda self: MOCK_OCR_PAG13 + "\x0c" + MOCK_OCR_PAG17,
    )
    return SPPdfExtractor(str(dummy)).parse_multiple()


def test_as_duas_paginas_sao_a_mesma_nota():
    for texto in (MOCK_OCR_PAG13, MOCK_OCR_PAG17):
        assert "268" in texto
        assert "05/08/2026 14:16" in texto
        assert "23.807.349/0001-35" in texto


def test_gera_um_unico_xml_para_a_nota_268(notas):
    assert len(notas) == 1
    n = notas[0]
    assert n.numero == "268"
    assert n.prestador.cnpj_cpf == "23807349000135"
    assert n.data_emissao.strftime("%d/%m/%Y %H:%M") == "05/08/2026 14:16"
    assert n.valores.valor_servicos == 1000.00
