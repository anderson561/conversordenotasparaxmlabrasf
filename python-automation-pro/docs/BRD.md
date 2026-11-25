# BRD — Business Requirements Document

**Conversor de Notas Fiscais em PDF para XML (ABRASF 2.01 / NF-e / CT-e OS)**

| Item | Valor |
| --- | --- |
| Versão do documento | 1.0 |
| Data | 25/11/2026 |
| Versão do sistema | v1.10.0 |
| Status | Rascunho para revisão |
| Público | Equipe interna / técnica |
| Documentos relacionados | [FRD](FRD.md) · [SRS](SRS.md) · [TRD](TRD.md) |

> Convenção: o que não pôde ser derivado do código, da documentação do repositório ou das regras já consolidadas aparece como **A confirmar**.

---

## 1. Contexto e problema de negócio

O escritório contábil recebe notas fiscais de fornecedores e prestadores **em PDF** — digitais, escaneadas, fotografadas, às vezes de cabeça para baixo ou protegidas por senha — emitidas por dezenas de prefeituras e emissores diferentes. A escrituração é feita no sistema contábil **Domínio (Thomson Reuters)**, que importa notas por arquivo XML, mas não lê PDF.

Sem o conversor, cada nota precisa ser **digitada manualmente** no Domínio (número, código de verificação, datas, prestador, tomador, valores, retenções, item da LC 116). Os problemas decorrentes:

- volume de digitação proporcional ao número de notas e de páginas por PDF;
- erros de digitação em campos fiscais (CNPJ, valores, retenções, competência) que viram lançamentos errados;
- ausência de um formato único: cada prefeitura imprime um modelo diferente de NFS-e, e há ainda documentos que não são NFS-e (faturas de locação, NFCom, DANFE, DACTE OS).

## 2. Objetivos de negócio

| ID | Objetivo |
| --- | --- |
| OB-01 | Substituir a digitação manual por importação de XML no Domínio para as notas recebidas em PDF. |
| OB-02 | Produzir XML que a rotina de importação do Domínio aceite, para cada família de documento (serviço: ABRASF 2.01; produto: NF-e 4.00; transporte: CT-e OS Modelo 67). |
| OB-03 | Nunca introduzir no XML um dado fiscal que o documento não contém: dado ausente é sinalizado ao usuário, não inventado. |
| OB-04 | Processar lotes (vários PDFs, várias notas por PDF) numa única operação, com relatório do que foi e do que não foi convertido. |
| OB-05 | Permitir que usuários não técnicos operem por interface gráfica e se mantenham na versão mais recente sem procedimento manual. |
| OB-06 | Absorver novos modelos de nota (novas prefeituras/emissores) sem reescrever o núcleo. |

## 3. Escopo

### 3.1 Dentro do escopo

- Conversão de PDF para XML de:
  - NFS-e de prefeituras e do Portal Nacional (DANFSe v1.0 e v2.0/reforma) → **ABRASF 2.01**;
  - faturas de locação, notas de débito/cobrança, NFCom/NF de comunicação e outros documentos de serviço sem layout NFS-e → **ABRASF 2.01**;
  - DANFE Estadual (NF-e Modelo 55, produto) → **NF-e 4.00**;
  - DACTE OS (CT-e OS Modelo 67, transporte) → **CT-e OS leiaute 4.00** (sem assinatura digital).
