# Conversor de Notas Abrasf

## Visão Geral

Este projeto fornece um conversor de PDFs de Notas Fiscais de Serviço (NFS‑e) e Contratos de Locação para o padrão **ABRASF 2.01 XML**. Ele inclui:

- **Extratores de PDF** com detecção automática de layout, cobrindo **38 layouts** (37 específicos + genérico de fallback) de múltiplos municípios e emissores:
  - **Prefeituras/NFS-e:** Cuiabá/MT, Barreiras/BA, Camaçari/BA (digital, escaneado/OCR **e Nota Avulsa da Prefeitura** — três layouts dedicados), Salvador/BA, Feira de Santana/BA, Simões Filho/BA, Lauro de Freitas/BA, Iaçu/BA, Mata de São João/BA (plataforma SAATRI), Rosário da Limeira/MG (plataforma FUTURIZE), Rio de Janeiro/RJ (Nota Carioca), São Paulo/SP (digital **e escaneado/OCR** como layouts dedicados), Ribeirão Pires/SP, Campinas/SP, Joinville/SC, Fortaleza/CE, Brasília/DF (GDF) e o Portal Nacional (DANFSe v1.0).
  - **Faturas de locação / serviços específicos:** Localiza Rent A Car, CPE Tecnologia, Guincho Cidade, B.F. Serviços Ambientais, LMR Engenharia, Geração & Energia, Locontainers, SUL&SEG (Nota de Cobrança), F&F Comércio (locação de CFTV, escaneada), **PJB Construção** (locação de máquinas, Simões Filho/BA, escaneada), **Fatura de Locação Genérica** (qualquer locadora não catalogada) e **ARMAC** (escaneada, tabela multi-item).
  - **Outros:** NF-e de Serviço de Comunicação (Telecom), Osasco/SP NF-R de Repasse (ex.: iFood Benefícios), PASSWORD/eNotas Gateway (NFS-e tributada), ISBET (Nota de Contribuição) e um layout **Genérico** de fallback.
- **OCR integrado** (Tesseract via `pytesseract` + PyMuPDF) para PDFs escaneados/imagem sem camada de texto — o extrator tolera os erros de reconhecimento típicos de cada layout.
- **Transformadores** que mapeiam os dados extraídos para o XML ABRASF 2.01.
- **Interface de linha de comando** (`app.py`) para conversões individuais ou em lote.
- **Interface gráfica** (`gui_app.py`) baseada em *flet* para usuários não‑técnicos.
- **Gerador de contratos de locação** a partir de JSON, produzindo XML pronto para importação.

## Principais Funcionalidades

- Suporte a múltiplos layouts de NFS‑e com detecção automática (`_detect_layout`).
- OCR automático para PDFs escaneados (sem texto extraível).
- Processamento de PDFs com múltiplas páginas e múltiplas notas por página.
- Geração de lote XML (`ListaNfse`).
- Conversão de contratos de locação (dados preenchidos via GUI ou JSON).
- **Avisos de baixa confiança** (`Nfse.avisos`): sinaliza quando um campo caiu em valor de fallback (número/CNPJ zerado, data atual, valor zero) em vez de falhar silenciosamente.
- Logs detalhados e barra de progresso.

## Como Instalar

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt  # dependências principais
pip install "flet[desktop]"   # para a GUI
```

## Uso via CLI

```bash
# Conversão de um PDF único
python app.py --input path/to/file.pdf --output path/to/output.xml

# PDF com várias notas: converter só páginas específicas (alternadas ou intervalo)
python app.py --input path/to/file.pdf --output path/to/output.xml --pages "1,3,6"
python app.py --input path/to/file.pdf --output path/to/output.xml --pages "1-3,6"

# Conversão em lote (diretório)
python app.py --batch path/to/pdfs --output path/to/output_dir

