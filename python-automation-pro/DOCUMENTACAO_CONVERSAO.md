# Documentação de Conversão — Conversor NFS-e / Contratos ABRASF 2.01

Este documento detalha os layouts e formatos suportados pelo conversor.

---

## Layouts Suportados (PDF → XML)

O extrator PDF (`SPPdfExtractor`) conta com um motor de heurística profunda, capaz de ler as disposições textuais do PDF e classificar dinamicamente qual regra de negócio aplicar (`_detect_layout` / `_detect_layout_page`). São **37 layouts** ao todo (36 específicos + o genérico de fallback), agrupados abaixo por tipo. Obs.: o São Paulo (nº 7) tem **duas variantes dedicadas** (digital e escaneada) e o Camaçari (nº 3) tem **três** (digital, escaneada e Nota Avulsa da Prefeitura — nº 16d); Mata de São João (nº 16b), Rosário da Limeira (nº 16c) e F&F Comércio (nº 26b) foram adicionados fora da sequência — por isso a numeração das entradas não bate 1-para-1 com as 36 constantes de layout. PDFs escaneados/imagem (sem texto extraível) passam automaticamente por **OCR** (Tesseract via `pytesseract` + PyMuPDF, `lang='por'`) antes da extração.

> **Nota sobre OCR:** o texto pós-OCR (e às vezes até o de PDF com texto embutido) diverge do que parece "óbvio" na imagem — troca de caracteres, glifos ilegíveis, colunas intercaladas. As regras por layout são propositalmente tolerantes a esses ruídos.

### Prefeituras / NFS-e municipal

### 1. Cuiabá/MT — `cuiaba_issnet`
- **Cabeçalho**: "Prefeitura Municipal de Cuiabá / Nota Fiscal de Serviço Eletrônica - NFS-e"
- **Número da Nota**: Canto superior direito
- **Cód. de Autenticidade**: Abaixo da data de competência (Ex: `E6679FDB0`)
- **Data de Competência**: Rótulo `Data de Competência`
- **Entidades**: Blocos "Dados do Prestador de Serviço" e "Dados do Tomador de Serviços"
- **Cidade/UF**: Rótulo `Cidade/UF` (Ex: `Lauro de Freitas/ BA`)
- **⚠️ Dois formatos de OCR (rótulo limpo vs grade escaneada)**: notas de boa qualidade têm rótulos limpos (`Número da Nota Fiscal: 205`, `Vl. Total dos Serviços: R$ ...`) e caem nos extratores genéricos. Já em **scans degradados** (ex.: consolidado "NFS PRESTADORES MTI", nota nº 134) o cabeçalho e a grade de valores saem garbleados, exigindo ramos dedicados:
  - **Número**: a caixa do número sai ilegível; o número vem **imediatamente antes de "Dados do Prestador de Serviço"** (confirmável pelo rodapé "substitui a nota nº N-1"). Sem isto o genérico pescava o `Número: 554` do **endereço do tomador** ("Avenida Praia de Pajussara Número: 554").
  - **Município do prestador**: extraído de `- Cuiabá! MT` (ou `Cidade/UF`); sem isto o resolver escolhia um IBGE errado (pegava os dígitos da Inscrição Municipal, ex.: `295033` → `2950330`, em vez de **Cuiabá 5103403**).
  - **Código de serviço**: item da LC116 na grade de atividade (`... Serviços de engenharia - 5,00 | 701 <NBS 9díg>`) → `0701`.
  - **Valores (grade)**: linha de valores lida por **posição** (`[0]`=serviços, `[3]`=base, `[4]`=Total do ISSQN); alíquota da coluna de atividade; ISS confere com base×alíquota (560×5% = 28,00); "Não/Sim" na linha define ISSQN retido. O OCR troca "Vl."→"Vi.".
  - **Cód. autenticidade**: primeiro token alfanumérico **misto** de 7-10 caracteres (ex.: `3B3DC3576`) — CNPJ/CEP/telefone são só dígitos e não casam.
- **⚠️ Vazamento do TOMADOR para o bloco do PRESTADOR (cabeçalho "Dados do Tomador" ausente)**: em scans mais degradados (ex.: página 14 do mesmo consolidado MTI, nota ANDERSON FAUSTINO/FA TELAS → São Pedro) o cabeçalho "Dados do Tomador de Serviços" some por completo do OCR. Sem ele, o bloco do PRESTADOR (delimitado genericamente até o próximo rótulo reconhecido) engole também o CNPJ/Razão/Endereço do TOMADOR até "Dados do Intermediário" — o CNPJ ainda sai certo (1º a validar), mas razão social e município saem do TOMADOR. Correção: usar a **inversão de ordem CNPJ/CPF** como âncora do início do bloco do tomador — o prestador sempre usa `CPF/CNPJ` (CPF antes), o tomador usa `CNPJ/CPF` ou `CNPJICPF` (CNPJ antes, a barra vira "I" no OCR) — independente do rótulo de cabeçalho estar legível. Quando nem essa âncora sobrevive, um fallback secundário usa o **CNPJ nu seguido de "Razão Social:"** na linha seguinte (validado: essa combinação só ocorre no bloco do tomador). **Número honesto**: quando nenhuma âncora confiável de número existe neste scan, não cai no padrão genérico `Número[:\s]+(\d+)` (que pescaria o "Número: 554" do endereço do tomador) — vai direto ao fallback de nome de arquivo/placeholder + aviso, em vez de fabricar um número plausível-porém-errado.
- **⚠️ Grade de valores truncada no zoom 3 padrão + intermediário fantasma (mesma página 14)**: além do vazamento acima, essa nota expôs mais dois problemas:
  1. A grade "Detalhamento dos Tributos" quebrava a linha de valores no meio (`R$443,80 | R$000` numa linha, `R$ 0,00` isolado bem abaixo), perdendo o Total do ISSQN e parte da Base de Cálculo — saía serviços 443,80/alíquota 0/ISS 0 quando o real (confirmado por recorte em zoom alto) era 4.113,50/2%/R$ 82,27. `_ocr_page` agora detecta a grade truncada (menos de 4 tokens `R$` na linha logo após "Vl. Total dos Serviços") e reprocessa a página inteira em **zoom 5 + PSM 6** (`_ocr_valores_cuiaba`), prependando o texto limpo — mesma técnica das demais notas degradadas; zoom 6 também recompõe a grade, mas nesse zoom específico a alíquota "2,00" cai do texto, por isso zoom 5.
  2. A tabela "Dados do Intermediário de Serviços" desta nota está **vazia** (só o cabeçalho da grade), mas faltava o delimitador para a variante **plural** "Descrição **dos Serviços**" (só havia o singular "Descrição do Serviço"); o bloco genérico vazava para o texto de descrição do serviço seguinte e pescava o **CNPJ do próprio PRESTADOR** (linha "pix para pagamento cnpj ...") como se fosse do intermediário. Corrigido o delimitador e adicionado um rótulo completo (`Dados do Intermediário de Serviços`) para consumir a frase toda. Como o intermediário é uma entidade **opcional** (ao contrário de prestador/tomador, que sempre aparecem), quando nada de fato é identificado (CNPJ cai no sentinela **e** razão fica no default genérico) o extrator agora devolve `None` em vez de fabricar um intermediário fantasma — o `<Intermediario>` some do XML.
  3. **Número**: nenhuma das duas âncoras de número sobrevivia neste scan (usuário confirmou contra o documento real que o número é **16**). Um recorte dedicado da caixa "Número da Nota Fiscal" (canto superior direito, excluindo o logo/QR "NOTA CUIABANA" ao lado — que confunde o OCR e faz o dígito variar entre zooms, ex.: "16"→"18") em **zoom 6/8/10 + PSM 7** (linha única) + whitelist de dígitos recupera o valor de forma estável; só é aceito quando **pelo menos 2 dos 3 zooms concordam** — sem consenso, segue para o fallback honesto de sempre em vez de arriscar um dígito errado. Só dispara quando as duas âncoras normais já falharam (não roda para notas já resolvidas, ex.: nº 134).
