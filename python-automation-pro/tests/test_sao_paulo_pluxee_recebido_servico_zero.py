# -*- coding: utf-8 -*-
"""São Paulo/SP digital, PLUXEE BENEFICIOS BRASIL S.A. (CNPJ 69.034.668/0001-56):
"VALOR TOTAL DO SERVIÇO = R$ 0,00" COM "VALOR TOTAL RECEBIDO = R$ 9.867,48".

Achado real 2026-11-13, nota nº 08969996 ("2026.10.03 - NFS 08969996 - PLUXEE
BENEFICIOS BRASIL SA.pdf", PDF digital, 2 páginas, a 2ª é o anexo IBS/CBS).
Dois defeitos:

1. Grade lida deslocada: o pdfminer despeja os rótulos Base/Alíquota/ISS ANTES
   do rótulo "Valor Total das Deduções" e põe "OUTRAS INFORMAÇÕES" no meio dos
   5 valores; a leitura estrutural via só 3 valores e a posicional colocava o
   "2,00%" da alíquota em Deduções (XML: ValorDeducoes 2.00, Aliquota 0.00).
2. Buraco de regra: a regra do recebido exige serviço > 0 e a do crédito EMV
   não agia com recebido impresso - ValorServicos saía 0,00.

Esperado (decisão do usuário): ValorServicos = 9.867,48 (recebido),
ValorDeducoes = 0,00 como impresso (decisão de 2026-11-13: "não há deduções na
nota fiscal"; até então ia o próprio recebido, como repasse), Base 0,00,
Alíquota 2%, ISS 0,00, líquido 9.867,48; o crédito EMV da discriminação
(9867.48) confere o recebido.

`NOTA_PLUXEE_08969996` = retorno REAL e verbatim de
`pdfminer.high_level.extract_text()` no PDF real; os negativos trocam UM
trecho do texto real (marcado em cada teste).
"""
import xml.etree.ElementTree as ET

from src.extractors.pdf_extractor import SPPdfExtractor
from src.transformers.abrasf_transformer import Abrasf201Transformer
from tests.test_sao_paulo_flash_valor_recebido import NOTA_FLASH_05710445

