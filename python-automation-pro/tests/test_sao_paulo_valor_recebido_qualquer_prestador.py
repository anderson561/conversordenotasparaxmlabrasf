# -*- coding: utf-8 -*-
r"""São Paulo/SP (LAYOUT_SAO_PAULO digital / LAYOUT_SAO_PAULO_2 escaneado) -
regra do "VALOR TOTAL RECEBIDO" AMPLIADA para QUALQUER prestador.

Achado real 2026-11-18, prestador VR BENEFICIOS E SERVICOS DE PROCESSAMENTO
(CNPJ 02.535.864/0001-33, IM 6.131.480-3), tomador VERDE FLORICULTURA LTDA:

- "VR VERDE.pdf", NF 101217349 (fontes CID: o pdfminer devolve lixo e a nota
  vai para o OCR - LAYOUT_SAO_PAULO_2): serviço R$ 0,00, recebido R$ 2.300,00;
- "NFSe_61314803_102003139.pdf", NF 102003139 (digital): serviço R$ 0,00,
  recebido R$ 1.800,00.

Antes as duas saíam com ValorServicos 0,00: a regra do recebido exigia
serviço > 0 e o caso serviço 0,00 só existia para Flash e Pluxee. Decisão do
usuário (2026-11-18): para qualquer prestador, recebido lido com segurança e
> 0 com serviço 0,00 ou menor que ele -> ValorServicos = recebido,
ValorDeducoes como impresso (a diferença NÃO vai mais para deduções, "não há
deduções na nota fiscal"), Base/Alíquota/ISS/retenções como impressos,
líquido = recebido - retenções, aviso explícito. Flash e Pluxee (serviço
0,00) seguem nas regras próprias, com resultado inalterado.

`NOTA_VR_101217349_OCR` = retorno REAL de `SPPdfExtractor._extract_via_ocr`
no PDF real; `NOTA_VR_102003139` = retorno REAL e verbatim de
`pdfminer.high_level.extract_text()`. Os negativos trocam UM trecho do texto
real (marcado em cada teste)."""
import xml.etree.ElementTree as ET

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor
from src.transformers.abrasf_transformer import Abrasf201Transformer
from tests.test_sao_paulo_flash_valor_recebido import NOTA_FLASH_05710445
from tests.test_sao_paulo_pluxee_recebido_servico_zero import AVISO_OK as AVISO_PLUXEE_OK
from tests.test_sao_paulo_pluxee_recebido_servico_zero import NOTA_PLUXEE_08969996

