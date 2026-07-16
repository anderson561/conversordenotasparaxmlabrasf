# Changelog — Feature: Campinas/SP Layout Support

## Data: 2026-07-16

### 📋 Resumo
Adição de suporte nativo ao layout de **NFSe Campinas** (Secretaria Municipal de Finanças de Campinas/SP), validado contra duas notas reais do mesmo emitente. O trabalho revelou que o **mesmo layout** pode chegar em **duas estruturas de texto diferentes** (PDF imagem via OCR × PDF digital via pdfminer), tratadas por parsers de entidade distintos com detecção automática.

### ✨ Mudanças Implementadas

#### 1. Detecção de Layout Campinas/SP
- Nova constante `LAYOUT_CAMPINAS = 'campinas_sp'`.
- Padrões em `_detect_layout()` e `_detect_layout_page()`:
  - "NFSe Campinas"
  - "Prefeitura Municipal Campinas"
  - "Nota Fiscal de Serviços eletrônica de Campinas"

#### 2. Extração de campos
- **Número/Série** (`_extrair_numero`): formato `NNNN/L` (ex.: `1712/E` → `1712`).
- **Item de serviço** (`_extrair_codigo_servico`): LC 116/03 `13.02 - FONOGRAFIA...` → `1302` (sem confundir com o CNAE `5920-1/00`).
- **Discriminação** (`_extrair_discriminacao`): captura o bloco "DESCRIÇÃO DO SERVIÇO PRESTADO (...)".
- **Valores** (`_extrair_valores`): grades "CÁLCULO DO ISSQN" e "VALOR TOTAL"; a **Base de cálculo** é usada como âncora do valor dos serviços (o OCR corrompe o "Valor total", ex.: `700,00` → `00,00`), e o líquido é reconstruído quando a grade vem truncada.
- **Optante do Simples** (`parse`): detecção tolerante a "OPTANTE PELO SIMPLES" e a "OPTANTE"/"SIMPLES NACIONAL" em linhas separadas.

#### 3. Duas estruturas de texto (mesmo layout)
- **`_extrair_entidade_campinas`** — PDF imagem/OCR: grade com vários campos por linha.
- **`_extrair_entidade_campinas_digital`** — PDF digital/pdfminer: tabela de 2 colunas com campos intercalados; regra "a N-ésima ocorrência de cada rótulo pertence à N-ésima entidade" (1ª = prestador, 2ª = tomador).
- **`_split_endereco_campinas`** — helper compartilhado (logradouro/número/complemento/bairro).
- Detecção automática da estrutura pela linha de cabeçalho do CNPJ.

#### 4. IBGE resolver
- Adicionado `"CAMPINAS": "3509502"` em `IBGEResolver.KNOWN_CITIES` (`src/utils/ibge_resolver.py`).

#### 5. Testes Unitários
- Novo arquivo `tests/test_campinas_layout.py` — **13 testes** (9 estrutura OCR + 4 estrutura digital), usando o texto real de cada estrutura como mock (sem dependência de Tesseract em runtime).

#### 6. Documentação
- **DOCUMENTACAO_CONVERSAO.md**: seção do Campinas + reorganização de todos os 25 layouts em grupos, correção de numeração e nota sobre "mesmo layout, duas estruturas de texto".
- **README.md**: lista de layouts atualizada (25), OCR e avisos documentados, guia de "Adicionando um Novo Layout".
- **COMO_USAR_GUI.md**: requisito de OCR para PDFs escaneados esclarecido.

### 🎯 Validação
- ✅ Duas notas reais convertidas ponta a ponta (imagem e digital), XML ABRASF 2.01 válido.
- ✅ Suíte completa: **114 testes** passando, sem regressões nos layouts existentes.

### 📝 Nota de Integração
- Sem breaking changes; adição totalmente retrocompatível.

---

**Branch**: `saas/layout-campinas`
