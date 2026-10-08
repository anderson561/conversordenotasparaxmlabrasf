# -*- coding: utf-8 -*-
"""PDF protegido por senha de abertura (/Encrypt): detecção, cópia temporária
desprotegida, mensagens de erro claras (nunca vazias), `run_conversion`/batch
com `password`, CLI `--password` e o estado puro do diálogo de senhas da GUI.

Origem: PDF real de convênio (AMIL) protegido por senha mostrava só "Erro:" na
GUI porque `pdfminer.PDFPasswordIncorrect` tem `str(ex) == ''`. Não há PDF
protegido real utilizável (privado, senha desconhecida): os PDFs daqui são
GERADOS com pymupdf a partir do texto de uma nota real já coberta pelo projeto
(fatura de locação CPE, em `tests/test_cpe_layout.py`) e protegidos com
RC4-128 (mesmo esquema /V 2 /R 3 do arquivo real).
"""
import glob
import os
import re
import subprocess
import sys
import tempfile

import pymupdf
import pytest

import src.main as main
from src.main import run_batch_conversion, run_conversion
from src.utils.erros import descrever_erro
from src.utils.pdf_senha import (
    ColetorDeSenhas,
    PdfProtegidoPorSenhaError,
    PdfSenhaError,
    PdfSenhaIncorretaError,
    desproteger_para_temporario,
    pdf_desprotegido,
    pdf_protegido,
    senha_correta,
)

SENHA = "Senha-De-Teste-9137"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _texto_nota_real() -> str:
    """Texto da nota real usada em tests/test_cpe_layout.py (fatura de locação CPE)."""
    fonte = open(os.path.join(RAIZ, "tests", "test_cpe_layout.py"), encoding="utf-8").read()
    bloco = re.search(r'mock_text = """(.*?)"""', fonte, re.S).group(1)
    return "\n".join(l.strip() for l in bloco.splitlines())


def _gerar_pdf(destino: str, user_pw: str = None, owner_pw: str = None) -> str:
    doc = pymupdf.open()
    pagina = doc.new_page()
    y = 40
    for linha in _texto_nota_real().splitlines():
        pagina.insert_text((40, y), linha, fontsize=9)
        y += 12
    if user_pw is None and owner_pw is None:
        doc.save(destino)
    else:
        doc.save(destino, encryption=pymupdf.PDF_ENCRYPT_RC4_128,
                 user_pw=user_pw or "", owner_pw=owner_pw or "dono-xyz")
    doc.close()
    return destino


@pytest.fixture
def pdf_aberto(tmp_path):
    return _gerar_pdf(str(tmp_path / "nota_cpe.pdf"))


@pytest.fixture
def pdf_com_senha(tmp_path):
    pasta = tmp_path / "prot"
    pasta.mkdir()
    return _gerar_pdf(str(pasta / "nota_cpe.pdf"), user_pw=SENHA)


@pytest.fixture
def temp_isolado(tmp_path, monkeypatch):
    """Redireciona o diretório temporário para uma pasta do teste, para provar
    que nada sobra lá depois."""
    pasta = tmp_path / "tmp_nfse"
    pasta.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(pasta))
    return pasta


# ------------------------------- detecção -------------------------------

def test_deteccao_aberto_protegido_e_so_senha_de_dono(tmp_path, pdf_aberto, pdf_com_senha):
    so_dono = _gerar_pdf(str(tmp_path / "so_dono.pdf"), user_pw="", owner_pw="somente-dono")
    assert pdf_protegido(pdf_aberto) is False
    assert pdf_protegido(pdf_com_senha) is True
    # senha só de DONO abre com senha vazia: não é "protegido" para o conversor
    assert pdf_protegido(so_dono) is False
    # e segue convertível normalmente, sem cópia
    with pdf_desprotegido(so_dono) as caminho:
        assert caminho == so_dono


def test_deteccao_arquivo_inexistente_ou_corrompido_nao_levanta(tmp_path):
    lixo = tmp_path / "lixo.pdf"
    lixo.write_bytes(b"isto nao e um pdf")
    assert pdf_protegido(str(lixo)) is False
    assert pdf_protegido(str(tmp_path / "nao_existe.pdf")) is False


def test_senha_correta(pdf_com_senha):
    assert senha_correta(pdf_com_senha, SENHA) is True
    assert senha_correta(pdf_com_senha, "errada") is False
    assert senha_correta(pdf_com_senha, "") is False


# ------------------------- cópia temporária / erros -------------------------

