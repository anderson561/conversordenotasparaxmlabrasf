import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
import os

# Texto real capturado via OCR (Tesseract, zoom 3x) de uma NFS-e real emitida
# via eNotas Gateway pelo prestador TÉSSERA HOSPITALITY LTDA, de Lauro de
# Freitas/BA — pág. 4 do lote "Notas Fiscais Recebidas 07.2026 - Guarajuba
# Suítes" (Numero 202600000001829, RPS 988 Série 01). É a 1ª nota ESCANEADA
# desta plataforma (PASSWORD e INFOMIX, já validadas em
# test_password_enotas_layout.py, são digitais/pdfminer): o scan funde a
# grade "DADOS DO TOMADOR" numa única linha por rótulo, degrada a coluna
# direita do cabeçalho (Número/Competência/Código/Data se sobrepõem ao
# endereço do prestador) e perde o rótulo "(=) BASE DE CÁLCULO" por completo
# na grade de valores pareados. Este texto já reflete a saída de `_ocr_page`
# APÓS o recorte de cabeçalho (28%/zoom8/PSM automático) ser prependado com
# a etiqueta "DADOS DO TOMADOR" removida (ver comentário em `_ocr_page`) —
# preserva os 2 blocos "TESSERA HOSPITALITY LTDA" (um limpo, do recorte; um
# fundido ao rótulo "NÚMERO DA NOTA", da leitura padrão) para travar
# regressão na prioridade de sufixo social sobre a heurística posicional.
MOCK_TEXT_TESSERA_PAGINA4 = """NFS-e - NOTA FISCAL DE SERVIÇOS ELETRÔNICA - RPS 988 Série 01, emitido em: 01/07/2026

HOSPITALITY



TESSERA HOSPITALITY LTDA
SANTOS DUMONT, 1883 SALA 507 ESP AERO EMP KM 15
CENTRO - Lauro de Freitas - BA - 42702400
TELEFONE: 7193120017
EMAIL: FRANKLINQTESSERAHOSPITALITY.COM.BR
CNPJ: 03.814.827/0001-27
INSCRIÇÃO MUNICIPAL: 0010034437011

TE MOCIMMCAMMECTERIOECER CA Ca nETtTrEREaAAroso era rererererenreeeerreoroeereeroneneereusemener aee ac acsrsrere cores resessecesoverevesareneeacesesereverererereeror

|
|
|
|

emeeeeererorerermermerrecees TOTO tree renomear rrererrrremmmerrovermeniororenscers veres peisicorcmemepuoreresecniniyeverirvescorstetererorerevovevesorrervereceseseereeerererveresvereremeeneees ereeeesenereasene

| NOME / RAZÃO SOCIAL

NÚMERO DA NOTA
202600000001829
COMPETÊNCIA

07/2026

CÓDIGO DE VERIFICAÇÃO
04F8C91BB
DATA DE EMISSÃO
01/07/2026 10:49:59

Were nene erre r em cereeecererereeremrra ren renececsreneererererereeniscreseesorrerenas

|
| TELEEONE

NFS-e - NOTA FISCAL DE SERVIÇOS ELETRÔNICA - RPS 988 Série 01, emitido em: 01/07/2026

TESSERA HOSPITALITY LTDA NÚMERO DA NOTA
SANTOS DUMONT, 1883 SALA 507 ESP AERO EMPKM 15 202600000001829
CENTRO - Lauro de Freitas - BA - 42702400 COMPETÊNCIA
07/2026

HOSPITALITY EMAIL: FRANKLINOTESSERAHOSPITALITY.COM.BR | VER NESSA

DATA DE EMISSÃO
9107/2026 10:49:59

CNPJ: 03.814.827/0001-27
INSCRIÇÃO MUNICIPAL: 001 O0s44s7011

|
|
|
"TESSERA | TELEFONE: 7193120017
|

DADOS DO TOMADOR

E-MAIL
PRISCILAQGUARAJUBANEGOCIOS.COM.B
R

' NOME / RAZÃO SOCIAL

1
| TELEFONE
LPH GESTAO E CONSULTORIA S.A. |

7400

|
|
|
-|
i

| ENDEREÇO BAIRRO / DISTRITO
+ HUMAITA, S/N COND GUARAJUBA S PREMIUS "GUARAJUBA (MONTE G

| MUNICÍPIO (UF | PAÍS CPF /CNPJ/ OUTROS INSCRIÇÃO MUNICIPAL | INSCRIÇÃO ESTADUAL
| Camaçari LBA (Brasi | 25311 856/0001-09 |

PRESTACAO DE SERVICO CONFORME CONTRATO.

CÓDIGO DO SERVIÇO

17.02 / 1702 - Datilografia, digitação, estenografia, expediente, secretaria em geral, resposta audível, redação, edição, interpretação, revisão, tradução, apoio e
infra-estrutura administrativa e congêneres.

MUNICÍPIO ONDE O SERVIÇO FOI PRESTADO NATUREZA DA OPERAÇÃO
- 2919207 / Lauro de Freitas E meta . Tributação no municipio

VALOR DOS SERVIÇOS: R$ 2964,77

E ) DESCONTOS: % R$ 0,00 R$ 0,00
RETENÇÕES FEDERAIS: R$ 0,00 R$ 2964,77

(-) ISS RETIDO NA FONTE: R$ 0,00 (x) ALÍQUOTA: 3,00 %

VALOR LÍQUIDO: R$ 2964,77 (=) VALOR DO ISS: -

OUTRAS INFORMAÇÕES

Documento emitido por ME ou EPP optante pelo simples nacional;
Trib aprox R$: 398,76 Federal, R$: 0,00 Estadual e R$: 148,24 Municipal Fonte: IBPT/empresometro.com.br 92589A
"""

