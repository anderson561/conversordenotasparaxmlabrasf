# -*- coding: utf-8 -*-
r"""Layout NOVO: Fatura de Locação da NEO-TAGUS INDUSTRIAL LTDA (CNPJ raiz
61.092.565, Extrema/MG). Achado real: nota nº 5135 (controle "000005135/LOC")
-> CONDOMINIO EDIFICIO TK TOWER, R$1.190,34. Pedido do usuário: "corrigir a
extração do pdf em anexo, se não existir, criar um novo layout fatura de
locação-neo-tagus".

CAUSA-RAIZ: o documento caía em `LAYOUT_FATURA_LOCACAO_GENERICA`, que é
detectado SÓ pela frase "FATURA DE LOCAÇÃO" — e o título desta nota é "FATURA
DE LOCAÇÃO DE MAQUINAS/EQUIPAMENTOS". Mas os extratores daquela rota são
calibrados no template da LOC BAHIA, cujas âncoras NENHUMA existe aqui:

    LOC BAHIA (genérico)          NEO-TAGUS (esta nota)
    "LOCADORA" / "LOCATÁRIO"      "Razão Social:" / "Dados do Cliente:"
    "QTDE - DESCRIÇÃO"            "Item Produto Descrição Quantidade ..."
    "Cidade:" / "Estado:"         "CEP: 37646-354 - EXTREMA - MG"
    "NÚMERO:"                     "Nº do Controle: 000005135/LOC"
    "TOTAL: R$"                   "Total:" impresso ANTES dos números

Resultado no XML: valor 0,00, prestador e tomador vazios, e a discriminação
saindo "354 - EXTREMA - MG" — um pedaço do CEP do PRÓPRIO prestador, pescado
pelo regex de linha de item da LOC BAHIA, que casa o mesmo formato
"<números> - <TEXTO>".

O `<Numero>5135</Numero>` parecia certo, mas vinha do NOME DO ARQUIVO
("NOTA 5135.pdf") — copiando o PDF para outro nome, a nota saía `00000000`.
Coberto por teste dedicado abaixo.

Decisão: layout próprio, detectado pelo CNPJ RAIZ do emitente (casa qualquer
filial — esta nota é da 0022), posicionado ANTES do check genérico. Mesma
decisão já tomada para a ARMAC, e é o que o próprio comentário do layout
genérico prevê: "só cai aqui uma fatura de locação de locadora ainda não
catalogada".

Texto REAL extraído via pdfminer (`extract_text`), direto do PDF original."""
import os

import pytest

from src.extractors.pdf_extractor import (SPPdfExtractor, LAYOUT_NEOTAGUS_LOCACAO,
                                          LAYOUT_FATURA_LOCACAO_GENERICA)

MOCK_NEOTAGUS = (
    'FATURA DE LOCAÇÃO DE MAQUINAS/EQUIPAMENTOS\n'
    '\n'
    'Razão Social: \n'
    'CNPJ: \n'
    'Inscrição Estadual: \n'
    'Endereço: \n'
    'CEP: \n'
    'Fone: \n'
    '\n'
    'NEO-TAGUS INDUSTRIAL LTDA\n'
    '61.092.565/0022-65\n'
    '0629622930106\n'
    'Estrada da Represa, 917 (Rod. Fernão Dias KM933)\n'
    '37646-354 - EXTREMA - MG\n'
    '35-30263000   \n'
    '\n'
    'Nº do Controle: \n'
    'Emissão: \n'
    'Vencimento: \n'
    '\n'
    '000005135/LOC\n'
    '01/08/2026\n'
    '31/08/2026\n'
    '\n'
    'Dados do Cliente: CONDOMINIO EDIFICIO TK TOWER                                                    \n'
    'CNPJ/CPF: \n'
    'Inscr. Estadual: \n'
    'Endereço: \n'
    'CEP: \n'
    '\n'
    'AV PROFESSOR MAGALHAES NETO1856\n'
    '41810-012 - SALVADOR - BA\n'
    '\n'
    '07.834.816/0001-60\n'
    '\n'
    'Item\n'
    '\n'
    'Produto\n'
    '\n'
    'Descrição\n'
    '\n'
    'Quantidade\n'
    '\n'
    'Vl.Unitário\n'
    '\n'
    'Vl.Total\n'
    '\n'
    '01\n'
    '\n'
    'LO-A           \n'
    '\n'
    'LOCACAO (ACESSO)                                            \n'
    '\n'
    'Total: \n'
    '\n'
    '1\n'
    '\n'
    '1\n'
    '\n'
    '1.190,34\n'
    '\n'
    '1.190,34\n'
    '\n'
    '            1.190,34\n'
    '\n'
    'Descrição - Serviços prestados: LOCACAO (ACESSO) \n'
    '\n'
    'Obs: \n'
    '\n'
    'O presente documento substitui a Nota Fiscal de Serviços, conforme lei complementar 116 de 31/07/2003\n'
    '\n'
    'Página: 1\n'
    '\n'
    ''
)


