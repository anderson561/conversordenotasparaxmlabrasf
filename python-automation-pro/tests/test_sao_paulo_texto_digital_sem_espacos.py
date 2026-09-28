# -*- coding: utf-8 -*-
r"""São Paulo/SP (LAYOUT_SAO_PAULO / LAYOUT_SAO_PAULO_2), nota real nº
05299158, FLASH TECNOLOGIA E INSTITUICAO DE PAGAMENTO LTDA -> MASSA
ALIMENTAÇÃO E SERVICOS S/A. (Salvador/BA), R$ 40,18. PDF de 2 páginas
(a 2ª é o bloco federal IBS/CBS da Reforma Tributária), **DIGITAL** (nunca
escaneado) - arquivo real do usuário
("32223020000118-5299158.pdf").

Causa-raiz: exatamente a MESMA patologia já corrigida no PR #116 para
LAYOUT_NACIONAL/LAYOUT_NACIONAL_REFORMA (`test_danfse_nacional_reforma_
texto_digital_sem_espacos.py`) - `pdfminer.high_level.extract_text()` extrai
o texto embutido desta nota SEM NENHUM ESPAÇO entre palavras/rótulos/valores
(3696 caracteres, ZERO espaços nas 2 páginas) - mas ocorrendo num layout
DIFERENTE (São Paulo/SP, não a DANFSe Nacional). O gate que decide quando
`_texto_digital_sem_espacos()` desvia uma página para OCR (dentro de
`parse_multiple()`) era restrito a `LAYOUT_NACIONAL`/`LAYOUT_NACIONAL_
REFORMA` - generalizado para qualquer layout, já que a patologia é uma
característica do TEXTO/gerador do PDF, não do layout específico. Sem o
fix, o XML saía com "Prestador Não Identificado", ValorServicos=0.00,
endereço do prestador virando um blob colado sem espaço nenhum e Uf do
prestador saindo "BA" (o fallback genérico de UF, não a Bahia de verdade -
o prestador é de São Paulo).

O texto digital abaixo (`RAW_DIGITAL_SEM_ESPACOS`) é o retorno REAL e
verbatim de `extract_text()` no PDF original (via `repr()`), já incluindo o
`\x0c` que separa as 2 páginas.

Os textos OCR abaixo (`MOCK_OCR_PAGINA1`/`MOCK_OCR_PAGINA2`) são o retorno
REAL do Tesseract via `_ocr_page()` no MESMO PDF (uma página por vez) -
incluindo os quirks de OCR desta nota: o Código de Verificação sai com um
"6" espúrio a mais ("YTH8-X46GY"/"YTH8-X46Y" em vez do real "YTH8-X4GY" -
por isso `_extrair_codigo_verificacao` prioriza o texto digital original
guardado em `_texto_digital_glued_pagina`, mais confiável que o OCR para
esse token compacto) e o endereço do tomador com o tipo de logradouro
duplicado "rua rua senador theotônio vilela" (erro do PRÓPRIO emissor,
confirmado na imagem renderizada em 300 DPI - não é rótulo colado pelo
parser - corrigido por `_remover_tipo_logradouro_duplicado`, já usado em
João Pessoa)."""
import os

from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_SAO_PAULO

