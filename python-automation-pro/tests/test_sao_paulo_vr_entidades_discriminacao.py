# -*- coding: utf-8 -*-
r"""São Paulo/SP - notas da VR BENEFICIOS E SERVICOS DE PROCESSAMENTO (CNPJ
02.535.864/0001-33) para VERDE FLORICULTURA LTDA (achado real 2026-11-18):
NF 101217349 (escaneada, OCR) e NF 102003139 (digital, pdfminer). Os textos
são os REAIS de `test_sao_paulo_valor_recebido_qualquer_prestador.py`.

1. Tomador da 102003139: o pdfminer põe "VERDE FLORICULTURA LTDA" antes do
   cabeçalho "TOMADOR DE SERVIÇOS" e o endereço do tomador (Salvador) sai SEM
   CEP; o refinamento do bloco exigia o âncora "- CEP:" e o genérico usava a
   linha de endereço como razão social (endereço "Não informado"). Agora a
   linha "<logradouro> <número>[, ...] - <bairro>" logo após o CNPJ formatado
   do bloco também é âncora (CEP não inventado) e a razão igual à linha de
   endereço é tratada como suspeita.
2. Intermediário fantasma da 102003139 (CNPJ 00000000000100, razão "Vencimento
   em"): o "CPF/CNPJ: ----" sai ANTES do cabeçalho "INTERMEDIÁRIO DE
   SERVIÇOS"; no layout São Paulo, sem CPF/CNPJ com DV válido no bloco, não há
   intermediário.
3. Endereço do prestador impresso "AV DOS BANDEIRANTES 460 460 - ...": número
   repetido idêntico = um número só (logradouro "AV DOS BANDEIRANTES", número
   "460") nas duas notas.
4. Discriminação: o quadro termina em "VALOR TOTAL DO SERVIÇO" (o bloco de
   valores/retenções não entra), a 1ª linha deslocada pelo pdfminer volta para
   o início e o cabeçalho "INTERMEDIÁRIO DE SERVIÇOS" sai do texto; no
   escaneado a linha impressa "Trib aprox. Lei nº 12.741/12: ..." fica.
"""
import xml.etree.ElementTree as ET

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor
from src.models.nfse_models import Endereco, Entidade
from src.transformers.abrasf_transformer import Abrasf201Transformer
from tests.test_sao_paulo_pluxee_recebido_servico_zero import NOTA_PLUXEE_08969996
from tests.test_sao_paulo_valor_recebido_qualquer_prestador import (
    NOTA_VR_101217349_OCR, NOTA_VR_102003139, _digital, _ocr, _trocar)

DISC_1800 = (
    "Total de Crédito VR Multi - VR+VA Auxílio: R$ 1.800,00 - (3 cartão(ões)) Vencimento em "
    "02/11/2026 Trib aprox. Lei nº 12.741/12: R$0,00 Federal, R$0,00 Municipal e R$0,00 pelos "
    "serviços Fonte: IBPT/empresometro.com.br C44399 26.2.B Valor da corretagem ou comissão: zero "
    "Número do protocolo do pedido: 20261102001231 REALIZE O PAGAMENTO APENAS DE BOLETOS EMITIDOS "
    "POR VOCÊ NA ÁREA LOGADA E SEGURA DO SEU PORTAL RH. PREVINA-SE E EVITE PREJUÍZOS FINANCEIROS.")
DISC_2300 = (DISC_1800.replace("1.800,00 - (3", "2.300,00 - (4").replace("02/11/2026", "05/10/2026")
             .replace("20261102001231", "20261005005214"))

AMBAS = pytest.mark.parametrize("parse", [_ocr, _digital], ids=["101217349_scan", "102003139_digital"])


def _xml(nota):
    return ET.fromstring(Abrasf201Transformer().transform(nota))


# --- 1. tomador ------------------------------------------------------------

