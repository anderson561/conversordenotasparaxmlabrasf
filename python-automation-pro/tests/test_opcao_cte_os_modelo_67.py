# -*- coding: utf-8 -*-
"""Opção explícita "CT-e OS (DACTE OS - Modelo 67)" (`output_format="cteos"`)
na GUI, na CLI (`app.py --format cteos`) e no lote.

Com "cteos" a conversão gera SOMENTE os documentos CT-e OS (`CteOS`, Modelo
67) do PDF e IGNORA as demais páginas (NFS-e, NF-e), registrando cada página
ignorada; sem nenhum CT-e OS, erro claro (`NenhumCteOsError`), sem XML vazio.
Os outros modos continuam idênticos - em especial o roteamento automático de
um CT-e OS para `cteProc` mod 67 no modo "abrasf" (ver `_pick_transformer`).

O `CteOS` usado aqui é o da nota REAL nº 17268 (SIGMA -> STAUMMAQ, pág. 4 de
"STAUMMAQ - NFSe TERCEIROS.pdf"), extraído do texto OCR real gravado em
`test_dacte_os_staummaq_sigma_pag4.py` - sem OCR de verdade.
"""
import glob
import os
import re
import threading
from unittest import mock

import pymupdf
import pytest

import src.main as main
from src.main import (
    FORMATO_CTE_OS, run_batch_conversion, run_conversion, separar_por_formato,
)
from src.models.cte_os_model import CteOS
from src.models.nfse_models import Nfse
from src.utils.erros import NenhumCteOsError, descrever_erro
from src.utils.pdf_senha import PdfProtegidoPorSenhaError
from tests.test_dacte_os_staummaq_sigma_pag4 import MOCK_GRADE, MOCK_PAGINA, _parse
from tests.test_selecao_paginas import _mk_nfse


# --------------------------------------------------------------- fixtures

@pytest.fixture
def cte_17268(monkeypatch, tmp_path):
    cte = _parse(monkeypatch, tmp_path, MOCK_PAGINA, mock_grade=MOCK_GRADE, pagina_hint=4)
    assert isinstance(cte, CteOS)
    cte.pagina_origem = 4  # o mock é de uma página só; no PDF real é a 4ª
    return cte


@pytest.fixture
def lote_misto(cte_17268):
    """Espelha "STAUMMAQ - NFSe TERCEIROS.pdf": págs. 1-3 NFS-e, pág. 4 DACTE OS."""
    return [_mk_nfse("4560", 1), _mk_nfse("4538", 2), _mk_nfse("1359", 3), cte_17268]


def _fake_extracao(monkeypatch, por_arquivo):
    """`por_arquivo`: nome-base do PDF -> lista de notas (ou uma lista só,
    usada para qualquer arquivo)."""
    def parse_multiple(self):
        if isinstance(por_arquivo, list):
            return list(por_arquivo)
        return list(por_arquivo[os.path.basename(self.pdf_path)])
    monkeypatch.setattr(main.SPPdfExtractor, "parse_multiple", parse_multiple)


def _xmls(out_dir):
    return sorted(os.path.basename(f) for f in glob.glob(os.path.join(str(out_dir), "*.xml")))


def _ler(out_dir, nome):
    with open(os.path.join(str(out_dir), nome), encoding="utf-8") as f:
        return f.read()


def _pdf_dummy(tmp_path, nome):
    p = tmp_path / nome
    p.write_bytes(b"%PDF-1.4 dummy")
    return str(p)


# ------------------------------------------------------ filtro (src/main.py)

def test_separar_por_formato_cteos_mantem_so_cte(lote_misto):
    mantidos, ignorados = separar_por_formato(lote_misto, FORMATO_CTE_OS)
    assert [type(n) for n in mantidos] == [CteOS]
    assert [n.pagina_origem for n in ignorados] == [1, 2, 3]


@pytest.mark.parametrize("fmt", ["abrasf", "nfe"])
def test_separar_por_formato_outros_modos_nao_filtram(lote_misto, fmt):
    mantidos, ignorados = separar_por_formato(lote_misto, fmt)
    assert mantidos == lote_misto and ignorados == []


# --------------------------------------------------- (a) lote misto, cteos

