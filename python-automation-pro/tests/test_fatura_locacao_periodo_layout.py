# -*- coding: utf-8 -*-
r"""Novo layout: "FATURA DE LOCAÇÃO Nº <id>" com grade PERÍODO DE REFERÊNCIA
(`fatura_locacao_periodo`), achado real 2026-10-28: `LOCACAO OBRA - 18 DE
AGOSTO.pdf` e `LOCACAO OBRA - 19 DE AGOSTO.pdf` (PDF DIGITAL, 1 página cada,
fatura em cima e boleto Bradesco embaixo). EXTREMA LOCACAO DE EQUIPAMENTOS LTDA
(CNPJ 15.756.706/0001-55, Extrema/MG) -> H. Z. PATRIMONIAL LTDA. (CNPJ
10.791.569/0001-76, Lauro de Freitas/BA): ND-025919 (5 itens, R$ 350,00) e
ND-025924 (1 item, R$ 400,00).

Antes deste layout as duas caíam em LAYOUT_FATURA_LOCACAO_GENERICA (só pela
frase "FATURA DE LOCAÇÃO") e saíam com Numero "09" (a "Carteira" do boleto),
prestador e tomador "Não Identificado", valor 0,00 e a linha digitável do
boleto como discriminação.

`MOCK_ND025919`/`MOCK_ND025924` são o texto REAL que o `pdfminer.extract_text`
entrega (o `raw_text` do `parse`), verbatim. Quirks que travam regressões:
  - a tabela de itens sai POR COLUNA (quantidades, unidades, descrições,
    unitários, totais) intercalada com Observações/Contrato/Parcelas, em ordem
    diferente nas duas faturas (5 itens x 1 item);
  - a linha do ENDEREÇO do tomador quebra em "LAURO \nDE FREITAS";
  - a linha "ENTREGA ..." (endereço de entrega) e o "Pagador" do boleto
    repetem o tomador - nunca são a fonte;
  - o boleto traz "Carteira 09", "Nosso Número", linha digitável e
    "Número do Documento ND-0259xx" - nenhum deles é o Numero.
"""
import pytest

from src.extractors import fatura_locacao_periodo as fl
from src.extractors.pdf_extractor import (
    LAYOUT_FATURA_LOCACAO_GENERICA, LAYOUT_FATURA_LOCACAO_PERIODO, SPPdfExtractor, _ibge_resolver,
)
from src.transformers.abrasf_transformer import Abrasf201Transformer