RAW_DIGITAL_SEM_ESPACOS = 'PREFEITURADOMUNICÍPIODESÃOPAULOSECRETARIAMUNICIPALDAFAZENDANOTAFISCALELETRÔNICADESERVIÇOS-NFS-eNúmerodaNotaDataeHoradeEmissãoCódigodeVerificação20260804u32223020000118RPSNº3751677SérieNFSE2,emitidoem31/07/20260529915803/08/202611:54:50YTH8-X4GYIdentificadorNacional:35503081232223020000118000000529915826081956033853PRESTADORDESERVIÇOSCPF/CNPJ:InscriçãoMunicipal:Nome/RazãoSocial:Endereço:32.223.020/0001-186.141.672-0FLASHTECNOLOGIAEINSTITUICAODEPAGAMENTOLTDAREUGENIODEMEDEIROS242,ANDAR4-PINHEIROS-CEP:05425-000Município:SãoPauloUF:SPTOMADORDESERVIÇOSNome/RazãoSocial:CPF/CNPJ:InscriçãoMunicipal:Endereço:Município:UF:E-mail:MASSAALIMENTAÇÃOESERVICOSS/A.09.033.381/0001-80----ruaruasenadortheotôniovilela110,SALAS203E204EDIFCIDADELA-parquebelavista-CEP:40279-435SalvadorBAcx.ba@prc.com.brINTERMEDIÁRIODESERVIÇOSCPF/CNPJ:Nome/RazãoSocial:--------DISCRIMINAÇÃODESERVIÇOSValorTotal-R$40,18Prestaçãodeserviçosjulhode2026BenefíciosFlash+TotalPassValorNF:R$5,74/mêsmultiplicadopor7colaboradorescontratadosPagamentoporboletobancárioVALORTOTALDOSERVIÇO=R$40,18ContribuiçãoPrevidenciária-Retida(R$)IRRF(R$)COFINS(R$)PIS/PASEP(R$)IPI(R$)0,000,003,050,660,00ContribuiçõesSociais-Retidas(R$)DescriçãoContribuiçõesSociais-Retidas0,000-PIS/COFINS/CSLLNãoRetidos.CódigodoServiço06298-Agenciamento,corret.Intermed.bensmóveis,nãoabrangidosemoutrositens,porquaisquermeios.ValorTotaldasDeduções(R$)BasedeCálculo(R$)Alíquota(%)ValordoISS(R$)CréditoProgramadaNFP(R$)0,0040,185,00%2,000,00MunicípiodePrestaçãodoServiçoNúmeroInscriçãodaObraValorAproximadodosTributos/Fonte---OUTRASINFORMAÇÕES(1)EstaNFS-efoiemitidacomrespaldonaLeinº14.097/2005;(2)EstaNFS-esubstituioRPSNº3751677SérieNFSE2,emitidoem31/07/2026;(3)DatadevencimentodoISSdestaNFS-e:10/08/2026;(4)OISSrelativoaestaNFS-edeveráserrecolhidodeacordocomasregrasdaDES-IF,medianteoenviodadeclaraçãoeaposterioremissãodarespectivaguiadepagamentopormeiodosistemadaDES-IF.;(5)InformaçõespreenchidasnoscamposdePISeCOFINSsãoreferentesaosvalorestotaissobreaoperação.;Página1de2\x0cIMPOSTOECONTRIBUIÇÃOSOBREBENSESERVIÇOS(IBSECBS)Identificador:35503081232223020000118000000529915826081956033853CPF/CNPJ/NIFdoFornecedorNúmerodaNotaCódigodeVerificação32.223.020/0001-1805299158YTH8-X4GYDESTINATÁRIOCPF/CNPJ:NIF:Nome/RazãoSocial:Endereço:Nº:Compl.:Bairro:E-mail:INFORMAÇÕESDEENDEREÇONACIONALMunicípio:CEP:INFORMAÇÕESDEENDEREÇONOEXTERIORPaís:Cidade:Estado/Província/Região:CEP:NÃOINFORMADO--------------------------------------------------ADQUIRENTECPF/CNPJ:NIF:Nome/RazãoSocial:Endereço:Nº:Compl.:Bairro:E-mail:INFORMAÇÕESDEENDEREÇONACIONALMunicípio:CEP:INFORMAÇÕESDEENDEREÇONOEXTERIORPaís:Cidade:Estado/Província/Região:CEP:09.033.381/0001-80MassaAlimentaçãoeServicosS/A.ruaruasenadortheotôniovilela110SALAS203E204EDIFCIDADELAparquebelavistacx.ba@prc.com.br2927408-Salvador-BA40279-435----------------SERVIÇOPRESTADOLocaldeprestação:Códigoindicadordaoperação:Localidadedeincidência:Tipodeoperação:Operaçãodeuso:2927408-Salvador-BA1003012927408-Salvador-BA-----NãoCLASSIFICAÇÃOTRIBUTÁRIASituaçãotributária:000-TributaçãointegralClassificaçãotributária:000001-SituaçõestributadasintegralmentepeloIBSeCBS.OUTRASCLASSIFICAÇÕESNBS:NCM:114062000-Aquisiçãoouvendadeespaçooutempoparapropaganda,sobcomissão----Valordosserviçosantesdostributos(R$)Valordamulta(R$)Valordojuros(R$)34,46--ValordasDeduçõesdeIBSeCBS(R$)BasedeCálculodoIBSeCBS(R$)AlíquotaEstadualdoIBS(%)AlíquotaMunicipaldoIBS(%)ReduçãodeAlíquotadoIBS(%)AlíquotaEfetivadoIBS(%)ValorDiferidodoIBS(R$)ValordoIBS(R$)0,10%0,00%0,00%0,10%-0,03AlíquotadaCBS(%)ReduçãodeAlíquotadaCBS(%)AlíquotaEfetivadaCBS(%)ValorDiferidodaCBS(R$)ValordaCBS(R$)0,90%0,00%0,90%0,000,310,0034,46VALORTOTALCOBRADO=R$40,18INFORMAÇÕESADICIONAISPágina2de2\x0c'

