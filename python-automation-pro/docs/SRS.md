# SRS — Software Requirements Specification

**Conversor de Notas Fiscais em PDF para XML (ABRASF 2.01 / NF-e / CT-e OS)**

| Item | Valor |
| --- | --- |
| Versão do documento | 1.0 |
| Data | 25/11/2026 |
| Versão do sistema | v1.10.0 |
| Status | Rascunho para revisão |
| Público | Equipe interna / técnica |
| Estrutura | Inspirada na IEEE 830 / ISO/IEC/IEEE 29148 |
| Documentos relacionados | [BRD](BRD.md) · [FRD](FRD.md) · [TRD](TRD.md) |

---

## 1. Introdução

### 1.1 Propósito

Especificar os requisitos de software do conversor na versão v1.10.0: interfaces externas, requisitos funcionais (detalhados no [FRD](FRD.md)), requisitos não funcionais, restrições de projeto e rastreabilidade entre requisitos, módulos e testes. Público: mantenedores e revisores técnicos.

### 1.2 Escopo do produto

Aplicação desktop Windows (GUI Flet + CLI) que lê PDFs de documentos fiscais, identifica o layout entre 74 reconhecidos e gera XML ABRASF 2.01 (serviço), NF-e 4.00 (produto) ou CT-e OS 4.00 (transporte) para importação no sistema contábil Domínio. Escopo de negócio: [BRD §3](BRD.md#3-escopo).

### 1.3 Definições e siglas

| Termo | Definição |
| --- | --- |
| ABRASF 2.01 | Leiaute de XML de NFS-e (`CompNfse`, `InfDeclaracaoPrestacaoServico`). |
| ADN / Padrão Nacional | Leiaute XML da NFS-e nacional (`infNFSe`/`DPS`); **não** emitido pelo sistema. |
| Aviso | Mensagem anexada a uma nota (`Nfse.avisos`) sobre campo não lido, de baixa confiança ou documento suspeito. |
| CT-e OS | Conhecimento de Transporte Eletrônico para Outros Serviços, Modelo 67; documento auxiliar: DACTE OS. |
| DANFE | Documento auxiliar da NF-e (produto, Modelo 55). |
| DANFSe | Documento auxiliar da NFS-e do Portal Nacional (v1.0 e v2.0/reforma). |
| Layout | Modelo de documento reconhecido, identificado por uma constante `LAYOUT_*`. |
| NFCom | Nota Fiscal Fatura de Serviços de Comunicação. |
| OCR | Reconhecimento óptico de caracteres (Tesseract). |
| Onedir / onefile | Formatos de empacotamento PyInstaller: pasta (zip) ou executável único. |
| Recorte (recut) | Nova leitura OCR de uma região específica da página, com zoom/PSM/idioma próprios. |
| Sentinela | Valor neutro gravado quando o campo não foi lido (`00000000000000`, `0.00`, `XXXX-XXXX`, …). |
| Superset (layout) | Layout que herda os ramos de outro como fallback e só sobrepõe o tratamento novo. |

### 1.4 Referências

- `README.md`, `DOCUMENTACAO_CONVERSAO.md`, `COMO_USAR_GUI.md`, `CHANGELOG.md` (repositório).
- ABRASF — Leiaute NFS-e versão 2.01.
- LC 116/2003 (lista de serviços; art. 8º, II — alíquota máxima do ISS).
- Pacote de schemas PL_CTe_400 (CT-e/CT-e OS 4.00); leiaute NF-e 4.00.

## 2. Descrição geral

### 2.1 Perspectiva do produto

Ferramenta autônoma e local. Sem banco de dados, sem servidor. Única dependência de rede: API pública do GitHub para atualização da GUI. O XML gerado é importado manualmente no Domínio.

### 2.2 Classes de usuário

| Classe | Uso |
| --- | --- |
| Operador contábil | GUI; não técnico. |
| Usuário técnico / automação | CLI (`app.py` ou `nfse_converter_cli.exe`). |
| Mantenedor | Código-fonte, testes, build e release. |

### 2.3 Ambiente operacional

| Item | Requisito |
| --- | --- |
| SO | Windows (executáveis PyInstaller). Versões mínimas **A confirmar**. |
| OCR | Tesseract OCR em `C:\Program Files\Tesseract-OCR\tesseract.exe` (ou no PATH), com tessdata `por` (obrigatório), `eng` e `deu` (usados em recortes específicos). |
| Python (desenvolvimento) | `.venv` do projeto, Python 3.13 (3.13.12 no ambiente atual). |
| Rede | Opcional; só para atualização. |

### 2.4 Premissas e dependências

Ver [BRD §5](BRD.md#5-premissas). Dependência crítica: qualidade do scan e disponibilidade do Tesseract.

## 3. Interfaces externas

### 3.1 Interface com o usuário

| Interface | Descrição | Ref. |
| --- | --- | --- |
| GUI (`gui_app.py`, Flet 0.21.2) | Pastas de entrada/saída, "Tipo de Arquivo", formulário de contrato, log, barra de progresso, diálogos de senha, seleção de notas e atualização. | FRD §2.7, §2.9 |
| CLI (`app.py`) | `--input`/`--batch`/`--contrato`, `--output`, `--format`, `--pages`, `--password`. | FRD §2.8 |

### 3.2 Interface com o Domínio (saída)

| Documento | Formato emitido | Rota de importação no Domínio | Situação |
| --- | --- | --- | --- |
| NFS-e e serviço | ABRASF 2.01 (`CompNfse`, sem `xmlns`) | Importação de NFS-e — Arquivo XML | Em uso |
| DANFE (Modelo 55) | NF-e 4.00 (`nfeProc`) | Importação Padrão > NF-e Arquivo XML | Rejeita arquivo sem `det`; rota completa **A confirmar** |
| DACTE OS (Modelo 67) | CT-e OS 4.00 (`cteOSProc`) | Utilitários > Importação > Importação Padrão > CT-e e CT-eOS > Arquivo XML | Confirmada |
| Contrato de locação | ABRASF 2.01 | Mesma rota da NFS-e | Em uso |

Campos que o Domínio usa para escolher acumulador (ex.: `NaturezaOperacao`, retenções, `IssRetido`) são tratados como sensíveis; a lógica interna do Domínio é inferida, não verificada.

### 3.3 Interface com o GitHub Releases

| Item | Valor |
| --- | --- |
| Endpoint | `GET https://api.github.com/repos/<GITHUB_OWNER>/<GITHUB_REPO>/releases/latest` (constantes em `src/version.py`) |
| Autenticação | Nenhuma (API pública) |
| Assets esperados | `nfse_converter_gui.zip` (onedir) e `nfse_converter_gui.exe` (onefile) — nomes fixos |
| Falha | Checagem automática silenciosa; botão manual informa o resultado |

### 3.4 Interface com o Tesseract / tessdata

| Idioma | Uso |
| --- | --- |
| `por` | Leitura padrão de página e da maioria dos recortes |
| `eng` | Recortes com whitelist alfanumérica (ex.: códigos de verificação em que `por` confunde letras/dígitos) |
| `deu` | Leitura de número manuscrito (o "7" cortado à europeia) no Camaçari CPqD escaneado |

Ausência de `eng`/`deu` afeta apenas os recortes que os usam (comportamento exato sem o idioma: **A confirmar**).

### 3.5 Interface de arquivos

- Entrada: arquivos `.pdf` (pasta local ou de rede); JSON de contrato (UTF-8).
- Saída: XML por nota (`<pdf>[_Pagina_<p>]_NF_<n>.xml`), `CONTRATO_LOCACAO_<ANO>.xml`.
- Temporários: cópia desprotegida do PDF (apagada ao final), downloads e `.bat` de atualização em `%TEMP%`, log `%TEMP%\nfse_update_falhou.log`.

## 4. Requisitos específicos

### 4.1 Requisitos funcionais

Definidos no [FRD §2](FRD.md#2-requisitos-funcionais) (RF-001 a RF-095). Agrupamento:

| Área | RF |
| --- | --- |
| Entrada | RF-001 – RF-010 |
| Detecção de layout | RF-011 – RF-015 |
| Extração por campo | RF-016 – RF-026 |
| Regras fiscais e integridade | RF-030 – RF-044 |
| Geração de XML | RF-050 – RF-059 |
| Avisos e relatórios | RF-060 – RF-063 |
| GUI | RF-070 – RF-074 |
| CLI | RF-080 – RF-082 |
| Atualização automática | RF-090 – RF-095 |

### 4.2 Requisitos não funcionais

| ID | Categoria | Requisito | Verificação / evidência |
| --- | --- | --- | --- |
| RNF-01 | Desempenho | GUI abre em ~3 s (onedir) e ~8–12 s (onefile, extração para `%TEMP%` a cada abertura). Valores **observados**, não metas. | Medição registrada na decisão de empacotamento (TRD §6). |
| RNF-02 | Desempenho | Tempo de conversão por página digital/escaneada: **A confirmar** (não há medição registrada). OCR de página inteira usa zoom 3x; recortes usam 3x–9x. | — |
| RNF-03 | Desempenho | Página cujo render excede o limite de pixels do PIL é pulada no render de página inteira (sem travar). | `test_guarda_pixels_render_pil.py` |
| RNF-04 | Determinismo | A mesma página produz o mesmo texto em qualquer processo e posição do lote (desempate estável no agrupamento do pdfminer). | `test_pdfminer_ordem_deterministica_entre_pdfs.py` |
| RNF-05 | Determinismo | Extração sem estado compartilhado entre PDFs; nota distinta nunca descartada como duplicata. | Testes de lote/duplicidade |
| RNF-06 | Confiabilidade | Erro em um arquivo do lote não interrompe os demais. | `main.run_batch_conversion` |
| RNF-07 | Confiabilidade / integridade | Nenhum valor fiscal fabricado; sentinela + aviso (FRD RF-030–RF-044). | Testes de regressão com texto real |
| RNF-08 | Confiabilidade | Falha de rede na checagem de atualização não gera erro ao usuário; falha na troca do executável é registrada e exibida. | `test_auto_updater*.py` |
| RNF-09 | Segurança | Senha de PDF só em memória durante a execução; nunca logada, impressa ou gravada; cópia desprotegida apagada ao sair (com ou sem exceção). | `test_pdf_protegido_senha.py` |
| RNF-10 | Segurança | Na CLI, o usuário é avisado de que `--password` fica no histórico e na lista de processos. | Texto de ajuda do argumento |
| RNF-11 | Segurança | Atualização só a partir do Release publicado do repositório configurado, após confirmação do usuário. Verificação de integridade/assinatura do asset: **não há** (ver TRD §10). | `auto_updater.py` |
| RNF-12 | Portabilidade | Somente Windows (`.bat` de troca, `tasklist`, Toolhelp32 via `ctypes`, caminho padrão do Tesseract). | — |
| RNF-13 | Usabilidade | Mensagens em português; erros nunca vazios; `[AVISO]`/`[ERRO]` distinguíveis. | `test_pdf_protegido_senha.py`, `test_opcao_cte_os_modelo_67.py` |
| RNF-14 | Robustez de console | Nomes de arquivo com caracteres fora do code page não abortam a CLI. | `test_cli_console_encoding.py` |
| RNF-15 | Manutenibilidade | Novo layout adicionado sem reescrever o núcleo (constante + detecção + ramos por campo + teste com texto real). | Processo em `DOCUMENTACAO_CONVERSAO.md` |
| RNF-16 | Testabilidade | Suíte `pytest tests/` verde a cada entrega; testes baseados em texto real dos PDFs. Lógica de GUI extraída para módulos puros testáveis (`gui_selecao.py`, `ColetorDeSenhas`). | 1.818 testes (TRD §8) |
| RNF-17 | Fidelidade | Desproteção de senha pode alterar marginalmente a ordem de texto do pdfminer (28 de 29 PDFs idênticos em amostra). | Ressalva documentada |

### 4.3 Restrições de projeto

| ID | Restrição |
| --- | --- |
| RP-01 | Saída de serviço exclusivamente ABRASF 2.01; IBS/CBS descartados. |
| RP-02 | Cada tipo de documento tem modelo e transformer próprios (`Nfse`, `NfeProduto`, `CteOS`); um tipo nunca é emitido com as tags de outro. |
| RP-03 | Build sempre com o Python do `.venv` (flet 0.21.2); o Python do PATH (flet 0.82.2) gera executável que não abre. |
| RP-04 | Dependências de terceiros embarcadas: PIL, flet, numpy, pdfminer.six, pydantic, PyMuPDF, pytesseract, requests (+ `cryptography` para PDF criptografado). |
| RP-05 | Nomes dos assets do Release são contrato com instalações existentes e não podem mudar. |
| RP-06 | Correções e layouts novos partem de um caso real e entram com teste do texto real. |

## 5. Rastreabilidade

| RF (FRD) | Módulos principais | Testes representativos |
| --- | --- | --- |
| RF-001 – RF-003 | `extractors/pdf_extractor.py` (extração pdfminer, OCR, rotação), `utils/pdfminer_deterministico.py` | `test_ocr_rotacao_limiar_staummaq_scan3.py`, `test_danfse_nacional_reforma_texto_digital_sem_espacos.py`, `test_pdfminer_ordem_deterministica_entre_pdfs.py` |
| RF-004 – RF-006 | `src/main.py` (`run_conversion`, `run_batch_conversion`), `pdf_extractor.parse_multiple` | `test_pdf_extractor_pages.py`, `test_camacari_nota_duplicada_paginas_13_17_ph_gestao.py` |
| RF-007 | `main.parse_page_spec`, `src/gui_selecao.py` | `test_selecao_paginas.py`, `test_gui_selecao_varios_pdfs.py` |
| RF-008, RF-009 | `utils/pdf_senha.py`, `utils/erros.py`, `app.py` | `test_pdf_protegido_senha.py` |
| RF-010, RF-059 | `models/contrato_locacao_model.py`, `transformers/contrato_transformer.py` | `test_contrato_transformer.py` |
| RF-011 – RF-015 | `pdf_extractor._detect_layout`, `_detect_layout_page`, extratores auxiliares em `src/extractors/` | Um `test_<layout>_layout.py` por layout (ex.: `test_barueri_sp_layout.py`, `test_natal_rn_layout.py`) |
| RF-016 – RF-026 | `pdf_extractor._extrair_*`, `utils/ibge_resolver.py`, `models/nfse_models.py` | `test_data_emissao_prefere_horario_completo.py`, testes por layout |
| RF-030 – RF-033 | `pdf_extractor` (sentinelas, avisos, identidade Base × Alíquota) | `test_barreiras_valores_grade_locacao.py`, testes por layout |
| RF-034 | `pdf_extractor` (ramo São Paulo) | `test_sao_paulo_valor_total_recebido.py`, `test_sao_paulo_valor_recebido_qualquer_prestador.py`, `test_sp_flash_escaneada_valor_recebido_nautica_p5.py` |
| RF-035 | `pdf_extractor.ALIQUOTA_ISS_TETO` (guarda geral), `natal_nfse.py`, `eldorado_do_sul_nfse.py` | `test_salvador_instituicao_2278_scan.py`, `test_natal_rn_layout.py`, `test_eldorado_do_sul_layout.py` |
| RF-036 | `pdf_extractor`, `transformers/abrasf_transformer.py` | `test_lauro_freitas_mei_rotulo_valor_mesma_linha.py`, `test_danfse_nacional_reforma_mei_razao_social_apos_cnpj.py` |
| RF-037, RF-038 | `pdf_extractor` (competência, `municipio_incidencia_override`) | `test_osasco_nfse_layout.py`, `test_competencia_ano_ocr_trocado_generalizado.py` |
| RF-039, RF-040 | `abrasf_transformer._outras_retencoes_total` | `test_danfse_nacional_retencoes_federais.py` |
| RF-041 | `pdf_extractor.NOTA_CANCELADA_PATTERN` | `test_lauro_freitas_tessera_prefeitura_vs_enotas.py` |
| RF-042 | `pdf_extractor` (recorte Camaçari, `deu`) | `test_camacari_cpqd_escaneada_guarajuba_p8.py` |
| RF-050 – RF-053, RF-058 | `transformers/abrasf_transformer.py`, `main._pick_transformer` | `test_transformer.py`, `test_rio_xml.py`, `test_gui_nome_xml.py` |
| RF-054 | `models/nfe_produto_models.py`, `transformers/nfe_produto_transformer.py`, `extractors/danfe_produto_texto.py`, `main.aviso_nfe_sem_itens` | `test_danfe_produto_*.py` |
| RF-055, RF-056 | `models/cte_os_model.py`, `transformers/cte_transformer.py`, `extractors/dacte_os_texto.py`, `main.separar_por_formato` | `test_cte_os_leiaute_oficial_4_00.py`, `test_dacte_os_*.py`, `test_opcao_cte_os_modelo_67.py` |
| RF-057 | `transformers/nfe_transformer.py` | `test_nfe_transformer.py` |
| RF-060 – RF-063 | `models/nfse_models.Nfse.avisos`, `main._reportar`, `utils/erros.descrever_erro` | `test_pdf_protegido_senha.py`, `test_opcao_cte_os_modelo_67.py` |
| RF-070 – RF-074 | `gui_app.py`, `src/gui_selecao.py`, `pdf_senha.ColetorDeSenhas` | `test_gui_selecao_varios_pdfs.py`, `test_gui_nome_xml.py` (o código Flet não tem teste automatizado) |
| RF-080 – RF-082 | `app.py` | `test_cli_console_encoding.py`, `test_selecao_paginas.py`, `test_opcao_cte_os_modelo_67.py` |
| RF-090 – RF-095 | `utils/auto_updater.py`, `src/version.py`, `gui_app.py` | `test_auto_updater.py`, `test_auto_updater_onedir_e_falhas.py` |

## 6. Apêndice — Itens a confirmar

| Item | Seção |
| --- | --- |
| Versões mínimas de Windows suportadas | §2.3 |
| Tempo de conversão por página | RNF-02 |
| Comportamento sem tessdata `eng`/`deu` | §3.4 |
| Rota completa de importação de NF-e no Domínio | §3.2 |
