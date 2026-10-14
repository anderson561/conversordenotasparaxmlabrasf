# -*- coding: utf-8 -*-
r"""NFCom / NF-e de Serviço de Comunicação (`telecom_comunicacao`) - CNPJ do
prestador (e Código de Verificação) deslocados quando a chave de acesso de 44
dígitos vem COLADA ao final da linha anterior ("Nº TELEFONE: (71) 99168-8997
2926 0913 ...").

Achado real: pág. 4 do lote `Notas_Fiscais_Recebidas_09.2026_-_Guarajuba_
Suites.pdf`, nota nº 35972 do Grupo F&F (13.398.812/0001-89) para Boutique
Guarajuba PH Gestao (25.311.856/0001-09), R$558,40, emitida em 02/09/2026.

A chave impressa é "2926 0913 3988 1200 0189 6200 1000 0359 7210 3787 4279".
O OCR da coluna do destinatário/chave (zoom 6x) a devolve na MESMA linha do
"Nº TELEFONE: (71) 99168-8997" do tomador, então o texto fica
"... 99168-8997 2926 0913 3988 ... 3787 4279". O localizador antigo da chave
(`\b(?:\d{4}\s+){10}\d{4}\b` = "11 grupos de 4 dígitos") casava
"8997 2926 ... 3787" (começando no fim do telefone e perdendo o último grupo
"4279") - 44 dígitos, mas deslocados 4 posições. Consequências no XML:

  * `CodigoVerificacao` = "89972926091339881200018962001000035972103787"
    (lixo "8997" no início, "4279" cortado no fim);
  * `Prestador/Cnpj` = chave[6:20] = "26091339881200" = AAMM + 10 dígitos do
    CNPJ real (inválido no dígito verificador, e mesmo assim aceito).

Corrigido localizando a chave por ESTRUTURA/VALIDAÇÃO (qualquer janela de 44
dígitos cujo dígito verificador mod-11 fecha e cujo CNPJ do emitente passa no
DV), não por offset fixo - e exigindo DV válido em todo CNPJ de prestador
aceito (sentinela + aviso quando nada for confirmável).

`MOCK_OCR` é o texto REAL de produção, capturado via
`SPPdfExtractor._ocr_page(3)` sobre a pág. 4 do lote (já reflete a leitura
padrão 3x + recorte 6x).
"""
import re

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_TELECOM_COMUNICACAO

CHAVE_REAL = "29260913398812000189620010000359721037874279"
CNPJ_PRESTADOR = "13398812000189"

