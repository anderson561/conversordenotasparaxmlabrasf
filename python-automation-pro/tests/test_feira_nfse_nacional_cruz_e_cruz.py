# -*- coding: utf-8 -*-
r"""Layout `feira_de_santana_nfse_nacional`: foto de celular (180°, bordas
esquerda/direita cortadas) da NFS-e de Feira de Santana/BA com a chave
"NFS-e Nacional" de 50 dígitos.

Nota real "cruz e cruz.pdf" (CRUZ E CRUZ ADVOCACIA E ASSESSORIA JURIDICA
SOCIEDADE DE ADVOGADOS -> SARAVIMANA PATRIMONIAL LTDA, R$ 6.316,62,
29/09/2026). Antes: caía no LAYOUT_FEIRA (marca da cidade) e saía com Número
"8055622" (o nº do PROCESSO JUDICIAL da descrição), CNPJ do prestador e do
tomador `00000000000100`, razão do prestador poluída com o rótulo da linha
seguinte, razão do tomador copiada do prestador, valores 0,00, ISS 29,00
fabricado e município Salvador.

As fixtures são a saída REAL do pipeline (`_extract_via_ocr`): `RECORTES` =
linhas sintéticas FEIRANAC_* dos recortes dedicados; `PAGINA` = leitura de
página inteira (sem a chave, com o CNPJ do tomador e o CNAE lidos errado).
"""

import os

import pytest

from src.extractors import feira_nfse_nacional as fn
from src.extractors import pdf_extractor as pdf_extractor_mod
from src.extractors.pdf_extractor import (
    LAYOUT_FEIRA,
    LAYOUT_FEIRA_NFSE_NACIONAL,
    SPPdfExtractor,
)

RECORTES = r'''FEIRANAC_CHAVE: 29108001246065189000100202600000002926090408657100
FEIRANAC_END_PREST: 4 BARÃO DO RIO BRANCO, 1517, EDIF PETROPOLIS SALA 204, Kalilândia|44001205||
FEIRANAC_CNPJ_PREST_SUFIXO: 065189000100
FEIRANAC_END_TOM: ida Getúlio Vargas, 744 - PARQUE GETÚLIO VARGAS|44075425|Feira de Santana|BA
FEIRANAC_CNPJ_TOM_SUFIXO: 04636000119
FEIRANAC_CNAE: 6911701
FEIRANAC_VALOR_SERVICOS: 6.316,62
FEIRANAC_VALOR_LIQUIDO: 6.316,62
FEIRANAC_SERVICO: Advocacia, CNAE: 6911703,
FEIRANAC_SERVICO: Esse ãEf fãgZT ÊÇÊÕMMEMÇCMCFga o
FEIRANAC_DESC: nhamento do processo judicial de nº 8055622-41.2022.8.05.0001, referente à AÇÃO DE DESPEJO C/C COBRANÇA DE ALUGUÉIS,
FEIRANAC_DESC: RIOS E PEDIDO LIMINAR PARA DESOCUPAÇÃO em faco de AZ COMERCIO E SERVICOS DE ALIMENTOS LTDA e ANDRE ALVES CAVENDISH,
FEIRANAC_DESC: smita na 3º VARA CÍVEL DA COMARCA DE SALVADOR - BA. '
FEIRANAC_DESC_CORTADO: 1'''

