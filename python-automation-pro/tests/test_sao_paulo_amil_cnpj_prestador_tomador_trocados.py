# -*- coding: utf-8 -*-
"""NFS-e São Paulo/SP digital (template com rótulo "Bairro:", extrator próprio
`_extrair_entidade_sao_paulo`), nota 72483704, prestador AMIL ASSISTÊNCIA MÉDICA
INTERNACIONAL SA -> tomador SAMP ADMINISTRACAO LTDA, com boleto anexo na mesma
página.

Bug real (2026-10-20): o XML saía com os CPF/CNPJ de prestador e tomador
TROCADOS — os dois com dígito verificador válido, então nada barrava. Causa: a
regra "1º CNPJ válido do documento = prestador, 2º = tomador" usava a varredura
tolerante `_scavenge_all_cnpjs`, que atravessa quebras de linha; o "3" final do
código de verificação "8CHGHGH3" grudava no CNPJ do prestador logo abaixo
(15 dígitos, descartado), e o 1º CNPJ válido passava a ser o do tomador.

MOCK_TEXT é o texto REAL do pdfminer desta página, verbatim. O PDF original é
protegido por senha; a senha NÃO faz parte do repositório (nem é necessária:
o texto já está embutido aqui).
"""
import re

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_SAO_PAULO
from src.models.nfse_models import Entidade, Endereco

# CPF/CNPJ montados a partir da forma impressa (com pontuação).
CNPJ_AMIL = re.sub(r'\D', '', '29.309.127/0001-79')
CNPJ_SAMP = re.sub(r'\D', '', '33.903.444/0001-96')

MOCK_TEXT = """PREFEITURA DO MUNICÍPIO DE SÃO PAULO
SECRETARIA MUNICIPAL DE FINANÇAS
NOTA FISCAL DE SERVIÇOS ELETRÔNICA - NFS-e

Número da Nota:
72483704
Data e Hora de Emissão:

03/09/2026 07:51:40

Código de Verificação:

8CHGHGH3

29.309.127/0001-79

PRESTADOR DE SERVIÇOS
Inscrição municipal:

39569896

AMIL ASSISTÊNCIA MÉDICA INTERNACIONAL SA

AV AV DOUTOR CHUCRI ZAIDAN - S/N 0 AND 6 A 23 TORRE EZ

CPF/CNPJ
Nome/Razão
Endereço
Bairro:

VILA SAO FRANCISCO (ZONA SUL)

 Município:

SAO PAULO

UF

SP

CEP

04711-130

Nome/Razão

SAMP ADMINISTRACAO LTDA

CPF/CNPJ

33.903.444/0001-96

Inscrição municipal:

TOMADOR DE SERVIÇOS

Endereço

RUA WALDEMAR FALCAO 000641 APT 1701

Bairro:

CANDEAL

E-mail:

MARXAVLIM@YAHOO.COM.BR

COBERTURA DE CUSTOS DE ASSISTÊNCIA MÉDICA E HOSPITALAR

REFERENTE AO PERÍODO DE: 18/09/2026 À 17/10/2026

 Município:

SALVADOR

UF:

BA

CEP:

40296-710

DISCRIMINAÇÃO DOS SERVIÇOS

R$ 7.095,55

Vencto:

18/09/2026

206808200/0

Compe: Setembro/2026

Código do Serviço

05312 - Planos de saúde que se cumpram através de serviços de terceiros contratados e credenciados.

VALOR TOTAL DA NOTA =

R$ 7.095,55

Valor Total das Deduções

Desconto Incond.

Base de Cálculo

Alíquota (%)

Valor ISS

Crédito p/ Abatimento do IPTU

0,00

0,00

7.095,55

2,00

141,91

0,00

- Esta NFS-e foi emitida com respaldo na Lei n. 14.097/2005
- Esta NFS-e substitui o RPS No.26420275 Série PJSPS, emitido em 03/09/2026

OUTRAS INFORMAÇÕES

Autenticação Mecânica

RECIBO DO PAGADOR

341-7 34191.09263 95575.002936 83957.670009 1 15730000709555

Local de Pagamento
PAGAVEL EM QUALQUER BANCO ATE O VENCIMENTO

Beneficiário
AMIL ASSISTENCIA MEDICA INTERNACIONAL SA

Data Documento

Número Documento

03/09/2026

206808200

Uso Banco

Instruções

Carteira

109

Espécie
R$

Após o vencimento pagar preferencialmente no Banco Itaú.
Valor da Mora por dia de atraso : R$ 2,36
Após Vencimento : R$ 141,91 de multa

Espécie Documento

RECIBO

Quantidade

Aceite

N

Valor

Beneficiário:
Endereço:
CNPJ:

AMIL ASSISTENCIA MEDICA INTERNACIONAL SA
AV AV DOUTOR CHUCRI ZAIDAN - S/N 0 AND 6 A 23 TORRE EZ
29.309.127/0001-79

Pagador

SAMP ADMINISTRACAO LTDA

18/09/2026

2938/39576-7

109-26955750-0

R$ 7.095,55

Vencimento

Agência / Código Beneficiário

Data Processamento
03/09/2026

Nosso Número

Valor do Documento

(-) Desconto

(-) Outras Deduções

(+) Mora / Multa

(+) Outros Acréscimos

(=) Valor Cobrado

RUA WALDEMAR FALCAO 000641 APT 1701

CANDEAL
CPF/CNPJ: 33.903.444/0001-96

Pagador Avalista:

SALVADOR

BA

40296-710

Código de Baixa

Autenticação Mecânica - FICHA DE COMPENSAÇÃO

PAGUE AQUI - PIX

"""

