# -*- coding: utf-8 -*-
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
import os

# Texto REAL do OCR (Tesseract) da pagina 14 do PDF
# "Notas_Fiscais_emitidas_e_recebidas_05.2026_-_PH_Gestao_SEDE.pdf": NFS-e
# ESCANEADA de Camacari/BA (layout camacari_ba_scan), CONCRETO FORTE LTDA ->
# PH Gestao, nota no 9100, usinagem de concreto, R$ 3.930,00. Regressao do bug
# real: o recorte largo do cabecalho (x=0.72) lia a "Inscricao Municipal:
# 0042148001" do prestador no lugar da celula "Numero da Nota / Data de
# Emissao / Codigo", fazendo o numero sair "9042148001" (a IM) e a data cair
# na "Data da prestacao do servico" (08/05) em vez da emissao (11/05). O
# recorte estreito ADITIVO (x=0.78) recupera "9100 / 11/05/2026 12:50 /
# 8075HO406" (so corta a 1a letra dos rotulos -> "imero"/"ata"/"digo", que a
# extracao tolera). O texto abaixo contem AMBOS os recortes concatenados.
MOCK_TEXT = 'Número da Nota\nData de Emissão\nCódigo de autenticidade\n9042148001\nNº: S/N\nCAMACARI\n\nimero da Nota\n9100\nata de Emissão\n11/05/2026 12:50\nódigo de autenticidade\n8075H0406\n\n)1\n\nNº: S/N\nRi\n\nUF: BA\n\nES ur as Número da Nota\nSn PREFEITURA MUNICIPAL DE CAMAÇARI\nii SE . Data de Emissão\nCRE Secretaria da Fazenda\n[a NOTA FISCAL DE SERVIÇOS ELETRÔNICA\n8075H0406\nPRESTADOR DE SERVIÇOS\nNome/Razão Social: CONCRETO FORTE LTDA\nCPF/CNPJ: 39.416.241/0001-51 Inscrição Municipal: 0042148001\nLogradouro: | RUA DOS PLASTICOS Nº: S/N\nCompl.: Bairro: POLO INDUSTRIAL DE CAMACARI\nCEP: 42816230 Município: CAMAÇARI UF: BA\nTOMADOR DE SERVIÇOS\nNome/Razão Social: PH GESTAO E CONSULTORIA S A\nCPF/CNPJ: 25.311.856/0001-09 Inscrição Municipal: 0032346001\nLogradouro: | ALM HUMAITA Nº 0\nCompl.: COND GUARAJUBA S PRE Bairro: GUARAJUBA (MONTE GOR\nCEP: 42840562 Município: CAMACARI UF: BA\nDISCRIMINAÇÃO DOS SERVIÇOS\nUSINAGEM DE CONCRETO CONCRETO USINADO QT.: 1,00 VLR.UNIT.: R$0,03 VLR.TOT.: R$0,03FCK 30,0 BO 120 +- 20 GERAL\nQT.: 6,50 VLR.UNIT.: R$604,61 VLR.TOT.: R$3.929,97NUMERO REMESSAS: 0, 26347FATURA: 11626 END. OBRA: ALM\nGUARAJUBA MALLS O AO LADO DO HIPER IDEAL - BAIRRO: GUARAJUBA (MONTE GOR - CEP: 42840312 MUNICIPIO DA OBRA:\nCAMACARI BA NOME DA OBRA: CONCRETOVAL. APROX. DOS TRIBUTOS R$ 0,00 (0,00%) FONTE: IBPT999/2090-\n26COND. PAGAMENTO: ANTECIPADO\n[mma XML PDF [cade\nRetenções (R$) Totais (R$)\nPIS: 0,00 | Valor dos Serviços (R$) 3.930,00\nCOFINS: 0,00 | Deduções (-) 0,00\nINSS: 0,00 | Base de Cálculo (=) 3.930,00\nIR: 0,00 | Alíquota (%) 5,00\nCSLL: 0,00 | Valor do ISS (R$) 196,50\nOutras: 0,00 | Valor Líquido da Nota (=) 3.930,00\nTotal de Retenções: 0,00\nTipo de tributação: A RECOLHER PELO PRESTADOR Data da prestação do serviço: 08/05/2026\nMunicípio da prestação do serviço: 2905701 - CAMACARI\nMunicípio da tributação: 2905701 - CAMACARI\nCNAE: . . .\nServiço: 000702 - EXECUÇÃO, POR ADMINISTRAÇÃO, EMPREITADA OU SUBEMPREITADA, DE OBRAS DE CONSTRUÇÃO CIVIL,\nHIDRÁULICA OU ELETRICA E DE OUTRAS OBRAS SEMELHANTES, INCLUSIVE SONDAGEM, PERFURAÇÃO DE POÇOS, ESCAVAÇÃO,\nDRENAGEM E IRRIGAÇÃO, TERRAPLANAGEM, PAVIMENTAÇÃO, CONCRETAGEM E A INSTALAÇÃO E MONTAGEM DE PRODUTOS, PEÇAS\nE EQUIPAMENTOS (EXCETO O FORNECIMENTO DE MERCADORIAS PRODUZIDAS PELO PRESTADOR DE SERVIÇOS FORA DO LOCAL DA\nPRESTAÇÃO DOS SERVIÇOS, QUE FICA SUJEITO AO ICMS).\nCPqD - Gestão Pública Data Impressão: 11/05/2026 17:30\n'


def test_extract_camacari2_numero_data_pag14(monkeypatch):
    dummy_path = "tests/dummy_camacari2_pag14.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        # Nucleo do fix: numero NAO pode ser a Inscricao Municipal (9042148001)
        # e a data deve ser a de EMISSAO (11/05), nao a da prestacao (08/05).
        assert nfse.numero == "9100"
        assert nfse.data_emissao.year == 2026
        assert nfse.data_emissao.month == 5
        assert nfse.data_emissao.day == 11
        assert nfse.data_emissao.hour == 12
        assert nfse.data_emissao.minute == 50

        # Codigo de verificacao: alfanumerico (letra+digito) da celula, nao a
        # IM puramente numerica que era capturada antes.
        assert nfse.codigo_verificacao == "8075H0406"
        assert nfse.codigo_verificacao != "9042148001"

        # Entidades/valor de apoio (nao eram o alvo, mas travam contexto).
        assert nfse.prestador.cnpj_cpf == "39416241000151"
        assert nfse.prestador.razao_social == 'CONCRETO FORTE LTDA'
        assert nfse.tomador.cnpj_cpf == "25311856000109"
        assert nfse.valores.valor_servicos == pytest.approx(3930.00)
        assert nfse.servico_codigo == "0702"
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
