# -*- coding: utf-8 -*-
"""Nota real nº 18770 (SETE CONNECT TECNOLOGIA DA INFORMAÇÃO LTDA ->
NORDESTE TUBETES, R$109,99), achado 2026-09-17 - layout NOVO
`nfcom_sete_connect`, mesmo template nacional NFCom (dfe-portal.svrs.rs.
gov.br/NfCom) já usado por `nfcom_salvador`/`nfcom_rlgr`/`nfcom_lotec_
fibra`, mas de um 4º emitente diferente.

É uma NFCom (tributada por ICMS/IBS/CBS), não NFS-e ABRASF - sem detecção
dedicada, a nota caía no fallback amplo LAYOUT_NACIONAL (parser de DANFSe
ABRASF, incompatível com a estrutura de uma NFCom) e saía com Valor dos
Serviços zerado e o endereço do tomador poluído.

Detecção: CNPJ do emitente (13.060.537/0001-99) + marcador de texto "FATURA
DE SERVIÇOS DE COMUNICAÇÃO ELETRÔNICA". Prestador FIXO (mesmo emitente
sempre, endereço do letterhead hardcoded - mesmo racional dos outros 3
layouts NFCom). Tomador extraído dinamicamente do bloco "CLIENTE:"/
"CNPJ:"/"ENDEREÇO:" (mesmo formato do LOTEC_FIBRA/RLGR) - MAS nesta nota
específica o rótulo do CNPJ do tomador sai "CNP:" (o "J" foi comido pelo
OCR), tolerado via `CNPJ?` no regex. Competência via "REFERÊNCIA
(ANO/MÊS)"; Data de Emissão via "DATA DE EMISSÃO...às..."; Código de
Serviço fixo "0000" (não-incidência de ISS, tributado por ICMS); Código de
Verificação = chave de acesso de 44 dígitos, fallback 'NFCOM' quando
ilegível; Valor dos Serviços = "TOTAL A PAGAR: R$"; Base de Cálculo/
Alíquota/ISS mantidos em 0,00 propositalmente, com aviso.

O texto abaixo é um MOCK do texto digital/OCR desta nota, moldado sobre o
template real já validado em `test_nfcom_lotec_fibra_layout_novo.py`, usado
como fixture para travar a extração sem precisar do PDF de origem (não
disponível neste ambiente)."""
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_NFCOM_SETE_CONNECT

MOCK_OCR = (
    "NOTA FISCAL FATURA Nº 00000018770\n"
    "SÉRIE: 1\n\n"
    "DATA DE EMISSÃO: 20/08/2026 às 14:32:10\n\n"
    "CHAVE DE ACESSO:\n"
    "1326 0605 3700 0199 6200 1000 1877 0044 1234 5678 9012\n\n"
    "Protocolo de Autorização: 2292600198125999\n\n\n"
    "DOCUMENTO AUXILIAR DA NOTA FISCAL FATURA DE SERVIÇOS DE COMUNICAÇÃO ELETRÔNICA\n\n"
    "SETE CONNECT TECNOLOGIA DA INFORMAÇÃO LTDA\n"
    "CNPJ: 13.060.537/0001-99\n"
    "AV LUIS EDUARDO MAGALHAES, 1245 - SALA 302 - STIEP\n\n"
    "Salvador - BA - 41770235\n"
    "Telefone: 7133334444\n\n"
    "CLIENTE:\n"
    "NORDESTE TUBETES LTDA\n\n"
    "CNP: 11.222.333/0001-81\n\n"
    "ENDEREÇO:\n"
    "RUA DO COMERCIO, 120 - SALA 5 - CENTRO\n"
    "DIAS DAVILA / BA - 44580000\n\n"
    "REFERÊNCIA (ANO/MÊS): 08/2026 ÁREA DO CONTRIBUINTE:\n\n"
    "VENCIMENTO: 10/09/2026 APÓS VENCIMENTO COBRAR MULTA DE R$ 2,20 E JUROS DE R$ 0,04 AO DIA,\n\n"
    "TOTAL A PAGAR: R$ 109,99\n\n"
    "INFORMAÇÕES DOS TRIBUTOS RESERVADO AO FISCO\n\n"
    "VALOR NFF R$ 109,99\n"
    "TOTAL BC ICMS\n"
    "R$0,00\n"
    "VALOR ICMS\n"
    "R$0,00\n\n"
    "IMPOSTO E CONTRIBUIÇÃO SOBRE BENS E SERVIÇOS (IBS E CBS)\n\n"
    "INFORMAÇÕES COMPLEMENTARES\n\n"
    "- Documento emitido por empresa optante pelo Simples Nacional. - Nao gera direito a Credito Fiscal de ICMS, ISS e IPI conforme Lei Complementar 123/2006.\n\n"
)


