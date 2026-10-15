# -*- coding: utf-8 -*-
r"""São Paulo/SP (LAYOUT_SAO_PAULO digital / LAYOUT_SAO_PAULO_2 escaneado) -
regra de negócio do prestador FLASH TECNOLOGIA E INSTITUICAO DE PAGAMENTO
LTDA (CNPJ 32.223.020/0001-18): quando o "VALOR TOTAL DO SERVIÇO" é impresso
como R$ 0,00, usar o "VALOR TOTAL RECEBIDO" como `ValorServicos`.

Decisão do USUÁRIO (2026-10-15), não achado de bug de extração: a nota de
"Compra de Créditos na Plataforma Flash" imprime
    VALOR TOTAL DO SERVIÇO = R$ 0,00
    VALOR TOTAL RECEBIDO   = R$ 1.113,00
(só o "serviço Flash" é tributável pelo ISS e vale zero; o resto é compra de
benefícios - Auxílio Alimentação/Mobilidade). Antes, o XML saía com
ValorServicos = ValorLiquidoNfse = 0,00. Os textos abaixo são o retorno REAL e
verbatim de `pdfminer.high_level.extract_text()` nos PDFs reais do usuário
("FLASH BENEFICIO - CR406 30.09.pdf", nota 05710445, e "FLASH BENEFICO GERAL
30.09.pdf", nota 05710815), já com o `\x0c` que separa as 2 páginas (a 2ª é o
anexo IBS/CBS).

Escopo ESTREITO: só prestador Flash, só com o zero IMPRESSO e o valor
recebido legível. Base de Cálculo/Alíquota/ISS/retenções ficam como o
documento imprime; só o líquido acompanha. Sem valor recebido confiável:
0,00 + aviso, nada é inventado. No scan (OCR) o recebido só vale se
confirmado pelo "Valor Total - R$ X" da discriminação."""
import os
import xml.etree.ElementTree as ET

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_SAO_PAULO, LAYOUT_SAO_PAULO_2
from src.models.nfse_models import Endereco, Entidade, Valores
from src.transformers.abrasf_transformer import Abrasf201Transformer

