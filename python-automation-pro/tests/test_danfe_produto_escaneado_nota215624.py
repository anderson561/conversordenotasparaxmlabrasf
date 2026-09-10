# -*- coding: utf-8 -*-
"""DANFE Estadual (NF-e Modelo 55) da EDITORA WMF MARTINS FONTES LTDA (CNPJ
08.463.170/0004-67, São Paulo/SP) -> SINDICATO DOS DELEGADOS DE POLICIA DO
ESTADO DA BAHIA (Salvador/BA), nota real nº 215624, série 7, R$124,70
(livro "COMENTARIOS A LEI ORGANICA NACIONAL DAS POLICIAS CIVIS", 1 un x
R$107,80 + R$16,90 de frete) - 2ª nota ESCANEADA deste layout, vendida via
marketplace (MAGALU) e entregue pela MAGALU ENTREGAS.

O que esta nota trouxe de novo em relação à nº 764 (ver
`test_danfe_produto_escaneado.py`), e que a fazia sair errada:

1. **Detecção**: a condição `portal nacional da NF-e` era exigida como
   frase contígua em 3 lugares (`_detect_layout`, `_detect_layout_page` e o
   portão dos recortes em `_ocr_page`). Aqui o OCR quebra a frase entre duas
   linhas ("...portal nacional da\nNF-e www.nfe.fazenda.gov.br/portal..."),
   então as 3 falhavam juntas: os recortes nunca rodavam, o layout nunca era
   detectado e a nota caía no transformer ABRASF - saindo como se fosse uma
   NFS-e de serviço/ISS. Corrigido por `DANFE_PORTAL_NFE_PATTERN`, que
   aceita a quebra e também a URL isolada.

2. **Recortes dedicados**: as frações fixas de Y calibradas na nota nº 764
   caem sobre o bloco TRANSPORTADOR/VOLUMES desta nota - a grade "CÁLCULO DO
   IMPOSTO" da WMF é mais curta e desloca a tabela de itens para baixo -,
   devolvendo só rótulos de coluna. Corrigido por
   `_ocr_recut_danfe_produto_ancorado`, que ancora a faixa no rótulo
   impresso ("DADOS DO(S) PRODUTOS") via caixas de palavra do OCR, em vez de
   exigir calibração por emitente. Só entra em ação quando o recorte de
   fração fixa não devolve as colunas, de modo que a nota nº 764 segue
   lendo exatamente o mesmo recorte de antes.

3. **Campos autoverificáveis**: a chave de acesso (mod-11) e o código do
   produto - um ISBN-13, porque o item é um livro - têm dígito verificador,
   o que permite ACEITAR ou REJEITAR uma leitura de OCR em vez de confiar
   nela. É o que desempata as duas leituras do código: a de página inteira
   sai "9766556754772" (reprovada no mod-10) e a do recorte
   "9786556754772" (aprovada), que é a impressa.

4. **Separador decimal PONTO**: esta nota imprime os valores como "107.80"
   e "124.70", não no padrão pt-BR com vírgula, o que fazia `_num` ler
   10780,00. A grade só é aceita quando fecha a identidade contábil
   (produtos + frete + seguro + outras - desconto + IPI == total da nota).

5. **Imunidade constitucional de livros**: o item traz CST **041** e as
   informações complementares registram a imunidade ("Im imp conf.art 150
   inc VI al d const fed 88"), NCM 49019900. A leitura fiel é o grupo
   **ICMS40** com base e valor zerados - BC/ICMS em branco no papel é dado
   REAL aqui, não falha de leitura.

6. **origem + CST na mesma coluna**: o DANFE imprime os dois concatenados
   ("041" = origem 0 + CST 41), enquanto o XML os separa em `orig` (1
   dígito) e `CST` (2). Sem a divisão o `CST` sairia com 3 dígitos e o
   arquivo seria rejeitado - ver `test_orig_e_cst_saem_separados_no_xml`.

Limites assumidos, sinalizados por aviso em vez de preenchidos por
estimativa: o **peso líquido** do volume é cortado fisicamente na margem
direita do documento digitalizado ("0.30" + caractere partido), e completá-lo
seria fabricar o valor - `vol/pesoL` é opcional no XML e sai omitido.

IMPORTANTE (distinção de domínio, ver
https://suporte.dominioatendimento.com/central/faces/solucao.html?codigo=1195):
um DANFE Modelo 55 é documento de PRODUTO/mercadoria tributado por ICMS/IPI,
estruturalmente DIFERENTE de uma NFS-e ABRASF (SERVIÇO, tributado por ISS) -
retorna `NfeProduto` e usa `NfeProdutoTransformer`, nunca o ABRASF.

O texto abaixo é o resultado REAL de `_ocr_page` (Tesseract, zoom 3x, já com
os 4 recortes dedicados prependados) para a página 1 desta nota, usado como
fixture para travar a extração sem precisar rodar Tesseract no teste."""
import os
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_DANFE_PRODUTO
from src.models.nfe_produto_models import NfeProduto
from src.transformers.nfe_produto_transformer import NfeProdutoTransformer

