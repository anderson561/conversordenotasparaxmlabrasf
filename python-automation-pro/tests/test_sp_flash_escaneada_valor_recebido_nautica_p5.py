# -*- coding: utf-8 -*-
r"""São Paulo/SP ESCANEADA (LAYOUT_SAO_PAULO_2) - prestador FLASH TECNOLOGIA E
INSTITUICAO DE PAGAMENTO LTDA (32.223.020/0001-18), tomador NAUTICA
(16.699.869/0001-06), nota nº 05904515 de 28/10/2026 12:41:18, código
X7LB-KR9W, serviço 03205 - página 5 de "NAUTICA NFSe.pdf".

Impresso: "VALOR TOTAL DO SERVIÇO = R$ 0,00" e "VALOR TOTAL RECEBIDO =
R$ 5.777,33"; deduções/base/ISS 0,00, alíquota 2,00%, retenções 0,00. O XML
saía com ValorServicos/Líquido 0,00 porque (1) o OCR colou "NVALORTOTAL
RECEBIDO" (sem espaço entre VALOR e TOTAL) e a regra Flash não achava o
recebido; (2) a trava do scan exige o recebido ecoado no "Valor Total - R$ X"
da discriminação, que o OCR leu como "R$ 5171733" - mas a linha seguinte da
mesma discriminação, "Compra de Créditos na Plataforma Flash - R$ 5.777,33",
imprime o mesmo valor legível.

O texto abaixo é o retorno REAL e verbatim do OCR (Tesseract) da página 5."""
import os

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor

OCR_NAUTICA_P5 = "SP2RET_FEDERAIS: 0,00 0,00 0,00 0,00\nSP2RET_CSLL: 0,00\n\nIRRF (R$) CSLL (R$) COFINS (R$) PIS/PASEP (R$)\n0,00 0,00 0,00 0,00\n\nNúmero da Nota\n05904515\nData e Hora de Emissão\n28/10/2026 12:41:18\nCódigo de Verificação\nX7LB-KR9W\n\nT nha\n\nNúmero da Nota |\n\nPREFEITURA DO MUNICÍPIO DE SÃO PAULO 05904515\nSECRETARIA MUNICIPAL DA FAZENDA DataeHorade Emissão |\n\nà 28/10/2026 12:\nNOTA FISCAL ELETRÔNICA DE SERVIÇOS - NFS-e | 28/10/2026 174\n\nCódigo de Verificação\nRPS Nº 4357335 Série NFSE2, emitido em 28/10/2026\n\nX7LB-KR9W\n\n| 20261028U32223020000118\nIdentificador Nacional: 35503081232223020000118000000590451526107939347986\n\n| PRESTADOR DE SERVIÇOS\n\nCPF/CNPJ: 32.223.020/0001-18 Inscrição Municipal: 6.141.672-0\nNome/Razão Social: FLASH TECNOLOGIA E INSTITUICAO DE PAGAMENTO LTDA\n\n| Endereço: R EUGENIO DE MEDEIROS 242, ANDAR 4 - PINHEIROS - CEP: 05425-000\n\n| Município: São Paulo UF: SP\n| DD]\n| TOMADOR DE SERVIÇOS\n| Nome/Razão Social: NAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVIÇOS EIRELLI\n| CPF/CNPJ: 16.699.869/0001-06 Inscrição Municipal: ----\n' Endereço: lot loteamento fazenda coutos iii O, GALPAO 14 - coutos - CEP: 41760-000 |\nMunicípio: Salvador UF: BA E-mail: nauticaQQnauticamoveis.com\n|\n| INTERMEDIÁRIO DE SERVIÇOS\n\n[ CPF/CNPJ: --- Nome/Razão Social: ----\nDISCRIMINAÇÃO DE SERVIÇOS\n\n|Valor Total - R$ 5171733\n[Compra de Créditos na Plataforma Flash - R$ 5.777,33\nvalor total de serviços Flash - R$ 0,00\n\n'Data da Compra: 28/10/2026\n\n|\n\n|\n\n| Compra de benefícios - Mobilidade: R$ 5.777,33 (6 depósitos)\nContrato JO2ndm7FXiTJCHTeavzLr\n\n[Autorização de Regime especial - SEI 6017.2019/0041453-7\nlo ISS incide apenas sobre o valor de serviços Flash indicado acima\n\n[Local da prestação de serviços: São Paulo - SP OO\n\ngiseo 10 cubo IO\n\nVALOR TOTAL DO SERVIÇO = R$ 0,00 =\n\n” NVALORTOTAL RECEBIDO = R$ 5.777,33\n\n| Contribuição Previdenciária - Retida (R$) RA “IRRF (R$) COFINS (R$) PIS/PASEP (R$) IPI (R$) |\n| 0,00 0,00 0,00 0,00 2 e dOiDO\n[sei “Contribuições Sociais - Retidas (R$) Descrição Contribuições Sociais - Retidas |\n| 0,00 0 - PIS/COFINS/CSLL Não Retidos.\n\n| Código do Serviço ' o ;\n03205 - Fornecimento e administração de vales-refeição, vales-alimentação, vales-transporte e similares\n\nValor Total das Deduções (R$) Base de Cálculo (R$) Alíquota (%) Valor do ISS (R$) Crédito Programa da NFP (R$) |\n0,00 0,00 2,00% 0,00 0,00\n\nii Município de Prestação do Serviço j Número Inscrição da Obra Valor Aproximado dos Tributos / Fonte |\n\n, OUTRAS INFORMAÇÕES |\n\n(1) Esta NFS-e foi emitida com respaldo na Lei nº 14.097/2005; (2) Esta NFS-e substitui o RPS Nº 4357335 Série NFSE2, emitido em 28/10/2026; (3)0\nISS relativo a esta NFS-e deverá ser recolhido de acordo com as regras da DES-IF, mediante o envio da declaração e a posterior emissão da respectiva |\nguia de pagamento por meio do sistema da DES-IF.;\n\n|\n|\n| |\n|\n\n- Rn\nPágina 1 de 2\n\n"


