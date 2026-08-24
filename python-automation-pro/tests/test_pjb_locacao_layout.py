# -*- coding: utf-8 -*-
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
import os

# Texto REAL do OCR (Tesseract, via _ocr_page padrao) da pagina 13 do PDF
# "Notas_Fiscais_emitidas_e_recebidas_05.2026_-_PH_Gestao_SEDE.pdf": a FATURA DE
# LOCACAO da PJB Construcao Aluguel de Maq. e Ser. (Simoes Filho/BA, CNPJ
# 08.885.357/0001-06) para PH Gestao e Consultoria S.A. (nota 22980, locacao de
# equipamento para bombeamento de concreto, R$ 1.050,00). Preservado verbatim,
# incluindo os quirks que travam regressoes:
#  - a frase "FATURA DE LOCACAO" chega garblada ("FATURA Dl N / LOCACAO"), logo
#    a deteccao NAO pode depender dela nem do fallback generico de locacao;
#  - o CNPJ do emitente (08.885.357) nao sobrevive ao OCR padrao desta pagina,
#    por isso a deteccao e por razao "PJB CONSTRU" + marcador estrutural da
#    fatura (DESTINATARIO/NATUREZA), e o prestador e FIXO;
#  - o texto cita "SIMOES FILHO", "CAMACARI" e "MONTE GORDO" (cidades do
#    emitente/tomador) - a deteccao fica no TOPO da cadeia para nao ser
#    interceptada pelos layouts municipais homonimos;
#  - o bairro do tomador vem impresso TRUNCADO pelo proprio scan ("GUARAJUBA
#    (MONTE GOR") - extraido como esta, sem completar/fabricar.
MOCK_TEXT = 'PJB CONSTRUCAO ALUGUEL DE\n\no | ço | E MAQ. E SER.LTD\n\nUGUEL DE MAQUINAS FONE/FAX:\n\nFATURA Dl Nº\nLOCAÇÃO 22.980\n(0) 0-\n\nVIA ACESSO II BR 324, 0\nCIA SUL - SIMÕES FILHO - BA CEP 43700000\n\nNatureza da Operação\nLOCAÇÃO DE MÁQUINAS E EQUIPAMENTOS SEM OPERADOR\n\nDESTINATÁRIO/REMETENTE\n\nPH GESTAO E CONSULTORIA S.A. 25.311.856/0001-09\nEndereço Bairro/Distrito CEP\n\nALM HUMAITÁ, O GUARAJUBA (MONTE GOR\nMunicípio Fone/Fax UF Inscrição Estadual\nengenhariafguarajubacenter.com.br\n\nR$ 1.050,00 22980 1 08/05/2026\n\nADOS DO PRODUTO\nDESCRIÇÃO QUANT. VALOR UNITARIO VALOR TOTAL\n\nLOCAÇÃO DE EQUIPAMENTO PARA BOMBEAMENTO DE CONCRETO. 1 1.050,00 1.050,00\nEnd. Obra: ALM GUARAJUBA MALLS O AO LADO DO HIPER\n\nIDEAL - Bairro: GUARAJUBA (MONTE GOR - CEP: 42840312 -—\n\nMunicípio da Obra: CAMAÇARI BA - Nome da Obra:\n\nBOMBA COM ESPALHAMENTO -\n\nVAL. APROX. DOS TRIBUTOS R$ 525,00 (50,00%) Fonte:\n\nIBPT Quantidade = 6,50\n\nVALOR POR EXTENSO VALOR TOTAL DA FATURA EM R$\nUm mil cinquenta reais\ndé etnqu + 1.050,00\n\nêVIA EMITENTE\n\nEstadual\nISENTO\n\nData Emissão\n08/05/2026\n\nData Saída/Entrada\n08/05/2026\n\nNÃO INCIDÊNCIA DO ISS CONFORME LEI FEDERAL COMPLEMENTAR N.116\n\nDE 31.07.2003. NÃO É POSSÍVEL A EMISSÃO DE NFS, DE QUALQUER\n\nESPÉCIE, PARA TAL TIPO DE ATIVIDADE (LOCAÇÃO DE BENS MÓVEIS) ANTECIPADO\nÉ ILEGAL A CONCESSÃO DE AUTORIZAÇÃO PARA IMPRESSÃO DE\n\nDOCUMENTOS FISCAIS COM A FINALIDADE DE DOCUMENTAR A ATIVIDADE\n\nDE LOCAÇÃO DE BENS MÓVEIS.\n\nRECONHEÇO (EMOS) A EXATIDÃO DESTA FATURA NA IMPORTÂNCIA ACIMA QUE PAGAREI (EMOS) À FATURA\nSERVIÇOS PJB CONSTRUCAO ALUGUEL DE MAQ. E SER.LTD, OU A SUA ORDEM NO VENCIMENTO\n\nNº 22.980\n\n'


def test_extract_pjb_locacao_layout(monkeypatch):
    dummy_path = "tests/dummy_pjb_locacao.pdf"
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

        assert nfse.numero == "22980"
        assert nfse.servico_codigo == "0000"
        assert nfse.data_emissao.year == 2026
        assert nfse.data_emissao.month == 5
        assert nfse.data_emissao.day == 8

        # Prestador FIXO (emitente PJB, Simoes Filho/BA registrada no KNOWN_CITIES).
        assert nfse.prestador.cnpj_cpf == "08885357000106"
        assert nfse.prestador.razao_social == 'PJB CONSTRUÇÃO ALUGUEL DE MÁQ. E SER. LTDA'
        assert nfse.prestador.endereco.logradouro == 'Via Acesso II BR 324'
        assert nfse.prestador.endereco.numero == "S/N"
        assert nfse.prestador.endereco.municipio == 'Simões Filho'
        assert nfse.prestador.endereco.codigo_municipio == "2930709"
        assert nfse.prestador.endereco.uf == "BA"
        assert nfse.prestador.endereco.cep == "43700000"

        # Tomador parseado do bloco DESTINATARIO/REMETENTE. Municipio assumido
        # Camacari/BA (Guarajuba/Monte Gordo e distrito de Camacari) - decisao
        # do usuario. Bairro truncado pelo scan (nao fabricar o "DO)" faltante).
        assert nfse.tomador.cnpj_cpf == "25311856000109"
        assert nfse.tomador.razao_social == 'PH GESTAO E CONSULTORIA S.A'
        assert nfse.tomador.endereco.logradouro == 'ALM HUMAITÁ'
        assert nfse.tomador.endereco.numero == "S/N"
        assert nfse.tomador.endereco.bairro == 'GUARAJUBA (MONTE GOR'
        assert nfse.tomador.endereco.municipio == 'Camaçari'
        assert nfse.tomador.endereco.codigo_municipio == "2905701"
        assert nfse.tomador.endereco.uf == "BA"

        # Fatura de locacao nao tem intermediario.
        assert nfse.intermediario is None

        # Locacao de bens moveis: NAO incide ISS (base/aliquota/ISS = 0).
        val = nfse.valores
        assert val.valor_servicos == pytest.approx(1050.00)
        assert val.valor_liquido_nfse == pytest.approx(1050.00)
        assert val.valor_iss == 0.0
        assert val.aliquota == 0.0
        assert val.base_calculo == 0.0

        # So o aviso do codigo de verificacao (fatura nao tem NFS-e verification
        # code) - o de "valor zero" NAO pode aparecer (valor foi extraido).
        assert not any("valor" in a.lower() for a in nfse.avisos)
        assert nfse.avisos == ['Código de verificação/autenticidade não encontrado']
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