def _parse(texto, monkeypatch):
    dummy = "tests/dummy_neotagus.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy, "wb") as f:
        f.write(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text",
                        lambda path: texto)
    try:
        ex = SPPdfExtractor(dummy)
        return ex, ex.parse()
    finally:
        os.remove(dummy)


def test_layout_dedicado_ganha_do_generico(monkeypatch):
    """A frase "FATURA DE LOCAÇÃO" está no título desta nota, então sem o
    layout próprio ela cai na rota genérica da LOC BAHIA."""
    ex, _ = _parse(MOCK_NEOTAGUS, monkeypatch)
    assert ex.layout == LAYOUT_NEOTAGUS_LOCACAO
    assert ex.layout != LAYOUT_FATURA_LOCACAO_GENERICA
    assert "FATURA DE LOCAÇÃO" in MOCK_NEOTAGUS


def test_deteccao_pela_raiz_do_cnpj_casa_outras_filiais(monkeypatch):
    """Detecção pelo CNPJ RAIZ (61.092.565), não pelo sufixo de filial — esta
    nota é da filial 0022, e outra filial da mesma empresa tem de rotear
    igual."""
    outra_filial = MOCK_NEOTAGUS.replace("61.092.565/0022-65", "61.092.565/0001-05")
    assert outra_filial != MOCK_NEOTAGUS
    ex, _ = _parse(outra_filial, monkeypatch)
    assert ex.layout == LAYOUT_NEOTAGUS_LOCACAO


def test_valor_da_fatura(monkeypatch):
    """R$1.190,34. O rótulo "Total:" é impresso ANTES dos números, então não há
    valor colado a ele para ancorar — o total geral é o último valor monetário
    antes da linha que fecha a tabela."""
    _, nfse = _parse(MOCK_NEOTAGUS, monkeypatch)
    assert nfse.valores.valor_servicos == pytest.approx(1190.34)
    assert nfse.valores.valor_liquido_nfse == pytest.approx(1190.34)


def test_locacao_de_bens_moveis_nao_gera_iss(monkeypatch):
    """Convenção de toda a família de faturas de locação deste projeto:
    base/alíquota/ISS zerados e item "0601". A própria nota declara substituir
    a NFS-e (LC 116/2003)."""
    _, nfse = _parse(MOCK_NEOTAGUS, monkeypatch)
    assert nfse.valores.base_calculo == pytest.approx(0.0)
    assert nfse.valores.aliquota == pytest.approx(0.0)
    assert nfse.valores.valor_iss == pytest.approx(0.0)
    assert "substitui a Nota Fiscal de Serviços" in MOCK_NEOTAGUS


def test_numero_vem_do_documento_e_nao_do_nome_do_arquivo(monkeypatch):
    """O defeito silencioso: `<Numero>5135</Numero>` parecia correto, mas vinha
    do nome do arquivo. O mock aqui é parseado a partir de "tests/dummy_neotagus.pdf",
    um nome sem nenhum dígito — se o número sair certo, saiu do documento."""
    _, nfse = _parse(MOCK_NEOTAGUS, monkeypatch)
    assert nfse.numero == "5135"
    assert "Nº do Controle:" in MOCK_NEOTAGUS
    assert "000005135/LOC" in MOCK_NEOTAGUS


