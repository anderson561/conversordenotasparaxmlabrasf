# -*- coding: utf-8 -*-
import os

from src.extractors.pdf_extractor import SPPdfExtractor

# Texto REAL do OCR (Tesseract) da pagina 1 do PDF "NF 6013.pdf" (3 paginas;
# so a 1a e a NFS-e, as outras duas sao a fatura anexa do prestador): NFS-e
# ESCANEADA de Camacari/BA (layout camacari_cpqd), CLINICA MEDICINA HUMANA
# LTDA -> MASSA ALIMENTACAO E SERVICOS S/A, nota no 6013, R$ 477,45.
#
# Regressao do bug real: o XML saia com <Numero>3</Numero> / Id="NFSe3". Das
# varias tentativas de leitura da caixa "Numero da Nota / Data de Emissao /
# Codigo de autenticidade", so UMA tem o rotulo limpo ("e Numero da Nota",
# colado ao icone "e" do OCR), e logo depois dele o texto traz a faixa
# "PREFEITURA MUNICIPAL DE CAMACARI" e o rotulo vizinho "3 Data de Emissao" -
# o "3" e o fragmento do icone colado ao rotulo da PROXIMA celula, nao o valor
# deste rotulo. O valor real "6013" sobrevive em outras duas leituras: a linha
# sintetica de abertura (antes de qualquer rotulo) e "mero da Nota" seguido de "6013" na linha
# de baixo (rotulo degradado - perdeu o "Nu", por isso o regex de rotulo limpo nao casa).
MOCK_TEXT = '6013\nData de Emissão\nCódigo de autenticidade\n058126001\nNº 76\n\nmero da Nota\n6013\na de Emissão\n13/01/2026 09:19\nligo de autenticidade\nY665T5W64\n1\nNº: 76\n\né Número da Nota\nPREFEITURA MUNICIPAL DE CAMAÇARI\n3 Data de Emissão\n|\nNOTA FISCAL DE SERVIÇOS ELETRÔNICA\nY665T5W64\nPRESTADOR DE SERVIÇOS\nNome/Razão Social: CLINICA MEDICINA HUMANA LTDA\nCPF/CNPJ: 50.091.585/0001-70 Inscrição Municipal: 0058126001\nLogradouro: | RUA DO ALECRIM Nº: 76\nCompl.: Bairro: CENTRO\nCEP: 42800025 Município: CAMAÇARI UF: BA\nTOMADOR DE SERVIÇOS\nNome/Razão Social: MASSA ALIMENTAÇÃO E SERVIÇOS S/A\nCPF/CNPJ: 09.033.381/0005-03 Inscrição Municipal:\nLogradouro: | VIA MANTOIM Nº S/N\nCompl.: Bairro: DISTRITO INDUSTRIAL\nCEP! 43813000 Município: CANDEIAS UF: BA\nDISCRIMINAÇÃO DOS SERVIÇOS\nDESCRIÇÃO QTD VALOR UNIT (R$) VALOR TOTAL (R$)\nREF. Á SERVIÇOS MÉDICOS PRESTADOS NO MÊS DE DEZEMBRO/2025 1,0000 477,45 477,45\nVENCIMENTO: 13/02/2026\nAp ES E frete o\na Eae\n[does XML PDF [of\nRetenções (R$) Totais (R$)\nPIS: 3,10 | Valor dos Serviços (R$) 477,45\nCOFINS: 14,32 |Deduções (-) 0,00\nINSS: 0,00 | Base de Cálculo (=) 477,45\nIR: 0,00 |Alíquota (%) 3,00\nCSLL: 4,77 | Valor do ISS (R$) 14,32\nOutras: 0,00 | Valor Líquido da Nota (=) 455,26\nTotal de Retenções: 22,19\nTipo de tributação: A RECOLHER PELO PRESTADOR Data da prestação do serviço: 13/01/2026\nMunicípio da prestação do serviço: 2905701 - CAMACARI\nMunicípio da tributação: 2905701 - CAMACARI\nCNAE:\nServiço: 000403 - HOSPITAIS, CLÍNICAS, LABORATÓRIOS, SANATÓRIOS, MANICÔMIOS, CASAS DE SAÚDE, PRONTOS-SOCORROS,\nAMBULATÓRIOS E CONGÊNERES.\nCPqD - Gestão Pública Data Impressão: 13/01/2026 09:19\n\n'