- **⚠️ Nota inteira sumindo do resultado (heurística de "nova nota" COMPARTILHADA por todos os layouts, achado no PDF "NFS PRESTADORES ANALISE DE NFS-iss e inss retido", pág. 3, nota nº 10)**: `parse_multiple`/`is_new_invoice` decide se um bloco de texto é nota nova ou continuação da anterior comparando "números" extraídos com a regex genérica `(?:Número|Nº).*?(\d+)`. Quando a caixa real "Número da Nota Fiscal" sai ilegível no OCR, essa regex cai no PRÓXIMO "Número" do texto — o do **endereço do tomador** ("Avenida Praia de Pajussara Número: 554"), igual em toda nota do mesmo tomador. Páginas de notas DIFERENTES batendo no mesmo "554" eram tratadas como continuação uma da outra — a nota seguinte nunca virava um XML próprio, ficava silenciosamente engolida (achado nas duas PDFs consolidados de Cuiabá desta sessão: recuperou 2 notas na "ANALISE" e 3 na "MTI"). Corrigido com `_numero_heuristico_bloco`: tenta primeiro rótulos específicos de "número da nota"; no fallback genérico, pula ocorrências cuja linha contém "Endereço".
- **⚠️ Prestador REAL deslocado para depois de "Dados do Intermediário de Serviços" (mesmo PDF "ANALISE", pág. 3, nota nº 10, DR3 TERCEIRIZAÇÃO → SÃO PEDRO CONSTRUTORA)**: variante ainda mais embaralhada do vazamento acima — depois de "Dados do Prestador de Serviço" vem, sem rótulo próprio, o CNPJ do TOMADOR; só depois de "Dados do Intermediário de Serviços" aparecem os dados REAIS do prestador (nome, endereço, CNPJ). Sem tratamento, prestador saía com o CNPJ do tomador e razão social quebrada, e o "intermediário" (tabela vazia) roubava os dados reais do prestador. Corrigido: quando o bloco "normal" do prestador não tem a assinatura `CPF/CNPJ` (CPF antes), procura essa assinatura no trecho entre "Dados do Intermediário de Serviços" e "Descrição dos Serviços" — só assume o deslocamento quando o trecho REALMENTE a tiver (não regride notas sem esse problema). Guard simétrico do lado do intermediário: se o bloco carrega a assinatura do PRESTADOR, devolve `None` em vez de um intermediário fantasma. Também ajustada a grade de valores: uma linha **completa** desta grade sempre tem **6 tokens `R$`** (serviços, desc. incond., deduções, base, ISS, desc. cond.) — o limiar do recut de valores (`_ocr_valores_cuiaba`) subiu de "< 4" para "< 6" tokens, pois esta nota tinha só 5 (faltava a Base de Cálculo, sem quebra de linha) e não disparava o recut antes.
- **⚠️ Extração do número da nota — endurecimento geral (achado ao consertar a nota nº 10, pág.3 do PDF "ANALISE": mesmo com os fixes anteriores, o número ainda saía `00000000`)**: três problemas distintos, todos no mecanismo de número:
  1. **Dígito espúrio isolado entre o rótulo e o valor** (nota real pág.10 do MTI, RC CONSTRUÇÕES ELÉTRICAS, número real **205**): o OCR intercala um dígito isolado numa linha própria — `"Número da Nota Fiscal\n5\n205\n"` — o "5" é ruído, "205" é o número de verdade; o padrão antigo pegava o PRIMEIRO grupo de dígitos (o "5" errado) sem nenhum aviso. Corrigido: captura até 3 grupos de dígitos após o rótulo e fica com o **mais longo** — um ruído de 1 dígito nunca vence o número real ao lado.
  2. **PSM errado no recorte dedicado do número** (`_ocr_numero_box_cuiaba`): nem PSM 6 (bloco) nem PSM 7 (linha única) é confiável sozinho — o recorte tem duas linhas (rótulo + número) e qual PSM lê melhor varia por nota (pág.14 do MTI só lê com PSM 7; nota nº 10 do "ANALISE" só lê de forma estável com PSM 6). Corrigido: vota com AMBOS os PSM em 3 zooms (6/8/10 — 6 tentativas), aceita com ≥2 votos concordando. Faixa vertical do recorte também alargada (0.065-0.098 da altura da página) — a faixa antiga (mais estreita) cortava ao meio números de 3 dígitos como "205".
  3. **Recorte dedicado agora roda SEMPRE** (não só quando as âncoras normais falham) e tem prioridade sobre a leitura de página inteira — porque a leitura de página inteira pode ler um dígito ERRADO com confiança total, sem nenhum sinal de ambiguidade. O recut de valores (`_ocr_valores_cuiaba`) também teve sua própria leitura incidental de "Número da Nota Fiscal" removida antes de ser prependado, para não competir com o recorte dedicado do número.
  - **Limite conhecido, não resolvido:** na nota GMS FLATS (pág.17), o recorte dedicado do número agora lê `9699` com consenso TOTAL (6/6 votos, todos os zooms e PSMs) — mas o número real, confirmado pela imagem, é `5639`. Mesmo um recorte cross-validado não detecta quando o Tesseract erra de forma unânime nessa nota especificamente (já sabidamente degradada — CNPJ do prestador com vírgula, intermediário residual, alíquota sem vírgula). Sem uma técnica de reconhecimento de dígito mais sofisticada (ex.: modelo dedicado), não há como distinguir algoritmicamente esse caso de um acerto real — registrado como limitação conhecida, não fabricado silenciosamente sem aviso ao usuário.

