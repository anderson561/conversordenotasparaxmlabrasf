# -*- coding: utf-8 -*-
"""São Paulo/SP digital: UF do tomador "roubada" do prestador.

Achado real 2026-11-13, nota nº 08969996 (PLUXEE BENEFICIOS BRASIL S.A. ->
DELTALINE SERVICOS LTDA.): o tomador imprime "Município: Salvador  UF: BA",
mas o XML saía com <Uf>SP</Uf> (o código IBGE 2927408 já saía certo).

Causa raiz: na camada de texto (pdfminer) os rótulos do bloco do tomador vêm
soltos antes dos valores ("Município:", ..., "Salvador", "UF:", "BA") e o
"UF: SP" do PRESTADOR (cujo bloco só traz "Município: São Paulo") cai DEPOIS,
dentro do bloco do tomador. `_sp_ler_bloco_entidade` dava prioridade a
qualquer "UF: XX" na mesma linha. Agora, com mais de uma UF candidata no
bloco, vale a que bate com o município lido (quando conhecido); sem essa
prova, a ordem antiga decide (nada muda).

Texto = retorno REAL de `pdfminer.high_level.extract_text()` no PDF real
(o mesmo de `test_sao_paulo_pluxee_recebido_servico_zero`).
"""
import xml.etree.ElementTree as ET

from src.extractors.pdf_extractor import SPPdfExtractor
from src.transformers.abrasf_transformer import Abrasf201Transformer
from tests.test_sao_paulo_flash_valor_recebido import NOTA_FLASH_05710445
from tests.test_sao_paulo_pluxee_recebido_servico_zero import NOTA_PLUXEE_08969996, PAGINA_1


def _bloco_tomador(texto=PAGINA_1):
    ini = texto.index("TOMADOR DE SERVIÇOS") + len("TOMADOR DE SERVIÇOS")
    return texto[ini:texto.index("INTERMEDIÁRIO DE SERVIÇOS")]


def _extrator():
    return SPPdfExtractor.__new__(SPPdfExtractor)


def _uma(monkeypatch, tmp_path, texto):
    pdf = tmp_path / "nota.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: texto)
    notas = SPPdfExtractor(str(pdf)).parse_multiple()
    assert len(notas) == 1
    return notas[0]


def test_bloco_real_do_tomador_tem_as_duas_ufs():
    bloco = _bloco_tomador()
    assert "UF:\n\nBA" in bloco and "UF: SP" in bloco


def test_bloco_real_uf_do_municipio_prevalece():
    lido = _extrator()._sp_ler_bloco_entidade(_bloco_tomador())
    assert (lido["municipio"], lido["uf"]) == ("Salvador", "BA")


def test_sem_a_uf_do_proprio_bloco_mantem_ordem_antiga():
    # trecho trocado: some o "UF:/BA" do tomador - só sobra o "UF: SP"; sem
    # prova de outra UF no bloco, nada muda em relação ao comportamento antigo.
    bloco = _bloco_tomador().replace("UF:\n\nBA\n\n", "")
    lido = _extrator()._sp_ler_bloco_entidade(bloco)
    assert lido["uf"] == "SP"


def test_tomador_de_sao_paulo_continua_sp():
    # trecho trocado: tomador em São Paulo/SP
    bloco = _bloco_tomador().replace("Salvador\n", "São Paulo\n").replace("UF:\n\nBA", "UF:\n\nSP")
    lido = _extrator()._sp_ler_bloco_entidade(bloco)
    assert (lido["municipio"], lido["uf"]) == ("São Paulo", "SP")


def test_nota_real_tomador_ba_prestador_sp(monkeypatch, tmp_path):
    nota = _uma(monkeypatch, tmp_path, NOTA_PLUXEE_08969996)
    t, p = nota.tomador.endereco, nota.prestador.endereco
    assert (t.municipio, t.uf, t.codigo_municipio) == ("Salvador", "BA", "2927408")
    assert (p.municipio, p.uf, p.codigo_municipio) == ("São Paulo", "SP", "3550308")
    root = ET.fromstring(Abrasf201Transformer().transform(nota))
    assert root.find(".//Tomador/Endereco/Uf").text == "BA"
    assert root.find(".//Tomador/Endereco/CodigoMunicipio").text == "2927408"
    assert root.find(".//PrestadorServico/Endereco/Uf").text == "SP"


def test_flash_real_uf_inalterada(monkeypatch, tmp_path):
    # Flash nº 05710445: tomador TEMIS em Salvador/BA, prestador em São Paulo/SP
    nota = _uma(monkeypatch, tmp_path, NOTA_FLASH_05710445)
    assert nota.tomador.endereco.uf == "BA"
    assert nota.prestador.endereco.uf == "SP"
