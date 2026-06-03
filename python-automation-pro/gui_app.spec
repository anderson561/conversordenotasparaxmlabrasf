# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas = []
binaries = []

hiddenimports = [
    # pdfminer — submódulos frequentemente não detectados pelo PyInstaller
    'pdfminer',
    'pdfminer.high_level',
    'pdfminer.layout',
    'pdfminer.pdfpage',
    'pdfminer.pdfinterp',
    'pdfminer.converter',
    'pdfminer.pdfdocument',
    'pdfminer.pdfparser',
    # pydantic — necessário para nfse_models.py
    'pydantic',
    'pydantic.v1',
    # pacote src e todos os seus submódulos
    'src',
    'src.main',
    'src.extractors',
    'src.extractors.pdf_extractor',
    'src.transformers',
    'src.transformers.abrasf_transformer',
    'src.models',
    'src.models.nfse_models',
    'src.utils',
    'src.utils.ibge_resolver',
]

tmp_ret = collect_all('flet')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

a = Analysis(
    ['gui_app.py'],
    pathex=['.'],           # garante que a raiz do projeto está no sys.path
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
