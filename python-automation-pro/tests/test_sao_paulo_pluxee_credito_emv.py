# -*- coding: utf-8 -*-
"""São Paulo/SP, PLUXEE BENEFICIOS BRASIL S.A. (CNPJ 69.034.668/0001-56):
nota com "VALOR TOTAL DO SERVIÇO = R$ 0,00" e SEM "VALOR TOTAL RECEBIDO" —
só o crédito de vale-alimentação/refeição repassado, impresso na
discriminação como item "EMV".

Decisão do usuário (2026-11-12), nota nº 08937118 (pág. 23 do lote
"Notas_Fiscais_Recebidas_10.2026_-_Guarajuba_Suites.pdf", escaneada):
discriminação "9 ALIMENTAÇÃO EMV 1620.00" e "TX ADMIN 0.00 N TX DISPON
CREDITO 0.00 N GESTAO COBRANCA 0.00"; grade 0,00 / 0,00 / 2,00% / 0,00.
XML: ValorServicos = ValorDeducoes = 1.620,00 (crédito EMV, repasse);
Base/Alíquota/ISS como impressos (0,00 / 2% / 0,00); líquido 1.620,00.

Textos = OCR REAL (`_ocr_page`) das págs. 23 e 24; os negativos trocam UMA
linha do texto real (marcada em cada teste).
"""
import xml.etree.ElementTree as ET

from src.extractors.pdf_extractor import SPPdfExtractor
from src.transformers.abrasf_transformer import Abrasf201Transformer
from tests.test_sao_paulo_flash_valor_recebido import NOTA_FLASH_05710445
from tests.test_sao_paulo_pagina_continuacao_valores import PAG31_NOTA_09125394, PAG32_ANEXO_DA_09125394

PAG23_NOTA_08937118 = 'SP2RET_FEDERAIS: 0,00 0,00 0,00 0,00\nSP2RET_CSLL: 0,00\n\nValor Total das Deduções Alíquota Valor do ISS\n0,00 2,00% 0,00\n\nNúmero da Nota\n08937118\nData e Hora de Emissão\n01/10/2026 10:13:49\nCódigo de Verificação\nLEF3-TDAF\n\nne - Número da Nota\nPREFEITURA DO MUNICÍPIO DE SÃO PAULO 08937118\nSECRETARIA MUNICIPAL DA FAZENDA Data e Hora de Emissão\n\' 01/10/2026 10:13:49\nNOTA FISCAL ELETRÔNICA DE SERVIÇOS - NFS-e Código de Verificação\nRPS Nº 315212 Série 4F, emitido em 30/09/2026 LEF3-TDAF\nIdentificador Nacional: 35503081269034668000156000000893711826106167342970\nPRESTADOR DE SERVIÇOS\nCPF/CNPJ: 69.034.668/0001-56 Inscrição Municipal: 7.718.411-4\nNome/Razão Social: PLUXEE BENEFICIOS BRASIL S.A.\nEndereço: AV DRA RUTH CARDOSO 7221, CONJ 801 901 E 1201 - PINHEIROS - CEP: 05425-902\nMunicípio: São Paulo , UF: SP\nTOMADOR DE SERVIÇOS\nNome/Razão Social: PH GESTAO E CONSULTORIA S.A.\nCPF/CNPJ: 25.311.856/0001-09 E "Inscrição Municipal: ----\nEndereço: Rua AL AL HUMAITA 00, GUARAJUBA SHOPPING SL 2 SU 102 - GUARAJUBA - CEP: 42840-562\nMunicípio: Camaçari UF: BA E-mail: admguarajubacenter(Qgmail.com\nINTERMEDIÁRIO DE SERVIÇOS\nCPF/CNPJ: ---- Nomey/Razão Social: ----\nDISCRIMINAÇÃO DE SERVIÇOS “a\n\n9 ALIMENTAÇÃO EMV 1620.00\n\nTX ADMIN 0.00 N TX DISPON CREDITO 0.00 N GESTAO COBRANCA 0.00\n\nIRRF RECOLHIMENTO EFETUADO PELO EMITENTE CONF. IN/SRF 153/87 R$0.00\n\nSERVIÇO ENQUADRADO COMO ADMINISTRAÇÃO DE CONVÊNIO\n\nEntr/Cred 01/10/2026\n\nNro Pedido.: 43787745/26\n\nESSA NOTA FISCAL NAO DEVE SER CONTABILIZADA PARA OS EFEITOS DA LEGISLACAO DO PAT\n\nVALOR TOTAL DO SERVIÇO = R$ 0,00\n\nContribuição Previdenciária - Retida (R$) IRRF (R$) COFINS (R$) PIS/PASEP (R$) | IPI (R$)\n0,00 0,00 0,00 0,00 0,00\nContribuições Sociais - Retidas (R$) Descrição Contribuições Sociais - Retidas CC\n0,00 -\nCódigo do Serviço\n03205 - Fornecimento e administração de vales-refeição, vales-alimentação, vales-transporte e similares\nValor Total das Deduções (R$) Base de Cálculo (R$) Alíquota (%) Valor do ISS (R$) “ Crédito Programa da NFP (R$)\n0,00 0,00 2,00% 0,00 0,00\nMunicípio de Prestação do Serviço Número Inscrição da Obra Valor Aproximado dos Tributos / Fonte\nOUTRAS INFORMAÇÕES\n\n(1) Esta NFS-e foi emitida com respaldo na Lei nº 14.097/2005; (2) Esta NFS-e substitui o RPS Nº 315212 Série 4F, emitido em 30/09/2026;\n\nPágina 1 de 2\n'

