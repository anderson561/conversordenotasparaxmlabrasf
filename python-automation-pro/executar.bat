@echo off
set "INPUT_DIR=L:\USUARIOS\ANDERSON\ARQUIVOS DESKTOP\Notas\032026"
set "OUTPUT_DIR=C:\Temp\xml_output"

if not exist "dist\nfse_converter.exe" (
    echo [!] Erro: Executavel nao encontrado em dist\nfse_converter.exe
    echo [!] Rode o build.bat primeiro.
    pause
    exit /b
)

echo [*] Iniciando processamento em lote...
dist\nfse_converter.exe --batch "%INPUT_DIR%" --output "%OUTPUT_DIR%"

echo.
echo [+] Concluido. Pressione qualquer tecla para sair.
pause
