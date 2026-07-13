---
name: scrum-flow-and-impediment-capability
description: Habilidades para auditar o fluxo de trabalho dos agentes, mapear a velocidade de entrega e gerar relatórios de status da sprint.
---

# Scrum Flow and Impediment Capability

Esta skill representa um conjunto conceitual de ferramentas para acompanhar o fluxo de trabalho ágil, auditar o backlog da sprint e reportar impedimentos técnicos ao Gerente de Projetos.

## Operações

* **audit_sprint_backlog** — Varre o arquivo de spec da sprint atual para atualizar o status das tarefas pendentes, em andamento e concluídas. Entrada esperada: `sprint_spec_path` (o caminho do arquivo de spec da sprint atual).
* **generate_impediment_report** — Cria uma seção estruturada detalhando falhas de compilação, testes quebrados ou lentidão de queries para o Gerente de Projetos. Entrada esperada: `blocker_description` (a descrição técnica do que está travando o desenvolvimento).
