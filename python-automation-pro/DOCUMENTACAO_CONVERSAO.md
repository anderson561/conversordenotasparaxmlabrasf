# Documentação de Conversão — Conversor NFS-e / Contratos ABRASF 2.01

Este documento detalha os layouts e formatos suportados pelo conversor.

---

## Layouts Suportados (PDF → XML)

O extrator PDF (`SPPdfExtractor`) conta com um motor de heurística profunda, capaz de ler as disposições textuais do PDF e classificar dinamicamente qual regra de negócio aplicar (`_detect_layout` / `_detect_layout_page`). São **25 layouts** ao todo, agrupados abaixo por tipo. PDFs escaneados/imagem (sem texto extraível) passam automaticamente por **OCR** (Tesseract via `pytesseract` + PyMuPDF, `lang='por'`) antes da extração.

> **Nota sobre OCR:** o texto pós-OCR (e às vezes até o de PDF com texto embutido) diverge do que parece "óbvio" na imagem — troca de caracteres, glifos ilegíveis, colunas intercaladas. As regras por layout são propositalmente tolerantes a esses ruídos.

### Prefeituras / NFS-e municipal

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

### 4. Salvador/BA — `salvador_ba` (Nota Salvador)
- **Cabeçalho**: "PREFEITURA MUNICIPAL DO SALVADOR" ou "NOTA SALVADOR" ou "Xique-Xique"
- **Código de Verificação**: Extração de código de autenticidade/verificação.
- **Número da Nota**: Extração nativa com fallback defensivo para o Nome do Arquivo caso o layout sofra extrema degradação.
- **Extração de Município/UF**: Tratamento robusto para remover sufixos de UF como `UF: BA` do nome do município e atualizar o endereço corretamente.

### 5. Feira de Santana/BA — `feira_de_santana`
- **Cabeçalho**: "FEIRA DE SANTANA"
- **Data de Competência**: Busca do campo `Fato Gerador`.

### 6. Rio de Janeiro/RJ — `rio_de_janeiro` (Nota Carioca)
- **Cabeçalho**: "RIO DE JANEIRO" ou "NOTA CARIOCA"
- **Data de Competência**: Busca do campo `Mês de Competência`.

### 7. São Paulo/SP — `sao_paulo_sp`
- **Cabeçalho**: "PREFEITURA DO MUNICÍPIO DE SÃO PAULO"
- **Data de Competência**: Busca do rótulo `Compe:` em formato mes/ano (ex: `Jan/2026`).

### 8. Joinville/SC — `joinville_sc`
- **Cabeçalho**: "Prefeitura de Joinville" ou "NF-em"
- **Data de Competência**: Busca do rótulo `Competência`.

### 9. Fortaleza/CE — `fortaleza_ce`
- **Cabeçalho**: "PREFEITURA MUNICIPAL DE FORTALEZA"
- **Data de Competência**: Busca do rótulo `Competência`.

### 10. Brasília/DF — `brasilia_df`
- **Cabeçalho**: "Governo do Distrito Federal", "Secretária de Estado de Economia do Distrito Federal" ou "Coordenação do ISS"
- **Número da Nota**: Extração do campo `Número da Nota Fiscal` ou equivalente
- **Código de Autenticidade**: Campo específico extraído com padrão de 20-44 dígitos numéricos contínuos
  - Localizado na seção "Código de Autenticidade" ou "Data Emissão da DPS"
  - Exemplo: `5300010812249298570001590000000001182260517794 14799` (após limpeza: `530001081224929857000159000000000118226051779414799`)
- **Data de Competência**: Busca do rótulo `Data de Competência` ou `Data de Geração de NFS-e`
- **Entidades**: Suporte completo a extração de Prestador, Tomador e dados de serviço
- **Status**: ✅ Suportado nativamente

### 11. Simões Filho/BA — `simoes_filho_ba`
- **Cabeçalho**: "Simões Filho"

### 12. Ribeirão Pires/SP — `ribeirao_pires_sp`
- **Cabeçalho**: "Ribeirão Pires"