MOCK_ND025919 = 'EXTREMA LOCACAO DE EQUIPAMENTOS LTDA\n\nAVENIDA DELEGADO WALDEMAR GOMES PINTO, 564\nPONTE NOVA - CEP:37640-000\nFONE: (35)3435-5921 - EXTREMA - MG\nCNPJ (MF): 15.756.706/0001-55\nINSC. ESTADUAL: 0019828430045\nE-MAIL: financeiromegalocacao@gmail.com\nNATUREZA  DA  OPERAÇÃO\nFatura de Locação de bens móveis\n\nTELEFONE\n\nPERÍODO  DE  REFERÊNCIA\n30 Dias : 21/07/2026 08:03 - 20/08/2026 08:03\n\nTOMADOR  -  RAZÃO  SOCIAL\nH. Z. PATRIMONIAL LTDA.\n\nENDEREÇO\n\nAVENIDA LUIZ TARQUINIO PONTES, 2580 - SALA 311 EDF VILLAS EMPRESARIAL I - BURAQUINHO - LAURO \nDE FREITAS - BA - 42700-130\n\nFATURA  DE\n\nLOCAÇÃO\n\nNº ND-025919\n\nDATA DE EMISSÃO\n21/07/2026\n\nC.N.P.J  /  CPF\n10.791.569/0001-76\n\nINSC  ESTADUAL  /  RG\nISENTO\n\nENTREGA H. Z. PATRIMONIAL LTDA.: AVENIDA LUIZ TARQUINIO PONTES, 2580 - SALA 311 EDF VILLAS EMPRESARIAL \n\nINSC  MUNICIPAL\n\nI - BURAQUINHO - LAURO DE FREITAS - BA - 42700-130 - CNPJ: 10.791.569/0001-76\n\nQuantidade Unidade\n\nDiscriminação\n\nValor Unitário\n\nValor Total\n\n1\n1\n1\n1\n1\n\nUN\nUN\nUN\nUN\nUN\n\n(061-0340X) MOTOR P/BETONEIRA\n(007-0337X) BETONEIRA 400L\nCJ TOMADA MACHO/ FEMEA JG COMUT\nDISJUNTOR\nJG P/ COMUTAÇÃO 127/220V\n\nObservações\n[Nota Fiscal (observação)]\n\nParcelas\nVencimento 18/08/2026 R$ 350,00\n\n50,00\n300,00\n0,00\n0,00\n0,00\n\nContrato\nLOC 023371\n\n50,00\n300,00\n0,00\n0,00\n0,00\n\nVALOR TOTAL\nR$ 350,00\n\nBeneficiário\nEXTREMA LOCACAO DE EQUIPAMENTOS LTDA\n\nAgência / Código Beneficiário\n0915-6/0005550-6\n\nMoeda\nR$\n\nNosso Número\n09/23700021856-4\n\nNúmero do Documento\nND-025919\n\nContrato\nLOC  023371\n\nCPF/CEI/CNPJ\n15.756.706/0001-55\n\nVencimento\n18/08/2026\n\n(=) Valor do Documento\n\n350,00\n\n23790.91503 92370.002187 56000.555005  3  15420000035000\n\nAutenticação Mecânica\n\n- Recibo do Pagador\n2ª via\n\n237-2\n\n23790.91503 92370.002187 56000.555005  3  15420000035000\n\nLocal de Pagamento\n\nPAGÁVEL PREFERENCIALMENTE NAS AGÊNCIAS BRADESCO\n\nBeneficiário\n\nEXTREMA LOCACAO DE EQUIPAMENTOS LTDA\nAVENIDA DELEGADO WALDEMAR GOMES PINTO , 564 -  - PONTE NOVA - EXTREMA - MG - 37640000\n\n15.756.706/0001-55\n\nCNPJ:\n\nData Documento\n21/07/2026\nUso do Banco\n\nNúmero do Documento\nND-025919\nCarteira\n\n09\n\nEspécie Moeda\nR$\n\nEspécie Doc.\nDS\n\nQuantidade\n\nAceite\n\nN\n\nData Processamento\n21/07/2026\nValor\n\nx\n\nVencimento\n\n18/08/2026\n\nAgência / Código Beneficiário\n\nNosso Número\n\n0915-6/0005550-6\n\n09/23700021856-4\n\n(=) Valor do Documento\n\n350,00\n\nInstruções:                                            (Todas as informações deste bloqueto são de exclusiva responsabilidade do beneficiário)\n\n(27)\n\n(-) Desconto\n\nAPÓS O VENCIMENTO, COBRAR MULTA DE 2,00% E JUROS DE 0,04% AO DIA.\n\n(35)\n\n(-) Outras Deduções/Abatimento\n\nTÍTULO SUJEITO A PROTESTO APÓS 5 DIAS DO VENCIMENTO.\n\n(19)\n\n(+) Mora/Multa/Juros\n\n(+) Outros Acréscimos\n\n(=) Valor Cobrado\n\nPagador\nH. Z. PATRIMONIAL LTDA.\nAVENIDA LUIZ TARQUINIO PONTES, 2580 - SALA 311 EDF VILLAS EMPRESARIAL I - BURAQUINHO - LAURO DE FREITAS - BA -\n\n10.791.569/0001-76\n\nSacador / Avalista\n\n2ª via\n\nAutenticação  Mecânica  -  Ficha  de  Compensação\n\n'

