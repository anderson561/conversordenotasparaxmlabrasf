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

- **Novo layout: João Pessoa/PB (`joao_pessoa_pb`)** — página 5 do PDF real `Scan2026-09-23_090227.pdf` (nota nº 1001671, ESPACO A COMERCIO DE MOVEIS LTDA → NAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVIÇOS - EIRELI, R$ 9.864,92) não tinha layout nenhum reconhecido — a conversão da página falhava com `ValueError: Nenhuma nota encontrada nas páginas selecionadas.`.
  - NFS-e **oficial** da Prefeitura de João Pessoa/PB (Secretaria da Receita Municipal, "Nota Fiscal de Serviços Eletrônica NFSe - Prestador"), PDF **escaneado** (OCR). Detectada pela marca exclusiva `Prefeitura Municipal de João Pessoa`.
  - Mesma grade "rótulos numa linha, valores na seguinte, vários campos por linha" do `LAYOUT_CAMPINAS`, inclusive a **mesma grade** "CÁLCULO DO ISSQN" / "VALOR TOTAL" (6 e 5 campos, mesma ordem) — reaproveitada tal e qual em `_extrair_valores` via `self.layout in (LAYOUT_CAMPINAS, LAYOUT_JOAO_PESSOA)`, sem nenhuma adaptação.
  - Extração de PRESTADOR/TOMADOR num parser dedicado (`_extrair_entidade_joao_pessoa`), não reaproveitando o de Campinas, por 3 quirks de OCR próprios desta nota: (1) separador `/` do cabeçalho `CPF / CNPJ / NIF` do prestador saindo como `!`; (2) `@` do e-mail corrompido em `(` + 1 letra maiúscula solta (`escritorio(Despacoamoveis.com.br` → `escritorio@espacoamoveis.com.br`), separado do local-part por CAIXA (razão social sempre maiúscula, e-mail a única parte minúscula da linha) em vez de posição de token; (3) linha de valor "Endereço/Município/CEP" quebrada em 2 linhas físicas.
  - Item da LC116 (`14.06`) lido como `1408"` (sem ponto decimal) na leitura de página inteira (zoom 3x) — recuperado por recorte dedicado `_ocr_recut_item_lc116_joao_pessoa` (zoom 6x, PSM linha única, rótulo "Serviço" localizado dinamicamente via `image_to_data`); zoom 10x reintroduz o mesmo erro, então não é um caso de "zoom mais alto sempre ajuda". Sem ponto decimal, o regex de extração nunca casa o valor corrompido — sem o recorte o campo fica vazio, nunca errado.
  - `KNOWN_CITIES` ganhou `JOAO PESSOA`/`JOÃO PESSOA` (IBGE `2507507`, confirmado em 2 fontes oficiais do IBGE); já era o fallback de capital de "PB" em `DEFAULT_CODES_BY_UF`, mas sem entrada própria a separação bairro/município do endereço do prestador (`TAMBAUZINHO JOAO PESSOA` → bairro + cidade) nunca reconhecia a cidade.
  - Suíte: 763 → **766 testes**; 3 novos em `tests/test_joao_pessoa_layout_espaco_a_moveis.py`.
  - Contagem de layouts: **61 → 62** (61 específicos + genérico de fallback).
- **Novo layout: Ribeirão Preto/SP (`ribeirao_preto_sp`)** — pedido explícito do usuário ("criar um plano de ação, para extração do número da nota fiscal, layout ribeirao preto, criar caso não existe. O número correto da nota é: 469"), a partir do arquivo real `NOTAS_DE_PRESTACAO_DE_SERVICOS_UNIAO_PARTICIPACOES_MES_DE_AGOSTO_DE_2026.pdf` (nota nº 469, Paschoalin Sociedade Individual de Advocacia → UNIÃO PARTICIPAÇÕES LTDA, R$ 4.500,00), reportada com número saindo sentinela `00000000`.
  - **Causa-raiz na DETECÇÃO, não na extração**: sem layout próprio, a nota caía no fallback bare `if re.search('FEIRA DE SANTANA', t): return LAYOUT_FEIRA` — mesma família "marca da CONTRAPARTE sequestra a nota" já vista em `LAYOUT_SIMOES_FILHO` — porque o TOMADOR é de Feira de Santana/BA, mesmo a nota sendo emitida pela Prefeitura de Ribeirão Preto/SP. Checado ANTES desse fallback pelo marcador próprio `PREFEITURA DE RIBEIRÃO PRETO`.
  - Sob o layout errado saíam sentinela/errados: Número, Código de Verificação, horário da Data de Emissão, Código de Município de AMBAS as entidades (default Salvador/BA — nem Ribeirão Preto nem Feira de Santana estavam em `KNOWN_CITIES`) e Alíquota/Valor do ISS (zerados apesar de a nota imprimir "R$ 90,00 (2,00%)").
  - Caixa "Número / Data de emissão / Código de verificação" recuperada por recorte dedicado (`_ocr_header_box_ribeirao_preto`); os regexes de extração toleram um caractere de ruído solto que o recorte real introduz colado aos rótulos (não capturado por um mock sintético "limpo" — só apareceu ao regenerar o XML contra o PDF real).
  - `KNOWN_CITIES` ganhou `RIBEIRAO PRETO` (IBGE `3543402`); `FEIRA DE SANTANA` já existia.
  - Suíte: 744 → **747 testes**; 3 novos em `tests/test_ribeirao_preto_layout_uniao_participacoes.py`.
  - Contagem de layouts: **59 → 60** (59 específicos + genérico de fallback).
- **Dois layouts novos, criados para corrigir o tomador das páginas 1 e 9 do lote "STAUMMAQ - SCAN 2.pdf"** (pedido: "corrigir a extração correta do tomador do serviço, que em ambos os casos, é a Staummaq Serviços [...] focar somente nesse problema"). As duas páginas devolviam `Tomador Não Identificado` com CNPJ sentinela.
  - **Causa-raiz única, e não estava na extração e sim na DETECÇÃO.** Os dois detectores terminam com um fallback solto `if re.search(r'Sim[oõ]es Filho', t) → LAYOUT_SIMOES_FILHO`. A **STAUMMAQ, tomadora de todas as notas destes lotes, fica em Simões Filho/BA** — então o nome da cidade aparece em qualquer nota do lote, venha de qualquer emitente. As págs. 2–8 escapam porque casam antes o marcador do Camaçari/CPqD; as págs. 1 e 9 não casam marcador nenhum e eram sequestradas para um layout municipal cujos rótulos elas não têm. É a família "detecção por uma marca que pertence à CONTRAPARTE, não ao emitente" — registrada agora como gotcha compartilhado.
  - **`sem_parar_fatura`** — "NOTA FISCAL FATURA DE SERVIÇOS" da SEM PARAR INSTITUIÇÃO DE PAGAMENTOS LTDA (CNPJ raiz `04.088.208`, Pinheiros/São Paulo-SP), pedágio/tag veicular, escaneada. Detectada pelo **CNPJ raiz do emitente**, nunca pelo município: a fatura cita `Cidade/UF: Simoes Filho - BA` porque esse é o endereço do CLIENTE. Nota real: nº **705320619**.
  - **`camacari_gestaoclick`** — NFS-e de Camaçari/BA pela plataforma **GestãoClick**, a TERCEIRA do município ao lado do CPqD e do SISLOC/Benefix, e como aquela detectada pela marca da plataforma. Seu cabeçalho é `PREFEITURA DE CAMAÇARI`, **sem** o `MUNICIPAL` que o marcador do CPqD exige — por isso não casava nem o próprio município. Endereço numa única linha (`VIA URBANA, 01 (CIA-SUL) - SIMOES FILHO - 43700-000`), com município/UF em rótulos próprios, que são a fonte preferida. Nota real: nº **2127**, R$ 2.500,00.
  - O fallback solto de "Simões Filho" ficou **intocado de propósito**: é rede de segurança para notas cujo cabeçalho da prefeitura não sobreviveu ao OCR. Os dois emitentes novos foram registrados **antes** dele, padrão que o arquivo já usa para SISLOC, DANFSe, PJB e Localiza. Roteamento das págs. 2–8 conferido inalterado.
  - **PRESTADOR das duas páginas**, que também saía no sentinela. Na pág. 9 o bloco é rotulado igual ao do tomador. Na pág. 1 o CNPJ (`04.088.208/0001-65`), a inscrição municipal, o bairro, o CEP e o município/UF saem limpos do texto de página; a **razão social e o logradouro não** — as duas primeiras linhas do cabeçalho vêm fundidas com a coluna da direita (`Av ra, Cain E2 nara AEAMENTO LTDA.`), e são recuperadas por um recorte dedicado (`_ocr_cabecalho_sem_parar`, faixa ancorada no rótulo `CNPJ/MF` por `image_to_data`, com a rotação redescoberta no próprio recorte). Sem o recorte, a razão social ainda tem uma reserva **dentro do documento**: a frase antifraude do rodapé, que nomeia o emitente por extenso.
  - **⚠️ O endereço de uma linha só do GestãoClick é AMBÍGUO** e não pode ser lido por posição. Na mesma nota: `VIA URBANA, 01 (CIA-SUL) - SIMOES FILHO - 43700-000` (tomador) e `Rua Arembepe, 488 (sala 101) - Bela Vista - 42809-326` (prestador) — no tomador o parêntese é o **bairro** e o campo seguinte o **município**; no prestador o parêntese é o **complemento** e o campo seguinte o **bairro**. Lido por posição, o prestador ficaria com bairro "sala 101" e município "Bela Vista". O desempate é comparar o campo seguinte com o rótulo `Município:` do próprio bloco.
  - **VALORES das duas páginas**. A pág. 9 tem grade limpa e passou a ser lida inteira: serviços R$ 2.500,00, base R$ 2.500,00, alíquota 4,52%, ISS R$ 113,00, líquido R$ 2.500,00, ISS retido NÃO — com a identidade contábil conferida (base × alíquota = ISS impresso). A grade **não** é lida por posição de coluna: o rótulo `ISS` saiu do OCR como `E)` (conferido no pixel que é mesmo ISS), então o valor é ancorado no percentual entre parênteses, que é próprio dele.
  - Na pág. 1 **não existe grade de ISS**: a fatura não imprime base, alíquota nem imposto em lugar nenhum, e é a "Página 1/5" de um documento cujas demais páginas não estão no PDF. O que ela imprime é um resumo de cobrança, fechando num `TOTAL` que o OCR **não** recupera (fica sobre faixa cinza; conferido no pixel: R$ 3.844,86). O valor dos serviços é **composto pelas rubricas que a própria nota declara** — Subtotal R$ 3.817,56 + Outras Arrec. R$ 27,30 = R$ 3.844,86, batendo exatamente com o TOTAL impresso —, e só quando as duas são lidas: não existe "meio total". Base, alíquota e ISS ficam **zerados de propósito**, com três avisos dizendo isso, como o valor foi composto, e que só 1 das 5 páginas está no PDF.
  - **⚠️ Regressão evitada, medida durante a implementação**: ao ganhar layout próprio, a pág. 9 passava a cair no extrator genérico para os valores, onde a linha `COD/MUNICÍPIO DA INCIDÊNCIA DO ISSQN: 2905701` é colhida por proximidade como se fosse dinheiro — a nota saía com `valor_iss = 2905701.00`, R$ 2.905.701,00 de ISS numa nota de R$ 2.500,00. Um teste trava esse número específico.
  - **⚠️ Limitação mantida por decisão do usuário**: a fatura Sem Parar imprime o nome do cliente com erro **do próprio emitente** — "Stammaq Servicos Tecnicos Automocao Motores E Maq", não "Staummaq ... Automacao" (conferido no pixel, recorte a 300 dpi; o OCR ainda troca o `q` final por `g`). O extrator entrega o que está escrito; a identificação confiável é o **CNPJ** `02.370.080/0001-00`, que passa no checksum e confere com as outras sete páginas do lote.
  - Suíte: 648 → **683 testes** (35 novos em `tests/test_tomador_staummaq_scan2_paginas_1_e_9.py`). Contagem de layouts: **57 → 59** (2 novas constantes `LAYOUT_`).
- **Novo tipo de documento fiscal: CT-e OS (Conhecimento de Transporte Eletrônico para Outros Serviços, Modelo 67, DACTE OS)** — pedido explícito do usuário ("criar de plano de ação, para o layout dcteos, caso não exista, criar um novo [...] nota fiscal icms, o padrao para a opção DANFE do software"), a partir do arquivo real `ciatrans 82026.pdf` (nota nº 438, CIATRANS POOL TRANSPORTES DE PASSAGEIROS LTDA → STAUMMAQ SERVICOS TECNICOS AUT MOT E MAQUINAS LTDA, transporte de funcionários, R$ 6.739,50). Estruturalmente distinto TANTO da NFS-e ABRASF (ICMS, não ISS) QUANTO do DANFE Estadual/Modelo 55 (o "produto" é o SERVIÇO de transporte, sem tabela de itens/NCM) — retorna um `CteOS` (novo `src/models/cte_os_model.py`), transformado por um `CteTransformer` dedicado (`src/transformers/cte_transformer.py`) num XML `cteProc`/`CTe`/`infCte`, `mod=67`, namespace próprio do CT-e — nunca as tags de NF-e, o que seria uma inverdade estrutural.
  - **`LAYOUT_DACTE_OS`**, checado logo após o `LAYOUT_DANFE_PRODUTO` (ANTES até da DANFSe Nacional e do fallback solto de `LAYOUT_SIMOES_FILHO` — a nota cita "CHAVE DE ACESSO" e "Simões Filho" como município do tomador, que colidiriam com os dois). Ver a seção dedicada em [DOCUMENTACAO_CONVERSAO.md](DOCUMENTACAO_CONVERSAO.md) para o detalhamento completo (recorte de OCR dedicado da grade de valores/imposto, chave de acesso conferida por dígito verificador mod-11, endereço do tomador em uma linha só com rótulos degradados, retenções federais num bloco próprio do XML).
  - Suíte: 683 → **714 testes**; 31 novos em `tests/test_dacte_os_ciatrans.py`; prova de mutação 5/6 mortas.
  - Contagem de layouts inalterada em **59** (mesmo tratamento do `LAYOUT_DANFE_PRODUTO`: documento de tipo próprio, fora da numeração de layouts de NFS-e).

### Corrigido

- **Tomador extraído com "STAUMMAO" em vez de "STAUMMAQ" no DACTE OS (`LAYOUT_DACTE_OS`, gerador "CT-e Prático"/Bsoft) — achado real 2026-09-24, mesma nota nº 000.017.268, pág. 4 do lote "STAUMMAQ - NFSe TERCEIROS.pdf".** O OCR desta página específica lê a razão social do tomador com "O" no lugar do "Q" ("STAUMMAO SERV. TEC. AUTO. MOT. E MAQ. LTDA"), enquanto o MESMO CNPJ (`02370080000100`) já sai corretamente grafado "STAUMMAQ" nas págs. 1-3 do mesmo lote — confirmando erro pontual de OCR desta página, não um problema de lógica de extração. **Fix:** em `_parse_dacte_os` (`src/extractors/pdf_extractor.py`), correção por correspondência do CNPJ já conhecido deste cliente recorrente (`cnpj_tom == "02370080000100"`) seguida de `re.sub(r'\bSTAUMMAO\b', 'STAUMMAQ', razao_social_tom)` — gate deliberadamente restrito a este CNPJ, não uma heurística genérica de troca "O"/"Q". A asserção antes frouxa (`"STAUMMA" in tom.razao_social`) em `tests/test_dacte_os_staummaq_sigma_pag4.py` foi apertada para o valor exato corrigido.
  - Suíte: **793 testes**, sem alteração de contagem (asserção existente apertada, nenhum teste novo). Contagem de layouts inalterada em **62** — correção pontual em layout já existente, não um layout novo.
- **Valor dos Serviços travado no total de UM item isolado quando a NFS-e de Camaçari/BA escaneada (`camacari_ba_scan_v3`) discrimina VÁRIOS itens na mesma grade — achado real 2026-09-23, nota nº 1359, pág. 3 do lote "STAUMMAQ - NFSe TERCEIROS.pdf" (GRAFICA E EDITORA ITACIMIRIM LTDA → STAUMMAQ SERVICOS TECNICOS).** XML saía com `ValorServicos=500,00`; o correto, confirmado pelo usuário, é R$ 2.700,00 (soma de 4 itens: 500,00 + 500,00 + 750,00 + 950,00). Causa raiz: a regra que prioriza a linha "`<qtd>,0000 <unitário> <total>`" da discriminação sobre a célula da grade (introduzida para a nota nº 148, ver seção Camaçari em [DOCUMENTACAO_CONVERSAO.md](DOCUMENTACAO_CONVERSAO.md)) usava `re.search`, que só acha a PRIMEIRA linha que casa por inteiro — aqui a 1ª e a 4ª linha quebram por ruído de OCR no unitário, e o total da 2ª linha (500,00) era usado como se fosse o total da nota inteira. A célula "Valor dos Serviços (R$)" da grade já vinha correta (2.700,00) — a mesma fonte que `BaseCalculo`/`ValorLiquidoNfse` já liam direto, por isso esses dois campos nunca chegaram a sair errados. **Fix:** quando há MAIS DE UMA linha de item com total totalmente legível (vírgula + 2 casas, valor > 0) na grade, o override por linha de item é desligado e o valor volta para a célula da grade — regra generalizável a qualquer quantidade de itens, não específica desta nota. Zero regressão: as 3 outras notas do mesmo lote (págs. 1, 2 e 4) saem byte-a-byte idênticas ao XML gerado antes da correção.
  - Suíte: 766 → **772 testes** (6 novos em `tests/test_camacari3_valor_servicos_multiplos_itens_staummaq_1359.py`, texto OCR real).
  - Contagem de layouts inalterada — correção em código de layout já existente (`LAYOUT_CAMACARI_3`), não um layout novo.
