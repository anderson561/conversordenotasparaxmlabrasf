---
name: docker-capabilities
description: Habilidades core de Docker para builds multi-stage otimizados, orquestração/redes locais e persistência inteligente de volumes.
---

# Docker Core Skills

## 1. Multi-Stage Builds Avançado
* Capacidade de isolar os ambientes de build (ex: `npm run build`, `composer install`) dos ambientes de execução final, gerando imagens de produção com tamanho reduzido em até 80%.

## 2. Orquestração e Redes Locais
* Configuração de redes isoladas (`bridge`, `overlay`) garantindo que serviços como Nginx, PHP-FPM, Node.js e bancos de dados se comuniquem por nomes de serviço (`hostname`), impedindo colisões de rede com a máquina hospedeira.

## 3. Persistência Inteligente (Volumes)
* Implementação de Bind Mounts performáticos para desenvolvimento em tempo real.
* Configuração de Named Volumes com drivers específicos para persistência segura de bancos de dados (MySQL, PostgreSQL, Redis).
* Uso de truques de sobreposição de volumes para evitar que caches de pacotes (`node_modules`, `vendor`) locais quebrem o container.
