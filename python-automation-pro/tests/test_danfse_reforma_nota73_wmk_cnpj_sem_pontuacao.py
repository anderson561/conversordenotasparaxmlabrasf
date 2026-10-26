# -*- coding: utf-8 -*-
r"""DANFSe v2.0 (LAYOUT_NACIONAL_REFORMA), nota real nº 73, W M K CONSTRUCOES
COMERCIO E SERVICOS LTDA - ME (Serrinha/BA, CNPJ 08.058.923/0001-06) -> SINAL
CONSTDRUTORA LTDA (Pojuca/BA), subempreitada 07.02 (obra CONDER em
Lajedinho/BA), R$ 292.301,88. PDF DIGITAL de 2 páginas (`73.pdf`, arquivo
real do usuário; a pág. 2 é só o canhoto de cientificação).

`RAW_DIGITAL` é o retorno REAL e verbatim de `extract_text()` (pdfminer) no
PDF original, via `repr()`.

Defeitos do XML gerado antes do fix (todos conferidos contra a imagem
renderizada da página):
1. Prestador `<Cpf>08058923000</Cpf>`: este gerador imprime o CNPJ só com
   dígitos ("08058923000106"); o regex exigia a barra e a alternativa de CPF
   casava os 11 primeiros dígitos. CNPJ truncado emitido como CPF.
2. Prestador "AV LOMANTO JUNIOR, 400 ANEXO A CASA": Numero S/N e Bairro
   "400 ANEXO A CASA" -> Numero 400, "ANEXO A CASA" é complemento.
3. Tomador "RUA Z EVANGELINA SIQUEIRA DIAS 9995 - NOVA PAJUCA" (sem
   vírgula): linha inteira no logradouro -> logradouro/número/bairro.
4. Tomador InscricaoMunicipal 9995 (o número do imóvel — o Indicador
   Municipal do tomador vem EM BRANCO na nota).
5. Tomador Telefone "71-3273-2450" (DDD com hífen) sumia do XML.
6. ValorDeducoes 0,00 apesar de "Total Deduções / Reduções R$ 146.150,94"
   impresso (BC ISSQN 146.150,94 = 292.301,88 - 146.150,94).
7. Município de incidência: o rótulo deste gerador é "Município / UF / País
   de Incidência do ISSQN" (sem "Sigla") -> a incidência caía no município
   do PRESTADOR (Serrinha 2930501) em vez de Lajedinho/BA (2919009, código
   impresso na linha "Código IBGE Incidência" da grade IBS/CBS).
8. Discriminação começava com a descrição padrão do item da LC 116 e o
   rótulo "Descrição do Serviço".

Mantidos (conferidos na imagem): razão social do tomador "SINAL
CONSTDRUTORA LTDA" é a grafia IMPRESSA (não é OCR — PDF digital); CEP do
tomador 48120-000; Pojuca 2925204 (IBGE impresso; a tabela do conversor
tinha 2925303, que é Porto Seguro — corrigida)."""
import os

from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_NACIONAL_REFORMA
from src.transformers.abrasf_transformer import Abrasf201Transformer
from src.utils.ibge_resolver import IBGEResolver