### 2. Barreiras/BA — `barreiras`
- **Cabeçalho**: "MUNICIPIO DE BARREIRAS"
- **Data de Competência**: Baseia-se no rótulo `Data Fato Gerador` ou através do recorte do Mês/Ano diretamente na **Chave de Acesso Nacional** (quando há falha estrutural de OCR nas datas).
- **⚠️ Locação de bens móveis não sujeita a ISS, emitida pelo MESMO portal (achado real 2026-07-31, nota nº 1162, OLIVEIRA & CHAVES → SÃO PEDRO CONSTRUTORA):** o portal municipal de Barreiras também emite fatura de locação (não só NFS-e tributada), com o item "00.00 - LOCAÇÃO DE BENS MÓVEIS" (código próprio do portal, não é item real da LC116) → mapeado para `0000`. **Valores em grade de 3 colunas**: "VALOR SERVIÇO (R$) DEDUÇÕES (R$) DESCONTO INCONDICIONAL" traz os 3 rótulos primeiro, só depois os valores ("4.755,00 0,00") — diferente da variante já suportada onde o valor vem colado ao próprio rótulo ("VALOR SERVIÇO (R$)\n16.473,00"). O genérico caía no fallback **zero** nessa estrutura (ERP contábil rejeitava a importação: "Valor contábil zerado para nota com situação diferente de cancelada"). Fix gateado por ausência de dígito logo após o rótulo "VALOR SERVIÇO" (a variante já funcional não é afetada); Base de Cálculo/Alíquota/ISS pela mesma técnica de grupo "rótulos-depois-valores"; Valor Líquido pelo ÚLTIMO número antes de "Chave de acesso" (fica separado do próprio rótulo por uma sequência de campos de retenção federal zerados).

### 3. Camaçari/BA — `camacari` (digital + escaneado) / `camacari_ba_scan` ⚠️ **DOIS LAYOUTS**
- **Sistema / Cabeçalho** (ambos): CPqD - Gestão Pública / "PREFEITURA MUNICIPAL DE CAMAÇARI".
- **Data de Competência**: Rótulo `Data da prestação do serviço`.
- **Discriminador**: a **origem do texto** decide o layout via `self.from_ocr`. PDF com texto embutido (pdfminer) → `camacari`. PDF **escaneado** (foto/JPG → OCR) → `camacari_ba_scan` (`LAYOUT_CAMACARI_2`).
- **Diferença em relação ao SP**: o `camacari` original **já tratava notas escaneadas** (grade OCR "Retenções × Totais", valores sem pontuação, CETREL). Por isso o `camacari_ba_scan` é um **SUPERSET**: herda todos os branches do `camacari` como fallback e só sobrepõe o tratamento próprio quando dá match. Assim as notas escaneadas que já funcionavam não regridem, e a nova família de fotos de baixa qualidade é atendida.
- **`camacari_ba_scan` (escaneado)**: para fotos de baixa qualidade em que a leitura padrão (zoom 3) **descarta a metade inferior inteira** da nota (grade de totais) e a caixa de cabeçalho:
  - **Re-OCR de página inteira** em zoom 4 + PSM 6 (`_ocr_camacari_scan`) recupera o corpo (grade, `Serviço: 000713`, entidades), na orientação já corrigida.
  - **Recorte dedicado do cabeçalho** (`_ocr_header_box_camacari`, zoom 6) recupera o número (ex.: `1050`, `4494`) e a data/hora de emissão — a caixa some no zoom 3.
  - **⚠️ Achado real 2026-07-31 (nota nº 4494, LAVANDERIA ÁGUA DE CHEIRO): número desaparecendo por completo, sem gerar aviso plausível de causa.** O limite superior do recorte do cabeçalho (`h * 0.045`) começava exatamente no início da linha "Data de Emissão", cortando fora a linha "Número da Nota" (rótulo + valor) inteira — o número não saía nem garbled, simplesmente não existia em lugar nenhum do texto (nem no recorte, nem na leitura de página inteira, que também perde essa caixa). Corrigido subindo o limite para `h * 0.01` (testado de 0.005 a 0.025 sem diferença no resultado — margem generosa, sem risco de também cortar as 2 linhas de baixo).
  - **Alíquota × ISS trocados**: a grade lê "Aliquota (%) 35,75" e "ISS 6,5%", mas o real é alíquota **6,5%** e ISS **35,75**. Regra imune à troca: a alíquota é o único token seguido de `%`; o ISS é **derivado de base × alíquota**.
  - **CNPJ do tomador com 1º dígito trocado** (OCR `49...` → real `19...`): corrigido por validação do dígito verificador (`_corrige_cnpj_primeiro_digito`), testando só as 10 variações do 1º dígito e aceitando apenas quando **exatamente uma** valida.
  - **Município do prestador some** no OCR → default Camaçari (toda NFS-e municipal de Camaçari é emitida por prestador local).
  - **Código de autenticidade** impresso em fonte fraca → ilegível mesmo com recorte; fica sinalizado em `avisos` **quando cai no placeholder `XXXX-XXXX`**. Limitação conhecida (não corrigida, registrada mas não escondida): em algumas notas (ex.: nº 4494) o OCR produz um valor **plausível-porém-errado** em vez do placeholder (`TOTAM7HFA` em vez do real `70T4M7HFA` — "7"/"0" e "T"/"O" são visualmente ambíguos nessa fonte fraca), e nesse caso **nenhum aviso é gerado** para o campo.