NOTA_FLASH_05710445 = 'PREFEITURA DO MUNICÍPIO DE SÃO PAULO\nSECRETARIA MUNICIPAL DA FAZENDA\n\nNOTA FISCAL ELETRÔNICA DE SERVIÇOS - NFS-e\nRPS Nº 4159843 Série NFSE2, emitido em 30/09/2026\n\nNúmero da Nota\n\n05710445\nData e Hora de Emissão\n02/10/2026 04:25:42\nCódigo de Verificação\nGZCS-2BDP\n\nIdentificador Nacional: 35503081232223020000118000000571044526101399600678\n\n20261002u32223020000118\n\nPRESTADOR DE SERVIÇOS\n\nInscrição Municipal:\n\n6.141.672-0\n\n32.223.020/0001-18\n\nCPF/CNPJ:\nNome/Razão Social:\nEndereço:\nMunicípio: São Paulo\n\nFLASH TECNOLOGIA E  INSTITUICAO DE PAGAMENTO LTDA\n\nR EUGENIO DE MEDEIROS 242, ANDAR 4 - PINHEIROS - CEP: 05425-000\nUF: SP\n\nTOMADOR DE SERVIÇOS\nTEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDA\n\nNome/Razão Social:\nCPF/CNPJ:\nEndereço:\nMunicípio:\n\n07.345.543/0001-90\n\nR T R TERRITORIO DO AMAPA 146, Casa 2 - PITUBA - CEP: 41830-540\nSalvador\n\nE-mail:\n\nUF:\n\nBA\n\nfinanceiro@temis-es.com.br\n\nInscrição Municipal:\n\n----\n\nCPF/CNPJ:\n\n----\n\nNome/Razão Social:\n\n----\n\nINTERMEDIÁRIO DE SERVIÇOS\n\nDISCRIMINAÇÃO DE SERVIÇOS\n\nValor Total - R$ 1.113,00\nCompra de Créditos na Plataforma Flash - R$ 1.113,00\nValor total de serviços Flash - R$ 0,00\nData da Compra: 30/09/2026\n\nCompra de benefícios - Auxilio Alimentação e Refeição: R$ 877,00 (1 depósito)\nCompra de benefícios - Auxilio Mobilidade: R$ 236,00 (1 depósito)\n\nContrato 5y6p1Uko4RlaWv1h0qrTg\n\nAutorização de Regime especial - SEI 6017.2019/0041453-7\nO ISS incide apenas sobre o valor de serviços Flash indicado acima\nLocal da prestação de serviços: São Paulo - SP\n\nVALOR TOTAL DO SERVIÇO = R$ 0,00\nVALOR TOTAL RECEBIDO = R$ 1.113,00\n\nContribuição Previdenciária - Retida (R$)\n\nIRRF (R$)\n\nCOFINS (R$)\n\nPIS/PASEP (R$)\n\nIPI (R$)\n\nContribuições Sociais - Retidas (R$)\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\nDescrição Contribuições Sociais - Retidas\n\n0 - PIS/COFINS/CSLL Não Retidos.\n\nCódigo do Serviço\n03205 - Fornecimento e administração de vales-refeição, vales-alimentação, vales-transporte e similares\n\nValor Total das Deduções (R$)\n0,00\n\nMunicípio de Prestação do Serviço\n-\n\n0,00\n\n2,00%\n\nNúmero Inscrição da Obra\n-\n\nBase de Cálculo (R$)\n\nAlíquota (%)\n\nValor do ISS (R$)\n\nCrédito Programa da NFP (R$)\n0,00\n\n0,00\n\nValor Aproximado dos Tributos / Fonte\n-\n\nOUTRAS INFORMAÇÕES\n(1) Esta NFS-e foi emitida com respaldo na Lei nº 14.097/2005; (2) Esta NFS-e substitui o RPS Nº 4159843 Série NFSE2, emitido em 30/09/2026; (3) O\nISS relativo a esta NFS-e deverá ser recolhido de acordo com as regras da DES-IF, mediante o envio da declaração e a posterior emissão da respectiva\nguia de pagamento por meio do sistema da DES-IF.;\n\nPágina 1 de 2\n\n\x0cIMPOSTO E CONTRIBUIÇÃO SOBRE BENS E SERVIÇOS (IBS E CBS)\nIdentificador: 35503081232223020000118000000571044526101399600678\n\nCPF/CNPJ/NIF do Fornecedor\n32.223.020/0001-18\n\nNÃO INFORMADO\n\nCPF/CNPJ:\nNome/Razão Social:\nEndereço:\nBairro:\n\n----\n\n----\n\n----\n\nE-mail:\n\n----\n\nNúmero da Nota\n05710445\n\nDESTINATÁRIO\n\nNIF:\n\n----\n\nNº:\n\n----\n\nCompl.:\n\n--\n\nCódigo de Verificação\nGZCS-2BDP\n\nINFORMAÇÕES DE ENDEREÇO NACIONAL\n\nINFORMAÇÕES DE ENDEREÇO NO EXTERIOR\n\nCidade:\n\n----\n\nADQUIRENTE\n\nNIF:\n\nMunicípio:\n\n----\n\n----\n\nPaís:\nEstado/Província/Região:\n\n----\n\n07.345.543/0001-90\n\nCPF/CNPJ:\nNome/Razão Social:\nEndereço:\nBairro:\n\nPITUBA\n\nR T R TERRITORIO DO AMAPA\n\nMunicípio:\n\n2927408 - Salvador - BA\n\n----\n\nPaís:\nEstado/Província/Região:\n\n----\n\nTEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDA\n\nE-mail:\n\nNº:\nfinanceiro@temis-es.com.br\n\n146\n\nCompl.:\n\nCasa 2\n\nINFORMAÇÕES DE ENDEREÇO NACIONAL\n\nINFORMAÇÕES DE ENDEREÇO NO EXTERIOR\n\nCidade:\n\n----\n\nSERVIÇO PRESTADO\n\nCEP:\n\n----\n\nCEP:\n\n----\n\nCEP:\n\n41830-540\n\nCEP:\n\n----\n\nLocal de prestação:\n\n2927408 - Salvador - BA\n\nCódigo indicador da operação:\n\n100301\n\nLocalidade de incidência:\n\n2927408 - Salvador - BA\n\nTipo de operação:\n\n5-Fornecimento e recebimento do pagamento concomitantes.\n\nOperação de uso:\n\nNão\n\nSituação tributária:\n\n000 - Tributação integral\n\nClassificação tributária: 000001 - Situações tributadas integralmente pelo IBS e CBS.\n\nCLASSIFICAÇÃO TRIBUTÁRIA\n\nOUTRAS CLASSIFICAÇÕES\n\nNBS:\n\n114012100 - Serviços de gestão em processos de negócios \n\nNCM:\n\n----\n\nValor da multa (R$)\n-\n\nValor do juros (R$)\n-\n\nValor das Deduções\n\nBase de Cálculo do\n\nAlíquota Estadual do\n\nAlíquota Municipal\n\nRedução de Alíquota\n\nAlíquota Efetiva do\n\nValor Diferido do IBS\n\nValor do IBS (R$)\n\nde IBS e CBS (R$)\n\nIBS e CBS (R$)\n\nIBS (%)\n0,10%\n\ndo IBS (%)\n0,00%\n\ndo IBS (%)\n0,00%\n\nIBS (%)\n0,10%\n\n(R$)\n-\n\n0,00\n\n1.113,00\n\n0,00\n\nAlíquota da CBS (%)\n\nRedução de Alíquota\n\nAlíquota Efetiva da\n\nValor Diferido da\n\nValor da CBS (R$)\n\n0,90%\n\nda CBS (%)\n0,00%\n\nCBS (%)\n0,90%\n\nCBS (R$)\n0,00\n\n0,00\n\n(1) Esta NFS-e referencia 1 documento(s) para fins de dedução de base cálculo de CBS e/ou IBS.\n\nVALOR TOTAL COBRADO =  R$ 1.113,00\n\nINFORMAÇÕES ADICIONAIS\n\nPágina 2 de 2\n\n\x0c'

