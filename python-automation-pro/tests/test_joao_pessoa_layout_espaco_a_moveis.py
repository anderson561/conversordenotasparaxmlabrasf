# -*- coding: utf-8 -*-
r"""Novo layout: João Pessoa/PB (`joao_pessoa_pb`), NFS-e oficial da
Secretaria da Receita Municipal ("Nota Fiscal de Serviços Eletrônica NFSe -
Prestador"), PDF ESCANEADO (OCR).

Nota real nº 1001671 (ESPACO A COMERCIO DE MOVEIS LTDA, João Pessoa/PB ->
NAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVIÇOS - EIRELI, Salvador/BA,
R$ 9.864,92), página 5 de "Scan2026-09-23_090227.pdf". Antes deste layout a
página não tinha NENHUM layout reconhecido (caía em LAYOUT_GENERICO e era
descartada como página sem nota), e a conversão da página inteira falhava
com "ValueError: Nenhuma nota encontrada nas páginas selecionadas.".

Mesma grade "rótulos numa linha, valores na seguinte, vários campos por
linha" do LAYOUT_CAMPINAS (inclusive a MESMA grade "CÁLCULO DO ISSQN" /
"VALOR TOTAL", reaproveitada tal e qual em `_extrair_valores` via
`self.layout in (LAYOUT_CAMPINAS, LAYOUT_JOAO_PESSOA)`), mas com quirks de
OCR próprios desta nota, todos exercitados pelos testes abaixo:

  1. O separador "/" do cabeçalho "CPF / CNPJ / NIF" do PRESTADOR sai como
     "!" ("CPF! CNPJ/NIF") — o cabeçalho do TOMADOR sai limpo ("CPF/CNPJ/
     NIF"), então o mesmo texto exercita as 2 variantes.
  2. O "@" do e-mail do prestador sai colado como "(" + 1 letra maiúscula
     solta ("escritorio(Despacoamoveis.com.br" em vez de "escritorio@
     espacoamoveis.com.br").
  3. O endereço do prestador quebra em 2 linhas físicas de valor
     ("AVENIDA ... TAMBAUZINHO" numa linha, "JOAO PESSOA ! PB BRASIL
     58042-006" na seguinte, com "!" no lugar da barra município/UF) — o
     do tomador sai numa linha só, com barra limpa.
  4. O e-mail vazio do tomador ("-") sai como ruído solto colado ao fim da
     razão social ("...SERVIÇOS - EIRELI Gê") — não pode contaminar nem a
     razão social nem virar um e-mail fabricado.
  5. O item da LC116 ("14.06") sai como "1408\"" (sem ponto decimal) na
     leitura de página inteira — recuperado por um recorte dedicado
     (`_ocr_recut_item_lc116_joao_pessoa`), aqui simulado prependendo ao
     texto a linha sintética que ele produz de fato contra a imagem real
     (zoom 6x, PSM 7): "| 14.06 - INSTALAÇÃO E MONTAGEM DE APARELHOS,
     MAQUINAS E EQUIPAMENTOS, INCLUSIVE MONTAGEM It".

Texto REAL extraído via OCR (Tesseract, zoom 3x) do PDF original - nunca
digitado à mão.
"""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
import src.extractors.pdf_extractor as pdf_extractor_mod

# Linha sintética que `_ocr_recut_item_lc116_joao_pessoa` produz de fato
# contra a imagem real (zoom 6x, PSM 7) - ver achado nº 5 do docstring.
RECUT_ITEM_LC116 = (
    "| 14.06 - INSTALAÇÃO E MONTAGEM DE APARELHOS, MAQUINAS E EQUIPAMENTOS, "
    "INCLUSIVE MONTAGEM It\n"
)

PAGE_TEXT = """Prefeitura Municipal de João Pessoa
Secretaria da Receita Municipal

Nota Fiscal de Serviços Eletrônica
IS TREPIDA o NFSe - Prestador

DADOS DA NFSe A autenticidade desta NFSe pode ser

verificada pela leitura deste código QR.

Data e hora de emissão Competência Número
14/08/2026 15:27:19 08/2026 1001671
Código de Verificação

2yYFiBlcd

EMITENTE PRESTADOR DO SERVIÇO

CPF! CNPJ/NIF Inscrição Municipal Telefone
03.942.564/0001-31 0000816469 (83) 3022-3023
Nome / Nome Empresarial E-mail

ESPACO A COMERCIO DE MOVEIS LTDA escritorio(Despacoamoveis.com.br

Endereço Município CEP

AVENIDA PRESIDENTE EPITACIO PESSOA 3000 TAMBAUZINHO

JOAO PESSOA ! PB BRASIL 58042-006

a a rsrsrsrsrs

TOMADOR DO SERVIÇO

CPF/CNPJ/NIF Inscrição Municipal Telefone
16.699.869/0001-06 - -

Nome / Nome Empresarial E-mail

NAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVIÇOS - EIRELI Gê

Endereço Município CEP

RUA RUA ARTHUR DE AZEVEDO MACHADO 1250 SALA 303 EDF YASMIM COSTA AZUL

SALVADOR / BA BRASIL 41760-000

rrrrreerrrerrrrrrrrrrrrrrrrerrrrrrrrrrrrerrrerrrrrrrrrrrerrrrrrrrrrrrrrrrrrrrrrrrrrrrrmeerrremmrmmrmemmmememmemmm

SERVIÇO PRESTADO

CNAE / CBO

3329-5/01-02 - SERVICOS DE MONTAGEM DE MOVEIS DE QUALQUER MATERIAL - INSTALACAO E MONTAGEM DE APARELHOS, MAQUINAS E EQUIPAMENTOS,
Servi

1408" INSTALAÇÃO E MONTAGEM DE APARELHOS, MAQUINAS E EQUIPAMENTOS, INCLUSIVE MONTAGEM INDUSTRIAL, PRESTADOS AO USUARIO FINAL,
Local da prestação do serviço País da prestação do serviço

JOAO PESSOA / PB BRASIL

DESCRIÇÃO DO SERVIÇO PRESTADO

SERVIÇO DE MONTAGEM E MANUTENÇÃO EM MOVEIS

Fathd

8
TIO 10 efto AO

TRIBUTAÇÃO MUNICIPAL

Exigibilidade do ISSQN Municipio da Incidência do ISSQN Responsável pelo recolhimento do ISSQN
Exigivel JOAO PESSOA - PB PRESTADOR DO SERVIÇO

Retenção do ISSQN Situação do prestador do serviço perante o Simples Nacional Regime especial de tributação do ISSQN
NÃO RETIDO NÃO OPTANTE -

CÁLCULO DO ISSQN
Valor total da NF Se (R$) Total das deduções (R$) Desc. incondiclonado (R$) Base de cálculo do ISSQN (R$) Aliq. (%) Valor do ISSQN (R$)
R$ 9.864,92 R$ 0,00 R$ 0,00 R$9.864,92  5,000000 R$ 493,24

RETENÇÕES
ISSQN (R$) IRRF (R$) PIS (R$) COFINS (R$) INSS (R$) CSLL (R$) Outras retenções (R$)
R$ 0,00 R$ 0,00 R$ 0,00 R$ 0,00 R$ 0,00 R$ 0,00 R$ 0,00

VALOR TOTAL
Base de cálculo do ISSQN (R$) Retenções (R$) Desc. incondicionado (R$) Desc. condicionado (R$) Valor Líquido da NF Se (R$)
R$ 9.864,92 R$ 0,00 R$ 0,00 R$ 0,00 R$ 9.864,92

INFORMAÇÕES COMPLEMENTARES
"""

