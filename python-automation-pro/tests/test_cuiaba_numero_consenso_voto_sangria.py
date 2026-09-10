# -*- coding: utf-8 -*-
"""NFS-e de Cuiabá/MT (ISSNet) ESCANEADA — nota real nº 308, FB PISOS E
REVESTIMENTOS (CNPJ 36.776.200/0001-88) -> SÃO PEDRO CONSTRUTORA LTDA,
R$1.368,00. Reportado pelo usuário: o `<Numero>` saía `00000000`.

Esta nota é do template PÓS-REFORMA de Cuiabá (traz as seções "TRIBUTAÇÃO
NACIONAL" e "IMPOSTO E CONTRIBUIÇÃO SOBRE BENS E SERVIÇOS - IBS/CBS", além de
"Número da DPS"/"Série da DPS"), o que muda o cabeçalho o suficiente para
derrubar as duas âncoras de texto de `_extrair_numero`:

- a âncora do rótulo limpo ("Número da Nota Fiscal: N") não casa porque o OCR
  funde as 3 colunas do cabeçalho e o valor cai colado ao FIM da linha do
  letterhead ("Prefeitura Municipal de Cuiabá MT 208" — e note que ali o OCR
  ainda lê 208, não o 308 real);
- a âncora de scan degradado espera "Dados do Prestador de Serviço", e este
  template diz "IDENTIFICAÇÃO DO PRESTADOR".

O número só é recuperável pelo recorte dedicado da caixa
(`_ocr_numero_box_cuiaba`). E o defeito estava justamente ali: o recorte LIA o
número certo nos 3 zooms, mas o consenso comparava a STRING INTEIRA de cada
leitura —

    zoom 6, PSM 6 -> "308"
    zoom 8, PSM 6 -> "308\n2"
    zoom 10, PSM 6 -> "308\n5"

— e o dígito de sangria da linha seguinte (que varia com o zoom, porque é
geometria do recorte) transformava 3 leituras CONCORDANTES em 3 votos
distintos de 1 voto cada. Com `contagem < 2` a função devolvia vazio e um
número perfeitamente legível caía no sentinela `00000000`.

Correção: cada voto passa a ser o PRIMEIRO grupo de dígitos da leitura, e os
votos concordantes têm de vir de ZOOMS DIFERENTES. A segunda condição existe
para que a normalização não fabrique um consenso falso: a sangria varia com o
zoom, um dígito real não; e dois PSM no MESMO zoom leem o MESMO bitmap, logo
concordarem é evidência fraca. Sem zooms distintos a função devolve vazio e a
extração cai no fallback honesto (sentinela + aviso) — dado ausente, nunca
dado ERRADO (é o caso documentado da nota GMS FLATS pág. 17, cujo número não é
recuperável em nenhuma combinação testada).

Este template pós-reforma mudou de lugar/formato outros 3 campos, corrigidos
na sequência (a pedido do usuário: "Pode corrigir o item: 1,2 e 3"), todos com
o mesmo desenho de portão — a marca que os liga a este template não existe em
nenhuma das 8 notas Cuiabá já cobertas, então nada regride:

- **Código de Autenticidade**: virou uma corrida de 57 dígitos PUROS, e a
  busca do template antigo exige um token alfanumérico MISTO de 7-10 chars
  ("3B3DC3576") — o campo caía no sentinela "XXXX-XXXX";
- **Cód. Trib. Nacional / Atividade Municipal**: a grade de atividade antiga
  (alíquota | item LC116 | NBS de 9 dígitos) não existe mais, então o item da
  LC 116 caía no default genérico "03115"; e o `CodigoCnae` era HARDCODED como
  "0000000" no transformer, para todos os layouts;
- **Endereço**: deixou de ter um rótulo por componente e virou uma linha de
  texto livre separada por vírgulas, com o número marcado por "nº" em posição
  variável — a quebra genérica trocava número por complemento e punha um
  pedaço do endereço no bairro.

`MOCK_PAGINA` é o texto REAL de página inteira desta nota (os 2 passes de OCR
concatenados, como em produção), SEM o recorte dedicado. `MOCK_COM_RECUT`
acrescenta na frente o que o recorte corrigido devolve, reproduzindo byte a
byte o `best_text` que `_ocr_page` monta em produção."""
import io
import os