def _converter(monkeypatch, nome_arquivo):
    caminho = os.path.join("tests", nome_arquivo)
    os.makedirs("tests", exist_ok=True)
    with open(caminho, "wb") as f:
        f.write(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_TEXT)
    try:
        lista = SPPdfExtractor(caminho).parse_multiple()
    finally:
        if os.path.exists(caminho):
            os.remove(caminho)
    return lista


def test_camacari_numero_nao_vira_fragmento_colado_ao_rotulo_vizinho(monkeypatch):
    lista = _converter(monkeypatch, "dummy_camacari_6013.pdf")
    assert len(lista) == 1
    nfse = lista[0]
    assert nfse.numero == "6013"
    assert nfse.data_emissao.day == 13
    assert nfse.data_emissao.month == 1
    assert nfse.data_emissao.year == 2026
    assert nfse.codigo_verificacao == "Y665T5W64"
    assert nfse.prestador.cnpj_cpf == "50091585000170"


def test_camacari_numero_nao_depende_do_nome_do_arquivo(monkeypatch):
    # Nome com outro numero que NAO pode ser usado como fallback do numero.
    lista = _converter(monkeypatch, "copia_qualquer_777.pdf")
    assert lista[0].numero == "6013"


# ---------------------------------------------------------------------------
# Colaterais da MESMA nota 6013 (mesmo texto OCR real): retencoes, tomador,
# hora da emissao e Candeias/BA no resolver de IBGE.
# ---------------------------------------------------------------------------

def _nfse(monkeypatch, texto=None, nome="dummy_camacari_6013_col.pdf"):
    caminho = os.path.join("tests", nome)
    os.makedirs("tests", exist_ok=True)
    with open(caminho, "wb") as f:
        f.write(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: texto or MOCK_TEXT)
    try:
        return SPPdfExtractor(caminho).parse_multiple()[0]
    finally:
        if os.path.exists(caminho):
            os.remove(caminho)


def test_camacari_scan_retencoes_federais_da_grade_impressa(monkeypatch):
    nfse = _nfse(monkeypatch)
    v = nfse.valores
    # Impresso: PIS 3,10 / COFINS 14,32 / CSLL 4,77 / Total de Retencoes 22,19
    assert v.valor_pis == 3.10
    assert v.valor_cofins == 14.32
    assert v.valor_csll == 4.77
    assert v.valor_inss == 0.0
    assert v.valor_ir == 0.0
    assert v.outras_retencoes == 0.0
    assert v.valor_servicos == 477.45
    assert v.valor_liquido_nfse == 455.26
    # coerencia: liquido = servicos - retencoes federais (ISS a recolher pelo prestador)
    assert round(v.valor_servicos - (v.valor_pis + v.valor_cofins + v.valor_csll), 2) == v.valor_liquido_nfse


def test_camacari_scan_retencoes_nao_preenche_quando_soma_nao_bate(monkeypatch):
    # Leitura errada de uma celula (COFINS 14,92 em vez de 14,32): a soma
    # (22,79) nao fecha com o "Total de Retencoes" (22,19) -> nada de valor
    # plausivel porem errado; fica zerado e avisado.
    texto = MOCK_TEXT.replace("COFINS: 14,32", "COFINS: 14,92")
    assert texto != MOCK_TEXT
    nfse = _nfse(monkeypatch, texto)
    v = nfse.valores
    assert (v.valor_pis, v.valor_cofins, v.valor_csll) == (0.0, 0.0, 0.0)
    assert any("Retenções" in a or "retenções" in a for a in nfse.avisos)


def test_camacari_scan_tomador_cep_com_exclamacao_e_numero_sn_sem_dois_pontos(monkeypatch):
    nfse = _nfse(monkeypatch)
    e = nfse.tomador.endereco
    assert e.logradouro == "VIA MANTOIM"
    assert e.numero == "S/N"
    assert e.bairro == "DISTRITO INDUSTRIAL"
    assert e.cep == "43813000"
    assert e.municipio == "CANDEIAS"
    assert e.uf == "BA"
    assert e.codigo_municipio == "2906501"


