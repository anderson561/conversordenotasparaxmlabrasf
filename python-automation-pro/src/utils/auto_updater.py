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
REQUEST_TIMEOUT = 10


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


def build_swap_script(pid, new_exe_path, current_exe_path):
    """Gera o conteúdo do .bat auxiliar que espera este processo (PID)
    encerrar, substitui o .exe antigo pelo novo, relança o app e se
    autodeleta. Extraído como função pura para ser testável sem tocar o
    disco/processo real."""
    return (
        "@echo off\n"
        ":wait\n"
        f'tasklist /FI "PID eq {pid}" | find "{pid}" >nul\n'
        "if not errorlevel 1 (\n"
        "    timeout /t 1 /nobreak >nul\n"
        "    goto wait\n"
        ")\n"
        f'move /Y "{new_exe_path}" "{current_exe_path}" >nul\n'
        f'start "" "{current_exe_path}"\n'
        'del "%~f0"\n'
    )


def apply_update_and_restart(new_exe_path):
    """Substitui o .exe em execução pelo baixado e reinicia o app.

    O Windows trava o .exe em execução, então a troca só pode acontecer
    DEPOIS que este processo terminar — daí o .bat auxiliar desanexado
    que espera o PID atual sumir da `tasklist` antes de mover o arquivo.
    Encerra o processo atual via os._exit para soltar o lock imediatamente
    (sem passar por finally/atexit, que poderiam travar em cleanup da UI).
    """
    if not is_frozen():
        raise RuntimeError(
            "apply_update_and_restart só é válido rodando como .exe empacotado"
        )

    current_exe = sys.executable
    pid = os.getpid()
    bat_path = os.path.join(tempfile.gettempdir(), f"nfse_update_{pid}.bat")

    with open(bat_path, "w") as f:
        f.write(build_swap_script(pid, new_exe_path, current_exe))

    subprocess.Popen(
        ["cmd", "/c", bat_path],
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        close_fds=True,
    )
    os._exit(0)


def download_update_to_temp(release):
    """Localiza o asset .exe do Release e baixa para um arquivo temporário.
    Retorna o caminho baixado, ou None se o Release não tiver asset .exe."""
    asset = find_exe_asset(release)
    if not asset:
        return None
    dest = os.path.join(tempfile.gettempdir(), f"nfse_converter_gui_new_{os.getpid()}.exe")
    return download_asset(asset, dest)