NOTA_FLASH_05710815 = 'PREFEITURA DO MUNICÍPIO DE SÃO PAULO\nSECRETARIA MUNICIPAL DA FAZENDA\n\nNOTA FISCAL ELETRÔNICA DE SERVIÇOS - NFS-e\nRPS Nº 4160219 Série NFSE2, emitido em 30/09/2026\n\nNúmero da Nota\n\n05710815\nData e Hora de Emissão\n02/10/2026 04:29:30\nCódigo de Verificação\nWNUW-RAQE\n\nIdentificador Nacional: 35503081232223020000118000000571081526100060387227\n\n20261002u32223020000118\n\nPRESTADOR DE SERVIÇOS\n\nInscrição Municipal:\n\n6.141.672-0\n\n32.223.020/0001-18\n\nCPF/CNPJ:\nNome/Razão Social:\nEndereço:\nMunicípio: São Paulo\n\nFLASH TECNOLOGIA E  INSTITUICAO DE PAGAMENTO LTDA\n\nR EUGENIO DE MEDEIROS 242, ANDAR 4 - PINHEIROS - CEP: 05425-000\nUF: SP\n\nTOMADOR DE SERVIÇOS\nTEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDA\n\nNome/Razão Social:\nCPF/CNPJ:\nEndereço:\nMunicípio:\n\n07.345.543/0001-90\n\nR T R TERRITORIO DO AMAPA 146, Casa 2 - PITUBA - CEP: 41830-540\nSalvador\n\nE-mail:\n\nUF:\n\nBA\n\nfinanceiro@temis-es.com.br\n\nInscrição Municipal:\n\n----\n\nCPF/CNPJ:\n\n----\n\nNome/Razão Social:\n\n----\n\nINTERMEDIÁRIO DE SERVIÇOS\n\nDISCRIMINAÇÃO DE SERVIÇOS\n\nValor Total - R$ 20.853,30\nCompra de Créditos na Plataforma Flash - R$ 20.853,30\nValor total de serviços Flash - R$ 0,00\nData da Compra: 30/09/2026\n\nCompra de benefícios - Auxilio Mobilidade: R$ 4.979,60 (22 depósitos)\nCompra de benefícios - Auxilio Alimentação e Refeição: R$ 15.873,70 (19 depósitos)\n\nContrato BOUbrnWLrYv6uMUQ90MV5\n\nAutorização de Regime especial - SEI 6017.2019/0041453-7\nO ISS incide apenas sobre o valor de serviços Flash indicado acima\nLocal da prestação de serviços: São Paulo - SP\n\nVALOR TOTAL DO SERVIÇO = R$ 0,00\nVALOR TOTAL RECEBIDO = R$ 20.853,30\n\nContribuição Previdenciária - Retida (R$)\n\nIRRF (R$)\n\nCOFINS (R$)\n\nPIS/PASEP (R$)\n\nIPI (R$)\n\nContribuições Sociais - Retidas (R$)\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\nDescrição Contribuições Sociais - Retidas\n\n0 - PIS/COFINS/CSLL Não Retidos.\n\nCódigo do Serviço\n03205 - Fornecimento e administração de vales-refeição, vales-alimentação, vales-transporte e similares\n\nValor Total das Deduções (R$)\n0,00\n\nMunicípio de Prestação do Serviço\n-\n\n0,00\n\n2,00%\n\nNúmero Inscrição da Obra\n-\n\nBase de Cálculo (R$)\n\nAlíquota (%)\n\nValor do ISS (R$)\n\nCrédito Programa da NFP (R$)\n0,00\n\n0,00\n\nValor Aproximado dos Tributos / Fonte\n-\n\nOUTRAS INFORMAÇÕES\n(1) Esta NFS-e foi emitida com respaldo na Lei nº 14.097/2005; (2) Esta NFS-e substitui o RPS Nº 4160219 Série NFSE2, emitido em 30/09/2026; (3) O\nISS relativo a esta NFS-e deverá ser recolhido de acordo com as regras da DES-IF, mediante o envio da declaração e a posterior emissão da respectiva\nguia de pagamento por meio do sistema da DES-IF.;\n\nPágina 1 de 2\n\n\x0cIMPOSTO E CONTRIBUIÇÃO SOBRE BENS E SERVIÇOS (IBS E CBS)\nIdentificador: 35503081232223020000118000000571081526100060387227\n\nCPF/CNPJ/NIF do Fornecedor\n32.223.020/0001-18\n\nNÃO INFORMADO\n\nCPF/CNPJ:\nNome/Razão Social:\nEndereço:\nBairro:\n\n----\n\n----\n\n----\n\nE-mail:\n\n----\n\nNúmero da Nota\n05710815\n\nDESTINATÁRIO\n\nNIF:\n\n----\n\nNº:\n\n----\n\nCompl.:\n\n--\n\nCódigo de Verificação\nWNUW-RAQE\n\nINFORMAÇÕES DE ENDEREÇO NACIONAL\n\nINFORMAÇÕES DE ENDEREÇO NO EXTERIOR\n\nCidade:\n\n----\n\nADQUIRENTE\n\nNIF:\n\nMunicípio:\n\n----\n\n----\n\nPaís:\nEstado/Província/Região:\n\n----\n\n07.345.543/0001-90\n\nCPF/CNPJ:\nNome/Razão Social:\nEndereço:\nBairro:\n\nPITUBA\n\nR T R TERRITORIO DO AMAPA\n\nMunicípio:\n\n2927408 - Salvador - BA\n\n----\n\nPaís:\nEstado/Província/Região:\n\n----\n\nTEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDA\n\nE-mail:\n\nNº:\nfinanceiro@temis-es.com.br\n\n146\n\nCompl.:\n\nCasa 2\n\nINFORMAÇÕES DE ENDEREÇO NACIONAL\n\nINFORMAÇÕES DE ENDEREÇO NO EXTERIOR\n\nCidade:\n\n----\n\nSERVIÇO PRESTADO\n\nCEP:\n\n----\n\nCEP:\n\n----\n\nCEP:\n\n41830-540\n\nCEP:\n\n----\n\nLocal de prestação:\n\n2927408 - Salvador - BA\n\nCódigo indicador da operação:\n\n100301\n\nLocalidade de incidência:\n\n2927408 - Salvador - BA\n\nTipo de operação:\n\n5-Fornecimento e recebimento do pagamento concomitantes.\n\nOperação de uso:\n\nNão\n\nSituação tributária:\n\n000 - Tributação integral\n\nClassificação tributária: 000001 - Situações tributadas integralmente pelo IBS e CBS.\n\nCLASSIFICAÇÃO TRIBUTÁRIA\n\nOUTRAS CLASSIFICAÇÕES\n\nNBS:\n\n114012100 - Serviços de gestão em processos de negócios \n\nNCM:\n\n----\n\nValor da multa (R$)\n-\n\nValor do juros (R$)\n-\n\nValor das Deduções\n\nBase de Cálculo do\n\nAlíquota Estadual do\n\nAlíquota Municipal\n\nRedução de Alíquota\n\nAlíquota Efetiva do\n\nValor Diferido do IBS\n\nValor do IBS (R$)\n\nde IBS e CBS (R$)\n\nIBS e CBS (R$)\n\nIBS (%)\n0,10%\n\ndo IBS (%)\n0,00%\n\ndo IBS (%)\n0,00%\n\nIBS (%)\n0,10%\n\n(R$)\n-\n\n0,00\n\n20.853,30\n\n0,00\n\nAlíquota da CBS (%)\n\nRedução de Alíquota\n\nAlíquota Efetiva da\n\nValor Diferido da\n\nValor da CBS (R$)\n\n0,90%\n\nda CBS (%)\n0,00%\n\nCBS (%)\n0,90%\n\nCBS (R$)\n0,00\n\n0,00\n\n(1) Esta NFS-e referencia 1 documento(s) para fins de dedução de base cálculo de CBS e/ou IBS.\n\nVALOR TOTAL COBRADO =  R$ 20.853,30\n\nINFORMAÇÕES ADICIONAIS\n\nPágina 2 de 2\n\n\x0c'