### 13. Campinas/SP — `campinas_sp` ⭐ **NOVO**
- **Sistema**: NFSe Campinas (Secretaria Municipal de Finanças de Campinas).
- **Detecção**: "NFSe Campinas", "Prefeitura Municipal Campinas" ou "Nota Fiscal de Serviços eletrônica de Campinas".
- **Número/Série**: rótulo `Número / Série`, valor no formato `NNNN/L` (ex.: `1712/E` → `1712`).
- **Item de serviço**: item da LC 116/03 no formato `13.02 - FONOGRAFIA...` → `1302` (distinto do CNAE `5920-1/00`).
- **Valores**: grade "CÁLCULO DO ISSQN" — a **Base de cálculo do ISSQN** é usada como âncora do valor dos serviços, porque o OCR frequentemente corrompe o "Valor total" (ex.: `700,00` → `00,00`); o líquido é reconstruído quando a grade "VALOR TOTAL" vem truncada.
- **Optante do Simples**: detecção tolerante a "OPTANTE PELO SIMPLES" e a "OPTANTE"/"SIMPLES NACIONAL" em linhas separadas.
- **⚠️ Duas estruturas de texto para o MESMO layout** (ponto de atenção arquitetural):
  - **PDF imagem → OCR**: grade com vários campos por linha (`CPF/CNPJ NIF  Inscrição Municipal  Telefone`). Tratado por `_extrair_entidade_campinas`.
  - **PDF digital → pdfminer**: tabela de 2 colunas extraída campo a campo, com CNPJ/Nome/Endereço contíguos por entidade e os demais campos (IM, e-mail, município, telefone, CEP) num bloco posterior **com as colunas intercaladas**. Regra estável: a *N-ésima ocorrência* de cada rótulo pertence à N-ésima entidade (1ª = prestador, 2ª = tomador). Tratado por `_extrair_entidade_campinas_digital`, escolhido por detecção automática da estrutura.

### 14. Portal Nacional DANFSe — `danfse_nacional`
- **Cabeçalho**: "DANFSe v1.0", "Documento Auxiliar da NFS-e"
- **Competência**: Rótulos `Competência da NFS-e` (aceita `MM/YYYY` e `DD/MM/YYYY`) com regra de prioridade sobre a *Data/Hora da Emissão* em caso de conflitos.
- **Entidades**: Suporte avançado a extração segmentada para **Prestador**, **Tomador** e **Intermediário do Serviço**, isolando perfeitamente seus respectivos CNPJs e controlando contaminações cruzadas quando campos vêm indicados como "NÃO IDENTIFICADO".

### Faturas de locação / serviços específicos

Layouts de emissores fixos (a razão social e o endereço do prestador são conhecidos e, em vários casos, fixados no código). Geralmente `CodigoVerificacao = "FATURA"` e item de serviço `0601` (locação de bens móveis).

### 15. Localiza — `localiza_fatura`
- Faturas de locação/revenda de serviços veiculares da Localiza Rent A Car.
- Identificado por "LOCALIZA RENT A CAR S/A" ou "FATURA / DUPLICATA".

### 16. CPE Tecnologia — `cpe_locacao`
- Fatura de locação; detecção por "CPE BAHIA" ou "cpe tecnologia".

### 17. Guincho Cidade — `guincho_cidade`
- Fatura de locação; detecção por "GUINCHO CIDADE".

### 18. B.F. Serviços Ambientais — `bf_ambientais`
- Fatura de locação; detecção por "B.F. SERVIÇOS AMBIENTAIS" (com/sem cedilha).

### 19. LMR Engenharia — `lmr_engenharia`
- Fatura/duplicata; detecção por "LMR ENGENHARIA" (tolerante a OCR: "LTR"/"L.M.R.").

### 20. Geração & Energia — `geracao_energia`
- Fatura de locação; detecção pelo CNPJ `03.292.008/0001-67`.

### 21. Locontainers — `locontainers`
- Locação de containers (Vidal Locação); detecção por "LOCONTAINERS", "VIDAL LOCAÇÃO" ou CNPJ `00.111.704`.

### Outros documentos fiscais

