# -*- coding: utf-8 -*-
"""Nota real nº 2086 (RADIO E TELEVISAO BANDEIRANTES DA BAHIA LTDA -> PORTO
UNO AGENCIA DE IMOVEIS LTDA, R$3.000,00), achado 2026-09-24 - layout NOVO
`nfcom_bandeirantes`, mesmo template nacional NFCom (dfe-portal.svrs.rs.gov.br/
Nfcom) já usado por `nfcom_salvador`/`nfcom_rlgr`/`nfcom_lotec_fibra`/
`nfcom_sete_connect`/`nfcom_net_mund`, mas de um 6º emitente diferente.

Reportado pelo usuário com o PDF fonte real (1 página, ESCANEADA, 180°
INVERTIDA - o pipeline de OCR corrige a rotação sozinho) e o XML gerado (com
erro) como evidência. Sem detecção dedicada, a nota caía no fallback amplo
LAYOUT_NACIONAL (parser de DANFSe ABRASF, incompatível com a estrutura de
uma NFCom tributada por ICMS) e saía com <ValorServicos>0.00</ValorServicos>,
<CodigoVerificacao>XXXX-XXXX</CodigoVerificacao> (sentinela) e a razão social
do tomador poluída com a chave de acesso + o texto de placeholder do QR Code
PIX ("2926 0813 ... NÃO HÁ DADOS A SEREM IMPRESSOS").

Razão social/CNPJ do prestador confirmados por imagem renderizada da própria
página (300 DPI, rotação corrigida): "RADIO E TELEVISAO BANDEIRANTES DA
BAHIA LTDA", CNPJ 13.810.015/0001-67 - ambos sobrevivem limpos na leitura de
página inteira ("RAZÃO SOCIAL: ...", "CNPJ: 13,810,015/0001-67"), mas o CEP
e o número do endereço saem com dígitos trocados ("40715-150"/"194" em vez
dos reais "40215-150"/"19A") - por isso o prestador é hardcoded (mesmo
racional dos 5 layouts irmãos), não extraído do OCR.

Tomador extraído de um bloco SEM rótulos "CLIENTE:"/"CNPJ:"/"ENDEREÇO:" (ao
contrário dos 4 irmãos com bloco rotulado) - razão social e endereço vêm em
texto corrido logo após "Protocolo de Autorização:", terminando no rótulo
"CNPJ/CPF:". A linha "[[�������� – NÃO HÁ DADOS A SEREM IMPRESSOS." (placeholder
do QR Code PIX) é descartada por filtro de conteúdo. A linha do logradouro
sai colada pelo OCR ("ALSALVADOR" em vez de "AL SALVADOR") - corrigida por
um regex que reinsere o espaço só quando a linha começa literalmente por
"AL" seguido de maiúscula.

Competência: a "REFERÊNCIA" sai com o ano corrompido nesta nota ("08/1016"
em vez de "08/2026") - usa o mês/ano da Data de Emissão já resolvida em vez
de arriscar um ano errado (mesmo racional já usado em LAYOUT_GUARULHOS).

A caixa "TOTAL A PAGAR: R$ 3.000,00" se funde com a linha "DATA DE EMISSÃO"
na leitura de página inteira e o PRÓPRIO VALOR sai corrompido junto do
rótulo ("DATA DE EMISSÃO: 18/08/2026 EURAL – PAGAR: R$ 3.099,09" - confirmado
por imagem renderizada da página que o valor real é R$ 3.000,00, não
R$ 3.099,09) - recuperada por um recorte dedicado
(`_ocr_recut_total_pagar_nfcom_bandeirantes`, 49%-100% da largura,
14,8%-17,0% da altura, MESMO zoom 3x da leitura padrão), que devolve a linha
já no MESMO formato dos irmãos ("TOTAL A PAGAR: R$ 3.000,00") e é prependada
ao texto principal - reproduzido abaixo como já estaria depois desse
recorte (mesma convenção das fixtures de
`test_nfcom_salvador_escaneado_nota4777.py`/`test_nfcom_net_mund_layout_novo.py`).

Chave de Acesso: sobrevive limpa e completa na leitura de página inteira
desta nota (raro entre os 6 irmãos) - "2926 0813 8100 1500 0167 6210 0000
0020 8610 6115 0820" decodifica exatamente contra os demais campos já
confirmados (cUF=29 Bahia, AAMM=2608, CNPJ do emitente=13810015000167 nas
posições 6:20, modelo=62, série=100, número=000002086) e valida pelo dígito
verificador mod-11.

O texto abaixo (exceto a 1ª linha, o recorte dedicado do TOTAL A PAGAR
prependado) é o resultado REAL e integral de `_extract_via_ocr` (Tesseract,
zoom 3x, rotação 180° já corrigida) para a página única desta nota - usado
como fixture para travar a extração sem precisar rodar Tesseract no teste,
incluindo o ruído real (dígitos trocados no CEP/número do prestador, "EURAL
– PAGAR" em vez de "TOTAL A PAGAR", grade de itens ilegível)."""
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_NFCOM_BANDEIRANTES

