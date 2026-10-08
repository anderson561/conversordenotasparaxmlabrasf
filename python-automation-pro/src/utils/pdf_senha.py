"""PDFs protegidos por senha de abertura (/Encrypt, senha de usuário).

Princípio: desproteger UMA vez, na entrada, numa cópia temporária — o extrator
(`SPPdfExtractor`) tem dezenas de pontos que abrem o PDF (`pdfminer`,
`pymupdf.open`) e nenhum deles precisa saber de senha: recebem o caminho da
cópia, que mantém EXATAMENTE o mesmo nome-base do original (há lógica que lê o
número da nota do nome do arquivo).

Garantias:
  * a cópia descriptografada de um documento fiscal é apagada sempre
    (`finally`), inclusive quando a conversão levanta exceção;
  * a senha nunca é logada, impressa nem gravada em disco;
  * PDF protegido só por senha de DONO (abre com senha vazia) conta como
    NÃO protegido: segue o fluxo normal, sem cópia.
"""
import os
import shutil
import tempfile
from contextlib import contextmanager
from typing import Dict, Iterable, List, Optional

import pymupdf


class PdfSenhaError(Exception):
    """Base dos erros de senha de PDF (sempre com mensagem não vazia)."""


class PdfProtegidoPorSenhaError(PdfSenhaError):
    def __init__(self, nome: str):
        super().__init__(
            f"O PDF '{nome}' está protegido por senha. "
            "Informe a senha para convertê-lo."
        )


class PdfSenhaIncorretaError(PdfSenhaError):
    def __init__(self, nome: str):
        super().__init__(f"Senha incorreta para o PDF '{nome}'.")


def pdf_protegido(path: str) -> bool:
    """True se o PDF exige senha de ABERTURA. Arquivo ilegível/inexistente ->
    False (o fluxo normal reporta o problema real)."""
    try:
        doc = pymupdf.open(path)
    except Exception:
        return False
    try:
        return bool(doc.needs_pass)
    finally:
        doc.close()


def senha_correta(path: str, senha: str) -> bool:
    """True se `senha` abre o PDF (usado pela GUI para validar cada tentativa)."""
    if not senha:
        return False
    try:
        doc = pymupdf.open(path)
    except Exception:
        return False
    try:
        return bool(doc.authenticate(senha))
    finally:
        doc.close()


def desproteger_para_temporario(path: str, senha: Optional[str]) -> str:
    """Grava uma cópia SEM criptografia de `path` numa pasta temporária nova,
    com o mesmo nome-base, e devolve o caminho. Quem chama é responsável por
    `descartar_temporario(caminho)` (prefira `pdf_desprotegido`, que garante).

    Levanta `PdfProtegidoPorSenhaError` (sem senha) ou `PdfSenhaIncorretaError`.
    """
    nome = os.path.basename(path)
    doc = pymupdf.open(path)
    pasta = None
    try:
        if doc.needs_pass:
            if not senha:
                raise PdfProtegidoPorSenhaError(nome)
            if not doc.authenticate(senha):
                raise PdfSenhaIncorretaError(nome)
        pasta = tempfile.mkdtemp(prefix="nfse_pdf_")
        destino = os.path.join(pasta, nome)
        doc.save(destino, encryption=pymupdf.PDF_ENCRYPT_NONE)
        return destino
    except BaseException:
        if pasta:
            shutil.rmtree(pasta, ignore_errors=True)
        raise
    finally:
        doc.close()


def descartar_temporario(caminho: str) -> None:
    """Apaga a cópia criada por `desproteger_para_temporario` e sua pasta."""
    shutil.rmtree(os.path.dirname(caminho), ignore_errors=True)


@contextmanager
def pdf_desprotegido(path: str, senha: Optional[str] = None):
    """Entrega o caminho a ser lido: o próprio `path` se o PDF não exige senha
    (nenhuma cópia, comportamento idêntico ao anterior) ou uma cópia temporária
    desprotegida, apagada ao sair do bloco — com ou sem exceção."""
    if not pdf_protegido(path):
        yield path
        return
    copia = desproteger_para_temporario(path, senha)
    try:
        yield copia
    finally:
        descartar_temporario(copia)


class ColetorDeSenhas:
    """Estado puro do diálogo de senhas da GUI (sem Flet — testável).

    Percorre os arquivos protegidos um a um: `atual` é o arquivo aguardando
    senha; `tentar(senha)` valida e avança em caso de acerto; `pular()` descarta
    o arquivo atual; `cancelar()` aborta tudo. Senhas só ficam em memória.
    """

    def __init__(self, arquivos_protegidos: Iterable[str], total_arquivos: int = 1):
        self._fila: List[str] = list(arquivos_protegidos)
        self._total_arquivos = total_arquivos
        self.senhas: Dict[str, str] = {}
        self.pulados: List[str] = []
        self.cancelado = False

    @property
    def atual(self) -> Optional[str]:
        if self.cancelado or not self._fila:
            return None
        return self._fila[0]

    @property
    def concluido(self) -> bool:
        return self.cancelado or not self._fila

    @property
    def pode_pular(self) -> bool:
        """Só faz sentido pular quando há mais de um arquivo no processamento."""
        return self._total_arquivos > 1

    def tentar(self, senha: str) -> bool:
        arq = self.atual
        if arq is None or not senha_correta(arq, senha):
            return False
        self.senhas[arq] = senha
        self._fila.pop(0)
        return True

    def pular(self) -> None:
        if self.atual is not None:
            self.pulados.append(self._fila.pop(0))

    def cancelar(self) -> None:
        self.cancelado = True