import pytesseract
from PIL import Image

from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_CUIABA
from src.transformers.abrasf_transformer import Abrasf201Transformer

MOCK_PAGINA = (
    'E a 5 % Série do Documento\n'
    'Prefeitura Municipal de Cuiabá ç N Fi | e Nota Fiscal de Serviç\n'
    'Secretaria Municipal de Economia Eletrônica do oa\n'
    ': pi . E Número da Nota Fiscal\n'
    'Prefeitura Municipal de Cuiabá MT 208\n'
    'Data de Geração da NF5-e Data de Competência Código de Autenticidade [=] Rd tal [7]\n'
    'ar, el “a\n'
    '04/08/2026 16:41:00 04/08/2026 510334060803482670000100000000008200030826080416415523120 SUE RAT\n'
    'EA eae\n'
    'Emitente da NF5-e Número da DPS Data Emissão da DPS Série da DPS Não e \'\n'
    'Prestador 308 04/08/2026 DPS 15088 Va; Pe\n'
    '[Eds\n'
    'Consulte a autenticidade desta nota lendo o QRCode ou acessando o site:  https://onlinecba.issnetonline.com.br/cuiaba/ ii E\n'
    'IDENTIFICAÇÃO DO PRESTADOR\n'
    'CNPJ/CPF/NIF: 36.776.200/0001-88 Inscrição Municipal: 137208758 Telefone: (65) 98157-2565\n'
    'Nome/Razão Social: FB PISOS E REVESTIMENTOS\n'
    'Nome Fantasia: FB PISOS E REVESTIMENTOS\n'
    'Endereço: Rua M4, Quadra 155, nº N2\n'
    'Cidade: Cuiabá Estado/Prov./Reg.: Mato Grosso Pais: Brasil CEP. 78043-263\n'
    'E-mail: | marcosfbp(Ohotmail.com\n'
    'Inscrição Estadual:  13.263.227-6\n'
    'IDENTIFICAÇÃO DO TOMADOR\n'
    'CNPJ/CPF/NIF: 03.051.741/0001-90 Inscrição Municipal: - Telefone: -\n'
    'Nome/Razão Social: SÃO PEDRO CONSTRUTORA LTDA\n'
    'Nome Fantasia: SÃO PEDRO CONSTRUTORA LTDA\n'
    'Endereço: Av. Praia de Pajussara, nº 554, Quadra 28, Lote 09\n'
    'Cidade: Lauro de Freitas  Estado/Prov./Reg.: Bahia Pais: Brasil CEP:  42.708-720\n'
    'E-mail: -\n'
    'INTERMEDIÁRIO DO SERVIÇO NÃO IDENTIFICADO NA NFS-E\n'
    'DESTINATÁRIO DO SERVIÇO NÃO IDENTIFICADO NA NFS-E\n'
    'DADOS DO SERVIÇO PRESTADO\n'
    'Cód. Trib. Nacional: 07.06.02 NES: 07.06.02.00 Atividade Municipal:  14330-4/05 Aplicação de revestimentos e de resinas\n'
    'Local da Prestação: Cuiabá - MT Pais Resultado da Prestação do Serviço: -\n'
    'VI. do Serviço: R$1.368,00 VI. do Desc. Incondicionado: - VI. do Desc. Condicionado: -\n'
    'Descrição dos Serviços e Materiais:\n'
    'Prestação de serviços de instalação de piso tátil, referente à demanda da\n'
    'SÃO PEDRO CONSTRUTORA LTDA.\n'
    'CONTA BANCÁRIA PARA DEPÓSITO: R$ 1.368,00\n'
    'BANCO: 0260 AGÊNCIA: 0001 CONTA: 32242182-6\n'
    'IMPOSTO SOBRE SERVIÇO DE QUALQUER NATUREZA - ISSQN\n'
    'Tipo Tributação: Operação Tributável Tipo Susp. Exig.: - Nº Proc. Susp.: -\n'
    'Município de Incidência: Cuiabá - MT Tipo de Retenção: Não Retido Valor Dedução: R$0,00\n'
    'Base de Cálculo:  R$1.368,00 Alíquota: 5% VI. ISSQN: R$68,40\n'
    'TRIBUTAÇÃO NACIONAL\n'
    'CST. Operação Tributável com ÁAliquota Básica\n'
    'Tipo de Retenção: PIS/COFINS/CSLL Não Retidos MI. PIS:  R$8,88 VI COFINS: R$40,92\n'
    'MI. CSLL: - VI. IRRF: - VI. CP Retido: -\n'
    'IMPOSTO E CONTRIBUIÇÃO SOBRE BENS E SERVIÇOS - IBS/CBS\n'
    'Cód. Ind. Op.: - Classif. Tributária: - Situação Tributária: -\n'
    'Municipio de Incidência: - Tipo de Operação: -\n'
    'Tipo de Ente Governamental: - Pere. Red. Compra Gov.: - Base de Cálculo: -\n'
    'Aliq. CBS: - Pere. Red. Alig. CBS: - Alia. Efet. CBS: - Valor CBS: -\n'
    'Alig. IBS Est,: - Pere. Red, Alig. IBS Est,: - Aliq. Efet. IBS Est.: - Valor IBS Est.: -\n'
    'Alig. IBS Mun.: - Perc. Red. Alig. IBS Mun.: - Alig. Efet. IBS Mun.: - Valor IBS Mun.: -\n'
    'Cód. Créd. Pres.: - Aliq. do Créd. Pres. (CBS): - Alia. do Créd. Pres. (IBS): -\n'
    'VI. do Créd, Pres, (CBS): - VI. do Créd. Pres. (IBS): -\n'
    'Classif. Tributária Regular: - Situação Tributária Regular: -\n'
    'Aliq. Efet. Regular - CBS: - Alig. Efet. Regular - IBS Estadual: - Aliq. Efet. Regular - IBS Municipal: -\n'
    'Valor CBS: - VI. IBS Regular Estadual: - MI. IBS Regular Municipal: -\n'
    'Total de Retenção Valor Total do CBS Valor Total do IBS Valor Total Liquido Valor Total da Nota Fiscal - IBS/CBS\n'
    '- - - - R$ 1.368,00 -\n'
    'ORMAÇÕES COMPLEM ARES\n'
    'PROCON Municipal Cuiabá - Endereço: R. Joaquim Murtinho, 554 - Centro, Cuiabá - MT, 78020-290 Telefone: (65) 3632-6400 PROCON\n'
    'Estadual - Endereço: Avenida Historiador Rubens de Mendonça, nº917 - Bosque da Saúde, Cuiabá - MT, 78050-000 Telefone: (65) 3613-2100 / 151\n'
    '\n'
    '. .. . » Série do Documento\n'
    'Prefeitura Municipal de Cuiabá As ota Fiscal E | Nota Fiscal de servi\n'
    '\n'
    'Secretaria Municipal de Economia Eletrônica - NFS-e\n'
    '\n'
    'Prefeitura Municipal de Cuiabá MT Eleirônica,\n'
    '\n'
    'Data de Geração da NFS-e Data de Competência Código de Autenticidade\n'
    '04/08/2026 16:41:00 04/08/2026 510334060803482670000100000000008200030826080416415523120\n'
    '\n'
    'Emitente da NFS-e Data Emissão da DPS\n'
    'Prestador 04/08/2026\n'
    '\n'
    'Consulte a autenticidade desta nota lendo o QRCode ou acessando o site: https://onlinecba.issnetonline.com.br/cuiaba/\n'
    '\n'
    'IDENTIFICAÇÃO DO PRESTADOR\n'
    'CNPJ/CPF/NIF: 36.776.200/0001-88 Inscrição Municipal: 137208758 Telefone: (65) 98157-2565\n'
    'Nome/Razão Social: FB PISOS E REVESTIMENTOS\n'
    'Nome Fantasia: FB PISOS E REVESTIMENTOS\n'
    'Endereço: Rua M4, Quadra 155, nº N2\n'
    'Cidade: Cuiabá Estado/Prov./Reg.: Mato Grosso Pais: Brasil CEP: 78043-263\n'
    'E-mail: marcosfbp(hotmail.com\n'
    'Inscrição Estadual: 13.263.227-6\n'
    '\n'
    'IDENTIFICAÇÃO DO TOMADOR\n'
    'CNPJ/CPF/NIF: 03.051.741/0001-90 Inscrição Municipal: - Telefone: -\n'
    'Nome/Razão Social: SÃO PEDRO CONSTRUTORA LTDA\n'
    'Nome Fantasia: SÃO PEDRO CONSTRUTORA LTDA\n'
    'Endereço: Av. Praia de Pajussara, nº 554, Quadra 28, Lote 09\n'
    'Cidade: Lauro de Freitas  Estado/Prov./Reg.: Bahia País: Brasil CEP:  42.708-720\n'
    '\n'
    'E-mail: -\n'
    '\n'
    'INTERMEDIÁRIO DO SERVIÇO NÃO IDENTIFICADO NA NFS-E\n'
    'DESTINATÁRIO DO SERVIÇO NÃO IDENTIFICADO NA NFS-E\n'
    '\n'
    'DADOS DO SERVIÇO PRESTADO\n'
    'Cód. Trib. Nacional: 07.06.02 NBS: 07.06.02.00 Atividade Municipal: 14330-4/05 Aplicação de revestimentos e de resinas\n'
    '\n'
    'Local da Prestação: Cuiabá - MT País Resultado da Prestação do Serviço: -\n'
    'VI. do Serviço: R$1.368,00 VI. do Desc. Incondicionado: - MI. do Desc. Condicionado: -\n'
    'Descrição dos Serviços e Materiais:\n'
    '\n'
    'Prestação de serviços de instalação de piso tátil, referente à demanda da\n'
    'SÃO PEDRO CONSTRUTORA LTDA.\n'
    '\n'
    'CONTA BANCÁRIA PARA DEPÓSITO: R$ 1.368,00\n'
    '\n'
    'BANCO: 0260 AGÊNCIA: 0001 CONTA: 32242182-6\n'
    '\n'
    'IMPOSTO SOBRE SERVIÇO DE QUALQUER NATUREZA - ISSQN\n'
    'Tipo Tributação: Operação Tributável Tipo Susp. Exig.: - Nº Proc. Susp.: -\n'
    'Município de Incidência: Cuiabá - MT Tipo de Retenção: Não Retido Valor Dedução: R$0,00\n'
    'Base de Cálculo: R$1.368,00 Alíquota: 5% VI. ISSQN: R$68,40\n'
    '\n'
    'TRIBUTAÇÃO NACIONAL\n'
    '\n'
    'CST: Operação Tributável com Alíquota Básica\n'
    'Tipo de Retenção: PIS/COFINS/CSLL Não Retidos VI. PIS: R$8,88 VI. COFINS: R$40,92\n'
    'MI. CSLL: - VI. IRRF: - VI. CP Retido: -\n'
    '\n'
    'IMPOSTO E CONTRIBUIÇÃO SOBRE BENS E SERVIÇOS - IBS/CBS\n'
    'Cód. Ind. Op.: - Classif. Tributária: - Situação Tributária: -\n'
    'Municipio de Incidência: - Tipo de Operação: -\n'
    'Tipo de Ente Governamental: - Perc. Red. Compra Gov.: - Base de Cálculo: -\n'
    '\n'
    'Aliq. CBS: - Perc. Red. Aliq. CBS: - a o Valor CBS: -\n'
    'Aliq. IBS Est.: - Perc. Red. Alig. IBS Est.: - - Valor IBS Est.: -\n'
    'Aliq. IBS Mun.: - Perc. Red. Alig. IBS Mun.: - - Valor IBS Mun.: -\n'
    '\n'
    'Cód. Créd. Pres.: - Aliq. do Créd. Pres. (CBS): - Aliq. do Créd. Pres. (IBS): -\n'
    'VI. do Créd. Pres. (CBS): - VI. do Créd. Pres. (IBS): -\n'
    '\n'
    'Classif. Tributária Regular: - Situação Tributária Regular: -\n'
    'Alíig. Efet. Regular - CBS: - Aliq. Efet. Regular - IBS Estadual: - Alíq. Efet. Regular - IBS Municipal: -\n'
    'Valor CBS: - VI. IBS Regular Estadual: - Mi. IBS Regular Municipal: -\n'
    '\n'
    'Total de Retenção Valor Total do CBS Valor Total do IBS Valor Total Líquido Valor Total da Nota Fiscal - IBS/CBS\n'
    '- - - - R$ 1.368,00 -\n'
    'NFORMAÇÕO OMPLEMENTARES\n'
    '\n'
    'PROCON Municipal Cuiabá - Endereço: R. Joaquim Murtinho, 554 - Centro, Cuiabá - MT, 78020-290 Telefone: (65) 3632-6400 PROCON\n'
    'Estadual - Endereço: Avenida Historiador Rubens de Mendonça, nº917 - Bosque da Saúde, Cuiabá - MT, 78050-000 Telefone: (65) 3613-2100 / 151\n'
    '\n'
    '\n'
    ''
)
MOCK_COM_RECUT = "Número da Nota Fiscal\n308\n" + "\n" + MOCK_PAGINA


