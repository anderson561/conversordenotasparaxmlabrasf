# -*- coding: utf-8 -*-
r"""NFCom / NF-e de Serviço de Comunicação (`telecom_comunicacao`) - defeitos
que sobraram na nota nº 35972 do Grupo F&F depois da correção do CNPJ/chave
(pág. 4 do lote `Notas_Fiscais_Recebidas_09.2026_-_Guarajuba_Suites.pdf`).

Cada item abaixo foi conferido contra a IMAGEM da página (cabeçalho do
emitente, bloco do destinatário e tabela de itens renderizados a 3x):

1. RazaoSocial do prestador = "GRUPO" (truncada). "GRUPO" é o letreiro do
   LOGOTIPO, uma linha própria do OCR antes do nome; o nome impresso do
   emitente é "Grupo FeF", na linha logo acima do endereço.
2. Endereço do prestador numa linha só e "Numero" = "5 (71) 4062-8609": o
   endereço impresso é "Rua Senhor do Bonfim 544 Monte Gordo 42839852
   Camacari - BA" (SEM vírgulas) e o regex antigo atravessava a quebra de linha.
3. CodigoMunicipio do prestador = 2927408 (Salvador) com endereço em Camaçari,
   e NENHUM aviso: o município saía como a linha de endereço inteira (com
   dígitos), o resolvedor não a tratava como nome e caía na capital em silêncio.
4. Discriminacao com tributos, "RESERVADO AO FISCO", avisos da ANATEL e telefone
   (a regex ia até o 1º "TOTAL A PAGAR" depois do cabeçalho, que na cópia de
   zoom alto vem ANTES da tabela). A tabela impressa tem 2 itens: "INTERNET
   COLETIVA _400MEGA_GUARAJUBA_SUITES" e "Servico de Telecomunicacoes Top Full".
5. Sem aviso de que o documento é tributado por ICMS (os demais layouts NFCom
   já o recebiam).
6. Tomador "Não informado"/"S/N" - o impresso é "GUARAJUBA 0 Guarajuba 42840310"
   / "Camacari - BA".

`MOCK_OCR` (importado do teste do CNPJ) é o texto REAL de produção da pág. 4.
"""
import re

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor
from test_telecom_chave_colada_ao_telefone_guarajuba_suites_35972 import MOCK_OCR

SENTINELA_DISCRIMINACAO = 'Serviços de telecomunicação conforme nota fiscal.'
ENDERECO_PRESTADOR = "Rua Senhor do Bonfim 544 Monte Gordo 42839852 Camacari - BA"


def _converter(monkeypatch, tmp_path, texto):
    dummy = tmp_path / "dummy_telecom_35972_b.pdf"
    dummy.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: texto)
    notas = SPPdfExtractor(str(dummy)).parse_multiple()
    assert len(notas) == 1
    return notas[0]


@pytest.fixture
def nfse(monkeypatch, tmp_path):
    return _converter(monkeypatch, tmp_path, MOCK_OCR)


def test_fixture_reproduz_as_armadilhas_do_texto_real():
    # Letreiro do logotipo ANTES do nome, ruído de logotipo colado na frente
    # do nome nas 2 cópias (diferente em cada uma) e endereço sem vírgulas.
    assert "GRUPO |\n\ncm\" à Grupo FeF\nRua Senhor" in MOCK_OCR
    assert "GRUPO\no 4 Grupo FeF\nRua Senhor" in MOCK_OCR
    assert ENDERECO_PRESTADOR + "\n5 (71) 4062-8609" in MOCK_OCR
    # "TOTAL A PAGAR" vem ANTES da tabela na 1ª cópia (zoom alto).
    assert MOCK_OCR.index("TOTAL A PAGAR") < MOCK_OCR.index("ITENS DA FATURA")


# --- item 1: razão social do prestador ---------------------------------------

def test_razao_social_e_o_nome_impresso_nao_o_letreiro_do_logotipo(nfse):
    # Antes: "GRUPO".
    assert nfse.prestador.razao_social == "Grupo FeF"