def test_sem_senha_levanta_erro_claro_e_nao_vazio(pdf_com_senha, temp_isolado):
    with pytest.raises(PdfProtegidoPorSenhaError) as ex:
        desproteger_para_temporario(pdf_com_senha, None)
    assert str(ex.value) == (
        "O PDF 'nota_cpe.pdf' está protegido por senha. Informe a senha para convertê-lo."
    )
    assert list(temp_isolado.iterdir()) == []   # nada sobrou no disco


def test_senha_errada_levanta_erro_claro_e_nao_vazio(pdf_com_senha, temp_isolado):
    with pytest.raises(PdfSenhaIncorretaError) as ex:
        desproteger_para_temporario(pdf_com_senha, "errada")
    assert str(ex.value) == "Senha incorreta para o PDF 'nota_cpe.pdf'."
    assert list(temp_isolado.iterdir()) == []


def test_erros_de_senha_tem_base_comum_e_texto_nunca_vazio():
    for erro in (PdfProtegidoPorSenhaError("a.pdf"), PdfSenhaIncorretaError("a.pdf")):
        assert isinstance(erro, PdfSenhaError)
        assert str(erro).strip()


def test_copia_mantem_nome_base_e_e_apagada_ao_sair(pdf_com_senha, temp_isolado):
    with pdf_desprotegido(pdf_com_senha, SENHA) as caminho:
        assert os.path.basename(caminho) == os.path.basename(pdf_com_senha)
        assert os.path.dirname(caminho) != os.path.dirname(pdf_com_senha)
        assert os.path.exists(caminho)
        assert pdf_protegido(caminho) is False       # a cópia abre sem senha
        doc = pymupdf.open(caminho)
        assert not doc.is_encrypted and "FATURA DE LOCA" in doc[0].get_text()
        doc.close()
    assert not os.path.exists(caminho)
    assert list(temp_isolado.iterdir()) == []


def test_copia_e_apagada_mesmo_com_excecao_no_bloco(pdf_com_senha, temp_isolado):
    capturado = {}
    with pytest.raises(RuntimeError):
        with pdf_desprotegido(pdf_com_senha, SENHA) as caminho:
            capturado["c"] = caminho
            assert os.path.exists(caminho)
            raise RuntimeError("falha durante a conversão")
    assert not os.path.exists(capturado["c"])
    assert list(temp_isolado.iterdir()) == []


def test_pdf_nao_protegido_nao_gera_copia(pdf_aberto, temp_isolado):
    with pdf_desprotegido(pdf_aberto, None) as caminho:
        assert caminho == pdf_aberto
        assert list(temp_isolado.iterdir()) == []


def test_senha_nao_aparece_em_stdout_stderr_nem_logs(pdf_com_senha, tmp_path, capsys, caplog, temp_isolado):
    caplog.set_level("DEBUG")
    saida = str(tmp_path / "out" / "x.xml")
    run_conversion(pdf_com_senha, saida, password=SENHA)
    with pytest.raises(PdfSenhaIncorretaError):
        run_conversion(pdf_com_senha, saida, password=SENHA + "x")
    capturado = capsys.readouterr()
    assert SENHA not in capturado.out and SENHA not in capturado.err
    assert SENHA not in caplog.text
    # nem no XML gerado
    for xml in glob.glob(os.path.join(tmp_path, "out", "*.xml")):
        assert SENHA not in open(xml, encoding="utf-8").read()


# --------------------------- run_conversion (E2E) ---------------------------

def _xmls(pasta) -> dict:
    return {os.path.basename(f): open(f, encoding="utf-8").read()
            for f in glob.glob(os.path.join(str(pasta), "*.xml"))}


def test_run_conversion_protegido_gera_xml_identico_ao_do_pdf_aberto(tmp_path, pdf_aberto, pdf_com_senha, temp_isolado):
    run_conversion(pdf_aberto, str(tmp_path / "a" / "saida.xml"))
    run_conversion(pdf_com_senha, str(tmp_path / "b" / "saida.xml"), password=SENHA)
    a, b = _xmls(tmp_path / "a"), _xmls(tmp_path / "b")
    assert a and a.keys() == b.keys()          # mesmo nome de arquivo => número da nota preservado
    assert a == b                              # conteúdo idêntico
    assert list(temp_isolado.iterdir()) == []


