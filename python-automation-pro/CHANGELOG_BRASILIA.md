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

**Branch**: `feature/brasilia-codigo-autenticidade`  
**Commits relacionados**: Será feito merge com `feature/brasilia-codigo-autenticidade`
