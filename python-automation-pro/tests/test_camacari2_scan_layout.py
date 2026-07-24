import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_CAMACARI, LAYOUT_CAMACARI_2
import os

# Texto REAL do OCR (Tesseract) da NFS-e de Camaçari/BA ESCANEADA (foto/JPG
# convertida em PDF e rotacionada 180° — nota real nº 1050, PEREIRA SANTOS ->
# AMANE AGUIAR). Preservado verbatim, incluindo o que o pipeline monta:
#  - as 5 primeiras linhas ("Número da Nota\n1050\nData de Emissão...\nCódigo
#    de autenticidade") vêm do recorte dedicado do cabeçalho
#    (_ocr_header_box_camacari); na página inteira essa caixa some;
#  - o corpo vem do re-OCR em zoom 4 + PSM 6 (_ocr_camacari_scan); na leitura
#    padrão (zoom 3) a metade inferior inteira (grade de totais) é descartada.
# Quirks deliberadamente preservados para travar as regressões:
#  - o CNPJ do TOMADOR sai com o 1º dígito trocado ("49..." em vez de "19...");
#  - o MUNICÍPIO do PRESTADOR some ("CEP: MUNICÍPIO: .");
#  - a grade lê a Alíquota e o ISS TROCADOS ("Aliquota (%) 35,75" / "ISS 6,5%"),
#    quando o real é alíquota 6,5% e ISS 35,75;
#  - o código de autenticidade é impresso em fonte fraca e sai ilegível.
MOCK_TEXT = """Número da Nota
1050
Data de Emissão : |
— 28/05/2026 16:22
Código de autenticidade

| = & PREFEITURA MUNICIPAL DE CAMAÇARI E da Nota
El 1050
| EEE Código de rn rt
| NOTA FISCAL DE SERVI ELETRÔNICA |
| PRESTADORDE SERVIÇOS |
Nome/Razão Social: PEREIRA SANTOS DESINSETIZACAO E SERVICOS LTDA
| CPF/CNPJ: 05.457.337/0001-46 Inscrição Municipal: 0031077001
| Logradouro:  MIRAMAR SANTIAGO Nº: SN
Compl: LOTE 24 QUADRA 15 Barro: JARDIM LIMOBRO
CEP: MUNICÍPIO: .
| TOMADOR DE SERVIÇOS
| Nome/Razão Social: AMANE AGUIAR DIAS DE AZEVEDO
CPF/CNPJ: 49.477.725/0001-01 inscrição Municipal:
| Logradouro:BOTO ROSA N: |
Compl.: CASA 42 C CONDOMINIO BUSCA VIDA Beira: FANTES
CEP:42.800-970 MUNICÍPIO: LAURO DE FREITAS EaMiisia UF: BAHIA
DISCRIMINAÇÃO DOS SERVIÇOS |
. STD VALOR UNIT (RSj VALOR TOTAL (R$)
ESCaurCiio 1,0090 550,00 550,00
ERVIÇO DE DESINSETIZAÇÃO PARA TRAÇAS 2,0000 0,00 0,00
PTANTE PELO SIMPLES NACIONAL
Retenções (R$) Totais (R$)
PIS: 0,00 Nalor dos Serviços (R$) 550,00
COFINS: 0,00 [Deduções () 0,00
NSS: 0,00 Basa de Cálculo (=) 550,00
R: 0,00 iAliquota (%) 35,75
CSLL 0,00 Nalor do ISS (R$) 6,5%
Dutras 0,00 Nalor Líquido da Nota (=) 550,00
otal de Retenções: 0,00
AMACARI CNAE: 8122-2/00 - IMUNIZAÇÃO E CONTROLE PRAGAS URBANAS . E E
Serviço: 000713 - DEDETIZAÇÃO, DESINFECÇÃO, DESINSETIZAÇÃO, IMUNIZAÇÃO, HIGIENIZAÇÃO, DESRATIZAÇÃO, PULVERIZAÇÃO E
ONGÊNERES.
Data da prestação do serviço: 28/05/2026
"""