def test_run_conversion_sem_senha_ou_errada_da_erro_claro_e_nao_gera_xml(tmp_path, pdf_com_senha, temp_isolado):
    saida = str(tmp_path / "o" / "x.xml")
    with pytest.raises(PdfProtegidoPorSenhaError, match="protegido por senha"):
        run_conversion(pdf_com_senha, saida)
    with pytest.raises(PdfSenhaIncorretaError, match="Senha incorreta"):
        run_conversion(pdf_com_senha, saida, password="errada")
    assert _xmls(tmp_path / "o") == {}
    assert list(temp_isolado.iterdir()) == []


def test_run_conversion_apaga_copia_quando_o_parse_falha(tmp_path, pdf_com_senha, temp_isolado, monkeypatch):
    def _boom(self):
        assert os.path.exists(self.pdf_path)       # leu da cópia, não do original criptografado
        assert os.path.basename(self.pdf_path) == "nota_cpe.pdf"
        raise RuntimeError("falha no parse")
    monkeypatch.setattr(main.SPPdfExtractor, "parse_multiple", _boom)
    with pytest.raises(RuntimeError):
        run_conversion(pdf_com_senha, str(tmp_path / "o" / "x.xml"), password=SENHA)
    assert list(temp_isolado.iterdir()) == []


# ------------------------------- batch -------------------------------

def test_batch_pdf_protegido_sem_senha_falha_so_ele(tmp_path, pdf_aberto, capsys, temp_isolado):
    entrada = tmp_path / "lote"
    entrada.mkdir()
    _gerar_pdf(str(entrada / "aberto.pdf"))
    _gerar_pdf(str(entrada / "trancado.pdf"), user_pw=SENHA)
    avisos = []
    run_batch_conversion(str(entrada), str(tmp_path / "saida"),
                         progress_callback=lambda p, m: avisos.append(m))
    xmls = _xmls(tmp_path / "saida")
    assert len(xmls) == 1 and next(iter(xmls)).startswith("aberto_")
    out = capsys.readouterr().out
    assert "Falha ao processar trancado.pdf: O PDF 'trancado.pdf' está protegido por senha" in out
    assert "PDFs com Falha Total: 1" in out
    assert any(m.startswith("[ERRO] trancado.pdf: O PDF 'trancado.pdf' está protegido") for m in avisos)
    assert list(temp_isolado.iterdir()) == []


def test_batch_com_password_unico_e_com_dict_por_arquivo(tmp_path, capsys, temp_isolado):
    entrada = tmp_path / "lote"
    entrada.mkdir()
    a = _gerar_pdf(str(entrada / "aberto.pdf"))
    b = _gerar_pdf(str(entrada / "trancado_b.pdf"), user_pw=SENHA)
    c = _gerar_pdf(str(entrada / "trancado_c.pdf"), user_pw="outra-senha")
    run_batch_conversion(str(entrada), str(tmp_path / "s1"), password=SENHA)
    out = capsys.readouterr().out
    assert len(_xmls(tmp_path / "s1")) == 2          # aberto + trancado_b; trancado_c (outra senha) falha
    assert "Senha incorreta para o PDF 'trancado_c.pdf'." in out
    # GUI: dict caminho -> senha por arquivo
    run_batch_conversion(pdf_files=[a, b, c], output_dir=str(tmp_path / "s2"),
                         senhas={b: SENHA, c: "outra-senha"})
    assert len(_xmls(tmp_path / "s2")) == 3
    assert list(temp_isolado.iterdir()) == []


# --------------------------------- CLI ---------------------------------

def _cli(*args):
    return subprocess.run(
        [sys.executable, os.path.join(RAIZ, "app.py"), *args],
        cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )


def test_cli_input_com_password_certo_errado_e_ausente(tmp_path, pdf_aberto, pdf_com_senha):
    ok = _cli("--input", pdf_com_senha, "--output", str(tmp_path / "ok" / "x.xml"), "--password", SENHA)
    assert ok.returncode == 0, ok.stderr
    assert SENHA not in ok.stdout + ok.stderr
    ref = _cli("--input", pdf_aberto, "--output", str(tmp_path / "ref" / "x.xml"))
    assert ref.returncode == 0, ref.stderr
    assert _xmls(tmp_path / "ok") == _xmls(tmp_path / "ref") != {}

    errada = _cli("--input", pdf_com_senha, "--output", str(tmp_path / "e1" / "x.xml"), "--password", "errada")
    assert errada.returncode != 0
    assert "Senha incorreta para o PDF 'nota_cpe.pdf'." in errada.stderr
    assert "Traceback" not in errada.stderr

    ausente = _cli("--input", pdf_com_senha, "--output", str(tmp_path / "e2" / "x.xml"))
    assert ausente.returncode != 0
    assert "protegido por senha" in ausente.stderr and "Traceback" not in ausente.stderr
    assert _xmls(tmp_path / "e1") == {} and _xmls(tmp_path / "e2") == {}


