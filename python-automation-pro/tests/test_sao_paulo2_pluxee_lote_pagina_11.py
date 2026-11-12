"""Regressao: lote PH Gestao 10/2026 - NFS-e de Sao Paulo escaneadas da PLUXEE
(LAYOUT_SAO_PAULO_2), pags. 9 a 12 do PDF "Notas_Fiscais_emitidas_e_recebidas_
10.2026_-_PH_Gestao_SEDE.pdf".

Pag. 9 = nota 08980330 (cod. verificacao WN9H-KAHK); pag. 11 = nota 08980332
(XX95-VZL3), mesmo prestador/tomador/hora de emissao/valores. Pags. 10 e 12 sao
o anexo IBS/CBS ("Pagina 2 de 2") - mas TROCADOS no PDF: a pag. 10 e o anexo da
08980332 e a pag. 12 o da 08980330.

Bug: `_sp_numero_pela_chave` pegava a chave do anexo da pagina SEGUINTE (pag.
12 -> 08980330) e ela vencia a leitura correta da caixa (08980332); depois a
deduplicacao de `parse_multiple` (chave numero+CNPJ) descartava a pag. 11 como
duplicata da pag. 9, sem aviso nenhum.

Textos abaixo = OCR REAL de cada pagina (o `raw_text` que `parse_multiple`
monta no lote, com as linhas sinteticas dos recortes dedicados), sem edicao.
"""
import pytest

from src.extractors import sp_identificador as sp_ident
from src.extractors.pdf_extractor import SPPdfExtractor

PAG9_NOTA_08980330 = 'SP2RET_FEDERAIS: 0,00 0,00 0,00 0,00\nSP2RET_CSLL: 0,00\n\nNúmero da Nota\n08980330\nData e Hora de Emissão\n03/10/2026 15:34:12\nCódigo de Verificação\nWN9H-KAHK\n\nÁ\nDen\n\npa f x Número da Nota\nPREFEITURA DO MUNICÍPIO DE SÃO PAULO 08980330\nSECRETARIA MUNICIPAL DA FAZENDA Data e Hora de Emissão\na 03/10/2026 15:34:12\nNOTA FISCAL ELETRÔNICA DE SERVIÇOS - NFS-e Código de Verificação\n20261006169034668000156 RPS Nº 364969 Série 4F, emitido em 02/10/2026 WN9H-KAHK\n\nIdentificador Nacional: 35503081269034668000156000000898033026105938992304\n\nPRESTADOR DE SERVIÇOS\nCPF/CNPJ: 69.034.668/0001-56 Inscrição Municipal: 7.718.411-4\nNome/Razão Social: PLUXEE BENEFICIOS BRASIL S.A.\nW Endereço: AV DRA RUTH CARDOSO 7221, CONJ 801 901 E 1201 - PINHEIROS - CEP: 05425-902\nMunicípio: São Paulo UF: SP\n\n>>>\nTOMADOR DE SERVIÇOS\n\nNomey/Razão Social: PH GESTAO E CONSULTORIA S.A.\n\nCPF/CNPJ: 25.311.856/0001-09 Inscrição Municipal: ----\nEndereço: Rua AL AL HUMAITA 00, GUARAJUBA SHOPPING SL 2 SU 102 - GUARAJUBA - CEP: 42840-562 |\nMunicípio: Camaçari UF: BA E-mail: admguarajubacenter(ogmail.com\n\nINTERMEDIÁRIO DE SERVIÇOS\nCPF/CNPJ: ---- Nomey/Razão Social: ----\n\nDISCRIMINAÇÃO DE SERVIÇOS\n1 REFEIÇÃO EMV 10.00\nTAR COBRANCA 0.00 N TX DISPON CREDITO 0.00 N TX EMISSAO CARTAO 0.00 N TX ADM SERV 0.00 N TX ENTREGA 6.00 N Tx\nANTECIPAÇÃO CRÉDITO 0.00\nIRRF RECOLHIMENTO EFETUADO PELO EMITENTE CONF. IN/SRF 153/87 R$0.09\nSERVIÇO ENQUADRADO COMO ADMINISTRAÇÃO DE CONVÊNIO\nEntr/Cred 02/10/2026\nNro Pedido.: 43744226/26\nESSA NOTA FISCAL NAO DEVE SER CONTABILIZADA PARA OS EFEITOS DA LEGISLACAO DO PA?.\n\nVALOR TOTAL DO SERVIÇO = R$ 6,00\n\nVALOR TOTAL RECEBIDO = R$ 16,00\n\nContribuição Previdenciária - Retida (R$) IRRF (R$) | COFINS (R$) PIS/PASEP (R$) IPI(R$)\n0,00 0,00 | 0,00 0,00 0,00\nContribuições Sociais - Retidas (R$) | Descrição Contribuições Sociais - Retidas\n0,00 | E\nCódigo do Serviço\n03205 - Fornecimento e administração de vales-refeição, vales-alimentação, vales-transporte e similares\nValor Total das Deduções (R$) Base de Cálculo (R$) Alíquota (%) | Valor do ISS (R$) Crédito Programa da NFP (R$)\n0,00 6,00 2,00% | 0,12 0,00\nMunicípio de Prestação do Serviço Número Inscrição da Obra Valor Aproximado dos Tributos / Fonte\nOUTRAS INFORMAÇÕES\n\n(1) Esta NFS-e foi emitida com respaldo na Lei nº 14.097/2005; (2) Esta NFS-e substitui o RPS Nº 364969 Série 4F, emitido em 02/1 0/2026; (3) Data\nde vencimento do ISS desta NFS-e: 10/11/2026; |\n\nPágina 7 de 2\n\n'

