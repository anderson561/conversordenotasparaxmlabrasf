# Workflow: Ciclo Iterativo e Refatoração Extrema (XP)

## Fase 1: Varredura de Simplicidade e Testes
1. Execute a análise do projeto e mapeie o estado atual da cobertura de testes.
2. Identifique os pontos críticos que violam as regras de "Design Simples".

## Fase 2: Ciclo TDD Estrito (Orquestração de Código)
1. Antes de autorizar a escrita da lógica de negócio, oriente o subagente (`tddmaster.md` ou o dev da linguagem) a criar a suite de testes que falha (`Red`).
2. Com os testes falhando, comande a escrita do código mínimo necessário para fazer os testes passarem (`Green`).
3. Dispare imediatamente o gatilho de **Refatoração Implacável** (`Refactor`): remova duplicidades, melhore nomes de variáveis e simplifique estruturas sem quebrar os testes.

## Fase 3: Parceria e Code Review de Par (Pair Programming Simulado)
1. Atue como o "Navegador" enquanto o executor técnico atua como o "Piloto".
2. Verifique se o executor seguiu a risca a especificação em `.agent/specs/xp-engineering-spec-template.md`.

## Fase 4: Integração Local Segura
1. Acione o motor de testes correspondente (`testerengine.md`) para garantir estabilidade e regressão zero.