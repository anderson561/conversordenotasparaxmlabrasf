# -*- coding: utf-8 -*-
"""Nome e pasta dos XMLs gerados pela GUI — prefixo SEMPRE o nome do PDF original.

Achado real 2026-10-27: "MAPA CONSULTORIA - 12.pdf" (1 página) convertido pela
GUI gerou `temp_Pagina_1_NF_12.xml`. Causa: o fluxo de ARQUIVO ÚNICO da GUI
passava a `run_conversion` o caminho fixo `<pasta de saída>/temp.xml`, e
`run_conversion` usa o nome desse caminho como prefixo. Defeito pré-existente
em main (não introduzido pela seleção com vários PDFs). Os fluxos de lote
(vários PDFs, com ou sem seleção) já usavam o nome original (`nome_xml_lote`).

Cobre cada caminho da GUI sem Flet: 1 PDF de 1 página, 1 PDF multipágina com
seleção, PDF protegido (lido de cópia temporária com outro nome), vários PDFs
com e sem seleção (inclusive protegido).
"""
import contextlib
import glob
import os
import shutil

import pytest

import src.main as main
from src.gui_selecao import caminho_xml_arquivo_unico, nome_xml_lote
from src.main import run_batch_conversion, run_conversion
from tests.test_selecao_paginas import _mk_nfse

NOME_REAL = "MAPA CONSULTORIA - 12.pdf"


def _pdf_dummy(pasta, nome):
    os.makedirs(pasta, exist_ok=True)
    p = os.path.join(str(pasta), nome)
    with open(p, "wb") as f:
        f.write(b"%PDF-1.4 dummy")
    return p


def _xmls(out_dir):
    return sorted(os.path.basename(f) for f in glob.glob(os.path.join(str(out_dir), "*.xml")))


def _fake_parse(monkeypatch, notas_por_nome):
    """parse_multiple devolve as notas pelo nome do arquivo LIDO (que, para PDF
    protegido, é o da cópia temporária — por isso a chave pode ser o temp)."""
    def parse_multiple(self):
        return list(notas_por_nome[os.path.basename(self.pdf_path)])
    monkeypatch.setattr(main.SPPdfExtractor, "parse_multiple", parse_multiple)


@pytest.fixture
def desprotegido_em_temp(monkeypatch, tmp_path):
    """Simula PDF protegido: a leitura acontece numa cópia `tmpXYZ.pdf` em
    outra pasta (como `desproteger_para_temporario`)."""
    pasta_tmp = tmp_path / "tmpcopias"
    pasta_tmp.mkdir()

    @contextlib.contextmanager
    def fake(path, senha=None):
        assert senha == "s3nha"
        copia = os.path.join(str(pasta_tmp), "tmpXYZ.pdf")
        shutil.copyfile(path, copia)
        try:
            yield copia
        finally:
            os.remove(copia)
    monkeypatch.setattr(main, "pdf_desprotegido", fake)
    return pasta_tmp


# ------------------------------------------------------------ helper puro

def test_caminho_arquivo_unico_usa_nome_do_pdf_original_na_pasta_de_saida(tmp_path):
    pdf = os.path.join("L:/Notas/092026", NOME_REAL)
    out = str(tmp_path / "saida")
    assert caminho_xml_arquivo_unico(pdf, out) == os.path.join(out, "MAPA CONSULTORIA - 12.xml")


def test_caminho_arquivo_unico_nunca_temp_e_mesmo_prefixo_do_lote():
    for nome in ("a.pdf", "a.b.pdf", "NOTA.PDF", NOME_REAL):
        prefixo = os.path.basename(caminho_xml_arquivo_unico(os.path.join("C:/x", nome), "C:/o")).rsplit(".", 1)[0]
        assert prefixo != "temp"
        assert nome_xml_lote(nome, 1, "12") == f"{prefixo}_Pagina_1_NF_12.xml"


# ------------------------------------------------- arquivo único (run_conversion)