### 4. Salvador/BA — `salvador_ba` (Nota Salvador)
- **Cabeçalho**: "PREFEITURA MUNICIPAL DO SALVADOR" ou "NOTA SALVADOR" ou "Xique-Xique"
- **Código de Verificação**: Extração de código de autenticidade/verificação.
- **Número da Nota**: Extração nativa com fallback defensivo para o Nome do Arquivo caso o layout sofra extrema degradação.
- **Extração de Município/UF**: Tratamento robusto para remover sufixos de UF como `UF: BA` do nome do município e atualizar o endereço corretamente.
- **⚠️ Duas sub-estruturas de entidade (digital rotulada vs escaneada sem rótulo de tomador)**: na variante **digital** o tomador vem sob "TOMADOR DE SERVIÇOS" com campos "Município:/UF:" (caminho genérico). Já na variante **escaneada/OCR** (ex.: nota Cajado → São Pedro) **não há cabeçalho "TOMADOR"**: prestador e tomador são dois blocos consecutivos separados apenas pelos rótulos "Nome/Razão Social", com **ordem de campos invertida** (prestador `CPF/CNPJ → Nome → Endereço`; tomador `Nome → CPF/CNPJ → Endereço`). Sem recorte dedicado, a busca genérica pelo rótulo "TOMADOR" falhava, o bloco virava o texto inteiro e o **tomador copiava o CNPJ/nome/endereço do prestador**. Correção: quando não há rótulo de tomador, fatiamos prestador (de "PRESTADOR DE SERVIÇOS" até o 2º "Nome/Razão Social") e tomador (do 2º "Nome/Razão Social" até "DISCRIMINAÇÃO"). Endereço em texto livre `logradouro - [bairro -] município - CEP:` (município no penúltimo/último segmento; ex.: tomador em **Lauro de Freitas** IBGE 2919207). Gate por ausência do rótulo → a variante digital rotulada segue intocada.
- **⚠️ Tomador corrompido no zoom 3 → recut em zoom alto (`_ocr_tomador_salvador`)**: em scans de baixa qualidade **com** cabeçalho "TOMADOR DE SERVIÇOS" (ex.: nota nº 46, BALUARTE → SÃO PEDRO), o zoom 3 padrão corrompe o CNPJ e a razão do tomador (`03.051.741/0001-90` → `05051.74110001.00`; `SÃO PEDRO` → `es EO`), fazendo o CNPJ cair no sentinela `00000000000100`. O bloco é localizado corretamente (município/CEP certos), mas o CNPJ/razão dentro dele saem ilegíveis. Correção: um re-OCR da página em **zoom 5** (`_ocr_tomador_salvador`) recupera ambos limpos; devolve só o recorte "TOMADOR … DISCRIMINAÇÃO", que é **prependado** ao texto base para a extração genérica achar o CNPJ/razão corretos primeiro. **Gate:** só dispara quando o bloco do tomador no zoom 3 **não** tem um CNPJ bem-formado (`\d{2}.\d{3}.\d{3}/\d{4}-\d{2}`) — notas que já saem limpas pulam o custo extra. Não troca o texto inteiro (zoom 5 fragmenta a discriminação — por isso o zoom global segue 3x).
- **⚠️ Espaço espúrio antes do dígito verificador do CNPJ do PRESTADOR → 3 campos contaminados de uma vez** (ex.: nota nº 00000072, ORGEN ENGENHARIA → SÃO PEDRO): o OCR gera `48.310.477/0001 -08` (espaço antes do `-08`) e lê o `:` do rótulo `Nome/Razão Social:` como a letra `e`. Uma única degradação produzia três erros simultâneos: (1) **CNPJ do prestador saía igual ao do tomador** — o regex de CNPJ exigia `-` colado, não casava, e o fallback "primeiro CNPJ válido da página inteira" (`is_prestador → all_cnpjs[0]`) roubava o do tomador; (2) **Inscrição Municipal saía `483104770001`**, um pedaço do próprio CNPJ — ao remover a pontuação, `48.310.477/0001` vira um blob de 12 dígitos que passa pelo filtro de IM; (3) **Razão Social saía `e ORGEN ENGENHARIA…`**, com o glifo do rótulo colado. Correções: separadores do regex de CNPJ aceitam `[ \t]*` em volta de `/` e `-`; o candidato a IM é descartado quando é substring do CNPJ já identificado (`d not in cnpj`); e um caractere **minúsculo** solto seguido de maiúscula é removido do início da razão (só minúsculo, para não comer um `E`/`A` legítimo em caixa alta). Distinto dos dois casos acima: aqui é o **prestador** que corrompe, e o rótulo "TOMADOR DE SERVIÇOS" está legível (não passa pelo recorte sem rótulo nem pelo recut de zoom alto). Coberto por `tests/test_salvador_prestador_cnpj_ruido.py`.

### 5. Feira de Santana/BA — `feira_de_santana`
- **Cabeçalho**: "FEIRA DE SANTANA"
- **Data de Competência**: Busca do campo `Fato Gerador`.

### 6. Rio de Janeiro/RJ — `rio_de_janeiro` (Nota Carioca)
- **Cabeçalho**: "RIO DE JANEIRO" ou "NOTA CARIOCA"
- **Data de Competência**: Busca do campo `Mês de Competência`.

