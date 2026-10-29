# -*- coding: utf-8 -*-
r"""Novo layout: impresso "Fatura de Locação" de equipamentos
(`fatura_locacao_equipamentos`), achado real 2026-10-28
(`LOCACAO DE BANHEIRO QUIMICO - 16 DE JULHO.pdf`, 1 página só imagem): IVAN
BARBOZA CORREA (CNPJ 30.226.394/0001-61, logo S&C, Bragança Paulista/SP) ->
H. Z. PATRIMONIAL LTDA. (CNPJ 10.791.569/0001-76, Lauro de Freitas/BA), fatura
15827, banheiro químico, R$ 2.250,00, vencimento 16/07/2026, contrato 91.

Antes deste layout a página caía em LAYOUT_FATURA_LOCACAO_GENERICA (só pela
frase "FATURA DE LOCAÇÃO", calibrado na LOC BAHIA) e o XML saía com prestador
00000000000000 "Prestador Não Identificado", tomador com o CNPJ do PRESTADOR,
valor 0,00 e endereços em Salvador.

`MOCK_FATURA` é o texto REAL que o `_ocr_page` entrega (Tesseract zoom 3),
verbatim: as linhas sintéticas `FATLOC_*` dos recortes célula a célula seguidas
do texto de página inteira, com os quirks que travam regressões:
  - a grade "Fatura | Valor | Vencimento" some da página inteira ("EE E
    TeIo7i2024") - só o recorte (FATLOC_FATURA) a recupera;
  - Dias/Quantidade do item não aparecem na página inteira;
  - "DOM PEDRO I"/"EMPRESARIAL I" saem "DOM PEDRO |"/"EMPRESARIAL |";
  - o recorte lê "H.Z." e a página inteira "H. Z." (impresso: "H. Z.");
  - CFOP 5949 e nº 15827 (caixas da direita) colados ao fim do endereço do
    prestador;
  - "frete 180,00" e o "Endereço de Entrega" em Extrema/MG nos Dados
    Adicionais não são valor nem endereço de nenhuma das partes.
"""
import pytest

from src.extractors import fatura_locacao_equipamentos as fl
from src.extractors.pdf_extractor import (
    LAYOUT_FATURA_LOCACAO_EQUIPAMENTOS, LAYOUT_FATURA_LOCACAO_GENERICA, SPPdfExtractor, _ibge_resolver,
)
from src.transformers.abrasf_transformer import Abrasf201Transformer

MOCK_FATURA = 'FATLOC_DEST_NOME: H.Z. PATRIMONIAL LTDA.\nFATLOC_DEST_CNPJ: 10.791.569/0001-76\nFATLOC_DEST_DATA: 15/07/2026\nFATLOC_DEST_ENDERECO: AV LUIZ TARQUINIO PONTES, 2580- SL 311 EDF VILLAS EMPRESARIAL |\nFATLOC_DEST_BAIRRO: BURAQUINHO\nFATLOC_DEST_CEP: 42700-130\nFATLOC_DEST_CIDADE: LAURO DE FREITAS / BA\nFATLOC_DEST_TELEFONE: (71)31839000\nFATLOC_DEST_IE: ISENTO\nFATLOC_DEST_CONTRATO: 91\nFATLOC_FATURA: 15827 ;; 2.250,00 ;; 16/07/2026\nFATLOC_ITEM: PRODUTO=49 ;; DESCRICAO=BANHEIRO QUÍMICO STANDARD C/ PORTA PAPEL E ASSENTO 85 KG ;; SERIE=B123 ;; PERIODO=15/07/2026 a 13/10/2026 ;; DIAS=90 ;; QUANTIDADE=1 ;; VALOR=2.250,00\n\nIVAN BARBOZA CORREA\nCNPJ: 30.226.394/0001-61 IE: 225298079117 Natureza de Operação: | Fatura de Locação:\n\nAVENIDA DOM PEDRO |, 1395- CXPST 1 - TABOAO - BRAGANCA PAULISTA 5949 15827\n/SP-CEP 12914-481\n\nDestinatário / Remetente\n\nNome/Razão Social CPF/CNPJ Data Emissão\nH. Z. PATRIMONIAL LTDA. 10.791.569/0001-76 | 15/07/2026\nEndereço Bairro Cep\n\nAV LUIZ TARQUINIO PONTES, 2580- SL 311 EDF VILLAS EMPRESARIAL | BURAQUINHO | 42700-130 CONTRATO\nCidade Tel./Fax Inscrição Estadual 91\nLAURO DE FREITAS / BA (71)31839000 | ISENTO\n\nEE E TeIo7i2024\n\nNúmero de\n\nSéri Período de Locação Dias Quantidade Valor\nerie\n\nProduto Descrição\n\nBANHEIRO QUÍMICO STANDARD C/ PORTA PAPEL E B123 15/07/2026 a\n\nASSENTO 85 KG 13/10/2026 2.250,00\n\n49\n\nTaxa Entrega/Retirada 0,00\n\nTotal Locação 2.250,00\n\nNão incidência de ISS Conforme item 3.01 da Lei Complementar 116 de 21/07/2003\n\nDados Adicionais\n\nsolicitado por alexandre palma frete 180,00 limp. 1x na semana\n\nEndereço de Entrega: - RUA JOAO BATISTA CARDOSO, S/N - TENENTES - EXTREMA/MG CEP: 37645-008\n\nRecebi(emos) de IVAN BARBOZA CORREA, OS BENS MÓVEIS EM LOCAÇÃO, CONSTANTES DESTA FATURA DE\nLOCAÇÃO INDICADA ACIMA. FATURA DE\n\nLOCAÇÃO\nData do Recebimento. Identificação e assinatura do recebedor. Nº 15827\n/. /\n\n'

