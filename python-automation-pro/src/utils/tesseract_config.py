"""Resolução do executável do Tesseract OCR (um único lugar para o app todo).

Ordem de resolução:

1. Variável de ambiente ``TESSERACT_CMD`` — caminho completo do
   ``tesseract.exe``, para instalações fora do local padrão. Se ela apontar
   para um arquivo que não existe, é ignorada (segue para o próximo passo).
2. Caminho padrão do instalador Windows:
   ``C:\\Program Files\\Tesseract-OCR\\tesseract.exe``.
3. ``tesseract`` no PATH — o padrão do próprio ``pytesseract``, usado quando
   nenhum dos anteriores existe (``tesseract_cmd`` não é alterado).

A pasta de idiomas (tessdata) não é configurada aqui: o próprio Tesseract lê
a variável de ambiente ``TESSDATA_PREFIX`` quando ela está definida.
"""
import os

ENV_TESSERACT_CMD = "TESSERACT_CMD"
CAMINHO_PADRAO_TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def resolver_tesseract_cmd():
    """Devolve o caminho do executável a usar, ou ``None`` para deixar o
    ``pytesseract`` procurar ``tesseract`` no PATH."""
    do_ambiente = os.environ.get(ENV_TESSERACT_CMD, "").strip().strip('"')
    if do_ambiente and os.path.isfile(do_ambiente):
        return do_ambiente
    if os.path.exists(CAMINHO_PADRAO_TESSERACT):
        return CAMINHO_PADRAO_TESSERACT
    return None


def configurar_pytesseract(pytesseract_mod):
    """Aplica a resolução acima ao módulo ``pytesseract`` recebido. Sem
    caminho resolvido, não mexe em ``tesseract_cmd`` (fica o PATH)."""
    caminho = resolver_tesseract_cmd()
    if caminho:
        pytesseract_mod.pytesseract.tesseract_cmd = caminho
    return caminho
