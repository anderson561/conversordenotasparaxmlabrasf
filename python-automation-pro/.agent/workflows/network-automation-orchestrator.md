---
name: network-automation-orchestrator
description: Orienta o agente no design, desenvolvimento e validação de scripts ou aplicações Node.js focadas em tarefas de rede.
---

# 🔄 Workflow: Orquestração de Ferramentas e Automação de Redes

Este fluxo orienta o agente no design, desenvolvimento e validação de scripts ou aplicações Node.js focadas em tarefas de rede (como port scanners, coletores SNMP, clientes SSH ou APIs de monitoramento de tráfego).

## 📋 Fase 1: Mapeamento de Protocolo e Requisitos Técnicos
1. Identifique o protocolo alvo da automação (TCP, UDP, HTTP, ICMP, SNMP, SSH).
2. Mapeie as portas de rede padrão envolvidas e os tempos limite máximos permitidos (*timeouts*).
3. Avalie se a tarefa exige privilégios de administrador/root (ex: raw sockets para pacotes ICMP/Ping).

## 🔨 Fase 2: Arquitetura Assíncrona e Engine Concorrente
1. Estruture o motor de conexões usando Promises reaproveitáveis ou Streams.
2. Implemente um controlador de concorrência (ex: uma fila com limite máximo de workers ativos) para evitar inundar o switch ou roteador alvo com requisições (*Denial of Service acidental*).
3. Inicialize as conexões e configure os ouvintes de eventos para capturar estados críticos (`connect`, `data`, `timeout`, `close`, `error`).

## 📥 Fase 3: Processamento e Parsing Binário
1. Capture os buffers de entrada.
2. Se o protocolo possuir cabeçalho de tamanho fixo, leia os bytes exatos necessários usando `buffer.readUInt16BE()` ou métodos equivalentes de Big-Endian/Little-Endian dependendo da RFC do protocolo.
3. Formate os dados brutos extraídos em objetos estruturados JavaScript limpos (JSON) para consumo posterior.

## 🚀 Fase 4: Resiliência, Auditoria e Diagnóstico
1. Implemente uma lógica de reconexão inteligente com recuo exponencial (*exponential backoff*) caso a rede balance.
2. Crie logs de telemetria detalhados contendo: IP de origem, IP de destino, latência da operação (RTT - Round Trip Time) e status final.
3. Exiba um relatório descritivo no terminal sobre a saúde e eficiência do script de rede construído.