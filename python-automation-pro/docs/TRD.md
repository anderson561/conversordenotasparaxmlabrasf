# TRD — Technical Requirements Document

**Conversor de Notas Fiscais em PDF para XML (ABRASF 2.01 / NF-e / CT-e OS)**

| Item | Valor |
| --- | --- |
| Versão do documento | 1.0 |
| Data | 25/11/2026 |
| Versão do sistema | v1.10.0 |
| Status | Rascunho para revisão |
| Público | Equipe interna / técnica |
| Documentos relacionados | [BRD](BRD.md) · [FRD](FRD.md) · [SRS](SRS.md) |

---

## 1. Arquitetura

Camadas com dependência em um único sentido; a leitura não conhece a escrita.

```
┌──────────── Apresentação ────────────┐
│ gui_app.py (Flet)      app.py (CLI)  │
└───────────────┬──────────────────────┘
                ▼
┌──────────── Orquestração ────────────┐
│ src/main.py  run_conversion / run_batch_conversion / run_contrato_conversion
│              separar_por_formato · _pick_transformer · relatórios
│ src/gui_selecao.py (lógica pura da seleção de notas e nomes de XML)
│ src/utils/pdf_senha.py (desproteção na entrada)
└───────────────┬──────────────────────┘
                ▼
┌──────────── Extração ────────────────┐
│ src/extractors/pdf_extractor.py  SPPdfExtractor
│   texto (pdfminer) | OCR (PyMuPDF → PIL → Tesseract)
│   _detect_layout / _detect_layout_page → _extrair_* por campo
│   + extratores auxiliares por layout/documento
└───────────────┬──────────────────────┘
                ▼
┌──────────── Modelo (Pydantic) ───────┐
│ Nfse · NfeProduto · CteOS · ContratoLocacao
└───────────────┬──────────────────────┘
                ▼
┌──────────── Transformação ───────────┐
│ Abrasf201Transformer · NfeProdutoTransformer · CteTransformer
│ NfeTransformer · ContratoLocacaoTransformer          → XML
└──────────────────────────────────────┘
```

Princípios arquiteturais em vigor:

