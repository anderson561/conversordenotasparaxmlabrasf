---
name: xp-refactoring-tools
description: Habilidades técnicas para monitorar a saúde do código, complexidade de software e execução automatizada de testes locais.
---

# XP Refactoring and Metrics Capability

Esta skill representa um conjunto conceitual de ferramentas para práticas de Extreme Programming (XP), cobrindo execução automatizada de testes e análise de complexidade de código para apoiar o ciclo de refatoração contínua.

## Operações

* **run_test_suite** — Executa de forma rápida os testes locais baseados na stack detectada (pytest, phpunit, jest) para validar o ciclo TDD. Entrada esperada: `environment` (o ambiente do projeto atual detectado: `python`, `javascript` ou `php`).
* **check_code_complexity** — Analisa o arquivo indicado em busca de complexidade ciclomática alta, métodos muito longos ou violações de YAGNI. Entrada esperada: `file_path` (o caminho relativo do arquivo a ser inspecionado).