@AMBAS
def test_tomador_igual_nas_duas_notas(monkeypatch, tmp_path, parse):
    t = parse(monkeypatch, tmp_path).tomador
    assert t.cnpj_cpf == "13502158000101"
    assert t.razao_social == "VERDE FLORICULTURA LTDA"
    e = t.endereco
    assert (e.logradouro, e.numero, e.complemento, e.bairro) == (
        "AVENIDA TANCREDO NEVES", "148", e.complemento, "CAMINHO DAS ARVORES")
    assert " ".join((e.complemento or "").split()) == "SHOP. C. IGUATEMI TERR"
    assert (e.uf, e.codigo_municipio) == ("BA", "2927408")
    assert set(e.cep.replace("-", "")) == {"0"}       # CEP não impresso: não inventado


@AMBAS
def test_tomador_no_xml(monkeypatch, tmp_path, parse):
    tom = _xml(parse(monkeypatch, tmp_path)).find(".//Tomador")
    assert tom.find("RazaoSocial").text == "VERDE FLORICULTURA LTDA"
    assert {c: tom.find(f"Endereco/{c}").text for c in ("Endereco", "Numero", "Bairro", "CodigoMunicipio", "Uf", "Cep")} == {
        "Endereco": "AVENIDA TANCREDO NEVES", "Numero": "148", "Bairro": "CAMINHO DAS ARVORES",
        "CodigoMunicipio": "2927408", "Uf": "BA", "Cep": "00000000"}


def test_endereco_sem_cep_so_vale_logo_apos_o_cnpj():
    ext = SPPdfExtractor.__new__(SPPdfExtractor)
    bloco = "CPF/CNPJ:\n13.502.158/0001-01\n\nAV X 148, SALA 2 - CENTRO\nSalvador\n"
    assert ext._sp_ler_bloco_entidade(bloco)["endereco"] == ("AV X", "148", "SALA 2", "CENTRO", None)
    # longe do CNPJ: não é âncora
    assert ext._sp_ler_bloco_entidade("CPF/CNPJ:\n13.502.158/0001-01\nSalvador\nAV X 148, SALA 2 - CENTRO\n") is None
    # sem número lido: não é âncora (nada de S/N adivinhado)
    assert ext._sp_ler_bloco_entidade("13.502.158/0001-01\nAV X - CENTRO\n") is None


# --- 2. intermediário ------------------------------------------------------

@AMBAS
def test_sem_intermediario(monkeypatch, tmp_path, parse):
    nota = parse(monkeypatch, tmp_path)
    assert nota.intermediario is None
    assert _xml(nota).find(".//Intermediario") is None


def test_intermediario_com_cnpj_valido_continua_lido(monkeypatch, tmp_path):
    texto = _trocar(NOTA_VR_101217349_OCR, "CPF/CNPJ: ---- Nomey/Razão Social: ----",
                    "CPF/CNPJ: 11.222.333/0001-81 Nome/Razão Social: INTERMEDIARIA EXEMPLO LTDA")
    nota = _ocr(monkeypatch, tmp_path, texto)
    assert nota.intermediario is not None
    assert nota.intermediario.cnpj_cpf == "11222333000181"


def test_intermediario_com_cnpj_de_dv_invalido_nao_e_aceito(monkeypatch, tmp_path):
    texto = _trocar(NOTA_VR_101217349_OCR, "CPF/CNPJ: ---- Nomey/Razão Social: ----",
                    "CPF/CNPJ: 11.222.333/0001-82 Nome/Razão Social: INTERMEDIARIA EXEMPLO LTDA")
    assert _ocr(monkeypatch, tmp_path, texto).intermediario is None


# --- 3. número repetido no endereço do prestador ---------------------------

