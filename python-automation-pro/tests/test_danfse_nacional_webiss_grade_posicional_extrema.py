# -*- coding: utf-8 -*-
r"""WebISS PÓS-REFORMA / Município de Extrema/MG (achado real, nota nº
2026000130650, D-SAAS TECNOLOGIA EM DESENVOLVIMENTO DE SOFTWARE LTDA ->
CONDOMINIO EDIFICIO TK TOWER, R$335,00): reportado pelo usuário — "Corrigir a
extração do valor da nota fiscal, o valor correto é: R$ 335,00, sempre o valor
dos serviços, antes das retenções ou descontos".

Mesma `LAYOUT_NACIONAL` e mesma plataforma WebISS já cobertas pela nota de
Aracaju (`test_danfse_nacional_aracaju_webiss.py`), mas com a grade despejada
pelo pdfminer numa forma DIFERENTE: lá rótulo e valor saem INTERCALADOS, aqui
saem os 8 RÓTULOS em sequência e só então os 8 VALORES. A extração por
PROXIMIDADE do rótulo, calibrada em Aracaju, casa o vizinho errado nesta forma:

    Valor dos Serviços (R$) | Deduções | Desc. Cond. | Desc. Incond. |
    B.C. do ISS | Alíquota ISS (%) | ISS (R$) | ISS Retido (R$
    335,00 | 0,00 | 0,00 | 0,00 | 335,00 | 2,00 | 6,70 | ****

    B.C. do IBS/CBS (R$) | Alíquota IBS/CBS (%) | Redução IBS/CBS (%) |
    IBS (R$) | CBS (R$) | Valor Líquido (R$) | Valor Total (R$
    328,30 | 0,10/0,90 | 0,00/0,00 | 0,33 | 2,95 | 335,00 | 335,00

O rótulo "Valor Líquido (R$)" fica colado ao 1º valor da 2ª linha — que é a
**B.C. do IBS/CBS** (328,30 = 335,00 − 6,70 de ISS), base de OUTRO tributo — e
"ISS (R$)" ao 1º valor da 1ª linha (335,00). O XML saía com
`ValorServicos`/`BaseCalculo`/`ValorLiquidoNfse` = 328,30 e `ValorIss` = 335,00,
um ISS MAIOR que o próprio serviço.

Essa 2ª linha de grade (IBS/CBS) é da reforma tributária e não existia na
variante de Aracaju — é ela que cria o vizinho errado. IBS e CBS não têm campo
equivalente no ABRASF 2.01 e ficam de fora do XML, mesma decisão já tomada em
`LAYOUT_NACIONAL_REFORMA`.

Corrigido com mapeamento por ÍNDICE (convenção de Guarulhos/Campinas/Monte
Santo/Goiânia), disparado só quando os 8 rótulos aparecem em sequência
CONTÍGUA — na forma de Aracaju eles saem separados pelos próprios valores, e lá
o caminho por proximidade continua intacto.

Texto REAL extraído via pdfminer (`extract_text`), direto do PDF original —
nunca digitado à mão.
"""
import os

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_EXTREMA = (
    'MUNICÍPIO DE EXTREMA\n'
    '\n'
    'Secretaria Municipal de Planejamento, Orçamento e Gestão\n'
    'Gerência de Arrecadação - Av. Delegado Waldemar Gomes Pinto, Nº 1624, Da Ponte\n'
    'Nova - CEP: 37.640-000 - Extrema/MG Telefone: (35) 3435-6829\n'
    '\n'
    'NOTA FISCAL DE SERVIÇOS ELETRÔNICA - NFS-e\n'
    'RPS número 751957 Série RPS emitido em 15/08/2026\n'
    '\n'
    'Emissão (Horário de Brasília)\n'
    '\n'
    'Período de Competência\n'
    '\n'
    'Município de Prestação do Serviço\n'
    '\n'
    '15/08/2026 05:47:45\n'
    'Reg. Especial Tributação\n'
    '\n'
    '08/2026\n'
    'Exigibilidade do ISS\n'
    '\n'
    'Extrema - MG\n'
    '\n'
    'Nenhum\n'
    '\n'
    'Exigível em Extrema\n'
    '\n'
    'PRESTADOR DE SERVIÇOS\n'
    'Razão Social\n'
    '\n'
    'D-SAAS TECNOLOGIA EM DESENVOLVIMENTO DE SOFTWARE LTDA\n'
    '\n'
    'Nome Fantasia\n'
    '\n'
    'D-SAAS\n'
    '\n'
    'CPF/CNPJ\n'
    '\n'
    'Inscrição Municipal\n'
    '\n'
    'Inscrição Estadual\n'
    '\n'
    'Simples Nacional\n'
    '\n'
    'Incentivador Cultural\n'
    '\n'
    'Fone/Fax\n'
    '\n'
    'Email\n'
    '\n'
    'minhafatura@neotagus.com.br\n'
    '\n'
    '46.220.369/0002-91\n'
    '\n'
    '0018022\n'
    '\n'
    'Não\n'
    '\n'
    'Não\n'
    '\n'
    '(11) 5199-9199\n'
    '\n'
    'Endereço\n'
    '\n'
    'ESTRADA MUNICIPAL DA REPRESA, 917, D-SAAS, PESSEGUEIROS - CEP: 37640-000 - Extrema - MG\n'
    '\n'
    'TOMADOR DE SERVIÇOS\n'
    '\n'
    'Nome/Razão Social\n'
    '\n'
    'CONDOMINIO EDIFICIO TK TOWER\n'
    '\n'
    'CPF/CNPJ\n'
    '\n'
    'Inscrição Municipal\n'
    '\n'
    'Inscrição Estadual\n'
    '\n'
    'Fone/Fax\n'
    '\n'
    'E-mail\n'
    '\n'
    '07.834.816/0001-60\n'
    '\n'
    'Endereço\n'
    '\n'
    'nf@tkpatrimonial.com.br\n'
    '\n'
    'AV PROFESSOR MAGALHAES NETO1856, 1856 - PITUBA - CEP: 41810-012 - Salvador - BA\n'
    '\n'
    'SERVIÇO PRESTADO\n'
    '0105 - Licenciamento ou cessão de direito de uso de programas de computação. CNAE: 6202300. NBS: 111032200.\n'
    '\n'
    'DESCRIÇÃO DOS SERVIÇOS\n'
    '** Use nosso aplicativo para registro de marcacao de ponto! ** Servicos Prestados: MDACESSO CLOUD LICENCA PARA 01 PONTO referente\n'
    'ao inicio do periodo 15/08/2026 .\n'
    'Fatura: 533308743 Informacoes Adicionais:\n'
    '\n'
    'CONFORME LEI 12.741/2012 o valor aproximado dos tributos e R$ 55,04 (16,43%), FONTE: IBPT/empresometro.com.br (21.1.F)\n'
    '\n'
    'TRIBUTOS FEDERAIS\n'
    '\n'
    'INSS (R$)\n'
    '\n'
    '0,00\n'
    '\n'
    'IR (R$)\n'
    '\n'
    '0,00\n'
    '\n'
    'PIS (R$)\n'
    '\n'
    '0,00\n'
    '\n'
    'COFINS (R$)\n'
    '\n'
    '0,00\n'
    '\n'
    'CSLL (R$)\n'
    '\n'
    '0,00\n'
    '\n'
    'Outras Retenções (R$\n'
    '\n'
    '0,00\n'
    '\n'
    'VALORES\n'
    '\n'
    'Valor dos Serviços (R$)\n'
    '\n'
    'Deduções (R$)\n'
    '\n'
    'Desc. Cond. (R$)\n'
    '\n'
    'Desc. Incond. (R$)\n'
    '\n'
    'B.C. do ISS (R$)\n'
    '\n'
    'Alíquota ISS (%)\n'
    '\n'
    'ISS (R$)\n'
    '\n'
    'ISS Retido (R$\n'
    '\n'
    '335,00\n'
    '\n'
    '0,00\n'
    '\n'
    '0,00\n'
    '\n'
    '0,00\n'
    '\n'
    '335,00\n'
    '\n'
    '2,00\n'
    '\n'
    '6,70\n'
    '\n'
    '****\n'
    '\n'
    'B.C. do IBS/CBS (R$)\n'
    '\n'
    'Alíquota IBS/CBS (%)\n'
    '\n'
    'Redução IBS/CBS (%)\n'
    '\n'
    'IBS (R$)\n'
    '\n'
    'CBS (R$)\n'
    '\n'
    'Valor Líquido (R$)\n'
    '\n'
    'Valor Total (R$\n'
    '\n'
    '328,30\n'
    '\n'
    '0,10/0,90\n'
    '\n'
    '0,00/0,00\n'
    '\n'
    '0,33\n'
    '\n'
    '2,95\n'
    '\n'
    '335,00\n'
    '\n'
    '335,00\n'
    '\n'
    'OUTRAS INFORMAÇÕES\n'
    'Trib. aprox. R$ 45,06 Federal e R$ 9,98 Municipal. Fonte: IBPT [92589A]\n'
    'Chave de Acesso da NFS-e Nacional: 31251011246220369000291202600013065026080035008892\n'
    'CST: 000, cClassTrib: 000001, cIndOp: 100501.\n'
    '\n'
    ' \n'
    ' \n'
    'Visualizado em: 27/08/2026 16:31:51 | Para validação desta NFSe acesse: http://extremamg.webiss.com.br/externo/nfse/validar\n'
    'Esta NFS-e é autodeclaratória. Esta NFS-e foi emitida com respaldo no Decreto nº 2.948 de 27 de novembro de 2015.\n'
    '\n'
    ''
)


