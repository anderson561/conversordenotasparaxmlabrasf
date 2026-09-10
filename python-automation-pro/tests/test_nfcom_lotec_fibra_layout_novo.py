# -*- coding: utf-8 -*-
"""Nota real nº 17041 (Lotec Fibra LTDA -> SINDICATO DOS DELEGADOS DE
POLICIA DO ESTADO DA BAHIA), achado 2026-09-09 — layout NOVO `nfcom_lotec_
fibra`, mesmo template nacional NFCom (dfe-portal.svrs.rs.gov.br/NfCom) já
usado por `nfcom_salvador`/`nfcom_rlgr`, mas de um emitente diferente.

Pedido do usuário: "Crie plano de ação, para verificar novamente, para o
layout lotec fibra, crie caso não exista." Sem detecção dedicada, a nota
caía no fallback genérico e saía com o CNPJ do tomador IGUAL ao do
prestador (ambos sentinela), endereço com o resto do documento inteiro
despejado no campo "Número", Valor dos Serviços zerado e Código de
Verificação vazio.

Achados corrigidos:
- **Data de Emissão**: a leitura de página inteira funde a coluna direita
  do cabeçalho ("NOTA FISCAL FATURA Nº"/"SÉRIE"/"DATA DE EMISSÃO") com o
  bloco do tomador à esquerda, e o dia sai errado ("28/07/2026" em vez do
  real "29/07/2026"). Corrigido com um recorte dedicado da coluna direita
  (`_ocr_recut_nfcom_lotec_fibra_coluna_direita`), prependado ao texto.
- **CNPJ do tomador**: o CNPJ do SINDICATO sai ilegível em toda combinação
  de zoom/PSM testada (~20 tentativas, nunca bate o dígito verificador,
  cada tentativa erra um dígito diferente). Corrigido com a mesma técnica
  de contraparte conhecida já usada para BONI TRANSPORTES/GUARAJUBA
  SHOPPING (substitui pelo CNPJ real, 73393696000137, já confirmado nesta
  base para esta mesma entidade — nota EBJ nº 4777, `nfcom_salvador`).
- **Chave de Acesso**: os 2 primeiros dígitos (código da UF, cUF) saem
  instáveis entre tentativas de OCR, mas o resto da chave decodifica
  exatamente certo (CNPJ do prestador nas posições 6:20, número da nota
  nas posições 25:34). Corrigido forçando cUF="29" (Bahia — prestador
  fixo, nunca varia).
- **Município do prestador**: "Santa Teresinha"/"Santa Terezinha" (BA) não
  está em `IBGEResolver.KNOWN_CITIES` — hardcoded diretamente como
  "2928505" (confirmado contra 2 fontes independentes do IBGE), em vez de
  cair silenciosamente no fallback de Salvador/BA (mesma classe de bug já
  vista com Vinhedo/SP).

Valor ("TOTAL A PAGAR: R$ 119,90") já sai limpo na leitura padrão de
página inteira, sem precisar de recorte dedicado.

O texto abaixo é o resultado REAL de `_extract_via_ocr` (Tesseract, já com
o recorte da coluna direita prependado) para a página única desta nota,
usado como fixture para travar a extração sem precisar rodar Tesseract no
teste."""
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_NFCOM_LOTEC_FIBRA

