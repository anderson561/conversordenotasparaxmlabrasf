# Conversor de Notas Abrasf

## Visão Geral

Este projeto fornece um conversor de PDFs de Notas Fiscais de Serviço (NFS‑e) e Contratos de Locação para o padrão **ABRASF 2.01 XML**. Ele inclui:

- **Extratores de PDF** capazes de lidar com layouts variados de múltiplos municípios (Cuiabá/MT, Barreiras/BA, Camaçari/BA, Salvador/BA, Feira de Santana/BA, Rio de Janeiro/RJ, São Paulo/SP, Joinville/SC, Fortaleza/CE, **Brasília/DF**, Simões Filho/BA, Ribeirão Pires/SP, ISBET, Fatura Localiza, Nacional e Genérico).
- **Transformadores** que mapeiam os dados extraídos para o XML ABRASF.
- **Interface de linha de comando** (`app.py`) para conversões individuais ou em lote.
- **Interface gráfica** (`gui_app.py`) baseada em *flet* para usuários não‑técnicos.
- **Gerador de contratos de locação** a partir de JSON, produzindo XML pronto para importação.

## Principais Funcionalidades

- Suporte a múltiplos layouts de NFS‑e.
- Processamento de PDFs com múltiplas páginas e múltiplas notas por página.
- Geração de lote XML (`ListaNfse`).
- Conversão de contratos de locação (dados preenchidos via GUI ou JSON).
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
│  ├─ extractors/           # Extratores de PDF
│  ├─ transformers/         # Transformadores para XML
│  ├─ models/              # Modelos de dados (NFS‑e, contrato)
│  └─ utils/               # Utilidades auxiliares
├─ tests/                   # Testes unitários
├─ templates/              # Templates de UI (se houver)
├─ gui_app.py               # Aplicação de desktop baseada em flet
├─ app.py                   # CLI de alto nível
└─ README.md                # Documentação principal (este arquivo)
```

## Contribuição

1. Fork o repositório.
2. Crie uma branch para sua feature (`git checkout -b feature/minha-feature`).
3. Submeta seus testes e documentação.
4. Abra um Pull Request.

---

*Documentação gerada automaticamente em 2026‑06‑03.*