MOCK_SEM_RECORTES = fl.sem_marcadores(MOCK_FATURA)

# Células REAIS lidas pelo recorte do bloco Destinatário: (linha da grade, x0,
# x1, linhas do OCR PSM 6). A célula "CONTRATO" é mesclada nas 2 linhas de
# baixo: o rótulo cai numa faixa e o "91" na seguinte, sem rótulo.
CELULAS_DESTINATARIO = [
    (0, 94, 1275, ['Nome/Razão Social', 'H.Z. PATRIMONIAL LTDA.']),
    (0, 1288, 1525, ['CPF/CNPJ', '10.791.569/0001-76']),
    (0, 1537, 1694, ['Data Emissão', '15/07/2026']),
    (1, 94, 1084, ['Endereço', 'AV LUIZ TARQUINIO PONTES, 2580- SL 311 EDF VILLAS EMPRESARIAL |']),
    (1, 1096, 1275, ['Bairro', 'BURAQUINHO']),
    (1, 1288, 1525, ['Cep', '42700-130']),
    (1, 1537, 1694, ['CONTRATO']),
    (2, 94, 1084, ['Cidade', 'LAURO DE FREITAS / BA']),
    (2, 1096, 1275, ['Tel./Fax', '(71)31839000']),
    (2, 1288, 1525, ['Inscrição Estadual', 'ISENTO']),
    (2, 1537, 1694, ['91']),
]


def _converter(monkeypatch, tmp_path, texto, nome="fatura.pdf"):
    pdf = tmp_path / nome
    pdf.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: texto)
    return SPPdfExtractor(str(pdf)).parse_multiple()


def _uma_nota(monkeypatch, tmp_path, texto):
    notas = _converter(monkeypatch, tmp_path, texto)
    assert len(notas) == 1
    return notas[0]


def _extrair(texto):
    ex = SPPdfExtractor.__new__(SPPdfExtractor)
    return fl.extrair(texto, _ibge_resolver, lambda d: SPPdfExtractor._validate_cnpj_cpf(ex, d))


def _ex(tmp_path, texto):
    pdf = tmp_path / "f.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    ex = SPPdfExtractor(str(pdf))
    ex.raw_text = texto
    return ex


# ---------------------------------------------------------------------------
# Detecção
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("texto", [MOCK_FATURA, MOCK_SEM_RECORTES])
def test_detecta_nos_dois_detectores(tmp_path, texto):
    ex = _ex(tmp_path, texto)
    assert ex._detect_layout() == LAYOUT_FATURA_LOCACAO_EQUIPAMENTOS
    assert ex._detect_layout_page(texto) == LAYOUT_FATURA_LOCACAO_EQUIPAMENTOS