def test_camacari_scan_data_emissao_com_hora_do_rotulo_degradado(monkeypatch):
    nfse = _nfse(monkeypatch)
    d = nfse.data_emissao
    assert (d.year, d.month, d.day, d.hour, d.minute) == (2026, 1, 13, 9, 19)


def test_camacari_scan_competencia_segue_data_da_prestacao(monkeypatch):
    # A nota NAO imprime campo "Competencia" (conferido na imagem); vale a
    # regra existente: 1o dia do mes da "Data da prestacao do servico".
    nfse = _nfse(monkeypatch)
    assert (nfse.competencia.year, nfse.competencia.month, nfse.competencia.day) == (2026, 1, 1)


def test_ibge_resolver_candeias_ba_codigo_oficial():
    from src.utils.ibge_resolver import IBGEResolver
    r = IBGEResolver()
    assert r.extract_and_validate("CANDEIAS", "BA", city_hint="CANDEIAS") == "2906501"


# ---------------------------------------------------------------------------
# Resolver de IBGE: municipio LIDO mas ausente da tabela nao cai na capital
# em silencio (aviso), e nome curto sem city_hint tambem consulta a tabela.
# ---------------------------------------------------------------------------

def test_resolver_municipio_lido_ausente_da_tabela_registra_fallback_e_avisa():
    from src.utils.ibge_resolver import IBGEResolver
    r = IBGEResolver()
    cod = r.extract_and_validate("XIQUE XIQUE", "BA", city_hint="XIQUE XIQUE")
    # o valor devolvido continua sendo o da capital da UF (API inalterada) ...
    assert cod == "2927408"
    # ... mas agora o fallback fica registrado e gera aviso nominal
    aviso = r.aviso_fallback_capital("Xique Xique", "BA", cod, "tomador")
    assert "Xique Xique" in aviso and "não consta" in aviso and "2927408" in aviso
    assert "tomador" in aviso
    # codigo diferente do fallback (ex.: outro codigo lido) nao gera aviso
    assert r.aviso_fallback_capital("Xique Xique", "BA", "2933604") == ""


def test_resolver_capital_da_uf_placeholder_e_vazio_nao_sao_sinalizados():
    from src.utils.ibge_resolver import IBGEResolver
    r = IBGEResolver()
    assert r.extract_and_validate("Maceió", "AL", city_hint="Maceió") == "2704302"
    assert r.extract_and_validate("Não informado", "BA", city_hint="Não informado") == "2927408"
    assert r.extract_and_validate("", "BA") == "2927408"
    assert r.extract_and_validate("CANDEIAS", "BA", city_hint="CANDEIAS") == "2906501"
    for nome, uf in (("Maceió", "AL"), ("Não informado", "BA"), ("CANDEIAS", "BA")):
        for cod in ("2704302", "2927408", "2906501"):
            assert r.aviso_fallback_capital(nome, uf, cod) == ""
    r.limpar_fallbacks_capital()


def test_resolver_nome_curto_sem_city_hint_consulta_a_tabela_de_cidades():
    from src.utils.ibge_resolver import IBGEResolver
    # Antes: sem city_hint o lookup era pulado e Camaçari saia 2927408 (Salvador).
    assert IBGEResolver().extract_and_validate("Camacari", "BA") == "2905701"


def test_nfse_municipio_do_tomador_ausente_da_tabela_gera_aviso(monkeypatch):
    texto = MOCK_TEXT.replace("Município: CANDEIAS", "Município: XIQUE XIQUE")
    assert texto != MOCK_TEXT
    nfse = _nfse(monkeypatch, texto)
    assert nfse.tomador.endereco.codigo_municipio == "2927408"  # fallback (capital) mantido
    avisos = [a for a in nfse.avisos if "não consta na tabela de códigos IBGE" in a]
    assert len(avisos) == 1
    assert "XIQUE XIQUE" in avisos[0] and "tomador" in avisos[0]