RAW_DIGITAL = 'DANFSe v2.0\nDocumento Auxiliar da NFS-e\n\nMunicípio: SERRINHA - BA\nAmbiente Gerador: 2\nTipo de Ambiente: 1\n\nCHAVE DE ACESSO DA NFS-e\n29305011208058923000106000000000007326100220845629\nNÚMERO DA NFS-e\n73\n\nCOMPETÊNCIA DA NFS-e\n10/2026\n\nNÚMERO DA DPS\n73\n\nEMITENTE DA NFS-e\nPrestador\n\nPRESTADOR / FORNECEDOR\n\nSÉRIE DA DPS\n1\n\nSITUAÇÃO DA NFS-e\nNFS-e Gerada\n\nCNPJ / CPF / NIF\n08058923000106\n\nNome / Nome Empresarial\nW M K CONSTRUCOES COMERCIO E SERVICOS LTDA - ME\n\nEndereço\nAV LOMANTO JUNIOR, 400 ANEXO A CASA\n\nDATA E HORA DA EMISSÃO DA NFS-e\n20/10/2026 09:43:51\n\nDATA E HORA DA EMISSÃO DA DPS\n20/10/2026 09:43:51\n\nFINALIDADE\nNFS-e Regular\n\nIndicador Municipal (Inscrição)\n1905\n\nMunicípio / Sigla UF\nSERRINHA / BA\n\nE-mail\nservcont12@gmail.com\n\nA autenticidade desta NFS-e pode ser verificada\npela leitura deste código QR ou pela consulta da\nchave de acesso no portal nacional da NFS-e.\n\nTelefone\n75992106985\n\nCódigo IBGE / CEP\n2930501 / 48700000\n\nSimples Nacional na Data de Competência\nOptante - Microempresa ou Empresa de …\n\nRegime de Apuração Tributária pelo SN\nRegime de apuração dos tributos federais e municipal pelo Simples Nacional\n\nTOMADOR / ADQUIRENTE\n\nNome / Nome Empresarial\nSINAL CONSTDRUTORA LTDA\n\nCNPJ / CPF / NIF\n33.811.381/0001-48\n\nIndicador Municipal (Inscrição)\n\nMunicípio / Sigla UF\nPOJUCA / BA\n\nTelefone\n71-3273-2450\n\nCódigo IBGE / CEP\n2925204 / 48120-000\n\nEndereço\nRUA Z EVANGELINA SIQUEIRA DIAS 9995 - NOVA PAJUCA\n\nE-mail\nADM@SINALCONSTRUTORA.COM\n\nDESTINATÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-E\nINTERMEDIÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-E\n\nSERVIÇO PRESTADO\n\nCódigo de Tributação Nacional/Municipal\n07.02.01 / 000\n\nCódigo da NBS\n1.0101.11.00 - Serviços de construção de …\n\nLocal da Prestação / Sigla UF / País\nLAJEDINHO / BA / BR\n\n07.02 - Execução; por administração; empreitada ou subempreitada; de obras de construção civil; hidráulica ou elétrica e de outras obras semelhantes; inclusive sondagem; perfuraçã…\n\nDescrição do Serviço\nSERVIÇOS DE SUBEMPREITADAS EM OBRA 026 CONDER PONTE 2 CONFORME BM 01 REFERENTE AO PERÍODO 06/08/2026 A 14/10/2026\n\n50% VALOR DE MÃO DE OBRA: R$ 146.150,94\n50% VALOR DE DE MATERIAL: R$ 146.150,94\n\nDADOS PARA DEPOSITO BANCO DO BRADESCO AGENCIA 3064-3 CONTA CORRENTE 38749-5\nPIX : 08.058.923/0001-06\n\nTRIBUTAÇÃO MUNICIPAL (ISSQN)\n\nRegime Especial de Tributação do ISSQN\nNenhum\n\nTipo de Tributação do ISSQN\nOperação Tributável\n\nTipo de Imunidade do ISSQN\n\nBenefício Municipal\n\nCálculo do BM\n\nBC ISSQN\nR$ 146.150,94\n\nTRIBUTAÇÃO FEDERAL (EXCETO CBS)\n\nAlíquota Aplicada\n5,00 %\n\nIRRF\nR$ 0,00\n\nMunicípio / UF / País de Incidência do ISSQN\nLAJEDINHO / BA / BR\n\nSuspensão da Exigibilidade do ISSQN\nNão\n\nTotal Deduções / Reduções\nR$ 146.150,94\n\nRetenção do ISSQN\nRetido pelo tomador\n\nNúmero Processo Suspensão\n\nDesconto Incondicionado\nR$ 0,00\n\nISSQN Apurado\nR$7.307,55\n\nContribuição Previdenciária - Retida\nR$ 16.076,60\n\nContribuições Sociais - Retidas\nR$ 0,00\n\nPIS - Débito Apuração Própria\nR$ -\n\nTRIBUTAÇÃO IBS/CBS\n\nCOFINS - Débito Apuração Própria\nR$ -\n\nDescrição Contrib. Sociais - Retidas\n0 - PIS/COFINS/CSLL Não Retidos\n\nCST / ClassTrib\n200 / 200045\n\nIndicador de Operação / Código IBGE Incidência / Município Incidência / Sigla UF\n020201 / 2919009 / LAJEDINHO / BA\n\nExclusões e Reduções da Base de Cálculo\n7.307,55\n\nBase de Cálculo Após Exclusões e Reduções\n284.994,33\n\nRed. Alíquota IBS / Red. Alíquota CBS\n60.00 % / 60.00 % / 60.00 %\n\nAlíquota - IBS UF / IBS Mun\n0.10 % / 0.00 %\n\nAlíq. Efetiva Municipal - IBS\n0.00 %\n\nValor Total Apurado - IBS\nR$ 114.00\n\nVALOR TOTAL DA NFS-E\n\nValor Apurado Municipal - IBS\nR$ 0.00\n\nAlíquota - CBS\n0.90 %\n\nVALOR DA OPERAÇÃO / SERVIÇO\nR$ 292.301,88\n\nTotal das Retenções (ISSQN / Federais)\nR$ 23.384,15\n\nVALOR LÍQUIDO DA NFS-e\nR$ 268.917,73\n\nINFORMAÇÕES COMPLEMENTARES\n\n- Nota Fiscal emitida de acordo com o Decreto n° 0000/0000\nTotais aproximados dos tributos: Estadual: R$ 0,00, Federal: R$ 16.076,60\n\nAlíq. Efetiva Estadual - IBS\n0.04 %\n\nAlíquota Efetiva - CBS\n0.36 %\n\nDesconto Incondicionado\nR$ 0,00\n\nTotal do IBS/CBS\nR$ 1.139,98\n\nValor Apurado Estadual - IBS\nR$ 114.00\n\nValor Total Apurado - CBS\nR$ 1025.98\n\nDesconto Condicionado\nR$ 0,00\n\nVALOR LÍQUIDO DA NFS-e + IBS/CBS\nR$ 268.917,73\n\n\x0cData da Cientificação:\n\nIdentificação e Assinatura:\n\nN° NFS-e / Chave NFS-e:\n73 / 29305011208058923000106000000000007326100220845629\n\n\x0c'


