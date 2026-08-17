# -*- coding: utf-8 -*-
"""Salvador/BA escaneado — nota nº 2169 (INSTITUIÇÃO ASSISTENCIAL BENEFICENTE
CONCEIÇÃO MACEDO -> BONI TRANSPORTES): 2 degradações distintas na mesma nota,
achadas ao investigar o bug do prestador trocado (mesma investigação da nota
irmã nº 2150, mesmo par prestador/tomador, competências diferentes).

1. Código de Verificação saía como a palavra "PRESTADOR" — o rótulo "Código de
   Verificação:" ficava colado, sem nenhum valor legível no meio, diretamente
   ao início da seção seguinte ("PRESTADOR DE SERVIÇOS"), e o regex específico
   de Salvador (que tolera o rótulo saindo truncado/embaralhado) capturava a
   palavra do rótulo seguinte como se fosse o próprio código. Corrigido:
   (a) rejeita explicitamente candidatos que são rótulos conhecidos do
   documento ("PRESTADOR", "TOMADOR", "PREFEITURA", "SECRETARIA", "ALVADOR");
   (b) `_ocr_header_box_salvador` ganhou tentativas adicionais de zoom/PSM/
   altura de recorte, validando que o texto recuperado contém um código
   plausível antes de aceitar o recorte (em vez de aceitar só a presença do
   rótulo) — o valor real ("RKAR-XEEJ", conferido na imagem da página) só
   aparece legível em zoom 8x/PSM 4/recorte mais alto.

2. CNPJ/razão social/endereço do TOMADOR saíam corrompidos: CNPJ com
   formatação perfeita mas DÍGITO errado ("04.655.283/0003-50", reprova
   checksum; o certo é "04.555.283/0003-50" — mesmo tomador da nota 2150,
   onde esse mesmo CNPJ já sai correto até no zoom padrão), razão social com
   lixo à direita ("...LTDA. Pe") e endereço embaralhado ("Ea ARA: QUITERIA"
   em vez de "RUA MARIA QUITERIA"). Como o CNPJ malformado tinha pontuação
   sintaticamente válida, o gatilho antigo do recorte dedicado do tomador (que
   só olhava a FORMATAÇÃO) nunca disparava — sem o recorte, o CNPJ inválido
   caía direto no sentinela "não identificado" em vez de ser corrigido.
   Corrigido: o gatilho agora também valida o CHECKSUM do CNPJ candidato, não
   só o formato; e `_ocr_tomador_salvador` passou a tentar múltiplos zooms
   (5x/6x/7x), ficando com o primeiro cujo CNPJ recuperado valida — zoom 6x é
   o que lê esta nota corretamente."""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_OCR = 'TOMADOR DE SERVIÇOS\n\nNome/Razão Social\n\nBONI TRANSPORTES, LOGISTICA E COMERCIO LTDA.\n\nCPF/CNPJ: Inserção Municipal:\n04.555.283/0003-50 em\n\nEndereço:\n\nRUA MARIA QUITERIA 263, GALPAO ITINGA - Lauro de Freitas - CEP: 42738-205/BA\nE-mail:\n\nIMPOSTOSGBNORTECCONTABILIDADE COM BR\n\n\nNúmero da Nota:\n00002169\n\nData e Hora de Emissão:\n07/07/2026 12:00:49\n\nCódigo de Verificação:\nRKAR-XEE) :\n\nJOR\n\n\nPREFEITURA MUNICIPAL DO SALVADOR 000UZ TOS Not\n\nSECRETARIA MUNICIPAL DA FAZENDA Data e Hora de Emissão:\n07/07/2026 12:00:49\n\nNOTA FISCAL DE SERVIÇOS ELETRÔNICA - Nota Salvador RdRo deerificação:\nPRESTADOR DE SERVIÇOS\n\nCPF/CNPJ Inscrição Municipal\n\n00.584.568/0001-05 00.258.440/001-06\n\nNome/Razão Social\n\nINSTITUICÃO ASSISTENCIAL BENEFICENTE CONCEIÇÃO MACEDO\n\nEndereço:\n\nRua Santa Clara 85 , ANDAR 1 E2 SUBS - NAZARE - Salvador - CEP: 40040-450 - BA\nE-mail\n\nTOMADOR DE SERVIÇOS\n\nNome/Razão Social\nBONI TRANSPORTES, LOGISTICA E COMERCIO LTDA.\nPe Inscrição Municipal\n04.655.283/0003-50 —\nEndereço:\nEa ARA: QUITERIA 263, GALPAO ITINGA - Lauro de Freitas - CEP: 42738-205/BA\nmail\nIMPOSTOSMNORTECCONTABILIDADE.COM.BR\nDISCR VIÇOS\n«RISSRIMINAÇÃO DOS SER O scantes : THAMIRES DO NASCIMENTO LOPES DA SILVA, REFERENTE AO MÊS\nJULHO/2026.\n\nDADOS BANCÁRIOS:\n\nAGÊNCIA :3072\n\nCONTA CORRENTE: 69.077-5\n\nCHAVE PIX (E-MAIL) aprendiz .ibecmffterra.com.br\n\nNOME: INSTITUIÇÃO ASSISTENCIAL BENEFICENTE CONCEIÇÃO MACEDO\n\nVALOR TOTAL DA NOTA = R$170,00\n\nCNAE\n\n9430800 - Atividades de associação de defesa de direitos sociais\n\nItem da Lista de Serviços.\n\n01701 - Assessoria ou consultoria de qualquer natureza, não contida em outros itens desta lista; análise, exame, pesquisa, coleta, co...\n\nValor Total das Deduções A Base de Cálculo (R$) Alíquota (%) a do ISS (R$) Crédito Nota Salvador (R$)\n170,00 8,50 -— 0,00\n\nValor INSS (R$) NES Valor PIS (R$): Valor COFINS (R$ Valor IR (R$) Valor CSLL E Outras Retenções (R$) Valor Líquido (R$)\n0,00 0,00 0,00 0,00 170,00\n\nAlíquota TES (3%) Valor BS (R$) | Alíquota CBS (%) Valor CBS (R$) E\n\na * *\n\nOUTRAS INFORMAÇÕES\n\n- Esta Nota Salvador foi emitida com respaldo na Lei 7 186/2006\n- Data de vencimento do ISS desta Nota Salvador: 05/08/2026\n\n- COMPETÊNCIA: 07/2026 (mês/ano)\n\n- Código de Tributação do Município: 1701-0/01 - Assessoria ou consultoria de qualquer natureza, exceto econômica, financeira, de imprensa,\nem informática ou relacionada a operações de fatorização (factoring)\n\n\n'


