"""Verificador e aplicador de atualização automática via GitHub Releases.

Estratégia escolhida pelo usuário em 2026-08-18: download e substituição
automática do .exe em execução (não apenas notificar/linkar), com
checagem automática ao abrir o app + botão manual na GUI.

Pré-requisito operacional: cada tag publicada precisa virar um GitHub
Release "estável" (não draft, não pre-release) com o
`nfse_converter_gui.exe` gerado pelo build.bat anexado como asset —
`GET /releases/latest` só enxerga Releases publicados, tags sozinhas não
aparecem aqui. Ver "Processo de Release" em DOCUMENTACAO_CONVERSAO.md.
"""
import os
import re
import sys
import tempfile
import subprocess

import requests

from src.version import APP_VERSION, GITHUB_OWNER, GITHUB_REPO

API_LATEST_RELEASE_URL = (
    f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
)
EXE_ASSET_NAME = "nfse_converter_gui.exe"
ZIP_ASSET_NAME = "nfse_converter_gui.zip"
REQUEST_TIMEOUT = 10

# Arquivo deixado pelo .bat de troca quando a substituição NÃO deu certo. O
# app procura por ele ao abrir e mostra o motivo — antes a falha era
# silenciosa: o .bat relançava a versão ANTIGA e o usuário ficava achando que
# tinha atualizado (achado real 2026-09-11, update travado com o app aberto).
FALHA_LOG = os.path.join(tempfile.gettempdir(), "nfse_update_falhou.log")


def _parse_version(version_str):
    """'v1.3.0' ou '1.3.0' -> (1, 3, 0). Ignora sufixos não numéricos."""
    nums = re.findall(r'\d+', version_str or "")
    return tuple(int(n) for n in nums[:3]) if nums else (0, 0, 0)


def is_newer(remote_version, local_version=APP_VERSION):
    return _parse_version(remote_version) > _parse_version(local_version)


def check_latest_release():
    """Consulta o Release estável mais recente publicado no GitHub.

    Retorna um dict {"version", "assets", "url", "notes"} se houver uma
    versão mais nova que APP_VERSION, ou None quando já está atualizado,
    quando ainda não existe nenhum Release publicado (404) ou quando a
    consulta falha por qualquer motivo (rede indisponível, rate limit,
    resposta inesperada) — o chamador trata None como "nada a fazer" e
    nunca precisa capturar exceção desta função.
    """
    try:
        resp = requests.get(
            API_LATEST_RELEASE_URL,
            timeout=REQUEST_TIMEOUT,
            headers={"Accept": "application/vnd.github+json"},
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError):
        return None

    tag = data.get("tag_name", "")
    if not tag or not is_newer(tag):
        return None

    return {
        "version": tag,
        "assets": data.get("assets", []),
        "url": data.get("html_url", ""),
        "notes": data.get("body", "") or "",
    }


def find_exe_asset(release, exe_name=EXE_ASSET_NAME):
    """Localiza o asset .exe do Release (match exato pelo nome; senão,
    primeiro asset terminado em .exe)."""
    assets = release.get("assets", [])
    for a in assets:
        if a.get("name") == exe_name:
            return a
    for a in assets:
        if a.get("name", "").lower().endswith(".exe"):
            return a
    return None


def find_zip_asset(release, zip_name=ZIP_ASSET_NAME):
    """Localiza o asset .zip do Release — a build onedir empacotada."""
    assets = release.get("assets", [])
    for a in assets:
        if a.get("name") == zip_name:
            return a
    for a in assets:
        if a.get("name", "").lower().endswith(".zip"):
            return a
    return None


