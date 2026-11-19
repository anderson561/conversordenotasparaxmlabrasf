# -*- coding: utf-8 -*-
"""NFS-e de Ribeirão Pires/SP, modelo Ginfes com IBS/CBS (LAYOUT_RIBEIRAO_PIRES).

Achado real 2026-11-19: notas nº 20831 e 22716, AMBAR INOVACOES SPE LTDA ->
STAUMMAQ (Simões Filho/BA), R$ 1.000,00, PDF DIGITAL. Na main as duas caíam em
LAYOUT_SIMOES_FILHO (Numero 72 = número do endereço do prestador, valores
zerados, tomador não identificado, município Salvador).

PDFMINER_*: texto REAL do pdfminer (extract_text). COORD_*: texto REAL
reconstruído por coordenada (`_reconstruir_texto_por_coordenadas`) do mesmo PDF.
"""
import os

import pytest

from src.extractors.pdf_extractor import (
    SPPdfExtractor, LAYOUT_RIBEIRAO_PIRES, LAYOUT_SIMOES_FILHO)
from src.extractors.ribeirao_pires_texto import ler_campos
from src.transformers.abrasf_transformer import Abrasf201Transformer

PDFMINER_20831 = 'PREFEITURA MUNICIPAL DE RIBEIRÃO PIRES\n\nSECRETARIA MUNICIPAL DE FINANÇAS\n\nNOTA FISCAL DE SERVIÇO ELETRÔNICA - NFS-e\n\nRPS\n22730\n\nSérie RPS\n1\n\nTipo RPS\n1\n\nNFS-e\n20831\nCódigo de Verificação\n2LNW7XR1X\nEmissão da NFS-e\n08/10/2026 14:34:52\nNFS-e Substituída\n\nPrestador de Serviço\n\nCPF/CNPJ:\n\n59.224.647/0001-40\n\nInscrição\n\n1031550\n\nNome/Razão Social:\n\nAMBAR INOVACOES SPE LTDA\n\nEndereço\n\nRua Palmar\n\nComplemento:\n\nANDAR 3\n\nCEP:\n\n09400-360\n\nMunicípio:\n\nRIBEIRAO PIRES\n\nUF: SP\n\nNúmero:\n\n72\n\nBairro:\n\nPaís:\n\nCentro\n\nBrasil\n\nE-mail:\n\nfinanceiro@atlasinovacoes.com.br\n\nTelefone:\n\n(21)97507-5064\n\nCPF/CNPJ:\n\n02.370.080/0001-00\n\nInscrição Municipal:\n\nNIF:\n\nNome/Razão Social:\n\nSTAUMMAQ SERVICOS TECNICOS AUTOMACAO MOTORES E MAQUINAS LTDA\n\nTomador de Serviço\n\nEndereço:\n\nVIA URBANA\n\nComplemento:\n\nNúmero:\n\n1\n\nBairro:\n\nCIA Sul\n\nCEP:\n\n43721-450\n\nMunicípio: SIMOES FILHO\n\nUF: BA\n\nPaís:\n\nBrasil\n\nE-mail:\n\nbruno@staummaq.com.br\n\nTelefone:\n\n(71)99968-4922\n\nFatura: 80718 |Bronze R$ 1.000,00\n\nAtividade Econômica\n17.22 / 8.1722 - Cobrança Em Geral.\n\nDiscriminação do Serviço\n\nTipo PIS\n\nTributos Federais (R$)\nTipo COFINS\n\nINSS\n\nCOFINS\n\nApuração Própria\n\n30,00\n\nApuração Própria\n\n0,00\n\nPIS\n\n6,50\n\nIR\n\n0,00\n\nCSLL\n\n0,00\n\nValor Aproximado dos Tributos\n\nFederal\n\nEstadual Municipal\n\nFonte\n\nSimples\n\n-\n\n-\n\n-\n\n-\n\n-\n\nIdentificação Prestação de Serviços\n\nDetalhamento de Valores (R$)\n\nCódigo da Obra\n\nCódigo A.R.T.\n\nExigibilidade ISSQN\n\nRegime Especial de Tributação\n\nSimples Nacional\n\nNomenclatura Brasileira de Serviços\n\nIndicador de Operação\n\nSituação Tributária\n\nClassificação Tributária\n\nCompetência\n\nMunicípio Prestação\n\nMunícipio Incidência\n\nISSQN a Reter\n\n1-Exigível\n\n0-Nenhum\n\n( ) Sim (X) Não\n\n1.1806.20.00\n\n100301\n\n000\n\n000001\n\n10/2026\n\nRIBEIRAO PIRES - SP\n\nRIBEIRAO PIRES - SP\n\n( ) Sim (X) Não\n\nValor do Serviço\n\nDesconto Incondicionado\n\nDesconto Condicionado\n\nRetenções Federais\n\nPIS/COFINS - Apuração Própria\n\nOutras Retenções\n\nDeduções Previstas em Lei\n\nBase de Cálculo\n\nAlíquota\n\nISSQN\n\nIBS\n\nCBS\n\nContribuições Sociais - Retidas\n\nValor Líquido\n\nOutras Informações\n\n1.000,00\n\n0,00\n\n0,00\n\n0,00\n\n36,50\n\n0,00\n\n1.000,00\n\n2,00\n\n20,00\n\n0,94\n\n8,49\n0,00\n1.000,00\n\n\x0c'