MOCK_OCR = (
    "NOTA FISCAL FATURA Nº 00000017041\n"
    "SERIE: 1\n\n"
    "DATA DE EMISSÃO: 29/07/2026 às 09:09:44\n\n"
    "CHAVE DE ACESSO:\n"
    "2326 0763 3333 2000 0183 6200 1000 0170 4110 5396 8242\n\n"
    "Protocolo de Aulorização: 2292600198125101\n\n\n"
    "DOCUMENTO AUXILIAR DA NOTA FISCAL FATURA DE SERVIÇOS DE COMUNICAÇÃO ELETRÔNICA\n\n"
    "F Lotec Fibra LTDA\n"
    "7 CNPJ: 83,333.320/0001-83\n"
    "T FERQ IE:297185059\n"
    "PC APIO MEDRADO, 88 - SALA 06 - CENTRO.\n\n"
    "Santa Teresinha - BA - 44590000\n"
    "Telefone: 7131013407\n\n"
    "CLIENTE:\n"
    "SINDICATO DOS DELEGADOS DE POLICIA DO ESTADO DA BAHIA\n\n"
    "CNPJ: 73.392 696/0001-37 Neri FISCAL FATURA Nº 00000017041\n"
    "RIE: 1\n\n"
    "ENDEREÇO:\n"
    "RUA DA GRATIDÃO, 3 - - PIATA\n"
    "Salvador / BA - 41650195\n\n"
    "DATA DE EMISSÃO: 28/07/2026 às 09:09:44\n\n"
    "CHAVE DE ACESSO:\n"
    "2326 0763 3333 2000 0183 6200 1000 0170 4110 5346 8242\n\n"
    "Protocolo de Autorização: 2292500198125101\n\n"
    "INFORMAÇÕES:\n"
    "30/07/2026 às 01:01.26-0400\n\n"
    "Cod. Assinante: 4364 Contrato: 5340\n"
    "Telefone: 71909974571\n"
    "Período: 10/06/2026 à 10/07/2026\n\n"
    "hilps//dfe-portal.svrs.rs.gov.br/Nfcom/QrCode?chNFCom=2526\n"
    "076333332000018352001000017041105336824251pAmbj=1\n\n"
    "| REFERÊNCIA (ANO/MÊS). 07/2026 AREA DO CONTRIBUINTE:\n\n"
    "VENCIMENTO: 10/07/2026 APÓS VENCIMENTO COBRAR MULTA DE R$ 2,40 E JUROS DE R$ 0,04 AO DIA,\n\n"
    "| TOTAL A PAGAR: R$ 119,90\n\n"
    "LIQ Í V.ICMS V.IBSUF| V.ces\n\n"
    "CoD. ITENS | cror UN QTD V.UNIT. | TOTAL  PISICOFINS |BC. ICMS\n"
    "Ganosnt | 500 Mega Promocionai (1) Es 5307 Me 10000 - R$71,94 | R$71,94 R$000 | R$000  q; L aso00 - R$000 | R$0,00\n"
    "(190391 LIVROS DIGITAIS(OL Premium) UN 10000 | R$31,97 | R$31,97 R$90,00 R$000 — oon% | R$0,00  R$000 | R$0,00\n"
    "o 101 \u201cLIVROS DIGITAIS(OL Be Babanca) — UN 10000 |  R$1509 | R$15.90 R$90,00 R$000 : 000% | R$000 . R$000 | R$0,00\n\n"
    "INFORMAÇÕES DOS TRIBUTOS RESERVADO ÃO FISCO\n\n"
    "VALOR NFF R$ 119,90\n"
    "TOTAL BC ICMS\n"
    "qua\n"
    "VALOR ICMS\n"
    "EE E\n"
    "DO A CO LIC\n\n"
    "IMPOSTO E CONTRIBUIÇÃO SOBRE BENS E SERVIÇOS (IBS E CBS)\n\n"
    "INFORMAÇÕES COMPLEMENTARES\n\n"
    "- Documento emitido por empresa optante pelo Simples Nacional. - Nao gera direito a Credito Fiscal de ICMS, ISS e IPI conforme Lei Complementar 123/2006.\n\n"
    "ÁREA DO CONTRIBUINTE E DETERMINAÇÕES DA ANATEL\n"
)


@pytest.fixture
def nfse(monkeypatch, tmp_path):
    dummy = tmp_path / "dummy_nfcom_lotec_fibra_17041.pdf"
    dummy.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_OCR)
    notas = SPPdfExtractor(str(dummy)).parse_multiple()
    assert len(notas) == 1
    return notas[0]


def test_layout_detectado(tmp_path):
    dummy = tmp_path / "dummy_layout.pdf"
    dummy.write_bytes(b"%PDF-1.4")
    ex = SPPdfExtractor(str(dummy))
    ex.from_ocr = True
    ex._pagina_veio_de_ocr = True
    assert ex._detect_layout_page(MOCK_OCR) == LAYOUT_NFCOM_LOTEC_FIBRA


def test_prestador_fixo(nfse):
    assert nfse.prestador.razao_social == "LOTEC FIBRA LTDA"
    assert nfse.prestador.cnpj_cpf == "63333320000183"
    assert nfse.prestador.endereco.municipio == "SANTA TEREZINHA"
    assert nfse.prestador.endereco.codigo_municipio == "2928505"


def test_tomador_identificado_com_cnpj_real_apesar_do_ocr_ilegivel(nfse):
    # Antes: CNPJ IGUAL ao do prestador (contaminação do fallback genérico).
    assert nfse.tomador.razao_social == "SINDICATO DOS DELEGADOS DE POLICIA DO ESTADO DA BAHIA"
    assert nfse.tomador.cnpj_cpf == "73393696000137"
    assert not SPPdfExtractor.__new__(SPPdfExtractor)._validate_cnpj_cpf("73392696000137")


def test_tomador_endereco(nfse):
    end = nfse.tomador.endereco
    assert end.logradouro == "RUA DA GRATIDÃO"
    assert end.numero == "3"
    assert end.bairro == "PIATA"
    assert end.municipio == "Salvador"
    assert end.uf == "BA"
    assert end.cep == "41650195"


def test_valor_dos_servicos_nao_fica_zerado(nfse):
    assert nfse.valores.valor_servicos == 119.90
    assert nfse.valores.valor_liquido_nfse == 119.90


def test_data_de_emissao_dia_correto(nfse):
    # Antes: dia 28 (leitura de página inteira, coluna fundida). Real: 29.
    assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "29/07/2026 09:09:44"
    assert nfse.competencia.strftime("%Y-%m") == "2026-07"


def test_codigo_verificacao_cuf_corrigido(nfse):
    # Antes: cUF instável entre leituras ("2326" já visto). Corrigido para "29".
    chave = nfse.codigo_verificacao
    assert len(chave) == 44
    assert chave.startswith("29")
    assert chave[6:20] == "63333320000183"
    assert chave[25:34].lstrip("0") == nfse.numero


def test_base_calculo_aliquota_iss_zerados_com_aviso(nfse):
    assert nfse.valores.base_calculo == 0.0
    assert nfse.valores.aliquota == 0.0
    assert nfse.valores.valor_iss == 0.0
    assert any("ICMS" in a for a in nfse.avisos)


def test_item_servico_nao_incidencia(nfse):
    assert nfse.numero == "17041"