# Recorte dedicado do bloco "DADOS DO TOMADOR" (zoom 8x, PSM 6, região
# localizada dinamicamente entre os rótulos "TOMADOR" e "PRESTACAO" — ver
# `_ocr_recut_tomador_password_enotas`), capturado real contra a mesma nota.
# Guardado por página em `_password_enotas_tomador_recut_por_pagina` (ver
# `_ocr_page`), NUNCA prependado ao texto principal.
MOCK_TOMADOR_RECUT_TESSERA = (
    "monto DO IOMADOR Di a Us\n\n\n"
    "| NOME / RAZÃO SOCIAL | EA, | | TELEFONE\n\n"
    "J E COMB |\n\n"
    "' PH GESTAO E CONSULTORIA S.A. | PRISCILAGGUARAJUBANEGOCIOS.COM '* 7132487400\n\n"
    "a Dee dd R a aa DE SEP RA SOSDSE ESO e PEER\n\n"
    "| ENDEREÇO | BAIRRO / DISTRITO | CEP\n\n"
    "-MHUMAITA, SIN COND GUARAJUBA SPREMIUS| GUARAJUBA (MONTE GORDO) | 42840562\n\n"
    "' MUNICÍPIO | UF | PAÍS | CPF / CNPJ / OUTROS INSCRIÇÃO MUNICIPAL | INSCRIÇÃO ESTADUAL\n\n"
    ": : i !\n\n"
    "Camaçari o BA Brasil | | 25.311.856/0001.09 PE DR\n\n"
    "East oa cAc 1224/05\n"
)

MOCK_IM_RECUT_TESSERA = "0010034437011"

# Página vizinha, sem rótulo nenhum desta plataforma — usada só para provar
# que os recortes acima ficam guardados POR PÁGINA (dicionário indexado por
# `page_num`) e sobrevivem ao processamento de páginas seguintes no mesmo
# lote. Antes do fix, eram atributos escalares resetados no INÍCIO de toda
# chamada a `_ocr_page`; ao rodar `_ocr_page` para esta 2ª página, o valor da
# pág.4 (TÉSSERA) era apagado antes de `parse_multiple()` conseguir
# propagá-lo para o `sub_ext` que de fato monta a Entidade (achado real: o
# lote tem 33 páginas, e a página TÉSSERA nunca era a última processada).
PAGINA_VIZINHA_IRRELEVANTE = "PAGINA SEM NENHUM PADRAO DE LAYOUT CONHECIDO NESTE LOTE.\n" * 5


