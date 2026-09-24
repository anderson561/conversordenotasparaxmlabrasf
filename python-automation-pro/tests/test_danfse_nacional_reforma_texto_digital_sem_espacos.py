# -*- coding: utf-8 -*-
r"""DANFSe v2.0 (LAYOUT_NACIONAL_REFORMA), nota real nº 171 (DPS nº 173/série
900), SUL&SEG COMERCIO E SERVICOS DE MANUTENCAO ELETRICOS LTDA (Lauro de
Freitas/BA) -> MACEDO COMERCIAL DE CALCADOS LTDA (Lauro de Freitas/BA),
R$ 40,00. PDF de 1 pagina, **DIGITAL** (nunca escaneado) - `Nota Macedo
173.pdf`, arquivo real do usuario.

Causa-raiz: `pdfminer.high_level.extract_text()` extrai o texto embutido
desta nota especificamente SEM NENHUM ESPACO entre palavras (glifos
posicionados sem gap detectavel pelo layout do pdfminer - testado
`LAParams(word_margin=...)` de 0.1 a 2.0, resultado identico em todos os
casos). Isso derruba toda extracao de `LAYOUT_NACIONAL_REFORMA` baseada em
`\s+` entre rotulo e valor (a DETECCAO de layout continua funcionando por
acidente, com `\s*`), e o XML saia com "Prestador Nao Identificado",
"Tomador Nao Identificado", ValorServicos=0.00, CodigoVerificacao sentinela
"XXXX-XXXX" e DataEmissao no fallback `datetime.now()`.

Fix: `SPPdfExtractor._texto_digital_sem_espacos` detecta a patologia (texto
digital longo com densidade de espacos proxima de zero) de forma GENERICA
(razao espacos/tamanho, nao o CNPJ desta empresa) e, quando a pagina ja
detectada como `LAYOUT_NACIONAL`/`LAYOUT_NACIONAL_REFORMA` cai nela,
`parse_multiple()` descarta o texto digital e usa OCR (`_ocr_page`) para
aquela pagina em vez de tentar consertar regex para tolerar texto colado.

O texto digital abaixo (`RAW_DIGITAL_SEM_ESPACOS`) e o retorno REAL e
verbatim de `extract_text()` no PDF original (via `repr()`) - inclusive a
ordem de leitura invertida do pdfminer (o rodape "DATA CIENTIFICACAO..."
sai ANTES do cabecalho).

O texto OCR abaixo (`MOCK_OCR`) e o retorno REAL do Tesseract via
`_extract_via_ocr()` no MESMO PDF - grade "rotulo numa linha, valor na
linha seguinte" tipica de OCR, incluindo colunas fundidas em uma unica
linha ("Indicador Municipal (Inscricao) Telefone" / "10030574 -") e o "@"
do e-mail do tomador lido como duas maiusculas soltas coladas
("valmirGQmaxcalcados.com.br")."""
import os

from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_NACIONAL_REFORMA

