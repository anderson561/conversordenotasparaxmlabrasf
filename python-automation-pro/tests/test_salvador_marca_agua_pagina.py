# -*- coding: utf-8 -*-
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
import os

# Texto REAL do OCR (Tesseract) da pagina unica do PDF "NF - 39029.pdf"
# (nota no 00039029, layout Salvador/BA, prestador A LIMPCANO DESENTUPIMENTO E
# SUCCAO DE FOSSAS LTDA - EPP -> tomador SOHO RESTAURANTE LTDA), JA COM os
# recuts de `_ocr_page` aplicados (as 4 primeiras linhas do texto abaixo sao
# os blocos limpos prependados). Achado real: uma marca d'agua diagonal
# (carimbo "...ISS DEVERA SER RETIDO...") cobre a pagina INTEIRA e degrada o
# OCR onde cruza texto impresso - corrompendo o rotulo "PRESTADOR DE
# SERVICOS" (le "PRESPAD RVIÇOS", nenhuma etiqueta reconhece), o Codigo de
# Verificacao ("ALVADORLYQ", puro lixo) e a grade de valores (rotulo "Valor
# do ISS" le "Ne alét.do ISS", o regex padrao nao casa). Sem rotulo de
# prestador reconhecivel, o bloco generico da entidade virava o documento
# INTEIRO e o CNPJ/razao do TOMADOR (o unico par bem formado que sobra)
# vazava para as DUAS entidades; sem a linha "VALOR TOTAL DA NOTA" legivel, a
# grade tambem falhava e o fallback zerava valor_servicos E base_calculo
# junto (o fallback antigo herda `base = val_serv`). Corrigido com 4 recuts
# dedicados gateados por evidencia do defeito (nenhum rotulo de prestador
# reconhecivel antes de "TOMADOR" / linha "VALOR TOTAL DA NOTA" ilegivel):
# Codigo de Verificacao e bloco do Prestador via recorte+despeculagem
# (filtro de mediana) em zoom alto; grade de valores via recorte por CELULA
# (Deducao/Base/Aliquota recuperados, ISS DERIVADO matematicamente de
# Base x Aliquota - a celula do ISS continua ilegivel mesmo isolada -,
# Credito/Outras Retencoes fixados em 0,00 por serem sempre zero nesta nota
# ["Esta Nota Salvador nao gera credito"] e por serem irrecuperaveis via OCR
# em qualquer combinacao de zoom/kernel testada).
MOCK_TEXT = "Valor Total das Dedu\u00e7\u00f5es (R$): Base de C\u00e1lculo (R$) Al\u00edquota (%) Valor do ISS (R$) Cr\u00e9dito Nota Salvador (R$):\n0,00 1.860,00 5,00% 93,00 0,00\nValor INSS (R$): Valor PIS (R$); Valor COFINS (R$) Valor IR (R$) Valor CSLL (R$) Outras Reten\u00e7\u00f5es (R$) Valor L\u00edquido (R$):\n0,00 12,09 55,80 18,60 18,60 0,00 1.661,91\nVALOR TOTAL DA NOTA = R$ 1.860,00\nC\u00f3digo de Verifica\u00e7\u00e3o: LYQC-YTIS\nPRESTADOR DE SERVI\u00c7OS\nCPF/CNPJ\n16.390.536/0001-09\nNome/Raz\u00e3o Social\nA LIMP\u00c7ANO DESENTUPIMENTO ESUCCAO DE FOSSAS LTDA - EPP\nEndere\u00e7o\n\nN\u00famero da Nota:\nJOR 00039029\n\nData e Hora de Emiss\u00e3o:\n\n21/07/2026 16:31:43\nR C\u00f3digo de Verifica\u00e7\u00e3o:\nalvador LYQ\u00ca-YTIS\n\nPREFEITURA MUNICIPAL DO SALVADOR 00039628\" Nota:\n\nECRETARIA MUNICIPAL DA FAZENDA Data e Hora de Emiss\u00e3o:\n21/07/2026 16:31:43\n\np\u00f3digo de Verifica\u00e7\u00e3o:\n\nOTA FISCAL DE SERVI\u00c7OS ELETR\u00d4NICA - Nota Salvador LYQENTIS\nPRESPAD RVI\u00c7OS\nF/CNP. Inscri\u00e7\u00e3o Municipal\n165390.536, -09 00.061.090/001-14\nNoriyRaz\u00e3o ] [\nCCAO DE FOSSAS LTDA - EPP IC\n\nA LIMB\u00c7ANO Di NT!\nEndere\u00e7i\n\nRua Guary8 - eroia\nE-mail\nlimpcanoQDlimbeano.co!\n\nTOMADOR DE SERVI\u00c7OS\n\nNome/Raz\u00e3o Social A\nSOHO RESTAURANT\u00caLTDA.\n\nCPFICNPJ \u00abfo\nE\n\n02.077.434/0001-15 es\nEndere\u00e7o \u00ba\nAve Lafayete Coutinho 1010 MERC\u00cdS Salva : 15-160/BA\n\nE-mail &\nDISCRIMINA\u00c7\u00c3O. DOS SERV\u00cdIGOS\n\nVIAGEM DO C, NH\u00c3O DE SUC\u00c7\u00c3O N\u00c1CUO CA\nCAIXAS DE ESGOTO E ELEVAT\u00d3RIAS ROCALI\n\nLAFAYETTE E TAXA DE DESLOCAMENTO EQU\nCONFORME 0.5 20260710117 E 202607082.\n\n40283-790 -\n\nInscri\u00e7\u00e3o Municipal\n00.142.642/001-23\n\n12M*, RA SUC\u00c7\u00c3O DE RES\u00cdDUOS L\u00cdQUIDOS CONTIDOS EM\nHO E DE GRELHAS E CANALETAS LOCALIZADAS NA \u00c1REA DO\n06/07/2026. SERVI\u00c7O REALIZADO EM 13/07/2026,\n\nIR FONTE = R$ 18,60\n\nPIS/COFINS/CSLL (4,65%) = R$ 86,49 Ea\nVENCIMENTO: 12/08/2026 Pes\nFORMA DE PAGAMENTO: BOLETO Se,\n\n\u201ca\n\na\nVALOR TOTAL DA NO =R$ -B50,\nCNAE: EM\n3702900 - Atividades relacionadas a esgoto, exceto a gest\u00e3o de redes E\nItem da Lista de Servi\u00e7os E\n00710 - Limpeza, manuten\u00e7\u00e3o e conserva\u00e7\u00e3o de vias e logradouros p\u00fablicos, im\u00f3veis, cha , piSginas, par: s, jardins e &ong\u00eane...\nValor Total das Dedu\u00e7\u00f5es (R$): Base de C\u00e1lculo (R$) Al\u00edquota (%); Ne al\u00e9t.do ISS (F\u00ba dito Nota Salvad\u00eag (R$):\n0,00 1.860,00 500% .00 oo\nValor INSS (R$): Valor PIS (R$); Valor COFINS (R$) Valor IR (R$) Valor CSLL (R$ Oufefgeten \u00cdquido (R$)\n0,00 12,09 55,80 18,60 1g:g0 1.661,91\nAl\u00edquota IBS (%) Valor IBS (R$) Al\u00edquota CBS (%)) alor CESTAS\na x a \u00e7 a\n\nOUTRAS INFORMA\u00c7\u00d5ES\n\n- Esta Nota Salvador foi emitida com respaldo na Lei 7.186/2006\n\n- Esta Nota Salvador n\u00e3o gera cr\u00e9dito\n\n- O ISS desta Nota Salvador ser\u00e1 RETIDO pelo Tomador de Servi\u00e7o que dever\u00e1 recolher atrav\u00e9s da Guia de Nota Salvad\n- COMPET\u00caNCIA: 07/2026 (m\u00eas/ano)\n\n- C\u00f3digo de Tributa\u00e7\u00e3o do Munic\u00edpio: 0710-0/01 - Limpeza de vias e logradouros p\u00fablicos, parques, jardins e cong\u00eaneres\n"