- PDFs digitais (camada de texto) e escaneados/fotografados (OCR).
- PDFs protegidos por senha de abertura.
- Lote de PDFs, PDFs com várias notas e seleção de páginas.
- Geração de XML ABRASF de **contrato de locação** a partir de dados digitados (sem PDF).
- 74 layouts reconhecidos na v1.10.0 (ver [FRD §3](FRD.md#3-catálogo-de-layouts-74)).
- Interface gráfica (Windows) e linha de comando; atualização automática da GUI.

### 3.2 Fora do escopo

| Item | Observação |
| --- | --- |
| Envio/integração direta com o Domínio (API, banco) | O XML é importado manualmente pelo usuário nas rotinas do Domínio. |
| Emissão de nota fiscal | O sistema só converte documentos já emitidos. |
| Assinatura digital dos XMLs | CT-e OS sai sem assinatura do emitente. |
| XML no **Padrão Nacional/ADN** da NFS-e | Não há transformer para esse leiaute; só ABRASF 2.01. |
| Campos de **IBS/CBS** (reforma tributária) no XML de serviço | ABRASF 2.01 não tem tags para eles; são descartados. |
| Configuração do Domínio (acumuladores, "Conjunto de Dados") | Ajustada no próprio Domínio, nunca distorcendo o XML. |
| Plataformas além de Windows | A confirmar se há demanda. |
| Notas de outros modelos não catalogados | Caem no layout genérico, sem garantia de completude. |

## 4. Partes interessadas (por papel)

| Papel | Interesse / responsabilidade |
| --- | --- |
| Usuário operador (escritório contábil) | Converte os PDFs, confere os avisos e importa os XMLs no Domínio. Decide as regras fiscais de negócio quando o documento é ambíguo. |
| Responsável pelo negócio / patrocinador | A confirmar. |
| Mantenedor / desenvolvedor | Cria layouts, corrige extrações, publica releases. |
| Sistema Domínio (consumidor do XML) | Define o que é "XML correto" na prática: o arquivo precisa passar pela rotina de importação e cair no acumulador certo. |
| Suporte do Domínio | Fonte de verdade para dúvidas sobre o comportamento interno do Domínio (regras de acumulador, rotas de importação). |
| Clientes do escritório (empresas escrituradas) | Beneficiários indiretos: escrituração correta e no período certo. |

## 5. Premissas

- P-01 — O consumidor de todo XML é o Domínio; "correto" significa importável e lançado no acumulador correto, não apenas válido em schema.
- P-02 — Rotas de importação no Domínio:
  - NFS-e: "Importação de NFS-e — Arquivo XML" (ABRASF 2.01).
  - CT-e OS: `Utilitários > Importação > Importação Padrão > CT-e e CT-eOS > Arquivo XML` (confirmada).
  - NF-e: `Importação Padrão > NF-e Arquivo XML` (rejeita NF-e sem itens; rota completa **a confirmar**).
- P-03 — O comportamento interno do Domínio (escolha de acumulador, prioridade de regras) é inferido, não verificado; dúvidas estruturais vão ao suporte do Domínio.
- P-04 — O Tesseract OCR com o idioma português está instalado na máquina que converte PDFs escaneados.
- P-05 — Uso em estação Windows, por usuário que tem acesso aos PDFs em pasta local ou de rede.
- P-06 — Cada novo modelo de nota chega como um caso real (PDF), que serve de base para o layout e para os testes.

## 6. Restrições

### 6.1 Regulatórias / fiscais

| ID | Restrição | Efeito no produto |
| --- | --- | --- |
| RG-01 | Leiaute **ABRASF 2.01** para NFS-e | Estrutura `CompNfse`/`InfDeclaracaoPrestacaoServico`, retenções em `ValorPis/Cofins/Inss/Ir/Csll`, `IssRetido` 1/2. |
| RG-02 | **LC 116/2003**, art. 8º, II — ISS máximo de 5% | Alíquota lida acima de 5% é tratada como erro de leitura (sentinela + aviso), nunca gravada. |
| RG-03 | LC 116/2003 — lista de serviços | `ItemListaServico` derivado do item impresso; contrato de locação usa `0601` por padrão. |
| RG-04 | Reforma tributária (IBS/CBS) fora do ABRASF 2.01 | Valores IBS/CBS descartados; "local de incidência = domicílio do adquirente" é IBS/CBS e não define a incidência do ISS. |
| RG-05 | NF-e Modelo 55 (leiaute 4.00) e CT-e OS Modelo 67 (PL_CTe_400) | Cada documento sai com as suas próprias tags; nunca um tipo disfarçado de outro. |
| RG-06 | Simples Nacional / MEI | Alíquotas fracionárias ou zeradas são legítimas; não há piso de alíquota. |

### 6.2 Operacionais / técnicas

- Executáveis apenas para Windows; distribuição via GitHub Releases.
- OCR depende do Tesseract externo (não embutido no executável).
- Sem servidor: processamento 100% local; a única chamada de rede é a consulta de versão/baixa de atualização.

## 7. Riscos

| ID | Risco | Prob. | Impacto | Mitigação existente |
| --- | --- | --- | --- | --- |
| R-01 | OCR lê valor/CNPJ errado e o XML é lançado com dado plausível porém falso | Média | Alto | Validações (DV de CNPJ, mod-11 da chave, Base × Alíquota = ISS, teto de 5%), sentinela + aviso, recortes dedicados. |
| R-02 | Prefeitura muda o modelo da nota e o layout deixa de reconhecer | Média | Médio | Layout genérico de fallback, avisos de baixa confiança, criação de layout novo a partir do caso real. |
| R-03 | Domínio importa mas lança no acumulador errado | Média | Alto | Ajuste na configuração do Domínio; `NaturezaOperacao` fixa em "1" é um defeito conhecido em aberto (ver [TRD §10](TRD.md#10-limitações-conhecidas-e-débitos-técnicos)). |
| R-04 | NF-e sem itens extraídos gera XML rejeitado pelo Domínio | Baixa | Médio | Mensagem `[ERRO]` explícita; nenhum item fictício. Decisão final adiada pelo usuário. |
| R-05 | Atualização automática falha e o usuário segue em versão antiga sem saber | Baixa | Médio | Até 10 tentativas de troca; log de falha exibido na abertura seguinte. |
| R-06 | Senha de PDF exposta | Baixa | Médio | Senha só em memória; na CLI o risco de histórico/lista de processos é avisado ao usuário. |

> Probabilidade e impacto são estimativas qualitativas deste rascunho — **A confirmar** com o responsável pelo negócio.

## 8. Critérios de sucesso

| ID | Critério | Meta / medição |
| --- | --- | --- |
| CS-01 | XMLs aceitos pela rotina de importação do Domínio | Confirmado caso a caso para ABRASF e CT-e OS; meta percentual **A confirmar**. |
| CS-02 | Nenhum valor fiscal fabricado | Todo campo não lido sai com sentinela + aviso (verificado por testes de regressão). |
| CS-03 | Cobertura de modelos de nota | 74 layouts na v1.10.0; meta de cobertura **A confirmar**. |
| CS-04 | Regressão controlada | Suíte automatizada verde a cada entrega (1.818 testes; em 25/11/2026: 1797 aprovados e 21 pulados — os pulados dependem de PDFs reais e do XSD oficial presentes na máquina). |
| CS-05 | Redução do tempo de lançamento manual | Linha de base e meta **A confirmar** (não há medição registrada). |
| CS-06 | Taxa de notas com aviso / conferência manual | **A confirmar** (não há medição registrada). |
| CS-07 | Abertura da GUI | Observado ~3 s (pasta/onedir) e ~8 s (executável único); não é meta formal. |

## 9. Glossário resumido

| Termo | Significado |
| --- | --- |
| ABRASF 2.01 | Leiaute nacional de XML de NFS-e usado pelo Domínio na importação. |
| DANFSe | Documento auxiliar da NFS-e do Portal Nacional (v1.0 e v2.0/reforma). |
| DANFE | Documento auxiliar da NF-e (produto, Modelo 55). |
| DACTE OS | Documento auxiliar do CT-e OS (transporte, Modelo 67). |
| NFCom | Nota Fiscal Fatura de Serviços de Comunicação. |
| Layout | Modelo de documento reconhecido, com regras de extração próprias. |
| Sentinela | Valor neutro (`00000000000000`, `0.00`, etc.) gravado quando um campo não pôde ser lido. |
| Aviso | Mensagem ao usuário indicando campo não lido, de baixa confiança ou documento suspeito. |
| Acumulador | Configuração do Domínio que define como a nota é lançada. |

Definições completas: [SRS §1.3](SRS.md#13-definições-e-siglas).
