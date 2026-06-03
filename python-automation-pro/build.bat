@echo off
echo [*] Gerando executaveis...

echo [*] Construindo CLI (app.py)...
python -m PyInstaller -y --onefile --name nfse_converter_cli --collect-all pdfminer app.py

echo [*] Construindo GUI (gui_app.py)...
call .venv\Scripts\flet.exe pack gui_app.py --name nfse_converter_gui -y --hidden-import pdfminer.six

echo [+] Executaveis gerados na pasta dist/
pause
