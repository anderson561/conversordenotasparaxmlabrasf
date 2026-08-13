# -*- coding: utf-8 -*-
"""Extração genérica de Data de Emissão (compartilhada por ~30 layouts):
quando o texto tem MAIS de um rótulo de data batendo, a data com HORA
completa deve ganhar de uma data sem hora, mesmo que o rótulo sem hora
apareça mais cedo na lista de prioridade (`data_emissao_labels`).

Nota real São Paulo/SP escaneada (FLASH TECNOLOGIA E INSTITUICAO DE
PAGAMENTO LTDA, nº 05121900): o aviso de substituição do RPS ("...Esta
NFS-e substitui o RPS Nº 3574129 Série NFSE2, emitido em 06/07/2026")
casa com o padrão "Emitido em" (1º da lista, sem hora) ANTES do padrão
"Data e Hora de Emissão" (mais abaixo na lista, mas com o timestamp
completo "06/07/2026 16:41:44" vindo do cabeçalho de verdade) — o loop
antigo retornava no primeiro match e zerava a hora para 00:00:00.
"""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_OCR = 'Número da Nota\n05121900\n\n» - Número da Nota\nPREFEITURA DO MUNICÍPIO DE SÃO PAULO 05121900\nSECRETARIA MUNICIPAL DA FAZENDA Data e Hora de Emissão\nR 06/07/2026 16:41:44\n\nNOTA FISCAL ELETRÔNICA DE SERVIÇOS - NFS-e Código de Verificação\n20260706132223020000118 RPS Nº 3574129 Série NFSE2, emitido em 06/07/2026 MKT3-B9ZH\n\nIdentificador Nacional: 35503081232223020000118000000512190026077877029781\n\nPRESTADOR DE SERVIÇOS\nCPF/CNPJ: 32.223.020/0001-18 Inscrição Municipal: 6.141.672-0\n\nNomey/Razão Social: FLASH TECNOLOGIA E INSTITUICAO DE PAGAMENTO LTDA\nEndereço: R EUGENIO DE MEDEIROS 242, ANDAR 4 - PINHEIROS - CEP: 05425-000\nMunicípio: São Paulo UF: SP\n\nTOMADOR DE SERVIÇOS\nNomey/Razão Social: TEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDA\nCPF/CNPJ: 07.345.543/0001-90 Inscrição Municipal: ----\nEndereço: RT R TERRITORIO DO AMAPA 146, Casa 2 - PITUBA - CEP: 41830-540\nMunicípio: Salvador UF: BA E-mail: financeirotemis-es.com.br\nINTERMEDIÁRIO DE SERVIÇOS\nCPF/CNPJ: ---- Nomey/Razão Social: ----\n\nDISCRIMINAÇÃO DE SERVIÇOS\n\nValor Total - R$ 1.990,00\n\nCompra de Créditos na Plataforma Flash - R$ 1.990,00\nValor total de serviços Flash - R$ 0,00\n\nData da Compra: 06/07/2026\n\nCompra de benefícios - Auxilio Alimentação e Refeição: R$ 1.754,00 (2 depósitos)\nCompra de benefícios - Auxilio Mobilidade: R$ 236,00 (1 depósito)\n\nContrato Glodv7UkFo96b2k2nZHxV\nAutorização de Regime especial - SEI 6017.2019/0041453-7\nO ISS incide apenas sobre o valor de serviços Flash indicado acima\n\nLocal da prestação de serviços: São Paulo - SP\n\nBeneficio Julho\n\nVALOR TOTAL DO SERVIÇO = R$ 1.990,00\nContribuição Previdenciária - Retida (R$) IRRF (R$) COFINS (R$) PIS/PASEP (R$) IPI(R$)\n0,00 0,00 0,00 0,00 0,00\nContribuições Sociais - Retidas (R$) Descrição Contribuições Sociais - Retidas\n0,00 -\n\nCódigo do Serviço\n03205 - Fornecimento e administração de vales-refeição, vales-alimentação, vales-transporte e similares\n\nValor Total das Deduções (R$) Base de Cálculo (R$) Alíquota (%) Valor do ISS (R$) Crédito Programa da NFP (R$)\n1.990,00 0,00 2,00% 0,00 0,00\nMunicípio de Prestação do Serviço Número Inscrição da Obra Valor Aproximado dos Tributos / Fonte\nOUTRAS INFORMAÇÕES\n\n(1) Esta NFS-e foi emitida com respaldo na Lei nº 14.097/2005; (2) Esta NFS-e substitui o RPS Nº 3574129 Série NFSEZ2, emitido em 06/07/2026; (3) O\nISS relativo a esta NFS-e deverá ser recolhido de acordo com as regras da DES-IF, mediante o envio da declaração e a posterior emissão da respectiva\nguia de pagamento por meio do sistema da DES-IF.; (4) Dedução com base em decisão judicial e/ou administrativa.;\n\nPágina 1 de 2\n\n'


def test_data_emissao_prefere_horario_completo_a_emitido_em_sem_hora(monkeypatch):
    dummy_path = "tests/dummy_flash_beneficio.pdf"
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

        # BUG CORRIGIDO: número saía "392" (recorte fixo por percentual caía
        # na caixa "Código de Verificação" vizinha).
        assert nfse.numero == "05121900"
        assert nfse.codigo_verificacao == "MKT3-B9ZH"

        # BUG CORRIGIDO: hora saía 00:00:00 ("emitido em 06/07/2026", sem
        # hora, vencia "Data e Hora de Emissão...16:41:44" por prioridade de
        # lista, não por completude do match.
        assert nfse.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "06/07/2026 16:41:44"
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