PAG10_ANEXO_DA_08980332 = 'IMPOSTO E CONTRIBUIÇÃO SOBRE BENS E SERVIÇOS T\n\nBS E CBS)\n\nIdentificador: 35503081269034668000156000000898033226105846240117\n\nCPF/CNPJ/NIF do Fornecedor Número da Nota Código de Verificação\n69.034.668/0001-56 08980332 XX95-VZL3\nDESTINATÁRIO\n\nCPF/CNPJ: NÃO INFORMADO NIF: ===\nNome/Razão Social:  ----\nEndereço:  ---- Nº; me Compl: --\nBairro: --== E-mail: ----\n\nINFORMAÇÕES DE ENDEREÇO NACIONAL\nMunicípio:  ---- CEP. ---\n\nINFORMAÇÕES DE ENDEREÇO NO EXTERIOR\nPaís: === Cidade: ----\nEstado/Província/Região: mu CEP: =\nADQUIRENTE\n\nCPF/CNPJ: 25.311.856/0001-09 NiF:\nNome/Razão Social: PH GESTAO E CONSULTORIA S.A.\nEndereço: Rua AL AL HUMAITA Nº. 00 Compl.: - GUARAJUBA SHOPPING SL 2 SU 102\nBairro: GUARAJUBA E-mail: admguarajubacenterGOgmail.com\n\nINFORMAÇÕES DE ENDEREÇO NACIONAL\nMunicípio: 2905701 - Camaçari - BA CEP: 42840-562\n\nINFORMAÇÕES DE ENDEREÇO NO EXTERIOR\nPaís: ---- Cidade: ----\nEstado/Província/Região: m.— CEP: =\nSERVIÇO PRESTADO\nLocal de prestação: 3550308 - São Paulo - SP Código indicador da operação: 100301\nLocalidade de incidência: 2905701 - Camaçari - BA a.\nTipo de operação:  5-Fornecimento e recebimento do pagamento concomitantes. Operação de uso: Não\nCLASSIFICAÇÃO TRIBUTÁRIA\nSituação tributária: 000 - Tributação integral\nClassificação tributária: 000001 - Situações tributadas integralmente pelo IBS e CBS.\nOUTRAS CLASSIFICAÇÕES\nNBS: 114012100 - Serviços de gestão em processos de negócios\nNCM: ==. e\nValor da multa (R$) Valor do juros (R$)\n0,00 . 0,00\nValor das Deduções | Base de Cálculo do |Alíquota Estadual do Alíquota Municipal |Redução de Alíquota| Alíquota Efetiva do | Valor Diferido do IBS| Valor do IBS (R$)\nde IBS e CBS (R$) IBS e CBS (R$) IBS (%) do IBS (%) do IBS (%) IBS (%) (R$)\n0,10% 0,00% 0,00% 0,10% - 0,01\n10,00 588 Alíquota da CBS (%) Redução de Alíquota| Alíquota Efetiva da | Valor Diferido da | Valor da CBS (R$)\n, À)\nda CBS (%) CBS (%) CBS (R$)\n0,90% 0,00% 0,90% 0,00 0,05\nVALOR TOTAL COBRADO = R$ 16,00\nINFORMAÇÕES ADICIONAIS\n\n(1) Esta NFS-e referencia 1 documento(s) para fins de dedução de base cálculo de CBS e/ou IBS.\n\nPágina2 de 2\n'

