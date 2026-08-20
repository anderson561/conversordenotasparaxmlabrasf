# -*- coding: utf-8 -*-
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_GOIANIA, LAYOUT_CUIABA

# Texto REAL reconstruído por coordenada (`_reconstruir_texto_por_coordenadas`)
# da NFS-e nº 4 — ID Producao Musical Ltda -> ELOS ESTUDIO E SERVICOS LTDA,
# Prefeitura Municipal de Goiânia/GO, plataforma ISSNet Online
# (issnetonline.com.br/goiania). PDF DIGITAL cujo `pdfminer.extract_text()`
# padrão embaralha a ordem de leitura de forma NÃO-monotônica (a nota inteira
# colidia com LAYOUT_CUIABA porque o detector daquele layout casava a palavra
# solta "ISSNet", presente em QUALQUER cidade dessa plataforma) — corrigido
# com detecção pelo nome do MUNICÍPIO e reconstrução por coordenada de
# caractere (mesma técnica de `camacari_sisloc`).
MOCK_TEXT = 'Série do Documento\nPrefeitura Municipal de Goiânia - GO  Nota Fiscal de Serviço\nSecretaria Municipal da Fazenda Eletrônica - NFS-e\n \nNúmero da Nota Fiscal\nFone: (62) 35243335 - https://www.goiania.go.gov.br/ \n4\nDados do Prestador de Serviço\n Data de Geração da NFS-e\nID Producao Musical Ltda\n27/07/2026 13:37:24 \nItalo Dias\n Data de Competência\nRua T 33,188 Lote: 4E - Quadra: 85 - Setor Bueno\n27/07/2026 \nCEP 74215-140 - Fone: (62)3636-2834 - Goiânia/\n Cód. de Autenticidade\nGO\ndestravacontabilidade@gmail.com 71B42E967 \nInscrição Municipal 5637473 - CPF/CNPJ Responsável pela Retenção\n45.463.870/0001-35\n \nIdentificação da Nota Fiscal Eletrônica\nNatureza da Operação Número do RPS Série do RPS Data de Emissão do RPS\nExigível  4   27/07/2026 \nLocal dos Serviços Município Incidência\nGoiânia - Goiás Goiânia - Goiás\nDados do Tomador de Serviços\nCNPJ/CPF : 04.386.913/0001-49  IM : \nRazão Social : ELOS ESTUDIO E SERVICOS LTDA \nEndereço : AVENIDA ANTONIO CARLOS MAGALHAES  Número : 2671 \nComplemento : SALA1202EDIFBAHIACENTER  Bairro : BROTAS \nCEP : 40280-900  Cidade/UF : Salvador/ BA \nTelefone :  E-mail : ATENDIMENTO@ESTUDIOELOS.COM.BR \nDados do Intermediário de Serviços\nCNPJ/CPF Inscrição Municipal Razão Social\n   \nDescrição dos Serviços\nReferente a gravacao de voz para o jingle de Haddad - campanha de governador 2026 - SP.JOB 5748 \nDetalhamento dos Tributos\nAtividade do Município Alíquota Item da LC116/2003 Cód. NBS Cód. CNAE\n1212 - 12.12 - Execução de música. -   2,01  1212 125031000 9001902\nVl. Total dos Serviços Desconto Incondicionado Deduções Base Cálculo Base de Cálculo Total do ISSQN ISSQN Retido Desconto Condicionado\nR$ 600,00  R$ 0,00  R$ 0,00  R$ 600,00  R$ 12,06  Não  R$ 0,00 \nPIS COFINS INSS IRRF CSLL Outras Retenções Vl. ISSQN Retido Vl. Líquido da Nota Fiscal\nR$ 0,00  R$ 0,00  R$ 0,00  R$ 0,00  R$ 0,00  R$ 0,00  R$ 0,00  R$ 600,00 \nConstrução Civil Cód. Obra :    Art. :   \nInformações Adicionais\nBanco BTG Pactual\nConta Corrente\nAg 0050\nCc 1458067-4\nPIX: 45.463.870/0001-35\nTrib aprox: R$ 0.00 (0.00% - Federal) e R$ 12.06 (2.0100000000% - Municipal). Fonte: IBPT\nI - "DOCUMENTO EMITIDO POR ME OU EPP OPTANTE PELO SIMPLES NACIONAL"; e \nII - "NÃO GERA DIREITO A CRÉDITO FISCAL DE IPI." \nConsulte a autenticidade deste documento acessando o site: https://www.issnetonline.com.br/goiania/online/'