MOCK_TEXT = (
    'PÁ pm IDENTIFICAÇÃO E ASSINATURA DO RECEBEDOR\n'
    'Editora WMF Martins Fontes Ltda. - Internet\n'
    'Rua Professor Laerte Ramos de Carvalho N 155 Bela Vista\n'
    'Sao Paulo - SP\n'
    'Fone: 1132922660 Cep: 01325030\n'
    'NATUREZA DA OPERAÇÃO\n'
    'Venda\n'
    '\n'
    '<<<DANFE_PRODUTO_RECUT>>>\n'
    'MM\n'
    'CÁLCULO DO IMPOSTO\n'
    'PARE DE CÁLCULO DO ICMS VALOR DO ICMS BASE DE CÁLCULO DO ICMS SURST. VALOR DO ICMS SUBST, VALOR TOTAL DOS PRODUTOS\n'
    'VALOR DO FRETE [ VALOR DO SEGURO [DesconNTO i [ouTRAS DESPESAS ACESSÓRIAS [VALOR TOTAL DO IP| , [VALOR TOTAL DA NOTA\n'
    '\n'
    '<<<DANFE_PRODUTO_RECUT>>>\n'
    'DESCRIÇÃO DOS PRODUTOS\n'
    '\n'
    'eia COMENTARIOS A LEI ORGAN\n'
    '9786556754772 DAS POLICIAS CIVIS - FREITA\n'
    'CÁLCULO DO ISSQN\n'
    '\n'
    '<<<DANFE_PRODUTO_RECUT>>>\n'
    'NAL\n'
    'asojas0o | 041 | 6115 | UN | 1,0000 107,80\n'
    '\n'
    'VALOR TOTAL\n'
    '\n'
    '49019900 6115 1,0000\n'
    '\n'
    '107,80\n'
    '\n'
    '\n'
    'FRETE POR CONTA | Emitente\n'
    '\n'
    '<<<DANFE_PRODUTO_RECUT>>>\n'
    'do a - . = -— o\n'
    'y -\n'
    'É CESEMOS DE Edipra WMF Marins Fontes Lida. -Inlemei OS PRODUTOS CONSTANTES NA NOTA FISCAL INDICADA AO LADO NF-e\n'
    'Nº 215624\n'
    '(DATA DE RECEBIMENTO [eo E ASSINATURA DO RECEBEDOR SÉRIE: 7\n'
    'TcontaoLE DO Fisco\n'
    'DOCUMENTO AUXILIAR\n'
    'DE NOTA FISCAL\n'
    'ELETRÔNICA\n'
    '0- ENTRADA 1 CHAVE DE ACESSO\n'
    '1- SAÍDA\n'
    '|3526.0808.4631.7000.0467.5500.7000.2156.2410.1888.9478\n'
    'Editora WMF Martins Fontes Ltda. - Internet Negise2s 526\n'
    'Rua Professor Laerte Ramos de Carvalho N 155 Bela Vista SÉRIE 7 Consulta de autenticidade no portal nacional da\n'
    'Sao Paulo - SP PÁGINA 1 DE1 NF-e www.nfe.fazenda.gov.br/portal ou no site da Sefaz\n'
    'Fone: 1132922660 Cep: 01325030 Autorizadora.\n'
    'NATUREZA DA OPERAÇÃO PROTOCOLO DE AUTORIZAÇÃO DE USO n\n'
    'Venda 135263328746092 14/08/2026 16:44:05\n'
    '(INSCRIÇÃO ESTADUAL INSCRIÇÃO ESTADLIAL DE SUSST. fONPJ\n'
    '147024991112 | 08.463.170/0004-67\n'
    'DESTINATÁRIO / REMETENTE\n'
    'NOME / RAZÃO SOCIAL CNPJ/CPF DATA EMISSÃO\n'
    '(201474566-SINDICATO DOS DELEGADOS DE POLICIA DO ESTADO DA BA 73.393.696/0001-37 14/08/2026 16:44\n'
    'ENDEREÇO BAIRRO / DISTRITO cer DATA ENTRADA /SAÍDA\n'
    'DIREITA DA PIEDADE Nr 11 BARRIS 40070190 14/08/2026\n'
    'MUNICÍPIO [FONE / FAX UF INSCRIÇÃO ESTADUAL HORA ENTRADA / SAÍDA\n'
    'SALVADOR BA 16:44\n'
    'CÁLCULO DO IMPOSTO\n'
    'BASE DE CÁLCULO DO ICMS VALOR DO ICMS BASE DE CÁLCULO DO ICMS SURST. VALOR DO ICMS SUBST. VALOR TOTAL DOS PRODUTOS\n'
    '0.00 0.00 | 0.00 0.00 107.80\n'
    'VALOR DO FRETE VALOR DO SEGURO DESCONTO OUTRAS DESPESAS ACESSÓRIAS [VALOR TOTAL DO IPI VALOR TOTAL DA NOTA\n'
    '16.90 0.00 0.00 0.00 0.00 124.70\n'
    'TRANSPORTADOR / VOLUMES TRANSPORTADOS\n'
    'NOME / RAZÃO SOCIAL FRETE POR CONTA CÓDIGO ANTT PLACA DO VEÍCULO ur CNPJ/CPF\n'
    'MAGALU ENTREGAS Eta 47.960.950/0001-21\n'
    'ENDEREÇO MUNICÍPIO ur INSCRIÇÃO ESTADUAL\n'
    'VOLUNTARIOS DA FRANCA FRANCA SP ISENTO\n'
    'QUANTIDADE ESPÉCIE MARCA * NUMERAÇÃO PESO BRUTO PESO LiquiDO\n'
    '1 CAIXAS WMF Nove Julho 0.300 0.30€\n'
    'DADOS DO PRODUTOS / SERVIÇOS\n'
    'cónico DESCRIÇÃO DOS PRODUTOS /SERVIÇOS NCM/SH | [a | crop uno] QUANT. | VALOR UNITÁRIO | VALOR TOTAL BCICMS V.IcMs | vip na: ALIQ. IP\n'
    'oi COMENTARIOS A LEI ORGANICA NACIONAL\n'
    '9766556754772 DAS POLICIAS CIVIS - FREITAS BASTOS 49019900 | 041 [eus UN | 10000] 10740] 107,80 0,00 |\n'
    'CÁLCULO DO ISSQN\n'
    'INSCRIÇÃO MUNICIPAL VALOR TOTAL DOS SERVIÇOS fe DE CÁLCULO DO SON [e DO ISSON\n'
    'DADOS ADICIONAIS\n'
    'INFORMAÇÕES COMPLEMENTARES RESERVADO AO FISCO\n'
    'Nro. Ped. Orig.: 1277596 Pedido Web: 1277596 Valor do frete: 16.90 Forma de pagamento: Marketplace Forma de\n'
    'Pagamento: MAGALU - MARKETPLACE Qtd. Parcelas: 1 [Trib aprox R$: 14 50 Federal e 19 40 Estadual Fonte:\n'
    'IBPT FECOMERCIO SP 81AAFF IEnd. Entrega: DIREITA DA PIEDADE N 11 BARRIS SALVADOR - BA\n'
    'CEP:40070190 Im imp conf.art 150 inc VI al d const fed 88 N Inc ICMS cof art 7 inc XIll do RICMS 2000 IPI im Cof\n'
    'art 18 inc | do RIPI 98.Conf.lei 11.033 d 21 12 2004 Art6 PIS COFINS Aliq.Red.a Zero. Operacao esta sujeila ao\n'
    'disposto na LC n 224 de 2025. Operacao esta sujeita ao disposto na LC n 224, de 2025\n'
    '\n'
)