PAG11_NOTA_08980332 = "\nSP2RET_FEDERAIS: 0,00 0,00 0,00 0,00\nSP2RET_CSLL: 0,00\n\nNúmero da Nota\n08980332\nData e Hora de Emissão\n03/10/2026 15:34:12\nCódigo de Verificação\nXX95-VZL3\n\n: = Número da Nota\nPREFEITURA DO MUNICÍPIO DE SÃO PAULO . 08980332\nSECRETARIA MUNICIPAL DA FAZENDA : Data e Hora de Emissão\n' 03/10/2026 15:34:12\n* NOTA FISCAL ELETRÔNICA DE SERVIÇOS - NFS-e . Código de Verificação\nana oo fiesdáissaniviso RPS Nº 364971 Série 4F, emitido em 02/10/2026 XX95-VZL3\nPRESTADOR DE SERVIÇOS\nCPF/CNPJ: 69.034.668/0001-56 Inscrição Municipal: 7.718.411-4\nNome/Razão Social: PLUXEE BENEFICIOS BRASIL S.A.\nEndereço: AV DRA RUTH CARDOSO 7221, CONJ 801 901 E 1201 - PINHEIROS - CEP: 05425-902\nMunicípio: São Paulo UF: SP\nTOMADOR DE SERVIÇOS\nNomey/Razão Social: PH GESTAO E CONSULTORIA S.A.\nCPF/CNPJ: 25.311.856/0001-09 Inscrição Municipal: ----\nEndereço: Rua AL AL HUMAITA 00, GUARAJUBA SHOPPING SL 2 SU 102 - GUARAJUBA - CEP: 42840-562\nMunicípio: Camaçari UF: BA E-mail: admguarajubacenter(ogmail.com\nINTERMEDIÁRIO DE SERVIÇOS\nCPF/CNPJ: ---- Nomey/Razão Social: ----\n\nDISCRIMINAÇÃO DE SERVIÇOS\n1 ALIMENTAÇÃO EMV 10.00\nGESTAO COBRANCA 0.00 N TX DISPON CREDITO 0.00 N TX EMISSAO CARTAO 0.00 N TX ADMIN 0.00 N TX ENTREGA 6.00\nIRRF RECOLHIMENTO EFETUADO PELO EMITENTE CONF. IN/SRF 153/87 R$0.09\nSERVIÇO ENQUADRADO COMO ADMINISTRAÇÃO DE CONVÊNIO\nEntr/Cred 05/10/2026\nNro Pedido.: 43744226/26\nESSA NOTA FISCAL NAO DEVE SER CONTABILIZADA PARA OS EFEITOS DA LEGISLACAO DO PAT\n\nVALOR TOTAL DO SERVIÇO = R$ 6,00\nVALOR TOTAL RECEBIDO = R$ 16,00\n\nContribuição Previdenciária - Retida (R$) IRRF (R$) COFINS (R$) PIS/PASEP (R$) IPI (R$)\n0,00 0,00 0,00 0,00 0,00\nContribuições Sociais - Retidas (R$) Descrição Contribuições Sociais - Retidas\n0,00 -\n\nCódigo do Serviço\n03205 - Fornecimento e administração de vales-refeição, vales-alimentação, vales-transporte e similares\n\nValor Total das Deduções (R$) Base de Cálculo (R$) Alíquota (%) Valor do ISS (R$) Crédito Programa da NFP (R$)\n0,00 6,00 2,00% 0,12 0,00\nMunicípio de Prestação do Serviço Número Inscrição da Obra Valor Aproximado dos Tributos / Fonte\nOUTRAS INFORMAÇÕES\n\n(1) Esta NFS-e foi emitida com respaldo na Lei nº 14.097/2005; (2) Esta NFS-e substitui o RPS Nº 364971 Série 4F, emitido em 02/1 0/2026; (3) Data\nde vencimento do ISS desta NFS-e: 10/11/2026;\n\nPágina dez\n\n"