| Princípio | Aplicação |
| --- | --- |
| Isolamento leitura × escrita | O extrator só preenche o modelo; o transformer não conhece o PDF. |
| Roteamento pelo tipo real | `_pick_transformer` decide pelo tipo do objeto (`NfeProduto`/`CteOS`), não pela opção da GUI. |
| Um tipo de documento = um modelo + um transformer | Nenhum documento emitido com as tags de outro (ex.: CT-e nunca como `infNFe`). |
| Superset de layout | Variante nova herda a anterior como fallback (ex.: `camacari_ba_scan_v3` ⊃ `camacari_ba_scan` ⊃ `camacari_cpqd`), evitando regressão no código validado. |
| Sentinela + aviso | Valor não lido nunca é inventado (ver [FRD §2.4](FRD.md#24-regras-fiscais-e-de-integridade)). |

## 2. Módulos e responsabilidades

| Módulo | Linhas | Responsabilidade |
| --- | --- | --- |
| `app.py` | 95 | CLI (argparse), console tolerante a encoding, códigos de saída. |
| `gui_app.py` | 952 | GUI Flet: formulários, threads de conversão, diálogos (senha, seleção, atualização), log. |
| `src/main.py` | 326 | Orquestração de conversão única/lote/contrato, nomes de XML, relatórios, roteamento de transformer. |
| `src/gui_selecao.py` | 149 | Lógica pura (testável) da seleção de notas em um ou vários PDFs. |
| `src/version.py` | 10 | `APP_VERSION`, `GITHUB_OWNER`, `GITHUB_REPO` (fonte única da versão). |
| `src/extractors/pdf_extractor.py` | 30.654 | `SPPdfExtractor`: texto/OCR, detecção dos layouts, extração por campo, recortes, validações, avisos, construção do modelo (`parse`, `parse_multiple`). |
| `src/extractors/danfe_produto_texto.py` | 1.084 | DANFE (NF-e Modelo 55) por estrutura. |
| `src/extractors/dacte_os_texto.py` | 300 | DACTE OS (CT-e Modelo 67). |
| `src/extractors/{natal_nfse, eldorado_do_sul_nfse, saubara_nfse, feira_nfse_nacional, ribeirao_pires_texto, sp_identificador, localiza_fatura, nota_locacao, nota_debito_locacao, fatura_locacao_periodo, fatura_locacao_equipamentos, danfse_rotulos_imagem}.py` | 176–731 cada | Extratores dedicados de layouts mais recentes, isolados do monólito. |
| `src/models/nfse_models.py` | 73 | `Nfse`, `Entidade`, `Endereco`, `Valores` (inclui `avisos`, `pagina_origem`, `municipio_incidencia_override`). |
| `src/models/nfe_produto_models.py` | 89 | `NfeProduto`, itens, transportador, totais. |
| `src/models/cte_os_model.py` | 124 | `CteOS`, modal rodoviário, impostos/retenções. |
| `src/models/contrato_locacao_model.py` | 52 | `ContratoLocacao`. |
| `src/transformers/abrasf_transformer.py` | 260 | XML ABRASF 2.01 (`CompNfse`, `ListaNfse`). |
| `src/transformers/nfe_produto_transformer.py` | 290 | XML NF-e 4.00 de DANFE. |
| `src/transformers/cte_transformer.py` | 333 | XML CT-e OS 4.00 (`cteOSProc`). |
| `src/transformers/nfe_transformer.py` | 198 | NF-e a partir de `Nfse` (opção `--format nfe`). |
| `src/transformers/contrato_transformer.py` | 191 | XML ABRASF de contrato de locação. |
| `src/utils/ibge_resolver.py` | 330 | Código IBGE: tabela `KNOWN_CITIES` → código impresso → capital (fallback com aviso). |
| `src/utils/pdf_senha.py` | 160 | Detecção/validação de senha, cópia temporária desprotegida, `ColetorDeSenhas`. |
| `src/utils/pdfminer_deterministico.py` | 121 | Patch de desempate estável no `group_textboxes` do pdfminer. |
| `src/utils/auto_updater.py` | 496 | Checagem de Release, download, troca do executável/pasta, limpeza. |
| `src/utils/erros.py` | 25 | `descrever_erro`, `NenhumCteOsError`. |
| `tools/build_excludes.py` | — | Lista única de exclusões dos três `.spec`. |
| `tools/gen_version_info.py` | — | Gera `version_info.txt` a partir de `src/version.py`. |
| `tools/empacota_release.py` | — | Compacta o onedir em `dist/nfse_converter_gui.zip`. |

## 3. Pipeline de extração e OCR

1. **Desproteção** (`pdf_desprotegido`): PDF com senha de usuário vira cópia temporária sem criptografia (PyMuPDF), com o mesmo nome-base; apagada ao sair.
2. **Texto digital** (pdfminer.six): `extract_text`/`extract_pages`; para geradores que despejam valores fora de ordem, reconstrução por coordenadas de caractere (`_reconstruir_texto_por_coordenadas`).
3. **Decisão de OCR**: página sem texto, camada de texto ilegível, texto digital sem espaços ou DANFSe só com valores → OCR.
4. **OCR de página** (PyMuPDF → PNG → PIL → `pytesseract`, `lang='por'`):
   - zoom **3x** (validado como melhor custo-benefício; 2x perde barras de CNPJ, 5x fragmenta a discriminação);
   - teste das 4 rotações quando a qualidade (`_score_ocr_text`) é baixa;
   - PSM 6/4/7 conforme o layout;
   - guarda de pixels: render que excede o limite do PIL é pulado.
5. **Recortes dedicados** (≈176 funções `_ocr_recut*`/`_ocr_clip_leituras`/`_score_ocr_text`): região do campo relida com zoom 3x–9x, PSM e whitelist próprios; idiomas `eng` (códigos alfanuméricos) e `deu` (número manuscrito); desentorto da faixa de cabeçalho com numpy; escolha por **maioria/consenso** entre leituras e por identidades (DV, mod-11, Base × Alíquota = ISS, teto de 5%).
6. **Detecção de layout** (`_detect_layout` no documento, `_detect_layout_page` por página): DANFE e DACTE OS primeiro, depois as marcas de cada layout, genérico por último.
7. **Extração por campo** (`_extrair_numero`, `_extrair_valores`, `_extrair_entidade`, `_extrair_data_emissao`, …) com ramos por layout.
8. **Validações e avisos** gerais no ponto único de construção do modelo (nota cancelada, teto do ISS, município IBGE de fallback).

Executável do Tesseract, resolvido num só lugar (`src/utils/tesseract_config.py`, `configurar_pytesseract`): variável de ambiente `TESSERACT_CMD` (se apontar para um arquivo existente) → `C:\Program Files\Tesseract-OCR\tesseract.exe` quando existe → o do PATH. A pasta de idiomas segue a `TESSDATA_PREFIX` do próprio Tesseract.

## 4. Determinismo do pdfminer

- **Problema**: `LTLayoutContainer.group_textboxes` desempata distâncias iguais por `id()` (endereço de memória). Em colunas simétricas, a ordem do texto variava conforme o que o processo alocou antes (medido: 23 × 17 em 40 extrações da mesma página), trocando campos de prestador e tomador em lote.
- **Solução**: `src/utils/pdfminer_deterministico.py` substitui o `id()` por número de sequência estável; aplicado uma vez no import de `src.extractors` (idempotente).
- **Requisito de manutenção**: o corpo é cópia do método do pdfminer.six **20260107**. Ao atualizar o pdfminer, conferir o método original e rodar `tests/test_pdfminer_ordem_deterministica_entre_pdfs.py`.

## 5. Stack e versões

| Componente | Versão (`.venv`) | Uso |
| --- | --- | --- |
| Python | 3.13 (3.13.12) | Runtime e build |
| flet | **0.21.2** (flet-core/runtime 0.21.2) | GUI |
| pdfminer.six | 20260107 | Texto digital (patch de determinismo amarrado a esta versão) |
| PyMuPDF | 1.27.2.2 | Render de página, desproteção |
| pytesseract | 0.3.13 | Ponte para o Tesseract |
| Tesseract OCR | externo; versão **A confirmar** | OCR (`por`, `eng`, `deu`) |
| Pillow | 12.1.1 | Imagens para OCR |
| numpy | 2.4.3 | Desentorto da faixa de cabeçalho |
| pydantic | 2.12.5 | Modelos |
| requests | 2.32.5 | API do GitHub / download |
| cryptography | 46.0.5 | PDF criptografado (pdfminer) |
| PyInstaller | 6.19.0 (+ hooks-contrib 2026.3) | Build |
| pytest | 9.0.2 | Testes |

**Armadilha**: o Python do PATH tem flet **0.82.2** (ícones migraram para `flet.controls.material.icons`); o executável construído com ele abre e morre com `has no attribute 'SYSTEM_UPDATE'`. Usar sempre `.venv\Scripts\python.exe`.

`requirements.txt` é um snapshot do `.venv` (UTF-16) que é compartilhado com outros projetos e inclui pacotes que o app não usa; a superfície real de terceiros é `PIL, flet, numpy, pdfminer, pydantic, pymupdf, pytesseract, requests`.

## 6. Build (PyInstaller)

| Comando | Resultado |
| --- | --- |
| `build.bat` | GUI onedir (`dist\nfse_converter_gui\`) + CLI onefile (`dist\nfse_converter_cli.exe`) |
| `build.bat release` | o acima + `dist\nfse_converter_gui.zip` (onedir zipado) + `dist\nfse_converter_gui.exe` (onefile) |
| `build.bat limpo` | descarta o cache em `build\` e refaz do zero |

| `.spec` | Formato | Console | Observação |
| --- | --- | --- | --- |
| `nfse_converter_gui.spec` | onedir | não | Formato principal (abertura ~3,4 s, sem extração em `%TEMP%`) |
| `nfse_converter_gui_onefile.spec` | onefile | não | Asset de transição para instalações ≤ v1.7.0 (~12 s; extrai ~206 MB a cada abertura) |
| `nfse_converter_cli.spec` | onefile | sim | Não publicado no Release |

Regras de build:

- `.spec` fixos e versionados; `version_info.txt` gerado por `tools/gen_version_info.py`.
- Sem `--clean` (destrói o cache); sem UPX.
- Exclusões em `tools/build_excludes.py` (scipy, pandas, matplotlib, cv2, torch, pytest, …). **Não excluir**: `numpy`, `cryptography`, `libmpv-2.dll`, `flutter_windows.dll`, `libGLESv2.dll` (dependências de link do `flet.exe`).
- Sem build incremental real: a análise de imports roda sempre (~50 s); rebuild sem mudança ~57 s.
- App aberto trava `dist\` ("Acesso negado"): construir com `--distpath build\<pasta>`.
- **Prova de build**: conversão real pela CLI construída (XML parseia e traz número/valor/CNPJ/município corretos). "A janela abriu" não prova o bundle.

## 7. Release e atualização automática

Processo (detalhe em `DOCUMENTACAO_CONVERSAO.md` › Processo de Release):

1. Atualizar `APP_VERSION` em `src/version.py` antes do build.
2. `build.bat release`.
3. Criar e enviar a tag `vX.Y.Z`.
4. Publicar o Release (não draft/pre-release) com **os dois** assets, nomes inalterados: `nfse_converter_gui.zip` e `nfse_converter_gui.exe`.
5. Conferir no ar: `/releases/latest` + `auto_updater.is_newer(tag, versão_antiga)`.

Auto-updater (`src/utils/auto_updater.py`, só GUI):

| Etapa | Implementação |
| --- | --- |
| Checagem | Thread ao abrir + botão manual; `check_latest_release` (GitHub API pública). |
| Comparação | `is_newer` — SemVer `(major, minor, patch)`, tolera `v`. |
| Formato | `is_onedir()` compara `sys._MEIPASS` com a pasta do executável → asset `.zip` ou `.exe` (`find_update_asset`). |
| Download | `download_asset` com progresso para `%TEMP%`. |
| Troca | `.bat` gerado em runtime aguarda o PID sair, tenta `move` 10× a cada 2 s, relança e se autoapaga; onedir renomeia a pasta atual e restaura em falha. |
| Encerramento | Processos filhos (incl. `flet.exe`) enumerados via Toolhelp32 (`ctypes`) e encerrados um a um; depois `os._exit(0)`. |
| Falha | `%TEMP%\nfse_update_falhou.log`, lido e exibido na abertura seguinte (`ler_falha_pendente`). |
| Limpeza | `limpar_restos_de_updates` remove restos com mais de 24 h. |

## 8. Testes

| Item | Valor |
| --- | --- |
| Comando | `.venv\Scripts\python.exe -X utf8 -m pytest tests/ -q -p no:cacheprovider` (sempre `tests/`, nunca `pytest` sem caminho) |
| Arquivos | 220 em `tests/` |
| Casos | 1.818 coletados; em 25/11/2026: **1797 aprovados, 21 pulados** (≈ 70 s) |
| Pulados | Dependem de recursos locais: PDFs reais do corpus fora do repositório e XSD oficial do CT-e 4.00 (`CTE_OS_XSD_DIR`). |

Padrão de testes:

- Um `test_<layout>_layout.py` por layout + um arquivo por achado real (`test_<layout>_<caso>.py`).
- Entradas são o **texto real** do PDF (OCR e/ou digital) embutido no teste, não mocks limpos; quando o PDF real está disponível, testes adicionais rodam ponta a ponta.
- Toda regra de integridade tem teste que trava o comportamento (ex.: zero legítimo preservado; mudar só o líquido não move `ValorServicos`; leitura OCR com teto conhecido fixada).
- Código Flet (`gui_app.py`) não tem cobertura; a lógica testável é extraída para `src/gui_selecao.py` e `ColetorDeSenhas`. Correção só de GUI exige build e verificação manual.

## 9. Convenções de desenvolvimento

| Tema | Convenção |
| --- | --- |
| Branches | Uma frente por branch, a partir de `main`: `fix/<layout>-<caso>`, `feat/<layout>`, `docs/…`, `chore/…`. Trabalho isolado em worktree. |
| Commits | Conventional Commits em português com escopo do layout: `fix(salvador): …`, `feat(natal): …`, `chore(release): vX.Y.Z`. |
| Integração | Pull Request para `main` e merge; release a partir de `main`. |
| Versionamento | SemVer; tag `vX.Y.Z` = `APP_VERSION`. |
| Docs gate (no mesmo commit/PR) | Suíte verde; `CHANGELOG.md` (Keep a Changelog, `## [Não lançado]`); `DOCUMENTACAO_CONVERSAO.md` quando o comportamento de um layout muda; `README.md` com nova entrada no rodapé em cascata (sempre) e contadores de layouts quando aplicável. |
| Contagem de layouts | Derivada: constantes `LAYOUT_*` (77) − 4 (3 fora da contagem + genérico) = 73 específicos; total = 74. README e `DOCUMENTACAO_CONVERSAO.md` mudam juntos. |
| Novo layout | Constante `LAYOUT_*`; marca em `_detect_layout` **e** `_detect_layout_page`; ramos `_extrair_*`; `IBGEResolver.KNOWN_CITIES`; teste com texto real. |

## 10. Limitações conhecidas e débitos técnicos

Itens já registrados no código, no CHANGELOG ou em `DOCUMENTACAO_CONVERSAO.md`, exceto os marcados *(observação)*, constatados na leitura do código para este documento.

| ID | Item | Impacto |
| --- | --- | --- |
| DT-01 | `NaturezaOperacao` fixa em `"1"` no `Abrasf201Transformer`. | Notas isentas/imunes/fora do município declaradas como tributadas no município; pode afetar o acumulador no Domínio. Correção não aprovada. |
| DT-02 | Fallback IBGE: município fora da tabela → capital da UF (com aviso); município vazio → código padrão; transformer usa `3550308` (São Paulo) se o código chegar vazio. | Código de município errado possível; aviso só para `Nfse` (não `CteOS`/`NfeProduto`). |
| DT-03 | NF-e sem itens é gravada sem `det` + `[ERRO]`. | Domínio rejeita o arquivo; decisão final adiada. |
| DT-04 | Não há transformer para o Padrão Nacional/ADN da NFS-e. | Só ABRASF 2.01. |
| DT-05 | `gui_app.py` sem testes automatizados. | Correções de GUI dependem de verificação manual. |
| DT-06 | Desproteção por cópia regravada pode alterar a ordem de texto do pdfminer (1 em 29 na amostra). | Alternativa documentada: passar `password=` direto aos pontos do pdfminer. |
| DT-07 | Recortes OCR de página inteira dependem de memória do Tesseract; sob pressão (`pixdata_malloc fail`) voltam vazios. | Nota sai só com a leitura padrão. |
| DT-08 | Limites de leitura OCR conhecidos (ex.: caractere que nenhuma combinação lê corretamente). | Leitura gravada como lida, documentada e travada por teste; nunca corrigida por regra fixa. |
| DT-09 | `pdf_extractor.py` concentra ~30,6 mil linhas. *(observação)* | Alto custo de navegação/regressão; layouts novos já vão para módulos próprios. |
| DT-10 | Patch de determinismo copia um método interno do pdfminer.six 20260107. | Atualizar o pdfminer exige revalidar o patch. |
| DT-11 | ~~Caminho do Tesseract fixo para `C:\Program Files\Tesseract-OCR` (fallback: PATH).~~ **Resolvido** (25/11/2026): os 8 pontos que fixavam o caminho (`pdf_extractor.py` ×4, `danfse_rotulos_imagem.py`, `eldorado_do_sul_nfse.py`, `feira_nfse_nacional.py`, `natal_nfse.py`) chamam `src/utils/tesseract_config.py`; ordem `TESSERACT_CMD` → caminho padrão → PATH. Testes: `tests/test_tesseract_config.py`. | Instalação em outro local: basta definir `TESSERACT_CMD`. Sem a variável, comportamento idêntico ao anterior. |
| DT-12 | Asset de atualização baixado sem verificação de hash/assinatura. *(observação)* | Confiança depende da integridade do Release no GitHub. Mitigação **A confirmar**. |
| DT-13 | `requirements.txt` não reflete a superfície real de dependências (snapshot do `.venv` compartilhado, UTF-16). *(observação)* | Instalação limpa traz pacotes desnecessários. |
| DT-14 | Sem migração automática entre formatos onefile → onedir. | Usuário em onefile migra manualmente baixando o `.zip`. |
