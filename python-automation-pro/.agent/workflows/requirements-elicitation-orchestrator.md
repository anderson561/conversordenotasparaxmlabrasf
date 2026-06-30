# Workflow: Elicitação e Refinamento de Requisitos de Alta Complexidade

## Fase 1: Análise de Contexto Local
1. Varra o repositório atual para entender onde a nova demanda se encaixa na arquitetura existente.
2. Identifique os arquivos que serão impactados direta e indiretamente.

## Fase 2: Pesquisa e Validação Externa (Se aplicável)
1. Se a tarefa envolver padrões de mercado, APIs externas ou bibliotecas específicas, use a skill `web_search` para buscar as documentações oficiais mais recentes.
2. Extraia as regras estritas de payloads, esquemas e limites de requisições dessas fontes.

## Fase 3: Engenharia de Questionamento (Alinhamento com o Usuário)
1. Formule de 3 a 5 perguntas críticas para o usuário sanar ambiguidades antes de documentar (ex: "O que acontece se o token expirar no meio do processo?").

## Fase 4: Geração da Spec Técnica
1. Monte o documento final seguindo à risca a estrutura de `.agent/specs/requirements-elicitation-template.md`.
2. Encaminhe o documento gerado para o Gerente de Projetos (`senior-project-manager.md`) para que ele possa iniciar a delegação da codificação para os desenvolvedores (`dev-craftsmanship-suite`, `php-laravel-devops-pro`, etc.).