NOTA_PLUXEE_08969996 = 'PREFEITURA DO MUNICÍPIO DE SÃO PAULO\nSECRETARIA MUNICIPAL DA FAZENDA\n\nNOTA FISCAL ELETRÔNICA DE SERVIÇOS - NFS-e\nRPS Nº 354117 Série 4F, emitido em 02/10/2026\n\nNúmero da Nota\n\n08969996\nData e Hora de Emissão\n03/10/2026 15:26:22\nCódigo de Verificação\n6JYX-7582\n\nIdentificador Nacional: 35503081269034668000156000000896999626101817900013\n\n20261006u69034668000156\n\nPRESTADOR DE SERVIÇOS\n\nInscrição Municipal:\n\n7.718.411-4\n\n69.034.668/0001-56\n\nCPF/CNPJ:\nNome/Razão Social:\nEndereço:\nMunicípio: São Paulo\n\nPLUXEE BENEFICIOS BRASIL S.A.\n\nAV DRA RUTH CARDOSO 7221, CONJ 801 901 E 1201 - PINHEIROS - CEP: 05425-902\n\nDELTALINE SERVICOS LTDA.\n\nTOMADOR DE SERVIÇOS\n\nNome/Razão Social:\nCPF/CNPJ:\nEndereço:\nMunicípio:\n\n01.813.680/0001-25\n\nRua R CAMBORIU 39 - IAPI - CEP: 40330-533\nSalvador\n\nUF:\n\nBA\n\nE-mail:\n\nsp.deltaline@gmail.com\n\nUF: SP\n\nInscrição Municipal:\n\n----\n\nCPF/CNPJ:\n\n----\n\nNome/Razão Social:\n\n----\n\nINTERMEDIÁRIO DE SERVIÇOS\n\nDISCRIMINAÇÃO DE SERVIÇOS\n\n41 ALIMENTAÇÃO EMV 9867.48\nGESTAO COBRANCA 0.00 \\ TX EMISSAO CARTAO 0.00\nIRRF RECOLHIMENTO EFETUADO PELO EMITENTE CONF. IN/SRF 153/87 R$0.00\nSERVIÇO ENQUADRADO COMO ADMINISTRAÇÃO DE CONVÊNIO\nEntr/Cred 02/10/2026\nNro Pedido.: 43768713/26\n\nVALOR TOTAL DO SERVIÇO = R$ 0,00\nVALOR TOTAL RECEBIDO = R$ 9.867,48\n\nContribuição Previdenciária - Retida (R$)\n\nIRRF (R$)\n\nCOFINS (R$)\n\nPIS/PASEP (R$)\n\nIPI (R$)\n\nContribuições Sociais - Retidas (R$)\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\n0,00\n\nDescrição Contribuições Sociais - Retidas\n-\n\nCódigo do Serviço\n03205 - Fornecimento e administração de vales-refeição, vales-alimentação, vales-transporte e similares\n\nBase de Cálculo (R$)\n\nAlíquota (%)\n\nValor do ISS (R$)\n\nValor Total das Deduções (R$)\n0,00\n\nMunicípio de Prestação do Serviço\n-\n\n0,00\n\n2,00%\n\nNúmero Inscrição da Obra\n-\n\nOUTRAS INFORMAÇÕES\n\nCrédito Programa da NFP (R$)\n0,00\n\n0,00\n\nValor Aproximado dos Tributos / Fonte\n-\n\n(1) Esta NFS-e foi emitida com respaldo na Lei nº 14.097/2005; (2) Esta NFS-e substitui o RPS Nº 354117 Série 4F, emitido em 02/10/2026;\n\nPágina 1 de 2\n\n\x0cIMPOSTO E CONTRIBUIÇÃO SOBRE BENS E SERVIÇOS (IBS E CBS)\nIdentificador: 35503081269034668000156000000896999626101817900013\n\nCPF/CNPJ/NIF do Fornecedor\n69.034.668/0001-56\n\nNÃO INFORMADO\n\nCPF/CNPJ:\nNome/Razão Social:\nEndereço:\nBairro:\n\n----\n\n----\n\n----\n\nE-mail:\n\n----\n\nNúmero da Nota\n08969996\n\nDESTINATÁRIO\n\nNIF:\n\n----\n\nNº:\n\n----\n\nCompl.:\n\n--\n\nCódigo de Verificação\n6JYX-7582\n\nMunicípio:\n\n----\n\n----\n\nPaís:\nEstado/Província/Região:\n\n----\n\n01.813.680/0001-25\n\nCPF/CNPJ:\nNome/Razão Social:\nEndereço:\nBairro:\n\nIAPI\n\nRua R CAMBORIU\n\nDELTALINE SERVICOS LTDA.\n\nMunicípio:\n\n2927408 - Salvador - BA\n\n----\n\nPaís:\nEstado/Província/Região:\n\n----\n\nINFORMAÇÕES DE ENDEREÇO NACIONAL\n\nINFORMAÇÕES DE ENDEREÇO NO EXTERIOR\n\nCidade:\n\n----\n\nADQUIRENTE\n\nNIF:\n\nNº:\n\n39\n\nCompl.:\n\nE-mail:\n\nsp.deltaline@gmail.com\n\nINFORMAÇÕES DE ENDEREÇO NACIONAL\n\nINFORMAÇÕES DE ENDEREÇO NO EXTERIOR\n\nCidade:\n\n----\n\nSERVIÇO PRESTADO\n\nCEP:\n\n----\n\nCEP:\n\n----\n\nCEP:\n\n40330-533\n\nCEP:\n\n----\n\nLocal de prestação:\n\n3550308 - São Paulo - SP\n\nCódigo indicador da operação:\n\n100301\n\nLocalidade de incidência:\n\n2927408 - Salvador - BA\n\nTipo de operação:\n\n5-Fornecimento e recebimento do pagamento concomitantes.\n\nOperação de uso:\n\nNão\n\nSituação tributária:\n\n000 - Tributação integral\n\nClassificação tributária: 000001 - Situações tributadas integralmente pelo IBS e CBS.\n\nCLASSIFICAÇÃO TRIBUTÁRIA\n\nOUTRAS CLASSIFICAÇÕES\n\nNBS:\n\n114012100 - Serviços de gestão em processos de negócios \n\nNCM:\n\n----\n\nValor da multa (R$)\n0,00\n\nValor do juros (R$)\n0,00\n\nValor das Deduções\n\nBase de Cálculo do\n\nAlíquota Estadual do\n\nAlíquota Municipal\n\nRedução de Alíquota\n\nAlíquota Efetiva do\n\nValor Diferido do IBS\n\nValor do IBS (R$)\n\nde IBS e CBS (R$)\n\nIBS e CBS (R$)\n\nIBS (%)\n0,10%\n\ndo IBS (%)\n0,00%\n\ndo IBS (%)\n0,00%\n\nIBS (%)\n0,10%\n\n(R$)\n-\n\n0,00\n\n9.867,48\n\n0,00\n\nAlíquota da CBS (%)\n\nRedução de Alíquota\n\nAlíquota Efetiva da\n\nValor Diferido da\n\nValor da CBS (R$)\n\n0,90%\n\nda CBS (%)\n0,00%\n\nCBS (%)\n0,90%\n\nCBS (R$)\n0,00\n\n0,00\n\n(1) Esta NFS-e referencia 1 documento(s) para fins de dedução de base cálculo de CBS e/ou IBS.\n\nVALOR TOTAL COBRADO =  R$ 9.867,48\n\nINFORMAÇÕES ADICIONAIS\n\nPágina 2 de 2\n\n\x0c'