def _parse(monkeypatch, raw, nome="dummy_nota73_wmk.pdf"):
    caminho = f"tests/{nome}"
    os.makedirs("tests", exist_ok=True)
    with open(caminho, "wb") as f:
        f.write(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: raw)
    try:
        notas = SPPdfExtractor(caminho).parse_multiple()
    finally:
        if os.path.exists(caminho):
            os.remove(caminho)
    assert len(notas) == 1
    return notas[0]


def test_layout_detectado_e_reforma():
    ex = SPPdfExtractor("x.pdf")
    ex.raw_text = RAW_DIGITAL
    assert ex._detect_layout() == LAYOUT_NACIONAL_REFORMA


def test_prestador_cnpj_sem_pontuacao_nao_vira_cpf_truncado(monkeypatch):
    nota = _parse(monkeypatch, RAW_DIGITAL)
    p = nota.prestador
    assert p.cnpj_cpf == "08058923000106"
    assert p.razao_social == "W M K CONSTRUCOES COMERCIO E SERVICOS LTDA - ME"
    assert p.inscricao_municipal == "1905"
    assert p.telefone == "75992106985"
    assert p.email == "servcont12@gmail.com"
    xml = Abrasf201Transformer().transform(nota)
    assert "<Cnpj>08058923000106</Cnpj>" in xml
    assert "<Cpf>" not in xml


