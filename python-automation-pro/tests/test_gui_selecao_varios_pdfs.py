# -*- coding: utf-8 -*-
"""Janela de seleção de notas na GUI com VÁRIOS PDFs (antes só existia para
arquivo único: com 2+ PDFs a GUI ia direto para o lote, todas as páginas).

Cobre a lógica pura em `src/gui_selecao.py` (agrupamento, decisão de mostrar
a janela, mapa arquivo->páginas, altura do diálogo, nome dos XMLs) e o filtro
`paginas_por_arquivo` de `run_batch_conversion`, que mantém o MESMO padrão de
nomes do lote. O código Flet de `gui_app.py` (diálogo, thread de pré-análise)
NÃO é coberto por teste automatizado.
"""
import glob
import os

import pytest

import src.main as main
from src.gui_selecao import (
    ALTURA_MAX_DIALOGO, ALTURA_MIN_DIALOGO, AnaliseArquivo, altura_dialogo,
    analise_de_notas, deve_mostrar_dialogo, montar_grupos,
    montar_paginas_por_arquivo, nao_selecionaveis, nome_xml_lote,
)
from src.main import run_batch_conversion
from tests.test_selecao_paginas import _mk_nfse


def _pdf_dummy(tmp_path, nome):
    p = tmp_path / nome
    p.write_bytes(b"%PDF-1.4 dummy")
    return str(p)


def _xmls(out_dir):
    return sorted(os.path.basename(f) for f in glob.glob(os.path.join(str(out_dir), "*.xml")))


@pytest.fixture
def analises():
    return [
        AnaliseArquivo("C:/n/a.pdf", notas=[(1, "10"), (2, "11"), (3, "12")]),
        AnaliseArquivo("C:/n/b.pdf", notas=[(1, "20")]),
        AnaliseArquivo("C:/n/c.pdf", erro="falha de OCR"),
        AnaliseArquivo("C:/n/d.pdf", notas=[]),
    ]


# ------------------------------------------------------- decisão de mostrar

def test_mostra_dialogo_se_algum_pdf_tem_mais_de_uma_nota(analises):
    assert deve_mostrar_dialogo(analises)


def test_nao_mostra_dialogo_se_todos_tem_no_maximo_uma_nota():
    assert not deve_mostrar_dialogo([
        AnaliseArquivo("a.pdf", notas=[(1, "1")]),
        AnaliseArquivo("b.pdf", notas=[]),
        AnaliseArquivo("c.pdf", erro="x"),
    ])


def test_arquivo_com_erro_nao_conta_para_mostrar_dialogo():
    a = AnaliseArquivo("a.pdf", notas=[(1, "1"), (2, "2")], erro="x")
    assert not deve_mostrar_dialogo([a])


# ------------------------------------------------------------- agrupamento

def test_grupos_por_arquivo_com_rotulo_data_e_marcacao(analises):
    grupos = montar_grupos(analises)
    assert [g["titulo"] for g in grupos] == ["a.pdf", "b.pdf"]
    a, b = grupos
    assert [i["rotulo"] for i in a["itens"]] == [
        "Página 1 — Nota 10", "Página 2 — Nota 11", "Página 3 — Nota 12"]
    assert [i["data"] for i in a["itens"]] == [("C:/n/a.pdf", 1), ("C:/n/a.pdf", 2), ("C:/n/a.pdf", 3)]
    assert not any(i["marcado"] for i in a["itens"])
    # arquivo com uma única nota já vem marcado
    assert b["itens"] == [{"rotulo": "Página 1 — Nota 20", "data": ("C:/n/b.pdf", 1), "marcado": True}]


def test_nao_selecionaveis_sao_os_com_erro_ou_sem_nota(analises):
    assert [a.nome for a in nao_selecionaveis(analises)] == ["c.pdf", "d.pdf"]


def test_analise_de_notas_usa_pagina_origem_e_numero():
    a = analise_de_notas("x.pdf", [_mk_nfse("4560", 1), _mk_nfse("4538", 3)])
    assert a.notas == [(1, "4560"), (3, "4538")] and a.erro is None


# --------------------------------------------------- mapa arquivo -> páginas

def test_mapa_paginas_por_arquivo(analises):
    arquivos = [a.caminho for a in analises]
    marcados = [("C:/n/a.pdf", 3), ("C:/n/a.pdf", 1)]  # b.pdf desmarcado pelo usuário
    pdf_files, mapa, ignorados = montar_paginas_por_arquivo(arquivos, analises, marcados)
    # c (erro) e d (sem nota) vão inteiros, fora do mapa; b sem marca é ignorado
    assert pdf_files == ["C:/n/a.pdf", "C:/n/c.pdf", "C:/n/d.pdf"]
    assert mapa == {"C:/n/a.pdf": [1, 3]}
    assert ignorados == ["C:/n/b.pdf"]


def test_mapa_preserva_ordem_original_dos_arquivos(analises):
    arquivos = ["C:/n/d.pdf", "C:/n/b.pdf", "C:/n/a.pdf", "C:/n/c.pdf"]
    marcados = [("C:/n/b.pdf", 1), ("C:/n/a.pdf", 2)]
    pdf_files, mapa, ignorados = montar_paginas_por_arquivo(arquivos, analises, marcados)
    assert pdf_files == arquivos
    assert mapa == {"C:/n/b.pdf": [1], "C:/n/a.pdf": [2]}
    assert ignorados == []


# ------------------------------------------------------------ altura/diálogo

