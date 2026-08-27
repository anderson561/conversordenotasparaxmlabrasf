# Changelog

Todas as mudanças notáveis deste projeto são documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
e este projeto segue [Versionamento Semântico](https://semver.org/lang/pt-BR/).

Changelogs detalhados de features específicas (com o passo a passo técnico
completo) ficam em arquivos próprios: [CHANGELOG_BRASILIA.md](CHANGELOG_BRASILIA.md),
[CHANGELOG_CAMPINAS.md](CHANGELOG_CAMPINAS.md). O histórico completo, sessão a
sessão, de todos os layouts/fixes entregues está em
[DOCUMENTACAO_CONVERSAO.md](DOCUMENTACAO_CONVERSAO.md).

## [Não lançado]

### Corrigido

- **`danfe_produto` (NF-e Modelo 55/ICMS) em nota ESCANEADA (nota nº 764, PENELI METAIS LTDA)**: o cabeçalho funde 3 colunas na mesma faixa de Y (letterhead do emitente | caixa "DANFE" | código de barras), derrubando a palavra "DANFE" por completo e quebrando "Documento Auxiliar da Nota Fiscal Eletrônica"/"0-ENTRADA"/"1-SAÍDA" — sem tratamento, a nota caía no fallback genérico de NFS-e/DANFSe (documento de SERVIÇO/ISS), saindo com razão social vazada, valor zerado e CNPJ do tomador cruzado. Corrigido com detecção OCR-tolerante (marca alternativa exclusiva do Modelo 55, só ativa com `from_ocr=True`), extrator dedicado (`_parse_danfe_produto_ocr`, o parser digital original — nota nº 52.136/GRAN COFFEE — fica intocado) e 3 recortes dedicados (emitente/grade de ICMS/linha do item). Suíte 325→329 verdes; 4 testes novos em `tests/test_danfe_produto_escaneado.py`. Desenvolvido em branch própria (`feature/layout-danfe-55`), separada de layouts de NFS-e/SERVIÇO. Ver detalhes em [DOCUMENTACAO_CONVERSAO.md](DOCUMENTACAO_CONVERSAO.md#danfe-estadual--nf-e-de-produto-modelo-55--xml-nf-e-400).

## [1.4.1] - 2026-08-26

### Corrigido

- **Fix — Bloco inteiro do PRESTADOR e grade de valores derrubados pelo PSM
  padrão do OCR, sem nenhuma marca d'água (layout Salvador/BA, nota real nº
  00024910, BDP LOGÍSTICA INTEGRADA DE RESÍDUOS LTDA -> BONI TRANSPORTES,
  PDF de 1 página)**: a leitura de página inteira em zoom 3x com PSM
  automático pulava direto de "Código de verificação:" pra "Endereço:" —
  rótulo "PRESTADOR DE SERVIÇOS", CPF/CNPJ e Nome/Razão Social nem chegavam
  a aparecer (ausentes, não garblados), e a grade de valores (Base de
  Cálculo/Alíquota/ISS/Líquido) saía por completo perdida. O MESMO zoom com
  PSM 6 (bloco único de texto) recupera a maior parte desse bloco — `_ocr_page`
  agora tenta as duas leituras quando o layout Salvador é detectado e usa a
  que pontuar melhor em `_score_ocr_text`, preservando o comportamento já
  validado nas notas onde o PSM padrão já é suficiente. 3 bugs adicionais
  achados na mesma nota, generalizáveis: (1) razão social do PRESTADOR sem
  rótulo "Nome/Razão Social" reconhecível pegava a própria linha do CNPJ
  como candidata — corrigido pulando qualquer linha que comece com um CNPJ
  formatado no fallback linha-a-linha; (2) razão social do TOMADOR sem
  rótulo "CPF/CNPJ" reconhecível engolia o CNPJ formatado e o endereço
  inteiro na mesma captura (sem stop-pattern pro NÚMERO do CNPJ, só pro
  rótulo) — corrigido adicionando o padrão de CNPJ formatado como
  stop-pattern; (3) "VALOR TOTAL DA NOTA" saiu com "DA"/"NOTA" colados e o
  valor sem separador decimal (não confiável pra reformatar) — usa a linha
  "Valor Liquido R$ X" (formatação intacta) como último recurso em vez de
  deixar `valor_servicos` como 0,00. Também generalizada a votação por
  maioria do Número da Nota (`_ocr_numero_nota_salvador_votado`): 2 amostras
  novas (zoom 7x/9x, PSM 4) e o critério de aceite relaxado de maioria
  estrita pra pelo menos metade das amostras, corrigindo um caso em que as 4
  amostras originais não convergiam numa maioria clara. CNPJ do prestador e
  do tomador, Código de Verificação e logradouro/CEP de ambas as entidades
  continuam ilegíveis mesmo após o PSM 6 — mantidos como sentinela/"Não
  informado" (nunca fabricados), mesma família de degradação já registrada
  numa issue GitHub aberta para o padrão recorrente Salvador/Luniteck-BONI.
  NÃO foi criado um layout `salvador_bdp` — é o mesmo template oficial
  "PREFEITURA MUNICIPAL DO SALVADOR" já coberto por `LAYOUT_SALVADOR`, só
  mal-escaneado. Suíte 321→**325 verdes** (4 testes novos).

- **Fix — Razão social fabricada com ruído em vez de sentinela honesto, e
  Código de Serviço perdido, na mesma nota já catalogada como
  catastroficamente degradada (layout Salvador/BA, nota real nº 2419,
  LUNITECK SOLUÇÕES E DESENVOLVIMENTO EM TECNOLOGIA LTDA ME -> BONI
  TRANSPORTES, pág.1 — a pág.2/NFTS já era e continua correta)**: pedido de
  auditoria do usuário na mesma nota já diagnosticada em 2026-08-21 como
  catastroficamente degradada (Número/CNPJ/Código de Verificação já saem
  com sentinela honesto, reconfirmado sem regressão). Achados novos: (1) o
  guard `_NOISE_RAZAO` que deveria rejeitar o próprio rótulo garblado
  "CPF/CNPJ Inscrição Municipal" como razão social tinha um bug de `\b` que
  nunca casava contra a palavra completa "Inscrição"/"Endereço" — proteção
  morta desde sempre, corrigida de forma genérica (beneficia os ~30 layouts
  que usam este extrator de entidade compartilhado); (2) razão social da
  BONI TRANSPORTES (tomadora) vazando para o bloco do PRESTADOR quando o
  cabeçalho "TOMADOR DE SERVIÇOS" não sobra reconhecível em nenhuma forma —
  corrigido com um guard específico (BONI nunca é prestadora nesta base);
  (3) fragmentos de ruído puro (colchete/pipe de borda de tabela, dois-pontos
  de rótulo colado, fragmentos de 3 letras) passando como razão social —
  3 guards genéricos novos; (4) uma 3ª variante de garble do rótulo
  "Nome/Razão Social" ainda diferente das 2 já cobertas — trocada a
  enumeração de regex literais por comparação fuzzy (`difflib`) contra o
  rótulo canônico; (5) `servico_codigo` caindo no fallback genérico "03115"
  mesmo com a linha "Código de Tributação do Município: 1402-004 -
  Assistência técnica" legível nesta página — novo fallback para
  `LAYOUT_SALVADOR`, confirmado batendo com o item real da pág.2 (14.02).
  **Tentativa revertida durante o desenvolvimento:** um requisito adicional
  de "parece nome de empresa" no fallback mais às cegas causou a busca por
  razão social atravessar a quebra de página e capturar texto da PÁG.2,
  fazendo `parse_multiple` deduplicar as 2 páginas como se fossem a MESMA
  nota (perdendo a nota da pág.1 inteira do resultado) — revertido antes de
  entrar na suíte; razão social do prestador nesta nota específica segue sem
  recuperação garantida (mesma decisão de 2026-08-21 de não perseguir mais
  fixes de regex nesta página específica). Suíte 314→**319 verdes**; 5
  testes novos em `test_salvador_lauro_freitas_2419_razao_e_codigo_servico.py`.

  **Ampliação na MESMA leva (nota real nº 2418, PDF irmão da 2419, mesmo
  prestador LUNITECK — achado real 2026-08-25):** o usuário reportou que a
  LUNITECK "não está extraindo corretamente" nesta 2ª nota e pediu para
  verificar se havia ferramenta no projeto pra contornar. Achado mais grave:
  a heurística "confiar na grade de Base de Cálculo recuperada quando
  diverge da linha isolada VALOR TOTAL DA NOTA" (introduzida pra corrigir a
  nota 00000061/MCLA, cujo cabeçalho saía consistentemente errado por
  R$0,03) **trocou um valor CORRETO por um ERRADO nesta nota** — "VALOR
  TOTAL DA NOTA = R$397,14" estava certo e legível, mas a mesma grade
  densamente corrompida fez o recut ler "8,00" — zoom único validado numa
  nota não generaliza pra uma nota irmã. Corrigido exigindo que a
  divergência entre a grade e o cabeçalho seja PEQUENA (≤10%, plausível
  como 1 dígito trocado, cobre o caso real do MCLA) antes de confiar na
  grade; divergência grande (aqui, ~98%) mantém o valor do cabeçalho e
  deriva a Base dele. **Decisão do usuário (via `AskUserQuestion`):** não
  implementar o padrão "prestador fixo" (identidade hardcoded, já usado
  para BIOCONTROL/PJB Construção/F&F Locação) pra LUNITECK apesar do CNPJ
  raiz já confirmado em 2 notas reais — razão social/CNPJ do prestador
  nesta nota seguem sem recuperação garantida, mesma decisão já tomada.
  Suíte 319→**321 verdes**; 2 testes novos em
  `test_salvador_2418_valor_grade_recut_divergencia.py`.

