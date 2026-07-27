# Conversor de Notas Abrasf

## Visão Geral

Este projeto fornece um conversor de PDFs de Notas Fiscais de Serviço (NFS‑e) e Contratos de Locação para o padrão **ABRASF 2.01 XML**. Ele inclui:

- **Extratores de PDF** com detecção automática de layout, cobrindo **34 layouts** (33 específicos + genérico de fallback) de múltiplos municípios e emissores:
  - **Prefeituras/NFS-e:** Cuiabá/MT, Barreiras/BA, Camaçari/BA (digital **e escaneado/OCR** como layouts dedicados), Salvador/BA, Feira de Santana/BA, Simões Filho/BA, Lauro de Freitas/BA, Iaçu/BA, Mata de São João/BA (plataforma SAATRI), Rio de Janeiro/RJ (Nota Carioca), São Paulo/SP (digital **e escaneado/OCR** como layouts dedicados), Ribeirão Pires/SP, Campinas/SP, Joinville/SC, Fortaleza/CE, Brasília/DF (GDF) e o Portal Nacional (DANFSe v1.0).
  - **Faturas de locação / serviços específicos:** Localiza Rent A Car, CPE Tecnologia, Guincho Cidade, B.F. Serviços Ambientais, LMR Engenharia, Geração & Energia, Locontainers, SUL&SEG (Nota de Cobrança), **Fatura de Locação Genérica** (qualquer locadora não catalogada) e **ARMAC** (escaneada, tabela multi-item).
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

# Conversão em lote (diretório)
python app.py --batch path/to/pdfs --output path/to/output_dir

# Conversão de contrato de locação (JSON)
python app.py --contrato path/to/contrato.json --output path/to/output_dir
```

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

*Documentação atualizada em 2026‑07‑24 (34 layouts suportados).*