def test_altura_sempre_explicita_com_piso_e_teto():
    pouco = [AnaliseArquivo("a.pdf", notas=[(1, "1"), (2, "2")])]
    assert altura_dialogo(pouco) >= ALTURA_MIN_DIALOGO
    assert isinstance(altura_dialogo([]), int) and altura_dialogo([]) == ALTURA_MIN_DIALOGO
    muito = [AnaliseArquivo(f"{i}.pdf", notas=[(p, str(p)) for p in range(1, 9)]) for i in range(6)]
    assert altura_dialogo(muito) == ALTURA_MAX_DIALOGO == 480


def test_altura_escala_com_total_de_linhas():
    um = [AnaliseArquivo("a.pdf", notas=[(1, "1"), (2, "2")])]
    dois = um + [AnaliseArquivo("b.pdf", notas=[(1, "1")])]
    assert altura_dialogo(dois) > altura_dialogo(um)


# ----------------------------------------------------------------- nomes

def test_nome_xml_lote_padrao_inalterado():
    assert nome_xml_lote("misto.pdf", 4, "000017268") == "misto_Pagina_4_NF_000017268.xml"
    assert nome_xml_lote("a.b.pdf", None, "7") == "a.b_NF_7.xml"


# ------------------------------------- run_batch_conversion + paginas_por_arquivo

def _fake(monkeypatch, por_arquivo):
    def parse_multiple(self):
        return list(por_arquivo[os.path.basename(self.pdf_path)])
    monkeypatch.setattr(main.SPPdfExtractor, "parse_multiple", parse_multiple)


def test_lote_converte_so_paginas_escolhidas_com_nomes_do_lote(tmp_path, monkeypatch):
    _fake(monkeypatch, {
        "a.pdf": [_mk_nfse("10", 1), _mk_nfse("11", 2), _mk_nfse("12", 3)],
        "b.pdf": [_mk_nfse("20", 1), _mk_nfse("21", 2)],
    })
    a, b = _pdf_dummy(tmp_path, "a.pdf"), _pdf_dummy(tmp_path, "b.pdf")
    out = tmp_path / "saida"
    msgs = []
    run_batch_conversion(output_dir=str(out), pdf_files=[a, b],
                         paginas_por_arquivo={a: [1, 3]},
                         progress_callback=lambda p, m: msgs.append(m))
    assert _xmls(out) == [
        "a_Pagina_1_NF_10.xml", "a_Pagina_3_NF_12.xml",
        "b_Pagina_1_NF_20.xml", "b_Pagina_2_NF_21.xml",
    ]
    assert msgs[-1].startswith("Concluído! 4 Notas convertidas | 0 PDFs Ignorados | 0 PDFs Falhos")


def test_lote_sem_mapa_identico_ao_anterior(tmp_path, monkeypatch):
    _fake(monkeypatch, {"a.pdf": [_mk_nfse("10", 1), _mk_nfse("11", 2)]})
    out = tmp_path / "saida"
    run_batch_conversion(output_dir=str(out), pdf_files=[_pdf_dummy(tmp_path, "a.pdf")])
    assert _xmls(out) == ["a_Pagina_1_NF_10.xml", "a_Pagina_2_NF_11.xml"]


def test_lote_paginas_sem_nota_viram_ignorado_e_erro_nao_para_os_demais(tmp_path, monkeypatch):
    def parse_multiple(self):
        nome = os.path.basename(self.pdf_path)
        if nome == "ruim.pdf":
            raise RuntimeError("OCR falhou")
        return {"a.pdf": [_mk_nfse("10", 1)], "c.pdf": [_mk_nfse("30", 1), _mk_nfse("31", 2)]}[nome]
    monkeypatch.setattr(main.SPPdfExtractor, "parse_multiple", parse_multiple)
    a, ruim, c = (_pdf_dummy(tmp_path, n) for n in ("a.pdf", "ruim.pdf", "c.pdf"))
    out = tmp_path / "saida"
    msgs = []
    run_batch_conversion(output_dir=str(out), pdf_files=[a, ruim, c],
                         paginas_por_arquivo={a: [5], c: [2]},
                         progress_callback=lambda p, m: msgs.append(m))
    assert _xmls(out) == ["c_Pagina_2_NF_31.xml"]
    assert any("a.pdf IGNORADO (Nenhuma nota nas páginas selecionadas)" in m for m in msgs)
    assert any("[ERRO] ruim.pdf" in m for m in msgs)
    assert msgs[-1].startswith("Concluído! 1 Notas convertidas | 1 PDFs Ignorados | 1 PDFs Falhos")


def test_lote_com_mapa_respeita_cteos(tmp_path, monkeypatch):
    """Seleção + opção CT-e OS: páginas marcadas que não são DACTE OS são
    ignoradas pelo filtro de formato, como no arquivo único."""
    _fake(monkeypatch, {"a.pdf": [_mk_nfse("10", 1), _mk_nfse("11", 2)]})
    a = _pdf_dummy(tmp_path, "a.pdf")
    out = tmp_path / "saida"
    msgs = []
    run_batch_conversion(output_dir=str(out), pdf_files=[a], output_format="cteos",
                         paginas_por_arquivo={a: [2]}, progress_callback=lambda p, m: msgs.append(m))
    assert _xmls(out) == []
    assert any("a.pdf IGNORADO (Nenhum DACTE OS (Modelo 67) encontrado)" in m for m in msgs)


def test_gui_app_importa_e_usa_selecao_varios():
    """Fumaça: o módulo da GUI importa (Flet 0.21.2 do .venv) e tem o fluxo novo."""
    import gui_app
    import inspect
    fonte = inspect.getsource(gui_app)
    assert "analisar_varios" in fonte and "paginas_por_arquivo" in fonte
    assert "height=altura_dialogo(analises)" in fonte