def test_prestador_endereco_numero_colado_ao_complemento(monkeypatch):
    end = _parse(monkeypatch, RAW_DIGITAL).prestador.endereco
    assert end.logradouro == "AV LOMANTO JUNIOR"
    assert end.numero == "400"
    assert end.complemento == "ANEXO A CASA"
    # A nota não imprime bairro: sentinela, nunca o complemento.
    assert end.bairro == "Não informado"
    assert end.codigo_municipio == "2930501"
    assert end.municipio == "SERRINHA"
    assert end.cep == "48700000"


def test_tomador_endereco_sem_virgula_im_em_branco_e_telefone(monkeypatch):
    t = _parse(monkeypatch, RAW_DIGITAL).tomador
    assert t.cnpj_cpf == "33811381000148"
    # Grafia IMPRESSA na nota (PDF digital) — não é erro de OCR.
    assert t.razao_social == "SINAL CONSTDRUTORA LTDA"
    # Indicador Municipal do tomador vem em branco: nunca o nº do imóvel.
    assert not t.inscricao_municipal
    assert t.telefone == "71-3273-2450"
    assert t.email == "ADM@SINALCONSTRUTORA.COM"
    assert t.endereco.logradouro == "RUA Z EVANGELINA SIQUEIRA DIAS"
    assert t.endereco.numero == "9995"
    assert t.endereco.bairro == "NOVA PAJUCA"
    assert t.endereco.codigo_municipio == "2925204"
    assert t.endereco.municipio == "POJUCA"
    assert t.endereco.cep == "48120000"


def test_valores_deducoes_fecham_a_base(monkeypatch):
    v = _parse(monkeypatch, RAW_DIGITAL).valores
    assert v.valor_servicos == 292301.88
    assert v.valor_deducoes == 146150.94
    assert v.base_calculo == 146150.94
    assert round(v.valor_servicos - v.valor_deducoes, 2) == v.base_calculo
    assert v.aliquota == 0.05
    assert v.valor_iss == 7307.55
    assert v.iss_retido is True
    assert v.valor_inss == 16076.60
    assert v.valor_ir == 0.0
    assert v.valor_liquido_nfse == 268917.73


def test_municipio_incidencia_e_discriminacao(monkeypatch):
    nota = _parse(monkeypatch, RAW_DIGITAL)
    assert nota.municipio_incidencia_override == "2919009"  # Lajedinho/BA
    assert nota.discriminacao.startswith("SERVIÇOS DE SUBEMPREITADAS EM OBRA 026 CONDER")
    assert "Descrição do Serviço" not in nota.discriminacao
    assert "PIX : 08.058.923/0001-06" in nota.discriminacao
    xml = Abrasf201Transformer().transform(nota)
    assert "<MunicipioIncidencia>2919009</MunicipioIncidencia>" in xml


def test_demais_campos_e_sem_avisos(monkeypatch):
    nota = _parse(monkeypatch, RAW_DIGITAL)
    assert nota.numero == "73"
    assert nota.codigo_verificacao == "29305011208058923000106000000000007326100220845629"
    assert nota.data_emissao.strftime("%Y-%m-%dT%H:%M:%S") == "2026-10-20T09:43:51"
    assert nota.servico_codigo.replace(".", "").startswith("0702")
    assert nota.avisos == []


# ---------------------------------------------------------------- degradados

def test_cnpj_prestador_com_dv_invalido_recuperado_pela_chave(monkeypatch):
    """Documento do bloco que reprova o DV (aqui, 11 dígitos — o próprio
    sintoma do truncamento) é substituído pelo CNPJ da chave de acesso, que
    passa no DV e cujo emitente é o Prestador."""
    raw = RAW_DIGITAL.replace("CNPJ / CPF / NIF\n08058923000106", "CNPJ / CPF / NIF\n08058923000", 1)
    assert raw != RAW_DIGITAL
    nota = _parse(monkeypatch, raw)
    assert nota.prestador.cnpj_cpf == "08058923000106"


