# -*- coding: utf-8 -*-
r"""NFCom / NF-e de Serviço de Comunicação (`telecom_comunicacao`) - bloco de
identificação colado ao QR Code descartado pelo OCR.

Achado real: pág. 29 do lote `Notas_Fiscais_emitidas_e_recebidas_08.2026_-
_PH_Gestao_SEDE.pdf`, nota nº 34350 do Grupo F&F (13.398.812/0001-89) para
PH Gestao e consultoria S.A. (25.311.856/0001-09), R$129,90, emitida em
20/08/2026.

O bloco "NOTA FISCAL Nº 34350 - SÉRIE: 1 / DATA DE EMISSÃO: 20/08/2026 /
CHAVE DE ACESSO / Protocolo de autorização" é impresso em fonte nítida e
alto contraste, mas fica colado ao QR Code - a segmentação automática do
Tesseract trata a faixa inteira como imagem e o DESCARTA por completo. Nem
a leitura padrão (zoom 3x) nem o re-OCR de página inteira em zoom 6x
(`_ocr_recut_telecom_comunicacao`, que existe justamente para recuperar
essa coluna em outras notas do layout) devolviam uma única ocorrência de
"NOTA FISCAL Nº", "EMISSÃO", "CHAVE" ou "Protocolo".

Consequência no XML: `Numero 765` - capturado de "Resolução ANATEL nº
765/2023", no rodapé de avisos regulatórios, pelo padrão genérico de
último recurso - e `DataEmissao` caindo no `datetime.now()` (a data
realmente não existia em lugar nenhum do texto).

Corrigido com um recorte dedicado da região SEM o QR Code
(`_ocr_recut_identificacao_telecom`), prependado ao texto. Com o bloco
disponível, os extratores de número, data e chave de acesso que já
existiam para este layout acertam sozinhos - nenhum deles precisou mudar.

`MOCK_OCR` é o texto REAL de produção, capturado via
`SPPdfExtractor._ocr_page(0)` sobre a página recortada (já reflete o
combinado zoom 3x + recorte 6x + recorte de identificação).
"""
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_TELECOM_COMUNICACAO