def test_prestador_lido_por_indice(monkeypatch):
    """O pdfminer despeja "rótulos todos, depois valores todos" neste bloco:
    Razão Social | CNPJ | Inscrição Estadual | Endereço | CEP | Fone."""
    _, nfse = _parse(MOCK_NEOTAGUS, monkeypatch)
    p = nfse.prestador
    assert p.razao_social == "NEO-TAGUS INDUSTRIAL LTDA"
    assert p.cnpj_cpf == "61092565002265"
    assert p.endereco.logradouro == "Estrada da Represa"
    assert p.endereco.numero == "917"
    assert p.endereco.cep == "37646354"


def test_municipio_do_prestador_e_extrema_mg(monkeypatch):
    """Extrema/MG não está em `IBGEResolver.KNOWN_CITIES` — sem o código
    explícito (3125101, conferido contra o IBGE e contra a faixa de CEP
    37640-000/37649-999 impressa na nota) o município cairia no fallback
    silencioso de Salvador/BA. Isso desloca também `OrgaoGerador` e
    `MunicipioIncidencia`, ou seja, o município de incidência do ISS."""
    _, nfse = _parse(MOCK_NEOTAGUS, monkeypatch)
    assert nfse.prestador.endereco.codigo_municipio == "3125101"
    assert nfse.prestador.endereco.uf == "MG"
    assert nfse.prestador.endereco.codigo_municipio != "2927408"


def test_tomador_lido_por_forma_do_conteudo(monkeypatch):
    """No bloco do cliente os valores saem FORA da ordem dos rótulos (endereço
    e CEP vêm ANTES do CNPJ), então índice não serve — cada campo é achado pela
    forma. E o número sai COLADO no logradouro ("MAGALHAES NETO1856")."""
    _, nfse = _parse(MOCK_NEOTAGUS, monkeypatch)
    tom = nfse.tomador
    assert tom.razao_social == "CONDOMINIO EDIFICIO TK TOWER"
    assert tom.cnpj_cpf == "07834816000160"
    assert tom.endereco.logradouro == "AV PROFESSOR MAGALHAES NETO"
    assert tom.endereco.numero == "1856"
    assert tom.endereco.codigo_municipio == "2927408"
    assert tom.endereco.uf == "BA"
    assert "MAGALHAES NETO1856" in MOCK_NEOTAGUS


def test_as_duas_entidades_sao_distintas(monkeypatch):
    _, nfse = _parse(MOCK_NEOTAGUS, monkeypatch)
    assert nfse.prestador.cnpj_cpf != nfse.tomador.cnpj_cpf
    assert nfse.prestador.endereco.codigo_municipio != nfse.tomador.endereco.codigo_municipio


def test_discriminacao_nao_e_pedaco_do_cep(monkeypatch):
    """Saía "354 - EXTREMA - MG", fragmento do CEP do prestador
    ("37646-354 - EXTREMA - MG") pescado pelo regex de item da LOC BAHIA."""
    _, nfse = _parse(MOCK_NEOTAGUS, monkeypatch)
    assert nfse.discriminacao == "LOCACAO (ACESSO)"
    assert "EXTREMA" not in nfse.discriminacao


def test_data_de_emissao(monkeypatch):
    _, nfse = _parse(MOCK_NEOTAGUS, monkeypatch)
    assert nfse.data_emissao.strftime("%d/%m/%Y") == "01/08/2026"


def test_xml_final(monkeypatch):
    """Fecha o ciclo no artefato que a Domínio consome."""
    from src.transformers.abrasf_transformer import Abrasf201Transformer
    import xml.etree.ElementTree as ET

    _, nfse = _parse(MOCK_NEOTAGUS, monkeypatch)
    xml = Abrasf201Transformer().transform(nfse)
    if not isinstance(xml, str):
        xml = ET.tostring(xml, encoding="unicode")
    assert "<ValorServicos>1190.34</ValorServicos>" in xml
    assert "<Numero>5135</Numero>" in xml
    assert "<ItemListaServico>0601</ItemListaServico>" in xml
    assert "<CodigoVerificacao>FATURA</CodigoVerificacao>" in xml
    assert "<CodigoMunicipio>3125101</CodigoMunicipio>" in xml
    assert "NEO-TAGUS INDUSTRIAL LTDA" in xml
    assert "CONDOMINIO EDIFICIO TK TOWER" in xml
