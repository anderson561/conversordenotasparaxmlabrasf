# Skill: Segundo Cérebro Sincronizado (Obsidian Integration)
# ID: obsidian-memory-sync
# Version: 1.0.0

## Descrição
Capacita o agente a usar o servidor MCP `obsidian-memory` como fonte de verdade de longo prazo para regras de negócio, decisões arquiteturais e histórico de bugs do usuário.

## Protocolo de Ação (Gatilhos Autônomos)

### 1. Pré-Voo (Antes de iniciar qualquer `/goal` ou alteração de código)
* **Ação:** Antes de modificar ou criar arquivos, o agente DEVE rodar uma busca no Obsidian usando termos-chave do projeto (ex: nome do módulo, tabela do banco ou funcionalidade).
* **Objetivo:** Evitar quebrar regras de negócio previamente documentadas pelo usuário.

### 2. Pós-Voo (Após concluir uma tarefa ou resolver um bug complexo)
* **Ação:** Se um bug bizarro foi resolvido ou uma nova arquitetura foi implementada, pergunte discretamente ou crie autonomamente uma nota de "Post-Mortem" ou "Docs" no Obsidian.
* **Formato da Nota:** * Título: `DevLog - [Assunto] - [Data Atual]`
    * Conteúdo: Contexto do problema, Solução aplicada, Arquivos modificados.

### 3. Gestão de Contexto
* Se o usuário disser "lembre-se disso", use a ferramenta `append_note` ou `Notes` imediatamente para salvar o insight no arquivo principal do projeto no Obsidian.

## Restrições
* Não sobrescreva notas inteiras sem usar `read_note` primeiro para garantir que não está apagando anotações manuais do usuário.
* Use Markdown limpo e mantenha o padrão de tags do usuário (ex: `#todo`, `#bug`, `#arquitetura`).