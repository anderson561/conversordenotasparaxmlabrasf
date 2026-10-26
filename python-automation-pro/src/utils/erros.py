"""Texto de erro para exibição ao usuário."""


def descrever_erro(ex: BaseException) -> str:
    """Texto seguro para mostrar ao usuário: `str(ex)` ou, se a exceção não
    trouxer mensagem (ex.: `pdfminer.pdfdocument.PDFPasswordIncorrect`, que
    sempre tem `str(ex) == ''`), o nome da classe — nunca uma string vazia
    (a GUI chegou a exibir só "Erro:" por causa disso)."""
    return str(ex).strip() or type(ex).__name__


class NenhumCteOsError(ValueError):
    """Opção "CT-e OS (DACTE OS - Modelo 67)" (`output_format="cteos"`) num
    PDF sem nenhum DACTE OS reconhecido: nada é gerado (nenhum XML vazio) e a
    mensagem diz isso claramente, em vez de converter as NFS-e/NF-e que essa
    opção existe justamente para deixar de fora."""

    def __init__(self, nome_pdf: str = "", paginas_selecionadas: bool = False):
        onde = "nas páginas selecionadas do PDF" if paginas_selecionadas else "no PDF"
        nome = f" '{nome_pdf}'" if nome_pdf else ""
        super().__init__(
            f"Nenhum DACTE OS (Modelo 67) encontrado {onde}{nome}. "
            "Nenhum XML foi gerado: a opção \"CT-e OS (DACTE OS - Modelo 67)\" "
            "converte só CT-e OS; para NFS-e/NF-e escolha o tipo de arquivo correspondente."
        )
