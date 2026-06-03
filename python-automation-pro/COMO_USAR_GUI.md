# Guia de Uso: Interface Gráfica (GUI) - Conversor NFS-e

Este documento explica como utilizar a interface visual do Conversor de Notas Fiscais e Contratos de Locação (padrão ABRASF 2.01).

## 1. Como Iniciar

Existem duas formas de abrir a interface:

### Via Script (Desenvolvimento)

Se você tem o Python instalado, basta dar um duplo clique no arquivo:

- `executar_gui.bat`

### Via Executável (Produção)

Após rodar o script de build, você encontrará o executável em:

- `dist/nfse_converter_gui.exe`

---

## 2. Tipos de Arquivo Suportados

No campo **"Tipo de Arquivo"**, selecione uma das três opções:

| Opção | Descrição |
|---|---|
| **NFS-e (Padrão ABRASF 2.01)** | Converte PDFs de notas fiscais de serviço para XML ABRASF |
| **NF-e (DANFE Estadual - Modelo 55)** | Converte PDFs de notas fiscais eletrônicas estaduais |
| **Contrato de Locação (ABRASF XML)** | Gera XML ABRASF a partir de dados digitados do contrato (sem PDF) |

---

## 3. Conversão de NFS-e / NF-e (via PDF)

Siga estes passos para converter PDFs:

1. **Selecionar Entrada (Pasta ou Arquivos)**:
   - Para processar todos os PDFs de uma pasta, clique no ícone de pasta 📂 ao lado do campo "Pasta de Entrada".
   - Para selecionar arquivos PDF individualmente, clique no ícone de PDF 📄. Você pode selecionar múltiplos arquivos segurando a tecla `Ctrl` ou `Shift`.
   - O campo de texto mostrará o caminho da pasta ou a quantidade de arquivos selecionados.
2. **Selecionar Pasta de Saída**: Clique no ícone ao lado do campo "Pasta de Saída". Selecione onde os XMLs serão salvos.
3. **Iniciar Conversão**: Clique no botão **"Iniciar Conversão"**.

---

## 4. Geração de XML para Contratos de Locação

Quando selecionar **"Contrato de Locação (ABRASF XML)"**, o formulário de dados aparecerá automaticamente:

### Mapeamento de papéis no XML
| Contrato | XML ABRASF |
|---|---|
| **Locador** (quem aluga o bem) | → `<Tomador>` |
| **Locatário** (quem usa o bem) | → `<Prestador>` |

### Campos a preencher

**Locador** (laranja):
- Razão Social / Nome
- CNPJ ou CPF
- Inscrição Municipal (opcional)
- Endereço completo (logradouro, número, bairro, município IBGE, UF, CEP)

**Locatário** (verde):
- Razão Social / Nome
- CNPJ ou CPF
- Inscrição Municipal (opcional)
- Endereço completo

**Dados do Serviço**:
- **Valor Mensal (R$)**: valor do aluguel mensal
- **Alíquota ISS**: ex. `0.03` para 3%
- **Código Serviço LC116**: padrão `0601` (locação de bens móveis)
- **Discriminação**: descrição livre do bem alugado (ex: "Locação de veículo CRUZE LT 2013, placa OLG-4701")

**Data de Emissão**:
- Clique em **"Escolher Data"** para abrir o calendário e selecionar a data.

### Regras automáticas do XML gerado
- `<Numero>` = **ano da data de emissão** (ex: `2026`)
- `<Acumulador>` = **916** (fixo)
- `<CodigoVerificacao>` = `CONTRATO`
- Arquivo salvo como: `CONTRATO_LOCACAO_<ANO>.xml`

---

## 5. Monitoramento e Resultados

- **Barra de Progresso**: Uma barra azul mostrará o avanço do processamento.
- **Log em Tempo Real**: Na parte inferior, você verá cada etapa sendo processada, avisos de erro ou arquivos ignorados.
- **Finalização**: Ao concluir, uma mensagem de sucesso aparecerá no rodapé.

---

## 6. Requisitos do Sistema

- **PDFs**: Certifique-se de que os PDFs são notas fiscais legíveis (não são imagens/fotos sem texto).
- **Pasta de Saída**: O programa criará a pasta caso ela não exista.

---
> [!IMPORTANT]
> **Para Desenvolvedores**: Se você for executar o script `gui_app.py` diretamente via terminal, certifique-se de instalar as dependências completas com:
> `pip install "flet[desktop]"`
>
> O executável na pasta `dist/` já contém todas as dependências necessárias.