def find_update_asset(release):
    """Escolhe QUAL asset baixar, conforme o formato desta instalação, e
    devolve `(asset, tipo)` com tipo em {"zip", "exe"} — ou `(None, None)`.

    Uma instalação **onedir** (pasta) se atualiza pelo .zip; uma **onefile**
    (executável único) se atualiza pelo .exe. Os dois assets são publicados em
    todo Release, então nenhuma das duas fica sem caminho de atualização.

    Não existe migração automática de onefile para onedir: são formatos de
    instalação diferentes, e trocar um pelo outro por baixo do usuário mexeria
    na pasta dele sem aviso. Quem está em onefile continua recebendo onefile
    (já bem mais leve) e migra baixando o .zip uma vez, quando quiser.
    """
    if is_onedir():
        asset = find_zip_asset(release)
        if asset:
            return asset, "zip"
        # Instalação onedir e Release sem .zip: não dá para instalar um
        # onefile por cima de uma pasta. Melhor não fazer nada do que
        # bagunçar a instalação.
        return None, None

    asset = find_exe_asset(release)
    if asset:
        return asset, "exe"
    return None, None


def download_asset(asset, dest_path, progress_callback=None):
    """Baixa o asset para dest_path, chamando progress_callback(fracao_0_a_1)
    a cada bloco quando o tamanho total é conhecido. Levanta IOError se o
    download vier truncado."""
    url = asset["browser_download_url"]
    total = asset.get("size", 0)
    downloaded = 0
    with requests.get(url, stream=True, timeout=30) as resp:
        resp.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 256):
                if not chunk:
                    continue
                f.write(chunk)
                downloaded += len(chunk)
                if progress_callback and total:
                    progress_callback(downloaded / total)
    if total and downloaded != total:
        raise IOError(f"Download incompleto: {downloaded}/{total} bytes")
    return dest_path


def is_frozen():
    """True quando rodando como .exe empacotado (PyInstaller); False em dev
    (rodando via `python gui_app.py`), caso em que não há .exe para trocar."""
    return getattr(sys, "frozen", False)


def is_onedir():
    """True quando esta instalação é a build **onedir** (executável + pasta
    `_internal/` ao lado), False quando é **onefile** (executável único).

    Como distinguir: o PyInstaller expõe `sys._MEIPASS` apontando para onde os
    arquivos empacotados estão. Em onedir isso é o `_internal/` DENTRO da
    pasta do app, então `dirname(_MEIPASS) == dirname(executável)`. Em onefile
    é o `%TEMP%\\_MEIxxxxx` sorteado a cada partida, que não fica perto do
    executável nenhum.
    """
    if not is_frozen():
        return False
    mei = getattr(sys, "_MEIPASS", None)
    if not mei:
        return False
    return (os.path.normcase(os.path.dirname(os.path.abspath(mei)))
            == os.path.normcase(os.path.dirname(os.path.abspath(sys.executable))))


