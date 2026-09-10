# -*- coding: utf-8 -*-
"""Nota real nº 4777 (Empresa Baiana de Jornalismo S.A./EBJ -> SIND
DELEGADOS DE POLICIA DO EST DA BAHIA ADPEB/SINDICATO), achado 2026-09-09 —
1ª nota ESCANEADA já vista do layout `nfcom_salvador` (até então só PDF
digital, ver seção 27b do DOCUMENTACAO_CONVERSAO.md).

Reportado pelo usuário: "Valor e tomador do serviço incorretos". A leitura
de página inteira funde as 2 colunas do cabeçalho linha a linha — mesma
família de bug já vista em `nfcom_rlgr` escaneado ("NOME DO DESTINATÁRIO:
SIND DELEGADOS DE POLICIA DO EST DA BAHIA NOTA FISCAL FATURA Nº 000004777",
a coluna direita vazando pra dentro do bloco do tomador) — e o CNPJ do
tomador sai com o "-" lido como ":" ("73.393.696/0001:37"). Sem correção, o
tomador saía "Tomador Não Identificado"/CNPJ zerado.

A caixa cinza "TOTAL A PAGAR (R$): 440,00" não aparece em NENHUMA combinação
de zoom/PSM testada na leitura de página inteira (3/4/6/11/12) — só "VALOR
TOTAL NFF" sobrevive, sem o número ao lado. Sem correção, Valor dos Serviços
saía 0,00.

Corrigido com 2 recortes dedicados, gated pelo mesmo marcador (CNPJ da EBJ +
título) já usado em `_detect_layout`:
- `_ocr_recut_tomador_nfcom_salvador_escaneado`: isola a caixa esquerda do
  cabeçalho (0%-48% da largura, 19%-28,5% da altura), zoom 3x + `--psm 4` —
  devolve rótulo e valor na MESMA linha/ordem DIRETA (o oposto da ordem
  parcialmente invertida do PDF digital original).
- `_ocr_recut_total_pagar_nfcom_salvador_escaneado`: isola só a caixa
  "TOTAL A PAGAR" (55%-100% da largura, 28,3%-31,7% da altura), zoom 6x +
  `--psm 6` — o rótulo em si sai instável entre zoom/PSM, mas o número
  ("440,00") sai consistente; devolvido já formatado como texto sintético
  ("TOTAL A PAGAR (R$): 440,00") para garantir que o regex de extração
  sempre bata, com o valor 100% vindo do OCR real.

`_extrair_tomador_nfcom_salvador` ganhou um novo branch (tentado primeiro)
para a estrutura rótulo:valor na mesma linha/ordem direta, com fallback
para a lógica digital original quando não bate — validado sem regressão
contra as notas digitais já existentes deste layout.

O texto abaixo é o resultado REAL de `_extract_via_ocr` (Tesseract, já com
os 2 recortes prependados) para a página única desta nota, usado como
fixture para travar a extração sem precisar rodar Tesseract no teste."""
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_NFCOM_SALVADOR

