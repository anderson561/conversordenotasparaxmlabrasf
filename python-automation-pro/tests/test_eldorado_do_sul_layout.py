# -*- coding: utf-8 -*-
r"""Novo layout: Eldorado do Sul/RS (`eldorado_do_sul_rs`), NFS-e do portal
municipal govbr.cloud ("nfseeldoradodosul.govbr.cloud/nfse.portal"), título
"Nota Fiscal de Serviços Eletrônica (DANFSE)" - NÃO é DANFSe Nacional nem NF-e.

Achado real 2026-11-19: DELL_NF2955797.pdf, 1 página SEM camada de texto
(pdfminer devolve só "\x0c"), DELL COMPUTADORES DO BRASIL LTDA -> NAUTICA
INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA, nota 202600002955797,
R$ 151,52, ISS 2% (3,03) não retido. Antes: o texto de OCR caía em
LAYOUT_GENERICO, a página era descartada como "Layout não reconhecido" e a
conversão terminava sem XML ("parece ser baseado em imagem/scan").

`OCR_PAGINA` é a saída REAL de `_extract_via_ocr` do PDF e `RECORTES` a saída
REAL de `eldorado_do_sul_nfse.ler_recortes`, preservadas verbatim com os erros
de OCR que travam regressões:
  - a caixa "Número da NFS-e" e o "Dt. de Emissão" somem do texto de página
    inteira (só os recortes os leem);
  - o CNPJ do tomador sai "16.665 B69/0002.97" (só o recorte, conferido pelo
    dígito verificador, dá 16.699.869/0002-97);
  - o '@' do e-mail do tomador vira "O" ("COMERCIALSPOTIDELLI.COM.BR");
  - a coluna "Município de Prestação" sai colada na razão social do tomador;
  - o código de barras do rodapé imprime NÚMERO + CÓDIGO VERIFICADOR + CNPJ do
    prestador ("202600002955797830e3b7ff72381189000110").
"""
from src.extractors import eldorado_do_sul_nfse as eld
from src.extractors.pdf_extractor import LAYOUT_ELDORADO_DO_SUL, SPPdfExtractor
from src.transformers.abrasf_transformer import Abrasf201Transformer
from src.utils.ibge_resolver import IBGEResolver