### 7. São Paulo/SP — `sao_paulo_sp` (digital) / `sao_paulo_sp_scan` (escaneado) ⚠️ **DOIS LAYOUTS**
- **Cabeçalho** (ambos): "PREFEITURA DO MUNICÍPIO DE SÃO PAULO".
- **Discriminador**: a **origem do texto** decide o layout, sem ambiguidade. PDF **digital** (texto embutido, pdfminer) → `sao_paulo_sp`; PDF **escaneado** (JPG/foto → OCR) → `sao_paulo_sp_scan` (`LAYOUT_SAO_PAULO_2`). Só o escaneado passa por OCR, então a flag `self.from_ocr` roteia entre os dois. **Os dois são layouts/constantes separados** — o digital fica 100% isolado das regras do escaneado.
- **`sao_paulo_sp` (digital)**: competência via rótulo `Compe:` (mês/ano, ex.: `Jan/2026`); demais campos via regras genéricas (texto limpo).
  - **Achado 2026-07-31 (nota AMIL/TEMIS):** em algumas notas reais o pdfminer extrai o texto numa ordem física **diferente da visual** — os cabeçalhos "PRESTADOR DE SERVIÇOS"/"TOMADOR DE SERVIÇOS" ficam **deslocados no meio dos próprios dados** da entidade (o CNPJ do prestador chega a vazar sozinho, antes de qualquer cabeçalho; "TOMADOR DE SERVIÇOS" só aparece depois de Nome/Razão + CPF/CNPJ + Endereço do tomador já terem passado). O extrator genérico (que delimita bloco por cabeçalho de seção) erra o alvo: CNPJ do prestador saía = CNPJ do tomador; razão social do tomador saía = bairro dele; logradouro vazio nas duas entidades; alíquota/ISS zerados (grade "rótulos em bloco, depois valores em bloco", mesmo efeito do `LAYOUT_CAMACARI_2`). Corrigido com um ramo dedicado (`_extrair_entidade_sao_paulo`), gateado pela presença do rótulo "Bairro:" (marca específica deste template, ausente do mock sintético mais simples que já cobria o caminho genérico) — usa CNPJ por ordem de aparição no documento (1º=prestador, 2º=tomador) em vez de bloco por cabeçalho, e ancora razão/endereço pelo próprio rótulo mais próximo, pulando rótulos decorativos sem valor colado.
- **`sao_paulo_sp_scan` (escaneado)**: OCR ruidoso de 2 colunas, frequentemente **rotacionado** (foto). A caixa "Número da Nota" do canto superior direito sai ilegível na página inteira (o número vira "5") → **recorte dedicado** (`_ocr_header_box_sao_paulo`, zoom 6 + PSM 6 + whitelist de dígitos, reaproveitando o ângulo de rotação já corrigido) recupera o número (ex.: `00331020`). Branches próprias: código de verificação `XXXX-XXXX` no fim da linha do RPS (evita casar "RPS Nº"→"RPSN"); item de serviço do cadastro paulistano (`02498`); valores pela grade oficial "Base de Cálculo / Alíquota (%) / Valor do ISS", ignorando os **valores-isca** do corpo (ex.: "Valor ISS: 137,06" que é o COFINS de 7,60%); discriminação limpando rótulos/Lei 12.741 vazados.

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
- **Cabeçalho**: "DANFSe v1.0", "Documento Auxiliar da NFS-e" (a detecção também casa pela âncora "Chave de Acesso", pois em DANFSe **escaneada** o OCR corrompe o cabeçalho — ex.: "DANFSo vi", "NFS-g").
- **Competência**: Rótulos `Competência da NFS-e` (aceita `MM/YYYY` e `DD/MM/YYYY`) com regra de prioridade sobre a *Data/Hora da Emissão* em caso de conflitos.
- **Entidades**: Suporte avançado a extração segmentada para **Prestador**, **Tomador** e **Intermediário do Serviço**, isolando perfeitamente seus respectivos CNPJs e controlando contaminações cruzadas quando campos vêm indicados como "NÃO IDENTIFICADO".
- **⚠️ Chave de Acesso como fonte de verdade (DANFSe escaneada)**: a Chave de Acesso de **50 dígitos** codifica IBGE do município + CNPJ do emitente + **número da NFS-e** (posições 24-36, zero-preenchidas). Em notas escaneadas o OCR come dígitos do número impresso ao lado do rótulo (ex.: `21` vira `2`), então o **número é decodificado da chave** (`chave[23:36].lstrip('0')`), não do rótulo. A própria chave (50 díg.) preenche o `<CodigoVerificacao>` do XML — o DANFSe **não tem** um "Código de Verificação" separado.
- **Item de serviço**: "Código de Tributação Nacional 16.02.01" → 2 primeiros pares (`1602`); o 3º par é o desdobro municipal. Sem este ramo, caía no default genérico `03115`.
- **Valores (grade "rótulo em cima / valor embaixo")**: campos vazios marcados por `-`; o `R$ n,nn` é capturado por **proximidade de cada rótulo próprio** ("Valor do Serviço", "Valor Líquido da NFS-e"). Os padrões genéricos falhavam nessa estrutura (pescavam o número da nota como ISS e deixavam o valor zerado). **MEI** ("Optante - Microempreendedor Individual"): BC/alíquota/ISS em branco → tributação zero, não retido.

### 15. Lauro de Freitas/BA — `lauro_de_freitas_ba`
- **Detecção**: "MUNICÍPIO DE LAURO DE FREITAS" ou domínio `laurodefreitas.ba.gov.br`.
- **Item de serviço**: código municipal de 6 dígitos (item.subitem LC116 + subitem municipal, ex.: `110201`) → usamos os 4 primeiros (`1102`).
- **⚠️ Campos deslocados pelo pdfminer**: Município/UF/E-mail do **prestador** saem *depois* do cabeçalho "TOMADOR DE SERVIÇOS" (mas antes do nome do tomador). Extração dedicada particiona o texto em 3 blocos pelos cabeçalhos de seção para o tomador não herdar o município/e-mail do prestador.
- **⚠️ Variante NFTS (Nota Fiscal Eletrônica do TOMADOR de Serviços)**: neste tipo de documento (ex.: nota 2026302, BDP LOGISTICA → BONI TRANSPORTES) o cabeçalho "TOMADOR DE SERVIÇOS" vem **antes** de "PRESTADOR DE SERVIÇOS" (ordem invertida frente à NFS-e regular), e cada bloco sai completo/autocontido, sem vazamento. Assumir a ordem fixa da NFS-e regular fazia o bloco do prestador virar vazio (slice com início depois do fim) — o prestador saía inteiro como "Não Identificado". Corrigido detectando qual cabeçalho aparece fisicamente primeiro. Também nesta variante, a grade de valores (Deduções/Base/Alíquota/ISS/ISSQN Retido) pode vir **sem o prefixo "R$"** antes dos 2 primeiros números — tolerado como opcional no regex.