def test_razao_social_sem_ruido_de_logotipo_quando_so_ha_uma_copia(monkeypatch, tmp_path):
    # Só a 1ª cópia (com 'cm" à ' colado na frente): nada para tirar o ruído
    # por concordância - sai como o OCR leu, mas NUNCA o letreiro "GRUPO".
    um_titulo = MOCK_OCR[: MOCK_OCR.index("\n\n\nDOCUMENTO AUXILIAR")]
    nota = _converter(monkeypatch, tmp_path, um_titulo)
    assert nota.prestador.razao_social.endswith("Grupo FeF")
    assert nota.prestador.razao_social != "GRUPO"


def test_razao_social_nome_limpo_e_ruido_diferente_em_cada_copia_concordam(monkeypatch, tmp_path):
    texto = MOCK_OCR.replace('cm" à Grupo FeF', "Grupo FeF").replace("o 4 Grupo FeF", "; Grupo FeF .")
    nota = _converter(monkeypatch, tmp_path, texto)
    assert nota.prestador.razao_social == "Grupo FeF"


def test_razao_social_ilegivel_vira_sentinela_com_aviso(monkeypatch, tmp_path):
    # Nenhuma linha de nome entre o título e o endereço (nem o letreiro).
    texto = MOCK_OCR.replace("GRUPO |\n\ncm\" à Grupo FeF\n", "").replace("GRUPO\no 4 Grupo FeF\n", "")
    nota = _converter(monkeypatch, tmp_path, texto)
    assert nota.prestador.razao_social == "Prestador de Telecomunicação"
    assert nota.prestador.razao_social not in ("GRUPO", "Grupo")
    assert any("razão social do prestador" in a.lower() for a in nota.avisos)
    # O endereço continua lido: a razão social ruim não derruba o resto.
    assert nota.prestador.endereco.logradouro == "Rua Senhor do Bonfim"


def test_razao_social_confiavel_nao_gera_aviso(nfse):
    assert not any("razão social do prestador" in a.lower() for a in nfse.avisos)


# --- item 2: endereço do prestador --------------------------------------------

def test_endereco_do_prestador_separado_em_campos(nfse):
    e = nfse.prestador.endereco
    # Antes: logradouro = a linha inteira; numero = "5 (71) 4062-8609"; bairro "Não informado".
    assert e.logradouro == "Rua Senhor do Bonfim"
    assert e.numero == "544"
    assert e.bairro == "Monte Gordo"
    assert e.cep == "42839852"
    assert e.municipio == "Camacari"
    assert e.uf == "BA"
    assert "(71)" not in e.numero and "4062" not in e.numero


def test_endereco_do_prestador_com_virgulas_continua_lido(monkeypatch, tmp_path):
    texto = MOCK_OCR.replace(ENDERECO_PRESTADOR, "Rua Senhor do Bonfim, 544, Monte Gordo, 42839-852 Camacari - BA")
    e = _converter(monkeypatch, tmp_path, texto).prestador.endereco
    assert (e.logradouro, e.numero, e.bairro, e.cep) == ("Rua Senhor do Bonfim", "544", "Monte Gordo", "42839852")


def test_endereco_do_prestador_sem_cep_nao_inventa_campos_nem_pega_o_do_tomador(monkeypatch, tmp_path):
    # Sem o CEP a estrutura "logradouro número bairro CEP" não fecha: nada de
    # número "5 (71) 4062-8609" nem, pior, o CEP do TOMADOR (42840310) no lugar.
    texto = MOCK_OCR.replace("42839852 ", "")
    e = _converter(monkeypatch, tmp_path, texto).prestador.endereco
    assert e.logradouro == "Não informado"
    assert e.numero == "S/N"
    assert e.cep == "00000000"
    assert "(71)" not in e.numero


# --- item 3: município / código IBGE do prestador ---------------------------------

