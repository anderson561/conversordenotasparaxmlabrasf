# -*- coding: utf-8 -*-
"""Salvador/BA escaneado — 4 bugs na MESMA nota, todos frutos de ruído de OCR
não coberto pelos testes anteriores.

Achado real (nota nº 00006508, RPS 8487, INTERNET TECNOLOGIA DE SISTEMAS LTDA
-> ITACIMIRIM PARTICIPACÕOES E EMPREENDIMENTOS SA, LICENCIAMENTO TEMPORÁRIO DO
SISTEMA FINANCEIRO INTERBAN, R$301,00): texto OCR real capturado via
`SPPdfExtractor._ocr_page(2)` (mesmo caminho usado em produção, com o recorte de
cabeçalho que recupera o "Número da Nota:
DOR 00006508").

1. CNPJ do PRESTADOR e do TOMADOR reprovam o dígito verificador (1 dígito
   corrompido no scan de cada um) e caem no sentinela `00000000000100`
   (comportamento correto, mesmo precedente do Camaçari-3: nunca propagar CNPJ
   com checksum inválido) — mas a Inscrição Municipal do prestador saia
   contaminada com os próprios dígitos do CNPJ rejeitado (o filtro só excluia
   o `cnpj` JÁ resolvido/sentinela, não o candidato bruto rejeitado).
2. Endereço do prestador: o campo `Numero` saia com o complemento+bairro+
   cidade inteiros colados ("COND BOULEVARD SIDE EMPR SALA - CAMINHO DAS
   ÁRVORES - Salvador -") em vez de "290" — o bloco Salvador-específico corrigia
   logradouro/bairro/município mas nunca separava número de complemento.
3. Grade Base de Cálculo/Alíquota/Valor do ISS saia errada (9.00 / 0.00 / 0.00
   em vez de 301.00 / 0.05 / 15.05) porque o rótulo veio com ruído de OCR
   embutido ("Alíquota (9%)" em vez de "(%)"), e as 3 regex antigas liam
   "primeiro número depois do rótulo" em vez da linha de 5 valores na posição
   certa.
4. Código de serviço caia no fallback genérico "03115" em vez de "0105" porque
   o OCR leu "ltem" (l minúsculo) em vez de "Item".
"""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_OCR = 'Número da Nota:\nDOR 00006508\nData e Hora de Emissão:\n\nPREFEITURA MUNICIPAL DO SALVADOR  |ootasos o\n\nSECRETARIA MUNICIPAL DA FAZENDA Data é Hora de Emissão:\n01/07/2026 06:03:23\nNOTA FISCAL DE SERVIÇOS ELETRÔNICA - Nota Salvador RAP up jo reação:\nRPS Nº 8487 Série 1, emitido em 01/07/2026\n\nPRESTADOR DE SERVIÇOS\n\nCPF/CNPJ: Inscrição Municipal\n\n34.288.699/0001-79 00.073.343/001-13\n\nNome/Razão Social\n\nINTERNET TECNOLOGIA DE SISTEMAS LTDA\n\nEndereço: .\n\nua Ewerton Visco 290 , COND BOULEVARD SIDE EMPR SALA - CAMINHO DAS ÁRVORES - Salvador - CEP: 41820-022 - BA\n-mail:\n\nwilliams Qinterban.com.br\n\nTOMADOR DE SERVIÇOS\n\nNome/Razão Social\nITACIMIRIM PARTICIPACÕOES E EMPREENDIMENTOS SA\nCPF/CNPJ: Inscrição Municipal\n\n61.229.895/0001-90 ==\nEndereço:\nRUA ALA DAS DUNAS SN, AL GUARAJUBA MAALLS GUARAJUBA (MONTE GORDO) - Camaçari - CEP: 42840312/BA\n\nDISCRIMINAÇÃO DOS SERVIÇOS\n\nLICENCIAMENTO TEMPORARIO DO SISTEMA FINANCEIRO INTERBAN\n\nVALOR TOTAL DA NOTA = R$301,00\n\nCNAE:\n6202300 - Desenvolvimento e licenciamento de programas de computador customizáveis\n\nltem da Lista de Serviços:\n\n00105 - Licenciamento ou cessão de direito de uso de programas de computação.\n\nValor Total das Deduções (R$): Base de Cálculo (R$): Alíquota (9%): Valor do ISS (R$): Crédito Mota Salvador (R$):\n0,00 301,00 5,00% 15,05 0,00\n\nValor INSS (R$) Valor PIS (R$) Valor COFINS (R$) | Valor IR (R$) Valor CSLL (R$) Outras Retenções (R$)] Valor Líquido (R$)\n0,00 0,00 0,00 0,00 0,00 0,00 301,00\n\nAlíquota IBS (%) Valor IBS (R$) Alíquota CBS (%) Valor CBS (R$)\n\nOUTRAS INFORMAÇÕES\n\n- Esta Nota Salvador foi emitida com respaldo na Lei 7.186/2006\n\n- Esta Nota Salvador substitui o RPS Nº 848? Série 1, emitido em 01/07/2026\n\n- Data de vencimento do ISS desta Nota Salvador: 05/08/2026\n\n- COMPETÊNCIA: 07/2026 (mês/ano)\n\n- Código de Tributação do Município: 0105-0/01 - Licenciamento de uso de programa de computação\n\n'