def test_extract_password_enotas_tessera_hospitality_scan(monkeypatch):
    """1ª nota ESCANEADA da plataforma PASSWORD/eNotas Gateway (emitente
    TÉSSERA HOSPITALITY LTDA). Trava as 3 classes de regressão descobertas
    ao corrigi-la:
    1. Bloco do PRESTADOR não fica truncado pela etiqueta "DADOS DO TOMADOR"
       espúria do recorte de cabeçalho (fora de ordem física, PSM automático).
    2. Razão social do prestador prioriza a linha com sufixo social (LTDA/
       S.A./...) sobre a heurística posicional "linha após 'emitido em'",
       que aqui cai num fragmento solto ("HOSPITALITY").
    3. Os recortes de tomador/IM são propagados POR PÁGINA do extrator
       "pai" (que roda o OCR) para o `sub_ext` que de fato monta a
       Entidade em `parse_multiple()` — sem isso, ficam sempre None.
    4. CNPJ tolera separador "." no lugar do "-" final; Base de Cálculo é
       reconstituída (Serviços - Deduções) quando a fusão de coluna do OCR
       elimina o rótulo por completo.
    """
    dummy_path = "tests/dummy_tessera_hospitality.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    # Sem texto embutido (pdfminer) -> força o fallback de OCR, exatamente
    # como o PDF real (escaneado) do lote Guarajuba Suítes.
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")

    def fake_extract_via_ocr(self):
        self.from_ocr = True
        # Efeito colateral real de `_ocr_page` para a página 0 (TÉSSERA):
        # guarda os recortes dedicados POR PÁGINA antes de devolver o texto.
        self._password_enotas_prestador_im_recut_por_pagina[0] = MOCK_IM_RECUT_TESSERA
        self._password_enotas_tomador_recut_por_pagina[0] = MOCK_TOMADOR_RECUT_TESSERA
        return "\n\x0c\n".join([MOCK_TEXT_TESSERA_PAGINA4, PAGINA_VIZINHA_IRRELEVANTE])

    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", fake_extract_via_ocr)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        assert nfse.numero == "202600000001829"
        assert nfse.codigo_verificacao == "04F8C91BB"
        assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "01/07/2026 10:49:59"
        assert nfse.competencia.strftime("%m/%Y") == "07/2026"
        assert nfse.optante_simples_nacional is True

        prest = nfse.prestador
        assert prest.cnpj_cpf == "03814827000127"
        assert prest.inscricao_municipal == "0010034437011"
        assert prest.razao_social == "TESSERA HOSPITALITY LTDA"
        assert prest.endereco.logradouro == "SANTOS DUMONT"
        assert prest.endereco.numero == "1883"
        assert prest.endereco.complemento == "SALA 507 ESP AERO EMP KM 15"
        assert prest.endereco.bairro == "CENTRO"
        assert prest.endereco.municipio == "Lauro de Freitas"
        assert prest.endereco.codigo_municipio == "2919207"
        assert prest.endereco.uf == "BA"
        assert prest.endereco.cep == "42702400"
        assert prest.telefone == "7193120017"

        tom = nfse.tomador
        assert tom.cnpj_cpf == "25311856000109"
        assert tom.razao_social == "PH GESTAO E CONSULTORIA S.A."
        assert tom.endereco.bairro == "GUARAJUBA (MONTE GORDO)"
        assert tom.endereco.cep == "42840562"
        assert tom.endereco.uf == "BA"

        val = nfse.valores
        assert val.valor_servicos == pytest.approx(2964.77)
        assert val.valor_deducoes == pytest.approx(0.0)
        # "(=) BASE DE CÁLCULO" perde o rótulo por completo na fusão de
        # coluna do OCR -- reconstituída como Serviços - Deduções.
        assert val.base_calculo == pytest.approx(2964.77)
        assert val.aliquota == pytest.approx(0.03)
        assert val.valor_liquido_nfse == pytest.approx(2964.77)
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__])
