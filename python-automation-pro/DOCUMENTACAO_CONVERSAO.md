# Documentação de Conversão — Conversor NFS-e / Contratos ABRASF 2.01

Este documento detalha os layouts e formatos suportados pelo conversor.

---

## Layouts Suportados (PDF → XML)

O extrator PDF (`SPPdfExtractor`) conta com um motor de heurística profunda, capaz de ler as disposições textuais do PDF e classificar dinamicamente qual regra de negócio aplicar (`_detect_layout` / `_detect_layout_page`). São **31 layouts** ao todo (30 específicos + o genérico de fallback), agrupados abaixo por tipo. PDFs escaneados/imagem (sem texto extraível) passam automaticamente por **OCR** (Tesseract via `pytesseract` + PyMuPDF, `lang='por'`) antes da extração.

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

### 13. Campinas/SP — `campinas_sp`
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

### 15. Lauro de Freitas/BA — `lauro_de_freitas_ba`
- **Detecção**: "MUNICÍPIO DE LAURO DE FREITAS" ou domínio `laurodefreitas.ba.gov.br`.
- **Item de serviço**: código municipal de 6 dígitos (item.subitem LC116 + subitem municipal, ex.: `110201`) → usamos os 4 primeiros (`1102`).
- **⚠️ Campos deslocados pelo pdfminer**: Município/UF/E-mail do **prestador** saem *depois* do cabeçalho "TOMADOR DE SERVIÇOS" (mas antes do nome do tomador). Extração dedicada particiona o texto em 3 blocos pelos cabeçalhos de seção para o tomador não herdar o município/e-mail do prestador.

### 16. Iaçu/BA — `iacu_nfse`
- **Sistema**: Prefeitura Municipal de Iaçu/BA via plataforma **nfservico.com.br** (NFS-e tributada, escaneada → OCR).
- **Detecção**: "PREFEITURA MUNICIPAL DE IAÇU" (tolerante ao "ç" corrompido no OCR) ou `nfservico.com.br/iacu`. Específico do município — **não** casa pela marca genérica da plataforma, para não colidir com outros municípios do mesmo SaaS.
- **⚠️ Caixa de cabeçalho + QR**: Número da nota / Data e hora / Código de Verificação ficam ilegíveis na leitura de página inteira (caixa pequena ao lado de um QR Code). Recorte dedicado do canto superior direito em zoom alto + PSM 6 (`_ocr_header_box_iacu`) recupera os três campos, prependido ao texto principal (mesmo padrão do Salvador).
- **Item de serviço**: item LC116 no formato `7.02` → `0702`.
- **Valores**: NFS-e **tributada** (ISS real, ex.: 3% sobre a base) — grade "Valor total das deduções / Base de cálculo / Alíquota / Valor do ISS / Crédito"; base/alíquota/ISS espelhados da face (diferente da família de locação).
- **Entidades**: endereço em linha única (`RUA X N, - BAIRRO - CEP: NNNNNNNN - CIDADE - UF`); parser ignora o ruído do carimbo de recebimento intercalado no bloco do tomador (o CNPJ correto é o primeiro de 14 dígitos).

### Faturas de locação / serviços específicos

Layouts de emissores fixos (a razão social e o endereço do prestador são conhecidos e, em vários casos, fixados no código). Geralmente `CodigoVerificacao = "FATURA"` e item de serviço `0601` (locação de bens móveis).

### 17. Localiza — `localiza_fatura`
- Faturas de locação/revenda de serviços veiculares da Localiza Rent A Car.
- Identificado por "LOCALIZA RENT A CAR S/A" ou "FATURA / DUPLICATA".

### 18. CPE Tecnologia — `cpe_locacao`
- Fatura de locação; detecção por "CPE BAHIA" ou "cpe tecnologia".

### 19. Guincho Cidade — `guincho_cidade`
- Fatura de locação; detecção por "GUINCHO CIDADE".

### 20. B.F. Serviços Ambientais — `bf_ambientais`
- Fatura de locação; detecção por "B.F. SERVIÇOS AMBIENTAIS" (com/sem cedilha).