MOCK_OCR_PAGINA1 = 'IRRF (R$) CSLL (R$) COFINS (R$) PIS/PASEP (R$)\n0,00 0,00 3,05 0,66\nCódigo do Serviço\n06298 - Agenciamento, corret. Intermed. bens móveis, não abrangidos em outros itens, por quaisquer meios.\nValor Total das Deduções Alíquota Valor do ISS\n0,00 5,00% 2,00\n\nNúmero da Nota\n05299158\nData e Hora de Emissão\n03/08/2026 11:54:50\nCódigo de Verificação\nYTH8-X46GY\n\ní a Nú da Not:\nPREFEITURA DO MUNICÍPIO DE SÃO PAULO 05299158\nSECRETARIA MUNICIPAL DA FAZENDA Data e Hora de Emissão\nR 03/08/2026 11:54:50\nNOTA FISCAL ELETRÔNICA DE SERVIÇOS - NFS-e Código de Verificação\n20260804U32223020000118 RPS Nº 3751677 Série NFSE2, emitido em 31/07/2026 YTH8-X4GY\n\nIdentificador Nacional: 35503081232223020000118000000529915826081956033853\n\nPRESTADOR DE SERVIÇOS\nCPF/CNPJ: 32.223.020/0001-18 Inscrição Municipal: 6.141.672-0\nNome/Razão Social: FLASH TECNOLOGIA E INSTITUICAO DE PAGAMENTO LTDA\nEndereço: R EUGENIO DE MEDEIROS 242, ANDAR 4 - PINHEIROS - CEP: 05425-000\nMunicípio: São Paulo UF: SP\n\nTOMADOR DE SERVIÇOS\nNomey/Razão Social: MASSA ALIMENTAÇÃO E SERVICOS S/A.\nCPF/CNPJ: 09.033.381/0001-80 Inscrição Municipal: ----\nEndereço: rua rua senador theotônio vilela 110, SALAS 203 E 204 EDIF CIDADELA - parque bela vista - CEP: 40279-435\nMunicípio: Salvador UF: BA E-mail: cex.baQopre.com.br\n\nINTERMEDIÁRIO DE SERVIÇOS\nCPF/CNPJ: ---- Nomey/Razão Social: ----\n\nDISCRIMINAÇÃO DE SERVIÇOS\nValor Total - R$ 40,18\n\nPrestação de serviços julho de 2026\n\nBenefícios Flash + TotalPass\nValor NF: R$ 5,74 /mês multiplicado por 7 colaboradores contratados\n\nPagamento por boleto bancário\n\nVALOR TOTAL DO SERVIÇO = R$ 40,18\n\nContribuição Previdenciária - Retida (R$) IRRF (R$) COFINS (R$) PIS/PASEP (R$) IPI(RS)\n0,00 0,00 3,05 0,66 0,00\nContribuições Sociais - Retidas (R$) Descrição Contribuições Sociais - Retidas\n0,00 O - PIS/COFINS/CSLL Não Retidos.\n\nCódigo do Serviço\n06298 - Agenciamento, corret. Intermed. bens móveis, não abrangidos em outros itens, por quaisquer meios.\n\nValor Total das Deduções (R$) Base de Cálculo (R$) Alíquota (%) Valor do ISS (R$) Crédito Programa da NFP (R$)\n0,00 40,18 5,00% 2,00 0,00\nMunicípio de Prestação do Serviço Número Inscrição da Obra Valor Aproximado dos Tributos / Fonte\n\nOUTRAS INFORMAÇÕES\n(1) Esta NFS-e foi emitida com respaldo na Lei nº 14.097/2005; (2) Esta NFS-e substitui o RPS Nº 3751677 Série NFSE2, emitido em 31/07/2026; (3)\nData de vencimento do ISS desta NFS-e: 10/08/2026; (4) O ISS relativo a esta NFS-e deverá ser recolhido de acordo com as regras da DES-IF, mediante\no envio da declaração e a posterior emissão da respectiva guia de pagamento por meio do sistema da DES-IF.; (5) Informações preenchidas nos\ncampos de PIS e COFINS são referentes aos valores totais sobre a operação.;\n\nPágina 1 de 2\n'