def _parse(texto, monkeypatch):
    dummy_path = "tests/dummy_danfse_webiss_extrema.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text",
                        lambda path: texto)
    try:
        extractor = SPPdfExtractor(dummy_path)
        return extractor, extractor.parse()
    finally:
        os.remove(dummy_path)


def test_valor_dos_servicos_e_o_valor_bruto_da_nota(monkeypatch):
    """O defeito reportado: R$335,00, não os R$328,30 que vinham da coluna
    vizinha."""
    extractor, nfse = _parse(MOCK_EXTREMA, monkeypatch)
    assert extractor.layout == "danfse_nacional"
    v = nfse.valores
    assert v.valor_servicos == pytest.approx(335.00)
    assert v.valor_servicos != pytest.approx(328.30)


def test_328_30_e_base_do_ibs_cbs_e_nao_entra_em_nenhum_campo(monkeypatch):
    """328,30 é a B.C. do IBS/CBS (335,00 − 6,70 de ISS) — base de outro
    tributo, que o ABRASF 2.01 não tem onde registrar. Não pode reaparecer em
    campo nenhum do XML, que era exatamente o defeito (ele ocupava Valor dos
    Serviços, Base de Cálculo e Valor Líquido ao mesmo tempo)."""
    _, nfse = _parse(MOCK_EXTREMA, monkeypatch)
    v = nfse.valores
    for campo in ("valor_servicos", "base_calculo", "valor_liquido_nfse",
                  "valor_iss", "valor_deducoes", "desconto_incondicionado",
                  "desconto_condicionado"):
        assert getattr(v, campo) != pytest.approx(328.30), campo