PAG12_ANEXO_DA_08980330 = 'IMPOSTO E CONTRIBUIÇÃO SOBRE BENS E SERVIÇOS (IBS E CBS)\nIdentificador: 35503081269034668000156000000898033026105938992304\n\nCPF/CNPJ/NIF do Fornecedor Número da Nota Código de Verificação\n69.034.668/0001-56 08980330 WN9H-KAHK\nDESTINATÁRIO E\nCPF/CNPJ: NÃO INFORMADO NIF; ===\nNomey/Razão Social: ----\nEndereço:  ---- Nº; Compl: --\nBairro: E-mail: -===\nINFORMAÇÕES DE ENDEREÇO NACIONAL\nMunicípio:  ---- CEP: -—\nINFORMAÇÕES DE ENDEREÇO NO EXTERIOR\nPaís: === Cidade: ----\nEstado/Província/Região: -.— CEP: =\nADQUIRENTE\nCPF/CNPJ: 25.311.856/0001-09 NIF:\nNome/Razão Social: PH GESTAO E CONSULTORIA S.A.\nEndereço: Rua AL AL HUMAITA Nº: 00 Compl: GUARAJUBA SHOPPING SL 2 SU 102\nBairro: GUARAJUBA E-mail: admguarajubacenter(ogmail.com\nINFORMAÇÕES DE ENDEREÇO NACIONAL\nMunicípio: 2905701 - Camaçari - BA CEP: 42840-562\nINFORMAÇÕES DE ENDEREÇO NO EXTERIOR\nPaís: --=— Cidade: ----\nEstado/Província/Região: m.— CEP:\nSERVIÇO PRESTADO\n\nLocal de prestação: 3550308 - São Paulo - SP Código indicador da operação: 100301\nLocalidade de incidência: 2905701 - Camaçari - BA\nTipo de operação:  5-Fornecimento e recebimento do pagamento concomitantes. Operação de uso: Não\n\nCLASSIFICAÇÃO TRIBUTÁRIA\n\nSituação tributária: 000 - Tributação integral\nClassificação tributária: 000001 - Situações tributadas integralmente pelo IBS e CBS.\nOUTRAS CLASSIFICAÇÕES\nNBS: 114012100 - Serviços de gestão em processos de negócios\nNCM; = )\nValor da multa (R$) Valor do juros (R$)\n0,00 0,00\nValor das Deduções | Base de Cálculo do |Alíquota Estadual do| Alíquota Municipal |Redução de Alíquota| Alíquota Efetiva do |Valor Diferido do IBS| Valor do IBS (R$)\nde IBS e CBS (R$) IBS e CBS (R$) IBS (%) do IBS (%) do IBS (%) IBS (%) (R$)\n0,10% 0,00% 0,00% 0,10% m 0,01\n10,00 588 Alíquota da CBS (%) Redução de Alíquota] Alíquota Efetiva da | Valor Diferido da | Valor da CBS (R$)\n. da CBS (%) ces (x) . CBS (R$)\n0,90% 0,00% 0,90% = 0,00 0,05\nVALOR TOTAL COBRADO = R$ 16,00 q\nINFORMAÇÕES ADICIONAIS\n\n(1) Esta NFS-e referencia 1 documento(s) para fins de dedução de base cálculo de CBS e/ou IBS.\n\nPágina 2 de2\n'


