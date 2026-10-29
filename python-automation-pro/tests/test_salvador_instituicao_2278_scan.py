# -*- coding: utf-8 -*-
"""Salvador/BA ESCANEADA — nota real nº 00002278, INSTITUIÇÃO ASSISTENCIAL
BENEFICENTE CONCEIÇÃO MACEDO -> BONI TRANSPORTES, LOGISTICA E COMERCIO LTDA.
(R$170,00, arquivo "INSTITUTO ASSISTENCIAL B. CONCEIÇÃO MACEDO -2278.pdf").

Antes do fix: prestador "Prestador Não Identificado"/CNPJ sentinela (a linha
da razão social saía com a borda da caixa colada, "“| INSTITUICÃO ..."),
endereço do prestador com o logotipo vazado ("eição Macio º o . Rua Santa
Clara85"), Alíquota 0.06/ISS 8.60 (impresso 5,00%/8,50 — o scan fecha a
barriga do "5" e o OCR lê "6"), discriminação genérica (texto do serviço
impresso POR CIMA do rótulo "DISCRIMINAÇÃO DOS SERVIÇOS"), Código de
Verificação "XTDBDGDS" (impresso "XTDP-DGD5") e tomador com ruído
("BONI. ... LTDA. o", logradouro "NR = o a gua MARIA QUITERIA").

MOCK_OCR é cópia literal de `_extract_via_ocr` da nota real, já com os
recortes Salvador (inclusive os marcadores `SSA_ALIQ_ISS_LEITURAS` e
`SSA_DISCRIMINACAO_RECORTE` desta correção)."""
import os

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_SALVADOR

