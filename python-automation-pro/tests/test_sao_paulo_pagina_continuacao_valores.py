# -*- coding: utf-8 -*-
"""São Paulo/SP escaneada com a nota DESLOCADA entre duas páginas.

Lote "Notas_Fiscais_Recebidas_10.2026_-_Guarajuba_Suites.pdf", NFS-e Pluxee
nº 09125393 (cód. verificação FT4E-HMTM): a pág. 33 traz só a metade de cima
(cabeçalho, prestador, tomador, discriminação) e a pág. 34 a metade de baixo
("VALOR TOTAL DO SERVIÇO = R$ 6,00", "VALOR TOTAL RECEBIDO = R$ 16,00", grade
0,00 / 6,00 / 2,00% / 0,12, código 03205, "Página 1 de 2"). A pág. 35/36 é o
anexo IBS/CBS ("Página 2 de 2").

Bug: a pág. 34, sem cabeçalho, caía em "Layout não reconhecido" e era
descartada antes do fatiamento; a nota saía com todos os valores 0,00 e
código 03115 (default). Agora a página de continuação com o bloco de valores
é anexada à nota SP da página anterior.

Textos = OCR REAL (`_ocr_page`) das págs. 31 a 36, sem edição.
"""
import xml.etree.ElementTree as ET

from src.extractors import sp_identificador as sp_ident
from src.extractors.pdf_extractor import SPPdfExtractor
from src.transformers.abrasf_transformer import Abrasf201Transformer
from tests.test_sao_paulo2_pluxee_lote_pagina_11 import PAG11_NOTA_08980332

PAG31_NOTA_09125394 = 'SP2RET_FEDERAIS: 0,00 0,00 0,00 0,00\nSP2RET_CSLL: 0,00\n\nValor Total das Deduções Alíquota Valor do ISS\n0,00 2,00% 0,12\n\nNúmero da Nota\n09125394\nData e Hora de Emissão\n23/10/2026 20:37:16\nCódigo de Verificação\nWASP-YNB2\n\nfi a Nú da Not\nPREFEITURA DO MUNICÍPIO DE SÃO PAULO “09125394\nSECRETARIA MUNICIPAL DA FAZENDA Data e Hora de Emissão\nN 23/10/2026 20:37:16\nNOTA FISCAL ELETRÔNICA DE SERVIÇOS - NFS-e Código de Verificação\n20261026U69034668000156 RPS Nº 536574 Série 4F, emitido em 23/10/2026 WASP-YNB2\n\nIdentificador Nacional: 35503081269034668000156000000912539426109906649022\n\nPRESTADOR DE SERVIÇOS\n\nCPF/CNPJ: 69.034.668/0001-56 Inscrição Municipal: 7.718.411-4\nNomey/Razão Social: PLUXEE BENEFICIOS BRASIL S.A.\n\n[)| Endereço: AV DRA RUTH CARDOSO 7221, CONJ 801 901 E 1201 - PINHEIROS - CEP: 05425-902\nMunicípio: São Paulo UF: SP\n\nTOMADOR DE SERVIÇOS\nNomey/Razão Social: PH GESTAO E CONSULTORIA S.A.\nCPF/CNPJ: 25.311.856/0001-09 Inscrição Municipal: ----\nEndereço: Rua AL AL HUMAITA 00, GUARAJUBA SHOPPING SL 2 SU 102 - GUARAJUBA - CEP: 42840-562\nMunicípio: Camaçari UF: BA E-mail: admguarajubacenter(Qgmail.com\n\nINTERMEDIÁRIO DE SERVIÇOS\nCPF/CNPJ: ---- Nome/Razão Social: ----\n\nDISCRIMINAÇÃO DE SERVIÇOS\n1 REFEIÇÃO EMV 10.00\nTX ANTECIPAÇÃO CRÉDITO 0.00 N TX ENTREGA 6.00 N TX ADM SERV 0.00 N TX EMISSAO CARTAO 0.00 N TX DISPON CREDITO\n0.00 N TAR COBRANCA 0.00\nIRRF RECOLHIMENTO EFETUADO PELO EMITENTE CONF. IN/SRF 153/87 R$0.09\nSERVIÇO ENQUADRADO COMO ADMINISTRAÇÃO DE CONVÊNIO\nEntr/Cred 23/10/2026\nNro Pedido.: 43960378/26\nESSA NOTA FISCAL NAO DEVE SER CONTABILIZADA PARA OS EFEITOS DA LEGISLACAO DO PAT\n\nVALOR TOTAL DO SERVIÇO = R$ 6,00\n\nVALOR TOTAL RECEBIDO = R$ 16,00\nContribuição Previdenciária - Retida (R$) IRRF (R$) COFINS (R$) PIS/PASEP (R$) IPI(RS)\n0,00 0,00 0,00 0,00 0,00\nContribuições Sociais - Retidas (R$) Descrição Contribuições Sociais - Retidas\n0,00 -\n\nCódigo do Serviço\n03205 - Fornecimento e administração de vales-refeição, vales-alimentação, vales-transporte e similares\n\nValor Total das Deduções (R$) Base de Cálculo (R$) Alíquota (%) Valor do ISS (R$) Crédito Programa da NFP (R$)\n0,00 6,00 2,00% 0,12 0,00\nMunicípio de Prestação do Serviço Número Inscrição da Obra Valor Aproximado dos Tributos / Fonte\n\nOUTRAS INFORMAÇÕES\n(1) Esta NFS-e foi emitida com respaldo na Lei nº 14.097/2005; (2) Esta NFS-e substitui o RPS Nº 536574 Série 4F, emitido em 23/10/2026; (3) Data\nde vencimento do ISS desta NFS-e: 10/11/2026;\n\nPágina 1 de 2\n'