def _lote(monkeypatch, tmp_path, paginas):
    pdf = tmp_path / "lote.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: "".join(paginas))
    ext = SPPdfExtractor(str(pdf))
    return ext, ext.parse_multiple()


LOTE_REAL = [PAG9_NOTA_08980330, PAG10_ANEXO_DA_08980332, PAG11_NOTA_08980332, PAG12_ANEXO_DA_08980330]


# ---------------------------------------------------------------------------
# sp_identificador: codigo de verificacao amarra o anexo a sua nota
# ---------------------------------------------------------------------------

def test_anexos_reais_trazem_o_codigo_de_verificacao_da_propria_nota():
    assert sp_ident.codigo_verificacao_anexo(PAG10_ANEXO_DA_08980332) == "XX95-VZL3"
    assert sp_ident.codigo_verificacao_anexo(PAG12_ANEXO_DA_08980330) == "WN9H-KAHK"


def test_codigos_lidos_nas_paginas_das_notas():
    assert sp_ident.codigos_verificacao_nota(PAG9_NOTA_08980330) == {"WN9H-KAHK"}
    assert sp_ident.codigos_verificacao_nota(PAG11_NOTA_08980332) == {"XX95-VZL3"}


def test_anexo_trocado_e_reconhecido_como_de_outra_nota():
    cvs11 = sp_ident.codigos_verificacao_nota(PAG11_NOTA_08980332)
    assert sp_ident.anexo_e_de_outra_nota("WN9H-KAHK", cvs11)
    assert not sp_ident.anexo_e_de_outra_nota("XX95-VZL3", cvs11)


@pytest.mark.parametrize("a,b,diverge", [
    ("XX95-VZL3", "WN9H-KAHK", True),
    ("XX95-VZL3", "XX95-VZL3", False),
    ("XX95-VZL3", "XX9S-VZL3", False),   # S/5: confusao de OCR, mesma nota
    ("XX95-VZL3", "XX95-VZ13", False),   # L/1
    ("XX95-VZL3", "XX95-VZLE", False),   # 1 posicao trocada nao prova nada
    ("XX95-VZL3", None, False),          # ilegivel de um lado: sem prova
])
def test_codigos_verificacao_divergem(a, b, diverge):
    assert sp_ident.codigos_verificacao_divergem(a, b) is diverge


# ---------------------------------------------------------------------------
# parse_multiple no lote real
# ---------------------------------------------------------------------------

def test_lote_real_gera_as_duas_notas_com_numero_e_codigo_certos(monkeypatch, tmp_path):
    _, notas = _lote(monkeypatch, tmp_path, LOTE_REAL)
    por_pagina = {n.pagina_origem: (n.numero, n.codigo_verificacao) for n in notas}
    assert por_pagina == {1: ("08980330", "WN9H-KAHK"), 3: ("08980332", "XX95-VZL3")}
    for n in notas:
        assert n.prestador.cnpj_cpf == "69034668000156"
        assert n.tomador.cnpj_cpf == "25311856000109"
        assert not any("duplicata" in a or "repetido" in a for a in n.avisos)


def test_lote_real_discriminacoes_nao_se_misturam(monkeypatch, tmp_path):
    _, notas = _lote(monkeypatch, tmp_path, LOTE_REAL)
    por_numero = {n.numero: n.discriminacao for n in notas}
    assert "REFEIÇÃO" in por_numero["08980330"]
    assert "ALIMENTAÇÃO" in por_numero["08980332"]


def test_nota_da_pagina_11_tem_o_numero_da_chave_do_anexo_certo(monkeypatch, tmp_path):
    """Mesmo sem o anexo da pagina seguinte (pag. 12 removida), a chave
    08980332 vem da pag. 10, reconhecida pelo codigo de verificacao."""
    ext, notas = _lote(monkeypatch, tmp_path, [PAG9_NOTA_08980330, PAG10_ANEXO_DA_08980332, PAG11_NOTA_08980332])
    assert sorted(n.numero for n in notas) == ["08980330", "08980332"]
    assert ext._sp_cv_anexos_doc == {1: "XX95-VZL3"}


