# -*- coding: utf-8 -*-
r"""Novo layout: Ribeirão Preto/SP (`ribeirao_preto_sp`), PDF digital
(pdfminer, Portal Betha/GINFES-like).

Nota real nº 469 (Paschoalin Sociedade Individual de Advocacia -> UNIÃO
PARTICIPAÇÕES LTDA, R$ 4.500,00). Reportada pelo usuário como "número da
nota fiscal incorreto" (saía sentinela "00000000"). A causa raiz NÃO era de
extração, e sim de DETECÇÃO — a nota não tinha layout próprio, e o fallback
bare `if re.search('FEIRA DE SANTANA', t): return LAYOUT_FEIRA` (mesma
família de "marca da CONTRAPARTE, não do emitente, sequestra a nota" já
vista em `LAYOUT_SIMOES_FILHO`/STAUMMAQ) capturava a nota inteira porque o
TOMADOR é de Feira de Santana/BA — mesmo a nota sendo emitida pela
Prefeitura de Ribeirão Preto/SP, sem nenhuma relação com o layout Feira de
Santana. Sob o layout errado: Número da Nota e Código de Verificação saíam
sentinela, Data de Emissão perdia o horário (usava só "RPS: 261 - Data:
03/08/2026", não a "Data de emissão 03/08/2026 14:05" real), o Código de
Município de AMBAS as entidades caía no default Salvador/BA (nem Ribeirão
Preto nem Feira de Santana estavam em `KNOWN_CITIES`) e Alíquota/Valor do
ISS saíam zerados apesar de a nota imprimir claramente "R$ 90,00 (2,00%)".

A caixa "Número / Data de emissão / Código de verificação" (topo da
página) não aparece na leitura de página inteira além do rótulo "Número"
sozinho — recuperada por recorte dedicado
(`_ocr_header_box_ribeirao_preto`), que aqui é simulado prependendo ao
texto a linha sintética que ele produziria.

Endereço de prestador/tomador em 2 linhas ("<logradouro>, <número> -
[complemento -] <bairro>" e "<município> - <UF> - <CEP>"); o endereço do
prestador nesta nota tem um separador " - " DUPLICADO (sem complemento de
verdade) e o nome do próprio prestador ("PASCHOALIN") colado ao fim do
bairro sem separador — provavelmente um carimbo/marca d'água da própria
linha, removido por não ser parte legítima do nome do bairro.

Texto REAL extraído via OCR (Tesseract, zoom 3x) do PDF original -
nunca digitado à mão.
"""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
import src.extractors.pdf_extractor as pdf_extractor_mod

# Linha sintética que `_ocr_header_box_ribeirao_preto` produz de fato contra
# a imagem real (zoom 4x, PSM 6) - inclui um caractere de ruído solto ("E")
# colado a 2 dos 3 rótulos antes da quebra de linha ("Número E\n469",
# "emissão E\n..."), provavelmente borda/artefato do próprio recorte. Achado
# ao regenerar o XML real: a versão "limpa" (sem o "E") passava no teste mas
# a nota real continuava saindo com Número sentinela - os regexes de
# `_extrair_numero`/`_extrair_data_emissao` exigiam `\s*` puro entre rótulo
# e quebra de linha, sem tolerar esse ruído.
HEADER_RECUT = "e\nNúmero E\n469\nData de emissão E\n03/08/2026 14:05 EE\nCódigo de verificação\nF6730843C E\n"

PAGE_TEXT = """Número

Prefeitura de Ribeirão Preto o so .
NFS-e - Nota Fiscal ata de emissão
de Serviços Eletrônica CE e
RPS: 261 - Data: 03/08/2026 a

Prestador de Serviços

Razão Social: Paschoalin Sociedade Individual de Advocacia
CNPJ: 31.250.316/0001-65
Inscrição Municipal: 20111180
Avenida Presidente Vargas, 2001 - - sala 14 - Jardim Santa Ângela PASCHOALIN
Ribeirão Preto - SP - 14020-525
legalizacaoQribercontabilidade.com.br - (01) 03877-0022

Tomador dos Serviços

Razão Social: UNIÃO PARTICIPAÇÕES LTDA
CNPJ: 27.500.056/0001-61

Avenida Getúlio Vargas, 744 - 1o andar - Centro
Feira de Santana - BA - 44001-496

Serviços

—— o — pe
| Código CNAE | Item LC 116/2003 Cód. NBS | Atividade do Município
| 6911701 17.14 1.1301.20.00 | 171400 - 17.14.01 - Advocacia
| Descrição do Serviço
| Honorários

Município de Incidência | Município de Prestação do Serviço | Natureza da Operação

Ribeirão Preto - SP | Ribeirão Preto - SP Exigível

| Desconto Condicionado Desconto Incondicionado Deduções Base de Cálculo |
| R$ 0,00 j S 0,00
| PIS | COFINS | INSS | IRRF |
| R$ 0,00 | s 0, no | RS 0,00 l R$ 0,00
| RD ' l — ad re —
| CSLL ISS Retido Outras Retenções |
| R$ 0.00 Não | R$ 0,00

Valor Total dos Serviços | Total ISSQN (%) Valor Líquido da NFS-e

R$ 4.500,00 IE R$ 90,00 (2,00%) R$ 4.500,00

, am aaa na ES

|- "DOCUMENTO EMITIDO POR ME OU EPP OPTANTE PELO SIMPLES NACIONAL": e
Il - "NÃO GERA DIREITO A CRÉDITO FISCAL DE IPI."

"5 NOTARP
"""