MOCK_TEXT = RECUT_ITEM_LC116 + PAGE_TEXT


def _run(monkeypatch):
    dummy_path = "tests/dummy_joao_pessoa.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr(pdf_extractor_mod, "extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        return nfse_list
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_joao_pessoa_detectado_e_dados_da_nfse(monkeypatch):
    """Blindagem principal: antes deste layout a página caía em
    LAYOUT_GENERICO e era descartada - a conversão da página 5 real falhava
    com 'Nenhuma nota encontrada'."""
    nfse_list = _run(monkeypatch)
    assert len(nfse_list) == 1
    nfse = nfse_list[0]

    assert nfse.numero == "1001671"
    assert nfse.codigo_verificacao == "2yYFiBlcd"
    assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "14/08/2026 15:27:19"
    assert nfse.competencia.strftime("%m/%Y") == "08/2026"
    assert nfse.discriminacao == "SERVIÇO DE MONTAGEM E MANUTENÇÃO EM MOVEIS"
    assert nfse.servico_codigo == "1406"
    assert nfse.codigo_cnae == "3329501"
    assert nfse.avisos == []


def test_joao_pessoa_extrai_prestador_e_tomador(monkeypatch):
    """Prestador: separador '!' no cabeçalho CPF/CNPJ, '@' do e-mail
    corrompido em '(' + letra maiúscula solta, endereço quebrado em 2
    linhas físicas. Tomador: e-mail vazio ('-') não pode virar ruído colado
    à razão social nem um e-mail fabricado."""
    nfse_list = _run(monkeypatch)
    nfse = nfse_list[0]

    p = nfse.prestador
    assert p.cnpj_cpf == "03942564000131"
    assert p.inscricao_municipal == "0000816469"
    assert p.razao_social == "ESPACO A COMERCIO DE MOVEIS LTDA"
    assert p.email == "escritorio@espacoamoveis.com.br"
    assert p.telefone == "8330223023"
    assert p.endereco.logradouro == "AVENIDA PRESIDENTE EPITACIO PESSOA"
    assert p.endereco.numero == "3000"
    assert p.endereco.bairro == "TAMBAUZINHO"
    assert p.endereco.municipio == "JOAO PESSOA"
    assert p.endereco.uf == "PB"
    assert p.endereco.cep == "58042006"
    assert p.endereco.codigo_municipio == "2507507"

    t = nfse.tomador
    assert t.cnpj_cpf == "16699869000106"
    assert t.razao_social == "NAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVIÇOS - EIRELI"
    assert t.email is None
    assert t.endereco.logradouro == "RUA ARTHUR DE AZEVEDO MACHADO"
    assert t.endereco.numero == "1250"
    assert t.endereco.municipio == "SALVADOR"
    assert t.endereco.uf == "BA"
    assert t.endereco.cep == "41760000"
    assert t.endereco.codigo_municipio == "2927408"

    assert nfse.intermediario is None


def test_joao_pessoa_extrai_valores(monkeypatch):
    """Grade 'CÁLCULO DO ISSQN' / 'VALOR TOTAL', idêntica à do Campinas
    reaproveitada por `self.layout in (LAYOUT_CAMPINAS, LAYOUT_JOAO_PESSOA)`
    - inclui a Alíquota impressa com 6 casas decimais ('5,000000')."""
    nfse_list = _run(monkeypatch)
    v = nfse_list[0].valores

    assert v.valor_servicos == pytest.approx(9864.92)
    assert v.base_calculo == pytest.approx(9864.92)
    assert v.aliquota == pytest.approx(0.05)
    assert v.valor_iss == pytest.approx(493.24)
    assert v.valor_liquido_nfse == pytest.approx(9864.92)
    assert v.valor_deducoes == pytest.approx(0.0)
    assert v.desconto_incondicionado == pytest.approx(0.0)