SERVICO_ZERO = "VALOR TOTAL DO SERVIÇO = R$ 0,00"
RECEBIDO_1113 = "VALOR TOTAL RECEBIDO = R$ 1.113,00"
FLASH_CNPJ_FMT = "32.223.020/0001-18"
FLASH_RAZAO = "FLASH TECNOLOGIA E  INSTITUICAO DE PAGAMENTO LTDA"
PAGINA_1 = NOTA_FLASH_05710445.split("\x0c")[0]


def _dummy(nome):
    caminho = f"tests/{nome}"
    os.makedirs("tests", exist_ok=True)
    with open(caminho, "wb") as f:
        f.write(b"%PDF-1.4")
    return caminho


def _parse(monkeypatch, texto_digital):
    caminho = _dummy("dummy_flash_valor_recebido.pdf")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: texto_digital)
    try:
        return SPPdfExtractor(caminho).parse_multiple()
    finally:
        if os.path.exists(caminho):
            os.remove(caminho)


def _parse_ocr(monkeypatch, texto_ocr):
    caminho = _dummy("dummy_flash_valor_recebido_ocr.pdf")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: texto_ocr)
    try:
        return SPPdfExtractor(caminho).parse_multiple()
    finally:
        if os.path.exists(caminho):
            os.remove(caminho)


