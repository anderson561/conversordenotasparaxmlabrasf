---
name: dev-craftsmanship-suite
description: Ativa diretrizes de excelência em Engenharia de Software. Foca em TDD (Test-Driven Development), Padrões de Projeto (Design Patterns), Documentação técnica (C4 Model/Swagger) e fluxos avançados de GitHub/CI-CD.
---

# 🛠️ Software Craftsmanship & Architecture

## 🎯 Objetivo
Transformar código funcional em software de nível corporativo. Você deve garantir que cada linha de código siga princípios de manutenibilidade, escalabilidade e clareza técnica.

## 🔴 Ciclo TDD (Red-Green-Refactor)
Ao desenvolver novas funcionalidades, você deve seguir e propor o fluxo:
1.  **RED:** Escreva um teste que falha para a funcionalidade desejada.
2.  **GREEN:** Implemente o código mínimo necessário para fazer o teste passar.
3.  **REFACTOR:** Refatore o código seguindo os padrões de design, removendo duplicidade e melhorando a legibilidade, garantindo que os testes continuem passando.

## 🏛️ Padrões de Projeto & SOLID
Aplique padrões de projeto clássicos (GoF) adaptados para Python:
* **Strategy:** Para alternar entre diferentes provedores de Proxy ou Scrapers.
* **Factory:** Para criação dinâmica de instâncias de drivers ou parsers.
* **Singleton/Borg:** Para gerenciamento de configurações globais.
* **SOLID:** Garanta o *Single Responsibility* (classes pequenas) e *Dependency Inversion* (dependa de abstrações, não de implementações).

## 📝 Documentação de Alta Fidelidade
O código não está pronto se não houver documentação. Exija e gere:
* **Docstrings:** Padrão Google ou NumPy em todas as funções.
* **README.md:** Deve conter: Stack Tecnológica, Instruções de Setup (Docker/Poetry), Arquitetura do Sistema e Guia de Contribuição.
* **Diagramas Mermaid:** Gere diagramas de sequência e de classe dentro do Markdown para explicar fluxos complexos.
* **API Docs:** Se houver interface web, utilize FastAPI com Swagger/OpenAPI.

## 🐙 GitHub & Workflow Profissional
Siga os padrões de elite do GitHub:
* **Conventional Commits:** `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`.
* **Pull Request Templates:** Crie templates que exijam a descrição da mudança, evidências de testes e checklist de qualidade.
* **GitHub Actions (CI/CD):** * Pipeline de Linting (Ruff/Black).
    * Pipeline de Testes Automáticos (Pytest com cobertura).
    * Segurança: Scan de segredos e vulnerabilidades (Bandit/Safety).

## 🗂️ Estrutura de Projeto Sugerida
```text
project-name/
├── .github/workflows/  # CI/CD pipelines
├── docs/               # Documentação detalhada e diagramas
├── src/                # Código fonte (módulos limpos)
├── tests/              # Suíte de testes (unitários, integrados)
├── pyproject.toml      # Gestão de dependências (Poetry/uv)
└── README.md           # Porta de entrada do projeto