def _novo_extrator():
    dummy_path = "tests/dummy_danfe_produto_nota215624.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = MOCK_TEXT
    extractor.from_ocr = True
    return extractor, dummy_path


def test_deteccao_tolera_frase_do_portal_quebrada_em_duas_linhas():
    """A frase "portal nacional da NF-e" vem partida entre duas linhas nesta
    nota; sem tolerar a quebra, a nota caía no fallback ABRASF (documento de
    SERVIÇO) em vez de ser reconhecida como DANFE de PRODUTO."""
    extractor, dummy_path = _novo_extrator()
    try:
        assert 'portal nacional da NF-e' not in MOCK_TEXT
        assert extractor._detect_layout() == LAYOUT_DANFE_PRODUTO
        assert extractor._detect_layout_page(MOCK_TEXT) == LAYOUT_DANFE_PRODUTO
    finally:
        os.remove(dummy_path)


def test_extract_danfe_produto_escaneado_nota_215624():
    """Regressão: a nota vira exatamente 1 `NfeProduto` com chave, entidades,
    transportador, item e valores REAIS do documento."""
    extractor, dummy_path = _novo_extrator()
    try:
        nfe = extractor.parse()

        assert isinstance(nfe, NfeProduto)

        assert nfe.numero == "215624"
        assert nfe.serie == "7"
        assert nfe.chave_acesso == "35260808463170000467550070002156241018889478"
        assert nfe.natureza_operacao == "Venda"
        assert nfe.data_emissao.strftime("%d/%m/%Y %H:%M") == "14/08/2026 16:44"
        assert nfe.protocolo_autorizacao == "135263328746092"
        assert nfe.protocolo_data_hora.strftime("%d/%m/%Y %H:%M:%S") == "14/08/2026 16:44:05"

        assert nfe.emitente.cnpj_cpf == "08.463.170/0004-67"
        assert nfe.emitente.inscricao_estadual == "147024991112"
        assert nfe.emitente.razao_social == "EDITORA WMF MARTINS FONTES LTDA"
        assert nfe.emitente.endereco.logradouro == "Rua Professor Laerte Ramos de Carvalho"
        assert nfe.emitente.endereco.numero == "155"
        assert nfe.emitente.endereco.bairro == "Bela Vista"
        assert nfe.emitente.endereco.municipio == "Sao Paulo"
        assert nfe.emitente.endereco.uf == "SP"
        assert nfe.emitente.endereco.cep == "01325030"
        assert nfe.emitente.endereco.codigo_municipio == "3550308"

        assert nfe.destinatario.cnpj_cpf == "73.393.696/0001-37"
        assert nfe.destinatario.endereco.logradouro == "DIREITA DA PIEDADE"
        assert nfe.destinatario.endereco.numero == "11"
        assert nfe.destinatario.endereco.bairro == "BARRIS"
        assert nfe.destinatario.endereco.municipio == "SALVADOR"
        assert nfe.destinatario.endereco.uf == "BA"
        assert nfe.destinatario.endereco.cep == "40070190"
        assert nfe.destinatario.endereco.codigo_municipio == "2927408"
    finally:
        os.remove(dummy_path)