PAGINA = r'''ato d Da at Da A, 17 à a
de Administração 1ovm. SEMP E O Sd DAS lo:
aa CEP 44.001-550 = Feira de Santana/BA - Telefona: (75) 368%
2500
S ELETRÔNICA - NFS-e

NOTA FISCAL DE SERVIÇO.
Municipio de Prestação do

Emissão (Nocário de Nrasilta) 05/1 é cerngieaasd
29/09/2026 08:50:58 09/202 Serviço
A Feira de Santana
- BA
Reg. Especial Tributação Exdgibilidade do 155
Empresa de Pequeno Exigivel em Feira de

Microempresário e
porte (ME EPP) Santana
PRESTADOR DE SERVIÇOS

Razão Social
CRUZ E CRUZ ADVOCACIA E ASSESSORIA JURIDICA SOCIEDADE DE ADVOGADOS
vome Fantasia Email
ppa aiii eoconsensocontabilidade.com-br
inscrição Municipal Inscrição Estadual Simples Nacional Incenitivador Cultural Pons/FU%
(75) 8823-0699

SF/CNP)
6.065.189/0001-00 831557 ISENTO Sim Não
-205 - Feira de Santana - BA

jereço
A BARAO DO RIO BRANCO, 1517, EDIF PETROPOLIS SALA 204, Kalilândia - CEP: 44001 e

TADOR DE SERVIÇOS

=/Razão Social
TAVIMANA PATRIMONIAL LTDA
NP) Inscrição Municipal Inscrição Estadual Fone/Fax E-mail
704.636/0001-19 (71) 3221-6000 adm.smecsb.med.br
ço
ida Getúlio Vargas, 744 - PARQUE GETÚLIO VARGAS - CEP: 44075-425 - Feira de Santana - BA
ÇO PRESTADO
Advocacia, CNAE: 6911703.
IÇÃO DOS SERVIÇOS
referente à AÇÃO DE DESPEJO C/C COBRANÇA DE ALUGUÉIS,

nhamento do processo judicial de nº 8055622-41.2022.8.05.0001,
LTDA e ANDRE ALVES CAVENDISH,

RIOS E PEDIDO LIMINAR PARA DESOCUP, em faco de AZ COMERCIO E SERVICOS DE ALIMENTOS

amita na 3º VARA CÍVEL DA COMARCA DE SALVADOR - BA.
EDERAIS
INSS (R$) IR (R$) PIS (R$) COFINS (R$) CSLL (R$) Outras Retençõe
0,00 0,00 0,00 0,00 0,00
r ,
Deduções

a E Desc. Cond. (R$) Desc. Incond. (R$) Base de Cólculo ISS (R$) Aliquota

o 0,00 0,00 dedo
ISS (R$) ISS Retido (R$) Valor Líquido (R$) Valor Total Ee

6.316,62 ee e+ es 631662 |

IMAÇÕES'''

MOCK_TEXT = RECORTES + "\n" + PAGINA

CHAVE = "29108001246065189000100202600000002926090408657100"


