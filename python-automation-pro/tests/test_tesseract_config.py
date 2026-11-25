"""DT-11 — caminho do Tesseract configurável.

Ordem: variável de ambiente TESSERACT_CMD -> caminho padrão do instalador
Windows -> PATH (tesseract_cmd intocado).
"""
import os
import types

import pytest

from src.utils import tesseract_config as tc


def _fake_pytesseract(cmd="tesseract"):
    mod = types.SimpleNamespace()
    mod.pytesseract = types.SimpleNamespace(tesseract_cmd=cmd)
    return mod


@pytest.fixture
def sem_padrao(monkeypatch):
    """Simula máquina sem o Tesseract no caminho padrão."""
    real_exists = os.path.exists
    monkeypatch.setattr(
        tc.os.path, "exists",
        lambda p: False if p == tc.CAMINHO_PADRAO_TESSERACT else real_exists(p))


@pytest.fixture
def com_padrao(monkeypatch):
    """Simula máquina com o Tesseract no caminho padrão."""
    real_exists = os.path.exists
    monkeypatch.setattr(
        tc.os.path, "exists",
        lambda p: True if p == tc.CAMINHO_PADRAO_TESSERACT else real_exists(p))


def test_variavel_de_ambiente_tem_prioridade(tmp_path, monkeypatch, com_padrao):
    exe = tmp_path / "tesseract.exe"
    exe.write_bytes(b"")
    monkeypatch.setenv("TESSERACT_CMD", str(exe))
    assert tc.resolver_tesseract_cmd() == str(exe)


def test_variavel_de_ambiente_aceita_aspas(tmp_path, monkeypatch, sem_padrao):
    exe = tmp_path / "tesseract.exe"
    exe.write_bytes(b"")
    monkeypatch.setenv("TESSERACT_CMD", f'"{exe}"')
    assert tc.resolver_tesseract_cmd() == str(exe)


def test_variavel_apontando_para_arquivo_inexistente_cai_no_padrao(tmp_path, monkeypatch, com_padrao):
    monkeypatch.setenv("TESSERACT_CMD", str(tmp_path / "nao_existe.exe"))
    assert tc.resolver_tesseract_cmd() == tc.CAMINHO_PADRAO_TESSERACT


def test_sem_variavel_usa_caminho_padrao(monkeypatch, com_padrao):
    monkeypatch.delenv("TESSERACT_CMD", raising=False)
    assert tc.resolver_tesseract_cmd() == tc.CAMINHO_PADRAO_TESSERACT


def test_sem_variavel_e_sem_padrao_fica_no_path(monkeypatch, sem_padrao):
    monkeypatch.delenv("TESSERACT_CMD", raising=False)
    assert tc.resolver_tesseract_cmd() is None
    mod = _fake_pytesseract()
    assert tc.configurar_pytesseract(mod) is None
    assert mod.pytesseract.tesseract_cmd == "tesseract"


def test_configurar_pytesseract_aplica_caminho_resolvido(tmp_path, monkeypatch, sem_padrao):
    exe = tmp_path / "tesseract.exe"
    exe.write_bytes(b"")
    monkeypatch.setenv("TESSERACT_CMD", str(exe))
    mod = _fake_pytesseract()
    assert tc.configurar_pytesseract(mod) == str(exe)
    assert mod.pytesseract.tesseract_cmd == str(exe)


def test_caminho_padrao_inalterado():
    assert tc.CAMINHO_PADRAO_TESSERACT == r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def test_nenhum_extrator_mantem_caminho_fixo():
    """O caminho fixo só pode existir no módulo central."""
    raiz = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
    achados = []
    for pasta, _, arquivos in os.walk(raiz):
        for nome in arquivos:
            if not nome.endswith(".py") or nome == "tesseract_config.py":
                continue
            with open(os.path.join(pasta, nome), encoding="utf-8") as f:
                if "Tesseract-OCR" in f.read():
                    achados.append(nome)
    assert achados == []