- **Fix — Prestador/Tomador colidiam no mesmo CNPJ e Valor Total saía errado
  quando o PSM automático do Tesseract derruba a razão social do prestador e
  o cabeçalho "TOMADOR DE SERVIÇOS" (layout Salvador/BA)** (nota real nº
  00000061, MCLA CONSTRUÇÕES LTDA -> BONI TRANSPORTES, LOGISTICA E COMERCIO
  LTDA; achado real 2026-08-25): a leitura de página inteira (zoom 3, PSM
  padrão) derrubava POR COMPLETO a linha "Nome/Razão Social: MCLA
  CONSTRUÇÕES LTDA" do prestador e corrompia "TOMADOR DE SERVIÇOS" a ponto
  da palavra "TOMADOR" não sobreviver nem corrompida ("vVIÇOS") — sem os
  dois sinais, o bloco genérico do prestador não tinha onde parar e vazava a
  razão/CNPJ do TOMADOR para as duas entidades; a guarda existente de CNPJ
  de BONI TRANSPORTES (corrige o CNPJ crônico mal-impresso dessa
  contraparte) então disparava para as duas, reforçando o erro. A linha
  "VALOR TOTAL DA NOTA" também saía com 1 dígito errado ("R$6.875,81" em vez
  de "R$6.878,81", confirmado por imagem em zoom 20x) — defeito irrecuperável
  mesmo numa releitura ultra-zoom dedicada da própria linha
  (`_ocr_recut_valor_total_marca_agua_salvador`).
  Correções: (1) CNPJ agora tolera vírgula no lugar do ponto como separador
  E espaço espúrio antes dele (`_extrair_entidade`, `_scavenge_all_cnpjs`) —
  os dígitos do prestador já saíam certos, só a pontuação rejeitava o
  candidato; (2) novo recorte dedicado `_ocr_recut_prestador_razao_salvador`
  recupera a razão do prestador e é EMENDADO (não prependado solto) logo
  antes do 1º "Endereço" do documento — o recut do tomador
  (`_ocr_tomador_salvador`) passa a disparar também quando o cabeçalho
  "TOMADOR" some por completo, não só quando aparece malformado; (3) novo
  recorte `_ocr_recut_base_calculo_grade_salvador` localiza a grade de
  valores dinamicamente (âncora "(R$" na linha de rótulos, não no texto
  "Base de Cálculo"/"Deduções" em si, que sai corrompido de formas
  imprevisíveis) e recupera só a Base de Cálculo; quando Deduções = 0 e ela
  diverge do "VALOR TOTAL DA NOTA" da linha isolada, `_extrair_valores`
  passa a confiar na grade (2 leituras redundantes) sobre a linha única.
  Suíte 309→**313 verdes**; 4 testes novos em
  `test_salvador_prestador_tomador_colisao_psm_padrao.py`.

  **Ampliação na MESMA leva (nota real nº 00000006, RC INFORMÁTICA E
  ACESSÓRIOS LTDA -> BONI TRANSPORTES; achado real 2026-08-25):** 2 bugs
  adicionais da mesma família, achados ao verificar outra nota reportada
  pelo usuário. (4) O próprio rótulo "Nome/Razão Social" saía garblado a
  ponto de nenhum filtro reconhecer ("NomeiRazão Socia'" — a "/" vira "i" e
  o "l" final de "Social" some) mas ainda "parecia" texto normal o
  bastante pra passar como razão social de verdade, roubando a linha real
  (a empresa) que vinha logo depois — `is_valid_razao` agora rejeita esse
  padrão de rótulo garblado explicitamente. (5) Dois bugs de ORDEM nos
  recortes dedicados do Salvador, ambos causados pelo mesmo problema
  estrutural — um gatilho/índice calculado sobre o texto JÁ ACUMULADO com
  prepends sintéticos anteriores, em vez do texto real da página: (5a) o
  gatilho da marca d'água (`nenhum rótulo de PRESTADOR antes do 1º
  "TOMADOR"`) via falso-positivo quando outro recorte já tinha prependado
  um snippet curto (ex. "CPF/CNPJ: ...") que não cita "PRESTADOR", mesmo
  com o rótulo real perfeitamente legível na página; (5b) o recorte que
  corrige CNPJ com 1 dígito trocado (`_ocr_recut_cnpj_invalido_salvador`,
  índice "0=prestador, 1=tomador") recebia um índice calculado sobre uma
  lista de candidatos que misturava texto sintético já prependado com o da
  página real, colando o CNPJ do PRESTADOR no bloco do TOMADOR. Ambos
  corrigidos avaliando/indexando contra uma cópia do texto ANTES de
  qualquer prepend Salvador-específico (`best_text_ocr_original`), nunca
  contra o acumulado. Suíte 313→**314 verdes**; 1 teste novo no mesmo
  arquivo.

## [1.4.0] - 2026-08-25

### Corrigido

- **Fix — Competência com ano trocado pelo OCR generalizado para TODOS os
  layouts (`_extrair_competencia`), guard que só rodava em `LAYOUT_SALVADOR`**
  (nota real nº 202600000016746, MAG COMERCIO VAREJISTA, layout Lauro de
  Freitas/BA 3ª variante; achado real 2026-08-25): o XML saía com
  `<Competencia>2025-07-24</Competencia>` (ano errado) mesmo com
  `<DataEmissao>2026-07-24T10:27:01</DataEmissao>` já correta no mesmo
  documento — o OCR lê "Competência: 24/07/2025" em vez do real
  "24/07/2026" (mesmo dígito trocado "6"→"5" já visto antes em Salvador,
  "0"→"9"). A correção para essa MESMA classe de erro (usar o ano da Data
  de Emissão quando o mês da competência bate mas o ano diverge — uma
  competência legítima de outro mês/ano sempre vem com mês diferente
  também) já existia, mas só dentro do branch `elif layout ==
  LAYOUT_SALVADOR`; `LAYOUT_LAURO_FREITAS` não tem branch próprio em
  `_extrair_competencia`, cai direto no fallback genérico
  (`_extrair_competencia_generica`), que nunca passava por essa validação.
  Como o raciocínio do guard não é específico de nenhum layout, movido do
  branch do Salvador para o fim da função, rodando incondicionalmente
  depois de QUALQUER branch (inclusive o fallback genérico) já ter
  tentado — corrige a mesma classe de bug em qualquer um dos ~44 layouts
  que ainda não tinham essa proteção, não só o que motivou o achado. Suíte
  303→**305 verdes**; teste novo
  `test_competencia_ano_ocr_trocado_generalizado.py` (2 casos: guard
  disparando fora de Salvador + guard NÃO disparando quando o mês
  realmente diverge, preservando competências de mês/ano anteriores
  legítimas).

- **Fix — Zoom único não confiável na 3ª variante do Lauro de Freitas/BA
  (`_ocr_recut_lauro_freitas_v3`), causando PDF "ignorado" (0 notas
  reconhecidas) em algumas notas do MESMO template já coberto** (nota real
  nº 202600000016746, MAG COMERCIO VAREJISTA → BONI LOGISTICA, R$410,00;
  achado real 2026-08-25, nota irmã da nº 202600000016748 do fix acima, só 2
  notas depois na numeração, mesmo prestador/template): mesmo com o recorte
  dedicado já implementado, um ZOOM ÚNICO por região não é confiável — o
  Tesseract lê o Número NFS-e de forma DIFERENTE (e diferente ENTRE SI) a
  cada zoom testado ("99260000001674%", "9250000001674%",
  "W2600000016746"...), a grade VALORES perde as 3 primeiras colunas
  ("Valor Serviço"/"Desc. Cond."/"Desc. Incond." somem), e o CEP do
  prestador perde 1 dígito ("4270º-450" em vez de "42701-450") no mesmo
  zoom que lê o resto do bloco certo — tudo isso na MESMA prestadora/
  template da nota já corrigida, provando que zoom fixo não generaliza.
  Corrigido com reamostragem + votação/derivação em vez de zoom único: (1)
  Número NFS-e reamostrado em 6 zooms × 2 PSMs (12 tentativas), votado
  pelos últimos 11 dígitos capturados + prefixo "20"+ano (ano extraído da
  Data de Emissão por FORMATO — `\d\d/\d\d/\d{4}\s+\d\d:\d\d:\d\d` — não por
  rótulo, que também sai embaralhado: "Dara e Mora de Emissão"); nova
  sentinela `LFV3_DATA_EMISSAO` (mesma técnica) resolve a Data de Emissão
  que antes caía no fallback "agora"; Código de Verificação só aceito com
  ≥2 tentativas concordando, senão cai no fallback honesto de página
  inteira (nunca fabricado); (2) CEP prestador/tomador reamostrado em 6
  zooms dedicados (`_cep_dedicado`), só aceita leituras com exatamente 8
  dígitos limpos — regex também passou a tolerar "CEP;" (ponto e vírgula em
  vez de dois-pontos); (3) grade VALORES: quando a extração estrita de 8
  colunas falha, reamostra só a dupla mais estável (Base de Cálculo +
  Alíquota, presente em TODAS as ~20 combinações testadas) e deriva o resto
  matematicamente (Valor Serviço = Base de Cálculo quando nenhuma tentativa
  indica desconto/dedução diferente de zero; Valor ISS = Base × Alíquota) —
  mesmo princípio já usado no recorte BioControl. Suíte 298→**303 verdes**;
  testes novos em `test_lauro_freitas_v3_numero_e_valores_votados.py`; zero
  regressão na nota 16748 já coberta (revalidada ponta a ponta).

- **Fix — 3ª variante do layout Lauro de Freitas/BA (`LAYOUT_LAURO_FREITAS`),
  template novo da plataforma compatível com a Reforma Tributária** (nota
  real nº 202600000016748, MAG COMERCIO VAREJISTA DE MATERIAL ELETRICO E
  SERVICOS TECNICOS DE INSTALAÇÃO E MANUTENÇÃO → BONI LOGISTICA LTDA,
  R$220,00; achado real 2026-08-25): a Prefeitura passou a emitir um
  template com campos IBS/CBS, NBS, Finalidade, Destinatário e Classificação
  Tributária ausentes das 2 variantes já cobertas (NFS-e regular e NFTS).
  Diagnosticado como bug na existente `LAYOUT_LAURO_FREITAS` (não um layout
  novo) — a marca de detecção já casava, mas a leitura de página inteira
  (zoom 3x) **perde por completo, não apenas corrompe**, vários campos deste
  template: Número NFS-e/Código de Verificação saem truncados ("4F723" em
  vez de "4F7233055"); o CEP do prestador nunca aparece; o bloco "Cód. Trib.
  Municipal" (coluna esquerda de uma grade 2 colunas) desaparece inteiro; a
  grade VALORES (10 colunas) sai com só 5 rótulos e valores incompletos
  (retornava tudo zero). Corrigido com `_ocr_recut_lauro_freitas_v3`: 4
  recortes dedicados (cabeçalho zoom8/PSM6; bloco prestador+tomador zoom6/
  PSM6; tributação/atividade zoom6/PSM6; grade valores zoom8/PSM4 — PSM4
  leu 8/10 colunas certas contra PSM6 errando o separador decimal da
  alíquota "5,0000"→"50000"), devolvidos como sentinelas `LFV3_*` que
  `_extrair_numero`/`_extrair_codigo_verificacao`/`_extrair_codigo_servico`/
  `_extrair_valores`/`_extrair_entidade` (nova `_extrair_entidade_lauro_
  freitas_v3`) conferem ANTES da lógica das variantes 1/2, com fallback
  total pra elas quando o gatilho não dispara (nota antiga, sem "TRIBUTAÇÃO
  DE ISSQN" no texto). CNPJ do prestador recuperado com o dígito certo
  ("15.243.835", a leitura de página inteira trocava para "15.242.835" —
  cross-validado contra a linha "Recebi(emos)...CNPJ:" do rodapé); UF
  validada contra whitelist de UFs em vez de regex tolerante (zoom 6x lê
  "UF: BA" como "ur: BA"/"UF: EA" dependendo do recorte). Nº da casa do
  tomador ("11" em "RUA GERINO DE SOUZA FILHO 11 ITINGA") não foi
  recuperável em NENHUM zoom/PSM testado (Tesseract insiste em ler "TI"
  nesta fonte, mesmo com a imagem perfeitamente legível a olho nu) —
  mantido "S/N", nunca fabricado (campo de baixo impacto fiscal); razão
  social do prestador sai truncada em "...E MANUTEN" porque o próprio PDF
  original já imprime o campo cortado na borda da tabela (confirmado via
  inspeção visual do PDF-fonte, não é bug de OCR/extração). Suíte
  291→**298 verdes**; testes novos em
  `test_lauro_freitas_v3_mag_comercio.py`.

- **Fix — Competência com ano trocado em Salvador/BA (`salvador_ba`) e CNPJ
  do tomador impresso ERRADO na própria nota** (mesma nota nº 00003327/
  CONEX4 MULTIMÍDIA LIMITADA dos 2 fixes acima; software de importação do
  usuário — Domínio Escrita Fiscal — rejeitava o lote com "CNPJ do arquivo
  diferente do CNPJ da empresa ativa" e mostrava a data `01/07/2926`):
  - `Competencia` saía `2926-07-01` — OCR lê "COMPETÊNCIA 07/2926" ("0"→"9"
    no ano) — mesmo mês da Data de Emissão (já confiável, extraída de outro
    trecho do documento), só o ano divergia. Corrigido usando o ano da Data
    de Emissão quando o mês da competência bate mas o ano diverge — uma
    competência legítima de outro ano sempre vem com mês diferente também
    (nunca emitida meses depois sem que o mês mude), então o guard não
    afeta competências de fato distintas (ex. nota de janeiro para
    competência de dezembro do ano anterior).
  - CNPJ do tomador (BONI TRANSPORTES) saía com o sentinela
    `00000000000100`: diferente de TODOS os outros achados de CNPJ
    corrompido desta base (sempre um erro de LEITURA de um valor impresso
    certo), aqui o CNPJ está ERRADO NA PRÓPRIA IMAGEM da nota —
    "04.565.293/0001-99" impresso (confirmado em zoom alto), que reprova o
    dígito verificador. O usuário confirmou o CNPJ real como
    "04.555.283/0001-99" — mesma raiz já vista em várias outras notas desta
    base como tomador fixo/recorrente (notas 6508 e 2150, filiais
    "0001"/"0003" da mesma empresa). Nenhum recorte/zoom recuperaria esse
    valor (a sequência correta nunca esteve impressa nesta nota) —
    corrigido em `_extrair_entidade` apenas quando o CNPJ extraído já
    reprova o checksum E a razão social bate com "BONI TRANSPORTES", para
    não mascarar CNPJs genuinamente diferentes de outras empresas com nome
    parecido; nunca sobrescreve um CNPJ que já é válido.
  Suíte 285→**289 verdes**; testes novos em `test_notas_layouts.py` e
  `test_boni_transportes_cnpj_impresso_errado.py`.

- **Fix — Número da nota em Salvador/BA (`salvador_ba`) saía com 1 dígito
  trocado quando o recorte dedicado do cabeçalho lia num zoom "azarado"**
  (nota real nº 00003327/CONEX4 MULTIMÍDIA LIMITADA → BONI TRANSPORTES,
  R$ 690,00): `_ocr_header_box_salvador` (zoom fixo 4.5x) leu "09003327" —
  "0"→"9" — em todo PSM testado (4, 6, 11); confirmado contra a imagem real
  que o valor impresso é "00003327". Não é ruído de amostra única: nos zooms
  3x, 6x, 8x e 10x o mesmo recorte lê o valor certo em TODAS as tentativas —
  artefato de renderização específico daquele zoom para esta digitação.
  Corrigido com `_ocr_numero_nota_salvador_votado`, que reamostra a mesma
  caixa em zooms distintos (independente da checagem de validade do Código
  de Verificação, que nesta nota nunca passa) e usa maioria simples; o valor
  apurado é prependado em `_ocr_page` ANTES do recorte de zoom único, para
  que `_extrair_numero` (1º match vence) prefira o valor por maioria. Valor
  da nota (R$ 690,00) já saía correto, nenhuma mudança necessária ali.
  Achado colateral, fora do escopo pedido (não corrigido nesta entry, ver
  próxima): CNPJ/CPF do prestador e do tomador saíam os DOIS com o mesmo
  sentinela `00000000000100` nesta nota. Suíte 281→**283 verdes**; teste
  novo `test_salvador_numero_zoom_ambiguo.py`.

- **Fix — CPF/CNPJ do prestador em Salvador/BA (`salvador_ba`) saía com o
  sentinela `00000000000100`** (mesma nota nº 00003327/CONEX4 MULTIMÍDIA
  LIMITADA do fix acima): o CNPJ real do prestador, `09.034.217/0001-97`
  (confirmado pelo usuário e batendo com a nota irmã — pág. 2 do mesmo PDF,
  que já extraía esse CNPJ corretamente), saía como ruído sem nenhum dígito
  reconhecível na leitura de página inteira — só a Inscrição Municipal
  vizinha sobrevivia ("00.291.063/001-70"). Sem CNPJ válido em lugar nenhum
  do bloco (o próprio rótulo "PRESTADOR DE SERVIÇOS" sai "BRESTADOR DE
  SERVIÇOS", "B" no lugar de "P" — nem o fatiamento genérico reconhece onde
  o prestador começa), caía no fallback de sentinela compartilhado por
  prestador E tomador. Corrigido com `_ocr_recut_prestador_cnpj_salvador`,
  que reprocessa em zoom alto (8x) só a coluna esquerda da linha do CNPJ;
  `_ocr_page` prepende o valor recuperado (já validado por checksum) antes
  do resto do texto, para que a extração genérica de CNPJ (1º candidato
  válido vence) encontre esta leitura limpa primeiro. Prependado em
  `best_text` (não guardado só num atributo de instância): `parse_multiple`
  cria um `sub_ext` novo por nota/bloco e só propaga pra ele `raw_text` e
  poucos atributos específicos — um atributo novo não chegaria até a
  chamada real de `_extrair_entidade`. CNPJ do TOMADOR permanece com o
  sentinela nesta nota — fora do escopo pedido pelo usuário ("trate
  exclusivamente o CNPJ [do prestador]"); avisado via `Nfse.avisos`. Suíte
  283→**285 verdes**; teste novo `test_salvador_prestador_cnpj_ilegivel.py`.

- **Fix — CNPJ do prestador em Simões Filho/BA (`simoes_filho_ba`) saía com 1
  dígito errado** (nota real nº 122/VITORIOS EMPILHADEIRAS, mesma nota do
  entry abaixo): o registro anterior deste CHANGELOG documentava
  `50.945.432/0001-11` como "limitação do motor de OCR" após teste
  exaustivo (zooms 3-12, 4 PSMs, whitelist de caracteres) — aceito como
  best-effort por acreditar-se irrecuperável. O usuário confirmou o CNPJ
  real como `50.949.432/0001-11` ("945" deveria ser "949"). Corrigido sem
  depender de melhorar a leitura da MESMA região degradada: o mesmo CNPJ do
  prestador é citado de novo, fora do bloco PRESTADOR, na seção de forma de
  pagamento da discriminação ("Condições de pagamento ... Pix CNPJ:
  50.949.432/0001-11") — essa segunda ocorrência sempre saiu correta em
  toda leitura de OCR testada nesta sessão. `_extrair_entidade_simoes_filho`
  agora valida o dígito verificador do CNPJ lido no bloco PRESTADOR e, se
  falhar, usa essa citação alternativa (também validada) como fallback.
  Suíte 281 verdes; `test_prestador_e_tomador_nao_compartilham_cnpj`
  atualizado para o valor correto.

### Adicionado

- Novo layout **Barueri/SP** (`barueri_sp`, barueri.sp.gov.br/nfe). Nota real
  nº 0380578, ALELO INSTITUIÇAO DE PAGAMENTO S.A. → CLINICA PNEUMOLOGICA PROF
  ALMERIO MACHADO (Salvador/BA), R$ 2,74 de tarifa (fatura de "agenciamento,
  corretagem ou intermediação" cobrada pela Alelo sobre um benefício-
  alimentação de R$ 430,00 repassado ao tomador). PDF digital (pdfminer, sem
  OCR). Peculiaridades de ordem de leitura por campo (nenhuma delas segue o
  padrão único de outro layout já suportado): a caixa de cabeçalho é uma
  grade 2 colunas × 3 linhas lida por COLUNA, então "Data Emissão" e "Hora
  Emissão" nunca ficam adjacentes um ao outro; "Código Autenticidade" aparece
  2× no documento — a 1ª ocorrência tem "Hora Emissão" colado logo abaixo (não
  o valor real), corrigido iterando todas as ocorrências e aceitando a 1ª cujo
  valor seguinte já pareça um código de verdade (tem dígito); o bloco do
  PRESTADOR (razão social + 2 linhas de endereço) vem em ORDEM FIXA antes de
  qualquer rótulo de campo, mapeado por posição; "CEP"/"Bairro" do TOMADOR
  saem como 2 rótulos consecutivos com um único valor combinado logo abaixo
  ("40150-130 Graça", sem separador); a grade do item (Descrição do
  Serviço/Código Serviço/Alíquota/Valor Unitário/Valor Total) e a grade de
  retenções federais (IRRF/PIS-PASEP/COFINS/CSLL) seguem o padrão "N rótulos
  dumped, depois os N valores na mesma ordem" já visto em Monte Santo/Ginfes/
  Santos. Decisão de modelagem do usuário: "VALOR LIQUIDO DA NOTA" impresso no
  rodapé (R$ 432,74) inclui o repasse a terceiros (R$ 430,00, crédito de
  benefício-alimentação que a Alelo só está repassando, não é receita de
  serviço) somado à tarifa — usar esse valor como `ValorServicos`/
  `ValorLiquidoNfse` sobrestimaria em ~150× o valor tributável real.
  `ValorServicos`/`BaseCalculo` = "TOTAL DE TARIFA" (R$ 2,74, bate com o
  "Valor Total" da grade do item); `ValorIss` mantido em 0,00 (nenhum valor de
  ISS impresso separadamente — "TOTAL DE IMPOSTOS" bate exatamente com o IRRF
  sozinho, não fabricado); o repasse é descartado do XML (não é
  `ValorDeducoes` nem faz parte do serviço tributável) e sinalizado em
  `Nfse.avisos` para o usuário conferir manualmente se precisa de tratamento
  contábil à parte. Código de serviço extraído como impresso (4 primeiros
  dígitos de "100202220" → "1002"), sem reclassificação manual. Testes novos
  em `tests/test_barueri_sp_layout.py`.

- Novo layout **Simões Filho/BA** (`simoes_filho_ba`, constante já existia mas
  sem extração dedicada nem prioridade de detecção correta). Nota real nº 122
  (VITORIOS EMPILHADEIRAS COMERCIO E SERVIÇOS LTDA → BONI TRANSPORTES,
  LOGISTICA E COMERCIO LTDA, R$ 440,00), pág. 1 de um PDF de 2 páginas cuja
  pág. 2 é a nota irmã Lauro de Freitas/NFTS. Mesma plataforma/template de
  Barreiras/BA ("Data Fato Gerador | Exigibilidade de ISS | Regime Tributário
  | Número RPS | Serie RPS | Nº da Nota Fiscal") — a marca genérica de
  Barreiras casava PRIMEIRO na cadeia de detecção e a nota inteira caía no
  layout errado; corrigido detectando pelo nome da PREFEITURA ("PREFEITURA
  MUNICIPAL DE SIMÕES FILHO") ANTES do marcador genérico compartilhado, em
  `_detect_layout` e `_detect_layout_page`. Blocos "PRESTADOR"/"TOMADOR" com
  rótulo→valor na mesma linha, seguidos de uma linha SOLTA "<Município> - <UF>
  - CEP: <cep>" sem rótulo próprio (não reconhecida pelo parser genérico,
  caía em "Não informado"/fallback de Salvador) — nova
  `_extrair_entidade_simoes_filho` dedicada. Achados corrigidos: `Numero`
  saía "246" (vazado de "orçamento nº 246" na discriminação do serviço, não o
  "Nº da Nota Fiscal" real "202600000000122" — âncora tolerante a colunas
  fundidas pelo OCR); CNPJ do prestador saía IGUAL ao do tomador
  (cross-contaminação de entidade); grade de valores "VALOR SERVIÇO (R$)
  DEDUÇÕES (R$) DESCONTO INCONDICIONAL (R$) BASE CÁLCULO (R$) ALÍQUOTA (%) ISS
  (R$)" não tinha extração própria (Alíquota/ISS saíam zerados) — Alíquota sem
  separador decimal no OCR ("285" em vez de "2,85") tratada como
  percentual×100; `Discriminacao` vazava até o fim do documento inteiro
  (grade de valores + demonstrativo de tributos + rodapé legal), sem limite
  dedicado até "OBSERVAÇÃO". Recorte OCR dedicado em zoom 6x do bloco do
  PRESTADOR (`_ocr_recut_prestador_simoes_filho`) recupera CEP e Inscrição
  Municipal quando a leitura de página inteira erra (best-effort, como outros
  recortes desta base — pode cair de volta ao valor do corpo em notas/rodadas
  de OCR menos favoráveis). ~~CNPJ do prestador permanece com um possível
  dígito trocado~~ — **corrigido, ver entry "Fix — CNPJ do prestador" no topo
  deste arquivo** (o dígito era mesmo recuperável, via a citação do CNPJ na
  seção de pagamento). Pelo mesmo motivo,
  `CodigoVerificacao` (valor real alfanumérico "bd17528e3", conferido
  caractere a caractere contra a imagem) fica no sentinela `XXXX-XXXX` — toda
  tentativa de OCR devolve uma leitura numérica diferente e garantidamente
  errada, nunca o valor real; sentinela honesto é preferível. **Corrigido também
  o código IBGE de Simões Filho/BA no `IBGEResolver.KNOWN_CITIES`: estava
  `2929206` (errado, nunca conferido contra fonte oficial) — a própria
  Prefeitura imprime na nota o código oficial `2930709` (confirmado contra
  cidades.ibge.gov.br); afeta também o prestador fixo do `LAYOUT_PJB_LOCACAO`
  (mesma cidade), corrigido junto.**
  - **Fix — Data de Emissão caindo no fallback "agora" (pedido explícito do
    usuário após o primeiro round: "Data de emissão incorreta")**: a linha
    "Emitido em 22/07/2026 21:14:46" nunca sai legível do OCR nesta
    plataforma — testado exaustivamente (zooms 3 a 14, autocontraste,
    binarização, whitelist de caracteres, recorte isolado da faixa, mesma
    região castigada pelo QR Code/marca d'água do Código de Verificação):
    cada tentativa devolve dígitos/separadores diferentes, nunca o valor
    real. Sem tratamento dedicado, `DataEmissao` caía em "agora" (a
    `Competencia` saía do MÊS ERRADO — agosto em vez de julho). Corrigido com
    um fallback que usa a data de atendimento citada na própria discriminação
    do serviço ("...atendimento realizado no dia 15/07/2026") — texto livre,
    fora da faixa degradada, que sobrevive ÍNTEGRO em toda leitura testada.
    Não é o timestamp exato de emissão (hora fica 00:00:00), mas acerta
    dia/mês/ano reais, confirmados de forma independente pela nota irmã
    (Lauro de Freitas/NFTS, mesma transação): "Competência: 07/2026" — as
    duas fontes concordam em julho/2026, nunca em agosto.
  - `Numero` (vazava "246" do orçamento) e o CNPJ do prestador (saía IGUAL ao
    do tomador) já estavam corrigidos desde o commit anterior desta mesma
    branch — reconfirmados contra a nota real após o usuário reportar os 3
    problemas juntos ("Número incorreto; data de emissão incorreta; tomador
    do serviço incorreto"): o XML que o usuário viu ainda era da versão
    ANTES do merge desta branch.
  Suíte 269→**281 verdes**; teste novo
  `test_data_emissao_usa_data_de_atendimento_em_vez_de_hoje` em
  `test_simoes_filho_layout.py` (9 testes) e
  `test_lauro_de_freitas_nfts_simoes_filho_prestador.py` (3 testes, cobrindo 3
  achados novos na pág. 2/Lauro de Freitas NFTS da mesma nota: rótulo
  "Nome/Razão" do prestador saindo "Noma/Razão" não reconhecido — prestador
  caía em "Não Identificado"; "UF." com ponto em vez de dois-pontos vazava
  "UF. BA" inteiro para dentro do Município do tomador; grade de valores
  degradada por completo na leitura de página inteira, salvo um 3º fallback
  que recupera Dedução/Base pela janela entre "ITEM DA LISTA DE SERVIÇOS" e
  "VALOR LÍQUIDO DA NOTA FISCAL").

- Novo layout **Goiânia/GO** (`goiania_go`) — plataforma ISSNet Online
  (issnetonline.com.br/goiania). Nota real nº 4 (ID Producao Musical Ltda →
  ELOS ESTUDIO E SERVICOS LTDA, R$ 600,00) caía inteira em `LAYOUT_CUIABA`:
  o detector daquele layout casava a palavra solta "ISSNet" (sem exigir
  "Cuiabá" por perto) em qualquer documento que a contivesse, e
  "issnetonline.com.br/goiania" contém "issnet" como substring — a nota
  saía com `valor_servicos` zerado, `ValorIss`/`ValorIr` trocados (ambos
  600,00; o real é ValorIss=12,06/ValorIr=0,00), razão social do prestador
  como "Série do Documento" (rótulo solto do letterhead), razão social do
  tomador igual ao próprio endereço dele, e um Intermediário fantasma
  inventado a partir do rótulo "Município Incidência".
- **Fix — colisão de detecção Goiânia/GO × Cuiabá/MT (`cuiaba_issnet`)**: a
  marca "ISSNet" de Cuiabá passou a exigir que não seja seguida de "online"
  (`ISSNet(?!\s*[Oo]nline)`); Goiânia agora detectada pelo nome do
  MUNICÍPIO, não pela marca da plataforma (compartilhada por várias
  cidades) — mesma decisão já tomada para Mata de São João/SAATRI e
  Rosário da Limeira/FUTURIZE. PDF digital cuja ordem de leitura do
  `extract_text()` padrão sai embaralhada de forma NÃO-monotônica (nem
  índice fixo resolve, diferente do Vinhedo) — usa
  `_reconstruir_texto_por_coordenadas` (mesma técnica do
  `camacari_sisloc`) antes de extrair qualquer campo; após a
  reconstrução, o bloco do PRESTADOR fica intercalado linha a linha com os
  metadados do cabeçalho (mesma faixa de Y) — cada regex de campo pula 1
  linha até o valor real. Suíte 265→268 verdes; teste novo
  `test_goiania_go_layout.py`.
- Novo layout **Vinhedo/SP** (`vinhedo_sp`) — plataforma Balker
  (vinhedo.balker.com.br). Nota real nº 139 (WEDO DECOR LTDA → NAUTICA
  INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA, R$ 1.049,79) caía no
  fallback `generico`, que produzia vários dados errados: `valor_servicos`
  zerado, `valor_iss` fabricado como `28.0` (não bate com o valor real,
  41,99), UF do prestador saindo `BA` em vez de `SP`, município do
  prestador caindo no fallback Salvador/BA (Vinhedo não cadastrada em
  `KNOWN_CITIES`), `servico_codigo` saindo `"03115"` (não bate com o item
  real "7.19"), e a razão social do TOMADOR saindo `"País: BRASIL"`.
  Estrutura própria: blocos "PRESTADOR DE SERVIÇOS"/"TOMADOR DE SERVIÇOS"
  com rótulo→valor adjacente na MESMA linha, mas o cabeçalho de seção
  "TOMADOR DE SERVIÇOS" aparece deslocado no MEIO do próprio bloco do
  tomador (mesmo quirk do Santos/SP) — fatiamento pela 2ª ocorrência de
  "Razão Social/Nome:". Data de Emissão em formato "DD/MMM/AAAA -
  HH:MM:SS" com mês abreviado em PT-BR. Grade de Retenções Federais +
  Base/Alíquota/ISS (2 linhas x 7 colunas sem linhas de separação) onde o
  pdfminer emite cada valor defasado em 1 coluna em relação ao próprio
  rótulo — mapeado por índice fixo, documentado no código. Suíte
  261→265 verdes; teste novo `test_vinhedo_sp_layout.py`.
- Novo layout **Santos/SP** (`santos_sp`) — plataforma Ginfes
  (santos.ginfes.com.br, mesma do `guarulhos_sp`, mas nota DIGITAL/pdfminer,
  não escaneada). Nota real nº 16 (IN.OUT MOVEIS E DECORACOES LTDA →
  NAUTICA INDUSTRIA E COMERCIO DE MOVEIS LTDA, R$ 6.666,86) caía no fallback
  `generico`, que produzia vários dados errados: `valor_servicos` zerado,
  `valor_iss` fabricado como `14.0` (número aleatório pescado do
  documento), UF do prestador e do tomador saindo `BA` em vez de `SP`,
  município do prestador caindo no fallback Salvador/BA (Santos não
  cadastrada em `KNOWN_CITIES`), e a razão social do TOMADOR saindo igual
  ao próprio endereço dele. Estrutura própria: cada campo é rótulo→valor
  adjacente, mas em ORDEM VISUAL de 2 colunas (não top-to-bottom) — o
  cabeçalho de seção "Tomador de Serviço" aparece deslocado no MEIO do
  próprio bloco do tomador, então o fatiamento usa a 2ª ocorrência do
  rótulo "CPF/CNPJ:" como âncora, não o cabeçalho. Duas grades "rótulos em
  cima, valores embaixo" — a de valores tem 13 rótulos fixos mas só 10
  valores nesta nota, porque ISSQN/IBS/CBS saem literalmente EM BRANCO
  (Simples Nacional, ISS pago via guia única/DAS) — mapeados pelos 2
  extremos fixos da lista (9 primeiros rótulos = 9 primeiros valores;
  Valor Líquido = último valor, robusto ao nº de campos em branco no
  meio). ISSQN mantido em 0,00 sempre (decisão do usuário: nunca
  derivar de Base×Alíquota, mesmo critério do fix Aracaju/WebISS). Santos
  cadastrada em `KNOWN_CITIES` (IBGE `3548500`, confirmado via API
  oficial). Suíte 257→**261 verdes**; teste novo `test_santos_sp_layout.py`.

- Novo layout **NFCom Salvador** (`nfcom_salvador`) — Empresa Baiana de
  Jornalismo S.A. (EBJ, CNPJ 14.583.041/0001-62, Salvador/BA), NFCom (Nota
  Fiscal de Serviço de Comunicação Eletrônica, padrão nacional SVRS,
  tributada por ICMS, não ISS). Nota real nº 624 (SIND DELEGADOS DE POLICIA
  DO EST DA BAHIA, R$ 400,00) caía no fallback `danfse_nacional` (a chave de
  acesso de 44 dígitos da NFCom também casa o gatilho amplo "Chave de
  Acesso") e saía com o valor ZERADO e o tomador com a razão social vazada
  do rótulo "Nº TELEFONE" — o parser da NFS-e Nacional não serve para a
  estrutura de uma NFCom. Corrigido com detecção específica do CNPJ do
  emissor, prestador fixo (mesmo emitente sempre), extração dedicada do
  tomador (rótulos e valores em ordem parcialmente invertida no bloco do
  destinatário) e leitura do "TOTAL A PAGAR (R$)". BaseCalculo/Aliquota/
  ValorIss mantidos em 0,00 propositalmente (decisão do usuário: ICMS ≠ ISS),
  sinalizado via `Nfse.avisos`. Suíte 225→**227 verdes**; teste novo
  `test_nfcom_salvador_layout.py`.

- Novo layout **São José/SC** (`sao_jose_sc`) — INTELBRAS S/A (CNPJ
  82.901.000/0001-27, matriz em São José/SC) → SINDICATO DOS DELEGADOS DE
  POLICIA (Salvador/BA), nota real nº 348301, R$ 178,80. Blocos "PRESTADOR
  DE SERVIÇOS"/"TOMADOR DE SERVIÇOS" com reordenação própria (razão social/
  nome fantasia antes do bloco de rótulos; Município realocado para o
  início da sequência de valores restante) e CEP/UF do prestador deslocados
  para depois do cabeçalho "TOMADOR DE SERVIÇOS" (artefato de leitura em 2
  colunas do pdfminer). IBGE de São José/SC (`4216602`) registrado em
  `KNOWN_CITIES`, confirmado via fonte oficial. Suíte 227→**229 verdes**;
  teste novo `test_sao_jose_sc_layout.py`.

- **DANFE Estadual — NF-e de Produto (Modelo 55)** (`LAYOUT_DANFE_PRODUTO`,
  novo modelo `NfeProduto` + `NfeProdutoTransformer`): 1º documento de
  PRODUTO/mercadoria (tributado por ICMS/IPI) tratado pelo conversor,
  estruturalmente diferente de qualquer NFS-e de serviço (tabela de N itens
  com NCM/CFOP, grade de ICMS, bloco de transportador). Achado a partir de
  uma nota real de compra de café (GRAN COFFEE COM. LOC. E SERVICOS S.A. →
  SINDICATO DOS DELEGADOS DE POLICIA DO ESTADO DA BAHIA, nº 52.136, R$
  595,00): caía inteira em `LAYOUT_LOCALIZA` porque o rótulo genérico
  "FATURA/DUPLICATA" (presente em qualquer DANFE) colidia com a marca da
  locadora Localiza, saindo com tomador não identificado, valor zerado e o
  prestador hardcoded errado ("LOCALIZA RENT A CAR S/A"). Detecção
  ESTRUTURAL (não gated a nenhum emitente — decisão do usuário, pois notas
  de compra vêm de fornecedores variados), checada no topo de
  `_detect_layout`/`_detect_layout_page`: exige "DANFE" + "Documento
  Auxiliar da Nota Fiscal Eletrônica" + "0-ENTRADA"/"1-SAÍDA", assinatura
  padronizada nacionalmente (SEFAZ/CONFAZ) para todo Modelo 55. Gera XML
  NF-e 4.00 com a chave de acesso e os valores de ICMS **reais** do
  documento (diferente do `NfeTransformer` legado, que só é usado quando a
  nota-fonte é uma NFS-e de serviço e calcula uma chave/zera ICMS como
  *workaround*) — `src/main.py` escolhe o transformer certo automaticamente
  pelo tipo do objeto extraído, sob a mesma opção "NF-e (DANFE Estadual -
  Modelo 55)" da GUI. Suíte 229→**231 verdes**; teste novo
  `test_danfe_produto_layout.py`.

- **Retenções federais no Portal Nacional (`danfse_nacional`)** — extração de
  IRRF, INSS ("Contribuição Previdenciária - Retida") e um novo campo
  `Valores.valor_contribuicoes_sociais_retidas` (valor COMBINADO de
  PIS+COFINS+CSLL, rótulo "Contribuições Sociais - Retidas", sem abertura
  individual — soma para `OutrasRetencoes` no XML por não haver tag ABRASF
  própria). Nenhum dos três era extraído antes, mesmo com valor real na nota
  (achado a partir de um pedido do usuário pra analisar viabilidade de
  extrair PIS/COFINS/CSLL/Contribuições Sociais/INSS/ISS/IRRF Retidos em
  todo o conversor). Extração por adjacência ESTRITA rótulo→valor — em
  notas onde o pdfminer despeja os rótulos desta seção juntos sem os
  valores aparecerem no texto, os campos ficam em 0,00 em vez de atribuir
  errado (regressão coberta por teste). Não confundir com "PIS - Débito
  Apuração Própria"/"COFINS - Débito Apuração Própria" (débito próprio do
  prestador, não retenção — permanece não extraído). Suíte 231→**234
  verdes**; teste novo `test_danfse_nacional_retencoes_federais.py`.

- Novo layout **BIO CONTROL DESINSETIZADORA** (`biocontrol_dedetizadora`) —
  BIO CONTROL DESINSETIZADORA LTDA (CNPJ 04.811.846/0001-62, Lauro de
  Freitas/BA) → BONI TRANSPORTES, LOGISTICA E COMERCIO LTDA, nota real nº
  202600000036345, R$ 5.200,00 (dedetização/controle de pragas urbanas). 3º
  sistema diferente para o MESMO município (ao lado da Prefeitura oficial
  `lauro_de_freitas_ba` e da plataforma eNotas Gateway `password_enotas`),
  template próprio "DEMONSTRATIVO DA NOTA FISCAL DE SERVIÇO" — antes caía
  inteira em `LAYOUT_GENERICO` (0 notas). Detecção pelo CNPJ/razão social do
  emissor específico. Entidades prestador/tomador extraídas DINAMICAMENTE
  (ao contrário do padrão "prestador fixo" de outras faturas de locação),
  pois o bloco sai limpo o bastante em zoom 3x padrão. Um recorte dedicado
  em zoom 8x (`_ocr_recut_biocontrol`) recupera 2 grades densas que a
  leitura de página inteira embaralha: a linha "Tributação de Serviços"
  (Código LC 116 "7.13" sai corrompido como "743") e a dupla "Tributos
  Federais"/"Impostos sobre serviços ISSQN" (PIS/COFINS/IR saem com os
  valores trocados entre si; Alíquota/Valor ISS somem por completo) —
  validado contra o render real da página, não só o texto OCR. Item LC116
  "7.13" (dedetização/desinsetização/controle de pragas urbanas), confirmado
  tanto pelo recorte quanto pela discriminação real da nota. Suíte
  234→**236 verdes**; teste novo `test_biocontrol_layout.py`.

### Corrigido

- Salvador/BA (`salvador_ba`): prestador saindo com o CNPJ do TOMADOR (notas
  reais nº 2150/2169, INSTITUIÇÃO ASSISTENCIAL BENEFICENTE CONCEIÇÃO MACEDO →
  BONI TRANSPORTES, reportado pelo usuário) — o recut dedicado de CNPJ com
  dígito errado (`_ocr_recut_cnpj_invalido_salvador`) já lia o dígito certo do
  prestador, mas exigia ponto literal como separador e o zoom alto às vezes
  recupera espaço no lugar; regex sem match caía no `None`, e o fallback
  genérico ("1º CNPJ válido do documento") pegava o do tomador. Corrigido para
  tolerar espaço/tab OU ponto nesse separador, reformatando com pontuação
  canônica antes de devolver. Achados colaterais na mesma nota (2169):
  Código de Verificação saindo como a palavra `"PRESTADOR"` (rótulo sem valor
  legível no meio, capturado como se fosse o código — mesmo recorte de
  cabeçalho ganhou tentativas adicionais de zoom/PSM/altura, agora exigindo um
  candidato plausível antes de aceitar); e CNPJ/razão social/endereço do
  TOMADOR corrompidos (CNPJ com formatação válida mas dígito errado, sem
  disparar o recut porque o gatilho só olhava a formatação — passou a validar
  também o checksum, e o recut de tomador tenta múltiplos zooms em sequência).
  Suíte 236→**241 verdes**; teste novo
  `test_salvador_codigo_verificacao_e_tomador_2169.py`.

- `parse_multiple`: um bloco de PREÂMBULO (canhoto/recibo do destinatário)
  antes da 1ª nota real de um PDF, separado por uma linha divisória longa
  (200+ hifens), virava uma "nota" fantasma isolada (nº `00000000`, razão
  social = o próprio texto do canhoto) quando o bloco seguinte (a nota real)
  forçava o flush do que já estava acumulado — achado real ao criar o
  layout São José/SC (nota nº 348301, canhoto "Identificação e assinatura...
  do recebedor" antes do conteúdo da nota). Corrigido de forma GENÉRICA (não
  gated a nenhum layout): um bloco sem NENHUM sinal de nota (CNPJ/CPF,
  rótulo de entidade, "Nota"/"NFS") é descartado quando `current_invoice`
  ainda está vazio (nenhuma nota iniciada) — restrito a esse caso para não
  afetar páginas de CONTINUAÇÃO de uma nota já iniciada (ex.: 2ª página do
  Monte Santo). Zero regressão na suíte completa.

- 2 funções de extração de entidade (uma do NFCom Salvador, duas do São
  José/SC) chamavam `IBGEResolver.extract_and_validate(municipio, uf)` sem
  passar `city_hint=municipio` — o lookup direto por nome nunca era
  acionado, e o código caía silenciosamente no fallback de CAPITAL do
  estado (São José/SC → Florianópolis `4205407`, em vez de São José
  `4216602`). O caso do NFCom Salvador "funcionava por coincidência"
  (Salvador é a capital da Bahia). Corrigido nos 3 call sites; **não
  auditado** nos demais layouts que possam compartilhar essa omissão.

- **Atualização automática do app (GUI) via GitHub Releases**
  (`src/version.py` + `src/utils/auto_updater.py`): checagem automática
  ao abrir + botão manual "Verificar atualizações", com download e
  substituição automática do `nfse_converter_gui.exe` em execução
  (decisão do usuário: não apenas notificar/linkar). Consulta
  `GET /repos/.../releases/latest` (só enxerga Releases PUBLICADOS, não
  tags soltas — novo passo manual do processo de release, documentado em
  "Processo de Release" no `DOCUMENTACAO_CONVERSAO.md`); compara SemVer
  contra `APP_VERSION`; baixa o asset `.exe` do Release com barra de
  progresso; a troca do arquivo travado pelo Windows é feita por um
  `.bat` auxiliar desanexado que aguarda o PID atual encerrar, move o
  novo `.exe` por cima do antigo e relança o app. Pede confirmação do
  usuário antes de aplicar (diálogo "Atualizar agora" / "Depois") — a
  checagem é automática, a substituição em si não é silenciosa. Sem
  Release publicado, sem rede, ou rodando via código-fonte (não `.exe`),
  a checagem falha silenciosamente (retorna `None`), sem popup de erro.
  Suíte 242→**256 verdes**; teste novo `test_auto_updater.py`.

### Corrigido

- São Paulo/SP escaneado (`sao_paulo_sp_scan`): `Numero` saindo com dígitos
  da data/hora de emissão em vez do número real da nota (nota real nº
  08336055, PLUXEE BENEFÍCIOS BRASIL S.A. → PH GESTÃO E CONSULTORIA, pág.23
  do lote Guarajuba 07/2026) — o valor do número saía com uma aspa espúria
  colada na frente (`"08336055`, ruído de borda de célula do OCR), e o
  gatilho do recorte dedicado de cabeçalho (`_ocr_header_box_sao_paulo`)
  exigia o token inteiro ser dígito puro (`re.fullmatch`), descartando esse
  candidato mesmo com 8 dígitos legíveis; caía então no recorte fixo por
  percentual (calibrado numa nota de cabeçalho mais baixo), que nesta nota
  acerta a caixa "Data e Hora de Emissão" e devolve `16072026203205` em vez
  de `08336055`. Corrigido trocando `fullmatch` por `search` no gatilho —
  aceita dígitos com ruído colado antes/depois, mantendo a exigência de 6+
  dígitos CONSECUTIVOS (datas/CEPs/Inscrição Municipal, com separador a cada
  2-5 dígitos, continuam não casando). Suíte 224→**225 verdes**.