def test_nfse_municipio_cadastrado_nao_gera_aviso_de_municipio(monkeypatch):
    nfse = _nfse(monkeypatch)
    assert not any("tabela de códigos IBGE" in a for a in nfse.avisos)


# ---------------------------------------------------------------------------
# Camacari2: mesmas tolerancias de OCR do Camacari3 (Nº S/N, CEP!, data).
# ---------------------------------------------------------------------------

def _extrator_camacari2(monkeypatch):
    from src.extractors.pdf_extractor import LAYOUT_CAMACARI_2
    caminho = os.path.join("tests", "dummy_camacari2_6013.pdf")
    os.makedirs("tests", exist_ok=True)
    with open(caminho, "wb") as f:
        f.write(b"%PDF-1.4")
    try:
        ex = SPPdfExtractor(caminho)
    finally:
        os.remove(caminho)
    ex.raw_text = MOCK_TEXT
    ex.layout = LAYOUT_CAMACARI_2
    return ex


def test_camacari2_tomador_aceita_cep_com_exclamacao_e_numero_sn(monkeypatch):
    ex = _extrator_camacari2(monkeypatch)
    e = ex._extrair_entidade_camacari2(False).endereco
    assert e.logradouro == "VIA MANTOIM"
    assert e.numero == "S/N"
    assert e.cep == "43813000"
    assert e.codigo_municipio == "2906501"
    p = ex._extrair_entidade_camacari2(True).endereco
    assert p.numero == "76" and p.cep == "42800025"


def test_camacari2_data_emissao_com_rotulo_degradado(monkeypatch):
    ex = _extrator_camacari2(monkeypatch)
    d = ex._extrair_data_emissao()
    assert (d.year, d.month, d.day, d.hour, d.minute) == (2026, 1, 13, 9, 19)


# ---------------------------------------------------------------------------
# Retencoes com a virgula perdida pelo OCR: recuperadas SO se uma unica
# combinacao fechar com o "Total de Retencoes" impresso.
# ---------------------------------------------------------------------------

def test_camacari_scan_retencao_sem_virgula_e_recuperada_pela_soma(monkeypatch):
    texto = MOCK_TEXT.replace("COFINS: 14,32", "COFINS: 1432")
    assert texto != MOCK_TEXT
    nfse = _nfse(monkeypatch, texto)
    v = nfse.valores
    assert (v.valor_pis, v.valor_cofins, v.valor_csll) == (3.10, 14.32, 4.77)
    assert not any("Retenções federais" in a for a in nfse.avisos)


def test_camacari_scan_total_de_retencoes_sem_virgula_tambem_e_recuperado(monkeypatch):
    texto = MOCK_TEXT.replace("Total de Retenções: 22,19", "Total de Retenções: 2219")
    assert texto != MOCK_TEXT
    v = _nfse(monkeypatch, texto).valores
    assert (v.valor_pis, v.valor_cofins, v.valor_csll) == (3.10, 14.32, 4.77)


def test_camacari_scan_retencao_sem_virgula_impossivel_zera_e_avisa(monkeypatch):
    # "1499" -> 14,99: nenhuma combinacao fecha com 22,19 -> zerado + aviso.
    texto = MOCK_TEXT.replace("COFINS: 14,32", "COFINS: 1499")
    nfse = _nfse(monkeypatch, texto)
    v = nfse.valores
    assert (v.valor_pis, v.valor_cofins, v.valor_csll) == (0.0, 0.0, 0.0)
    assert any("Retenções federais" in a for a in nfse.avisos)


def test_combinacao_unica_exige_exatamente_uma_combinacao():
    f = SPPdfExtractor._combinacao_unica
    assert f([[3.10], [14.32], [4.77]], 22.19) == (3.10, 14.32, 4.77)
    assert f([[3.10], [14.32], [4.77]], 22.00) is None            # 0 combinacoes
    # duas leituras por celula, duas combinacoes fecham (0,05+5,00 e 5,00+0,05)
    assert f([[0.05, 5.0], [0.05, 5.0]], 5.05) is None            # ambiguo
    assert f([[0.05, 5.0], [0.07]], 5.07) == (5.0, 0.07)          # so uma fecha