def test_prefixo_de_codigo_do_marketplace_sai_da_razao_social_do_destinatario():
    """A razão social vem prefixada pelo código do cliente no marketplace
    ("(201474566-SINDICATO DOS..."), que não é parte do nome."""
    extractor, dummy_path = _novo_extrator()
    try:
        nfe = extractor.parse()
        assert nfe.destinatario.razao_social == (
            "SINDICATO DOS DELEGADOS DE POLICIA DO ESTADO DA BA")
    finally:
        os.remove(dummy_path)


def test_grade_de_valores_com_separador_decimal_ponto():
    """Esta nota imprime "107.80"/"124.70" (ponto), não o padrão pt-BR com
    vírgula. A grade só é aceita se fechar a identidade contábil
    produtos + frete + seguro + outras - desconto + IPI == total da nota."""
    extractor, dummy_path = _novo_extrator()
    try:
        v = extractor.parse().valores
        assert v.valor_total_produtos == 107.80
        assert v.valor_frete == 16.90
        assert v.valor_total_nota == 124.70
        assert v.valor_seguro == 0.0
        assert v.desconto == 0.0
        assert v.outras_despesas == 0.0
        assert v.valor_ipi == 0.0
        # Livro imune: BC e ICMS zerados são LEITURA REAL do papel
        assert v.base_calculo_icms == 0.0
        assert v.valor_icms == 0.0
        soma = (v.valor_total_produtos + v.valor_frete + v.valor_seguro
                + v.outras_despesas - v.desconto + v.valor_ipi)
        assert abs(soma - v.valor_total_nota) < 0.01
    finally:
        os.remove(dummy_path)