def test_salvador_marca_agua_pagina_recupera_prestador_e_valores(monkeypatch):
    dummy_path = "tests/dummy_salvador_marca_agua.pdf"
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

        assert nfse.numero == "00039029"
        assert nfse.codigo_verificacao == "LYQCYTIS"

        # Nucleo do bug: o CNPJ/razao do PRESTADOR nao pode ser o do TOMADOR
        # (vazamento por rotulo "PRESTADOR DE SERVIÇOS" ilegivel).
        assert nfse.prestador.cnpj_cpf == "16390536000109"
        assert "LIMP" in nfse.prestador.razao_social.upper()
        assert "FOSSAS" in nfse.prestador.razao_social.upper()

        assert nfse.tomador.cnpj_cpf == "02077434000115"
        assert nfse.tomador.cnpj_cpf != nfse.prestador.cnpj_cpf

        v = nfse.valores
        assert v.valor_servicos == pytest.approx(1860.00)
        assert v.base_calculo == pytest.approx(1860.00)
        assert v.aliquota == pytest.approx(0.05)
        assert v.valor_iss == pytest.approx(93.00)
        assert v.valor_deducoes == pytest.approx(0.0)
        assert v.valor_inss == pytest.approx(0.0)
        assert v.valor_pis == pytest.approx(12.09)
        assert v.valor_cofins == pytest.approx(55.80)
        assert v.valor_ir == pytest.approx(18.60)
        assert v.valor_csll == pytest.approx(18.60)
        assert v.outras_retencoes == pytest.approx(0.0)
        assert v.valor_liquido_nfse == pytest.approx(1661.91)
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
