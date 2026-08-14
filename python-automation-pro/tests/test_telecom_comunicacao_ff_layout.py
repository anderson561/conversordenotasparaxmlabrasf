# -*- coding: utf-8 -*-
r"""NF-e de Serviço de Comunicação (`telecom_comunicacao`) — layout sem
NENHUM teste até então, achado num pedido do usuário para revisar se a
página 3 de um lote real (`Complemento3_Notas_Fiscais_Recebidas_07.2026_-
_Guarajuba_Suites.pdf`) já era tratada pelo layout F&F (`ff_locacao`).

Não é: é uma fatura de INTERNET/comunicação do "Grupo F&F" (F&F Comunicações,
CNPJ 13.398.812/0001-89 — o MESMO CNPJ do `ff_locacao`, mas um documento
estruturalmente diferente da fatura de locação de CFTV) para a Boutique
Guarajuba/PH Gestão (CNPJ 25.311.856/0001-09), nota real nº 31696,
R$558,40. Corretamente cai no layout `telecom_comunicacao` (o título
"NOTA FISCAL DE FATURA DE SERVIÇO DE COMUNICAÇÃO" é mais específico que o
CNPJ do emissor) — mas esse layout, sem teste nenhum, produzia um XML
inteiro errado nesta nota real:

1. **Prestador com o CNPJ do TOMADOR**: o CNPJ do emissor sai do OCR como
   "13.398,812/0001-89" (vírgula em vez de ponto entre "398" e "812") — não
   batia a regex antiga do fallback "1º CNPJ bem-formado", que pulava
   direto pro 2º CNPJ do texto (o do TOMADOR, "25.311.856/0001-09",
   labelado "CNPJ/CPF:") — prestador e tomador saíam com o MESMO CNPJ.
2. **Leitura padrão (zoom 3x) perde a coluna direita inteira do
   cabeçalho**: "NOTA FISCAL Nº 31696", "DATA DE EMISSÃO: 15/07/2026",
   "REFERÊNCIA (ANO/MÊS): 2026/07", "VENCIMENTO" e "TOTAL A PAGAR" não
   apareciam no texto — número caía no fallback genérico (pescava "nº 765"
   da "Resolução ANATEL nº 765/2023" citada no rodapé, em vez do número
   real), data de emissão caía em `datetime.now()`, competência ficava sem
   resolver, e o valor saía zero.
3. **Total a pagar com rótulo colado e sem vírgula decimal**: numa das
   variantes de OCR desta mesma coluna recuperada, o rótulo sai colado sem
   espaço nenhum ("TOTALAPAGAR:R$55840", sem a vírgula) — sem tolerância a
   isso, o valor sairia R$55.840,00 (100x o valor real, R$558,40) em vez de
   zero.
4. **Endereço do tomador vazando o do PRESTADOR**: o tomador não tem
   "Rua/Av" no próprio endereço (é só o nome do bairro/praia, "Guarajuba")
   — a janela de busca do endereço alcançava (e "roubava") a "Rua Senhor
   do Bonfim..." do prestador, impressa mais acima no documento.
5. **Nomes corrompidos pelo recorte de zoom alto prependado**: o recorte
   dedicado que resolve o bug #2 (`_ocr_recut_telecom_comunicacao`, zoom
   6x) tem suas PRÓPRIAS colunas fundidas/ruidosas — sem preferir a cópia
   mais limpa (a da leitura padrão, que vem depois no texto combinado), o
   nome do prestador saía com ruído de pontuação colado ("; Grupo FeF .")
   e o nome do tomador saía como um fragmento de ruído do recorte inteiro
   ("Ds nn RR )") em vez de "Boutique Guarajuba PH Gestao".

Texto OCR real capturado via `SPPdfExtractor._ocr_page(2)` (mesmo caminho
usado em produção — já reflete o texto combinado zoom 3x + recorte 6x).
"""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_OCR = '. | DOCUMENTO AUXILIAR DA NOTA FISCAL DE FATURA DE SERVIÇO DE COMUNICAÇÃO ELETRÔNICA\n; Grupo FeF .\n\nRua Senhor do Bonfim 544 Monte Gordo 42839852 Camacari - BA\n\n(71) 4062-8609\n\n13.398.812/0001-89\n\n019.192.620 |\n\nDs nn RR )\n\nBoutique Guarajuba PH Gestao [a]: a LE Tm] NOTA FISCAL Nº 31696 - SÉRIE: 1\n\nGUARAJUBA 0 Guarajuba 42840310 &» DATA DE EMISSÃO: 15/07/2026\nCamacari - BA\n\nCNPJ/CPF: 25.311.856/0001-09\nINSCRIÇÃO ESTADUAL:\n\nCÓD. DO CLIENTE: 7396\n\nNº TELEFONE: (71) 99168-8997\nPERÍODO: 15/07/2026 á 14/08/2026\n\n| ÁREA CONTRIBUINTE: |\n| VENCIMENTO: 17/08/2026 o Capusia aee\n* TOTAL A PAGAR: R$ 558,40\nem O CARTAS EE aa | VALOR |\nnda feias GRE | essi UM [QUANT UNIT (RS) DESC. (R$) ACR.(R$) TOTAL(RS) (R$) | (R$) | (%) | ICMSIRS)\nINTERNET COLETIVA | a | | I |\n| AOOMEGA GUARAJUBA SUITES (0100201 UN | 1 11168 900 0,00 168 1033 7627\nEr de Telecomunicacoes Top ne00601 | UN | 1º 44872 0,00 E | 900 000\n- ia (SR (TT\n\'VALORTOTALNF 55840. INFORMAÇÃO DOS TRIBUTOS | E RESERVADO AO FISCO DI\nE a E | "= EASTRIBUTO | VALOR ||:\nTOTAL BASE DE CÁLCULO | toa | O\ne + PIS | 184 |\nVALOR ICMS 15,64 | fred |\nE E COFINS 849 |\n\'vaLOR OUTROS | 0,00, FUNTTEL 0,00 .\nLie | sai CAE si | INFORMAÇÕES COMPLEMENTARES é\n| ID titulo referencia - 610976 j |\n|\n[ E \' ÁREA DO CONTRIBUINTE E DETERMINAÇÕES DA ANATEL\n\nfia MR pe erorranevererren em f\nLinha digitável “ | Nº Identificador de débito automático |\n\nemma rasansarasransenesapom\n\n75691.30078 01719.450106 08790.120011 9 15410000316369 RR |\n\nTenenennmanamams\n\nO\n\n| Avisos Regulatórios Direito de contestação da cobrança\n\n| 1. Esta fatura é emitida conforme a Resolução ANATEL nº 765/2023. Você pode contestar valores desta fatura sem custo.\n\n2. Você pode contestar valores cobrados sem custo e receber resposta em até 30 dias. Entre em contato com nossa Central de Atendimento: Telefone (71) 4062-8609 e\n\n! 3. Central de Atendimento do ISP (71) 4062-8609 e WhatsApp (71) 4062-8609. WihatsApp (71) 4062-8609, ou pelo e-mail: financeiroffcomunicacoes.net.br.\n\nÉ 4. Central de Atendimento da ANATEL: 1331 (ligação gratuita). - A análise será concluída em até 30 dias, conforme a regra da ANATEL. |\ni 5. Fatura emitida com antecedência mínima de 5 dias do vencimento. Enquanto sua contestação estiver em andamento, o serviço não será suspenso. |\n| 6. Dados pessoais tratados conforme LGPD - Lei nº 13.709/2018..\n\n7. O não pagamento poderá acarretar suspensão do serviço, conforme regras da ANATEL.\n\nj . À\n\nt Es. meme\nDa\n\n. | DOCUMENTO AUXILIAR DA NOTA FISCAL DE FATURA DE SERVIÇO DE COMUNICAÇÃO ELETRÔNICA\n\nGrupo FeF\n\nRua Senhor do Bonfim 544 Monte Gordo 42839852 Camacari - BA\n(71) 4062-8609\n\n13.398,812/0001-89\n\n019.192.620\n\nBoutique Guarajuba PH Gestao\n\nGUARAJUBA 0 Guarajuba 42840310\nCamacari - BA\n\nCNPJ/CPF: 25.311.856/0001-09\nINSCRIÇÃO ESTADUAL:\n\nCÓD. DO CLIENTE: 7396\n\nNº TELEFONE: (71) 99168-8997\nPERÍODO: 15/07/2026 á 14/08/2026\n\nCONSULTE PELA CHAVE DE ACESSO EM:\nhttps://dfe-portal.svrs.rs.gov.brinfcom/consulta\n\nCHAVE DE ACESSO:\nY\n|\n|\n\nProtocolo de autorização:\n\nVALOR | VALOR |\n\n| | VALOR | VALOR \'PISICOFINS BCICMS | ALÍQ | VALOR\n[ITENS DA FATURA | | UNIT(RS) | DESC.(R$) | ACR.(R$) [TOTAL (R$) | R9 | (R9 | (%) | ICMS (R$)\n(INTERNET COLETIVA i | | | | | | |\n\n| AOOMEGA GUARAJUBA SUITES 0100201 | Cad 1 mes 0,00) 0.00) mes 1053] 7627| 20.50 | 15,64\ncenico de Telecomunicacoes Top ranogo | UN | 0,00. 0,00] 446,72] | |\n\n(vaLORTOTALNE o 558,40) (INFORMAÇÃO DOS TRIBUTOS | fu\n+\n| T | |. TRIBUTO | VALOR |\n[TOTAL BASE DE CÁLCULO | 76,27. ani mé |\nVALOR ICMS | 15,64] e can É\n| | | COFINS 849 ||\njvator SENT | 000 (FUsT | 0,50),\n| VALOR OUTROS | 0,00 FUNTIEL | 000! |\n(\nÉ o (1 INFORMAÇÕES COMPLEMENTARES\n\nID titulo referencia - 610976\n\nÁREA DO CONTRIBUINTE E DETERMINAÇÕES DA ANATEL\n\nf o\n\nLinha digitável Nº Identificador de débito automático\n75691.30078 01719.450106 08790.120011 9 15410000316369 dio Í\n| à\nPague também via Pix.\nÉ sa\n\n| Sé f>L\nAvisos Regulatórios Direito de contestação da cobrança\n\n1. Esta fatura é emitida conforme a Resolução ANATEL nº 765/2023. Você pode contestar valores desta fatura sem custo.\n| 2. Você pode contestar valores cobrados sem custo e receber resposta em até 30 dias. Entre em contato com nossa Central de Atendimento: Telefone (71) 4062-8609 e\n! 3. Central de Atendimento do ISP (71) 4062-8609 e WhatsApp (71) 4062-8609. WihatsApp (71) 4062-8609, ou pelo e-mail: financeiroQffcomunicacoes.net.br.\n| 4. Central de Atendimento da ANATEL: 1331 (ligação gratuita). - A análise será concluída em até 30 dias, conforme a regra da ANATEL.\n| 5. Fatura emitida com antecedência mínima de 5 dias do vencimento. Enquanto sua contestação estiver em andamento, o serviço não será suspenso.\n\n6. Dados pessoais tratados conforme LGPD - Lei nº 13.709/2018.\n\n7. O não pagamento poderá acarretar suspensão do serviço, conforme regras da ANATEL.\ni %\nÀ\n\n'