def test_run_conversion_cteos_gera_so_o_mod_67(tmp_path, monkeypatch, lote_misto):
    _fake_extracao(monkeypatch, lote_misto)
    out = tmp_path / "saida"
    msgs = []
    run_conversion(_pdf_dummy(tmp_path, "t.pdf"), str(out / "STAUMMAQ.xml"),
                   output_format="cteos", progress_callback=lambda p, m: msgs.append(m))

    # Mesmo padrão de nome que o CT-e já recebe hoje no modo abrasf.
    assert _xmls(out) == ["STAUMMAQ_Pagina_4_NF_000017268.xml"]
    xml = _ler(out, "STAUMMAQ_Pagina_4_NF_000017268.xml")
    assert "<cteProc" in xml and "<mod>67</mod>" in xml
    assert "CompNfse" not in xml

    ignoradas = [m for m in msgs if "não é DACTE OS" in m]
    assert len(ignoradas) == 3
    for pag in (1, 2, 3):
        assert any(f"Página {pag} não é DACTE OS" in m and "ignorada nesta opção" in m for m in ignoradas)
    assert any("3 página(s) ignorada(s)" in m for m in msgs)


def test_run_conversion_cteos_respeita_selecao_de_paginas(tmp_path, monkeypatch, lote_misto):
    _fake_extracao(monkeypatch, lote_misto)
    out = tmp_path / "saida"
    run_conversion(_pdf_dummy(tmp_path, "t.pdf"), str(out / "x.xml"),
                   output_format="cteos", selected_pages=[2, 4])
    assert _xmls(out) == ["x_Pagina_4_NF_000017268.xml"]

    out2 = tmp_path / "saida2"
    with pytest.raises(NenhumCteOsError, match="páginas selecionadas"):
        run_conversion(_pdf_dummy(tmp_path, "t.pdf"), str(out2 / "x.xml"),
                       output_format="cteos", selected_pages=[1, 2])
    assert _xmls(out2) == []


# ------------------------------------------- (b) só NFS-e -> nada + mensagem

def test_run_conversion_cteos_sem_cte_erro_claro_e_nenhum_xml(tmp_path, monkeypatch):
    _fake_extracao(monkeypatch, [_mk_nfse("1", 1), _mk_nfse("2", 2)])
    out = tmp_path / "saida"
    with pytest.raises(NenhumCteOsError) as exc:
        run_conversion(_pdf_dummy(tmp_path, "so_nfse.pdf"), str(out / "x.xml"), output_format="cteos")
    msg = descrever_erro(exc.value)
    assert msg.startswith("Nenhum DACTE OS (Modelo 67) encontrado no PDF")
    assert "so_nfse.pdf" in msg
    assert _xmls(out) == []


# --------------------------------------------- (c) modo abrasf inalterado

def test_modo_abrasf_inalterado_abrasf_mais_cteproc_auto_roteado(tmp_path, monkeypatch, lote_misto):
    _fake_extracao(monkeypatch, lote_misto)
    out = tmp_path / "saida"
    msgs = []
    run_conversion(_pdf_dummy(tmp_path, "t.pdf"), str(out / "S.xml"),
                   output_format="abrasf", progress_callback=lambda p, m: msgs.append(m))
    assert _xmls(out) == [
        "S_Pagina_1_NF_4560.xml", "S_Pagina_2_NF_4538.xml",
        "S_Pagina_3_NF_1359.xml", "S_Pagina_4_NF_000017268.xml",
    ]
    for nome in _xmls(out)[:3]:
        assert "CompNfse" in _ler(out, nome)
    assert "<mod>67</mod>" in _ler(out, "S_Pagina_4_NF_000017268.xml")
    assert not any("não é DACTE OS" in m for m in msgs)


# ----------------------------------------------------------- (d) CLI

def test_cli_aceita_format_cteos():
    import app
    args = app.build_parser().parse_args(["--input", "a.pdf", "--output", "o.xml", "--format", "cteos"])
    assert args.format == "cteos"
    with pytest.raises(SystemExit):
        app.build_parser().parse_args(["--input", "a.pdf", "--output", "o.xml", "--format", "xyz"])


def test_cli_cteos_repassa_formato_e_paginas(monkeypatch):
    import app
    chamadas = {}
    monkeypatch.setattr(app, "run_conversion", lambda *a, **k: chamadas.update(k))
    app.main(["--input", "a.pdf", "--output", "o.xml", "--format", "cteos", "--pages", "4"])
    assert chamadas["output_format"] == "cteos" and chamadas["selected_pages"] == [4]


