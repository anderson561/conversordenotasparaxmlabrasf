# -*- coding: utf-8 -*-
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_MONTE_SANTO
import os

# Texto REAL extraído por pdfminer (`extract_text`) da NFS-e de Monte Santo/BA
# (nota real nº 65, PEAD NORDESTE LTDA -> DELTALINE SERVICOS LTDA., PDF
# DIGITAL, sem OCR). Preservado verbatim, incluindo os quirks que travam
# regressões:
#  - a nota é impressa em 2 páginas (separador "\x0c") e os VALORES (Valor
#    Total da Nota, Deduções, Base de Cálculo, ISS, Tributação Federal,
#    Optante pelo Simples) só existem na 2ª página, que não repete o
#    cabeçalho "PREFEITURA MUNICIPAL DE MONTE SANTO" nem número/CNPJ -
#    detectada por fingerprint próprio ("Deduz Materiais?" + "Base de
#    Cáculo R$") tanto na detecção de layout quanto no `is_new_invoice` do
#    parse_multiple (sem isso, a 2ª página cai em LAYOUT_GENERICO e é
#    descartada como lixo, OU é tratada como o início de uma nota nova
#    fantasma, perdendo os valores da nota real);
#  - o pdfminer despeja os RÓTULOS das entidades (prestador/tomador) em
#    blocos separados dos VALORES ("labels dumped, depois values dumped"),
#    não em pares rótulo=valor na mesma linha;
#  - "Responsável pelo Pagamento do imposto: Contratante, tomador do
#    serviço" -> ISS retido pelo TOMADOR (não pelo prestador);
#  - "Base de Cáculo" (sem o "l" de "Cálculo") é o erro de digitação real do
#    gerador de PDF desta prefeitura - preservado como está impresso.
MOCK_TEXT = 'PREFEITURA MUNICIPAL DE MONTE SANTO\nSECRETARIA MUNICIPAL DE PLANEJAMENTO, GESTÃO E FINANÇAS\n\nNota Fiscal de Serviços Eletrônica  - NFSe\n\nA autenticidade desta NFS-e pode\nser verificada pela leitura deste\ncódigo QR ou pela consulta da chave\nde acesso no portal nacional da\nNFS-e\n\nChave de Acesso\n29215001254849932000132000000000006526071354504745\n\nCódigo de Verificação Municipal\n0555 - 5851 - 6010\n\nNúmero da Nota\n65\n\nCompetência\n23/07/2026\n\nData e Hora da Emissão\n23/07/2026 às 10:28:18\n\nNúmero do Lote\n-\n\nSérie da DPS\n2026\n\nCódigo Mobiliário\nRazão Social\nLogradouro\nBairro\nMunicípio\nInscrição Estadual\n\nRazão Social\nLogradouro\nBairro\nMunicípio\nInscrição Estadual\n\n05401808\nPEAD NORDESTE LTDA\nDESEMBARGADOR SALVIO MARTINS\nCENTRO\nMONTE SANTO\n\nPRESTADOR DO SERVIÇO\nInscrição Municipal\nCNPJ/CPF\nNúmero\nCep\nUF\n\n05401808\n54.849.932/0001-32\n62\n48.800-000\nBA\n\nTOMADOR DO SERVIÇO\n\nDELTALINE SERVICOS LTDA.\nRUA CAMBORIU\nIAPI\nSALVADOR\n\nCNPJ/CPF\nNúmero\nCep\nUF\n\n01.813.680/0001-25\n39\n40.330-533\nBA\n\nServiço\n\nDescrição\n\nValor Unitário\n\nQuantidade\n\nDesconto\n\n1\n\nINSTALAÇÕES HIDRÁULICAS\n\n4800,0000\n\n1,0000\n\n0,0000\n\nTotal\n4800,0000\n\nDISCRIMINAÇÃO DOS SERVIÇOS\n\nValor Total dos Serviços R$\n\n4.800,00\n\nMaterial\n\n138\n\nMATERIAIS, INSUMOS, FERRAMENTAS E EQUIPAMENTOS PARA\nEXECUÇÃO.\n\nDescrição\n\nValor Unitário\n\nQuantidade\n\nTotal\n\n7200,0000\n\n1,0000\n\n7200,0000\n\nDISCRIMINAÇÃO DOS MATERIAIS\n\nValor Total dos Materiais R$\n\n7.200,00\n\nITEM DA LISTA DE SERVIÇO\n\n07.02 - EXECUÇÃO, POR ADMINISTRAÇÃO, EMPREITADA OU SUBEMPREITADA, DE OBRAS DE CONSTRUÇÃO CIVIL, HIDRÁULICA OU ELÉTRICA E DE OUTRAS OBRAS SEMELHANTES,\nINCLUSIVE SONDAGEM, PERFURAÇÃO DE POÇOS, ESCAVAÇÃO, DRENAGEM E IRRIGAÇÃO, TERRAPLENAGEM, PAVIMENTAÇÃO, CONCRETAGEM E A INSTALAÇÃO E MONTAGEM DE\nPRODUTOS, PEÇAS E EQUIPAMENTOS (EXCETO O FORNECIMENTO DE MERCADORIAS PRODUZIDAS PELO PRESTADOR DE SERVIÇOS FORA DO LOCAL DA PRESTAÇÃO DOS SERVIÇOS,\nNBS:\nQUE FICA SUJEITO AO ICMS).\n\n1.0106.22.00 - Serviços de instalação de tubulação para escoamento de água\n\nINFORMAÇÕES REFERENTE A DISCRIMINAÇÃO DOS SERVIÇOS\n\nOBJETO DO CONTRATO: EXECUÇÃO DE SOLDAS DE TERMOFUSÃO EM REDE PEAD DE630 E DE710, EM CAMAÇARI/BA\nOBRA: DESVIO REDE DE ESGOTO DA CETREL, CAMAÇARI/BA\nPROPOSTA Nº 0130A\nBOLETIM DE MEDICAO Nº 0001\nPERIODO: 01/07/2026 A 15/07/2026\nVALOR R$ 12.000,00\nISS: 2% = R$ 96,00\nINSS 11% = R$528 ,00\nVENCIMENTO: 07/08/2026\nDADOS BANCÁRIOS: Agência: 0001, Conta Corrente: 36738701-8, Banco: 077 - INTER, PEAD NORDESTE LTDA.\nPIX CNPJ: 54.849.932/0001-32\n\nPágina  1 de\n\n2\n\nNota Fiscal de Serviços\n\n\x0c Valor Total da Nota R$ 12.000,00\nOperação\nCom lançamentos de materiais\nOptante pelo Simples ?\nSim\nAtividade\n4322301 - Instalações hidráulicas, sanitárias e de gás\n\nVALOR TOTAL DA NOTA\n\nDeduz Materiais?\nSim\nLocal do Serviço\nFora do Município\n\nResponsável pelo Pagamento do imposto\nContratante, tomador do serviço\nSituação da Nota\nSimples Nacional\n\nValor Total das Deduções R$\n7.200,00\n\nBase de Cáculo R$\n\nAliquota %\n\nValor do ISS R$\n\nValor Total Retido R$\n\n4.800,00\n\n2,00\n\n96,00\n\n624,00\n\n Valor Liquido da Nota R$ 11.376,00\n\nTRIBUTAÇÃO FEDERAL\n\nIR R$\n\nPIS R$\n\n0,00\n\nINSS R$\n\nCSLL R$\n\nCOFINS R$\n\nOutras Retenções R$\n\n0,00\n\n528,00\n\n0,00\n\n0,00\n\n0,00\n\nALIQUOTA IBS\n\n-\n\nVALOR IBS\n-\n\nALIQUOTA CBS\n\nVALOR CBS\n\n-\n\n-\n\nPágina  2 de\n\n2\n\nNota Fiscal de Serviços\n\n\x0c'


