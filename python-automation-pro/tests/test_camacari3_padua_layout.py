# -*- coding: utf-8 -*-
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor
import os

# Texto REAL do OCR (Tesseract) da NFS-e de Camaçari/BA ESCANEADA (nota real
# nº 20335, PADUA COMERCIO E REFORMA DE PNEUS LTDA - ME -> DELTALINE SERVICOS
# LTDA). Preservado verbatim, incluindo os quirks que motivaram o novo layout
# LAYOUT_CAMACARI_3 (superset de topo do LAYOUT_CAMACARI_2, sem alterar o
# código deste último):
#  - o recorte de cabeçalho (_ocr_header_box_camacari) concatena 2-3
#    tentativas independentes de OCR da MESMA região; nesta nota, NENHUMA das
#    3 tentativas preservou "Número" com "ú" - saem "Núrmero"/"enero"/"Nirmaro"
#    - e o valor que aparece junto ("20338") sai com o penúltimo dígito
#    trocado pelo OCR (o valor real, "20335", só é recuperável pelo nome do
#    arquivo - por isso o teste usa um dummy_path com "NF 20335" no nome,
#    replicando a convenção real de nomenclatura desta pasta de notas);
#  - "Nome/Raz~ao Social" do PRESTADOR sai "Nome/Razho Social." (garbling
#    ão -> ho) e do TOMADOR sai "None/Razão Social:" (garbling Nome -> None) -
#    dois garbles DIFERENTES do mesmo rótulo na mesma nota;
#  - o CNPJ do PRESTADOR sai "24.928 188/0001-47" (espaço no lugar do ponto E
#    dígito trocado) - checksum inválido, então LAYOUT_CAMACARI_3 descarta e
#    cai no sentinela + aviso em vez de propagar um CNPJ plausível-mas-errado;
#  - o CNPJ do TOMADOR sai "01 813.680/0001-25" (só o separador é espaço) -
#    checksum válido, extraído normalmente;
#  - "Bairro" do prestador sai "Balro" (l no lugar do i) e "Nº" da razão
#    social "Nome/Razho Social." quase colide com o padrão de número de
#    endereço (regride para "me" se o separador não exigir pontuação
#    explícita logo após "Nº").
MOCK_TEXT = ('Núrmero da Nta\n21072028 09:12\nS00symryu\n0032057004\nNº: '
             '00022:\n\nenero da Nota\n20338\n\nta da Emingás :\n\n2110712008 '
             '09:42\n\n S008MPYU\n\n014\nNº: 00022:\n\npasaa UF. BA\n\n'
             'Nirmaro da Nota\nmtas  riendo\n270712026 09:12\n— SO08YM7YU\n'
             '12057001\nNº 00022;\n\nPREFEITURA MUNICIPAL DE CAMAÇARI\n'
             'Secretaria da Fazenda eta da Emissão\nNOTA FISCAL DE SERVIÇOS '
             'ELETRÔNICA ese UR 09:12\no — PRESTADOR DE SERVIÇOS add dido\n'
             'Nome/Razho Social. PADUA COMERCIO E REFORMA DE PNEUS LTDA - '
             'ME\nCPFICNPI. 24.928 188/0001-47 losci\nLogradouro: RIO '
             'BANDEIRA | neerição Municipal: 0032087001\nCompl: LOTE 21 '
             'QUADRA 55 Balro: A Nº; 00022:\nCEP. 42804039 Municipio: '
             'CAMAÇARI | A SRANGULO\nTOMADOR DE LR,\nNone/Razão Social: '
             'DELTALINE SERVICOS LTDA. SERVIÇOS\nCPF/CNPJ. 01 '
             '813.680/0001-25\nLogradouro: RUA CAMBORIU Inscrição '
             'Municipal.\nCompl.: ;\nBairro: Nº. 38\nCEP. 40330533 '
             'Munteiplo: SALVADOR a\nDISCRIMINAÇÃO DOS SERVIÇOS MA,\nFR - '
             'QTDE 2 X VALOR UNIT. R$ 60,00 = TOTAL R$ 120,00. [| FORMA DE '
             'PAG\nAMENTO CARTÃO DE CREDITO | PLACA\nRetenções (R$) Totais '
             '(R$)\nPIS: 0,00 | Valor dos Serviços (R$) 120,00\nCOFINS: '
             '0,00 | Deduções (-) 0,00\nINSS: 0,00 | Base de Cálculo (=) '
             '120,00\nIR: 0,00 |Aliquota (%) 5.00\nCSLL: 0,00 | Vator do '
             'ISS (R$) 6,00\nOutras: 0,00 | Valor Liquido da Nota (=) '
             '120,00\nTotal de Retenções: 0,00\nTipo de tributação: A '
             'RECOLHER PELO PRESTADOR Data da prestação do serviço: '
             '27/07/2026\nMunicipio da prestação do serviço: 2905701 - '
             'CAMACARI\nMunicípio da tributação: 2905701 - CAMACARI | O '
             'TORES\nCNAE: 4520-0/04 - SERVIÇOS DE ALINHAMENTO E '
             'BALANCEAMENTO DE VE CULOS AU\nServiço: 001401 -  '
             'OERIFICAÇÃO: LIMPEZA, LUSTRAÇÃO, REVISÃO, CARGA E RECARGA, '
             'CONSERTO, Da EE OU DE\nMANUTENÇÃO E CONSERVAÇÃO DE MÁQUINAS, '
             'VEÍCULOS, APARELHOS, EQUIPAMENTOS, inata :\nQUALQUER OBJETO '
             '(EXCETO PEÇAS E PARTES EMPREGADAS, QUE FICAM SUJEITAS AO | '
             ').\n| CPqD - Gestão Pública Data Impressão: 27/07/2026 '
             '09:13\n')