COORD_20831 = 'NFS-e\nPREFEITURA MUNICIPAL DE RIBEIRÃO PIRES\n20831\nSECRETARIA MUNICIPAL DE FINANÇAS\nCódigo de Verificação\nNOTA FISCAL DE SERVIÇO ELETRÔNICA - NFS-e 2LNW7XR1X\nEmissão da NFS-e\n08/10/2026 14:34:52\nRPS Série RPS Tipo RPS NFS-e Substituída\n22730 1 1\nPrestador de Serviço\nCPF/CNPJ: 59.224.647/0001-40 Inscrição 1031550\nNome/Razão Social: AMBAR INOVACOES SPE LTDA\nEndereço Rua Palmar Número: 72\nComplemento: ANDAR 3 Bairro: Centro\nCEP: 09400-360 Município: RIBEIRAO PIRES UF: SP País: Brasil\nE-mail: financeiro@atlasinovacoes.com.br Telefone: (21)97507-5064\nTomador de Serviço\nCPF/CNPJ: 02.370.080/0001-00 Inscrição Municipal: NIF:\nNome/Razão Social: STAUMMAQ SERVICOS TECNICOS AUTOMACAO MOTORES E MAQUINAS LTDA\nEndereço: VIA URBANA Número: 1\nComplemento: Bairro: CIA Sul\nCEP: 43721-450 Município: SIMOES FILHO UF: BA País: Brasil\nE-mail: bruno@staummaq.com.br Telefone: (71)99968-4922\nAtividade Econômica\n17.22 / 8.1722 - Cobrança Em Geral.\nDiscriminação do Serviço\nFatura: 80718 |Bronze R$ 1.000,00\nTributos Federais (R$) Valor Aproximado dos Tributos\nPIS Tipo PIS COFINS Tipo COFINS INSS IR CSLL Federal Estadual Municipal Fonte Simples\n6,50 Apuração Própria 30,00 Apuração Própria 0,00 0,00 0,00 - - - - -\nIdentificação Prestação de Serviços Detalhamento de Valores (R$)\nCódigo da Obra Valor do Serviço 1.000,00\nCódigo A.R.T. Desconto Incondicionado 0,00\nExigibilidade ISSQN 1-Exigível Desconto Condicionado 0,00\nRegime Especial de Tributação 0-Nenhum Retenções Federais 0,00\nSimples Nacional ( ) Sim (X) Não PIS/COFINS - Apuração Própria 36,50\nNomenclatura Brasileira de Serviços 1.1806.20.00 Outras Retenções\nIndicador de Operação 100301 Deduções Previstas em Lei 0,00\nSituação Tributária 000 Base de Cálculo 1.000,00\nClassificação Tributária 000001 Alíquota 2,00\nCompetência 10/2026 ISSQN 20,00\nMunicípio Prestação RIBEIRAO PIRES - SP IBS 0,94\nMunícipio Incidência RIBEIRAO PIRES - SP CBS 8,49\nISSQN a Reter ( ) Sim (X) Não Contribuições Sociais - Retidas 0,00\nValor Líquido 1.000,00\nOutras Informações'