- **Valor ISS extraído como zero no layout Brasília/DF (`brasilia_df`) para notas ESCANEADAS/OCR, achado real 2026-09-23 (Scan2026-09-23_090227.pdf, pág. 3, FLUIR PRODUCOES DE EVENTOS LTDA → NÁUTICA INDÚSTRIA E COMÉRCIO DE MÓVEIS LTDA, R$ 4.931,50).** Não é um layout novo — `brasilia_df` já existia e continua sendo o único layout de Brasília/DF (contagem total de layouts inalterada); a correção é só no branch de extração de valores, que nunca existira dedicado para este layout.
  - **Causa-raiz**: `_extrair_valores` nunca teve um branch próprio para `LAYOUT_BRASILIA` — caía direto no fallback genérico, cuja regex de ISS (`ISS(?:QN)?...`) casa a PRIMEIRA ocorrência da palavra "ISS" no texto inteiro. Toda nota deste layout imprime, no cabeçalho, a URL fixa de consulta "...acessando o site: https://iss.fazenda.df.gov.br/online/" (texto de TEMPLATE, não específico de nenhuma nota), que o OCR desta nota degradou para "https:/liss,fazenda,df,gov..."; a vírgula que sobra no lugar do ponto cai dentro da classe de caracteres do fallback (`[\d\.,]+`), que casava "iss," e devolvia `Valor ISS = 0,00` SEMPRE — mesmo com "Vl. ISSQN: R$ 99,12" (lido pelo OCR como "VI. ISSQN") presente mais adiante no texto real. Um valor errado e plausível, sem nenhum aviso ao usuário.
  - **Fix**: âncora dedicada na linha "Base de Cálculo: R$ X Alíquota: Y% Vl. ISSQN: R$ Z" da seção "IMPOSTO SOBRE SERVIÇO DE QUALQUER NATUREZA - ISSQN" (as 3 colunas saem na mesma linha, na ordem de leitura do OCR), tolerante a "Vl."/"VI." (OCR troca "l" minúsculo por "I" maiúsculo). Só dispara quando esta âncora específica bate — as variantes de texto DIGITAL (pdfminer, sem OCR) já cobertas pelos testes existentes não usam esta ordem de colunas e continuam pelo fallback genérico, comportamento inalterado.
  - Conferido também neste achado, sem necessidade de correção: Prestador, Tomador, Valor dos Serviços, Base de Cálculo e Valor Líquido já saíam corretos. Número da Nota Fiscal (impresso "20"), Código de Autenticidade e Data de Emissão real (impressos no cabeçalho da nota) não sobrevivem à passagem única de OCR de página inteira nesta nota escaneada — saem com sentinela (`00000000`/`XXXX-XXXX`) e aviso explícito ao usuário, comportamento seguro e já esperado do projeto (dado ausente é preferível a um dado fabricado); recuperar esses campos via um recorte de OCR dedicado ao cabeçalho (mesmo padrão já usado em outros layouts escaneados) fica como melhoria futura, fora do escopo desta correção.
  - Suíte: 762 → **763 testes** (1 novo em `tests/test_brasilia_layout.py`).
  - Contagem de layouts inalterada em **61** (correção em layout já existente, não um layout novo).
