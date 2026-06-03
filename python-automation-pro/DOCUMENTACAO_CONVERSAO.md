# Documentação de Conversão — Conversor NFS-e / Contratos ABRASF 2.01

Este documento detalha os layouts e formatos suportados pelo conversor.

---

## Layouts de NFS-e Suportados (PDF → XML)

### 1. Cuiabá/MT — `cuiaba_issnet`

O sistema está calibrado para processar o layout da **Prefeitura Municipal de Cuiabá**:

- **Cabeçalho**: "Prefeitura Municipal de Cuiabá / Nota Fiscal de Serviço Eletrônica - NFS-e"
- **Número da Nota**: Canto superior direito
- **Cód. de Autenticidade**: Abaixo da data de competência (Ex: `E6679FDB0`)
- **Data de Competência**: Rótulo `Data de Competência`
- **Entidades**: Blocos "Dados do Prestador de Serviço" e "Dados do Tomador de Serviços"
- **Cidade/UF**: Rótulo `Cidade/UF` (Ex: `Lauro de Freitas/ BA`)

### 2. Barreiras/BA — `barreiras`

- **Cabeçalho**: "MUNICIPIO DE BARREIRAS"
- **Data de Competência**: Rótulo `Data Fato Gerador`

### 3. Camaçari/BA — `camacari`

- **Sistema**: CPqD - Gestão Pública
- **Data de Competência**: Rótulo `Data da prestação do serviço`

### 4. Portal Nacional DANFSe — `nacional`

- **Cabeçalho**: "DANFSe v1.0" ou "Documento Auxiliar da NFS-e"
- **Competência**: Rótulos `Competência da NFS-e` (aceita `MM/YYYY` e `DD/MM/YYYY`)
- **Prestador**: Aceita seções "Prestador de Serviços", "Prestador do Serviço" e "Fornecedor"

### 5. Genérico — `generico`

Fallback para layouts não identificados. Usa heurísticas de extração geral.

---

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