MOCK_OCR_PAGINA2 = 'IMPOSTO E CONTRIBUIÇÃO SOBRE BENS E SERVIÇOS (IBS E CBS)\nIdentificador: 35503081232223020000118000000529915826081956033853\n\nCPF/CNPJ/NIF do Fornecedor\n\nNúmero da Nota\n\nCódigo de Verificação\n\n32.223.020/0001-18 05299158 YTH8-X46Y\nDESTINATÁRIO\nCPF/CNPJ: NÃO INFORMADO NIF: ==\nNome/Razão Social: ----\nEndereço:  ---- Nº: = Compl: --\nBairro: ---- E-mail: ----\nINFORMAÇÕES DE ENDEREÇO NACIONAL\nMunicípio: ---- CEP: ----\nINFORMAÇÕES DE ENDEREÇO NO EXTERIOR\nPaís: ---- Cidade: ----\nEstado/Província/Região: -——— CEP: ----\nADQUIRENTE\nCPF/CNPJ: 09.033.381/0001-80 NIF:\nNome/Razão Social: Massa Alimentação e Servicos S/A.\nEndereço: rua rua senador theotônio vilela Nº: 110 Compl: SALAS 203 E 204 EDIF CIDADELA\nBairro: parque bela vista E-mail: cx.baQpre.com.br\nINFORMAÇÕES DE ENDEREÇO NACIONAL\nMunicípio: 2927408 - Salvador - BA CEP: 40279-435\nINFORMAÇÕES DE ENDEREÇO NO EXTERIOR\nPaís: ---- Cidade: ----\nEstado/Província/Região: -——— CEP: ----\nSERVIÇO PRESTADO\n\nLocal de prestação: 2927408 - Salvador - BA Código indicador da operação: 100301\nLocalidade de incidência: 2927408 - Salvador - BA\nTipo de operação:  ----- Operação de uso: Não\n\nSituação tributária:\n\n000 - Tributação integral\n\nCLASSIFICAÇÃO TRIBUTÁRIA\n\nClassificação tributária: 000001 - Situações tributadas integralmente pelo IBS e CBS.\n\nNBS:\nNCM:\n\nOUTRAS CLASSIFICAÇÕES\n\n114062000 - Aquisição ou venda de espaço ou tempo para propaganda, sob comissão\n\nValor dos serviços antes dos tributos (R$)\n\nValor da multa (R$)\n\nValor do juros (R$)\n\nValor das Deduções\nde IBS e CBS (R$)\n\n0,00\n\nBase de Cálculo do\nIBS e CBS (R$)\n\n34,46 - -\nAlíquota Estadual do| Alíquota Municipal |Redução de Alíquota| Alíquota Efetiva do |Valor Diferido do IBS| Valor do IBS (R$)\nIBS (%) do IBS (%) do IBS (%) IBS (%) (R$)\n0,10% 0,00% 0,00% 0,10% - 0,03\n3446 Alíquota da CBS (%) Redução de Alíquota| Alíquota Efetiva da | Valor Diferido da Valor da CBS (R$)\nº da CBS (%) CBS (%) CBS (R$)\n0,90% 0,00% 0,90% 0,00 0,31\n\nVALOR TOTAL COBRADO = R$ 40,18\n\nINFORMAÇÕES ADICIONAIS\n\nPágina 2 de 2\n'