PDFMINER_22716 = 'PREFEITURA MUNICIPAL DE RIBEIRÃO PIRES\n\nSECRETARIA MUNICIPAL DE FINANÇAS\n\nNOTA FISCAL DE SERVIÇO ELETRÔNICA - NFS-e\n\nRPS\n24598\n\nSérie RPS\n1\n\nTipo RPS\n1\n\nNFS-e\n22716\nCódigo de Verificação\nON6P2G0FA\nEmissão da NFS-e\n05/11/2026 05:01:14\nNFS-e Substituída\n\nPrestador de Serviço\n\nCPF/CNPJ:\n\n59.224.647/0001-40\n\nInscrição\n\n1031550\n\nNome/Razão Social:\n\nAMBAR INOVACOES SPE LTDA\n\nEndereço\n\nRua Palmar\n\nComplemento:\n\nANDAR 3\n\nCEP:\n\n09400-360\n\nMunicípio:\n\nRIBEIRAO PIRES\n\nUF: SP\n\nNúmero:\n\n72\n\nBairro:\n\nPaís:\n\nCentro\n\nBrasil\n\nE-mail:\n\nrogerio@atlasinovacoes.com.br\n\nTelefone:\n\n(21)2391-2911\n\nCPF/CNPJ:\n\n02.370.080/0001-00\n\nInscrição Municipal:\n\nNIF:\n\nNome/Razão Social:\n\nSTAUMMAQ SERVICOS TECNICOS AUTOMACAO MOTORES E MAQUINAS LTDA\n\nTomador de Serviço\n\nEndereço:\n\nVIA URBANA\n\nComplemento:\n\nNúmero:\n\n1\n\nBairro:\n\nCIA Sul\n\nCEP:\n\n43721-450\n\nMunicípio: SIMOES FILHO\n\nUF: BA\n\nPaís:\n\nBrasil\n\nE-mail:\n\nbruno@staummaq.com.br\n\nTelefone:\n\n(71)99968-4922\n\nFatura: 82867 |Bronze R$ 1.000,00\n\nAtividade Econômica\n17.22 / 8.1722 - Cobrança Em Geral.\n\nDiscriminação do Serviço\n\nTipo PIS\n\nTributos Federais (R$)\nTipo COFINS\n\nINSS\n\nCOFINS\n\nApuração Própria\n\n30,00\n\nApuração Própria\n\n0,00\n\nPIS\n\n6,50\n\nIR\n\n0,00\n\nCSLL\n\n0,00\n\nValor Aproximado dos Tributos\n\nFederal\n\nEstadual Municipal\n\nFonte\n\nSimples\n\n-\n\n-\n\n-\n\n-\n\n-\n\nIdentificação Prestação de Serviços\n\nDetalhamento de Valores (R$)\n\nCódigo da Obra\n\nCódigo A.R.T.\n\nExigibilidade ISSQN\n\nRegime Especial de Tributação\n\nSimples Nacional\n\nNomenclatura Brasileira de Serviços\n\nIndicador de Operação\n\nSituação Tributária\n\nClassificação Tributária\n\nCompetência\n\nMunicípio Prestação\n\nMunícipio Incidência\n\nISSQN a Reter\n\n1-Exigível\n\n0-Nenhum\n\n( ) Sim (X) Não\n\n1.1806.20.00\n\n100301\n\n000\n\n000001\n\n11/2026\n\nRIBEIRAO PIRES - SP\n\nRIBEIRAO PIRES - SP\n\n( ) Sim (X) Não\n\nValor do Serviço\n\nDesconto Incondicionado\n\nDesconto Condicionado\n\nRetenções Federais\n\nPIS/COFINS - Apuração Própria\n\nOutras Retenções\n\nDeduções Previstas em Lei\n\nBase de Cálculo\n\nAlíquota\n\nISSQN\n\nIBS\n\nCBS\n\nContribuições Sociais - Retidas\n\nValor Líquido\n\nOutras Informações\n\n1.000,00\n\n0,00\n\n0,00\n\n0,00\n\n36,50\n\n0,00\n\n1.000,00\n\n2,00\n\n20,00\n\n0,94\n\n8,49\n0,00\n1.000,00\n\n\x0c'