def _um(notas):
    assert len(notas) == 1
    return notas[0]


def _tem_aviso_recebido(nfse):
    return any("usado o VALOR TOTAL RECEBIDO" in a and "Flash" in a for a in nfse.avisos)


# --- (a) Flash + serviço 0,00 + recebido > 0 ---------------------------------

def test_flash_servico_zero_usa_valor_total_recebido(monkeypatch):
    nfse = _um(_parse(monkeypatch, NOTA_FLASH_05710445))
    assert nfse.numero == "05710445"
    assert nfse.prestador.cnpj_cpf == "32223020000118"
    v = nfse.valores
    assert v.valor_servicos == 1113.00
    assert v.valor_liquido_nfse == 1113.00
    # Como IMPRESSO: o ISS incide só sobre o "serviço Flash" (R$ 0,00); nada
    # de base de cálculo/ISS inventados sobre o valor recebido.
    assert v.base_calculo == 0.0
    assert v.valor_iss == 0.0
    assert (v.valor_pis, v.valor_cofins, v.valor_inss, v.valor_ir, v.valor_csll) == (0.0,) * 5
    assert v.outras_retencoes == 0.0
    assert v.valor_deducoes == 0.0
    assert _tem_aviso_recebido(nfse)
    assert any("R$ 1.113,00" in a for a in nfse.avisos)
    # a regra tratou o zero: o aviso genérico de "zero" não deve sobrar
    assert "Valor dos serviços extraído como zero" not in nfse.avisos