NOTA_VR_101217349_OCR = "SP2RET_FEDERAIS: 0,00 0,00 0,00 0,00\nSP2RET_CSLL: 0,00\n\nIRRF (R$) CSLL (R$) COFINS (R$) PIS/PASEP (R$)\n0,00 0,00 0,00 0,00\nCódigo do Serviço\n03205 - Fornecimento e administração de vales-refeição, vales-alimentação, vales-transporte e similares\nValor Total das Deduções Alíquota Valor do ISS\n0,00 2,00% 0,00\n\nNúmero da Nota\n101217349\nData e Hora de Emissão\n06/10/2026 07:50:31\nCódigo de Verificação\n1GIQ-VKKG\n\nFe x Número da Nota\nPREFEITURA DO MUNICÍPIO DE SÃO PAULO 101217349\n\nSECRETARIA MUNICIPAL DA FAZENDA Data e Hora de Emissão\nN 06/10/2026 07:50:31\nNOTA FISCAL ELETRÔNICA DE SERVIÇOS - NFS-e Código de Verificação\n20261118U02535864000133 RPS Nº 101075789 Série 1, emitido em 06/10/2026 1 GIQ-VKKG\n\nIdentificador Nacional: 35503081202535864000133000010121734926103095828970\n\nPRESTADOR DE SERVIÇOS\nCPF/CNPJ: 02.535.864/0001-33 Inscrição Municipal: 6.131.480-3\nNome/Razão Social: VR BENEFICIOS E SERVICOS DE PROCESSAMENTO INSTITUICAO DE PAGA\nEndereço: AV DOS BANDEIRANTES 460 460 - BROOKLIN PAULISTA - CEP: 04553-900\nMunicípio: São Paulo UF: SP\n\nTOMADOR DE SERVIÇOS\nNomey/Razão Social: VERDE FLORICULTURA LTDA\nCPF/CNPJ: 13.502.158/0001-01 Inscrição Municipal: ----\nEndereço: AVENIDA TANCREDO NEVES 148, SHOP. C. IGUATEMI TERR - CAMINHO DAS ARVORES\nMunicípio: Salvador UF: BA E-mail: verdefloriculturaçogmail.com\n\nINTERMEDIÁRIO DE SERVIÇOS\nCPF/CNPJ: ---- Nomey/Razão Social: ----\n\nDISCRIMINAÇÃO DE SERVIÇOS\n\nTotal de Crédito VR Multi - VR+VA Auxílio: R$ 2.300,00 - (4 cartão(ões))\n\nVencimento em 05/10/2026\n\nTrib aprox. Lei nº 12.741/12: R$0,00 Federal, R$0,00 Municipal e R$0,00 pelos serviços\nFonte: IBPT/empresometro.com.br C44399 26.2.B\n\nValor da corretagem ou comissão: zero\n\nNúmero do protocolo do pedido: 20261005005214\n\nREALIZE O PAGAMENTO APENAS DE BOLETOS EMITIDOS POR VOCÊ NA ÁREA LOGADA E SEGURA DO SEU\nPORTAL RH. PREVINA-SE E EVITE PREJUÍZOS FINANCEIROS.\n\nVALOR TOTAL DO SERVIÇO = R$ 0,00\nVALOR TOTAL RECEBIDO = R$ 2.300,00\n\nContribuição Previdenciária - Retida (R$) IRRF (R$) COFINS (R$) PIS/PASEP (R$) IPI(R$)\n0,00 0,00 0,00 0,00 0,00\nContribuições Sociais - Retidas (R$) Descrição Contribuições Sociais - Retidas\n0,00 O - PIS/COFINS/CSLL Não Retidos.\n\nCódigo do Serviço\n03205 - Fornecimento e administração de vales-refeição, vales-alimentação, vales-transporte e similares\n\nValor Total das Deduções (R$) Base de Cálculo (R$) Alíquota (%) Valor do ISS (R$) Crédito Programa da NFP (R$)\n0,00 0,00 2,00% 0,00 0,00\nMunicípio de Prestação do Serviço Número Inscrição da Obra Valor Aproximado dos Tributos / Fonte\n- - 17,64% / IBPT\n\nOUTRAS INFORMAÇÕES\n(1) Esta NFS-e foi emitida com respaldo na Lei nº 14.097/2005; (2) Esta NFS-e substitui o RPS Nº 101075789 Série 1, emitido em 06/10/2026;\n\nPágina 1 de 2\n\n\x0c\nIMPOSTO E CONTRIBUIÇÃO SOBRE BENS E SERVIÇOS (IBS E CBS)\nIdentificador: 35503081202535864000133000010121734926103095828970\n\nCPF/CNPJ/NIF do Fornecedor Número da Nota Código de Verificação\n02.535.864/0001-33 101217349 1GIQ-VKKG\nDESTINATÁRIO\nCPF/CNPJ: NÃO INFORMADO NIF:\nNome/Razão Social: ----\nEndereço:  ---- Nº: = Compl: --\nBairro: E-mail: -\nINFORMAÇÕES DE ENDEREÇO NACIONAL\nMunicípio:  ---- CEP: ----\nINFORMAÇÕES DE ENDEREÇO NO EXTERIOR\nPaís: ---- Cidade: ----\nEstado/Província/Região: -——— CEP:\nADQUIRENTE\nCPF/CNPJ: 13.502.158/0001-01 NIF:\nNome/Razão Social: VERDE FLORICULTURA LTDA\nEndereço: AVENIDA TANCREDO NEVES Nº: 148 Compl.: SHOP. C. IGUATEMI TERR\nBairro: CAMINHO DAS ARVORES E-mail: verdefloriculturaçogmail.com\nINFORMAÇÕES DE ENDEREÇO NACIONAL\nMunicípio: 2927408 - Salvador - BA CEP: ----\nINFORMAÇÕES DE ENDEREÇO NO EXTERIOR\nPaís: ---- Cidade: ----\nEstado/Província/Região: -——— CEP: ----\nSERVIÇO PRESTADO\n\nLocal de prestação: 3550308 - São Paulo - SP Código indicador da operação: 100301\nLocalidade de incidência: 2927408 - Salvador - BA\nTipo de operação: ' 5-Fornecimento e recebimento do pagamento concomitantes. Operação deuso: Não\n\nCLASSIFICAÇÃO TRIBUTÁRIA\nSituação tributária: 000 - Tributação integral\nClassificação tributária: 000001 - Situações tributadas integralmente pelo IBS e CBS.\nOUTRAS CLASSIFICAÇÕES\nNBS: 114012100 - Serviços de gestão em processos de negócios\nNCM: =\n\nValor da multa (R$) Valor do juros (R$)\n\nValor das Deduções Base de Cálculo do Alíquota Estadual do Alíquota Municipal Redução de Alíquota Alíquota Efetiva do Valor Diferido do IBS Valor do IBS (R$)\n\nde IBS e CBS (R$) IBS e CBS (R$) IBS (%) do IBS (%) do IBS (%) IBS (%) (R$)\n0,10% 0,00% 0,00% 0,10% - 0,00\nAlíquota da CBS (%) Redução de Alíquota Alíquota Efetiva da | Valor Diferido da Valor da CBS (R$)\n2.300,00 0,00\nda CBS (%) CBS (%) CBS (R$)\n0,90% 0,00% 0,90% 0,00 0,00\n\nVALOR TOTAL COBRADO = R$ 2.300,00\n\nINFORMAÇÕES ADICIONAIS\n(1) Esta NFS-e referencia 1 documento(s) para fins de dedução de base cálculo de CBS e/ou IBS.\n\nPágina 2 de 2\n"