COORD_22716 = 'NFS-e\nPREFEITURA MUNICIPAL DE RIBEIRÃO PIRES\n22716\nSECRETARIA MUNICIPAL DE FINANÇAS\nCódigo de Verificação\nNOTA FISCAL DE SERVIÇO ELETRÔNICA - NFS-e ON6P2G0FA\nEmissão da NFS-e\n05/11/2026 05:01:14\nRPS Série RPS Tipo RPS NFS-e Substituída\n24598 1 1\nPrestador de Serviço\nCPF/CNPJ: 59.224.647/0001-40 Inscrição 1031550\nNome/Razão Social: AMBAR INOVACOES SPE LTDA\nEndereço Rua Palmar Número: 72\nComplemento: ANDAR 3 Bairro: Centro\nCEP: 09400-360 Município: RIBEIRAO PIRES UF: SP País: Brasil\nE-mail: rogerio@atlasinovacoes.com.br Telefone: (21)2391-2911\nTomador de Serviço\nCPF/CNPJ: 02.370.080/0001-00 Inscrição Municipal: NIF:\nNome/Razão Social: STAUMMAQ SERVICOS TECNICOS AUTOMACAO MOTORES E MAQUINAS LTDA\nEndereço: VIA URBANA Número: 1\nComplemento: Bairro: CIA Sul\nCEP: 43721-450 Município: SIMOES FILHO UF: BA País: Brasil\nE-mail: bruno@staummaq.com.br Telefone: (71)99968-4922\nAtividade Econômica\n17.22 / 8.1722 - Cobrança Em Geral.\nDiscriminação do Serviço\nFatura: 82867 |Bronze R$ 1.000,00\nTributos Federais (R$) Valor Aproximado dos Tributos\nPIS Tipo PIS COFINS Tipo COFINS INSS IR CSLL Federal Estadual Municipal Fonte Simples\n6,50 Apuração Própria 30,00 Apuração Própria 0,00 0,00 0,00 - - - - -\nIdentificação Prestação de Serviços Detalhamento de Valores (R$)\nCódigo da Obra Valor do Serviço 1.000,00\nCódigo A.R.T. Desconto Incondicionado 0,00\nExigibilidade ISSQN 1-Exigível Desconto Condicionado 0,00\nRegime Especial de Tributação 0-Nenhum Retenções Federais 0,00\nSimples Nacional ( ) Sim (X) Não PIS/COFINS - Apuração Própria 36,50\nNomenclatura Brasileira de Serviços 1.1806.20.00 Outras Retenções\nIndicador de Operação 100301 Deduções Previstas em Lei 0,00\nSituação Tributária 000 Base de Cálculo 1.000,00\nClassificação Tributária 000001 Alíquota 2,00\nCompetência 11/2026 ISSQN 20,00\nMunicípio Prestação RIBEIRAO PIRES - SP IBS 0,94\nMunícipio Incidência RIBEIRAO PIRES - SP CBS 8,49\nISSQN a Reter ( ) Sim (X) Não Contribuições Sociais - Retidas 0,00\nValor Líquido 1.000,00\nOutras Informações'


