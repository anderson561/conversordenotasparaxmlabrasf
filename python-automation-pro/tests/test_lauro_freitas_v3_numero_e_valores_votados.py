# -*- coding: utf-8 -*-
"""3ª variante do layout Lauro de Freitas/BA (`LAYOUT_LAURO_FREITAS`) — nota
irmã da coberta por `test_lauro_freitas_v3_mag_comercio.py` (mesma
prestadora, mesmo template): nota real nº 202600000016746 (MAG COMERCIO
VAREJISTA DE MATERIAL ELETRICO E SERVICOS TECNICOS DE INSTALAÇÃO E
MANUTENÇÃO → BONI LOGISTICA LTDA, R$410,00), achado real 2026-08-25, MESMO
DIA da nota 16748, só 2 notas depois na numeração.

Apesar de ser o MESMO layout/template já coberto, esta nota expôs que um
recorte de zoom ÚNICO não é confiável para vários campos que na nota 16748
saíam limpos de primeira: o Tesseract embaralha o Número NFS-e de forma
DIFERENTE a cada zoom testado (nunca 2 tentativas concordam), a grade
VALORES sai com as 3 primeiras colunas ausentes/fora de ordem, e o CEP do
prestador perde 1 dígito ("4270º-450" em vez de "42701-450") no MESMO zoom
que lê o resto do bloco corretamente. Motivou 3 mecanismos novos e
GENÉRICOS em `_ocr_recut_lauro_freitas_v3` (não específicos desta nota):

1. Número NFS-e + Data de Emissão: reamostrados em 6 zooms x 2 PSMs (12
   tentativas), votados pelos ÚLTIMOS 11 dígitos capturados + ano da Data de
   Emissão (capturada por FORMATO, não por rótulo — o rótulo "Data e Hora de
   Emissão" também sai embaralhado em várias tentativas).
2. CEP do prestador/tomador: reamostrado em 6 zooms dedicados, só aceita
   leituras com exatamente 8 dígitos limpos (rejeita a leitura truncada em
   vez de propagar um CEP de 4-7 dígitos).
3. Grade VALORES: quando a extração estrita de 8 colunas falha, cai para
   reamostrar só a dupla mais estável (Base de Cálculo + Alíquota, presente
   em TODAS as ~20 tentativas testadas) e DERIVA o resto matematicamente
   (Valor Serviço = Base de Cálculo quando nenhuma tentativa indica desconto/
   dedução != 0; Valor ISS = Base × Alíquota) — mesmo princípio já usado no
   recorte BioControl.

`MOCK_TEXT` é o texto REAL capturado via `_ocr_page` (sentinelas + OCR de
página inteira), preservando os mesmos ruídos que motivaram os fixes acima.
"""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_LAURO_FREITAS

