@echo off
REM ---------------------------------------------------------------------
REM  Build dos executaveis.
REM
REM  Modos:
REM      build.bat            GUI (onedir) + CLI  -- o do dia a dia, rapido
REM      build.bat release    o acima + .zip do onedir + .exe onefile,
REM                           que sao os dois assets do GitHub Release
REM      build.bat limpo      descarta o cache em build\ e refaz do zero
REM
REM  *** SEMPRE o python do .venv, NUNCA o `python` do PATH. ***
REM  As duas instalacoes tem versoes DIFERENTES do flet:
REM      .venv        -> flet 0.21.2  (ft.icons.SYSTEM_UPDATE existe)
REM      PATH/sistema -> flet 0.82.2  (icones migraram para
REM                                    flet.controls.material.icons)
REM  Construir com o do PATH gera um .exe que ABRE e entao morre com
REM  "module 'flet.controls.material.icons' has no attribute
REM  'SYSTEM_UPDATE'" (erro real, 2026-09-11). O PyInstaller empacota as
REM  bibliotecas do interpretador que o executa: o interpretador E' parte
REM  da configuracao da build.
REM
REM  Por que a GUI virou onedir: em --onefile o executavel extrai o bundle
REM  INTEIRO para %TEMP%\_MEIxxxxx a cada partida (206 MB em 986 arquivos),
REM  e o passo PKG que costura esses arquivos dentro do .exe leva ~22s e e'
REM  SEMPRE refeito -- 2a build seguida, sem alterar nada, ainda levava 82s.
REM  Em onedir nao ha extracao e o PyInstaller so recopia o que mudou.
REM
REM  NAO acrescente --clean aos comandos abaixo: e' a opcao que apaga o
REM  cache e transforma toda build numa build completa. Use `build.bat
REM  limpo` quando quiser isso de proposito.
REM ---------------------------------------------------------------------

set PY=.venv\Scripts\python.exe

if not exist "%PY%" (
    echo [!] Nao achei %PY% -- o ambiente virtual do projeto.
    echo     A build PRECISA dele: o python do PATH tem outro flet e gera
    echo     um executavel que morre na partida.
    goto :fim
)

if /i "%~1"=="limpo" (
    echo [*] Build COMPLETA pedida: descartando o cache em build\ ...
    if exist build rmdir /s /q build
)

echo [*] Gerando version_info.txt a partir de src\version.py ...
"%PY%" tools\gen_version_info.py
if errorlevel 1 goto :erro

echo [*] Construindo GUI onedir (gui_app.py)...
"%PY%" -m PyInstaller -y nfse_converter_gui.spec
if errorlevel 1 goto :erro

echo [*] Construindo CLI (app.py)...
"%PY%" -m PyInstaller -y nfse_converter_cli.spec
if errorlevel 1 goto :erro

if /i not "%~1"=="release" goto :pronto

echo.
echo [*] --- Artefatos do Release ---
echo [*] Compactando dist\nfse_converter_gui\ em dist\nfse_converter_gui.zip ...
if exist dist\nfse_converter_gui.zip del /q dist\nfse_converter_gui.zip
"%PY%" tools\empacota_release.py
if errorlevel 1 goto :erro

echo [*] Construindo GUI onefile (asset de transicao)...
"%PY%" -m PyInstaller -y nfse_converter_gui_onefile.spec
if errorlevel 1 goto :erro

:pronto
echo.
echo [+] Gerado em dist\
dir /b dist
goto :fim

:erro
echo.
echo [!] FALHOU. Se o erro for "Acesso negado" gravando em dist\, o
echo     aplicativo esta aberto -- feche-o e rode de novo.

:fim
pause