def pids_filhos(pid_pai=None):
    """PIDs dos processos cujo pai é `pid_pai` (por padrão, este processo).

    Usa o snapshot Toolhelp32 da API do Windows por `ctypes` — sem dependência
    nova e sem abrir processo auxiliar. As alternativas óbvias não servem
    aqui: `psutil` não está instalado, `wmic` foi removido do Windows 11, e
    `tasklist` não informa o processo pai.

    Devolve [] em qualquer falha, e fora do Windows.
    """
    if os.name != "nt":
        return []
    try:
        import ctypes
        from ctypes import wintypes

        TH32CS_SNAPPROCESS = 0x00000002
        INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

        class PROCESSENTRY32(ctypes.Structure):
            _fields_ = [
                ("dwSize", wintypes.DWORD),
                ("cntUsage", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                ("th32ModuleID", wintypes.DWORD),
                ("cntThreads", wintypes.DWORD),
                ("th32ParentProcessID", wintypes.DWORD),
                ("pcPriClassBase", ctypes.c_long),
                ("dwFlags", wintypes.DWORD),
                ("szExeFile", ctypes.c_char * 260),
            ]

        k32 = ctypes.windll.kernel32
        snapshot = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if snapshot == INVALID_HANDLE_VALUE:
            return []
        alvo = os.getpid() if pid_pai is None else pid_pai
        achados = []
        try:
            entrada = PROCESSENTRY32()
            entrada.dwSize = ctypes.sizeof(PROCESSENTRY32)
            ok = k32.Process32First(snapshot, ctypes.byref(entrada))
            while ok:
                if entrada.th32ParentProcessID == alvo:
                    achados.append(entrada.th32ProcessID)
                ok = k32.Process32Next(snapshot, ctypes.byref(entrada))
        finally:
            k32.CloseHandle(snapshot)
        return achados
    except Exception:
        return []


def encerrar_processos_filhos():
    """Encerra os processos que ESTE app iniciou — na prática o `flet.exe`,
    que desenha a interface.

    Por que importa: em onefile o bootloader do PyInstaller apaga o
    `%TEMP%\\_MEIxxxxx` quando o app termina, mas o `flet.exe` roda DE DENTRO
    dessa pasta e mantém arquivos abertos. Como a atualização encerra o
    processo com `os._exit(0)`, o filho sobrevivia, a pasta ficava travada e a
    limpeza falhava com "Failed to remove temporary directory" (o aviso que
    apareceu na tela do usuário). Sobraram 32 dessas pastas, 428 MB, nesta
    máquina.

    Mata cada filho individualmente, NUNCA a própria árvore: o `.bat` que faz
    a troca também é filho deste processo, e um `taskkill /T` no próprio PID
    levaria justamente ele junto — a atualização morreria antes de acontecer.
    Por isso esta função é chamada ANTES de o `.bat` ser criado.

    Melhor-esforço: falhar aqui não pode impedir a atualização de seguir.
    """
    for filho in pids_filhos():
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(filho)],
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                timeout=5,
                capture_output=True,
            )
        except Exception:
            pass


# Trecho de .bat, reaproveitado pelos dois scripts de troca: espera o processo
# indicado sumir da tasklist.
def _espera_pid(pid):
    return (
        ":wait\n"
        f'tasklist /FI "PID eq {pid}" | find "{pid}" >nul\n'
        "if not errorlevel 1 (\n"
        "    timeout /t 1 /nobreak >nul\n"
        "    goto wait\n"
        ")\n"
    )


def build_swap_script(pid, new_exe_path, current_exe_path, falha_log=FALHA_LOG):
    """Gera o .bat que espera este processo (PID) encerrar, substitui o .exe
    antigo pelo novo, relança o app e se autodeleta. Função pura, para ser
    testável sem tocar disco nem processo real.

    Duas correções sobre a 1ª versão, ambas de falha real observada em
    2026-09-11 (o app estava aberto, a troca não aconteceu e o usuário seguiu
    na versão antiga sem saber):

    - **Tenta de novo.** O Windows trava o .exe em execução; se sobrou outra
      instância aberta (ou o antivírus está com o arquivo na mão), o primeiro
      `move` falha. Agora são 10 tentativas espaçadas de 2s.
    - **Não falha calado.** Esgotadas as tentativas, escreve o motivo em
      `falha_log` e relança a versão antiga — o app lê esse arquivo ao abrir e
      conta o que aconteceu. Antes, o `move` falhava, o `start` relançava o
      binário velho e nada indicava que a atualização não tinha ocorrido.
    """
    return (
        "@echo off\n"
        + _espera_pid(pid)
        + "set TENTATIVA=0\n"
        ":tentar\n"
        "set /a TENTATIVA+=1\n"
        f'move /Y "{new_exe_path}" "{current_exe_path}" >nul 2>&1\n'
        "if not errorlevel 1 goto ok\n"
        "if %TENTATIVA% GEQ 10 goto falhou\n"
        "timeout /t 2 /nobreak >nul\n"
        "goto tentar\n"
        ":falhou\n"
        f'>"{falha_log}" echo Nao foi possivel substituir o executavel apos 10 tentativas.\n'
        f'>>"{falha_log}" echo Destino: {current_exe_path}\n'
        f'>>"{falha_log}" echo Baixado: {new_exe_path}\n'
        f'>>"{falha_log}" echo Causa provavel: o aplicativo estava aberto em outra janela.\n'
        f'start "" "{current_exe_path}"\n'
        'del "%~f0"\n'
        "exit /b 1\n"
        ":ok\n"
        f'if exist "{falha_log}" del "{falha_log}"\n'
        f'start "" "{current_exe_path}"\n'
        'del "%~f0"\n'
    )