@pytest.fixture
def nfse(monkeypatch):
    dummy_path = "tests/dummy_salvador_6508.pdf"
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
    assert nfse.numero == "00006508"


def test_prestador_cnpj_invalido_cai_no_sentinela_sem_contaminar_im(nfse):
    p = nfse.prestador
    # CNPJ reprova checksum (dígito esperado seria 5, veio 7) -> sentinela + aviso,
    # nunca propagar um CNPJ inválido (mesmo precedente do Camaçari-3).
    assert p.cnpj_cpf == "00000000000100"
    # Inscrição Municipal REAL ("00.073.343/001-13" no OCR) — antes vinha
    # contaminada com os próprios dígitos do CNPJ rejeitado (34288699000179).
    assert p.inscricao_municipal == "0007334300113"
    assert p.inscricao_municipal != "34288699000179"


def test_tomador_cnpj_invalido_cai_no_sentinela_sem_contaminar_im(nfse):
    tm = nfse.tomador
    # CNPJ reprova checksum (dígito esperado seria 2, veio 9) -> mesmo sentinela.
    assert tm.cnpj_cpf == "00000000000100"
    # OCR não traz um 2º número legível pra IM do tomador ("==" é ruído) — None,
    # nunca o próprio CNPJ rejeitado vazando pra IM.
    assert tm.inscricao_municipal != "61229895000190"


def test_prestador_endereco_numero_separado_do_complemento(nfse):
    e = nfse.prestador.endereco
    assert e.numero == "290"
    assert e.complemento == "COND BOULEVARD SIDE EMPR SALA"
    assert "COND BOULEVARD" not in e.numero
    assert e.bairro == "CAMINHO DAS ÁRVORES"
    assert e.municipio == "Salvador"
    assert e.uf == "BA"
    assert e.cep == "41820022"


def test_tomador_endereco_sn_glued_ao_logradouro(nfse):
    # "RUA ALA DAS DUNAS SN" (sem vírgula) — variante distinta da do
    # prestador (que tem número real + vírgula): o "SN" (sem número) fica
    # colado ao logradouro, sem separador nenhum. Sem tolerar isso, o campo
    # `numero` ficava com o lixo do split genérico por vírgula (o bloco
    # Salvador-específico só sobrescrevia `numero` quando achava um dígito).
    e = nfse.tomador.endereco
    assert e.logradouro == "RUA ALA DAS DUNAS"
    assert e.numero == "S/N"
    assert e.municipio == "Camaçari"
    assert e.uf == "BA"


def test_grade_base_aliquota_iss_imune_a_ruido_no_rotulo(nfse):
    v = nfse.valores
    assert v.valor_servicos == 301.00
    assert v.valor_deducoes == 0.00
    assert v.base_calculo == 301.00
    assert v.aliquota == 0.05
    assert v.valor_iss == 15.05


def test_codigo_servico_tolera_ltem_no_lugar_de_item(nfse):
    assert nfse.servico_codigo == "0105"
    assert nfse.servico_codigo != "03115"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