MOCK_ND025924 = 'EXTREMA LOCACAO DE EQUIPAMENTOS LTDA\n\nAVENIDA DELEGADO WALDEMAR GOMES PINTO, 564\nPONTE NOVA - CEP:37640-000\nFONE: (35)3435-5921 - EXTREMA - MG\nCNPJ (MF): 15.756.706/0001-55\nINSC. ESTADUAL: 0019828430045\nE-MAIL: financeiromegalocacao@gmail.com\nNATUREZA  DA  OPERAÇÃO\nFatura de Locação de bens móveis\n\nTELEFONE\n\nPERÍODO  DE  REFERÊNCIA\n03 Dias : 22/07/2026 07:16 - 25/07/2026 07:16\n\nTOMADOR  -  RAZÃO  SOCIAL\nH. Z. PATRIMONIAL LTDA.\n\nENDEREÇO\n\nAVENIDA LUIZ TARQUINIO PONTES, 2580 - SALA 311 EDF VILLAS EMPRESARIAL I - BURAQUINHO - LAURO \nDE FREITAS - BA - 42700-130\n\nFATURA  DE\n\nLOCAÇÃO\n\nNº ND-025924\n\nDATA DE EMISSÃO\n22/07/2026\n\nC.N.P.J  /  CPF\n10.791.569/0001-76\n\nINSC  ESTADUAL  /  RG\nISENTO\n\nENTREGA H. Z. PATRIMONIAL LTDA.: AVENIDA LUIZ TARQUINIO PONTES, 2580 - SALA 311 EDF VILLAS EMPRESARIAL \n\nINSC  MUNICIPAL\n\nI - BURAQUINHO - LAURO DE FREITAS - BA - 42700-130 - CNPJ: 10.791.569/0001-76\n\nQuantidade Unidade\n\nDiscriminação\n\n1\n\nUN\n\n(004-0316X) COMPACTADOR PERCUSSAO\n\nObservações\n[Nota Fiscal (observação)]\n\nValor Unitário\n\n400,00\n\nContrato\nLOC 023378\n\nValor Total\n\n400,00\n\nParcelas\nVencimento 19/08/2026 R$ 400,00\n\nVALOR TOTAL\nR$ 400,00\n\nBeneficiário\nEXTREMA LOCACAO DE EQUIPAMENTOS LTDA\n\nAgência / Código Beneficiário\n0915-6/0005550-6\n\nMoeda\nR$\n\nNosso Número\n09/23700021859-9\n\nNúmero do Documento\nND-025924\n\nContrato\nLOC  023378\n\nCPF/CEI/CNPJ\n15.756.706/0001-55\n\nVencimento\n19/08/2026\n\n(=) Valor do Documento\n\n400,00\n\n23790.91503 92370.002187 59000.555009  4  15430000040000\n\nAutenticação Mecânica\n\n- Recibo do Pagador\n2ª via\n\n237-2\n\n23790.91503 92370.002187 59000.555009  4  15430000040000\n\nLocal de Pagamento\n\nPAGÁVEL PREFERENCIALMENTE NAS AGÊNCIAS BRADESCO\n\nBeneficiário\n\nEXTREMA LOCACAO DE EQUIPAMENTOS LTDA\nAVENIDA DELEGADO WALDEMAR GOMES PINTO , 564 -  - PONTE NOVA - EXTREMA - MG - 37640000\n\n15.756.706/0001-55\n\nCNPJ:\n\nData Documento\n22/07/2026\nUso do Banco\n\nNúmero do Documento\nND-025924\nCarteira\n\n09\n\nEspécie Moeda\nR$\n\nEspécie Doc.\nDS\n\nQuantidade\n\nAceite\n\nN\n\nData Processamento\n22/07/2026\nValor\n\nx\n\nVencimento\n\n19/08/2026\n\nAgência / Código Beneficiário\n\nNosso Número\n\n0915-6/0005550-6\n\n09/23700021859-9\n\n(=) Valor do Documento\n\n400,00\n\nInstruções:                                            (Todas as informações deste bloqueto são de exclusiva responsabilidade do beneficiário)\n\n(27)\n\n(-) Desconto\n\nAPÓS O VENCIMENTO, COBRAR MULTA DE 2,00% E JUROS DE 0,04% AO DIA.\n\n(35)\n\n(-) Outras Deduções/Abatimento\n\nTÍTULO SUJEITO A PROTESTO APÓS 5 DIAS DO VENCIMENTO.\n\n(19)\n\n(+) Mora/Multa/Juros\n\n(+) Outros Acréscimos\n\n(=) Valor Cobrado\n\nPagador\nH. Z. PATRIMONIAL LTDA.\nAVENIDA LUIZ TARQUINIO PONTES, 2580 - SALA 311 EDF VILLAS EMPRESARIAL I - BURAQUINHO - LAURO DE FREITAS - BA -\n\n10.791.569/0001-76\n\nSacador / Avalista\n\n2ª via\n\nAutenticação  Mecânica  -  Ficha  de  Compensação\n\n'