def test_cnpj_prestador_invalido_sem_chave_confiavel_gera_aviso(monkeypatch):
    """Sem chave utilizável (emitente não é o Prestador) o documento lido
    é mantido, mas NUNCA em silêncio: aviso nomeando o valor."""
    raw = (RAW_DIGITAL
           .replace("CNPJ / CPF / NIF\n08058923000106", "CNPJ / CPF / NIF\n08058923000107", 1)
           .replace("EMITENTE DA NFS-e\nPrestador", "EMITENTE DA NFS-e\nTomador", 1))
    nota = _parse(monkeypatch, raw)
    assert nota.prestador.cnpj_cpf == "08058923000107"
    assert any("08058923000107" in a and "dígito verificador" in a for a in nota.avisos)


def test_doc_chave_exige_emitente_prestador():
    ex = SPPdfExtractor("x.pdf")
    ex.raw_text = RAW_DIGITAL
    assert ex._doc_emitente_chave_nacional_reforma() == "08058923000106"
    ex.raw_text = RAW_DIGITAL.replace("EMITENTE DA NFS-e\nPrestador", "EMITENTE DA NFS-e\nTomador", 1)
    assert ex._doc_emitente_chave_nacional_reforma() is None


def test_deducoes_que_nao_fecham_a_base_ficam_zeradas_com_aviso(monkeypatch):
    raw = RAW_DIGITAL.replace("BC ISSQN\nR$ 146.150,94", "BC ISSQN\nR$ 150.000,00", 1)
    assert raw != RAW_DIGITAL
    nota = _parse(monkeypatch, raw)
    assert nota.valores.valor_deducoes == 0.0
    assert any("Total Deduções / Reduções" in a for a in nota.avisos)


def test_deducoes_ausentes_continuam_zero(monkeypatch):
    raw = RAW_DIGITAL.replace("Total Deduções / Reduções\nR$ 146.150,94", "Total Deduções / Reduções\n-", 1)
    nota = _parse(monkeypatch, raw)
    assert nota.valores.valor_deducoes == 0.0
    assert not any("Deduções" in a for a in nota.avisos)


def test_incidencia_nao_usa_codigo_de_outro_municipio_da_grade_ibs(monkeypatch):
    """A linha IBS/CBS só vale quando traz o MESMO município; senão o código
    vem do resolver por nome (Lajedinho cadastrado)."""
    raw = RAW_DIGITAL.replace("020201 / 2919009 / LAJEDINHO / BA", "020201 / 2930501 / SERRINHA / BA", 1)
    assert raw != RAW_DIGITAL
    nota = _parse(monkeypatch, raw)
    assert nota.municipio_incidencia_override == "2919009"


def test_incidencia_municipio_fora_da_tabela_sem_codigo_impresso_avisa(monkeypatch):
    raw = (RAW_DIGITAL
           .replace("LAJEDINHO / BA / BR", "CIDADE INEXISTENTE / BA / BR")
           .replace("020201 / 2919009 / LAJEDINHO / BA", "-"))
    nota = _parse(monkeypatch, raw)
    assert any("CIDADE INEXISTENTE" in a and "incidência" in a for a in nota.avisos)


def test_incidencia_capital_fora_da_tabela_nao_avisa(monkeypatch):
    """Capital da UF: o fallback do resolver devolve o código certo - sem aviso."""
    raw = (RAW_DIGITAL
           .replace("LAJEDINHO / BA / BR", "Florianópolis / SC / BR")
           .replace("020201 / 2919009 / LAJEDINHO / BA", "-"))
    nota = _parse(monkeypatch, raw)
    assert nota.municipio_incidencia_override == "4205407"
    assert not any("incidência" in a for a in nota.avisos)


def test_ibge_pojuca_e_lajedinho():
    r = IBGEResolver()
    assert r.extract_and_validate("POJUCA", "BA", city_hint="POJUCA") == "2925204"
    assert r.extract_and_validate("LAJEDINHO", "BA", city_hint="LAJEDINHO") == "2919009"
    assert r.extract_and_validate("SERRINHA", "BA", city_hint="SERRINHA") == "2930501"