@AMBAS
def test_prestador_numero_repetido_vira_um_so(monkeypatch, tmp_path, parse):
    nota = parse(monkeypatch, tmp_path)
    e = nota.prestador.endereco
    assert (e.logradouro, e.numero, e.bairro, e.cep) == ("AV DOS BANDEIRANTES", "460", "BROOKLIN PAULISTA", "04553900")
    end = _xml(nota).find(".//PrestadorServico/Endereco")
    assert (end.find("Endereco").text, end.find("Numero").text) == ("AV DOS BANDEIRANTES", "460")


def _ent(logradouro, numero):
    return Entidade(cnpj_cpf="02535864000133", razao_social="X", endereco=Endereco(
        logradouro=logradouro, numero=numero, bairro="B", codigo_municipio="3550308", uf="SP", cep="04553900"))


@pytest.mark.parametrize("logradouro,numero,esperado", [
    ("AV DOS BANDEIRANTES 460 460", "S/N", ("AV DOS BANDEIRANTES", "460")),
    ("AV DOS BANDEIRANTES 460", "460", ("AV DOS BANDEIRANTES", "460")),
    ("AV DOS BANDEIRANTES 460 460", "460", ("AV DOS BANDEIRANTES", "460")),
    ("AV DOS BANDEIRANTES 460 470", "S/N", ("AV DOS BANDEIRANTES 460 470", "S/N")),   # diferentes: nada muda
    ("AV DOS BANDEIRANTES 460 460", "12", ("AV DOS BANDEIRANTES 460 460", "12")),     # outro nº lido: nada muda
    ("RUA 15", "15", ("RUA 15", "15")),                                                # sobraria só o tipo
    ("AV DOS BANDEIRANTES", "460", ("AV DOS BANDEIRANTES", "460")),
])
def test_numero_repetido_unidade(logradouro, numero, esperado):
    e = SPPdfExtractor._sp_numero_repetido(_ent(logradouro, numero)).endereco
    assert (e.logradouro, e.numero) == esperado


# --- 4. discriminação ------------------------------------------------------

def test_discriminacao_digital(monkeypatch, tmp_path):
    nota = _digital(monkeypatch, tmp_path)
    assert nota.discriminacao == DISC_1800
    assert _xml(nota).find(".//Servico/Discriminacao").text == DISC_1800


def test_discriminacao_escaneada_mesma_estrutura(monkeypatch, tmp_path):
    assert _ocr(monkeypatch, tmp_path).discriminacao == DISC_2300


def test_discriminacao_pluxee_sem_bloco_de_valores(monkeypatch, tmp_path):
    d = _digital(monkeypatch, tmp_path, NOTA_PLUXEE_08969996).discriminacao
    assert d == ("41 ALIMENTAÇÃO EMV 9867.48 GESTAO COBRANCA 0.00 \\ TX EMISSAO CARTAO 0.00 "
                 "IRRF RECOLHIMENTO EFETUADO PELO EMITENTE CONF. IN/SRF 153/87 R$0.00 "
                 "SERVIÇO ENQUADRADO COMO ADMINISTRAÇÃO DE CONVÊNIO Entr/Cred 02/10/2026 "
                 "Nro Pedido.: 43768713/26")


def test_discriminacao_sem_deslocamento_nao_puxa_texto_de_fora(monkeypatch, tmp_path):
    """Com o cabeçalho do intermediário ANTES do quadro (ordem normal) nada
    de fora do quadro é puxado para o início."""
    texto = _trocar(NOTA_VR_102003139,
                    "Total de Crédito VR Multi - VR+VA Auxílio: R$ 1.800,00 - (3 cartão(ões))\n\n"
                    "DISCRIMINAÇÃO DE SERVIÇOS\n\nINTERMEDIÁRIO DE SERVIÇOS\n\n",
                    "INTERMEDIÁRIO DE SERVIÇOS\n\nDISCRIMINAÇÃO DE SERVIÇOS\n\n")
    d = _digital(monkeypatch, tmp_path, texto).discriminacao
    assert d == DISC_1800.replace(
        "Total de Crédito VR Multi - VR+VA Auxílio: R$ 1.800,00 - (3 cartão(ões)) ", "")
