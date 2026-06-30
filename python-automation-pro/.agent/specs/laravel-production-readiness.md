# 📐 Spec: Critérios de Prontidão para Produção (Laravel Production Readiness)

Esta especificação define o padrão mínimo obrigatório de arquitetura e infraestrutura que o código produzido por este agente precisa atingir antes de ser considerado "Pronto para Produção".

## 1. Requisitos de Configuração do Framework (Laravel App)
* **APP_DEBUG:** Deve ser estritamente `false` em ambientes que não sejam locais.
* **APP_ENV:** Deve ser explicitamente configurado como `production`.
* **Drivers de Alta Performance:** O cache e a sessão não devem usar o driver `file`. Devem ser configurados para usar `redis` ou `database`.

## 2. Padrões de Docker para PHP-FPM
* **Imagem Base:** Utilizar imagens oficiais baseadas em Alpine Linux (`php:8.x-fpm-alpine`) para redução de vulnerabilidades e tamanho de disco.
* **User Privileges:** O container não deve rodar comandos internos como `root`. Deve mapear o usuário para o grupo `www-data` (id 82 no Alpine).

## 3. Segurança de Dados e Infraestrutura
* **Criptografia:** Todas as rotas expostas no Nginx de produção devem forçar terminação TLS/SSL (HTTPS).
* **Logs:** O log da aplicação (`LOG_CHANNEL`) deve ser configurado para `stack` direcionando para `syslog` ou `stderr`, permitindo que coletores de log (como Promtail, Fluentd ou AWS CloudWatch) capturem os outputs do container.
* **Rate Limiting:** Todas as rotas de API devem implementar o middleware `throttle` nativo do Laravel para evitar ataques de força bruta ou negação de serviço (DoS).

## 4. Validação de Sucesso
O agente considerará a tarefa concluída apenas se o projeto passar no seguinte checklist:
- [ ] Nenhum dump de depuração (`dd()`, `dump()`, `print_r()`) foi deixado no código.
- [ ] O comando `php artisan config:cache` executa sem lançar exceções (indica que nenhuma função `env()` foi usada fora dos arquivos da pasta `config/`).
- [ ] Os testes de integração cobrem pelo menos 80% das rotas de escrita.