def test_municipio_do_prestador_e_camacari_nao_a_capital(nfse):
    e = nfse.prestador.endereco
    # Antes: 2927408 (Salvador) e município = a linha de endereço inteira.
    assert e.municipio == "Camacari"
    assert e.codigo_municipio == "2905701"
    assert not any("Município" in a and "fallback" in a for a in nfse.avisos)


def test_municipio_fora_da_tabela_gera_aviso_em_vez_de_cair_na_capital_em_silencio(monkeypatch, tmp_path):
    texto = MOCK_OCR.replace("42839852 Camacari - BA", "42839852 Narnia - BA")
    nota = _converter(monkeypatch, tmp_path, texto)
    e = nota.prestador.endereco
    assert e.municipio == "Narnia"
    assert e.codigo_municipio == "2927408"          # capital da UF: valor NÃO confiável...
    avisos = [a for a in nota.avisos if "Narnia" in a]
    assert avisos and "prestador" in avisos[0]       # ...e agora o usuário é avisado
    # O tomador (Camaçari, na tabela) não é afetado.
    assert nota.tomador.endereco.codigo_municipio == "2905701"


def test_municipio_lido_com_ocr_diferente_em_cada_copia_usa_a_cópia_conhecida(monkeypatch, tmp_path):
    # 1ª cópia "Camacarl" (l no lugar do i), 2ª "Camacari": o resultado é o
    # município que o conversor conhece, sem aviso.
    primeira = MOCK_OCR.index(ENDERECO_PRESTADOR)
    texto = MOCK_OCR[:primeira] + ENDERECO_PRESTADOR.replace("Camacari", "Camacarl") + MOCK_OCR[primeira + len(ENDERECO_PRESTADOR):]
    nota = _converter(monkeypatch, tmp_path, texto)
    assert nota.prestador.endereco.municipio == "Camacari"
    assert nota.prestador.endereco.codigo_municipio == "2905701"
    assert not any("não consta na tabela" in a for a in nota.avisos)


def test_municipio_ilegivel_nas_duas_copias_gera_aviso(monkeypatch, tmp_path):
    texto = MOCK_OCR.replace("42839852 Camacari - BA", "42839852 Camacarl - BA")
    nota = _converter(monkeypatch, tmp_path, texto)
    assert nota.prestador.endereco.codigo_municipio == "2927408"
    assert any("Camacarl" in a and "prestador" in a for a in nota.avisos)


# --- item 4: discriminação -------------------------------------------------------

def test_discriminacao_so_tem_os_itens_da_fatura(nfse):
    d = nfse.discriminacao
    assert d.startswith("INTERNET COLETIVA")
    assert "Telecomunicacoes Top" in d
    for lixo in ("RESERVADO", "FISCO", "ANATEL", "TRIBUTO", "4062-8609", "TOTAL A PAGAR",
                 "VALOR TOTAL", "Linha digit", "LGPD", "558,40", "111,68"):
        assert lixo not in d, lixo
    assert len(d) < 120


def test_discriminacao_sem_itens_legiveis_vira_a_frase_padrao(monkeypatch, tmp_path):
    # Esvazia a tabela (as 2 cópias) mantendo cabeçalho e rodapé.
    texto = re.sub(r"(ITENS DA FATURA[^\n]*\n)(.*?)(VALOR TOTAL N)", r"\1\n\3", MOCK_OCR, flags=re.S)
    assert "INTERNET COLETIVA" not in texto
    nota = _converter(monkeypatch, tmp_path, texto)
    assert nota.discriminacao == SENTINELA_DISCRIMINACAO


def test_discriminacao_sem_fim_de_tabela_nao_despeja_o_resto_do_documento(monkeypatch, tmp_path):
    # Sem NENHUM marcador de fim da tabela, o antigo regex ia até o fim do texto.
    texto = MOCK_OCR.replace("VALOR TOTAL NF", "xx").replace("VALOR TOTAL NE", "xx")
    texto = re.sub(r"TOTAL BASE DE CÁLCULO|RESERVADO AO FISCO|INFORMAÇÃO DOS TRIBUTOS|INFORMAÇÕES COMPLEMENTARES", "yy", texto)
    nota = _converter(monkeypatch, tmp_path, texto)
    assert "ANATEL" not in nota.discriminacao
    assert "4062-8609" not in nota.discriminacao