### 22. NF-e de Serviço de Comunicação (Telecom) — `telecom_comunicacao`
- **Cabeçalho**: "NOTA FISCAL DE FATURA DE SERVIÇO DE COMUNICAÇÃO".
- CNPJ do emitente decodificado da chave de acesso de 44 dígitos; total via "TOTAL A PAGAR"; BC/alíquota de ICMS mapeados.

### 23. Osasco/SP — NF-R de Repasse — `osasco_nfr_repasse`
- **Cabeçalho**: "Nota Fiscal Eletrônica de Repasse" ou domínio `nfe.osasco.gov.br` (ex.: iFood Benefícios).
- Campos no formato "Rótulo: valor"; regime especial (sem BC/alíquota/ISS discriminados); competência via "Ref. Fiscal MM/AAAA".

### 24. ISBET — `isbet_recibo`
- **Cabeçalho**: "NOTA DE CONTRIBUIÇÃO SOLIDÁRIA" ou "ISBET".

### Fallback

### 25. Genérico — `generico`
- Fallback para layouts de prefeituras ainda não mapeadas. Usa heurísticas universais de busca de tags de XML padrão ABRASF.

---

## 🚀 Escalabilidade e Adição de Novos Layouts

O **Conversor NFS-e** foi projetado seguindo o padrão de **Design Patterns Orientado a Expressões Regulares (Regex) e Etiquetas (Labels)**, o que significa que o código-fonte **nunca precisa ser reescrito ou quebrado** para adicionar novas prefeituras.

**Para adicionar um novo layout de qualquer cidade do Brasil, o software é escalável pelas seguintes características:**
1. **Registrar a detecção nos DOIS métodos**: adicione a marca do novo layout em `_detect_layout` **e** em `_detect_layout_page` (`if re.search(...): return LAYOUT_X`). ⚠️ Um layout com todas as regras de campo corretas ainda falha silenciosamente se a detecção não o reconhecer, ou se um layout anterior na cadeia "roubar" o documento — teste a detecção contra o texto real, não só a extração.
2. **Dicionário de Etiquetas**: adicione as palavras-chave do novo layout (ex: `"Tomador do Serviço:"`, `"Dados do Cliente:"`) nas listas `_LABELS_TOMADOR`/`_LABELS_PRESTADOR` no topo de `pdf_extractor.py`. O sistema automaticamente recorta e isola aquele bloco.
3. **Métodos Modulares**: cada metadado (ex: `_extrair_valores`, `_extrair_data_emissao`, `_extrair_numero`, `_extrair_entidade`) usa condicionais simples (`if self.layout == LAYOUT_NOVA_CIDADE:`). Plugue a regra do novo município sem afetar nenhuma cidade já suportada.
4. **IBGE resolver**: registre a cidade em `IBGEResolver.KNOWN_CITIES` (`src/utils/ibge_resolver.py`) e sempre passe `city_hint` específico da entidade — senão o resolver pode devolver a capital do estado (ex.: Salvador para um prestador de Camaçari).
5. **Isolamento entre Leitura e Escrita**: o robô de leitura (`pdf_extractor.py`) não conhece o de escrita (`abrasf_transformer.py`). Ele apenas preenche um Modelo Pydantic unificado (`Nfse`). Por mais fora de padrão que seja o PDF, basta ensinar o extractor a preencher o Modelo que o XML ABRASF sairá idêntico para o ERP.
6. **Avisos de baixa confiança**: `Nfse.avisos` acumula alertas quando um campo cai em fallback (número/CNPJ zerado, data atual, valor zero). Prefira sinalizar a mascarar — foi assim que bugs silenciosos de OCR foram flagrados.

> **Atenção — mesmo layout, estruturas de texto diferentes:** um layout pode chegar como PDF imagem (OCR, campos em grade) ou PDF digital (pdfminer, colunas intercaladas), exigindo parsers de entidade distintos com detecção automática da estrutura. Ver o layout **Campinas/SP** (`_extrair_entidade_campinas` vs `_extrair_entidade_campinas_digital`) como referência.

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

*Documentação atualizada em: 2026-07-16 (25 layouts; adicionado Campinas/SP).*