def test_grade_inteira_mapeada_por_indice(monkeypatch):
    """As 8 colunas da 1ª linha na ordem impressa, mais o Valor Líquido da 2ª.
    A alíquota (2,00%) vinha zerada e o ISS vinha com o valor do serviço."""
    _, nfse = _parse(MOCK_EXTREMA, monkeypatch)
    v = nfse.valores
    assert v.valor_servicos == pytest.approx(335.00)
    assert v.valor_deducoes == pytest.approx(0.00)
    assert v.desconto_condicionado == pytest.approx(0.00)
    assert v.desconto_incondicionado == pytest.approx(0.00)
    assert v.base_calculo == pytest.approx(335.00)
    assert v.aliquota == pytest.approx(0.02)
    assert v.valor_iss == pytest.approx(6.70)
    assert v.valor_liquido_nfse == pytest.approx(335.00)


def test_identidade_contabil_fecha(monkeypatch):
    """base × alíquota == ISS. Não é usada para derivar nada aqui — serve de
    juiz de que as 3 células vieram da mesma linha, e não de vizinhas."""
    _, nfse = _parse(MOCK_EXTREMA, monkeypatch)
    v = nfse.valores
    assert abs(v.base_calculo * v.aliquota - v.valor_iss) < 0.01


def test_iss_retido_mascarado_nao_e_fabricado(monkeypatch):
    """A nota imprime "****" na célula "ISS Retido (R$" — não há valor real
    para extrair. Fica zerado E com aviso, nunca preenchido por dedução."""
    _, nfse = _parse(MOCK_EXTREMA, monkeypatch)
    assert "****" in MOCK_EXTREMA
    assert nfse.valores.iss_retido is False
    assert nfse.valores.valor_iss_retido == pytest.approx(0.00)
    assert any("mascara" in a.lower() for a in nfse.avisos)


