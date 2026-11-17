"""Ordem de leitura DETERMINÍSTICA no pdfminer (`extract_text`/`extract_pages`).

Achado real 2026-11-16 (DANFSe v2.0 nº 3615, NOTALIZE TECNOLOGIA LTDA, Campo
Grande/MS -> NORTE SOLUCOES CONTABEIS, Salvador/BA, "norta notalize.pdf"):
convertida sozinha, num processo novo, a nota saía sempre certa; convertida
DEPOIS de outros PDFs no mesmo processo (rodada sequencial do corpus, lote da
GUI) o `CodigoMunicipio` e o `Cep` do prestador e do tomador saíam TROCADOS
entre si. O estado que vazava entre conversões não era do conversor: era o
ENDEREÇO DE MEMÓRIA dos objetos do pdfminer.

`LTLayoutContainer.group_textboxes` (pdfminer.six) agrupa as caixas de texto
por distância mantendo um heap de tuplas `(skip, dist, id(obj1), id(obj2),
obj1, obj2)`. Quando duas distâncias EMPATAM — o caso de colunas simétricas,
como os dois blocos "Telefone / Código IBGE / CEP" lado a lado da DANFSe v2.0
—, o desempate é `id()`, isto é, o endereço do objeto na memória, que depende
de tudo o que o processo alocou antes. A árvore de grupos muda, e com ela a
ordem em que `extract_text` despeja as caixas: medido no mesmo processo,
40 extrações seguidas da nota nº 3615 deram 23 vezes "5002704 ... 2927408" e
17 vezes a ordem invertida. Os layouts que colhem colunas por ORDINAL
(1ª ocorrência = prestador, 2ª = tomador) herdavam a troca.

A correção troca o `id()` do desempate por um número de sequência estável
(posição da caixa na lista de entrada; grupos novos numerados na ordem em que
são criados). Nada mais muda: distâncias, regra do `isany`, tipo de grupo e
iteração do `Plane` são os do pdfminer. Com isso a mesma página produz
sempre o mesmo texto, em qualquer processo e em qualquer posição do lote.

Aplicado UMA vez, no import de `src.extractors` (idempotente). O corpo é
cópia do `group_textboxes` do pdfminer.six 20260107 (versão do `.venv` e do
build); ao atualizar o pdfminer, conferir se o método original mudou além do
`id()` e rodar `tests/test_pdfminer_ordem_deterministica_entre_pdfs.py`.
"""

import heapq
from typing import List, Sequence, Union, cast

from pdfminer.layout import (
    LAParams,
    LTComponent,
    LTLayoutContainer,
    LTTextBox,
    LTTextBoxVertical,
    LTTextGroup,
    LTTextGroupLRTB,
    LTTextGroupTBRL,
)
from pdfminer.utils import Plane


def _group_textboxes_deterministico(
    self: LTLayoutContainer,
    laparams: LAParams,
    boxes: Sequence[LTTextBox],
) -> List[LTTextGroup]:
    """Cópia de `LTLayoutContainer.group_textboxes` com desempate por
    sequência estável em vez de `id()` (ver docstring do módulo)."""
    ElementT = Union[LTTextBox, LTTextGroup]
    plane: Plane[ElementT] = Plane(self.bbox)

    def dist(obj1: LTComponent, obj2: LTComponent) -> float:
        x0 = min(obj1.x0, obj2.x0)
        y0 = min(obj1.y0, obj2.y0)
        x1 = max(obj1.x1, obj2.x1)
        y1 = max(obj1.y1, obj2.y1)
        return (x1 - x0) * (y1 - y0) - obj1.width * obj1.height - obj2.width * obj2.height

    def isany(obj1: ElementT, obj2: ElementT) -> bool:
        x0 = min(obj1.x0, obj2.x0)
        y0 = min(obj1.y0, obj2.y0)
        x1 = max(obj1.x1, obj2.x1)
        y1 = max(obj1.y1, obj2.y1)
        return bool(set(plane.find((x0, y0, x1, y1))).difference((obj1, obj2)))

    seq = {id(box): i for i, box in enumerate(boxes)}
    proximo = [len(boxes)]

    def chave(obj: ElementT) -> int:
        return seq[id(obj)]

    dists = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            dists.append((False, dist(boxes[i], boxes[j]), i, j, boxes[i], boxes[j]))
    heapq.heapify(dists)

    plane.extend(boxes)
    done = set()
    while dists:
        (skip_isany, d, k1, k2, obj1, obj2) = heapq.heappop(dists)
        if k1 in done or k2 in done:
            continue
        if not skip_isany and isany(obj1, obj2):
            heapq.heappush(dists, (True, d, k1, k2, obj1, obj2))
            continue
        if isinstance(obj1, (LTTextBoxVertical, LTTextGroupTBRL)) or isinstance(
                obj2, (LTTextBoxVertical, LTTextGroupTBRL)):
            group: LTTextGroup = LTTextGroupTBRL([obj1, obj2])
        else:
            group = LTTextGroupLRTB([obj1, obj2])
        plane.remove(obj1)
        plane.remove(obj2)
        done.update([k1, k2])
        # O objeto `group` fica vivo até o fim (está no `plane`/heap), então
        # seu id() não é reaproveitado enquanto esta chave existir.
        seq[id(group)] = kg = proximo[0]
        proximo[0] += 1
        for other in plane:
            heapq.heappush(dists, (False, dist(group, other), kg, chave(other), group, other))
        plane.add(group)
    return [cast(LTTextGroup, g) for g in plane]


def aplicar() -> None:
    """Instala o `group_textboxes` determinístico (idempotente)."""
    if getattr(LTLayoutContainer.group_textboxes, '_deterministico', False):
        return
    _group_textboxes_deterministico._deterministico = True
    LTLayoutContainer.group_textboxes = _group_textboxes_deterministico


aplicar()