MOCK_OCR = "NOTA FISCAL Nº 34350 - SÉRIE: 1\nE. DATA DE EMISSÃO: 20/08/2026\n\nFE CONSULTE PELA CHAVE DE ACESSO EM:\nhttps://dfe-portal.svrs.rs.gov.br/nfcom/consulta\n\nCHAVE DE ACESSO:\n2926 0813 3988 1200 0189 6200 1000 0343 5010 9563 5755\n\nProtocolo de autorização:\nFº 3292600219264996 - 20/08/2026 às 16:53:33\n\nÁREA CONTRIBUINTE:\n\nGRUPO\n\nPIO\n\nDOCUMENTO AUXILIAR DA NOTA FISCAL DE FATURA DE SERVIÇO DE COMUNICAÇÃO ELETRÔNICA\n\nGrupo FeF\n\nRua Senhor do Bonfim 544 Monte Gordo 42839852 Camacari - BA\n(71) 4062-8609\n\n13.398.812/0001-89\n\n019.192.620\n\nPH Gestao e consultoria S.A.\n\nGuarajuba Center 02 Guarajuba 42840310\n\nCamacari - BA\n\nCNPJ/CPF: 25.311.856/0001-09\nINSCRIÇÃO ESTADUAL:\n\nCÓD. DO CLIENTE: 6647\n\nNº TELEFONE: (71) 99168-8997\n\nPERÍODO: 05/08/2026 á 04/09/2026\n\nREFERÊNCIA (ANO/MÊS): 2026/08\n(0) a\nVENCIMENTO: 07/09/2026 Nº do Contrato: 6642\n\nTOTAL A PAGAR: R$ 129,90\n\nITENS DA FATURA\n\nServico de Telecomunicacoes Top\nFull\n\ncClass QUANT VALOR VALOR VALOR VALOR IS/COFINS | BCICMS | ALÍQ | VALOR\nUNIT (R$) | DESC. (R$) | ACR.(R$) | TOTAL (R$) (R$) (R$) (%) | ICMS (R$)\n\n0.00\n\nVALOR ISENTO\n\nRESERVADO AO FISCO\n\nVALOR OUTROS\n\nFUNTTEL\n\nID titulo referencia - 619895\n\nINFORMAÇÕES COMPLEMENTARES\n\nÁREA DO CONTRIBUINTE E DETERMINAÇÕES DA ANATEL\n\nLinha digitável\n\nNº Identificador de débito automático\n\n75691.30078 01719.450106 09640.040011 2 15620000012990 -\n\nAvisos Regulatórios\n\nDireito de contestação da cobrança\n\n1. Esta fatura é emitida conforme a Resolução ANATEL nº 765/2023. Você pode contestar valores desta fatura sem custo.\n\n2. Você pode contestar valores cobrados sem custo e receber resposta em até 30 dias. Entre em contato com nossa Central de Atendimento: Telefone (71) 4062-8609 e\n3. Central de Atendimento do ISP (71) 4062-8609 e WhatsApp (71) 4062-8609. WhatsApp (71) 4062-8609, ou pelo e-mail: financeiro(Dffcomunicacoes.net.br.\n\n4. Central de Atendimento da ANATEL: 1331 (ligação gratuita). A análise será concluída em até 30 dias, conforme a regra da ANATEL.\n\n5. Fatura emitida com antecedência mínima de 5 dias do vencimento. Enquanto sua contestação estiver em andamento, o serviço não será suspenso.\n6. Dados pessoais tratados conforme LGPD - Lei nº 13.709/2018.\n\n7. O não pagamento poderá acarretar suspensão do serviço, conforme regras da ANATEL.\n\n\nDOCUMENTO AUXILIAR DA NOTA FISCAL DE FATURA DE SERVIÇO DE COMUNICAÇÃO ELETRÔNICA\nGRUPO '\n\no 4 Grupo FeF\nRua Senhor do Bonfim 544 Monte Gordo 42839852 Camacari - BA\n(71) 4062-8609\n13.398.812/0001-89\n\n019.192.620\n\nPH Gestao e consultoria S.A.\n\nGuarajuba Center 02 Guarajuba 42840310\nCamacari - BA\n\nCNPJ/CPF: 25.311.856/0001-09\nINSCRIÇÃO ESTADUAL:\n\nCÓD. DO CLIENTE: 6647\n\nNº TELEFONE: (71) 99168-8997\nPERÍODO: 05/08/2026 á 04/09/2026\n\nREFERÊNCIA (ANO/MÊS): 2026/08 ÁREA CONTRIBUINTE:\n\no\nVENCIMENTO: 07/09/2026 Acolcorisiodo ca\n\nTOTAL A PAGAR: R$ 129,90\n\nVALOR VALOR VALOR VALOR PIS/COFINS | BC ICMS ALÍQ VALOR\nDENSA ATORES cClass | UN | QUANT | un (R$) | DESC. (R$) | ACR.(R$) |TOTAL(R$)| (R$) (R$) (%) | ICMS(R$)\nFF. 300, Mega 0100201 | UN 1 25,98 0,00 0,00 25,98 2,40 17,74 | 20.50 3,64\nEM ico de Telecomunicacoes Top gsgggg1 | UN | 1 103,92 0,00 0,00) 103,92 0,00 0.00| 0.00 0.00\nVALOR TOTAL NF 129,90 INFORMAÇÃO DOS TRIBUTOS RESERVADO AO FISCO\n- TRIBUTO VALOR\n\nTOTAL BASE DE CÁLCULO 17,74\n\nPIS 0,43\nVALOR ICMS 3,64\n\nCOFINS 1,97\nVALOR ISENTO 0,00) [FUST 012\nVALOR OUTROS 0,00) | FUNTTEL 0,00\n\nINFORMAÇÕES COMPLEMENTARES\n\nID titulo referencia - 619895\n\nÁREA DO CONTRIBUINTE E DETERMINAÇÕES DA ANATEL\n\nLinha digitável Nº Identificador de débito automático\n\n75691.30078 01719.450106 09640.040011 2 15620000012990 -\n\nAvisos Regulatórios Direito de contestação da cobrança\n\n1. Esta fatura é emitida conforme a Resolução ANATEL nº 765/2023. Você pode contestar valores desta fatura sem custo.\n\n2. Você pode contestar valores cobrados sem custo e receber resposta em até 30 dias. Entre em contato com nossa Central de Atendimento: Telefone (71) 4062-8609 e\n3. Central de Atendimento do ISP (71) 4062-8609 e WhatsApp (71) 4062-8609. WhatsApp (71) 4062-8609, ou pelo e-mail: financeiroDffcomunicacoes.net.br.\n\n4. Central de Atendimento da ANATEL: 1331 (ligação gratuita). A análise será concluída em até 30 dias, conforme a regra da ANATEL.\n\n5. Fatura emitida com antecedência mínima de 5 dias do vencimento. Enquanto sua contestação estiver em andamento, o serviço não será suspenso.\n\n6. Dados pessoais tratados conforme LGPD - Lei nº 13.709/2018.\n7. O não pagamento poderá acarretar suspensão do serviço, conforme regras da ANATEL.\n\n"


