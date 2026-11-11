"""CLI não pode cair com UnicodeEncodeError por causa do nome do PDF.

Bug real: o exe CLI (console Windows cp1252) quebrava em
`print(f"[*] Carregando PDF: {pdf_path}")` quando o nome do arquivo tinha acento
em forma DECOMPOSTA ("Digitalizac" + U+0327 + "a" + U+0303 + "o", como gravam alguns
scanners) — U+0327 não existe em cp1252. A conversão em si funcionava (cópia com
nome ASCII gerava o XML). `app._configurar_saida_console()` troca errors="strict"
por "replace" em stdout/stderr, mantendo a codificação do console.
"""
import io
import os
import subprocess
import sys

import pytest

import app
from test_pdf_protegido_senha import _gerar_pdf  # PDF com o texto da nota real (CPE)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOME_DECOMPOSTO = "Digitalização 0001.pdf"
ENV_CP1252 = {**os.environ, "PYTHONIOENCODING": "cp1252"}


def _rodar(cmd):
    return subprocess.run(cmd, cwd=RAIZ, capture_output=True, env=ENV_CP1252)


def _texto(b: bytes) -> str:
    return b.decode("cp1252", errors="replace")


# ----------------------- unidade: _configurar_saida_console -----------------------

def test_stream_cp1252_strict_passa_a_substituir():
    bruto = io.BytesIO()
    stream = io.TextIOWrapper(bruto, encoding="cp1252", errors="strict")
    with pytest.raises(UnicodeEncodeError):
        print("ç", file=stream, flush=True)

    app._configurar_saida_console([stream])
    print("Carregando: Digitalização / São", file=stream, flush=True)
    saida = bruto.getvalue().decode("cp1252")
    assert stream.encoding == "cp1252"            # codificação do console preservada
    assert "Digitalizac?a?o / São" in saida       # só o que não cabe vira "?"


def test_streams_none_ou_sem_reconfigure_sao_ignorados():
    # exe windowed (stdout/stderr None) e streams que não são TextIOWrapper
    app._configurar_saida_console([None, io.StringIO(), object()])


def test_stream_fechado_nao_derruba():
    stream = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
    stream.close()
    app._configurar_saida_console([stream])


# ----------------------- CLI de verdade (subprocess, cp1252) -----------------------

def test_controle_sem_ajuste_reproduz_o_bug(tmp_path):
    """Sem o ajuste, o mesmo fluxo cai com UnicodeEncodeError (prova que o teste
    abaixo exercita o bug real)."""
    pdf = str(tmp_path / NOME_DECOMPOSTO)
    codigo = ("import sys, app; app.main(['--input', sys.argv[1], '--output', sys.argv[2]])")
    r = _rodar([sys.executable, "-c", codigo, pdf, str(tmp_path / "x.xml")])
    assert r.returncode != 0
    assert "UnicodeEncodeError" in _texto(r.stderr)


def test_cli_nome_decomposto_converte_em_console_cp1252(tmp_path):
    pdf = _gerar_pdf(str(tmp_path / NOME_DECOMPOSTO))
    saida = tmp_path / "saida" / "nota.xml"
    r = _rodar([sys.executable, os.path.join(RAIZ, "app.py"),
                "--input", pdf, "--output", str(saida)])
    assert "UnicodeEncodeError" not in _texto(r.stderr)
    assert r.returncode == 0, _texto(r.stderr)
    assert "Carregando PDF" in _texto(r.stdout)
    assert list((tmp_path / "saida").glob("*.xml"))  # o caminho original abriu o arquivo


def test_cli_nome_decomposto_inexistente_falha_sem_unicode_error(tmp_path):
    r = _rodar([sys.executable, os.path.join(RAIZ, "app.py"),
                "--input", str(tmp_path / NOME_DECOMPOSTO), "--output", str(tmp_path / "x.xml")])
    assert r.returncode != 0                      # erro posterior legítimo (arquivo não existe)
    assert "UnicodeEncodeError" not in _texto(r.stderr)
    assert "Carregando PDF" in _texto(r.stdout)