MOCK_OCR = (
    "TOTAL A PAGAR: R$ 3.000,00\n\n"
    "DOCUMENTO AUXILIAR DA NOTA FISCAL FATURA DE SERVIÇOS DE COMUNICAÇÃO ELETRÔNICA\n"
    "RAZÃO SOCIAL: RADIO E TELEVISAO BANDEIRANTES DA BAHIA LTDA\n\n"
    "ENDEREÇO: RUA MAE MENININHA DO GANTOIS, 194 - FEDERACAO\n\n"
    "SALVADOR - BA - CEP: 40715-150\n\n"
    "CNPJ: 13,810,015/0001-67 LE: 06932983\n"
    "| REFERÊNCIA: 08/1016 4\n"
    "NOTA FISCAL FATURA No. 000002086\n\n"
    "DATA DE EMISSÃO: 18/08/2026 EURAL – PAGAR: R$ 3.099,09\n\n"
    "CÓDIGO DO CLIENTE: 99ABIPOL\n\n"
    "SÉRIE: 100 FM | VENCIMENTO: 20/08/2026\n"
    "FOLHA: 01/01\n"
    "J\n\n"
    "PERÍODO INICIAL: 11/08/2026 / PERIODO FINAL: 31/08/2026\n\n"
    "CONSULTE PELA CHAVE DE ACESSO EM: NS IDENTI DÉBITO AUTOMÁTICO: 00000000000000000000\n"
    "https://dfe-portaLsvre.rs.gov.br/Nfcom/QrCode CONGO DE BARRAS BOLETO: = =\n\n"
    "CHAVE DE ACESSO:\n\n"
    "2926 0813 8100 1500 0167 6210 0000 0020 8610 6115 0820 NÃO HÁ DADOS A SEREM IMPRESSOS.\n\n"
    "| QRCODE PIX:\n"
    "Protocolo de Autorização: 3292600217238894 - 18/08/2026\n"
    "[[�������� – NÃO HÁ DADOS A SEREM IMPRESSOS.\n\n"
    "PORTO UNO AGENCIA DE IMOVEIS LTDA\n"
    "| ALSALVADOR, S/N, SALA 2013 TORRE EUROPA\n"
    "CAMINHO DAS ARVORES - CEP: 41820-790\n\n"
    "SALVADOR - BA\n"
    "CNPJ/CPF: 04.022.897/0001-05\n"
    "ÁREA CONTRIBUINTE:\n"
    "2 T ] ;\n"
    "ITEM DA FATURA UN QUANT PREÇO UNIT (R$) VALOR TOTAL (R$) | PEVCOFINS (RS) ECICMS (RS) | amy | VALOR OMS (E\n"
    "VEICULACAO PAGA UN 1000 200,00 000,00 | uoe so avo uso | um"
)


@pytest.fixture
def nfse(monkeypatch, tmp_path):
    dummy = tmp_path / "dummy_nfcom_bandeirantes_2086.pdf"
    dummy.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_OCR)
    notas = SPPdfExtractor(str(dummy)).parse_multiple()
    assert len(notas) == 1
    return notas[0]


def test_layout_detectado_pelo_cnpj_do_emitente(tmp_path):
    assert "13,810,015/0001-67" in MOCK_OCR
    assert "FATURA DE SERVIÇOS DE COMUNICAÇÃO ELETRÔNICA" in MOCK_OCR

    dummy = tmp_path / "dummy_layout.pdf"
    dummy.write_bytes(b"%PDF-1.4")
    ex = SPPdfExtractor(str(dummy))
    ex.from_ocr = True
    ex._pagina_veio_de_ocr = True
    assert ex._detect_layout_page(MOCK_OCR) == LAYOUT_NFCOM_BANDEIRANTES


def test_prestador_fixo(nfse):
    assert nfse.prestador.razao_social == "RADIO E TELEVISAO BANDEIRANTES DA BAHIA LTDA"
    assert nfse.prestador.cnpj_cpf == "13810015000167"
    assert nfse.prestador.endereco.logradouro == "RUA MAE MENININHA DO GANTOIS"
    assert nfse.prestador.endereco.numero == "19A"
    assert nfse.prestador.endereco.bairro == "FEDERACAO"
    assert nfse.prestador.endereco.municipio == "SALVADOR"
    assert nfse.prestador.endereco.codigo_municipio == "2927408"
    assert nfse.prestador.endereco.uf == "BA"
    # O prestador é FIXO/hardcoded justamente porque o CEP e o número saem
    # com dígitos trocados no OCR desta nota ("40715-150"/"194") - a nota
    # real confirmada visualmente traz "40215-150"/"19A".
    assert nfse.prestador.endereco.cep == "40215150"
    assert "40715150" not in nfse.prestador.endereco.cep


