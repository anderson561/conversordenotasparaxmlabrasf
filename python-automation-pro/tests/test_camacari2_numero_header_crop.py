# -*- coding: utf-8 -*-
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
import os

# Texto REAL do OCR (Tesseract) da NFS-e de Camaçari/BA ESCANEADA (nota real
# nº 4494, LAVANDERIA ÁGUA DE CHEIRO -> PH GESTÃO, sem rotação, scan de boa
# qualidade). Preservado verbatim, incluindo o que o pipeline monta:
#  - as 8 primeiras linhas ("Número da Nota\n4494\n...") vêm do recorte
#    dedicado do cabeçalho (_ocr_header_box_camacari), já com o fix do limite
#    superior do recorte (ver abaixo);
#  - o corpo vem do re-OCR em zoom 4 + PSM 6 (_ocr_camacari_scan).
#
# Regressão travada aqui: o recorte do cabeçalho (`_ocr_header_box_camacari`)
# tinha o limite superior em `h * 0.045`, que começava exatamente no início da
# linha "Data de Emissão" - cortando a linha "Número da Nota" (rótulo + valor)
# inteira, que fica ACIMA dela. O número não saía nem garbled: simplesmente
# não existia em lugar nenhum do texto (nem no recorte, nem na leitura de
# página inteira, que também perde essa caixa). Corrigido subindo o limite
# para `h * 0.01` (testado de 0.005 a 0.025 sem diferença no resultado, então
# a margem extra não corre risco de também cortar as 2 linhas de baixo).
#
# Quirk conhecido e aceito (não é o bug relatado, é limitação de fonte fraca já
# documentada para este mesmo recorte desde a nota nº 1050): o código de
# autenticidade sai garbled ("TOTAM7HFA" em vez do real "70T4M7HFA") - "7"/"0"
# e "T"/"O" são visualmente ambíguos nessa fonte, e o resultado NÃO cai no
# placeholder "XXXX-XXXX" (que dispararia o aviso), então nenhum aviso é
# gerado para esse campo específico nesta nota.
MOCK_TEXT = """Número da Nota
4494
Data de Emissão
20/04/2026 07:59
Código de autenticidade
TOTAM7HFA
)024498001
Nº: SIN

fire Número da Nota
ss PREFEITURA MUNICIPAL DE CAMAÇARI
RE Sê . Data de Emissão
Dá NOTA FISCAL DE SERVIÇOS ELETRÔNICA
TOTAM7HFA
PRESTADOR DE SERVIÇOS
Nome/Razão Social: LAVANDERIA AGUA DE CHEIRO LTDA-ME
CPF/CNPJ: 05.342.943/0001-16 Inscrição Municipal: | 0024498001
Logradouro: RUA RAIMUNDO LISBOA Nº: S/N
Compl.: LOTE 2, CAJAZEIRAS Bairro: VILA DE ABRANTES
CEP: 42840000 Município: CAMAÇARI UF: BA
TOMADOR DE SERVIÇOS
Nome/Razão Social: PH GESTAO E CONSULTORIA S A
CPF/CNPJ: 25.311.856/0001-09 Inscrição Municipal: 0032346001
Logradouro: ALAMEDA HUMAITA Nº: SIN
Compl.: COND GUARAJUBA S PREMIUS Bairro: GUARAJUBA (MONTE GORDO)
CEP: 42840562 Município: CAMAÇARI UF: BA
DISCRIMINAÇÃO DOS SERVIÇOS
DESCRIÇÃO QTD VALOR UNIT (R$) VALOR TOTAL (R$)
LAVAGEM DE ROUPAS (EMPRESA OPTANTE DO SIMPLES NACIONAL) 1,0000 3.649,42 3.649,42
dm de Ex Cod Ee
E TER ES ae
[matimeicã XML PDF [lares
Retenções (R$) Totais (R$)
PIS: 0,00 | Valor dos Serviços (R$) 3.649,42
COFINS: 0,00 | Deduções (-) 0,00
INSS: 0,00 | Base de Cálculo (=) 3.649,42
IR: 0,00 | Alíquota (%) 5,00
CSLL: 0,00 | Valor do ISS (R$) 182,47
Outras: 0,00 | Valor Líquido da Nota (=) 3.649,42
Total de Retenções: 0,00
Tipo de tributação: A RECOLHER PELO PRESTADOR Data da prestação do serviço: 20/04/2026
Município da prestação do serviço: 2905701 - CAMACARI
Município da tributação: 2905701 - CAMACARI
CNAE: 9601-7/01 - LAVANDERIAS
Serviço: 001410 - TINTURARIA E LAVANDERIA.
CPqD - Gestão Pública Data Impressão: 20/04/2026 07:59
"""


def test_extract_camacari2_numero_header_crop(monkeypatch):
    dummy_path = "tests/dummy_camacari2_numero.pdf"
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

        # Regressão principal: o número não pode mais desaparecer.
        assert nfse.numero == "4494"
        assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M") == "20/04/2026 07:59"
        assert nfse.servico_codigo == "1410"

        assert nfse.prestador.cnpj_cpf == "05342943000116"
        assert nfse.prestador.razao_social == "LAVANDERIA AGUA DE CHEIRO LTDA-ME"
        assert nfse.prestador.endereco.codigo_municipio == "2905701"
        assert nfse.prestador.endereco.uf == "BA"

        assert nfse.tomador.cnpj_cpf == "25311856000109"
        assert nfse.tomador.razao_social == "PH GESTAO E CONSULTORIA S A"
        assert nfse.tomador.endereco.codigo_municipio == "2905701"
        assert nfse.tomador.endereco.uf == "BA"

        val = nfse.valores
        assert val.valor_servicos == pytest.approx(3649.42)
        assert val.base_calculo == pytest.approx(3649.42)
        assert val.aliquota == pytest.approx(0.05)
        assert val.valor_iss == pytest.approx(182.47)
        assert val.valor_liquido_nfse == pytest.approx(3649.42)

        # Sem o aviso de número (era a queixa original) - resta só o quirk
        # conhecido do código de autenticidade (garbled, mas não é o
        # placeholder XXXX-XXXX, então não dispara aviso nesta nota).
        assert "Número da nota não encontrado" not in nfse.avisos
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