@pytest.fixture
def nfse(monkeypatch, tmp_path):
    dummy = tmp_path / "dummy_telecom_34350.pdf"
    dummy.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_OCR)
    notas = SPPdfExtractor(str(dummy)).parse_multiple()
    assert len(notas) == 1
    return notas[0]


def test_o_recorte_recuperou_o_bloco_de_identificacao():
    """Sem estas 3 marcas no texto OCR, o resto do teste não teria sentido -
    elas são exatamente o que a leitura de página inteira perdia."""
    assert "NOTA FISCAL Nº 34350" in MOCK_OCR
    assert "DATA DE EMISSÃO: 20/08/2026" in MOCK_OCR
    assert "2926 0813 3988 1200 0189 6200 1000 0343 5010 9563 5755" in MOCK_OCR


def test_layout_detectado(tmp_path):
    dummy = tmp_path / "dummy_layout.pdf"
    dummy.write_bytes(b"%PDF-1.4")
    ex = SPPdfExtractor(str(dummy))
    ex.from_ocr = True
    ex._pagina_veio_de_ocr = True
    assert ex._detect_layout_page(MOCK_OCR) == LAYOUT_TELECOM_COMUNICACAO


def test_numero_nao_vem_da_resolucao_anatel(nfse):
    # Antes: "765", pescado de "Resolução ANATEL nº 765/2023" no rodapé.
    assert nfse.numero == "34350"
    assert "765/2023" in MOCK_OCR  # a armadilha continua no texto


def test_data_de_emissao_nao_e_a_data_de_hoje(nfse):
    # Antes: `datetime.now()` (o XML saía com a data da conversão).
    assert nfse.data_emissao.strftime("%d/%m/%Y") == "20/08/2026"
    assert nfse.competencia.strftime("%Y-%m") == "2026-08"


def test_chave_de_acesso_como_codigo_de_verificacao(nfse):
    # Antes: o sentinela "TELECOM" (a chave não chegava ao texto).
    assert nfse.codigo_verificacao == "29260813398812000189620010000343501095635755"
    assert len(nfse.codigo_verificacao) == 44
    # Modelo 62 (NFCom) e o número da nota nas posições 25:34 da chave.
    assert nfse.codigo_verificacao[20:22] == "62"
    assert nfse.codigo_verificacao[25:34].lstrip("0") == nfse.numero


def test_entidades_e_valor_preservados(nfse):
    assert nfse.prestador.cnpj_cpf == "13398812000189"
    assert nfse.tomador.cnpj_cpf == "25311856000109"
    assert nfse.valores.valor_servicos == 129.90
