# -*- coding: utf-8 -*-
"""Texto REAL do OCR (Tesseract) da NFS-e de Camaçari/BA ESCANEADA — nota real
nº 201, AVANÇO GESTÃO E ADMINISTRAÇÃO LTDA -> GUARAJUBA MALLS S/A (3º PDF do
lote Guarajuba Shopping, "NFSe TOMADOS 3.pdf", página 5 de 5). Pedido do
usuário: "verificar o motivo da página 5 não está sendo extraída" — a página
tinha texto 100% legível na imagem, mas o PSM automático do Tesseract (modo
padrão de `_ocr_page`) não encontrava NENHUM bloco de texto em nenhuma das 4
rotações testadas (0 caracteres), derrubando a nota inteira do resultado.

Este texto já é o resultado APÓS o fallback de `_ocr_page` que tenta `--psm 6`
como último recurso quando o PSM automático falha por completo em qualquer
rotação (generalização do mesmo fallback já usado só para Salvador). PSM 6
recupera a página, mas reordena colunas de forma diferente do PSM automático,
introduzindo 3 corrupções novas travadas por este teste:
 - o rótulo "CPF/CNPJ" do prestador saiu "CPFICNPJ" (a "/" lida como "I");
 - a razão social do prestador saiu com "Inscrição Municipal: 0066628001"
   colado na MESMA linha (normalmente em linha separada);
 - a linha do item na discriminação foi partida em 2 pedaços não-contíguos,
   deixando só um "1" solto (sem vírgula) onde deveria estar o 2º valor
   total "12.694,47" — a grade "Valor dos Serviços (R$)" está limpa e deve
   prevalecer neste caso.

Limitação conhecida, não escondida: a razão social do TOMADOR sai "GUARAJUBA
MALLS S/A É 035001" (fragmento "035001" da Inscrição Municipal vazando sem
nenhum rótulo por perto para ancorar um corte) — sem um rótulo reconhecível
colado, não há como distinguir esse ruído de um sufixo legítimo da razão
social sem arriscar cortar nomes de empresas de verdade; mantido como está.
"""
import os

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_TEXT = """201
16/04/2026 15:41
Código de autenticidade
R705XU5B2
66628001
Nº; SN
ORDO)

pro da Nota
201

de Emissão

16/04/2026 15:41
go de autenticidade
R705XU5B2

Nº; SN
UF: BA

Número da Nota
201
Data de Emissão
16/04/2026 15:41
Código de autenticidade
R705XU5B2
0066628001
Nº; SN

; 201
a PREFEITURA MUNICIPAL DE CAMAÇARI
pa Secretaria da Fazenda ss ea Lind
k FE gd
Ms NOTA FISCAL DE SERVIG
PRESTADOR DE SERVIÇOS
ÃO LTDA
Nome/Razão Social: AVANÇO GESTÃO E ADMINISTRAÇ inscrição Municipal: 0066628001
CPFICNPJ: 59.132.742/0001-13 Nº: SN
Logradouro: RUA ALA DAS DUNAS y DO
Compl: :GUARAJUBA SHOPPING;LOJA:03;QUADRA:C-4 Bairro: GUARAJUBA (MONTE GORDO) cm
CEP: 42840312 Município: CAMAÇARI
TOMADOR DE SERVIÇOS
Nome/Razão Social: GUARAJUBA MALLS S/A É 035001
CPF/CNPJ: 24.890.395/0001-03 Inscrição Municipal: 0032 or
Logradouro: RODOVIA BA 099 ESTRADA DO COCO :
Compl.: ALAMEDA DAS DUNAS GUARAJUBA SHOPPING  Balrro: GUARAJUBA (MONTE GORDO) dE
CEP: 42840310 Município: CAMAÇARI
DISCRIMINAÇÃO DOS SERVIÇOS
êndico QTD VALOR UNIT (R$) VALOR or Ed
s 2.694,
Er paiol COMBINADOS DE ESCRITÓRIO E APOIO ADMINISTRATIVO 1,0000 12.694,47 1
EMMA ao Dra eat
Berta E . E VS e
Eldasiia XML PDF [agia
Retenções (R$) Totais (R$)
PIS: 0,00 | Valor dos Serviços (R$) 12.694,47
COFINS: 0,00 | Deduções (-) 0,00
INSS: 0,00 |Base de Cálculo (=) 12.694,47
IR: 0,00 |Alíquota (%) 4,82
CSLL: 0,00 | Valor do ISS (R$) 611,87
Outras: 0,00 | Valor Líquido da Nota (=) 12.694,47
Total de Retenções: 0,00
Tipo de tributação: A RECOLHER PELO PRESTADOR Data da prestação do serviço: 16/04/2026
Município da prestação do serviço: 2905701 - CAMACARI
Município da tributação: 2905701 - CAMACARI
CNAE: 8211-3/00 - SERVIÇOS COMBINADOS DE ESCRITÓRIO E APOIO ADMINISTRATIVO
Serviço: 001703 - PLANEJAMENTO, COORDENAÇÃO, PROGRAMAÇÃO OU ORGANIZAÇÃO TÉCNICA, FINANCEIRA OU ADMINISTRATIVA.
CPqD - Gestão Pública ; Data Impressão: 16/04/2026 15:41
"""


@pytest.fixture
def nfse(monkeypatch):
    dummy_path = "tests/dummy_camacari3_nota201.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_TEXT)

    try:
        nfse_list = SPPdfExtractor(dummy_path).parse_multiple()
        assert len(nfse_list) == 1
        yield nfse_list[0]
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_numero_da_nota(nfse):
    assert nfse.numero == "201"


def test_prestador_cnpj_tolera_rotulo_cpficnpj(nfse):
    # "CPFICNPJ" (a "/" lida como "I") não deve mais cair no sentinela.
    assert nfse.prestador.cnpj_cpf == "59132742000113"


def test_prestador_razao_social_corta_rotulo_colado(nfse):
    # "Inscrição Municipal: 0066628001" colado na mesma linha da razão social
    # é removido; a truncagem da própria razão ("ADMINISTRAÇÃO LTDA" ->
    # "ADMINISTRAÇ") é perda de OCR anterior à extração, fora do alcance de
    # um corte por regex — não escondida, só não recuperável aqui.
    assert nfse.prestador.razao_social == "AVANÇO GESTÃO E ADMINISTRAÇ"
    assert "Inscri" not in nfse.prestador.razao_social


def test_valor_dos_servicos_ignora_linha_do_item_partida(nfse):
    # A linha do item foi partida pelo OCR ("...12.694,47 1", só um "1" solto
    # sobra do 2º valor) — sem vírgula, não é confiável; a grade limpa
    # ("Valor dos Serviços (R$) 12.694,47") deve prevalecer.
    val = nfse.valores
    assert val.valor_servicos == pytest.approx(12694.47)
    assert val.base_calculo == pytest.approx(12694.47)
    assert val.valor_iss == pytest.approx(611.87)
    assert val.valor_liquido_nfse == pytest.approx(12694.47)


def test_tomador_permanece_correto(nfse):
    assert nfse.tomador.cnpj_cpf == "24890395000103"
    assert nfse.tomador.razao_social.startswith("GUARAJUBA MALLS S/A")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