MOCK_OCR = 'Código de Verificação:\nXTDP-DGDS\n\nBASE_CALCULO_RECUPERADA: 170,00\nTOMADOR DE SERVIÇOS | BOQUIRENTE\n\n Nome/Razão Social:\n\nBONI. TRANSPORTES, LOGISTICA E COMERCIO LTDA. o\n\nCPF/CNPJ: inscrição Municipal:\n\n04.555.283/0003-50 -——\n\nEndereço: NR = o a\n\ngua MARIA QUITERIA 263, GALPÃO ITINGA - Lauro de Freitas - CEP: 42738-205/BA\n-mail:\n\nET ÃO DOS SERVICO a BR\n\nDDAGOCICA DI ADOLESCENTE: THAMIRES DO NASCIMENTO LOPES DA SILVA, REFERENTE AO MÊS DE\n\nq\n\nSETEMBRO/2 52 Õ.\n\nDADOS BANCÁRIOS:\n\nAGÊNCIA :3072\n\nCONTA CORRENTE: 69.077-5\n\nCHAVE PIX (E-MAIL) :aprendiz.ibcmnfêterra.com.br\n\nNOME: INSTITUIÇÃO ASSISTENCIAL BENEFICENTE CONCEIÇÃO, MACEDO\n\nVALOR TOTAL DA NOTA = R$170,00\n\nCNAE:\n9430800 - Atividades de associação de defesa de direitos sociais\n\nitem da Lista de Serviços: R\n01701 - Assessoria ou consultoria de qualquer natureza, não contida em outros itens desta lista; análise, exame, pesquisa, coleta, co..\n\nYalor Total das Deduções (R$): Base de Cálculo (R$): Alíquota ( Vo): Valor do I38 (R$): Crédito Nota Salvador (RS\n0,00 170,00 5,00% 8,60 0,00\nValor INSS (R$) [valorPIS (RS: [Valor COFNS(RS: |ValorIR(RS, | Contribuições Bociais [outras Retenções (REI Valar Lindo (RS\n\nValor INSS ça | valor PIS (R$); Valor COFINS (R$). | Valor IR (R8) ES Sociais | Outras Retenções (R$) Valor Líquido (R$)\n- 0,00 0,00 0,00 0,00 170,00\nE 000 0004 0 (00 000 170,00\nAliquota IES (56). Valor IB3 (R$ Alíquota CES (5): Valor CBS (R$):\n\nOUTRAS INFORMAÇÕES\n\n- Esta Nota Salvador foi omilida com respaldo na Lei 7.186/2006.\n\n- Data de vencimento do. [SS desta Nota Salvador: 06/10/2026\n\n- COMPETÊNCIA; 09/2026 (mês/ano) |\n\n- Código de Tributação do Município: 1701-0/01 - Assessoria ou consultoria de qualquer natureza, exceto econômica, financeira, de imprensa,\nem informática ou relacionada a operações de fatorização (factoring)\n\n- Os valores de PIS/COFINS referem-se aos Valores de Apuração Própria, conforme Nota Técnica nº 07 do IBS/CBS.\n\nNúmero da Nota:\n00002278\n\nNúmero da Nota: "=:\nDOR | 00002278...\nData. e Hora de Emissão: .\ncoco | 02/09/2026 14:22:57... o\nCódigo de Verificação:\nalvador XTDBDGDS\n\nstd Do sa E ia Digi RS Número da Nota:\nge PREFEITURA MUNICIPAL DO SALVADOR 00002SE\n=» ra . SECRETARIA MUNICIPAL DA FAZENDA Data e Hora de Emissão:\nNa di Í ansaa a “+ 02/09/2026 14:22:57. ;\ne VA . A : Código de Verificação:\n\' NOTA FISCAL DE SERVIÇOS ELETRÔNICA - Nota Salvador XTDEDGDS lá\nPRESTADOR DE SERVIÇOS :\n\nPo À CPRICNPS: RR Inscrição Municipal: : U j .\n00.584.668/0001-05 . : 00.258.440/001-06 e : : :\nNome/Razão Social: . A :\n\n“| INSTITUICÃO ASSISTENÇIAL BENEFICENTE CONCEIÇÃO MACEDO a a )\nEndereço: eição Macio º o\n. Rua Santa Clara85. , ANDAR1E2Z SUBS - NAZARE - Salvador - CEP: 40040-450 - BA - : sy\nE-mail: É : :\no lbcm33gBterra.com.br -\nTOMADOR DE SERVIÇOS / ADQUIRENTE , .\n- Nome/Razão Social: É\nBONI. TRANSPORTES, LOGISTICA E COMERCIO LTDA. se :\nCPF/CNPJ: . Inscrição Municipal: : o\n04.555.283/0005-60 -—— ,\nEndereço: . . . . .\nRUA MARIA QUITERIA 263, GALPÃO ITINGA - Lauro de Freitas - CEP: 42738-205/BA . : ]\nE-mail: é :\nIMPOSTOSGBNORTECCONTABILIDADE.COM.BR o l\n\' . AS CRININAÇ ÃO DOS SERV O scante: THAMIRES DO NASCIMENTO LOPES DA SILVA, REFERENTE AO MÊS DE\nSETEMBRO/2 026. vo .\nDADOS BANCÁRIOS:\nAGÊNCIA :3072\nCONTA CORRENTE: 69.077-5\nCHAVE PIX (E-MAIL) :aprendiz.ibcmfêterra.com.br\nNOME-: INSTITUIÇÃO ASSISTENCIAL BENEFICENTE CONCEIÇÃO. MACEDO :\nVALOR TOTAL DA NOTA = R$170,00\nCNAE: :\n9430800 - Atividades de associação de defesa de direitos sociais\nItem da Lista de Serviços: p\n01701 - Assessoria ou consultoria de qualquer natureza, não contida em outros Itens desta lista; análise, exame, pesquisa, coleta, co...\nValor Total das Deduções (R$): Base de Cálculo (R$): . Alíquota (%): Valor do ISS (R$): Crédito Nota Salvador (R$):\n0,00 170,00 6,00% 8,60 0,00\nValor INSS (R$): Valor PIS (R$): Valor COFINS (R$): cus Sociais Ioutras Retenções (R$)] Valor Líquido (R$ \'\n0,00 0,00 0,00 — 0,00 — 0,00 0,00 170,00\n[DT DD TE ———A AA\nAlíquota IBS (%): Valor IBS (R$): Alíquota CBS (%): Valor CBS (R$):\nx a x a .\nLI] lJJD]J]][WVYVDJZDZ70õC—=—=—==>=>]]]—>D——IIID=F FA\nOUTRAS INFORMAÇÕES\n- Esta Nota Salvador foi emitida. com respaldo na Lei 7.186/2006.\n- Data de vencimento do. ISS desta Nota Salvador: 06/10/2026\n- COMPETÊNCIA: 09/2026 (mês/ano)\n- Código de Tributação do Município: 1701-0/01 - Assessoria ou consultoria de qualquer natureza, exceto econômica, financeira, de imprensa,\nem informática ou relacionada a operações de fatorização (factoring) ”\n- Os valores de PIS/COFINS referem-se aos Valores de Apuração Própria, conforme Nota Técnica nº 07 do IBS/CBS\n\nSSA_ALIQ_ISS_LEITURAS: aliq=6,00;6,00;6,00;6,00;5,00;5,00;6,00;6,00;6,00;6,00;6,00;5,00;5,00;6,00;6,00;5,00;5,00;6,00;5,00;5,00;5,00;6,00 iss=8,50;8,60;8,60;8,50;8,80;8,50;8,50;8,60;8,50;8,60;8,60;8,60;8,60;8,60;8,60;8,60;8,60;8,60;8,60;8,60;8,60;8,60;8,60;8,60;8,60;8,60;8,60;8,60\nSSA_DISCRIMINACAO_RECORTE: TAXA FORMAÇÃO PEDAGÓGICA DA ADOLESCENTE: THAMIRES DO NASCIMENTO LOPES DA SILVA, REFERENTE AO MÊS DE SETEMBRO/2026.'