def _converter(monkeypatch, tmp_path, texto, nome="fatura.pdf"):
    pdf = tmp_path / nome
    pdf.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: texto)
    return SPPdfExtractor(str(pdf)).parse_multiple()


def _uma_nota(monkeypatch, tmp_path, texto):
    notas = _converter(monkeypatch, tmp_path, texto)
    assert len(notas) == 1
    return notas[0]


def _extrair(texto):
    ex = SPPdfExtractor.__new__(SPPdfExtractor)
    return fl.extrair(texto, _ibge_resolver, lambda d: SPPdfExtractor._validate_cnpj_cpf(ex, d))


# ---------------------------------------------------------------------------
# Detecção
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("texto", [MOCK_ND025919, MOCK_ND025924])
def test_detecta_nos_dois_detectores(tmp_path, texto):
    pdf = tmp_path / "f.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    ex = SPPdfExtractor(str(pdf))
    ex.raw_text = texto
    assert ex._detect_layout() == LAYOUT_FATURA_LOCACAO_PERIODO
    assert ex._detect_layout_page(texto) == LAYOUT_FATURA_LOCACAO_PERIODO


@pytest.mark.parametrize("rotulo", [
    "PERÍODO  DE  REFERÊNCIA", "NATUREZA  DA  OPERAÇÃO", "TOMADOR  -  RAZÃO  SOCIAL",
    "DATA DE EMISSÃO", "Valor Unitário", "Parcelas", "Nº ND-025919",
])
def test_sem_um_rotulo_estrutural_nao_e_este_layout(rotulo):
    assert fl.eh_fatura_locacao_periodo(MOCK_ND025919)
    assert not fl.eh_fatura_locacao_periodo(MOCK_ND025919.replace(rotulo, "XXXX"))


def test_nfse_nunca_e_este_layout():
    assert not fl.eh_fatura_locacao_periodo("NFS-e - Nota Fiscal de Serviços Eletrônica\n" + MOCK_ND025919)


def test_fatura_locacao_generica_loc_bahia_continua_generica(tmp_path):
    from tests.test_fatura_locacao_generica_layout import MOCK_TEXT
    assert not fl.eh_fatura_locacao_periodo(MOCK_TEXT)
    pdf = tmp_path / "g.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    ex = SPPdfExtractor(str(pdf))
    ex.raw_text = MOCK_TEXT
    assert ex._detect_layout() == LAYOUT_FATURA_LOCACAO_GENERICA


# ---------------------------------------------------------------------------
# Faturas reais completas
# ---------------------------------------------------------------------------