def test_sem_as_caixas_do_cabecalho_volta_ao_generico(tmp_path):
    """Âncora do bug: sem a caixa "Natureza de Operação" o texto não é deste
    layout e cai, como antes, no genérico (só pela frase "FATURA DE LOCAÇÃO")."""
    texto = MOCK_SEM_RECORTES.replace('Natureza de Operação:', '')
    assert not fl.eh_fatura_locacao(texto)
    assert _ex(tmp_path, texto)._detect_layout() == LAYOUT_FATURA_LOCACAO_GENERICA


@pytest.mark.parametrize("trecho, troca", [
    ('Fatura de Locação:', 'Fatura:'),                          # caixa do número
    ('Destinatário / Remetente', 'Cliente'),                     # bloco do destinatário
    ('Total Locação 2.250,00', 'Total 2.250,00'),                # grade de itens
])
def test_falta_de_ancora_estrutural_nao_detecta(trecho, troca):
    texto = MOCK_SEM_RECORTES.replace(trecho, troca)
    if trecho.startswith('Total'):
        texto = texto.replace('Período de Locação', 'Período')
    assert not fl.eh_fatura_locacao(texto)


@pytest.mark.parametrize("prefixo", ["NFS-e - Nota Fiscal de Serviços Eletrônica\n", "DANFE\n"])
def test_documento_fiscal_nao_vira_este_layout(prefixo):
    assert not fl.eh_fatura_locacao(prefixo + MOCK_SEM_RECORTES)


# ---------------------------------------------------------------------------
# Fatura real completa
# ---------------------------------------------------------------------------

def test_campos_da_fatura_15827(monkeypatch, tmp_path):
    nf = _uma_nota(monkeypatch, tmp_path, MOCK_FATURA)
    assert nf.numero == "15827"
    assert nf.codigo_verificacao == "FATURA"
    assert nf.data_emissao.strftime('%Y-%m-%dT%H:%M:%S') == "2026-07-15T00:00:00"
    # Competência = mês da EMISSÃO (decisão do usuário); o período 15/07 a
    # 13/10/2026 é o do aluguel.
    assert nf.competencia.strftime('%Y-%m-%d') == "2026-07-01"

    p = nf.prestador
    assert p.cnpj_cpf == "30226394000161"
    assert p.razao_social == "IVAN BARBOZA CORREA"
    assert p.endereco.logradouro == "AVENIDA DOM PEDRO I"
    assert p.endereco.numero == "1395"
    assert p.endereco.complemento == "CXPST 1"
    assert p.endereco.bairro == "TABOAO"
    assert p.endereco.municipio == "BRAGANCA PAULISTA"
    assert p.endereco.codigo_municipio == "3507605"  # Bragança Paulista/SP (API IBGE)
    assert p.endereco.uf == "SP"
    assert p.endereco.cep == "12914481"

    t = nf.tomador
    assert t.cnpj_cpf == "10791569000176"
    assert t.razao_social == "H. Z. PATRIMONIAL LTDA."
    assert t.endereco.logradouro == "AV LUIZ TARQUINIO PONTES"
    assert t.endereco.numero == "2580"
    assert t.endereco.complemento == "SL 311 EDF VILLAS EMPRESARIAL I"
    assert t.endereco.bairro == "BURAQUINHO"
    assert t.endereco.codigo_municipio == "2919207"  # Lauro de Freitas/BA
    assert t.endereco.uf == "BA"
    assert t.endereco.cep == "42700130"
    assert t.telefone == "7131839000"
    # O endereço de entrega (Extrema/MG) não vaza para nenhuma das partes.
    assert "EXTREMA" not in (p.endereco.municipio or '') + (t.endereco.municipio or '')

    v = nf.valores
    assert v.valor_servicos == pytest.approx(2250.00)  # "frete 180,00" NÃO soma
    assert v.valor_liquido_nfse == pytest.approx(2250.00)
    assert v.base_calculo == 0.0 and v.aliquota == 0.0 and v.valor_iss == 0.0
    assert v.iss_retido is False

    assert nf.servico_codigo == "0601"
    assert nf.optante_simples_nacional is False
    assert nf.discriminacao == (
        "49 - BANHEIRO QUÍMICO STANDARD C/ PORTA PAPEL E ASSENTO 85 KG - Série B123 - "
        "Período de locação 15/07/2026 a 13/10/2026 (90 dias) - Qtd 1 - Valor 2.250,00 | "
        "Taxa Entrega/Retirada 0,00 | Total Locação 2.250,00 | "
        "Fatura de Locação 15827 - Contrato 91 - Vencimento 16/07/2026 | "
        "Não incidência de ISS Conforme item 3.01 da Lei Complementar 116 de 21/07/2003 | "
        "Dados adicionais: solicitado por alexandre palma frete 180,00 limp. 1x na semana; "
        "Endereço de Entrega: - RUA JOAO BATISTA CARDOSO, S/N - TENENTES - EXTREMA/MG CEP: 37645-008")
    assert any("FATURA DE LOCAÇÃO" in a and "não é NFS-e" in a for a in nf.avisos)
    assert any("item 3.01" in a and "0601" in a for a in nf.avisos)
    assert any("Endereço de Entrega" in a for a in nf.avisos)
    assert any("frete" in a for a in nf.avisos)
    assert not any("não identificados" in a for a in nf.avisos)
    assert not any("diverge" in a for a in nf.avisos)


