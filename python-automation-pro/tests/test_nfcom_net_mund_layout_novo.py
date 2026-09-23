# -*- coding: utf-8 -*-
"""Nota real nº 683 (NET MUND BRASIL INTERNET E SEGURANCA LTDA -> RG
RESTAURANTE LTDA - EPP, R$150,00), achado 2026-09-23 - layout NOVO
`nfcom_net_mund`, mesmo template nacional NFCom (dfe-portal.svrs.rs.gov.br/
Nfcom) já usado por `nfcom_salvador`/`nfcom_rlgr`/`nfcom_lotec_fibra`/
`nfcom_sete_connect`, mas de um 5º emitente diferente.

Reportado pelo usuário com o PDF fonte real e o XML gerado (com erro) como
evidência. Sem detecção dedicada, a nota caía no fallback amplo
LAYOUT_NACIONAL (parser de DANFSe ABRASF, incompatível com a estrutura de
uma NFCom) e saía com o prestador sentinela ("Prestador Não Identificado",
CNPJ "00000000000100") e o campo <Numero> do endereço do tomador poluído
com um blob de ~250 caracteres vazado de outras seções da nota (data de
emissão, chave de acesso, protocolo, Cod. Assinante/Contrato).

Nome/CNPJ do prestador confirmados em 2 fontes independentes: (1) imagem
renderizada da própria página (zoom 6x, letterhead) e (2) consulta pública
do CNPJ 37.976.210/0001-20 na Receita Federal (razão social e endereço
idênticos, byte a byte) - "NET MUND BRASIL INTERNET E SEGURANCA LTDA", SEM
"O" final em "MUND" e SEM cedilha em "SEGURANCA", exatamente como impresso
no documento oficial (não é erro de OCR nem palpite).

DETECÇÃO ATÍPICA em relação aos 4 irmãos: nesta nota, TODA a faixa cinza do
cabeçalho (título "DOCUMENTO AUXILIAR..."/CNPJ impresso do prestador) falha
por completo na leitura de página inteira do Tesseract - nem o CNPJ
impresso nem a marca "FATURA DE SERVIÇOS..." sobrevivem no texto OCR real
(confirmado no dump completo abaixo). O gate usa a decodificação estrutural
da própria chave de acesso (dígitos 6:20 = CNPJ do emitente, mesma técnica
já validada no NFCOM_LOTEC_FIBRA para o cUF) combinada com a URL do portal
nacional do QR Code (também sobrevive). CONSEQUÊNCIA: ao contrário dos
irmãos, aqui a detecção e a extração do Código de Verificação dependem da
MESMA chave de 44 dígitos - se ela não sobrevive ao OCR, a nota nem chega a
ser detectada como este layout (não há teste de "chave ilegível mas layout
detectado" para este layout, diferente dos 4 irmãos - ver
`test_codigo_verificacao_fallback_nfcom_via_layout_forcado` abaixo, que
testa o fallback chamando `_extrair_codigo_verificacao` diretamente, com o
layout forçado, e não através da detecção).

A caixa "TOTAL A PAGAR: R$ 150,00" (mesma faixa cinza) também some da
leitura de página inteira, apesar de nitidamente legível na imagem
renderizada - recuperada por um recorte dedicado
(`_ocr_recut_total_pagar_nfcom_net_mund`, 0%-40% da largura, 32,5%-34,8% da
altura, zoom 6x + `--psm 6`), que devolve a linha já no MESMO formato dos
irmãos ("TOTAL A PAGAR: R$ 150,00") e é prependada ao texto principal -
reproduzido abaixo como já estaria depois desse recorte (mesma convenção
das fixtures de `test_nfcom_salvador_escaneado_nota4777.py`).

O endereço do tomador ("RODOVIA BA-535 - VIA PARAFUSO, 535 -
BOULEVARD-GIRAFFAS - PONTO CERTO") tem um hífen SEM espaços dentro do nome
composto do complemento ("BOULEVARD-GIRAFFAS", nome do empreendimento) -
`_extrair_tomador_nfcom_net_mund` usa um separador de campo que exige
espaço nos 2 lados do hífen (`\\s+-\\s+`, distinto do `\\s*-\\s*` dos
irmãos) para não quebrar o complemento ao meio nesse hífen interno.

O texto abaixo (exceto a 1ª linha, o recorte dedicado do TOTAL A PAGAR
prependado) é o resultado REAL e integral de `_extract_via_ocr` (Tesseract,
zoom 3x, leitura de página inteira) para a página única desta nota - usado
como fixture para travar a extração sem precisar rodar Tesseract no teste,
incluindo o ruído real da grade de itens/tributos que o OCR não consegue
ler bem (não usado por nenhum regex de extração deste layout)."""
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_NFCOM_NET_MUND

