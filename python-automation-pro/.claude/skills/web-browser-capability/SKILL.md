---
name: web-research-capability
description: Permite ao Analista de Requisitos fazer consultas e leituras de documentações oficiais diretamente na internet para embasamento técnico.
---

# Web Research Capability

Esta skill representa um conjunto conceitual de ferramentas para pesquisa técnica na internet, permitindo buscar e ler documentações oficiais, APIs e RFCs para embasar decisões de requisitos e implementação.

## Operações

* **web_search** — Busca na internet por documentações, APIs, RFCs e regras de negócio atualizadas. Entrada esperada: `query` (a string de busca focada na documentação técnica desejada).
* **fetch_url** — Lê o conteúdo textual bruto de uma URL de documentação específica encontrada na busca. Entrada esperada: `url` (a URL exata da documentação a ser analisada).
