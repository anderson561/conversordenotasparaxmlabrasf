---
description: Conduz o ciclo de sprint Scrum, do planning à gestão de impedimentos e revisão da Definition of Done.
---

# Workflow: Ciclo de Sprint Scrum e Gestão de Impedimentos

## Fase 1: Sprint Planning (Alinhamento Inicial)
1. Leia o arquivo gerado pelo Analista de Requisitos (`.claude/specs/requirements-elicitation-template.md`).
2. Divida os requisitos em tarefas técnicas menores dentro do template `.claude/specs/scrum-sprint-spec-template.md`.
3. Defina qual subagente técnico (`php`, `python`, `js`) receberá cada tarefa.

## Fase 2: Daily Check & Gestão de Impedimentos
1. Inspecione o andamento das tarefas delegadas aos subagentes.
2. Se um subagente falhar nos testes do `testerengine.md` ou encontrar erro de arquitetura, classifique como **Impedimento**.
3. Acione o `xp-coach.md` para ajudar na simplificação ou o `phd-dba-expert.md` se o gargalo for infra/banco de dados.

## Fase 3: Revisão e Definição de Pronto (Definition of Done)
1. Garanta que nenhuma tarefa seja marcada como concluída se não atender ao *Definition of Done* (DoD) estipulado na Spec da Sprint.
2. Repasse o pacote pronto para o Gerente de Projetos para o fechamento formal.