class TestDiscriminacaoTelecom:
    def test_ignora_colunas_numericas_e_cabecalho_quebrado(self):
        t = ("ITENS DA FATURA cClass | UN | QUANT\nVALOR\nTOTAL (R$)| (R$)\n"
             "FeF ULTRA 120 MEGA 0100201 | UN | 1 23,98 0,00\n"
             "Servico de Telecomunicacoes Top | 0600601 | UN | 1 95,92\n"
             "VALOR TOTAL NF 119,90\nRESERVADO AO FISCO\nAvisos Regulatórios")
        assert SPPdfExtractor._discriminacao_telecom(t) == "FeF ULTRA 120 MEGA | Servico de Telecomunicacoes Top"

    def test_linha_de_ruido_de_ocr_fica_de_fora(self):
        t = ("ITENS DA FATURA\nFeF ULTRA 120 MEGA\n"
             'coma tas + im ve tm em rasarmeamarmrmam mem me "e ven enem\n'
             "VALOR TOTAL NF 119,90")
        assert SPPdfExtractor._discriminacao_telecom(t) == "FeF ULTRA 120 MEGA"

    def test_sem_marcador_de_fim_devolve_vazio(self):
        assert SPPdfExtractor._discriminacao_telecom("ITENS DA FATURA\nINTERNET\nlixo qualquer") == ""

    def test_rotulo_de_fim_garbled_pelo_ocr_ainda_encerra(self):
        t = "ITENS DA FATURA x\nINTERNET COLETIVA | 0100201\n(vaLORTOTALNE o 558,40)\nResto do texto"
        assert SPPdfExtractor._discriminacao_telecom(t) == "INTERNET COLETIVA"


# --- item 5: aviso de ICMS ---------------------------------------------------------------

def test_aviso_de_documento_tributado_por_icms(nfse):
    avisos = [a for a in nfse.avisos if "ICMS" in a]
    assert len(avisos) == 1
    assert avisos[0].startswith("Documento tributado por ICMS (NFCom")
    assert "não sujeito a ISS" in avisos[0]
    # ICMS NÃO é mapeado para o ISS do ABRASF.
    assert nfse.valores.valor_iss == 0.0


def test_valor_dos_servicos_intacto(nfse):
    assert nfse.valores.valor_servicos == 558.40
    assert nfse.valores.valor_liquido_nfse == 558.40


# --- item 6: endereço do tomador -----------------------------------------------------------

def test_endereco_do_tomador_extraido_do_bloco_do_destinatario(nfse):
    e = nfse.tomador.endereco
    # Antes: "Não informado" / "S/N" / "Não informado" (só o CEP saía).
    assert e.logradouro == "GUARAJUBA"
    assert e.numero == "0"
    assert e.bairro == "Guarajuba"
    assert e.cep == "42840310"
    assert e.municipio == "Camacari"
    assert e.uf == "BA"
    assert e.codigo_municipio == "2905701"
    # Nada do emitente (Bonfim/Monte Gordo/CEP 42839852) nem do rodapé.
    assert "Bonfim" not in e.logradouro and e.bairro != "Monte Gordo" and e.cep != "42839852"
    assert nfse.tomador.razao_social == "Boutique Guarajuba PH Gestao"
    assert nfse.tomador.cnpj_cpf == "25311856000109"


def test_endereco_do_tomador_degradado_fica_nao_informado_sem_inventar(monkeypatch, tmp_path):
    # CEP do destinatário perdido pelo OCR: a linha não tem mais a estrutura.
    texto = MOCK_OCR.replace("GUARAJUBA 0 Guarajuba 42840310", "GUARAJUBA 0 Guarajuba")
    e = _converter(monkeypatch, tmp_path, texto).tomador.endereco
    assert (e.logradouro, e.numero, e.bairro) == ("Não informado", "S/N", "Não informado")
    assert e.cep == "00000000"
    assert "Bonfim" not in e.logradouro and "Monte Gordo" not in e.bairro
    assert e.municipio == "Camacari"