def _dummy(nome):
    caminho = f"tests/{nome}"
    os.makedirs("tests", exist_ok=True)
    with open(caminho, "wb") as f:
        f.write(b"%PDF-1.4")
    return caminho


def test_texto_digital_sem_espacos_detecta_a_patologia_em_sao_paulo():
    """Mesma densidade quase-zero de espaços já coberta genericamente por
    `_texto_digital_sem_espacos` (ver o teste homônimo da DANFSe Nacional),
    confirmada aqui também contra o texto REAL desta nota São Paulo/SP -
    prova de que a detecção não é amarrada a nenhum layout específico."""
    assert SPPdfExtractor._texto_digital_sem_espacos(RAW_DIGITAL_SEM_ESPACOS)


def test_pdf_digital_sem_espacos_sao_paulo_cai_para_ocr_e_extrai_nota_corretamente(monkeypatch):
    """Reproduz o caminho real desta nota: `extract_text()` (pdfminer) devolve
    o texto digital colado sem espaços nas 2 páginas; o extrator detecta a
    patologia em CADA página (gate GENERALIZADO, sem restrição de layout) e
    usa `_ocr_page()` especificamente para elas, cujo retorno (mockado aqui
    com o OCR real de cada página) alimenta a extração de
    LAYOUT_SAO_PAULO_2."""
    caminho = _dummy("dummy_sao_paulo_flash_05299158.pdf")
    monkeypatch.setattr(
        "src.extractors.pdf_extractor.extract_text", lambda path: RAW_DIGITAL_SEM_ESPACOS)

    def _fake_ocr_page(self, page_num):
        if page_num == 0:
            return MOCK_OCR_PAGINA1
        if page_num == 1:
            return MOCK_OCR_PAGINA2
        return ""

    monkeypatch.setattr(SPPdfExtractor, "_ocr_page", _fake_ocr_page)
    try:
        nfse_list = SPPdfExtractor(caminho).parse_multiple()
    finally:
        if os.path.exists(caminho):
            os.remove(caminho)

    assert len(nfse_list) == 1
    nfse = nfse_list[0]

    assert nfse.numero == "05299158"
    assert nfse.data_emissao.strftime("%Y-%m-%dT%H:%M:%S") == "2026-08-03T11:54:50"
    # O OCR desta nota lê o código com um "6" espúrio a mais em AMBAS as
    # páginas ("YTH8-X46GY"/"YTH8-X46Y") - o valor correto só sobrevive no
    # texto digital original (guardado em `_texto_digital_glued_pagina`),
    # priorizado por `_extrair_codigo_verificacao` para LAYOUT_SAO_PAULO_2.
    assert nfse.codigo_verificacao == "YTH8-X4GY"

    p = nfse.prestador
    assert p.cnpj_cpf == "32223020000118"
    assert p.razao_social == "FLASH TECNOLOGIA E INSTITUICAO DE PAGAMENTO LTDA"
    assert p.inscricao_municipal == "61416720"
    assert p.endereco.logradouro == "R EUGENIO DE MEDEIROS"
    assert p.endereco.numero == "242"
    assert p.endereco.complemento == "ANDAR 4"
    assert p.endereco.bairro == "PINHEIROS"
    assert p.endereco.codigo_municipio == "3550308"
    assert p.endereco.municipio == "São Paulo"
    # UF do PRESTADOR - achado real: sem o fix da patologia acima, a
    # extração inteira falhava e este campo saía "BA" (fallback genérico),
    # apesar do prestador ser de São Paulo. Com o texto chegando via OCR,
    # sai correto sozinho, sem precisar de nenhuma correção própria deste
    # campo.
    assert p.endereco.uf == "SP"
    assert p.endereco.cep == "05425000"

    t = nfse.tomador
    assert t.cnpj_cpf == "09033381000180"
    assert t.razao_social == "MASSA ALIMENTAÇÃO E SERVICOS S/A"
    assert t.inscricao_municipal is None
    # Tipo de logradouro duplicado ("rua rua ...") - erro do PRÓPRIO emissor
    # (confirmado na imagem renderizada em 300 DPI), corrigido por
    # `_remover_tipo_logradouro_duplicado` (mesma correção já usada em João
    # Pessoa, reaproveitada aqui em vez de duplicada).
    assert t.endereco.logradouro == "rua senador theotônio vilela"
    assert t.endereco.numero == "110"
    assert t.endereco.complemento == "SALAS 203 E 204 EDIF CIDADELA"
    assert t.endereco.bairro == "parque bela vista"
    assert t.endereco.codigo_municipio == "2927408"
    assert t.endereco.municipio == "Salvador"
    assert t.endereco.uf == "BA"
    assert t.endereco.cep == "40279435"

    v = nfse.valores
    assert v.valor_servicos == 40.18
    assert v.valor_deducoes == 0.0
    assert v.valor_pis == 0.66
    assert v.valor_cofins == 3.05
    assert v.valor_inss == 0.0
    assert v.valor_ir == 0.0
    assert v.base_calculo == 40.18
    assert v.aliquota == 0.05
    assert v.valor_iss == 2.00
    assert v.iss_retido is False

    assert nfse.servico_codigo == "06298"