# ------------------------------------------- nota nº 53, outro gerador da v2.0
# Mesmo prestador/tomador (W M K -> SINAL), PDF digital real
# `08058923000106_DANFSe_SAIDA_2026_10_DANFSe_2930501...5326090216484092.pdf`
# ("Ambiente Gerador: 1"): CNPJ pontuado, rótulo "Município / Sigla UF / País
# de Incidência", município do tomador impresso "Pojuca - BA" (hífen).
RAW_DIGITAL_NOTA_53 = 'DANFSe v2.0\nDocumento Auxiliar da NFS-e\n\nMunicí pio: SERRINHA /  BA \nAmbiente Gerador: 1 \nTipo de Ambiente: 1\n\nCHAVE DE ACESSO DA NFS-E\n29305011208058923000106000000000005326090216484092\nNÚMERO DA NFS-E\n53\nNÚMERO DA DPS\n53\nEMITENTE DA NFS-E\nPrestador\nPrestador\nPRESTADOR / FORNECEDOR\n\nCOMPETÊNCIA DA NFS-E\n03/09/2026\nSÉRIE DA DPS\n1\nSITUAÇÃO DA NFS-E\nNFS-e Gerada\nCNPJ / CPF / NIF\n08.058.923/0001-06\n\nNome / Nome Empresarial\nW M K CONSTRUCOES COMERCIO E SERVICOS LTDA - ME\nEndereço\nAV LOMANTO JUNIOR, 400, ANEXO A CASA - COLINA DAS MANGUEIRAS\nSimples Nacional na Data de Competência\nOptante - Microempresa ou Empresa de Pequeno Porte (ME/EPP)\nTOMADOR / ADQUIRENTE\n\nCNPJ / CPF / NIF\n33.811.381/0001-48\n\nNome / Nome Empresarial\nSINAL CONSTDRUTORA LTDA\nEndereço\nRUA Z EVANGELINA SIQUEIRA DIAS 9995, - - NOVA PAJUCA\n\nDATA E HORA DA EMISSÃO DA NFS-E\n03/09/2026 00:00:00\nDATA E HORA DA EMISSÃO DA DPS\n03/09/2026 00:00:00\nFINALIDADE\nNFS-e regular\nIndicador Municipal (Inscrição)\n1905\nMunicípio / Sigla UF\nSERRINHA / BA\nE-mail\nservcont12@gmail.com\nRegime de Apuração Tributária pelo SN\nRegime de apuração dos tributos federais e municipal pelo Simples Nacional\nIndicador Municipal (Inscrição)\n-\nMunicípio / Sigla UF\nPojuca - BA\nE-mail\n-\nO DESTINATÁRIO É O PRÓPRIO TOMADOR/ADQUIRENTE DA OPERAÇÃO\nINTERMEDIÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e\n\nTelefone\n-\nCódigo IBGE / CEP\n2930501 / 48700-000\n\nTelefone\n-\nCódigo IBGE / CEP\n2925204 / 48120-000\n\nA autenticidade desta NFS-e pode ser\nverificada pela leitura deste código QR ou pela\nconsulta da chave de acesso no portal nacional\nda NFS-e\n\nSERVIÇO PRESTADO\n\nCódigo de Tributação Nacional/Municipal\n07.02.01 / -\n\nCódigo da NBS\n1.0101.11.00\n\nLocal da Prestação / Sigla UF / País\nLAJEDINHO / BA / -\n\n07.02 - Execução; por administração; empreitada ou subempreitada; de obras de construção civil; hidráulica ou elétrica e de outras obras semelhantes; inclusive...\nDescrição do Serviço\nREFERENTE A ALUGUEL DE UM CAMINHÃO PIPA PLACA NTU 1A81 ANO 2010 PARA TRANSPORTE DE AGUA NA OBRA 018 LAJEDINHO BA NO PERIODO 01082026 A 31082026\nCOMFORME BM 02BR BR DADOS BANCARIO BANCO DO BRADESCO AGENCIA 30643 CONTA CORRENTE 387495BR PIX 08058923000106BR OBS SEM MÃO DE OBRA\nTRIBUTAÇÃO MUNICIPAL (ISSQN)\n\nBC ISSQN\nR$ 4.400,00\nTRIBUTAÇÃO FEDERAL (EXCETO CBS)\n\nPIS - Débito Apuração Própria\n-\nTRIBUTAÇÃO IBS/CBS\n\nExclusões e Reduções da Base de Cálculo\nR$ 88,00\nAlíq. Efetiva Municipal - IBS\n0,00%\nValor Total Apurado - IBS\nR$ 1,72\nVALOR TOTAL DA NFS-E\n\nTipo de Tributação do ISSQN\nOperação Tributável\nAlíquota Aplicada\n2,00%\nIRRF\n-\nCOFINS - Débito Apuração Própria\n-\nCST / cClassTrib\n200 / 200045\nBase de Cálculo Após Exclusões e Reduções\nR$ 4.312,00\nValor Apurado Municipal - IBS\nR$ 0,00\nAlíquota - CBS\n0,90%\nValor da Operação / Serviço\nR$ 4.400,00\nR$ 4.400,00\nValor Líquido da NFS-e\nR$ 4.312,00\nR$ 4.312,00\n\nISSQN Apurado\nR$ 88,00\nContribuições Sociais - Retidas\n-\n\nMunicípio / Sigla UF / País de Incidência do ISSQN\nLAJEDINHO / BA / -\nRetenção do ISSQN\nRetido pelo Tomador\nContribuição Previdenciária - Retida\n-\nDescrição Contrib. Sociais - Retidas\n-\nIndicador de Operação / Código IBGE Incidência / Município Incidência / Sigla UF\n020201 / 2919009 / LAJEDINHO / BA\nRed. Alíquota IBS / Red. Alíquota CBS\n60,00% / 60,00% / 60,00%\nAlíq. Efetiva Estadual - IBS\n0,04%\nAlíquota Efetiva - CBS\n0,36%\nDesconto Incondicionado\n-\nTotal do IBS/CBS\nR$ 17,24\n\nAlíquota - IBS UF / IBS Mun\n0,10% / 0,00%\nValor Apurado Estadual - IBS\nR$ 1,72\nValor Total Apurado - CBS\nR$ 15,52\nDesconto Condicionado\n-\nValor Líquido da NFS-e + IBS/CBS\nR$ 4.312,00\nR$ 4.312,00\n\nTotal das Retenções (ISSQN / Federais)\n-\nINFORMAÇÕES COMPLEMENTARES\nCod. Obra: 1234 | Insc. Imob.: 12345678\nTotais Aproximados dos Tributos cfe. Lei nº 12.741/2012: Federais: -; Estaduais: -; Municipais: -;\n\nDATA CIENTIFICAÇÃO:\n\nIDENTIFICAÇÃO E ASSINATURA\n\nNº NFS-E / CHAVE NFS-E\n53 / 29305011208058923000106000000000005326090216484092\n\n  \n  \n\x0c'


def test_nota53_incidencia_lajedinho_e_tomador_pojuca_com_hifen(monkeypatch):
    nota = _parse(monkeypatch, RAW_DIGITAL_NOTA_53, nome="dummy_nota53_wmk.pdf")
    assert nota.numero == "53"
    assert nota.prestador.cnpj_cpf == "08058923000106"
    # Antes: Serrinha (1º código "29xxxxx" do documento, Lajedinho fora da tabela).
    assert nota.municipio_incidencia_override == "2919009"
    # Antes: "Pojuca - BA" rejeitado -> tomador com município-padrão São Paulo/SP.
    assert nota.tomador.endereco.codigo_municipio == "2925204"
    assert nota.tomador.endereco.uf == "BA"
    assert nota.valores.valor_servicos == 4400.00
    assert nota.valores.valor_deducoes == 0.0
