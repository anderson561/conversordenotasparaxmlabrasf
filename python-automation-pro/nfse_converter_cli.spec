# -*- mode: python ; coding: utf-8 -*-
"""CLI (`app.py`) em --onefile — aqui o onefile faz sentido: é uma ferramenta
de linha de comando, sem interface, que se quer poder copiar como um arquivo
só, e o bundle é pequeno (61 MB) porque o flet inteiro fica de fora.

A CLI não entra no Release do GitHub — só a GUI tem auto-update. É construída
porque o build.bat sempre a construiu.
"""
import sys

sys.path.insert(0, SPECPATH)
from tools.build_excludes import EXCLUDES  # noqa: E402
from PyInstaller.utils.hooks import collect_all  # noqa: E402

datas = []
binaries = []
hiddenimports = []
tmp_ret = collect_all('pdfminer')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# A CLI não tem interface gráfica: o flet inteiro (89 MB, mais as DLLs do
# Flutter) não tem o que fazer aqui.
EXCLUDES_CLI = EXCLUDES + ['flet']

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES_CLI,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='nfse_converter_cli',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX não está instalado; em onefile ele custa build e partida.
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