NOTA_VR_102003139 = 'PREFEITURA DO MUNICÍPIO DE SÃO PAULO\nSECRETARIA MUNICIPAL DA FAZENDA\n\nNOTA FISCAL ELETRÔNICA DE SERVIÇOS - NFS-e\nRPS Nº 101848559 Série 1, emitido em 04/11/2026\n\nNúmero da Nota\n\n102003139\nData e Hora de Emissão\n04/11/2026 08:30:20\nCódigo de Verificação\nGNEA-J7CC\n\nIdentificador Nacional: 35503081202535864000133000010200313926110065703809\n\n20261118u02535864000133\n\nPRESTADOR DE SERVIÇOS\n\nInscrição Municipal:\n\n6.131.480-3\n\n02.535.864/0001-33\n\nCPF/CNPJ:\nNome/Razão Social:\nEndereço:\nMunicípio: São Paulo\n\nVR BENEFICIOS E SERVICOS DE PROCESSAMENTO INSTITUICAO DE PAGA\n\nAV DOS BANDEIRANTES 460 460 - BROOKLIN PAULISTA - CEP: 04553-900\n\nVERDE FLORICULTURA LTDA\n\nTOMADOR DE SERVIÇOS\n\nNome/Razão Social:\nCPF/CNPJ:\nEndereço:\nMunicípio:\n\n13.502.158/0001-01\n\nAVENIDA TANCREDO NEVES 148, SHOP. C. IGUATEMI         TERR - CAMINHO DAS ARVORES\nSalvador\n\nverdefloricultura@gmail.com\n\nE-mail:\n\nUF:\n\nBA\n\nUF: SP\n\nInscrição Municipal:\n\n----\n\nCPF/CNPJ:\n\n----\n\nNome/Razão Social:\n\n----\n\nTotal de Crédito VR Multi - VR+VA Auxílio: R$ 1.800,00 - (3 cartão(ões))\n\nDISCRIMINAÇÃO DE SERVIÇOS\n\nINTERMEDIÁRIO DE SERVIÇOS\n\nVencimento em 02/11/2026\nTrib aprox. Lei nº 12.741/12: R$0,00 Federal, R$0,00 Municipal e R$0,00 pelos serviços\nFonte: IBPT/empresometro.com.br C44399 26.2.B\nValor da corretagem ou comissão: zero\nNúmero do protocolo do pedido: 20261102001231\nREALIZE O PAGAMENTO APENAS DE BOLETOS EMITIDOS POR VOCÊ NA ÁREA LOGADA E SEGURA DO SEU\nPORTAL RH. PREVINA-SE E EVITE PREJUÍZOS FINANCEIROS.\n\nVALOR TOTAL DO SERVIÇO = R$ 0,00\nVALOR TOTAL RECEBIDO = R$ 1.800,00\n\nContribuição Previdenciária - Retida (R$)\n\nIRRF (R$)\n\nCOFINS (R$)\n\nPIS/PASEP (R$)\n\nIPI (R$)\n\nContribuições Sociais - Retidas (R$)\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\nDescrição Contribuições Sociais - Retidas\n\n0 - PIS/COFINS/CSLL Não Retidos.\n\nCódigo do Serviço\n03205 - Fornecimento e administração de vales-refeição, vales-alimentação, vales-transporte e similares\n\nBase de Cálculo (R$)\n\nAlíquota (%)\n\nValor do ISS (R$)\n\nValor Total das Deduções (R$)\n0,00\n\nMunicípio de Prestação do Serviço\n-\n\n0,00\n\n2,00%\n\nNúmero Inscrição da Obra\n-\n\nOUTRAS INFORMAÇÕES\n\nCrédito Programa da NFP (R$)\n0,00\n\n0,00\n\nValor Aproximado dos Tributos / Fonte\n17,64% / IBPT\n\n(1) Esta NFS-e foi emitida com respaldo na Lei nº 14.097/2005; (2) Esta NFS-e substitui o RPS Nº 101848559 Série 1, emitido em 04/11/2026;\n\nPágina 1 de 2\n\n\x0cIMPOSTO E CONTRIBUIÇÃO SOBRE BENS E SERVIÇOS (IBS E CBS)\nIdentificador: 35503081202535864000133000010200313926110065703809\n\nCPF/CNPJ/NIF do Fornecedor\n02.535.864/0001-33\n\nNÃO INFORMADO\n\nCPF/CNPJ:\nNome/Razão Social:\nEndereço:\nBairro:\n\n----\n\n----\n\n----\n\nE-mail:\n\n----\n\nNúmero da Nota\n102003139\n\nDESTINATÁRIO\n\nNIF:\n\n----\n\nNº:\n\n----\n\nCompl.:\n\n--\n\nCódigo de Verificação\nGNEA-J7CC\n\nMunicípio:\n\n----\n\n----\n\nPaís:\nEstado/Província/Região:\n\n----\n\n13.502.158/0001-01\n\nCPF/CNPJ:\nNome/Razão Social:\nEndereço:\nBairro:\n\nAVENIDA TANCREDO NEVES\n\nCAMINHO DAS ARVORES\n\nVERDE FLORICULTURA LTDA\n\nMunicípio:\n\n2927408 - Salvador - BA\n\n----\n\nPaís:\nEstado/Província/Região:\n\n----\n\nINFORMAÇÕES DE ENDEREÇO NACIONAL\n\nINFORMAÇÕES DE ENDEREÇO NO EXTERIOR\n\nCidade:\n\n----\n\nADQUIRENTE\n\nNIF:\n\nCEP:\n\n----\n\nCEP:\n\n----\n\nE-mail:\n\nNº:\nverdefloricultura@gmail.com\n\n148\n\nINFORMAÇÕES DE ENDEREÇO NACIONAL\n\nCompl.:\n\nSHOP. C. IGUATEMI         TERR\n\nINFORMAÇÕES DE ENDEREÇO NO EXTERIOR\n\nCidade:\n\n----\n\nSERVIÇO PRESTADO\n\nCEP:\n\n----\n\nCEP:\n\n----\n\nLocal de prestação:\n\n3550308 - São Paulo - SP\n\nCódigo indicador da operação:\n\n100301\n\nLocalidade de incidência:\n\n2927408 - Salvador - BA\n\nTipo de operação:\n\n5-Fornecimento e recebimento do pagamento concomitantes.\n\nOperação de uso:\n\nNão\n\nSituação tributária:\n\n000 - Tributação integral\n\nClassificação tributária: 000001 - Situações tributadas integralmente pelo IBS e CBS.\n\nCLASSIFICAÇÃO TRIBUTÁRIA\n\nOUTRAS CLASSIFICAÇÕES\n\nNBS:\n\n114012100 - Serviços de gestão em processos de negócios \n\nNCM:\n\n----\n\nValor da multa (R$)\n-\n\nValor do juros (R$)\n-\n\nValor das Deduções\n\nBase de Cálculo do\n\nAlíquota Estadual do\n\nAlíquota Municipal\n\nRedução de Alíquota\n\nAlíquota Efetiva do\n\nValor Diferido do IBS\n\nValor do IBS (R$)\n\nde IBS e CBS (R$)\n\nIBS e CBS (R$)\n\nIBS (%)\n0,10%\n\ndo IBS (%)\n0,00%\n\ndo IBS (%)\n0,00%\n\nIBS (%)\n0,10%\n\n(R$)\n-\n\n0,00\n\n1.800,00\n\n0,00\n\nAlíquota da CBS (%)\n\nRedução de Alíquota\n\nAlíquota Efetiva da\n\nValor Diferido da\n\nValor da CBS (R$)\n\n0,90%\n\nda CBS (%)\n0,00%\n\nCBS (%)\n0,90%\n\nCBS (R$)\n0,00\n\n0,00\n\n(1) Esta NFS-e referencia 1 documento(s) para fins de dedução de base cálculo de CBS e/ou IBS.\n\nVALOR TOTAL COBRADO =  R$ 1.800,00\n\nINFORMAÇÕES ADICIONAIS\n\nPágina 2 de 2\n\n\x0c'