MOCK_TEXT = (
    "LFV3_NUMERO: 202600000016746\n"
    "LFV3_DATA_EMISSAO: 24/07/2026 10:27:01\n"
    "LFV3_PREST_CNPJ: 15243835000140\n"
    "LFV3_PREST_RAZAO: MAG COMERCIO VAREJISTA DE MATERIAL ELETRICO E SERVICOS TECNICOS DE INSTALAÇÃO E MANUTEN\n"
    "LFV3_PREST_LOGRADOURO: Avenicis Luiz Tarquínio Portes\n"
    "LFV3_PREST_NUMERO: 1904\n"
    "LFV3_PREST_COMPLEMENTO: Sais 70)\n"
    "LFV3_PREST_BAIRRO: Pitangueiras\n"
    "LFV3_PREST_MUNICIPIO: LAURO DE FREITAS\n"
    "LFV3_PREST_UF: BA\n"
    "LFV3_PREST_CEP: 42701450\n"
    "LFV3_TOM_CNPJ: 04555283000199\n"
    "LFV3_TOM_RAZAO: BONI LOGISTICA LTDA\n"
    "LFV3_TOM_LOGRADOURO: RUA GERINO DE SOUZA FILHO 11 FTINGA\n"
    "LFV3_TOM_NUMERO: S/N\n"
    "LFV3_TOM_MUNICIPIO: Lauro de Freitas\n"
    "LFV3_TOM_UF: BA\n"
    "LFV3_TOM_CEP: 42738200\n"
    "LFV3_COD_SERVICO: 1401\n"
    "LFV3_VALOR_SERVICO: 410,00\n"
    "LFV3_BASE_CALCULO: 410,00\n"
    "LFV3_DESC_COND: 0,00\n"
    "LFV3_DESC_INCOND: 0,00\n"
    "LFV3_DEDUCOES: 0,00\n"
    "LFV3_ALIQUOTA: 5,0000\n"
    "LFV3_VALOR_ISS: 20,50\n"
    "LFV3_ISSQN_RETIDO: 0,00\n"
    "Número NFS-s\n\n"
    "PREFEITURA MUNICIPAL DE — 202800000016746\n"
    "LAURO DE FREITAS / BA gears pro\n"
    "NOTA FISCAL DE SERVIÇOS ELETRÔNICA - NES-e Código de Verificação\n\n"
    "OFDOA1DE\n\n"
    "meme rm) RPS Nº: 6969 Séria: 1 Emitido em: 24/07/2026\n\n"
    "PRESTADOR DE SERVIÇOS\n\n"
    "CNPJ/CPF: 15.243.835/0001-40 Inscrição Municipe\": COO039s 220011 Inscrição Estadual 278453\n"
    "Nome/Razão Social: MAG COMERCIO VAREJISTA DE MATERIAL ELETRICO E SERVICOS TECNICOS DE INSTALACAO E MANUTEN\n"
    "Endereço: Avenida Lutz Tarquínio Pontes 1904 Sais 70, Pitangueiras\n\n"
    "Município: LAURO DE FREITAS UF: BA CEP: 42701-450\n\n"
    "Fone:\n\n(71) 3280-2050 E-mail: assisencisfomagengenharia com.br\n\n"
    "TOMADOR DE SERVIÇOS\n"
    "CNPJ/CPF: 04.555.283/0001-99 Inscrição Municipal: Inscrição Estadual: ISENTO\n"
    "Nome/Razão Social: BONI LOGISTICA LTDA\n"
    "RUA GERINO DE SOUZA FILHO 11 ITINGA\n"
    "Município: Lauro de Freitas UFBA CEP: 42738-200 PAÍS: Bresil\n"
    "Fone: 71) 3283-5310 E-mail: fiscolgiboniakimentos com lx\n"
    "DISCRIMINAÇÃO DOS SERVIÇOS\n\n"
    "Ordem de Servico 8096 - 1.1.2 - Serviço Manutenção Laborstório\n"
    "- Serviço de manutenção preventiva e corretiva em nobreak com substituição de peças - Garantia ce baterias |- mases a partir da\n"
    "Instalação (Materiais aplicados conforme OS-Bateria 12V TAH )- 05:26 .8056 - Sente -2X0M3000%:34G7 NOBREAK ATTIV 1200 VA BIVOLT INTELBRAS\n\n"
    "- Forma de pagamento: Boleto - 24.08.2026\n"
    "NBS:120018900\n\n"
    "TRIBUTAÇÃO DE ISSQN\n"
    "Regime Espacial de Tributaçéic: 6 - ME S==- Simples Nacional\n"
    "ISS Retido: NÃO Natureza da Operação: 7 - Tibutação na município\n\n"
    "Optante Simples: SIM Local de Prestação; LAURO DE FEEITAS \"BA\n"
    "Incentivador Cultural: NÃO Município ce Incidêncie: LAJRO DE FOEITAS 'BA e\n"
    "VALORES\n"
    "Valor Serviço Desc. Cond. Desc. Incond. Deduções Bese de Cálculo Allg. ISS (%) Vuior ISS ISSQN Retido j 185 Reúdo\n"
    "R$410,00 R$0,00 R$ 0,00 R$000 R$ 410,00 5.0000 RS 20,50 R$0,00. x NÃO\n"
    "OUTRAS INFORMAÇÕES\n\n"
    "- Esta NFS-e foi emitida através do RPS Nº 6969 séria 1, emitido em 24/07/25.\n"
)


