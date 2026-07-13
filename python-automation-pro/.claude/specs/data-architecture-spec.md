# 📐 Spec: Critérios Técnicos de Arquitetura de Dados (Data Production Readiness)

Esta especificação dita as regras obrigatórias de qualidade, governança e eficiência que qualquer script ou pipeline estruturado em Python precisa cumprir.

## 1. Padrões de Qualidade de Código e Reprodutibilidade
* **Modularidade:** Lógicas de transformação de dados devem ser desacopladas da lógica de IO (leitura/escrita). Cadernos Jupyter (`.ipynb`) servem apenas para exploração rápida; o código final deve ser extraído para módulos `.py`.
* **Reprodutibilidade:** É obrigatório o isolamento de ambientes. O projeto deve listar explicitamente suas dependências em um arquivo `requirements.txt`, `pyproject.toml` (Poetry) ou `Pixi`.

## 2. Governança e Validação do Schema
* **Check de Integridade:** Nenhum dado pode ser injetado na camada final sem passar por um validador de contrato. Falhas críticas no schema de entrada devem interromper o pipeline (*fail-fast*) imediatamente.
* **Camadas de Dados (Medallion Architecture):** O projeto deve estruturar as saídas simulando as camadas:
  * `Bronze (Raw)`: Dados brutos como foram recebidos.
  * `Silver (Cleaned)`: Dados tipados, limpos e validados.
  * `Gold (Curated)`: Dados agregados prontos para consumo por BI ou Modelos de ML.

## 3. Eficiência de Performance e Escalabilidade
* **Memory Bounds:** Processamentos que rodem localmente não podem estourar a memória RAM disponível. É obrigatório o uso de geradores (*generators*), iteradores ou frameworks de lazy loading se o arquivo de entrada for maior que 50% da RAM livre.
* **No Side-Effects:** Funções de transformação de DataFrames devem retornar cópias modificadas ou novos DataFrames, evitando o uso generalizado de `inplace=True` para prevenir comportamentos imprevisíveis em encadeamentos.

## 🏁 Checklist de Aceitação (Definition of Done)
- [ ] O script executa de ponta a ponta sem loops explícitos nas linhas dos DataFrames.
- [ ] O schema final foi validado e gerou um log de sucesso/falha.
- [ ] Arquivos finais foram salvos usando tipagem explícita e formatos compactados eficazes (como Parquet).
- [ ] Existe documentação inline (docstrings) explicando a regra de negócio por trás de cada agregação complexa.