def test_detect_layout_monte_santo():
    dummy_path = "tests/dummy_monte_santo.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    try:
        ex = SPPdfExtractor(dummy_path)
        ex.raw_text = MOCK_TEXT
        assert ex._detect_layout() == LAYOUT_MONTE_SANTO
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_extract_monte_santo_nfse_65(monkeypatch):
    """PDF digital de 2 páginas; os valores só existem na 2ª página, que não
    repete o cabeçalho municipal nem número/CNPJ - exercita o fingerprint de
    continuação (LAYOUT_MONTE_SANTO na 2ª página + carve-out no
    `is_new_invoice`), sem o qual a nota perderia todos os valores."""
    dummy_path = "tests/dummy_monte_santo_full.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        assert nfse.numero == "65"
        assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "23/07/2026 10:28:18"
        assert nfse.competencia.strftime("%d/%m/%Y") == "23/07/2026"
        assert nfse.codigo_verificacao == "0555 - 5851 - 6010"
        assert nfse.servico_codigo == "0702"
        assert nfse.discriminacao == "INSTALAÇÕES HIDRÁULICAS"
        assert nfse.optante_simples_nacional is True

        p = nfse.prestador
        assert p.cnpj_cpf == "54849932000132"
        assert p.razao_social == "PEAD NORDESTE LTDA"
        assert p.inscricao_municipal == "05401808"
        assert p.endereco.logradouro == "DESEMBARGADOR SALVIO MARTINS"
        assert p.endereco.numero == "62"
        assert p.endereco.bairro == "CENTRO"
        assert p.endereco.municipio == "MONTE SANTO"
        assert p.endereco.codigo_municipio == "2921550"
        assert p.endereco.uf == "BA"
        assert p.endereco.cep == "48800000"

        t = nfse.tomador
        assert t.cnpj_cpf == "01813680000125"
        assert t.cnpj_cpf != p.cnpj_cpf
        assert t.razao_social == "DELTALINE SERVICOS LTDA."
        assert t.endereco.logradouro == "RUA CAMBORIU"
        assert t.endereco.numero == "39"
        assert t.endereco.bairro == "IAPI"
        assert t.endereco.municipio == "SALVADOR"
        assert t.endereco.codigo_municipio == "2927408"
        assert t.endereco.uf == "BA"
        assert t.endereco.cep == "40330533"

        # Valores: construção civil com dedução de materiais da base do ISS.
        # Base de Cálculo (4.800) = Valor Total da Nota (12.000) - Materiais
        # (7.200). ISS retido pelo TOMADOR (Responsável pelo Pagamento do
        # imposto: Contratante). INSS 528,00 retido na fonte (Tributação
        # Federal).
        val = nfse.valores
        assert val.valor_servicos == pytest.approx(12000.00)
        assert val.valor_deducoes == pytest.approx(7200.00)
        assert val.base_calculo == pytest.approx(4800.00)
        assert val.aliquota == pytest.approx(0.02)
        assert val.valor_iss == pytest.approx(96.00)
        assert val.iss_retido is True
        assert val.valor_iss_retido == pytest.approx(96.00)
        assert val.valor_inss == pytest.approx(528.00)
        assert val.valor_ir == pytest.approx(0.0)
        assert val.valor_pis == pytest.approx(0.0)
        assert val.valor_cofins == pytest.approx(0.0)
        assert val.valor_csll == pytest.approx(0.0)
        assert val.valor_liquido_nfse == pytest.approx(11376.00)

        assert nfse.avisos == []
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
