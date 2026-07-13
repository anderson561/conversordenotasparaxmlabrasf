---
description: Workflow para mapeamento de jornadas, refinamento de fluxos de telas, auditoria heurística e tradução de requisitos de negócio em componentes estruturados e prontos para front-end.
---

# 🔄 Workflow: Processo de Design de Interface e Experiência

Este fluxo orienta o agente na análise, design e auditoria completa de telas e fluxos de experiência do produto.

## 📋 Fase 1: Descoberta e Mapeamento de Jornada
1. Identifique as personas do usuário e os objetivos de negócio da tela atual.
2. Mapeie o fluxo de tarefas principais (*User Flow*), detalhando o ponto de entrada, decisões do usuário e estados finais de sucesso.
3. Identifique possíveis pontos de fricção no fluxo atual (ex: excesso de cliques, formulários muito longos).

## 📐 Fase 2: Estruturação e Arquitetura de Informação
1. Defina a disposição estrutural dos elementos na tela (Layout e Grids).
2. Organize as sessões por ordem de relevância (*Scannability* e *F-Shaped Pattern*).
3. Determine os principais pontos de chamada para ação (CTAs) e garanta que sua visibilidade e peso visual se destaquem no fluxo.

## 💄 Fase 3: UI Systematization e Componentização
Converta a estrutura em componentes reaproveitáveis usando as melhores práticas de Front-end/Design:
1. **Design Tokens:** Mapeie a paleta de cores (primária, secundária, neutros, alertas) e escala tipográfica.
2. **Estados do Componente:** Defina o visual do componente em repouso, carregando (*skeleton/loading*), com erro, vazio (*empty state*) e ativo.
3. **Responsividade:** Detalhe o comportamento e quebras de layout necessárias para dispositivos móveis (Mobile) e telas grandes (Desktop).

## 🏁 Fase 4: Inspeção, Validação e Handover
1. Conduza uma auditoria nas 10 Heurísticas de Nielsen sobre o resultado final.
2. Verifique o cumprimento de todos os itens da especificação de acessibilidade (WCAG).
3. Entregue um relatório estruturado contendo a especificação visual limpa, pronta para o desenvolvedor Front-end implementar.