def _novo_extrator(texto):
    dummy_path = "tests/dummy_cuiaba_voto_sangria.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = texto
    extractor.from_ocr = True
    return extractor, dummy_path


# --------------------------------------------------------------------------
# Votação do recorte dedicado — o defeito real. Não havia NENHUMA cobertura
# desta lógica: o teste pré-existente (`test_cuiaba_issnet_numero_recut.py`)
# faz mock do texto JÁ prependado e nunca exercita a votação.
# --------------------------------------------------------------------------
def _pagina_falsa():
    """Página mínima: só precisa devolver um pixmap cujo PNG o PIL abra."""
    buf = io.BytesIO()
    Image.new("RGB", (200, 200), "white").save(buf, format="PNG")
    dados = buf.getvalue()

    class _Pix:
        def tobytes(self, _formato):
            return dados

    class _Page:
        def get_pixmap(self, matrix=None):
            return _Pix()

    return _Page()


def _sequencia_de_leituras(monkeypatch, leituras):
    """Devolve as leituras na ORDEM em que a função consulta o Tesseract:
    zoom 6 (PSM 6, PSM 7), zoom 8 (PSM 6, PSM 7), zoom 10 (PSM 6, PSM 7)."""
    estado = {"i": 0}

    def _falso(_crop, lang=None, config=None):
        i = estado["i"]
        estado["i"] += 1
        return leituras[i] if i < len(leituras) else ""

    monkeypatch.setattr(pytesseract, "image_to_string", _falso)