# Conversão de contrato de locação (JSON)
python app.py --contrato path/to/contrato.json --output path/to/output_dir
```

> `--pages` vale só com `--input` (um único PDF). Aceita páginas soltas (`1,3,6`) e intervalos (`1-3,6`); a numeração é a **página real do PDF** (1-based) e só páginas com nota reconhecida são geradas. Na GUI, o mesmo é feito pela janela de seleção com caixas por página (ver [COMO_USAR_GUI.md](COMO_USAR_GUI.md)).

## Uso via GUI

```bash
python gui_app.py
```

## Estrutura de Diretórios

```
python-automation-pro/
├─ src/                     # Código-fonte principal
│  ├─ extractors/           # Extratores de PDF (pdf_extractor.py: SPPdfExtractor)
│  ├─ transformers/         # Transformadores para XML (abrasf_transformer.py)
│  ├─ models/               # Modelos de dados Pydantic (Nfse, Entidade, Endereco, Valores)
│  └─ utils/                # Utilidades auxiliares (ibge_resolver.py, etc.)
├─ tests/                   # Testes unitários (um test_<cidade>_layout.py por layout)
├─ templates/               # Templates de UI (se houver)
├─ gui_app.py               # Aplicação de desktop baseada em flet
├─ app.py                   # CLI de alto nível
├─ DOCUMENTACAO_CONVERSAO.md# Detalhamento de cada layout suportado
├─ COMO_USAR_GUI.md         # Guia da interface gráfica
└─ README.md                # Documentação principal (este arquivo)
```

## Adicionando um Novo Layout

O extrator é escalável por layout, sem reescrever o núcleo. O checklist típico (ver detalhes em [DOCUMENTACAO_CONVERSAO.md](DOCUMENTACAO_CONVERSAO.md)):

1. Definir a constante `LAYOUT_<NOME>` em `pdf_extractor.py`.
2. Adicionar a marca de detecção em `_detect_layout` **e** `_detect_layout_page`.
3. Plugar ramos específicos onde o layout divergir do genérico (`_extrair_numero`, `_extrair_valores`, `_extrair_entidade`, etc.).
4. Registrar a cidade no `IBGEResolver.KNOWN_CITIES` (`src/utils/ibge_resolver.py`) quando aplicável.
5. Criar `tests/test_<nome>_layout.py` validando contra o **texto real** do PDF (imagem→OCR e/ou digital), não só mocks limpos.

## Contribuição

1. Fork o repositório.
2. Crie uma branch para sua feature (`git checkout -b feature/minha-feature`).
3. Submeta seus testes e documentação.
4. Abra um Pull Request.

---

*Documentação atualizada em 2026‑08‑04 (38 layouts suportados; regra de negócio no DANFSe Nacional — quando a nota traz "TOMADOR DO SERVIÇO NÃO IDENTIFICADO NA NFS-e" (campo em branco na origem) mas há um INTERMEDIÁRIO identificado, o intermediário é promovido a tomador e o bloco `<Intermediario>` é esvaziado (nota nº 44, pág.18 do lote Guarajuba Suítes: o MEI prestador lançou a PH Gestão como intermediário e deixou o tomador vazio; para a contabilidade, a PH Gestão é o tomador efetivo — decisão do usuário, regra geral gated por layout); junto, dois fixes no parser de entidade DANFSe: município lido pelo padrão "<Cidade> - <UF> <CEP>" (o rótulo "Município" é cabeçalho de coluna e o valor real fica na linha de valores — antes o resolver pescava a capital "Salvador" do topo do documento) e limpeza da razão social (prefixo do CNPJ com vírgula e inicial isolada da coluna "E-mail" vazada no fim); zero regressão (baseline-vs-fix no lote de 21 notas muda só a nota-alvo). Antes: fix no Osasco/NF-R de Repasse (iFood) ESCANEADO — a detecção do layout já funcionava no OCR, mas as âncoras de extração (feitas para o NF-R digital) quebravam no ruído do scan: número "Nota No,:" (vírgula no lugar do ponto) caía para "00000000", rótulo do CNPJ do tomador degradado ("CPF/CNPJ"→"CEF/CNPI") zerava o CNPJ, e "UF; BA" (ponto-e-vírgula) fazia o UF cair no default SP — com o resolver chamado sem city_hint, Camaçari/BA virava São Paulo/SP; corrigido de forma aditiva/gated (número tolera vírgula; CNPJ do tomador tem fallback ao 1º CNPJ bem-formado do bloco, imune ao rótulo garblado; UF tolera ";"; city_hint passado; e a hora de emissão agora é capturada do rodapé "emitida em … às HH:MM:SS") — nota nº 2279456 iFood, pág.8 do lote Guarajuba Suítes, agora com número/tomador/município corretos, zero regressão nas outras 19 notas do lote. Antes: fix no Camaçari escaneado com página TORTA — quando o scan está levemente inclinado (~1°), a linha "Número da Nota" (a mais alta da célula do cabeçalho) sai do enquadramento dos recortes fixos e a âncora do número não casa, fazendo o número desabar para o fallback "00000000" (nota nº 246, AVANÇO GESTÃO, pág.29 do lote PH Gestão); corrigido com um 3º recorte aditivo que estima a inclinação fina por página (±3°, por variância do perfil horizontal), desentorta e reprocessa a célula — recupera "Número da Nota → 246" sem tocar nos recortes já validados (zero regressão). Antes: fix no Camaçari escaneado — o recorte largo do cabeçalho lia a Inscrição Municipal do prestador no lugar da célula "Número/Data/Código", fazendo sair número e data de emissão errados; corrigido com um recorte estreito aditivo da célula + extração robusta (rejeita candidato de ≥8 dígitos como número, tolera rótulo com 1ª letra cortada, exige letra+dígito no código de autenticidade). Antes: novo layout PJB Construção — fatura de locação de máquinas/bens móveis escaneada, Simões Filho/BA, sem incidência de ISS; detecção no topo da cadeia por razão do emitente + marcador estrutural da fatura, para não colidir com os layouts municipais homônimos citados na nota nem com a planilha-resumo que lista o fornecedor; prestador fixo e tomador parseado do bloco DESTINATÁRIO. Anteriormente: novo layout F&F Comércio — fatura de locação de CFTV; fixes de robustez no Localiza — 2 estruturas de texto —, no São Paulo digital — extração de entidades/valores da nota AMIL —, no Camaçari escaneado — recorte do cabeçalho cortava o número da nota —, no Barreiras — grade de valores da locação de bens móveis caía no fallback zero — e no São Paulo (digital+escaneado) — endereço em linha única e intermediário fantasma).* — quando o scan está levemente inclinado (~1°), a linha "Número da Nota" (a mais alta da célula do cabeçalho) sai do enquadramento dos recortes fixos e a âncora do número não casa, fazendo o número desabar para o fallback "00000000" (nota nº 246, AVANÇO GESTÃO, pág.29 do lote PH Gestão); corrigido com um 3º recorte aditivo que estima a inclinação fina por página (±3°, por variância do perfil horizontal), desentorta e reprocessa a célula — recupera "Número da Nota → 246" sem tocar nos recortes já validados (zero regressão). Antes: fix no Camaçari escaneado — o recorte largo do cabeçalho lia a Inscrição Municipal do prestador no lugar da célula "Número/Data/Código", fazendo sair número e data de emissão errados; corrigido com um recorte estreito aditivo da célula + extração robusta (rejeita candidato de ≥8 dígitos como número, tolera rótulo com 1ª letra cortada, exige letra+dígito no código de autenticidade). Antes: novo layout PJB Construção — fatura de locação de máquinas/bens móveis escaneada, Simões Filho/BA, sem incidência de ISS; detecção no topo da cadeia por razão do emitente + marcador estrutural da fatura, para não colidir com os layouts municipais homônimos citados na nota nem com a planilha-resumo que lista o fornecedor; prestador fixo e tomador parseado do bloco DESTINATÁRIO. Anteriormente: novo layout F&F Comércio — fatura de locação de CFTV; fixes de robustez no Localiza — 2 estruturas de texto —, no São Paulo digital — extração de entidades/valores da nota AMIL —, no Camaçari escaneado — recorte do cabeçalho cortava o número da nota —, no Barreiras — grade de valores da locação de bens móveis caía no fallback zero — e no São Paulo (digital+escaneado) — endereço em linha única e intermediário fantasma).*