def test_item_lido_do_recorte_ancorado_na_tabela():
    """NCM/CST/CFOP/UNID/QTD desta nota só saem no recorte ANCORADO no
    rótulo da tabela - o de fração fixa (calibrado na nota nº 764) cai no
    bloco do transportador."""
    extractor, dummy_path = _novo_extrator()
    try:
        nfe = extractor.parse()
        assert len(nfe.itens) == 1
        item = nfe.itens[0]
        assert item.ncm == "49019900"
        assert item.cst_icms == "041"
        assert item.cfop == "6115"
        assert item.unidade == "UN"
        assert item.quantidade == 1.0
        assert item.valor_unitario == 107.80
        assert item.valor_total == 107.80
        assert item.aliquota_icms == 0.0
    finally:
        os.remove(dummy_path)


def test_codigo_do_produto_e_isbn_validado_pelo_digito_verificador():
    """O código é um ISBN-13 e tem dígito verificador mod-10, então a leitura
    é ACEITA ou REJEITADA em vez de presumida: a de página inteira
    ("9766556754772") reprova e a do recorte ("9786556754772") aprova."""
    extractor, dummy_path = _novo_extrator()
    try:
        assert SPPdfExtractor._dv_ean13("978655675477") == "2"
        assert SPPdfExtractor._dv_ean13("976655675477") != "2"
        assert extractor.parse().itens[0].codigo == "9786556754772"
    finally:
        os.remove(dummy_path)


def test_descricao_completa_vem_das_duas_linhas_da_celula():
    """O recorte estreito da coluna corta a descrição no meio
    ("COMENTARIOS A LEI ORGAN"); a versão íntegra é montada das duas linhas
    da célula no texto de página inteira, sem o código nem as colunas
    numéricas colados nas pontas."""
    extractor, dummy_path = _novo_extrator()
    try:
        assert extractor.parse().itens[0].descricao == (
            "COMENTARIOS A LEI ORGANICA NACIONAL "
            "DAS POLICIAS CIVIS - FREITAS BASTOS")
    finally:
        os.remove(dummy_path)