def test_sangria_de_digito_nao_destroi_mais_o_consenso(monkeypatch):
    """Os 6 votos REAIS desta nota: 3 leituras que concordam em 308, duas
    delas com um dígito de sangria colado numa 2ª linha."""
    _sequencia_de_leituras(monkeypatch, ["308", "", "308\n2", "", "308\n5", ""])
    assert SPPdfExtractor._ocr_numero_box_cuiaba(_pagina_falsa()) == (
        "Número da Nota Fiscal\n308\n")


def test_consenso_limpo_de_uma_linha_segue_valendo(monkeypatch):
    """Regressão das 3 notas em que o recorte foi calibrado (205/16/10): uma
    leitura já limpa não muda de comportamento."""
    _sequencia_de_leituras(monkeypatch, ["205"] * 6)
    assert SPPdfExtractor._ocr_numero_box_cuiaba(_pagina_falsa()) == (
        "Número da Nota Fiscal\n205\n")


def test_um_psm_so_ainda_vence_se_concordar_entre_zooms(monkeypatch):
    """Achado já documentado: em algumas notas só UM dos PSM lê o número (o
    outro vem vazio). Isso continua aceito, porque os 3 votos vêm de zooms
    diferentes."""
    _sequencia_de_leituras(monkeypatch, ["", "16", "", "16", "", "16"])
    assert SPPdfExtractor._ocr_numero_box_cuiaba(_pagina_falsa()) == (
        "Número da Nota Fiscal\n16\n")