def _parse(monkeypatch, tmp_path, pdfminer_txt, coord_txt):
    """Roda o pipeline real (`parse_multiple`) com o texto REAL das notas:
    `extract_text` devolve o texto do pdfminer e a reconstrução por
    coordenada devolve o texto reconstruído do mesmo PDF."""
    dummy = tmp_path / "rp.pdf"
    dummy.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: pdfminer_txt)
    monkeypatch.setattr(SPPdfExtractor, "_reconstruir_texto_por_coordenadas", lambda self: coord_txt)
    notas = SPPdfExtractor(str(dummy)).parse_multiple()
    assert len(notas) == 1
    return notas[0]


def _xml(nfse):
    return Abrasf201Transformer().transform(nfse)


# ---------------------------------------------------------------------------
# Detecção
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("texto", [PDFMINER_20831, PDFMINER_22716], ids=["20831", "22716"])
def test_detecta_ribeirao_pires_e_nao_simoes_filho(texto):
    """Na main a nota caía em LAYOUT_SIMOES_FILHO: o tomador STAUMMAQ é de
    Simões Filho/BA e a nota imprime "Série RPS" (marcador estrutural da rede
    de segurança do Simões Filho)."""
    ex = SPPdfExtractor.__new__(SPPdfExtractor)
    ex.raw_text = texto
    assert ex._detect_layout() == LAYOUT_RIBEIRAO_PIRES
    assert ex._detect_layout_page(texto) == LAYOUT_RIBEIRAO_PIRES


def test_simoes_filho_de_verdade_continua_simoes_filho():
    """Guarda: a rede de segurança do Simões Filho segue valendo para nota
    SEM o cabeçalho da Prefeitura de Ribeirão Pires."""
    texto = ("NOTA FISCAL DE SERVIÇO ELETRÔNICA\nSérie RPS\n1\nTomador\n"
             "Município: SIMOES FILHO\nUF: BA\nDESCONTO INCONDICIONADO\n")
    ex = SPPdfExtractor.__new__(SPPdfExtractor)
    ex.raw_text = texto
    assert ex._detect_layout() == LAYOUT_SIMOES_FILHO