OCR_PAGINA = 'Nota Fiscal de Serviços Eletrônica (DANFSE)\n\nDELL COMPUTADORES DO BRASIL LTDA\nAV INDUSTRIAL BELGRAF, 400 - -\n\nCEP: 92990-000 - Bairro: Industrial\nMunicípio: Eldorado do Sul - RS\nFones (05) 19274.5800 * E. É k Data do Serviço Código Verificador\n\nCNPJ/CPF Inscrição Estadual Inscrição Municipal E E 10/02/2026 830e3b7ff\n72.381.189/0001-10 2670013494 3033 E SP =\n\nSecretaria da Fazenda\n\nMUNICÍPIO DE ELDORADO DO SUL/RS Exigibilidade Tributado no Município\n(o\n\nFone: - https://nfseeldoradodosul.govbr.cloud/nfse.portal Exigível Eldorado do Sul/RS\n\nTOMADOR DO SERVIÇO Município de Prestação do Serviço\n\n[Nome / Razão Social\n\nNAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA Eldorado do Sul/RS\nEndereço\n\nAL GABRIEL MONTEIRO DA SILVA C TERREA,1480\n\n[Cidade UF fone CEP\n\nSão Paulo sp | 5) 13481-5500 01442-001\n\n[Bairro\n\nJD AMERICA\n\nCNPJ 7 CPF inscrição Municipal inscrição Estadual\n\n16.665 B69/0002.97 O\nE-mail\n\nCOMERCIALSPOTIDELLI.COM.BR\n\nINTERMEDIÁRIO DO SERVIÇO\nNome / Razão Social CNPJ / CPF Inscrição Municipal\n\nDESCRIÇÃO DOS SERVIÇOS VALOR TOTAL VALOR IMPOSTO RETIDO\n\nINSS: nao tem cessao de mao-de-obra e nao se enquadra na IN RFB n 2110/2022***PIS, COFINS 151,52 2,00 3,03 Não\ne CSLL nao sujeitos a retencao***NFSe 1 de 1 ***DOF: 02-728767245004.01***Forma Pag: Boleto\n\n1025753691092***Prazo: PD*** 802-7004 - Suporte tecnico - CompleteCare, 1 ano (QTD: 1 VL\n\nUNIT: R$ 52,48) 802-7016 - Suporte tecnico de Informatica no local apos diagnostico, 1 ano (QTD:\n\n1 VL UNIT: R$ 99,04) . Alíquota Efetiva: 2,0000000000%.\n\nCódigo do Serviço Código NBS\n01.07 - Suporte técnico em informática, inclusive instalação, configuração e ad\nmanutenção de programas de computação e bancos de dados.\n\nCIDE [COFINS [COFINS Importação ICMS PIS/PASEP PIS/PASEP Importação\n0,00 [0,00 0,00 [0,00 0,00 [0,00 0,00 [0,00\n\n[Base Cálculo ISSQN Próprio [Valor do ISSQN Próprio [Base Cálculo ISSQN Retido [Valor do ISSQN Retido [Valor Total do ISSQN [Valor Dedução/Descontos\n\n151,52 3,03 0,00 0,00 3,03 0,00\n\nInformações Adicionais\n\nNFS-e Gerada a Partir do RPS 2955694 | Série: E | Emitido em: 10/02/2026 | Tipo: Recibo Provisório de Serviço.\nLei 12741/2012: Mun: R$3,03; Est: R$0,00; Fed: R$20,38; Total Aprox: R$23,41. Fonte: IBPT.\n\nConsulta realizada em 10/02/2026 às 20:15:17.\nPara consultar a autenticidade acesse: https://nfseeldoradodosul.govbr.cloud/nfse.portal\n\n202600002955797830e3b7ff72381189000110\n'

RECORTES = {
    'cabecalho': [
        'Número da NFS-e\n202600002955797\nData do Serviço Código Verificador\n10/02/2026 830e3b7ff\n',
        'Número da NFS-e\n202600002955797\nData do Serviço Código Verificador\n10/02/2026 830e3b7ff\n',
    ],
    'emissao': [
        'Dt. de Emissão Tributado no Município\n10/02/2026 Eldorado do Sul/RS\nMunicíbio de Prestacão do Servico\n',
        'LEI Lois | o | CM alra\nDt. de Emissão Tributado no Município\n10/02/2026 Eldorado do Sul/RS\nMunicíbio de Prestacão do Servico\n',
    ],
    'prestador': [
        'INOUA PisCal GO SOCrVICOS EICUrOMI\nDELL COMPUTADORES DO BRASIL LTDA zl\nAV INDUSTRIAL BELGRAF, 400 - -\nCEP: 92990-000 - Bairro: Industrial\nMunicipio: Eldorado do Sul - RS\nE-mail: NFE@DELL.COM\nFone: (05) 13274-5500 b\nCNPJ / CPF Inscrigdo Estadual Inscri¢ao Municipal\n72.381.189/0001-10 2670013494 3033 El\n',
        'INOUd Pistal OC SCrVICUS FAICUOMI\nDELL COMPUTADORES DO BRASIL LTDA Oo}\nAV INDUSTRIAL BELGRAF, 400 - -\nCEP: 92990-000 - Bairro: Industrial\nMunicipio: Eldorado do Sul - RS\nE-mail: NFE@DELL.COM\nFone: (05) 13274-5500 .\nCNPJ / CPF Inscrigao Estadual Inscrigao Municipal\n72.381.189/0001-10 2670013494 3033 Oo}\n',
    ],
    'cnpj_tomador': [
        '[16.699.869/0002-97 Lo l Lo |\n',
        '[16.699.869/0002-97 | l | l |\n',
    ],
    'email_tomador': [
        '|COMERCIALSP@TIDELLI.COM.BR _ _ |\n',
        '[COMERCIALSP@TIDELLI.COM.BR a _ |\n',
    ],
}