def _run(monkeypatch, texto=MOCK_TEXT, nome="tests/dummy_feira_nfse_nacional.pdf"):
    os.makedirs("tests", exist_ok=True)
    with open(nome, "wb") as f:
        f.write(b"%PDF-1.4")
    monkeypatch.setattr(pdf_extractor_mod, "extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: texto)
    try:
        return SPPdfExtractor(nome).parse_multiple()
    finally:
        if os.path.exists(nome):
            os.remove(nome)


def _detectores(texto):
    ext = SPPdfExtractor.__new__(SPPdfExtractor)
    ext.pdf_path = "fake.pdf"
    ext.raw_text = texto
    ext.layout = None
    return ext._detect_layout(), ext._detect_layout_page(texto)


# ----------------------------------------------------------------- detecção

def test_detecta_template_novo_e_detectores_sao_simetricos():
    assert _detectores(MOCK_TEXT) == (LAYOUT_FEIRA_NFSE_NACIONAL, LAYOUT_FEIRA_NFSE_NACIONAL)
    # mesmo sem os recortes: gate estrutural da própria página
    assert _detectores(PAGINA) == (LAYOUT_FEIRA_NFSE_NACIONAL, LAYOUT_FEIRA_NFSE_NACIONAL)


def test_nao_regressao_feira_template_antigo_segue_em_layout_feira():
    """Só a cidade (ou a cidade + 1 marca) NÃO basta: o fallback bare continua
    servindo o template antigo, sem alteração."""
    for texto in (
        "PREFEITURA MUNICIPAL DE FEIRA DE SANTANA\nSECRETARIA MUNICIPAL DA FAZENDA",
        "PREFEITURA MUNICIPAL DE FEIRA DE SANTANA\nFato Gerador 03/02/2026\nExigível em Feira de Santana",
        "Tomador: ACME LTDA - Feira de Santana - BA\nNOTA FISCAL DE SERVIÇOS ELETRÔNICA - NFS-e",
    ):
        assert _detectores(texto) == (LAYOUT_FEIRA, LAYOUT_FEIRA), texto


def test_eh_template_exige_cidade():
    assert not fn.eh_template("Reg. Especial Tributação\nMunicípio de Prestação do Serviço\nSão Paulo")
    assert fn.eh_template(PAGINA)


# --------------------------------------------------------- campos da nota real

def test_numero_codigo_e_datas(monkeypatch):
    notas = _run(monkeypatch)
    assert len(notas) == 1
    nota = notas[0]
    # nNFSe da chave — NUNCA o nº do processo judicial ("8055622-41.2022...")
    assert nota.numero == "2026000000029"
    assert nota.codigo_verificacao == CHAVE
    assert nota.data_emissao.strftime("%Y-%m-%dT%H:%M:%S") == "2026-09-29T08:50:58"
    assert nota.competencia.strftime("%Y-%m-%d") == "2026-09-01"


def test_numero_nao_vem_do_nome_do_arquivo(monkeypatch):
    """Família 9: o mesmo PDF sob outro nome (que PARECE um número de nota)."""
    nota = _run(monkeypatch, nome="tests/NF 8055622.pdf")[0]
    assert nota.numero == "2026000000029"


def test_prestador(monkeypatch):
    p = _run(monkeypatch)[0].prestador
    assert p.cnpj_cpf == "46065189000100"
    # corta no fim da linha: "vome Fantasia Email ppa aiii -br" não entra
    assert p.razao_social == "CRUZ E CRUZ ADVOCACIA E ASSESSORIA JURIDICA SOCIEDADE DE ADVOGADOS"
    assert p.inscricao_municipal == "831557"
    assert p.endereco.numero == "1517"
    assert p.endereco.bairro == "Kalilândia"
    assert p.endereco.cep == "44001205"
    assert p.endereco.municipio == "Feira de Santana"
    assert p.endereco.uf == "BA"
    assert p.endereco.codigo_municipio == "2910800"
    assert "BRANCO" in p.endereco.logradouro


def test_tomador(monkeypatch):
    t = _run(monkeypatch)[0].tomador
    assert t.cnpj_cpf == "04904636000119"
    assert t.razao_social == "SARAVIMANA PATRIMONIAL LTDA"
    assert t.cnpj_cpf != _run(monkeypatch)[0].prestador.cnpj_cpf
    assert t.endereco.numero == "744"
    assert t.endereco.bairro == "PARQUE GETÚLIO VARGAS"
    assert t.endereco.cep == "44075425"
    assert t.endereco.municipio == "Feira de Santana"
    assert t.endereco.codigo_municipio == "2910800"
    # o início cortado do logradouro ("ida") não é completado nem vaza
    assert t.endereco.logradouro == "Getúlio Vargas"


def test_valores_iss_asterisco_e_ausente_nao_fabricado(monkeypatch):
    nota = _run(monkeypatch)[0]
    v = nota.valores
    assert v.valor_servicos == pytest.approx(6316.62)
    assert v.valor_liquido_nfse == pytest.approx(6316.62)
    # antes: 29.00 (dia/chave); "*****" = AUSENTE; alíquota cortada = não inventada
    assert v.valor_iss == 0.0
    assert v.base_calculo == 0.0
    assert v.aliquota == 0.0
    assert any('"*****"' in a for a in nota.avisos)


def test_cnae_votado_e_discriminacao_real(monkeypatch):
    nota = _run(monkeypatch)[0]
    # a leitura de página inteira diz 6911703; os recortes (zooms distintos) e a imagem dizem 6911701
    assert nota.codigo_cnae == "6911701"
    d = nota.discriminacao
    assert d.startswith("Advocacia, CNAE: 6911701.")
    assert "AÇÃO DE DESPEJO C/C COBRANÇA DE ALUGUÉIS" in d
    assert "8055622-41.2022.8.05.0001" in d
    assert "3º VARA CÍVEL DA COMARCA DE SALVADOR - BA." in d
    assert d != "Serviços prestados conforme nota fiscal."
    # palavras cortadas pela borda esquerda não ficam como lixo no começo das linhas
    assert "nhamento" not in d and "smita" not in d and "RIOS E PEDIDO" not in d


def test_optante_e_avisos(monkeypatch):
    nota = _run(monkeypatch)[0]
    assert nota.optante_simples_nacional is True
    assert nota.regime_especial_tributacao == "6"
    assert any("Foto cortada" in a for a in nota.avisos)
    assert any("contraparte confirmada" in a for a in nota.avisos)


# ------------------------------------------- sentinela quando nada autoverifica

def _sem(linhas_prefixos, texto=MOCK_TEXT):
    return "\n".join(l for l in texto.split("\n") if not l.startswith(linhas_prefixos))


def test_sem_chave_numero_e_codigo_ficam_sentinela(monkeypatch):
    texto = _sem(("FEIRANAC_CHAVE",))
    nota = _run(monkeypatch, texto)[0]
    assert nota.numero == "00000000"
    assert nota.codigo_verificacao == "XXXX-XXXX"
    assert any("Número da nota não encontrado" in a for a in nota.avisos)
    # sem a chave o prestador só tem o sufixo "065189000100" (3 completações
    # válidas por checksum: 37/46/81) -> sentinela, nunca uma das três
    assert nota.prestador.cnpj_cpf.startswith("00000000000")
    assert any("Dados do prestador não identificados" in a for a in nota.avisos)


def test_tomador_ambiguo_sem_evidencia_de_identidade_vira_sentinela(monkeypatch):
    """O sufixo admite 8 completações válidas por checksum: sem a identidade
    confirmada (nome + sufixo), NUNCA se escolhe uma."""
    texto = MOCK_TEXT.replace("TAVIMANA PATRIMONIAL LTDA", "OUTRA EMPRESA QUALQUER LTDA")
    nota = _run(monkeypatch, texto)[0]
    assert nota.tomador.cnpj_cpf.startswith("00000000000")
    assert nota.tomador.razao_social == "OUTRA EMPRESA QUALQUER LTDA"
    assert any("Dados do tomador não identificados" in a for a in nota.avisos)


def test_sem_recortes_numero_nunca_vem_do_processo_judicial(monkeypatch):
    nota = _run(monkeypatch, PAGINA)[0]
    assert nota.numero == "00000000"
    assert nota.numero != "8055622"
    assert nota.valores.valor_iss == 0.0  # nunca o "29.00" fabricado


# -------------------------------------------------------------- helpers puros

def test_chave_decodificada():
    d = fn.decodificar_chave(CHAVE, "2609")
    assert d["numero"] == "2026000000029"
    assert d["cnpj"] == "46065189000100"


def test_chave_rejeitada_por_estrutura():
    assert fn.decodificar_chave(CHAVE, "2509") is None  # AAMM != mês da emissão
    assert fn.decodificar_chave("2927408" + CHAVE[7:]) is None  # outro município
    assert fn.decodificar_chave(CHAVE[:9] + "46065189000101" + CHAVE[23:]) is None  # CNPJ reprova
    assert fn.decodificar_chave(CHAVE[:-1]) is None  # 49 dígitos


def test_votar_chave():
    errada = CHAVE.replace("2926090408", "2925090408")  # leitura 2926 -> 2925
    assert fn.votar_chave([CHAVE, CHAVE, errada], "2609") == CHAVE
    assert fn.votar_chave([CHAVE], "2609") is None  # 1 leitura não é evidência
    assert fn.votar_chave([], "2609") is None
    outra = CHAVE.replace("000000029", "000000030")
    assert fn.votar_chave([CHAVE, outra], "2609") is None  # empate


def test_cnpj_por_sufixo():
    # 1 dígito faltando: completação única
    assert fn.completar_cnpj_por_sufixo("6065189000100") == ["46065189000100"]
    assert fn.resolver_cnpj_por_sufixo("6065189000100") == ("46065189000100", "checksum_unico")
    # 2 dígitos faltando: 3 completações (37/46/81...) -> sem identidade confirmada, nada é escolhido
    assert len(fn.completar_cnpj_por_sufixo("065189000100")) == 3
    assert fn.resolver_cnpj_por_sufixo("065189000100") == (None, None)
    # 3 dígitos faltando: 8 completações válidas
    assert len(fn.completar_cnpj_por_sufixo("04636000119")) == 8
    assert fn.resolver_cnpj_por_sufixo("04636000119", "RAVIMANA PATRIMONIAL LTDA") == (
        "04904636000119", "contraparte_confirmada")
    assert fn.resolver_cnpj_por_sufixo("04636000119", "OUTRA LTDA") == (None, None)
    # sufixo com dígito errado: não é contraparte e não é única -> sentinela
    assert fn.resolver_cnpj_por_sufixo("04636000118", "RAVIMANA PATRIMONIAL LTDA") == (None, None)


def test_razao_so_e_corrigida_pelo_cnpj_confirmado():
    assert fn.corrigir_razao_confirmada("04904636000119", "TAVIMANA PATRIMONIAL LTDA") == "SARAVIMANA PATRIMONIAL LTDA"
    assert fn.corrigir_razao_confirmada("11111111000191", "TAVIMANA PATRIMONIAL LTDA") == "TAVIMANA PATRIMONIAL LTDA"


def test_logradouro_cortado():
    assert fn.logradouro_sem_fragmento_cortado("ida Getúlio Vargas") == ("Getúlio Vargas", True)
    assert fn.logradouro_sem_fragmento_cortado("4 BARÃO DO RIO BRANCO") == ("BARÃO DO RIO BRANCO", True)
    assert fn.logradouro_sem_fragmento_cortado("Avenida Getúlio Vargas") == ("Avenida Getúlio Vargas", False)
    assert fn.logradouro_sem_fragmento_cortado("RUA BARAO DO RIO BRANCO") == ("RUA BARAO DO RIO BRANCO", False)


def test_parse_endereco_prefixo():
    c = fn.parse_endereco_prefixo("BARÃO DO RIO BRANCO, 1517, EDIF PETROPOLIS SALA 204, Kalilândia")
    assert (c["logradouro"], c["numero"], c["complemento"], c["bairro"]) == (
        "BARÃO DO RIO BRANCO", "1517", "EDIF PETROPOLIS SALA 204", "Kalilândia")
    c = fn.parse_endereco_prefixo("ida Getúlio Vargas, 744 - PARQUE GETÚLIO VARGAS")
    assert (c["numero"], c["complemento"], c["bairro"]) == ("744", None, "PARQUE GETÚLIO VARGAS")