def test_endereco_do_tomador_com_zero_lido_como_letra_o(monkeypatch, tmp_path):
    # A 1ª cópia (zoom alto) lê o "0" do número como a letra "O".
    texto = MOCK_OCR.replace("GUARAJUBA 0 Guarajuba 42840310", "GUARAJUBA O Guarajuba 42840310")
    e = _converter(monkeypatch, tmp_path, texto).tomador.endereco
    assert (e.logradouro, e.numero, e.bairro, e.cep) == ("GUARAJUBA", "0", "Guarajuba", "42840310")


class TestParseEnderecoTelecom:
    def test_prestador_sem_virgulas(self):
        r = SPPdfExtractor._parse_endereco_telecom(ENDERECO_PRESTADOR, prestador=True)
        assert r == {'logradouro': 'Rua Senhor do Bonfim', 'numero': '544', 'bairro': 'Monte Gordo',
                     'cep': '42839852', 'municipio': 'Camacari', 'uf': 'BA'}

    def test_logradouro_com_numero_no_nome(self):
        r = SPPdfExtractor._parse_endereco_telecom("Rua 7 de Setembro 123 Centro 40000-000 Salvador - BA", prestador=True)
        assert (r['logradouro'], r['numero'], r['bairro'], r['cep']) == ("Rua 7 de Setembro", "123", "Centro", "40000000")

    def test_nao_confunde_avisos_com_avenida(self):
        assert SPPdfExtractor._parse_endereco_telecom("Avisos Regulatórios 12 Centro 40000000", prestador=True) is None

    def test_linha_sem_cep_nao_e_endereco(self):
        assert SPPdfExtractor._parse_endereco_telecom("Rua Senhor do Bonfim 544 Monte Gordo", prestador=True) is None
        assert SPPdfExtractor._parse_endereco_telecom("5 (71) 4062-8609", prestador=True) is None

    def test_tomador_sem_tipo_de_logradouro(self):
        r = SPPdfExtractor._parse_endereco_telecom("GUARAJUBA 0 Guarajuba 42840310", prestador=False)
        assert (r['logradouro'], r['numero'], r['bairro'], r['cep']) == ("GUARAJUBA", "0", "Guarajuba", "42840310")

    def test_sem_numero_impresso(self):
        r = SPPdfExtractor._parse_endereco_telecom("Rua das Flores S/N Centro 40000000", prestador=True)
        assert r['numero'] == 'S/N'


class TestConsensoNomeEmitente:
    def test_sufixo_em_comum_remove_ruido_de_logotipo_diferente(self):
        assert SPPdfExtractor._consenso_nome_emitente_telecom(['cm" à Grupo FeF', "o Grupo FeF"]) == "Grupo FeF"

    def test_uma_leitura_so_vale_como_esta(self):
        assert SPPdfExtractor._consenso_nome_emitente_telecom(["Grupo FeF"]) == "Grupo FeF"

    def test_sem_leitura_devolve_vazio(self):
        assert SPPdfExtractor._consenso_nome_emitente_telecom([]) == ""
        assert SPPdfExtractor._consenso_nome_emitente_telecom(["", ""]) == ""

    def test_sem_concordancia_vale_a_primeira_leitura(self):
        assert SPPdfExtractor._consenso_nome_emitente_telecom(["Alfa Beta", "Gama Delta"]) == "Alfa Beta"

    def test_limpeza_de_pontas(self):
        limpar = SPPdfExtractor._limpar_nome_emitente_telecom
        assert limpar("; Grupo FeF .") == "Grupo FeF"
        assert limpar("| » 4 Grupo F&F LTDA.") == "Grupo F&F LTDA"
        assert limpar("| » 4") == ""
