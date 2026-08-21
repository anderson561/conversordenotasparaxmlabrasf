import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_BRASILIA
from src.models.nfse_models import Nfse
import os

def test_detect_brasilia_layout():
    """Testa a detecção correta do layout Brasília/DF"""
    mock_text = """
    Governo do Distrito Federal
    Secretária de Estado de Economia do Distrito Federal
    Coordenação do ISS
    Nota Fiscal de Serviço Eletrônica - NFS-e
    """
    
    dummy_path = "tests/dummy_brasilia.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = mock_text
    layout = extractor._detect_layout()
    
    assert layout == LAYOUT_BRASILIA, f"Expected {LAYOUT_BRASILIA}, got {layout}"
    
    if os.path.exists(dummy_path):
        os.remove(dummy_path)


def test_extract_brasilia_codigo_autenticidade():
    """
    Testa a extração do Código de Autenticidade no layout Brasília/DF
    Baseado na NFS-e real do GDF fornecida
    """
    mock_text = """
    Governo do Distrito Federal
    Secretária de Estado de Economia do Distrito Federal
    Coordenação do ISS
    
    Data de Geração de NFS-e: 21/05/2026 22:53:10
    Data de Competência: 21/05/2026
    Código de Autenticidade: 5300010812249298570001590000000001182260517794 14799
    
    Dados do Prestador
    RC CONSTRUCOES ELETRICAS LTDA
    CNPJ/CPF: 24.929.857/0001-59
    
    Dados do Tomador
    SINAL CONSTRUTORA LTDA
    CNPJ/CPF: 33.811.381/0001-48
    
    Detalhamento
    Valor Total Serviços: R$ 27.796,65
    Base de Cálculo: R$ 27.796,65
    Alíquota: 5,00%
    Total ISS: R$ 1.389,83
    Valor Líquido: R$ 27.796,65
    """
    
    dummy_path = "tests/dummy_brasilia_auth.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = mock_text
    extractor.layout = LAYOUT_BRASILIA
    
    # Testa extração do código de autenticidade
    codigo = extractor._extrair_codigo_autenticidade_brasilia()
    
    # Remove espaços e caracteres especiais do código esperado
    expected_code = "530001081224929857000159000000000118226051779414799"
    
    assert codigo == expected_code, f"Expected {expected_code}, got {codigo}"
    assert len(codigo) >= 20, f"Código deve ter pelo menos 20 dígitos, got {len(codigo)}"
    
    if os.path.exists(dummy_path):
        os.remove(dummy_path)


def test_extract_brasilia_full_nfse():
    """
    Testa extração completa de uma NFS-e no layout Brasília/DF
    """
    mock_text = """
    Governo do Distrito Federal
    Secretária de Estado de Economia do Distrito Federal
    Coordenação do ISS
    
    Nota Fiscal de Serviço Eletrônica - NFS-e
    Número da Nota: 1162
    Data de Geração: 21/05/2026 22:53:10
    Data de Competência: 21/05/2026
    Código de Autenticidade: 5300010812249298570001590000000001182260517794 14799
    
    IDENTIFICAÇÃO DO PRESTADOR
    CNPJ: 24.929.857/0001-59
    Nome: MENNDEL & MELO ADVOCACIA
    Inscrição Municipal: 0771119001 00
    Telefone: (61)9649-6252
    CEP: 71655-040
    
    IDENTIFICAÇÃO DO TOMADOR
    CNPJ: 33.811.381/0001-48
    Nome: SINAL CONSTRUTORA LTDA
    Inscrição Municipal: -
    Telefone: (71)3273-2450
    CEP: 48120-000
    
    DADOS DO SERVIÇO PRESTADO
    Código: 17.14.01
    Descrição: Advocacia
    Valor Serviço: R$ 27.796,65
    
    IMPOSTOS
    Base Cálculo: R$ 27.796,65
    Alíquota ISS: 5,00%
    Valor ISS: R$ 1.389,83
    Valor Deduções: R$ 0,00
    Valor Líquido: R$ 27.796,65
    """
    
    dummy_path = "tests/dummy_brasilia_full.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = mock_text
    extractor.layout = extractor._detect_layout()
    
    assert extractor.layout == LAYOUT_BRASILIA
    
    nfse = extractor.parse()
    
    # Validações gerais
    assert nfse.numero == "1162"
    assert nfse.codigo_verificacao == "530001081224929857000159000000000118226051779414799"
    assert nfse.prestador.cnpj_cpf == "24929857000159"
    assert nfse.tomador.cnpj_cpf == "33811381000148"
    assert nfse.valores.valor_servicos == pytest.approx(27796.65)
    assert nfse.valores.base_calculo == pytest.approx(27796.65)
    assert nfse.valores.aliquota == pytest.approx(0.05)
    assert nfse.valores.valor_iss == pytest.approx(1389.83)
    assert nfse.valores.valor_liquido_nfse == pytest.approx(27796.65)
    
    if os.path.exists(dummy_path):
        os.remove(dummy_path)