SERVICO_ZERO = "VALOR TOTAL DO SERVIÇO = R$ 0,00"
RECEBIDO_2300 = "VALOR TOTAL RECEBIDO = R$ 2.300,00"
RECEBIDO_1800 = "VALOR TOTAL RECEBIDO = R$ 1.800,00"
AVISO_2300 = ("Serviço impresso R$ 0,00; Valor total recebido R$ 2.300,00 usado como "
              "ValorServicos; sem deduções - ValorDeducoes como impresso na nota (R$ 0,00); "
              "Base de Cálculo/Alíquota/ISS mantidos como impressos; conferir")
AVISO_1800 = AVISO_2300.replace("2.300,00", "1.800,00")
CAMPOS_XML = ("ValorServicos", "ValorDeducoes", "BaseCalculo", "Aliquota", "ValorIss")


def _digital(monkeypatch, tmp_path, texto=NOTA_VR_102003139):
    pdf = tmp_path / "vr.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: texto)
    notas = SPPdfExtractor(str(pdf)).parse_multiple()
    assert len(notas) == 1
    return notas[0]


def _ocr(monkeypatch, tmp_path, texto=NOTA_VR_101217349_OCR):
    pdf = tmp_path / "vr_scan.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: texto)
    notas = SPPdfExtractor(str(pdf)).parse_multiple()
    assert len(notas) == 1
    return notas[0]


