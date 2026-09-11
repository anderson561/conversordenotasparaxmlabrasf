# -*- mode: python ; coding: utf-8 -*-
"""GUI em **--onefile** — asset de TRANSIÇÃO, não o formato principal.

A distribuição passou a ser onedir (`nfse_converter_gui.spec`, que vira o
`nfse_converter_gui.zip`). Este spec continua existindo por um motivo só:
toda instalação já existente até a v1.7.0 é onefile, e o `auto_updater` dela
procura no Release um asset chamado exatamente `nfse_converter_gui.exe`.
Publicar apenas o .zip deixaria essas instalações sem caminho de atualização.

Então o Release publica os DOIS:
  - `nfse_converter_gui.zip`  -> onedir, partida quase instantânea (preferido)
  - `nfse_converter_gui.exe`  -> onefile, para quem ainda está em onefile

O .exe gerado aqui já é bem menor e mais rápido que o da v1.7.0 (101 MB contra
170 MB; 206 MB extraídos por partida contra 354 MB), porque herda os mesmos
`EXCLUDES`. Ele também carrega o `auto_updater` novo, que sabe migrar para o
.zip na atualização seguinte.

Só é construído por `build.bat release` — o `build.bat` do dia a dia constrói
apenas o onedir, que é o rápido.
"""
import sys

sys.path.insert(0, SPECPATH)
from tools.build_excludes import EXCLUDES  # noqa: E402


a = Analysis(
    ['gui_app.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['pdfminer'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
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
    name='nfse_converter_gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
)
