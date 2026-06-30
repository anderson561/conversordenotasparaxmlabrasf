# Workflow: Governança Técnica e Revisão Arquitetural

## Fase 1: Avaliação de Impacto Estrutural
1. Quando uma nova funcionalidade for planejada, faça a varredura do repositório para validar se o design respeita a arquitetura existente.
2. Registre grandes alterações estruturais usando o formato `.agent/specs/architecture-decision-log.md`.

## Fase 2: Revisão de Contrato de APIs e Serviços
1. Valide os contratos de input/output (interfaces, DTOs, Schemas JSON) antes que os desenvolvedores preencham a lógica interna das funções.