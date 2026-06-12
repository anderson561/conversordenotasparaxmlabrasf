# Conversor NFS-e e Contratos para ABRASF 2.01

Bem-vindo ao repositório do **Conversor de Notas Fiscais e Contratos**. Este projeto é uma solução completa em Python para extrair dados de arquivos PDF (Notas Fiscais de Serviço e Danfes) ou através de input manual (Contratos de Locação) e convertê-los em arquivos XML compatíveis com o formato ABRASF 2.01 (Padrão Nacional da Associação Brasileira das Secretarias de Finanças das Capitais).

## Visão Geral

O conversor foi construído com foco em **escalabilidade, resiliência e facilidade de uso**, combinando parse de texto nativo de PDF (`pdfminer`) e leitura ótica de caracteres (OCR via `pytesseract`) como contingência para imagens, garantindo a extração de dados mesmo nas situações mais adversas (falhas de codificação, rasuras virtuais ou quebra de tabelas).

### Principais Recursos
- **Interface Gráfica (GUI)**: Aplicação amigável em modo Desktop construída em Flet.
- **Linha de Comando (CLI)**: Utilitário para automação e execução em lote.
- **Motor de OCR Automático**: PDFs escaneados ou imagens convertidas em texto sem intervenção do usuário.
- **Inteligência Multi-Página**: Fatiamento de notas compostas por dezenas de páginas em arquivos XML distintos ou agrupamento de discriminações gigantes.
- **Escalabilidade Extrema de Layouts**: Facilidade em acrescentar prefeituras e formatos sem mexer no núcleo (veja mais na [Documentação de Conversão](DOCUMENTACAO_CONVERSAO.md)).

## Como Executar

### Pré-requisitos
- Python 3.10 ou superior instalado.
- Tesseract OCR (para leitura de PDFs escaneados).
  - *No Windows*: baixe e instale em `C:\Program Files\Tesseract-OCR`.
- Poppler (opcional, recomendado pelo pdf2image).

### Instalação (Desenvolvedores)
1. Clone o repositório.
2. Crie um ambiente virtual (`python -m venv .venv`).
3. Ative o ambiente (`.venv\Scripts\activate` no Windows).
4. Instale as dependências: `pip install -r requirements.txt`.

### Abrindo o Conversor
Você pode executar diretamente via script ou através dos executáveis pré-compilados na pasta `dist/`.
- **Interface Gráfica**: Dê um duplo clique em `executar_gui.bat` ou rode `python gui_app.py`.
- **Linha de Comando**: Dê um duplo clique em `executar.bat` ou rode `python app.py`.

## Manuais e Documentações Secundárias
- 📖 [Documentação Técnica de Conversão e Layouts Suportados](DOCUMENTACAO_CONVERSAO.md)
- 🖱️ [Guia Rápido de Uso da Interface (GUI)](COMO_USAR_GUI.md)

---
*Desenvolvido para automatizar as rotinas fiscais e quebrar as barreiras de integração de dados.*