# Texto REAL (pdfminer.extract_text, sem OCR) da NFS-e nº 44 — AFG DIGITAL
# COMUNICACAO E PRODUCAO LTDA -> ELOS ESTUDIO E SERVICOS LTDA, Brasília/DF,
# plataforma "ISS.NET - Sistema Nota Control". Achado real (2026-08-20):
# Anderson pediu para verificar a extração do TOMADOR (ELOS ESTUDIO) e o
# bloco de endereço saía com 3 bugs, todos no extrator GENÉRICO de entidade
# (compartilhado por ~30 layouts, não específico do Brasília):
# (1) a lookahead do Endereço não conhecia o rótulo "Cidade:" (só
#     "Município"/"Municipio"), então a captura do logradouro nunca parava e
#     engolia a linha inteira seguinte ("0 Cidade: Brasília Estado/Prov./
#     Reg.: Distrito Federal País: Brasil") dentro do campo Número;
# (2) o casamento de Município/UF só reconhecia os rótulos "Município" e
#     "Cidade/UF" — esta plataforma usa "Cidade:" isolado, então
#     município/UF/codigo_municipio nunca eram extraídos e caíam no
#     fallback de capital (Salvador/BA);
# (3) mesmo reconhecendo o rótulo, "Estado/Prov./Reg.: Distrito Federal"
#     imprime o NOME COMPLETO da UF (não a sigla de 2 letras que a regex
#     original exigia) — precisa de um dicionário nome->sigla.
# Corrigido: "Cidade\s*:" somado às duas listas de rótulos/lookahead;
# "Estado/Prov./Reg." aceita nome completo via `_UF_POR_NOME_ESTADO`.
# Achados colaterais na MESMA investigação (bugs pré-existentes, não gated
# a este layout — afetavam E-mail/Telefone de QUALQUER nota que passasse
# pelo extrator genérico): (a) a regex de E-mail/Telefone não tolerava o
# ":" impresso entre o rótulo e o valor ("E-mail: valor"/"Telefone: valor")
# — `relax()` só cobre espaço ENTRE os caracteres do próprio rótulo, nunca
# um separador extra; (b) a regex de Telefone tinha `{8,20}` com chave
# SIMPLES dentro de uma f-string — Python interpreta isso como a tupla
# `(8, 20)` e insere o literal "(8, 20)" na regex em vez do quantificador,
# quebrando o casamento silenciosamente (sem erro de sintaxe). Os dois
# juntos faziam Telefone ficar sempre `None`.
MOCK_TEXT_BRASILIA_ELOS = 'Governo do Distrito Federal \nSecretaria de Estado de Economia do Distrito Federal \nCoordenação do ISS \n\nSérie do Documento\n\nNota Fiscal de Serviço\nEletrônica - NFS-e\n\nNúmero da Nota Fiscal\n\n44\n\nData de Geração da NFS-e\n\nData de Competência\n\nCódigo de Autenticidade\n\n23/07/2026 14:03:31 \n\n23/07/2026 \n\n53001081239282701000104000000000004426071784826217 \n\nEmitente da NFS-e\n\nNúmero da DPS\n\nData Emissão da DPS\n\nSérie da DPS\n\nPrestador \n\nConsulte a autenticidade desta nota lendo o QRcode ou acessando o site: https://iss.fazenda.df.gov.br/online/\n\nIDENTIFICAÇÃO DO PRESTADOR\n\nInscrição Municipal: 0800740900103\n\nCNPJ/CPF/NIF: 39.282.701/0001-04\nNome/Razão Social: AFG DIGITAL COMUNICACAO E PRODUCAO LTDA\nNome Fantasia: AFG DIGITAL\nEndereço: QNN 24 CONJUNTO I LOTE 09 S/N, 0\nCidade: Brasília   Estado/Prov./Reg.: Distrito Federal   País: Brasil\nE-mail: arynaldof@hotmail.com\nSituação Simples Nacional: Optante - Microempresa ou Empresa de Pequeno Porte (ME/EPP)   Regime Apuração: Regime de apuração dos\ntributos federais e municipal pelo SN   Regime Especial: Nenhum\n\nTelefone: (61)8104-9825\n\nCEP: 72220-249\n\nIDENTIFICAÇÃO DO TOMADOR\n\nCNPJ/CPF/NIF: 04.386.913/0003-00 \nNome/Razão Social: ELOS ESTUDIO E SERVICOS LTDA \nNome Fantasia: *** \nEndereço: SCN Q 4 BL B S/N SALA 702/PARTE 3257 ASA NORTE, 0\nCidade: Brasília   Estado/Prov./Reg.: Distrito Federal   País: Brasil \nE-mail: atendimento@estudioelos.com.br \n\nInscrição Municipal: 0820519000388 \n\nTelefone: (71)3452-0938 \n\nCEP: 70714-020\n\nINTERMEDIÁRIO DO SERVIÇO NÃO IDENTIFICADO NA NFS-E\nDESTINATÁRIO É O PRÓPRIO TOMADOR IDENTIFICADO NA NFS-E\nDADOS DO SERVIÇO PRESTADO\n\nCód. Trib. Nacional: 17.06.01  NBS: 1.1406.11.00  Atividade Municipal: 17.06 - Propaganda e publicidade, inclusive promoç...\nLocal da Prestação: Brasília - DF \nVl. do Serviço: R$ 4.950,00 \nDescrição do Serviço: Referente a Produção\n\nPaís Resultado da Prestação do Serviço: - \n\nVl. do Desc. Incondicionado: - \n\nVl. do Desc. Condicionado: - \n\nIMPOSTO SOBRE SERVIÇO DE QUALQUER NATUREZA - ISSQN\n\nTipo Tributação: Operação tributável \nMunicípio de Incidência: Brasília - DF   Tipo de Retenção: Não Retido   Valor Dedução: R$ 0,00 \nBase de Cálculo: R$ 4.950,00 \n\nTipo Susp. Exig.: - \n\nNº Proc. Susp.: - \n\nVl. ISSQN: R$ 0,00 \n\nAlíquota: - \nTRIBUTAÇÃO NACIONAL\n\nCST: Nenhum \nTipo de Retenção: PIS/COFINS/CSLL Não Retidos \nVl. CSLL: - \n\nVl. PIS: - \nVl. IRRF: - \n\nVl. COFINS: - \nVl. CP Retido: - \n\nIMPOSTO E CONTRIBUIÇÃO SOBRE BENS E SERVIÇOS - IBS/CBS\n\nClassif. Tributária: 000001  Situação Tributária: Tributação integral \n\nCód. Ind. Op.: 100301 \nMunicípio de Incidência: Brasília - DF \nTipo de Ente Governamental: - \nAlíq. CBS: 0,9% \nAlíq. IBS Est.: 0,1% \nAlíq. IBS Mun.: 0% \nCód. Créd. Pres.:  \nVl. do Créd. Pres. (CBS): - \nClassif. Tributária Regular: - \nAliq. Efet. Regular - CBS: - \nValor CBS: - \nTotal de Retenção\n- \n\nValor Total do CBS\nR$ 44,55 \n\nTipo de Operação: - \nPerc. Red. Compra Gov.: - \n\nBase de Cálculo: R$ 4.950,00 \n\nPerc. Red. Alíq. CBS: - \nPerc. Red. Alíq. IBS Est.: - \nPerc. Red. Alíq. IBS Mun.: - \nAlíq. do Créd. Pres. (CBS): - \n\nAlíq. Efet. CBS: 0,9% \nAlíq. Efet. IBS Est.: 0,1% \nAlíq. Efet. IBS Mun.: 0% \nAlíq. do Créd. Pres. (IBS): - \nVl. do Créd. Pres. (IBS): - \n\nValor CBS: R$ 44,55 \nValor IBS Est.: R$ 4,95 \nValor IBS Mun.: R$ 0,00 \n\nSituação Tributária Regular: - \n\nAlíq. Efet. Regular - IBS Estadual: - \nVl. IBS Regular Estadual: - \n\nAlíq. Efet. Regular - IBS Municipal: - \nVl. IBS Regular Municipal: - \n\nValor Total do IBS\nR$ 4,95 \n\nValor Total Líquido\nR$ 4.950,00 \n\nValor Total da Nota Fiscal - IBS/CBS\nR$ 4.950,00 \n\nI - "DOCUMENTO EMITIDO POR ME OU EPP OPTANTE PELO SIMPLES NACIONAL"; e\nII - "NÃO GERA DIREITO A CRÉDITO FISCAL DE IPI."\n• PROCON: TEL 151- SETOR COMERCIAL SUL, QUADRA 8, BLOCO B-60, SALA 240- BRASILIA - DF\n\nISS.NET - Sistema Nota Control® • www.notacontrol.com.br\n\nINFORMAÇÕES COMPLEMENTARES\n\n \n \n \n\x0c'