PAGINA_1 = NOTA_PLUXEE_08969996.split("\x0c")[0]
LINHA_EMV = "41 ALIMENTAÇÃO EMV 9867.48"
RECEBIDO = "VALOR TOTAL RECEBIDO = R$ 9.867,48"
AVISO_OK = ("Serviço impresso R$ 0,00; Valor total recebido R$ 9.867,48 usado como "
            "ValorServicos, sem deduções (ValorDeducoes como impresso na nota, R$ 0,00) - "
            "confere com o crédito EMV R$ 9.867,48 da discriminação; conferir")


def _uma(monkeypatch, tmp_path, texto=NOTA_PLUXEE_08969996):
    pdf = tmp_path / "pluxee.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: texto)
    notas = SPPdfExtractor(str(pdf)).parse_multiple()
    assert len(notas) == 1
    return notas[0]


def _trocar(velho, novo, texto=NOTA_PLUXEE_08969996):
    assert texto.count(velho) == 1, texto.count(velho)
    return texto.replace(velho, novo)


def _avisos_pluxee(nota):
    return [a for a in nota.avisos if "recebido" in a.lower() or "EMV" in a]


def _valores(nota):
    v = nota.valores
    return (v.valor_servicos, v.valor_deducoes, v.base_calculo, v.aliquota, v.valor_iss,
            v.valor_liquido_nfse)


# --- grade (causa raiz 1) -------------------------------------------------------

def test_grade_real_lida_pela_estrutura():
    assert SPPdfExtractor._sp_grade_valores_por_estrutura(PAGINA_1) == (0.0, 0.0, 0.02, 0.0)


def test_grade_sem_os_5_valores_nao_e_lida():
    # trecho trocado: some o valor do "Crédito Programa da NFP" (4 valores)
    texto = _trocar("Crédito Programa da NFP (R$)\n0,00", "Crédito Programa da NFP (R$)\n-", PAGINA_1)
    assert SPPdfExtractor._sp_grade_valores_por_estrutura(texto) is None


# --- regra aplicada no texto real ----------------------------------------------

def test_real_recebido_vira_valor_servicos_sem_deducao(monkeypatch, tmp_path):
    nota = _uma(monkeypatch, tmp_path)
    assert nota.numero == "08969996"
    assert nota.prestador.cnpj_cpf == "69034668000156"
    assert _valores(nota) == (9867.48, 0.0, 0.0, 0.02, 0.0, 9867.48)
    v = nota.valores
    assert (v.valor_pis, v.valor_cofins, v.valor_inss, v.valor_ir, v.valor_csll,
            v.outras_retencoes, v.iss_retido) == (0.0,) * 6 + (False,)
    assert _avisos_pluxee(nota) == [AVISO_OK]
    assert not any("extraído como zero" in a for a in nota.avisos)


