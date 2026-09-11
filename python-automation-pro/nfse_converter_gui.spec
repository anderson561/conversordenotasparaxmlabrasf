# -*- mode: python ; coding: utf-8 -*-
"""GUI em **--onedir**: a forma normal de distribuir e a única que permite
build incremental de verdade. Gera `dist/nfse_converter_gui/` (executável +
`_internal/`), que o build.bat compacta em `nfse_converter_gui.zip`.

Por que onedir (decidido em 2026-09-11, com medição):

- **Partida.** Em `--onefile` o executável extrai o bundle INTEIRO para
  `%TEMP%\\_MEIxxxxx` a cada inicialização — 206 MB em 986 arquivos, mesmo já
  enxuto. Era a causa da lentidão relatada ("a ponto de não completar": um
  `_MEI42562` parou em 73 MB de 354). Em onedir não há extração nenhuma: os
  arquivos já estão no disco, ao lado do .exe.
- **Build incremental.** Também é consequência do onefile: o passo PKG, que
  costura os 986 arquivos dentro do .exe, leva ~22 s e é SEMPRE refeito, mesmo
  sem nenhuma alteração (medido: 2ª build seguida = 82 s). Em onedir o
  PyInstaller só recopia o que mudou.
- **Lixo em %TEMP%.** Cada partida em onefile deixa um `_MEI*` para trás
  quando a limpeza falha; havia 32 deles, 428 MB, nesta máquina.

O `nfse_converter_gui_onefile.spec`, ao lado, continua existindo: é o asset de
TRANSIÇÃO para quem já tem uma instalação onefile e atualiza pelo próprio app
(ver `src/utils/auto_updater.py`).

O flet não precisa do `flet pack` para ser empacotado: o próprio pacote traz
`flet/__pyinstaller/hook-flet.py`, que o PyInstaller descobre sozinho.
"""
import sys

sys.path.insert(0, SPECPATH)
from tools.build_excludes import EXCLUDES  # noqa: E402


a = Analysis(
    ['gui_app.py'],
    pathex=[],
    binaries=[],
    datas=[],
    # `pdfminer` (o módulo). O comando antigo pedia 'pdfminer.six', que é o
    # nome da DISTRIBUIÇÃO no PyPI, não um módulo importável — o PyInstaller
    # logava "ERROR: Hidden import 'pdfminer.six' not found" em toda build.
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
    [],
    exclude_binaries=True,       # onedir: os binários vão para o COLLECT
    name='nfse_converter_gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Caminho ESTÁVEL, gerado por tools/gen_version_info.py a partir de
    # src/version.py. O `flet pack` apontava para um diretório temporário de
    # nome ALEATÓRIO a cada execução, o que (a) impedia qualquer cache do
    # passo EXE e (b) fazia este arquivo aparecer eternamente modificado no
    # `git status`. De quebra, o recurso que ele gravava trazia a versão do
    # FLET (0.21.2), não a do aplicativo.
    version='version_info.txt',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='nfse_converter_gui',
)