# Só a NFS-e, sem o boleto anexo: a correção na causa não depende do boleto.
MOCK_TEXT_SEM_BOLETO = MOCK_TEXT.split("Autenticação Mecânica\n\nRECIBO DO PAGADOR")[0]


def _parse(monkeypatch, tmp_path, texto):
    pdf = tmp_path / "amil_72483704.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: texto)
    notas = SPPdfExtractor(str(pdf)).parse_multiple()
    assert len(notas) == 1
    return notas[0]


def _extrator(tmp_path, texto):
    pdf = tmp_path / "amil_72483704_unit.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    ex = SPPdfExtractor(str(pdf))
    ex.raw_text = texto
    ex.layout = LAYOUT_SAO_PAULO
    return ex


def _entidade(cnpj, razao):
    return Entidade(cnpj_cpf=cnpj, razao_social=razao, endereco=Endereco(
        logradouro="X", numero="S/N", bairro="Y", codigo_municipio="3550308",
        municipio="SAO PAULO", uf="SP", cep="00000000"))


def test_detecta_sao_paulo(tmp_path):
    assert _extrator(tmp_path, MOCK_TEXT)._detect_layout() == LAYOUT_SAO_PAULO


def test_prestador_e_tomador_com_cnpj_certo(monkeypatch, tmp_path):
    nfse = _parse(monkeypatch, tmp_path, MOCK_TEXT)
    assert nfse.numero == "72483704"
    assert nfse.prestador.cnpj_cpf == CNPJ_AMIL
    assert nfse.prestador.razao_social == "AMIL ASSISTÊNCIA MÉDICA INTERNACIONAL SA"
    assert nfse.prestador.inscricao_municipal == "39569896"
    assert nfse.prestador.endereco.cep == "04711130"
    assert nfse.tomador.cnpj_cpf == CNPJ_SAMP
    assert nfse.tomador.razao_social == "SAMP ADMINISTRACAO LTDA"
    assert nfse.tomador.endereco.bairro == "CANDEAL"
    assert nfse.tomador.endereco.uf == "BA"
    assert nfse.tomador.endereco.cep == "40296710"
    assert nfse.tomador.email == "MARXAVLIM@YAHOO.COM.BR"
    assert nfse.valores.valor_servicos == pytest.approx(7095.55)
    assert nfse.valores.valor_iss == pytest.approx(141.91)
    # A extração já sai certa: a guarda do boleto não tem o que corrigir.
    assert not any("TROCADOS" in a or "troca" in a for a in nfse.avisos)


def test_sem_boleto_cnpjs_continuam_certos(monkeypatch, tmp_path):
    """Caso degradado: só a NFS-e (sem a evidência do boleto) — a atribuição
    ancorada no bloco "Nome/Razão" do tomador resolve sozinha."""
    assert "Beneficiário" not in MOCK_TEXT_SEM_BOLETO
    nfse = _parse(monkeypatch, tmp_path, MOCK_TEXT_SEM_BOLETO)
    assert nfse.prestador.cnpj_cpf == CNPJ_AMIL
    assert nfse.tomador.cnpj_cpf == CNPJ_SAMP