DISCRIMINACAO = (
    "INSS: nao tem cessao de mao-de-obra e nao se enquadra na IN RFB n 2110/2022***PIS, COFINS "
    "e CSLL nao sujeitos a retencao***NFSe 1 de 1 ***DOF: 02-728767245004.01***Forma Pag: Boleto "
    "1025753691092***Prazo: PD*** 802-7004 - Suporte tecnico - CompleteCare, 1 ano (QTD: 1 VL "
    "UNIT: R$ 52,48) 802-7016 - Suporte tecnico de Informatica no local apos diagnostico, 1 ano (QTD: "
    "1 VL UNIT: R$ 99,04) . Alíquota Efetiva: 2,0000000000%."
)


# ---------------------------------------------------------------------------
# Infra
# ---------------------------------------------------------------------------

def _converter(monkeypatch, tmp_path, texto=OCR_PAGINA, recortes=RECORTES):
    """Caminho real (`parse_multiple`) de um PDF sem camada de texto: o
    pdfminer devolve só o form feed, o OCR de página inteira devolve `texto`
    e os recortes dedicados devolvem `recortes`."""
    pdf = tmp_path / "DELL_NF2955797.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "\x0c")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: texto)
    monkeypatch.setattr(eld, "ler_recortes", lambda pdf_path, page_idx: recortes)
    return SPPdfExtractor(str(pdf)).parse_multiple()


def _uma_nota(monkeypatch, tmp_path, texto=OCR_PAGINA, recortes=RECORTES):
    notas = _converter(monkeypatch, tmp_path, texto, recortes)
    assert len(notas) == 1
    return notas[0]


def _extrair(texto=OCR_PAGINA, recortes=RECORTES):
    r = IBGEResolver()
    return eld.extrair(texto, recortes, lambda nome, uf: r.extract_and_validate(nome, uf, city_hint=nome))


# ---------------------------------------------------------------------------
# Detecção
# ---------------------------------------------------------------------------

def test_detecta_layout_no_texto_real(tmp_path):
    ex = SPPdfExtractor(str(tmp_path / "x.pdf"))
    assert ex._detect_layout_page(OCR_PAGINA) == LAYOUT_ELDORADO_DO_SUL
    ex.raw_text = OCR_PAGINA
    assert ex._detect_layout() == LAYOUT_ELDORADO_DO_SUL


def test_gate_nao_dispara_com_eldorado_do_sul_solto_no_endereco(tmp_path):
    """"Eldorado do Sul" como município de prestador/tomador de outra nota
    (sem o título "(DANFSE)" do portal) nunca basta."""
    texto = ("PREFEITURA MUNICIPAL DE PORTO ALEGRE\nNOTA FISCAL DE SERVIÇOS ELETRÔNICA\n"
             "Tomador: FULANO LTDA\nMunicípio: Eldorado do Sul - RS\nCódigo Verificador: ABC123\n")
    assert not eld.eh_template(texto)
    sem_titulo = OCR_PAGINA.replace("(DANFSE)", "")
    assert not eld.eh_template(sem_titulo)
    ex = SPPdfExtractor(str(tmp_path / "x.pdf"))
    assert ex._detect_layout_page(sem_titulo) != LAYOUT_ELDORADO_DO_SUL


def test_gate_exige_marca_do_municipio():
    outro = (OCR_PAGINA.replace("nfseeldoradodosul", "nfseoutracidade")
             .replace("MUNICÍPIO DE ELDORADO DO SUL", "MUNICÍPIO DE OUTRA CIDADE"))
    assert not eld.eh_template(outro)


