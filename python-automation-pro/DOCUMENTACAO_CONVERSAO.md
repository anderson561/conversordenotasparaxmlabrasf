# Documentação de Conversão — Conversor NFS-e / Contratos ABRASF 2.01

Este documento detalha os layouts e formatos suportados pelo conversor.

---

## Layouts de NFS-e Suportados (PDF → XML)

O extrator PDF (`SPPdfExtractor`) conta com um motor de heurística profunda, capaz de ler as disposições textuais do PDF e classificar dinamicamente qual regra de negócio aplicar.

### 1. Cuiabá/MT — `cuiaba_issnet`
- **Cabeçalho**: "Prefeitura Municipal de Cuiabá / Nota Fiscal de Serviço Eletrônica - NFS-e"
- **Número da Nota**: Canto superior direito
- **Cód. de Autenticidade**: Abaixo da data de competência (Ex: `E6679FDB0`)
- **Data de Competência**: Rótulo `Data de Competência`
- **Entidades**: Blocos "Dados do Prestador de Serviço" e "Dados do Tomador de Serviços"
- **Cidade/UF**: Rótulo `Cidade/UF` (Ex: `Lauro de Freitas/ BA`)

### 2. Barreiras/BA — `barreiras`
- **Cabeçalho**: "MUNICIPIO DE BARREIRAS"
- **Data de Competência**: Baseia-se no rótulo `Data Fato Gerador` ou através do recorte do Mês/Ano diretamente na **Chave de Acesso Nacional** (quando há falha estrutural de OCR nas datas).

### 3. Camaçari/BA — `camacari`
- **Sistema**: CPqD - Gestão Pública
- **Data de Competência**: Rótulo `Data da prestação do serviço`

### 4. Salvador/BA — `salvador` (Nota Salvador)
- **Cabeçalho**: "PREFEITURA MUNICIPAL DO SALVADOR" ou "NOTA SALVADOR"
- **Código de Verificação**: Extração suportada
- **Número da Nota**: Extração nativa com fallback defensivo para o Nome do Arquivo caso o layout sofra extrema degradação na exportação PDF.

### 5. SSF Locação / Localiza — `localiza`
- Focado na importação de faturas de locação e revenda de serviços genéricos veiculares.
- Identificado pelos rótulos "SSF LOCAÇÃO" ou "LOCALIZA".

### 6. Portal Nacional DANFSe — `nacional`
- **Cabeçalho**: "DANFSe v1.0", "Documento Auxiliar da NFS-e"
- **Competência**: Rótulos `Competência da NFS-e` (aceita `MM/YYYY` e `DD/MM/YYYY`) com regra de prioridade sobre a *Data/Hora da Emissão* em caso de conflitos.
- **Entidades**: Suporte avançado a extração segmentada para **Prestador**, **Tomador** e **Intermediário do Serviço**, isolando perfeitamente seus respectivos CNPJs e controlando contaminações cruzadas quando campos vêm indicados como "NÃO IDENTIFICADO".

### 7. Genérico — `generico`
Fallback para layouts de prefeituras ainda não mapeadas. Usa heurísticas universais de busca de tags de XML padrão ABRASF.

---

## 🚀 Escalabilidade e Adição de Novos Layouts

O **Conversor NFS-e** foi projetado seguindo o padrão de **Design Patterns Orientado a Expressões Regulares (Regex) e Etiquetas (Labels)**, o que significa que o código-fonte **nunca precisa ser reescrito ou quebrado** para adicionar novas prefeituras.

**Para adicionar um novo layout de qualquer cidade do Brasil, o software é infinitamente escalável pelas seguintes características:**
1. **Dicionário de Etiquetas**: Basta adicionar as palavras-chave do novo layout (ex: `"Tomador do Serviço:"`, `"Dados do Cliente:"`) nas listas `_LABELS_TOMADOR` no topo de `pdf_extractor.py`. O sistema automaticamente aprenderá a recortar e isolar aquele bloco.
2. **Métodos Modulares**: Cada metadado (ex: `_extrair_valores`, `_extrair_data`, `_extrair_numero`) utiliza condicionais simples (`if self.layout == 'nova_cidade':`). Você pode plugar a regra regex do novo município em três ou quatro linhas de código sem afetar nenhuma outra cidade já suportada.
3. **Isolamento entre Leitura e Escrita**: O robô de leitura (`pdf_extractor.py`) não conhece o robô de escrita (`abrasf_transformer.py`). Ele apenas preenche um Modelo Pydantic unificado em memória (`Nfse`). Portanto, por mais maluco e fora de padrão que seja o PDF do novo layout, basta ensinar o extractor a colocar os dados naquele Modelo padrão que o XML ABRASF sempre sairá 100% perfeito e idêntico para o seu ERP.

## Mapeamento para XML ABRASF 2.01 (NFS-e)

| Campo PDF | Tag XML ABRASF | Descrição |
| :--- | :--- | :--- |
| Número da Nota Fiscal | `<Numero>` | Número sequencial da nota |
| Cód. de Autenticidade | `<CodigoVerificacao>` | Código para validação no portal |
| Data de Geração | `<DataEmissao>` | Data e hora em formato ISO |
| Data de Competência | `<Competencia>` | Data no formato YYYY-MM-DD |
| CPF/CNPJ | `<CpfCnpj>` | Documento limpo (apenas dígitos) |
| Razão Social | `<RazaoSocial>` | Nome completo da entidade |
| Cidade/UF | `<CodigoMunicipio>` | Convertido para o código IBGE |

---

## Contratos de Locação (Formulário → XML)

Geração de XML ABRASF 2.01 diretamente a partir dos dados digitados na GUI, **sem necessidade de PDF**.

### Mapeamento de papéis

| Parte no Contrato | Tag no XML ABRASF | Motivo |
| :--- | :--- | :--- |
| **Locador** (proprietário do bem) | `<Tomador>` | Recebe o pagamento |
| **Locatário** (usuário do bem) | `<Prestador>` | Declara o serviço |

### Regras automáticas

| Campo | Valor gerado |
| :--- | :--- |
| `<Numero>` | Ano da data de emissão (ex: `2026`) |
| `<Acumulador>` | `916` (fixo) |
| `<CodigoVerificacao>` | `CONTRATO` |
| `<NaturezaOperacao>` | `1` (tributação no município) |
| `<ItemListaServico>` | `0601` padrão (locação de bens móveis — LC 116/2003) |
| `<ValorIss>` | `valor_mensal × aliquota_iss` |
| `<ValorLiquidoNfse>` | `valor_mensal − valor_iss` |

### Arquivo gerado

```
CONTRATO_LOCACAO_<ANO>.xml
```

---

## Processamento de Múltiplas Páginas (PDFs)

O sistema conta com um motor de fatiamento inteligente que suporta:

- **Faturas com múltiplas páginas**: Identifica quando uma fatura continua em páginas subsequentes e agrupa o texto para garantir a extração completa da discriminação dos serviços.
- **Múltiplas faturas por página**: Detecta divisores visuais (como linhas horizontais longas) ou novos cabeçalhos no meio de uma página, separando-os em arquivos XML distintos.
- **Rastreamento de Número**: Usa o número da nota fiscal para decidir se um bloco de texto é uma nova nota ou a continuação da anterior.

---

*Documentação atualizada em: 2026-05-29*