def test_xml_final_da_fatura_15827(monkeypatch, tmp_path):
    xml = Abrasf201Transformer().transform(_uma_nota(monkeypatch, tmp_path, MOCK_FATURA))
    for trecho in (
        "<Numero>15827</Numero>", "<CodigoVerificacao>FATURA</CodigoVerificacao>",
        "<DataEmissao>2026-07-15T00:00:00</DataEmissao>", "<Competencia>2026-07-01</Competencia>",
        "<ValorServicos>2250.00</ValorServicos>", "<ValorLiquidoNfse>2250.00</ValorLiquidoNfse>",
        "<ValorIss>0.00</ValorIss>", "<Aliquota>0.00</Aliquota>", "<IssRetido>2</IssRetido>",
        "<ItemListaServico>0601</ItemListaServico>", "<CodigoTributacaoMunicipio>0601</CodigoTributacaoMunicipio>",
        "<Cnpj>30226394000161</Cnpj>", "<RazaoSocial>IVAN BARBOZA CORREA</RazaoSocial>",
        "<Cnpj>10791569000176</Cnpj>", "<RazaoSocial>H. Z. PATRIMONIAL LTDA.</RazaoSocial>",
        "<Cep>12914481</Cep>", "<Cep>42700130</Cep>", "<Bairro>BURAQUINHO</Bairro>",
        "<CodigoMunicipio>2919207</CodigoMunicipio>",
        # Incidência no município do prestador (mesma regra de Localiza/ELEVAR).
        "<MunicipioIncidencia>3507605</MunicipioIncidencia>",
    ):
        assert trecho in xml, trecho
    assert "<Intermediario>" not in xml
    assert "2927408" not in xml  # nada caiu no default Salvador
    assert xml.count("30226394000161") == 2  # só prestador (InfNfse + Declaração), nunca o tomador


# ---------------------------------------------------------------------------
# Sem recortes (PDF digital / recorte falhou) e integridade fiscal
# ---------------------------------------------------------------------------

def test_sem_recortes_usa_pagina_inteira_e_avisa(monkeypatch, tmp_path):
    nf = _uma_nota(monkeypatch, tmp_path, MOCK_SEM_RECORTES)
    assert nf.numero == "15827"              # do canhoto "FATURA DE LOCAÇÃO Nº 15827"
    assert nf.data_emissao.strftime('%Y-%m-%d') == "2026-07-15"
    assert nf.valores.valor_servicos == pytest.approx(2250.00)
    assert nf.prestador.cnpj_cpf == "30226394000161"
    t = nf.tomador
    assert t.cnpj_cpf == "10791569000176"
    assert t.razao_social == "H. Z. PATRIMONIAL LTDA."
    assert t.endereco.bairro == "BURAQUINHO"
    assert t.endereco.cep == "42700130"
    assert t.endereco.codigo_municipio == "2919207"
    assert "Contrato 91" in nf.discriminacao
    assert "Vencimento" not in nf.discriminacao  # a grade da fatura só existe no recorte
    assert any("Itens da fatura" in a for a in nf.avisos)


