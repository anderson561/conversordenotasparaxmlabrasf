---
name: software-architecture-and-design-inspector
description: Ferramentas para auditar o acoplamento de código, violações de camadas arquiteturais e validação de padrões de projeto.
---

# Software Architecture and Design Inspector

Esta skill representa um conjunto conceitual de ferramentas para inspecionar a saúde arquitetural de um código-fonte, focando em acoplamento excessivo, violações de camadas e desvios de padrões de projeto estabelecidos.

## Operações

* **analyze_code_smells** — Examina arquivos de código-fonte em busca de violações severas de herança, falta de interfaces ou dependências circulares. Entrada esperada: `target_directory` (caminho do diretório a ser inspecionado).
