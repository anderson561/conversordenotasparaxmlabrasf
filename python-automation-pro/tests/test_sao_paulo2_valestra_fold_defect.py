import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
import os

# Texto REAL do OCR (Tesseract, zoom 3x) de uma NFS-e de São Paulo ESCANEADA
# (nota real nº 00028202, VALESTRA NEGOCIOS E INVESTIMENTOS LTDA -> MASSA
# ALIMENTACAO E SERVICOS S/A). Uma dobra física do papel (canto da foto
# curvado) cobre literalmente a palavra "PREFEITURA DO" no título do
# cabeçalho, quebrando a detecção de layout e disparando uma cascata de
# efeitos colaterais na mesma nota:
#  - "Número da Nota\n00028202" e as linhas sintéticas de recorte dedicado
#    (Data e Hora de Emissão / Código de Verificação / grades de valores)
#    vêm PREPENDADAS pelo recorte dedicado (_ocr_header_box_sao_paulo e
#    _ocr_recut_grade_valores_sao_paulo), tal como capturado após os fixes
#    de 2026-08-17;
#  - a data do RPS na página inteira sai com o ano errado ("27/02/2028");
#  - o código de verificação da página inteira sai corrompido
#    ("BWP2-LR3IZ" em vez do real "BWP2-LR3Z");
#  - o endereço do prestador tem 3 segmentos separados por " - " (em vez
#    dos 2 segmentos historicamente assumidos), com um fragmento de CEP
#    truncado pela dobra ("CE...");
#  - "Município" sai sem acento ("Municipio"), quebrando o relax() que
#    exige o "í" literal;
#  - o e-mail do tomador tem o "@" lido como "Q" ("oriane.costaQnwgroup.com.br");
#  - o rótulo "Nome/Razão Social" do tomador sai com ";" em vez de ":".
MOCK_TEXT = """Número da Nota
00028202

IRRF (R$) CSLL (R$) COFINS (R$) PIS/PASEP (R$)
274,19 182,80 548,39 118,82
Valor Total das Deduções Alíquota Valor do ISS
0,00 5,00% 913,98

Número da Nota
00028202
Data e Hora de Emissão
27/02/2026 13:42:10
Código de Verificação
BWP2-LR3Z

poa
sia

> mUNICÍPIO DE SÃO PAULO [Nnsndnica

00028202
ECRETARIA MUNICIPAL DA FAZENDA Data e Hora de Emissão
e NOTA FISCAL ELETRÔNICA DE SERVIÇOS - NFS-e — is mo
IEOZZTU3OBABI64O0O104 RPS Nº 28139 Série 1, emitido em 27/02/2028 BWP2-LR3IZ
PRESTADOR DE SERVIÇOS
CPFICNPJ: 30.646.364/0001-04

A Inscrição Municipal: 59920149
loleste: Nome/Razão Social: VALESTRA NEGOCIOS E INVESTIMENTOS LTDA - MATRIZ

Endereço: AVENIDA DAS NAÇÕES UNIDAS 12901 - BROOKLIN PAULISTA - CONJ NORTE BLOCO A SALA 3301 - CE...
Municipio: São Paulo UF: SP

TOMADOR DE SERVIÇOS
Nome/Razão Social; MASSA ALIMENTACAO E SERVICOS S/A
CPFICNPJ: 09.033.381/0001-80

Inscrição Municipal;
Endereço: R SENADOR THEOTONIO VILELA 110 - PARQUE BELA VISTA - SALAS 203 E 204 - CEP: 40279-435
Municipio: Salvador UF: BA E-mail oriane.costaQnwgroup.com.br
INTERMEDIÁRIO DE SERVIÇOS
CPF/CNPJ: —

Nome/Razão Social: —

DISCRIMINAÇÃO DOS SERVIÇOS
Servicos Prestados
Vencimento; 06/03/2026
Valor Líquido: R$ 17155,45
AUDITORIA FEDERAL
PIS/COFINS | IRPJ/CSLL

o) pagamento deverá ser realizado exclusivamente pelo BOLETO, que será enviado junto a NF-e.
Valor Aprox. Tributos: RS 2038,18 - 11,15%

VALOR TOTAL DO SERVIÇO = R$ 18.279,65
INSS (R$)

IRRF (RS) CSLL IRS) COFINS (R$) PIS/PASEP (R$)
1 TO ray E" caso

118,82

IPI(RS)
0.00

Pr o coma Base de Cálculo (R$) Alíquota (%) Valor do ISS (R$) Crédito Programa da NFP (R$) aveles
some som a |
— EE

Valor Aproximado dos Tributos 7 Fonte pndet
- R$ 2.038,18 (11,15%) [IBPT pro
OUTRAS INFORMAÇÕES

| foi emitida com respaldo na Lei nº 14.097/2005; (2) O ISS desta NFS-e é devido DENTRO do Município de
do Belo: (3) Est NFS-e não gera crédito; (4) Esta NFS-e substitui o RPS Nº 28139 Série 1, emitido em 27/02/2026;
"""


