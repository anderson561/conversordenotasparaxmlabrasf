# -*- coding: utf-8 -*-
"""Cuiabá/MT (ISSNet) escaneado — prestador REAL deslocado para depois do
cabeçalho "Dados do Intermediário de Serviços".

Achado real (PDF "NFS PRESTADORES ANALISE DE NFS-iss e inss retido", pág. 3,
nota nº 10, DR3 TERCEIRIZAÇÃO -> SÃO PEDRO CONSTRUTORA): a ordem física do
OCR ficou mais embaralhada que a já vista na pág. 14 do MTI 03-2026 — depois
de "Dados do Prestador de Serviço" vem, SEM rótulo próprio, o CNPJ do
TOMADOR; só depois de "Dados do Intermediário de Serviços" é que aparecem os
dados REAIS do prestador (nome, endereço, CNPJ). Sem tratamento:
  - prestador saía com o CNPJ do TOMADOR e uma razão social toda quebrada
    (pescada de um trecho de rótulo garbled);
  - "intermediário" (que deveria ficar vazio) roubava os dados REAIS do
    prestador (DR3 TERCEIRIZAÇÃO, CNPJ 62.981.187/0001-09).

Corrigido em `bloco_cuiaba`: quando o bloco "normal" do prestador (entre o
cabeçalho "Dados do Prestador" e a âncora do tomador) NÃO tem a assinatura
"CPF/CNPJ" (CPF antes), procura essa assinatura no trecho entre "Dados do
Intermediário de Serviços" e "Descrição dos Serviços" — só assume o
deslocamento quando esse trecho REALMENTE a tiver. E, do lado do
intermediário, um guard simétrico: se o bloco carrega a assinatura do
PRESTADOR, não é um intermediário de verdade — devolve `None`.

Este teste usa o OCR REAL da nota (zoom 3 padrão + o recut de grade de
valores em zoom 5 já prependado pelo `_ocr_page`, mesma convenção dos
demais testes de OCR-zoom deste projeto)."""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor

# Recorte limpo (zoom 5 + PSM 6, página inteira) que `_ocr_page` prependa
# quando detecta a grade de valores truncada (nesta nota, a linha original
# só tinha 5 dos 6 tokens "R$" esperados — faltava a Base de Cálculo real).
VALORES_RECUT = (
    'Prefeitura Municipal de Cuiabá Série do Documento\n'
    'Secretaria Municipal de Economia NOTA Eletrônica - NFS-e\n'
    'Fone: () - http:/Awww.cuiaba.mt.gov.br/\n'
    'Dados do Prestador de Serviço\n'
    'DR3 TERCEIRIZACAO LTDA 06/04/2026 19:49:51\n'
    'DR3 TERCEIRIZACAO\n'
    'Rua Brigadeiro Eduardo Gomes,86 SALA: 105; - Goiabeira\n'
    'CEP 78032-030 - Fone: (65)99206-9540 - Cuiabá! MT\n'
    'genesisassessoria26(Dgmail.com E320F124C\n'
    'Inscrição Municipal 321599 - CPF/CNPJ 62.981.187/0001-09 Responsável pela Retenção\n'
    'Identificação da Nota Fiscal Eletrônica\n'
    'Natureza da Operação Número do RPS Série do RPS Data de Emissão do RPS\n'
    'Cuiabá - Mato Grosso Cuiabá - Mato Grosso\n'
    'Dados do Tomador de Serviços\n'
    'CNPJ/CPF : 03.051.741/0001-90 IM: 1492591\n'
    'Razão Social: Sao Pedro Construtora Ltda\n'
    'Endereço : Avenida Praia de Pajussara Número: 554\n'
    'Complemento : QD 28, LOTE 9 Bairro : Vilas do Atlântico\n'
    'CEP: 42708-720 Cidade/UF : Lauro de Freitas/ BA\n'
    'Telefone : (71)3272-0733 E-mail : sp(Dsaopedroconstrutora.com.br\n'
    'Dados do Intermediário de Serviços\n'
    'Descrição dos Serviços\n'
    "REJUNTAMENTO EXTERNO RAMPA DE ACESSO, ESPELHO D'ÁGUA,FACHADA ,LIMPEZA INTERNA: REVESTIMENTOS (inclusão de banheiros e piso)\n"
    'DADOS BANCARIOS\n'
    'Nome: DR3 TERCEIRIZAÇÃO\n'
    'Renata Lourenço do Nascimento\n'
    'Banco: C6 Chave Pix CNPJ 62981187000109\n'
    'Detalhamento dos Tributos\n'
    'Atividade do Município Alíquota [Item da LC 116/2003 Cód. NBS Cód. CNAE\n'
    '8121400 - [8121-4/00] Limpeza em prédios e em domicílios - 118031000 | 8121400\n'
    'VI. Total dos Serviços | Desconto Incondicionado |Deduções Base Cálculo Base de Cálculo Total do ISSQN ISSQN Retido Desconto Condicionado\n'
    'R$ 22.709,56 R$ 0,00 R$ 0,00 R$ 22.709,56 R$ 454,19 | Não R$ 0,00\n'
    'PIS COFINS INSS IRRF CSLL Outras Retenções Vi. ISSQN Retido |VI. Líquido da Nota Fiscal\n'
    'R$ 0,00 R$ 0,00 R$ 0,00 R$ 0,00 | R$ 0,00 R$ 0,00 R$ 0,00 R$ 22.709,56\n'
)