def test_flash_segunda_nota_real_usa_valor_total_recebido(monkeypatch):
    nfse = _um(_parse(monkeypatch, NOTA_FLASH_05710815))
    assert nfse.numero == "05710815"
    assert nfse.valores.valor_servicos == 20853.30
    assert nfse.valores.valor_liquido_nfse == 20853.30
    assert nfse.valores.base_calculo == 0.0 and nfse.valores.valor_iss == 0.0


def test_flash_filial_com_cnpj_valido_tambem_aplica_a_regra(monkeypatch):
    # filial /0002-07 (DV válido): mesma raiz 32.223.020
    texto = NOTA_FLASH_05710445.replace(FLASH_CNPJ_FMT, "32.223.020/0002-07")
    nfse = _um(_parse(monkeypatch, texto))
    assert nfse.prestador.cnpj_cpf == "32223020000207"
    assert nfse.valores.valor_servicos == 1113.00


# --- (b) Flash com serviço > 0: NÃO usa o recebido ---------------------------

def test_flash_servico_maior_que_zero_nao_usa_o_recebido(monkeypatch):
    texto = NOTA_FLASH_05710445.replace(SERVICO_ZERO, "VALOR TOTAL DO SERVIÇO = R$ 500,00")
    assert RECEBIDO_1113 in texto
    nfse = _um(_parse(monkeypatch, texto))
    assert nfse.valores.valor_servicos == 500.00
    assert nfse.valores.valor_liquido_nfse == 500.00
    assert not _tem_aviso_recebido(nfse)


# --- (c) outro prestador de SP com serviço 0,00 e recebido > 0: inalterado ---

def test_outro_prestador_sp_com_servico_zero_nao_muda(monkeypatch):
    texto = (NOTA_FLASH_05710445
             .replace(FLASH_CNPJ_FMT, "11.222.333/0001-81")
             .replace(FLASH_RAZAO, "OUTRA EMPRESA DE BENEFICIOS LTDA"))
    assert "FLASH TECNOLOGIA" not in texto.split("TOMADOR DE SERVIÇOS")[0]
    nfse = _um(_parse(monkeypatch, texto))
    assert nfse.prestador.cnpj_cpf == "11222333000181"
    assert nfse.valores.valor_servicos == 0.0
    assert nfse.valores.valor_liquido_nfse == 0.0
    assert not _tem_aviso_recebido(nfse)
    assert "Valor dos serviços extraído como zero" in nfse.avisos


# --- (d) Flash sem VALOR TOTAL RECEBIDO legível: 0,00 + aviso -----------------

@pytest.mark.parametrize("trecho_recebido", [
    "",                                            # linha ausente
    "VALOR TOTAL RECEBIDO = R$ 1.1?3,00",          # valor ilegível
    "VALOR TOTAL RECEBIDO = R$ 0,00",              # zero
])
def test_flash_sem_valor_recebido_legivel_mantem_zero_e_avisa(monkeypatch, trecho_recebido):
    texto = NOTA_FLASH_05710445.replace(RECEBIDO_1113, trecho_recebido)
    nfse = _um(_parse(monkeypatch, texto))
    assert nfse.valores.valor_servicos == 0.0
    assert nfse.valores.valor_liquido_nfse == 0.0
    assert any("Prestador Flash" in a and "mantido em 0,00" in a for a in nfse.avisos)
    assert not _tem_aviso_recebido(nfse)


# --- (e) XML final pelo transformer: totais coerentes ------------------------