def test_tomador_dinamico_sem_bloco_rotulado(nfse):
    assert nfse.tomador.razao_social == "PORTO UNO AGENCIA DE IMOVEIS LTDA"
    assert nfse.tomador.cnpj_cpf == "04022897000105"

    end = nfse.tomador.endereco
    # "ALSALVADOR" (colado pelo OCR) -> "AL SALVADOR" (espaço reinserido).
    assert end.logradouro == "AL SALVADOR"
    assert end.numero == "S/N"
    assert end.complemento == "SALA 2013 TORRE EUROPA"
    assert end.bairro == "CAMINHO DAS ARVORES"
    assert end.municipio == "SALVADOR"
    assert end.uf == "BA"
    assert end.cep == "41820790"
    assert end.codigo_municipio == "2927408"  # Salvador/BA

    # O bug original: a razão social/endereço do tomador saíam poluídos com
    # a chave de acesso e o placeholder do QR Code PIX. Nenhum desses
    # marcadores pode aparecer em nenhum campo do tomador.
    campos = (nfse.tomador.razao_social, end.logradouro, end.numero, end.complemento, end.bairro)
    for marcador in ("NÃO HÁ DADOS", "2926 0813", "QRCODE", "CHAVE DE ACESSO"):
        for campo in campos:
            assert marcador not in campo


def test_competencia_via_data_emissao(nfse):
    # A "REFERÊNCIA" sai com o ano corrompido nesta nota ("08/1016") - usa
    # o mês/ano da Data de Emissão em vez de arriscar um valor errado.
    assert nfse.competencia.strftime("%Y-%m") == "2026-08"


def test_data_de_emissao(nfse):
    assert nfse.data_emissao.strftime("%d/%m/%Y") == "18/08/2026"


def test_codigo_servico_nao_incidencia(nfse):
    assert nfse.servico_codigo == "0000"


def test_codigo_verificacao_chave_de_44_digitos_validada_por_dv(nfse):
    chave = nfse.codigo_verificacao
    assert len(chave) == 44
    assert chave == "29260813810015000167621000000020861061150820"
    # Decodificação estrutural: dígitos 6:20 = CNPJ do prestador.
    assert chave[6:20] == "13810015000167"
    # dígitos 25:34 = número da nota (2086), confirmado batendo com o
    # cabeçalho ("NOTA FISCAL FATURA No. 000002086").
    assert chave[25:34] == "000002086"
    # Dígito verificador mod-11 confere.
    ex = SPPdfExtractor.__new__(SPPdfExtractor)
    assert ex._dv_chave_nfe(chave[:43]) == chave[43]


def test_codigo_verificacao_fallback_nfcom_quando_dv_nao_bate(tmp_path):
    # Fallback honesto 'NFCOM' (mesmo critério dos outros 5 layouts NFCom)
    # quando o dígito verificador mod-11 não bate - simulado corrompendo
    # 1 dígito da chave lida.
    dummy = tmp_path / "dummy_chave_invalida.pdf"
    dummy.write_bytes(b"%PDF-1.4")
    ex = SPPdfExtractor(str(dummy))
    ex.layout = LAYOUT_NFCOM_BANDEIRANTES
    ex.raw_text = MOCK_OCR.replace(
        "2926 0813 8100 1500 0167 6210 0000 0020 8610 6115 0820",
        "2926 0813 8100 1500 0167 6210 0000 0020 8610 6115 0821")
    assert ex._extrair_codigo_verificacao() == "NFCOM"


def test_valor_total_a_pagar_recuperado_via_recorte_dedicado(nfse):
    # A caixa "TOTAL A PAGAR" se funde com "DATA DE EMISSÃO" na leitura de
    # página inteira e o valor sai corrompido ("R$ 3.099,09") - o MOCK_OCR
    # já simula o texto COM o recorte dedicado prependado (1ª linha), mesma
    # convenção da fixture de `test_nfcom_net_mund_layout_novo.py`.
    assert nfse.valores.valor_servicos == pytest.approx(3000.00)
    assert nfse.valores.valor_liquido_nfse == pytest.approx(3000.00)


def test_base_calculo_aliquota_iss_zerados_com_aviso(nfse):
    assert nfse.valores.base_calculo == 0.0
    assert nfse.valores.aliquota == 0.0
    assert nfse.valores.valor_iss == 0.0
    assert any("ICMS" in a for a in nfse.avisos)


def test_prestador_nao_fica_sentinela(nfse):
    assert not nfse.prestador.cnpj_cpf.startswith("00000000000")
    assert nfse.prestador.razao_social != "Prestador Não Identificado"
    assert not any("prestador" in a.lower() for a in nfse.avisos)
