"""DT-12 — o asset baixado só é instalado se o SHA-256 bater com o `digest`
publicado pela API do GitHub ("sha256:<hex>"). Sem rede: requests.get é
substituído por uma resposta falsa.
"""
import hashlib
import os

import pytest
import requests

from src.utils import auto_updater


CONTEUDO = b"conteudo do executavel novo"
SHA_OK = hashlib.sha256(CONTEUDO).hexdigest()


class _Resp:
    def __init__(self, chunks):
        self._chunks = chunks

    def raise_for_status(self):
        pass

    def iter_content(self, chunk_size=1024):
        yield from self._chunks

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _release(digest):
    asset = {
        "name": "nfse_converter_gui.exe",
        "browser_download_url": "http://x/exe",
        "size": len(CONTEUDO),
    }
    if digest is not None:
        asset["digest"] = digest
    return {"version": "v99.0.0", "url": "https://github.com/o/r/releases/tag/v99.0.0",
            "assets": [asset]}


@pytest.fixture
def ambiente(tmp_path, monkeypatch):
    """Instalação onefile, %TEMP% isolado e download falso contando chamadas."""
    chamadas = []

    def fake_get(*a, **k):
        chamadas.append(a)
        return _Resp([CONTEUDO[:10], CONTEUDO[10:]])

    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(auto_updater, "is_onedir", lambda: False)
    monkeypatch.setattr(auto_updater.tempfile, "gettempdir", lambda: str(tmp_path))
    return tmp_path, chamadas


def test_digest_confere_devolve_arquivo_para_instalar(ambiente):
    tmp, _ = ambiente
    dest, tipo = auto_updater.download_update_to_temp(_release(f"sha256:{SHA_OK}"))
    assert tipo == "exe"
    assert os.path.dirname(dest) == str(tmp)
    with open(dest, "rb") as f:
        assert f.read() == CONTEUDO


def test_digest_em_maiusculas_tambem_confere(ambiente):
    dest, _ = auto_updater.download_update_to_temp(_release(f"sha256:{SHA_OK.upper()}"))
    assert os.path.exists(dest)


def test_digest_divergente_apaga_arquivo_e_nao_instala(ambiente):
    tmp, _ = ambiente
    with pytest.raises(auto_updater.IntegridadeError) as exc:
        auto_updater.download_update_to_temp(_release("sha256:" + "0" * 64))
    msg = str(exc.value)
    assert "não confere" in msg
    assert "Nada foi instalado" in msg
    assert "releases/tag/v99.0.0" in msg
    assert os.listdir(tmp) == []


def test_asset_sem_digest_nao_baixa_e_orienta_download_manual(ambiente):
    tmp, chamadas = ambiente
    with pytest.raises(auto_updater.IntegridadeError) as exc:
        auto_updater.download_update_to_temp(_release(None))
    msg = str(exc.value)
    assert "SHA-256" in msg
    assert "manualmente" in msg
    assert "releases/tag/v99.0.0" in msg
    assert chamadas == []
    assert os.listdir(tmp) == []


@pytest.mark.parametrize("digest", ["", "sha1:" + "a" * 40, "sha256:xyz", "sha256:" + "a" * 63])
def test_digest_malformado_e_tratado_como_ausente(ambiente, digest):
    _, chamadas = ambiente
    with pytest.raises(auto_updater.IntegridadeError):
        auto_updater.download_update_to_temp(_release(digest))
    assert chamadas == []


def test_integridade_error_e_ioerror():
    # A GUI captura Exception e mostra a mensagem; IOError mantém o contrato
    # das demais falhas de download.
    assert issubclass(auto_updater.IntegridadeError, IOError)


def test_sha256_esperado_extrai_hex():
    assert auto_updater.sha256_esperado({"digest": f"sha256:{SHA_OK}"}) == SHA_OK
    assert auto_updater.sha256_esperado({}) is None