MOCK_OCR = (
    "TOTAL A PAGAR: R$ 150,00\n\n"
    "CLIENTE:\n\n"
    "RG RESTAURANTE LTDA - EPP\n\n"
    "CNPJ: 23.918.316/0001-62 IE: 129715168 IM: 20210225 [=] eta FISCAL FATURA Nº 00000000683\n"
    "A SÉRIE: 1\n\n"
    "ENDEREÇO:\n\n"
    "RODOVIA BA-535 - VIA PARAFUSO, 535 - BOULEVARD-GIRAFFAS - PONTO CERTO\n"
    "Camacari / BA - 42800938\n\n"
    "DATA DE EMISSÃO: 17/08/2026 às 08:08:21\n\n"
    "CHAVE DE ACESSO:\n"
    "2926 0837 9762 1000 0120 6200 1000 0006 8310 1272 4081\n\n"
    "Protocolo de Autorização: 3292600215842510\n\n"
    "INFORMAÇÕES:\n"
    "17/08/2026 às 08:08:24-0300\n\n"
    "Cod. Assinante: 107472 Contrato: 105627\n"
    "Telefone: 71999484558\n\n"
    "https://dfe-portal.svrs.rs.gov.br/Nfcom/ArCode?chNFCo! 926\n"
    "Período: 26/07/2026 à 25/08/2026\n\n"
    "0837976210000120620010000006831012724081 &tpAmb;=1\n\n"
    "REFERÊNCIA (ANO/MÊS): 08/2026 | ÁREA DO CONTRIBUINTE:\n\n"
    "| APÓS VENCIMENTO COBRAR MULTA DE R$ 3,00 E JUROS DE R$ 0,49 AO DIA,\n\n"
    "CoD. ITENS croP UN [ego] V. UNIT. TOTAL PIS/COFINS BC.ICMS | ALIQ V.ICMS V.IBSUF v.CBS\n\n"
    "0100201 Provimento de Acesso a Internet 5307, MB 1.000 R$150,00 R$150,00 R$0,00 |\n\n"
    "= PRAIA TAN DR: JP R$000 | 000% | R$000 R$000 | R$000 |\n\n"
    "E E E EI\n"
    "jo [== [em [mom\n\n"
    "Aliquota IBS UF\n\n"
    "Redução Alíquota IBS UF Alíquota Efetiva IBS\n"
    "Alíquota CBS Redução Alíquota CBS Alíquota Efetiva CBS\n\n"
    "SÃO\n\n"
    "Valor Diferido IBS UF. Valor IBS\n"
    "É R$ 0,00\n\n"
    "Valor Diferido CBS Valor CBS\n"
    "- R$ 0,00\n\n"
    "st ES\n\n"
    "Nº IDENTIFICADOR DE CÓDIGO DE BARRAS\n"
    "DÉBITO AUTOMÁTICO\n\n"
    "4039\n\n"
    "0.00007 37976.210015 97503.110013 2 15490000015000\n\n"
)


@pytest.fixture
def nfse(monkeypatch, tmp_path):
    dummy = tmp_path / "dummy_nfcom_net_mund_683.pdf"
    dummy.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_OCR)
    notas = SPPdfExtractor(str(dummy)).parse_multiple()
    assert len(notas) == 1
    return notas[0]


def test_layout_detectado_pela_chave_de_acesso_decodificada(tmp_path):
    # Nesta nota o CNPJ impresso do prestador (formatado, "37.976.210/...")
    # e a marca de título "FATURA DE SERVIÇOS..." NÃO sobrevivem ao OCR (ao
    # contrário dos 4 irmãos) - a detecção depende só da chave de acesso +
    # URL do portal. (Os dígitos "37976210" ainda aparecem soltos, sem
    # formatação, dentro do parâmetro bruto da URL do QR Code - por isso a
    # detecção real usa a posição exata dentro da CHAVE DE ACESSO, não uma
    # busca solta por esses dígitos em qualquer lugar do texto.)
    assert "37.976.210" not in MOCK_OCR
    assert "FATURA DE SERVI" not in MOCK_OCR.upper()
    assert "dfe-portal.svrs.rs.gov.br" in MOCK_OCR

    dummy = tmp_path / "dummy_layout.pdf"
    dummy.write_bytes(b"%PDF-1.4")
    ex = SPPdfExtractor(str(dummy))
    ex.from_ocr = True
    ex._pagina_veio_de_ocr = True
    assert ex._detect_layout_page(MOCK_OCR) == LAYOUT_NFCOM_NET_MUND


def test_prestador_fixo(nfse):
    assert nfse.prestador.razao_social == "NET MUND BRASIL INTERNET E SEGURANCA LTDA"
    assert nfse.prestador.cnpj_cpf == "37976210000120"
    assert nfse.prestador.endereco.municipio == "CAMAÇARI"
    assert nfse.prestador.endereco.codigo_municipio == "2905701"
    assert nfse.prestador.endereco.uf == "BA"


