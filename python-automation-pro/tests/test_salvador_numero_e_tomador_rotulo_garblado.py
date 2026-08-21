# -*- coding: utf-8 -*-
"""Salvador/BA escaneado — nota real nº 2418 (LUNITECK -> BONI TRANSPORTES,
mesma família das notas 2419/PREFEITURA e 2418/ERESTADOR já cobertas):
"Número da Nota" sai "Número da Nóta" (acento espúrio no "o" de "Nota") e o
rótulo "TOMADOR DE SERVIÇOS" garbla só a parte final ("TOMADOR BE SERVIÇOS."),
deixando "BE SERVIÇOS" sobrar como se fosse a 1ª linha de conteúdo do bloco —
e o rótulo seguinte "Nome/Razão Social" (garblado "Norma/Razab Sonia") também
sobrevive como candidato antes da razão social real.
"""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_OCR_P1 = (
    'PRESTADOR DE SERVIÇOS\n'
    'CPF/CNPJ\n'
    '07.295.620/0001-44\n'
    'Nome/Razão Social\n'
    'LUNITECK - SOLUCOES E DESENVOLVIMENTO EM TECNOLOGIA LTDA - ME RG Er\n'
    'Endereço\n\n'
    'PS apa Número da Nóta:\n'
    'fADOR 00002418\n'
    'Data-e:Hora de Emissão:\n'
    '13/07/2026 16:00:06:\n'
    'ei mes CGódicao de Verficarãe-.\n\n'
    'PREFEITURA MUNICIPAL DO SALVADOR DOneR a Nota:\n'
    'SECRETARIA MUNICIPAL DA FAZENDA Data:e:Hora de.\n\n'
    'NOTA FISCAL DE SERVIÇOS ELETRÔNICA -Notá salvador | Código de Verificação:\n\n'
    'ERESTADOR DE SERVIÇOS\n\n'
    'Inserição:Miihicipar.\n'
    ':D0/384:869/001-60\n\n'
    'TOMADOR BE SERVIÇOS.\n\n'
    'Norma/Razab Sonia\n'
    'BONI. TRANSRORTES, LOGISTICA E-COMERCÍO LTDA. .\n'
    '"CPREYCNPJ Insenção Municipal;\n'
    'Da. 66.263/0003:50 cime o\n'
    'Endereço:\n'
    'udãs MARIA QUITERIA. 1268; GALPAO. TINHA, » \'Ldurode Freitas  «CEP::42738-205/BA\n\n'
    '= mail;\n\n'
    'jRação Pe seus\n\n'
    'VALOR TOTAL DA NOTA = R$397,14\n\n'
    'RE 800-= Reparação: ecmaniitenção- de computadores e -dé equipamentos periféricos\n\n'
    'item da Lista de Serviços;\n'
    '01402: Assistência Téchica.\n'
)


def test_salvador_numero_e_tomador_recuperados_apesar_do_rotulo_garblado():
    dummy_path = "tests/dummy_salvador_luniteck_2418_numero_tomador.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    try:
        extractor = SPPdfExtractor(dummy_path)
        extractor.raw_text = MOCK_OCR_P1
        extractor.layout = extractor._detect_layout()
        assert extractor.layout == 'salvador_ba'

        # BUG CORRIGIDO — "Número da Nóta" (acento espúrio) não pode mais
        # cair no sentinela "00000000".
        assert extractor._extrair_numero() == "00002418"

        # BUG CORRIGIDO — a razão social do tomador não pode ser o resto
        # garblado do próprio cabeçalho de seção ("BE SERVIÇOS") nem o
        # rótulo garblado seguinte ("Norma/Razab Sonia"); tem que achar a
        # linha real da empresa.
        tomador = extractor._extrair_entidade('tomador')
        assert tomador.razao_social != "BE SERVIÇOS"
        assert "Razab" not in tomador.razao_social
        assert "BONI" in tomador.razao_social
        assert "LTDA" in tomador.razao_social
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
