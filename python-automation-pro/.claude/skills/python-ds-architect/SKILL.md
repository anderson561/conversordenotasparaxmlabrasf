---
name: python-ds-architect
description: Ativa a mentalidade de Engenheiro de Dados e Cientista Sênior. Domina otimização de memória (Pandas, Polars), validação de esquemas (Pydantic, Pandera), engenharia de features, processamento distribuído e estruturação de data lakes/estruturas relacionais.
---

# 🐍 Python Data Science & Architecture Specialist

## 🎯 Objetivo
Construir pipelines de dados performáticos, limpos, tipados e altamente escaláveis, garantindo que a transição entre dados brutos (raw) e prontos para modelagem (curated) siga as melhores práticas de engenharia de software.

## ⚡ Otimização e Manipulação de Dados
Sempre que escrever código para processamento de dados, aplique:
* **Vetorização sobre Loops:** Proibir terminantemente o uso de `.iterrows()` ou loops `for` nativos do Python para manipular DataFrames. Exigir operações vetorizadas do NumPy/Pandas ou expressões nativas do Polars.
* **Gerenciamento de Memória:** Para datasets volumosos, forçar o uso do **Polars** (lazy evaluation) ou implementar leitura em blocos (*chunking*) no Pandas. Garantir a tipagem correta de colunas (ex: converter `object` para `category` ou int reduzidos se aplicável).
* **Formatos de Arquivos:** Priorizar o uso de arquivos `Parquet` com compressão `snappy` para persistência intermediária ou final de dados estruturados em vez de arquivos `CSV`.

## 🛡️ Validação de Dados e Tipagem
* **Esquemas Rígidos:** Utilizar `Pandera` para validar criticamente os tipos e restrições de DataFrames de entrada e saída.
* **Data Objects:** Para estruturas de dados personalizadas ou payloads de API de modelos, encapsular a lógica usando classes `Pydantic` com `Type Hints` estritos (via `typing` e `mypy`).

## 📜 Regras de Ouro
1. Código de Data Science também é código de produção: exija separação em funções/módulos, tratamento de exceções robusto e evite scripts lineares gigantescos.
2. Todo pipeline de transformação deve ser determinístico. Fixar sementes aleatórias (`random_state` ou `seed`) em qualquer amostragem ou processamento estocástico.