def test_brasilia_tomador_elos_estudio_endereco_e_contato(monkeypatch):
    dummy_path = "tests/dummy_brasilia_elos.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT_BRASILIA_ELOS)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        assert nfse.numero == "44"

        p = nfse.prestador
        assert p.cnpj_cpf == "39282701000104"
        assert p.razao_social == "AFG DIGITAL COMUNICACAO E PRODUCAO LTDA"
        assert p.endereco.logradouro == "QNN 24 CONJUNTO I LOTE 09 S/N"
        assert p.endereco.numero == "0"
        assert p.endereco.municipio == "Brasília"
        assert p.endereco.uf == "DF"
        assert p.endereco.codigo_municipio == "5300108"
        assert p.endereco.cep == "72220249"
        assert p.email == "arynaldof@hotmail.com"
        assert p.telefone == "(61)8104-9825"

        t = nfse.tomador
        assert t.cnpj_cpf == "04386913000300"
        assert t.cnpj_cpf != p.cnpj_cpf
        assert t.razao_social == "ELOS ESTUDIO E SERVICOS LTDA"
        # Achado real: sem o fix, este campo saía como
        # "0 Cidade: Brasília Estado/Prov./Reg.: Distrito Federal País: Brasil"
        # (a captura do Endereço engolia a linha inteira seguinte).
        assert t.endereco.numero == "0"
        assert t.endereco.logradouro == "SCN Q 4 BL B S/N SALA 702/PARTE 3257 ASA NORTE"
        # Achado real: sem o fix, município ficava "Não informado" e UF/
        # codigo_municipio caíam no fallback de capital (Salvador/BA).
        assert t.endereco.municipio == "Brasília"
        assert t.endereco.uf == "DF"
        assert t.endereco.codigo_municipio == "5300108"
        assert t.endereco.cep == "70714020"
        # Achado real: e-mail/telefone saíam sempre `None` (bugs
        # independentes na regex genérica, não gated a este layout).
        assert t.email == "atendimento@estudioelos.com.br"
        assert t.telefone == "(71)3452-0938"
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