def _novo_extrator():
    dummy_path = "tests/dummy_lauro_freitas_v3_16746.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = MOCK_TEXT
    return extractor, dummy_path


def test_numero_reconstruido_por_voto_apesar_do_cabecalho_embaralhado():
    extractor, dummy_path = _novo_extrator()
    try:
        extractor.layout = LAYOUT_LAURO_FREITAS
        # BUG CORRIGIDO: um zoom único do cabeçalho lia o Número NFS-e
        # totalmente errado ("99260000001674%", "9250000001674%",
        # "W2600000016746"...) — nenhuma tentativa isolada acertava.
        assert extractor._extrair_numero() == "202600000016746"
    finally:
        os.remove(dummy_path)


def test_data_emissao_recuperada_apesar_do_rotulo_embaralhado():
    extractor, dummy_path = _novo_extrator()
    try:
        extractor.layout = LAYOUT_LAURO_FREITAS
        # BUG CORRIGIDO: "Data e Hora de Emissão" virou ruído total na
        # leitura de página inteira ("LAURO DE FREITAS / BA gears pro"),
        # caindo no sentinela "agora" (mês errado na Competência).
        data = extractor._extrair_data_emissao()
        assert data.year == 2026
        assert data.month == 7
        assert data.day == 24
        assert data.hour == 10
        assert data.minute == 27
        assert not extractor._data_emissao_fallback
    finally:
        os.remove(dummy_path)


def test_prestador_cep_nao_fica_truncado():
    extractor, dummy_path = _novo_extrator()
    try:
        extractor.layout = LAYOUT_LAURO_FREITAS
        prestador = extractor._extrair_entidade('Prestador')
        # BUG CORRIGIDO: o zoom fixo único lia "4270º-450" (1 dígito virou
        # "º"), que sem validação de 8 dígitos viraria um CEP de 4 dígitos.
        assert prestador.endereco.cep == "42701450"
    finally:
        os.remove(dummy_path)


def test_tomador_cep_tolera_ponto_e_virgula_no_lugar_de_dois_pontos():
    extractor, dummy_path = _novo_extrator()
    try:
        extractor.layout = LAYOUT_LAURO_FREITAS
        tomador = extractor._extrair_entidade('Tomador')
        # BUG CORRIGIDO: "CEP; 42738-200" (ponto e vírgula, não dois pontos)
        # não batia com o `:?` literal da regex antiga.
        assert tomador.endereco.cep == "42738200"
    finally:
        os.remove(dummy_path)


def test_valores_derivados_quando_grade_estrita_nao_bate():
    extractor, dummy_path = _novo_extrator()
    try:
        extractor.layout = LAYOUT_LAURO_FREITAS
        # BUG CORRIGIDO: a grade de 8 colunas saía embaralhada (rótulos
        # "Valor Serviço"/"Desc. Cond."/"Desc. Incond." ausentes de várias
        # tentativas), retornando tudo zero. Corrigido reamostrando a dupla
        # Base de Cálculo+Alíquota (estável em todas as tentativas) e
        # derivando o resto (Valor Serviço = Base; Valor ISS = Base×Alíquota).
        valores = extractor._extrair_valores()
        assert valores.valor_servicos == pytest.approx(410.0)
        assert valores.base_calculo == pytest.approx(410.0)
        assert valores.aliquota == pytest.approx(0.05)
        assert valores.valor_iss == pytest.approx(20.50)
        assert valores.desconto_condicionado == pytest.approx(0.0)
        assert valores.desconto_incondicionado == pytest.approx(0.0)
        assert valores.valor_deducoes == pytest.approx(0.0)
    finally:
        os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