@pytest.fixture
def nfse(monkeypatch, tmp_path):
    dummy = tmp_path / "dummy_nfcom_sete_connect_18770.pdf"
    dummy.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_OCR)
    notas = SPPdfExtractor(str(dummy)).parse_multiple()
    assert len(notas) == 1
    return notas[0]


def test_layout_detectado_pelo_cnpj_e_marcador(tmp_path):
    dummy = tmp_path / "dummy_layout.pdf"
    dummy.write_bytes(b"%PDF-1.4")
    ex = SPPdfExtractor(str(dummy))
    ex.from_ocr = True
    ex._pagina_veio_de_ocr = True
    assert ex._detect_layout_page(MOCK_OCR) == LAYOUT_NFCOM_SETE_CONNECT


def test_prestador_fixo(nfse):
    assert nfse.prestador.razao_social == "SETE CONNECT TECNOLOGIA DA INFORMACAO LTDA"
    assert nfse.prestador.cnpj_cpf == "13060537000199"
    assert nfse.prestador.endereco.municipio == "SALVADOR"
    assert nfse.prestador.endereco.uf == "BA"


def test_tomador_dinamico_com_cnp_sem_j_tolerado(nfse):
    # A nota real imprime "CNP:" (o "J" foi comido pelo OCR) em vez de "CNPJ:".
    assert "CNP:" in MOCK_OCR
    assert "CNPJ:" not in MOCK_OCR.split("CLIENTE:")[1].split("ENDEREÇO:")[0]
    assert nfse.tomador.razao_social == "NORDESTE TUBETES LTDA"
    assert nfse.tomador.cnpj_cpf == "11222333000181"

    end = nfse.tomador.endereco
    assert end.logradouro == "RUA DO COMERCIO"
    assert end.numero == "120"
    assert end.bairro == "CENTRO"
    assert end.uf == "BA"
    assert end.cep == "44580000"
    assert end.codigo_municipio == "2910057"   # Dias d'Ávila/BA


def test_competencia(nfse):
    assert nfse.competencia.strftime("%Y-%m") == "2026-08"


def test_data_de_emissao(nfse):
    assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "20/08/2026 14:32:10"


def test_codigo_servico_nao_incidencia(nfse):
    assert nfse.servico_codigo == "0000"


def test_codigo_verificacao_chave_de_44_digitos_com_fallback_nfcom(nfse, tmp_path, monkeypatch):
    chave = nfse.codigo_verificacao
    assert len(chave) == 44
    assert chave == "13260605370001996200100018770044123456789012"

    # Fallback honesto 'NFCOM' quando a chave não sobrevive ao OCR (mesmo
    # critério dos outros 3 layouts NFCom) - mesmo texto, só sem a chave.
    mock_sem_chave = MOCK_OCR.replace(
        "CHAVE DE ACESSO:\n1326 0605 3700 0199 6200 1000 1877 0044 1234 5678 9012\n\n", "")
    dummy = tmp_path / "dummy_sem_chave.pdf"
    dummy.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: mock_sem_chave)
    notas = SPPdfExtractor(str(dummy)).parse_multiple()
    assert len(notas) == 1
    assert notas[0].codigo_verificacao == "NFCOM"


def test_valor_total_a_pagar_nao_fica_zerado(nfse):
    assert nfse.valores.valor_servicos == pytest.approx(109.99)
    assert nfse.valores.valor_liquido_nfse == pytest.approx(109.99)


def test_base_calculo_aliquota_iss_zerados_com_aviso(nfse):
    assert nfse.valores.base_calculo == 0.0
    assert nfse.valores.aliquota == 0.0
    assert nfse.valores.valor_iss == 0.0
    assert any("ICMS" in a for a in nfse.avisos)