def test_concordancia_dentro_de_um_unico_zoom_e_rejeitada(monkeypatch):
    """A guarda que impede a normalização de fabricar consenso falso: dois PSM
    do MESMO zoom leem o mesmo bitmap, então concordarem não é evidência de
    que o dígito é real. Sem zooms distintos -> vazio."""
    _sequencia_de_leituras(monkeypatch, ["", "", "9699\n1", "9699\n2", "", ""])
    assert SPPdfExtractor._ocr_numero_box_cuiaba(_pagina_falsa()) == ""


def test_leituras_divergentes_continuam_sem_consenso(monkeypatch):
    """Sem nenhuma concordância, devolve vazio (a extração cai no fallback
    honesto), em vez de escolher um dígito qualquer."""
    _sequencia_de_leituras(monkeypatch, ["1", "", "2", "", "3", ""])
    assert SPPdfExtractor._ocr_numero_box_cuiaba(_pagina_falsa()) == ""


# --------------------------------------------------------------------------
# Extração ponta a ponta desta nota
# --------------------------------------------------------------------------
def test_layout_detectado_como_cuiaba():
    extractor, dummy_path = _novo_extrator(MOCK_PAGINA)
    try:
        assert extractor._detect_layout() == LAYOUT_CUIABA
    finally:
        os.remove(dummy_path)


