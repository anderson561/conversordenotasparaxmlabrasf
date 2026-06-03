# 🔄 Workflow: Orquestração de Pipeline de Dados (ETL/ELT)

Este fluxo orienta o agente no design e na implementação passo a passo de um pipeline de estruturação, limpeza e preparação de dados.

## 📊 Fase 1: Ingestão e Inspeção Quantitativa
1. Identifique as fontes de dados (bancos relacionais, APIs, CSVs, arquivos Parquet ou JSON).
2. Escreva um script de inspeção inicial para gerar um relatório do ecossistema de dados:
   * Contagem total de linhas e colunas.
   * Porcentagem de valores nulos/ausentes por coluna.
   * Detecção de tipos de dados inconsistentes (ex: datas salvas como strings).

## 🧽 Fase 2: Validação e Higienização (Sanitization)
1. Crie uma camada isolada de limpeza (`cleansing`).
2. Defina o contrato de validação usando `Pandera` ou `Pydantic`.
3. Trate os valores nulos com base na regra de negócio informada (remoção, inputação pela mediana, ou flag específica).
4. Aplique a padronização de strings (remover espaços extras, aplicar caixa baixa, tratar caracteres especiais em nomes de colunas).

## 🏗️ Fase 3: Estruturação, Engenharia de Features e Agregação
1. Execute as transformações analíticas necessárias:
   * Junções (*merges/joins*) garantindo que os tipos das chaves sejam idênticos.
   * Criação de novas variáveis (Engenharia de Features) de forma totalmente vetorizada.
   * Agregações e agrupamentos (*group by*) para consolidar métricas de negócio.

## 💾 Fase 4: Persistência e Log de Execução
1. Salve o output final na estrutura de destino respeitando a Spec técnica (ex: partilhamento por data em formato Parquet).
2. Escreva uma rotina de log que registre o tempo de execução de cada fase, o volume de dados trafegado e possíveis anomalias encontradas.