@pytest.fixture
def nfse(monkeypatch):
    dummy_path = "tests/dummy_telecom_ff_31696.pdf"
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


def test_numero_da_nota(nfse):
    # Antes: "765" (da "Resolução ANATEL nº 765/2023" citada no rodapé).
    assert nfse.numero == "31696"


def test_data_emissao_e_competencia(nfse):
    assert nfse.data_emissao.strftime("%Y-%m-%d") == "2026-07-15"
    assert nfse.competencia.strftime("%Y-%m") == "2026-07"


def test_valor_servicos_nao_e_100x_maior(nfse):
    assert nfse.valores.valor_servicos == 558.40
    assert nfse.valores.valor_liquido_nfse == 558.40


def test_prestador_cnpj_diferente_do_tomador(nfse):
    p = nfse.prestador
    tm = nfse.tomador
    # Antes: os dois saíam com "25311856000109" (CNPJ do TOMADOR).
    assert p.cnpj_cpf == "13398812000189"
    assert tm.cnpj_cpf == "25311856000109"
    assert p.cnpj_cpf != tm.cnpj_cpf


def test_prestador_razao_social_sem_ruido_de_pontuacao(nfse):
    # Antes: "; Grupo FeF ." (ruído colado nas pontas pelo recorte de zoom alto).
    assert nfse.prestador.razao_social == "Grupo FeF"


def test_tomador_razao_social_correta(nfse):
    # Antes: "Ds nn RR )" (fragmento de ruído do recorte de zoom alto).
    assert nfse.tomador.razao_social == "Boutique Guarajuba PH Gestao"


def test_tomador_endereco_nao_vaza_o_do_prestador(nfse):
    e = nfse.tomador.endereco
    # Antes: "Rua Senhor do Bonfim 544 Monte Gordo..." (endereço do PRESTADOR).
    assert "Bonfim" not in e.logradouro
    # Antes: município saía com o bloco inteiro colado ("Boutique Guarajuba
    # PH Gestao\n\nGUARAJUBA 0 Guarajuba 42840310\nCamacari") por um "\s"
    # que também casava quebra de linha.
    assert e.municipio == "Camacari"
    assert e.uf == "BA"
    assert e.codigo_municipio == "2927408"  # IBGE de Camaçari/BA
    assert e.cep == "42840310"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