### 21. LMR Engenharia — `lmr_engenharia`
- Fatura/duplicata; detecção por "LMR ENGENHARIA" (tolerante a OCR: "LTR"/"L.M.R.").

### 22. Geração & Energia — `geracao_energia`
- Fatura de locação; detecção pelo CNPJ `03.292.008/0001-67`.

### 23. Locontainers — `locontainers`
- Locação de containers (Vidal Locação); detecção por "LOCONTAINERS", "VIDAL LOCAÇÃO" ou CNPJ `00.111.704`.

### 24. SUL&SEG — Nota de Cobrança — `sulseg_cobranca`
- **Nota de Cobrança privada** de locação de bens móveis (equipamento de alarme), distinta da NFS-e prefeitural da mesma empresa. Traz "OPERAÇÃO NÃO SUJEITA AO I.S.S.".
- Detecção por "NOTA DE COBRANÇA" + CNPJ da emitente (`18.294.792`). Prestador fixo; tomador extraído. Número ancorado em "NOTA DE COBRANÇA Nº" (evita colidir com o rótulo genérico "NÚMERO").

### 25. Fatura de Locação Genérica — `fatura_locacao_generica`
- Cobre **qualquer** "FATURA DE LOCAÇÃO" ainda não catalogada por emissor específico, parseando **locadora e locatário direto do texto** (sem hardcode).
- Detecção ancorada em "FATURA DE LOCAÇÃO", posicionada **por último** nas duas cadeias (depois de todos os emissores específicos e layouts municipais) para não "roubar" a detecção deles.

### 26. ARMAC — `armac_locacao`
- Fatura de locação de equipamentos pesados da ARMAC (CNPJ `00.242.184`), **PDF 100% imagem** (escaneado), com **tabela multi-item**.
- Detecção por CNPJ/"ARMAC" **antes** do genérico de locação (estrutura própria: blocos "Dados do Locador/Tomador", grade de equipamentos). A leitura padrão embaralha a grade; um **re-OCR dedicado da página inteira em zoom 4x + PSM 6** (`_ocr_armac`) recupera "Valor total", datas, CNPJs e endereços.

### Outros documentos fiscais

### 27. NF-e de Serviço de Comunicação (Telecom) — `telecom_comunicacao`
- **Cabeçalho**: "NOTA FISCAL DE FATURA DE SERVIÇO DE COMUNICAÇÃO".
- CNPJ do emitente decodificado da chave de acesso de 44 dígitos; total via "TOTAL A PAGAR"; BC/alíquota de ICMS mapeados.

### 28. Osasco/SP — NF-R de Repasse — `osasco_nfr_repasse`
- **Cabeçalho**: "Nota Fiscal Eletrônica de Repasse" ou domínio `nfe.osasco.gov.br` (ex.: iFood Benefícios).
- Campos no formato "Rótulo: valor"; regime especial (sem BC/alíquota/ISS discriminados); competência via "Ref. Fiscal MM/AAAA".

### 29. PASSWORD / eNotas Gateway — `password_enotas`
- NFS-e **tributada** (ISS 3%, Simples Nacional) emitida via **eNotas Gateway** pelo prestador PASSWORD - SISTEMAS ELETRONICOS LTDA (Lauro de Freitas/BA). Não faz parte da família "locação não sujeita a ISS".
- Detecção ancorada especificamente no **CNPJ do emitente** (`04.021.023`), para não colidir com futuras notas de outros emitentes que usem o mesmo gateway.
- Código do serviço LC116 `15.03 / 1503` → `1503`; "VALOR DO ISS" impresso como "-" (recolhido via DAS do Simples) → base/alíquota preenchidas, ISS = 0,00.

### 30. ISBET — `isbet_recibo`
- **Cabeçalho**: "NOTA DE CONTRIBUIÇÃO SOLIDÁRIA" ou "ISBET".

### Fallback

### 31. Genérico — `generico`
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

*Documentação atualizada em: 2026-07-23 (31 layouts; adicionados Lauro de Freitas/BA, Iaçu/BA, SUL&SEG Cobrança, Fatura de Locação Genérica, ARMAC e PASSWORD/eNotas).*