@pytest.fixture
def nfse(monkeypatch):
    dummy_path = "tests/dummy_salvador_2278.pdf"
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_OCR)
    try:
        notas = SPPdfExtractor(dummy_path).parse_multiple()
        assert len(notas) == 1
        yield notas[0]
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_cabecalho(nfse):
    assert nfse.numero == "00002278"
    assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "02/09/2026 14:22:57"
    # Convenção do layout: código sem hífen. O "5" final impresso sai "S" na
    # maioria das leituras (limitação conhecida, ver DOCUMENTACAO).
    assert nfse.codigo_verificacao == "XTDPDGDS"
    # Competência da referência impressa ("COMPETÊNCIA: 09/2026").
    assert nfse.competencia.strftime("%Y-%m-%d") == "2026-09-01"


def test_prestador_identificado_com_cnpj_valido_e_im_separada(nfse):
    p = nfse.prestador
    assert p.cnpj_cpf == "00584568000105"
    assert p.razao_social == "INSTITUICÃO ASSISTENCIAL BENEFICENTE CONCEIÇÃO MACEDO"
    # IM impressa 00.258.440/001-06 — nunca confundida com o CNPJ.
    assert p.inscricao_municipal == "0025844000106"


def test_prestador_endereco_sem_logotipo_e_numero_separado(nfse):
    e = nfse.prestador.endereco
    assert e.logradouro == "Rua Santa Clara"
    assert e.numero == "85"
    assert e.bairro == "NAZARE"
    assert e.municipio == "Salvador"
    assert e.cep == "40040450"
    assert e.codigo_municipio == "2927408"


def test_tomador(nfse):
    t = nfse.tomador
    assert t.cnpj_cpf == "04555283000350"
    assert t.razao_social == "BONI TRANSPORTES, LOGISTICA E COMERCIO LTDA"
    assert t.endereco.logradouro == "RUA MARIA QUITERIA"
    assert t.endereco.numero == "263"
    assert t.endereco.municipio == "Lauro de Freitas"
    assert t.endereco.codigo_municipio == "2919207"
    assert t.endereco.cep == "42738205"


def test_aliquota_e_iss_lidos_que_fecham_com_a_base(nfse):
    v = nfse.valores
    assert v.valor_servicos == pytest.approx(170.00)
    assert v.base_calculo == pytest.approx(170.00)
    assert v.aliquota == pytest.approx(0.05)
    assert v.valor_iss == pytest.approx(8.50)
    assert v.valor_liquido_nfse == pytest.approx(170.00)
    assert not any('teto legal' in a or 'não confere' in a for a in nfse.avisos)