MOCK_OCR = 'DOCUMENTO AUXILIAR DA NOTA FISCAL DE FATURA DE SERVIÇO DE COMUNICAÇÃO ELETRÔNICA\nGRUPO |\n\ncm" à Grupo FeF\nRua Senhor do Bonfim 544 Monte Gordo 42839852 Camacari - BA\n5 (71) 4062-8609\n13.398.812/0001-89\n\n019.192.620\n\nBoutique Guarajuba PH Gestao [M] NOTA FISCAL Nº 35972 - SÉRIE: 1\nGUARAJUBA O Guarajuba 42840310 a DATA DE EMISSÃO: 02/09/2026\nCamacari - BA CONSULTE PELA CHAVE DE ACESSO EM:\n\nCNPJ/CPF: 25.311.856/0001-09 Luma pletgr Pr 3 https://dfe-portal.svrs.rs.gov.br/nfcom/consulta\nINSCRIÇÃO ESTADUAL: CHAVE DE ACESSO:\n\nCÓD. DO CLIENTE: 7396\nNº TELEFONE: (71) 99168-8997 2926 0913 3988 1200 0189 6200 1000 0359 7210 3787 4279\nProtocolo de autorização:\n\nPERÍODO: 00/00/0000 á 00/00/0000\n3292600231706988 - 02/09/2026 às 15:45:25\n\nREFERÊNCIA (ANO/MÊS): 2026/09 ÁREA CONTRIBUINTE:\nVENCIMENTO: 02/09/2026\n\nTOTAL A PAGAR: R$ 558,40\n\nVALOR VALOR VALOR VALOR PIS/COFINS | BC ICMS ALÍQ VALOR\nITENS DA FATURA ER QUANT | UNIT(R$) | DESC.(R$) ACR.(R$) TOTAL(R$)| (R$) (R$) ICMS (R$)\n\nINTERNET COLETIVA\n“JOOMEGA GUARAJUBA SUITES | 9100201 111,68 0,00 76,27 | 20.50 15,64\nCorvico de Telecomunicacoes Top | 9599601 446,72 0,00 0.00 | 0.00 0.00\n\nVALOR TOTAL NF 558,40\nTOTAL BASE DE CÁLCULO 76,27\n\nRESERVADO AO FISCO\n\nINFORMAÇÃO DOS TRIBUTOS\nTRIBUTO VALOR\n\nVALOR ICM 15,64\n\nVALOR OUTROS FUNTTEL 000\n\nINFORMAÇÕES COMPLEMENTARES\n\nID titulo referencia - 610976\n\nÁREA DO CONTRIBUINTE E DETERMINAÇÕES DA ANATEL\n\nLinha digitável Nº Identificador de débito automático\n\n00000.00000 00000.000000 00000.000000 O 00000000000000 -\n\nAvisos Regulatórios Direito de contestação da cobrança\n\n1. Esta fatura é emitida conforme a Resolução ANATEL nº 765/2023. Você pode contestar valores desta fatura sem custo.\n2. Você pode contestar valores cobrados sem custo e receber resposta em até 30 dias. Entre em contato com nossa Central de Atendimento: Telefone (71) 4062-8609 e\n3. Central de Atendimento do ISP (71) 4062-8609 e WhatsApp (71) 4062-8609. WhatsApp (71) 4062-8609, ou pelo e-mail: financeiro(Dffcomunicacoes.net.br.\n\n4. Central de Atendimento da ANATEL: 1331 (ligação gratuita). A análise será concluída em até 30 dias, conforme a regra da ANATEL.\n\n5. Fatura emitida com antecedência mínima de 5 dias do vencimento. Enquanto sua contestação estiver em andamento, o serviço não será suspenso.\n6. Dados pessoais tratados conforme LGPD - Lei nº 13.709/2018.\n\n7. O não pagamento poderá acarretar suspensão do serviço, conforme regras da ANATEL.\n\n\nDOCUMENTO AUXILIAR DA NOTA FISCAL DE FATURA DE SERVIÇO DE COMUNICAÇÃO ELETRÔNICA\n\nGRUPO\no 4 Grupo FeF\nRua Senhor do Bonfim 544 Monte Gordo 42839852 Camacari - BA\n(71) 4062-8609\n13.398.812/0001-89\n019.192.620\n\nBoutique Guarajuba PH Gestao\n\nGUARAJUBA 0 Guarajuba 42840310\nCamacari - BA\n\nCNPJ/CPF: 25.311.856/0001-09\nINSCRIÇÃO ESTADUAL:\n\nCÓD. DO CLIENTE: 7396\n\nNº TELEFONE: (71) 99168-8997\nPERÍODO: 00/00/0000 á 00/00/0000\n\nNOTA FISCAL Nº 35972 - SÉRIE: 1\nDATA DE EMISSÃO: 02/09/2026\n\nhttps://dfe-portal.svrs.rs.gov.br/nfcom/consulta\n\nGF CHAVE DE ACESSO:\n\nE mm JA\n\nEn EE CONSULTE PELA CHAVE DE ACESSO EM:\nER Ba e\nra AR\n\nProtocolo de autorização:\n3292600231706988 - 02/09/2026 às 15:45:25\n\n2926 0913 3988 1200 0189 6200 1000 0359 7210 3787 4279\n\nREFERÊNCIA (ANO/MÊS): 2026/09\n\nÁREA CONTRIBUINTE:\n\nVENCIMENTO: 02/09/2026\n\nTOTAL A PAGAR: R$ 558,40\n\nNº do Contrato: 8867\n\nITENS DA FATURA cblies | UN [QUANT] unas) | neo (rs) | acntRo) |rorates | Rei | Rojo | to. | remsqas\nOMEGA GUARAJUB A surres | 0100201 | UN | 1 111,68 0,00 0,00) 111,68 10,33] 76,27| 20.50 15,64\nconto de Telecomunicacoes Top | gggogg1 | UN | 1 446,72 0,00 0,00| 446,72 0,00 0.00 0.00 0.00\nVALOR TOTAL NE 558,40 | | INFORMAÇÃO DOS TRIBUTOS RESERVADO AO FISCO\nTOTAL BASE DE CÁLCULO 76,27 TRIBUTO VALOR\n\nPIS 1,84\nVALOR ICMS 1564) COFINS As\nVALOR ISENTO 0,00) [FUST 0,50\nVALOR OUTROS 0,00) | FUNTTEL 0,00\n\nINFORMAÇÕES COMPLEMENTARES\n\nID titulo referencia - 610976\n\nÁREA DO CONTRIBUINTE E DETERMINAÇÕES DA ANATEL\n\nLinha digitável\n00000.00000 00000.000000 00000.000000 O 00000000000000\n\nNº Identificador de débito automático\n\nAvisos Regulatórios\n\n1. Esta fatura é emitida conforme a Resolução ANATEL nº 765/2023.\n\n2. Você pode contestar valores cobrados sem custo e receber resposta em até 30 dias.\n\n3. Central de Atendimento do ISP (71) 4062-8609 e WhatsApp (71) 4062-8609.\n\n4. Central de Atendimento da ANATEL: 1331 (ligação gratuita).\n\n5. Fatura emitida com antecedência mínima de 5 dias do vencimento.\n\n6. Dados pessoais tratados conforme LGPD - Lei nº 13.709/2018.\n\n7. O não pagamento poderá acarretar suspensão do serviço, conforme regras da ANATEL.\n\nDireito de contestação da cobrança\n\nVocê pode contestar valores desta fatura sem custo.\n\nEntre em contato com nossa Central de Atendimento: Telefone (71) 4062-8609 e\nWhatsApp (71) 4062-8609, ou pelo e-mail: financeiroDffcomunicacoes.net.br.\n\nA análise será concluída em até 30 dias, conforme a regra da ANATEL.\nEnquanto sua contestação estiver em andamento, o serviço não será suspenso.\n\n'