# ---------------------------------------------------------------------------
# Notas reais
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("pdfminer_txt,coord_txt,numero,codigo,emissao,comp,disc,email,fone", [
    (PDFMINER_20831, COORD_20831, "20831", "2LNW7XR1X", "2026-10-08 14:34:52", "2026-10",
     "Fatura: 80718 |Bronze R$ 1.000,00", "financeiro@atlasinovacoes.com.br", "(21)97507-5064"),
    (PDFMINER_22716, COORD_22716, "22716", "ON6P2G0FA", "2026-11-05 05:01:14", "2026-11",
     "Fatura: 82867 |Bronze R$ 1.000,00", "rogerio@atlasinovacoes.com.br", "(21)2391-2911"),
], ids=["20831", "22716"])
def test_nota_real_ambar(monkeypatch, tmp_path, pdfminer_txt, coord_txt, numero, codigo,
                         emissao, comp, disc, email, fone):
    n = _parse(monkeypatch, tmp_path, pdfminer_txt, coord_txt)
    assert n.numero == numero
    assert n.codigo_verificacao == codigo
    assert n.data_emissao.strftime("%Y-%m-%d %H:%M:%S") == emissao
    assert n.competencia.strftime("%Y-%m") == comp
    assert n.discriminacao == disc
    assert n.servico_codigo == "1722"
    assert n.codigo_cnae is None  # não impresso ("8.1722" é a atividade municipal)
    assert n.optante_simples_nacional is False
    assert n.intermediario is None
    assert n.avisos == []

    p = n.prestador
    assert p.cnpj_cpf == "59224647000140"
    assert p.inscricao_municipal == "1031550"
    assert p.razao_social == "AMBAR INOVACOES SPE LTDA"
    e = p.endereco
    assert (e.logradouro, e.numero, e.complemento, e.bairro) == ("Rua Palmar", "72", "ANDAR 3", "Centro")
    assert (e.municipio, e.uf, e.cep, e.codigo_municipio) == ("RIBEIRAO PIRES", "SP", "09400360", "3543303")
    assert p.email == email and p.telefone == fone

    t = n.tomador
    assert t.cnpj_cpf == "02370080000100"
    assert t.inscricao_municipal is None
    assert t.razao_social == "STAUMMAQ SERVICOS TECNICOS AUTOMACAO MOTORES E MAQUINAS LTDA"
    e = t.endereco
    assert (e.logradouro, e.numero, e.complemento, e.bairro) == ("VIA URBANA", "1", None, "CIA Sul")
    assert (e.municipio, e.uf, e.cep, e.codigo_municipio) == ("SIMOES FILHO", "BA", "43721450", "2930709")
    assert t.email == "bruno@staummaq.com.br" and t.telefone == "(71)99968-4922"

    v = n.valores
    assert v.valor_servicos == 1000.0
    assert v.desconto_incondicionado == 0.0 and v.desconto_condicionado == 0.0
    # "Outras Retenções" EM BRANCO não desloca a grade: Deduções 0,00 e Base 1.000,00.
    assert v.valor_deducoes == 0.0
    assert v.base_calculo == 1000.0
    assert v.aliquota == pytest.approx(0.02)
    assert v.valor_iss == 20.0
    assert v.iss_retido is False and v.valor_iss_retido == 0.0
    # PIS 6,50 / COFINS 30,00 de "Apuração Própria" NÃO são retenção.
    assert v.valor_pis == 0.0 and v.valor_cofins == 0.0
    assert v.valor_inss == 0.0 and v.valor_ir == 0.0 and v.valor_csll == 0.0
    assert v.outras_retencoes == 0.0 and v.valor_contribuicoes_sociais_retidas == 0.0
    assert v.valor_liquido_nfse == 1000.0

    xml = _xml(n)
    assert f"<Numero>{numero}</Numero>" in xml
    assert "<ItemListaServico>1722</ItemListaServico>" in xml
    assert "<CodigoTributacaoMunicipio>1722</CodigoTributacaoMunicipio>" in xml
    assert "<CodigoCnae>0000000</CodigoCnae>" in xml
    assert "<IssRetido>2</IssRetido>" in xml
    assert "<ValorLiquidoNfse>1000.00</ValorLiquidoNfse>" in xml
    assert "<MunicipioIncidencia>3543303</MunicipioIncidencia>" in xml
    assert "<OrgaoGerador>\n        <CodigoMunicipio>3543303</CodigoMunicipio>" in xml
    assert "2927408" not in xml  # nada caiu no default Salvador/BA


# ---------------------------------------------------------------------------
# Variações e guardas (texto real com uma alteração pontual)
# ---------------------------------------------------------------------------

def test_pis_cofins_retidos_entram_como_retencao(monkeypatch, tmp_path):
    coord = COORD_20831.replace("6,50 Apuração Própria 30,00 Apuração Própria",
                                "6,50 Retido 30,00 Retido")
    coord = coord.replace("Retenções Federais 0,00", "Retenções Federais 36,50")
    coord = coord.replace("Valor Líquido 1.000,00", "Valor Líquido 963,50")
    n = _parse(monkeypatch, tmp_path, PDFMINER_20831, coord)
    assert n.valores.valor_pis == 6.5 and n.valores.valor_cofins == 30.0
    assert n.valores.valor_liquido_nfse == 963.5
    assert n.avisos == []


def test_tipo_pis_desconhecido_vira_aviso_sem_retencao(monkeypatch, tmp_path):
    coord = COORD_20831.replace("6,50 Apuração Própria", "6,50 Outro Regime")
    n = _parse(monkeypatch, tmp_path, PDFMINER_20831, coord)
    assert n.valores.valor_pis == 0.0
    assert any("PIS R$ 6,50 com tipo não reconhecido" in a for a in n.avisos)