### 16. Iaçu/BA — `iacu_nfse`
- **Sistema**: Prefeitura Municipal de Iaçu/BA via plataforma **nfservico.com.br** (NFS-e tributada, escaneada → OCR).
- **Detecção**: "PREFEITURA MUNICIPAL DE IAÇU" (tolerante ao "ç" corrompido no OCR) ou `nfservico.com.br/iacu`. Específico do município — **não** casa pela marca genérica da plataforma, para não colidir com outros municípios do mesmo SaaS.
- **⚠️ Caixa de cabeçalho + QR**: Número da nota / Data e hora / Código de Verificação ficam ilegíveis na leitura de página inteira (caixa pequena ao lado de um QR Code). Recorte dedicado do canto superior direito em zoom alto + PSM 6 (`_ocr_header_box_iacu`) recupera os três campos, prependido ao texto principal (mesmo padrão do Salvador).
- **Item de serviço**: item LC116 no formato `7.02` → `0702`.
- **Valores**: NFS-e **tributada** (ISS real, ex.: 3% sobre a base) — grade "Valor total das deduções / Base de cálculo / Alíquota / Valor do ISS / Crédito"; base/alíquota/ISS espelhados da face (diferente da família de locação).
- **Entidades**: endereço em linha única (`RUA X N, - BAIRRO - CEP: NNNNNNNN - CIDADE - UF`); parser ignora o ruído do carimbo de recebimento intercalado no bloco do tomador (o CNPJ correto é o primeiro de 14 dígitos).

### 16b. Mata de São João/BA — `mata_sao_joao_ba`
- **Sistema**: Prefeitura Municipal de Mata de São João/BA via plataforma **SAATRI** (`matadesaojoao.saatri.com.br`) — NFS-e tributada, escaneada → OCR, mas **scan de boa qualidade** (OCR limpo em zoom 3, sem rotação — bem mais simples que Camaçari/SP2).
- **Detecção**: "Mata de São João" (tolerante ao "ã" corrompido) ou `matadesaojoao.saatri`. Específico do município — **não** casa só por `saatri.com.br`, para não rotear outras prefeituras SAATRI ainda não testadas (decidido com o usuário). **Não** é gated por `from_ocr`: não há layout digital concorrente a proteger.
- **Número**: "Número da Nota ... 00000018" — zero-preenchido; removemos os zeros à esquerda (`00000018` → `18`).
- **Item de serviço**: "Classificação do Serviço (LEI 116/2003) + Desdobro: 01.01.01" — o 3º par é o desdobro municipal; usamos os 2 primeiros (`01.01` → `0101`). Ancorado no rótulo próprio para não casar com o NBS (`115021000`) logo abaixo.
- **Valores**: duas grades "rótulo-em-cima / valores-embaixo" (Serviços/Dedução/Desc.Incond./Base de Cálculo e Alíquota/ISS/ISS Retido/Desc.Cond.) + total em "Total do(s) Serviço(s) / Total Líquido". Já traz colunas de **IBS/CBS** (reforma tributária) — presentes mas zeradas; **não mapeadas** por ora.
- **Entidades**: blocos "Prestador/Tomador do(s) Serviço(s)" com linhas contíguas (razão / [fantasia] / logradouro / `Bairro - MUNICÍPIO/UF CEP` / `CNPJ Insc. Municipal`). A coluna de rótulos (`Nome/Razão Social:`, `CPF/CNPJ:`...) é dumpada em bloco separado no fim e ignorada.
- **⚠️ IBGE**: Mata de São João → **2921005**. Foi preciso registrá-lo em `IBGEResolver.KNOWN_CITIES` — sem isso o resolver caía no default **Salvador (2927408)**.
- **Simples**: a nota diz "optante **do** simples nacional" (não "pelo"); a regex genérica foi ampliada para `(?:PELO|DO)`.

### 16c. Rosário da Limeira/MG — `rosario_da_limeira_mg`
- **Sistema**: Prefeitura Municipal de Rosário da Limeira/MG via plataforma **FUTURIZE** — NFS-e tributada, **PDF digital** (pdfminer limpo, **sem OCR**).
- **Detecção**: "ROSÁRIO DA LIMEIRA" (específico do município). **Não** casa por "FUTURIZE" — plataforma usada por vários municípios; evita rotear prefeituras ainda não testadas (mesmo padrão de Iaçu/Mata, decidido com o usuário).
- **Número**: "Nº da Nota\n72/2026" → a parte antes da "/" (`72`); o resto é o ano. Ancorado no rótulo para não pegar o "Nº Integral" (`202600000000072`).
- **Item de serviço**: "Código de Trib. Nacional: 09.01.04" → 2 primeiros pares (`0901`); o 3º par é o desdobro. Ancorado no rótulo para não casar com o NBS (`1.0303.11.00`).
- **Discriminação**: o texto real ("HOSPEDAGEM") é entregue pelo pdfminer **entre** o rótulo "ART:" e o cabeçalho "DISCRIMINAÇÃO DOS SERVIÇOS" (a grade de valores vem logo após o cabeçalho, sem a descrição).
- **Valores**: grade FUTURIZE rótulo-em-cima/valor-na-linha-de-baixo; total de "VALOR TOTAL DE SERVIÇOS = R$ ..." (na mesma linha). ISS real (ex.: 2% sobre 158,40 = 3,17).
- **Entidades**: rótulos por linha ("Razão Social:" no prestador / **"Nome:"** no tomador — cuidado para não confundir com "Nome Fantasia:"); endereço em **linha única** "logradouro, nº - [extras] - bairro - CEP - MUNICÍPIO - UF", parseado de trás pra frente (UF=último, município=penúltimo, CEP pelo padrão, bairro antes do CEP) — robusto ao nº variável de segmentos (o tomador tem um "SC" extra). Quirk: bairro com **letra-espaçada** ("F R A N C I S C O B E R T O N I", todas em espaço simples) → colapsado sem inventar o espaço de palavra (`FRANCISCOBERTONI`), e só quando o segmento é de caracteres isolados.
- **⚠️ IBGE**: Rosário da Limeira → **3156452**. Registrado em `KNOWN_CITIES` — sem isso o resolver caía no default **MG Belo Horizonte (3106200)**.
- **⚠️ Tributação fora do município**: a nota é "TRIBUTAÇÃO FORA DO MUNICÍPIO" (prestação em Luís Eduardo Magalhães/BA). Por decisão do usuário, a incidência **mantém o município do prestador** (Rosário da Limeira) — igual aos demais layouts, sem alterar o transformer compartilhado.
- **Simples**: campo "Simples Nac/MEI/Outros: Simples Nacional" (não usa "optante") → tratado por regex própria; regime especial fica ausente (o campo "Reg. Especial Tributação:" vem vazio).

