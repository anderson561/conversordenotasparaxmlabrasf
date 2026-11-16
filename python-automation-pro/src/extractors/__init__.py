# Ordem de leitura determinística do pdfminer ANTES de qualquer extração (ver
# `src/utils/pdfminer_deterministico.py`: sem isso a ordem das caixas de texto
# dependia do endereço de memória dos objetos e variava entre conversões).
from ..utils import pdfminer_deterministico  # noqa: F401
