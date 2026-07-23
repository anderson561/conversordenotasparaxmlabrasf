import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
import os

# Texto REAL do OCR (Tesseract) da NFS-e escaneada de Iaçu/BA emitida pela
# plataforma nfservico.com.br (nota real nº 2, N'S ASSUNÇÃO -> SINAL
# CONSTRUTORA). Preservado verbatim, incluindo:
#  - o cabeçalho recuperado pelo recorte dedicado (_ocr_header_box_iacu),
#    prependido ao texto ("Número da nota: 2", "c5cae3fd79" + ruído do QR
#    "o / ES OPOE");
#  - o ruído do carimbo de recebimento no bloco do tomador ("45840 e BUT",
#    "Es E eero Noreita", "Carlos Alberto ias", "Encarregado de Almoxarita");
#  - a URL da plataforma mangled pelo OCR ("nfservico.com.briiacu").
# O mock alimenta o texto via extract_text (pdfminer), reproduzindo o que o
# _ocr_page produziria, sem depender do Tesseract no CI.
MOCK_TEXT = """Número da nota:

2

Data e hora de Emissão:

10/07/2026 16:37:22

Código de Verificação:

c5cae3fd79

o
ES OPOE

PREFEITURA MUNICIPAL DE IAÇU - BA Ra

RUA JUSTINIANO DE MOURA MEDRADO, SN - CENTRO Data é liora de Emissão:
CNPJ: 13889993000146 | e-mail:luciano, IslimaQhotmail.com TEL:7599200007 10/07/2026 16:37:22

Código de Verificação:

NOTA FISCAL DE SERVIÇOS ELETRÔNICA

PRESTADOR DE SERVIÇOS

CPF/CNPJ: Inscrição Municipal:

54982133000130

Nome/Razão Social:

N'S ASSUNÇÃO CONSTRUTORA LTDA

Endereço:

RUA JUVENTINO MEDRADO 94, - BOIADEIRA - CEP: 46860000 - IACU - BA
E-mail:

natanael.carregadeira(dgmail.com

TOMADOR DE SERVIÇOS

Nome/Razão Social:

SINAL CONSTRUTORA

CPF/CNPJ: Inscrição Municipal:

33811381000148 45840 e BUT
Endereço: E eero Noreita
RUA EVANGELINA SIQUEIRA DIAS 9995, - NOVA POJUCA - CEP: 48120000 - POJUCA - BA Carlos Alberto ias
E-mail: Encarregado de Almoxarita
sinalQ)sinalconstrutora.com

DISCRIMINAÇÃO DOS SERVIÇOS
PRESTAÇÃO DE SERVIÇOS REFERENTE A APOIO, PRODUÇÃO E DRENAGEM PROFUNDA 18
LAJEDINHO

LOCAL DE PRESTAÇÃO DOS SERVIÇOS
IACU - BA

VALOR TOTAL DA NOTA = R$119.399,37

CNAE:

4120400 - Construção de edifícios

Item da lista de serviços:

7.02 - Execução, por administração, empreitada ou subempreitada, de obras de construção civil, hidráulica ou elétrica e de
outras obras semelhantes, inclusive sondagem, perfuração de poços, escavação, drenagem e irrigação, terraplanagem,

pavimentação, concretagem e a instalação e montagem de produtos, peças e equipamentos (exceto o fornecimento de
mercadorias produzidas pelo prestador de serviços fora do local da prestação dos serviços, que fica sujeito ao ICMS)

Valor total das deduções (R$): Base de cálculo (R$): Aliquota (%): Valor do ISS (R$): Crédito (R$):
0,00 119.399,37 3,00 3.581,98 0,00

OUTRAS INFORMAÇÕES

Valor INSS (R$): Valor PIS (R$): Valor COFINS (R$): Valor IR (R$): Valor CSLL (R$): Outras rentenções (R$):
0,00 0,00 0,00 0,00 0,00 0,00

- Documento emitido por ME, MEI ou EPP, optante pelo Simples Nacional

Valor líquido (R$):
119.399,37

- COMPETÊNCIA: 07/2026 (mês/ano)
- Para consultar a autenticidade desse Documento Fiscal acesse: https:/lwww.nfservico.com.briiacu
"""


def test_extract_iacu_nfse_layout(monkeypatch):
    dummy_path = "tests/dummy_iacu_nfse.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        extractor.raw_text = MOCK_TEXT
        extractor.layout = extractor._detect_layout()

        assert extractor.layout == 'iacu_nfse'

        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        # Cabeçalho recuperado do recorte dedicado (não fica legível na página
        # inteira): número, código de verificação e data/hora.
        assert nfse.numero == "2"
        assert nfse.codigo_verificacao == "c5cae3fd79"
        assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "10/07/2026 16:37:22"
        assert nfse.competencia.strftime("%m/%Y") == "07/2026"
        # Item LC116 7.02 normalizado para 4 dígitos.
        assert nfse.servico_codigo == "0702"

        # Prestador N'S ASSUNÇÃO (Iaçu/BA) — não pode cair no fallback da capital
        # (Salvador). Endereço parseado da linha única do layout.
        prest = nfse.prestador
        assert prest.cnpj_cpf == "54982133000130"
        assert prest.razao_social == "N'S ASSUNÇÃO CONSTRUTORA LTDA"
        assert prest.endereco.logradouro == "RUA JUVENTINO MEDRADO"
        assert prest.endereco.numero == "94"
        assert prest.endereco.bairro == "BOIADEIRA"
        assert prest.endereco.municipio == "IACU"
        assert prest.endereco.codigo_municipio == "2912707"
        assert prest.endereco.uf == "BA"
        assert prest.endereco.cep == "46860000"

        # Tomador SINAL CONSTRUTORA (Pojuca/BA) — mesmo tomador da nota ARMAC.
        # O bloco vem contaminado com o carimbo de recebimento; o CNPJ correto é
        # o primeiro de 14 dígitos, não o "45840" do carimbo.
        tom = nfse.tomador
        assert tom.cnpj_cpf == "33811381000148"
        assert tom.razao_social == "SINAL CONSTRUTORA"
        assert tom.endereco.logradouro == "RUA EVANGELINA SIQUEIRA DIAS"
        assert tom.endereco.numero == "9995"
        assert tom.endereco.bairro == "NOVA POJUCA"
        assert tom.endereco.municipio == "POJUCA"
        assert tom.endereco.codigo_municipio == "2925303"
        assert tom.endereco.uf == "BA"
        assert tom.endereco.cep == "48120000"

        # NFS-e tributada (construção civil): ISS real de 3% sobre a base.
        val = nfse.valores
        assert val.valor_servicos == pytest.approx(119399.37)
        assert val.base_calculo == pytest.approx(119399.37)
        assert val.aliquota == pytest.approx(0.03)
        assert val.valor_iss == pytest.approx(3581.98)
        assert val.valor_liquido_nfse == pytest.approx(119399.37)
        assert val.iss_retido is False

        # Simples Nacional (ME/MEI/EPP) reconhecido mesmo com "optante pelo".
        assert nfse.optante_simples_nacional is True
        assert nfse.regime_especial_tributacao == "6"

        assert "DRENAGEM PROFUNDA" in nfse.discriminacao
        assert "LOCAL DE PRESTAÇÃO" not in nfse.discriminacao

        assert nfse.avisos == []
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__])