def _trocar(texto, velho, novo):
    assert texto.count(velho) == 1, texto.count(velho)
    return texto.replace(velho, novo)


def _valores(nota):
    v = nota.valores
    return (v.valor_servicos, v.valor_deducoes, v.base_calculo, v.aliquota, v.valor_iss,
            v.valor_liquido_nfse)


def _avisos_regra(nota):
    return [a for a in nota.avisos if "recebido" in a.lower()]


def _xml(nota):
    root = ET.fromstring(Abrasf201Transformer().transform(nota))
    secoes = [{c: root.find(f"{s}/{c}").text for c in CAMPOS_XML}
              for s in (".//ValoresNfse", ".//Servico/Valores")]
    return secoes, root.find(".//ValoresNfse/ValorLiquidoNfse").text


# --- textos reais: regra aplicada --------------------------------------------

def test_vr_101217349_escaneada_usa_o_recebido(monkeypatch, tmp_path):
    nota = _ocr(monkeypatch, tmp_path)
    assert nota.numero == "101217349"
    assert nota.prestador.cnpj_cpf == "02535864000133"
    assert _valores(nota) == (2300.0, 0.0, 0.0, 0.02, 0.0, 2300.0)
    assert _avisos_regra(nota) == [AVISO_2300]
    assert not any("extraído como zero" in a for a in nota.avisos)