def build_swap_script_dir(pid, new_dir, current_dir, exe_name=EXE_ASSET_NAME,
                          falha_log=FALHA_LOG):
    """Versão onedir da troca: substitui a PASTA da instalação inteira.

    A pasta atual é renomeada antes (não apagada) — se o `move` da nova falhar
    no meio, a antiga ainda está lá para ser restaurada, e o usuário não fica
    sem aplicativo. Só depois que a nova está no lugar a antiga é descartada.
    """
    antiga = f"{current_dir}.anterior_{pid}"
    return (
        "@echo off\n"
        + _espera_pid(pid)
        + "set TENTATIVA=0\n"
        ":tentar\n"
        "set /a TENTATIVA+=1\n"
        f'move /Y "{current_dir}" "{antiga}" >nul 2>&1\n'
        "if not errorlevel 1 goto instalar\n"
        "if %TENTATIVA% GEQ 10 goto falhou\n"
        "timeout /t 2 /nobreak >nul\n"
        "goto tentar\n"
        ":instalar\n"
        f'move /Y "{new_dir}" "{current_dir}" >nul 2>&1\n'
        "if errorlevel 1 goto desfazer\n"
        f'rmdir /s /q "{antiga}"\n'
        f'if exist "{falha_log}" del "{falha_log}"\n'
        f'start "" "{current_dir}\\{exe_name}"\n'
        'del "%~f0"\n'
        "exit /b 0\n"
        ":desfazer\n"
        f'move /Y "{antiga}" "{current_dir}" >nul 2>&1\n'
        f'>"{falha_log}" echo A nova versao nao pode ser instalada; a anterior foi mantida.\n'
        f'>>"{falha_log}" echo Destino: {current_dir}\n'
        f'start "" "{current_dir}\\{exe_name}"\n'
        'del "%~f0"\n'
        "exit /b 1\n"
        ":falhou\n"
        f'>"{falha_log}" echo Nao foi possivel substituir a pasta do aplicativo apos 10 tentativas.\n'
        f'>>"{falha_log}" echo Destino: {current_dir}\n'
        f'>>"{falha_log}" echo Causa provavel: o aplicativo estava aberto em outra janela.\n'
        f'start "" "{current_dir}\\{exe_name}"\n'
        'del "%~f0"\n'
        "exit /b 1\n"
    )


def ler_falha_pendente():
    """Devolve o texto do último fracasso de atualização (e apaga o arquivo),
    ou None. Chamado pela GUI ao abrir."""
    try:
        if not os.path.exists(FALHA_LOG):
            return None
        with open(FALHA_LOG, "r", encoding="utf-8", errors="replace") as f:
            texto = f.read().strip()
        os.remove(FALHA_LOG)
        return texto or None
    except OSError:
        return None


def extrair_zip_para_temp(zip_path):
    """Descompacta o .zip do Release num diretório temporário e devolve o
    caminho da pasta `nfse_converter_gui/` de dentro dele.

    O zip é gerado por `tools/empacota_release.py` com essa pasta na raiz.
    Levanta IOError se o conteúdo não tiver o formato esperado — melhor
    abortar do que instalar uma pasta que não é o aplicativo.
    """
    import zipfile

    destino = tempfile.mkdtemp(prefix="nfse_update_")
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(destino)

    pasta = os.path.join(destino, "nfse_converter_gui")
    if not os.path.isdir(pasta):
        raise IOError("O .zip não contém a pasta 'nfse_converter_gui/' na raiz.")
    if not os.path.exists(os.path.join(pasta, EXE_ASSET_NAME)):
        raise IOError(f"O .zip não contém '{EXE_ASSET_NAME}' dentro da pasta.")
    return pasta


