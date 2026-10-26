# -*- coding: utf-8 -*-
"""Lógica pura da janela de seleção de notas da GUI quando VÁRIOS PDFs são
convertidos de uma vez (sem Flet aqui, para ser testável).

Fluxo na GUI (`gui_app.py`): cada PDF é pré-analisado (`SPPdfExtractor.parse_multiple`
+ `separar_por_formato`) e vira um `AnaliseArquivo`. Se ao menos um PDF tiver
mais de uma nota válida, a GUI mostra UMA janela com as notas agrupadas por
arquivo; a escolha do usuário (conjunto de `(caminho, pagina)`) vira o mapa
`paginas_por_arquivo` repassado a `run_batch_conversion`, que mantém o MESMO
padrão de nomes de XML do lote (`<pdf>_Pagina_<p>_NF_<n>.xml`).
"""
from dataclasses import dataclass, field
import os
from typing import Dict, Iterable, List, Optional, Tuple

ALTURA_MIN_DIALOGO = 160
ALTURA_MAX_DIALOGO = 480
LARGURA_DIALOGO = 460


@dataclass
class AnaliseArquivo:
    """Resultado da pré-análise de um PDF.

    `notas`: lista de `(pagina_origem, numero)` das notas válidas (já filtradas
    pelo formato de saída). `erro`: mensagem se a pré-análise falhou — nesse
    caso o arquivo é convertido inteiro, sem seleção."""
    caminho: str
    notas: List[Tuple[Optional[int], str]] = field(default_factory=list)
    erro: Optional[str] = None

    @property
    def nome(self) -> str:
        return os.path.basename(self.caminho)

    @property
    def selecionavel(self) -> bool:
        """Entra na janela (tem ao menos uma nota e foi analisado sem erro)."""
        return self.erro is None and len(self.notas) >= 1


def analise_de_notas(caminho: str, nfse_list) -> AnaliseArquivo:
    """Monta a análise a partir das notas já extraídas e filtradas pelo formato."""
    return AnaliseArquivo(
        caminho=caminho,
        notas=[(getattr(n, "pagina_origem", None), str(getattr(n, "numero", ""))) for n in nfse_list],
    )


def deve_mostrar_dialogo(analises: Iterable[AnaliseArquivo]) -> bool:
    """A janela só aparece se ao menos um PDF tiver mais de uma nota válida;
    senão o lote segue direto (comportamento anterior)."""
    return any(a.erro is None and len(a.notas) > 1 for a in analises)


def rotulo_nota(pagina, numero) -> str:
    return f"Página {pagina} — Nota {numero}"


def montar_grupos(analises: Iterable[AnaliseArquivo]):
    """Grupos da janela, um por arquivo selecionável, na ordem recebida.

    Retorna lista de dicts `{"titulo", "caminho", "itens"}`; cada item é
    `{"rotulo", "data": (caminho, pagina), "marcado"}`. Arquivos com uma
    única nota já vêm marcados; os com várias, desmarcados."""
    grupos = []
    for a in analises:
        if not a.selecionavel:
            continue
        marcado = len(a.notas) == 1
        grupos.append({
            "titulo": a.nome,
            "caminho": a.caminho,
            "itens": [
                {"rotulo": rotulo_nota(p, n), "data": (a.caminho, p), "marcado": marcado}
                for p, n in a.notas
            ],
        })
    return grupos


def nao_selecionaveis(analises: Iterable[AnaliseArquivo]) -> List[AnaliseArquivo]:
    """Arquivos fora da janela (pré-análise falhou ou nenhuma nota): são
    convertidos inteiros, como no lote — o próprio lote loga IGNORADO/ERRO."""
    return [a for a in analises if not a.selecionavel]


def montar_paginas_por_arquivo(
    arquivos: List[str],
    analises: Iterable[AnaliseArquivo],
    marcados: Iterable[Tuple[str, Optional[int]]],
):
    """Converte a escolha da janela no que o lote precisa.

    Retorna `(pdf_files, paginas_por_arquivo, ignorados)`:
    - `pdf_files`: arquivos a converter, na ordem original;
    - `paginas_por_arquivo`: caminho -> lista ordenada das páginas marcadas
      (arquivos não selecionáveis ficam FORA do mapa = converter todas);
    - `ignorados`: arquivos selecionáveis sem nenhuma página marcada."""
    por_caminho = {a.caminho: a for a in analises}
    escolhidas: Dict[str, set] = {}
    for caminho, pagina in marcados:
        escolhidas.setdefault(caminho, set()).add(pagina)

    pdf_files, mapa, ignorados = [], {}, []
    for caminho in arquivos:
        analise = por_caminho.get(caminho)
        if analise is None or not analise.selecionavel:
            pdf_files.append(caminho)
            continue
        paginas = escolhidas.get(caminho)
        if not paginas:
            ignorados.append(caminho)
            continue
        pdf_files.append(caminho)
        mapa[caminho] = sorted(paginas, key=lambda p: (p is None, p or 0))
    return pdf_files, mapa, ignorados


def altura_dialogo(analises: Iterable[AnaliseArquivo]) -> int:
    """Altura SEMPRE explícita (com piso e teto) do conteúdo da janela:
    `height=None` dentro de um `AlertDialog` colapsa o diálogo no Flet
    desktop (achado 2026-09-16). Escala por total de linhas (títulos de
    arquivo + uma por nota); acima do teto, a Column rola."""
    grupos = montar_grupos(analises)
    linhas = sum(1 + len(g["itens"]) for g in grupos)
    return min(ALTURA_MAX_DIALOGO, max(ALTURA_MIN_DIALOGO, 110 + 36 * linhas))


def nome_xml_lote(nome_pdf: str, pagina, numero) -> str:
    """Nome do XML gerado pelo lote — padrão importado pelo usuário no Domínio,
    NÃO mudar: `<pdf sem extensão>[_Pagina_<p>]_NF_<numero>.xml`."""
    base = nome_pdf.rsplit('.', 1)[0]
    pag_str = f"_Pagina_{pagina}" if pagina else ""
    return f"{base}{pag_str}_NF_{numero}.xml"
