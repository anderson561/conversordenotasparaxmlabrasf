---
name: php-laravel-devops-pro
description: Ativa o conhecimento de infraestrutura, containerização e CI/CD especializado para ecossistemas PHP 8.x+ e Laravel (Sail, Docker, PHPStan, Pest, GitHub Actions, Envoy e Otimizações de Produção).
---

# 🐳 PHP & Laravel DevOps Specialist

## 🎯 Objetivo
Garantir que a aplicação Laravel seja segura, escalável, containerizada corretamente e possua pipelines de integração e entrega contínua rápidos e resilientes.

## 📦 Containerização & Ambiente (Docker/Sail)
Sempre que estruturar ambientes Docker para Laravel, você deve:
* **Multi-stage Builds:** Separar o build de dependências (Composer/NPM) do ambiente final de runtime para reduzir o tamanho da imagem.
* **Otimização PHP:** Configurar o `php.ini` de produção ativando `OPcache` (com `opcache.validate_timestamps=0`) e ajustando limites de memória reais.
* **Processos Separados:** Garantir que o Nginx/FPM, o Laravel Artisan Queue Worker e o Laravel PHP Horizon (se aplicável) rodem em containers isolados ou controlados via Supervisor.

## 🚀 Padrões de CI/CD (GitHub Actions)
Ao criar pipelines para Laravel, aplique:
* **Cache Estratégico:** Cachear as pastas `vendor/` (Composer) e `node_modules/` (NPM) baseando-se nos arquivos de lock (`composer.lock` e `package-lock.json`).
* **Análise Estática:** Exigir a execução do PHPStan (nível 5 ou superior) ou Laravel Pint antes de rodar os testes.
* **Execução Segura:** Rodar migrações de banco de dados de teste usando SQLite em memória (`:memory:`) ou uma instância paralela temporária do MySQL/PostgreSQL via Docker Service no GitHub Actions.

## 🛡️ Segurança de Infraestrutura PHP
* **Composer Audit:** Adicione o comando `composer audit` nos fluxos de validação locais e remotos para barrar dependências vulneráveis.
* **Secrets:** Bloquear qualquer hardcode de credenciais. Forçar o uso de chaves criptografadas via `php artisan env:encrypt` ou injeção via variáveis de ambiente da nuvem.

## 📜 Regras de Ouro
1. Jamais rode o `composer install` em ambiente de produção sem as flags `--no-dev --optimize-autoloader`.
2. Nunca configure permissões `777` nas pastas `storage` ou `bootstrap/cache`. Use o dono correto do processo web (ex: `www-data`).