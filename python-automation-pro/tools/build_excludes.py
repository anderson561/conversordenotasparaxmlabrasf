# -*- coding: utf-8 -*-
"""Lista única de módulos que NÃO devem entrar nos executáveis.

Importada pelos três .spec (GUI onedir, GUI onefile e CLI) via `SPECPATH`,
para a lista não divergir entre eles.

Por que existe: o `.venv` deste projeto é compartilhado com outros trabalhos e
carrega scipy, pandas, matplotlib, opencv, camelot, tabula, llama-index,
openai, nibabel, nipype e mais. Sem `excludes`, o PyInstaller empacota tudo
que conseguir alcançar a partir dos imports — o bundle chegava a 354 MB
extraídos em 1228 arquivos (medido em 2026-09-11).

A superfície real de dependências de terceiros do app é pequena e conhecida,
conferida por grep sobre `src/`, `app.py` e `gui_app.py`:

    PIL  flet  numpy  pdfminer  pydantic  pymupdf  pytesseract  requests

Duas que PARECEM dispensáveis e não são:
  - **numpy** é usado de verdade (desentorto da faixa do cabeçalho, em
    `pdf_extractor.py`);
  - **cryptography** é exigida pelo pdfminer.six para abrir PDF criptografado.
"""

EXCLUDES = [
    'scipy', 'pandas', 'matplotlib', 'cv2', 'sklearn', 'sympy',
    'camelot', 'tabula', 'llama_index', 'openai', 'nibabel', 'nipype',
    'networkx', 'customtkinter', 'tkinter', 'cookiecutter',
    'IPython', 'jupyter', 'notebook', 'pytest', 'torch', 'tensorflow',
    'plotly', 'seaborn', 'statsmodels', 'bokeh', 'dask', 'altair',
]

# ⚠️ NÃO acrescente `libmpv-2.dll` a nenhum filtro de binários, por mais que o
# app não use `ft.Video` nem `ft.Audio` (conferido por grep — nenhum uso).
# Foi tentado em 2026-09-11: o executável MORRE antes de qualquer janela, com
# "flet.exe - Erro do sistema: a execução de código não pode continuar porque
# libmpv-2.dll não foi encontrado". A DLL não é carregada sob demanda quando se
# usa mídia — é dependência de LINK do próprio `flet.exe`, o processo do
# Flutter que desenha a interface. O mesmo vale para flutter_windows.dll e
# libGLESv2.dll.
