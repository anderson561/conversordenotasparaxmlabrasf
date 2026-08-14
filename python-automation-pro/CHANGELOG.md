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
