# -*- coding: utf-8 -*-
r"""Salvador/BA escaneado — tomador extraído com o CNPJ ERRADO (reprovava
checksum) por causa de um recut de OCR desnecessário.

Achado real (nota nº 00011629, SAFE - SEGURANÇA ELETRÔNICA LTDA ->
MANUELLA CARVALHO MARTINS BAHIA, IMPLANTAÇÃO SISTEMA MONITORAMENTO 24H,
R$699,00): o OCR da página principal já lia o CNPJ do tomador corretamente
("13.583.542/0001 -86", só com um espaço extra antes do hífen — ruído
tolerado pela extração real), mas o gatilho do recut `_ocr_tomador_salvador`
exigia o formato `\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}` sem tolerar esse espaço,
então disparava o recut mesmo sem necessidade. O recut então lia o CNPJ
ERRADO ("...0001 66", reprova checksum) e, por ser prependado ao texto,
criava um 2º bloco "TOMADOR DE SERVIÇOS" que o fatiamento genérico
encontrava primeiro — o CNPJ correto do bloco original nunca era alcançado,
e o tomador caía no sentinela `00000000000100` com o aviso "Dados do
tomador não identificados".

Esta nota também carregava, na mesma página, o bug pré-catalogado de fusão
"alvador" + Código de Verificação: o rótulo real "Verificação:" está tão
perto do fim de "Salvador" (do título) que o OCR funde os dois sem
separador ("alvador ETNE-WBUQ"), e o candidato final saía "ALVADORETNEWBUQ"
em vez de "ETNEWBUQ" — o guard antigo exigia um dígito no candidato, mas o
código real desta nota é só letras.

Texto OCR real capturado via `SPPdfExtractor._ocr_page(0)` (já com os dois
fixes aplicados, ou seja, o bloco único e correto que passa a chegar em
produção — sem a duplicação do recut indevido).
"""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_OCR = 'Número da Nota:\nJOR 00011629\n\nData e Hora de Emissão:\n\n12/08/2026 11:48:10\nR Código de Verificação:\nalvador ETNE-WBUQ\n\nPREFEITURA MUNICIPAL DO SALVADOR 00011629\n\nSECRETARIA MUNICIPAL DA FAZENDA Data e Hora de Emissão:\n12/08/2026 11:48:10\n\nNOTA FISCAL DE SERVIÇOS ELETRÔNICA - Nota Salvador gongo de verificação:\n\nPRESTADOR DE SERVIÇOS\n\nCPF/CNPJ Inscrição Municipal\n05.688.944/0001-17 00.233.273/001-50\nNome/Razão Social o\n\nSAFE - SEGURANÇA ELETRÔNICA LTDA\n\nEndereço S/mlala\nAve Santiago de Compostela 351 , GALPAOC PLATO 2 - BROTAS - Salvador - CEP: 40279-150 - BA SAFE\n\nacdmédsafeseg.com.br\n\nTOMADOR DE SERVIÇOS\n\nNome/Razão Social\n\nMANUELLA CARVALHO MARTINS BAHIA\n\nCPF/CNPJ Inscrição Municipal\n13.583.542/0001 -86 00.382.887/001-80\nEndereço\n\nRua Amélia Rodrigues 000085, CASA TERREO GRACA - Salvador - CEP: 40150-180/BA\n\nCQgrupomignon.com.br\n\nDISCRIMINAÇÃO DOS SERVICOS\nIMPLANTAÇÃO SISTEMA MONITORAMENTO 24H. (11066)\n\nVALOR LÍQUIDO R$ 666,50\n\nVALOR TOTAL DA NOTA = R$699,00\n\nCNAE:\n8020001 - Atividades de monitoramento de sistemas de segurança eletrônico\n\nltem da Lista de Serviços:\n01102 - Vigilância, segurança ou monitoramento de bens, pessoas e semoventes.\nValor Total das Deduções (R$) Base de Cálculo (R$) Alíquota (%) Valor do ISS (R$) Crédito Nota Salvador (R$)\n0,00 699,00 5,00% 34,95 0,00\nValor INSS (R$) Valor PIS (R$) Valor COFINS (R$) Valor IR (R$) Valor CSLL (R$): Outras Retenções (R$)] Valor Líquido (R$)\n0,00 4,54 20,97 0,00 6,99 0,00 666,50\nAlíquota IBS (%) Valor IBS (R$) Alíquota CBS (%)) Valor CBS (R$)\n\nOUTRAS INFORMAÇÕES\n\n- Esta Nota Salvador foi emitida com respaldo na Lei 7.186/2006\n\n- Esta Nota Salvador não gera crédito\n\n- Data de vencimento do ISS desta Nota Salvador: 05/05/2026\n\n- COMPETÊNCIA: 04/2026 (mês/ano)\n\n- Código de Tributação do Município: 1102-0/01 - Vigilância, segurança ou monitoramento de bens e pessoas\n\n'


@pytest.fixture
def nfse(monkeypatch):
    dummy_path = "tests/dummy_salvador_11629.pdf"
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


def test_numero_da_nota(nfse):
    assert nfse.numero == "00011629"


def test_tomador_cnpj_correto_nao_cai_no_sentinela(nfse):
    tm = nfse.tomador
    # CNPJ real do OCR ("13.583.542/0001 -86") aprova o checksum — precisa
    # chegar íntegro, nunca o sentinela nem o dígito errado do recut antigo
    # ("...0001 66", que reprova checksum).
    assert tm.cnpj_cpf == "13583542000186"
    assert tm.cnpj_cpf != "00000000000100"
    assert tm.razao_social == "MANUELLA CARVALHO MARTINS BAHIA"


def test_avisos_vazio_sem_dados_do_tomador_nao_identificados(nfse):
    assert nfse.avisos == []


def test_codigo_verificacao_sem_prefixo_alvador_colado(nfse):
    # Antes: "ALVADORETNEWBUQ" (fusão com o fim de "Salvador" do título).
    assert nfse.codigo_verificacao == "ETNEWBUQ"
    assert not nfse.codigo_verificacao.startswith("ALVADOR")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