### 16d. Camaçari/BA — Nota Avulsa — `camacari_ba_avulsa`
- **Sistema**: **NOTA FISCAL DE PRESTAÇÃO DE SERVIÇOS (AVULSA)** Série "A", emitida diretamente pela **Prefeitura Municipal de Camaçari/BA** (Secretaria da Fazenda) — distinta das notas Camaçari via CPqD (`camacari`/`camacari_ba_scan`). Escaneada → OCR.
- **Detecção**: casa **`AVULSA` + `CAMAÇARI`** e **precede** o bloco Camaçari CPqD. A marca "AVULSA" não aparece nas notas CPqD (digital/escaneada), então não há falso positivo; e o OCR quebra "PREFEITURA MUNICIPAL DE" e "CAMAÇARI" em linhas separadas, por isso **não** se casa a frase inteira. Guarda de regressão no teste: nota CPqD sem "AVULSA" continua indo para `camacari`/`camacari_ba_scan`.
- **Número**: "...DE SERVIÇOS (AVULSA) 00000088462" → zeros à esquerda removidos (`88462`). Ancorado em "AVULSA" para não casar com o "Código Pessoa: 0000630812" do prestador.
- **Data**: "DATA DE PRESTAÇÃO: 12.06.2026" (datas com **ponto**). Não há rótulo de emissão; a competência é o mês da prestação.
- **Item de serviço**: "PE 000709" → item **7.09** da LC 116 (`0709`, 4 dígitos significativos). Ancorado no traço que separa código e descrição (o número da nota não é seguido de traço).
- **Discriminação**: linha do item logo após o cabeçalho da tabela ("...Preço Total"), no formato "1 TRANSPORTE E DESTINAÇÃO FINAL DE RESIDUO CLASSE II B 16.500,00! 16.500,00" → removidos a quantidade inicial e os dois valores finais (o "!" é ruído de borda).
- **⚠️ Valores (camada digital)**: nota **ISENTA** (alíquota 0 / ISS 0 / sem retenção — a própria nota diz "NÃO CABE RETENÇÃO NA FONTE"). O OCR troca o **1º dígito do VALOR TRIBUTÁVEL** (14.685 → **74.685**) e deixa o **VALOR LÍQUIDO em branco**, então `base`/`líquido` vêm da **camada digital** (`pdfminer`, relida no ramo de valores) — que traz os números exatos. O rótulo "TOTAL SERVIÇOS 16.500,00" sai limpo no OCR e identifica o bruto. **Decisão do usuário**: `ValorServicos` = total bruto (16.500), `BaseCalculo` = valor tributável (14.685); líquido = base.
- **Entidades**: blocos "IDENTIFICAÇÃO DO PRESTADOR/TOMADOR"; rótulos "Nome / Razão", "CPF / CNPJ:", "CEP: ... Município: ... UF:", "Logradouro: ... Nº ...", "Bairro: ...". Quirk: bairro do tomador sai **"API"** (o OCR comeu o "I" de "IAPI") — mantido fiel, sem inventar a letra.
- **IBGE**: Camaçari (**2905701**) e Salvador (**2927408**) já estavam em `KNOWN_CITIES`; nada a registrar, mas os códigos são **asseridos** no teste.
- **Código de verificação**: nota avulsa física **não** tem hash de autenticidade → cai no placeholder `XXXX-XXXX` e gera o aviso honesto "Código de verificação/autenticidade não encontrado".

### Faturas de locação / serviços específicos

Layouts de emissores fixos (a razão social e o endereço do prestador são conhecidos e, em vários casos, fixados no código). Geralmente `CodigoVerificacao = "FATURA"` e item de serviço `0601` (locação de bens móveis).

