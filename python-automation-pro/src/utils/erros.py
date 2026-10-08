"""Texto de erro para exibição ao usuário."""


def descrever_erro(ex: BaseException) -> str:
    """Texto seguro para mostrar ao usuário: `str(ex)` ou, se a exceção não
    trouxer mensagem (ex.: `pdfminer.pdfdocument.PDFPasswordIncorrect`, que
    sempre tem `str(ex) == ''`), o nome da classe — nunca uma string vazia
    (a GUI chegou a exibir só "Erro:" por causa disso)."""
    return str(ex).strip() or type(ex).__name__
