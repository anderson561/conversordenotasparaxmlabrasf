---
description: Executa a auditoria de segurança e dependências do projeto e blinda o ambiente de infraestrutura antes do deploy.
---

# Workflow: Validação de Confiabilidade e Orquestração de Deploy

## Fase 1: Auditoria de Segurança e Dependências
1. Varra os arquivos de configuração do projeto (`package.json`, `composer.json`, `requirements.txt`) procurando por bibliotecas desatualizadas ou vulneráveis.

## Fase 2: Blindagem de Ambiente
1. Crie ou otimize as receitas de infraestrutura seguindo o template `.claude/specs/infrastructure-reliability-spec.md`.
2. Garanta que o `qa-automation-expert.md` tenha os ganchos de automação integrados nos pipelines criados por você.