def _confere_entidades(nf):
    p = nf.prestador
    assert p.cnpj_cpf == "15756706000155"
    assert p.razao_social == "EXTREMA LOCACAO DE EQUIPAMENTOS LTDA"
    assert p.endereco.logradouro == "AVENIDA DELEGADO WALDEMAR GOMES PINTO"
    assert p.endereco.numero == "564"
    assert p.endereco.bairro == "PONTE NOVA"
    assert p.endereco.cep == "37640000"
    assert p.endereco.codigo_municipio == "3125101"  # Extrema/MG (API IBGE)
    assert p.endereco.uf == "MG"
    assert p.telefone == "3534355921"
    t = nf.tomador
    assert t.cnpj_cpf == "10791569000176"
    assert t.razao_social == "H. Z. PATRIMONIAL LTDA."
    assert t.endereco.logradouro == "AVENIDA LUIZ TARQUINIO PONTES"
    assert t.endereco.numero == "2580"
    assert t.endereco.complemento == "SALA 311 EDF VILLAS EMPRESARIAL I"
    assert t.endereco.bairro == "BURAQUINHO"
    assert t.endereco.codigo_municipio == "2919207"  # Lauro de Freitas/BA
    assert t.endereco.uf == "BA"
    assert t.endereco.cep == "42700130"
    assert nf.intermediario is None


def _confere_convencao(nf):
    v = nf.valores
    assert v.base_calculo == 0.0 and v.aliquota == 0.0 and v.valor_iss == 0.0
    assert v.iss_retido is False
    assert nf.servico_codigo == "0601"
    assert nf.codigo_verificacao == "FATURA"
    assert nf.optante_simples_nacional is False
    assert any("FATURA DE LOCAÇÃO" in a and "não é NFS-e" in a for a in nf.avisos)
    assert not any("não identificados" in a for a in nf.avisos)
    assert not any("diverge" in a for a in nf.avisos)
    for boleto in ("23790", "09/237000", "0915-6"):
        assert boleto not in nf.discriminacao


def test_campos_da_fatura_nd025919(monkeypatch, tmp_path):
    nf = _uma_nota(monkeypatch, tmp_path, MOCK_ND025919)
    assert nf.numero == "25919"
    assert nf.data_emissao.strftime('%Y-%m-%dT%H:%M:%S') == "2026-07-21T00:00:00"
    assert nf.competencia.strftime('%Y-%m-%d') == "2026-07-01"
    assert nf.valores.valor_servicos == pytest.approx(350.00)
    assert nf.valores.valor_liquido_nfse == pytest.approx(350.00)
    assert nf.discriminacao == (
        "FATURA DE LOCAÇÃO Nº ND-025919 | ITENS: 1 UN (061-0340X) MOTOR P/BETONEIRA R$ 50,00; "
        "1 UN (007-0337X) BETONEIRA 400L R$ 300,00; 1 UN CJ TOMADA MACHO/ FEMEA JG COMUT R$ 0,00; "
        "1 UN DISJUNTOR R$ 0,00; 1 UN JG P/ COMUTAÇÃO 127/220V R$ 0,00 | "
        "PERÍODO: 30 Dias : 21/07/2026 08:03 - 20/08/2026 08:03 | CONTRATO: LOC 023371 | "
        "VENCIMENTO: 18/08/2026 R$ 350,00")
    _confere_entidades(nf)
    _confere_convencao(nf)


def test_campos_da_fatura_nd025924(monkeypatch, tmp_path):
    nf = _uma_nota(monkeypatch, tmp_path, MOCK_ND025924)
    assert nf.numero == "25924"
    assert nf.data_emissao.strftime('%Y-%m-%dT%H:%M:%S') == "2026-07-22T00:00:00"
    assert nf.competencia.strftime('%Y-%m-%d') == "2026-07-01"
    assert nf.valores.valor_servicos == pytest.approx(400.00)
    assert nf.discriminacao == (
        "FATURA DE LOCAÇÃO Nº ND-025924 | ITENS: 1 UN (004-0316X) COMPACTADOR PERCUSSAO R$ 400,00 | "
        "PERÍODO: 03 Dias : 22/07/2026 07:16 - 25/07/2026 07:16 | CONTRATO: LOC 023378 | "
        "VENCIMENTO: 19/08/2026 R$ 400,00")
    _confere_entidades(nf)
    _confere_convencao(nf)


