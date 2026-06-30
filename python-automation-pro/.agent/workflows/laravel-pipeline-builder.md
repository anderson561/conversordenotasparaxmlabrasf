---
name: laravel-pipeline-builder
description: Orienta o agente na criação ou auditoria completa de uma infraestrutura de deploy do zero para aplicações Laravel.
---

# 🔄 Workflow: Construção de Pipeline de Implantação Laravel

Este workflow orienta o agente na criação ou auditoria completa de uma infraestrutura de deploy do zero para aplicações Laravel.

## 📋 Fase 1: Diagnóstico de Ambiente
1. Analise o arquivo `composer.json` para verificar a versão do PHP e pacotes instalados.
2. Verifique o arquivo `.env.example` para mapear todas as dependências de infraestrutura necessárias (Redis, MySQL, SQS, etc.).
3. Cheque se já existe um arquivo `Dockerfile`, `docker-compose.yml` ou configuração de Laravel Sail.

## 🔨 Fase 2: Configuração e Geração do Pipeline (CI)
Crie um arquivo de workflow do GitHub Actions (`.github/workflows/ci.yml`) que execute rigidamente os seguintes passos nesta ordem:
1. **Setup PHP:** Instalar a versão correta do PHP com as extensões necessárias (`mbstring`, `openssl`, `pdo`, `xml`, `zip`, `bcmath`).
2. **Dependency Resolution:** Rodar `composer install --prefer-dist --no-progress`.
3. **Code Quality:** Executar o linter/formatador (`./vendor/bin/pint --test` ou PHPStan).
4. **Test Suite:** Executar os testes automatizados com PHPUnit ou Pest em modo paralelo se suportado.

## 🚀 Fase 3: Estrutura de Deploy (CD)
Se o usuário solicitar deploy automatizado, configure um fluxo baseado em SSH seguro (via Laravel Envoy ou GitHub Action SSH) que execute na máquina de destino:
1. `git pull origin main`
2. `composer install --no-dev --optimize-autoloader`
3. `php artisan down --refresh=15` (Coloca a aplicação em modo de manutenção de forma segura)
4. `php artisan migrate --force` (Executa migrações críticas de banco de dados)
5. `php artisan config:cache`, `php artisan route:cache`, `php artisan view:cache` (Ativa cache de alta performance)
6. `php artisan up` (Traz a aplicação de volta ao ar)
7. `php artisan queue:restart` (Reinicia os workers para lerem o código novo)

## 🏁 Fase 4: Relatório de Entrega
Apresente ao usuário os arquivos criados e forneça um resumo descritivo de quais secrets precisam ser adicionados ao repositório do GitHub (ex: `SSH_PRIVATE_KEY`, `SERVER_IP`) para o fluxo funcionar.