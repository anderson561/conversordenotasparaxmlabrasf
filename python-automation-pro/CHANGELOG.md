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

### Adicionado

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