def _converter(monkeypatch, tmp_path, texto):
    dummy = tmp_path / "dummy_telecom_35972.pdf"
    dummy.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: texto)
    notas = SPPdfExtractor(str(dummy)).parse_multiple()
    assert len(notas) == 1
    return notas[0]


@pytest.fixture
def nfse(monkeypatch, tmp_path):
    return _converter(monkeypatch, tmp_path, MOCK_OCR)


def test_fixture_reproduz_a_armadilha_do_texto_real():
    """Sem esta linha o teste não provaria nada: os 4 dígitos finais do
    telefone do tomador estão colados à chave, na mesma linha."""
    assert "99168-8997 2926 0913 3988 1200 0189 6200 1000 0359 7210 3787 4279" in MOCK_OCR
    # O CNPJ certo também está impresso, mas isso NÃO pode ser o que salva o
    # teste: a chave autoverificável é a fonte principal.
    assert "13.398.812/0001-89" in MOCK_OCR


def test_layout_detectado(tmp_path):
    dummy = tmp_path / "dummy_layout.pdf"
    dummy.write_bytes(b"%PDF-1.4")
    ex = SPPdfExtractor(str(dummy))
    ex.from_ocr = True
    ex._pagina_veio_de_ocr = True
    assert ex._detect_layout_page(MOCK_OCR) == LAYOUT_TELECOM_COMUNICACAO


def test_cnpj_do_prestador_vem_da_chave_nao_da_janela_deslocada(nfse):
    # Antes: "26091339881200" (AAMM + 10 dígitos do CNPJ; falha no DV).
    assert nfse.prestador.cnpj_cpf == CNPJ_PRESTADOR
    assert SPPdfExtractor._cnpj_valido(nfse.prestador.cnpj_cpf)
    assert not SPPdfExtractor._cnpj_valido("26091339881200")  # o valor antigo era inválido


def test_codigo_de_verificacao_e_a_chave_limpa_de_44_digitos(nfse):
    # Antes: "89972926091339881200018962001000035972103787".
    assert nfse.codigo_verificacao == CHAVE_REAL
    assert len(nfse.codigo_verificacao) == 44
    assert nfse.codigo_verificacao[6:20] == CNPJ_PRESTADOR
    assert nfse.codigo_verificacao[20:22] == "62"
    assert nfse.codigo_verificacao[25:34].lstrip("0") == nfse.numero


def test_demais_campos_preservados(nfse):
    assert nfse.numero == "35972"
    assert nfse.tomador.cnpj_cpf == "25311856000109"
    assert nfse.valores.valor_servicos == 558.40
    assert nfse.data_emissao.strftime("%d/%m/%Y") == "02/09/2026"
    assert not any("prestador" in a.lower() for a in nfse.avisos)