RAW_DIGITAL_SEM_ESPACOS = 'DATACIENTIFICAÇÃO:IDENTIFICAÇÃOEASSINATURAN°NFS-e/CHAVENFS-e171/29192072218294792000110000000000017126094422711907DANFSev2.0DocumentoAuxiliardaNFS-eMunicípio:LaurodeFreitas-BAAmbienteGerador:2TipodeAmbiente:1CHAVEDEACESSODANFS-e29192072218294792000110000000000017126094422711907AautenticidadedestaNFS-epodeserverificadapelaleituradestecódigoQRoupelaconsultadachavedeacessonoportalnacionaldaNFS-eNÚMERODANFS-e171COMPETÊNCIADANFS-e08/09/2026DATAEHORADAEMISSÃODANFS-e08/09/202612:02:20NÚMERODADPS173SÉRIEDADPS900DATAEHORADAEMISSÃODADPS08/09/202612:00:53EMITENTEDANFS-ePrestadorSITUAÇÃODANFS-eNFS-eGeradaFINALIDADENFS-eregularPRESTADOR/FORNECEDORCNPJ/CPF/NIF18.294.792/0001-10IndicadorMunicipal(Inscrição)10030574Telefone-Nome/NomeEmpresarialSUL&SEGCOMERCIOESERVICOSDEMANUTENCAOELETRICOSLTDAMunicípio/SiglaUFLaurodeFreitas/BACódigoIBGE/CEP29.19207/42.702-010EndereçoAVNBRIGADEIROALBERTOCOSTAMATOS,1184,CENTRO,ARACUIE-mail-SimplesNacionalnaDatadeCompetênciaNãooptanteRegimedeApuraçãoTributáriapeloSN-TOMADOR/ADQUIRENTECNPJ/CPF/NIF04.074.648/0003-25IndicadorMunicipal(Inscrição)-Telefone(71)3342-4542Nome/NomeEmpresarialMACEDOCOMERCIALDECALCADOSLTDAMunicípio/SiglaUFLaurodeFreitas/BACódigoIBGE/CEP29.19207/42.700-130EndereçoRUASAOCRISTOVAO,1241,LOTJARDIMMETROPOLEQUADRAGLOTE16,ITINGAE-mailvalmir@maxcalcados.com.brDESTINATÁRIODAOPERAÇÃONÃOIDENTIFICADONANFS-eINTERMEDIÁRIODAOPERAÇÃONÃOIDENTIFICADONANFS-eSERVIÇOPRESTADOCódigodeTributaçãoNacional/Municipal11.02.01/-CódigodaNBS1.1802.90.00LocaldaPrestação/SiglaUF/PaísLaurodeFreitas/BA/-Vigilância,segurançaoumonitoramentodebens,pessoasesemoventes.DescriçãodoServiçoSERVICOSDEMONITORAMENTOREF.ASETEMBRO/2026ValoraproximadodostributosR$6,60(16,50%)-LeiN.12.741/2012-FonteIBPTTRIBUTAÇÃOMUNICIPAL(ISSQN)TipodeTributaçãodoISSQNOperaçãoTributávelMunicípio/SiglaUF/PaísdeIncidênciadoISSQNLaurodeFreitas/BA/-BCISSQNR$40,00AlíquotaAplicada3,00%RetençãodoISSQNNãoRetidoISSQNApuradoR$1,20TRIBUTAÇÃOFEDERAL(EXCETOCBS)IRRF-ContribuiçãoPrevidenciária-Retida-ContribuiçõesSociais-Retidas-PIS-DébitoApuraçãoPrópriaR$0,00COFINS-DébitoApuraçãoPrópriaR$0,00DescriçãoContrib.Sociais-Retidas0-PIS/COFINS/CSLLNãoRetidosTRIBUTAÇÃOIBS/CBSCST/cClassTrib000/000001IndicadordeOperação/CódigoIBGEIncidência/MunicípioIncidência/SiglaUF100301/2919207/LaurodeFreitas/BAExclusõeseReduçõesdaBasedeCálculoR$1,20BasedeCálculoApósExclusõeseReduçõesR$38,80Red.AlíquotaIBS/Red.AlíquotaCBS-/-/-Alíquota-IBSUF/IBSMun0,10%/0,00%Alíq.EfetivaMunicipal-IBS0,00%ValorApuradoMunicipal-IBSR$0,00Alíq.EfetivaEstadual-IBS0,10%ValorApuradoEstadual-IBSR$0,04ValorTotalApurado-IBSR$0,04Alíquota-CBS0,90%AlíquotaEfetiva-CBS0,90%ValorTotalApurado-CBSR$0,35VALORTOTALDANFS-eVALORDAOPERAÇÃO/SERVIÇOR$40,00DescontoIncondicionado-DescontoCondicionado-TotaldasRetenções(ISSQN/Federais)-VALORLÍQUIDODANFS-eR$40,00TotaldoIBS/CBSR$0,39VALORLÍQUIDODANFS-e+IBS/CBSR$40,00INFORMAÇÕESCOMPLEMENTARESTotaisaproximadosdosTributoscfe.Lein°12.741/2012:Federais:6,15%;Estaduais:0,00%;Municipais:3,00%;\x0c'