@pytest.mark.parametrize("texto, numero, valor", [
    (MOCK_ND025919, "25919", "350.00"), (MOCK_ND025924, "25924", "400.00"),
])
def test_xml_final(monkeypatch, tmp_path, texto, numero, valor):
    xml = Abrasf201Transformer().transform(_uma_nota(monkeypatch, tmp_path, texto))
    for trecho in (
        f"<Numero>{numero}</Numero>", "<CodigoVerificacao>FATURA</CodigoVerificacao>",
        "<Competencia>2026-07-01</Competencia>", f"<ValorServicos>{valor}</ValorServicos>",
        f"<ValorLiquidoNfse>{valor}</ValorLiquidoNfse>", "<ValorIss>0.00</ValorIss>",
        "<Aliquota>0.00</Aliquota>", "<IssRetido>2</IssRetido>",
        "<ItemListaServico>0601</ItemListaServico>", "<CodigoTributacaoMunicipio>0601</CodigoTributacaoMunicipio>",
        "<Cnpj>15756706000155</Cnpj>", "<Cnpj>10791569000176</Cnpj>",
        "<CodigoMunicipio>3125101</CodigoMunicipio>", "<CodigoMunicipio>2919207</CodigoMunicipio>",
        "<Cep>37640000</Cep>", "<Cep>42700130</Cep>", "<Bairro>BURAQUINHO</Bairro>",
        "<MunicipioIncidencia>3125101</MunicipioIncidencia>",
    ):
        assert trecho in xml, trecho
    assert "<Intermediario" not in xml
    assert "2927408" not in xml  # nunca o default de Salvador


# ---------------------------------------------------------------------------
# Itens (colunas do pdfminer)
# ---------------------------------------------------------------------------

def test_itens_reconstruidos_das_colunas():
    nota = _extrair(MOCK_ND025919)
    assert [(i.descricao, i.quantidade, i.valor_unitario, i.valor_total) for i in nota.itens] == [
        ("(061-0340X) MOTOR P/BETONEIRA", 1, 50.0, 50.0),
        ("(007-0337X) BETONEIRA 400L", 1, 300.0, 300.0),
        ("CJ TOMADA MACHO/ FEMEA JG COMUT", 1, 0.0, 0.0),
        ("DISJUNTOR", 1, 0.0, 0.0),
        ("JG P/ COMUTAÇÃO 127/220V", 1, 0.0, 0.0),
    ]


def test_colunas_que_nao_fecham_levam_so_descricoes_com_aviso():
    texto = MOCK_ND025919.replace("50,00\n300,00\n0,00\n0,00\n0,00\n\nContrato",
                                  "50,00\n300,00\n0,00\n0,00\n\nContrato")
    nota = _extrair(texto)
    assert nota.itens == []
    assert "ITENS: (061-0340X) MOTOR P/BETONEIRA; (007-0337X) BETONEIRA 400L;" in nota.discriminacao
    assert any("não reconstruída" in a for a in nota.avisos)
    assert nota.valores.valor_servicos == pytest.approx(350.0)  # o VALOR TOTAL impresso vale


def test_total_que_nao_fecha_com_itens_e_parcelas_mantem_o_impresso_e_avisa():
    texto = MOCK_ND025919.replace("VALOR TOTAL\nR$ 350,00", "VALOR TOTAL\nR$ 360,00")
    nota = _extrair(texto)
    assert nota.valores.valor_servicos == pytest.approx(360.0)
    assert any("diverge da soma dos itens" in a for a in nota.avisos)
    assert any("diverge da soma das parcelas" in a for a in nota.avisos)


