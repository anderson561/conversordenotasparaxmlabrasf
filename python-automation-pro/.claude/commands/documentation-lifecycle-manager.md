---
description: Workflow passo a passo para auditoria de código, extração de contexto técnico e geração estruturada de artefatos de documentação (README, APIs, ADRs).
---

# 🔄 Workflow: Ciclo de Vida da Documentação Técnica

Este fluxo orienta o agente na análise de repositórios e na geração de documentações precisas e padronizadas.

## 📋 Fase 1: Descoberta e Extração de Contexto
1. Analise os arquivos principais do projeto (ex: `package.json`, `composer.json`, `requirements.txt` ou `docker-compose.yml`) para entender o stack tecnológico e dependências.
2. Leia as rotas e controladores para mapear os endpoints disponíveis, caso seja uma API.
3. Identifique o público-alvo da documentação solicitada (desenvolvedores internos, clientes externos ou usuários finais).

## 🏗️ Fase 2: Estruturação do Esqueleto (Drafting)
Dependendo do artefato solicitado, monte a estrutura base:
* **Para README.md:** Título, Badges, Descrição Curta, Pré-requisitos, Instalação, Configuração (.env), Como Executar, Execução de Testes e Licença.
* **Para API:** Autenticação, Base URL, Endpoints (Método, Rota, Parâmetros, Headers, Body) e Respostas (Sucesso e Erro).
* **Para ADR (Architecture Decision Record):** Título, Status, Contexto, Decisão, Consequências (Positivas e Negativas).

## ✍️ Fase 3: Preenchimento e Formatação
1. Escreva o conteúdo utilizando Markdown rico (tabelas para variáveis de ambiente, blocos delimitados para código).
2. Adicione exemplos de requisição e resposta usando dados fictícios (mock), mas verossímeis.
3. Se houver links para outras partes da documentação ou arquivos internos do repositório, garanta que os caminhos relativos estejam corretos.

## 🔍 Fase 4: Revisão de Qualidade
1. Revise o texto buscando jargões desnecessários ou ambiguidades.
2. Certifique-se de que os passos de instalação são sequenciais e que nenhum comando essencial foi pulado.
3. Entregue o artefato final formatado ao usuário.