def test_anexos_na_ordem_certa_continuam_funcionando(monkeypatch, tmp_path):
    _, notas = _lote(monkeypatch, tmp_path, [PAG9_NOTA_08980330, PAG12_ANEXO_DA_08980330,
                                            PAG11_NOTA_08980332, PAG10_ANEXO_DA_08980332])
    assert {n.pagina_origem: n.numero for n in notas} == {1: "08980330", 3: "08980332"}


# ---------------------------------------------------------------------------
# Deduplicacao do lote: notas distintas nunca somem; duplicata real avisa
# ---------------------------------------------------------------------------

def test_mesmo_numero_com_codigos_diferentes_mantem_as_duas_notas_com_aviso(monkeypatch, tmp_path):
    """Se o numero ainda sair igual por qualquer motivo (aqui: caixa da pag. 11
    forcada a 08980330 e sem anexos), as duas notas ficam, com aviso."""
    pag11_numero_errado = PAG11_NOTA_08980332.replace("08980332", "08980330")
    _, notas = _lote(monkeypatch, tmp_path, [PAG9_NOTA_08980330, pag11_numero_errado])
    assert [(n.pagina_origem, n.codigo_verificacao) for n in notas] == [(1, "WN9H-KAHK"), (2, "XX95-VZL3")]
    for n in notas:
        assert any("repetido no lote" in a and "WN9H-KAHK" in a and "XX95-VZL3" in a for a in n.avisos)


def test_duplicata_verdadeira_e_descartada_com_aviso_visivel(monkeypatch, tmp_path, capsys):
    """A mesma nota (mesmo numero, CNPJ e codigo) repetida mais adiante no lote
    continua descartada - mas nunca em silencio: console + `invalid_pages`."""
    ext, notas = _lote(monkeypatch, tmp_path, [PAG9_NOTA_08980330, PAG11_NOTA_08980332, PAG9_NOTA_08980330])
    assert {n.pagina_origem: n.numero for n in notas} == {1: "08980330", 2: "08980332"}
    assert {"page": 3, "reason": "Duplicata da nota 08980330 (pág 1)"} in ext.invalid_pages
    assert "[AVISO] Nota 08980330 (pág 1): Página 3 descartada como duplicata" in capsys.readouterr().out


def test_duplicata_sem_codigo_de_verificacao_legivel_avisa_tambem_na_nota(monkeypatch, tmp_path):
    """Sem codigo legivel num dos lados a identidade nao esta provada: o
    descarte tambem vai para os avisos da nota mantida."""
    original = SPPdfExtractor._extrair_codigo_verificacao

    def codigo_ilegivel_na_pagina_3(self):
        # Sentinela do conversor para codigo nao lido.
        return "XXXX-XXXX" if getattr(self, "_pagina_hint", None) == 3 else original(self)

    monkeypatch.setattr(SPPdfExtractor, "_extrair_codigo_verificacao", codigo_ilegivel_na_pagina_3)
    ext, notas = _lote(monkeypatch, tmp_path, [PAG9_NOTA_08980330, PAG11_NOTA_08980332, PAG9_NOTA_08980330])
    nota9 = next(n for n in notas if n.pagina_origem == 1)
    assert len(notas) == 2
    assert any("Página 3 descartada como duplicata" in a for a in nota9.avisos)


def test_paginas_vizinhas_da_mesma_nota_continuam_unidas(monkeypatch, tmp_path):
    """Mesmo numero e mesmo codigo em paginas vizinhas = continuacao (o guarda
    contra fusao so age com codigos de verificacao divergentes)."""
    _, notas = _lote(monkeypatch, tmp_path, [PAG9_NOTA_08980330, PAG9_NOTA_08980330])
    assert len(notas) == 1