PAG32_ANEXO_DA_09125394 = "IMPOSTO E CONTRIBUIÇÃO SOBRE BENS E SERVIÇOS (IBS E CBS)\nIdentificador: 35503081269034668000156000000912539426109906649022\n\nCPF/CNPJ/NIF do Fornecedor\n\nNúmero da Nota\n\nCódigo de Verificação\n\n69.034.668/0001-56 09125394 WASP-YNB2\nDESTINATÁRIO\n\nCPF/CNPJ: NÃO INFORMADO NIF: ==\nNome/Razão Social: --—-\nEndereço:  ---- Nº. === Compl: --\nBairro: ---- E-mail. ----\n\nINFORMAÇÕES DE ENDEREÇO NACIONAL\nMunicípio: ---- CEP: ---\n\nINFORMAÇÕES DE ENDEREÇO NO EXTERIOR\nPaís: ---- Cidade: ----\nEstado/Província/Região: --—- CEP: ---\nADQUIRENTE\n\nCPF/CNPJ: 25.311.856/0001-09 NIF:\nNomey/Razão Social: PH GESTAO E CONSULTORIA S.A.\nEndereço: Rua AL AL HUMAITA Nº: 00 Compl: GUARAJUBA SHOPPING SL 2 SU 102\nBairro: GUARAJUBA E-mail: admguarajubacenter(Ogmail.com\n\nINFORMAÇÕES DE ENDEREÇO NACIONAL\nMunicípio: 2905701 - Camaçari - BA CEP: 42840-562\n\nINFORMAÇÕES DE ENDEREÇO NO EXTERIOR\nPaís: ---- Cidade: ----\nEstado/Província/Região: e... CEP: =.\nSERVIÇO PRESTADO\nLocal de prestação: 3550308 - São Paulo - SP Código indicador da operação: 100301\nLocalidade de incidência: 2905701 - Camaçari - BA\nTipo de operação: | 5-Fornecimento e recebimento do pagamento concomitantes. Operação de uso: Não\nCLASSIFICAÇÃO TRIBUTÁRIA\nSituação tributária: 000 - Tributação integral\nClassificação tributária: 000001 - Situações tributadas integralmente pelo IBS e CBS.\nOUTRAS CLASSIFICAÇÕES\nNBS: 114012100 - Serviços de gestão em processos de negócios\nNCM:  ---\nValor da multa (R$) Valor do juros (R$)\n0,00 0,00\nValor das Deduções | Base de Cálculo do |Alíquota Estadual do| Alíquota Municipal |Redução de Alíquota| Alíquota Efetiva do | Valor Diferido do IBS| Valor do IBS (R$)\nde IBS e CBS (R$) IBS e CBS (R$) IBS (%) do IBS (%) do IBS (%) IBS (%) (R$)\n0,10% 0,00% 0,00% 0,10% - 0,01\n10,00 588 Alíquota da CBS (%) Redução de Alíquota| Alíquota Efetiva da | Valor Diferido da Valor da CBS (R$)\n' ' da CBS (%) CBS (%) CBS (R$)\n0,90% 0,00% 0,90% 0,00 0,05\nVALOR TOTAL COBRADO = R$ 16,00\nINFORMAÇÕES ADICIONAIS\n\n(1) Esta NFS-e referencia 1 documento(s) para fins de dedução de base cálculo de CBS e/ou IBS.\n\nPágina 2 de 2\n\n"