MOCK_TEXT = HEADER_RECUT + PAGE_TEXT


def _run(monkeypatch):
    dummy_path = "tests/dummy_ribeirao_preto.pdf"
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


def test_ribeirao_preto_nao_e_sequestrada_por_feira_de_santana(monkeypatch):
    """Blindagem principal: o TOMADOR é de Feira de Santana/BA, mas a nota é
    emitida pela Prefeitura de Ribeirão Preto/SP. Antes deste fix, o
    fallback bare de detecção de Feira de Santana capturava a nota inteira
    (mesma família de bug já vista em LAYOUT_SIMOES_FILHO/STAUMMAQ)."""
    nfse_list = _run(monkeypatch)
    assert len(nfse_list) == 1
    nfse = nfse_list[0]

    # Sob o layout errado (Feira de Santana) estes 3 campos saíam sentinela
    # ou incompletos - a prova mais direta de que a detecção está correta.
    assert nfse.numero == "469"
    assert nfse.codigo_verificacao == "F6730843C"
    assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "03/08/2026 14:05:00"
    assert nfse.servico_codigo == "1714"
    assert nfse.discriminacao == "Honorários"


def test_ribeirao_preto_extrai_prestador_e_tomador(monkeypatch):
    """Prestador tem separador ' - ' duplicado (sem complemento real) e o
    próprio nome ('PASCHOALIN') colado ao fim do bairro - ambos os quirks
    precisam ser tratados sem contaminar bairro/complemento. Município de
    AMBAS as entidades caía no default Salvador/BA antes deste fix (nem
    Ribeirão Preto nem Feira de Santana estavam em KNOWN_CITIES)."""
    nfse_list = _run(monkeypatch)
    nfse = nfse_list[0]

    p = nfse.prestador
    assert p.cnpj_cpf == "31250316000165"
    assert p.inscricao_municipal == "20111180"
    assert p.razao_social == "Paschoalin Sociedade Individual de Advocacia"
    assert p.endereco.logradouro == "Avenida Presidente Vargas"
    assert p.endereco.numero == "2001"
    assert p.endereco.complemento == "sala 14"
    assert p.endereco.bairro == "Jardim Santa Ângela"
    assert p.endereco.municipio == "Ribeirão Preto"
    assert p.endereco.uf == "SP"
    assert p.endereco.cep == "14020525"
    assert p.endereco.codigo_municipio == "3543402"

    t = nfse.tomador
    assert t.cnpj_cpf == "27500056000161"
    assert t.razao_social == "UNIÃO PARTICIPAÇÕES LTDA"
    assert t.endereco.logradouro == "Avenida Getúlio Vargas"
    assert t.endereco.numero == "744"
    assert t.endereco.complemento == "1o andar"
    assert t.endereco.bairro == "Centro"
    assert t.endereco.municipio == "Feira de Santana"
    assert t.endereco.uf == "BA"
    assert t.endereco.cep == "44001496"
    assert t.endereco.codigo_municipio == "2910800"

    assert nfse.intermediario is None


def test_ribeirao_preto_extrai_valores(monkeypatch):
    """A grade 'Valor Total dos Serviços | Total ISSQN (%) | Valor Líquido
    da NFS-e' saía com Alíquota e Valor do ISS zerados sob o layout errado,
    apesar de a nota imprimir claramente 'R$ 90,00 (2,00%)'."""
    nfse_list = _run(monkeypatch)
    v = nfse_list[0].valores

    assert v.valor_servicos == pytest.approx(4500.0)
    assert v.base_calculo == pytest.approx(4500.0)
    assert v.aliquota == pytest.approx(0.02)
    assert v.valor_iss == pytest.approx(90.0)
    assert v.iss_retido is False
    assert v.valor_iss_retido == pytest.approx(0.0)
    assert v.valor_liquido_nfse == pytest.approx(4500.0)

    assert nfse_list[0].avisos == []
