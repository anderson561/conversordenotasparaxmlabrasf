---
name: infrastructure-and-security-auditor
description: Ferramentas para gerar automações de infraestrutura, revisar configurações Docker e simular testes de estresse/carga.
---

# Infrastructure and Security Auditor

Esta skill representa um conjunto conceitual de ferramentas para automatizar a geração de infraestrutura como código, revisar configurações de containers e apoiar simulações de testes de estresse/carga.

## Operações

* **generate_pipeline_config** — Gera arquivos YAML estruturados para CI/CD (GitHub Actions, GitLab CI) baseados no ecossistema do projeto. Entrada esperada: `pipeline_type` (o tipo de arquivo de infra a gerar, ex.: `github_actions` ou `docker_compose`).