def test_tomador_dinamico_endereco_sem_vazamento(nfse):
    assert nfse.tomador.razao_social == "RG RESTAURANTE LTDA - EPP"
    assert nfse.tomador.cnpj_cpf == "23918316000162"

    end = nfse.tomador.endereco
    assert end.logradouro == "RODOVIA BA-535 - VIA PARAFUSO"
    assert end.numero == "535"
    # Hífen SEM espaço dentro do nome composto ("BOULEVARD-GIRAFFAS") não
    # pode quebrar o complemento ao meio - achado real desta nota, causa
    # raiz distinta do vazamento original (que era o parser genérico
    # capturando o documento inteiro, não este hífen específico).
    assert end.complemento == "BOULEVARD-GIRAFFAS"
    assert end.bairro == "PONTO CERTO"
    assert end.uf == "BA"
    assert end.cep == "42800938"
    assert end.codigo_municipio == "2905701"   # Camaçari/BA

    # O bug original: o <Numero> do tomador vazava data de emissão, chave
    # de acesso, protocolo e Cod. Assinante/Contrato de outras seções da
    # nota. Nenhum desses marcadores pode aparecer em NENHUM campo do
    # endereço do tomador.
    campos_endereco = (end.logradouro, end.numero, end.complemento, end.bairro)
    for marcador in ("DATA DE EMISSÃO", "CHAVE DE ACESSO", "Protocolo de Autorização", "Cod. Assinante"):
        for campo in campos_endereco:
            assert marcador not in campo


def test_competencia(nfse):
    assert nfse.competencia.strftime("%Y-%m") == "2026-08"


def test_data_de_emissao(nfse):
    assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "17/08/2026 08:08:21"


def test_codigo_servico_nao_incidencia(nfse):
    assert nfse.servico_codigo == "0000"


def test_codigo_verificacao_chave_de_44_digitos(nfse):
    chave = nfse.codigo_verificacao
    assert len(chave) == 44
    assert chave == "29260837976210000120620010000006831012724081"[:44]
    assert chave == "29260837976210000120620010000006831012724081"
    # Decodificação estrutural: dígitos 6:20 = CNPJ do prestador.
    assert chave[6:20] == "37976210000120"
    # dígitos 25:34 = número da nota (683), confirmado batendo com o
    # cabeçalho ("NOTA FISCAL FATURA Nº 00000000683").
    assert chave[25:34] == "000000683"


def test_codigo_verificacao_fallback_nfcom_via_layout_forcado(tmp_path):
    # Ao contrário dos 4 irmãos, para ESTE layout a detecção em si depende
    # da mesma chave de 44 dígitos usada no Código de Verificação (ver
    # docstring do módulo) - não é possível montar um texto onde a nota
    # seja detectada como `nfcom_net_mund` MAS a chave esteja ilegível.
    # O fallback honesto 'NFCOM' (mesmo critério dos outros 4 layouts
    # NFCom) é testado chamando `_extrair_codigo_verificacao` diretamente,
    # com o layout forçado, simulando um texto sem a chave.
    dummy = tmp_path / "dummy_sem_chave.pdf"
    dummy.write_bytes(b"%PDF-1.4")
    ex = SPPdfExtractor(str(dummy))
    ex.layout = LAYOUT_NFCOM_NET_MUND
    ex.raw_text = MOCK_OCR.replace(
        "CHAVE DE ACESSO:\n2926 0837 9762 1000 0120 6200 1000 0006 8310 1272 4081\n\n", "")
    assert ex._extrair_codigo_verificacao() == "NFCOM"


def test_valor_total_a_pagar_recuperado_via_recorte_dedicado(nfse):
    # A caixa "TOTAL A PAGAR" some da leitura de página inteira nesta nota
    # (ver `_ocr_recut_total_pagar_nfcom_net_mund`) - o MOCK_OCR já simula
    # o texto COM o recorte prependado (1ª linha), mesma convenção da
    # fixture de `test_nfcom_salvador_escaneado_nota4777.py`.
    assert nfse.valores.valor_servicos == pytest.approx(150.00)
    assert nfse.valores.valor_liquido_nfse == pytest.approx(150.00)


def test_base_calculo_aliquota_iss_zerados_com_aviso(nfse):
    assert nfse.valores.base_calculo == 0.0
    assert nfse.valores.aliquota == 0.0
    assert nfse.valores.valor_iss == 0.0
    assert any("ICMS" in a for a in nfse.avisos)


def test_prestador_nao_fica_sentinela(nfse):
    # Bug original: sem detecção, o prestador saía "Prestador Não
    # Identificado" com CNPJ sentinela "00000000000100".
    assert not nfse.prestador.cnpj_cpf.startswith("00000000000")
    assert nfse.prestador.razao_social != "Prestador Não Identificado"
    assert not any("prestador" in a.lower() for a in nfse.avisos)