PAG33_NOTA_09125393_TOPO = 'Fe - Número da Nota\nPREFEITURA DO MUNICÍPIO DE SÃO PAULO 09125393\nSECRETARIA MUNICIPAL DA FAZENDA Data e Hora de Emissão\nA 23/10/2026 20:37:16\nNOTA FISCAL ELETRÔNICA DE SERVIÇOS - NFS-e Código de Verificação\n20261026U690346680001 56 RPS Nº 536573 Série 4F, emitido em 23/10/2026 FT4E-HMTM\nPRESTADOR DE SERVIÇOS\nCPF/CNPJ: 69.034.668/0001-56 Inscrição Municipal: 7.718.411-4\nNome/Razão Social: PLUXEE BENEFICIOS BRASIL S.A.\nEndereço: AV DRA RUTH CARDOSO 7221, CONJ 801 901 E 1201 - PINHEIROS - CEP: 05425-902\nMunicípio: São Paulo UF: SP\nTOMADOR DE SERVIÇOS\nNome/Razão Social: PH GESTAO E CONSULTORIA S.A.\nCPF/CNPJ: 25.311.856/0001-09 Inscrição Municipal: ----\nEndereço: Rua AL AL HUMAITA 00, GUARAJUBA SHOPPING SL 2 SU 102 - GUARAJUBA - CEP: 42840-562\nMunicípio: Camaçari UF: BA E-mail: admguarajubacenter(dgmail.com\nINTERMEDIÁRIO DE SERVIÇOS\nCPF/CNPJ: ---- Nomey/Razão Social: ----\n\nDISCRIMINAÇÃO DE SERVIÇOS\n1 ALIMENTAÇÃO EMV 10.00\nGESTAO COBRANCA 0.00 N TX DISPON CREDITO 0.00 N TX EMISSAO CARTAO 0.00 N TX ADMIN 0.00 N TX ENTREGA 6.00 N Tx\nANTECIPAÇÃO CRÉDITO 0.00\nIRRF RECOLHIMENTO EFETUADO PELO EMITENTE CONF. IN/SRF 153/87 R$0.09\nSERVIÇO ENQUADRADO COMO ADMINISTRAÇÃO DE CONVÊNIO\nEntr/Cred 23/10/2026\nNro Pedido.: 43960378/26\nESSA NOTA FISCAL NAO DEVE SER CONTABILIZADA PARA OS EFEITOS DA LEGISLACAO DO PAT\n\n'

PAG34_NOTA_09125393_VALORES = 'VALOR TOTAL DO SERVIÇO = R$ 6,00\n\nVALOR TOTAL RECEBIDO = R$ 16,00\n\nContribuição Previdenciária - Retida (R$) IRRF (R$) COFINS (R$) PIS/PASEP (R$) IPI(R$)\n0,00 0,00 0,00 0,00 0,00\n\nContribuições Sociais - Retidas (R$) Descrição Contribuições Sociais - Retidas\n0,00 -\n\nCódigo do Serviço\n03205 - Fornecimento e administração de vales-refeição, vales-alimentação, vales-transporte e similares\n\nValor Total das Deduções (R$) Base de Cálculo (R$) Alíquota (%) Valor do ISS (R$) Crédito Programa da NFP (R$)\n0,00 6,00 2,00% 0,12 0,00\nMunicípio de Prestação do Serviço Número Inscrição da Obra Valor Aproximado dos Tributos / Fonte\n\nOUTRAS INFORMAÇÕES\n(1) Esta NFS-e foi emitida com respaldo na Lei nº 14.097/2005; (2) Esta NFS-e substitui o RPS Nº 536573 Série 4F, emitido em 23/10/2026; (3) Data\nde vencimento do ISS desta NFS-e: 10/11/2026;\n\nPágina 1 de 2\n'