# ---------------------------------------------------------------------------
# Conversão completa (na main: nenhuma nota)
# ---------------------------------------------------------------------------

def test_nota_real_campo_a_campo(monkeypatch, tmp_path):
    n = _uma_nota(monkeypatch, tmp_path)
    assert n.avisos == []
    assert n.numero == "202600002955797"
    assert n.codigo_verificacao == "830e3b7ff"
    assert n.data_emissao.strftime("%Y-%m-%d") == "2026-02-10"
    assert n.competencia.strftime("%Y-%m-%d") == "2026-02-01"
    assert n.servico_codigo == "0107"
    assert n.discriminacao == DISCRIMINACAO
    assert n.intermediario is None
    assert n.municipio_incidencia_override is None

    p = n.prestador
    assert (p.cnpj_cpf, p.inscricao_municipal, p.razao_social) == (
        "72381189000110", "3033", "DELL COMPUTADORES DO BRASIL LTDA")
    e = p.endereco
    assert (e.logradouro, e.numero, e.complemento, e.bairro, e.codigo_municipio, e.uf, e.cep) == (
        "AV INDUSTRIAL BELGRAF", "400", None, "Industrial", "4306767", "RS", "92990000")
    assert p.email == "NFE@DELL.COM"
    assert p.telefone == "(05)13274-5500"

    t = n.tomador
    assert (t.cnpj_cpf, t.inscricao_municipal, t.razao_social) == (
        "16699869000297", None, "NAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA")
    e = t.endereco
    assert (e.logradouro, e.numero, e.complemento, e.bairro, e.codigo_municipio, e.uf, e.cep) == (
        "AL GABRIEL MONTEIRO DA SILVA", "1480", "C TERREA", "JD AMERICA", "3550308", "SP", "01442001")
    assert t.email == "COMERCIALSP@TIDELLI.COM.BR"

    v = n.valores
    assert (v.valor_servicos, v.valor_deducoes, v.base_calculo, v.aliquota, v.valor_iss) == (
        151.52, 0.0, 151.52, 0.02, 3.03)
    assert v.iss_retido is False and v.valor_iss_retido == 0.0
    assert (v.valor_pis, v.valor_cofins, v.valor_inss, v.valor_ir, v.valor_csll, v.outras_retencoes) == (0.0,) * 6
    assert v.valor_liquido_nfse == 151.52


def test_xml_abrasf(monkeypatch, tmp_path):
    xml = Abrasf201Transformer().transform(_uma_nota(monkeypatch, tmp_path))
    for trecho in (
        "<Numero>202600002955797</Numero>", "<CodigoVerificacao>830e3b7ff</CodigoVerificacao>",
        "<Competencia>2026-02-01</Competencia>", "<ValorServicos>151.52</ValorServicos>",
        "<BaseCalculo>151.52</BaseCalculo>", "<Aliquota>0.02</Aliquota>", "<ValorIss>3.03</ValorIss>",
        "<IssRetido>2</IssRetido>", "<ValorLiquidoNfse>151.52</ValorLiquidoNfse>",
        "<ItemListaServico>0107</ItemListaServico>", "<MunicipioIncidencia>4306767</MunicipioIncidencia>",
        "<Cnpj>16699869000297</Cnpj>",
    ):
        assert trecho in xml, trecho
    # prestador, órgão gerador e serviço
    assert xml.count("<CodigoMunicipio>4306767</CodigoMunicipio>") == 3


def test_ibge_eldorado_do_sul_cadastrado():
    assert IBGEResolver().extract_and_validate("Eldorado do Sul", "RS", city_hint="Eldorado do Sul") == "4306767"


# ---------------------------------------------------------------------------
# Sem recortes (PDF digital / Tesseract indisponível) e guardas
# ---------------------------------------------------------------------------