def test_camacari_digital_nao_vira_camacari2():
    """Blindagem: o Camaçari DIGITAL (texto embutido, from_ocr=False) continua
    sendo detectado como LAYOUT_CAMACARI. O LAYOUT_CAMACARI_2 é um superset
    roteado APENAS quando o texto veio de OCR — o digital não pode regredir.
    Os testes existentes de Camaçari (CETREL/511541) setam raw_text sem
    from_ocr, então permanecem em LAYOUT_CAMACARI por este mesmo gate."""
    dummy_path = "tests/dummy_camacari_digital.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = "PREFEITURA MUNICIPAL DE CAMAÇARI\nData da prestação do serviço: 28/05/2026"
    extractor.from_ocr = False  # texto embutido (pdfminer), não OCR

    assert extractor._detect_layout() == LAYOUT_CAMACARI

    if os.path.exists(dummy_path):
        os.remove(dummy_path)


def test_extract_camacari2_scan_layout(monkeypatch):
    dummy_path = "tests/dummy_camacari2.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    # extract_text vazio força o caminho de OCR do parse_multiple, que seta
    # self.from_ocr=True; _extract_via_ocr devolve o texto canônico capturado.
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        # Número (1050) e data/hora de emissão vêm do recorte dedicado do
        # cabeçalho — na página inteira essa caixa some.
        assert nfse.numero == "1050"
        assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M") == "28/05/2026 16:22"
        assert nfse.competencia.strftime("%m/%Y") == "05/2026"
        # Item de serviço 000713 (07.13) -> 0713.
        assert nfse.servico_codigo == "0713"

        # Prestador em Camaçari/BA (município some no OCR -> default Camaçari).
        assert nfse.prestador.cnpj_cpf == "05457337000146"
        assert nfse.prestador.razao_social == "PEREIRA SANTOS DESINSETIZACAO E SERVICOS LTDA"
        assert nfse.prestador.inscricao_municipal == "0031077001"
        assert nfse.prestador.endereco.codigo_municipio == "2905701"
        assert nfse.prestador.endereco.uf == "BA"

        # Tomador em Lauro de Freitas/BA; CNPJ com 1º dígito corrigido
        # (OCR "49.477.725..." -> real "19.477.725...", via validação do DV).
        assert nfse.tomador.cnpj_cpf == "19477725000101"
        assert nfse.tomador.razao_social == "AMANE AGUIAR DIAS DE AZEVEDO"
        assert nfse.tomador.endereco.codigo_municipio == "2919207"
        assert nfse.tomador.endereco.uf == "BA"

        # NFS-e tributada: ISS real de 6,5% = 35,75 sobre a base de 550,00 — NÃO
        # os valores trocados de linha que o OCR imprime ("Aliquota 35,75",
        # "ISS 6,5%"). O ISS é derivado de base × alíquota (imune à troca).
        val = nfse.valores
        assert val.valor_servicos == pytest.approx(550.00)
        assert val.base_calculo == pytest.approx(550.00)
        assert val.aliquota == pytest.approx(0.065)
        assert val.valor_iss == pytest.approx(35.75)
        assert val.valor_liquido_nfse == pytest.approx(550.00)

        # Discriminação: texto do serviço em caixa alta (o 1º caractere de cada
        # linha foi comido pela borda da grade: "SERVIÇO"->"ERVIÇO",
        # "OPTANTE"->"PTANTE"); o rótulo "DESCRIÇÃO" corrompido é filtrado.
        assert nfse.discriminacao == "ERVIÇO DE DESINSETIZAÇÃO PARA TRAÇAS PTANTE PELO SIMPLES NACIONAL"

        # Único aviso legítimo: o código de autenticidade é impresso em fonte
        # fraca e sai ilegível no OCR (não fabricamos um valor errado).
        assert nfse.avisos == ["Código de verificação/autenticidade não encontrado"]
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
