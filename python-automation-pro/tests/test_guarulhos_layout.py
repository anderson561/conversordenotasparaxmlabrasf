# -*- coding: utf-8 -*-
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
import os

# Texto REAL do OCR (Tesseract) da NFS-e escaneada de Guarulhos/SP (plataforma
# Ginfes, guarulhos.ginfes.com.br), nota real nº 3, KICHLER INDUSTRIA COMERCIO
# E INSTALACAO DE ESQUADRIA DE ALUMINIO LTDA -> SÃO PEDRO CONSTRUTORA, R$
# 4.511,41 (obra Sede de Tecnologia MTI - SECITECI, em Cuiabá/MT). Preservado
# verbatim, incluindo:
#  - o bloco canônico recuperado pelos recortes dedicados (_ocr_recut_guarulhos)
#    e prependido ao texto -- a leitura de página inteira perde o Código de
#    Verificação, o Local da Prestação e a grade "Cálculo do ISSQN devido no
#    Município" por completo;
#  - os rótulos de campo corrompidos pelo OCR na leitura de página inteira
#    ("Razão. Se aNo" em vez de "Razão Social/Nome", "Municípic" em vez de
#    "Município", "ND:"/"NO DA OBRA:" com a 1ª letra comida de "END:"/"CNO DA
#    OBRA:");
#  - a assinatura do engenheiro responsável ("Thiago Gued", "Eng. Civil",
#    "CREA-BA...") colada entre a discriminação e o código de serviço;
#  - a grade de valores praticamente ilegível na leitura de página inteira
#    (células cinza densas) -- por isso os valores REAIS vêm só do bloco
#    canônico, não desta parte do texto.
# O mock alimenta o texto via extract_text (pdfminer), reproduzindo o que o
# _ocr_page produziria, sem depender do Tesseract no CI (mesma convenção dos
# testes do Iaçu/Brotas de Macaúbas).
MOCK_TEXT = (
    "Número da nota: 3\n"
    "Data e Hora da Emissão: 18/06/2026 17:17:00\n"
    "Código de Verificação: 4J6UQZOW7\n"
    "Local da Prestação: CUIABA - MT\n"
    "Natureza Operação: Tributação fora do município\n"
    "ISS a reter: Não\n"
    "Valor dos Serviços: 4.511,41\n"
    "Base de Cálculo: 4.511,41\n"
    "Alíquota: 4,00\n"
    "Valor do ISS: 0,00\n"
    "Valor Líquido: 4.511,41\n"
    "PREFEITURA MUNICIPAL DE GUARULHOS Número da | ElsZE]\n"
    "SECRETARIA DE FINANÇAS NFS-e e\n"
    "NOTA FISCAL ELETRÔNICA DE SERVIÇO - NFS-e 3 DSTs\n"
    "no es \"à\n"
    "Data e Hora da Emissão | 18/06/2026 17:17:00 ompetência | 18/6/2026 a Nois asicação| E 4JGUQZOWT\n"
    "E Razão. Se aNo KICHLER INDUSTRIA COMERCIO E INSTALACAO DE ESQUADRIA DE ALUMINIO LTDA\n"
    "CNPJICPF| 66.986.458/0001-70 ição Mun 776221 | Municípic GUARULHOS - SP\n"
    "E: no De Cep | RUA MINEIRA +320 - VILA ESPLANADA CEP: 07043-120\n"
    "| FUNDOS» | 1945263628 ekichlerQOkichier.com.br\n"
    "| Razão SociallNome | SÃO PEDRO CONSTRUTORA\n"
    "FONPJICPR| 03051:741/0001-90  [inseriçioMunicipal) | LAURO DE FREITAS - BA\n"
    "E . Q 8 CER | AVENIDA Praia de Pajussara ,554 - Vilas do Atlântico CEP: 42708-720\n"
    "REF: 60% - SERVIÇO DE MÃO DE OBRA\n"
    "OBRA: Sede de Tecnologia MTI - SECITECI\n"
    "ND: RUA UM, S/N QUADRA 28 LOTE 09 - CENTRO POLITICO ADMINISTRATIVO CEP:42.708-720 CUIABA/MT Á\n"
    "tt lo es\n"
    "NO DA OBRA:90.018.32011/78 Thiago Gued\n"
    "Eng. Civil\n"
    "CREA-BA 052233594-2\n"
    "7.02 / 439910100 - Administração de obras\n"
    "E \"5884 Código da Ob 1912973 ódigo À 1912973\n"
    "(3 Desconto Incond clonado rurais 2-Tributação fora do município [N BESUSSES pemmindas em E A\n"
    "o Sears [om | onentum — Posodecálado EEN |\n"
    "= % y past nes ed Se «o un e ; E\n"
    "oces [E RE TO EEE\n"
    "1- Uma via desta Nota Fiscal será enviada através do e-mail fomecido pelo Tomador dos Serviços. '\n"
    "- A autenticidade desta Nota Fiscal poderá ser verificada no site, guarulhos.ginfes.com.br com a utilização do Código de Verificação.\n"
    "Avisos PP - Documento emitido por ME ou EPP optante pelo Simples Nacional.Não gera direito a crédito fiscal de ISS e IRI. A\n"
    "Scanned with\n"
    "CamScanner\n"
)


