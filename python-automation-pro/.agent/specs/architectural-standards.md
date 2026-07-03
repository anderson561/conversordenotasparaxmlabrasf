# Padrões de Arquitetura de Containers

## Arquivos de Configuração Obrigatórios
Todo projeto conteinerizado complexo deve possuir:
1. `.env.example`: Contendo todas as portas locais e credenciais parametrizadas.
2. `Dockerfile`: Otimizado, utilizando cache de camadas de forma inteligente.
3. `docker-compose.yml`: Utilizando a especificação moderna (sem a tag depreciada `version`).

## Checklist de Validação de Código
Antes de entregar uma configuração Docker, certifique-se de cumprir:
* **Mapeamento de Portas:** Sempre no formato `"PORTA_HOST:PORTA_CONTAINER"`.
* **Logs Limpos:** Configuração de `logging` no compose para evitar estouro de disco por logs infinitos.
* **Healthchecks:** Inclusão de testes de integridade (`healthcheck`) para serviços críticos como bancos de dados, garantindo que o app web só suba quando o banco estiver pronto para receber conexões.