def test_extract_camacari3_padua_layout(monkeypatch):
    # Nome de arquivo replica a convenção real desta pasta de notas
    # ("<data> - NF <numero> - <razão social>.pdf"): é o fallback que
    # recupera o número correto quando as 3 tentativas de OCR do cabeçalho
    # concordam em errar o dígito ("20338" em vez de "20335").
    dummy_path = ("tests/2026.07.27 - NF 20335 - PADUA COMERCIO E REFORMA "
                  "DE PNEUS LTDA - ME.pdf")
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

        # Regressão principal #1: número correto (era "00022", fantasma das
        # 3 tentativas de header-crop; recuperado via fallback do nome do
        # arquivo, já que nenhuma tentativa de OCR do cabeçalho acerta o
        # dígito nesta nota específica).
        assert nfse.numero == "20335"
        assert nfse.data_emissao.strftime("%d/%m/%Y") == "27/07/2026"
        assert nfse.competencia.strftime("%m/%Y") == "07/2026"
        assert nfse.servico_codigo == "1401"

        # Regressão principal #2: o CNPJ do prestador NUNCA pode ser o do
        # tomador (bug relatado: "prestador de serviços incorretos"). Como o
        # CNPJ capturado ("24.928 188/0001-47") não passa no checksum e não
        # há mecanismo de correção de dígito para prestador, o layout
        # descarta para o sentinela + aviso em vez de arriscar um fallback
        # genérico que poderia atribuir o CNPJ de OUTRA entidade do
        # documento.
        assert nfse.prestador.cnpj_cpf == "00000000000000"
        assert nfse.prestador.cnpj_cpf != nfse.tomador.cnpj_cpf
        assert nfse.prestador.razao_social == "PADUA COMERCIO E REFORMA DE PNEUS LTDA - ME"
        assert nfse.prestador.endereco.numero == "00022"
        assert nfse.prestador.endereco.complemento == "LOTE 21 QUADRA 55"
        assert nfse.prestador.endereco.codigo_municipio == "2905701"
        assert nfse.prestador.endereco.municipio == "CAMACARI"
        assert nfse.prestador.endereco.uf == "BA"
        assert nfse.prestador.endereco.cep == "42804039"

        # Tomador: CNPJ com checksum válido, extraído normalmente (era o
        # valor que aparecia erradamente no prestador antes do fix).
        assert nfse.tomador.cnpj_cpf == "01813680000125"
        assert nfse.tomador.razao_social == "DELTALINE SERVICOS LTDA. SERVIÇOS"
        assert nfse.tomador.endereco.numero == "38"
        assert nfse.tomador.endereco.cep == "40330533"
        assert nfse.tomador.endereco.uf == "BA"

        val = nfse.valores
        assert val.valor_servicos == pytest.approx(120.0)
        assert val.base_calculo == pytest.approx(120.0)
        assert val.valor_liquido_nfse == pytest.approx(120.0)

        # Avisos honestos esperados: sem código de verificação eletrônico
        # nesta nota e prestador não identificado (sentinela CNPJ).
        assert "Código de verificação/autenticidade não encontrado" in nfse.avisos
        assert "Dados do prestador não identificados" in nfse.avisos
        # A regressão do número foi corrigida: não deve mais gerar aviso.
        assert "Número da nota não encontrado" not in nfse.avisos
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