def test_pdf_digital_normal_sao_paulo_nao_cai_para_ocr(monkeypatch):
    """Regressão do gate GENERALIZADO (sem restrição de layout): uma nota
    digital SAUDÁVEL de LAYOUT_SAO_PAULO (texto com espaçamento normal, ver
    `test_sao_paulo_amil_layout.MOCK_TEXT`) não pode ser desviada para OCR -
    `_ocr_page` nunca deve ser chamado quando o texto digital já é
    utilizável, mesmo agora que a detecção não está mais amarrada a
    LAYOUT_NACIONAL/LAYOUT_NACIONAL_REFORMA."""
    from tests.test_sao_paulo_amil_layout import MOCK_TEXT

    caminho = _dummy("dummy_sao_paulo_amil_regressao.pdf")

    def _ocr_page_nao_deveria_ser_chamado(self, page_num):
        raise AssertionError("_ocr_page nao deveria ser chamado para um texto digital saudavel")

    monkeypatch.setattr(
        "src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT)
    monkeypatch.setattr(SPPdfExtractor, "_ocr_page", _ocr_page_nao_deveria_ser_chamado)
    try:
        nfse_list = SPPdfExtractor(caminho).parse_multiple()
    finally:
        if os.path.exists(caminho):
            os.remove(caminho)

    assert len(nfse_list) == 1
    assert nfse_list[0].numero == "68372315"