def test_extract_guarulhos_layout(monkeypatch):
    dummy_path = "tests/dummy_guarulhos.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        extractor.raw_text = MOCK_TEXT
        extractor.layout = extractor._detect_layout()

        assert extractor.layout == "guarulhos_sp"

        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        # Cabeçalho recuperado do bloco canônico (não fica legível na leitura
        # de página inteira): número, código de verificação e data.
        assert nfse.numero == "3"
        assert nfse.codigo_verificacao == "4J6UQZOW7"
        assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "18/06/2026 17:17:00"
        assert nfse.competencia.strftime("%m/%Y") == "06/2026"

        # Código de serviço: "7.02 / 439910100 - Administração de obras" —
        # vem explícito na nota, sem ambiguidade de mapeamento (diferente de
        # Brotas de Macaúbas).
        assert nfse.servico_codigo == "0702"

        # Prestador KICHLER (Guarulhos/SP) — rótulos de campo corrompidos no
        # OCR ("Razão. Se aNo", "Municípic") não podem vazar para os valores.
        prest = nfse.prestador
        assert prest.cnpj_cpf == "66986458000170"
        assert prest.razao_social == "KICHLER INDUSTRIA COMERCIO E INSTALACAO DE ESQUADRIA DE ALUMINIO LTDA"
        assert prest.inscricao_municipal == "776221"
        assert prest.endereco.logradouro == "RUA MINEIRA"
        assert prest.endereco.numero == "320"
        assert prest.endereco.bairro == "VILA ESPLANADA"
        assert prest.endereco.municipio == "GUARULHOS"
        assert prest.endereco.codigo_municipio == "3518800"
        assert prest.endereco.uf == "SP"
        assert prest.endereco.cep == "07043120"

        # Tomador SÃO PEDRO CONSTRUTORA (Lauro de Freitas/BA) — sem rótulo
        # "Município" explícito no bloco (célula de Inscrição Municipal
        # vazia), só o padrão "CIDADE - UF" solto.
        tom = nfse.tomador
        assert tom.cnpj_cpf == "03051741000190"
        assert tom.razao_social == "SÃO PEDRO CONSTRUTORA"
        assert tom.endereco.logradouro == "AVENIDA Praia de Pajussara"
        assert tom.endereco.numero == "554"
        assert tom.endereco.bairro == "Vilas do Atlântico"
        assert tom.endereco.municipio == "LAURO DE FREITAS"
        assert tom.endereco.codigo_municipio == "2919207"
        assert tom.endereco.uf == "BA"
        assert tom.endereco.cep == "42708720"

        # Grade "Cálculo do ISSQN devido no Município": ISS NÃO retido nem
        # devido em Guarulhos (Simples Nacional + serviço tributado fora do
        # município).
        val = nfse.valores
        assert val.valor_servicos == pytest.approx(4511.41)
        assert val.base_calculo == pytest.approx(4511.41)
        assert val.aliquota == pytest.approx(0.04)
        assert val.valor_iss == pytest.approx(0.0)
        assert val.valor_liquido_nfse == pytest.approx(4511.41)
        assert val.iss_retido is False

        # Decisão do usuário: serviço de construção civil (item 7.02)
        # prestado em OUTRO município (Cuiabá/MT, "Local da Prestação" +
        # "Tributação fora do município") -- a incidência do ISSQN deve ir
        # para o município da obra, não para o do prestador (Guarulhos).
        assert nfse.municipio_incidencia_override == "5103403"

        # Discriminação não pode incluir a assinatura do engenheiro
        # responsável ("Thiago Gued", "Eng. Civil", "CREA-BA...").
        assert "REF: 60% - SERVIÇO DE MÃO DE OBRA" in nfse.discriminacao
        assert "OBRA: Sede de Tecnologia MTI - SECITECI" in nfse.discriminacao
        assert "Thiago" not in nfse.discriminacao
        assert "CREA" not in nfse.discriminacao

        assert nfse.avisos == []
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__])
