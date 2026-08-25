# -*- coding: utf-8 -*-
"""Salvador/BA escaneado — variante do OCR que corrompe "PRESTADOR" para uma
palavra que não bate a lista de exclusão por igualdade exata (nota real
nº 2418, LUNITECK -> BONI TRANSPORTES, mesma família da nota 2419 já coberta
em test_salvador_codigo_verificacao_nao_confunde_titulo.py).

Aqui o OCR leu "PRESTADOR" como "ERESTADOR" (1º caractere trocado) — não bate
nenhuma palavra da lista antiga de exclusão exata, mas ainda É o mesmo rótulo
de seção, não um código. Sem a comparação por sufixo/prefixo (ver
gotcha_layout_detection_collision / correção 2026-08-21), esse valor caía no
fallback GENÉRICO mais abaixo (compartilhado por ~30 layouts, mais permissivo
com espaço/tab dentro do candidato) e virava "ERESTADORDESERVI" — ainda pior,
por atravessar a palavra seguinte "DE SERVIÇOS".
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


def test_salvador_codigo_verificacao_rejeita_prestador_garblado():
    dummy_path = "tests/dummy_salvador_luniteck_2418_p1.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    try:
        extractor = SPPdfExtractor(dummy_path)
        extractor.raw_text = MOCK_OCR_P1
        extractor.layout = extractor._detect_layout()
        assert extractor.layout == 'salvador_ba'

        codigo = extractor._extrair_codigo_verificacao()

        # BUG CORRIGIDO — nem a variante garblada do rótulo, nem o fallback
        # genérico ainda mais permissivo por trás dela.
        assert codigo != "ERESTADOR"
        assert "SERVI" not in codigo
        assert codigo == "XXXX-XXXX"
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