def test_cli_cteos_sem_cte_sai_com_mensagem_clara(monkeypatch):
    import app

    def _falha(*a, **k):
        raise NenhumCteOsError("so_nfse.pdf")
    monkeypatch.setattr(app, "run_conversion", _falha)
    with pytest.raises(SystemExit) as exc:
        app.main(["--input", "so_nfse.pdf", "--output", "o.xml", "--format", "cteos"])
    assert str(exc.value).startswith("[ERRO] Nenhum DACTE OS (Modelo 67) encontrado no PDF")


def test_cli_batch_repassa_cteos(monkeypatch):
    import app
    chamadas = {}
    monkeypatch.setattr(app, "run_batch_conversion", lambda *a, **k: chamadas.update(k))
    app.main(["--batch", "dir", "--output", "out", "--format", "cteos"])
    assert chamadas["output_format"] == "cteos"


# ---------------------------------------------------------- (e) lote

def test_batch_cteos_so_mod_67_e_pdf_sem_cte_vira_ignorado(tmp_path, monkeypatch, lote_misto):
    _fake_extracao(monkeypatch, {"misto.pdf": lote_misto, "so_nfse.pdf": [_mk_nfse("9", 1)]})
    pdfs = [_pdf_dummy(tmp_path, "misto.pdf"), _pdf_dummy(tmp_path, "so_nfse.pdf")]
    out = tmp_path / "saida"
    msgs = []
    run_batch_conversion(output_dir=str(out), pdf_files=pdfs, output_format="cteos",
                         progress_callback=lambda p, m: msgs.append(m))
    assert _xmls(out) == ["misto_Pagina_4_NF_000017268.xml"]
    assert "<mod>67</mod>" in _ler(out, "misto_Pagina_4_NF_000017268.xml")
    assert any("so_nfse.pdf IGNORADO" in m and "Nenhum DACTE OS (Modelo 67)" in m for m in msgs)
    assert any("misto.pdf" in m and "Página 1 não é DACTE OS" in m for m in msgs)
    assert msgs[-1].startswith("Concluído! 1 Notas convertidas | 1 PDFs Ignorados | 0 PDFs Falhos")


def test_batch_abrasf_inalterado(tmp_path, monkeypatch, lote_misto):
    _fake_extracao(monkeypatch, lote_misto)
    out = tmp_path / "saida"
    run_batch_conversion(output_dir=str(out), pdf_files=[_pdf_dummy(tmp_path, "m.pdf")], output_format="abrasf")
    assert len(_xmls(out)) == 4


# ------------------------------------------------------ PDF com senha

def test_cteos_em_pdf_protegido_por_senha(tmp_path, monkeypatch, lote_misto):
    caminho = str(tmp_path / "protegido.pdf")
    doc = pymupdf.open()
    doc.new_page()
    doc.save(caminho, encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="s3nha", owner_pw="dono")
    doc.close()
    _fake_extracao(monkeypatch, lote_misto)
    out = tmp_path / "saida"
    with pytest.raises(PdfProtegidoPorSenhaError):
        run_conversion(caminho, str(out / "p.xml"), output_format="cteos")
    run_conversion(caminho, str(out / "p.xml"), output_format="cteos", password="s3nha")
    assert _xmls(out) == ["p_Pagina_4_NF_000017268.xml"]


# ------------------------------------------------------------------ GUI

def _controles(raiz):
    """Percorre a árvore de controles Flet (sem janela) a partir de `raiz`."""
    pilha, vistos = [raiz], []
    while pilha:
        c = pilha.pop()
        vistos.append(c)
        for attr in ("controls", "content"):
            filho = getattr(c, attr, None)
            if isinstance(filho, list):
                pilha.extend(filho)
            elif filho is not None and hasattr(filho, "_get_control_name"):
                pilha.append(filho)
    return vistos


@pytest.fixture
def gui(monkeypatch):
    """Constrói a página real de `gui_app.main` sobre um `Page` falso (sem
    abrir janela nem acessar a rede) e devolve seus controles."""
    import flet as ft
    import gui_app
    monkeypatch.setattr(gui_app.auto_updater, "check_latest_release", lambda: None)
    monkeypatch.setattr(gui_app.auto_updater, "ler_falha_pendente", lambda: None)
    monkeypatch.setattr(gui_app.auto_updater, "limpar_restos_de_updates", lambda: None)
    page = mock.MagicMock()
    page.overlay = []
    gui_app.main(page)
    raiz = page.add.call_args[0][0]
    todos = _controles(raiz)
    dropdown = next(c for c in todos if isinstance(c, ft.Dropdown))
    campos = {c.label: c for c in todos if isinstance(c, ft.TextField)}
    botao = next(c for c in todos if isinstance(c, ft.ElevatedButton) and c.text == "Iniciar Conversão")
    return dict(page=page, dropdown=dropdown, campos=campos, botao=botao, todos=todos)