MOCK_OCR = (
    "NOME DO DESTINATÁRIO: SIND DELEGADOS DE POLICIA DO EST DA BAHIA\n"
    "ADPEB/SINDICATO\n\n"
    "END.: R DIREITA DA PIEDADE, 11 - BARRIS - SALVADOR - BA\n\n"
    "CPF/CNPJ: 73.393.696/0001-37 CÓD. DO CLIENTE:\n"
    "INSC. EST.: INSC. MUN.:\n\n\n"
    "TOTAL A PAGAR (R$): 440,00\n\n"
    "Correio\n\n"
    "páginal/1\n"
    "DOCUMENTO AUXILIAR DA NOTA FISCAL FATURA DE SERVIÇOS DE COMUNICAÇÃO ELETRÔNICA\n\n"
    "EMPRESA BAIANA DE JORNALISMO S.A,\n\n"
    "END: RUA PROFESSOR ARISTIDES NOVIS, 123 BAIRRO: FEDERACAO\n\n"
    "CEP 40210-630 MUNICÍPIO: SALVADOR ur BA\n\n"
    "CNPy 14.583.041/0001-62 INSC.EST: 070667430\n"
    "NOME DO DESTINATÁRIO: SIND DELEGADOS DE POLICIA DO EST DA BAHIA NOTA FISCAL FATURA Nº 000004777\n\n"
    "ADPEB/SINDICATO séRiE: 090\n"
    "END.: R DIREITA DA PIEDADE, 11 - BARRIS - SALVADOR - BA DATA DE EMISSÃO: 09/07/2026\n"
    "CONSULTE PELA CHAVE DE ACESSO:  tttp:/Jdteportal rss poe br/Nícom\n\n"
    "CPF/CNPJ: 73.393.696/0001:37 CÓD. DO CLIENTE: CHAVE DE ACESSO: 2926 0714 5830 4100 0162 6209 0000 0047 7710 8312 2558\n"
    "INSC. EST.: INSC. MUN.: PROTOCOLO DE AUTORIZAÇÃO: — 3292600176348236 - 09/07/2026 - 11h48min\n\n"
    "impostos Retidos:\n\n"
    "VEICULACAO PUBLICIDADE JORNAL IMPRESSO\n\n"
    "' VALOR TOTAL NFF\n\n"
    "RESERVADO AO FISCO\n\n"
    "INFORMAÇÕES COMPLEMENTARES\n\n"
    "EDITAL DE CONVOCAÇÃO PUBLICAÇÃO: 08/07/2026\n\n"
)


@pytest.fixture
def nfse(monkeypatch, tmp_path):
    dummy = tmp_path / "dummy_nfcom_salvador_4777.pdf"
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
    assert ex._detect_layout_page(MOCK_OCR) == LAYOUT_NFCOM_SALVADOR


def test_tomador_identificado_com_nome_e_cnpj_corretos(nfse):
    # Antes: "Tomador Não Identificado" / CNPJ 00000000000000.
    assert nfse.tomador.razao_social == "SIND DELEGADOS DE POLICIA DO EST DA BAHIA ADPEB/SINDICATO"
    assert nfse.tomador.cnpj_cpf == "73393696000137"
    # Antes da correção do "-" lido como ":", o dígito verificador batia
    # errado por causa do separador — o CNPJ real tem checksum válido.
    assert "73.393.696/0001:37" in MOCK_OCR  # a armadilha continua no texto


def test_tomador_endereco(nfse):
    end = nfse.tomador.endereco
    assert end.logradouro == "R DIREITA DA PIEDADE"
    assert end.numero == "11"
    assert end.bairro == "BARRIS"
    assert end.municipio == "SALVADOR"
    assert end.uf == "BA"


def test_valor_dos_servicos_nao_fica_zerado(nfse):
    # Antes: 0.0 (a caixa "TOTAL A PAGAR" não sobrevivia à leitura de
    # página inteira em nenhuma combinação de zoom/PSM).
    assert nfse.valores.valor_servicos == 440.00
    assert nfse.valores.valor_liquido_nfse == 440.00


def test_prestador_numero_data_codigo_verificacao_preservados(nfse):
    # Estes já saíam corretos antes da correção — travados aqui para
    # garantir que os 2 recortes novos não regridem nada.
    assert nfse.prestador.cnpj_cpf == "14583041000162"
    assert nfse.numero == "4777"
    assert nfse.data_emissao.strftime("%d/%m/%Y") == "09/07/2026"
    assert nfse.codigo_verificacao == "29260714583041000162620900000047771083122558"


def test_base_calculo_aliquota_iss_zerados_com_aviso(nfse):
    assert nfse.valores.base_calculo == 0.0
    assert nfse.valores.aliquota == 0.0
    assert nfse.valores.valor_iss == 0.0
    assert any("ICMS" in a for a in nfse.avisos)