- Salvador/BA (`salvador_ba`): Código de Verificação, CNPJ/razão social do
  PRESTADOR e grade de valores saindo todos ERRADOS/zerados numa nota real
  (nº 00039029, A LIMPCANO DESENTUPIMENTO E SUCÇÃO DE FOSSAS LTDA - EPP →
  SOHO RESTAURANTE LTDA) — causa nova para este layout: uma marca d'água
  diagonal (carimbo "...ISS DEVERÁ SER RETIDO...") cobrindo a página
  INTEIRA, cujo padrão de pontos (halftone) degrada o OCR onde cruza texto
  impresso. Isso corrompia o rótulo "PRESTADOR DE SERVIÇOS" (lido "PRESPAD
  RVIÇOS", irreconhecível), fazendo o bloco genérico da entidade virar o
  documento INTEIRO e o CNPJ/razão do TOMADOR (o único par bem formado que
  sobrava) vazar para as DUAS entidades; e corrompia os rótulos da grade de
  valores ("Valor do ISS" → "Ne alét.do ISS"), zerando `valor_servicos` E
  `base_calculo` juntos (o fallback antigo herdava `base = val_serv`).
  Corrigido com 4 recortes dedicados, gateados por evidência do defeito
  (nenhum rótulo de prestador reconhecível antes de "TOMADOR" / linha
  "VALOR TOTAL DA NOTA" ilegível): Código de Verificação e bloco do
  Prestador via recorte + despeculagem (filtro de mediana) em zoom alto;
  grade de valores via recorte por CÉLULA individual (Dedução/Base/
  Alíquota recuperados; o Valor do ISS continua ilegível mesmo isolado —
  DERIVADO matematicamente de Base × Alíquota; Crédito/Outras Retenções
  fixados em 0,00, sempre zero nesta nota e irrecuperáveis via OCR em
  qualquer zoom/kernel testado).
- DANFSe Nacional (`danfse_nacional`): razão social do prestador saindo
  ERRADA — o próprio endereço dele (ex.: `RUA ITAIPU, S/N, MONTE GORDO
  (MONTE GORDO) Camaçari - BA 42840-178`) em vez do nome (nota real nº 4,
  Camaçari/BA, prestador MEI ANA PAULA RIBEIRO DA SILVA) — quando a linha
  "Nome / Nome Empresarial" vem colada com o e-mail na mesma linha da
  grade e o OCR corrompe o "@" em `" (O"` (espaço + parênteses + O) em
  vez das corrupções já toleradas (`Q`/`O`/`.` colados sem espaço), a
  limpeza de e-mail não reconhecia o padrão, descartava a linha inteira
  como inválida, e o fallback linha-a-linha acabava aceitando a linha de
  Endereço/Município/CEP (sem rótulo de ruído reconhecido) como razão
  social. Corrigido tolerando `"(O"`/`"QO"` (com espaço opcional antes)
  como forma corrompida do "@".
- NF-e de Serviço de Comunicação (`telecom_comunicacao`): 6 bugs achados
  num review de uma nota real (nº 31696, F&F Comunicações/Grupo F&F →
  Boutique Guarajuba/PH Gestão, R$558,40) — layout que não tinha teste
  nenhum até então. (1) Colisão de detecção com `ff_locacao` (mesmo
  emissor, documentos diferentes) — o título da fatura de comunicação
  agora tem prioridade sobre o CNPJ do emissor. (2) CNPJ do prestador saía
  igual ao do tomador quando o OCR degradava o separador do CNPJ da F&F
  — corrigido tolerando o ruído e excluindo candidatos já rotulados
  "CNPJ/CPF" (sempre do tomador). (3) Leitura padrão perdia a coluna
  direita inteira do cabeçalho (número, data de emissão, referência,
  vencimento, total) — número caía num fallback genérico perigoso que
  pescava o número da Resolução ANATEL citada no rodapé; novo recorte
  dedicado em zoom 6x resolve. (4) Total a pagar com rótulo colado sem
  vírgula decimal causaria valor 100x maior — corrigido. (5) Endereço do
  tomador vazava o do prestador quando o tomador não tinha "Rua/Av" no
  próprio endereço; município também vazava o bloco anterior colado por
  um regex que casava quebra de linha. (6) Nomes do prestador/tomador
  saíam corrompidos pelo recorte de zoom alto (ruído de colunas fundidas)
  quando esse recorte é prependado ao texto. Suíte 211→218 verdes; teste
  novo `test_telecom_comunicacao_ff_layout.py`.
- Camaçari/BA escaneado (`camacari_ba_scan_v3`): número da nota saía
  zerado (`00000000`, nota real nº 285, pág.20 do lote PH Gestão 07/2026,
  AVANÇO GESTÃO E ADMINISTRAÇÃO LTDA → PH GESTÃO) — uma das 3 tentativas
  de recorte do cabeçalho degrada o rótulo "Número da Nota" para "nero da
  Nota" (perde o "úm" inteiro), e a âncora antiga não tolerava essa
  variante; a ocorrência com o rótulo limpo não tem número por perto.
  Corrigido tolerando "nero da Nota", exigindo que o número colado também
  apareça como linha isolada em outro bloco do texto antes de aceitá-lo
  (evita repetir o erro já catalogado na nota nº 20335/PADUA, onde o
  número colado ao rótulo degradado era simplesmente errado).
- Monte Santo/BA: serviço de construção civil (item 07.02) prestado fora da
  sede do prestador não estava incidindo o ISSQN no município correto da
  obra (LC 116/2003 art. 3º III) — a nota traz "Local do Serviço: Fora do
  Município" e a cidade da obra em texto livre ("OBRA: ..., <CIDADE>/<UF>"),
  extraível de forma confiável pela âncora de fim de linha. `Nfse.
  municipio_incidencia_override` agora também cobre esse layout (mesmo
  padrão já usado no Guarulhos/SP).
- São Paulo/SP escaneado (`sao_paulo_sp_scan`): número da nota saindo
  ERRADO (ex.: `13`/`7668` em vez de `05114339`/`05210826`) quando o
  próprio rótulo "Número" sai corrompido em fragmentos no zoom de
  localização (3x) e o recorte dedicado cai no fallback fixo por
  percentual, que pode acertar a caixa errada ("Código de Verificação").
  Corrigido buscando o valor direto pela própria assinatura (token
  puramente numérico, ≥6 dígitos, no topo da região) quando o rótulo não
  é localizado. Corrigido também o código de verificação saindo como lixo
  concatenado (ex.: `20260724U32223020000118RPSN`) quando o OCR insere um
  espaço espúrio dentro do próprio código (`"1 LU3-QLER"` em vez de
  `"1LU3-QLER"`), quebrando o regex rígido sem tolerância a espaço.
- PASSWORD/eNotas Gateway: layout passa a cobrir um 3º emitente na mesma
  plataforma (TÉSSERA HOSPITALITY LTDA, Lauro de Freitas/BA) — a 1ª nota
  ESCANEADA desta plataforma (PASSWORD/INFOMIX, já validados, são
  digitais). O scan funde a grade "DADOS DO TOMADOR" numa única linha por
  rótulo (ilegível pela extração dedicada) e degrada a coluna direita do
  cabeçalho; recortes dinâmicos em zoom mais alto recuperam número/
  competência/código/data/CNPJ/IM/tomador. Corrigido também um bug de
  propagação em lote: os recortes ficavam guardados em atributos ESCALARES
  de instância, resetados no início de toda chamada a `_ocr_page` — em lotes
  de várias páginas, o valor da nota TÉSSERA era apagado pelo processamento
  das páginas seguintes antes de `parse_multiple()` conseguir propagá-lo
  para o extrator dedicado (`sub_ext`) que de fato monta a Entidade,
  cruzando CNPJ/razão social do prestador com o tomador. Passaram a ser
  dicionários indexados por página. Também corrigidos: CNPJ do tomador com
  separador final "." em vez de "-"; razão social do prestador priorizando
  a linha com sufixo social (LTDA/S.A./...) sobre a heurística posicional
  (que caía num fragmento solto do logo); Base de Cálculo reconstituída
  (Serviços - Deduções) quando a fusão de coluna do OCR elimina esse
  rótulo por completo.
- Salvador/BA escaneado: tomador extraído com o CNPJ ERRADO (nota real
  nº 00011629, SAFE - SEGURANÇA ELETRÔNICA LTDA → MANUELLA CARVALHO
  MARTINS BAHIA) — o gatilho do recut `_ocr_tomador_salvador` era mais
  estrito que a extração real (não tolerava o espaço antes do hífen que a
  extração já tolera), disparando o recut sem necessidade; o recut lia o
  CNPJ errado e, por ser prependado, criava um 2º bloco "TOMADOR DE
  SERVIÇOS" que a extração genérica encontrava primeiro, caindo no
  sentinela. Corrigido alinhando a tolerância do gatilho à da extração.
  Na mesma nota, `CodigoVerificacao` saía `ALVADORETNEWBUQ` (fusão com o
  fim de "Salvador" do título) em vez de `ETNEWBUQ` — o guard antigo
  exigia um dígito no candidato, mas o código real pode ser só letras;
  corrigido pulando o prefixo "(S)ALVADOR" explicitamente na regex.
- PASSWORD/eNotas Gateway: layout passa a cobrir um 2º emitente na mesma
  plataforma (INFOMIX Soluções em Tecnologia LTDA, Lauro de Freitas/BA,
  antes caía em "layout não reconhecido", 0 XML gerado) — código do serviço
  com nº de dígitos variável no "código interno" do gateway saía truncado, e
  a razão social do tomador podia sair como o rótulo "E-MAIL" quando os
  rótulos "NOME/RAZÃO SOCIAL" e "E-MAIL" vêm despejados juntos antes dos 2
  valores.
- Salvador/BA: 4 bugs achados num review de uma nota real (nº 00006508) —
  CNPJ do prestador/tomador com checksum inválido contaminava a Inscrição
  Municipal com os próprios dígitos rejeitados; o número do endereço do
  prestador saía colado ao complemento/bairro/cidade no campo `Numero`;
  a grade Base de Cálculo/Alíquota/Valor do ISS saía zerada/errada quando o
  rótulo "Alíquota (%)" vinha com um dígito de ruído de OCR embutido
  (`"Alíquota (9%)"`); o código de serviço caía no fallback genérico
  `03115` quando o OCR lia "ltem" em vez de "Item"; e "SN" (sem número)
  colado ao logradouro sem vírgula ficava sem separar do lixo do split
  genérico. Nenhum exige layout novo — correções aditivas no
  `LAYOUT_SALVADOR` existente.
- Salvador/BA: CNPJ do prestador/tomador com dígito errado NO MEIO do
  número (não no dígito verificador) confirmava sentinela na importação
  real do usuário (Domínio Sistemas rejeitava a nota inteira). Novo
  recorte dedicado (`_ocr_recut_cnpj_invalido_salvador`, gated por
  checksum reprovado) reprocessa em zoom alto só a linha de valores do
  CNPJ e recupera o dígito certo quando possível, validando o resultado
  antes de aceitar — nunca propaga um valor não validado.
- Lauro de Freitas/BA: `MunicipioIncidencia`/`Servico.CodigoMunicipio`
  saíam com o município do prestador mesmo quando a nota indicava
  explicitamente "LOCAL DA PRESTAÇÃO DO(S) SERVIÇO(S)" em outra cidade e
  "Tributado fora do Município de Lauro de Freitas" (obra de construção
  civil, LC 116/2003 art. 3º III) — o override de incidência já existia
  mas só cobria o layout Guarulhos/SP. Estendido para também cobrir Lauro
  de Freitas/BA, sem criar layout novo.
- São Paulo/SP escaneado (`sao_paulo_sp_scan`): número da nota saía errado
  (`392` em vez de `05121900`, nota real FLASH TECNOLOGIA) quando o
  cabeçalho acima da caixa "Número da Nota" tinha altura diferente da nota
  usada para calibrar o recorte fixo por percentual — o recorte caía na
  caixa vizinha ("Código de Verificação") e a whitelist de dígitos
  "inventava" um número a partir das letras. `_ocr_header_box_sao_paulo`
  agora localiza o rótulo "Número da Nota" dinamicamente antes de recortar,
  imune à altura variável do cabeçalho (recorte fixo antigo mantido como
  fallback).
- Extração genérica de Data de Emissão (compartilhada por ~30 layouts):
  quando o texto tem mais de um rótulo de data batendo, a hora saía zerada
  (`00:00:00`) se um rótulo sem hora ("Emitido em") aparecesse antes de um
  rótulo com hora completa ("Data e Hora de Emissão") na lista de
  prioridade — mesma nota FLASH TECNOLOGIA (o aviso de substituição do RPS
  bate em "Emitido em" sem hora). Agora prefere o primeiro candidato COM
  hora entre os que casaram, em vez do primeiro da lista.
- São Paulo/SP escaneado (`sao_paulo_sp_scan`): uma dobra física do papel
  cobrindo "PREFEITURA DO" no título (nota real nº 00028202, VALESTRA
  NEGOCIOS E INVESTIMENTOS LTDA → MASSA ALIMENTACAO E SERVICOS S/A) fazia a
  nota inteira cair em `generico` (0 notas extraídas) — prefixo tornado
  opcional na detecção de layout. A mesma dobra derrubava mais 6 campos na
  mesma nota, todos corrigidos: Data/Hora de Emissão e Código de Verificação
  recuperados por recorte dedicado (o rótulo do código some do OCR,
  recuperado por busca da FORMA do próprio valor); endereço do prestador com
  3 segmentos separados por " - " (bairro nem sempre é o último); "Município"
  sem acento quebrava o casamento de rótulo (ambos prestador e tomador
  caíam no fallback de capital, Salvador/BA); e-mail do tomador com "@" lido
  como "Q"; razão social do tomador com ";" (em vez de ":") vazando no
  início do valor (fix genérico, não específico de São Paulo); e as duas
  grades de valores (retenções federais + Deduções/Alíquota/ISS)
  totalmente ilegíveis em zoom padrão, recuperadas por recorte dedicado —
  Base de Cálculo e Valor Líquido passam a ser DERIVADOS matematicamente
  em vez de re-OCRizados, por não serem confiáveis em nenhum zoom testado.
  Suíte 236→**237 verdes**; teste novo
  `test_sao_paulo2_valestra_fold_defect.py`.
- São Paulo/SP escaneado (`sao_paulo_sp_scan`, mesma nota Valestra acima):
  "Código do Serviço" (item de tributação municipal) desaparecia por
  completo do OCR — nem rótulo nem valor —, caindo no fallback genérico
  `03115` em vez do real `01899` ("Planejamento, coordenação, programação
  ou organização técnica, financeira ou administrativa"), achado ao
  reconferir o XML campo a campo contra a imagem depois do fix acima.
  Recuperado com uma 3ª captura no mesmo recorte dedicado, na mesma
  região/zoom do IRRF mas com PSM 4 em vez de PSM 6 (mesma imagem pode
  precisar de PSM diferente pra sub-regiões adjacentes). Teste existente
  ampliado; suíte permanece **242 verdes**.
- São Paulo/SP (digital e escaneado, `sao_paulo_sp`/`sao_paulo_sp_scan`,
  mesma nota Valestra acima): intermediário FANTASMA — bloco
  `<Intermediario>` emitido no XML com CNPJ sentinela
  `00000000000100` e `RazaoSocial=": —"` mesmo quando a nota não tem
  intermediário de verdade (`CPF/CNPJ: —` / `Nome/Razão Social: —`, tudo
  vazio). O guard existente contra esse fantasma (achado 2026-07-31, nota
  UNIMED CNU) só reconhecia o placeholder `"----"` (2+ hífens ASCII); esta
  nota usa um único travessão "—" (em dash, U+2014) em vez de hífen —
  corrigido tolerando também 1+ caractere da família en/em dash
  (U+2010-U+2015, nunca usada num CNPJ real), mantendo a exigência de 2+
  hifens ASCII (para não colidir com o hífen único de um CNPJ real bem
  formado, ex. `12.345.678/0001-01`). Teste existente ampliado; suíte
  permanece **242 verdes**.
- DANFSe Nacional (`danfse_nacional`), plataforma **WebISS** (achado real,
  Prefeitura Municipal de Aracaju/SE, nota nº 2026000000014, LY5T-1DG5,
  reportado pelo usuário): `Valor dos Serviços`/`Valor Líquido`/`Base de
  Cálculo ISS`/`Alíquota ISS` saíam todos ZERADOS (R$ 4.000,00 reais) — esta
  plataforma usa vocabulário próprio ("Valor **dos** Serviços", plural, em
  vez de "Valor do Serviço") e imprime o número da célula da grade SEM o
  token "R$" (só o rótulo tem o sufixo "(R$)"), formato que os padrões
  existentes (que exigem "R$ n,nn" logo após o rótulo) nunca casavam.
  Estendido de forma ADITIVA (fallback só ativa quando o padrão original
  não casou, sem risco às demais cidades que já usam este layout
  compartilhado): reconhece o rótulo no plural, aceita número sem "R$", e
  passa a extrair também Alíquota ISS e as Retenções Federais individuais
  (PIS/COFINS/INSS/IR/CSLL) desta plataforma. A própria nota imprime
  `"*****"` (mascarado) em Base de Cálculo ISS/ISS/ISS Retido (regime
  ME/EPP do Simples Nacional) — mantidos em 0,00 (nunca fabricar um valor
  sem lastro no documento), sinalizado por um aviso dedicado em
  `Nfse.avisos`. Suíte 256→**257 verdes**; teste novo
  `test_danfse_nacional_aracaju_webiss.py`.

### Corrigido

- **Brasília/DF (`brasilia_df`): endereço/município/UF/e-mail/telefone do
  TOMADOR (e do prestador) saindo corrompidos numa nota real** (nº 44, AFG
  DIGITAL COMUNICACAO E PRODUCAO LTDA → ELOS ESTUDIO E SERVICOS LTDA,
  R$ 4.950,00), reportado pelo usuário. Três bugs no extrator GENÉRICO de
  entidade (compartilhado por ~30 layouts, não específicos do Brasília):
  (1) a captura de Endereço não parava antes do rótulo "Cidade:" (só
  reconhecia "Município"/"Municipio"), engolindo a linha inteira seguinte
  dentro do campo Número (`"0 Cidade: Brasília Estado/Prov./Reg.: Distrito
  Federal País: Brasil"`); (2) o casamento de Município/UF também não
  reconhecia o rótulo "Cidade:" isolado (plataforma "ISS.NET - Sistema
  Nota Control"), caindo no fallback de capital (Salvador/BA); (3) mesmo
  reconhecendo o rótulo, "Estado/Prov./Reg.:" imprime o nome COMPLETO da
  UF ("Distrito Federal"), não a sigla de 2 letras que a regex exigia —
  novo dicionário `_UF_POR_NOME_ESTADO` resolve o nome completo. Achados
  colaterais (bugs pré-existentes e independentes, não gated a este
  layout): e-mail/telefone saíam sempre `None` porque a regex genérica não
  tolerava o ":" impresso entre rótulo e valor, e a regex de Telefone
  tinha um `{8,20}` com chave simples dentro de uma f-string — o Python
  interpreta isso como a tupla `(8, 20)` e insere o literal `"(8, 20)"` na
  regex em vez do quantificador, quebrando o casamento sem erro de
  sintaxe. Removidos também 3 `print()` de debug esquecidos na extração do
  Código de Autenticidade do Brasília. Suíte 268→**269 verdes**; teste
  novo em `test_brasilia_layout.py`.

- **Salvador/BA (`salvador_ba`) e Lauro de Freitas/BA (`lauro_de_freitas_ba`,
  variante NFTS): 2 bugs numa nota real de 2 páginas** (nº 2419, LUNITECK
  SOLUÇÕES E DESENVOLVIMENTO EM TECNOLOGIA LTDA ME → BONI TRANSPORTES,
  LOGÍSTICA E COMÉRCIO LTDA; pág.1 = NFS-e emitida pela Prefeitura de
  Salvador/prestador, pág.2 = NFTS emitida pela Prefeitura de Lauro de
  Freitas/tomador), reportado pelo usuário. (1) Salvador: `CodigoVerificacao`
  saindo como a palavra **"PREFEITURA"** (do título "PREFEITURA MUNICIPAL DO
  SALVADOR") numa digitalização degradada onde o valor real nunca sai
  legível em NENHUM ponto do texto, nem mesmo com os 4 recuts dedicados já
  existentes para esse layout — o rótulo "Verificação:" saía legível, mas o
  `\s*` até o candidato atravessava várias linhas de ruído e capturava o
  título do documento; mesmo bug de "ALVADOR"/"PRESTADOR"/"TOMADOR" (já
  rejeitados), agora também rejeitando "PREFEITURA"/"MUNICIPAL"/
  "SECRETARIA"/"FAZENDA" — cai honestamente no sentinela `XXXX-XXXX` quando
  nada mais sobra. Os demais campos desta página (Número, Razão Social,
  CNPJ) permanecem não recuperáveis nesta digitalização específica: os
  próprios rótulos de seção saem irreconhecíveis no OCR, e a nota da pág.2
  (mesma transação, mesmo CNPJ/valor) já cobre os dados corretos. (2) Lauro
  de Freitas/NFTS: grade de valores (Base de Cálculo/Alíquota/Valor do ISS)
  saindo ZERADA numa variante onde a grade sai PARTIDA em 3 pedaços não-
  contíguos, em vez dos 5 rótulos+5 valores contíguos já cobertos — as 2
  regras antigas nunca casavam, perdendo dados presentes e legíveis no
  texto; e `Município`/`UF` do tomador vazando "UF; BA" inteiro para dentro
  do campo Município quando o OCR lê "UF;" (ponto-e-vírgula) em vez de
  "UF:" — corrigido tolerando `[:;]` nos 4 pontos onde o rótulo "UF" é
  usado. Suíte 269→**271 verdes**; testes novos
  `test_salvador_codigo_verificacao_nao_confunde_titulo.py` e
  `test_lauro_de_freitas_nfts_grade_partida.py`.

- **Mesmo par Salvador/Lauro de Freitas — 3 bugs adicionais achados numa 2ª
  nota da mesma dupla** (nº 2418, mesmo par LUNITECK → BONI TRANSPORTES),
  reportado pelo usuário como "continua extraindo com erro". (1) Salvador: a
  lista de exclusão do `CodigoVerificacao` por igualdade EXATA (`ALVADOR`/
  `PRESTADOR`/`TOMADOR`/`PREFEITURA`/... ) não pega variantes do OCR que
  corrompem só uma BORDA da palavra (aqui, "PRESTADOR" saiu "ERESTADOR") —
  trocada por uma comparação de sufixo/prefixo de 6+ caracteres contra os
  mesmos rótulos, e o candidato rejeitado agora encerra direto no sentinela
  `XXXX-XXXX` em vez de cair no fallback genérico ainda mais permissivo
  (que produzia um valor pior, "ERESTADORDESERVI", ao atravessar a palavra
  seguinte). (2) Lauro de Freitas/NFTS: CNPJ do prestador saindo
  `00000000000000` — o separador do CNPJ veio com VÍRGULA no lugar do 1º
  PONTO ("07,295.620/0001-44"), e o regex exigia ponto literal nos 2
  separadores; agora tolera `[.,]` nos dois. (3) Discriminação engolindo
  rótulos vazados do bloco do PRESTADOR ("Inscrição Estadual"/"Email:")
  que, nesta digitalização, saem fisicamente DESLOCADOS para DEPOIS do
  cabeçalho "DISCRIMINAÇÃO DOS SERVIÇOS" — a captura agora também para
  nesses 2 rótulos, além do já existente "VALOR TOTAL DA NOTA". Suíte
  271→**273 verdes**; testes novos
  `test_salvador_codigo_verificacao_rotulo_garblado.py` e
  `test_lauro_de_freitas_cnpj_virgula_e_discriminacao_vazada.py`.

- **Mesma nota 2418 — `Numero` e `RazaoSocial` do tomador (Salvador) pedidos
  explicitamente pelo usuário após os fixes acima ainda não cobrirem esses 2
  campos.** `_extrair_numero`: rótulo "Número da Nota" saindo "Número da
  Nóta" (acento espúrio no "o") não era reconhecido — regex ampliado pra
  `N[oó]ta`. `RazaoSocial` do tomador saindo `"BE SERVIÇOS"` (resto do
  próprio cabeçalho de seção "TOMADOR **DE** SERVIÇOS" garblado só na parte
  final, "DE"→"BE" — o rótulo reconhecido consumia só a palavra "Tomador",
  deixando o resto sobrar como se fosse a 1ª linha de conteúdo real): função
  compartilhada `is_valid_razao` (usada por ~30 layouts) ganhou 2 rejeições
  novas — linha inteira "`<sigla curta> SERVIÇOS`" (nenhuma razão social
  real é só isso) e linha com "/" sem NENHUMA sequência de 2+ maiúsculas
  seguidas (Title Case puro — o padrão do rótulo "Nome/Razão Social" quando
  ele também garbla, ex. "Norma/Razab Sonia", contra o ALL-CAPS universal
  das razões sociais reais deste corpus; restrito à combinação com "/" pra
  não afetar razões legítimas em Title Case sem "/", como "Sao Pedro
  Construtora Ltda"). CNPJ do tomador nesta página permanece não
  recuperável (dígitos genuinamente ilegíveis no OCR, não um problema de
  formatação/pontuação) — a nota irmã da pág.2 (Lauro de Freitas) já tem o
  CNPJ correto. Suíte 273→**274 verdes**; teste novo
  `test_salvador_numero_e_tomador_rotulo_garblado.py`.

## [1.3.0] - 2026-08-10

### Adicionado

- Novo layout **Monte Santo/BA** — município nunca antes suportado. PDF
  digital construído sobre o padrão nacional da NFS-e, mas com template
  próprio; os rótulos das entidades e os valores da nota vêm em blocos
  separados do texto, e os valores só existem na 2ª página da nota (sem
  cabeçalho/número/CNPJ próprios), exigindo detecção e tratamento
  dedicados de continuação para não serem descartados como lixo.

### Corrigido

- Localiza (fatura de locação): nota de uma filial cujo próprio endereço
  menciona "FEIRA DE SANTANA" caía no layout genérico dessa cidade em vez do
  layout Localiza (colisão de detecção); uma página de continuação (resumo
  de carros) virava nota-fantasma por citar "Localiza Rent a Car S.A." com
  ponto em vez de barra; município do prestador/tomador caía no fallback da
  capital da UF mesmo já cadastrado por nome (faltava `city_hint` em 2
  chamadas ao resolver de IBGE); código do serviço saía como o genérico
  "03115" em vez de "0601" (locação de bens móveis).

42 layouts suportados (41 específicos + genérico de fallback). Suíte: 196
testes passando.

## [1.2.0] - 2026-08-10

### Adicionado

- Novo layout **Camaçari/BA via plataforma SISLOC** ("NFS-e Easy" da Benefix)
  — PDF digital cujo gerador desenha rótulos e valores como blocos de texto
  separados; `pdfminer.extract_text()` padrão despejava tudo concatenado
  num blob único ao final do documento, sem relação com o rótulo. Corrigido
  reconstruindo o texto por coordenada de caractere em vez da ordem de
  leitura padrão.

### Corrigido

- Camaçari/BA (escaneado/OCR): número da nota e CNPJ do prestador saindo
  incorretos em algumas notas (ex.: nº 20335, PADUA COMÉRCIO E REFORMA DE
  PNEUS) — o recorte de cabeçalho podia não recuperar o número corretamente
  em nenhuma das tentativas, e um CNPJ de prestador com dígito trocado
  (checksum inválido) podia acabar herdando o CNPJ do TOMADOR pelo fallback
  genérico. Corrigido via novo layout `LAYOUT_CAMACARI_3`, superset do
  layout escaneado anterior (preservado intocado): número cai no fallback
  do nome do arquivo quando o recorte falha, e um CNPJ de prestador sem
  checksum válido é descartado para o sentinela + aviso em vez de herdar o
  CNPJ de outra entidade do documento.

## [1.1.1] - 2026-08-07

### Corrigido

- DANFSe Nacional: página com uma única nota podia gerar uma **nota-fantasma**
  extra (número "00000000", todos os campos zerados) antes da nota real — o
  split de múltiplas-notas-por-página cortava no próprio título "DANFSe v1.0"
  de abertura da página.
- DANFSe Nacional: em notas cuja grade OCR lê as linhas fora de ordem física,
  o tomador podia sair com o **mesmo CNPJ do prestador** em vez do seu
  próprio, quando o CNPJ do prestador vazava para dentro do bloco de texto do
  tomador.

## [1.1.0] - 2026-08-07

### Adicionado

- Novo layout **Guarulhos/SP** (plataforma Ginfes, escaneada/CamScanner) —
  município nunca antes suportado (nota real caía em "layout não
  reconhecido", 0 XML gerado). Recorte dedicado de OCR isola a coluna
  numérica da grade de valores, ilegível em conjunto com o rótulo.
- `Nfse.municipio_incidencia_override`: campo aditivo (default `None` em
  todos os ~39 layouts existentes) que permite a incidência do ISSQN ir
  para o município da obra, e não o do prestador, em serviços de
  construção civil executados fora da sede do prestador (LC 116/2003 art.
  3º III).

### Corrigido

- DANFSe Nacional: notas cujos campos monetários estruturados usam PONTO
  decimal em vez de vírgula (ex.: plataforma Domínio Sistemas, nota real
  de Criciúma/SC) saíam com Valor dos Serviços, Base de Cálculo, Valor do
  ISS e Valor Líquido todos zerados.

40 layouts suportados (39 específicos + genérico de fallback). Suíte: 187
testes passando.

## [1.0.1] - 2026-07-20

### Adicionado

- CI (GitHub Actions) rodando a suíte de testes em PR/push para `main`.
- Template de Pull Request.

### Corrigido

- OCR não tratava fotos/JPGs rotacionados (180/90/270 graus); páginas
  viravam "layout não reconhecido" e a nota era descartada sem erro.
- Alíquota do ISS (layout Camaçari) podia capturar número da célula errada
  em tabelas embaralhadas pelo OCR, reportando percentual fiscal
  incorreto.
- Trava de "página de lixo" descartava notas reais com número/CNPJ
  ilegíveis mesmo com nome de prestador/tomador legível.
- Aviso "dados não identificados" não disparava para um dos dois
  valores-sentinela de CNPJ usados internamente pelo extrator.

## [1.0.0] - 2026-06-30

### Adicionado

- Primeira versão estável do conversor de NFS-e/NF-e em PDF para XML
  ABRASF 2.01.

[Não lançado]: https://github.com/anderson561/conversordenotasparaxmlabrasf/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/anderson561/conversordenotasparaxmlabrasf/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/anderson561/conversordenotasparaxmlabrasf/compare/v1.1.1...v1.2.0
[1.1.1]: https://github.com/anderson561/conversordenotasparaxmlabrasf/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/anderson561/conversordenotasparaxmlabrasf/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/anderson561/conversordenotasparaxmlabrasf/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/anderson561/conversordenotasparaxmlabrasf/releases/tag/v1.0.0
