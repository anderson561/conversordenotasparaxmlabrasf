# -*- coding: utf-8 -*-
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
import os

# Texto REAL do OCR (Tesseract) da pagina 20 do PDF
# "Notas_Fiscais_emitidas_e_recebidas_07.2026_-_PH_Gestao_SEDE.pdf": NFS-e
# ESCANEADA de Camacari/BA (layout camacari_ba_scan_v3), AVANCO GESTAO E
# ADMINISTRACAO LTDA -> PH Gestao, nota no 285, R$ 572,42. Regressao do bug
# real: das 3 tentativas de recorte do cabecalho empilhadas, UMA perde o
# "um" inteiro do rotulo ("nero da Nota" em vez de "numero"/"...mero da
# Nota") - e e justo essa tentativa que traz o numero colado ("nero da
# Nota\n285"); a tentativa com o rotulo limpo ("Numero da Nota", mais
# abaixo, no corpo) nao tem numero por perto (cai antes do nome da
# prefeitura). Sem tolerar essa variante degradada, a ancora "...mero da
# Nota" nao casava com numero nenhum por perto e o numero desabava para o
# fallback "00000000". Distinto do caso da nota 20335 (PADUA, ver
# test_camacari3_padua_layout.py): aqui o "285" e corroborado por aparecer
# TAMBEM como 1a linha solta de outro bloco do cabecalho (script de
# seguranca contra aceitar um numero de OUTRO campo so porque ele calhou de
# ficar colado a um rotulo degradado).
MOCK_TEXT = (
    '285\nData de Emissão\nCódigo de autenticidade\n066628001\nNº: SN\n'
    'SORDO)\n\nnero da Nota\n285\na de Emissão\n15/07/2026 10:44\nJigo de '
    'autenticidade\n641K11H27\n1\nNº: SN\nUF: BA\n\n285\nData de Emissão\n'
    'Código de autenticidade\n)066628001\nNº: SN\nORDO)\n\nEAR ra Número '
    'da Nota\npl PREFEITURA MUNICIPAL DE CAMAÇARI\nerp . Data de Emissão\n'
    'Eus Secretaria da Fazenda\nNOTA FISCAL DE SERVIÇOS ELETRÔNICA\n'
    'PRESTADOR DE SERVIÇOS\nNome/Razão Social: AVANÇO GESTÃO E '
    'ADMINISTRAÇÃO LTDA\nCPF/CNPJ: 59.132.742/0001-13 Inscrição '
    'Municipal: 0066628001\nLogradouro: RUA ALA DAS DUNAS Nº: SN\n'
    'Compl.: | :GUARAJUBA SHOPPING;LOJA:03;QUADRA:C-4 Bairro: GUARAJUBA '
    '(MONTE GORDO)\nCEP: 42840312 Município: CAMAÇARI UF: BA\nTOMADOR DE '
    'SERVIÇOS\nNome/Razão Social: PH GESTAO E CONSULTORIA S A\n'
    'CPF/CNPJ: 25.311.856/0001-09 Inscrição Municipal: 0032346001\n'
    'Logradouro: | ALAMEDA HUMAITA Nº: S/N\nCompl.: COND GUARAJUBA S '
    'PREMIUS Bairro: GUARAJUBA (MONTE GORDO)\nCEP: 42840562 Município: '
    'CAMAÇARI UF: BA\nDISCRIMINAÇÃO DOS SERVIÇOS\nDESCRIÇÃO QTD VALOR '
    'UNIT (R$) VALOR TOTAL (R$)\nTAXA DE SERVIÇOS COMBINADOS DE '
    'ESCRITÓRIO E APOIO ADMINISTRATIVO 1,0000 572,42 572,42\nfofa XML '
    'PDF [loEini\nRetenções (R$) Totais (R$)\nPIS: 0,00 |Valor dos '
    'Serviços (R$) 572,42\nCOFINS: 0,00 | Deduções (-) 0,00\nINSS: 0,00 '
    '| Base de Cálculo (=) 572,42\nIR: 0,00 | Alíquota (%) 5,00\n'
    'CSLL: 0,00 | Valor do ISS (R$) 28,62\nOutras: 0,00 | Valor Líquido '
    'da Nota (=) 572,42\nTotal de Retenções: 0,00\nTipo de tributação: '
    'A RECOLHER PELO PRESTADOR Data da prestação do serviço: '
    '15/07/2026\nMunicípio da prestação do serviço: 2905701 - CAMACARI\n'
    'Município da tributação: 2905701 - CAMACARI\nCNAE: 8211-3/00 - '
    'SERVIÇOS COMBINADOS DE ESCRITÓRIO E APOIO ADMINISTRATIVO\n'
    'Serviço: 001703 - PLANEJAMENTO, COORDENAÇÃO, PROGRAMAÇÃO OU '
    'ORGANIZAÇÃO TÉCNICA, FINANCEIRA OU ADMINISTRATIVA.\nLE ===\n'
    'CPqD - Gestão Pública Data Impressão: 15/07/2026 10:44\n'
)


def test_extract_camacari3_numero_nero_da_nota(monkeypatch):
    dummy_path = "tests/dummy_camacari3_pag20_285.pdf"
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

        # Nucleo do fix: numero NAO pode ser o fallback "00000000" -> deve
        # ser "285", recuperado da ocorrencia degradada "nero da Nota"
        # (corroborada por aparecer solta em outro bloco do cabecalho).
        assert nfse.numero == "285"
        assert nfse.numero != "00000000"
        assert "Número da nota não encontrado" not in nfse.avisos

        assert nfse.codigo_verificacao == "641K11H27"
        assert nfse.data_emissao.strftime("%d/%m/%Y") == "15/07/2026"
        assert nfse.competencia.strftime("%m/%Y") == "07/2026"

        assert nfse.prestador.cnpj_cpf == "59132742000113"
        assert nfse.prestador.razao_social == "AVANÇO GESTÃO E ADMINISTRAÇÃO LTDA"
        assert nfse.tomador.cnpj_cpf == "25311856000109"
        assert nfse.tomador.razao_social == "PH GESTAO E CONSULTORIA S A"
        assert nfse.valores.valor_servicos == pytest.approx(572.42)
        assert nfse.servico_codigo == "1703"
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