def test_numero_308_extraido_com_o_recorte():
    extractor, dummy_path = _novo_extrator(MOCK_COM_RECUT)
    try:
        nfse = extractor.parse()
        assert nfse.numero == "308"
        assert nfse.numero != "00000000"
    finally:
        os.remove(dummy_path)


def test_sem_o_recorte_o_numero_nao_e_fabricado():
    """O texto de página inteira NÃO permite recuperar o número: as duas
    âncoras falham e o "208" que o OCR funde ao letterhead é uma leitura
    ERRADA (o número real é 308). Nada no caminho de texto deve capturá-lo —
    o correto aqui é o sentinela, e é o que trava este teste."""
    extractor, dummy_path = _novo_extrator(MOCK_PAGINA)
    try:
        nfse = extractor.parse()
        assert "MT 208" in MOCK_PAGINA          # o erro de OCR está no fixture
        assert nfse.numero != "208"             # e nunca deve virar o número
        assert nfse.numero == "00000000"
    finally:
        os.remove(dummy_path)


def test_demais_campos_da_nota_308():
    extractor, dummy_path = _novo_extrator(MOCK_COM_RECUT)
    try:
        nfse = extractor.parse()
        assert nfse.valores.valor_servicos == 1368.00
        assert nfse.valores.valor_iss == 68.40
        assert nfse.prestador.razao_social == "FB PISOS E REVESTIMENTOS"
        assert nfse.tomador.razao_social == "SÃO PEDRO CONSTRUTORA LTDA"
        assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M") == "04/08/2026 16:41"
    finally:
        os.remove(dummy_path)


# --------------------------------------------------------------------------
# Os 3 campos que este template pós-reforma mudou de lugar/formato
# --------------------------------------------------------------------------
CODIGO_AUTENTICIDADE = "510334060803482670000100000000008200030826080416415523120"