def test_vr_102003139_digital_usa_o_recebido(monkeypatch, tmp_path):
    nota = _digital(monkeypatch, tmp_path)
    assert nota.numero == "102003139"
    assert nota.prestador.cnpj_cpf == "02535864000133"
    assert _valores(nota) == (1800.0, 0.0, 0.0, 0.02, 0.0, 1800.0)
    v = nota.valores
    assert (v.valor_pis, v.valor_cofins, v.valor_inss, v.valor_ir, v.valor_csll,
            v.outras_retencoes, v.iss_retido) == (0.0,) * 6 + (False,)
    assert _avisos_regra(nota) == [AVISO_1800]
    assert not any("extraído como zero" in a for a in nota.avisos)


@pytest.mark.parametrize("parse,valor", [(_ocr, "2300.00"), (_digital, "1800.00")],
                         ids=["escaneada", "digital"])
def test_vr_xml_final_nas_duas_secoes(monkeypatch, tmp_path, parse, valor):
    secoes, liquido = _xml(parse(monkeypatch, tmp_path))
    esperado = {"ValorServicos": valor, "ValorDeducoes": "0.00", "BaseCalculo": "0.00",
                "Aliquota": "0.02", "ValorIss": "0.00"}
    assert secoes == [esperado, esperado]
    assert liquido == valor


def test_servico_maior_que_zero_e_menor_que_recebido_sem_deducao(monkeypatch, tmp_path):
    """Serviço 100,00 (base 100,00, ISS 2,00) e recebido 1.800,00 em
    prestador que não é Pluxee: o recebido vai para ValorServicos e a
    diferença NÃO vai mais para ValorDeducoes (mapeamento extinto)."""
    texto = _trocar(NOTA_VR_101217349_OCR, SERVICO_ZERO, "VALOR TOTAL DO SERVIÇO = R$ 100,00")
    texto = _trocar(texto, "0,00 0,00 2,00% 0,00 0,00", "0,00 100,00 2,00% 2,00 0,00")
    nota = _ocr(monkeypatch, tmp_path, texto)
    assert _valores(nota) == (2300.0, 0.0, 100.0, 0.02, 2.0, 2300.0)
    avisos = _avisos_regra(nota)
    assert len(avisos) == 1 and "maior que o valor do serviço, R$ 100,00" in avisos[0], avisos
    assert not any("repasse" in a or "Pluxee" in a for a in nota.avisos)


# --- negativos: mantém e (quando há dúvida) avisa ----------------------------

def test_recebido_igual_ao_servico_nao_aplica(monkeypatch, tmp_path):
    texto = _trocar(NOTA_VR_102003139, SERVICO_ZERO, "VALOR TOTAL DO SERVIÇO = R$ 1.800,00")
    nota = _digital(monkeypatch, tmp_path, texto)
    assert nota.valores.valor_servicos == 1800.0
    assert _avisos_regra(nota) == []


def test_recebido_menor_que_servico_nao_aplica(monkeypatch, tmp_path):
    texto = _trocar(NOTA_VR_101217349_OCR, SERVICO_ZERO, "VALOR TOTAL DO SERVIÇO = R$ 2.500,00")
    texto = _trocar(texto, "0,00 0,00 2,00% 0,00 0,00", "0,00 2.500,00 2,00% 50,00 0,00")
    nota = _ocr(monkeypatch, tmp_path, texto)
    assert nota.valores.valor_servicos == 2500.0
    assert not any("usado como ValorServicos" in a for a in nota.avisos)
    assert any("menor que o do serviço" in a for a in nota.avisos)


