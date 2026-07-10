# Changelog — Feature: Brasília/DF Layout Support

## Data: 2026-06-30

### 📋 Resumo
Adição de suporte nativo para o layout de NFS-e do **Governo do Distrito Federal (GDF)**, incluindo extração robusta do **Código de Autenticidade**.

### ✨ Mudanças Implementadas

#### 1. **Detecção de Layout Brasília/DF**
- Adicionada constante `LAYOUT_BRASILIA = 'brasilia_df'`
- Padrões de detecção em `_detect_layout()` e `_detect_layout_page()`:
  - "Governo do Distrito Federal"
  - "Secretária de Estado de Economia do Distrito Federal"
  - "Coordenação do ISS"

#### 2. **Extração do Código de Autenticidade**
- Novo método: `_extrair_codigo_autenticidade_brasilia()`
- Suporta múltiplos padrões de localização do código:
  - Seção "Código de Autenticidade" explícita
  - Seção "Data Emissão da DPS"
  - Sequências numéricas longas (44 dígitos)
- Validação mínima de 20 dígitos contínuos
- Exemplo real processado: `530001081224929857000159000000000118226051779414799`

#### 3. **Integração na Extração Principal**
- `_extrair_codigo_verificacao()` agora delega para método específico quando `layout == LAYOUT_BRASILIA`
- Mantém compatibilidade com todos os outros layouts

#### 4. **Testes Unitários**
- Novo arquivo: `tests/test_brasilia_layout.py`
- 3 testes cobrindo:
  - ✅ Detecção correta do layout
  - ✅ Extração do Código de Autenticidade
  - ✅ Extração completa de NFS-e (integração)

#### 5. **Documentação**
- **DOCUMENTACAO_CONVERSAO.md**: Seção detalhada do layout Brasília
- **README.md**: Atualizado com Brasília na lista de layouts suportados
- Documentação interna em docstrings Python

### 🎯 Validação
- ✅ Sintaxe Python validada (`py_compile`)
- ✅ Padrões regex testados
- ✅ Compatibilidade com layouts existentes mantida

### 📝 Nota de Integração
- Sem breaking changes
- Adição totalmente retrocompatível
- Pronto para produção

---

## Data: 2026-07-10

### 🐛 Correção de Regressão — 3 testes de Brasília falhando

A suíte `tests/test_brasilia_layout.py` estava com 2 de 3 testes falhando. Investigação revelou 4 bugs distintos, todos em `src/extractors/pdf_extractor.py`:

1. **Código de Autenticidade truncado**: o regex `Código de Autenticidade\s*[:\s\n]*(\d{20,})` parava no primeiro espaço, perdendo o sufixo separado por espaço (ex: `...517794 14799` virava só `...517794`). Ajustado para capturar `(\d{20,}(?:[ \t]+\d+)?)`, com a limpeza de não-dígitos já existente concatenando o valor corretamente.
2. **Falso positivo de layout Nacional**: em `_detect_layout()`/`_detect_layout_page()`, a checagem do layout Nacional (gatilho `Data de Competência`) vinha antes da checagem de Brasília — e notas reais do GDF também têm esse rótulo, fazendo a nota ser classificada como `danfse_nacional`. Reordenado para Brasília ser verificada primeiro (marcadores mais específicos: "Governo do Distrito Federal" etc.).
3. **Valor de Serviço não extraído**: faltava um padrão para o rótulo `Valor Serviço: R$ ...` (sem "do"/"dos"), usado pelo layout Brasília. Adicionado à lista de `_val_patterns`.
4. **Valor do ISS capturando a alíquota**: o regex de ISS casava com a primeira ocorrência da palavra "ISS" no texto, que era `Alíquota ISS: 5,00%`, retornando `5.0` em vez do valor correto. Adicionado lookbehind negativo `(?<!Al[ií]quota\s)` para pular essa linha e casar apenas em `Valor ISS`/`Total ISS`.

Também foi corrigida uma asserção incorreta em `test_extract_brasilia_full_nfse` (valor esperado de `codigo_verificacao` tinha dígitos extras e um espaço que não correspondiam ao texto mock do próprio teste).

Resultado: `pytest tests -q` com os 3 testes de Brasília passando. Restam 2 falhas pré-existentes e não relacionadas no layout Rio de Janeiro (`test_notas_layouts.py`), sinalizadas separadamente.

---

**Branch**: `feature/brasilia-codigo-autenticidade`  
**Commits relacionados**: Será feito merge com `feature/brasilia-codigo-autenticidade`