def test_codigo_de_autenticidade_de_57_digitos_vai_para_o_codigo_verificacao():
    """O template antigo traz um código alfanumérico MISTO de 7-10 caracteres
    ("3B3DC3576"); este traz 57 dígitos PUROS, que a busca por letra+dígito
    rejeitava — o campo caía no sentinela "XXXX-XXXX" com aviso, apesar de
    estar impresso e legível (confirmado na imagem em zoom 16x).

    Não é a Chave de Acesso nacional de 50 dígitos: os 7 primeiros dígitos
    ("5103340") não são o IBGE de Cuiabá (5103403). É código próprio da
    plataforma, então vai para o XML como impresso — mesma decisão já tomada
    para a chave do LAYOUT_NACIONAL."""
    extractor, dummy_path = _novo_extrator(MOCK_COM_RECUT)
    try:
        nfse = extractor.parse()
        assert nfse.codigo_verificacao == CODIGO_AUTENTICIDADE
        assert len(nfse.codigo_verificacao) == 57
        assert not any("digo de verifica" in aviso for aviso in nfse.avisos)
    finally:
        os.remove(dummy_path)


def test_codigo_de_autenticidade_divergente_entre_os_passes_cai_no_sentinela():
    """A guarda que impede um código plausível-porém-errado: o risco desta
    leitura é o OCR errar a CONTAGEM de uma corrida de zeros (o código tem
    várias). `_ocr_page` concatena 2 passes de OCR da mesma página, então o
    código aparece 2x, lido de forma independente — só aceitamos quando as
    ocorrências CONCORDAM. Aqui a 2ª ocorrência perde um zero; o resultado
    correto é o sentinela + aviso, não escolher uma das duas."""
    assert MOCK_COM_RECUT.count(CODIGO_AUTENTICIDADE) == 2
    truncado = CODIGO_AUTENTICIDADE.replace("00001", "0001", 1)
    texto = MOCK_COM_RECUT.replace(CODIGO_AUTENTICIDADE, truncado, 1)
    extractor, dummy_path = _novo_extrator(texto)
    try:
        nfse = extractor.parse()
        assert nfse.codigo_verificacao == "XXXX-XXXX"
        assert any("digo de verifica" in aviso for aviso in nfse.avisos)
    finally:
        os.remove(dummy_path)


def test_item_lista_servico_vem_do_codigo_de_tributacao_nacional():
    """A grade de atividade do template antigo (alíquota | item LC116 | NBS de
    9 dígitos) não existe mais aqui — a seção "DADOS DO SERVIÇO PRESTADO" traz
    "Cód. Trib. Nacional: 07.06.02". Sem âncora nesse rótulo o código caía no
    default genérico "03115". 07.06 da LC 116/2003 é justamente instalação de
    revestimentos, o serviço desta nota."""
    extractor, dummy_path = _novo_extrator(MOCK_COM_RECUT)
    try:
        nfse = extractor.parse()
        assert nfse.servico_codigo == "0706"
        assert nfse.servico_codigo != "03115"
    finally:
        os.remove(dummy_path)


def test_item_lista_servico_nao_pega_o_codigo_do_rotulo_vizinho_nbs():
    """Na MESMA linha, o rótulo vizinho repete o código com um 4º par
    ("NBS: 07.06.02.00" — o OCR lê "NES:"). A âncora é o rótulo, não o
    formato, justamente para não depender de qual dos dois vem primeiro."""
    assert "07.06.02.00" in MOCK_PAGINA
    extractor, dummy_path = _novo_extrator(MOCK_COM_RECUT)
    try:
        assert extractor.parse().servico_codigo == "0706"
    finally:
        os.remove(dummy_path)


def test_codigo_cnae_vem_da_atividade_municipal_sem_o_digito_de_prefixo():
    """`CodigoCnae` era HARDCODED como "0000000" no transformer, para todos os
    layouts. Esta nota imprime "Atividade Municipal: 14330-4/05 Aplicação de
    revestimentos e de resinas": o rótulo é MUNICIPAL, e o código traz um
    dígito de prefixo do município à esquerda da subclasse (confirmado na
    imagem em zoom 10x — não é ruído de OCR). A subclasse CNAE são os 4 dígitos
    antes do "-", e a leitura se autoconfirma pela descrição impressa ao lado,
    que é a descrição oficial da subclasse 4330-4/05."""
    extractor, dummy_path = _novo_extrator(MOCK_COM_RECUT)
    try:
        nfse = extractor.parse()
        assert nfse.codigo_cnae == "4330405"
    finally:
        os.remove(dummy_path)


