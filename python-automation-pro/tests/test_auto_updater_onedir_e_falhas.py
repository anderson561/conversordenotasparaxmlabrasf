# -*- coding: utf-8 -*-
r"""Atualização automática: formato da instalação (onedir × onefile), troca
com nova tentativa e relato de falha.

Contexto real (2026-09-11). O usuário mandou atualizar; o download terminou, a
tela ficou em "Reiniciando com a nova versão..." e apareceu o aviso "Failed to
remove temporary directory: ...\_MEI42562". Levantamento na máquina dele:

  - `%TEMP%\nfse_update_21636.bat` e `nfse_converter_gui_new_21636.exe`
    (170 MB) ainda lá, e `dist\nfse_converter_gui.exe` com a data do build
    ANTIGO — ou seja, o `move /Y` falhou (o app estava aberto numa segunda
    janela, e o Windows trava o .exe em execução). O script não tinha nova
    tentativa e não reportava nada: relançava o binário velho e pronto.
  - 32 pastas `_MEI*` órfãs, 428 MB, porque `os._exit(0)` não encerrava o
    `flet.exe`, que roda DE DENTRO da pasta extraída e a mantinha travada.
  - A partida do onefile extraía 354 MB em 1228 arquivos A CADA vez; um dos
    `_MEI` parou em 73 MB, extração interrompida no meio.

Daí as três mudanças cobertas aqui: instalação em pasta (onedir) para não
extrair nada, troca que insiste e avisa quando não deu, e encerramento dos
filhos antes de sair.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import auto_updater  # noqa: E402


# --------------------------------------------------------------- formato
def test_is_onedir_false_em_desenvolvimento():
    """Rodando pelo código-fonte não há instalação nenhuma para classificar."""
    assert auto_updater.is_onedir() is False


def test_is_onedir_detecta_pasta_do_app(monkeypatch):
    """Onedir: `_MEIPASS` é o `_internal/` DENTRO da pasta do app, então fica
    ao lado do executável."""
    monkeypatch.setattr(auto_updater.sys, "frozen", True, raising=False)
    monkeypatch.setattr(auto_updater.sys, "executable",
                        r"C:\apps\nfse\nfse_converter_gui.exe", raising=False)
    monkeypatch.setattr(auto_updater.sys, "_MEIPASS",
                        r"C:\apps\nfse\_internal", raising=False)
    assert auto_updater.is_onedir() is True


def test_is_onedir_false_quando_onefile(monkeypatch):
    """Onefile: `_MEIPASS` é o `_MEIxxxxx` sorteado em %TEMP%, longe do .exe."""
    monkeypatch.setattr(auto_updater.sys, "frozen", True, raising=False)
    monkeypatch.setattr(auto_updater.sys, "executable",
                        r"C:\apps\nfse\nfse_converter_gui.exe", raising=False)
    monkeypatch.setattr(auto_updater.sys, "_MEIPASS",
                        r"C:\Users\x\AppData\Local\Temp\_MEI42562", raising=False)
    assert auto_updater.is_onedir() is False


# ------------------------------------------------- escolha do asset
RELEASE_COMPLETO = {
    "assets": [
        {"name": "nfse_converter_gui.exe", "size": 1},
        {"name": "nfse_converter_gui.zip", "size": 2},
    ]
}


def test_instalacao_onedir_baixa_o_zip(monkeypatch):
    monkeypatch.setattr(auto_updater, "is_onedir", lambda: True)
    asset, tipo = auto_updater.find_update_asset(RELEASE_COMPLETO)
    assert tipo == "zip"
    assert asset["name"] == "nfse_converter_gui.zip"


def test_instalacao_onefile_baixa_o_exe(monkeypatch):
    """Quem já está em onefile continua em onefile — os dois assets são
    publicados justamente para ninguém ficar sem caminho de atualização."""
    monkeypatch.setattr(auto_updater, "is_onedir", lambda: False)
    asset, tipo = auto_updater.find_update_asset(RELEASE_COMPLETO)
    assert tipo == "exe"
    assert asset["name"] == "nfse_converter_gui.exe"


def test_onedir_nao_aceita_exe_como_substituto(monkeypatch):
    """Instalar um executável único por cima de uma instalação em pasta
    deixaria a pasta e o .exe em versões diferentes. Melhor não atualizar."""
    monkeypatch.setattr(auto_updater, "is_onedir", lambda: True)
    so_exe = {"assets": [{"name": "nfse_converter_gui.exe", "size": 1}]}
    asset, tipo = auto_updater.find_update_asset(so_exe)
    assert asset is None and tipo is None


def test_release_sem_assets_nao_quebra(monkeypatch):
    monkeypatch.setattr(auto_updater, "is_onedir", lambda: False)
    assert auto_updater.find_update_asset({"assets": []}) == (None, None)


# ------------------------------------------- troca do onefile (com retry)
def test_swap_onefile_tenta_de_novo_antes_de_desistir():
    """O defeito de 2026-09-11: uma única tentativa de `move`. Com o app
    aberto noutra janela o arquivo está travado e a atualização se perdia."""
    script = auto_updater.build_swap_script(
        1234, r"C:\tmp\novo.exe", r"C:\app\atual.exe")
    assert "goto tentar" in script
    assert "TENTATIVA" in script
    assert "GEQ 10" in script


def test_swap_onefile_registra_o_motivo_quando_nao_consegue():
    """E não pode falhar calado: antes, o `move` falhava, o `start` subia o
    binário VELHO e nada avisava que a atualização não tinha acontecido."""
    script = auto_updater.build_swap_script(
        1234, r"C:\tmp\novo.exe", r"C:\app\atual.exe", falha_log=r"C:\tmp\falhou.log")
    assert ":falhou" in script
    assert r"C:\tmp\falhou.log" in script
    assert "aplicativo estava aberto" in script


def test_swap_onefile_limpa_o_log_quando_da_certo():
    """Sucesso apaga um relato antigo — senão o aviso reapareceria na próxima
    abertura, depois de uma atualização que funcionou."""
    script = auto_updater.build_swap_script(
        1234, r"C:\tmp\novo.exe", r"C:\app\atual.exe", falha_log=r"C:\tmp\falhou.log")
    ok = script.split(":ok")[1]
    assert r'del "C:\tmp\falhou.log"' in ok


def test_swap_onefile_mantem_pid_e_caminhos():
    script = auto_updater.build_swap_script(
        1234, r"C:\tmp\novo.exe", r"C:\app\atual.exe")
    assert "1234" in script
    assert r"C:\tmp\novo.exe" in script
    assert r"C:\app\atual.exe" in script


# --------------------------------------------- troca do onedir (pasta)
def test_swap_onedir_renomeia_antes_de_instalar():
    """A pasta atual é RENOMEADA, não apagada: se a instalação da nova falhar
    no meio, a anterior ainda existe para voltar ao lugar."""
    script = auto_updater.build_swap_script_dir(
        99, r"C:\tmp\novo\nfse_converter_gui", r"C:\apps\nfse_converter_gui")
    assert r"C:\apps\nfse_converter_gui.anterior_99" in script
    i_renomeia = script.index(".anterior_99")
    i_instala = script.index(":instalar")
    assert i_renomeia < i_instala


def test_swap_onedir_desfaz_se_a_nova_nao_entrar():
    """Nunca deixar o usuário sem aplicativo."""
    script = auto_updater.build_swap_script_dir(
        99, r"C:\tmp\novo\nfse_converter_gui", r"C:\apps\nfse_converter_gui")
    assert ":desfazer" in script
    desfazer = script.split(":desfazer")[1]
    assert r'move /Y "C:\apps\nfse_converter_gui.anterior_99" "C:\apps\nfse_converter_gui"' in desfazer
    assert "anterior foi mantida" in desfazer


def test_swap_onedir_so_descarta_a_antiga_depois_de_instalar():
    script = auto_updater.build_swap_script_dir(
        99, r"C:\tmp\novo\nfse_converter_gui", r"C:\apps\nfse_converter_gui")
    i_instala = script.index(r'move /Y "C:\tmp\novo\nfse_converter_gui"')
    i_apaga = script.index("rmdir /s /q")
    assert i_instala < i_apaga


def test_swap_onedir_relanca_o_executavel_de_dentro_da_pasta():
    script = auto_updater.build_swap_script_dir(
        99, r"C:\tmp\novo\nfse_converter_gui", r"C:\apps\nfse_converter_gui")
    assert r'"C:\apps\nfse_converter_gui\nfse_converter_gui.exe"' in script


# ------------------------------------------------------- relato de falha
def test_ler_falha_pendente_sem_arquivo_devolve_none(tmp_path, monkeypatch):
    monkeypatch.setattr(auto_updater, "FALHA_LOG", str(tmp_path / "nao_existe.log"))
    assert auto_updater.ler_falha_pendente() is None


def test_ler_falha_pendente_consome_o_arquivo(tmp_path, monkeypatch):
    """Lê UMA vez: o aviso não pode reaparecer a cada abertura do app."""
    log = tmp_path / "falhou.log"
    log.write_text("Nao foi possivel substituir o executavel.\n", encoding="utf-8")
    monkeypatch.setattr(auto_updater, "FALHA_LOG", str(log))
    assert "Nao foi possivel substituir" in auto_updater.ler_falha_pendente()
    assert not log.exists()
    assert auto_updater.ler_falha_pendente() is None


# ------------------------------------------- encerramento dos filhos
def test_pids_filhos_nao_inclui_o_proprio_processo():
    """O `.bat` de troca também é filho deste processo: um `taskkill /T` no
    próprio PID levaria ele junto e a atualização morreria antes de acontecer.
    Por isso se enumera e mata cada filho, nunca a árvore inteira."""
    assert os.getpid() not in auto_updater.pids_filhos()


def test_pids_filhos_de_pid_inexistente_e_vazio():
    assert auto_updater.pids_filhos(pid_pai=0x7FFFFFFF) == []


# ---------------------------------------------------- faxina do %TEMP%
def test_limpeza_remove_restos_antigos(tmp_path, monkeypatch):
    """Um .exe baixado e nunca instalado ocupa mais de 100 MB; havia um de
    170 MB parado no %TEMP% da máquina do usuário."""
    monkeypatch.setattr(auto_updater.tempfile, "gettempdir", lambda: str(tmp_path))
    velho = tmp_path / "nfse_converter_gui_new_21636.exe"
    velho.write_bytes(b"x" * 2048)
    bat = tmp_path / "nfse_update_21636.bat"
    bat.write_text("@echo off", encoding="utf-8")
    antigo = 1000000000  # bem no passado
    os.utime(velho, (antigo, antigo))
    os.utime(bat, (antigo, antigo))

    liberados = auto_updater.limpar_restos_de_updates()

    assert liberados >= 2048
    assert not velho.exists()
    assert not bat.exists()


def test_limpeza_preserva_update_em_andamento(tmp_path, monkeypatch):
    """Arquivo recém-criado pode ser de uma atualização acontecendo AGORA."""
    monkeypatch.setattr(auto_updater.tempfile, "gettempdir", lambda: str(tmp_path))
    agora = tmp_path / "nfse_converter_gui_new_999.exe"
    agora.write_bytes(b"x" * 10)
    auto_updater.limpar_restos_de_updates()
    assert agora.exists()


def test_limpeza_nao_toca_em_arquivos_alheios(tmp_path, monkeypatch):
    """Só o que tem o nosso prefixo. `_MEI*` em especial fica de fora: pode
    ser de qualquer aplicativo empacotado com PyInstaller, não só deste."""
    monkeypatch.setattr(auto_updater.tempfile, "gettempdir", lambda: str(tmp_path))
    alheio = tmp_path / "_MEI123456"
    alheio.mkdir()
    outro = tmp_path / "coisa_de_outro_app.exe"
    outro.write_bytes(b"x")
    os.utime(outro, (1000000000, 1000000000))
    auto_updater.limpar_restos_de_updates()
    assert alheio.exists()
    assert outro.exists()


# ------------------------------------------------------ extração do zip
def test_extrair_zip_recusa_zip_sem_a_pasta_esperada(tmp_path):
    """Instalar o conteúdo de um zip que não é o aplicativo seria pior que
    não atualizar."""
    import zipfile

    z = tmp_path / "errado.zip"
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("outra_coisa/leiame.txt", "nada a ver")
    with pytest.raises(IOError):
        auto_updater.extrair_zip_para_temp(str(z))


def test_extrair_zip_recusa_pasta_sem_o_executavel(tmp_path):
    import zipfile

    z = tmp_path / "incompleto.zip"
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("nfse_converter_gui/_internal/algo.dll", "x")
    with pytest.raises(IOError):
        auto_updater.extrair_zip_para_temp(str(z))


def test_extrair_zip_devolve_a_pasta_do_app(tmp_path):
    import zipfile

    z = tmp_path / "ok.zip"
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("nfse_converter_gui/nfse_converter_gui.exe", "MZ")
        f.writestr("nfse_converter_gui/_internal/algo.dll", "x")
    pasta = auto_updater.extrair_zip_para_temp(str(z))
    assert os.path.basename(pasta) == "nfse_converter_gui"
    assert os.path.exists(os.path.join(pasta, "nfse_converter_gui.exe"))
