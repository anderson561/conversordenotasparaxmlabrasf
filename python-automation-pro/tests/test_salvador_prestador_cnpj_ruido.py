# -*- coding: utf-8 -*-
"""Salvador/BA escaneado — espaço espúrio antes do dígito verificador do CNPJ
do prestador contaminava CNPJ, Inscrição Municipal e Razão Social ao mesmo tempo.

Achado real (PDF "Nota_Salvador_assinado-6.pdf", nota 00000072,
ORGEN ENGENHARIA -> SAO PEDRO CONSTRUTORA; valores conferidos na imagem da
página: CNPJ 48.310.477/0001-08, IM 00.915.018/001-70, razão
"ORGEN ENGENHARIA E CONSTRUÇÃO LTDA"): o OCR gera
"48.310.477/0001 -08" (espaço antes do "-08") e lê o ":" do rótulo
"Nome/Razão Social:" como a letra "e". Uma única degradação, três sintomas:

1. CNPJ do prestador saía 03051741000190 — o CNPJ do TOMADOR. O regex de CNPJ
   exigia "-" colado nos dígitos, não casava, e o fallback "primeiro CNPJ válido
   da página inteira" roubava o do tomador.
2. Inscrição Municipal saía "483104770001" — pedaço do próprio CNPJ: ao remover
   a pontuação, "48.310.477/0001" vira um blob de 12 dígitos que passa por IM.
3. Razão Social saía "e ORGEN ENGENHARIA E CONSTRUÇÃO LTDA" — o "e" espúrio
   (o ":" do rótulo) sobrevivia à limpeza de prefixos.

O caso é distinto dos outros dois testes de Salvador, onde é o CNPJ do TOMADOR
que sai corrompido; aqui é o do PRESTADOR, e o rótulo "TOMADOR DE SERVIÇOS"
está presente e legível (não passa pelo recorte `bloco_sv`)."""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_OCR = 'Número da Nota:\nDOR 00000072 |\nData à Hara do Emicçãa-\n\nPREFEITURA MUNICIPAL DO SALVADOR 00000072\n\nSECRETARIA MUNICIPAL DA FAZENDA Data e Hora de Emissão:\n15/04/2026 13:46:45\nNOTA FISCAL DE SERVIÇOS ELETRÔNICA - Nota Salvador pSsigo SM cação:\n\nPRESTADOR DE SERVIÇOS\n\nCPF/CNPJ Inscrição Municipal\n\n48.310.477/0001 -08 00.915.018/001-70\n\nNome/Razão Social e\n\nORGEN ENGENHARIA E CONSTRUÇÃO LTDA\n\nEndereço )\n\nAve Tancredo Neves 001033, EDIF FERREIRA FERRAZ EMPRESARI - CAMINHO DAS ARVORES - Salvador - CEP: 41820-020 - BA\nE-mail\n\nTOMADOR DE SERVIÇOS\n\nNome/Razão Social\n\nSAO PEDRO CONSTRUTORA LTDA\n\nCPF/CNPJ Inscrição Municipal\n\n03.051.741/0001-90 -—\nEndereço\nAVE PRAIA DE PAJUSSARA 554, QUADRA 28 LOTE 09 VILAS DO ATLANTICO - Lauro de Freitas - CEP: 42708-720/BA\nE-mail\n(SAOPEDROCONSTRUTORA. COM.BR\nDISCRIMINAÇÃO DOS SERVIÇOS\nGestão de obra Atacadao Feira\nPeríodo: 01 a 15 de abril.\n\nVALOR TOTAL DA NOTA = R$7.500,00\n\nCNAE\n4120400 - Construção de edifícios\n\nItem da Lista de Serviços:\n00702 - Execução, por administração, empreitada ou subempreitada, de obras de construção civil, hidráulica ou elétrica e de outras o...\n\nValor Total das Deduções (R$) Base de Cálculo (R$) Alíquota (%) Valor do ISS (R$) Crédito Nota Salvador (R$)\n0,00 ia f Z 0,00\n\nValor INSS (R$) Valor PIS (R$) Valor COFINS (R$) Valor IR (R$) Valor CSLL (R$) Outras Retenções (R$):| Valor Líquido (R$)\n0,00 0,00 0,00 0,00 0,00 0,00 7.500,00\n\nAlíquota IBS (%)) Valor IBS (R$) Alíquota CBS (%) Valor CBS (R$)\n\nOUTRAS INFORMAÇÕES\n\n- Esta Nota Salvador foi emitida com respaldo na Lei 7.186/2006\n\n- Documento emitido por ME ou EPP optante pelo Simples Nacional\n\n- COMPETÊNCIA: 04/2026 (mês/ano)\n\n- Código de Tributação do Município: 0702-0/63 - Construção de edificações comerciais de qualquer tipo (Por Administração)\n\nDocumento assinado digitalmente\n\nbr LEANDRO SANTOS CHAVES\ngo. Data: 15/04/2026 13:49:29-0300\n\nVerifique em https://validar.iti gov.br\n'


@pytest.fixture
def nfse(monkeypatch):
    dummy_path = "tests/dummy_salvador_prestador_ruido.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_OCR)

    try:
        nfse_list = SPPdfExtractor(dummy_path).parse_multiple()
        assert len(nfse_list) == 1
        yield nfse_list[0]
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_prestador_cnpj_com_espaco_antes_do_digito_verificador(nfse):
    p = nfse.prestador
    assert p.cnpj_cpf == "48310477000108"
    # não é o CNPJ do tomador vazando pelo fallback "primeiro CNPJ da página"
    assert p.cnpj_cpf != "03051741000190"
    assert p.cnpj_cpf != "00000000000100"


def test_prestador_inscricao_municipal_nao_e_pedaco_do_cnpj(nfse):
    assert nfse.prestador.inscricao_municipal == "0091501800170"
    assert nfse.prestador.inscricao_municipal != "483104770001"


def test_prestador_razao_social_sem_glifo_espurio_do_rotulo(nfse):
    razao = nfse.prestador.razao_social
    assert razao == "ORGEN ENGENHARIA E CONSTRUÇÃO LTDA"
    assert not razao.startswith("e ")


def test_tomador_permanece_correto_e_distinto_do_prestador(nfse):
    tm = nfse.tomador
    assert tm.cnpj_cpf == "03051741000190"
    assert tm.razao_social == "SAO PEDRO CONSTRUTORA LTDA"
    assert tm.cnpj_cpf != nfse.prestador.cnpj_cpf
    assert tm.razao_social != nfse.prestador.razao_social


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
