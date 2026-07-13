# Workflows de Infraestrutura

## Fluxo 1: Diagnóstico de Conexão (ERR_EMPTY_RESPONSE / Connection Refused)
Quando o usuário reportar falha de carregamento no navegador:
1. Inspecionar o status do container (`docker ps` ou via logs do Docker Desktop).
2. Validar a diretiva `ports` no arquivo compose.
3. Verificar se o processo interno do container está escutando na interface correta (`0.0.0.0` em vez de `127.0.0.1`).
4. Propor alteração para uma porta alta não-convencional (ex: `8888`, `9090`).

## Fluxo 2: Criação de Novo Ambiente Dedicado
1. Analisar a stack tecnológica solicitada (PHP, Node, Python, C#, etc).
2. Criar a estrutura base de arquivos declarativos.
3. Instruir o usuário a iniciar o ambiente utilizando a interface do Docker Desktop ou a extensão da IDE, eliminando atritos de linha de comando.