@pytest.fixture
def nfse(monkeypatch):
    dummy_path = "tests/dummy_salvador_2169.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_OCR)

    try:
        nfse_list = SPPdfExtractor(dummy_path).parse_multiple()
        assert len(nfse_list) == 1
        yield nfse_list[0]
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_codigo_verificacao_nao_e_o_rotulo_prestador(nfse):
    assert nfse.codigo_verificacao == "RKARXEE"
    assert nfse.codigo_verificacao != "PRESTADOR"


def test_tomador_cnpj_com_digito_trocado_e_corrigido(nfse):
    assert nfse.tomador.cnpj_cpf == "04555283000350"
    assert nfse.tomador.cnpj_cpf != "00000000000100"
    assert nfse.tomador.cnpj_cpf != "04655283000350"


def test_tomador_razao_social_sem_lixo_a_direita(nfse):
    razao = nfse.tomador.razao_social
    assert razao == "BONI TRANSPORTES, LOGISTICA E COMERCIO LTDA"
    assert not razao.endswith("Pe")


def test_tomador_endereco_sem_embaralhamento(nfse):
    assert nfse.tomador.endereco.logradouro == "RUA MARIA QUITERIA"


def test_prestador_permanece_correto(nfse):
    p = nfse.prestador
    assert p.cnpj_cpf == "00584568000105"
    assert p.razao_social == "INSTITUICÃO ASSISTENCIAL BENEFICENTE CONCEIÇÃO MACEDO"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