@pytest.mark.parametrize("parse,texto,velho", [
    (_digital, NOTA_VR_102003139, RECEBIDO_1800),
    (_ocr, NOTA_VR_101217349_OCR, RECEBIDO_2300),
], ids=["digital", "escaneada"])
def test_recebido_ilegivel_mantem_zero_e_avisa(monkeypatch, tmp_path, parse, texto, velho):
    nota = parse(monkeypatch, tmp_path, _trocar(texto, velho, "VALOR TOTAL RECEBIDO = R$ 1.8O0,0O"))
    assert nota.valores.valor_servicos == 0.0
    assert any("não foi lido com segurança" in a and "mantido" in a for a in nota.avisos)


def test_recebido_com_leituras_divergentes_mantem_zero(monkeypatch, tmp_path):
    texto = _trocar(NOTA_VR_102003139, RECEBIDO_1800,
                    RECEBIDO_1800 + "\nVALOR TOTAL RECEBIDO = R$ 1.890,00")
    nota = _digital(monkeypatch, tmp_path, texto)
    assert nota.valores.valor_servicos == 0.0
    assert any("leituras divergentes" in a for a in nota.avisos)


def test_recebido_zero_nao_aplica(monkeypatch, tmp_path):
    texto = _trocar(NOTA_VR_102003139, RECEBIDO_1800, "VALOR TOTAL RECEBIDO = R$ 0,00")
    nota = _digital(monkeypatch, tmp_path, texto)
    assert nota.valores.valor_servicos == 0.0
    assert not any("usado como ValorServicos" in a for a in nota.avisos)


def test_escaneada_sem_confirmacao_na_discriminacao_mantem_zero(monkeypatch, tmp_path):
    """OCR leu o recebido 2.800,00 e a discriminação diz 2.300,00: no
    escaneado com serviço 0,00 o recebido precisa ser confirmado."""
    texto = _trocar(NOTA_VR_101217349_OCR, RECEBIDO_2300, "VALOR TOTAL RECEBIDO = R$ 2.800,00")
    nota = _ocr(monkeypatch, tmp_path, texto)
    assert nota.valores.valor_servicos == 0.0
    assert any("não foi confirmado" in a for a in nota.avisos)


def test_campo_recebido_ausente_nao_muda_nada(monkeypatch, tmp_path):
    nota = _digital(monkeypatch, tmp_path, _trocar(NOTA_VR_102003139, RECEBIDO_1800 + "\n", ""))
    assert nota.valores.valor_servicos == 0.0
    assert _avisos_regra(nota) == []
    assert "Valor dos serviços extraído como zero" in nota.avisos


# --- Flash e Pluxee: regras próprias, resultado inalterado -------------------

def test_flash_real_continua_na_regra_propria(monkeypatch, tmp_path):
    nota = _digital(monkeypatch, tmp_path, NOTA_FLASH_05710445)
    assert _valores(nota)[:3] == (1113.0, 0.0, 0.0)
    assert nota.valores.valor_liquido_nfse == 1113.0
    assert [a for a in nota.avisos if "usado como ValorServicos" in a or "VALOR TOTAL RECEBIDO" in a] == [
        a for a in nota.avisos if "Flash" in a]


def test_flash_escaneada_nao_confirmada_continua_em_zero(monkeypatch, tmp_path):
    """A Flash escaneada com recebido não confirmado fica em 0,00 pela regra
    própria; a regra geral não age em cima."""
    texto = NOTA_FLASH_05710445.split("\x0c")[0].replace(
        "VALOR TOTAL RECEBIDO = R$ 1.113,00", "VALOR TOTAL RECEBIDO = R$ 1.118,00")
    nota = _ocr(monkeypatch, tmp_path, texto)
    assert nota.valores.valor_servicos == 0.0
    assert not any(a.startswith("Serviço impresso R$ 0,00; Valor total recebido") for a in nota.avisos)


def test_pluxee_real_servico_zero_continua_na_regra_do_emv(monkeypatch, tmp_path):
    nota = _digital(monkeypatch, tmp_path, NOTA_PLUXEE_08969996)
    assert _valores(nota) == (9867.48, 0.0, 0.0, 0.02, 0.0, 9867.48)
    assert _avisos_regra(nota) == [AVISO_PLUXEE_OK]