PAG24_ANEXO_DA_08937118 = "IMPOSTO E CONTRIBUIÇÃO SOBRE BENS E SERVIÇOS (IBS E CBS)\nIdentificador: 35503081 269034668000156000000893711826106167342970\n\nCPF/CNPJ/NIF do Fornecedor Número da Nota Código de Verificação\n69.034.668/0001-56 08937118 LEF3-TDAF\nDESTINATÁRIO\nCPF/CNPJ: NÃO INFORMADO NIE: ==\nNome/Razão Social:  ----\nEndereço:  --== Nº; uma Compl: --\nBairro:  ---= E-mail: ----\nINFORMAÇÕES DE ENDEREÇO NACIONAL\nMunicípio: ---- CEP: e\nINFORMAÇÕES DE ENDEREÇO NO EXTERIOR\nPaís: == Cidade: q---\nEstado/Província/Região: — - CEP:\nADQUIRENTE\n\nCPF/CNPJ: 25.311.856/0001-09 NIF:\nNome/Razão Social: PH GESTAO E CONSULTORIA S.A.\nEndereço: Rua AL AL HUMAITA Nº: 00 Compl: GUARAJUBA SHOPPING SL 2 SU 102\nBairro: GUARAJUBA E-mail: admguarajubacenter(Ogmail.com\n\nINFORMAÇÕES DE ENDEREÇO NACIONAL\nMunicípio: 2905701 - Camaçari - BA\n\nINFORMAÇÕES DE ENDEREÇO NO EXTERIOR\n\nCEP: 42840-562\n\nPaís: —— Cidade:\nEstado/Província/Região:  ---- CER; ==\nSERVIÇO PRESTADO\nLocal de prestação: 3550308 - São Paulo - SP Código indicador da operação: 100301\nLocalidade de incidência: 2905701 - Camaçari - BA\nTipo de operação: | 5-Fornecimento e recebimento do pagamento concomitantes. Operação deuso: Não\nCLASSIFICAÇÃO TRIBUTÁRIA\nSituação tributária: 000 - Tributação integral\nClassificação tributária: 000001 - Situações tributadas integralmente pelo IBS e CBS.\nOUTRAS CLASSIFICAÇÕES\nNBS: 114012100 - Serviços de gestão em processos de negócios\nNCM: -—=\nValor da multa (R$) Valor do juros (R$)\n0,00 0,00\nValor das Deduções | Base de Cálculo do |Alíquota Estadual do| Alíquota Municipal |Redução de Alíquota| Alíquota Efetiva do |Valor Diferido do IBS| Valor do IBS (R$)\nde IBS e CBS (R$) IBS e CBS (R$) IBS (%) do IBS (%) do IBS (%) IBS (%) (R$)\n0,10% 0,00% 0,00% 0,10% - 0,00\n0,00 0,00 Alíquota da CBS (%) Redução de Alíquota| Alíquota Efetiva da | Valor Diferido da | Valor da CBS (R$)\n' ' da CBS (%) CES (%) ces (R$)\n0,90% | 0,00% 0,90% 0,00 0,00\nVALOR TOTAL COBRADO = R$ 0,00\nINFORMAÇÕES ADICIONAIS\n\nPágina2 de 2\n"