### 17. Localiza — `localiza_fatura`
- Faturas de locação/revenda de serviços veiculares da Localiza Rent A Car.
- Identificado por "LOCALIZA RENT A CAR S/A" ou "FATURA / DUPLICATA".
- **Duas estruturas de texto bem diferentes, dependendo da nota (mesmo formato de PDF)**: (a) via OCR, quando a fonte embutida do PDF é ilegível para o pdfminer (texto quebrado em linhas, Tesseract) — a maioria das notas testadas; (b) via texto digital direto do pdfminer, quando a fonte é legível — tudo numa ÚNICA linha corrida, sem nenhuma quebra. As DUAS variantes, além disso, têm a ORDEM dos campos diferente entre si (e até entre notas do mesmo tipo — ver abaixo). Por isso nenhum regex do layout pode depender de `\n` ou de uma ordem fixa entre rótulos; todos usam âncoras "pegue a ÚLTIMA ocorrência antes de X" (via `finditer`) ou prefixos estáveis (ex.: logradouro sempre começa por AV/ROD/RUA/TV/...), validados contra 4 notas reais de filiais e formatos distintos.
- **CNPJ/endereço do prestador NÃO são fixos no código**: a Localiza usa um CNPJ por filial (raiz `16.670.085`, sufixo do estabelecimento). Um hardcode anterior (CNPJ/endereço de uma única filial amostrada) quebrava silenciosamente qualquer nota de outra filial com um `ValidationError` não capturado corretamente — a nota inteira era descartada (0 XMLs), sem aviso. A ordem relativa de "CNPJ - ..." e do logotipo "Localiza" TAMBÉM varia entre notas (ora um vem antes do outro) — a extração pega a última ocorrência de CNPJ e de CEP/Município/UF antes de "FATURA / DUPLICATA", não assume uma ordem fixa.
- A razão social do tomador aparece em 2 formatos: (a) quebrada em 2 fragmentos por colunas intercaladas do OCR (nome antes do rótulo "CÓDIGO:", sufixo "LTDA" depois do rótulo "CLIENTE:"); (b) já completa logo após "CLIENTE:" no texto digital sem quebras (só falta separar o sufixo societário colado, ex. "SUSTENTABILIDADELTDA"). Distinguido pela ordem entre os rótulos "CLIENTE:" e "CÓDIGO:" no texto.
- O CNPJ do tomador é buscado numa janela **depois** do endereço do tomador (buscar no texto inteiro pegaria o 1º "CNPJ:", que é o do prestador).
- "VALOR TOTAL" e o valor em R$ podem não ficar colados no texto (vencimento/condição de pagamento entre os dois, às vezes até colado sem espaço à data seguinte: "TOTAL04/05/2026") — regex tolerante a até 80 caracteres entre rótulo e valor, sem `\b` após "TOTAL" (letra→dígito não é fronteira de palavra pro regex).
- O "número" da fatura vem com um código de filial prefixado ("Nº: ACPIT - 311630") — o ERP contábil de destino rejeita "Número da NFS-e" não numérico, então extrai-se só os dígitos, descartando o prefixo (e qualquer rótulo colado sem espaço logo depois, ex. "212176CLIENTE:").
- A fatura (pág. 1) costuma vir seguida de um boleto/Pix (pág. 2) que repete "LOCALIZA RENT A CAR S/A" só como nome do beneficiário — tratado como continuação da mesma nota, não uma 2ª fatura.
- Não é uma NFS-e municipal (não tem código de verificação eletrônico) → `CodigoVerificacao = "FATURA"`, mesmo padrão dos demais layouts de locação.

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

### 26b. F&F Comércio — `ff_locacao`
- Fatura de locação de CFTV da F&F Comércio e Serviços de Telecomunicações de Segurança Eletrônica LTDA, **PDF 100% imagem** (escaneado).
- **Detecção pelo CNPJ do emissor** (`13.398.812/0001-89`), não pela frase "FATURA DE LOCAÇÃO": o layout de 2 colunas do OCR quebra essa frase em duas linhas, intercalada com o nome da empresa ("...SEGURANÇA FATURA DE" / "ELETRONICA LTDA LOCAÇÃO") — a marca genérica de locação nunca casa nesta nota.
- **⚠️ Leitura padrão (zoom 3x, objeto PIL em memória) perde mais da metade do conteúdo desta nota específica** (558 de 1016 caracteres reais — some o rótulo "RAZÃO SOCIAL", o bloco "ENDEREÇO"/"CNPJ/CPF" do tomador e a tabela de itens inteira). O MESMO pixmap, passado ao Tesseract por **caminho de arquivo** em vez de objeto PIL em memória, recupera o texto completo — provável diferença de metadado de DPI mudando o pré-processamento interno do Tesseract. Isolado como recut de layout específico (`_ocr_recut_ff_locacao`, disparado quando o CNPJ da F&F já foi reconhecido no texto degradado, só troca se o resultado for estritamente mais completo) — os outros ~35 layouts que já usam OCR continuam no caminho por objeto, sem alteração.
- **Prestador (locadora) fixo no código**: CNPJ, razão social, endereço e telefone, mesmo padrão dos demais locadores de filial única (LMR/Geração/Locontainers).
- **Tomador extraído do bloco "DESTINATARIO"**: razão social mantém o código de cliente colado ("7396 - Boutique Guarajuba PH Gestão"), sem inventar separação que a nota não delimita; endereço é o nome do próprio estabelecimento (não rua+número tradicional) — extraído como está.
- **⚠️ Campo "VALOR TOTAL DA FATURA" com placeholder de template não substituído na própria nota-fonte** (não é erro de OCR — confirmado na imagem renderizada: `R$ #venda_valor_total#`, bug do sistema de faturamento do emissor). O valor real vem da tabela de itens (coluna "Valor Liquido"; se uma nota futura vier com o campo do cabeçalho devidamente preenchido, ele é usado primeiro).
- Não é NFS-e municipal (operação não sujeita a ISS) → `CodigoVerificacao = "FATURA"`, item de serviço `0601`, mesmo padrão dos demais layouts de locação.

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

*Documentação atualizada em: 2026-07-31 (37 layouts; novo layout **F&F Comércio** — `ff_locacao`, fatura de locação de CFTV, detectado pelo CNPJ do emissor por causa da frase "FATURA DE LOCAÇÃO" quebrada pelo OCR de 2 colunas, com recut dedicado de OCR por caminho de arquivo — `_ocr_recut_ff_locacao` — e valor extraído da tabela de itens por causa de um placeholder de template quebrado na própria nota-fonte; mais quatro fixes de robustez em layouts existentes: (1) Localiza — `localiza_fatura` tornado robusto a 2 estruturas de texto distintas (OCR multi-linha vs. digital em linha única sem quebras) e a ordem variável de rótulos entre notas, mais correção do número — só dígitos — e do regex de valor total; (2) São Paulo digital — `sao_paulo_sp` ganhou ramo dedicado de extração de entidades/valores, corrigindo CNPJ/razão/endereço/ISS que saíam trocados numa nota real onde os cabeçalhos de seção vêm deslocados no meio dos próprios dados da entidade — nota AMIL/TEMIS; (3) Camaçari escaneado — `camacari_ba_scan` corrigido: o recorte dedicado do cabeçalho (`_ocr_header_box_camacari`) cortava a linha inteira do "Número da Nota", que sumia por completo — número nº 4494; (4) Barreiras — `barreiras` ganhou ramo dedicado de valores para a variante de locação de bens móveis não sujeita a ISS (item "00.00" → `0000`), cuja grade de 3 colunas ("rótulos primeiro, valores depois") caía no fallback zero no genérico — nota nº 1162).*