MOCK_OCR = 'Município: Lauro de Freitas - BA\nAmbiente Gerador: 2\nTipo de Ambiente: 1\n\nDANFSe v2.0\nDocumento Auxiliar da NFS-e\n\nNFSe:\n\nCHAVE DE ACESSO DA NFS-e\n29192072218294792000110000000000017126094422711907\n\nNÚMERO DA NFS-e COMPETÊNCIA DA NFS-e\n171 08/09/2026\n\nNÚMERO DA DPS SÉRIE DA DPS\n173 900\n\nEMITENTE DA NFS-e SITUAÇÃO DA NFS-e\nPrestador NFS-e Gerada\n\nPRESTADOR / FORNECEDOR CNPJ/CPF / NIF\n18.294.792/0001-10\n\nDATA E HORA DA EMISSÃO DA NFS-e\n08/09/2026 12:02:20\n\nDATA E HORA DA EMISSÃO DA DPS\n08/09/2026 12:00:53\n\nFINALIDADE\nNFS-e regular\n\n[e\nA autenticidade desta NFS-e pode ser verificada\n\npela leitura deste código QR ou pela consulta da\nchave de acesso no portal nacional da NFS-e\n\nIndicador Municipal (Inscrição) Telefone\n10030574 -\n\nCódigo IBGE / CEP\n29.19207 /42.702-010\n\nNome / Nome Empresarial Município / Sigla UF\nSUL&SEG COMERCIO E SERVICOS DE MANUTENCAO ELETRICOS LTDA Lauro de Freitas / BA\n\nEndereço E-mail\nAVN BRIGADEIRO ALBERTO COSTA MATOS, 1184, CENTRO, ARACUI -\n\nSimples Nacional na Data de Competência Regime de Apuração Tributária pelo SN\nNão optante -\n\nTOMADOR / ADQUIRENTE CNPJ/CPF/NIF Indicador Municipal (Inscrição) Telefone\n04.074.648/0003-25 - (71) 3342-4542\n\nNome / Nome Empresarial Município / Sigla UF Código IBGE / CEP\nMACEDO COMERCIAL DE CALCADOS LTDA Lauro de Freitas / BA 29.19207 / 42.700-130\n\nEndereço E-mail\nRUA SAO CRISTOVÃO, 1241, LOT JARDIM METROPOLE QUADRA G LOTE 16, ITINGA valmirGQmaxcalcados.com.br\n\nDESTINATÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e\nINTERMEDIÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e\nCódigo de Tributação Nacional/Municipal Código da NBS\n11.02.01/- 1.1802.90.00\n\nLocal da Prestação / Sigla UF / País\nLauro de Freitas / BA / -\n\nSERVIÇO PRESTADO\n\nVigilância, segurança ou monitoramento de bens, pessoas e semoventes.\n\nDescrição do Serviço\nSERVICOS DE MONITORAMENTO REF. A SETEMBRO/2026\nValor aproximado dos tributos R$ 6,60 (16,50%) - Lei N. 12.741/2012 - Fonte IBPT\n\nTRIBUTAÇÃO MUNICIPAL (ISSQN)\n\nBC ISSQN\nR$ 40,00\n\nTipo de Tributação do ISSQN\nOperação Tributável\n\nAlíquota Aplicada\n3,00 %\n\nMunicípio / Sigla UF / País de Incidência do ISSQN\nLauro de Freitas / BA / -\n\nRetenção do ISSQN ISSQN Apurado\nNão Retido R$ 1,20\n\nTRIBUTAÇÃO FEDERAL (EXCETO CBS)\n\nPIS - Débito Apuração Própria\nR$ 0,00\n\nIRRF\n\nCOFINS - Débito Apuração Própria\nR$ 0,00\n\nContribuição Previdenciária - Retida Contribuições Sociais - Retidas\n\nDescrição Contrib. Sociais - Retidas\nO- PIS/COFINS/CSLL Não Retidos\n\nTRIBUTAÇÃO IBSICBS\n\nExclusões e Reduções da Base de Cálculo\nR$ 1,20\n\nAlíg. Efetiva Municipal - IBS\n0,00 %\n\nValor Total Apurado - IBS\nR$ 0,04\n\nCST/ cClassTrib\n000 / 000001\n\nBase de Cálculo Após Exclusões e Reduções\nR$ 38,80\n\nValor Apurado Municipal - IBS\nR$ 0,00\n\nAlíquota - CBS\n0,90 %\n\nIndicador de Operação / Código IBGE Incidência / Muni jo Incidência / Sigla UF\n100301 / 2919207 / Lauro de Freitas / BA\n\nRed. Alíquota IBS / Red. Alíquota CBS\n\n=J-d-\n\nAlíqg. Efetiva Estadual - IBS\n\n0,10 %\n\nAlíquota Efetiva - CBS\n\n0,90 %\n\nAlíquota - IBS UF /IBS Mun\n0,10 % / 0,00 %\n\nValor Apurado Estadual - IBS\nR$ 0,04\n\nValor Total Apurado - CBS\nR$0,35\n\nVALOR TOTAL DA NFS-e\n\nTotal das Retenções (ISSQN / Federais)\n\nVALOR DA OPERAÇÃO / SERVIÇO\nR$40,00\n\nVALOR LÍQUIDO DA NFS-e\n\nDesconto Incondicionado\n\nTotal do IBS/CBS\n\nDesconto Condicionado\n\nVALOR LÍQUIDO DA NFS-e + IBS/CBS\n\n- R$ 40,00 R$ 0,39 R$40,00\nINFORMAÇÕES COMPLEMENTARES\n\nTotais aproximados dos Tributos cfe. Lei nº 12.741/2012: Federais: 6,15 %; Estaduais: 0,00 %; Municipais: 3,00 %;\n\nDATA CIENTIFICAÇÃO IDENTIFICAÇÃO E ASSINATURA Nº NFS-e / CHAVE NFS-e\n171 / 29192072218294792000110000000000017126094422711907\n\n'