SERVICO_ZERO = "VALOR TOTAL DO SERVIÇO = R$ 0,00"
LINHA_EMV = "9 ALIMENTAÇÃO EMV 1620.00"
LINHA_TAXAS = "TX ADMIN 0.00 N TX DISPON CREDITO 0.00 N GESTAO COBRANCA 0.00"
AVISO_EMV = ("Serviço impresso R$ 0,00 sem \"Valor total recebido\"; crédito EMV R$ 1.620,00 "
             "da discriminação usado como ValorServicos e lançado em ValorDeducoes (repasse)")


def _uma(monkeypatch, tmp_path, paginas):
    pdf = tmp_path / "lote.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: "\x0c".join(paginas))
    notas = SPPdfExtractor(str(pdf)).parse_multiple()
    assert len(notas) == 1
    return notas[0]


def _trocar(velho, novo, texto=PAG23_NOTA_08937118):
    assert texto.count(velho) == 1
    return texto.replace(velho, novo)


def _xml(nfse):
    root = ET.fromstring(Abrasf201Transformer().transform(nfse))
    campos = ("ValorServicos", "ValorDeducoes", "BaseCalculo", "Aliquota", "ValorIss")
    nfse_v = {c: root.find(f".//ValoresNfse/{c}").text for c in campos + ("ValorLiquidoNfse",)}
    serv_v = {c: root.find(f".//Servico/Valores/{c}").text for c in campos}
    return nfse_v, serv_v


def _avisos_emv(nota):
    return [a for a in nota.avisos if "EMV" in a]


# --- regra aplicada no texto real ---------------------------------------------

def test_pag23_credito_emv_vira_valor_servicos_e_deducao(monkeypatch, tmp_path):
    nota = _uma(monkeypatch, tmp_path, [PAG23_NOTA_08937118, PAG24_ANEXO_DA_08937118])
    assert nota.numero == "08937118"
    v = nota.valores
    assert (v.valor_servicos, v.valor_deducoes, v.base_calculo, v.aliquota, v.valor_iss,
            v.valor_liquido_nfse) == (1620.0, 1620.0, 0.0, 0.02, 0.0, 1620.0)
    assert _avisos_emv(nota) == [AVISO_EMV]
    assert not any("extraído como zero" in a for a in nota.avisos)


def test_pag23_xml_igual_nas_duas_secoes(monkeypatch, tmp_path):
    nota = _uma(monkeypatch, tmp_path, [PAG23_NOTA_08937118, PAG24_ANEXO_DA_08937118])
    esperado = {"ValorServicos": "1620.00", "ValorDeducoes": "1620.00", "BaseCalculo": "0.00",
                "Aliquota": "0.02", "ValorIss": "0.00"}
    assert _xml(nota) == (dict(esperado, ValorLiquidoNfse="1620.00"), esperado)