PAG35_ANEXO_DA_09125393 = 'IMPOSTO E CONTRIBUIÇÃO SOBRE BENS E SERVIÇOS (IBS E CBS)\nIdentificador: 35503081269034668000156000000912539326102365952141\n\nCPF/CNPJ/NIF do Fornecedor Número da Nota\n\nCódigo de Verificação\n\n69.034.668/0001-56 09125393 FT4E-HMTM\nDESTINATÁRIO\nCPF/CNPJ: NÃO INFORMADO NIF: ===\nNome/Razão Social: ----\nEndereço:  ---- Nº. = Compl: --\nBairro: ---- E-mail. ----\nINFORMAÇÕES DE ENDEREÇO NACIONAL\nMunicípio: ---- CEP: ---\nINFORMAÇÕES DE ENDEREÇO NO EXTERIOR\nPaís: ---- Cidade: ----\nEstado/Província/Região: --—— CEP: ---\nADQUIRENTE\nCPF/CNPJ: 25.311.856/0001-09 NIF:\nNomey/Razão Social: PH GESTAO E CONSULTORIA S.A.\nEndereço: Rua AL AL HUMAITA Nº. 00 Compl.: GUARAJUBA SHOPPING SL 2 SU 102\nBairro: GUARAJUBA E-mail: admguarajubacenter(Ogmail.com\nINFORMAÇÕES DE ENDEREÇO NACIONAL\nMunicípio: 2905701 - Camaçari - BA CEP: 42840-562\nINFORMAÇÕES DE ENDEREÇO NO EXTERIOR\nPaís: ---- Cidade: ----\nEstado/Província/Região: === CEP: ----\nSERVIÇO PRESTADO\n\nLocal de prestação: 3550308 - São Paulo - SP Código indicador da operação: 100301\nLocalidade de incidência: 2905701 - Camaçari - BA\nTipo de operação: | 5-Fornecimento e recebimento do pagamento concomitantes. Operação deuso: Não\n\nCLASSIFICAÇÃO TRIBUTÁRIA\nSituação tributária: 000 - Tributação integral\n\nClassificação tributária: 000001 - Situações tributadas integralmente pelo IBS e CBS.\n\nOUTRAS CLASSIFICAÇÕES\nNBS: 114012100 - Serviços de gestão em processos de negócios\n\nNCM:\n\nValor da multa (R$)\n0,00\n\nValor do juros (R$)\n0,00\n\nValor das Deducões | Base de Cálculo do lalíauota Estadual do | Alíquota Municipal\n\nReducão de Alíquota! Alíquota Efetiva do [Valor Diferido do IBS| Valor do IBS (R$)\n\n'

PAG36_ANEXO_DA_09125393_FIM = 'de IBS e CBS (R$)\n\n10,00\n\nIBS e CBS (R$)\n\n5,88\n\ndo IBS (%)\n\ndo IBS (%)\n\nIBS (%) IBS (%) (R$)\n0,10% 0,00% 0,00% 0,10% - 0,01\nAlíquota da CBS (%) Redução de Alíquota| Alíquota Efetiva da | Valor Diferido da Valor da CBS (R$)\nda CBS (%) CBS (%) CBS (R$)\n0,90% 0,00% 0,90% 0,00 0,05\n\nVALOR TOTAL COBRADO = R$ 16,00\n\nINFORMAÇÕES ADICIONAIS\n\n(1) Esta NFS-e referencia 1 documento(s) para fins de dedução de base cálculo de CBS e/ou IBS.\n\nPágina 2 de 2\n'

ANEXO_33 = [PAG35_ANEXO_DA_09125393, PAG36_ANEXO_DA_09125393_FIM]
AVISO_RECEBIDO = ("Valor total recebido R$ 16,00 usado como ValorServicos; diferença de "
                  "R$ 10,00 para o valor do serviço (R$ 6,00) lançada em ValorDeducoes (repasse)")
VALORES_ESPERADOS = {"ValorServicos": "16.00", "ValorDeducoes": "10.00", "BaseCalculo": "6.00",
                     "Aliquota": "0.02", "ValorIss": "0.12"}


def _lote(monkeypatch, tmp_path, paginas):
    pdf = tmp_path / "lote.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: "\x0c".join(paginas))
    ext = SPPdfExtractor(str(pdf))
    return ext, ext.parse_multiple()


def _xml(nfse):
    root = ET.fromstring(Abrasf201Transformer().transform(nfse))
    ns = {"n": root.tag.split("}")[0][1:]} if root.tag.startswith("{") else {}
    p = "n:" if ns else ""

    def _ler(sec, campos):
        return {c: sec.find(p + c, ns).text for c in campos}

    nfse_v = _ler(root.find(f".//{p}ValoresNfse", ns), list(VALORES_ESPERADOS) + ["ValorLiquidoNfse"])
    serv = root.find(f".//{p}Servico", ns)
    serv_v = _ler(serv.find(f"{p}Valores", ns), list(VALORES_ESPERADOS) + ["IssRetido"])
    return nfse_v, serv_v, serv.find(f"{p}ItemListaServico", ns).text


# --- reconhecimento da página de continuação ---------------------------------

def test_pag34_e_continuacao_de_valores():
    assert sp_ident.eh_pagina_continuacao_valores(PAG34_NOTA_09125393_VALORES)