def test_chave_com_lixo_de_ocr_no_comeco_de_outro_formato(monkeypatch, tmp_path):
    """Mesma chave, lixo diferente na frente (dois grupos de 4 + 2 dígitos
    soltos da linha anterior): o resultado não pode depender do tamanho do
    lixo nem de ele ser múltiplo de 4 dígitos."""
    antigo = "99168-8997 2926 0913"
    novo = "99168-8997 55 1234 7788 2926 0913"
    assert antigo in MOCK_OCR
    nfse = _converter(monkeypatch, tmp_path, MOCK_OCR.replace(antigo, novo, 1))
    assert nfse.codigo_verificacao == CHAVE_REAL
    assert nfse.prestador.cnpj_cpf == CNPJ_PRESTADOR


def test_chave_com_um_digito_errado_usa_o_cnpj_impresso_validado(monkeypatch, tmp_path):
    """Um dígito do CNPJ dentro da chave trocado pelo OCR: o DV da chave e o
    do CNPJ não fecham, então a chave não vale como fonte do CNPJ - mas o CNPJ
    impresso no cabeçalho (13.398.812/0001-89, DV ok) vale."""
    quebrada = "2926 0913 3988 1200 0189 6200 1000 0359 7210 3787 4279".replace("3988", "3989")
    texto = MOCK_OCR.replace("2926 0913 3988 1200 0189 6200 1000 0359 7210 3787 4279", quebrada)
    nfse = _converter(monkeypatch, tmp_path, texto)
    assert nfse.prestador.cnpj_cpf == CNPJ_PRESTADOR
    # A chave lida tem um dígito errado e não é confirmável: sentinela do
    # layout (nunca a janela deslocada de 44 dígitos que o localizador antigo
    # devolvia - "89972926...3787").
    assert nfse.codigo_verificacao == "TELECOM"


def test_sem_chave_nem_cnpj_impresso_validos_vira_sentinela_com_aviso(monkeypatch, tmp_path):
    """Nada confirmável: o prestador NÃO pode sair com um CNPJ plausível porém
    errado (a janela deslocada de antes) - sentinela + aviso."""
    texto = MOCK_OCR.replace("13.398.812/0001-89", "13.398.812/0001-80")  # DV errado
    texto = re.sub(r"2926 0913 3988 1200 0189 6200 1000 0359 7210 3787 4279",
                   "8997 2926 0913 3988 1200 0189 6200 1000 0359 7210 3787", texto)  # só 40 dígitos da chave real
    nfse = _converter(monkeypatch, tmp_path, texto)
    assert nfse.prestador.cnpj_cpf == "00000000000000"
    assert nfse.prestador.cnpj_cpf != "26091339881200"
    assert nfse.codigo_verificacao == "TELECOM"
    assert any("prestador" in a.lower() for a in nfse.avisos)


class TestLocalizarChaveNfcom:
    def test_chave_limpa(self):
        assert SPPdfExtractor._localizar_chave_nfcom("CHAVE DE ACESSO: " + CHAVE_REAL) == (CHAVE_REAL, True)

    def test_chave_com_espacos_impressos(self):
        assert SPPdfExtractor._localizar_chave_nfcom(
            "x 2926 0913 3988 1200 0189 6200 1000 0359 7210 3787 4279 y")[0] == CHAVE_REAL

    def test_lixo_numerico_colado_na_frente(self):
        for lixo in ("8997 ", "8", "12345678 ", "8997\n"):
            assert SPPdfExtractor._localizar_chave_nfcom(lixo + CHAVE_REAL) == (CHAVE_REAL, True)

    def test_chave_quebrada_em_duas_linhas(self):
        quebrada = CHAVE_REAL[:20] + "\n" + CHAVE_REAL[20:]
        assert SPPdfExtractor._localizar_chave_nfcom(quebrada) == (CHAVE_REAL, True)

    def test_dv_errado_com_estrutura_integra_e_devolvida_como_nao_confirmada(self):
        errada = CHAVE_REAL[:43] + "0"  # DV (9) trocado; CNPJ, mês e modelo 62 íntegros
        assert SPPdfExtractor._localizar_chave_nfcom(errada) == (errada, False)

    def test_janela_deslocada_nao_e_aceita(self):
        # 40 dígitos da chave + 4 do telefone na frente: nenhuma janela de 44 fecha.
        assert SPPdfExtractor._localizar_chave_nfcom("8997" + CHAVE_REAL[:40]) is None

    def test_numeros_quaisquer_nao_viram_chave(self):
        assert SPPdfExtractor._localizar_chave_nfcom("0" * 44) is None
        assert SPPdfExtractor._localizar_chave_nfcom("(71) 4062-8609 42839852 2026/09") is None
        assert SPPdfExtractor._localizar_chave_nfcom("") is None