def test_varios_itens_emv_legiveis_somam(monkeypatch, tmp_path):
    texto = _trocar(LINHA_EMV, LINHA_EMV + "\n1 REFEIÇÃO EMV 10.00")
    nota = _uma(monkeypatch, tmp_path, [texto])
    assert nota.valores.valor_servicos == 1630.0
    assert nota.valores.valor_deducoes == 1630.0


# --- casos em que NÃO aplica (mantém 0,00 + aviso) ----------------------------

def _mantido(nota, motivo):
    assert nota.valores.valor_servicos == 0.0
    assert nota.valores.valor_deducoes == 0.0
    avisos = _avisos_emv(nota)
    assert len(avisos) == 1 and "mantido em 0,00" in avisos[0] and motivo in avisos[0], avisos


def test_taxa_diferente_de_zero_mantem(monkeypatch, tmp_path):
    nota = _uma(monkeypatch, tmp_path, [_trocar("TX ADMIN 0.00", "TX ADMIN 6.00")])
    _mantido(nota, "taxas")


def test_taxa_ilegivel_mantem(monkeypatch, tmp_path):
    nota = _uma(monkeypatch, tmp_path, [_trocar("GESTAO COBRANCA 0.00", "GESTAO COBRANCA O.OO")])
    _mantido(nota, "taxas")


def test_emv_ilegivel_mantem(monkeypatch, tmp_path):
    nota = _uma(monkeypatch, tmp_path, [_trocar(LINHA_EMV, "9 ALIMENTAÇÃO EMV 162O.0O")])
    _mantido(nota, "EMV")


def test_um_de_dois_emv_ilegivel_mantem(monkeypatch, tmp_path):
    nota = _uma(monkeypatch, tmp_path, [_trocar(LINHA_EMV, LINHA_EMV + "\n1 REFEIÇÃO EMV 1O.00")])
    _mantido(nota, "EMV")


def test_base_impressa_diferente_de_zero_mantem(monkeypatch, tmp_path):
    texto = _trocar("0,00 0,00 2,00% 0,00 0,00", "0,00 6,00 2,00% 0,12 0,00")
    nota = _uma(monkeypatch, tmp_path, [texto])
    _mantido(nota, "base")


def test_com_valor_total_recebido_a_regra_emv_nao_age(monkeypatch, tmp_path):
    texto = _trocar(SERVICO_ZERO, SERVICO_ZERO + "\n\nVALOR TOTAL RECEBIDO = R$ 1.620,00")
    nota = _uma(monkeypatch, tmp_path, [texto])
    assert nota.valores.valor_servicos == 0.0
    assert _avisos_emv(nota) == []


def test_outro_prestador_nao_aplica(monkeypatch, tmp_path):
    texto = _trocar("CPF/CNPJ: 69.034.668/0001-56", "CPF/CNPJ: 11.222.333/0001-81")
    nota = _uma(monkeypatch, tmp_path, [texto])
    assert nota.valores.valor_servicos == 0.0
    assert _avisos_emv(nota) == []


def test_flash_com_servico_zero_continua_na_regra_propria(monkeypatch, tmp_path):
    pdf = tmp_path / "flash.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: NOTA_FLASH_05710445)
    antes = SPPdfExtractor(str(pdf)).parse_multiple()
    assert len(antes) == 1
    assert _avisos_emv(antes[0]) == []
    assert any("Flash" in a for a in antes[0].avisos)


def test_controle_pluxee_com_servico_impresso_continua_na_regra_do_recebido(monkeypatch, tmp_path):
    nota = _uma(monkeypatch, tmp_path, [PAG31_NOTA_09125394, PAG32_ANEXO_DA_09125394])
    assert (nota.valores.valor_servicos, nota.valores.valor_deducoes) == (16.0, 10.0)
    assert _avisos_emv(nota) == []