- **Brasília/DF (`brasilia_df`) escaneado: Número da Nota, Data de Emissão e Código de Autenticidade saindo sentinela apesar de legíveis na imagem — achado real 2026-09-23, nota nº 20, pág. 3 do lote `Scan2026-09-23_090227.pdf` (FLUIR PRODUCOES DE EVENTOS LTDA → NÁUTICA INDÚSTRIA E COMÉRCIO DE MÓVEIS LTDA).** Em notas escaneadas (caminho OCR, `_ocr_page`, não pdfminer), a leitura de página inteira (zoom 3x, PSM automático) derrubava por completo a linha de cabeçalho "Data de Geração da NFS-e / Data de Competência / Código de Autenticidade" e a caixa "Número da Nota Fiscal" (topo direito, ao lado do QR Code) — nenhum dos 4 valores aparecia no texto, em nenhum PSM automático testado, e a extração caía no sentinela (`Numero=00000000`, `CodigoVerificacao=XXXX-XXXX`, `DataEmissao`=instante da conversão) com aviso. **Fix:** novo recorte dedicado `_ocr_header_box_brasilia` (`src/extractors/pdf_extractor.py`) — faixa do topo (0-19% da altura, largura inteira, zoom 4x/PSM 6) para Data de Geração/Competência/Código, e caixa superior direita (78%-100% da largura, 0-10% da altura, zoom 6x/PSM 3-4) para o Número —, prependado ao texto de página inteira dentro de `_ocr_page` quando `Governo do Distrito Federal` é detectado no texto já lido (o layout ainda não foi resolvido neste ponto do pipeline). Validado contra a imagem real: `Numero=20`, `CodigoVerificacao=53001081257540290000183000000000002026081787593850`, `DataEmissao=2026-08-24T14:50:59`, `Competencia=2026-08-01`. Não é layout novo (contagem de layouts inalterada); o caminho digital (pdfminer) desta plataforma já resolvia esses campos sem OCR e não é afetado.
- **Duas notas com Valor dos Serviços extraído como zero no PDF "NORDESTE TUBETES - SCAN.pdf", achado real 2026-09-17 — duas causas-raiz distintas na mesma remessa.**
  - **Nota nº 705900227 (Sem Parar, `sem_parar_fatura`)**: uma VARIANTE desta fatura de pedágio/tag veicular não imprime nenhum rótulo "Subtotal" — o "Resumo da sua Fatura" fecha direto num "TOTAL" cuja linha o OCR lê com confiança baixíssima demais para usar ("TOTAL 8B07,00D" em vez de "807,00 D"). Sem "Subtotal", o código (criado pelo esforço da nota Staummaq, que soma "Subtotal + Outras Arrecadações" quando ambos existem) retornava `valor_servicos=0.0` incondicionalmente. **Fix:** quando "Subtotal" está ausente, soma-se em vez disso a coluna "TOTAL" de cada linha da tabela por placa (última célula, sempre "<valor>D" colado ao fim, tratada pela mesma convenção "2 últimos dígitos são centavos" já usada em `_parse_valor_camacari`) com o "TOTAL OUTRAS ARRECADAÇÕES" (rótulo próprio, valor limpo). Conferido na nota real: 45,40 + 96,70 + 308,00 + 281,90 + 75,00 = 807,00. O caso com "Subtotal" presente continua funcionando exatamente como antes.
  - **Nota nº 18770 (SETE CONNECT TECNOLOGIA DA INFORMAÇÃO LTDA → NORDESTE TUBETES, R$ 109,99)**: é uma NFCom (tributada por ICMS/IBS/CBS), não uma NFS-e ABRASF — sem detecção dedicada, caía no fallback amplo `LAYOUT_NACIONAL` (parser de DANFSe, incompatível com a estrutura de uma NFCom) e saía com Valor dos Serviços zerado e o endereço do tomador poluído. **Fix:** novo layout dedicado **`nfcom_sete_connect`**, 4º emitente do mesmo template nacional do portal SVRS já usado por `nfcom_salvador`/`nfcom_rlgr`/`nfcom_lotec_fibra` — gate pelo CNPJ do emitente (13.060.537/0001-99) + marcador "FATURA DE SERVIÇOS DE COMUNICAÇÃO ELETRÔNICA". Prestador FIXO (mesmo racional dos outros 3 layouts NFCom); tomador extraído dinamicamente do bloco "CLIENTE:"/"CNPJ:"/"ENDEREÇO:" — MAS nesta nota o rótulo do CNPJ do tomador sai "CNP:" (o "J" foi comido pelo OCR), tolerado via `CNPJ?` no regex; Competência via "REFERÊNCIA (ANO/MÊS)"; Data de Emissão via "DATA DE EMISSÃO...às..."; Código de Serviço fixo "0000"; Código de Verificação = chave de acesso de 44 dígitos com fallback honesto `'NFCOM'`; Valor dos Serviços = "TOTAL A PAGAR: R$"; Base de Cálculo/Alíquota/ISS mantidos em 0,00 propositalmente (ICMS, não ISS), com aviso.
  - `KNOWN_CITIES` ganhou `DIAS DAVILA`/`DIAS DÁVILA` (IBGE `2910057`, Dias d'Ávila/BA — município do tomador da nota SETE CONNECT).
  - Os XMLs de exemplo `temp_Pagina_1_NF_705900227.xml`/`temp_Pagina_2_NF_18770.xml` foram regenerados e conferidos na sessão original de descoberta do bug (PDF de origem não disponível neste ambiente para reprodução).
  - Suíte: 749 → **762 testes** (4 novos em `tests/test_nordeste_sem_parar_total_sem_subtotal.py`, 9 novos em `tests/test_nfcom_sete_connect_layout_novo.py`).
  - Contagem de layouts: **60 → 61** (nova constante `LAYOUT_NFCOM_SETE_CONNECT`).
- **Layout ISBET (`isbet_recibo`, "Nota de Contribuição Solidária") completado — antes tinha só detecção + stub de Número/Competência, sem extração de prestador/tomador/valores.** Pedido explícito do usuário ("Crie um plano de ação, para o novo layout instituto, crie um novo caso não exista"), a partir do arquivo real `ISBET - 1799.pdf` (nota nº SAL-2026-01799, Instituto Brasileiro Pró Educação, Trabalho e Desenvolvimento → BONI TRANSPORTES LOGÍSTICA E COMÉRCIO LTDA, R$ 130,00). A investigação revelou que o layout já existia no código (não era um layout novo), mas estava efetivamente morto:
  - **Detecção nunca disparava**: o check do ISBET vinha DEPOIS do check bare `RIO DE JANEIRO|NOTA CARIOCA`, e o próprio letterhead do ISBET imprime "Rio de Janeiro" (cidade do emitente) — toda nota real caía em `LAYOUT_RIO` (Nota Carioca) antes de chegar no check do ISBET. Corrigido subindo o check do ISBET para ANTES do de Rio de Janeiro, em ambos os detectores.
  - **Prestador saía com o CNPJ do TOMADOR**: o CNPJ do ISBET reprova o checksum nesta nota (a leitura de página inteira lê "43.125.366/0001-14"; o real, confirmado por crop em zoom 4x, é "43.126.366/0001-14") — o fallback genérico de prestador então usava o único CNPJ válido do documento inteiro, o da BONI (o TOMADOR), duplicando-o também no PRESTADOR.
  - **Número da nota**: por decisão explícita do usuário, passa a usar o "Boleto Nº" (ex. "656956"), não mais o "Nº:SAL-2026-XXXXX" interno do ISBET.
  - Prestador FIXO com o CNPJ correto (validado por checksum); tomador DINÂMICO do bloco "USUÁRIO DOS SERVIÇOS"; discriminação real extraída (sem a tabela "Relação de Jovens Aprendizes" vazando pro campo); valor recuperado por recorte OCR dedicado em zoom 10x (a linha do item sai como puro lixo no OCR de página inteira); ISS não incidente sinalizado em aviso. Ver a seção completa em [DOCUMENTACAO_CONVERSAO.md](DOCUMENTACAO_CONVERSAO.md).
  - Suíte: 714 → **717 testes** (3 novos em `tests/test_isbet_contribuicao_solidaria_layout.py`).
  - Contagem de layouts inalterada em **59** — nenhuma constante `LAYOUT_` nova (o layout já existia; a correção só completou a extração dele).
- **Prestador LUNITECK (layout `salvador`) saía com CNPJ sentinela ou razão social garblada, reportado pelo próprio importador Domínio no lote de 6 notas do Segment D** ("Relatório do Resumo da Importação": "CNPJ do fornecedor inválido, conteúdo '00000000000100'" para a nota 2437; "CNPJ do arquivo diferente do CNPJ da empresa ativa" para 2436 e 2437). Duas causas-raiz distintas, confirmadas por recorte em zoom 4x pixel a pixel em AMBAS as notas (mesma prestadora recorrente, mesma razão social, mesmo endereço, letra por letra idênticos):
  - **Nota 2437**: a linha inteira do CNPJ some do texto OCR entre "Inscrição Municipal" e "Nome/Razão Social" — sem nenhum dígito sobrando para o `_scavenge_all_cnpjs` recuperar, o campo cai no sentinela `00000000000100`.
  - **Nota 2436**: o CNPJ sai correto, mas a captura de razão social gruda no resto da linha de Inscrição Municipal em vez de pular para a linha seguinte com o nome real (sai "da - SOLUCOES E DESENVOLVIMENTO EM TECNOLOGIA LTDA - ME N aç", sem o prefixo "LUNITECK") — a raiz é a própria Inscrição Municipal impressa nesta nota ter formato parecido com CNPJ, confundindo a heurística de "primeira linha que não é o rótulo".
  - Corrigido com o mesmo princípio já usado para BONI TRANSPORTES/GUARAJUBA SHOPPING: substitui CNPJ + razão social + endereço completo (também pixel-confirmado) quando o CNPJ já é o real da LUNITECK (`07295620000144`) OU quando o checksum reprovou e a razão social bate com esta contraparte conhecida — nunca mascarando um CNPJ genuinamente diferente de outra empresa.
  - Suíte: 717 → **721 testes** (4 novos em `tests/test_luniteck_cnpj_contraparte_conhecida.py`, a partir do texto OCR real capturado das duas notas). Contagem de layouts inalterada em **59** — nenhuma constante `LAYOUT_` nova.
  - XMLs reais regenerados em produção: `LUNITECK - 2436_Pagina_1_NF_00002436.xml` e `LUNITECK - 2437_Pagina_1_NF_00002437.xml`.
- **Prestador da nota nº 2232 (INSTITUIÇÃO ASSISTENCIAL BENEFICENTE CONCEIÇÃO MACEDO) saía com o CNPJ do TOMADOR (BONI TRANSPORTES), reportado pelo Domínio como "BONI TRANSPORTES, LOGISTICA E COMERCIO LTDA." sendo o Fornecedor de uma nota cujo prestador real é outra entidade.** Diferente da nota UFFICIO (nº 00000080, já catalogada): o rótulo "PRESTADOR DE SERVIÇOS" está íntegro e delimita o bloco corretamente — o bug é que a LINHA do CNPJ do prestador está inteiramente ausente do OCR dentro desse bloco (pula direto do rótulo pro nome), e o "chute" de último recurso (1º CNPJ válido do documento inteiro) pegava cegamente o único CNPJ válido, que é o da BONI (tomadora). **Fix:** o chute agora recusa um candidato que só aparece DEPOIS do rótulo da OUTRA entidade no texto inteiro — sinal de que pertence a ela — preferindo o sentinela ao dado da entidade errada. Gated em `LAYOUT_SALVADOR`: no DANFSe Nacional a coluna de CNPJ é compartilhada entre entidades e o OCR pode ler fora de ordem no sentido OPOSTO (CNPJ do prestador aparecendo dentro do bloco do tomador) — `test_danfse_nacional_pagina_unica_sem_fantasma.py` continua verde, confirmando que o guard não generaliza pra esse layout.
- **Ampliação na MESMA nota nº 2232 — usuário rejeitou o sentinela do fix acima como "CNPJ incorreto".** O fix anterior evita a contaminação (CNPJ da BONI vazando pro prestador) mas devolve o sentinela honesto `00000000000100` quando não há candidato — o usuário esperava o CNPJ real, não um sentinela. Crop em zoom 10x, pixel a pixel, confirma "00.584.568/0001-05" (checksum válido) perfeitamente legível NA IMAGEM — mas nenhuma combinação de zoom (3 a 12) nem PSM (automático/4/6/11) testada na leitura de página inteira reproduz esses dígitos certos. Mesma classe de "defeito sistemático da imagem, não recuperável por OCR de página inteira" já documentada para o CNPJ da BONI TRANSPORTES — substituído pelo mesmo princípio de contraparte recorrente conhecida: quando o checksum já reprovou E a razão social bate com "BENEFICENTE CONCEIÇÃO", o CNPJ é substituído pelo valor pixel-confirmado.
  - Suíte: 721 → **725 testes** (4 novos em `tests/test_salvador_prestador_contaminado_tomador_cnpj_ausente.py`, cobrindo as duas rodadas desta mesma nota — guard de contaminação e recuperação do CNPJ real). Contagem de layouts inalterada em **59** — nenhuma constante `LAYOUT_` nova.
- **Competência da nota nº 2436 (LUNITECK) saindo `7025-04-01`, reportada pelo Domínio como "01/04/7025" na coluna Data do relatório de importação.** O `raw_text` real tem DUAS ocorrências de "COMPETÊNCIA" (recorte de página + leitura de página inteira): "COMPETÊNCIA: 0/2025" (mês "0", só 1 dígito, não casa o regex de 2 dígitos do `LAYOUT_SALVADOR`) e "COMPETÊNCIA 04/7025" (mês plausível, mas "2025"→"7025", "2"→"7") — o regex casa a 2ª por ser a 1ª a bater o formato exigido. O guard de "ano com 1 dígito trocado" já existente só dispara quando o MÊS bate com o da Data de Emissão (aqui, "04" ≠ "08" da nota) — o ano absurdo escapava incorrigido. **Fix:** novo guard, mais amplo, dispara sempre que o ano capturado se afasta da Data de Emissão por mais de 1 ano, independente do mês bater — nenhuma competência legítima fica a 5000 anos de distância da própria emissão.
  - Suíte: 725 → **728 testes** (3 novos em `tests/test_salvador_competencia_ano_absurdo_luniteck_2436.py`, incluindo regressão do guard de "ano com 1 dígito trocado" já existente). Contagem de layouts inalterada em **59** — nenhuma constante `LAYOUT_` nova.
- **Nota nº 46345 (VALOR COMÉRCIO E SERVIÇOS DE INFORMÁTICA LTDA) saindo com RazãoSocial = o próprio endereço e Valor dos Serviços/Base de Cálculo zerados — o zerado reportado pelo Domínio como "Valor contábil zerado para nota com situação diferente de cancelada".** Duas causas-raiz independentes:
  - **RazãoSocial**: o guard de ruído `_LABELS_NOISE` (compartilhado por ~30 layouts) rejeita qualquer candidato que COMECE com a palavra "Valor" — pensado pra rejeitar rótulos vazados tipo "Valor Total"/"Valor Líquido", mas a razão social real desta empresa também começa com essa palavra. O candidato correto ("VALOR COMERCIO E SERVICOS DE INFORMATICA LTDA", capturado certo pelo regex primário) era descartado e substituído pela linha de Endereço. **Fix:** o guard passa a exigir uma continuação típica de rótulo monetário depois de "Valor" (Total/Líquido/Bruto/Unit/dos Serviços/ISS/Retido/"("/":"/fim de linha) — nenhuma dessas aparece logo após "Valor" no início de uma razão social real deste corpus.
  - **Valores zerados**: a nota imprime "VALOR TOTAL DA NOTA FISCAL R$ 583,00" — com a palavra "FISCAL" no meio e sem "=" nem ":" antes de "R$", variante do template não vista nas notas Salvador já catalogadas. O regex exigia um desses 2 separadores logo após "NOTA", então a linha inteira não casava. **Fix:** "FISCAL" tolerado como opcional e o separador tornado opcional.
  - **Achado colateral, corrigido na mesma investigação**: a grade de Alíquota/ISS desta nota tem só 4 colunas (sem a coluna "Crédito" que o regex de 5 colunas já existente exige), e a própria Alíquota sai sem a vírgula decimal ("415" em vez de "4,15"). Novo regex de 4 colunas, com a Alíquota sem vírgula só aceita quando a identidade Base × Alíquota = ISS bate (583,00 × 4,15% ≈ 24,19, exatamente o ISS lido na mesma linha) — recupera Alíquota/ISS reais em vez de deixá-los zerados + aviso.
  - Suíte: 728 → **733 testes** (5 novos em `tests/test_salvador_valor_comercio_razao_e_valores_zerados.py`, a partir do texto OCR real da nota). Contagem de layouts inalterada em **59**.
  - XML real regenerado em produção: `VALOR COMERCIO - 33908_Pagina_1_NF_46345.xml`.
- **Segunda rodada de erros no mesmo lote de 6 notas do Segment D, todos reportados pelo usuário após a reimportação no Domínio.** Quatro causas apuradas, três delas exigindo correção de código:
  - **Número da Nota e Data de Emissão da nota nº 33908 (VALOR COMÉRCIO), ainda errados após a correção da RazãoSocial/Valores acima.** A Data de Emissão saía como o instante da CONVERSÃO (`datetime.now()`) — bug mais grave que um dígito trocado: nenhum padrão de data rotulada bate nesta nota (a data real aparece sem rótulo no topo da página; a única ocorrência rotulada, "Emitidoem:", tem o rótulo colado sem espaço E o ano corrompido). **Fix:** fallback tardio específico do `LAYOUT_SALVADOR`, ancorado no marcador estrutural "NOTA FISCAL DE SERVIÇOS ELETRÔNICA" logo após o timestamp sem rótulo. O Número da Nota saía "46345" (na verdade o "Pedido Numero" interno do prestador, dentro da discriminação do serviço) em vez do real "33908" — o gate que ativa os recortes dedicados do cabeçalho Salvador (`_ocr_header_box_salvador`, votação de número, recuts de tomador/prestador) exigia o título "PREFEITURA MUNICIPAL **DO** SALVADOR" literal, mas o OCR desta nota lê "**DE** SALVADOR" — o bloco inteiro de recortes nunca disparava, mesmo a nota já roteada para `LAYOUT_SALVADOR` (cuja própria detecção já é tolerante a "DE"/"DO"). **Fix:** gate alinhado à mesma tolerância — mas a troca do texto de página inteira por uma releitura em PSM 6 (dentro do mesmo bloco, motivada por uma nota diferente) permanece restrita à condição ORIGINAL ("DO"): testado contra esta nota, aquela releitura introduz ruído de marca d'água na Razão Social e uma 5ª coluna espúria na grade de Alíquota/ISS que zera valores já corretos — dois gates agora, um estrito e um amplo, cada recorte usando o que lhe cabe.
  - **CNPJ do prestador da nota nº 2232 (INSTITUIÇÃO ASSISTENCIAL), reportado de novo como "incorreto" pelo usuário.** Investigado e confirmado que **já estava coberto** pela correção anterior (PR #97): o valor de contraparte conhecida (`00584568000105`) já está em produção desde então — nenhuma mudança de código nem teste novo necessários aqui.
  - **"Um prestador não identificado" na nota nº 5 (SBS SOLUÇÕES INTEGRADAS DE SEGURANÇA ELETRÔNICA, layout `danfse_nacional_reforma`, DANFSe v2.0).** Ambas as entidades (prestador E tomador) saíam "Não Identificado", apesar de CNPJ/razão/endereço perfeitamente legíveis na imagem — quatro causas-raiz na mesma nota, em `_extrair_entidade_nacional_reforma`:
    1. O OCR lê a barra de "TOMADOR / ADQUIRENTE" como "TOMADOR |! ADQUIRENTE" — o rótulo exigia a barra literal, então o fim do bloco do PRESTADOR (que usa esse rótulo como limite) e o início do bloco do TOMADOR saíam vazios ao mesmo tempo. Separador agora tolera qualquer sequência curta de pontuação/ruído entre as duas palavras.
    2. Em vez das colunas "Nome/Nome Empresarial", "Município/Sigla UF" e "Código IBGE/CEP" caírem em linhas separadas (padrão já tratado), esta nota funde tudo numa única linha de rótulos seguida de uma única linha de valores — nem o extrator de razão isolada nem o de município isolado reconheciam essa forma. Novo fallback recupera razão + município de uma linha fundida, usando o próprio código IBGE já impresso nela como prova de onde a razão termina e o município começa (testado contra o resolver de IBGE — um corte por contagem de palavras é ambíguo e resolveria errado para nomes como "Lauro de Freitas").
    3. A palavra "OPERAÇÃO" sai tão degradada que nem "DESTINATÁRIO DA OPERAÇÃO" nem "INTERMEDIÁRIO DA OPERAÇÃO" batiam como fim do bloco do tomador — sem um fim reconhecido, a busca do CNPJ vazava para o documento INTEIRO e encontrava 11 dígitos da própria Chave de Acesso (repetida no rodapé), aceitando-os como se fossem o CNPJ do tomador. "IDENTIFICADO NA NFS" (frase de status que sobrevive íntegra nas duas linhas degradadas) adicionada como marcador de fim mais resiliente.
    4. O "0" inicial do CNPJ do tomador sai como a letra "D" ("D4.555.283/0003-50"). Tolerância pontual "D"/"O"→"0" só na posição inicial, aceita apenas quando o checksum corrigido bate.
  - **"Luniteck tomador do serviço incorreto" na nota nº 2436.** O CNPJ da BONI TRANSPORTES (tomadora recorrente, já com substituição de contraparte conhecida) saía com a filial "0001-99" — confirmada para uma nota DIFERENTE (CONEX4 MULTIMÍDIA) — quando a imagem desta nota mostra "0003-50" (mesma filial confirmada de forma cruzada em 3 outras notas desta mesma leva). A correção antiga sempre devolvia um valor FIXO, ignorando qual filial a nota realmente imprime. **Fix:** quando o checksum reprova, compara o(s) candidato(s) de CNPJ formatado realmente lidos em QUALQUER parte do documento (não só no bloco da entidade — esta nota tem a página inteira reimpressa 2x pelo OCR, e o candidato bom só sobrevive na 2ª cópia) contra as duas filiais conhecidas e usa a mais próxima por distância de dígitos; só cai no valor fixo antigo quando nenhum candidato bate perto o suficiente.
  - Suíte: 733 → **740 testes** (7 novos: `tests/test_salvador_valor_comercio_numero_nota_gate_de_salvador.py`, `tests/test_danfse_reforma_sbs_colunas_fundidas_prestador_nao_identificado.py`, `tests/test_boni_transportes_filial_0003_luniteck_2436.py`). Contagem de layouts inalterada em **59** — nenhuma constante `LAYOUT_` nova.
- **Dois problemas adicionais na mesma nota nº 5 (SBS SOLUÇÕES), descobertos ao verificar o XML já corrigido do item acima e corrigidos a pedido explícito do usuário ("Corrija também os dois problemas da SBS Soluções"): Endereço "Não informado" para prestador E tomador, e ValorServicos = 0,00 apesar de ValorLiquidoNfse = 660,51.** Ambos em `_extrair_entidade_nacional_reforma`/`_extrair_valores` (`LAYOUT_NACIONAL_REFORMA`):
  - **Endereço**: o rótulo "Endereço" imprime colado à coluna vizinha "E-mail"/"Email" na MESMA linha do cabeçalho ("Enderaço Email" no prestador — o OCR também troca "Endereço" por "Enderaço" —, "Endereço E-mall" no tomador); o padrão original exigia quebra de linha logo após o rótulo isolado e nunca casava. Como as duas colunas são vizinhas, o OCR de página inteira também funde os VALORES na mesma linha (endereço do prestador + e-mail colado sem separador). **Fix:** rótulo tolera texto/ruído após "Endereço"/"Enderaço" na mesma linha, e um sufixo de domínio comum (.com/.com.br/.net/.org/.gov) colado no fim da linha de valor é removido antes do parse dos segmentos. Achado colateral, corrigido junto: o bairro real do tomador ("ITINGA", Lauro de Freitas/BA, confirmado por captura de tela) saía "[TINGA «" — ruído solto de OCR limpo do fim do último segmento, com substituição pontual "["→"I" só quando imediatamente seguida de "TINGA".
  - **ValorServicos**: esta nota é "Serviços sem a incidência de ISSQN e ICMS" (operação não sujeita ao ISSQN) — nessas notas o rótulo "VALOR DA OPERAÇÃO / SERVIÇO" sai tão degradado pelo OCR ("NATO DA GERAÇÃO FRITO", sem nenhum fragmento reconhecível) que nunca casa, e "BC ISSQN" nem chega a ser impresso. **Fix:** quando não há nenhuma retenção detectada (ISS não retido, sem IRRF/INSS/contribuições sociais), o VALOR LÍQUIDO DA NFS-e (R$ 660,51, já extraído corretamente por um rótulo que sobrevive ao OCR) serve de fallback para `valor_servicos` — matematicamente idêntico ao bruto quando nada é retido; um teste de regressão negativo confirma que o fallback NÃO entra quando há retenção (o líquido seria menor que o valor da operação nesse caso).
  - Suíte: 740 → **744 testes** (4 novos em `tests/test_danfse_reforma_sbs_endereco_colado_email_e_valor_zerado.py`, a partir do texto OCR real completo da nota, incluindo a grade de valores). Contagem de layouts inalterada em **59** — nenhuma constante `LAYOUT_` nova.
  - XML real regenerado em produção: `SBS SOLUÇOES - 5_Pagina_1_NF_5.xml`.
- **Tomador extraído incorretamente na nota nº 59 (Campo Grande/MS, DANFSe v2.0, PDF digital), reportado pelo usuário como "tomador do serviço extraído incorreto".** Duas causas-raiz em `_extrair_entidade_nacional_reforma` (`LAYOUT_NACIONAL_REFORMA`), as DUAS ligadas ao fato de esta nota imprimir PRESTADOR → INTERMEDIÁRIO → TOMADOR, ordem diferente da assumida (PRESTADOR → TOMADOR → INTERMEDIÁRIO):
  - **Endereço "Não informado"** apesar de estar impresso: o cabeçalho "TOMADOR / ADQUIRENTE" desta nota é seguido, na mesma respiração, por "... NÃO IDENTIFICADO NA NFS-e\nDESTINATÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e" — e o marcador de fim de bloco resiliente "IDENTIFICADO NA NFS" (achado da nota nº 5/SBS acima) casava DENTRO dessa MESMA frase do próprio cabeçalho, cortando o bloco do tomador a quase nada e perdendo o Endereço real logo abaixo. **Fix:** pula esse preâmbulo fixo antes de procurar o fim de bloco de verdade.
  - **Código de Município/CEP herdado do INTERMEDIÁRIO** (Salvador/BA, CEP 40280900) em vez de vazio — a nota genuinamente não imprime Município/CEP próprios para um tomador não identificado. Como esses campos são colhidos por ORDINAL de ocorrência (1ª = prestador, 2ª = tomador) e o INTERMEDIÁRIO tem sua PRÓPRIA cópia deles e aparece ANTES do tomador nesta nota, sua ocorrência era pega como se fosse a do tomador — valor plausível-porém-errado. **Fix:** o trecho do intermediário é excluído da região de coleta ordinal quando ele cai entre prestador e tomador.
  - **Regra de negócio nova, pedido explícito do usuário na sequência: "quando [o layout nacional] não tiver o trecho tomador de serviço preenchido, porém, tiver o trecho intermediário do serviço preenchido, utilizar como o tomador de serviço"** (prioridade para o tomador de verdade quando ambos vêm preenchidos). Regra já existente para `LAYOUT_NACIONAL` (v1.0, decisão de 2026-08-04 — ver `test_danfse_intermediario_vira_tomador.py`), agora **estendida para `LAYOUT_NACIONAL_REFORMA` (v2.0)**: tomador não identificado (CNPJ sentinela ou razão com a tarja "NÃO IDENTIFICADO") + intermediário identificado → intermediário promovido a tomador, `<Intermediario>` esvaziado. Nesta nota, isso substitui o resultado do fix de Endereço acima (a Entidade inteira passa a ser a do intermediário). Colateral: o extrator do intermediário nunca capturava Município/Sigla UF/Código IBGE/CEP (só CNPJ/Nome — o `<Intermediario>` do ABRASF 2.01 não tem endereço); agora captura, pois esses campos passam a valer quando promovido a tomador (nesta nota: Salvador/BA, `2927408`, CEP `40280900`, sem logradouro — o layout nunca imprime "Endereço" para o intermediário).
  - Suíte: 747 → **749 testes** (2 testes em `tests/test_danfse_nacional_reforma_tomador_nao_identificado_intermediario_no_meio.py`, um cenário COM intermediário e um SEM, texto real via pdfminer). Contagem de layouts inalterada em **60** — nenhuma constante `LAYOUT_` nova.
  - XML real regenerado em produção: `temp_Pagina_1_NF_59.xml`.
- **GUI: tela de seleção de páginas ("O PDF possui mais de uma nota válida...") não aparecia para PDFs de poucas páginas, reportado pelo usuário com o arquivo real `STAUMMAQ - SCAN.pdf` (8 páginas, 8 notas válidas).** Investigação: com o PDF isolado (fora da GUI), `parse_multiple()` sempre devolveu corretamente `len(nfse_list) > 1` (8) — não é bug de extração nem de contagem de páginas. O `Container` que hospeda os checkboxes da tela usava `height=420 if len(nfse_list) > 8 else None` — exatamente o PDF reportado cai bem na fronteira (8 não é `> 8`) e recebe `height=None`; suspeita (não confirmável sem rodar o app nativo) é que isso deixa a `Column` interna sem altura limitada para o layout engine do Flet calcular no backend desktop, colapsando o diálogo. **Fix:** o `Container` agora sempre recebe uma altura explícita, escalada pela quantidade de notas (piso 160px, teto 420px) em vez de `None` para listas curtas; scroll do conteúdo sempre ativo (`AUTO`), sem custo para listas curtas. Colateral corrigido na mesma investigação: o `except Exception as ex: pass` que envolve toda a pré-checagem de páginas silenciava QUALQUER erro sem nenhum aviso ao usuário — se algo além da hipótese acima também estiver quebrando essa tela em algum PDF, agora fica registrado no log da própria GUI (`[AVISO] Não foi possível pré-analisar as páginas...`) em vez de desaparecer silenciosamente.
  - Sem teste automatizado (a tela é construída com componentes Flet reais, que exigem o runtime da GUI — mesma limitação já documentada para outras telas do `gui_app.py`); validado apenas por análise estática (`ast.parse` confirma sintaxe válida) e pela suíte completa (749 testes, sem alteração de contagem). Validação funcional completa (reconstruir `build.bat` e confirmar visualmente que a tela de seleção aparece para o PDF real `STAUMMAQ - SCAN.pdf`) fica pendente de confirmação manual do usuário, seguindo a convenção já documentada do projeto de que fixes GUI-only exigem esse passo (pytest não alcança).
- **CT-e OS (`LAYOUT_DACTE_OS`) caindo no fallback ABRASF genérico (`CompNfse`) na pág. 4 do lote real "STAUMMAQ - NFSe TERCEIROS.pdf" (nota nº 000.017.268, SIGMA TRANSPORTES LTDA → STAUMMAQ, R$ 2.115,08), com `PrestadorServico/RazaoSocial` saindo como o título de uma SEÇÃO do formulário ("INFORMAÇÕES ESPECÍFICAS DO MODAL RODOVIÁRIO") e todos os valores zerados.** Causa-raiz: a 2ª marca exigida pela detecção, "Conhecimento de Transporte Eletrônico" (contígua), nunca sobrevivia ao OCR desta página — "Documento Auxiliar do Conhecimento de Transporte" e "Eletrônico para Outros Serviços" saem em linhas NÃO-ADJACENTES (um bloco inteiro de outro conteúdo do formulário entre elas) — embora a 1ª marca ("CT-e OS") saísse intacta. **Fix:** "Eletrônico" tornado OPCIONAL após "Conhecimento de Transporte" em `_detect_layout`/`_detect_layout_page` — "Conhecimento de Transporte" sozinho já é exclusivo do CT-e/DACTE OS, preservando a blindagem contra falso positivo sem depender do padrão exato de degradação do OCR.
  - Esta nota também expôs um SEGUNDO gerador de DACTE OS ("Bsoft Internetworks - CT-e Prático", diferente do "Master CT-e" já coberto pela nota CIATRANS) — `_parse_dacte_os` e `_ocr_recut_dacte_os_grade` generalizados para cobrir os dois templates sem regredir nenhum: CNPJ do emitente pontuado com rótulo de IE degradado, razão social fundida com o título "DACTE OS" na mesma linha, endereço do emitente antes (não depois) da linha do CNPJ, rótulo do tomador "TOMADOR/USUÁRIO DO SERVIÇO:", bairro do tomador com hífen próprio ("CIA-SUL"), CEP do tomador colado ao rótulo degradado "cer:", chave de acesso/data de emissão afastadas dos próprios rótulos, protocolo com prefixo de ruído ("Lt "), âncora alternativa para a grade de valores quando "COMPONENTES" não sobrevive ao OCR (rabisco de assinatura sobreposto). Ver a seção completa em [DOCUMENTACAO_CONVERSAO.md](DOCUMENTACAO_CONVERSAO.md).
  - Suíte: 772 → **793 testes** (21 novos em `tests/test_dacte_os_staummaq_sigma_pag4.py`, texto OCR real). Contagem de layouts inalterada (CT-e OS é tipo de documento próprio, fora da numeração de layouts de NFS-e — mesmo tratamento do `LAYOUT_DANFE_PRODUTO`). Págs. 1-3 do mesmo lote conferidas byte-a-byte idênticas ao XML de referência — nenhuma regressão.
  - XML real regenerado em produção: `STAUMMAQ - NFSe TERCEIROS_Pagina_4_NF_000017268.xml` (agora `infCte`/`mod=67`, não mais `CompNfse`).

### Corrigido em detecção

- **O fallback solto por nome de cidade não sequestra mais notas de outros emitentes.** `_detect_layout`/`_detect_layout_page` terminavam com `if re.search(r'Sim[oõ]es Filho', t) → LAYOUT_SIMOES_FILHO`, bastando o nome da cidade aparecer em qualquer lugar do texto. Agora exige, junto, um marcador **estrutural** do template de Simões Filho (`Série/Número RPS`, `Exigibilidade de ISS` — tolerando o garble real "Exigibilidade de 155" —, `SERVIÇO NACIONAL`, `DESCONTO INCONDICIONAL`). A rede de segurança continua de pé para notas cujo cabeçalho da prefeitura não sobreviveu ao OCR, que é para o que ela existe. Sem esse aperto, o próximo emitente novo cujo cliente seja a Staummaq cairia na mesma armadilha.
  - **Varredura de segurança**, que é o que autoriza mexer numa rede de segurança: os dois detectores foram rodados sobre os **134 textos de nota reais** já versionados na suíte, com a regra antiga e com a nova. **8** citam "Simões Filho" e **nenhum** além das duas páginas-alvo muda de layout.
  - Precedência preservada: Barreiras compartilha o mesmo template e continua sendo checada antes (pelo rótulo `Data Fato Gerador`), comportamento já documentado.
- Contagem de layouts inalterada em **59** (58 específicos + genérico) nesta segunda passada — nenhuma constante `LAYOUT_` nova, verificado por contagem derivada. Suíte: 648 → **683 testes** (35 no arquivo do lote; 11 ficam vermelhos com as cinco peças desligadas, e cada uma morre isolada na prova de mutação).

### Corrigido

- **Layout `localiza_fatura` — tomador extraído incorreto (nota AAMCZ-529060, filial AGENCIA AEROPORTO MACEIO → STAUMMAQ ..., Simões Filho/BA, R$ 3.517,61)**. Duas causas-raiz independentes na mesma nota:
  - **Razão social fundida com a coluna vizinha.** A escolha do formato usava a ORDEM dos rótulos ("CLIENTE:" antes de "CÓDIGO:" ⇒ nome completo). Existe uma 3ª variante em que a ordem é essa **e mesmo assim** o nome vem quebrado em 2 fragmentos, com a coluna da direita intercalada — saía `—STAUMMAQ ... MOTORES E CÓDIGO: 01945295 "MAQUINAS LTDA INSC. ESTADUAL: 048137340`. O critério passou a ser se esses rótulos caíram dentro da janela `CLIENTE:`→`ENDEREÇO:`; caindo, são removidos com seus valores e os fragmentos remontam o nome.
  - **Rótulo `CEP/CID/UF:` ilegível derrubava cinco campos de uma vez.** O OCR do scan leu as barras como "I" (`CEPICID/UF:`) e o regex exigia as barras literais. Como esse rótulo ancora todo o bloco do tomador — e o CNPJ só é buscado numa janela depois dele — caíam juntos CNPJ (sentinela), endereço, bairro, município (fallback silencioso de Salvador, sendo a nota de Simões Filho) e CEP (zerado). Separadores agora toleram `/`, `I`, `|`, `1`, `l`.
  - **`<Intermediario>` fantasma nas faturas da Localiza**: a fatura não tem intermediário, mas o extrator do tomador rodava de novo para esse papel e o XML saía com o bloco duplicado. Guard `if is_intermediario: return None`, aplicado também ao `localiza_petrolina`, que tinha o defeito idêntico.
  - **Município do prestador nas filiais de aeroporto**: `RIO LARGO` (AL) acrescentada ao `IBGEResolver.KNOWN_CITIES` com o código `2707701`, confirmado na API oficial do IBGE — antes caía em Maceió (`2704302`), o que desloca `OrgaoGerador` e `MunicipioIncidencia`. O CEP impresso na nota (`51700-000`, faixa de Recife/PE) está errado no próprio documento, conferido na imagem; é preservado como impresso, não "corrigido".
  - **Endereço do prestador nas filiais de aeroporto**: `HALL AEROPORTO ZUMBI DOS PALMARES, S/N - AEROPORTO` não começa por prefixo de via (AV/RUA/ROD/...) e saía "Não informado". Fallback posicional (última linha antes do CEP no letterhead, descartando logotipo e e-mail colados) e `S/N` aceito como número, sem o que o bairro se perdia. Só roda quando o casamento por prefixo não acha nada.
  - Suíte: 603 → **622 testes**.
- **Páginas de cabeça para baixo ficavam presas na orientação errada e sumiam do resultado** (portão da busca de rotação do OCR, compartilhado por todos os layouts). `_ocr_page` corrige digitalização invertida testando 180°/90°/270°, mas a busca só rodava quando a leitura em 0° pontuava **exatamente zero** — e um único acerto acidental de palavra-chave no texto embaralhado bastava para travá-la. Achado no lote "STAUMMAQ - SCAN 3.pdf", cujas cinco páginas estão invertidas: as págs. 1/3/5 pontuaram 0 e foram corrigidas, mas as 2 e 4 pontuaram **1** (contra **82** e **84** a 180°) e ficaram presas; sem texto legível caíam em `LAYOUT_GENERICO` e `parse_multiple` descartava as páginas, então o lote saía com **1 nota em vez de 3**. O portão virou um limiar (`_OCR_ROTACAO_LIMIAR = 10`) e a aceitação de uma rotação ganhou margem de 3x — a rotação ERRADA também pode pontuar > 0 por coincidência (caso já documentado no fallback de PSM 6) e, sem margem, roubaria uma leitura 0° mediana porém correta. Com placar 0 a margem é inócua, então o comportamento já validado nas notas 160/201 fica idêntico. Suíte: 622 → **630 testes**.
- **Quatro campos errados nas NFS-e de Camaçari/BA escaneadas (`camacari_ba_scan_v3`)**, visíveis só depois que a correção do portão de rotação (acima) fez as notas 4497 e 4495 do lote "STAUMMAQ - SCAN 3.pdf" finalmente chegarem ao extrator:
  - **Bairro sempre "Não informado"** nas duas entidades — o campo estava **fixo** no `_extrair_entidade_camacari3`, embora a nota o imprima rotulado, dividindo a linha com o complemento (`Compl.: SALA 04 Bairro: CASCALHEIRA (ABRANTES)`), rótulo que o próprio extrator já usava como parada do complemento. Agora é lido, com três defesas tiradas de notas reais já na suíte: para no `Nº` que às vezes fecha a linha (`Balro: A Nº; 00022:`, nota 20335/PADUA), corta no primeiro token com minúscula (o bairro é impresso em caixa alta, então `(MONTE GORDO) cm` é sujeira da margem do scan) e descarta captura degenerada de menos de 3 alfanuméricos — mesma regra que o município já aplicava.
  - **CEP do prestador zerado na pág. 2**: o OCR leu o rótulo como `GEP: 42820512` e o padrão exigia `CEP`. O dado estava legível o tempo todo; quem falhava era o casamento do rótulo — mesma classe do `CEP/CID/UF` do `localiza_fatura`, um rótulo maltratado derrubando o dado que vem depois dele. Confirmado pela nota irmã (pág. 4), que imprime o rótulo certo e o **mesmo** CEP.
  - **Travessão colado no logradouro**: `Logradouro: — BA 522 - VIA CASCALHEIRA` ia com o traço para o XML — o `.strip(' .:|')` do `_campo` não cobre traço nem travessão. A limpeza nova é só à **esquerda**, então o `-` que separa `BA 522` de `VIA CASCALHEIRA` fica intacto.
  - **Código de autenticidade com um caractere a mais**: o cabeçalho é lido três vezes no fluxo escaneado; na nota 4497 duas leituras deram `BZz68G363T` e a terceira o impresso, `BZ68G363T`. Como o `.upper()` era aplicado **antes** da escolha, a primeira virava `BZZ68G363T` e era aceita de imediato. O desempate passou a preferir o candidato que já veio integralmente em caixa alta + dígitos (uma minúscula no meio denuncia leitura ruim); voto por maioria **não** serviria — aqui a leitura errada é que aparece duas vezes. Sem nenhum candidato limpo, mantém-se a primeira leitura, como antes.
  - ⚠️ **Teto de OCR assumido na nota 4495**: o código impresso é `ME5IPR77B`, mas as três leituras de página concordam em `MESIPR77B` (`S` no lugar do `5`) e um recorte dedicado varrendo 300/400/600 dpi × 2×/4× × PSM 6/7/8/13 × whitelist **não** produziu o valor impresso em nenhuma das 48 combinações. O extrator mantém o que leu em vez de escrever um valor que não consegue ler, e um teste fixa esse comportamento — o dia em que o OCR melhorar, ele avisa.
  - Suíte: 630 → **648 testes**, todos verdes (18 novos; com as 4 correções revertidas individualmente, 7 deles ficam vermelhos).

## [1.9.0] - 2026-09-14

### Adicionado

- **Layout `fatura_rotaexata` — RotaExata Software Ltda (Joinville/SC)**: fatura de locação de rastreadores veiculares e aparelhos de recepção, PDF digital, detectada pelo **CNPJ raiz** do emitente (`13.661.448`, casa qualquer filial futura) ou pelo nome junto do rótulo `FATURA:`. Nota real de referência: fatura nº **233530** → NEMUS - GESTAO E REQUALIFICACAO AMBIENTAL LTDA (Salvador/BA), **R$ 82,60**.
  - **Antes desta entrada o PDF não gerava nota nenhuma.** Esta é a única fatura da família de locação que **não imprime a frase "FATURA DE LOCAÇÃO"** — o título é só `FATURA:  Nº  233530`. Sem casar nem essa frase nem um CNPJ já cadastrado, caía em `generico`, e aí `parse_multiple` descarta a página como "Layout não reconhecido": o conversor terminava com *"O PDF ... parece ser baseado em imagem/scan ou vazio. Nenhuma nota pôde ser lida"*. Modo de falha silencioso — não havia XML errado para conferir, não havia XML.
  - Prestador **e** tomador extraídos dinamicamente (sem prestador hardcoded): neste template o pdfminer não embaralha rótulo e valor, cada campo sai na mesma linha do próprio rótulo. A única faceta "rótulos-depois-valores" é a grade do cabeçalho (`RF FATURA Nº`/`VALOR DA FATURA`/`EMISSÃO`, depois os três valores).
  - **Joinville/SC (IBGE `4209102`) acrescentada a `IBGEResolver.KNOWN_CITIES`** — sem isso o prestador cairia no fallback silencioso de Salvador/BA, erro que nesta nota passaria especialmente despercebido porque o **tomador** é de Salvador de verdade; isso desloca `OrgaoGerador` e `MunicipioIncidencia`, ou seja, o município de incidência do ISS.
  - Locação de bens móveis: base/alíquota/ISS zerados e item `0601`, convenção de toda a família (a própria nota invoca a LC 116/2003). **Retenções federais impressas só em percentual** (IRRF 4.80%, CSLL 1%, PIS 0.65%, COFINS 3%), sem nenhum valor em R$ — mantidas zeradas e sinalizadas em `avisos`, nunca calculadas a partir do percentual.
  - 28 testes novos em `tests/test_rotaexata_locacao_layout.py`, construídos sobre o texto real do PDF; **26 deles falham** com a detecção do layout desligada. Suíte: 575 → **603 testes**, todos verdes.

## [1.8.0] - 2026-09-11

### Adicionado

- **Distribuição em pasta (`--onedir`) e novo asset `nfse_converter_gui.zip`**: a GUI passa a ser publicada como pasta compactada, além do executável único. Motivo medido: em `--onefile` o executável extrai o bundle INTEIRO para `%TEMP%\_MEIxxxxx` **a cada inicialização** — eram 354 MB em 1228 arquivos —, e era isso que deixava a partida lenta "a ponto de não completar" (um `_MEI42562` da máquina do usuário parou em 73 MB de 354, extração interrompida no meio). Em onedir não há extração alguma: **janela visível em 3,4 s contra 12,0 s**, e **zero** pastas `_MEI` criadas por partida. O Release publica os **dois** assets — quem já tem instalação onefile continua se atualizando pelo `.exe` (também bem mais leve agora) e migra para a pasta baixando o `.zip` quando quiser; não há migração automática entre os formatos, porque trocar o formato de instalação por baixo do usuário mexeria na pasta dele sem aviso. O `auto_updater` escolhe o asset pelo formato da própria instalação (`is_onedir()`, que compara `sys._MEIPASS` com a pasta do executável).
- **`build.bat` com modos**: `build.bat` (GUI onedir + CLI, o do dia a dia), `build.bat release` (o anterior + `.zip` + `.exe` onefile, os dois assets do Release) e `build.bat limpo` (descarta o cache e refaz do zero).

### Corrigido

- **Executável 46% menor e partida 3,5× mais rápida — o `.venv` compartilhado ia inteiro para dentro do `.exe`**: os `.spec` eram regerados pelo `flet pack` com `excludes=[]`, então o PyInstaller empacotava tudo que alcançasse a partir dos imports. Como este `.venv` é compartilhado com outros trabalhos, iam junto scipy (67 MB), pandas, matplotlib, opencv, camelot, tabula, llama-index, openai, nibabel e nipype — nenhum deles importado por este projeto, cuja superfície de terceiros é só `PIL, flet, numpy, pdfminer, pydantic, pymupdf, pytesseract, requests` (conferido por grep). Com a lista de `excludes` centralizada em `tools/build_excludes.py`: **`.exe` de 170,7 MB → 101 MB**, bundle de **354 MB/1228 arquivos → 220 MB/987**, e a CLI (que não precisa do flet) em 61 MB. ⚠️ `numpy` FICA — é usado de verdade no desentorto da faixa do cabeçalho; `cryptography` FICA — o pdfminer.six precisa dela para PDF criptografado; e `libmpv-2.dll` (28 MB) FICA mesmo o app não usando `Video`/`Audio`, porque é dependência de LINK do `flet.exe` e sem ela o executável morre antes de qualquer janela ("a execução de código não pode continuar porque libmpv-2.dll não foi encontrado").
- **Atualização que falhava em silêncio e deixava o usuário na versão antiga achando que atualizou** (achado real 2026-09-11, v1.7.0): o `.bat` de troca tentava o `move /Y` **uma única vez**; com o aplicativo aberto numa segunda janela o Windows trava o `.exe` em execução, o `move` falhava, o `start` relançava o **binário velho** e nada avisava. Confirmado na máquina: `nfse_update_21636.bat` e `nfse_converter_gui_new_21636.exe` (170 MB) parados no `%TEMP%` e o `dist\nfse_converter_gui.exe` ainda com a data do build anterior. Agora são 10 tentativas espaçadas de 2 s e, se ainda assim não der, o motivo é registrado em `%TEMP%\nfse_update_falhou.log` e **mostrado na abertura seguinte do app**. A troca da pasta (onedir) renomeia a instalação atual antes de instalar a nova e a restaura se algo falhar no meio — nunca deixa o usuário sem aplicativo.
- **428 MB de pastas `_MEI*` órfãs acumuladas no `%TEMP%`** (32 delas, da mais antiga de 12/06 até o dia), com o aviso "Failed to remove temporary directory" aparecendo na tela durante a atualização: `apply_update_and_restart` encerrava o processo com `os._exit(0)` sem encerrar o `flet.exe` filho, que roda **de dentro** da pasta extraída e a mantinha travada, impedindo a limpeza do bootloader. Os filhos passam a ser encerrados antes da saída — enumerados pelo snapshot Toolhelp32 via `ctypes` (o `psutil` não está instalado e o `wmic` foi removido do Windows 11), **um a um e nunca a árvore inteira**, porque o próprio `.bat` de troca é filho deste processo e um `taskkill /T` no próprio PID levaria ele junto. Some na origem em onedir, que não extrai nada. O app também passa a limpar, ao abrir, restos de atualizações anteriores com mais de 24 h.
- **Build 3× mais lenta do que precisava, e refazendo trabalho jogado fora**: o `flet pack` (a) regerava o `.spec` a cada execução apontando o recurso de versão para um diretório temporário de nome **aleatório** — o que impedia qualquer reaproveitamento de cache e fazia o `.spec` aparecer eternamente modificado no `git status` — e (b) **apagava o `dist/` inteiro**, jogando fora o executável da CLI construído no passo anterior. Agora a build roda direto do PyInstaller sobre `.spec` fixos e versionados (o flet não precisa do `flet pack`: o pacote traz `flet/__pyinstaller/hook-flet.py`, descoberto sozinho), com o recurso de versão gerado em caminho estável por `tools/gen_version_info.py`. **177 s → ~60 s.** De quebra, as propriedades do arquivo passam a mostrar a versão do APLICATIVO; antes mostravam `0.21.2`, que era a versão do *flet*.
- **`build.bat` construía com o interpretador errado**: usava o `python` do PATH, cujo flet é 0.82.2, enquanto o `.venv` do projeto tem 0.21.2. O executável resultante abre e morre com `module 'flet.controls.material.icons' has no attribute 'SYSTEM_UPDATE'`. O `build.bat` agora exige `.venv\Scripts\python.exe` e **se recusa a rodar sem ele** — o interpretador é parte da configuração da build, já que é dele que o PyInstaller empacota as bibliotecas.
- **`hiddenimports=['pdfminer.six']`** era nome de distribuição do PyPI, não módulo importável: o PyInstaller logava `ERROR: Hidden import 'pdfminer.six' not found` em toda build. Corrigido para `pdfminer`.

## [1.7.0] - 2026-09-11

### Adicionado

- **Novo layout `fatura_neotagus` — Fatura de Locação da NEO-TAGUS INDUSTRIAL LTDA (CNPJ raiz `61.092.565`, Extrema/MG)**: pedido do usuário — "corrigir a extração do pdf em anexo, se não existir, criar um novo layout fatura de locação-neo-tagus" (nota real nº **5135**, controle `000005135/LOC`, → CONDOMINIO EDIFICIO TK TOWER/Salvador-BA, **R$ 1.190,34**). O documento caía em `fatura_locacao_generica`, detectado SÓ pela frase "FATURA DE LOCAÇÃO" — que está no título desta nota ("FATURA DE LOCAÇÃO DE MAQUINAS/EQUIPAMENTOS") —, mas cujos extratores são calibrados no template da LOC BAHIA, do qual **nenhuma âncora** existe aqui ("LOCADORA"/"LOCATÁRIO" → "Razão Social:"/"Dados do Cliente:"; "QTDE - DESCRIÇÃO" → "Item Produto Descrição Quantidade"; "NÚMERO:" → "Nº do Controle:"; "TOTAL: R$" → "Total:" impresso ANTES dos números). Resultado: valor `0,00`, prestador e tomador vazios e a discriminação saindo **"354 - EXTREMA - MG"** — um pedaço do CEP do PRÓPRIO prestador, pescado pelo regex de linha de item da LOC BAHIA, que casa o mesmo formato `<números> - <TEXTO>`. Detecção pelo **CNPJ RAIZ** do emitente (casa qualquer filial — esta nota é da `0022`), posicionada ANTES do check genérico. Corrigido junto um **defeito silencioso**: `<Numero>5135</Numero>` parecia certo, mas vinha do **nome do arquivo** ("NOTA 5135.pdf") — renomeando o PDF a nota saía `00000000`; agora o número vem do documento ("Nº do Controle: 000005135/LOC"). Prestador lido por índice no despejo "rótulos todos, depois valores todos" do pdfminer; tomador lido **por forma do conteúdo**, porque nesse bloco os valores saem FORA da ordem dos rótulos e o número sai colado no logradouro ("MAGALHAES NETO1856"). **Extrema/MG (IBGE `3125101`) hardcoded** — ausente de `IBGEResolver.KNOWN_CITIES`, cairia no fallback silencioso de Salvador/BA, deslocando junto `OrgaoGerador` e `MunicipioIncidencia`. Locação de bens móveis → base/alíquota/ISS em `0,00` e item `0601`, convenção de toda a família de faturas de locação. **12 testes novos** (`tests/test_neotagus_locacao_layout.py`) sobre o texto real do PDF, **10 deles vermelhos antes da correção**; suíte 538 → **550 verdes**.

- **Novo layout `nfcom_lotec_fibra` — NFCom Lotec Fibra LTDA (CNPJ 63.333.320/0001-83, Santa Teresinha/BA)**: pedido do usuário — "Crie plano de ação, para verificar novamente, para o layout lotec fibra, crie caso não exista" (nota real nº 17041, SINDICATO DOS DELEGADOS DE POLICIA DO ESTADO DA BAHIA, R$119,90). 3º emitente no mesmo template nacional NFCom (portal SVRS) já usado por `nfcom_salvador`/`nfcom_rlgr`, detectado pelo CNPJ específico deste emitente. Prestador FIXO (Santa Terezinha/BA, município ausente de `IBGEResolver.KNOWN_CITIES` — código IBGE `2928505` hardcoded diretamente, confirmado contra 2 fontes independentes, para não cair no fallback silencioso de Salvador/BA da mesma classe de bug já vista com Vinhedo/SP). Tomador dinâmico extraído do bloco "CLIENTE:"/"CNPJ:"/"ENDEREÇO:" com substituição de CNPJ de contraparte conhecida (SINDICATO → `73393696000137`, mesma entidade já confirmada na nota EBJ nº 4777, mesma técnica de BONI TRANSPORTES/GUARAJUBA SHOPPING). Recorte dedicado da coluna direita do cabeçalho corrige a Data de Emissão (leitura de página inteira lia "28" em vez do "29" real). Código de Verificação com os 2 primeiros dígitos (cUF) forçados para "29" (Bahia) quando a leitura de OCR não bate, validado por decodificação estrutural da própria chave. `BaseCalculo`/`Aliquota`/`ValorIss` propositalmente em 0,00 (tributado por ICMS, não ISS — mesma convenção de `nfcom_salvador`/`nfcom_rlgr`). Suíte 434→**443 verdes**; 9 testes novos em `tests/test_nfcom_lotec_fibra_layout_novo.py`.

### Corrigido

- **`danfse_nacional`: `ValorServicos` saindo com o valor LÍQUIDO (já retido), e ISS/alíquota zerados, no template WebISS pós-reforma (achado real 2026-09-11, nota nº 2026000130650, D-SAAS/Extrema-MG)**: reportado pelo usuário — "o valor correto é R$ 335,00, **sempre o valor dos serviços, antes das retenções ou descontos**". Nesta variante os valores vêm numa **grade posicional** de duas linhas (8 rótulos seguidos, depois as 8 células), e os fallbacks por proximidade pescavam a célula errada: `ValorServicos` 328,30 (líquido, após R$ 6,70 de ISS retido) em vez de **335,00**, `ValorIss` 335,00 (o valor dos serviços!) em vez de 6,70, e `Aliquota` 0 em vez de 0,02. Corrigido com leitura **por posição** da sequência contígua dos 8 rótulos ("Valor dos Serviços (R$" … "ISS Retido (R$"), tolerando o `)` que o layout não fecha no último rótulo de cada linha; células `-`/`*` viram ausência, não zero. A variante de Aracaju, cujos rótulos vêm **intercalados** com os valores, continua na rota de proximidade — o portão exige a sequência contígua. IBS/CBS da 2ª linha são lidos mas descartados (não existem na ABRASF 2.01); dela só o Valor Líquido é aproveitado. **7 testes novos** (`tests/test_danfse_nacional_webiss_grade_posicional_extrema.py`), **5 vermelhos antes da correção** — um deles muta apenas a célula do Valor Líquido, travando a regra do usuário; suíte 515 → 522.

- **`barreiras_ba` — lote INTEIRO (6 de 6 notas) saindo com valor 0,00 porque o OCR descarta uma FAIXA HORIZONTAL inteira de cada página, e 4 colaterais causados por uma assimetria na detecção de layout (lote real "NF VERIFICACAO" 08/2026, nota reportada nº 4059, BETINA SANTROVITSCH POSSATO/OBRAMAX LOCAÇÃO -> SÃO PEDRO CONSTRUTORA, R$480,00)**: pedido do usuário — "Criar um plano de ação, para extrair o valor correto da nota fiscal", com o XML quebrado (`<ValorServicos>0.00</ValorServicos>` em todos os campos) e o PDF em anexo; depois "Pode corrigir, e inclua os 4 colaterais". **Causa-raiz dos valores:** a segmentação automática do Tesseract joga fora uma faixa horizontal inteira de cada página — a faixa que contém a discriminação dos serviços, a OBSERVAÇÃO, a GRADE PRINCIPAL DE VALORES, o VALOR LÍQUIDO e, em parte das notas, a própria linha "Chave de acesso". O texto da pág. 3 pula direto de "DISCRIMINAÇÃO DOS SERVIÇOS" para "DEMONSTRATIVO DOS TRIBUTOS FEDERAIS": não existe nenhum "480" nem "VALOR SERVIÇO" ali, e `_extrair_valores` cai no fallback zero — não é regex errado, é texto ausente. Mesma família das notas 201/160 de Camaçari, numa variante que o portão existente **não** cobria: lá a página falhava por COMPLETO (`score_angle_0 == 0`) e o fallback generalizado de PSM 6 disparava; aqui o resto da página lê bem, a pontuação é alta e a perda é PARCIAL, então aquele portão nunca abria. Corrigido com um re-OCR de página inteira em zoom 5 + PSM 6 (`_ocr_valores_barreiras`) atrás de um portão por CONTEÚDO (`_grade_barreiras_completa`: linha de cabeçalho da grade seguida de uma linha com 5+ números — o rótulo "Valor Serviço" sozinho **não** serve de sinal, porque a mesma expressão aparece na frase de rodapé "(Valor Líquido = Valor Serviço - INSS - ...)", que sobrevive ao OCR nas 6 notas justamente quando a grade não sobrevive). Do re-OCR só a **fatia** da grade é costurada de volta, e **dentro** do corpo da nota (antes do "DEMONSTRATIVO DOS TRIBUTOS FEDERAIS"): prependar a página inteira duplica os marcadores que `is_new_invoice` usa e reparticiona a página — medido, o lote caiu de 6 para 5 notas e 2 delas voltaram a zerar. Pelo mesmo motivo a chave e a data vão como marcadores SINTÉTICOS (`BARR_CHAVE:`, `BARR_DATA_FG:`, `BARR_COD:`, técnica já usada em `LFV3_NUMERO:` de Lauro de Freitas): o rótulo real "Chave de acesso" é ao mesmo tempo separador de bloco em `parse_multiple` **e** marca de detecção do `LAYOUT_NACIONAL`, então reintroduzi-lo fazia a própria fatia virar um bloco órfão detectado como DANFSe Nacional. **Causa-raiz dos 4 colaterais (uma só):** `_detect_layout` aceitava apenas o rótulo "Data Fato Gerador" como marca de Barreiras, enquanto `_detect_layout_page` já aceitava também "MUNICIPIO DE BARREIRAS" — assimetria entre os dois detectores. Esse rótulo sobrevive ao OCR em só 2 das 6 notas; nas outras 4, sem marca municipal casando, a nota caía no check LARGO de DANFSe Nacional ("Chave de Acesso"), porque este portal municipal é integrado ao ambiente nacional e imprime "Chave de acesso Ambiente de Dados Nacional" — **é o anti-padrão de detecção por marca de plataforma compartilhada já documentado neste projeto, numa instância nova**. Detectadas como Portal Nacional, essas 4 notas eram parseadas inteiras pelo layout errado, o que produzia os 4 colaterais de uma vez: (1) **`Numero`** saindo `00000000` (pág. 3, onde a linha da chave também caiu na faixa descartada) ou com os 13 dígitos crus do campo nNFSe (`2600000004059`) — o `nNFSe` desta prefeitura **não** é o sequencial zero-preenchido do DANFSe Nacional, onde `chave[23:36].lstrip("0")` acerta: ela prefixa o ANO ("26"), então não sobra zero à esquerda e o número real vem DEPOIS da corrida de zeros (conferido contra o valor impresso nas 2 notas cuja célula o OCR leu, e corroborado pelo lote — prestadores repetidos têm números consecutivos, BETINA 4059/4060 e ATRIO 882/883); (2) **`DataEmissao`** gravando o INSTANTE DA CONVERSÃO (`datetime.now()`) para notas de 08/2026, sem aviso nenhum — agora ano e mês vêm das posições 37-40 da chave (AAMM), imunes ao OCR, e só o DIA depende do cabeçalho; (3) **`CodigoVerificacao`** inconsistente dentro do mesmo lote (4 notas com a chave de 50 dígitos, 2 com o código curto mal lido) — o código curto de 9 caracteres é irrecuperável nestes scans (seis tentativas independentes, seis respostas diferentes, todas erradas), então a regra passou a ser: duas leituras independentes que DISCORDAM devolvem a chave, que é estruturalmente verificável, e uma leitura válida (ou duas concordantes) mantém o código curto — a nota nº 1162, cujo "ACC8CDE89" sai limpo, segue com o código curto; um token de dígitos PUROS é rejeitado por formato mesmo com as duas leituras concordando (achado real na pág. 1, "565734070"); (4) **município de prestador e tomador** caindo no fallback de Salvador (2927408) — este template não tem rótulo "Cidade"/"Município" e imprime a linha como "LAURO DE FREITAS - BA - CEP: 42708720", agora ancorada por padrão próprio (tomador 2919207; prestador default Barreiras 2903201, que a nota declara em "Local de Prestação/Recolhimento"). Corrigidos junto, porque a mesma faixa perdida os expõe: **vazamento de bloco quando o cabeçalho de seção "TOMADOR" é comido pelo OCR** (pág. 1) — sem ele o bloco do tomador caía no fallback delimitado pelo rótulo do PRESTADOR e as duas entidades saíam idênticas; ancorado na 2ª linha "Razão Social:" (mesma família do vazamento já documentado em Cuiabá), com o limite SIMÉTRICO no bloco do prestador, que senão se estendia por cima do tomador e herdava a cidade dele; e a **razão social contaminada pela linha seguinte** ("SAO PEDRO CONSTRUTORA LTDA te 2d ta dd EL"), corrigida com releitura limitada à linha. Na grade, a coluna de percentual é impressa com PONTO decimal ("3.33") e as monetárias com vírgula — convenção do próprio documento, confirmada na imagem — e quando o OCR trunca a alíquota (pág. 6: "4" no lugar de "4.11", sobrando 5 números em vez de 6) o token ambíguo é desempatado pela plausibilidade (o ISS é limitado a 5% pela LC 116/2003, art. 8º, II, e a própria nota imprime "INFORMAR A ALÍQUOTA ENTRE 2 A 5%") e a alíquota é derivada de `ISS / base`. **A derivação só entra quando há DIVERGÊNCIA**, nunca para "preencher" um zero: alíquota 0 com ISS 0 é dado REAL nas notas do Simples deste portal (págs. 1 e 2, confirmado na imagem em zoom 9x), e completá-lo seria fabricar imposto. Limites registrados e não escondidos: o DIA da emissão só é recuperável em 2 das 6 notas — nas outras 4 o resultado é o 1º dia do mês CORRETO (o da chave) **com** o aviso "Data de emissão não encontrada", em vez da data da conversão em silêncio; um recorte dedicado só para o dia foi medido como capaz de alcançar 5 das 6 páginas, mas **não** foi implementado porque o PDF de origem saiu da pasta de rede durante o próprio trabalho e não seria possível verificá-lo (código de OCR que não se consegue conferir contra a imagem não entra); e a razão social do prestador da pág. 2 fica em "Prestador Não Identificado", porque a linha do rótulo dela não sobrevive a nenhuma das leituras. Suíte 482→**515 verdes**; 33 testes novos em `tests/test_barreiras_grade_faixa_descartada_nf_verificacao.py` (texto OCR REAL das págs. 1, 3 e 6, já com a fatia costurada como `_ocr_page` faz em produção), dos quais **26 falham contra o código pré-correção** (verificado revertendo `pdf_extractor.py` e rodando o arquivo). Sem constante `LAYOUT_` nova: contagem de layouts inalterada (54 específicos / 55 total). Nenhuma regressão em `test_barreiras_layout.py` (nota nº 23) nem em `test_barreiras_valores_grade_locacao.py` (nota nº 1162, variante "rótulos-depois-valores" do mesmo portal).
- **`barreiras_ba`: página inteira ilegível porque o PDF já vinha com uma camada de OCR DE TERCEIROS embutida (achado real 2026-09-11, `nfsss.pdf` pág. 4, nota nº 8965, CHAVES LOCAÇÕES → SÃO PEDRO CONSTRUTORA, R$ 196,00)**: reportado pelo usuário como "continuou gerando xml errado, a página 4". O PDF é escaneado, mas chega com um texto embutido produzido por OCR de outra ferramenta — longo o bastante para o portão `len(full_text) < 200 or not has_keywords` concluir que "há texto utilizável", então o **nosso Tesseract nunca roda** e cada marcador é lido de um texto corrompido ("IIUNICIPIO", "DIIIFMoGlradlf", "Razio Soclal:"). O XML saía com `Numero` `00000000`, todos os valores `0,00`, `DataEmissao` = instante da conversão e o **prestador preenchido com o CNPJ do tomador**. Medido antes de trocar a fonte (`_score_ocr_text`: camada embutida 44, nosso OCR 18), as duas leituras são **complementares** — a camada tem a grade de valores, o nosso OCR tem os rótulos de entidade limpos —, então cada uma é usada para o que lê bem, costuradas por **marcadores sintéticos** (`BARR_PREST_*`, `BARR_TOM_*`, `BARR_NUMERO:`, `BARR_DATA_FG:`) em vez de anexar texto solto (a 1ª tentativa inverteu prestador e tomador, porque a camada de terceiros embaralha os próprios cabeçalhos de seção). Número e data só saem quando **duas fontes independentes** concordam (recorte dedicado do cabeçalho em zoom 5/PSM 6 × camada embutida). A pág. 3 do mesmo lote melhorou de carona (prestador identificado, data 01/08 → 24/08). O `CodigoVerificacao` permanece `XXXX-XXXX` + aviso — três leituras, três respostas, nenhuma confiável. **16 testes novos** (`tests/test_barreiras_camada_ocr_terceiros_nfsss_pag4.py`), **10 vermelhos antes da correção**; suíte 522 → 538.

- **`cuiaba_issnet` — número da nota caindo no sentinela `00000000` porque o dígito de "sangria" da linha de baixo destruía o consenso do recorte dedicado (nota real nº 308, FB PISOS E REVESTIMENTOS, CNPJ 36.776.200/0001-88 -> SÃO PEDRO CONSTRUTORA LTDA, R$1.368,00, template pós-reforma tributária)**: pedido do usuário — "Criar um plano de ação, para extração do número da nota. Layout cuiabá", com o XML quebrado (`<Numero>00000000</Numero>`) em anexo. Esta nota é do template NOVO de Cuiabá (traz "TRIBUTAÇÃO NACIONAL", "IMPOSTO E CONTRIBUIÇÃO SOBRE BENS E SERVIÇOS - IBS/CBS" e os campos "Número/Série da DPS"), o que muda o cabeçalho o bastante para derrubar as DUAS âncoras de texto de `_extrair_numero`: o rótulo limpo não casa porque o OCR funde as 3 colunas do cabeçalho e joga o valor colado ao fim da linha do letterhead ("Prefeitura Municipal de Cuiabá MT 208" — e ali o OCR lê 208, não o 308 real), e a âncora de scan degradado espera "Dados do Prestador de Serviço" enquanto este template diz "IDENTIFICAÇÃO DO PRESTADOR". Sobra o recorte dedicado da caixa (`_ocr_numero_box_cuiaba`), e o defeito estava exatamente ali: o recorte LIA o número certo nos 3 zooms sob PSM 6 (`"308"`, `"308\n2"`, `"308\n5"`), mas o consenso comparava a **string inteira** de cada leitura — o dígito da linha de baixo que sangra para dentro do recorte (e que varia com o zoom, porque é geometria do corte, não tinta) transformava 3 leituras CONCORDANTES em 3 votos distintos de 1 voto cada, `contagem < 2` reprovava e um número perfeitamente legível caía no fallback honesto. Corrigido normalizando cada voto para o **primeiro grupo de dígitos** da leitura e exigindo que os votos concordantes venham de **zooms DIFERENTES** — a segunda condição existe para que a normalização não fabrique consenso falso: a sangria varia com o zoom e um dígito real não, e dois PSM no mesmo zoom leem o MESMO bitmap (concordarem é evidência fraca). Sem zooms distintos a função devolve vazio e a extração segue para o sentinela + aviso, que é o comportamento correto no limite conhecido da nota GMS FLATS pág. 17 (número irrecuperável em qualquer combinação testada, registrado na `v1.6.0`) — dado ausente, nunca dado errado. Descoberto ao escrever os testes: a lógica de votação não tinha **cobertura nenhuma** (o teste pré-existente `test_cuiaba_issnet_numero_recut.py` faz mock do texto já prependado e nunca exercita a votação); agora tem 5 testes diretos, com os votos reais desta nota. Achado ao verificar a nota inteira: o mesmo template pós-reforma tinha mudado de lugar/formato outros **3 campos**, todos corrigidos na sequência a pedido do usuário ("Pode corrigir o item: 1,2 e 3"), cada um com portão na marca do template novo — nenhuma das 8 notas Cuiabá já cobertas tem essas marcas, então nada regride. (1) **`CodigoVerificacao` no sentinela `XXXX-XXXX` com aviso**: o "Código de Autenticidade" virou uma corrida de **57 dígitos puros** e a busca do template antigo exige um token alfanumérico MISTO de 7-10 caracteres (`3B3DC3576`), então nada casava — agora vai para o XML como impresso, mesma decisão já tomada para a chave do `LAYOUT_NACIONAL`. Não é a Chave de Acesso nacional de 50 dígitos: os 7 primeiros dígitos ("5103340") não são o IBGE de Cuiabá (5103403), é código próprio da plataforma, então nada dele é decodificado. Como o risco desta leitura é o OCR errar a CONTAGEM de uma corrida de zeros (o código tem várias), só é aceito quando as **2 ocorrências concordam** — `_ocr_page` concatena 2 passes de OCR da mesma página, e divergência entre eles devolve o campo ao sentinela + aviso; uma corrida maior que 60 dígitos (OCR colando o código à data vizinha) também não casa, em vez de ser truncada num valor errado. Leitura confirmada na imagem em zoom 16x, dígito a dígito, em 3 recortes sobrepostos. (2) **`ItemListaServico` genérico `03115` e `CodigoCnae` `0000000`**: a grade de atividade do template antigo (alíquota | item LC116 | NBS de 9 dígitos) não existe mais — a seção "DADOS DO SERVIÇO PRESTADO" traz "Cód. Trib. Nacional: 07.06.02" (item 07.06 da LC 116/2003, instalação de revestimentos, exatamente o serviço desta nota) → `0706`, ancorado no RÓTULO e não no formato, para não pescar o rótulo vizinho "NBS: 07.06.02.00" que repete o código com um 4º par. O `CodigoCnae` era **hardcoded** como `0000000` no transformer, para todos os layouts; passou a ser um campo opcional do modelo (`codigo_cnae`), extraído de "Atividade Municipal: 14330-4/05 Aplicação de revestimentos e de resinas" → `4330405`. O rótulo é MUNICIPAL e o código traz um dígito de prefixo do município à esquerda da subclasse (confirmado na imagem em zoom 10x — não é ruído de OCR), então usamos os 4 dígitos imediatamente antes do "-", leitura que se autoconfirma pela descrição impressa ao lado (a descrição oficial da subclasse 4330-4/05). A mudança no transformer é aditiva: sem `codigo_cnae` extraído, segue o `0000000` de sempre — é o que mantém os outros 54 layouts intactos. (3) **Endereço com os componentes trocados de campo**: o endereço deixou de ter um rótulo por componente e virou UMA linha de texto livre separada por vírgulas, com o número marcado por "nº" em posição VARIÁVEL ("Rua M4, Quadra 155, nº N2" no prestador; "Av. Praia de Pajussara, nº 554, Quadra 28, Lote 09" no tomador) — a quebra genérica por vírgula tratava o 2º segmento como número e o 3º como bairro, produzindo `Numero="Quadra 155"`/`Bairro="nº N2"` e `Numero="nº 554"`/`Bairro="Quadra 28"`. Agora o número é o segmento marcado por "nº" onde quer que ele esteja, o 1º segmento é o logradouro e os demais formam o complemento; o bairro **não é impresso** neste template e vai para o sentinela "Não informado" em vez de receber um pedaço do endereço. Ressalva registrada: o bloco `<Endereco>` deste transformer não tem tag `Complemento`, então "Quadra 155" fica no modelo mas não chega ao XML — mesma situação do `LAYOUT_SALVADOR`, que já preenche `complemento` sabendo disso. Limites que seguem conhecidos e NÃO alterados: `CodigoTributacaoMunicipio` continua espelhando o `ItemListaServico` (comportamento compartilhado por todos os layouts) apesar de esta nota imprimir um código de atividade municipal próprio, e o template ANTIGO de Cuiabá imprime uma coluna "Cód. CNAÉ" que segue sem extração. Suíte 465→**482 verdes**; 17 testes novos em `tests/test_cuiaba_numero_consenso_voto_sangria.py`, dos quais 8 falham contra o código pré-correção (verificado revertendo as 3 fontes e rodando o arquivo).
- **`telecom_comunicacao` — Valor dos Serviços zerado pela 3ª vez por uma causa DIFERENTE, e tomador saindo como linha de ruído do formulário (nota real nº 19026, "Grupo FeF"/F&F Comunicações, CNPJ 13.398.812/0001-89 -> Guarajuba Shopping Ltda, R$119,90 — 6º PDF do lote Guarajuba Shopping, pág. 1 de 4)**: reportado pelo usuário — "o valor foi extraído zerado, o correto é R$ 119,90", indicando que a coluna VALOR UNIT (R$) da tabela de itens soma o VALOR TOTAL NF. Dois bugs, distintos dos já corrigidos nas notas nº 31696 e nº 22570: (1) nem "TOTAL A PAGAR" (caixa ilegível nas 2 tentativas de recorte, mesmo problema da 22570) nem o fallback "VALOR TOTAL NF" (introduzido justamente para a 22570) funcionam aqui — desta vez o próprio rótulo sai com a palavra "TOTAL" comida pelo OCR (`"VALOR O UNF 119,90"`), quebrando a busca pela palavra literal; corrigido com uma 3ª camada de fallback que soma unitário × quantidade de cada linha de item da tabela "ITENS DA FATURA" (ancorada em `"UN | <qtd> <valor unitário>"`, cujas linhas sobrevivem limpas mesmo quando os rótulos-resumo não), confirmado contra o documento: 23,98 + 95,92 = 119,90; (2) o tomador saía como `"TT CONSULTE PELA CHAVE DE ACESSO EM:"` em vez de "Guarajuba Shopping Ltda", por causa dupla — o nome do tomador sai colado na MESMA linha do cabeçalho da nota (`"Guarajuba Shopping Ltda [E] NOTA FISCAL Nº 19026 - SÉRIE: 1"`) e a guarda antiga descartava qualquer linha com dígito, jogando fora a linha inteira por causa do número da nota mais adiante nela (corrigido extraindo só a parte ANTES do marcador "NOTA FISCAL Nº"), e uma linha de furniture do formulário sem nenhum dígito satisfazia a heurística solta e era escolhida antes de a busca reversa alcançar o nome real (corrigido com lista de rejeição das instruções fixas da nota: chave de acesso, protocolo de autorização, data de emissão, área do contribuinte — texto impresso do formulário, nunca nome de empresa). Suíte 460→**465 verdes**; 5 testes novos em `tests/test_telecom_comunicacao_nota19026_grupo_fef.py`.
- **`salvador_ba` — PRESTADOR herdando os dados do TOMADOR quando o próprio rótulo é corrompido, e valor da nota truncado por "/" espúrio (nota real nº 00000080, RISERIO ARQUITETURA E ENGENHARIA LTDA -> UFFICIO - COMÉRCIO, REPRESENTAÇÃO, INSTALAÇÃO E MONTAGEM DE MÓVEIS LTDA.ME, R$18.080,73)**: reportado pelo usuário como "extração do tomador de serviços incorreto" — o sintoma (Prestador e Tomador com os MESMOS dados) era real, mas o lado quebrado era o **oposto** do relato. Três causas independentes: (1) o rótulo "PRESTADOR DE SERVIÇOS" saiu `"PRESPADOR,DESSERVIÇOS"` (T→P, fora de qualquer tolerância existente), `m_bloco` não casava e o fallback antigo usava o **documento inteiro** como bloco de busca — como o CNPJ do prestador também saiu ilegível (`"35457.695) 02"`, sem "/"), só sobrava o CNPJ do TOMADOR para encontrar; corrigido delimitando o fallback pelo rótulo da OUTRA entidade ("TOMADOR DE SERVIÇOS", íntegro no OCR), o que **restringe** o escopo já usado e nunca amplia, mais um 2º guard que impede o "chute" de último recurso (1º CNPJ do documento) de reintroduzir a mesma contaminação — o CNPJ do prestador é irrecuperável por regex nesta nota (a pontuação foi destruída, não só dígitos), então o resultado correto é sentinela + aviso, dado ausente e não dado errado; (2) `"VALOR TOTAL DA NOTA = R$18.080,73"` saiu `"R$18/080,73"` e a classe `[\d\.,]+` da captura parava em `"18"`, derrubando Valor dos Serviços/Base de Cálculo para 18,00 — corrigido tolerando "/" como separador espúrio nessa captura específica do `LAYOUT_SALVADOR`, normalizado para "." antes de `_parse_valor` ("/" nunca aparece de verdade num valor monetário); (3) o cabeçalho da grade de 5 valores exigia "Valor do ISS" (saiu `"Vajócdo ISS"`) e "Crédito" (saiu `"Cito"`) — corrigido ancorando na sigla curta "ISS" e dispensando "Crédito" por extenso. A correção (3) **não** recupera os valores desta nota: a linha de valores está corrompida demais (só 4 dos 5 números sobrevivem; o ISS real, R$904,04, não sobra em nenhuma forma numérica) — por decisão do usuário, Alíquota/Valor do ISS ficam zerados com aviso explícito (`_salvador_aliquota_iss_zerada`) em vez de receberem valor sem lastro no documento. Suíte 454→**460 verdes**; 6 testes novos em `tests/test_salvador_prestador_contaminado_tomador_valor_truncado_ufficio.py`.
- **DANFE Estadual (NF-e Modelo 55) escaneado saindo como NFS-e de serviço/ISS — detecção derrubada por uma frase quebrada em duas linhas (nota real nº 215624, série 7, EDITORA WMF MARTINS FONTES LTDA -> SINDICATO DOS DELEGADOS DE POLICIA DO ESTADO DA BAHIA, R$124,70)**: pedido do usuário — "Crie um plano de ação, para conversão de notas icms (DANFE), seguindo o padrão domínio", com o XML quebrado em anexo. Toda a infraestrutura DANFE já existia (`LAYOUT_DANFE_PRODUTO`, `NfeProduto`, parsers digital e OCR, 4 recortes, `NfeProdutoTransformer`) — ela simplesmente nunca era alcançada: a marca `portal nacional da NF-e` era exigida como frase **contígua** e nesta nota o OCR a quebra entre duas linhas ("...portal nacional da\nNF-e www.nfe.fazenda.gov.br/portal..."). A condição estava duplicada **inline em 3 lugares** (`_detect_layout`, `_detect_layout_page` e o portão dos recortes em `_ocr_page`), então as 3 falhavam juntas, o objeto saía do tipo errado e `_pick_transformer` escolhia o `NfeTransformer` de disfarce — produzindo um XML de serviço com chave de acesso fabricada para uma nota de mercadoria. Corrigido extraindo a condição para a constante `DANFE_PORTAL_NFE_PATTERN` (usada nos 3 portões, tolerando a quebra e aceitando a URL isolada como marca alternativa). Com os recortes voltando a rodar, apareceu o 2º defeito: as frações fixas de Y calibradas na nota nº 764 caem sobre o bloco TRANSPORTADOR/VOLUMES desta nota (a grade "CÁLCULO DO IMPOSTO" da WMF é mais curta e desloca a tabela de itens para baixo), devolvendo só rótulos de coluna — corrigido com `_ocr_recut_danfe_produto_ancorado`, que localiza a faixa pelo rótulo impresso ("DADOS DO(S) PRODUTOS") via caixas de palavra do OCR em vez de calibrar fração por emitente, e que só entra em ação quando o recorte de fração fixa não devolve as colunas (a nota nº 764 segue lendo exatamente o mesmo recorte de antes). Também nesta nota: separador decimal **ponto** ("107.80", não o padrão pt-BR com vírgula, que `_num` lia como 10.780,00) — a grade só é aceita quando fecha a identidade contábil produtos + frete + seguro + outras - desconto + IPI == total da nota; prefixo do código de cliente do marketplace colado na razão social do destinatário ("(201474566-SINDICATO DOS..."); e o **código do produto validado pelo dígito verificador do ISBN-13** (mod-10), que desempata as duas leituras de OCR — a de página inteira reprova (`9766556754772`) e a do recorte aprova (`9786556754772`, a impressa), em vez de confiar numa delas. Bloco do transportador passou a ser extraído do texto fundido pelo OCR (MAGALU ENTREGAS, CNPJ 47.960.950/0001-21, IE ISENTO/SP, 1 CAIXAS, peso bruto 0,300), com a modalidade do frete lida da **palavra** ao lado da caixa ("Emitente" -> `modFrete` 0), já que o dígito não sobrevive à leitura de página inteira. Limites assumidos e sinalizados por aviso em vez de estimados: **peso líquido** cortado fisicamente na margem do scan ("0.30" + caractere partido) sai omitido (`vol/pesoL` é opcional no XML), e `endereco`/`municipio` do transportador ficam de fora porque o OCR cola as duas caixas numa linha só sem separador de fronteira (nenhum dos dois é emitido no XML). Achado colateral, de tabela: o DANFE imprime **origem + CST concatenados** numa coluna só ("041" = origem 0 + CST 41) e o transformer emitia os 3 dígitos direto em `<CST>`, que a Domínio rejeita — corrigido dividindo em `orig` (1 dígito) e `CST` (2), o que também conserta a nota nº 764, que saía com `<CST>000</CST>`. Leitura fiscal desta nota: livro imune (CF/88 art. 150, VI, "d", NCM 49019900, imunidade registrada nas informações complementares) -> grupo **ICMS40**, CST 41, base e valor zerados; BC/ICMS em branco no papel é dado REAL, não falha de leitura. Suíte 443→**454 verdes**; 11 testes novos em `tests/test_danfe_produto_escaneado_nota215624.py`.
- **`camacari_ba_scan_v3` — grade de valores com 2 células corrompidas simultaneamente derrubando o Valor dos Serviços a zero (nota real nº 159, AVANÇO GESTÃO E ADMINISTRAÇÃO LTDA -> GUARAJUBA SHOPPING LTDA, R$9.194,55)**: pedido do usuário (revisão do layout Camaçari num lote de 30 notas onde Guarajuba Shopping, CNPJ 24.890.395/0001-03, é sempre a tomadora). A célula "Valor dos Serviços (R$)" saiu 100% ilegível ("RE pone") e a "Base de Cálculo (=)" perdeu o dígito de milhar ("0194," em vez de "9.194,55"), o que gerava uma alíquota derivada de ISS/Base acima de 100% (≈206%) — sinal inequívoco de célula corrompida. Corrigido com fallback do Valor dos Serviços para o Valor Líquido da Nota (lido limpo na mesma grade), recálculo da Base de Cálculo quando o valor capturado é implausível (menor que Valor dos Serviços - Deduções, não só zero como antes), e uma nova guarda que zera Alíquota/Valor do ISS + aviso quando a alíquota ultrapassar 100% (decisão do usuário: "dado errado é pior que dado ausente"; nesta nota a guarda não precisou disparar, pois a alíquota derivada após a correção da Base já é plausível, ≈4,35%). Achado colateral: o CNPJ do prestador (AVANÇO GESTÃO, `59.132,742/0001-13`) usa vírgula como separador de grupo, não tolerada pelos regex de `_extrair_entidade_camacari2`/`_extrair_entidade_camacari3` — caía no sentinela `00000000000000` mesmo com CNPJ legível e de checksum válido; corrigido tolerando vírgula nos dois regex. Suíte 369→370 verdes; teste novo em `tests/test_camacari3_grade_valores_ilegivel_guarajuba.py`.
- **CNPJ do tomador GUARAJUBA SHOPPING LTDA com 1 dígito trocado pelo OCR, layout `salvador_ba` (nota real nº 00054394, M ESCRITA COMÉRCIO E SERVIÇOS LTDA -> GUARAJUBA SHOPPING LTDA, R$391,57)**: o OCR deste scan lê consistentemente "24.890.396/0001-03" em vez do real "24.890.395/0001-03" (confirmado pelo usuário) — um único dígito trocado que reprova o dígito verificador, sem nenhum outro CNPJ válido sobrando no documento para o fallback de "scavenge" usar, então o tomador caía no sentinela `00000000000100`. Corrigido em `_extrair_entidade` pela mesma técnica já usada para BONI TRANSPORTES: substitui pelo CNPJ real confirmado apenas quando o CNPJ extraído já reprova o checksum E a razão social bate com esta contraparte recorrente (tomadora fixa num lote de 30 notas em municípios/layouts diferentes), nunca mascarando um CNPJ genuinamente diferente de outra empresa. Suíte 370→377 verdes; testes novos em `tests/test_salvador_guarajuba_shopping_tomador_cnpj_digito.py` e `tests/test_guarajuba_shopping_cnpj_contraparte_conhecida.py`.
- **`camacari_ba_scan_v3`/`camacari_ba_scan` — Valor dos Serviços plausível-porém-errado (2º PDF do lote Guarajuba Shopping, nota real nº 148, AVANÇO GESTÃO E ADMINISTRAÇÃO LTDA -> GUARAJUBA SHOPPING LTDA)**: reportado pelo usuário — "o valor da nota está errado, o correto é R$ 42.892,92", apontando os dois lugares onde o valor aparece no PDF (VALOR TOTAL da linha do item x Valor dos Serviços da grade). A célula "Valor dos Serviços (R$)" saiu "42.892,8" — diferente de todos os achados anteriores deste layout (sempre célula vazia/ilegível), aqui o número é SINTATICAMENTE válido, só com o último dígito de centavo perdido pelo OCR ("9" de "92" comido), então nenhuma guarda existente detectava o erro. A linha do item em "DISCRIMINAÇÃO DOS SERVIÇOS" está limpa e correta ("42.892,92" repetido 2x, unitário e total). Corrigido promovendo o total da linha do item a fonte PRIMÁRIA do Valor dos Serviços nos 3 layouts Camaçari que compartilham esta função de extração (`LAYOUT_CAMACARI`/`_2`/`_3`) — a célula da grade só é usada como fallback quando a linha do item não é encontrada; validado sem regressão contra os 8 fixtures de teste já existentes deste layout, onde item e grade sempre concordam. Achados colaterais na mesma nota: "Valor Líquido da Nota (=)" tinha um "." de ruído colado antes do número, fazendo o regex capturar só o ponto (nenhum dígito) e gravar `ValorLiquidoNfse=0.00` em vez do valor real — corrigido tratando uma captura sem nenhum dígito como não encontrada; e o rótulo do tomador saiu "Nome/Razão Soclal:" ("i" lido como "l"), derrubando a razão social para "Tomador Não Identificado" apesar do CNPJ já sair correto — corrigido tolerando "Soclal" como variante de "Social" nos extratores `_extrair_entidade_camacari2`/`_extrair_entidade_camacari3`. Suíte 377→383 verdes; 6 testes novos em `tests/test_camacari3_valor_dos_servicos_truncado_guarajuba.py`.
- **3º PDF do lote Guarajuba Shopping — página inteira ausente do resultado, não um bug de extração** (pedido do usuário: "verificar o motivo da página 5 não está sendo extraída", nota real nº 201, AVANÇO GESTÃO E ADMINISTRAÇÃO LTDA -> GUARAJUBA MALLS S/A, R$12.694,47): a imagem da página estava 100% legível, mas o PSM automático do Tesseract (modo padrão de `_ocr_page`) não encontrava NENHUM bloco de texto na página, em NENHUMA das 4 rotações testadas — 0 caracteres, derrubando a nota inteira do resultado sem erro nenhum. `--psm 6` (bloco único de texto) lê a página inteira corretamente. Este mesmo fallback pontuado já existia em `_ocr_page`, mas só disparava para o layout Salvador (achado da nota BDP 00024910, `v1.5.0`); generalizado para disparar em QUALQUER layout sempre que as 4 rotações com PSM automático já fracassaram por completo (`best_score == 0`) — zero risco de regressão, pois só roda no caso em que a página já sairia 100% vazia de qualquer forma. Recuperar a página expôs 3 corrupções novas, introduzidas pelo próprio PSM 6 (que reordena colunas de forma diferente do automático): (1) o rótulo "CPF/CNPJ" do prestador saiu "CPFICNPJ" (a "/" lida como "I"), quebrando o regex de CNPJ — tolerado nos dois extratores Camaçari escaneados; (2) a razão social do prestador saiu com "Inscrição Municipal: ..." colado na MESMA linha (normalmente em linha separada) — corrigido cortando a razão também no próximo rótulo conhecido, não só em 2+ espaços como antes; (3) a linha do item na discriminação foi partida em 2 pedaços não-contíguos, deixando um "1" solto sem vírgula onde deveria estar o total — o fix da nota 148 acima (item como fonte primária) aceitava esse "1" truncado como Valor dos Serviços válido; corrigido exigindo vírgula decimal no total capturado do item antes de confiar nele, senão cai na célula da grade (aqui lida limpa). Limitação conhecida, não escondida: a razão social do prestador permanece truncada ("ADMINISTRAÇÃO LTDA" -> "ADMINISTRAÇ", perda de OCR anterior à extração, não recuperável por regex) e a do tomador mantém um fragmento sem rótulo por perto para ancorar um corte seguro ("GUARAJUBA MALLS S/A É 035001"). Suíte 383→388 verdes; 5 testes novos em `tests/test_camacari3_nota201_psm6_recut.py` (texto OCR real, já com o fallback de `_ocr_page` aplicado — o fix do fallback em si não tem teste unitário dedicado, mesmo padrão dos outros recortes de página deste extrator, não mockável sem o PDF de origem).
- **4º PDF do lote Guarajuba Shopping — número da nota vazando para a data de emissão e Valor dos Serviços com 1 dígito trocado na linha do item** (nota real nº 258, pág. 7 de 7, AVANÇO GESTÃO E ADMINISTRAÇÃO LTDA -> GUARAJUBA MALLS S/A, R$512,28): reportado pelo usuário — "a página 7 foi extraída com o número da nota incorreto: 9, o número correto é: 258". Na ÚNICA tentativa de recorte do cabeçalho em que o rótulo "Número da Nota" sai limpo, o valor logo abaixo saiu ilegível — a busca genérica de proximidade "vazava" para a linha seguinte ("Data de Emissão\n09/06/2026") e devolvia "09"/"9" (a data, não o número); o valor real ("258") sobrevivia limpo em OUTRA tentativa, onde era o RÓTULO que saía ilegível. Corrigido detectando quando o valor logo após um rótulo limpo é contaminado (termina em "/" ou é um ano) e, nesse caso, buscando um candidato plausível numa tentativa de recorte anterior da mesma caixa — validado sem regressão contra a nota nº 20335 (PADUA COMÉRCIO), onde o rótulo nunca bate limpo em nenhuma tentativa, preservando o fallback por nome do arquivo já existente para aquele caso. Ao escrever o teste de regressão, achado colateral na mesma nota: o Valor dos Serviços saía **R$512,48** em vez de R$512,28 — a linha do item (`1,0000 512,28 512,48`) teve o dígito de centavo do TOTAL trocado pelo OCR ("2"→"4"), um valor sintaticamente válido (tem vírgula, não é zero) que passava despercebido pela guarda existente; as 3 células da grade concordavam em R$512,28. Corrigido exigindo que unitário e total sejam iguais quando a quantidade é "1" (sempre o caso nesta grade) — divergência descarta o total da linha do item e a grade prevalece. Suíte 388→391 verdes; testes novos em `tests/test_camacari3_numero_contaminado_por_data_guarajuba.py`.
- **5º PDF do lote Guarajuba Shopping — número da nota vazando para a data de emissão na 1ª ocorrência do rótulo, quando uma ocorrência posterior tinha o valor limpo** (nota real nº 256, pág. 2 de 6, AVANÇO GESTÃO E ADMINISTRAÇÃO LTDA -> GUARAJUBA MALLS S/A, R$2.350,90): mesma classe de bug da nota 258 acima, mas INVERTIDA — aqui é a PRIMEIRA ocorrência do rótulo "Número da Nota" que está contaminada (valor vaza para "09/06/2026" → "09"), e uma tentativa de recorte POSTERIOR no mesmo texto repete o rótulo com o valor limpo ("256"); como a busca antiga só olhava a 1ª ocorrência, nunca chegava a ver a boa. Corrigido generalizando a busca para iterar TODAS as ocorrências do rótulo (não só a primeira) e devolver o primeiro valor não-contaminado encontrado — com 2 guardas adicionais (candidato não pode ter mais de 6 dígitos nem vir seguido de uma letra) necessárias para não regredir a nota nº 9100 (PH GESTÃO, já validada), onde a mesma busca ingênua capturaria a Inscrição Municipal do prestador ou um fragmento do Código de autenticidade. Suíte 391→393 verdes; testes novos em `tests/test_camacari3_numero_contaminado_primeira_ocorrencia_guarajuba.py`.
- **NF-e de Serviço de Comunicação (`telecom_comunicacao`) — Valor dos Serviços zerado e razão social do prestador corrompida por ruído de OCR** (nota real nº 22570, "Grupo FeF"/F&F Comunicações, CNPJ 13.398.812/0001-89, R$119,90 — 5º PDF do lote Guarajuba Shopping, pág. 1 de 6): reportado pelo usuário — "o valor foi extraído zerado". O regex de valor só procurava o rótulo "TOTAL A PAGAR" (caixa de destaque no topo do documento); nesta nota, essa caixa nunca é lida pelo OCR em nenhuma das 2 tentativas de recorte concatenadas. Corrigido com fallback para o campo "VALOR TOTAL NF" da grade de itens (sempre presente, ex. "VALOR TOTAL NF 11990" → R$119,90), usado só quando "TOTAL A PAGAR" não é encontrado. Achado colateral, mesma investigação: a razão social do prestador saía como um trecho de ruído solto em vez de "Grupo FeF" — ao contrário da nota F&F nº 31696 (já coberta, onde o ruído sai colado NA MESMA linha do título "DOCUMENTO AUXILIAR..."), aqui o ruído é uma linha inteira e SEPARADA, ANTES do título; a busca por nome (que só pulava a própria linha do título, sem exigir tê-lo visto primeiro) escolhia essa linha de ruído por já ter letras e mais de 3 caracteres. Corrigido para só considerar candidatos a nome DEPOIS de ver o título pela 1ª vez. Suíte 393→398 verdes; 5 testes novos em `tests/test_telecom_comunicacao_nota22570_grupo_fef.py`.
- **`camacari_ba_scan_v3` — página inteira ausente do resultado + prestador/tomador "Não Identificado" após recuperar a página** (nota real nº 160, pág. 3 de 7, AVANÇO GESTÃO E ADMINISTRAÇÃO LTDA -> GUARAJUBA SHOPPING LTDA, R$3.994,77 — 2º PDF do lote Guarajuba Shopping): reportado pelo usuário — "os dados não foram extraídos" nas páginas 1 e 3 (página 1/nota 147 já extraía correta, XML revisado estava desatualizado). Bug 1, mesma família da nota 201 (`v1.6.0`, fallback de PSM 6 gated por `best_score == 0`), mas numa variante NOVA: na orientação CORRETA (0°) o PSM automático lê 0 caracteres, porém uma rotação ERRADA (90°) produz texto embaralhado que, por coincidência, pontua > 0 em `_score_ocr_text` — a busca de rotação "vencia" com a rotação errada e o fallback de PSM 6 nunca disparava, mesmo com PSM 6 em 0° recuperando a página inteira (1513 caracteres limpos). Corrigido guardando a pontuação da tentativa em 0° separadamente (`score_angle_0`), usada na condição do fallback em vez do `best_score` da busca de rotação — generaliza sem risco, pois não muda nada quando 0° já pontua > 0 (maioria das notas) nem quando todas as rotações já zeravam (caso original da nota 201). Bug 2: uma vez recuperada a página via PSM 6, o rótulo "Nome/Razão Social" saiu com uma corrupção NOVA e mais severa que qualquer tolerância existente — as PRÓPRIAS letras do prefixo "Raz" saíram trocadas ("Nois Rraão Social:" no prestador, "Nomemianão Social:" no tomador), e "CPF/CNPJ" saiu reduzido a só ":"/"PJ:". Corrigido com fallback POSICIONAL (não mais por rótulo): a razão social é sempre o 1º campo impresso logo após o cabeçalho "PRESTADOR/TOMADOR DE SERVIÇOS" neste layout — pega-se a 1ª linha não-vazia do bloco e tudo depois do 1º ":" nela, e o CNPJ é buscado sem rótulo dentro do bloco já isolado da entidade. Achado colateral ao escrever o teste de regressão: o mesmo fallback de CNPJ sem rótulo recupera um CNPJ que antes caía no sentinela numa nota já coberta (nº 148) — reclassificado de limitação conhecida para melhoria, teste atualizado. Suíte 398→401 verdes; testes novos em `tests/test_camacari3_entidade_posicional_rotulo_ilegivel_guarajuba.py`.
- **`camacari_cpqd` (digital) — página tratada como escaneada num lote misto, e ordem de leitura quebrada no cabeçalho (nota real nº 52, pág. 8 do lote PH Gestão 08/2026, RAFFA GLASS VIDRACARIA LTDA -> PH GESTAO E CONSULTORIA S A, R$288,00)**: pedido do usuário — "verificar a extração incorreta, das páginas: 8, 17 e 29". A pág. 8 é 100% digital (1493 caracteres embutidos), mas 30 das 41 páginas do lote exigiram OCR — a flag `from_ocr`, do DOCUMENTO inteiro, roteava a página para a variante de foto/scan em vez do digital. Corrigido rastreando a origem POR PÁGINA em `parse_multiple()` (`_pagina_e_escaneada`, novo) e usando essa origem, não a do documento, na detecção de layout. Uma vez roteada para o digital, um segundo defeito apareceu: o `pdfminer.extract_text()` desta plataforma despeja todos os rótulos do cabeçalho antes de todos os valores — número, código de verificação, razões sociais e a grade inteira de valores saíam errados ou zerados. Corrigido estendendo ao Camaçari digital a reconstrução de texto por coordenadas já usada pelo SISLOC/Goiânia (`_reconstruir_texto_por_coordenadas`), mais 2 ajustes pontuais (janela do código de autenticidade e Data de Emissão com hora). Achado adicional, não é defeito: a pág. 17 ("não gerou XML") é a MESMA nota (nº 268) da pág. 13, digitalizada duas vezes — a deduplicação já descartava a segunda ocorrência corretamente. Verificado sem regressão contra o PDF completo (41 páginas, 34 notas antes e depois). Suíte 401→411 verdes; testes novos em `tests/test_camacari_cpqd_digital_ordem_leitura_ph_gestao.py` e `tests/test_camacari_nota_duplicada_paginas_13_17_ph_gestao.py`.
- **`telecom_comunicacao` — bloco de identificação (número/data/chave de acesso) descartado pelo OCR por estar colado ao QR Code** (nota real nº 34350, Grupo FeF/F&F Comunicações, R$129,90 — pág. 29 do lote PH Gestão 08/2026): reportado pelo usuário — "verificar a extração incorreta, das páginas: 8, 17 e 29" (ver também a nota 52/pág. 8, Camaçari). O bloco fica colado ao QR Code e a segmentação do Tesseract descarta a faixa inteira como imagem — nem a leitura padrão nem o recorte de página inteira já existente para este layout recuperavam o bloco; número saía "765" (vazado da "Resolução ANATEL nº 765/2023" no rodapé), Data de Emissão caía em `datetime.now()`, Código de Verificação ficava no sentinela "TELECOM". Corrigido com um recorte dedicado da região sem o QR Code (`_ocr_recut_identificacao_telecom`), prependado ao texto — extratores já existentes acertam sozinhos com o bloco disponível. Suíte 411→**417 verdes**; teste novo em `tests/test_telecom_identificacao_colada_qrcode_ph_gestao.py`.
- **`lauro_de_freitas_ba` — mesmo CNPJ (TESSERA HOSPITALITY) roteado para o layout errado (`enotas_gateway`) por emitir por dois sistemas diferentes no mesmo lote, mais nota cancelada sem sinalização** (notas nº 20261879/pág. 5 e nº 20261893/pág. 38, PH Gestão 08/2026): reportado pelo usuário — "verificar o valor extraído incorreto da página 5. Layout lauro de freitas". A detecção de `enotas_gateway` usava o CNPJ da TESSERA como marca, mas a mesma empresa também emite pelo sistema próprio da Prefeitura de Lauro de Freitas neste lote — corrigido com uma marca-guarda (texto do cabeçalho/rodapé da própria Prefeitura) que sobrepõe o match por CNPJ. Achado colateral: tolerância de ruído de OCR ampliada na grade MEI/Simples. Achado adicional: a nota nº 20261893 está CANCELADA no próprio documento ("CANCELADA" + "Motivo: desistência") — extração já saía correta, mas sem qualquer sinalização; adicionado aviso genérico (`NOTA_CANCELADA_PATTERN`, válido para qualquer layout) no ponto único de construção de `Nfse`, mantendo a extração real (nunca zerada/fabricada). Suíte 417→**428 verdes**; 11 testes novos em `tests/test_lauro_freitas_tessera_prefeitura_vs_enotas.py`.
- **`nfcom_salvador` (EBJ) — 1ª nota ESCANEADA já vista deste layout (até então só PDF digital): tomador não identificado e Valor dos Serviços zerado** (nota real nº 4777, SIND DELEGADOS DE POLICIA DO EST DA BAHIA/ADPEB, R$440,00): pedido do usuário — "Verificar o valor extraído incorreto da página 5... Valor e tomador do serviço incorretos". A leitura de página inteira funde as 2 colunas do cabeçalho linha a linha (mesma família de bug já vista em `nfcom_rlgr` escaneado), e a caixa cinza "TOTAL A PAGAR (R$)" não sobrevive em nenhuma combinação de zoom/PSM testada. Corrigido com 2 recortes dedicados (`_ocr_recut_tomador_nfcom_salvador_escaneado`/`_ocr_recut_total_pagar_nfcom_salvador_escaneado`, gated pelo mesmo marcador de CNPJ+título já usado em `_detect_layout`), um novo branch em `_extrair_tomador_nfcom_salvador` para a ordem rótulo:valor direta que o recorte devolve (com fallback para o comportamento digital original quando não bate), e 2 regexes generalizados (`\n+`→`\n*`) para aceitar tanto o texto sintético do recorte quanto o PDF digital original. Suíte 428→**434 verdes**; 6 testes novos em `tests/test_nfcom_salvador_escaneado_nota4777.py`.

## [1.6.0] - 2026-09-03

### Adicionado

- **Novo layout — Portal Nacional DANFSe **v2.0** / reforma tributária (`danfse_nacional_reforma`) — nota real nº 11, UNICA SEGURANCA PATRIMONIAL LTDA (Lauro de Freitas/BA) → CONDOMINIO EDIFICIO TK TOWER (Salvador/BA), R$ 12.353,68**: o novo modelo do Portal Nacional (seções `TRIBUTAÇÃO IBS/CBS`, `CST/cClassTrib`, `VALOR LÍQUIDO DA NFS-e + IBS/CBS`) era engolido pelo detector genérico `DANFSe v\d` e roteado ao parser da v1.0, cujo vocabulário de rótulos é outro. **Regra do valor (definida pelo usuário):** nesta versão o valor do serviço aparece em dois campos distintos — `BC ISSQN` e `VALOR DA OPERAÇÃO / SERVIÇO`; quando divergem prevalece o **VALOR DA OPERAÇÃO / SERVIÇO** para `ValorServicos`/`ValorLiquidoNfse`, e o `BC ISSQN` fica apenas na `BaseCalculo` — o `VALOR LÍQUIDO DA NFS-e` nunca é fonte (era exatamente esse o defeito: sem o rótulo antigo "Valor do Serviço", o parser da v1.0 copiava o líquido e gravava 9.817,41 em vez de 12.353,68). Corrigidos no mesmo layout: **retenção do ISSQN** (a v2.0 diz "Retenção do ISSQN: Retido pelo Tomador" em vez da coluna "ISSQN Retido: Sim/Não" — a nota saía com `IssRetido=2` e sem a tag `<ValorIssRetido>` num ISS de R$ 617,68 efetivamente retido); **entidades** (a v2.0 despeja `Indicador Municipal`/`Município`/`E-mail`/`Telefone`/`Código IBGE-CEP` DEPOIS dos dois blocos, em pares prestador-depois-tomador — o tomador saía com o e-mail, o telefone e o código IBGE do prestador, e com o complemento "LOTE 02" no lugar do bairro PITUBA; passaram a ser pareados por ordinal de ocorrência, com campo em branco devolvendo `None` sem consumir a posição do outro); **município de incidência do ISSQN** lido do campo próprio da nota via `municipio_incidencia_override` (prestador em Lauro de Freitas, ISSQN devido em Salvador); **item da LC 116 e discriminação** (na v2.0 o valor é impresso ANTES do rótulo); **intermediário fantasma** ("INTERMEDIÁRIO DA OPERAÇÃO NÃO IDENTIFICADO" virava um `<Intermediario>` com essa frase como razão social); e a **nota-fantasma** que partia o PDF de 1 nota em 2 (no OCR da v2.0 o título "DANFSe v2.0" cai a ~230 caracteres, passando do `DANFSE_HEADER_MIN_OFFSET` que protegia a v1.0 — o split passou a exigir um CNPJ/CPF **pontuado** antes do título candidato). INSS e "Contribuições Sociais - Retidas" já vinham corretos, pois esses rótulos não mudaram da v1.0 para a v2.0 (extração entregue no PR #44 segue valendo); "PIS/COFINS - Débito Apuração Própria" continua intencionalmente fora (débito próprio do prestador, não retenção), assim como "Exclusões e Reduções da Base de Cálculo" (base do IBS/CBS, não do ISSQN). Implementado como SUPERSET do `danfse_nacional`, **sem alterar nenhuma linha do parser da v1.0**. Suíte 356→369 verdes; 13 testes novos em `tests/test_danfse_nacional_reforma_layout.py`, incluindo regressão explícita de que a v1.0 continua roteando para `danfse_nacional` e um caso com `BC ISSQN` ≠ `VALOR DA OPERAÇÃO / SERVIÇO`. Ver detalhes em [DOCUMENTACAO_CONVERSAO.md](DOCUMENTACAO_CONVERSAO.md#14b-portal-nacional-danfse-v20-reforma-tributária--danfse_nacional_reforma).

### Corrigido

- **`fortaleza_ce` — Data de Emissão e Código de Verificação derrubados pela ordem de leitura do cabeçalho (nota real nº 109, RESCUE SOLUCOES AMBIENTAIS LTDA -> TEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDA)**: o cabeçalho desta NFS-e é uma grade multi-coluna que o pdfminer reconstrói fora da ordem visual — o valor `19/12/2025 13:02:43` sai logo após o título da nota, ANTES de qualquer rótulo, enquanto "Data e Hora da Emissão" só aparece bem mais abaixo sem nenhum valor colado depois; sem âncora dedicada, o loop genérico de rótulos não encontrava nada e caía no fallback `datetime.now()` (a nota saía sempre com a data da conversão, nunca a real). Mesmo defeito derrubava o Código de Verificação (rótulo "Código de Verificação" cai adjacente ao bloco "Número da NFS-e", não ao próprio valor), retornando o sentinela `XXXX-XXXX` em vez do código real. Corrigido ancorando a Data de Emissão no título da nota ("NOTA FISCAL ELETRÔNICA DE SERVIÇO - NFS-e" seguido do timestamp) e o Código de Verificação na sequência "Número da NFS-e / <número> / <código>". Suíte 352→354 verdes; 2 testes novos em `tests/test_fortaleza_ce_data_emissao.py`.
- **Novo layout — Localiza, agência MC LOCADORA PETROLINA (`localiza_petrolina`) — nota real nº 53044, TEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDA**: agência franqueada em Petrolina/PE (mesmo CNPJ corporativo `06.890.020/0001-61` de `localiza_fatura`) cujo PDF imprime os campos do box "CLIENTE" em ordem invertida (valor antes do rótulo) — tomador saía "Não Identificado", valor zerado e o município do prestador saía Salvador/BA em vez de Petrolina/PE. Tomador recuperado dos campos limpos do boleto/ficha de compensação ("Pagador:"/"Endereço:") em vez do box embaralhado; valor real ancorado na página do contrato ("TOTAL GERAL"), não na página da fatura. De quebra, corrigido um bug pré-existente no fatiamento multi-página de `parse_multiple` que descartava silenciosamente páginas de continuação de QUALQUER nota Localiza (`if not is_localiza:` indevido no `append` de `is_new_invoice`) — nunca detectado antes porque o fluxo genérico não dependia dessas páginas para os campos essenciais. Suíte 354→356 verdes; 2 testes novos em `tests/test_localiza_petrolina_layout.py`; suíte de regressão de `localiza_fatura` (6 testes) confirmada intacta.

## [1.5.0] - 2026-08-28

### Adicionado

- **Novo layout — São Paulo/SP, SKYTEF (plataforma Qive) — `sp_skytef`**:
  fatura de licenciamento de uso de software (SKYTEF SOLUÇÕES EM CAPTURA DE
  TRANSAÇÕES LTDA, CNPJ 04.988.631/0001-11) caía inteira no fallback
  `generico` (entidades trocadas/garbladas, valores zerados). Detectado só
  pelo CNPJ do emitente (nunca pela marca "Qive", plataforma SaaS
  compartilhada por outros emitentes). Prestador fixo; tomador dinâmico
  tolerante ao rótulo "Nome / Nome Empresarial" deslocado ANTES do
  cabeçalho de seção e à Competência impressa como valor órfão. Ver detalhe
  completo em [DOCUMENTACAO_CONVERSAO.md](DOCUMENTACAO_CONVERSAO.md#30f-são-paulosp--skytef-qive--sp_skytef).
- **Novo layout — São Paulo/SP, CAIXA CARTÕES (mesma plataforma Qive do
  SKYTEF, outro emitente) — `sp_caixa_cartoes`**: fatura de "Taxa de
  Serviço" (reembolso/adquirência de cartões pré-pagos) da CAIXA CARTÕES
  PRÉ-PAGOS S.A. (CNPJ 39.459.331/0006-34) caía no fallback `generico`.
  Detectado só pelo CNPJ do emitente. Prestador fixo; tomador dinâmico
  (extrator separado do SKYTEF, mesmo racional já usado entre
  `nfcom_salvador`/`nfcom_rlgr`); ValorIr extraído de um valor de IRRF real
  citado na discriminação (R$ 0,09, com base legal própria), em vez de
  zerado como no SKYTEF. Ver detalhe completo em
  [DOCUMENTACAO_CONVERSAO.md](DOCUMENTACAO_CONVERSAO.md#30g-são-paulosp--caixa-cartões-qive--sp_caixa_cartoes).
- **Novo layout — NFCom Rlgr Telefonia (`nfcom_rlgr`)**: nota nº 7271 (SINDICATO DOS DELEGADOS DE POLICIA DO ESTADO DA BAHIA ADPE, R$71,37 de Serviço de Terminação de Tráfego de Voz/STTV) caía no fallback genérico e saía com o CNPJ do tomador igual ao do prestador, razão social do tomador vazada de um rótulo vizinho, valores zerados e Código de Verificação em branco. Mesmo template nacional NFCom (portal SVRS) já usado por `nfcom_salvador`, mas de um emitente diferente (Rlgr Telefonia LTDA, CNPJ 57.675.896/0001-26, Barueri/SP) — detecção gated especificamente por esse CNPJ, prestador fixo (letterhead hardcoded), tomador extraído dinamicamente (rótulos em ordem direta, ao contrário do nfcom_salvador; CEP do tomador extraído de verdade, pois esta nota o imprime inline no endereço). Valor via "TOTAL A PAGAR:"; Base de Cálculo/Alíquota/ISS mantidos em 0,00 (tributado por ICMS, não ISS) com aviso explicativo. Data de Emissão extraída por rótulo dedicado (data+hora na mesma linha, "DATA DE EMISSÃO: 05/01/2026 11:10:01"). Suíte 325→332 verdes; 7 testes novos em `tests/test_nfcom_rlgr.py`. Ver detalhes em [DOCUMENTACAO_CONVERSAO.md](DOCUMENTACAO_CONVERSAO.md#27c-nfcom-rlgr-telefonia--nfcom_rlgr).

### Corrigido

- **`nfcom_rlgr` em nota ESCANEADA (nota nº 29377)**: o OCR de página inteira com PSM padrão funde os 2 blocos lado a lado do cabeçalho (dados do destinatário à esquerda, dados da nota à direita), vazando a coluna direita pra dentro da razão social do tomador ("...NOTA FISCAL Nº; 000029377..."), trocando 1 dígito do CNPJ do tomador no meio (checksum inválido, mas formato plausível) e derrubando endereço/Código de Verificação por completo. Corrigido com uma 2ª tentativa de OCR em `--psm 4` (separa as colunas corretamente), trocada quando pontua pelo menos empatado com a leitura padrão; a marca de detecção foi ampliada para tolerar a palavra "FISCAL" do título partida ao meio (efeito colateral do PSM 4); validação de checksum adicionada ao CNPJ do tomador (cai no sentinela em vez de propagar dígito trocado). Grade de valores ("TOTAL A PAGAR") sai impressa em cinza muito claro, acima dos limiares usuais de binarização — recuperada com um recorte dedicado (`_ocr_recut_total_pagar_rlgr`: autocontraste + limiar alto de 230), agora extraindo `R$71,37` corretamente em vez de 0,00. Suíte 332→339 verdes; 7 testes novos em `tests/test_nfcom_rlgr_escaneado.py`.
- **`danfe_produto` (NF-e Modelo 55/ICMS) em nota ESCANEADA (nota nº 764, PENELI METAIS LTDA)**: o cabeçalho funde 3 colunas na mesma faixa de Y (letterhead do emitente | caixa "DANFE" | código de barras), derrubando a palavra "DANFE" por completo e quebrando "Documento Auxiliar da Nota Fiscal Eletrônica"/"0-ENTRADA"/"1-SAÍDA" — sem tratamento, a nota caía no fallback genérico de NFS-e/DANFSe (documento de SERVIÇO/ISS), saindo com razão social vazada, valor zerado e CNPJ do tomador cruzado. Corrigido com detecção OCR-tolerante (marca alternativa exclusiva do Modelo 55, só ativa com `from_ocr=True`), extrator dedicado (`_parse_danfe_produto_ocr`, o parser digital original — nota nº 52.136/GRAN COFFEE — fica intocado) e 3 recortes dedicados (emitente/grade de ICMS/linha do item). Suíte 325→329 verdes; 4 testes novos em `tests/test_danfe_produto_escaneado.py`. Desenvolvido em branch própria (`feature/layout-danfe-55`), separada de layouts de NFS-e/SERVIÇO. Ver detalhes em [DOCUMENTACAO_CONVERSAO.md](DOCUMENTACAO_CONVERSAO.md#danfe-estadual--nf-e-de-produto-modelo-55--xml-nf-e-400).
- **Teste `test_check_latest_release_retorna_dict_quando_ha_versao_nova` obsoleto desde o release 1.4.0**: mockava a tag remota como `"v1.4.0"` fixo, esperando que `check_latest_release()` a reconhecesse como "versão mais nova" — parou de bater assim que `APP_VERSION` alcançou 1.4.0, e passou a falhar (`check_latest_release()` corretamente retorna `None` quando não há versão mais nova, mas o teste ainda esperava um dict). Corrigido gerando a tag mockada dinamicamente a partir de `APP_VERSION` (major+1), pra nunca mais ficar obsoleto a cada bump de versão. Suíte volta a 100% verde (352/352).

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