def test_liquido_que_nao_fecha_mantem_impresso_e_avisa(monkeypatch, tmp_path):
    coord = COORD_20831.replace("Valor Líquido 1.000,00", "Valor Líquido 900,00")
    n = _parse(monkeypatch, tmp_path, PDFMINER_20831, coord)
    assert n.valores.valor_liquido_nfse == 900.0
    assert any("Valor Líquido impresso (R$ 900,00) não fecha" in a for a in n.avisos)


def test_iss_que_nao_fecha_com_base_aliquota_mantem_impresso(monkeypatch, tmp_path):
    coord = COORD_20831.replace("ISSQN 20,00", "ISSQN 25,00")
    n = _parse(monkeypatch, tmp_path, PDFMINER_20831, coord)
    assert n.valores.valor_iss == 25.0
    assert any("ISSQN impresso (R$ 25,00) não fecha" in a for a in n.avisos)


def test_iss_em_branco_fora_do_simples_avisa(monkeypatch, tmp_path):
    coord = COORD_20831.replace("ISSQN 20,00", "ISSQN")
    n = _parse(monkeypatch, tmp_path, PDFMINER_20831, coord)
    assert n.valores.valor_iss == 0.0
    assert any("\"ISSQN\" em branco" in a for a in n.avisos)


def test_iss_retido_marcado(monkeypatch, tmp_path):
    coord = COORD_20831.replace("ISSQN a Reter ( ) Sim (X) Não", "ISSQN a Reter (X) Sim ( ) Não")
    coord = coord.replace("Valor Líquido 1.000,00", "Valor Líquido 980,00")
    n = _parse(monkeypatch, tmp_path, PDFMINER_20831, coord)
    assert n.valores.iss_retido is True and n.valores.valor_iss_retido == 20.0
    assert n.avisos == []


def test_aliquota_acima_do_teto_vira_sentinela(monkeypatch, tmp_path):
    coord = COORD_20831.replace("Alíquota 2,00", "Alíquota 6,00")
    n = _parse(monkeypatch, tmp_path, PDFMINER_20831, coord)
    assert n.valores.aliquota == 0.0


def test_ler_campos_ignora_texto_de_outro_modelo():
    assert ler_campos("") is None
    assert ler_campos("PREFEITURA MUNICIPAL DE RIBEIRÃO PIRES\nNFS-e\n13241\nCódigo de Verificação") is None


def test_modelo_antigo_sem_coordenadas_mantem_caminho_antigo(monkeypatch):
    """Sem texto reconstruível (modelo antigo / raw_text de teste) o layout
    segue o caminho antigo: só o número da nota pelo regex histórico."""
    ex = SPPdfExtractor.__new__(SPPdfExtractor)
    ex.raw_text = "PREFEITURA MUNICIPAL DE RIBEIRÃO PIRES\nNFS-e\n13241\nCódigo de Verificação"
    ex.layout = LAYOUT_RIBEIRAO_PIRES
    monkeypatch.setattr(SPPdfExtractor, "_reconstruir_texto_por_coordenadas", lambda self: "")
    assert ex._ribeirao_pires_campos() is None
    assert ex._extrair_numero() == "13241"


_PASTA = r"L:\USUARIOS\ANDERSON\ARQUIVOS DESKTOP\Notas"


@pytest.mark.skipif(not os.path.isdir(_PASTA), reason="PDFs reais indisponíveis")
@pytest.mark.parametrize("arquivo,numero", [
    ("NF_20831_10-2026_Staummaq.pdf", "20831"),
    ("NF_22716_11-2026_Staummaq.pdf", "22716"),
])
def test_pdf_real(arquivo, numero):
    caminho = os.path.join(_PASTA, arquivo)
    if not os.path.exists(caminho):
        pytest.skip("PDF real indisponível")
    n = SPPdfExtractor(caminho).parse_multiple()[0]
    assert n.numero == numero
    assert n.valores.valor_servicos == 1000.0 and n.valores.valor_iss == 20.0
    assert n.valores.valor_liquido_nfse == 1000.0
    assert n.tomador.cnpj_cpf == "02370080000100"
    assert n.prestador.endereco.codigo_municipio == "3543303"
    assert n.avisos == []