def test_gui_dropdown_tem_opcao_cteos(gui):
    opcoes = {o.key: o.text for o in gui["dropdown"].options}
    assert opcoes["cteos"] == "CT-e OS (DACTE OS - Modelo 67)"
    assert set(opcoes) == {"abrasf", "nfe", "cteos", "contrato_locacao"}
    assert gui["dropdown"].value == "abrasf"  # padrão inalterado


def test_gui_cteos_mantem_painel_de_pdf(gui):
    gui["dropdown"].value = "cteos"
    gui["dropdown"].on_change(None)
    entrada = gui["campos"]["Pasta de Entrada (PDFs)"]
    painel_pdf = next(c for c in gui["todos"] if getattr(c, "controls", None) and any(
        entrada in getattr(r, "controls", []) for r in c.controls))
    assert painel_pdf.visible is True


def _rodar_gui(gui, monkeypatch, tmp_path, lote, formato):
    """Clica em "Iniciar Conversão" com um único PDF na pasta de entrada e
    espera a thread de conversão terminar."""
    _fake_extracao(monkeypatch, lote)
    ent = tmp_path / "ent"
    ent.mkdir()
    _pdf_dummy(ent, "STAUMMAQ.pdf")
    out = tmp_path / "out"
    out.mkdir()
    threads = []
    original = threading.Thread

    def _thread(*a, **k):
        t = original(*a, **k)
        threads.append(t)
        return t
    monkeypatch.setattr(threading, "Thread", _thread)
    gui["dropdown"].value = formato
    gui["dropdown"].on_change(None)
    gui["campos"]["Pasta de Entrada (PDFs)"].value = str(ent)
    gui["campos"]["Pasta de Saída (XMLs)"].value = str(out)
    gui["botao"].on_click(None)
    for t in threads:
        t.join(timeout=30)
    return out


def _log_da_gui(gui):
    import flet as ft
    lista = next(c for c in gui["todos"] if isinstance(c, ft.ListView))
    return [t.value for t in lista.controls]


def test_gui_cteos_arquivo_unico_converte_so_o_cte_sem_dialogo(gui, monkeypatch, tmp_path, lote_misto):
    out = _rodar_gui(gui, monkeypatch, tmp_path, lote_misto, "cteos")
    assert _xmls(out) == ["temp_Pagina_4_NF_000017268.xml"]
    log = _log_da_gui(gui)
    assert sum("não é DACTE OS" in m for m in log) == 3
    # Só 1 CT-e OS sobra: não abre o diálogo de seleção de páginas (que
    # ofereceria as NFS-e que esta opção vai ignorar).
    assert not any(getattr(o, "title", None) is not None and getattr(o.title, "value", "") ==
                   "Selecionar páginas para conversão" for o in gui["page"].overlay)


def test_gui_cteos_sem_cte_mostra_mensagem_clara(gui, monkeypatch, tmp_path):
    out = _rodar_gui(gui, monkeypatch, tmp_path, [_mk_nfse("1", 1)], "cteos")
    assert _xmls(out) == []
    log = _log_da_gui(gui)
    assert any(m.startswith("[ERRO] Nenhum DACTE OS (Modelo 67) encontrado no PDF") for m in log)


def test_gui_cteos_dois_cte_dialogo_oferece_so_os_dacte_os(gui, monkeypatch, tmp_path, cte_17268):
    outro = cte_17268.model_copy(update={"numero": "564", "pagina_origem": 6})
    out = _rodar_gui(gui, monkeypatch, tmp_path, [_mk_nfse("1", 1), cte_17268, outro], "cteos")
    import flet as ft
    dialogos = [o for o in gui["page"].overlay if isinstance(o, ft.AlertDialog)
                and getattr(o.title, "value", "") == "Selecionar páginas para conversão"]
    assert len(dialogos) == 1
    rotulos = [c.label for c in _controles(dialogos[0].content) if isinstance(c, ft.Checkbox)]
    assert sorted(rotulos) == ["Página 4 — Nota 000017268", "Página 6 — Nota 564"]
    assert _xmls(out) == []  # aguardando a escolha do usuário