def _parse_ocr(monkeypatch, texto_ocr):
    caminho = "tests/dummy_flash_nautica_p5_ocr.pdf"
    with open(caminho, "wb") as f:
        f.write(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: texto_ocr)
    try:
        notas = SPPdfExtractor(caminho).parse_multiple()
    finally:
        if os.path.exists(caminho):
            os.remove(caminho)
    assert len(notas) == 1
    return notas[0]


def test_texto_real_tem_as_duas_falhas_de_ocr():
    assert "NVALORTOTAL RECEBIDO = R$ 5.777,33" in OCR_NAUTICA_P5
    assert "Valor Total - R$ 5171733" in OCR_NAUTICA_P5
    assert "Compra de Créditos na Plataforma Flash - R$ 5.777,33" in OCR_NAUTICA_P5


def test_nautica_p5_usa_valor_total_recebido(monkeypatch):
    nfse = _parse_ocr(monkeypatch, OCR_NAUTICA_P5)
    assert nfse.numero == "05904515"
    assert nfse.prestador.cnpj_cpf == "32223020000118"
    v = nfse.valores
    assert v.valor_servicos == 5777.33
    assert v.valor_liquido_nfse == 5777.33
    assert v.valor_deducoes == 0.0
    assert v.base_calculo == 0.0
    assert v.aliquota == 0.02
    assert v.valor_iss == 0.0
    assert (v.valor_pis, v.valor_cofins, v.valor_inss, v.valor_ir, v.valor_csll,
            v.outras_retencoes) == (0.0,) * 6
    assert any("usado o VALOR TOTAL RECEBIDO" in a and "R$ 5.777,33" in a
               and "Flash" in a for a in nfse.avisos)
    assert "Valor dos serviços extraído como zero" not in nfse.avisos


def test_nautica_p5_recebido_divergente_da_discriminacao_mantem_zero(monkeypatch):
    # recebido lido diferente do eco "Compra de Créditos ... R$ 5.777,33": não confia
    texto = OCR_NAUTICA_P5.replace("NVALORTOTAL RECEBIDO = R$ 5.777,33",
                                   "NVALORTOTAL RECEBIDO = R$ 5.717,33")
    nfse = _parse_ocr(monkeypatch, texto)
    assert nfse.valores.valor_servicos == 0.0
    assert nfse.valores.valor_liquido_nfse == 0.0
    assert any("Prestador Flash" in a and "não foi confirmado" in a for a in nfse.avisos)


def test_nautica_p5_sem_eco_legivel_na_discriminacao_mantem_zero(monkeypatch):
    # sem nenhum eco legível do recebido na discriminação: a trava do scan segura
    texto = OCR_NAUTICA_P5.replace(
        "Compra de Créditos na Plataforma Flash - R$ 5.777,33",
        "Compra de Créditos na Plataforma Flash - R$ 5177733")
    nfse = _parse_ocr(monkeypatch, texto)
    assert nfse.valores.valor_servicos == 0.0
    assert any("Prestador Flash" in a and "não foi confirmado" in a for a in nfse.avisos)