def test_cli_batch_misto_converte_os_demais(tmp_path):
    entrada = tmp_path / "lote"
    entrada.mkdir()
    _gerar_pdf(str(entrada / "aberto.pdf"))
    _gerar_pdf(str(entrada / "trancado.pdf"), user_pw=SENHA)
    sem = _cli("--batch", str(entrada), "--output", str(tmp_path / "s1"))
    assert sem.returncode == 0
    assert len(_xmls(tmp_path / "s1")) == 1
    assert "Falha ao processar trancado.pdf" in sem.stdout and "protegido por senha" in sem.stdout
    com = _cli("--batch", str(entrada), "--output", str(tmp_path / "s2"), "--password", SENHA)
    assert com.returncode == 0 and len(_xmls(tmp_path / "s2")) == 2
    assert SENHA not in com.stdout + com.stderr


def test_cli_ajuda_documenta_password_e_avisa_do_risco():
    ajuda = _cli("--help").stdout
    assert "--password" in ajuda
    assert "histórico" in " ".join(ajuda.split())


def test_cli_password_com_contrato_e_rejeitado(tmp_path):
    r = _cli("--contrato", str(tmp_path / "c.json"), "--output", str(tmp_path), "--password", "x")
    assert r.returncode == 2 and "--password" in r.stderr


# --------------------- defesa contra mensagem de erro vazia ---------------------

def test_descrever_erro_nunca_devolve_vazio():
    from pdfminer.pdfdocument import PDFPasswordIncorrect
    assert str(PDFPasswordIncorrect()) == ""            # a causa raiz do "Erro:" em branco
    assert descrever_erro(PDFPasswordIncorrect()) == "PDFPasswordIncorrect"
    assert descrever_erro(ValueError("mensagem")) == "mensagem"
    assert descrever_erro(RuntimeError("   ")) == "RuntimeError"


def test_batch_exception_sem_mensagem_mostra_nome_da_classe(tmp_path, capsys, monkeypatch):
    from pdfminer.pdfdocument import PDFPasswordIncorrect
    aberto = _gerar_pdf(str(tmp_path / "a.pdf"))

    def _boom(self):
        raise PDFPasswordIncorrect()
    monkeypatch.setattr(main.SPPdfExtractor, "parse_multiple", _boom)
    msgs = []
    run_batch_conversion(pdf_files=[aberto], output_dir=str(tmp_path / "o"),
                         progress_callback=lambda p, m: msgs.append(m))
    assert "[ERRO] a.pdf: PDFPasswordIncorrect" in msgs
    assert "Falha ao processar a.pdf: PDFPasswordIncorrect" in capsys.readouterr().out


# ------------------- estado do diálogo de senhas da GUI -------------------

def test_coletor_fluxo_senha_errada_depois_certa(pdf_com_senha):
    c = ColetorDeSenhas([pdf_com_senha], total_arquivos=1)
    assert c.atual == pdf_com_senha and not c.concluido
    assert c.pode_pular is False                      # um arquivo só: sem "Pular"
    assert c.tentar("errada") is False and c.atual == pdf_com_senha   # permite novas tentativas
    assert c.tentar("") is False
    assert c.tentar(SENHA) is True
    assert c.atual is None and c.concluido and not c.cancelado
    assert c.senhas == {pdf_com_senha: SENHA} and c.pulados == []


def test_coletor_lote_pular_e_cancelar(tmp_path):
    p1 = _gerar_pdf(str(tmp_path / "um.pdf"), user_pw="s1")
    p2 = _gerar_pdf(str(tmp_path / "dois.pdf"), user_pw="s2")
    p3 = _gerar_pdf(str(tmp_path / "tres.pdf"), user_pw="s3")
    c = ColetorDeSenhas([p1, p2, p3], total_arquivos=5)
    assert c.pode_pular is True
    assert c.tentar("s1") is True and c.atual == p2
    c.pular()
    assert c.pulados == [p2] and c.atual == p3
    assert c.tentar("s2") is False                    # senha do arquivo anterior não vale
    c.cancelar()
    assert c.cancelado and c.concluido and c.atual is None
    assert c.senhas == {p1: "s1"}


def test_gui_importa_sem_quebrar():
    import gui_app
    assert callable(gui_app.main)