def _dummy(nome):
    caminho = f"tests/{nome}"
    os.makedirs("tests", exist_ok=True)
    with open(caminho, "wb") as f:
        f.write(b"%PDF-1.4")
    return caminho


def test_texto_digital_sem_espacos_detecta_a_patologia():
    """Densidade de espacos quase zero num texto longo (o achado real desta
    nota: 2972+ caracteres, ZERO espacos) - gate GENERICO, sem depender do
    CNPJ/emissor desta nota."""
    assert SPPdfExtractor._texto_digital_sem_espacos(RAW_DIGITAL_SEM_ESPACOS)


def test_texto_digital_sem_espacos_nao_dispara_em_texto_normal():
    """Um texto digital comum (com espacos normais entre palavras) nunca deve
    ser tratado como patologico, mesmo sendo longo - senao toda nota digital
    saudavel seria desviada para OCR a toa."""
    texto_normal = MOCK_OCR  # tem espacos normais entre palavras
    assert not SPPdfExtractor._texto_digital_sem_espacos(texto_normal)


def test_texto_curto_nao_dispara_a_patologia():
    """Texto curto (abaixo do limiar minimo) nunca aciona a deteccao - evita
    falso-positivo em paginas de boilerplate/lixo, que ja tem seu proprio
    tratamento (`OCR_MIN_CHARS`)."""
    assert not SPPdfExtractor._texto_digital_sem_espacos("PRESTADOR" * 5)