def test_codigo_cnae_continua_no_default_quando_a_nota_nao_o_imprime():
    """A mudança no transformer é aditiva: sem `codigo_cnae` extraído, o XML
    segue com o "0000000" que todos os layouts sempre emitiram — é o que
    impede esta correção de mexer nos outros 54 layouts."""
    extractor, dummy_path = _novo_extrator(
        MOCK_COM_RECUT.replace("Atividade Municipal:", "Atividade Xxxxxxxxx:"))
    try:
        nfse = extractor.parse()
        assert nfse.codigo_cnae is None
        assert "<CodigoCnae>0000000</CodigoCnae>" in \
            Abrasf201Transformer().transform(nfse)
    finally:
        os.remove(dummy_path)


def test_endereco_com_numero_marcado_por_n_em_posicao_variavel():
    """O endereço deixou de ter um rótulo por componente e virou UMA linha de
    texto livre, com os componentes separados por vírgula e o número marcado
    por "nº" — em posição VARIÁVEL (3º segmento no prestador, 2º no tomador):

        prestador: "Endereço: Rua M4, Quadra 155, nº N2"
        tomador:   "Endereço: Av. Praia de Pajussara, nº 554, Quadra 28, Lote 09"

    A quebra genérica por vírgula tratava o 2º segmento como número e o 3º
    como bairro, então saía Numero="Quadra 155"/Bairro="nº N2" no prestador e
    Numero="nº 554"/Bairro="Quadra 28" no tomador — campos trocados, com o
    "nº" ainda colado. O bairro NÃO é impresso neste template: vai para o
    sentinela "Não informado" em vez de receber um pedaço do endereço."""
    extractor, dummy_path = _novo_extrator(MOCK_COM_RECUT)
    try:
        nfse = extractor.parse()
        p = nfse.prestador.endereco
        assert (p.logradouro, p.numero, p.complemento) == ("Rua M4", "N2", "Quadra 155")
        assert p.bairro == "Não informado"
        tm = nfse.tomador.endereco
        assert tm.logradouro == "Av. Praia de Pajussara"
        assert tm.numero == "554"
        assert tm.complemento == "Quadra 28, Lote 09"
        assert tm.bairro == "Não informado"
        # Município/UF/CEP dos dois lados já saíam certos e seguem certos.
        assert (p.municipio, p.uf, p.cep) == ("Cuiabá", "MT", "78043263")
        assert (tm.municipio, tm.uf, tm.cep) == ("Lauro de Freitas", "BA", "42708720")
    finally:
        os.remove(dummy_path)


def test_xml_final_da_nota_308():
    """Os 3 campos corrigidos como a Domínio os recebe. `CodigoTributacaoMunicipio`
    segue espelhando o `ItemListaServico` (comportamento compartilhado por todos
    os layouts neste transformer), apesar de esta nota imprimir um código de
    atividade municipal próprio — limite conhecido, fora do escopo."""
    extractor, dummy_path = _novo_extrator(MOCK_COM_RECUT)
    try:
        xml = Abrasf201Transformer().transform(extractor.parse())
        assert "<Numero>308</Numero>" in xml
        assert f"<CodigoVerificacao>{CODIGO_AUTENTICIDADE}</CodigoVerificacao>" in xml
        assert "<ItemListaServico>0706</ItemListaServico>" in xml
        assert "<CodigoCnae>4330405</CodigoCnae>" in xml
        assert "<Endereco>Rua M4</Endereco>" in xml
        assert "<Numero>N2</Numero>" in xml
        assert "<Numero>554</Numero>" in xml
        assert "<ValorServicos>1368.00</ValorServicos>" in xml
        assert "<ValorIss>68.40</ValorIss>" in xml
    finally:
        os.remove(dummy_path)