def test_sem_recortes_numero_vem_do_codigo_de_barras_e_cnpj_ilegivel_vira_sentinela():
    n = _extrair(recortes={})
    # Código Verificador lido na linha fundida da página inteira; o número
    # sai do código de barras (corpo = número + CV, CNPJ do prestador confere).
    assert (n.numero, n.codigo_verificacao) == ("202600002955797", "830e3b7ff")
    # "16.665 B69/0002.97" não passa no DV: sentinela + aviso, nunca adivinha.
    assert n.tomador.cnpj_cpf == eld.SENTINELA_DOC
    assert any("CNPJ/CPF do tomador ilegível" in a for a in n.avisos)
    # "Dt. de Emissão" não sai na página inteira: usa a Data do Serviço, com aviso.
    assert n.data_emissao.strftime("%d/%m/%Y") == "10/02/2026"
    assert any("Dt. de Emissão ilegível" in a for a in n.avisos)
    # '@' lido como "O" e sem 2 leituras: sem e-mail (contato não se inventa).
    assert n.tomador.email is None
    assert n.prestador.email is None


def test_codigo_de_barras_divergente_gera_aviso():
    texto = OCR_PAGINA.replace("202600002955797830e3b7ff72381189000110", "202600002955798830e3b7ff72381189000110")
    n = _extrair(texto)
    assert n.numero == "202600002955797"
    assert any("não conferem com o texto do código de barras" in a for a in n.avisos)


def test_sem_numero_nem_codigo_de_barras_vira_sentinela():
    texto = OCR_PAGINA.replace("202600002955797830e3b7ff72381189000110", "")
    n = _extrair(texto, {})
    assert n.numero == eld.SENTINELA_NUMERO
    assert any("Número da NFS-e ilegível" in a for a in n.avisos)


def test_aliquota_acima_do_teto_vira_zero_com_aviso():
    texto = OCR_PAGINA.replace("151,52 2,00 3,03 Não", "151,52 6,00 3,03 Não")
    n = _extrair(texto)
    assert n.valores.aliquota == 0.0
    assert any("acima do teto legal de 5%" in a for a in n.avisos)


def test_iss_retido_sim_desconta_do_liquido():
    texto = (OCR_PAGINA.replace("151,52 2,00 3,03 Não", "151,52 2,00 3,03 Sim")
             .replace("151,52 3,03 0,00 0,00 3,03 0,00", "0,00 0,00 151,52 3,03 3,03 0,00"))
    n = _extrair(texto)
    assert n.valores.iss_retido is True
    assert n.valores.valor_iss_retido == 3.03
    assert n.valores.valor_liquido_nfse == 148.49


def test_cnpj_tomador_reprovado_no_dv_e_ignorado():
    recortes = dict(RECORTES, cnpj_tomador=["[16.699.869/0002-98 |\n", "[16.699.869/0002-97 |\n"])
    n = _extrair(recortes=recortes)
    assert n.tomador.cnpj_cpf == "16699869000297"
    assert not any("divergentes do CNPJ do tomador" in a for a in n.avisos)


def test_tributacao_fora_do_municipio_vira_incidencia(monkeypatch, tmp_path):
    recortes = dict(RECORTES, emissao=[r.replace("Eldorado do Sul/RS", "São Paulo/SP") for r in RECORTES["emissao"]])
    texto = OCR_PAGINA.replace("Exigível Eldorado do Sul/RS", "Exigível São Paulo/SP")
    n = _uma_nota(monkeypatch, tmp_path, texto=texto, recortes=recortes)
    assert n.municipio_incidencia_override == "3550308"


def test_logradouro_sem_complemento_reconhecivel_fica_inteiro():
    texto = OCR_PAGINA.replace("AL GABRIEL MONTEIRO DA SILVA C TERREA,1480", "RUA DAS FLORES,25")
    n = _extrair(texto)
    assert (n.tomador.endereco.logradouro, n.tomador.endereco.numero, n.tomador.endereco.complemento) == (
        "RUA DAS FLORES", "25", None)