def test_servicos_nao_vira_o_liquido_quando_ha_retencao(monkeypatch):
    """A regra que o usuário fixou: SEMPRE o valor dos serviços, ANTES das
    retenções e descontos. Nesta nota bruto e líquido coincidem (não há
    retenção), então o caso é forçado mutando só a célula do Valor Líquido —
    o Valor dos Serviços tem de continuar 335,00."""
    mutado = MOCK_EXTREMA.replace(
        "0,33\n\n2,95\n\n335,00\n\n335,00",
        "0,33\n\n2,95\n\n300,00\n\n335,00")
    assert mutado != MOCK_EXTREMA
    _, nfse = _parse(mutado, monkeypatch)
    assert nfse.valores.valor_servicos == pytest.approx(335.00)
    assert nfse.valores.valor_liquido_nfse == pytest.approx(300.00)


def test_forma_de_aracaju_nao_dispara_o_mapeamento_posicional(monkeypatch):
    """O portão da correção: na variante de Aracaju (mesma plataforma, mesmo
    layout) o pdfminer INTERCALA rótulos e valores, então os 8 rótulos não
    formam sequência contígua e o caminho por proximidade — que lá funciona —
    continua sendo o usado. Sem este portão, a correção de uma cidade
    reescreveria a leitura das outras ~8 que compartilham `danfse_nacional`."""
    import re
    rotulos = [
        r"Valor\s+dos\s+Servi[çc]os\s*\(R\$",
        r"Dedu[çc][õo]es\s*\(R\$",
        r"Desc\.\s*Cond\.\s*\(R\$",
    ]
    assert re.search(r"\)?\s*".join(rotulos), MOCK_EXTREMA, re.IGNORECASE)

    aracaju = (
        "VALORES\n\nDeduções (R$)\n\nDesc. Cond. (R$)\n\nDesc. Incond. (R$)\n\n"
        "Base de Cálculo ISS (R$)\n\nOutras Retenções (R$)\n\n0,00\n\n"
        "Alíquota ISS (%)\n\n5,0000\n\n0,00\n\nValor dos Serviços (R$)\n\n"
        "4.000,00\n\n0,00\n\nISS (R$)\n\n*****\n\n0,00\n\n*****\n\n"
        "ISS Retido (R$)\n\nValor Líquido (R$)\n\nValor Total da Nota (R$)\n\n"
        "*****\n\n4.000,00\n\n4.000,00\n")
    assert not re.search(r"\)?\s*".join(rotulos), aracaju, re.IGNORECASE)
