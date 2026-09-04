import os

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor

# Texto REAL do OCR (Tesseract) da NFS-e de Camaçari/BA ESCANEADA — nota real
# nº 159, AVANÇO GESTÃO E ADMINISTRAÇÃO LTDA -> GUARAJUBA SHOPPING LTDA
# (lote de 30 notas em que Guarajuba Shopping, CNPJ 24.890.395/0001-03, é
# sempre a tomadora). Preservado verbatim (cabeçalho duplicado 3x pelo OCR de
# páginas sobrepostas, ruído de fundo, tudo como veio do pipeline). Quirks
# deliberadamente preservados para travar as regressões:
#  - a célula "Valor dos Serviços (R$)" saiu 100% ilegível ("RE pone");
#  - a célula "Base de Cálculo (=)" perdeu o dígito de milhar ("0194," em vez
#    de "9.194,55"), o que por sua vez gerava uma alíquota derivada de >100%
#    antes desta correção (ISS 400,00 / base errada 194,00 = 206%);
#  - o CNPJ do prestador usa VÍRGULA como separador de grupo ("59.132,742/
#    0001-13" em vez de "59.132.742/0001-13").
MOCK_TEXT = """Número da Nota
159 ú
. 27/02/2026 11:52: ::. -
Código de autenticidade
066628001
Nº; SN
3ORDO)

imero da Nota 7
159 |
tado Emissão”,
27/02/2026 11:52: :.. :
digo de autenticidade
737Z40FYJ
1
Nº; SN
UF: BA

Número da Nota
159
. 27/02/2026 11:52" ::. ;
Código de autenticidade
737ZAOFYJ
56628001
Nº; SN
RDO)

> E o : : ” usos A b á
dá PERES MAE: A Naga Número da Nota
PAi cetro ci PREFEITURA MUNICIPAL DE CAMAÇARI 159
; i ERR a ? E Deita do Emissão”, ;
O Da CO . SecrotariadaFazenda ap O mamão qua é, |
À Ê NOTA FISCAL DE SERVIÇOS ELETRÔNICA
PRESTADOR DE SERVIÇOS
Nome/Razão Social: AVANÇO GESTÃO E ADMINISTRAÇÃO LTDA
CPF/CNPJ: 59.132,742/0001-13 Inscrição Municipal: 0066628001
Logradouro: RUA ALA DAS DUNAS Nº; SN
Compl: :GUARAJUBA SHOPPING;LOJA:03;QUADRA:C-4 Bairro: GUARAJUBA (MONTE GORDO)
CEP: 42840312 Município: CAMAÇARI UF: BA
TOMADOR DE SERVIÇOS
Nome/Razão Social: GUARAJUBA SHOPPING LTDA
CPF/CNPJ: 24.890.395/0001-03 Inscrição Municipal: 0032035001
Logradouro: RODOVIA BA 099 ESTRADA DO COCO Nº: SN
Compl.: ALAMEDA DAS DUNAS GUARAJUBA SHOPPING Bairro: GUARAJUBA (MONTE GORDO)
CEP: 42840310 Município: CAMAÇARI UF: BA
DISCRIMINAÇÃO DOS SERVIÇOS
DESCRIÇÃO QTD VALOR UNIT (R$) VALOR TOTAL (R$)
TAXA DE SERVIÇOS COMBINADOS DE ESCRITÓRIO E APOIO ADMINISTRATIVO 1,0000 9.194,55 9.194,55
= q eRraDE 4 Mg dat E mta E
EA pero, BR ai, ema fest, aii, ie ap POD acoe  ER DERAA RR LR O
Hs à ' se ado MR tr [E ee ig E
e Retenções (R$) di cia 48 Totais (R$) EO Po
“PIS: 0,00 |Valor dos Serviços (R$) RE pone
COFINS: 0,00 | Deduções (6) : : pa
INSS; 0,00 |Base de Cálculo (=) 0194,
IR: : 0,00 |Aliquota (6). eo
CSLL: 0,00 |Valor do ISS (R$) 400,
Outras: 0,00 | Valor Líquido da Nota (=) 9.194,55
Total de Retenções: 0,00 : TST]
Tipo de tributação: A RECOLHER PELO PRESTADOR serao MAD prOntma Ra da aattipo: Fte
Múnicípio da prestação go nerviço: 2908791. GAMAGARI ape trr ncs S do nbpda tod "nani Ap o ja A
Município da tributação: 2905701 - CAMACARI Gina ci ani red : ; .
: 8211-3/00 - SERVIÇOS COMBINADOS DE ESCR
Ep 001703 - PLANEJAMENTO, COORDENAÇÃO, PROGRAMAÇÃO OU ORGANIZAÇÃO TÉCNICA, FINANCEIRA OU ADMINISTRATIVA.
CPqD - Gestão Pública Data Impressão: 27/02/2026 11:52
"""


def test_camacari3_grade_ilegivel_recupera_valores_e_cnpj_virgula(monkeypatch):
    dummy_path = "tests/dummy_camacari3_guarajuba_159.pdf"
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

        assert nfse.numero == "159"

        # Prestador: CNPJ com vírgula no lugar do 2º ponto ("59.132,742/0001-13")
        # agora casa no regex e valida checksum — antes caía no sentinela
        # "00000000000000" mesmo com o CNPJ legível e correto na nota.
        assert nfse.prestador.cnpj_cpf == "59132742000113"
        assert nfse.prestador.razao_social == "AVANÇO GESTÃO E ADMINISTRAÇÃO LTDA"
        assert nfse.prestador.inscricao_municipal == "0066628001"

        assert nfse.tomador.cnpj_cpf == "24890395000103"
        assert nfse.tomador.razao_social == "GUARAJUBA SHOPPING LTDA"

        # "Valor dos Serviços (R$)" ilegível ("RE pone") -> recuperado do
        # "Valor Líquido da Nota (=)", lido limpo na mesma grade.
        val = nfse.valores
        assert val.valor_servicos == pytest.approx(9194.55)
        # "Base de Cálculo (=)" truncada ("0194," -> 194,00) é implausível
        # (menor que Valor dos Serviços) -> recalculada como
        # Valor dos Serviços - Deduções.
        assert val.base_calculo == pytest.approx(9194.55)
        # Alíquota derivada de ISS/Base (400,00 / 9.194,55 ≈ 4,35%) — uma vez
        # a base corrigida, o percentual resultante é plausível e NÃO precisa
        # ser zerado.
        assert val.aliquota == pytest.approx(400.0 / 9194.55)
        assert val.valor_iss == pytest.approx(400.0)
        assert val.valor_liquido_nfse == pytest.approx(9194.55)

        # Nada precisou ser zerado nesta nota (alíquota derivada ficou
        # plausível após a correção da base) -> nenhum aviso de
        # alíquota/ISS não confiáveis.
        assert nfse.avisos == []
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