def test_varredura_tolerante_gruda_codigo_de_verificacao():
    """Documenta a causa: a varredura tolerante perde o CNPJ do prestador
    no cabeçalho (o "3" do código de verificação gruda nele)."""
    ex = SPPdfExtractor.__new__(SPPdfExtractor)
    ex.raw_text = MOCK_TEXT_SEM_BOLETO
    assert ex._scavenge_all_cnpjs()[0] == CNPJ_SAMP
    assert [d[2] for d in ex._docs_formatados_validos(MOCK_TEXT_SEM_BOLETO)] == [CNPJ_AMIL, CNPJ_SAMP]


def test_boleto_identifica_beneficiario_e_pagador(tmp_path):
    achados = _extrator(tmp_path, MOCK_TEXT)._docs_do_boleto(MOCK_TEXT)
    assert achados["beneficiario"][0] == CNPJ_AMIL
    assert achados["pagador"][0] == CNPJ_SAMP


def test_guarda_corrige_cnpjs_trocados_pelo_boleto(tmp_path):
    ex = _extrator(tmp_path, MOCK_TEXT)
    p, t, avisos = ex._conferir_papeis_pelo_boleto(
        _entidade(CNPJ_SAMP, "AMIL ASSISTÊNCIA MÉDICA INTERNACIONAL SA"),
        _entidade(CNPJ_AMIL, "SAMP ADMINISTRACAO LTDA"))
    assert p.cnpj_cpf == CNPJ_AMIL
    assert t.cnpj_cpf == CNPJ_SAMP
    assert p.razao_social.startswith("AMIL") and t.razao_social.startswith("SAMP")
    assert len(avisos) == 1 and "TROCADOS" in avisos[0]


def test_guarda_so_avisa_sem_corroboracao_do_nome(tmp_path):
    """Papéis cruzados, mas nenhuma razão social confere com o boleto: não
    troca nada (não há evidência suficiente) — só avisa."""
    ex = _extrator(tmp_path, MOCK_TEXT)
    p, t, avisos = ex._conferir_papeis_pelo_boleto(
        _entidade(CNPJ_SAMP, "OUTRA EMPRESA QUALQUER LTDA"),
        _entidade(CNPJ_AMIL, "MAIS OUTRA EMPRESA LTDA"))
    assert p.cnpj_cpf == CNPJ_SAMP and t.cnpj_cpf == CNPJ_AMIL
    assert len(avisos) == 1 and "Possível troca" in avisos[0]


def test_guarda_so_avisa_com_cruzamento_parcial(tmp_path):
    """Só o tomador recebeu o CNPJ do beneficiário (prestador com outro CNPJ):
    contradição parcial -> aviso, nada é trocado."""
    outro = re.sub(r'\D', '', '11.222.333/0001-81')
    ex = _extrator(tmp_path, MOCK_TEXT)
    p, t, avisos = ex._conferir_papeis_pelo_boleto(
        _entidade(outro, "AMIL ASSISTÊNCIA MÉDICA INTERNACIONAL SA"),
        _entidade(CNPJ_AMIL, "SAMP ADMINISTRACAO LTDA"))
    assert p.cnpj_cpf == outro and t.cnpj_cpf == CNPJ_AMIL
    assert len(avisos) == 1 and "BENEFICIÁRIO" in avisos[0]


def test_guarda_nao_dispara_com_papeis_coerentes_ou_sem_boleto(tmp_path):
    ok = (_entidade(CNPJ_AMIL, "AMIL ASSISTÊNCIA MÉDICA INTERNACIONAL SA"),
          _entidade(CNPJ_SAMP, "SAMP ADMINISTRACAO LTDA"))
    assert _extrator(tmp_path, MOCK_TEXT)._conferir_papeis_pelo_boleto(*ok)[2] == []
    trocados = (ok[0].model_copy(update={"cnpj_cpf": CNPJ_SAMP}),
                ok[1].model_copy(update={"cnpj_cpf": CNPJ_AMIL}))
    p, t, avisos = _extrator(tmp_path, MOCK_TEXT_SEM_BOLETO)._conferir_papeis_pelo_boleto(*trocados)
    assert avisos == [] and p.cnpj_cpf == CNPJ_SAMP