def test_xml_final_flash_totais_coerentes_via_transformer(monkeypatch):
    nfse = _um(_parse(monkeypatch, NOTA_FLASH_05710445))
    raiz = ET.fromstring(Abrasf201Transformer().transform(nfse))

    def _g(no, tag):
        return float(no.find(tag).text)

    blocos_valores = list(raiz.iter("Valores")) + list(raiz.iter("ValoresNfse"))
    assert len(blocos_valores) == 2
    for no in blocos_valores:
        assert _g(no, "ValorServicos") == 1113.00
        assert _g(no, "BaseCalculo") == 0.0
        assert _g(no, "ValorIss") == 0.0
    for no in raiz.iter("ValoresNfse"):
        retencoes = sum(_g(no, t) for t in (
            "ValorPis", "ValorCofins", "ValorInss", "ValorIr", "ValorCsll", "OutrasRetencoes"))
        assert _g(no, "ValorLiquidoNfse") == pytest.approx(
            _g(no, "ValorServicos") - retencoes - _g(no, "ValorDeducoes"))


def test_flash_retencoes_ja_extraidas_abatem_o_liquido():
    # A grade digital de retenções desta nota não é lida pelo extrator de
    # valores (sai tudo 0,00, como impresso), então a regra é exercitada
    # direto com retenções já extraídas: líquido = recebido - retenções - deduções.
    ext = SPPdfExtractor("tests/nao_existe.pdf")
    ext.raw_text = PAGINA_1
    ext.layout = LAYOUT_SAO_PAULO
    prestador = Entidade(
        cnpj_cpf="32223020000118", razao_social=FLASH_RAZAO,
        endereco=Endereco(logradouro="R EUGENIO DE MEDEIROS", numero="242", bairro="PINHEIROS",
                          codigo_municipio="3550308", uf="SP", cep="05425000"))
    entrada = Valores(valor_servicos=0.0, valor_cofins=10.0, valor_pis=2.0, valor_deducoes=3.0,
                      base_calculo=0.0, aliquota=0.0, valor_liquido_nfse=0.0)
    saida, avisos = ext._aplicar_flash_valor_recebido(prestador, entrada)
    assert saida.valor_servicos == 1113.00
    assert saida.valor_liquido_nfse == pytest.approx(1113.00 - 10.0 - 2.0 - 3.0)
    # nada além de serviços/líquido muda
    assert saida.model_copy(update={"valor_servicos": 0.0, "valor_liquido_nfse": 0.0}) == entrada
    assert len(avisos) == 1


# --- várias notas Flash no mesmo PDF: cada uma tratada separadamente ----------

def test_duas_notas_flash_no_mesmo_pdf_sao_tratadas_separadamente(monkeypatch):
    texto = NOTA_FLASH_05710445 + "\x0c" + NOTA_FLASH_05710815
    por_numero = {n.numero: n for n in _parse(monkeypatch, texto)}
    assert set(por_numero) == {"05710445", "05710815"}
    assert por_numero["05710445"].valores.valor_servicos == 1113.00
    assert por_numero["05710815"].valores.valor_servicos == 20853.30


# --- escaneado (LAYOUT_SAO_PAULO_2): só vale o recebido confirmado ------------

def test_layouts_detectados_digital_e_escaneado():
    ext = SPPdfExtractor("tests/nao_existe.pdf")
    ext.raw_text = PAGINA_1
    ext.from_ocr = False
    assert ext._detect_layout() == LAYOUT_SAO_PAULO
    ext.from_ocr = True
    assert ext._detect_layout() == LAYOUT_SAO_PAULO_2


def test_flash_escaneado_recebido_confirmado_pela_discriminacao(monkeypatch):
    nfse = _um(_parse_ocr(monkeypatch, PAGINA_1))
    assert nfse.valores.valor_servicos == 1113.00
    assert nfse.valores.valor_liquido_nfse == 1113.00
    assert nfse.valores.base_calculo == 0.0 and nfse.valores.valor_iss == 0.0
    assert _tem_aviso_recebido(nfse)


def test_flash_escaneado_recebido_nao_confirmado_mantem_zero(monkeypatch):
    # OCR leu o recebido diferente do "Valor Total" da discriminação: não confia
    texto = PAGINA_1.replace(RECEBIDO_1113, "VALOR TOTAL RECEBIDO = R$ 1.118,00")
    nfse = _um(_parse_ocr(monkeypatch, texto))
    assert nfse.valores.valor_servicos == 0.0
    assert nfse.valores.valor_liquido_nfse == 0.0
    assert any("Prestador Flash" in a and "não foi confirmado" in a for a in nfse.avisos)