def test_numero_divergente_entre_leituras_vira_sentinela():
    texto = MOCK_FATURA.replace('FATLOC_FATURA: 15827', 'FATLOC_FATURA: 15821')
    n = _extrair(texto)
    assert n.numero == "00000000"
    assert any("divergente" in a for a in n.avisos)


def test_total_divergente_da_grade_avisa_e_mantem_total_impresso():
    n = _extrair(MOCK_FATURA.replace(';; 2.250,00 ;; 16/07', ';; 2.350,00 ;; 16/07'))
    assert n.valores.valor_servicos == pytest.approx(2250.00)
    assert any("diverge" in a and "2350.00" in a for a in n.avisos)


def test_tomador_com_cnpj_do_prestador_vira_sentinela():
    """A família do bug original: o CNPJ do emitente nunca é aceito como tomador."""
    texto = MOCK_FATURA.replace('FATLOC_DEST_CNPJ: 10.791.569/0001-76', 'FATLOC_DEST_CNPJ: 30.226.394/0001-61')
    n = _extrair(texto)
    assert n.tomador.cnpj_cpf == "00000000000000"
    assert any("destinatário" in a for a in n.avisos)


def test_cnpj_do_emitente_com_dv_invalido_vira_sentinela():
    n = _extrair(MOCK_FATURA.replace('30.226.394/0001-61', '30.226.394/0001-67'))
    assert n.prestador.cnpj_cpf == "00000000000000"
    assert any("emitente" in a and "sentinela" in a for a in n.avisos)


# ---------------------------------------------------------------------------
# Funções puras dos recortes
# ---------------------------------------------------------------------------

def test_celulas_do_destinatario_com_contrato_mesclado():
    assert fl.celulas_destinatario(CELULAS_DESTINATARIO) == [
        'FATLOC_DEST_NOME: H.Z. PATRIMONIAL LTDA.',
        'FATLOC_DEST_CNPJ: 10.791.569/0001-76',
        'FATLOC_DEST_DATA: 15/07/2026',
        'FATLOC_DEST_ENDERECO: AV LUIZ TARQUINIO PONTES, 2580- SL 311 EDF VILLAS EMPRESARIAL |',
        'FATLOC_DEST_BAIRRO: BURAQUINHO',
        'FATLOC_DEST_CEP: 42700-130',
        'FATLOC_DEST_CIDADE: LAURO DE FREITAS / BA',
        'FATLOC_DEST_TELEFONE: (71)31839000',
        'FATLOC_DEST_IE: ISENTO',
        'FATLOC_DEST_CONTRATO: 91',
    ]


def test_celula_sem_rotulo_fora_do_contrato_e_descartada():
    celulas = [c for c in CELULAS_DESTINATARIO if c[3] != ['CONTRATO']]
    assert not any('CONTRATO' in linha for linha in fl.celulas_destinatario(celulas))


def test_linha_da_grade_da_fatura():
    # Leitura REAL do recorte (PSM 6), com o lixo da faixa de baixo.
    assert fl.linha_fatura('15827 2.250,00 16/07/2026\nNiimern de |') == '15827 ;; 2.250,00 ;; 16/07/2026'
    assert fl.linha_fatura('EE E TeIo7i2024') is None


def test_linha_de_item_e_leitura_de_volta():
    cab = ['PRODUTO', 'DESCRICAO', 'SERIE', 'PERIODO', 'DIAS', 'QUANTIDADE', 'VALOR']
    cel = ['49', 'BANHEIRO QUÍMICO STANDARD C/ PORTA PAPEL E ASSENTO 85 KG', 'B123',
           '15/07/2026 a 13/10/2026', '90', '1', '2.250,00']
    assert fl.ler_item(fl.linha_item(cab, cel)) == dict(zip(cab, cel))


@pytest.mark.parametrize("rotulo, chave", [
    ('Produto', 'PRODUTO'), ('Descrição', 'DESCRICAO'), ('Número de Série', 'SERIE'),
    ('Período de Locação', 'PERIODO'), ('Dias', 'DIAS'), ('Quantidade', 'QUANTIDADE'), ('Valor', 'VALOR'),
])
def test_cabecalho_da_grade_de_itens(rotulo, chave):
    assert fl.chave_coluna_item(rotulo) == chave


def test_agrupar_fios():
    assert fl.agrupar([3, 4, 5, 9, 10, 30]) == [(3, 5), (9, 10), (30, 30)]