def test_discriminacao_real_sem_dados_bancarios(nfse):
    assert nfse.discriminacao == (
        "TAXA FORMAÇÃO PEDAGÓGICA DA ADOLESCENTE: THAMIRES DO NASCIMENTO LOPES "
        "DA SILVA, REFERENTE AO MÊS DE SETEMBRO/2026.")


# --------------------------------------------------------------------------
# Unidades das peças novas
# --------------------------------------------------------------------------

def test_sem_releitura_que_feche_aliquota_lida_valida_e_aviso_de_divergencia(monkeypatch):
    """Sem nenhuma leitura de ISS que feche a conta: fica a alíquota ≤ 5% mais
    votada (valor LIDO), o ISS lido é mantido (nunca calculado) e há aviso."""
    texto = MOCK_OCR.replace('iss=8,50;8,60;8,60;8,50;8,80;8,50;8,50;8,60;8,50',
                             'iss=8,60;8,60;8,60;8,60;8,80;8,60;8,60;8,60;8,60')
    dummy_path = "tests/dummy_salvador_2278b.pdf"
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: texto)
    try:
        nota = SPPdfExtractor(dummy_path).parse_multiple()[0]
    finally:
        os.remove(dummy_path)
    assert nota.valores.aliquota == pytest.approx(0.05)
    assert nota.valores.valor_iss == pytest.approx(8.60)
    assert any('não confere com o Valor do ISS' in a for a in nota.avisos)


def test_escolha_do_par_lido():
    esc = SPPdfExtractor._escolher_aliquota_iss_lidos
    assert esc(170.0, 0.06, 8.60, [6.0, 5.0, 5.0], [8.60, 8.50]) == (0.05, 8.50)
    assert esc(170.0, 0.06, 8.60, [6.0], [8.60]) is None
    # Teto: 6% nunca é aceito, nem fechando a conta (170 × 6% = 10,20).
    assert esc(170.0, 0.06, 10.20, [6.0], [10.20]) is None


def test_limpeza_de_borda_da_razao_social():
    limpar = SPPdfExtractor._limpar_borda_ocr_razao
    assert limpar("“| INSTITUICÃO ASSISTENCIAL MACEDO a a )") == "INSTITUICÃO ASSISTENCIAL MACEDO"
    assert limpar("BONI. TRANSPORTES LTDA. o") == "BONI. TRANSPORTES LTDA."
    # Caixa mista: não come o final do nome.
    assert limpar("Sao Pedro Construtora de") == "Sao Pedro Construtora de"
    assert limpar("EMPRESA X LTDA - ME") == "EMPRESA X LTDA - ME"


def test_endereco_a_partir_do_logradouro():
    f = SPPdfExtractor._endereco_salvador_a_partir_do_logradouro
    assert f("eição Macio º o\n. Rua Santa Clara85. , ANDAR - NAZARE") == "Rua Santa Clara85. , ANDAR - NAZARE"
    # 1ª linha legítima (com número) nunca é descartada.
    assert f("ua Ewerton Visco 290 , COND\nVILA X - Salvador") is None
    assert f("NR = o a\n\ngua MARIA QUITERIA 263") is None
    # A vírgula final que separa número de complemento é preservada
    # (regressão pega no lote: nota nº 754/fi.pdf, rótulo "Inscrição
    # Municipal" intercalado no meio do endereço).
    assert f("AVE PRAIA DE PAJUSSARA 554,\n\nInscrição Municipal\nQUADRA 28 - Lauro") == \
        "AVE PRAIA DE PAJUSSARA 554,\n\nInscrição Municipal\nQUADRA 28 - Lauro"


def test_discriminacao_para_nos_dados_bancarios():
    dummy_path = "tests/dummy_salvador_2278c.pdf"
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    try:
        ext = SPPdfExtractor(dummy_path)
        ext.layout = LAYOUT_SALVADOR
        ext.raw_text = ("DISCRIMINAÇÃO DOS SERVIÇOS\nSERVIÇO X REFERENTE A 09/2026\n"
                        "DADOS BANCÁRIOS:\nAGÊNCIA: 1\nVALOR TOTAL DA NOTA = R$10,00\n")
        assert ext._extrair_discriminacao() == "SERVIÇO X REFERENTE A 09/2026"
    finally:
        os.remove(dummy_path)