def test_observacao_real_entra_na_discriminacao_e_o_placeholder_nao():
    assert "OBS:" not in _extrair(MOCK_ND025924).discriminacao
    texto = MOCK_ND025924.replace("[Nota Fiscal (observação)]", "OBRA RUA X")
    nota = _extrair(texto)
    assert nota.discriminacao.endswith("| OBS: OBRA RUA X")
    assert [i.descricao for i in nota.itens] == ["(004-0316X) COMPACTADOR PERCUSSAO"]


# ---------------------------------------------------------------------------
# Sentinelas e fontes proibidas
# ---------------------------------------------------------------------------

def test_sem_numero_da_fatura_vira_sentinela_e_nunca_o_do_boleto():
    nota = _extrair(MOCK_ND025924.replace("Nº ND-025924", "Nº"))
    assert nota.numero == "00000000"
    assert any("Número da fatura" in a for a in nota.avisos)


def test_numero_divergente_do_boleto_avisa():
    texto = MOCK_ND025924.replace("Número do Documento\nND-025924", "Número do Documento\nND-025925", 1)
    assert any("difere do \"Número do Documento\"" in a for a in _extrair(texto).avisos)


def test_cnpj_do_locador_com_dv_invalido_vira_sentinela():
    nota = _extrair(MOCK_ND025924.replace("CNPJ (MF): 15.756.706/0001-55", "CNPJ (MF): 15.756.706/0001-56"))
    assert nota.prestador.cnpj_cpf == "00000000000000"
    assert any("CNPJ do locador" in a for a in nota.avisos)


def test_tomador_vem_do_endereco_e_nao_da_entrega():
    texto = MOCK_ND025924.replace("ENTREGA H. Z. PATRIMONIAL LTDA.: AVENIDA LUIZ TARQUINIO PONTES",
                                  "ENTREGA H. Z. PATRIMONIAL LTDA.: RUA DA OBRA")
    texto = texto.replace("I - BURAQUINHO - LAURO DE FREITAS - BA - 42700-130 - CNPJ",
                          "I - CENTRO - CAMACARI - BA - 42800-000 - CNPJ")
    t = _extrair(texto).tomador
    assert (t.endereco.logradouro, t.endereco.bairro, t.endereco.cep) == (
        "AVENIDA LUIZ TARQUINIO PONTES", "BURAQUINHO", "42700130")


def test_endereco_do_tomador_fora_do_padrao_avisa_e_nao_inventa():
    texto = MOCK_ND025924.replace("DE FREITAS - BA - 42700-130\n\nFATURA", "DE FREITAS\n\nFATURA")
    nota = _extrair(texto)
    assert nota.tomador.endereco.cep == "00000000"
    assert nota.tomador.endereco.bairro == "Não informado"
    assert any("Endereço do tomador fora do padrão" in a for a in nota.avisos)


def test_separar_endereco_tomador():
    assert fl.separar_endereco_tomador(
        "AVENIDA LUIZ TARQUINIO PONTES, 2580 - SALA 311 EDF VILLAS EMPRESARIAL I - BURAQUINHO - "
        "LAURO DE FREITAS - BA - 42700-130") == (
        "AVENIDA LUIZ TARQUINIO PONTES", "2580", "SALA 311 EDF VILLAS EMPRESARIAL I",
        "BURAQUINHO", "LAURO DE FREITAS", "BA", "42700130")
    assert fl.separar_endereco_tomador("RUA A, 10 - CENTRO - EXTREMA - MG - 37640-000") == (
        "RUA A", "10", None, "CENTRO", "EXTREMA", "MG", "37640000")
    assert fl.separar_endereco_tomador("RUA A, 10 - EXTREMA") is None


def test_extrema_mg_esta_na_tabela_ibge():
    assert _ibge_resolver.KNOWN_CITIES["EXTREMA"] == "3125101"
