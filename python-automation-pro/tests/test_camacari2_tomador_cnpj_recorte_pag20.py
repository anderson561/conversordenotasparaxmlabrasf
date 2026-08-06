# -*- coding: utf-8 -*-
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
import os

# Texto REAL do OCR (best_text, apos os recuts padrao de Camacari: header
# box + body scan) da pagina 20 do PDF
# "Notas_Fiscais_Recebidas_06.2026_-_Guarajuba_Suites.pdf": NFS-e ESCANEADA
# de Camacari/BA (layout camacari_ba_scan), L DE J NASCIMENTO TRANSPORTE ->
# PH Gestao, nota no 962, retirada de poda, R$ 600,00. Bug real: no scan
# original, o campo CPF/CNPJ do TOMADOR esta cobertO por um marca-texto
# amarelo com um rabisco a caneta por cima, que zera o OCR so nessa celula
# (o resto da pagina le normalmente, inclusive o CNPJ do PRESTADOR) -> o
# rotulo "CPF/CNPJ:" do bloco tomador sai SEM valor (linha 32: "CPF/CNPJ:
# Inscricao Municipal: 0032346001"), caindo no sentinela "00000000000000".
MOCK_TEXT = 'Número da Nota\n962\nData de Emissão\n16/06/2026 10:32\nCódigo de autenticidade\n3E0B597Z8\n27165001\nNº: 10BC\n\nero da Nota\n962\nde Emissão\n16/06/2026 10:32\ngo de autenticidade\n3E0B597Z8\nNº: 10BC\nUF: BA\n\npd PREFEITURA MUNICIPAL DE CAMAÇARI 962\nie . Data de Emissão\nNi] Secretaria da Fazenda\nENO NOTA FISCAL DE SERVIÇOS ELETRÔNICA\nSado 3E0B59728\nPRESTADOR DE SERVIÇOS\nNome/Razão Social: L DE J NASCIMENTO TRANSPORTE\nCPF/CNPJ: 15.338.964/0001-11 Inscrição Municipal: 0027165001\nLogradouro:  RDO TANQUE Nº: 10BC\nCompl.: CASA Bairro: MONTE GORDO\nCEP: 42820000 Município: CAMAÇARI UF: BA\nTOMADOR DE SERVIÇOS\nNome/Razão Social: PH GESTAO E CONSULTORIA S A\nCPF/CNPJ: Inscrição Municipal: 0032346001\nLogradouro: ALAMEDA HUMAITA . Nº: SIN\nCompl.: COND GUARAJUBA S PREMIUS Bairro: GUARAJUBA (MONTE GORDO)\nCEP: 42840562 Município: CAMAÇARI UF: BA\nDISCRIMINAÇÃO DOS SERVIÇOS\nDESCRIÇÃO QTD VALOR UNIT (R$) VALOR TOTAL (R$)\nRETIRADA DE PODA 2,0000 300,00 600,00\nrali Lad ch\neder ES E\nEles XML PDF [ajgit tia\nRetenções (R$) Totais (R$)\nPIS: 0,00 | Valor dos Serviços (R$) 600,00\nCOFINS: 0,00 | Deduções (-) 0,00\nINSS: 0,00 | Base de Cálculo (=) 600,00\nIR: 0,00 | Alíquota (%) 3,00\nCSLL: 0,00 | Valor do ISS (R$) 18,00\nOutras: 0,00 | Valor Líquido da Nota (=) 600,00\nTotal de Retenções: 0,00\nTipo de tributação: A RECOLHER PELO PRESTADOR Data da prestação do serviço: 16/06/2026\nMunicípio da prestação do serviço: 2905701 - CAMACARI\nMunicípio da tributação: 2905701 - CAMACARI\nCNAE:\nServiço: 001602 - OUTROS SERVIÇOS DE TRANSPORTE DE NATUREZA MUNICIPAL.\nCPqD - Gestão Pública Data Impressão: 16/06/2026 10:32\n'


def test_extract_camacari2_tomador_cnpj_recuperado_via_recorte(monkeypatch):
    dummy_path = "tests/dummy_camacari2_pag20_tomador_cnpj.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_TEXT)
    # O recorte dinamico (locate + binarizacao + OCR de alto zoom) precisa de
    # uma pagina PDF real renderizavel -- fora do escopo deste teste de
    # regressao da extracao/parsing, que fixa o OCR via MOCK_TEXT. Simulamos
    # o resultado ja validado contra a nota real (ver plano de acao) e
    # travamos que a chamada recebe o indice de pagina certo (0-based).
    chamadas = []

    def fake_recupera(self, page_idx):
        chamadas.append(page_idx)
        return "25311856000109"

    monkeypatch.setattr(SPPdfExtractor, "_recuperar_cnpj_tomador_camacari", fake_recupera)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        # Nucleo do fix: o CNPJ do tomador NAO pode ficar no sentinela -> deve
        # vir do recorte de recuperacao, e o aviso correspondente some.
        assert nfse.tomador.cnpj_cpf == "25311856000109"
        assert nfse.tomador.cnpj_cpf != "00000000000000"
        assert "Dados do tomador não identificados" not in nfse.avisos

        # O recorte de recuperacao foi chamado com a pagina certa (bloco unico
        # -> pagina 1, 0-based = 0) -- confirma o encadeamento do
        # `_pagina_hint` de parse_multiple() até a chamada de recuperacao.
        assert chamadas == [0]

        # Prestador/tomador/valores de apoio (travam contexto do layout, nao
        # sao o alvo do fix).
        assert nfse.prestador.cnpj_cpf == "15338964000111"
        assert nfse.prestador.razao_social == "L DE J NASCIMENTO TRANSPORTE"
        assert nfse.tomador.razao_social == "PH GESTAO E CONSULTORIA S A"
        assert nfse.numero == "962"
        assert nfse.valores.valor_servicos == pytest.approx(600.00)
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
