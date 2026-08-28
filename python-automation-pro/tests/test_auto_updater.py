import io
import pytest
import requests

from src.utils import auto_updater


class DummyResponse:
    def __init__(self, status_code=200, json_data=None, content_chunks=None, headers=None):
        self.status_code = status_code
        self._json_data = json_data or {}
        self._content_chunks = content_chunks or []
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._json_data

    def iter_content(self, chunk_size=1024):
        for c in self._content_chunks:
            yield c

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_parse_version_tolera_prefixo_v():
    assert auto_updater._parse_version("v1.3.0") == (1, 3, 0)
    assert auto_updater._parse_version("1.3.0") == (1, 3, 0)


def test_is_newer_compara_semver():
    assert auto_updater.is_newer("v1.4.0", "1.3.0") is True
    assert auto_updater.is_newer("v1.3.0", "1.3.0") is False
    assert auto_updater.is_newer("v1.2.9", "1.3.0") is False


def test_check_latest_release_retorna_none_quando_sem_release_publicado(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *a, **k: DummyResponse(status_code=404))
    assert auto_updater.check_latest_release() is None


def test_check_latest_release_retorna_none_quando_ja_atualizado(monkeypatch):
    resp = DummyResponse(json_data={"tag_name": "v1.3.0", "assets": [], "html_url": "x", "body": ""})
    monkeypatch.setattr(requests, "get", lambda *a, **k: resp)
    assert auto_updater.check_latest_release() is None


def test_check_latest_release_retorna_dict_quando_ha_versao_nova(monkeypatch):
    resp = DummyResponse(json_data={
        "tag_name": "v1.9.9",
        "assets": [{"name": "nfse_converter_gui.exe", "browser_download_url": "http://x/exe", "size": 100}],
        "html_url": "http://release",
        "body": "notas",
    })
    monkeypatch.setattr(requests, "get", lambda *a, **k: resp)
    release = auto_updater.check_latest_release()
    assert release["version"] == "v1.9.9"
    assert release["url"] == "http://release"
    assert len(release["assets"]) == 1


def test_check_latest_release_retorna_none_em_erro_de_rede(monkeypatch):
    def raise_conn_error(*a, **k):
        raise requests.ConnectionError("sem rede")
    monkeypatch.setattr(requests, "get", raise_conn_error)
    assert auto_updater.check_latest_release() is None


def test_find_exe_asset_prioriza_nome_exato():
    release = {"assets": [
        {"name": "outro.exe"},
        {"name": "nfse_converter_gui.exe"},
    ]}
    asset = auto_updater.find_exe_asset(release)
    assert asset["name"] == "nfse_converter_gui.exe"


def test_find_exe_asset_fallback_primeiro_exe():
    release = {"assets": [{"name": "algumacoisa.exe"}]}
    asset = auto_updater.find_exe_asset(release)
    assert asset["name"] == "algumacoisa.exe"


def test_find_exe_asset_retorna_none_sem_exe():
    release = {"assets": [{"name": "readme.txt"}]}
    assert auto_updater.find_exe_asset(release) is None


def test_download_asset_grava_arquivo_completo(tmp_path, monkeypatch):
    asset = {"browser_download_url": "http://x/exe", "size": 10}
    resp = DummyResponse(content_chunks=[b"12345", b"67890"])
    monkeypatch.setattr(requests, "get", lambda *a, **k: resp)

    dest = tmp_path / "novo.exe"
    progresses = []
    auto_updater.download_asset(asset, str(dest), progress_callback=progresses.append)

    assert dest.read_bytes() == b"1234567890"
    assert progresses[-1] == pytest.approx(1.0)


def test_download_asset_levanta_erro_se_truncado(tmp_path, monkeypatch):
    asset = {"browser_download_url": "http://x/exe", "size": 100}
    resp = DummyResponse(content_chunks=[b"1234"])
    monkeypatch.setattr(requests, "get", lambda *a, **k: resp)

    dest = tmp_path / "novo.exe"
    with pytest.raises(IOError):
        auto_updater.download_asset(asset, str(dest))


def test_is_frozen_false_em_ambiente_de_desenvolvimento():
    assert auto_updater.is_frozen() is False


def test_apply_update_and_restart_recusa_fora_do_exe_empacotado():
    with pytest.raises(RuntimeError):
        auto_updater.apply_update_and_restart("qualquer.exe")


def test_build_swap_script_contem_pid_e_caminhos():
    script = auto_updater.build_swap_script(1234, "C:\\tmp\\novo.exe", "C:\\app\\atual.exe")
    assert "1234" in script
    assert "C:\\tmp\\novo.exe" in script
    assert "C:\\app\\atual.exe" in script
    assert "move /Y" in script