def test_paginas_com_cabecalho_ou_anexo_nao_sao_continuacao():
    for t in (PAG33_NOTA_09125393_TOPO, PAG31_NOTA_09125394, PAG11_NOTA_08980332,
              PAG32_ANEXO_DA_09125394, PAG35_ANEXO_DA_09125393, PAG36_ANEXO_DA_09125393_FIM):
        assert not sp_ident.eh_pagina_continuacao_valores(t)


# --- lote real: págs. 33 a 36 -----------------------------------------------

def test_nota_deslocada_recebe_os_valores_da_pagina_seguinte(monkeypatch, tmp_path):
    ext, notas = _lote(monkeypatch, tmp_path, [PAG33_NOTA_09125393_TOPO, PAG34_NOTA_09125393_VALORES] + ANEXO_33)
    assert len(notas) == 1
    nota = notas[0]
    assert nota.numero == "09125393"
    assert nota.codigo_verificacao == "FT4E-HMTM"
    assert nota.pagina_origem == 1
    assert nota.servico_codigo == "03205"
    assert nota.valores.valor_liquido_nfse == 16.0
    assert AVISO_RECEBIDO in nota.avisos
    assert not any("extraído como zero" in a for a in nota.avisos)
    # a pág. 34 não é mais descartada; o anexo (págs. 35/36) continua fora
    assert [p["page"] for p in ext.invalid_pages] == [3, 4]


def test_xml_da_nota_deslocada(monkeypatch, tmp_path):
    _, notas = _lote(monkeypatch, tmp_path, [PAG33_NOTA_09125393_TOPO, PAG34_NOTA_09125393_VALORES] + ANEXO_33)
    nfse_v, serv_v, item = _xml(notas[0])
    assert nfse_v == dict(VALORES_ESPERADOS, ValorLiquidoNfse="16.00")
    assert serv_v == dict(VALORES_ESPERADOS, IssRetido="2")
    assert item == "03205"


def test_nota_deslocada_sai_igual_a_nota_de_pagina_unica_do_mesmo_lote(monkeypatch, tmp_path):
    _, notas = _lote(monkeypatch, tmp_path,
                     [PAG31_NOTA_09125394, PAG32_ANEXO_DA_09125394,
                      PAG33_NOTA_09125393_TOPO, PAG34_NOTA_09125393_VALORES] + ANEXO_33)
    assert [n.numero for n in notas] == ["09125394", "09125393"]
    assert [n.pagina_origem for n in notas] == [1, 3]
    assert _xml(notas[0]) == _xml(notas[1])


# --- controles ---------------------------------------------------------------

def test_controle_nota_sp_de_pagina_unica_continua_igual(monkeypatch, tmp_path):
    ext, notas = _lote(monkeypatch, tmp_path, [PAG31_NOTA_09125394, PAG32_ANEXO_DA_09125394])
    assert len(notas) == 1
    assert notas[0].numero == "09125394"
    nfse_v, serv_v, item = _xml(notas[0])
    assert nfse_v == dict(VALORES_ESPERADOS, ValorLiquidoNfse="16.00")
    assert item == "03205"
    assert [p["page"] for p in ext.invalid_pages] == [2]


def test_continuacao_nao_e_anexada_a_nota_que_ja_tem_valores(monkeypatch, tmp_path):
    # Nota de página única (com o próprio bloco de valores) seguida da pág. 34:
    # a pág. 34 não pode ser colada nela.
    ext, notas = _lote(monkeypatch, tmp_path, [PAG31_NOTA_09125394, PAG34_NOTA_09125393_VALORES])
    assert len(notas) == 1
    assert notas[0].numero == "09125394"
    assert {"page": 2, "reason": "Layout não reconhecido"} in ext.invalid_pages


def test_continuacao_sem_nota_sp_antes_e_descartada(monkeypatch, tmp_path):
    ext, notas = _lote(monkeypatch, tmp_path, [PAG34_NOTA_09125393_VALORES, PAG31_NOTA_09125394])
    assert [n.numero for n in notas] == ["09125394"]
    assert {"page": 1, "reason": "Layout não reconhecido"} in ext.invalid_pages


def test_topo_sozinho_continua_zerado_com_aviso(monkeypatch, tmp_path):
    _, notas = _lote(monkeypatch, tmp_path, [PAG33_NOTA_09125393_TOPO] + ANEXO_33)
    assert notas[0].valores.valor_servicos == 0.0
    assert any("extraído como zero" in a for a in notas[0].avisos)