# Texto original (zoom 3 padrão) — mesma nota.
ORIGINAL_TEXT = 'Série do Documento\nNota Fiscal de Serviço\nEletrônica - NFS-e\n\nPrefeitura Municipal de Cuiabá\nSecretaria Municipal de Economia\nFone: () - http:/Awww.cuiaba.mt.gov.br/\n\nDados do Prestador de Serviço\n\nData de Geração da NFS-e\n\n06/04/2026 19:49:51\n\nData de Competência\n06/04/2026\n\nCód. de Autenticidade\n\nE320F124C\n\nResponsável pela Retenção\n\nNatureza da Operação Número do RPS Série do RPS Data de Emissão do RPS\n\nEE ER E E RO\nLocal dos Serviços Município Incidência\n\nCNPJICPF:  03.051.741/0001-90 IM: 1492591\n\nRazão Social: Sao Pedro Construtora Ltda\n\nEndereço : Avenida Praia de Pajussara Número: 554\n\nComplemento : OD 28, LOTE 9 Bairro : Vilas do Atlântico\n\nCEP: 42708-720 Cidade/UF : Lauro de Freitas/ BA\n\nTelefone : (71)3272-0733 E-mail : sp(Osaopedroconstrutora.com.br\n\nDados do Intermediário de Serviços\n\nCNPJICPF Inscrição Municipal Razão Social\n\nDR3 TERCEIRIZACAO LTDA\n\nDR3 TERCEIRIZACAO\n\nRua Brigadeiro Eduardo Gomes,86 SALA: 105; - Goiabeira\nCEP 78032-030 - Fone: (65)99206-9540 - Cuiabá/ MT\n\ngenesisassessoria26(Ogmail.com\nInscrição Municipal 321599 - CPF/CNPJ 62.981.187/0001-09\n\nDescrição dos Serviços\nREJUNTAMENTO EXTERNO RAMPA DE ACESSO, ESPELHO D\'ÁGUA,FACHADA ,LIMPEZA INTERNA: REVESTIMENTOS (inclusão de banheiros e piso)\nDADOS BANCARIOS\n\nNome: DR3 TERCEIRIZAÇÃO\n\nRenata Lourenço do Nascimento\n\nBanco: C6 Chave Pix CNPJ 62981187000109\n\nDetalhamento dos Tributos\n\nAtividade do Município Cód. CNAE\n\n8121400 - [8121-4/00] Limpeza em prédios e em domicílios - 2,00 118031000 | 8121400\nVI. Total dos Serviços | Desconto Incondicionado  |Deduções Base Cálculo Base de Cálculo Total do ISSQN ISSQN Retido Desconto Condicionado\nR$ 22.709,56 R$ 0,00 R$ 0,00 R$ 454,19 | Não R$ 0,00\nPIS COFINS INSS IRRF CSLL Outras Retenções (Vi. ISSQN Retido [VI. Líquido da Nota Fiscal\nRs 0,00 R$ 000 RS 22.709,56\nConstrução Civil Cód. Obra : Art:\n'

MOCK_OCR = VALORES_RECUT + "\n" + ORIGINAL_TEXT


def test_prestador_deslocado_apos_intermediario(monkeypatch):
    dummy_path = "tests/dummy_cuiaba_prestador_deslocado.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_OCR)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        # Prestador: DR3 TERCEIRIZAÇÃO — antes vinha com o CNPJ do TOMADOR.
        p = nfse.prestador
        assert p.cnpj_cpf == "62981187000109"
        assert p.razao_social == "DR3 TERCEIRIZACAO LTDA"
        assert p.endereco.municipio == "Cuiabá"
        assert p.endereco.codigo_municipio == "5103403"

        # Tomador: São Pedro Construtora — não pode ser igual ao prestador.
        tm = nfse.tomador
        assert tm.cnpj_cpf == "03051741000190"
        assert tm.cnpj_cpf != p.cnpj_cpf
        assert tm.razao_social != p.razao_social

        # Intermediário: a tabela desta nota está vazia — o guard novo tem
        # que reconhecer que o bloco "roubado" é na verdade o prestador
        # deslocado e devolver None, não um intermediário fantasma com o
        # CNPJ/razão do prestador.
        assert nfse.intermediario is None

        # Valores: grade truncada (só 5 dos 6 tokens "R$" na linha original)
        # corrigida pelo recut — serviços=base=22.709,56 (sem divergência),
        # ISS 454,19 (=base×2%, bate com a grade).
        v = nfse.valores
        assert v.valor_servicos == pytest.approx(22709.56)
        assert v.base_calculo == pytest.approx(22709.56)
        assert v.valor_iss == pytest.approx(454.19)
        assert v.iss_retido is False
        assert v.valor_liquido_nfse == pytest.approx(22709.56)
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