def test_pdf_digital_sem_espacos_cai_para_ocr_e_extrai_nota_corretamente(monkeypatch):
    """Reproduz o caminho real desta nota: `extract_text()` (pdfminer) devolve
    o texto digital colado sem espacos (patologia confirmada); o extrator
    detecta e usa `_ocr_page()` para esta pagina especifica, cujo retorno
    (mockado aqui com o `MOCK_OCR` real) alimenta a extracao de
    `LAYOUT_NACIONAL_REFORMA`, ja preparada para o formato de grade OCR
    (rotulo numa linha, valor na linha seguinte)."""
    caminho = _dummy("dummy_macedo_173.pdf")
    monkeypatch.setattr(
        "src.extractors.pdf_extractor.extract_text", lambda path: RAW_DIGITAL_SEM_ESPACOS)
    monkeypatch.setattr(SPPdfExtractor, "_ocr_page", lambda self, page_num: MOCK_OCR)
    try:
        nfse_list = SPPdfExtractor(caminho).parse_multiple()
    finally:
        if os.path.exists(caminho):
            os.remove(caminho)

    assert len(nfse_list) == 1
    nfse = nfse_list[0]

    assert nfse.numero == "171"
    assert nfse.data_emissao.strftime("%Y-%m-%dT%H:%M:%S") == "2026-09-08T12:02:20"
    assert nfse.codigo_verificacao == "29192072218294792000110000000000017126094422711907"

    p = nfse.prestador
    assert p.cnpj_cpf == "18294792000110"
    assert p.razao_social == "SUL&SEG COMERCIO E SERVICOS DE MANUTENCAO ELETRICOS LTDA"
    assert p.inscricao_municipal == "10030574"
    assert p.endereco.logradouro == "AVN BRIGADEIRO ALBERTO COSTA MATOS"
    assert p.endereco.numero == "1184"
    assert p.endereco.complemento == "CENTRO"
    assert p.endereco.bairro == "ARACUI"
    assert p.endereco.codigo_municipio == "2919207"
    assert p.endereco.municipio == "Lauro de Freitas"
    assert p.endereco.uf == "BA"
    assert p.endereco.cep == "42702010"

    t = nfse.tomador
    assert t.cnpj_cpf == "04074648000325"
    assert t.razao_social == "MACEDO COMERCIAL DE CALCADOS LTDA"
    assert t.telefone == "(71) 3342-4542"
    assert t.email == "valmir@maxcalcados.com.br"
    assert t.endereco.logradouro == "RUA SAO CRISTOVÃO"
    assert t.endereco.numero == "1241"
    assert t.endereco.complemento == "LOT JARDIM METROPOLE QUADRA G LOTE 16"
    assert t.endereco.bairro == "ITINGA"
    assert t.endereco.codigo_municipio == "2919207"
    assert t.endereco.municipio == "Lauro de Freitas"
    assert t.endereco.uf == "BA"
    assert t.endereco.cep == "42700130"

    v = nfse.valores
    assert v.valor_servicos == 40.0
    assert v.base_calculo == 40.0
    assert v.aliquota == 0.03
    assert v.valor_iss == 1.20
    assert v.iss_retido is False
    assert v.valor_liquido_nfse == 40.0

    # Item da LC 116 (Vigilancia, seguranca ou monitoramento) - achado
    # colateral confirmado na conversao real: esta nota funde "Codigo de
    # Tributacao Nacional/Municipal" com o codigo NA MESMA linha, ANTES de
    # "SERVICO PRESTADO" - ordem oposta das notas 11/59 ja cobertas (onde
    # "SERVICO PRESTADO" vem primeiro e o codigo logo depois). Sem o fix,
    # nenhuma das duas ancoras achava o codigo e caia no default generico
    # "03115" (locacao de bens moveis, nada a ver com esta nota).
    assert nfse.servico_codigo == "1102"

    assert nfse.avisos == []


def test_pdf_digital_normal_do_mesmo_layout_nao_cai_para_ocr(monkeypatch):
    """Regressao: uma nota digital SAUDAVEL do mesmo layout (texto com
    espacos normais) nao pode ser desviada para OCR - `_ocr_page` nunca deve
    ser chamado quando o texto digital ja e utilizavel."""
    caminho = _dummy("dummy_macedo_173_digital_normal.pdf")

    def _ocr_page_nao_deveria_ser_chamado(self, page_num):
        raise AssertionError("_ocr_page nao deveria ser chamado para um texto digital saudavel")

    monkeypatch.setattr(
        "src.extractors.pdf_extractor.extract_text", lambda path: MOCK_OCR)
    monkeypatch.setattr(SPPdfExtractor, "_ocr_page", _ocr_page_nao_deveria_ser_chamado)
    try:
        nfse_list = SPPdfExtractor(caminho).parse_multiple()
    finally:
        if os.path.exists(caminho):
            os.remove(caminho)

    assert len(nfse_list) == 1
    assert nfse_list[0].numero == "171"