def test_sao_paulo2_valestra_dobra_no_titulo_ainda_detecta_layout(monkeypatch):
    """Blindagem principal: mesmo com a dobra física cobrindo 'PREFEITURA DO'
    no título, a nota continua sendo detectada como LAYOUT_SAO_PAULO_2 (nota
    escaneada) — não cai em 'generico' nem gera 0 notas."""
    dummy_path = "tests/dummy_sp2_valestra.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        assert nfse.numero == "00028202"
        assert nfse.codigo_verificacao == "BWP2-LR3Z"
        assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "27/02/2026 13:42:10"
        assert nfse.competencia.strftime("%m/%Y") == "02/2026"

        # Prestador em São Paulo/SP; tomador em Salvador/BA.
        assert nfse.prestador.cnpj_cpf == "30646364000104"
        assert nfse.prestador.razao_social == "VALESTRA NEGOCIOS E INVESTIMENTOS LTDA - MATRIZ"
        assert nfse.prestador.endereco.bairro == "BROOKLIN PAULISTA"
        assert nfse.prestador.endereco.complemento == "CONJ NORTE BLOCO A SALA 3301"
        assert nfse.prestador.endereco.municipio == "São Paulo"
        assert nfse.prestador.endereco.uf == "SP"
        assert nfse.prestador.endereco.codigo_municipio == "3550308"

        assert nfse.tomador.cnpj_cpf == "09033381000180"
        assert nfse.tomador.razao_social == "MASSA ALIMENTACAO E SERVICOS S/A"
        assert nfse.tomador.endereco.bairro == "PARQUE BELA VISTA"
        assert nfse.tomador.endereco.complemento == "SALAS 203 E 204"
        assert nfse.tomador.endereco.municipio == "Salvador"
        assert nfse.tomador.endereco.uf == "BA"
        assert nfse.tomador.endereco.codigo_municipio == "2927408"
        assert nfse.tomador.email == "oriane.costa@nwgroup.com.br"

        # Grades de valores recuperadas pelo recorte dedicado
        # (_ocr_recut_grade_valores_sao_paulo) — Base de Cálculo e Valor
        # Líquido são DERIVADOS (não re-OCRizados), ver comentário na
        # branch LAYOUT_SAO_PAULO_2 de _extrair_valores.
        val = nfse.valores
        assert val.valor_servicos == pytest.approx(18279.65)
        assert val.valor_deducoes == pytest.approx(0.0)
        assert val.base_calculo == pytest.approx(18279.65)
        assert val.aliquota == pytest.approx(0.05)
        assert val.valor_iss == pytest.approx(913.98)
        assert val.valor_ir == pytest.approx(274.19)
        assert val.valor_csll == pytest.approx(182.80)
        assert val.valor_cofins == pytest.approx(548.39)
        assert val.valor_pis == pytest.approx(118.82)
        assert val.valor_liquido_nfse == pytest.approx(17155.45)
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