def test_detect_layout_goiania():
    dummy_path = "tests/dummy_goiania.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    try:
        ex = SPPdfExtractor(dummy_path)
        ex.raw_text = MOCK_TEXT
        assert ex._detect_layout() == LAYOUT_GOIANIA
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_goiania_nao_colide_mais_com_cuiaba():
    """Achado real: "issnetonline.com.br/goiania" contém a substring "issnet"
    (case-insensitive), que o detector antigo de LAYOUT_CUIABA casava sem
    exigir "Cuiabá" por perto — a nota inteira caía em LAYOUT_CUIABA. A marca
    de Cuiabá agora exige que "ISSNet" NÃO seja seguido de "online"."""
    ex = SPPdfExtractor.__new__(SPPdfExtractor)
    ex.raw_text = "Prefeitura Municipal de Cuiabá\nISSNet\nAlgum texto da nota"
    assert ex._detect_layout() == LAYOUT_CUIABA


def test_extract_goiania_nfse_04(monkeypatch):
    """PDF digital cujo `extract_text()` padrão embaralha a grade de valores
    de forma NÃO-monotônica (nem um deslocamento fixo de coluna resolve,
    diferente do Vinhedo) — usa `_reconstruir_texto_por_coordenadas` para
    obter a ordem visual real antes de qualquer extração de campo."""
    dummy_path = "tests/dummy_goiania_full.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT)
    monkeypatch.setattr(SPPdfExtractor, "_reconstruir_texto_por_coordenadas", lambda self: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        assert nfse.numero == "4"
        assert nfse.codigo_verificacao == "71B42E967"
        assert nfse.servico_codigo == "1212"
        assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "27/07/2026 13:37:24"
        assert nfse.competencia.strftime("%d/%m/%Y") == "27/07/2026"
        assert "jingle de Haddad" in nfse.discriminacao

        p = nfse.prestador
        assert p.cnpj_cpf == "45463870000135"
        assert p.razao_social == "ID Producao Musical Ltda"
        assert p.inscricao_municipal == "5637473"
        assert p.endereco.logradouro == "Rua T 33"
        assert p.endereco.numero == "188"
        assert p.endereco.complemento == "Lote: 4E - Quadra: 85"
        assert p.endereco.bairro == "Setor Bueno"
        assert p.endereco.municipio == "Goiânia"
        assert p.endereco.uf == "GO"
        assert p.endereco.cep == "74215140"
        assert p.endereco.codigo_municipio == "5208707"
        assert p.email == "destravacontabilidade@gmail.com"
        assert p.telefone == "(62)3636-2834"

        t = nfse.tomador
        assert t.cnpj_cpf == "04386913000149"
        assert t.cnpj_cpf != p.cnpj_cpf
        assert t.razao_social == "ELOS ESTUDIO E SERVICOS LTDA"
        assert t.inscricao_municipal is None
        assert t.endereco.logradouro == "AVENIDA ANTONIO CARLOS MAGALHAES"
        assert t.endereco.numero == "2671"
        assert t.endereco.complemento == "SALA1202EDIFBAHIACENTER"
        assert t.endereco.bairro == "BROTAS"
        assert t.endereco.municipio == "Salvador"
        assert t.endereco.uf == "BA"
        assert t.endereco.cep == "40280900"
        assert t.email == "ATENDIMENTO@ESTUDIOELOS.COM.BR"

        assert nfse.intermediario is None

        v = nfse.valores
        # Achado real: fallback genérico/colisão com Cuiabá zerava
        # ValorServicos (era 0.00, real é 600.00) e trocava ValorIss/ValorIr
        # (saíam ambos 600.00 - o real é ValorIss=12.06 e ValorIr=0.00).
        assert v.valor_servicos == pytest.approx(600.0)
        assert v.base_calculo == pytest.approx(600.0)
        assert v.aliquota == pytest.approx(0.0201)
        assert v.valor_iss == pytest.approx(12.06)
        assert v.iss_retido is False
        assert v.valor_iss_retido == pytest.approx(0.0)
        assert v.valor_liquido_nfse == pytest.approx(600.0)
        assert v.valor_ir == pytest.approx(0.0)
        assert v.valor_pis == pytest.approx(0.0)
        assert v.valor_cofins == pytest.approx(0.0)
        assert v.valor_inss == pytest.approx(0.0)
        assert v.valor_csll == pytest.approx(0.0)
        assert v.outras_retencoes == pytest.approx(0.0)
        assert v.desconto_incondicionado == pytest.approx(0.0)
        assert v.desconto_condicionado == pytest.approx(0.0)
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