def test_pdf_unico_uma_pagina_gera_xml_com_nome_do_pdf(tmp_path, monkeypatch):
    _fake_parse(monkeypatch, {NOME_REAL: [_mk_nfse("12", 1)]})
    pdf = _pdf_dummy(tmp_path / "entrada", NOME_REAL)
    out = tmp_path / "saida"
    run_conversion(pdf_path=pdf, output_xml_path=caminho_xml_arquivo_unico(pdf, str(out)))
    assert _xmls(out) == ["MAPA CONSULTORIA - 12_Pagina_1_NF_12.xml"]


def test_pdf_unico_multipagina_com_selecao(tmp_path, monkeypatch):
    _fake_parse(monkeypatch, {"misto.pdf": [_mk_nfse("10", 1), _mk_nfse("11", 2), _mk_nfse("12", 3)]})
    pdf = _pdf_dummy(tmp_path / "entrada", "misto.pdf")
    out = tmp_path / "saida"
    run_conversion(pdf_path=pdf, output_xml_path=caminho_xml_arquivo_unico(pdf, str(out)),
                   selected_pages=[1, 3])
    assert _xmls(out) == ["misto_Pagina_1_NF_10.xml", "misto_Pagina_3_NF_12.xml"]


def test_pdf_unico_protegido_lido_de_temp_mantem_nome_original(tmp_path, monkeypatch, desprotegido_em_temp):
    _fake_parse(monkeypatch, {"tmpXYZ.pdf": [_mk_nfse("12", 1)]})
    pdf = _pdf_dummy(tmp_path / "entrada", NOME_REAL)
    out = tmp_path / "saida"
    run_conversion(pdf_path=pdf, output_xml_path=caminho_xml_arquivo_unico(pdf, str(out)), password="s3nha")
    assert _xmls(out) == ["MAPA CONSULTORIA - 12_Pagina_1_NF_12.xml"]
    assert _xmls(desprotegido_em_temp) == [] and os.listdir(desprotegido_em_temp) == []


# ------------------------------------------------- vários PDFs (run_batch_conversion)

def test_varios_pdfs_sem_selecao_nomes_originais(tmp_path, monkeypatch):
    _fake_parse(monkeypatch, {NOME_REAL: [_mk_nfse("12", 1)], "b.pdf": [_mk_nfse("20", 1), _mk_nfse("21", 2)]})
    a, b = _pdf_dummy(tmp_path / "e", NOME_REAL), _pdf_dummy(tmp_path / "e", "b.pdf")
    out = tmp_path / "saida"
    run_batch_conversion(output_dir=str(out), pdf_files=[a, b])
    assert _xmls(out) == ["MAPA CONSULTORIA - 12_Pagina_1_NF_12.xml", "b_Pagina_1_NF_20.xml", "b_Pagina_2_NF_21.xml"]


def test_varios_pdfs_com_selecao_e_protegido_nomes_originais(tmp_path, monkeypatch, desprotegido_em_temp):
    _fake_parse(monkeypatch, {"tmpXYZ.pdf": [_mk_nfse("12", 1), _mk_nfse("13", 2)]})
    a = _pdf_dummy(tmp_path / "e", NOME_REAL)
    out = tmp_path / "saida"
    run_batch_conversion(output_dir=str(out), pdf_files=[a], senhas={a: "s3nha"},
                         paginas_por_arquivo={a: [2]})
    assert _xmls(out) == ["MAPA CONSULTORIA - 12_Pagina_2_NF_13.xml"]


# ------------------------------------------------------- fumaça da GUI

def test_gui_arquivo_unico_nao_usa_mais_temp_xml():
    import inspect
    import gui_app
    fonte = inspect.getsource(gui_app)
    assert 'os.path.join(out_dir, "temp.xml")' not in fonte
    assert "output_xml = caminho_xml_arquivo_unico(files_to_check[0], out_dir)" in fonte