def test_real_xml_final(monkeypatch, tmp_path):
    root = ET.fromstring(Abrasf201Transformer().transform(_uma(monkeypatch, tmp_path)))
    esperado = {"ValorServicos": "9867.48", "ValorDeducoes": "0.00", "BaseCalculo": "0.00",
                "Aliquota": "0.02", "ValorIss": "0.00"}
    for secao in (".//ValoresNfse", ".//Servico/Valores"):
        assert {c: root.find(f"{secao}/{c}").text for c in esperado} == esperado
    assert root.find(".//ValoresNfse/ValorLiquidoNfse").text == "9867.48"
    assert root.find(".//Servico/Valores/IssRetido").text == "2"
    assert root.find(".//Servico/ItemListaServico").text == "03205"
    for c in ("ValorPis", "ValorCofins", "ValorInss", "ValorIr", "ValorCsll"):
        assert root.find(f".//Servico/Valores/{c}").text == "0.00"


# --- conferência com o crédito EMV (digital: usa o recebido e avisa) -----------

def test_emv_divergente_usa_recebido_e_avisa(monkeypatch, tmp_path):
    nota = _uma(monkeypatch, tmp_path, _trocar(LINHA_EMV, "41 ALIMENTAÇÃO EMV 9800.00"))
    assert _valores(nota) == (9867.48, 0.0, 0.0, 0.02, 0.0, 9867.48)
    avisos = _avisos_pluxee(nota)
    assert len(avisos) == 1 and "DIVERGE do crédito EMV R$ 9.800,00" in avisos[0], avisos


def test_emv_ilegivel_usa_recebido_e_avisa(monkeypatch, tmp_path):
    nota = _uma(monkeypatch, tmp_path, _trocar(LINHA_EMV, "41 ALIMENTAÇÃO EMV 98G7.4B"))
    assert nota.valores.valor_servicos == 9867.48
    avisos = _avisos_pluxee(nota)
    assert len(avisos) == 1 and "não conferido com a discriminação" in avisos[0], avisos


# --- casos em que NÃO aplica (mantém 0,00 + aviso) -----------------------------

def _mantido(nota, motivo, deducoes=0.0):
    assert nota.valores.valor_servicos == 0.0
    assert nota.valores.valor_deducoes == deducoes
    avisos = [a for a in nota.avisos if "Pluxee" in a]
    assert len(avisos) == 1 and "mantido em 0,00" in avisos[0] and motivo in avisos[0], avisos


def test_recebido_ilegivel_mantem(monkeypatch, tmp_path):
    nota = _uma(monkeypatch, tmp_path, _trocar(RECEBIDO, "VALOR TOTAL RECEBIDO = R$ 9.867,4B"))
    _mantido(nota, "não foi lido com segurança")


def test_recebido_divergente_mantem(monkeypatch, tmp_path):
    nota = _uma(monkeypatch, tmp_path, _trocar(RECEBIDO, RECEBIDO + "\nVALOR TOTAL RECEBIDO = R$ 9.876,48"))
    _mantido(nota, "leituras divergentes")


def test_deducoes_impressas_mantem(monkeypatch, tmp_path):
    texto = _trocar("Valor Total das Deduções (R$)\n0,00", "Valor Total das Deduções (R$)\n5,00")
    _mantido(_uma(monkeypatch, tmp_path, texto), "deduções/base/ISS", deducoes=5.0)


def test_outro_prestador_nao_aplica(monkeypatch, tmp_path):
    texto = NOTA_PLUXEE_08969996.replace("69.034.668/0001-56", "11.222.333/0001-81")
    nota = _uma(monkeypatch, tmp_path, texto)
    assert nota.valores.valor_servicos == 0.0
    assert not any("Pluxee" in a or "Valor total recebido R$" in a for a in nota.avisos)


def test_flash_real_continua_na_regra_propria(monkeypatch, tmp_path):
    nota = _uma(monkeypatch, tmp_path, NOTA_FLASH_05710445)
    assert nota.valores.valor_servicos == 1113.0
    assert nota.valores.valor_deducoes == 0.0
    assert any("Flash" in a for a in nota.avisos)
    assert not any("Pluxee" in a or "ValorDeducoes (repasse)" in a for a in nota.avisos)
