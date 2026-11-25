# FRD — Functional Requirements Document

**Conversor de Notas Fiscais em PDF para XML (ABRASF 2.01 / NF-e / CT-e OS)**

| Item | Valor |
| --- | --- |
| Versão do documento | 1.0 |
| Data | 25/11/2026 |
| Versão do sistema | v1.10.0 |
| Status | Rascunho para revisão |
| Público | Equipe interna / técnica |
| Documentos relacionados | [BRD](BRD.md) · [SRS](SRS.md) · [TRD](TRD.md) |

> Descreve o comportamento **atual** (v1.10.0). Itens sem fonte verificável estão marcados **A confirmar**. Rastreabilidade RF ↔ módulos ↔ testes: [SRS §5](SRS.md#5-rastreabilidade).

---

## 1. Visão funcional

```
PDF(s) ──► desproteção (senha) ──► texto (pdfminer) ou OCR (Tesseract)
       ──► detecção de layout (por documento e por página)
       ──► extração por campo ──► regras fiscais / validações / avisos
       ──► modelo (Nfse | NfeProduto | CteOS) ──► transformer ──► XML
```

Atores: **Usuário operador** (GUI ou CLI) e **Domínio** (consome os XMLs, fora do sistema).

## 2. Requisitos funcionais

Prioridade: **M** = obrigatório (já entregue e coberto); **D** = desejável. Todos os RF abaixo estão implementados na v1.10.0, salvo indicação.

### 2.1 Entrada

| ID | Requisito | Prior. | Critérios de aceitação |
| --- | --- | --- | --- |
| RF-001 | Aceitar PDF com camada de texto (digital). | M | Texto extraído via pdfminer; nenhuma chamada de OCR quando a camada de texto é legível. |
| RF-002 | Aceitar PDF escaneado/fotografado (sem texto, ou com camada de texto ilegível/só de valores). | M | Página passa por OCR (`por`) automaticamente; camada de texto de baixa qualidade também aciona OCR. |
| RF-003 | Corrigir a orientação de páginas fotografadas (90°/180°/270°). | M | Testadas as 4 rotações quando a leitura na orientação original tem baixa qualidade; escolhida a de melhor pontuação. |
| RF-004 | Converter um PDF único (CLI `--input`; GUI com arquivo). | M | Um XML por nota reconhecida na pasta de saída. |
| RF-005 | Converter lote (CLI `--batch <pasta>`; GUI com pasta ou vários arquivos). | M | Erro em um PDF não interrompe os demais; relatório final lista sucessos, ignorados e "PDFs com Falha Total". |
| RF-006 | Processar PDFs com várias páginas e várias notas por página. | M | Nota que continua na página seguinte é agrupada; várias notas na mesma página geram XMLs distintos. Nota distinta nunca é descartada como duplicata. |
| RF-007 | Converter só páginas escolhidas. | M | CLI `--pages "1,3,6"` / `"1-3,6"` (só com `--input`, numeração 1-based da página real); GUI: janela de seleção com uma caixa por nota, inclusive para vários PDFs numa única janela agrupada por arquivo. |
| RF-008 | Abrir PDF protegido por senha de abertura. | M | CLI `--password` (com `--input`/`--batch`, rejeitado com `--contrato`); GUI: diálogo por PDF com **Pular este arquivo** (só em lote) e **Cancelar**; senha errada reabre o diálogo. |
| RF-009 | Mensagens claras para PDF protegido sem senha ou com senha errada. | M | Texto em português, nunca vazio; CLI sai com código 1 sem traceback; no lote falha só o arquivo. |
| RF-010 | Gerar XML de contrato de locação a partir de dados digitados (GUI) ou JSON (CLI `--contrato`). | M | Ver RF-059. |

### 2.2 Detecção de layout

| ID | Requisito | Prior. | Critérios de aceitação |
| --- | --- | --- | --- |
| RF-011 | Identificar automaticamente o layout do documento (`_detect_layout`) e de cada página (`_detect_layout_page`). | M | Os 74 layouts da §3 reconhecidos pelo texto real (digital e/ou OCR) dos casos que os originaram. |
| RF-012 | Detectar DANFE (NF-e Modelo 55) e DACTE OS (CT-e Modelo 67) estruturalmente, antes de qualquer layout de NFS-e. | M | DANFE: "DANFE" + "Documento Auxiliar da Nota Fiscal Eletrônica" + "0-ENTRADA/1-SAÍDA", independente do emitente. |
| RF-013 | Discriminar variantes digital × escaneada do mesmo município quando há layouts dedicados. | M | Ex.: Camaçari CPqD digital → `camacari_cpqd`; escaneada → `camacari_ba_scan_v3` (superset de `camacari_ba_scan`). |
| RF-014 | Aplicar o layout genérico quando nenhum específico casa. | M | Documento não catalogado produz XML com o que for extraível e avisos para o que não for. |
| RF-015 | Reconhecer emitente por CNPJ raiz ou pela chave de acesso quando o texto impresso não basta. | D | Layouts de fatura por CNPJ raiz casam qualquer filial; NFCom com CNPJ ilegível usa a chave decodificada. |

### 2.3 Extração por campo (NFS-e → modelo `Nfse`)

| ID | Campo | Critérios de aceitação |
| --- | --- | --- |
| RF-016 | Número da nota | Rótulo do layout; alternativas por layout (chave de acesso, nome do arquivo, recortes dedicados). Não lido → sentinela + aviso. |
| RF-017 | Código de verificação/autenticidade | Quando o documento não imprime código, sentinela (ex.: `XXXX-XXXX`); nunca código inventado. |
| RF-018 | Data de emissão | Preferir data com horário completo; não lida → aviso (nunca data atual silenciosa). |
| RF-019 | Competência | Ver RF-037. |
| RF-020 | Prestador e tomador (CNPJ/CPF, IM, razão social, endereço, município, UF, CEP, e-mail, telefone) | CNPJ validado por dígito verificador; entidades não trocadas entre si; complemento não entra no logradouro. |
| RF-021 | Intermediário | Extraído quando impresso; bloco vazio não vira tomador. |
| RF-022 | Código de município IBGE | Resolvido por tabela interna e código impresso; município fora da tabela → capital da UF como fallback **com aviso**. |
| RF-023 | Discriminação do serviço | Texto do serviço faturado, sem rótulos de grade colados. |
| RF-024 | Item da lista LC 116 e CNAE | Item normalizado para 4 dígitos; CNAE de 7 dígitos quando impresso, senão `0000000`. |
| RF-025 | Valores e retenções (serviço, deduções, PIS, COFINS, INSS, IR, CSLL, outras retenções, ISS, ISS retido, base, alíquota, líquido) | Ver regras §2.4. |
| RF-026 | Optante do Simples Nacional / regime especial (MEI, ME/EPP) | Lido do documento quando impresso. |

### 2.4 Regras fiscais e de integridade

| ID | Regra | Critérios de aceitação |
| --- | --- | --- |
| RF-030 | **Sentinela + aviso**: valor não recuperável nunca é inventado. | Documento ilegível → `00000000000000`; valor → `0.00`; sempre acompanhado de aviso que nomeia o campo. |
| RF-031 | Não derivar valor que o documento não declara. | Ex.: fatura que imprime só a taxa da retenção sai com retenção 0,00 + aviso com os percentuais impressos; ISS ilegível não é recalculado como Base × Alíquota. |
| RF-032 | Valor derivado só corrige divergência, nunca preenche zero legítimo. | Zero impresso (ex.: Simples Nacional) é preservado; reparo por identidade contábil só quando ela falha. |
| RF-033 | `ValorServicos` = valor bruto dos serviços, antes de retenções e descontos. | Alterar só o "Valor Líquido" do documento não altera `ValorServicos`. |
| RF-034 | **São Paulo/SP — "VALOR TOTAL RECEBIDO"**: quando o valor dos serviços impresso é 0,00 ou menor que o valor total recebido, o recebido vira `ValorServicos`, para qualquer prestador (digital e escaneada). | A diferença não vai para `ValorDeducoes` (deduções saem como impressas). Recebido ilegível/não confirmado → mantém o impresso + aviso. |
| RF-035 | **Teto do ISS (LC 116, art. 8º, II)**: alíquota > 5% é erro de leitura. | Guarda geral em todos os layouts: releitura quando o layout tem recorte; senão alíquota 0 + aviso. Sem piso de 2% (Simples/MEI podem ter alíquotas menores/fracionárias). |
| RF-036 | **Simples Nacional / MEI** | `OptanteSimplesNacional` 1/2; `RegimeEspecialTributacao` = valor lido ou `6` (ME/EPP) para optante; ISS em branco no documento do optante permanece 0,00 (não derivado). |
| RF-037 | **Competência**: campo de referência impresso (ex.: "Ref. Fiscal") prevalece sobre o mês da emissão. | Sem referência impressa → convenção pela data de emissão. Ano de competência evidentemente trocado pelo OCR é corrigido/sinalizado. |
| RF-038 | **Incidência do ISS**: município do prestador, salvo indicação explícita de outro município de tributação. | "Local de incidência = domicílio do adquirente" (IBS/CBS) não altera a incidência do ISS. |
| RF-039 | **Retenções** mapeadas para as tags ABRASF do imposto correspondente. | "Contribuições sociais retidas" combinadas (DANFSe) somadas em `OutrasRetencoes`; `IssRetido` 1 = retido, 2 = não retido. |
| RF-040 | **IBS/CBS** não têm tag no ABRASF 2.01. | Valores IBS/CBS descartados no XML de serviço. |
| RF-041 | **Nota cancelada**: documento com marca de cancelamento é convertido normalmente e recebe aviso. | Detecção textual ("CANCELADA/CANCELADO" isolado ou "Motivo: … cancel/desisti/estorn/anulad"), válida para todos os layouts. |
| RF-042 | **Número manuscrito**: quando o número impresso está cortado/ilegível e há anotação a caneta, a anotação pode ser usada. | Só se o impresso não foi lido; compatível com dígitos impressos parciais; aceito por maioria de leituras; sempre com aviso "confira"; ilegível/incompatível → sentinela + aviso. Implementado no Camaçari CPqD escaneado. |
| RF-043 | Validações de consistência | DV de CNPJ/CPF, mod-11 de chave de acesso e de código de verificação quando aplicável, Base × Alíquota = ISS. |
| RF-044 | Código impresso só é corrigido por seleção entre leituras reais. | Proibido "corrigir" caractere por regra fixa (ex.: S→5) ou por caso especial de uma nota. |

### 2.5 Geração de XML

| ID | Requisito | Critérios de aceitação |
| --- | --- | --- |
| RF-050 | Gerar XML **ABRASF 2.01** para NFS-e e demais documentos de serviço. | Raiz `CompNfse`/`Nfse versao="2.01"`; um arquivo por nota. |
| RF-051 | Nome do arquivo: `<nome do PDF>[_Pagina_<p>]_NF_<número>.xml`. | Igual em todos os caminhos da GUI e do lote; nunca prefixo `temp`. |
| RF-052 | Gerar lote `ListaNfse` quando solicitado. | Suportado pelo transformer ABRASF. |
| RF-053 | Escolher o transformer pelo **tipo real** do documento extraído. | `NfeProduto` → NF-e 4.00 e `CteOS` → CT-e OS mesmo com a opção "NFS-e" selecionada. |
| RF-054 | Gerar **NF-e 4.00** para DANFE (Modelo 55) com chave de acesso e valores reais. | Itens (`det`) com NCM/CFOP/CST/valores, emitente, destinatário, transportador. Sem itens lidos → XML gravado sem item fictício + mensagem `[ERRO]` (será rejeitado pelo Domínio). |
| RF-055 | Gerar **CT-e OS** leiaute 4.00 (`cteOSProc`/`CTeOS`/`infCte`, mod 67) para DACTE OS. | Valida contra o XSD oficial (exceto assinatura); retenções federais em bloco próprio, nunca em `imp/ICMS`. |
| RF-056 | Opção "somente CT-e OS" (GUI "CT-e OS (DACTE OS - Modelo 67)"; CLI `--format cteos`). | Só os DACTE OS geram XML; uma linha de log por página ignorada; sem nenhum DACTE OS → mensagem clara, código 1, nenhum XML. |
| RF-057 | Opção NF-e de serviço (`--format nfe`). | Usa o transformer NF-e para documentos de serviço (legado). Uso atual **A confirmar**. |
| RF-058 | Campos obrigatórios para o Domínio nunca vazios. | Razão social, endereço, número, bairro, CEP preenchidos com padrão neutro (ex.: "Não informado", `S/N`, `00000000`) quando não lidos. |
| RF-059 | XML de **contrato de locação**. | Locador → `Tomador`; locatário → `Prestador`; `Numero` = ano; `CodigoVerificacao` = `CONTRATO`; item `0601`; `ValorIss` = mensal × alíquota; arquivo `CONTRATO_LOCACAO_<ANO>.xml`. |

### 2.6 Avisos e relatórios

| ID | Requisito | Critérios de aceitação |
| --- | --- | --- |
| RF-060 | Acumular avisos de baixa confiança por nota (`Nfse.avisos`). | Exibidos no console/log da GUI junto da nota. |
| RF-061 | Diferenciar severidade. | `[AVISO]` para conferência; `[ERRO]` (vermelho na GUI) para XML que o Domínio rejeitará. |
| RF-062 | Relatório de lote. | Contagem de convertidos, ignorados (com motivo) e falhas por arquivo. |
| RF-063 | Nunca exibir "Erro:" vazio. | Exceções sem mensagem mostram o nome da classe. |

### 2.7 Interface gráfica (GUI)

| ID | Requisito | Critérios de aceitação |
| --- | --- | --- |
| RF-070 | Selecionar pasta de entrada ou arquivos, pasta de saída e "Tipo de Arquivo". | Opções: NFS-e (ABRASF 2.01), NF-e (DANFE Modelo 55), CT-e OS (DACTE OS Modelo 67), Contrato de Locação. |
| RF-071 | Formulário de contrato de locação. | Locador, locatário, valor mensal, discriminação, alíquota, código de serviço; pasta de saída própria. |
| RF-072 | Progresso e log em tela. | Barra de progresso e log por arquivo; exceções aparecem no log da janela. |
| RF-073 | Seleção de notas (um ou vários PDFs). | Ver RF-007; botões "Converter selecionadas", "Marcar/limpar todas", "Converter todas as válidas", "Cancelar". |
| RF-074 | Diálogo de senha. | Ver RF-008. |

### 2.8 Linha de comando (CLI)

| ID | Requisito | Critérios de aceitação |
| --- | --- | --- |
| RF-080 | Argumentos `--input` \| `--batch` \| `--contrato` (mutuamente exclusivos), `--output` (obrigatório), `--format {abrasf,nfe,cteos}`, `--pages`, `--password`. | Combinações inválidas rejeitadas pelo parser com mensagem. |
| RF-081 | Saída tolerante a nomes de arquivo com caracteres fora da codificação do console. | Caractere não representável sai como "?"; a conversão não aborta. |
| RF-082 | Código de saída 1 com mensagem em stderr para erros de senha e "nenhum CT-e OS". | Sem traceback. |

### 2.9 Atualização automática (somente GUI)

| ID | Requisito | Critérios de aceitação |
| --- | --- | --- |
| RF-090 | Verificar versão nova ao abrir, sem bloquear a UI, e por botão "Verificar atualizações". | Consulta ao último Release publicado (não draft/pre-release); falha de rede silenciosa na checagem automática. |
| RF-091 | Comparar versões SemVer (tolerando prefixo `v`). | `is_newer` verdadeiro só para versão maior. |
| RF-092 | Pedir confirmação antes de atualizar. | Diálogo "Atualizar agora" / "Depois". |
| RF-093 | Atualizar no formato instalado. | Instalação em pasta → asset `.zip`; executável único → asset `.exe`; sem migração automática entre formatos. |
| RF-094 | Troca resiliente e falha visível. | Até 10 tentativas espaçadas de 2 s; falha gravada em log temporário e exibida na abertura seguinte; pasta anterior restaurada em caso de falha (onedir). |
| RF-095 | Não atualizar quando executado a partir do código-fonte. | Fluxo abortado com aviso. |

## 3. Catálogo de layouts (74)

Contagem derivada das constantes `LAYOUT_*` de `src/extractors/pdf_extractor.py` (77) menos as 3 que não contam como layout de serviço numerado: `camacari_ba_scan_v3` (superset interno do Camaçari escaneado), `danfe_produto` (NF-e Modelo 55) e `dacte_os` (CT-e OS Modelo 67) — estes dois têm seção própria (§4). Descrições genéricas; o detalhe de cada layout está em [`DOCUMENTACAO_CONVERSAO.md`](../DOCUMENTACAO_CONVERSAO.md).

### 3.1 NFS-e de prefeituras (38)

| UF | Layouts (`id`) | Qtde |
| --- | --- | --- |
| BA | `barreiras_ba`, `camacari_cpqd`, `camacari_ba_scan`, `camacari_ba_avulsa`, `camacari_sisloc`, `camacari_gestaoclick`, `salvador_ba`, `feira_de_santana`, `feira_de_santana_nfse_nacional`, `simoes_filho_ba`, `lauro_de_freitas_ba`, `iacu_nfse`, `brotas_macaubas_ba`, `mata_sao_joao_ba`, `monte_santo_ba`, `saubara_ba`, `saubara_ba_2` | 17 |
| SP | `sao_paulo_sp`, `sao_paulo_sp_scan`, `guarulhos_sp`, `santos_sp`, `vinhedo_sp`, `barueri_sp`, `osasco_nfse`, `ribeirao_preto_sp`, `ribeirao_pires_sp`, `campinas_sp` | 10 |
| SC | `joinville_sc`, `sao_jose_sc` | 2 |
| MT | `cuiaba_issnet` | 1 |
| MG | `rosario_da_limeira_mg` | 1 |
| RJ | `rio_de_janeiro` | 1 |
| CE | `fortaleza_ce` | 1 |
| DF | `brasilia_df` | 1 |
| GO | `goiania_go` | 1 |
| PB | `joao_pessoa_pb` | 1 |
| RN | `natal_rn` | 1 |
| RS | `eldorado_do_sul_rs` | 1 |

### 3.2 Portal Nacional (2)

| Layout | Descrição |
| --- | --- |
| `danfse_nacional` | DANFSe v1.0 |
| `danfse_nacional_reforma` | DANFSe v2.0 (reforma tributária; superset da v1.0) |

### 3.3 Documentos de serviço de emitentes/plataformas específicos (7)

| Layout | Descrição genérica |
| --- | --- |
| `password_enotas` | NFS-e via gateway eNotas (vários emitentes) |
| `biocontrol_dedetizadora` | Demonstrativo próprio de NFS-e de prestador de controle de pragas |
| `isbet_recibo` | Nota de contribuição de instituto (sem código de verificação impresso) |
| `sp_skytef` | Fatura de licenciamento de software (plataforma Qive) |
| `sp_caixa_cartoes` | Fatura de taxa de serviço de cartões pré-pagos (plataforma Qive) |
| `osasco_nfr_repasse` | NF-R de Repasse (Osasco/SP) |
| `sem_parar_fatura` | Nota fiscal fatura de serviços de pedágio/tag veicular |

### 3.4 Faturas e notas de locação (19)

| Tipo | Layouts | Qtde |
| --- | --- | --- |
| Locadora de veículos (matriz e agência) | `localiza_fatura`, `localiza_petrolina` | 2 |
| Faturas de locação de emitentes específicos | `cpe_locacao`, `guincho_cidade`, `bf_ambientais`, `lmr_engenharia`, `geracao_energia`, `locontainers`, `armac_locacao`, `ff_locacao`, `pjb_locacao`, `fatura_neotagus`, `fatura_rotaexata` | 11 |
| Nota de cobrança de locação | `sulseg_cobranca` | 1 |
| Modelos genéricos de locação (qualquer emitente) | `fatura_locacao_generica`, `nota_locacao`, `nota_debito_locacao`, `fatura_locacao_periodo`, `fatura_locacao_equipamentos` | 5 |

### 3.5 Serviços de comunicação (7)

| Layout | Descrição |
| --- | --- |
| `telecom_comunicacao` | NF-e/DANFE-COM de serviço de comunicação (genérico) |
| `nfcom_salvador`, `nfcom_rlgr`, `nfcom_lotec_fibra`, `nfcom_sete_connect`, `nfcom_net_mund`, `nfcom_bandeirantes` | NFCom (template nacional, portal SVRS), um layout por emitente |

### 3.6 Fallback (1)

| Layout | Descrição |
| --- | --- |
| `generico` | Qualquer documento não reconhecido |

**Total: 38 + 2 + 7 + 19 + 7 + 1 = 74.**

## 4. Documentos ICMS (fora da contagem de layouts)

| Constante | Documento | Saída |
| --- | --- | --- |
| `danfe_produto` | DANFE Estadual — NF-e Modelo 55 (digital e escaneado) | XML NF-e 4.00 (`NfeProdutoTransformer`) |
| `dacte_os` | DACTE OS — CT-e OS Modelo 67 | XML CT-e OS 4.00 (`CteTransformer`) |

## 5. Requisitos funcionais pendentes / em aberto

| Item | Situação |
| --- | --- |
| `NaturezaOperacao` reflete a natureza real do ISS (hoje fixa em "1") | Defeito conhecido; correção **não aprovada**. |
| Comportamento final para NF-e sem itens (gravar com erro × não gravar × sufixo) | Decisão adiada pelo usuário. |
| Transformer para XML no Padrão Nacional/ADN | Fora do escopo atual. |
| Aviso de município fora da tabela IBGE também para NF-e/CT-e OS | Hoje só para NFS-e. |