def test_transportador_do_bloco_fundido_pelo_ocr():
    """No documento escaneado o OCR cola rótulo e valor na mesma linha, ao
    contrário do layout vertical do PDF digital. A modalidade do frete vem
    da PALAVRA impressa ao lado da caixa ("Emitente" -> código 0), já que o
    dígito não sobrevive à leitura de página inteira."""
    extractor, dummy_path = _novo_extrator()
    try:
        transportador = extractor.parse().transportador
        assert transportador is not None
        assert transportador.razao_social == "MAGALU ENTREGAS"
        assert transportador.cnpj_cpf == "47.960.950/0001-21"
        assert transportador.inscricao_estadual == "ISENTO"
        assert transportador.uf == "SP"
        assert transportador.frete_por_conta == "0"
        assert transportador.quantidade_volumes == 1.0
        assert transportador.especie == "CAIXAS"
        assert transportador.marca == "WMF Nove Julho"
        assert transportador.peso_bruto == 0.300
    finally:
        os.remove(dummy_path)


def test_peso_liquido_cortado_na_margem_fica_ausente_com_aviso():
    """O scan corta fisicamente o último dígito do peso líquido na margem
    direita; completar o valor seria fabricá-lo. `vol/pesoL` é opcional no
    XML e sai omitido, com aviso explícito."""
    extractor, dummy_path = _novo_extrator()
    try:
        nfe = extractor.parse()
        assert nfe.transportador.peso_liquido is None
        assert any("Peso líquido" in aviso for aviso in nfe.avisos)
        xml = NfeProdutoTransformer().transform(nfe)
        assert "<pesoB>0.300</pesoB>" in xml
        assert "<pesoL>" not in xml
    finally:
        os.remove(dummy_path)


def test_orig_e_cst_saem_separados_no_xml():
    """O DANFE imprime origem+CST concatenados numa coluna só ("041"),
    enquanto o XML os separa em `orig` (1 dígito) e `CST` (2). Sem a divisão
    o `CST` sairia com 3 dígitos e o arquivo seria rejeitado."""
    extractor, dummy_path = _novo_extrator()
    try:
        xml = NfeProdutoTransformer().transform(extractor.parse())
        # Livro imune (CF/88 art. 150, VI, "d"): CST 41, não tributada
        assert "<ICMS40>" in xml
        assert "<orig>0</orig>" in xml
        assert "<CST>41</CST>" in xml
        assert "<CST>041</CST>" not in xml
    finally:
        os.remove(dummy_path)


def test_xml_final_da_nota_215624():
    """XML completo conferido campo a campo contra o papel."""
    extractor, dummy_path = _novo_extrator()
    try:
        xml = NfeProdutoTransformer().transform(extractor.parse())

        assert "35260808463170000467550070002156241018889478" in xml
        assert "<cUF>35</cUF>" in xml
        assert "<mod>55</mod>" in xml
        assert "<serie>7</serie>" in xml
        assert "<nNF>215624</nNF>" in xml
        assert "<cDV>8</cDV>" in xml
        # SP -> BA: operação interestadual, fato gerador no município do emitente
        assert "<idDest>2</idDest>" in xml
        assert "<cMunFG>3550308</cMunFG>" in xml
        assert "<CNPJ>08463170000467</CNPJ>" in xml
        assert "<CNPJ>73393696000137</CNPJ>" in xml
        assert "<cProd>9786556754772</cProd>" in xml
        assert "<NCM>49019900</NCM>" in xml
        assert "<CFOP>6115</CFOP>" in xml
        assert "<vProd>107.80</vProd>" in xml
        assert "<vFrete>16.90</vFrete>" in xml
        assert "<vNF>124.70</vNF>" in xml
        assert "<CRT>3</CRT>" in xml
        assert "<modFrete>0</modFrete>" in xml
        assert "<CNPJ>47960950000121</CNPJ>" in xml
        assert "<xNome>MAGALU ENTREGAS</xNome>" in xml
        assert "<nProt>135263328746092</nProt>" in xml
    finally:
        os.remove(dummy_path)