def apply_update_and_restart(baixado, tipo="exe"):
    """Instala a versão baixada e reinicia o app.

    `tipo="exe"`  -> instalação onefile: troca o executável único.
    `tipo="zip"`  -> instalação onedir: troca a PASTA inteira do aplicativo.

    O Windows trava o que está em execução, então a troca só pode acontecer
    DEPOIS que este processo terminar — daí o .bat desanexado que espera o PID
    atual sumir da `tasklist` antes de mexer em qualquer coisa. O processo sai
    por `os._exit` para soltar o lock imediatamente, sem passar por
    finally/atexit (que poderiam travar em cleanup da UI).

    Os filhos são encerrados ANTES de o .bat ser criado — ver
    `encerrar_processos_filhos` para o porquê da ordem.
    """
    if not is_frozen():
        raise RuntimeError(
            "apply_update_and_restart só é válido rodando como .exe empacotado"
        )

    pid = os.getpid()

    if tipo == "zip":
        nova_pasta = extrair_zip_para_temp(baixado)
        pasta_atual = os.path.dirname(os.path.abspath(sys.executable))
        script = build_swap_script_dir(pid, nova_pasta, pasta_atual)
    else:
        script = build_swap_script(pid, baixado, sys.executable)

    encerrar_processos_filhos()

    bat_path = os.path.join(tempfile.gettempdir(), f"nfse_update_{pid}.bat")
    with open(bat_path, "w") as f:
        f.write(script)

    subprocess.Popen(
        ["cmd", "/c", bat_path],
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        close_fds=True,
    )
    os._exit(0)


def download_update_to_temp(release, progress_callback=None):
    """Baixa o asset adequado a ESTA instalação (ver `find_update_asset`) para
    um arquivo temporário. Devolve `(caminho, tipo)`, ou `(None, None)` se o
    Release não tiver um asset compatível."""
    asset, tipo = find_update_asset(release)
    if not asset:
        return None, None
    sufixo = "zip" if tipo == "zip" else "exe"
    dest = os.path.join(
        tempfile.gettempdir(), f"nfse_converter_gui_new_{os.getpid()}.{sufixo}"
    )
    return download_asset(asset, dest, progress_callback=progress_callback), tipo


def limpar_restos_de_updates(idade_minima_horas=24):
    """Remove restos de atualizações anteriores em %TEMP%: os `.bat` de troca
    que não se autodeletaram e os executáveis/zips baixados que nunca foram
    instalados (170 MB cada, no caso dos .exe).

    Só mexe em arquivos com o NOSSO prefixo e mais velhos que
    `idade_minima_horas`, para nunca esbarrar numa atualização em andamento.
    As pastas `_MEI*` do PyInstaller não são tocadas aqui: elas podem ser de
    qualquer aplicativo empacotado, inclusive de outros, e a partir de agora a
    causa da sobra está corrigida (ver `encerrar_processos_filhos`).

    Devolve quantos bytes foram liberados. Melhor-esforço, nunca levanta.
    """
    import time

    liberados = 0
    limite = time.time() - idade_minima_horas * 3600
    tmp = tempfile.gettempdir()
    try:
        nomes = os.listdir(tmp)
    except OSError:
        return 0
    for nome in nomes:
        if not (nome.startswith("nfse_update_") or
                nome.startswith("nfse_converter_gui_new_")):
            continue
        caminho = os.path.join(tmp, nome)
        try:
            if not os.path.isfile(caminho) or os.path.getmtime(caminho) > limite:
                continue
            tamanho = os.path.getsize(caminho)
            os.remove(caminho)
            liberados += tamanho
        except OSError:
            continue
    return liberados
